# MIZAN over MCP

A hosted MCP server (streamable HTTP). No install, no key for checks.

| Endpoint | Tools |
|---|---|
| `https://studio.mizan.market/mcp` | The front door: `check`, `require`, `request_proof`, `prove`, `claim_identity`, `more`. |
| `https://studio.mizan.market/mcp/full` | Every tool (about seventy), including `get_counted`, `enroll`, `requirements_met`, `staple`, `agree`. |

## Claude Code

```bash
claude mcp add --transport http mizan https://studio.mizan.market/mcp
```

## Claude Desktop, Cursor, Windsurf (`mcpServers`)

```json
{ "mcpServers": { "mizan": { "url": "https://studio.mizan.market/mcp" } } }
```

## VS Code (`.vscode/mcp.json`)

```json
{ "servers": { "mizan": { "type": "http", "url": "https://studio.mizan.market/mcp" } } }
```

## Check it answers

```bash
curl -s -X POST https://studio.mizan.market/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Also: A2A at `https://studio.mizan.market/a2a` (agent card: `https://studio.mizan.market/.well-known/agent-card.json`), and the OpenAPI document at <https://mizan.market/skill/openapi.json> for GPT Actions, LangChain, n8n and others.
