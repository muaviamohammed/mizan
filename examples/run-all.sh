#!/bin/sh
# Run every quickstart, example and verifier against the live API. Exits non-zero on the first failure.
# Needs: Python 3.9+ with `cryptography`, Node 20+ (Node 22.6+ for the .ts quickstart).
set -eu
cd "$(dirname "$0")/.."
step() { printf '\n== %s\n' "$*"; }
step "quickstart · curl";        sh examples/quickstart/check.sh
step "quickstart · Python";      python3 examples/quickstart/check.py
step "quickstart · TypeScript";  node --experimental-strip-types --no-warnings examples/quickstart/check.ts
step "escrow release guard · advise";  python3 examples/escrow-release-guard/release.py
step "escrow release guard · enforce"; MIZAN_MODE=enforce python3 examples/escrow-release-guard/release.py
step "x402 payment check";       python3 examples/x402-payment-check/pay.py
step "marketplace listing gate"; python3 examples/marketplace-listing-gate/gate.py
step "agent-to-agent hire";      python3 examples/agent-hire/hire.py
step "model evaluation bar";     python3 examples/model-eval-bar/bar.py
step "verify a token offline";   python3 verify/verify_token.py
step "verify a ledger entry · Python"; python3 verify/verify_entry.py 388
step "verify a ledger entry · Node";   node verify/verify-entry.mjs
step "python package tests";     python3 packages/python/tests/test_live.py
printf '\nall examples ran against the live API\n'
