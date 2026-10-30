# mizan-agent-tools (TypeScript)

> Part of [MIZAN](../../../README.md), the open standard for proof before payment.

Typed, dependency-free TypeScript client for the public MIZAN API. Use it so an agent can check a
counterparty **before it pays, hires, copies or allocates**: one signed answer, refusals published beside
passes, unproven reported as unproven (never as false). A credential proves a named fact about a past
record, never a forecast. Remote MCP with no install: `https://studio.mizan.market/mcp`.

```bash
cd typescript/packages/sdk && npm ci && npm run build     # npm release pending; build from source
```

```ts
import { checkAgent, verifyCredential } from "mizan-agent-tools";

const c = await checkAgent("0xabc123", "pay");
// c.status: PROVEN | REFUSED | NOT_SIGNIFICANT | UNVERIFIED (unproven, which is not the same as false)
// c.forward_to_counterparty: a ready message the other side uses to prove itself (only when UNVERIFIED)

const r = await verifyCredential("v12-btc-trend-4h");   // verdict exactly as issued + bundle hash check
```

For the one-call signed ALLOW / REFUSE (`GET /api/check/{subject}`) with offline signature
verification, see [`examples/check-before-pay`](../../../examples/check-before-pay/) and
[`verify/js`](../../../verify/js/).

## What each call does

| Call | Endpoint | Notes |
|---|---|---|
| `checkAgent(agent, action?)` | `GET /api/agents/check?q=&action=` | `agent` may be a name/alias, credential id, wallet, ERC-8004 id, agent-card URL or sha256. Returns PROVEN / REFUSED / NOT_SIGNIFICANT / UNVERIFIED with matching credentials. |
| `listProvenAgents(limit = 25, realOnly = true)` | `GET /api/agents/proven` | PASS credentials; `realOnly` keeps Bitcoin-confirmed ones. Includes the issuer disclosure. |
| `verifyCredential(id \| {id, sha256})` | `GET /api/registry`, then the proof bundle | Verdict exactly as issued. Missing credential or bundle hash mismatch gives `UNVERIFIED`. Provenance read best-effort from `GET /api/public/registry`. |
| `searchCredentials({query, alias, issuer, verdict, dataset, kind, includeSandbox, limit})` | `GET /api/registry` | Client-side filter of the public registry. |
| `listDatasets({asset, interval, venue, cls, query, limit})` | `GET /api/blackbox-datasets` | Canonical markets a sealed-path credential can be minted on. CSV at `/api/catalog/{key}.csv`. |
| `mintPreview({dataset, positions, ...})` | `POST /x402/preview` | Free, private gate preview, no account, about 10 per IP per day. Positions only. Nothing is published. |

## Limits, stated plainly

- The hash check proves the bundle you downloaded is the one the registry anchored. It does not
  re-run the STARK. For full offline re-verification use the verifier at https://mizan.market/verify/.
- `/api/registry` sends no CORS headers; in a browser, proxy it or use the server side.
- Paid minting is not enabled through this client. See https://mizan.market/skill/.
- Every credential listed so far was minted by MIZAN itself (its own engines and open-testing mints).

## Develop

```bash
npm install
npm run build        # tsup → ESM + CJS + .d.ts
npm test             # unit tests, mocked fetch
npm run test:live    # live verify, checkAgent and listProvenAgents against the real API
```

MIT licensed.
