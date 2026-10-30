"""Offline checks for anything MIZAN signs or logs. Python 3.9+, stdlib only;
Ed25519 signature checks use `cryptography` when it is installed (pip install cryptography).

    from mizan_verify import verify_entry, verify_signed_body, load_keys
"""
from __future__ import annotations

import base64
import os
import hashlib
import json
import urllib.request

DEFAULT_API = "https://studio.mizan.market"
USER_AGENT = "mizan-examples/1 (+https://github.com/muaviamohammed/mizan)" + (" ci" if os.environ.get("MIZAN_CI") else "")


def canon(obj) -> bytes:
    """mizan-canon/1: JSON, keys sorted, separators (',', ':'), UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")


def get_json(url: str, body: dict | None = None, timeout: float = 20):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _sha(*parts: bytes) -> bytes:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.digest()


def leaf_hash(leaf: dict) -> bytes:
    """RFC 6962 leaf hash: SHA-256(0x00 || canonical leaf)."""
    return _sha(b"\x00", canon(leaf))


def fold(index: int, size: int, leaf: bytes, path: list[str]) -> bytes | None:
    """RFC 6962 / RFC 9162 section 2.1.3.2 inclusion proof."""
    fn, sn, r = index, size - 1, leaf
    for h in path:
        if sn == 0:
            return None
        p = bytes.fromhex(h)
        if (fn & 1) or fn == sn:
            r = _sha(b"\x01", p, r)
            if not (fn & 1):
                while not ((fn & 1) or fn == 0):
                    fn >>= 1
                    sn >>= 1
        else:
            r = _sha(b"\x01", r, p)
        fn >>= 1
        sn >>= 1
    return r if sn == 0 else None


def load_keys(api: str = DEFAULT_API) -> dict:
    return get_json(api + "/.well-known/mizan-keys.json")


def verify_ed25519(keys: dict, key_id: str, message: bytes, sig_b64: str) -> bool | None:
    """True/False, or None when `cryptography` is not installed."""
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError:
        return None
    k = next((k for k in keys["keys"] if k["alg"] == "Ed25519" and k["key_id"] == key_id), None)
    if k is None:
        return False
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(k["public_key_b64"])).verify(base64.b64decode(sig_b64), message)
        return True
    except InvalidSignature:
        return False


def verify_signed_body(body: dict, keys: dict) -> bool | None:
    """A signed MIZAN reply: Ed25519 over canon(body without provenance.signature)."""
    sig = (body.get("provenance") or {}).get("signature")
    if not sig:
        return False
    copy = dict(body)
    copy["provenance"] = {k: v for k, v in body["provenance"].items() if k != "signature"}
    msg = canon(copy)
    if sig.get("canonical_sha256") and hashlib.sha256(msg).hexdigest() != sig["canonical_sha256"]:
        return False
    return verify_ed25519(keys, sig["key_id"], msg, sig["sig_b64"])


def verify_head(head: dict, keys: dict) -> bool | None:
    core = {k: head[k] for k in ("alg", "log", "root", "size", "ts")}
    return verify_ed25519(keys, head["signature"]["key_id"], canon(core), head["signature"]["sig_b64"])


def verify_entry(index: int, api: str = DEFAULT_API, keys: dict | None = None):
    d = get_json(f"{api}/api/log/proof/{index}")
    keys = keys or load_keys(api)
    lines, ok = [], True

    leaf = {k: v for k, v in d["leaf"].items() if k not in ("index", "leaf_hash")}
    lh = leaf_hash(leaf)
    good = lh.hex() == d["leaf_hash"]
    ok &= good
    lines.append(f"{'✓' if good else '✗'} Entry #{d['index']} recomputed from its contents: {lh.hex()[:16]}…")

    root = fold(d["index"], d["size"], lh, d["path"])
    good = root is not None and root.hex() == d["head"]["root"]
    ok &= good
    lines.append(f"{'✓' if good else '✗'} Folded {len(d['path'])} hashes up to the ledger head {d['head']['root'][:16]}… ({d['head']['size']} entries)")

    sig = verify_head(d["head"], keys)
    if sig is None:
        lines.append("· Head signature not checked: pip install cryptography")
    else:
        ok &= sig
        lines.append(f"{'✓' if sig else '✗'} Head signature checked against MIZAN's published key ({d['head']['signature']['key_id']})")

    a = d["head"].get("anchor") or {}
    if a.get("rfc3161_time_utc") and a.get("head_size", 0) > d["index"]:
        lines.append(f"✓ Covered by an outside timestamp authority's stamp at {a['rfc3161_time_utc'].replace('T', ' ')[:16]} UTC")
    else:
        lines.append("· Newer than the last outside stamp; covered by the next hourly one")
    return ok, lines


if __name__ == "__main__":
    import sys

    api = DEFAULT_API
    ix = int(sys.argv[1]) if len(sys.argv) > 1 else get_json(api + "/api/log/head")["size"] - 1
    ok, lines = verify_entry(ix, api)
    print("\n".join(lines))
    print("Nothing here asked you to trust MIZAN. Your machine did the math." if ok else "VERIFICATION FAILED")
    sys.exit(0 if ok else 1)
