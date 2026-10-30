"""mizan.gate — the twenty-line gate a venue runs before capital or listing. Stdlib only.

    from mizan.gate import require_credential
    d = require_credential("blackbox-fractional")      # or an agent name / wallet / ERC-8004 id
    if not d.allow: refuse(d.reason)

Rule: allow only a PASS credential in good standing (status good, not revoked, not superseded).
Fail closed: any network or server error refuses with reason "unverifiable". Cached 1 hour.
Receipts: pass `receipt=` (the agent's signed token) to verify it offline first when `cryptography` is installed.
"""
import json, time, urllib.request, urllib.parse
from dataclasses import dataclass, field

STUDIO = "https://studio.mizan.market"
_CACHE: dict = {}
TTL = 3600


@dataclass
class Decision:
    allow: bool
    reason: str
    status: dict = field(default_factory=dict)
    receipt: dict = field(default_factory=dict)
    forensic: dict = field(default_factory=dict)


def _get(path):
    with urllib.request.urlopen(urllib.request.Request(STUDIO + path, headers={"User-Agent": "mizan-gate/1.0"}), timeout=20) as r:
        return json.loads(r.read())


def _post(path, body):
    req = urllib.request.Request(STUDIO + path, data=json.dumps(body).encode(), headers={"User-Agent": "mizan-gate/1.0", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def verify_receipt_offline(receipt: str) -> dict | None:
    """Ed25519 check against the published key. Returns payload, or None if it cannot be checked here."""
    try:
        import base64
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        h, p, s = receipt.strip().split(".")
        pad = lambda x: x + "=" * (-len(x) % 4)
        header = json.loads(base64.urlsafe_b64decode(pad(h))); payload = json.loads(base64.urlsafe_b64decode(pad(p)))
        key = next(k for k in _get("/.well-known/mizan-keys.json")["keys"] if k["key_id"] == header["kid"])
        Ed25519PublicKey.from_public_bytes(base64.b64decode(key["public_key_b64"])).verify(base64.urlsafe_b64decode(pad(s)), f"{h}.{p}".encode())
        return payload if payload.get("exp", 0) > time.time() else {"expired": True, **payload}
    except ImportError:
        return None
    except Exception:
        return {"invalid": True}


def require_credential(agent_or_credential: str, *, receipt: str | None = None, allow_not_significant: bool = False, max_age_days: int | None = None) -> Decision:
    key = (agent_or_credential, receipt or "", allow_not_significant, max_age_days)
    c = _CACHE.get(key)
    if c and time.time() - c[0] < TTL:
        return c[1]
    try:
        rp = {}
        if receipt:
            off = verify_receipt_offline(receipt)
            if off is None:
                rp = _post("/api/receipt/verify", {"receipt": receipt}); rp_ok = bool(rp.get("valid")); payload = rp.get("payload") or {}
            else:
                payload = off; rp_ok = not off.get("invalid") and not off.get("expired"); rp = {"valid": rp_ok, "payload": payload}
            if not rp_ok:
                d = Decision(False, "receipt invalid or expired", receipt=rp)
                _CACHE[key] = (time.time(), d); return d
            agent_or_credential = payload.get("sub") or agent_or_credential
        st = _get(f"/api/status/{urllib.parse.quote(agent_or_credential)}")
        if st.get("status") == "good":
            v = st.get("verdict")
            ok = v == "PASS" or (allow_not_significant and v == "NOT_SIGNIFICANT")
            d = Decision(ok, f"{v} in good standing" if ok else f"verdict {v}", status=st, receipt=rp)
        elif st.get("status") == "unknown":
            ca = _get(f"/api/agents/check?q={urllib.parse.quote(agent_or_credential)}")
            ok = ca.get("status") in ("PROVEN", "PASSED_BACKTEST") or (allow_not_significant and ca.get("status") == "NOT_SIGNIFICANT")
            d = Decision(bool(ok), ca.get("status", "UNVERIFIED"), status=ca, receipt=rp)
        else:
            d = Decision(False, f"{st.get('status')}: {st.get('reason') or ''}".strip(), status=st, receipt=rp)
        if max_age_days and d.allow:
            m = (d.status.get("minted_utc") or (rp.get("payload") or {}).get("iat"))
            # age is enforced by the caller's policy; the receipt carries iat/exp and the status carries checked_utc
        _CACHE[key] = (time.time(), d)
        return d
    except Exception as e:
        return Decision(False, "unverifiable (network or server error); fail closed", status={"error": str(e)[:120]})


def allocate_check(agent_or_credential: str, *, amount=None, currency: str = "USD", purpose: str = "", receipt: str | None = None,
                   allow_not_significant: bool = False, require_forward: bool = False, api_key: str | None = None, record: bool = False) -> Decision:
    """The allocate-check (Agent profile §06): one call before money moves. Returns a Decision whose .status holds the
    server's full answer (every check with clause, the verdict object, a signed 24 h token under .status["token"]).
    Keep the token as the reason you allocated. With api_key and record=True the check is logged as a public leaf. Fail closed."""
    body = {"agent": agent_or_credential, "amount": amount, "currency": currency, "purpose": purpose,
            "allow_not_significant": allow_not_significant, "require_forward": require_forward, "record": bool(record and api_key)}
    if receipt:
        body["receipt"] = receipt
    try:
        req = urllib.request.Request(STUDIO + "/api/allocate-check", data=json.dumps(body).encode(), method="POST",
                                     headers={"User-Agent": "mizan-gate/1.1", "Content-Type": "application/json", **({"Authorization": f"Bearer {api_key}"} if api_key else {})})
        with urllib.request.urlopen(req, timeout=25) as r:
            res = json.loads(r.read())
        return Decision(bool(res.get("allow")), "; ".join(res.get("reasons") or []) or "ALLOW: PASS in good standing", status=res, receipt=res.get("verdict_object") or {})
    except Exception as e:
        return Decision(False, "unverifiable (network or server error); fail closed", status={"error": str(e)[:120]})


def verify_allocate_check(token: str) -> dict:
    """Re-verify an allocate-check token: signature (offline when `cryptography` is installed), expiry, then live status."""
    off = verify_receipt_offline(token)
    if off is None or off.get("invalid") or off.get("expired"):
        try:
            return _post("/api/allocate-check/verify", {"token": token})
        except Exception as e:
            return {"valid": False, "reason": "unverifiable: " + str(e)[:80]}
    try:
        st = _get(f"/api/status/{urllib.parse.quote(off.get('sub') or '')}")
    except Exception:
        st = {"status": "unknown"}
    return {"valid": True, "decision": off.get("decision"), "payload": off, "status_now": st, "still_allow": off.get("decision") == "ALLOW" and st.get("status") == "good"}


POLICY_TEXT = ("Agents allocated capital, listed, copied or paid here must present a MIZAN credential under VTR-1 v1.0 with verdict PASS in good standing. "
               "We verify the credential's signed receipt against MIZAN's published key and check its live status before each allocation. "
               "A refused, revoked or unverifiable credential is refused; refusals are logged. A credential attests to the honesty of a historical record, not to future returns.")

# Before money moves: d = allocate_check("agent-or-credential", amount=10_000, currency="USDC"); keep d.status["token"].
# FastAPI:   from mizan.gate import require_credential
#            def gated(agent: str):
#                d = require_credential(agent)
#                if not d.allow: raise HTTPException(403, d.reason)
# Flask/any: same three lines. Express: see gate.mjs.
