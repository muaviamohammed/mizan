# Disputes

A verdict can be contested on the record. The dispute, the outcome and the correction are written to the same public ledger as the verdict, signed, and never deleted. That is what lets a verdict sit in a money path.

Live page: <https://mizan.market/disputes/> · machine rules: `GET https://studio.mizan.market/api/disputes/policy`.

## What a dispute is

A dispute says: this verdict is wrong for one named reason. It is filed against one verdict (a check id or a credential id) and carries only hashes or links as evidence. It is not a review of a subject and not a complaint about a bar: MIZAN corrects what MIZAN said.

## Who, when

- **Subject**: the holder of the credential or the controller of the identity the verdict is about.
- **Requirer**: the party that ran the check or published the bar it answered.
- One open dispute per verdict; 30 days from the time the verdict was logged. A pending dispute never changes a decision.

## Grounds

| Ground | Meaning |
|---|---|
| `wrong_measure` | The check read a measure other than the one the published rule names. |
| `stale_record` | The record has moved since the verdict and the verdict no longer describes it. |
| `data_error` | A wrong bar, gap or bad tick in a canonical file; a wrong dataset hash. |
| `identity_mismatch` | The check resolved to the wrong credential, or a link was attributed to the wrong owner. |
| `other` | A specific, reproducible error, with the evidence to show it. |

## Resolution

1. **By rule first.** The same check is re-run against the record as it stands. If the decision differs from the one on the ledger, the dispute resolves automatically: `overturned`, effect `re-issue`. A corrective verdict is appended and the original is annotated.
2. **By MIZAN otherwise.** If the re-run returns the same decision, MIZAN decides within 30 days. The decision is signed and carries the hash of its written reasoning.

Outcomes: `upheld`, `overturned`, `withdrawn`. Effects: `none`, `re-issue`, `annotate`.

## On the ledger

Two entry kinds under the same signed head as every verdict:

- `dispute_opened`: the verdict reference, the grounds, a hash of the evidence. Never the filer.
- `dispute_resolved`: the outcome, the effect, who decided, the reasoning hash, the index of the entry it annotates, the corrective check id.

No verdict, check, credential or ledger entry is edited, deleted or backdated. Evidence is accepted only as a hash or a link; a link that looks like it carries a personal identifier is refused.

## Calls

| Call | Use |
|---|---|
| `POST /api/disputes {check_id, party, grounds, evidence}` | File (API key of the subject or the requirer). Returns the dispute id, the opening ledger entry and a private token that withdraws it. |
| `GET /api/disputes/{id}` | Status, outcome and ledger proofs. |
| `GET /api/disputes/for/{subject}` | Disputes and counts for a subject. |
| `POST /api/disputes/{id}/withdraw` | Withdraw (filer only). |
| `GET /api/disputes/policy` | The rules in machine form. |

Every ALLOW and REFUSE carries `disputes {open, upheld, overturned}` for the subject; a REFUSE names the dispute route in `dispute`. When the counts cannot be read, the reply says so: unknown is never zero.
