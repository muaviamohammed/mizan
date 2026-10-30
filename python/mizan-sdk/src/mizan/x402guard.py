"""Check before your agent pays: MIZAN's allocate-check inside the x402 payment step. Stdlib only.

    from mizan.x402guard import guard
    pay = guard(my_x402_paying_get)                 # any callable that performs the paid request: pay(url, **kw)
    resp = pay("https://seller.example/api/thing")  # MIZAN checks the payee first, then your function pays

How it works: one unpaid request to the URL returns HTTP 402 with the seller's payment terms (x402 `accepts`,
including `payTo`, the address that would receive the money). MIZAN runs the allocate-check on that payee
and on the seller's host. Then:

  mode="advise"  (default) your payment proceeds; the signed decision is passed to on_decision and returned
                 on the wrapper's .last_decision. Use this while most sellers are unproven.
  mode="enforce" payment proceeds only on ALLOW. REFUSE raises MizanRefused and nothing is paid.

Fail closed means: in enforce mode a network error, an unreadable 402 or a timeout is a REFUSE.
If the URL does not answer 402 (free, or already paid), the guard steps aside and calls your function.
A MIZAN decision is about the counterparty's credential, never advice about the purchase; you keep responsibility.
On REFUSE the decision carries proof_request {url, forward}: send it to the seller; when they pass, your next check is ALLOW.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

STUDIO = "https://studio.mizan.market"


class MizanRefused(RuntimeError):
    def __init__(self, decision: dict):
        self.decision = decision
        why = "; ".join((decision.get("reasons") or [])[:2]) or "no ALLOW"
        pr = decision.get("proof_request") or {}
        self.proof_request = pr or None   # forward pr["forward"] or pr["url"] to the seller; re-check when it is PROVEN
        super().__init__(f"MIZAN refused payment to {decision.get('subject')}: {why}" + (f". Ask them to prove it: {pr['url']}" if pr.get("url") else ""))


def _payment_terms(url: str, method: str = "GET", timeout: float = 10.0):
    """Return (payTo, network, terms) from the seller's 402, or None if the URL does not ask for payment."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "mizan-x402guard/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return None                       # 2xx: nothing to pay
    except urllib.error.HTTPError as e:
        if e.code != 402:
            return None
        stapled_hdr = e.headers.get("X-Mizan-Receipt") if e.headers else None
        try:
            body = json.loads(e.read() or b"{}")
        except Exception:
            body = {}
    accepts = body.get("accepts") or []
    first = dict(accepts[0]) if accepts else {}
    if stapled_hdr:
        first["_stapled_header"] = stapled_hdr
    return first.get("payTo"), first.get("network"), first


def _declared_credential(terms) -> str | None:
    """Seller-side convention (MIZAN x402 extension v1): accepts[i].extra.mizan = {"credential": "<id>"}."""
    try:
        m = ((terms or {}).get("extra") or {}).get("mizan") or {}
        c = m.get("credential") if isinstance(m, dict) else None
        return str(c).strip() or None if c else None
    except Exception:
        return None


def check(subject: str, *, amount=None, currency: str = "USDC", purpose: str = "x402 payment",
          policy_id: str | None = None, timeout: float = 15.0) -> dict:
    """The allocate-check on one subject (wallet, host, credential, agent id). Network failure → REFUSE."""
    body = {"agent": subject, "currency": currency, "purpose": purpose}
    if amount is not None:
        body["amount"] = amount
    if policy_id:
        body["policy_id"] = policy_id
    try:
        req = urllib.request.Request(STUDIO + "/api/allocate-check", data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": "mizan-x402guard/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read())
    except Exception as e:  # fail closed
        d = {"decision": "REFUSE", "reasons": [f"unverifiable: {str(e)[:120]}"]}
    d["subject"] = subject
    return d


def guard(pay, *, mode: str = "advise", on_decision=None, policy_id: str | None = None, also_check_host: bool = True):
    """Wrap any paying callable pay(url, **kw). Returns a callable with the same signature and a .last_decision."""
    if mode not in ("advise", "enforce"):
        raise ValueError("mode must be 'advise' or 'enforce'")

    def wrapped(url, *args, **kw):
        method = kw.get("method", "GET")
        try:
            terms = _payment_terms(url, method)
        except Exception as e:
            terms = ("", None, {"error": str(e)[:120]})
        if terms is None:
            wrapped.last_decision = {"decision": "SKIPPED", "reasons": ["no 402: nothing to pay"], "subject": url}
            return pay(url, *args, **kw)
        pay_to, network, raw = terms
        # Stapled proof first: verified locally, zero calls to MIZAN; must be bound to the payee (or host).
        stapled = (((raw or {}).get("extra") or {}).get("mizan") or {}).get("receipt") if isinstance(((raw or {}).get("extra") or {}).get("mizan"), dict) else None
        stapled = stapled or (raw or {}).get("_stapled_header")
        if stapled:
            from mizan.receipt import verify_receipt
            for ident in [pay_to, urllib.parse.urlparse(url).netloc if also_check_host else None]:
                if not ident:
                    continue
                v = verify_receipt(stapled, identity=ident)
                if v.get("allow"):
                    best = {"decision": "ALLOW", "stapled": True, "subject": ident, "credential": v.get("credential"), "reasons": [], "verified": v.get("reason"), "network": network}
                    wrapped.last_decision = best
                    if on_decision:
                        on_decision(best)
                    return pay(url, *args, **kw)
        decisions = []
        declared = _declared_credential(raw)
        declared_result = check(declared, policy_id=policy_id) if declared else None
        if pay_to:
            decisions.append(check(pay_to, policy_id=policy_id))
        if also_check_host:
            decisions.append(check(urllib.parse.urlparse(url).netloc, policy_id=policy_id))
        if not decisions:
            decisions.append({"decision": "REFUSE", "reasons": ["402 carried no payTo"], "subject": url})
        allow = any(d.get("decision") == "ALLOW" for d in decisions)
        best = next((d for d in decisions if d.get("decision") == "ALLOW"), decisions[0])
        best["checked"] = [d.get("subject") for d in decisions]
        if declared:
            # A seller-declared credential never grants ALLOW by itself: anyone can paste someone else's id.
            # It counts only through the payee or host check, which binds it to who is actually being paid.
            best["declared_by_seller"] = {"credential": declared, "decision": (declared_result or {}).get("decision"),
                                          "counts": "only when the payee or host check resolves to it"}
        best["network"] = network
        wrapped.last_decision = best
        if on_decision:
            on_decision(best)
        if mode == "enforce" and not allow:
            raise MizanRefused(best)
        return pay(url, *args, **kw)

    wrapped.last_decision = None
    return wrapped
