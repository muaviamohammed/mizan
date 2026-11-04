# The signed verdict

> Part of [Counted 1.1](./README.md).

Nothing MIZAN returns asks to be trusted. Every answer is signed with a published key and verifies offline, by anyone, without calling MIZAN.

## Keys

<https://studio.mizan.market/.well-known/mizan-keys.json>

| `use` | Algorithm | Signs |
|---|---|---|
| `response-signature` | Ed25519 (raw 32-byte public key, base64) | Every JSON reply, check tokens, code-gate messages, attestations, price messages, ledger heads. |
| `eip712-receipt` | secp256k1 (EIP-712, domain `{name: "MIZAN", version: "1"}`) | On-chain receipts verified with one `ecrecover`. |

Pin the key file (or the `key_id` you accept) in production. Keys rotate only by a published ceremony: the key file publishes `successor_pubkey_sha256`, and the new key's raw public key must hash to it. A rotated key stays listed with `retired_utc`. Policy: <https://mizan.market/standard/continuity/>.

## 1. The check token

`token` on every check reply: a compact JWS, `header.payload.signature`, base64url.

- Header: `{"alg": "EdDSA", "kid": "<key_id>", "typ": "JWT"}`.
- Payload fields include `iss`, `sub`, `subject_as_given`, `decision`, `evidence_rung`, `basis`, `reasons`, `amount`, `currency`, `check_id`, `standing`, `log_size`, `iat`, `exp` (24 hours).
- `subject_requested`: present when the subject you sent was an alias that MIZAN resolved (for example `try-me`); it is the string exactly as you sent it.
- A check against a rule (requirement check) carries `subject_as_given`, `requirement` (`id`, `version`, `hash`, …) and, flat, `requirement_ref` (`"req_…@v"`, or `"inline"`) and `requirement_hash`. A check at the default bar carries no requirement fields.

Verify offline:

1. Split the token; base64url-decode header and payload.
2. Require `alg == "EdDSA"`; find the Ed25519 key whose `key_id == kid`.
3. Verify the signature over the ASCII bytes `header.payload` (the two base64url segments joined by `.`).
4. Require `exp > now`, `decision == "ALLOW"`, and that the token is about the party you are about to pay: `sub`, `subject_as_given` or `subject_requested` equals that payee. A token about anyone else is never an ALLOW for this payment.
   If you pinned a rule, also require `requirement_hash` equal to your pinned hash: an ALLOW at the default bar, or against another rule, does not satisfy it.
5. Keep the token with the payment record. Optional online check: `POST /api/check/verify {"token"}` also returns `still_allow` now.

Reference: [`verify/verify_token.py`](../verify/verify_token.py), `verify_token()` / `bind_token()` in [`packages/python`](../packages/python/), `verifyToken()` / `bindToken()` in [`packages/typescript`](../packages/typescript/); each package's `guard()` applies steps 1 to 4.

## 2. Signed messages: code gate, attestation, price

Three compact messages share one format: `{message, signature}` where `signature` is Ed25519 (base64url, no padding) over the **canonical JSON** of `message`: keys sorted, separators `,` and `:`, non-ASCII escaped (Python `json.dumps(m, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`). The reply also carries the exact `canonical` string. The signing key is named by `message.key_id`.

| Message | Where | Fields |
|---|---|---|
| Code-gate message (`contract_message`) | A check against a published bar | `rule_id, rule_hash, subject, decision, issued_at, expires_at, key_id` |
| Attestation (`attestation`) | An ALLOW against a published bar | `requirement, requirement_hash, subject, met, grade, check_id, issued, expires, key_id` + `sig`, `attestation_hash` |
| Price message (`pricing_message`) | Every check | `subject, score_0_100, tier, function_hash, version, requirement, issued_at, expires_at, key_id` |

Verify offline: recompute the canonical bytes, verify Ed25519 with the named key, then require `expires_at > now` (attestation: `expires`), the `subject` you mean, the `rule_id` and `rule_hash` you pinned, and the decision or tier your rule needs. Reference: `verify_message()` / `verifyMessage()` in the packages.

## 3. Signed replies

Every JSON reply carries `provenance.signature = {key_id, alg, sig_b64, canonical_sha256, public_key}`.

- Signed bytes: the canonical JSON of the whole body with `provenance.signature` removed: keys sorted, separators `,` and `:`, non-ASCII **not** escaped, UTF-8, numbers written exactly as served (`150.0` stays `150.0`). The signature is over these bytes; `canonical_sha256` is their hash, for reference.
- In JavaScript parse with a number-preserving parser ([`verify/mizan-canon.mjs`](../verify/mizan-canon.mjs)): `JSON.parse` rewrites `150.0` as `150`, which changes the bytes.

Reference: `verify_reply()` in [`packages/python`](../packages/python/), `verifySignedBody()` in [`verify/mizan-verify.mjs`](../verify/mizan-verify.mjs).

## 4. Ledger entries

Every verdict-bearing event is a leaf on the public ledger, which folds to a signed head stamped hourly by two outside timestamp authorities. See [`ledger.md`](./ledger.md).
