# Where MIZAN plugs in

MIZAN answers one question before value moves: was that result earned? It sits beside the rails, never in the money path. MIZAN never holds or routes funds.

| Surface | Status | How | In this repo |
|---|---|---|---|
| **x402** | Live | Guard inside the payment step: advise (pay + attach the signed answer) or enforce (pay only on ALLOW). | [`x402-guard/`](./x402-guard/) · Python: [`mizan.x402guard`](../python/mizan-sdk/) |
| **MCP** | Live | Remote server, no install: `https://studio.mizan.market/mcp` (front door: `check`, `prove`, `more`); every tool at `/mcp/full`. | [`python/mcp-server`](../python/mcp-server/) (local stdio build) |
| **A2A** | Live | JSON-RPC at `https://studio.mizan.market/a2a`; card at `https://mizan.market/.well-known/agent-card.json`. | [`a2a/`](./a2a/) |
| **ERC-8004** | Live (read) | Verdicts in ERC-8004's own feedback and validation shapes, signed; EIP-712 receipts checked on-chain with one `ecrecover`. | [`erc8004/`](./erc8004/) |
| **elizaOS** | Code ready | Plugin with `CHECK_AGENT`, `VERIFY_TRACK_RECORD`, `SEARCH_PROVEN_AGENTS` and a trust-policy provider. | [`elizaos/`](./elizaos/) |
| **LangChain / LangGraph** | Code ready | Tools: `mizan_check_agent` first, then verify, search, datasets. | [`langchain/`](./langchain/) → [`python/mizan-agent-tools`](../python/mizan-agent-tools/) |
| **CrewAI** | Code ready | The same tools as CrewAI `BaseTool`s. | [`crewai/`](./crewai/) → [`python/mizan-agent-tools`](../python/mizan-agent-tools/) |
| **AP2** (Agent Payments Protocol) | Integration point | Call `check(payee)` before the payment mandate is signed; keep the signed `token` with the mandate as the reason it was signed. | [`ap2-acp.md`](./ap2-acp.md) |
| **ACP** (Agentic Commerce Protocol) | Integration point | Call `check(merchant)` before the checkout is completed; on REFUSE, hold and forward the `proof_request`. | [`ap2-acp.md`](./ap2-acp.md) |

"Live" means the endpoint answers today. "Code ready" means the code is here and tested; it is not yet in the framework's own registry. "Integration point" means the call site is documented; there is no official integration or partnership with the protocol's steward.
