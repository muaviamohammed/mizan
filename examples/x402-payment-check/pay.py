"""x402: before paying a 402, check the payee named in the seller's PaymentRequired terms.
The seller may name the bar it meets in accepts[i].extra.mizan; a declared field never grants ALLOW alone."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..")); import _path  # noqa
from mizan_check import check, verify_token

payment_required = {  # what a seller's 402 carries (x402 PaymentRequired), trimmed
    "accepts": [{"scheme": "exact", "network": "base", "payTo": "try-me", "maxAmountRequired": "10000",
                 "extra": {"mizan": {"check": "https://studio.mizan.market/api/check/try-me"}}}]}
payee = payment_required["accepts"][0]["payTo"]
v = check(payee)
ok = v["decision"] == "ALLOW" and verify_token(v["token"])["sub"]
print(f"payee {payee}: {v['decision']} ({v['evidence_rung']}), token verified offline: {bool(ok)}")
print("sign the x402 payment" if ok else f"do not sign; forward: {(v.get('proof_request') or {}).get('url')}")
