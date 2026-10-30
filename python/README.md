# Python

| Package | Folder | What it is |
|---|---|---|
| `mizan-sdk` | [`mizan-sdk`](./mizan-sdk/) | The SDK and `mizan` CLI. Stdlib only. `mizan.x402guard.check / guard`, `mizan.gate`, receipts, `prove`, `verify`. |
| `mizan-agent-tools` | [`mizan-agent-tools`](./mizan-agent-tools/) | LangChain, LangGraph and CrewAI tools. |
| MCP server (stdio) | [`mcp-server`](./mcp-server/) | A local build of the MIZAN MCP server. The hosted one needs no install: `https://studio.mizan.market/mcp`. |
| Offline verification | [`../verify/python`](../verify/python/) | Canonical JSON, Ed25519 reply signatures, RFC 6962 ledger proofs. |

```bash
pip install https://mizan.market/skill/mizan_sdk-0.8.0-py3-none-any.whl                     # published wheel
pip install "git+https://github.com/muaviamohammed/mizan#subdirectory=python/mizan-sdk"         # from this repo
pip install "git+https://github.com/muaviamohammed/mizan#subdirectory=python/mizan-agent-tools"
```

PyPI releases are pending.
