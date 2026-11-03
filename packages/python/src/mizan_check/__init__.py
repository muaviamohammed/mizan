"""mizan-check: a signed yes or no on whether an AI agent's results are real, before you pay it.

A thin client for the public MIZAN API (https://studio.mizan.market). Standard library only;
offline signature checks use `cryptography` (installed with this package).

    from mizan_check import check, verify_token, guard

    d = check("try-me")                                   # free, no key
    d["decision"], d["evidence_rung"]                     # "ALLOW", "PROVEN"
    verify_token(d["token"])                              # Ed25519, offline, raises if forged or expired
    bind_token(d["token"], subject="try-me")              # ...and about THIS subject, ALLOW (what guard() requires)

    d = check("model:openai/gpt-oss-20b", rule="pass@1 at least 60% over at least 20 tasks")

Payer side: check, guard. Payee side: claim, link_challenge, link_complete, enroll.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

__all__ = [
    "API", "MizanError", "MizanRefused",
    "check", "compile_rule", "rule_hash", "verify_token", "bind_token", "verify_reply", "verify_message", "load_keys",
    "guard", "claim", "link_challenge", "link_complete", "enroll",
]
__version__ = "0.2.0"

API = os.environ.get("MIZAN_API", "https://studio.mizan.market")
USER_AGENT = f"mizan-check-py/{__version__} (+https://github.com/muaviamohammed/mizan)"


class MizanError(RuntimeError):
    """The API answered with an error, or could not be reached."""


class MizanRefused(RuntimeError):
    """Raised by guard(mode="enforce") when there is no verified ALLOW. Nothing was paid."""

    def __init__(self, verdict: dict):
        self.verdict = verdict
        self.proof_request = verdict.get("proof_request")
        super().__init__(f"MIZAN: {verdict.get('decision', 'REFUSE')} for {verdict.get('subject', '?')}: "
                         f"{verdict.get('explain') or verdict.get('error') or 'no verified ALLOW'}")


# ---------------------------------------------------------------- HTTP

def _req(method: str, path: str, body: dict | None = None, key: str | None = None, timeout: float = 20) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code >= 500:
            raise MizanError(f"HTTP {e.code} on {path}: service unavailable") from e
        try:
            return json.loads(e.read())          # MIZAN errors are JSON with explain + next
        except Exception:
            raise MizanError(f"HTTP {e.code} on {path}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise MizanError(f"unreachable: {e}") from e


# ---------------------------------------------------------------- rules (the bar)

def compile_rule(words: str) -> dict:
    """Plain words in, an exact rule back: {requirement, shown_back, unmatched, hash, publishable}. Free, no key."""
    return _req("POST", "/api/requirements/compile", {"text": words})


def rule_hash(requirement: dict) -> str:
    """Recompute a rule's hash locally: SHA-256 over canonical JSON (keys sorted, no spaces, ASCII)."""
    return hashlib.sha256(json.dumps(requirement, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


# ---------------------------------------------------------------- the check

def check(subject: str, rule: str | dict | None = None, *, amount: float | None = None, currency: str = "USD",
          purpose: str = "", key: str | None = None, timeout: float = 20) -> dict:
    """One signed ALLOW or REFUSE for `subject` (an agent id, domain, endpoint, model:<org>/<name>, wallet...).

    rule: None (default bar), a published rule id "req_...@v", plain words (compiled first),
    or a rule object as returned by compile_rule()["requirement"].
    """
    if rule is None and amount is None and not purpose:
        d = _req("GET", "/api/check/" + urllib.parse.quote(subject, safe=":@"), key=key, timeout=timeout)
    elif isinstance(rule, str) and rule.startswith("req_"):
        q = urllib.parse.urlencode({"requirement": rule})
        d = _req("GET", "/api/check/" + urllib.parse.quote(subject, safe=":@") + "?" + q, key=key, timeout=timeout)
    else:
        body: dict[str, Any] = {"agent": subject, "currency": currency}
        if amount is not None:
            body["amount"] = amount
        if purpose:
            body["purpose"] = purpose
        if isinstance(rule, str):
            c = compile_rule(rule)
            if c.get("unmatched") or not c.get("requirement"):
                raise MizanError(f"rule not understood: {c.get('unmatched') or c.get('refusal')}")
            rule = c["requirement"]
        if isinstance(rule, dict):
            body["requirement"] = rule
        d = _req("POST", "/api/check", body, key=key, timeout=timeout)
    if "decision" not in d:
        raise MizanError(d.get("explain") or d.get("error") or "no decision in reply")
    return d


# ---------------------------------------------------------------- offline verification

_KEYS: dict | None = None
PINNED_KEYS_ENV = "MIZAN_PINNED_KEYS"                 # path to your copy of mizan-keys.json, or that JSON inline
PINNED_KEYS_SHA256_ENV = "MIZAN_PINNED_KEYS_SHA256"   # optional: sha256 of that file; a mismatch raises (fail closed)


def _pinned_from_env() -> dict | None:
    env = (os.environ.get(PINNED_KEYS_ENV) or "").strip()
    if not env:
        return None
    raw = env.encode() if env.startswith("{") else open(os.path.expanduser(env), "rb").read()
    want = (os.environ.get(PINNED_KEYS_SHA256_ENV) or "").strip().lower()
    if want and hashlib.sha256(raw).hexdigest() != want:
        raise MizanError(f"{PINNED_KEYS_ENV} does not match {PINNED_KEYS_SHA256_ENV}: refusing to trust it")
    return json.loads(raw)


def load_keys(refresh: bool = False) -> dict:
    """The keys every verification in this package uses.

    Pinned (recommended in production): set MIZAN_PINNED_KEYS to a copy of
    https://studio.mizan.market/.well-known/mizan-keys.json (a path, or the JSON inline) and, optionally,
    MIZAN_PINNED_KEYS_SHA256 to that file's sha256. When pinned, keys are NEVER fetched from the network.
    You can also pass keys=<that object> to verify_token / verify_message / verify_reply / bind_token / guard.

    Default (no pin): FETCHED once per process from the URL above over HTTPS. That trusts the network path and the
    API at fetch time; pin the file to remove that trust.
    """
    global _KEYS
    pinned = _pinned_from_env()
    if pinned is not None:
        return pinned
    if _KEYS is None or refresh:
        _KEYS = _req("GET", "/.well-known/mizan-keys.json")
    return _KEYS


def _ed25519(key_id: str, message: bytes, sig: bytes, keys: dict | None = None) -> bool:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    keys = keys or load_keys()
    k = next((k for k in keys["keys"] if k.get("alg") == "Ed25519" and k.get("key_id") == key_id), None)
    if k is None:
        return False
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(k["public_key_b64"])).verify(sig, message)
        return True
    except InvalidSignature:
        return False


def _b64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def verify_token(token: str, *, keys: dict | None = None, now: float | None = None) -> dict:
    """Verify a check token (compact JWS, EdDSA) offline. Returns its payload; raises MizanError if invalid or expired."""
    try:
        h, p, s = token.split(".")
        header = json.loads(_b64u(h))
        payload = json.loads(_b64u(p))
    except Exception as e:
        raise MizanError("not a MIZAN token") from e
    if header.get("alg") != "EdDSA" or not _ed25519(header.get("kid", ""), f"{h}.{p}".encode(), _b64u(s), keys):
        raise MizanError("signature does not verify against the published key")
    if payload.get("exp", 0) < (now or time.time()):
        raise MizanError("token expired")
    return payload


def bind_token(token: str, *, subject: str, requirement_hash: str | None = None, keys: dict | None = None,
               now: float | None = None) -> dict:
    """verify_token, then the binding guard() needs. Returns the payload; raises MizanError unless ALL hold:
    the signature verifies and the token is unexpired; its decision is ALLOW; it is about `subject` (its sub,
    subject_as_given or subject_requested equals the payee you are about to pay); and, when you pinned a rule,
    its requirement_hash equals that hash. A token for one payee never authorises another; a default-bar
    ALLOW never satisfies a guard pinned to a stricter rule."""
    payload = verify_token(token, keys=keys, now=now)
    if payload.get("decision") != "ALLOW":
        raise MizanError(f"the signed decision is {payload.get('decision')}, not ALLOW")
    norm = lambda x: (lambda s: s.lower() if s.lower().startswith("0x") else s)(str(x or "").strip())  # noqa: E731
    want = norm(subject)
    have = [norm(payload.get(k)) for k in ("sub", "subject_as_given", "subject_requested") if payload.get(k)]
    # the server stores at most 120 characters of a subject: a longer payee matches only that full stored prefix
    if not want or not any(want == h or (len(h) >= 120 and len(want) > len(h) and want.startswith(h)) for h in have):
        raise MizanError(f"the token is about {have or 'nobody'}, not {subject!r}: never an ALLOW for another payee")
    if requirement_hash:
        req = payload.get("requirement")
        got = payload.get("requirement_hash") or (req.get("hash") if isinstance(req, dict) else None)
        if str(got or "").lower() != str(requirement_hash).lower():
            raise MizanError("the token is not about the pinned rule (requirement_hash differs or is absent)")
    return payload


def verify_message(signed: dict, *, keys: dict | None = None, now: float | None = None) -> dict:
    """Verify a signed message object {message, signature, ...}: pricing_message, contract_message, attestation.
    Raises MizanError if the signature fails or the message has expired (expires_at, or expires on attestations)."""
    msg = signed["message"]
    canon = json.dumps(msg, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    if not _ed25519(msg["key_id"], canon, _b64u(signed["signature"]), keys):
        raise MizanError("signature does not verify against the published key")
    # pricing and contract messages carry expires_at; attestations carry expires. Either one ends validity.
    for field in ("expires_at", "expires"):
        if field in msg and (not isinstance(msg[field], (int, float)) or msg[field] < (now or time.time())):
            raise MizanError("message expired")
    return msg


def verify_reply(body: dict, *, keys: dict | None = None) -> bool:
    """Every JSON reply is signed: Ed25519 over canonical JSON of the body without provenance.signature."""
    sig = (body.get("provenance") or {}).get("signature")
    if not sig:
        return False
    copy = dict(body)
    copy["provenance"] = {k: v for k, v in body["provenance"].items() if k != "signature"}
    msg = json.dumps(copy, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if sig.get("canonical_sha256") and hashlib.sha256(msg).hexdigest() != sig["canonical_sha256"]:
        return False
    return _ed25519(sig["key_id"], msg, base64.b64decode(sig["sig_b64"]), keys)


# ---------------------------------------------------------------- in your payment path

def guard(pay: Callable[..., Any], *, mode: str = "advise", rule: str | dict | None = None,
          requirement_hash: str | None = None, on_verdict: Callable[[dict], None] | None = None,
          keys: dict | None = None, timeout: float = 5, advise_timeout: float = 1.5) -> Callable[..., Any]:
    """Wrap your own pay(payee, *args, **kw). MIZAN never holds or moves the money.

    enforce : pays only when the signed token verifies here AND names this payee AND says ALLOW AND is unexpired
              AND (when a rule is pinned) carries that rule's hash. Anything else, including a network error or a
              timeout, raises MizanRefused and nothing is paid (fail-closed).
    advise  : always pays; the verdict (or UNVERIFIABLE) goes to on_verdict for your log. The payment waits at most
              advise_timeout seconds (default 1.5) for MIZAN, whatever the network does.

    rule             : None (default bar), "req_...@v", plain words, or a rule object (see check()).
    requirement_hash : pin the rule. Taken from rule="req_...@v#<hash>", or hashed here for a rule object; plain words
                       are compiled once and their hash pinned. A bare "req_...@v" is bound by its signed ref only.
    keys             : pinned keys (the mizan-keys.json object). Default: load_keys(), which reads MIZAN_PINNED_KEYS
                       when set and never fetches then; without a pin it fetches the published keys once (see load_keys).
    """
    if mode not in ("advise", "enforce"):
        raise ValueError('mode must be "advise" or "enforce"')
    pinned_hash = requirement_hash
    if isinstance(rule, str) and rule.startswith("req_") and "#" in rule:
        rule, _, h = rule.partition("#")
        pinned_hash = pinned_hash or h.strip().lower()
    elif isinstance(rule, dict) and pinned_hash is None:
        pinned_hash = rule_hash(rule)
    elif isinstance(rule, str) and not rule.startswith("req_") and pinned_hash is None:
        c = compile_rule(rule)
        if c.get("unmatched") or not c.get("requirement"):
            raise MizanError(f"rule not understood: {c.get('unmatched') or c.get('refusal')}")
        rule, pinned_hash = c["requirement"], c.get("hash") or rule_hash(c["requirement"])
    pinned_ref = rule if (isinstance(rule, str) and rule.startswith("req_") and not pinned_hash) else None

    def decide(payee: str) -> dict:
        reply = check(payee, rule, timeout=(advise_timeout if mode == "advise" else timeout))
        v = {"subject": payee, "decision": reply.get("decision"), "evidence_rung": reply.get("evidence_rung"),
             "token": reply.get("token"), "check_id": reply.get("check_id"), "explain": reply.get("explain"),
             "proof_request": reply.get("proof_request"), "reply": reply, "token_verified": False}
        try:
            pl = bind_token(reply.get("token") or "", subject=payee, requirement_hash=pinned_hash, keys=keys)
            if pinned_ref:   # a published id without its hash: at least the signed ref must be that rule
                req = pl.get("requirement") if isinstance(pl.get("requirement"), dict) else {}
                if (pl.get("requirement_ref") or f"{req.get('id')}@{req.get('version')}") != pinned_ref:
                    raise MizanError(f"the token is not about {pinned_ref}")
            v["token_verified"] = True
        except MizanError as e:
            v["not_verified_because"] = str(e)
        return v

    def guarded(payee: str, *args, **kw):
        if mode == "advise":
            import threading
            box: dict = {}
            th = threading.Thread(target=lambda: box.update(v=_safe(decide, payee)), daemon=True)
            th.start()
            th.join(advise_timeout)
            v = box.get("v") or {"subject": payee, "decision": "UNVERIFIABLE", "token_verified": False,
                                 "error": f"no answer within {advise_timeout:g}s; paid without waiting"}
        else:
            v = _safe(decide, payee)
        if on_verdict:
            on_verdict(v)
        if mode == "enforce" and not (v["decision"] == "ALLOW" and v["token_verified"]):
            raise MizanRefused(v)
        return pay(payee, *args, **kw)

    return guarded


def _safe(fn: Callable[[str], dict], payee: str) -> dict:
    try:
        return fn(payee)
    except Exception as e:  # network, timeout, malformed reply
        return {"subject": payee, "decision": "UNVERIFIABLE", "error": str(e)[:200], "token_verified": False}


# ---------------------------------------------------------------- payee side: get counted

def claim(name: str) -> dict:
    """Claim an identity: {agent_id, api_key (shown once), listing}. No account, no email."""
    return _req("POST", "/api/agents/claim", {"name": name})


def link_challenge(key: str, endpoint: str) -> dict:
    """Start proving you control an endpoint's origin. Serve reply["nonce"] at https://<host>/.well-known/mizan-challenge."""
    return _req("POST", "/api/link/challenge", {"identifier": endpoint}, key=key)


def link_complete(key: str, challenge_id: str) -> dict:
    """Finish the link once the nonce is served (web origins need no signature)."""
    return _req("POST", "/api/link/complete", {"challenge_id": challenge_id}, key=key)


def enroll(key: str, url: str, *, adapter: str = "openai", model: str | None = None, label: str | None = None) -> dict:
    """Enrol a linked endpoint for counted evaluation. adapter: openai (chat completions), mcp or a2a."""
    body: dict[str, Any] = {"url": url, "adapter": adapter}
    if model:
        body["model"] = model
    if label:
        body["label"] = label
    return _req("POST", "/api/eval/enroll", body, key=key)
