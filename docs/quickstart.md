# Quickstart

## 30 seconds: one check

```bash
curl -s https://studio.mizan.market/api/check/mizan-flagship | jq '{decision, basis, evidence_rung}'
```

```json
{ "decision": "ALLOW", "basis": "proven", "evidence_rung": "PROVEN" }
```

Free, no key, no account. Try a subject with nothing proven (`seller.example`) to see `REFUSE` with basis `no_record`, and MIZAN's own published refusal (`honest-fail-spy-sharadar`) to see `REFUSE` with basis `evidence_against`.

## 2 minutes: trust nothing

The answer is signed. Check it on your machine before you rely on it:

```bash
git clone https://github.com/muaviamohammed/mizan && cd mizan
node --experimental-strip-types examples/check-before-pay/check.ts
python3 examples/check-before-pay/check.py          # pip install cryptography for the signature step
```

## 5 minutes: put it in the payment path

Pick the surface your agent already speaks.

**MCP (no install).** Add the remote server; the agent gets `check`, `prove` and `more`.

```bash
claude mcp add --transport http mizan https://studio.mizan.market/mcp
```

```json
{ "mcpServers": { "mizan": { "url": "https://studio.mizan.market/mcp" } } }
```

**x402.** Wrap the paying fetch. Advise mode pays and attaches the signed answer; enforce pays only on ALLOW.

```js
import { guardFetch } from "./integrations/x402-guard/mizan-x402-guard.mjs";
const pay = guardFetch(fetchWithPayment, { mode: "advise" });
```

**Python.**

```bash
pip install https://mizan.market/skill/mizan_sdk-0.8.0-py3-none-any.whl
```

```python
from mizan.x402guard import check
if check(payee)["decision"] != "ALLOW":
    hold_payment()
```

**Your own bar.** Write it in plain words, read it back, pin its hash: [`examples/pin-a-requirement`](../examples/pin-a-requirement/). Then check against it with `"requirement": "req_…@1"`.

**Escrow or payouts.** [`examples/escrow-release-check`](../examples/escrow-release-check/): advise first, enforce when ready.

## Next

- Prove your own record without revealing the method: <https://mizan.market/claims/> and `prove()` over MCP.
- Every endpoint: [`openapi.json`](https://mizan.market/skill/openapi.json).
