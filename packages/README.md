# Packages

| Package | Install | What it is |
|---|---|---|
| [`python/`](./python/) | `pip install "git+https://github.com/muaviamohammed/mizan#subdirectory=packages/python"` | `mizan-check`: check, offline verification, the payment guard, get counted. Standard library + `cryptography`. |
| [`typescript/`](./typescript/) | `cd packages/typescript && npm install && npm run build` | `mizan-check`: the same surface, zero runtime dependencies, Node 20+. |
| [`mcp/`](./mcp/) | no install | The hosted MCP server, with config for Claude, Cursor and VS Code. |

Every package is tested live against `https://studio.mizan.market` (see each `tests/` folder and [`../examples/run-all.sh`](../examples/run-all.sh)).
