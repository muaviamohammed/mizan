"""Verify a stapled MIZAN proof locally: zero calls to MIZAN at decision time.

    from mizan.receipt import verify_receipt
    r = verify_receipt(receipt, identity=pay_to)     # r["allow"] is True only for a PASS bound to pay_to

ALLOW only if: Ed25519 signature verifies against a pinned MIZAN key, not expired, verdict PASS, status good, and
the identity you are paying is in `bind`. Needs the `cryptography` package for fully offline verification; without
it, one call to MIZAN verifies the signature (signature and binding rules unchanged). A decision about a
credential, never advice.
"""
import base64, json, time, urllib.request

KEYS = {"2266fb495f83b0a0": "DldoufXTa30rmfQINo1q6yAAF68Wk2qfG1A7c3OJ8yw="}   # mizan.market/.well-known/mizan-keys.json
STUDIO = "https://studio.mizan.market"
_CRL = {"at": 0, "body": None}


def _b64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _norm(s) -> str:
    s = str(s or "").strip()
    return s.lower() if s.lower().startswith("0x") else s


def _revoked(sub: str):
    if _CRL["body"] is None or time.time() - _CRL["at"] > 3600:
        try:
            with urllib.request.urlopen(urllib.request.Request(STUDIO + "/api/crl", headers={"User-Agent": "mizan-receipt/1"}), timeout=10) as r:
                _CRL["body"] = json.loads(r.read()); _CRL["at"] = time.time()
        except Exception:
            return None
    return any(x.get("credential") == sub for x in (_CRL["body"] or {}).get("revoked", []))


def verify_receipt(token: str, identity: str = "", keys: dict | None = None, check_revocation: bool = False, now: float | None = None) -> dict:
    keys = keys or KEYS
    def no(reason, payload=None):
        return {"allow": False, "reason": reason, "payload": payload}
    try:
        h, p, s = str(token or "").strip().split(".")
        header = json.loads(_b64u(h)); payload = json.loads(_b64u(p)); sig = _b64u(s)
    except Exception:
        return no("malformed receipt")
    pub = keys.get(header.get("kid"))
    if not pub:
        return no(f"unknown key id {header.get('kid')} (refresh keys from mizan-keys.json)", payload)
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        try:
            Ed25519PublicKey.from_public_bytes(base64.b64decode(pub)).verify(sig, f"{h}.{p}".encode())
        except Exception:
            return no("signature does not verify", payload)
        how = "verified locally"
    except ImportError:
        try:
            req = urllib.request.Request(STUDIO + "/api/receipt/verify", data=json.dumps({"receipt": token}).encode(), method="POST",
                                         headers={"Content-Type": "application/json", "User-Agent": "mizan-receipt/1"})
            with urllib.request.urlopen(req, timeout=15) as r:
                v = json.loads(r.read())
        except Exception as e:
            return no(f"cannot verify: install `cryptography` for offline checks ({str(e)[:60]})", payload)
        if not v.get("valid"):
            return no(v.get("reason") or "signature does not verify", payload)
        how = "verified by one call (install `cryptography` for zero calls)"
    if not payload.get("exp", 0) > (now or time.time()):
        return no("expired", payload)
    if payload.get("verdict") != "PASS" or payload.get("status") != "good":
        return no("not a PASS in good standing", payload)
    if not identity:
        return no("no identity given: pass the wallet, host or agent id you are paying", payload)
    if _norm(identity) not in [_norm(b) for b in payload.get("bind") or []]:
        return no(f"receipt is not bound to {identity}: never an ALLOW for someone else", payload)
    if check_revocation and _revoked(payload.get("sub", "")):
        return no("credential revoked", payload)
    return {"allow": True, "reason": f"proven · {how} · bound to {identity}", "credential": payload.get("sub"), "expires": payload.get("exp"), "payload": payload}
