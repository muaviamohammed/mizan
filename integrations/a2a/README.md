# A2A

MIZAN is an A2A agent. Any A2A client can ask it to check a counterparty.

- Endpoint (JSON-RPC 2.0): `https://studio.mizan.market/a2a`
- Agent card: <https://mizan.market/.well-known/agent-card.json> (a snapshot is in [`agent-card.json`](./agent-card.json); the live card governs)

```bash
curl -s https://studio.mizan.market/a2a -H 'Content-Type: application/json' -d '{
  "jsonrpc": "2.0", "id": 1, "method": "message/send",
  "params": { "message": { "role": "user", "messageId": "m1",
              "parts": [ { "kind": "text", "text": "check mizan-flagship" } ] } } }'
```

Results are signed like every other MIZAN reply; verify with [`verify/`](../../verify/).
