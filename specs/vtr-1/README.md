# VTR-1 · The Verifiable Track Record Standard

**Status:** v1.1, frozen 2026-08-01 (v1.0 remains available). **License:** CC BY 4.0. Free to implement, including by competitors of its steward.

| | |
|---|---|
| Plain-language standard | <https://mizan.market/standard/> |
| Formal specification (11 sections, appendices A to E, R-01 to R-41) | <https://mizan.market/standard-spec/> |
| Errata | <https://mizan.market/errata/> |
| Clauses as data | `GET https://studio.mizan.market/api/standard/clauses` · copy here: [`requirements.md`](./requirements.md) |
| Gate classes as data | `GET https://studio.mizan.market/api/standard/gates` |
| Conformance (how an independent verifier qualifies) | `GET https://studio.mizan.market/api/conformance` |
| Citation | Muavia, Mohammad. *VTR-1: The Verifiable Track Record Standard: Enforcing Backtest Honesty Without Trusting the Issuer or Revealing the Strategy* (August 1, 2026). SSRN: <https://ssrn.com/abstract=7215664> |

## What it fixes

VTR-1 defines what a **PROVEN** record must guarantee, what it assumes, and what it refuses:

- **Committed data.** The data a record is computed on is committed up front (Merkle-bound); a verifier re-derives the root from its own copy and rejects on mismatch.
- **Faithful execution.** The declared computation is executed inside a zero-knowledge proof (a STARK, no trusted setup) on the committed data, with costs applied.
- **Counted trials.** At the higher conformance level the trial ledger is committed before evaluation and the trial count is derived from it, not reported.
- **Zero knowledge.** A verifier learns the verdict and the disclosed metrics only. The method never leaves its owner.
- **Re-verification by anyone, offline.** A published verifier re-checks a credential on macOS, Linux or Windows; see [`verify/`](../../verify/).
- **Refusals published.** A FAIL is published beside a PASS.

VTR-1 was written first for track records, where the cost of a cherry-picked result is easiest to measure. The same evidence ladder and the same six-part counted claim carry every other kind of claim MIZAN checks (model evaluations, forecasts, service reliability, delivery, conduct against a mandate); those are versioned **profiles**, listed live at `GET https://studio.mizan.market/api/profiles`.

## Changing the standard

The frozen text is never edited. Corrections are published as errata; changes ship as a new version. Open an issue with the **Spec change** template to propose one.
