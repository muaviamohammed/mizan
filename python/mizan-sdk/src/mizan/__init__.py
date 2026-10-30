"""
mizan — proof before payment. Check any agent before you pay it; prove your own record without revealing your method. One line in, one line out.

    import mizan
    cred = mizan.prove(positions, markets=["btc_4h", "eth_4h"], alias="my-agent")   # preview → H100 mint → bundle
    mizan.verify(cred.bundle)                                                        # the public verifier, exit 0 / 1

Stdlib only. `positions` is a pandas DataFrame (one column per market, in order), a
list of rows, a 1-D list for one market, or a path to a CSV/JSON file. Values are
leverages: 1 = 100% long, -0.5 = 50% short, 0 = flat. One row per bar-move; the
catalogue tells you how many rows a market needs (`mizan.catalog()`).

Privacy, plainly: the hosted prover sees the positions you submit (never your
code); the credential reveals neither. Salts are generated here and saved under
~/.mizan/sdk/ — keep them to extend the track later.
"""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import re
import os
import platform
import secrets
import shutil
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

__version__ = "0.8.0"
BASE = os.environ.get("MIZAN_BASE", "https://studio.mizan.market")
SITE = os.environ.get("MIZAN_SITE", "https://mizan.market")
HOME = os.path.expanduser(os.environ.get("MIZAN_HOME", "~/.mizan/sdk"))
os.makedirs(HOME, exist_ok=True)
_JAR = os.path.join(HOME, "cookies.txt")
_jar = http.cookiejar.LWPCookieJar(_JAR)
if os.path.exists(_JAR):
    try:
        _jar.load(ignore_discard=True)
    except Exception:
        pass
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_jar))
_KEYFILE = os.path.join(HOME, "api_key")
_API_KEY = os.environ.get("MIZAN_API_KEY") or (open(_KEYFILE).read().strip() if os.path.exists(_KEYFILE) else "")


class MizanError(RuntimeError):
    pass


# ── HTTP ──────────────────────────────────────────────────────────────────────
def _req(path: str, body: dict | None = None, method: str | None = None, raw: bool = False, timeout: int = 120):
    url = path if path.startswith("http") else BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                               headers={"Content-Type": "application/json", "User-Agent": f"mizan-sdk/{__version__}",
                                        **({"Authorization": "Bearer " + _API_KEY} if _API_KEY else {})})
    try:
        with _opener.open(r, timeout=timeout) as resp:
            payload = resp.read()
            _jar.save(ignore_discard=True)
            out = payload if raw else (json.loads(payload) if payload else {})
            if not raw and isinstance(out, dict):
                _remember_key(out)
            return out
    except urllib.error.HTTPError as e:
        txt = e.read().decode(errors="replace")
        try:
            msg = json.loads(txt).get("error") or txt
        except Exception:
            msg = txt
        raise MizanError(f"{e.code} {path}: {msg[:400]}") from None


def login(email: str | None = None, password: str | None = None, signup: bool = False, api_key: str | None = None) -> dict:
    """Three ways in. (1) api_key="mzn_…" (or MIZAN_API_KEY): headless, no browser, what an agent uses.
    (2) email + password (or MIZAN_EMAIL / MIZAN_PASSWORD); signup=True creates a free account.
    (3) wallet_login(private_key) below: an EVM wallet signs a nonce, no email at all."""
    global _API_KEY
    api_key = api_key or os.environ.get("MIZAN_API_KEY")
    if api_key:
        _API_KEY = api_key.strip()
        _save_key(_API_KEY)
        return _req("/product/me")
    email = email or os.environ.get("MIZAN_EMAIL")
    password = password or os.environ.get("MIZAN_PASSWORD")
    if not email or not password:
        raise MizanError("login needs api_key, or email + password (or MIZAN_API_KEY / MIZAN_EMAIL / MIZAN_PASSWORD)")
    try:
        return _req("/product/signup" if signup else "/product/login", {"email": email, "password": password})
    except MizanError as e:
        if not signup and "401" in str(e) or "not found" in str(e).lower():
            return _req("/product/signup", {"email": email, "password": password})
        raise


def _remember_key(reply: dict) -> None:
    """MIZAN registers an agent on its first call and returns a key once (reply["you"]["key"]). Keep it, so the next call
    is identified and builds your record. Disable with MIZAN_NO_KEY_STORE=1; the file is chmod 600 in ~/.mizan/sdk/."""
    global _API_KEY
    try:
        k = ((reply or {}).get("you") or {}).get("key")
        if k and not _API_KEY and not os.environ.get("MIZAN_NO_KEY_STORE"):
            _API_KEY = k
            _save_key(k)
    except Exception:
        pass


def _save_key(key: str) -> None:
    try:
        with open(_KEYFILE, "w") as f:
            f.write(key)
        os.chmod(_KEYFILE, 0o600)
    except Exception:
        pass


def create_api_key(label: str = "agent") -> str:
    """Mint an API key for the signed-in account (shown once; stored in ~/.mizan/sdk/api_key)."""
    global _API_KEY
    d = _req("/product/keys", {"label": label})
    _API_KEY = d["api_key"]; _save_key(_API_KEY)
    return _API_KEY


def wallet_login(private_key: str | None = None, address: str | None = None, signer=None) -> dict:
    """Log in as an EVM wallet: the server issues a nonce, the wallet signs it (EIP-191), MIZAN returns an API key.
    Pass a private key (needs `pip install eth-account`), or address + signer(message)->signature for a custodial agent."""
    global _API_KEY
    if private_key:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        acct = Account.from_key(private_key); address = acct.address
        signer = lambda msg: acct.sign_message(encode_defunct(text=msg)).signature.hex()
    if not address or signer is None:
        raise MizanError("wallet_login needs private_key, or address + signer")
    n = _req("/product/wallet/nonce", {"address": address})
    sig = signer(n["message"]); sig = sig if sig.startswith("0x") else "0x" + sig
    d = _req("/product/wallet/login", {"address": address, "signature": sig})
    _API_KEY = d["api_key"]; _save_key(_API_KEY)
    return d


def me() -> dict | None:
    try:
        return _req("/product/me").get("user")
    except MizanError:
        return None


# ── catalogue ─────────────────────────────────────────────────────────────────
def catalog() -> dict:
    """Every mintable market: key → {label, bars, first, last, interval, sha256, root, align_group}."""
    d = _req("/api/blackbox-datasets")
    return {x["key"]: x for x in d.get("datasets", [])}


def markets(cls: str | None = None) -> list[str]:
    return [k for k, v in catalog().items() if not cls or v.get("cls") == cls]


# ── positions → integer rows ──────────────────────────────────────────────────
def _rows(positions, k_hint: int | None = None) -> list[list[int]]:
    if isinstance(positions, str) and os.path.exists(positions):
        txt = open(positions).read().strip()
        if txt[:1] in "[{":
            positions = json.loads(txt)
        else:
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            split = lambda l: [t.strip() for t in l.replace(";", ",").replace("\t", ",").split(",")]
            f0 = split(lines[0])
            start = 1 if any(_isdate(t) is False and not _isnum(t) for t in f0) else 0
            out = []
            for l in lines[start:]:
                f = split(l)
                if f and _isdate(f[0]):
                    f = f[1:]
                out.append([float(x) for x in f])
            positions = out
    try:                         # pandas DataFrame / Series without importing pandas
        if hasattr(positions, "to_numpy"):
            arr = positions.to_numpy()
            positions = arr.tolist()
    except Exception:
        pass
    if not positions:
        raise MizanError("positions is empty")
    rows = positions if isinstance(positions[0], (list, tuple)) else [[x] for x in positions]
    out = []
    for i, r in enumerate(rows):
        try:
            o = [int(round(float(x) * 100)) for x in r]
        except Exception:
            raise MizanError(f"row {i}: a value is not a number") from None
        if any(abs(x) > 1000 for x in o):
            raise MizanError(f"row {i}: |position| above 10× is refused")
        out.append(o)
    if k_hint and len(out[0]) != k_hint:
        raise MizanError(f"positions have {len(out[0])} columns but {k_hint} markets were given")
    return out


def _isnum(t: str) -> bool:
    try:
        float(t); return True
    except Exception:
        return False


def _isdate(t: str) -> bool:
    return (len(t) >= 10 and t[4] == "-" and t[7] == "-") or (t.isdigit() and 9 <= len(t) <= 13)


# ── check before you pay ──────────────────────────────────────────────────────
def check_before_you_pay(positions, markets: list[str] | str, model_id: str = "agent", leverage_x100: int = 100,
                         gross_cap_x100: int | None = None) -> dict:
    """Free. Runs the gate on your positions and returns the verdict plus the exact price a real mint would cost.
    Nothing is minted or charged. Keys: would_mint, gate_pass, metrics, price{amount, asset, network, free_trial}."""
    mk = [markets] if isinstance(markets, str) else list(markets)
    rows = _rows(positions, len(mk))
    gross = max(sum(abs(x) for x in r) for r in rows)
    cap = gross_cap_x100 or max(100, gross)
    base = {"model_id": model_id, "model_salt": secrets.token_hex(32), "track_salt": secrets.token_hex(32), "disclose": True}
    parity = len(mk) == 1 and all(r[0] in (-100, 0, 100) for r in rows)
    if parity:
        body = dict(base, positions=[r[0] // 100 for r in rows], dataset=mk[0], leverage_x100=leverage_x100)
    else:
        body = dict(base, positions=rows, datasets=mk, gross_cap_x100=cap, dataset=mk[0])
    return _req("/api/check-before-you-pay", body)


# ── the credential object ─────────────────────────────────────────────────────
class Credential:
    def __init__(self, job_id: str, status: dict, bundle: str | None, parts: str | None, track: str | None, markets_: list[str]):
        self.job_id, self.status, self.bundle, self.parts, self.track, self.markets = job_id, status, bundle, parts, track, markets_

    @property
    def verdict(self) -> str:
        return "PASS" if self.status.get("passed") else ("FAIL" if self.status.get("state") == "done" else self.status.get("state", "?"))

    @property
    def url(self) -> str:
        return f"{BASE}/credential/bb-{self.job_id}"

    @property
    def metrics(self) -> dict:
        return {k: self.status.get(k) for k in ("sharpe", "cagr", "maxdd") if self.status.get(k) is not None}

    def __repr__(self) -> str:
        return f"<mizan.Credential {self.verdict} job={self.job_id} markets={self.markets} bundle={self.bundle} url={self.url}>"


# ── prove ─────────────────────────────────────────────────────────────────────
def prove(positions, markets: list[str] | str, alias: str = "SEALED-AGENT", *, model_id: str | None = None,
          gross_cap: float | None = None, preview_only: bool = False, wait: bool = True, out_dir: str = ".",
          minimal: bool = False, marketplace: bool = False, poll_s: int = 30, verbose: bool = True) -> "Credential | dict":
    """Preview the gate (free, seconds). If it clears and preview_only is False, queue the
    real H100 mint, wait for it, download the bundle (+parts/track) and return a Credential.
    A preview that does not clear returns the preview dict (nothing minted)."""
    if isinstance(markets, str):
        markets = [markets]
    if not me():
        login()
    cat = catalog()
    for k in markets:
        if k not in cat:
            raise MizanError(f"unknown market '{k}' — see mizan.markets()")
    rows = _rows(positions, k_hint=len(markets))
    need = cat[markets[0]]["bars"] - 1
    if len(rows) != need:
        raise MizanError(f"{markets[0]} runs {cat[markets[0]]['first']} → {cat[markets[0]]['last']} ({cat[markets[0]]['bars']} bars): "
                         f"needs exactly {need} rows (one per bar-move); got {len(rows)}")
    groups = {cat[k]["align_group"] for k in markets}
    if len(groups) != 1:
        raise MizanError("markets in one book must share a calendar: " + ", ".join(f"{k}={cat[k]['first']}→{cat[k]['last']}" for k in markets))
    gross = max(sum(abs(x) for x in r) for r in rows)
    cap = int(round((gross_cap or max(1.0, gross / 100)) * 100))
    if gross > cap:
        raise MizanError(f"gross exposure reaches {gross/100:.2f}× but gross_cap is {cap/100:.2f}×")
    model_id = model_id or f"{alias.lower()}-{time.strftime('%Y-%m')}"
    salts = {"model_salt": secrets.token_hex(32), "track_salt": secrets.token_hex(32)}
    base = {"model_id": model_id, "alias": alias.upper().replace(" ", "-")[:40], "quant": (me() or {}).get("email", "quant").split("@")[0],
            "disclose": True, "minimal": minimal, "marketplace": marketplace, **salts}
    parity = len(markets) == 1 and all(r[0] in (-100, 0, 100) for r in rows)
    if parity:
        body = dict(base, positions=[r[0] // 100 for r in rows], dataset=markets[0], leverage_x100=cap)
    else:
        body = dict(base, positions=rows, datasets=markets, gross_cap_x100=cap, dataset=markets[0])
    prev = _req("/api/submit-blackbox", dict(body, preview_only=True), timeout=400)
    if verbose:
        print(f"[mizan] preview: gate {'PASS' if prev.get('gate_pass') else 'FAIL'} · Sharpe {prev.get('sharpe')} · CAGR {prev.get('cagr')}% · MaxDD {prev.get('maxdd')}% · {prev.get('n_periods')} rows × {len(markets)} market(s)")
    if preview_only or not prev.get("gate_pass"):
        return prev
    r = _req("/api/submit-blackbox", body, timeout=400)
    job = r.get("job_id")
    if not job:
        raise MizanError(f"mint not queued: {r}")
    with open(os.path.join(HOME, f"salts_{job}.json"), "w") as f:
        json.dump(dict(salts, model_id=model_id, markets=markets), f)
    if verbose:
        print(f"[mizan] real mint queued · job {job} · {r.get('message','')}")
    if not wait:
        return Credential(job, r, None, None, None, markets)
    return fetch(job, out_dir=out_dir, poll_s=poll_s, verbose=verbose, markets_=markets)


def status(job_id: str) -> dict:
    return _req(f"/api/blackbox-submission/{job_id}")


def fetch(job_id: str, out_dir: str = ".", poll_s: int = 30, verbose: bool = True, markets_: list[str] | None = None) -> Credential:
    """Wait for a queued mint, then download bundle + sidecars."""
    last = None
    while True:
        st = status(job_id)
        if st.get("state") != last and verbose:
            print(f"[mizan] {job_id}: {st.get('state')}" + (f" · #{st.get('queue_pos')} in line" if st.get("queue_pos") else ""))
            last = st.get("state")
        if st.get("state") in ("done", "failed", "cancelled"):
            break
        time.sleep(poll_s)
    if st.get("state") != "done":
        raise MizanError(f"mint {st.get('state')}: {st.get('error')}")
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for kind, name in (("bundle", f"{job_id}.bundle"), ("parts", f"{job_id}_parts.json"), ("track", f"{job_id}_track_head.json")):
        try:
            data = _req(f"/api/blackbox-submission/{job_id}/{kind}", raw=True)
        except MizanError:
            data = None
        if data:
            p = os.path.join(out_dir, name)
            open(p, "wb").write(data)
            paths[kind] = p
    mk = markets_ or st.get("datasets") or [st.get("dataset")]
    c = Credential(job_id, st, paths.get("bundle"), paths.get("parts"), paths.get("track"), mk)
    if verbose:
        print(f"[mizan] {c.verdict} · {c.bundle} · {c.url}")
    return c


# ── verify ────────────────────────────────────────────────────────────────────
def _os_tag() -> str:
    s, m = platform.system(), platform.machine().lower()
    if s == "Darwin" and m in ("arm64", "aarch64"):
        return "macos-arm64"
    if s == "Linux" and m in ("x86_64", "amd64"):
        return "linux-x86_64"
    if s == "Windows" and m in ("amd64", "x86_64"):
        return "windows-x86_64.exe"
    raise MizanError(f"no published verifier for {s}/{m} — see https://mizan.market/verify/ for the published platforms")


def _sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def _download(url: str, dest: str) -> str:
    if not os.path.exists(dest):
        data = _req(url, raw=True, timeout=600)
        open(dest, "wb").write(data)
    return dest


def verifier(era: str = "v12") -> str:
    """The published verifier for this OS and era, sha256-checked against SHA256SUMS.txt."""
    name = f"mizan-verifier-{era}-{_os_tag()}"
    sums = _req(f"{SITE}/verify/files/SHA256SUMS.txt", raw=True).decode()
    want = next((l.split()[0] for l in sums.splitlines() if l.strip().endswith(name)), None)
    if not want:
        raise MizanError(f"{name} is not in the published SHA256SUMS.txt")
    dest = _download(f"{SITE}/verify/files/{name}", os.path.join(HOME, name))
    if _sha(dest) != want:
        os.remove(dest)
        raise MizanError(f"{name}: downloaded sha256 does not match the published checksum — refused")
    os.chmod(dest, os.stat(dest).st_mode | stat.S_IXUSR)
    return dest


def series(key: str) -> str:
    """The canonical CSV for a catalogue market, sha256-checked against the catalogue."""
    cat = catalog()
    if key not in cat:
        raise MizanError(f"unknown market '{key}'")
    dest = _download(f"/api/catalog/{key}.csv", os.path.join(HOME, f"{key}.csv"))
    if _sha(dest) != cat[key]["sha256"]:
        os.remove(dest)
        raise MizanError(f"{key}.csv does not match the catalogue sha256 — refused")
    return dest


def verify(bundle, markets_: list[str] | None = None, *, aux: str | None = None, track: str | None = None,
           era: str | None = None, extra: list[str] | None = None, verbose: bool = True) -> int:
    """Run the PUBLIC era-pinned verifier on a bundle. Pass a Credential or a path.
    Returns the verifier's exit code (0 = verified). Markets default to the credential's."""
    if isinstance(bundle, Credential):
        markets_ = markets_ or bundle.markets
        aux, track, path = aux or bundle.parts, track or bundle.track, bundle.bundle
    else:
        path = bundle
    if not markets_:
        raise MizanError("verify needs the markets the credential was proved on (list of catalogue keys)")
    csvs = [series(k) for k in markets_]
    roots = _download("/api/catalog/roots.txt", os.path.join(HOME, f"roots_{int(time.time()) // 3600}.txt"))
    args = list(extra or [])
    if aux:
        args += ["--aux", aux]
    if track:
        args += ["--track", track]
    bin_ = verifier(era or "v12")
    p = subprocess.run([bin_, path, *csvs, *args, "--roots", roots], capture_output=True, text=True)
    out = p.stdout + p.stderr
    if era is None and p.returncode != 0:          # era law: verify with the minting era's verifier
        for line in out.splitlines():
            if "Engine era:" in line:
                found = line.split("Engine era:")[1].split("·")[0].strip()
                if found and found != "v12":
                    return verify(bundle, markets_, aux=aux, track=track, era=found, extra=extra, verbose=verbose)
    if verbose:
        print(out)
    return p.returncode


# ── receipts, status, log, gate (2026-10-20) ─────────────────────────────────
def receipt(credential_id: str) -> dict:
    """Signed verdict receipt to carry in an agent card; verify with mizan.gate.verify_receipt_offline."""
    return _req(f"/api/receipt/{credential_id}")


def status(credential_id: str) -> dict:  # noqa: F811 — job status is mizan.status(job_id); credential status by id works the same route family
    return _req(f"/api/status/{credential_id}") if not re.fullmatch(r"[0-9a-f]{12}", credential_id or "") else _req(f"/api/submission/{credential_id}/status")


def log_head() -> dict:
    return _req("/api/log/head")


def log_proof(credential_id: str) -> dict:
    return _req(f"/api/log/proof-for/{credential_id}")


def standing() -> dict:
    return _req("/api/standing")


def everything() -> dict:
    return _req("/api/everything")


from .gate import require_credential, allocate_check, verify_allocate_check, verify_receipt_offline, POLICY_TEXT  # noqa: E402,F401


# ---------------------------------------------------------------- where demand arrives (0.7.0)
def find(capability: str, bar: str = "", requirement_id: str = "", limit: int = 10, sort: str = "") -> dict:
    """Only listed agents that offer `capability` and meet your bar, each with a signed per-clause answer and a receipt.
    Filtered by proven facts only; ordering disclosed; never paid placement."""
    body = {"capability": capability, "limit": limit}
    if bar: body["text"] = bar
    if requirement_id: body["requirement_id"] = requirement_id
    if sort: body["sort"] = sort
    return _req("/api/find", body)


def declare_capabilities(capabilities: list, endpoints: list | None = None, listed: bool = True, pricing: str = "",
                         notify_url: str = "", notify_optin: bool = False) -> dict:
    """Be findable: declare what you offer (published vocabulary) and opt in to discovery. Needs your key (login(api_key=...))."""
    body = {"capabilities": capabilities, "listed": listed}
    if endpoints is not None: body["endpoints"] = endpoints
    if pricing: body["pricing"] = pricing
    if notify_url: body["notify_url"] = notify_url; body["notify_optin"] = notify_optin
    return _req("/api/agents/capabilities", body)


def unlist() -> dict:
    """Leave discovery immediately."""
    return _req("/api/agents/unlist", {})


def my_demand() -> dict:
    """Searches for your capabilities (shown only when 3+ buyers searched), bars you miss with the one step, open requests,
    your record clock and payments you lost by being unproven."""
    return _req("/api/agents/me/demand")


def demand(capability: str, bar: str, budget_band: str = "", days: int = 14) -> dict:
    """Post an anonymous buyer request sellers can see (no buyer identity is stored or shown)."""
    body = {"capability": capability, "text": bar, "days": days}
    if budget_band: body["budget_band"] = budget_band
    return _req("/api/demand", body)


def limits(policy_id: str, agent: str) -> dict:
    """The tier a platform's limits policy assigns to an agent, and the step up."""
    return _req("/api/limits/%s/check?agent=%s" % (urllib.parse.quote(policy_id), urllib.parse.quote(agent)))


# ── Accountable after payment (0.8.0): who an agent works for, what happened after others paid it, watch ─────
def acts_for(agent: str) -> dict:
    """The principals an agent acts for, each proven by the principal's own key (public authorities only)."""
    return _req("/api/authority/acts-for/" + urllib.parse.quote(agent, safe=""))


def prepare_authority(principal: str, agent: str, scope: list | None = None, max_amount: float | None = None, currency: str = "",
                      per: str = "", purpose: str = "", days: int = 365, visibility: str = "counterparty") -> dict:
    """The exact object a principal signs (sign_this) to authorise an agent, and how to sign it with its own key."""
    lim = {k: v for k, v in (("max_amount", max_amount), ("currency", currency or None), ("per", per or None)) if v is not None}
    return _req("/api/authority/prepare", {"principal": principal, "agent": agent, "scope": scope or ["pay"], "limits": lim, "purpose": purpose,
                                           "expires": int(time.time()) + max(1, min(int(days), 730)) * 86400, "visibility": visibility})


def submit_authority(authority: dict | None = None, *, jws: str = "", signature: str = "") -> dict:
    """Submit a principal-signed authority (jws for domain/key principals; signature for wallets/passkeys)."""
    return _req("/api/authority", {"authority": authority, "jws": jws, "signature": signature})


def accept_authority(authority_id: str) -> dict:
    return _req("/api/authority/%s/accept" % urllib.parse.quote(authority_id), {})


def revoke_authority(authority_id: str, *, jws: str = "", signature: str = "") -> dict:
    """The agent renounces with its API key; a principal sends its own signature over the revoke object."""
    return _req("/api/authority/%s/revoke" % urllib.parse.quote(authority_id), {"jws": jws, "signature": signature} if (jws or signature) else {})


def report_outcome(seller: str, payment_ref: str, check_token: str, *, delivered: bool | None = None, on_time: bool | None = None,
                   matched_spec: bool | None = None, spec_hash: str = "", evidence_hashes: list | None = None, note: str = "") -> dict:
    """After you paid: facts, never a rating. Needs the token of the check you ran before paying; one outcome per payment."""
    return _req("/api/outcomes", {"seller": seller, "payment_ref": payment_ref, "check_token": check_token, "delivered": delivered,
                                  "on_time": on_time, "matched_spec": matched_spec, "spec_hash": spec_hash,
                                  "evidence_hashes": evidence_hashes or [], "note": note})


def respond_outcome(outcome_id: str, stance: str, evidence_hashes: list | None = None, note: str = "") -> dict:
    """Sellers: 'accepted' or 'disputed'; shown beside the outcome, always."""
    return _req("/api/outcomes/%s/respond" % urllib.parse.quote(outcome_id), {"stance": stance, "evidence_hashes": evidence_hashes or [], "note": note})


def watch(subject: str, events: list | None = None, notify_url: str = "") -> dict:
    """Hear when an agent's standing changes (revoked, status, authority, outcome, listing, requirement:req_…)."""
    return _req("/api/watch", {"subject": subject, "events": events, "notify_url": notify_url or None})


def alerts() -> dict:
    """Your watches and unseen alerts."""
    return _req("/api/watch")


def unwatch(watch_id: str) -> dict:
    return _req("/api/watch/" + urllib.parse.quote(watch_id), method="DELETE")
