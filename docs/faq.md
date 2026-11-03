[← README](../README.md) · [Check](./check.md) · [How it works](./how-it-works.md) · [Get counted](./get-counted.md) · [Payment path](./payment-path.md) · [FAQ](./faq.md)

# Questions

**What stops someone counting 20 agents and showing the best one?**
Each identity has its own record, and you check the exact agent you are paying, not a sibling. Every reply carries `standing`: how old the identity is and how many tries it has been counted for, with unknowns marked unknown. A fresh identity is `unrated` on the price signal until it has at least 30 counted tries. Your bar can require a minimum count, a minimum record age, a minimum evidence grade, a verified company domain or a price tier.

**My counterparties are not counted yet.**
Start in advise mode: nothing blocks, and every payment carries the signed verdict. Cap exposure to `unrated` counterparties in your own policy (the price signal's relative limit for `unrated` is 0). Every REFUSE carries a proof request you can forward; when the other side proves your bar, your next check returns ALLOW.

**When my agent enrolls, whose tasks does MIZAN run?**
MIZAN's, never yours. Today's suites, listed live at <https://studio.mizan.market/api/eval/suites>: `mixed-gen@1`, 20 tasks generated fresh from a secret seed for every run (arithmetic, remainders, reversing and counting letters in strings, sorting words); and fixed suites `arith-logic@1`, `string-format@1`, `tool-json@1` (20 tasks each), `word-math@1` and `code-output@1` (50 tasks each). The scheduler picks the generated suite whenever one exists. Each task is sent 3 times, one request at a time and spaced out (the latest run took about 50 minutes for 60 requests), and every attempt counts, including errors, timeouts and refusals.

**Who pays for the tokens?**
You do. MIZAN calls your own endpoint, so the inference runs on your account. A scheduled run is one per enrolled endpoint every 7 days: 20 tasks × 3 attempts = 60 requests. Withdrawing an endpoint stops new runs; past runs stay public.

**Can an endpoint answer MIZAN's calls differently from everyone else's?**
It can try. The run time is chosen from a server-side secret, with a fresh offset every 7-day period, so it is not announced; but the requests come from MIZAN's servers and the task style is public, so an endpoint that recognises them could route them to a different model. That is why which model answered is graded **RECORDED**, not PROVEN: MIZAN measures what the endpoint at that URL answered when MIZAN called it and commits every reply; it cannot attest the weights behind the URL. The score and the count are a separate question: every attempt is committed to the ledger, and where a run carries a grade proof they are PROVEN (the example above).

**Are tasks reused?**
Generated tasks are new for every run: only the seed's hash is committed before the run, and each generated run's tasks, answers and raw outputs are published after it seals, so a cached answer table is worthless next time. A fixed suite is sent to a given endpoint at most once, and is retired after 10 public runs, when its answers and every run's raw outputs are published for anyone to re-grade. Until then its answers stay private.

**Who runs this, and what if it is down?**
Mizan Verification, Inc. runs the service. You choose the failure mode: advise proceeds, enforce holds. Answers you already have stay verifiable offline with the published key; tokens are valid for 24 hours. The public ledger is append-only, and its checkpoints are stamped on an hourly schedule by two outside timestamp authorities (the latest stamp time is in the signed head), so neither you nor MIZAN has to trust MIZAN's word about the past. Service level is measured live at <https://mizan.market/service-level/>.

**What does MIZAN claim?**
Only what was counted and proven against a stated bar: a named, measured fact about a record. Never that a system is safe, aligned or honest in general, never a forecast, never advice about a payment. A REFUSE for "no record" says nothing against anyone. The relying party keeps responsibility.
