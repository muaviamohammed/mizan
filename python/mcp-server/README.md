# MIZAN MCP server

**Hosted, no install:** `https://studio.mizan.market/mcp` (streamable HTTP). The default address lists the front door (`check`, `prove`, `more`); every tool is at `https://studio.mizan.market/mcp/full`. Checking needs no key.

```bash
claude mcp add --transport http mizan https://studio.mizan.market/mcp
```

```json
{ "mcpServers": { "mizan": { "url": "https://studio.mizan.market/mcp" } } }
```

## Local stdio build

This folder is a local build of the same tools for hosts that prefer stdio.

```bash
pip install -r requirements.txt          # mcp>=2
python3 mizan_mcp_server.py              # stdio
MIZAN_MCP_HTTP=9000 python3 mizan_mcp_server.py   # streamable HTTP on :9000
claude mcp add mizan -- python3 /path/to/mizan_mcp_server.py
```

Tools that write (minting, publishing) read `MIZAN_API_KEY` from the environment. `server.json` is the registry manifest for the hosted server (`io.github.muaviamohammed/mizan`); this repository does not publish it.
