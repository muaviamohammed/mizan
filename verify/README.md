# Verify without trusting MIZAN

Everything MIZAN signs or logs re-checks on your machine with public data only.

| What | Command | Needs |
|---|---|---|
| A check token (the signed verdict) | `python3 verify_token.py [token]` | Python 3.9+, `cryptography` |
| A ledger entry, end to end | `python3 verify_entry.py [index]` · `node verify-entry.mjs [index]` | Python 3.9+ (+ `cryptography` for the head signature) · Node 20+ |
| Any signed JSON reply | `verify_reply()` in [`packages/python`](../packages/python/) · `verifySignedBody()` in [`mizan-verify.mjs`](./mizan-verify.mjs) | as above |
| A zero-knowledge credential | the published verifier binary (below) | macOS, Linux or Windows |

## A token

```bash
python3 verify_token.py
# signature ✓ key 2266fb49… · ALLOW PROVEN for … · check … · expires …
```

Steps: base64url-decode the header and payload; take the Ed25519 key whose `key_id` equals the header's `kid` from <https://studio.mizan.market/.well-known/mizan-keys.json>; verify the signature over `header.payload`; require `exp > now`. Detail: [`specs/signed-verdict.md`](../specs/signed-verdict.md).

## A ledger entry

```bash
python3 verify_entry.py 388
# ✓ Entry #388 recomputed from its contents
# ✓ Folded 11 hashes up to the ledger head
# ✓ Head signature checked against MIZAN's published key
# ✓ Covered by an outside timestamp authority's stamp
```

Leaf = SHA-256(0x00 ‖ canonical entry); node = SHA-256(0x01 ‖ left ‖ right) (RFC 6962); the head is signed with Ed25519 and stamped hourly by two outside RFC 3161 timestamp authorities and OpenTimestamps. Detail: [`specs/ledger.md`](../specs/ledger.md). Or in the browser: <https://mizan.market/log/> (click any row).

Three calls, no trust in MIZAN at any step:

```bash
curl -s https://studio.mizan.market/api/log/head                         # signed head
curl -s https://studio.mizan.market/api/log/proof/388                    # inclusion path for one entry
curl -s "https://studio.mizan.market/api/log/consistency?old=100&new=600" # the log only grew
```

## A zero-knowledge credential

The verifier binaries are published with their SHA-256 sums; nothing is committed here.

```bash
curl -s https://studio.mizan.market/api/verifier/linux     # or macos, windows: url, sha256, command
curl -sO https://mizan.market/verify/files/SHA256SUMS.txt  # check the binary's sha256 against this list
```

Run it on a credential bundle with the market file it was proven on: exit 0 = verified, exit 1 = refused (any single flipped bit is refused). Page: <https://mizan.market/verify/>.
