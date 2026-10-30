"""Escrow release check, advise mode, fail-open.

Your escrow stays yours: MIZAN never holds or moves money. Before releasing a milestone payment,
ask MIZAN about the payee and attach the signed answer to your release record. In ADVISE mode the
release always proceeds (nothing breaks while most payees are still unproven); if MIZAN cannot be
reached within the timeout, the release proceeds and the record says "unverifiable" (fail-open).
Switch MODE to "enforce" to release only on a verified ALLOW (fail-closed).

    python3 release.py                # stdlib only; signature check needs: pip install cryptography
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "verify", "python"))
from mizan_verify import DEFAULT_API, USER_AGENT, load_keys, verify_signed_body  # noqa: E402

MODE = os.environ.get("MIZAN_MODE", "advise")  # "advise" (fail-open) or "enforce" (fail-closed)
TIMEOUT_S = 3.0


def check_payee(payee: str, amount: float, currency: str, api: str = DEFAULT_API) -> dict:
    """POST /api/check with the amount. Any failure becomes an 'unverifiable' answer, never an exception."""
    try:
        body = json.dumps({"agent": payee, "amount": amount, "currency": currency, "purpose": "escrow milestone release"}).encode()
        req = urllib.request.Request(api + "/api/check", data=body, headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            d = json.loads(r.read())
        signed = verify_signed_body(d, load_keys(api))
        return {"decision": d["decision"], "basis": d.get("basis"), "signed": signed, "check_id": d.get("check_id"),
                "token": d.get("token"), "proof_request": (d.get("proof_request") or {}).get("forward")}
    except Exception as e:  # network, timeout, bad JSON: advise mode must not break the release
        return {"decision": "UNVERIFIABLE", "basis": "unverifiable", "signed": None, "error": f"{type(e).__name__}: {e}"[:120]}


def release_milestone(escrow_id: str, payee: str, amount: float, currency: str = "USDC", api: str = DEFAULT_API) -> dict:
    answer = check_payee(payee, amount, currency, api)
    verified_allow = answer["decision"] == "ALLOW" and answer["signed"] is True  # enforce needs a checked signature
    release = verified_allow if MODE == "enforce" else True
    record = {"escrow": escrow_id, "payee": payee, "amount": amount, "currency": currency, "mode": MODE,
              "released": release, "mizan": answer}
    # your escrow release goes here, e.g. contract.release(escrow_id) when record["released"]
    return record


if __name__ == "__main__":
    cases = [
        ("esc_001", "mizan-flagship", 250.0, DEFAULT_API),            # a payee with a proven record
        ("esc_002", "seller.example", 500.0, DEFAULT_API),            # a payee with no record yet
        ("esc_003", "seller.example", 500.0, "https://unreachable.invalid"),  # MIZAN unreachable: fail-open
    ]
    for esc, payee, amount, api in cases:
        r = release_milestone(esc, payee, amount, api=api)
        m = r["mizan"]
        sig = {True: "signature ✓", False: "signature ✗", None: "no signature"}[m["signed"]]
        print(f"{esc}  payee={payee:<16} released={str(r['released']):<5}  mizan={m['decision']} ({m['basis']}, {sig})")
        if m.get("proof_request"):
            print(f"         forward to payee: {m['proof_request'][:110]}…")
        if m.get("error"):
            print(f"         {m['error']}")
