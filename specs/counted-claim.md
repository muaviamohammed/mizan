# The counted claim

Every check MIZAN answers is about one **counted claim**: a result, put next to everything needed to decide whether to rely on it. It has six parts.

| # | Part | Question it answers | Example (ledger entries #385 to #388) |
|---|---|---|---|
| 01 | **Result** | What is being claimed? | 70% first-try success |
| 02 | **Measure** | Measured how, on what? | Code reading: fifty fixed short programs; state exactly what each prints. Answers sealed, graded independently. |
| 03 | **Count** | How many tries stand behind it, registered before their outcomes? | 50 of 50 attempts. Interrupted once, resumed in order; nothing retried, nothing dropped. |
| 04 | **Evidence** | How strong is the evidence? One rung of the [ladder](./evidence-ladder.md). | RECORDED: declared, run and sealed in the public ledger, with times anyone can check. |
| 05 | **Requirement** | Whose bar, in whose words? Written by the buyer, fixed before anyone is checked. See [requirement language](./requirement-language.md). | "first-try success at least 90% over at least 50 tasks" |
| 06 | **Verdict** | ALLOW or REFUSE, signed, with its basis. | REFUSE: result 70% is below 90%. |

The example is live: `GET https://studio.mizan.market/api/log/proof/388` returns the entry and its inclusion proof, and [`examples/verify-ledger-entry`](../examples/verify-ledger-entry/) checks it on your machine.

## Rules

1. **Count before outcome.** A try counts only if it was registered before its outcome existed. On a past record the count is a floor (what was registered); on a forward record, registered before any outcome exists, the count is complete from that point on.
2. **First try next to best try.** Where a count exists, the first-try result is shown beside the best-of result, with the count.
3. **The rung is never inflated.** A RECORDED claim is never presented as PROVEN; a DECLARED claim never produces ALLOW on its own.
4. **The bar is fixed first.** A requirement is compiled, read back in plain words and hashed before anyone is checked against it. Changing a word makes a new version.
5. **The verdict is signed and published.** Every answer is signed with a published key and verifies offline. Refusals are published beside passes.
6. **The method stays private.** Proving a result never requires revealing the model, code, prompts or strategy behind it.

## Kinds of claim

The same six parts serve every kind of claim. Each kind is a versioned **profile** (for example `earned-performance@1.2`, `model-evaluation@1.1`, `forecast-accuracy@2.0`, `service-reliability@1.1`, `mandate-conduct@1.0`, `delivery-record@1.0`). The live list, with status, is at `GET https://studio.mizan.market/api/profiles`.
