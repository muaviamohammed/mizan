"""Escrow release guard. Advise mode: the release always proceeds and the signed verdict is logged.
MIZAN_MODE=enforce releases only on an ALLOW whose token verifies offline (fail-closed)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..")); import _path  # noqa
from mizan_check import guard, MizanRefused

def release(payee, amount):                      # your escrow's own release call goes here
    return f"released {amount} USDC to {payee}"

log = lambda v: print(f"  verdict {v['decision']:<12} signed token verified: {v['token_verified']}")
safe_release = guard(release, mode=os.environ.get("MIZAN_MODE", "advise"), on_verdict=log)
for payee in ["try-me", "unknown-seller.example"]:
    try:
        print(safe_release(payee, 250))
    except MizanRefused as e:
        print("  held, nothing released:", e.verdict["decision"])
