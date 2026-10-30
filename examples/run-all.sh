#!/bin/sh
# Run every example against the public MIZAN API. Exits non-zero on the first failure.
set -eu
cd "$(dirname "$0")"
NODE_TS="node --experimental-strip-types --no-warnings"
step() { printf '\n\033[1m▶ %s\033[0m\n' "$*"; }

step "check-before-pay · curl";        sh check-before-pay/check.sh
step "check-before-pay · TypeScript";  (cd check-before-pay && $NODE_TS check.ts)
step "check-before-pay · Python";      (cd check-before-pay && python3 check.py)
step "check-before-pay · a published refusal"; (cd check-before-pay && python3 check.py honest-fail-spy-sharadar)
step "escrow-release-check · Python (advise)"; (cd escrow-release-check && python3 release.py)
step "escrow-release-check · Node (advise)";   (cd escrow-release-check && node release.mjs)
step "verify-ledger-entry · newest";   (cd verify-ledger-entry && node verify.mjs)
step "verify-ledger-entry · #388";     (cd verify-ledger-entry && node verify.mjs 388)
step "verify-ledger-entry · Python";   python3 ../verify/python/mizan_verify.py 229
step "pin-a-requirement · Python";     (cd pin-a-requirement && python3 pin.py)
step "pin-a-requirement · Node";       (cd pin-a-requirement && node pin.mjs)
step "x402 guard · local stand-in seller"; (cd ../integrations/x402-guard && node demo.mjs)
printf '\nall examples ran\n'
