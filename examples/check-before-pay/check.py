"""Check before you pay: one signed ALLOW or REFUSE, verified on this machine before any money moves.

    python3 check.py [subject]        # stdlib only; signature check needs: pip install cryptography
"""
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "verify", "python"))
from mizan_verify import DEFAULT_API, get_json, load_keys, verify_signed_body  # noqa: E402

subject = sys.argv[1] if len(sys.argv) > 1 else "mizan-flagship"
decision = get_json(f"{DEFAULT_API}/api/check/{urllib.parse.quote(subject, safe='')}")
signed = verify_signed_body(decision, load_keys())

print(f"subject:   {subject}")
print(f"decision:  {decision['decision']} ({decision.get('basis')}, rung {decision.get('evidence_rung') or 'none'})")
print("signature: " + {True: "✓ valid", False: "✗ INVALID", None: "· not checked (pip install cryptography)"}[signed])

if signed is False:
    sys.exit("unsigned or tampered answer: do not pay")
if decision["decision"] == "ALLOW":
    print("→ pay")  # your payment call goes here
else:
    print("→ hold payment")
    for r in decision.get("reasons") or []:
        print(f"   reason: {r}")
