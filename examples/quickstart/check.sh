#!/bin/sh
# 60 seconds: one free, keyless check. Prints the decision and its evidence grade.
curl -s https://studio.mizan.market/api/check/try-me \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["decision"], d["evidence_rung"], d["check_id"])'
