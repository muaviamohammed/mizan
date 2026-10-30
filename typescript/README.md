# TypeScript

| Package | Folder | What it is |
|---|---|---|
| `mizan-agent-tools` | [`packages/sdk`](./packages/sdk/) | Typed, dependency-free client for the public API: `checkAgent`, `verifyCredential`, `searchCredentials`, `listProvenAgents`, `listDatasets`, `mintPreview`. |
| x402 guard | [`../integrations/x402-guard`](../integrations/x402-guard/) | `guardFetch(payingFetch, { mode })`: the check inside an x402 payment. Zero dependencies. |
| elizaOS plugin | [`../integrations/elizaos`](../integrations/elizaos/) | `plugin-mizan`. |
| Offline verification | [`../verify/js`](../verify/js/) | Canonical JSON, Ed25519 reply signatures, RFC 6962 ledger proofs. Node 20+. |

npm releases are pending; build from source:

```bash
cd typescript/packages/sdk && npm ci && npm run build && npm test
```

**MCP.** The MCP server is hosted, so there is nothing to install: `https://studio.mizan.market/mcp` (streamable HTTP). A local stdio build is in [`../python/mcp-server`](../python/mcp-server/).

```json
{ "mcpServers": { "mizan": { "url": "https://studio.mizan.market/mcp" } } }
```
