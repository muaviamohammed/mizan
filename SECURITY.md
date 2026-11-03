# Security

## Reporting a vulnerability

Please report security issues privately. Do not open a public issue.

- Contact: the address in <https://mizan.market/.well-known/security.txt>
- Policy: <https://mizan.market/security/>

Include what you found, how to reproduce it, and the `check_id` or ledger index involved if there is one. We acknowledge reports and keep you informed until the issue is resolved.

## In scope

- Anything that makes a forged, altered or expired verdict, token, attestation or price message verify.
- A ledger entry that can be changed, removed or backdated without detection.
- A path by which a check returns ALLOW for a subject whose record does not meet the stated bar.
- Bugs in the clients and verifiers in this repository.

## Keys

Published keys: <https://studio.mizan.market/.well-known/mizan-keys.json>. Keys rotate only by a published ceremony ([`specs/signed-verdict.md`](./specs/signed-verdict.md)); a compromised key is revoked by a signed statement from its successor plus a ledger entry.
