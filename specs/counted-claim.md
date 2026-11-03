# The counted claim

A counted claim is a result that carries everything a relying party needs to decide on it: how it was measured, every try behind it, the evidence and its grade, the relying party's own bar, and a signed answer.

## The six parts

| # | Part | Fixes | Fixed when |
|---|---|---|---|
| 01 | **Result** | The number shown. | Computed from the counted tries, never chosen among them. |
| 02 | **Measure** | How the number is measured, over what, and who may record. | Before the first try is registered. It cannot change afterwards. |
| 03 | **Count** | Every try behind the result, none left out. | Each try is registered on the public ledger before its outcome exists. |
| 04 | **Proof** | The evidence for the result, with its [grade](./evidence-grades.md) stated. | When the result is sealed. |
| 05 | **Bar** | The relying party's requirement, in plain words, compiled to an exact rule. | Read back and fixed by hash before anyone is checked against it. |
| 06 | **Verdict** | A signed ALLOW or REFUSE: does the result meet the bar. | At check time; valid for a stated window; re-checkable offline. |

## Rules

1. **Count before outcome.** A try that was not registered before its outcome existed MUST NOT count toward the result. First-try results are shown beside best-of results, with the count; a best-of figure is never shown alone.
2. **The measure is fixed first.** A measure MUST NOT change once its first try is registered. A changed measure is a new measure with a new record.
3. **The bar is the relying party's.** The bar is written by whoever relies on the result, read back as an exact rule ([requirement language](./requirement-language.md)), and pinned by hash. Words that cannot be bound are listed, never guessed.
4. **One grade, never inflated.** A claim carries the lowest grade any of its parts supports. A lower grade MUST NOT be presented as a higher one. Unknown is never reported as zero.
5. **Signed, offline-verifiable answers.** Every verdict is signed with a published key and verifies without asking MIZAN ([signed verdict](./signed-verdict.md)).
6. **Refusals are published.** A refusal is recorded under the same name as a pass. A record shows what failed as plainly as what passed.
7. **The method stays private.** A PROVEN result is established by a proof that verifies without revealing the model, code, prompts or strategy behind it.

## Measures

A measure (a *profile*) fixes how one kind of result is measured and counted; the six-part shape stays the same. The live list, each with its reachable grade, is at `GET https://studio.mizan.market/api/profiles` (agent-work measures: `GET https://studio.mizan.market/api/measures`). Examples: AI evaluation (pass@1 over tasks declared before the first ran), task completion, cost per completed task, instruction adherence, factual error rate, payment behaviour, latency SLA, tool-use safety, run consistency, service reliability, forecast accuracy, earned performance.

## A worked example

Public ledger entries #385 to #388; run `er_776c0a769ccedfbd`.

| Part | Value |
|---|---|
| Result | 70% first-try pass rate (35 of 50). |
| Measure | 50 fixed tasks, answers sealed, graded by a fixed grader. Statement `mizan/eval-grade/1`. |
| Count | 50 of 50 attempts, registered before they ran; nothing retried, nothing dropped. |
| Proof | **Score and count PROVEN**: every attempt re-graded inside a zero-knowledge proof against the sealed answers. **Which model answered: RECORDED** (MIZAN called the endpoint and committed the reply). |
| Bar | e.g. "pass@1 at least 60% over at least 50 tasks". |
| Verdict | ALLOW at a 60% bar; REFUSE at 90%. |

Read the proof: <https://studio.mizan.market/api/eval/run/er_776c0a769ccedfbd/grade-proof> (fields `grading: PROVEN`, `inference_provenance: RECORDED`, `proves`, `does_not_prove`). Verify the ledger entries on your machine with [`verify/`](../verify/).

## What a counted claim never says

A counted claim states a named, measured fact about a record. It never says a system is safe, aligned or honest in general, never forecasts, and never advises on a payment. A verdict reads the record against the stated bar; the relying party keeps responsibility for what it does next.
