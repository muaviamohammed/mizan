#!/bin/sh
# Check a counterparty before your agent pays it. Free, no key, no account.
#   ./check.sh                    # a subject with a proven record
#   ./check.sh seller.example     # anything: agent id, domain, wallet, endpoint, ERC-8004 id
set -eu
SUBJECT="${1:-mizan-flagship}"
UA="mizan-examples/1 (+https://github.com/muaviamohammed/mizan)${MIZAN_CI:+ ci}"

curl -fsS -A "$UA" "https://studio.mizan.market/api/check/$SUBJECT" \
  | jq '{decision, basis, evidence_rung, credential, signed_by: .provenance.signature.key_id}'
