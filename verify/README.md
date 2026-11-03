# Verify without trusting MIZAN

Everything MIZAN signs or logs re-checks on your machine with public data only.

| What | Command | Needs |
|---|---|---|
| A check token (the signed verdict) | `python3 verify_token.py [token]` | Python 3.9+, `cryptography`; optional pinned key file |
| A ledger entry, end to end | `python3 verify_entry.py [index]` · `node verify-entry.mjs [index]` | Python 3.9+ (+ `cryptography` for the head signature) · Node 20+ |
| Any signed JSON reply | `verify_reply()` in [`packages/python`](../packages/python/) · `verifySignedBody()` in [`mizan-verify.mjs`](./mizan-verify.mjs) | as above |
| A zero-knowledge credential | the published verifier binary for its era (below) | macOS, Linux or Windows |

## A token

```bash
python3 verify_token.py
# signature ✓ key 2266fb49… · ALLOW PROVEN for try-me · check … · expires …
```

Steps: base64url-decode the header and payload; take the Ed25519 key whose `key_id` equals the header's `kid` from <https://studio.mizan.market/.well-known/mizan-keys.json>; verify the signature over `header.payload`; require `exp > now`. Detail: [`specs/signed-verdict.md`](../specs/signed-verdict.md).

A valid signature says MIZAN signed this answer. Before paying on it, also check that it is **about the payee you are paying** (`sub`, `subject_as_given` or `subject_requested` equals that payee), that `decision` is `ALLOW`, and, if you pinned a rule, that `requirement_hash` equals your pinned hash. `bind_token()` in [`packages/python`](../packages/python/) and `bindToken()` in [`packages/typescript`](../packages/typescript/) do all of it; their `guard()` refuses otherwise.

### Pin the keys

By default the scripts and packages fetch the key file over HTTPS, which trusts that fetch. To remove that trust, keep your own copy and pin it; nothing is fetched afterwards:

```bash
curl -s https://studio.mizan.market/.well-known/mizan-keys.json -o mizan-keys.json
shasum -a 256 mizan-keys.json          # compare with a value you obtained another way, then keep it
export MIZAN_PINNED_KEYS=$PWD/mizan-keys.json
export MIZAN_PINNED_KEYS_SHA256=<that sha256>     # optional; a mismatch refuses
```

`verify_token.py`, `mizan_check` (Python) and `mizan-check` (TypeScript) read these two variables; the packages also take `keys=` / `{ keys }` directly. Keys rotate only by the ceremony the key file describes (`ceremony`), so a pinned copy changes only when you choose to update it.

## A ledger entry

```bash
python3 verify_entry.py 388
# ✓ Entry #388 recomputed from its contents
# ✓ Folded 11 hashes up to the ledger head
# ✓ Head signature checked against MIZAN's published key
# ✓ Covered by an outside timestamp authority's stamp
```

Leaf = SHA-256(0x00 ‖ canonical entry); node = SHA-256(0x01 ‖ left ‖ right) (RFC 6962); the head is signed with Ed25519, and checkpoints are stamped on an hourly schedule by two outside RFC 3161 timestamp authorities and OpenTimestamps; the latest stamp time is in the signed head (`anchor.stamped_utc` at `/api/log/head`). Detail: [`specs/ledger.md`](../specs/ledger.md). Or in the browser: <https://mizan.market/log/> (click any row).

Three calls, no trust in MIZAN at any step:

```bash
curl -s https://studio.mizan.market/api/log/head                         # signed head
curl -s https://studio.mizan.market/api/log/proof/388                    # inclusion path for one entry
curl -s "https://studio.mizan.market/api/log/consistency?old=100&new=600" # the log only grew
```

## A zero-knowledge credential

The verifier binaries are published at <https://mizan.market/verify/> with their SHA-256 sums in one list: <https://mizan.market/verify/files/SHA256SUMS.txt>. Nothing binary is committed here.

```bash
curl -s https://studio.mizan.market/api/verifier/macos        # or linux, windows: file, url, sha256, command (current era)
curl -sO https://mizan.market/verify/files/SHA256SUMS.txt     # every build, every era
shasum -a 256 <the binary>                                     # must equal its line in SHA256SUMS.txt
```

Run it on a credential bundle with the market file it was proven on: exit 0 = verified, exit 1 = refused. Each credential names its era; use the build of that era (older eras keep their own builds in the list). For example, the sample on the verify page (`mizan_sample_credential.bundle` with `btc_4h.csv`) is from an earlier era: it verifies with `mizan-verifier-macos-arm64` from the list (exit 0), and changing one bit of either file makes it exit 1. The current-era build does not read that older bundle (it exits 2, "cannot parse bundle").
