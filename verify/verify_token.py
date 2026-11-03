"""Verify a check token offline: Ed25519 (EdDSA compact JWS) against the published key, then expiry.
  python3 verify_token.py <token>          (no argument: fetches a fresh token for try-me first)"""
import base64, json, sys, time, urllib.request
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

API = "https://studio.mizan.market"
get = lambda u: json.load(urllib.request.urlopen(urllib.request.Request(API + u, headers={"User-Agent": "mizan-verify/1"})))
b64u = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
token = sys.argv[1] if len(sys.argv) > 1 else get("/api/check/try-me")["token"]
h, p, s = token.split(".")
header, payload = json.loads(b64u(h)), json.loads(b64u(p))
key = next(k for k in get("/.well-known/mizan-keys.json")["keys"] if k["key_id"] == header["kid"])  # pin this file in production
Ed25519PublicKey.from_public_bytes(base64.b64decode(key["public_key_b64"])).verify(b64u(s), f"{h}.{p}".encode())  # raises if forged
assert payload["exp"] > time.time(), "expired"
print(f"signature ✓ key {header['kid']} · {payload['decision']} {payload['evidence_rung']} for {payload['sub']} · check {payload['check_id']} · expires {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(payload['exp']))}")
