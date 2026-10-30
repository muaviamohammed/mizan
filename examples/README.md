# Examples

Every example runs against the public API (`https://studio.mizan.market`) with no key and no account, and CI runs all of them on every push. Node 20+ and Python 3.9+; no dependencies beyond `cryptography` for the Python signature step and `jq` for the shell one.

| Example | What it shows | Run |
|---|---|---|
| [`check-before-pay`](./check-before-pay/) | An agent checks a counterparty before paying it, and verifies the signed answer on its own machine. | `./check.sh` · `node --experimental-strip-types check.ts` · `python3 check.py` |
| [`escrow-release-check`](./escrow-release-check/) | An escrow asks MIZAN before releasing a milestone. Advise mode: the release proceeds and the signed answer is attached; if MIZAN is unreachable, the release still proceeds (fail-open). `MIZAN_MODE=enforce` releases only on a verified ALLOW. | `python3 release.py` · `node release.mjs` |
| [`verify-ledger-entry`](./verify-ledger-entry/) | Verify any ledger entry: recompute it, fold it to the signed head (RFC 6962), check the Ed25519 head signature, apply the stamp coverage rule. In the browser or in Node. | open `index.html` · `node verify.mjs 388` |
| [`pin-a-requirement`](./pin-a-requirement/) | Write a bar in plain words, read it back, recompute its hash locally and pin it. Nothing is published. | `python3 pin.py` · `node pin.mjs` |

Run them all from the repo root:

```bash
sh examples/run-all.sh
```

Requests from these examples identify themselves with the `User-Agent` `mizan-examples/1 (+https://github.com/muaviamohammed/mizan)`.
