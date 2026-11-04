# Evidence grades

> Part of [Counted 1.1](./README.md).

Every claim carries exactly one grade. A lower grade is never presented as a higher one, and a claim carries the lowest grade any of its parts supports.

| Grade | Meaning | Can it produce ALLOW? |
|---|---|---|
| **DECLARED** | The seller says so. Nothing has been checked. | Never on its own. |
| **RECORDED** | Logged on the public ledger as it happened, with its source named. Anyone can recompute it from the record. | When the relying party's bar accepts RECORDED (`min_rung`). |
| **PROVEN** | Checked by math: a proof that anyone re-verifies offline, without the method being revealed. | Yes. |

The ladder is served live at `GET https://studio.mizan.market/api/profiles` (`ladder`), with the reachable grade of every measure.

## Grades are per part, not per run

One run can carry different grades for different parts, and the answer says which. In the public example run `er_776c0a769ccedfbd`:

```json
{ "grading": "PROVEN", "inference_provenance": "RECORDED" }
```

The score and the attempt count are PROVEN (every attempt re-graded inside a zero-knowledge proof against sealed answers); which model produced the outputs is RECORDED (MIZAN called the endpoint and committed the reply). The reply's `proves` and `does_not_prove` fields say exactly this in words.

## Rules

1. **Unknown is never zero.** A missing count or grade is reported as unknown (`null` with a reason), never as 0.
2. **Unproven is not false.** A REFUSE for "no record" (`basis: no_record`) says nothing against the subject; it says nothing has been counted yet. It carries a forwardable proof request.
3. **Public facts never produce ALLOW.** Facts from named outside sources may be shown beside an answer (`public_facts`); only a counted claim decides.
4. **The bar decides the grade it accepts.** Without a bar, ALLOW needs a passing credential in good standing for the subject (graded PROVEN or RECORDED, never DECLARED). With a bar, the bar's `min_rung` decides.
