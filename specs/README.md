# MIZAN specifications

Everything in this folder is published under **CC BY 4.0** (see [`LICENSE-SPEC`](../LICENSE-SPEC)). Anyone may implement it, including competitors of its steward. The live API and the published standard at <https://mizan.market/standard/> are the reference; where a document here and the published text differ, the published text governs.

| Document | What it fixes |
|---|---|
| [`counted-claim.md`](./counted-claim.md) | The six-part counted claim: result, measure, count, evidence, requirement, verdict. The object every check answers. |
| [`evidence-ladder.md`](./evidence-ladder.md) | The three grades of evidence (DECLARED, RECORDED, PROVEN), the `basis` of every answer, and what ALLOW and REFUSE mean. |
| [`requirement-language.md`](./requirement-language.md) | How a buyer's plain words become a versioned rule: compile, read back, hash, publish, check. |
| [`ledger.md`](./ledger.md) | The public ledger: canonical JSON, RFC 6962 leaves and inclusion proofs, the signed head, outside timestamps, operative time. |
| [`signatures.md`](./signatures.md) | What MIZAN signs, with which published key, over which bytes; receipts; key rotation. |
| [`vtr-1/`](./vtr-1/) | VTR-1, the Verifiable Track Record Standard (frozen 2026-08-01), and its 41 requirement clauses. |

Conformance tests for the cryptographic parts are the runnable examples: [`examples/verify-ledger-entry`](../examples/verify-ledger-entry/) and [`verify/`](../verify/) recompute every hash and signature from public data, and CI runs them against the live ledger.
