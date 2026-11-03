# The public ledger

MIZAN's ledger (`mizan-verdict-log-v1`) is an append-only Merkle log. Every verdict, registration, probe, requirement and hourly check count is a leaf. Heads are signed; checkpoints are stamped hourly by two outside RFC 3161 timestamp authorities and by OpenTimestamps (Bitcoin). Anyone can verify any entry with public data only.

## Algorithms

| | |
|---|---|
| Hash | SHA-256 |
| Merkle tree | RFC 6962: leaf = `SHA-256(0x00 ‖ canon(leaf))`, node = `SHA-256(0x01 ‖ left ‖ right)` |
| Canonical JSON (`mizan-canon/1`) | keys sorted, separators `,` and `:`, UTF-8, non-ASCII **not** escaped, numbers written as the reference (Python `json.dumps`) writes them, so `150.0` stays `150.0` |
| Head signature | Ed25519 over `canon({alg, log, root, size, ts})` with the published key |
| Outside time | RFC 3161 tokens from two independent authorities + an OpenTimestamps proof on each checkpoint |

These values are also returned live in `GET https://studio.mizan.market/api/log/head` under `algorithms`.

## Endpoints

| Call | Returns |
|---|---|
| `GET /api/log/head` | The signed head: `size`, `root`, `ts`, `alg`, `log`, `signature`, the latest `anchor`, counts by kind and the clock. |
| `GET /api/log/latest?n=N` | The newest entries. |
| `GET /api/log/entries?start=&end=&limit=` | Entries by range. |
| `GET /api/log/proof/{index}` | One entry, its `leaf_hash`, the audit `path` and the head it folds to. |
| `GET /api/log/proof-for/{subject}` | The inclusion proof for a credential's entry. |
| `GET /api/log/consistency?old=&new=` | A consistency proof between two tree sizes. |
| `GET /api/log/anchors` | Every stamped checkpoint. |
| `GET /api/log/anchor/{size}/head-{size}.json` | The stamped file, byte for byte; beside it `.tsr`, `.tsr2` (RFC 3161) and `.ots` (OpenTimestamps). |

Base URL: `https://studio.mizan.market`. CORS is open, so a browser can verify directly.

## Verifying an entry

1. Fetch `/api/log/proof/{i}`. Remove `index` and `leaf_hash` from `leaf`; compute `SHA-256(0x00 ‖ canon(leaf))`; it must equal `leaf_hash`.
2. Fold `path` from the leaf hash to the root with the RFC 9162 §2.1.3.2 inclusion algorithm (`fn = i`, `sn = size − 1`; at each step hash `0x01 ‖ p ‖ r` when `fn` is odd or `fn = sn`, otherwise `0x01 ‖ r ‖ p`, shifting right as specified). It must end with `sn = 0` and equal `head.root`.
3. Verify `head.signature.sig_b64` (Ed25519) over `canon({alg, log, root, size, ts})` with the key named by `head.signature.key_id` in <https://studio.mizan.market/.well-known/mizan-keys.json>.
4. **Stamp coverage rule:** the entry is covered by an outside stamp when `head.anchor.rfc3161_time_utc` is set and `head.anchor.head_size > i`. Otherwise it is newer than the last checkpoint and is covered by the next hourly one.

Reference implementations: [`verify/mizan-verify.mjs`](../verify/mizan-verify.mjs) and [`verify/verify_entry.py`](../verify/verify_entry.py). In the browser: <https://mizan.market/log/> (click any row).

## Operative time

The operative time of a leaf at index *i* is the stamp of the **first covering checkpoint**: the first anchored head whose size exceeds *i*. Where that checkpoint carries two RFC 3161 tokens, its time is the **later** of the two, so one dishonest authority cannot move it earlier; with one token, that token's time. Its stronger time is the Bitcoin block that confirms the checkpoint's OpenTimestamps proof. A leaf's own `ts` is never its operative time. A leaf above the latest checkpoint has no operative time yet.

Checking a stamped checkpoint yourself:

```bash
openssl ts -verify -data head-<size>.json -in head-<size>.json.tsr  -CAfile <freetsa cacert> -untrusted <freetsa tsa.crt>
openssl ts -verify -data head-<size>.json -in head-<size>.json.tsr2 -CAfile <DigiCert Trusted Root G4>
ots verify head-<size>.json.ots
```

Use OpenSSL 3 or later; LibreSSL 3.3 (macOS default) does not build DigiCert's chain.

## Hourly check counts

Each hour a `check_interval` leaf commits how many checks were served in `[interval_start, interval_end)` UTC, with `root` = the RFC 6962 Merkle root over that hour's check ids sorted ascending, leaf = `SHA-256(0x00 ‖ "mizan-check-id-v1|" ‖ check_id)`. No checker identity, subject or decision is committed.
