# Verify offline

Don't take MIZAN's word for anything. Three things can be checked on your own machine, with public data only.

| What | How | Needs |
|---|---|---|
| **A signed answer** (any REST, A2A, x402 or MCP reply) | Ed25519 over the canonical body, against the published key | [`js/mizan-verify.mjs`](./js/mizan-verify.mjs) · [`python/mizan_verify.py`](./python/mizan_verify.py) |
| **A ledger entry** | Recompute the leaf, fold the RFC 6962 path to the signed head, check the head signature, apply the stamp coverage rule | same files, or the browser page in [`examples/verify-ledger-entry`](../examples/verify-ledger-entry/) |
| **A credential** (a zero-knowledge proof) | Run the published verifier binary on the bundle and the public data it is bound to | the binaries below |

## 1 · Signed answers and ledger entries

```bash
node examples/verify-ledger-entry/verify.mjs 388        # Node 20+, no dependencies
python3 verify/python/mizan_verify.py 388               # stdlib; pip install cryptography for the signature step
```

```js
import { fetchRaw, loadKeys, verifySignedBody } from "./verify/js/mizan-verify.mjs";
const answer = await fetchRaw("https://studio.mizan.market/api/check/mizan-flagship");
verifySignedBody(answer, await loadKeys());   // { ok: true, key_id: "…" }
```

Key file: <https://studio.mizan.market/.well-known/mizan-keys.json>. Byte rules: [`specs/signatures.md`](../specs/signatures.md) and [`specs/ledger.md`](../specs/ledger.md).

> **JavaScript note.** The reference canonical form is Python's `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`. `JSON.parse` turns `150.0` into `150`, which changes the bytes, so [`js/mizan-canon.mjs`](./js/mizan-canon.mjs) parses numbers as their exact source text. With it, every entry on the ledger verifies (CI checks a sample on every run).

## 2 · Credentials

The verifier is published as binaries with SHA-256 sums at <https://mizan.market/verify/>. The prover is private; the verifier is built separately from it.

| Platform | File (current era v12) |
|---|---|
| macOS (Apple Silicon) | [`mizan-verifier-v12-macos-arm64`](https://mizan.market/verify/files/mizan-verifier-v12-macos-arm64) |
| Linux (x86-64) | [`mizan-verifier-v12-linux-x86_64`](https://mizan.market/verify/files/mizan-verifier-v12-linux-x86_64) |
| Windows (x86-64) | [`mizan-verifier-v12-windows-x86_64.exe`](https://mizan.market/verify/files/mizan-verifier-v12-windows-x86_64.exe) |
| Checksums (every era) | [`SHA256SUMS.txt`](https://mizan.market/verify/files/SHA256SUMS.txt) |

```bash
B=https://mizan.market/verify/files
curl -fO $B/mizan-verifier-v12-macos-arm64 -fO $B/SHA256SUMS.txt -fO $B/v12_btc_trend_4h.bundle -fO $B/btc_4h.csv
grep v12-macos-arm64 SHA256SUMS.txt | shasum -a 256 -c      # → OK
chmod +x mizan-verifier-v12-macos-arm64
./mizan-verifier-v12-macos-arm64 v12_btc_trend_4h.bundle btc_4h.csv
echo $?                                                      # 0 = verified · 1 = refused (any flipped bit is refused)
```

Every registry row carries its own `verify_command` (`GET https://studio.mizan.market/api/registry`). A credential verifies under the era that minted it; older-era binaries are listed in `SHA256SUMS.txt`, and the era history is at <https://mizan.market/engine/eras/>. How an independent verifier implementation qualifies: `GET https://studio.mizan.market/api/conformance`.

## 3 · Outside time

Ledger checkpoints are stamped hourly by two RFC 3161 authorities and by OpenTimestamps. The `openssl ts -verify` and `ots verify` commands are in [`specs/ledger.md`](../specs/ledger.md#operative-time).
