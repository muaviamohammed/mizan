# Security

## Reporting a vulnerability

Email **muavia@mizan.market** with the subject line `SECURITY`. Please do not open a public issue for a suspected vulnerability.

Include what you found, how to reproduce it, and what an attacker could do with it. We aim to acknowledge reports promptly and keep you informed until the issue is resolved. We credit reporters who wish to be named.

## In scope

- Anything that makes a check return ALLOW when it should not, or a signature or ledger proof verify when it should not.
- Forged, replayed or mis-bound signed answers, tokens or receipts.
- Inconsistencies between the published ledger head, its inclusion proofs, consistency proofs and outside timestamps.
- A credential bundle that the published verifier accepts but should refuse.
- Flaws in the code in this repository (SDKs, integrations, examples, verification libraries).

## Out of scope

- Volume-based denial of service against the public API.
- Reports that only restate the published honest boundary (for example, that the count on a past record is a floor).

## Key compromise

MIZAN's signing keys rotate only by the published ceremony (<https://mizan.market/standard/continuity/>). A compromised key is revoked by a signed statement from the pre-committed successor key plus a ledger leaf. Always verify against <https://studio.mizan.market/.well-known/mizan-keys.json>.
