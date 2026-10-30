# MIZAN

**MIZAN is the open standard for proof before payment.** It aims to cover every kind of claim (models, agents, machines, data) and every grade of evidence (declared, recorded, proven), so no money moves to a machine on a result nobody counted.

*x402 lets machines pay. MIZAN proves they earned it.*

```bash
# an agent, before it pays another one: free, no key, signed
curl https://studio.mizan.market/api/check/mizan-flagship
# {"decision": "ALLOW", "basis": "proven", "evidence_rung": "PROVEN", "token": "eyJhbGciOiJFZERTQSIs…", …}
```

```ts
const res = await fetch(`https://studio.mizan.market/api/check/${payee}`);
const { decision, basis } = await res.json();          // Ed25519-signed; verify offline with verify/js
if (decision !== "ALLOW") throw new Error(`MIZAN: ${basis}`);
await pay(payee, amount);                              // only on ALLOW
```

```python
import json, urllib.request
d = json.load(urllib.request.urlopen(f"https://studio.mizan.market/api/check/{payee}"))
if d["decision"] != "ALLOW": raise SystemExit(f"MIZAN: {d['basis']}")   # signed; verify with verify/python
pay(payee, amount)                                                       # only on ALLOW
```

See [`examples/`](./examples/) for the full, runnable versions (CI runs every one against the live API).

## What it checks

Not one kind of claim. Every check answers the same object, the [counted claim](./specs/counted-claim.md): result, measure, count, evidence, requirement, verdict. Each kind of claim is a versioned **profile**: 19 live, 1 in draft, served at `GET https://studio.mizan.market/api/profiles`.

**AI models and agents**

| Profile | The question it answers |
|---|---|
| `model-evaluation` | What a model really scores |
| `model-retrain` | Every retrain is a trial *(draft)* |
| `service-reliability` | How reliable its service really is |
| `delivery-record` | What happened after others paid it |
| `denominator-reputation` | Of all its receipted jobs with independent counterparties, how many succeeded |
| `mandate-conduct` | Whether it stayed inside its own rules |
| `outcome-meter` | Billed outcomes match all conversations, under the rule fixed in advance |
| `forecast-accuracy` | How accurate its forecasts really are |

**Money**

| Profile | The question it answers |
|---|---|
| `earned-performance` | What it really earned. Trading records, under [VTR-1](./specs/vtr-1/) |
| `yield` | What yield a vault actually paid (advertised vs realised) |
| `signal-calls` | What a signal seller's calls actually did (every call counted) |
| `earnings-claim` | What typical earners actually earn (every earner counted) |
| `custody` | What a custodian or bridge says it holds (never proof of reserves) |

**Machines, chains and institutions**

| Profile | The question it answers |
|---|---|
| `depin-liveness` | Is the node really there and answering (counted challenges) |
| `onchain-event` | That it happened on-chain (settled, succeeded, confirmed) |
| `token-structure` | How a token is built: who can change it, mint it or freeze it |
| `random-draw` | Whether the operator's logged draws fit its committed odds (operator-reported) |
| `certification` | What it is certified for, by whom, until when |
| `rulebook` | Which rules were in force, and when they changed |
| `reporter-quality` | How often a security reporter's findings hold up |

A real one, not a trading record: ledger entry [#388](https://studio.mizan.market/api/log/proof/388) is a model evaluation, 50 tasks registered before their outcomes and sealed, first-try success 70%. Check it on your machine with [`examples/verify-ledger-entry`](./examples/verify-ledger-entry/).

Every answer states its evidence grade: [DECLARED, RECORDED or PROVEN](./specs/evidence-ladder.md). A live profile is one MIZAN checks today. It does not mean every claim under it is proven in zero knowledge, and the answer always says which grade it is.

## Installation

<details open>
<summary><b>MCP</b> (no install)</summary>

```bash
claude mcp add --transport http mizan https://studio.mizan.market/mcp
```

```json
{ "mcpServers": { "mizan": { "url": "https://studio.mizan.market/mcp" } } }
```

The front door lists `check`, `prove` and `more`; every tool is at `https://studio.mizan.market/mcp/full`. Local stdio build: [`python/mcp-server`](./python/mcp-server/).

</details>

<details>
<summary><b>TypeScript</b></summary>

> See [`typescript/`](./typescript/) for the SDK, the x402 guard and the elizaOS plugin.

```bash
cd typescript/packages/sdk && npm ci && npm run build      # npm release pending
```

```js
import { guardFetch } from "./integrations/x402-guard/mizan-x402-guard.mjs";   // zero dependencies
const pay = guardFetch(fetchWithPayment, { mode: "advise" });                  // later: { mode: "enforce" }
```

</details>

<details>
<summary><b>Python</b></summary>

> See [`python/`](./python/) for the SDK, the LangChain / CrewAI tools and the MCP server.

```bash
pip install https://mizan.market/skill/mizan_sdk-0.8.0-py3-none-any.whl
pip install "git+https://github.com/muaviamohammed/mizan#subdirectory=python/mizan-agent-tools"
```

```python
from mizan.x402guard import check, guard
check("mizan-flagship")["decision"]          # "ALLOW"
pay = guard(my_paying_get, mode="advise")    # inside an x402 payment
```

</details>

<details>
<summary><b>HTTP / any language</b></summary>

`GET https://studio.mizan.market/api/check/{subject}` · `POST https://studio.mizan.market/api/check {"agent": "…", "amount"?: …, "requirement"?: "req_…@1"}` · OpenAPI: <https://mizan.market/skill/openapi.json> · A2A: `https://studio.mizan.market/a2a`.

</details>

## Principles

- **Open standard.** The standard and these specifications are CC BY 4.0, free to implement by anyone, including competitors of its steward. MIZAN never asks to be the only party you rely on: every answer is signed with a published key, every ledger entry folds to a signed and externally stamped head, every credential re-verifies offline with a published verifier.
- **Count before outcome.** A try counts only if it was registered before its outcome existed. First-try results are shown beside best-of results, with the count.
- **Prove without revealing.** A proven claim is a zero-knowledge proof. The model, code, prompts and strategy never leave their owner's machine.
- **The buyer writes the bar.** Plain words in, a versioned rule back, read back and fixed by hash before anyone is checked. Words that cannot be bound are listed, never guessed.
- **Refusals are published.** A refusal is published beside a pass, MIZAN's own included. That is what makes a pass worth something.
- **Neutral.** Checks are free and no fee depends on a verdict. MIZAN never holds, routes or releases funds.

## How it works

Every check answers one **counted claim**, in six parts ([spec](./specs/counted-claim.md)):

| # | Part | What it fixes | Example (ledger entries #385 to #388) |
|---|---|---|---|
| 01 | **Result** | What is claimed | 70% first-try success |
| 02 | **Measure** | Measured how, on what | Code reading: fifty fixed short programs, answers sealed, graded independently |
| 03 | **Count** | Every try registered before its outcome | 50 of 50 attempts; nothing retried, nothing dropped |
| 04 | **Evidence** | Its rung: DECLARED · RECORDED · PROVEN | RECORDED: declared, run and sealed in the public ledger |
| 05 | **Requirement** | The buyer's bar, in the buyer's words, fixed first | first-try success at least 90% over at least 50 tasks |
| 06 | **Verdict** | ALLOW or REFUSE, signed, with its basis | REFUSE: 70% is below 90% |

```
agent ──check(payee, bar)──▶ MIZAN ──▶ count · evidence rung · requirement ──▶ ALLOW / REFUSE (signed)
                                          │
                                          └─▶ public ledger: RFC 6962 leaf · signed head · hourly outside stamps
```

A REFUSE carries a forwardable proof request: when the other side proves itself, the next check returns ALLOW.

## Live, not a proposal

| | |
|---|---|
| Public ledger, verifiable in your browser | <https://mizan.market> (click any row) · head: <https://studio.mizan.market/api/log/head> |
| Live counts (proofs, refusals, steps proven, checks served) | <https://studio.mizan.market/api/public/stats> |
| Registry of every credential, refusals included | <https://mizan.market/registry/> · <https://studio.mizan.market/api/registry> |
| Published keys | <https://studio.mizan.market/.well-known/mizan-keys.json> |
| Verifier binaries + SHA-256 sums | <https://mizan.market/verify/> |
| The standard | [`specs/`](./specs/): the counted claim, evidence ladder, requirement language, ledger, signatures, and the profiles. Trading records: VTR-1, frozen 2026-08-01, [SSRN 7215664](https://ssrn.com/abstract=7215664) · <https://mizan.market/standard/> |
| For agents | [`llms.txt`](https://mizan.market/llms.txt) · [`SKILL.md`](https://mizan.market/skill/SKILL.md) · [`openapi.json`](https://mizan.market/skill/openapi.json) |

## Where it plugs in

| | |
|---|---|
| **x402** | The [guard](./integrations/x402-guard/) checks the payee inside the payment step: advise or enforce. |
| **AP2** | Check before the payment mandate is signed; keep the signed token with the mandate. [Integration point](./integrations/ap2-acp.md). |
| **ACP** | Check the merchant before the checkout completes. [Integration point](./integrations/ap2-acp.md). |
| **MCP** | Hosted server at `https://studio.mizan.market/mcp`. |
| **A2A** | `https://studio.mizan.market/a2a` · [agent card](./integrations/a2a/). |
| **ERC-8004** | Verdicts in ERC-8004 feedback and validation shapes; EIP-712 receipts checked on-chain by [`MizanProof.sol`](./integrations/erc8004/). |
| **elizaOS** | [`plugin-mizan`](./integrations/elizaos/). |
| **LangChain / LangGraph** | [`mizan-agent-tools`](./python/mizan-agent-tools/). |
| **CrewAI** | [`mizan-agent-tools`](./python/mizan-agent-tools/). |

Status of each, stated plainly: [`integrations/README.md`](./integrations/README.md).

## Repository

```
specs/          the counted claim, evidence ladder, requirement language, ledger, signatures, profiles incl. VTR-1 (CC BY 4.0)
typescript/     SDK (mizan-agent-tools)
python/         SDK (mizan-sdk), LangChain / CrewAI tools, MCP server (stdio)
integrations/   x402 guard, elizaOS, A2A, ERC-8004, AP2 / ACP, LangChain, CrewAI
examples/       check-before-pay · escrow-release-check · verify-ledger-entry · pin-a-requirement
verify/         offline verification: published keys, ledger proofs, verifier binaries
docs/           quickstart, concepts, verify, FAQ, honest boundary
```

## Honest boundary

MIZAN proves named, measurable facts about the past. On a past record the count is a floor (what was registered); on a forward record, registered before any outcome exists, the count is complete from that point on. A lower rung is never shown as a higher one, and unproven is not false. MIZAN never claims the future, intent, or that any system is safe, aligned or honest in general. It never holds funds. The prover is private; the standard, specifications, SDKs, integrations and examples here are open. More: [`docs/honest-boundary.md`](./docs/honest-boundary.md).

## License

Code: [MIT](./LICENSE). Specifications in [`specs/`](./specs/): [CC BY 4.0](./LICENSE-SPEC). Security reports: [`SECURITY.md`](./SECURITY.md). Contributing: [`CONTRIBUTING.md`](./CONTRIBUTING.md).

MIZAN is a verification and technology provider. A decision is about a counterparty's record, never advice about a payment; the relying party keeps responsibility.
