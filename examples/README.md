# Examples

Each example is a few lines against the live API (`https://studio.mizan.market`): no key, no account. Python 3.9+ with `cryptography`; the TypeScript quickstart needs Node 22.6+ (`--experimental-strip-types`) or any TypeScript runner.

| Example | Shows | Run |
|---|---|---|
| [`quickstart`](./quickstart/) | One check, three languages. | `sh check.sh` · `python3 check.py` · `node --experimental-strip-types check.ts` |
| [`escrow-release-guard`](./escrow-release-guard/) | Advise mode: the release always proceeds and the signed verdict is logged. `MIZAN_MODE=enforce` releases only on a verified ALLOW. | `python3 release.py` |
| [`x402-payment-check`](./x402-payment-check/) | Check the `payTo` in a seller's 402 terms before signing the payment. | `python3 pay.py` |
| [`marketplace-listing-gate`](./marketplace-listing-gate/) | A plain-words bar; ALLOW lists, REFUSE hides with a proof request. | `python3 gate.py` |
| [`agent-hire`](./agent-hire/) | One agent hires another on a bar, and verifies the signed token itself. | `python3 hire.py` |
| [`model-eval-bar`](./model-eval-bar/) | The same counted record against two bars: ALLOW, then REFUSE with the gap. | `python3 bar.py` |
| [`get-counted`](./get-counted/) | The payee side: claim, link your endpoint, enrol. | `python3 get_counted.py <your endpoint>` |

Run every example and verifier at once (CI does this daily):

```bash
sh examples/run-all.sh
```
