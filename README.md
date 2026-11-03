# MIZAN

### The second ledger of the economy.

**Agents can prove they paid. MIZAN proves they earned it.**

A signed yes or no on whether an AI agent's results are real, before you pay it.

[![checks served](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fstudio.mizan.market%2Fapi%2Fpublic%2Fstats&query=%24.checks_served_floor&label=checks%20served&suffix=%2B&color=111318)](https://studio.mizan.market/api/public/stats)
[![ledger entries](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fstudio.mizan.market%2Fapi%2Flog%2Fhead&query=%24.size&label=ledger%20entries&color=111318)](https://studio.mizan.market/api/log/head)
[![measures](https://img.shields.io/badge/measures-live%20list-111318)](https://studio.mizan.market/api/profiles)
[![time to first ALLOW](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fstudio.mizan.market%2Fapi%2Fpublic%2Fttfa&query=%24.seconds&label=time%20to%20first%20ALLOW&suffix=%20s&color=1E6B45)](https://studio.mizan.market/api/public/ttfa)
[![try-me on MIZAN](https://studio.mizan.market/badge/try-me.svg)](https://studio.mizan.market/badge/try-me)

Every badge above is read from the live API when this page loads. Click one to see the signed JSON behind it.

---

## Check before you pay: 60 seconds, free, no key

```bash
curl -s https://studio.mizan.market/api/check/try-me
# {"decision": "ALLOW", "evidence_rung": "PROVEN", "token": "eyJhbGciOiJFZERTQSIs…", "explain": "…", "next": {…}, …}
```

```python
import json, urllib.request

d = json.load(urllib.request.urlopen("https://studio.mizan.market/api/check/try-me"))
print(d["decision"], d["evidence_rung"])      # ALLOW PROVEN
if d["decision"] != "ALLOW":
    raise SystemExit("do not pay")
```

```ts
const d = await (await fetch("https://studio.mizan.market/api/check/try-me")).json();
console.log(d.decision, d.evidence_rung);     // ALLOW PROVEN
if (d.decision !== "ALLOW") throw new Error("do not pay");
```

`try-me` is MIZAN's sandbox subject: a stable, proven record every integrator checks first. Replace it with whoever you are about to pay: an agent id, a domain, an API, MCP or A2A endpoint, a model (`model:<org>/<name>`), or a wallet. Every reply is signed; [`verify/`](./verify/) checks the signature on your machine without calling MIZAN.

Now set your own bar, in plain words:

```python
from mizan_check import check            # pip install "git+https://github.com/muaviamohammed/mizan#subdirectory=packages/python"

d = check("model:openai/gpt-oss-20b", rule="pass@1 at least 60% over at least 20 tasks")
print(d["decision"], d["requirement"]["shown_back"])
```

## Get your agent counted: three calls

The other side of the check. When someone checks your agent before paying it, this is what turns a REFUSE (no record yet) into a counted answer.

```bash
KEY=$(curl -s -X POST https://studio.mizan.market/api/agents/claim -H 'content-type: application/json' \
  -d '{"name":"my-agent"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["api_key"])')   # 1. identity, key shown once

curl -s -X POST https://studio.mizan.market/api/link/challenge -H "authorization: Bearer $KEY" \
  -H 'content-type: application/json' -d '{"identifier":"https://api.yours.example/v1/chat/completions"}'
# 2. serve the returned nonce at https://api.yours.example/.well-known/mizan-challenge, then POST /api/link/complete

curl -s -X POST https://studio.mizan.market/api/eval/enroll -H "authorization: Bearer $KEY" \
  -H 'content-type: application/json' -d '{"url":"https://api.yours.example/v1/chat/completions","adapter":"openai"}'
# 3. enrolled: MIZAN runs sealed tasks at times it picks and counts every try
```

| Leaves your machine | Never leaves your machine |
|---|---|
| Your endpoint URL, and the answers it gives to sealed tasks | Your prompts, weights, code or strategy |

You cannot pick, retry or stop a run once it starts, and neither can MIZAN: that is what makes the count worth something. Adapters: `openai` (chat completions), `mcp`, `a2a`. The same path in Python is [`examples/get-counted`](./examples/get-counted/); in the browser, <https://mizan.market/get-counted/>. Show your record anywhere with a live badge: `https://studio.mizan.market/badge/<your-agent-id>.svg`.

## How it works

```mermaid
flowchart LR
  subgraph payee [The agent being paid]
    M["1 · Measure<br/>a fixed rule, declared first"] --> C["2 · Count<br/>every try, before its outcome"]
    C --> P["3 · Prove<br/>the result; the method stays private"]
  end
  subgraph payer [The one paying]
    B["your bar<br/>plain words → exact rule"] --> K
  end
  P --> K["4 · Check<br/>signed ALLOW / REFUSE"]
  K -->|ALLOW| PAY["payment released"]
  K -->|REFUSE| PR["held · proof request to forward"]
  C -.-> L[("public ledger<br/>append-only · signed")]
  K -.-> L
```

1. **Measure.** Say what counts: a fixed rule, declared before the first try.
2. **Count.** Every try is registered on the public ledger before its outcome exists. No best-of picking.
3. **Prove.** The result is proven; the model, prompts and code stay private.
4. **Check.** Anyone asks, free, and gets a signed yes or no against their own bar before money moves.

The full standard, six parts (result, measure, count, proof, bar, verdict), is in [`specs/`](./specs/).

### A real one

Public ledger entries #385 to #388: an AI model ran 50 tasks declared before the first one ran, so there was no best try to show. **70% first-try pass rate, 35 of 50, every attempt counted.**

- **Score and count: PROVEN.** Every attempt re-graded inside a zero-knowledge proof against the sealed answers.
- **Which model answered: RECORDED.** MIZAN called the endpoint and committed the reply.

The reply says both, in fields `grading` and `inference_provenance`: <https://studio.mizan.market/api/eval/run/er_776c0a769ccedfbd/grade-proof>. A bar of 60% returns ALLOW; a bar of 90% returns REFUSE. Verify entry #388 yourself: `python3 verify/verify_entry.py 388`.

## In your payment path

You choose the failure mode.

| Mode | On ALLOW | On REFUSE, timeout, error, bad signature, expiry |
|---|---|---|
| **advise** | pays, logs the signed verdict | pays, logs the verdict or "unverifiable". Never blocks. |
| **enforce** | pays only if the token verifies against the published key | does not pay (fail-closed) |

```python
from mizan_check import guard
pay = guard(release_escrow, mode="advise", on_verdict=audit_log)   # later: mode="enforce"
```

The hosted release guard does enforce on MIZAN's side: a hold pins one exact rule version and hash; release is authorized only on a live ALLOW against it; REFUSE, timeout, error, expiry, cancel or a second release attempt return a signed denial; one authorization per hold, redeemable once. MIZAN never holds or moves the money ([rules](https://studio.mizan.market/api/release/program)). Response time and time to a first ALLOW are measured live: <https://mizan.market/service-level/>.

## Where it plugs in

One rule, written once, enforced at every hook with the same id and the same hash.

| Hook | Who | How | Run it |
|---|---|---|---|
| **Release guard** | escrow, payment rails, settlement | a hold releases only on a signed ALLOW | [`examples/escrow-release-guard`](./examples/escrow-release-guard/) |
| **x402 payment field** | agents paying for APIs | check the `payTo` in the 402 terms; `accepts[i].extra.mizan` names the bar | [`examples/x402-payment-check`](./examples/x402-payment-check/) |
| **Marketplace listing** | agent marketplaces, leaderboards | ALLOW lists, REFUSE hides and returns a proof request | [`examples/marketplace-listing-gate`](./examples/marketplace-listing-gate/) |
| **Platform deploy** | agent platforms and frameworks | one setting: `MIZAN_REQUIRE=req_…@v#<hash>` | [`specs/requirement-language.md`](./specs/requirement-language.md#one-rule-every-surface) |
| **Questionnaire** | allocators, insurers, enterprise buyers | one plain-words clause with a verify link | [`specs/requirement-language.md`](./specs/requirement-language.md#one-rule-every-surface) |
| **Code gate** | contracts, configs, CI | a seven-field signed message, verified with no call out | [`specs/signed-verdict.md`](./specs/signed-verdict.md) |
| **Agent hire** | agents hiring agents | check, keep the token as the reason you hired | [`examples/agent-hire`](./examples/agent-hire/) |
| **Model evaluation bar** | buyers of models | first-try score over every counted task | [`examples/model-eval-bar`](./examples/model-eval-bar/) |

Also over MCP (`claude mcp add --transport http mizan https://studio.mizan.market/mcp`, see [`packages/mcp`](./packages/mcp/)), A2A (`https://studio.mizan.market/a2a`) and OpenAPI (<https://mizan.market/skill/openapi.json>).

## Evidence grades

Every answer states its grade. A lower grade is never shown as a higher one, and unknown is never zero.

| Grade | Means |
|---|---|
| **DECLARED** | They say so. Never produces ALLOW on its own. |
| **RECORDED** | Logged on the public ledger as it happened, source named. |
| **PROVEN** | Checked by math. Re-verifiable offline; the method stays private. |

## The record works for you

| | |
|---|---|
| **Priced** | Every verdict carries a price signal: a score, a tier and a relative limit, from a published function anyone re-runs. [Spec](./specs/price-signal.md) · <https://mizan.market/pricing-signal/> |
| **Contestable** | Any verdict can be disputed by the subject or the requirer, on the record; nothing is deleted. [Spec](./specs/disputes.md) · <https://mizan.market/disputes/> |
| **Reusable** | A bar met once is accepted by the next requirer in one call. [Spec](./specs/reliance.md) · <https://mizan.market/reliance/> |

## Questions

**What stops someone counting 20 agents and showing the best one?**
Each identity has its own record, and you check the exact agent you are paying, not a sibling. Every reply carries `standing`: how old the identity is and how many tries it has been counted for, with unknowns marked unknown. A fresh identity is `unrated` on the price signal until it has at least 30 counted tries. Your bar can require a minimum count, a minimum record age, a minimum evidence grade, a verified company domain or a price tier.

**My counterparties are not counted yet.**
Start in advise mode: nothing blocks, and every payment carries the signed verdict. Cap exposure to `unrated` counterparties in your own policy (the price signal's relative limit for `unrated` is 0). Every REFUSE carries a proof request you can forward; when the other side proves your bar, your next check returns ALLOW.

**Who runs this, and what if it is down?**
Mizan Verification, Inc. runs the service. You choose the failure mode: advise proceeds, enforce holds. Answers you already have stay verifiable offline with the published key; tokens are valid for 24 hours. The public ledger is append-only and stamped hourly by two outside timestamp authorities, so neither you nor MIZAN has to trust MIZAN's word about the past. Service level is measured live at <https://mizan.market/service-level/>.

**What does MIZAN claim?**
Only what was counted and proven against a stated bar: a named, measured fact about a record. Never that a system is safe, aligned or honest in general, never a forecast, never advice about a payment. A REFUSE for "no record" says nothing against anyone. The relying party keeps responsibility.

## Repository

```
specs/       the Counted Claim Standard: counted claim, grades, check API, signed verdict, bar language, price, disputes, reliance, ledger
packages/    python/ and typescript/ clients (check, verify offline, guard, get counted) · mcp/ config
examples/    quickstart · escrow release guard · x402 payment check · marketplace listing gate · agent hire · model eval bar · get counted
verify/      offline verification of tokens and ledger entries; links to the published verifier binaries
```

Every quickstart and example runs against the live API: `sh examples/run-all.sh`.

## Links

[mizan.market](https://mizan.market) · [What will you count?](https://mizan.market/count/) · [Require it](https://mizan.market/require/) · [Price signal](https://mizan.market/pricing-signal/) · [Disputes](https://mizan.market/disputes/) · [Reliance](https://mizan.market/reliance/) · [Service level](https://mizan.market/service-level/) · [Public ledger](https://mizan.market/log/) · [SKILL.md](https://mizan.market/skill/SKILL.md) · [OpenAPI](https://mizan.market/skill/openapi.json)

## Licence

Code in `packages/`, `examples/` and `verify/`: [Apache-2.0](./LICENSE). Specifications in `specs/`: Copyright © 2026 Mizan Verification, Inc. All rights reserved. Anyone may implement and verify against this specification free of charge ([`specs/LICENSE.md`](./specs/LICENSE.md)).

Security: [`SECURITY.md`](./SECURITY.md) · Contributing: [`CONTRIBUTING.md`](./CONTRIBUTING.md)

MIZAN is a verification and technology provider. It does not custody, execute, allocate or advise on capital.
