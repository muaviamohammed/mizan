# Signatures and keys

Nothing MIZAN returns asks to be trusted. Every answer is signed with a published key and re-checks offline.

## The key file

<https://studio.mizan.market/.well-known/mizan-keys.json> (also served at `https://mizan.market/.well-known/mizan-keys.json`).

| `use` | Algorithm | Signs |
|---|---|---|
| `response-signature` | Ed25519 (raw 32-byte public key, base64) | Every JSON reply from the REST API, A2A, x402 and MCP tool results; ledger heads; compact tokens. |
| `eip712-receipt` | secp256k1 (EIP-712, domain `{name: "MIZAN", version: "1"}`) | On-chain receipts: `Receipt(address subject, bytes32 credential, uint64 issuedAt, uint64 expiresAt)`, verified with one `ecrecover` by [`MizanProof.sol`](../integrations/erc8004/MizanProof.sol). |

## Signed replies

Every JSON reply carries `provenance.signature = {key_id, alg, sig_b64, canonical_sha256, public_key}`.

- **Signed bytes:** the canonical JSON of the whole body with `provenance.signature` removed: keys sorted, separators `,` and `:`, `ensure_ascii=False`, UTF-8. The signature is over these bytes, not over their hash; `canonical_sha256` is published for reference.
- **Python:** `Ed25519PublicKey.from_public_bytes(b64decode(public_key_b64)).verify(b64decode(sig_b64), canonical)`.
- **JavaScript:** parse the body with a number-preserving parser (see [`verify/js/mizan-canon.mjs`](../verify/js/mizan-canon.mjs)). `JSON.parse` rewrites `150.0` as `150`, which changes the bytes.

## Tokens

`token` on a check is a compact EdDSA token (`header.payload.signature`, base64url) signed with the response key, valid 24 hours. Anyone verifies it offline with the published key, or online with `POST /api/check/verify {"token": "…"}`. Receipts for a credential: `GET /api/receipt/{credential_id}`; verify with `POST /api/receipt/verify` or offline. Revocations: `GET /api/crl` (signed).

## Rotation

Keys rotate only by a published ceremony, never silently. The key file publishes `successor_pubkey_sha256`: at rotation, the new key's raw 32-byte public key must hash to that value, and a fresh successor hash is published at the same time. A rotated key stays listed with a `retired_utc`. A compromised key is revoked by a signed statement from the successor key plus a ledger leaf. Policy: <https://mizan.market/standard/continuity/>.
