"""Verify a check token offline: Ed25519 against the published key, then expiry. Both token types: mizan.verdict/1 (mzv1.…)
and the previous EdDSA compact JWS.
  python3 verify_token.py <token>          (no argument: fetches a fresh token for try-me first)
Keys: MIZAN_PINNED_KEYS=<path to your copy of mizan-keys.json> (optionally MIZAN_PINNED_KEYS_SHA256=<its sha256>) pins them
and nothing is fetched; without it the keys are fetched from the published URL (which trusts that fetch)."""
import base64, hashlib, json, os, sys, time, urllib.request
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

API = "https://studio.mizan.market"
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(API + u, headers={"User-Agent": "mizan-verify/1"})))
b64u = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
token = sys.argv[1] if len(sys.argv) > 1 else get("/api/check/try-me")["token"]
h, p, s = token.split(".")
if h == "mzv1":   # mizan.verdict/1 token: "mzv1.<claims>.<sig>", Ed25519 over "mzv1.<claims>", key id in the claims
    payload = json.loads(b64u(p)); header = {"kid": payload["kid"]}
    payload.setdefault("evidence_rung", payload.get("grade")); payload.setdefault("check_id", payload.get("jti"))
else:              # the previous compact JWS
    header, payload = json.loads(b64u(h)), json.loads(b64u(p))
pin = os.environ.get("MIZAN_PINNED_KEYS")
if pin:
    raw = open(pin, "rb").read()
    want = os.environ.get("MIZAN_PINNED_KEYS_SHA256", "").strip().lower()
    assert not want or hashlib.sha256(raw).hexdigest() == want, "pinned keys file does not match MIZAN_PINNED_KEYS_SHA256"
    keys = json.loads(raw)
else:
    keys = get("/.well-known/mizan-keys.json")   # fetched: pin this file in production (see above)
key = next(k for k in keys["keys"] if k["key_id"] == header["kid"])
Ed25519PublicKey.from_public_bytes(base64.b64decode(key["public_key_b64"])).verify(b64u(s), f"{h}.{p}".encode())  # raises if forged
assert payload["exp"] > time.time(), "expired"
about = payload.get("subject_requested") or payload.get("subject_as_given") or payload.get("sub") or payload.get("subject")
rule = f" · rule {payload['requirement_hash'][:12]}…" if payload.get("requirement_hash") else ""
print(f"signature ✓ key {header['kid']} · {payload['decision']} {payload.get('evidence_rung')} for {about}{rule} · check {payload['check_id']} · expires {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(payload['exp']))}")
print("before paying: the payee must equal sub, subject_as_given or subject_requested; with a rule pinned, requirement_hash must equal it")
