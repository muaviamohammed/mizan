# AP2 and ACP: the integration point

AP2 (Agent Payments Protocol) and ACP (Agentic Commerce Protocol) define how an agent is authorised to pay and how a checkout completes. Neither says whether the party being paid earned it. MIZAN is the call that answers that, placed just before the commitment. There is no official integration or partnership with either protocol's steward; this is the documented call site.

## Where the call goes

| Protocol | Moment | Call | On ALLOW | On REFUSE |
|---|---|---|---|---|
| AP2 | Before the payment mandate is signed | `POST https://studio.mizan.market/api/check {"agent": payee, "amount": …, "currency": …}` | Sign the mandate; keep MIZAN's `token` with it as the reason. | Hold; send the `proof_request.forward` text to the payee. |
| ACP | Before the checkout is completed | `GET https://studio.mizan.market/api/check/{merchant}` (or POST with the amount) | Complete the checkout. | Hold, or complete in advise mode with the decision attached. |

Against your own bar, add `"requirement": "req_…@1"` (see [`specs/requirement-language.md`](../specs/requirement-language.md)).

## Sketch

```ts
const d = await (await fetch("https://studio.mizan.market/api/check", {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ agent: payee, amount, currency: "USD", purpose: "AP2 mandate" }),
})).json();
if (d.decision !== "ALLOW") return hold(d.proof_request?.forward);
mandate.evidence = { mizan_token: d.token };   // verifiable offline with the published key
await signMandate(mandate);
```

Verify `d` before relying on it: [`verify/js/mizan-verify.mjs`](../verify/js/mizan-verify.mjs) `verifySignedBody`. For advise versus enforce and fail-open versus fail-closed, see [`examples/escrow-release-check`](../examples/escrow-release-check/).
