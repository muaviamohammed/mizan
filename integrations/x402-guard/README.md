# x402 guard

> x402 lets machines pay. MIZAN proves they earned it.

The check, inside the payment step. One unpaid request reads the seller's x402 terms (`accepts[].payTo`); MIZAN checks the wallet being paid and the seller's host; then the payment proceeds.

| Mode | On ALLOW | On REFUSE | On network error |
|---|---|---|---|
| `advise` (default) | pays | pays; the signed decision goes to `onDecision` and the `X-Mizan-Decision` response header, and the payment request carries `X-Mizan-Proof-Request` so the seller learns how to prove itself | pays (fail-open) |
| `enforce` | pays | throws `MizanRefused` (with `proofRequest`); nothing is paid | throws; nothing is paid (fail-closed) |

Start in advise mode so nothing breaks while most sellers are unproven; switch to enforce when you are ready. A decision is about the counterparty's record, never advice about the purchase; you keep responsibility. MIZAN never holds or routes funds. A seller's own declaration never binds alone: a stapled receipt counts only when it is bound to the payee or host.

## JavaScript (zero dependencies)

```js
import { guardFetch } from "./mizan-x402-guard.mjs";      // or https://mizan.market/skill/mizan-x402-guard.mjs (Deno, browsers)
const pay = guardFetch(fetchWithPayment, { mode: "advise", onDecision: (d) => console.log(d.decision) });
const res = await pay("https://seller.example/api/thing");  // checked, then paid
```

`fetchWithPayment` is any paying fetch, for example `wrapFetchWithPayment` from the x402 SDK. Try it with no wallet against a stand-in seller: `node demo.mjs`.

## Python (stdlib only)

```python
from mizan.x402guard import guard            # python/mizan-sdk
pay = guard(my_paying_get, mode="advise")
```

## Files

- [`mizan-x402-guard.mjs`](./mizan-x402-guard.mjs): `guardFetch`, `check`, `MizanRefused`.
- [`mizan-receipt.mjs`](./mizan-receipt.mjs): offline verification of stapled receipts (zero calls).
- [`demo.mjs`](./demo.mjs): advise and enforce against a local 402 seller.
- Platforms: the require kit adds the Proven / Refused / Unproven label next to every agent: <https://mizan.market/require/>.
