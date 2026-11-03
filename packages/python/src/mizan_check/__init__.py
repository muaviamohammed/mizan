"""mizan-check: a signed yes or no on whether an AI agent's results are real, before you pay it.

A thin client for the public MIZAN API (https://studio.mizan.market). Standard library only;
offline signature checks use `cryptography` (installed with this package).

    from mizan_check import check, verify_token, guard

    d = check("try-me")                                   # free, no key
    d["decision"], d["evidence_rung"]                     # "ALLOW", "PROVEN"
    verify_token(d["token"])                              # Ed25519, offline, raises if forged or expired

    d = check("model:openai/gpt-oss-20b", rule="pass@1 at least 60% over at least 20 tasks")

Payer side: check, guard. Payee side: claim, link_challenge, link_complete, enroll.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

__all__ = [
    "API", "MizanError", "MizanRefused",
    "check", "compile_rule", "rule_hash", "verify_token", "verify_reply", "verify_message", "load_keys",
    "guard", "claim", "link_challenge", "link_complete", "enroll",
]
__version__ = "0.1.0"

API = os.environ.get("MIZAN_API", "https://studio.mizan.market")
USER_AGENT = f"mizan-check-py/{__version__} (+https://github.com/muaviamohammed/mizan)"


class MizanError(RuntimeError):
    """The API answered with an error, or could not be reached."""


class MizanRefused(RuntimeError):
    """Raised by guard(mode="enforce") when there is no verified ALLOW. Nothing was paid."""

    def __init__(self, verdict: dict):
        self.verdict = verdict
        self.proof_request = verdict.get("proof_request")
        super().__init__(f"MIZAN: {verdict.get('decision', 'REFUSE')} for {verdict.get('subject', '?')}: "
                         f"{verdict.get('explain') or verdict.get('error') or 'no verified ALLOW'}")


# ---------------------------------------------------------------- HTTP

def _req(method: str, path: str, body: dict | None = None, key: str | None = None, timeout: float = 20) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code >= 500:
            raise MizanError(f"HTTP {e.code} on {path}: service unavailable") from e
        try:
            return json.loads(e.read())          # MIZAN errors are JSON with explain + next
        except Exception:
            raise MizanError(f"HTTP {e.code} on {path}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise MizanError(f"unreachable: {e}") from e


# ---------------------------------------------------------------- rules (the bar)

def compile_rule(words: str) -> dict:
    """Plain words in, an exact rule back: {requirement, shown_back, unmatched, hash, publishable}. Free, no key."""
    return _req("POST", "/api/requirements/compile", {"text": words})


def rule_hash(requirement: dict) -> str:
    """Recompute a rule's hash locally: SHA-256 over canonical JSON (keys sorted, no spaces, ASCII)."""
    return hashlib.sha256(json.dumps(requirement, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


# ---------------------------------------------------------------- the check

def check(subject: str, rule: str | dict | None = None, *, amount: float | None = None, currency: str = "USD",
          purpose: str = "", key: str | None = None, timeout: float = 20) -> dict:
    """One signed ALLOW or REFUSE for `subject` (an agent id, domain, endpoint, model:<org>/<name>, wallet...).

    rule: None (default bar), a published rule id "req_...@v", plain words (compiled first),
    or a rule object as returned by compile_rule()["requirement"].
    """
    if rule is None and amount is None and not purpose:
        d = _req("GET", "/api/check/" + urllib.parse.quote(subject, safe=":@"), key=key, timeout=timeout)
    elif isinstance(rule, str) and rule.startswith("req_"):
        q = urllib.parse.urlencode({"requirement": rule})
        d = _req("GET", "/api/check/" + urllib.parse.quote(subject, safe=":@") + "?" + q, key=key, timeout=timeout)
    else:
        body: dict[str, Any] = {"agent": subject, "currency": currency}
        if amount is not None:
            body["amount"] = amount
        if purpose:
            body["purpose"] = purpose
        if isinstance(rule, str):
            c = compile_rule(rule)
            if c.get("unmatched") or not c.get("requirement"):
                raise MizanError(f"rule not understood: {c.get('unmatched') or c.get('refusal')}")
            rule = c["requirement"]
        if isinstance(rule, dict):
            body["requirement"] = rule
        d = _req("POST", "/api/check", body, key=key, timeout=timeout)
    if "decision" not in d:
        raise MizanError(d.get("explain") or d.get("error") or "no decision in reply")
    return d


# ---------------------------------------------------------------- offline verification

_KEYS: dict | None = None


def load_keys(refresh: bool = False) -> dict:
    """The published keys: https://studio.mizan.market/.well-known/mizan-keys.json (cached per process)."""
    global _KEYS
    if _KEYS is None or refresh:
        _KEYS = _req("GET", "/.well-known/mizan-keys.json")
    return _KEYS


def _ed25519(key_id: str, message: bytes, sig: bytes, keys: dict | None = None) -> bool:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    keys = keys or load_keys()
    k = next((k for k in keys["keys"] if k.get("alg") == "Ed25519" and k.get("key_id") == key_id), None)
    if k is None:
        return False
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(k["public_key_b64"])).verify(sig, message)
        return True
    except InvalidSignature:
        return False


def _b64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def verify_token(token: str, *, keys: dict | None = None, now: float | None = None) -> dict:
    """Verify a check token (compact JWS, EdDSA) offline. Returns its payload; raises MizanError if invalid or expired."""
    try:
        h, p, s = token.split(".")
        header = json.loads(_b64u(h))
        payload = json.loads(_b64u(p))
    except Exception as e:
        raise MizanError("not a MIZAN token") from e
    if header.get("alg") != "EdDSA" or not _ed25519(header.get("kid", ""), f"{h}.{p}".encode(), _b64u(s), keys):
        raise MizanError("signature does not verify against the published key")
    if payload.get("exp", 0) < (now or time.time()):
        raise MizanError("token expired")
    return payload


def verify_message(signed: dict, *, keys: dict | None = None, now: float | None = None) -> dict:
    """Verify a signed message object {message, signature, ...}: pricing_message, contract_message, attestation."""
    msg = signed["message"]
    canon = json.dumps(msg, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    if not _ed25519(msg["key_id"], canon, _b64u(signed["signature"]), keys):
        raise MizanError("signature does not verify against the published key")
    if msg.get("expires_at", float("inf")) < (now or time.time()):
        raise MizanError("message expired")
    return msg


def verify_reply(body: dict, *, keys: dict | None = None) -> bool:
    """Every JSON reply is signed: Ed25519 over canonical JSON of the body without provenance.signature."""
    sig = (body.get("provenance") or {}).get("signature")
    if not sig:
        return False
    copy = dict(body)
    copy["provenance"] = {k: v for k, v in body["provenance"].items() if k != "signature"}
    msg = json.dumps(copy, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if sig.get("canonical_sha256") and hashlib.sha256(msg).hexdigest() != sig["canonical_sha256"]:
        return False
    return _ed25519(sig["key_id"], msg, base64.b64decode(sig["sig_b64"]), keys)


# ---------------------------------------------------------------- in your payment path

def guard(pay: Callable[..., Any], *, mode: str = "advise", rule: str | dict | None = None,
          on_verdict: Callable[[dict], None] | None = None, timeout: float = 5) -> Callable[..., Any]:
    """Wrap your own pay(payee, *args, **kw). MIZAN never holds or moves the money.

    advise  : always pays; the verdict (or UNVERIFIABLE) goes to on_verdict for your log.
    enforce : pays only on an ALLOW whose token verifies offline; REFUSE, error, timeout,
              bad signature or expiry raise MizanRefused and nothing is paid (fail-closed).
    """
    if mode not in ("advise", "enforce"):
        raise ValueError('mode must be "advise" or "enforce"')

    def guarded(payee: str, *args, **kw):
        try:
            reply = check(payee, rule, timeout=timeout)
            ok = bool(reply.get("token")) and bool(verify_token(reply["token"]))
            v = {"subject": payee, "decision": reply["decision"], "evidence_rung": reply.get("evidence_rung"),
                 "token_verified": ok, "token": reply.get("token"), "check_id": reply.get("check_id"),
                 "explain": reply.get("explain"), "proof_request": reply.get("proof_request"), "reply": reply}
        except Exception as e:  # network, timeout, forged or expired token
            v = {"subject": payee, "decision": "UNVERIFIABLE", "error": str(e)[:200], "token_verified": False}
        if on_verdict:
            on_verdict(v)
        if mode == "enforce" and not (v["decision"] == "ALLOW" and v["token_verified"]):
            raise MizanRefused(v)
        return pay(payee, *args, **kw)

    return guarded


# ---------------------------------------------------------------- payee side: get counted

def claim(name: str) -> dict:
    """Claim an identity: {agent_id, api_key (shown once), listing}. No account, no email."""
    return _req("POST", "/api/agents/claim", {"name": name})


def link_challenge(key: str, endpoint: str) -> dict:
    """Start proving you control an endpoint's origin. Serve reply["nonce"] at https://<host>/.well-known/mizan-challenge."""
    return _req("POST", "/api/link/challenge", {"identifier": endpoint}, key=key)


def link_complete(key: str, challenge_id: str) -> dict:
    """Finish the link once the nonce is served (web origins need no signature)."""
    return _req("POST", "/api/link/complete", {"challenge_id": challenge_id}, key=key)


def enroll(key: str, url: str, *, adapter: str = "openai", model: str | None = None, label: str | None = None) -> dict:
    """Enrol a linked endpoint for counted evaluation. adapter: openai (chat completions), mcp or a2a."""
    body: dict[str, Any] = {"url": url, "adapter": adapter}
    if model:
        body["model"] = model
    if label:
        body["label"] = label
    return _req("POST", "/api/eval/enroll", body, key=key)
