"""Offline tests: the guard's binding rules, key pinning and message expiry. Tokens are signed here with a throwaway key.
Run: python3 -m pytest tests/test_offline.py"""
import base64, hashlib, json, os, sys, threading, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pytest  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

import mizan_check as m  # noqa: E402

SK, OTHER = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
PUB = base64.b64encode(SK.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
KEYS = {"keys": [{"key_id": "test", "alg": "Ed25519", "public_key_b64": PUB}]}
H = "a" * 64
b64u = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()  # noqa: E731


def tok(payload, sk=SK):
    h = b64u(json.dumps({"alg": "EdDSA", "kid": "test", "typ": "JWT"}).encode())
    p = b64u(json.dumps({"exp": time.time() + 3600, **payload}).encode())
    return f"{h}.{p}.{b64u(sk.sign(f'{h}.{p}'.encode()))}"


TRY_ME = {"sub": "track-btc-trend-4h-link2", "subject_as_given": "track-btc-trend-4h-link2", "subject_requested": "try-me", "decision": "ALLOW"}


def fake_check(reply):
    return lambda subject, rule=None, **kw: dict(reply(subject) if callable(reply) else reply)


def test_attack_try_me_allow_for_another_payee(monkeypatch):
    monkeypatch.setattr(m, "check", fake_check({"decision": "ALLOW", "token": tok(TRY_ME)}))
    paid = []
    g = m.guard(lambda payee: paid.append(payee), mode="enforce", keys=KEYS)
    with pytest.raises(m.MizanRefused) as e:
        g("evil-seller.example")
    assert paid == [] and "another payee" in e.value.verdict["not_verified_because"]
    g("try-me")   # the same token is fine for the subject it names
    assert paid == ["try-me"]


def test_attack_default_bar_allow_on_pinned_guard(monkeypatch):
    monkeypatch.setattr(m, "check", fake_check(lambda s: {"decision": "ALLOW", "token": tok({"subject_as_given": s, "decision": "ALLOW"})}))
    g = m.guard(lambda payee: "paid", mode="enforce", rule="req_strict@1#" + H, keys=KEYS)
    with pytest.raises(m.MizanRefused):
        g("seller.example")
    monkeypatch.setattr(m, "check", fake_check(lambda s: {"decision": "ALLOW", "token": tok(
        {"subject_as_given": s, "decision": "ALLOW", "requirement_ref": "req_strict@1", "requirement_hash": H})}))
    assert g("seller.example") == "paid"


@pytest.mark.parametrize("payload,sk,why", [
    ({**TRY_ME, "decision": "REFUSE"}, SK, "not ALLOW"),
    ({**TRY_ME, "exp": 1}, SK, "expired"),
    (TRY_ME, OTHER, "does not verify"),
])
def test_refused_tokens(payload, sk, why):
    with pytest.raises(m.MizanError, match=why):
        m.bind_token(tok(payload, sk), subject="try-me", keys=KEYS)


def test_json_says_allow_but_token_says_refuse(monkeypatch):
    monkeypatch.setattr(m, "check", fake_check({"decision": "ALLOW", "token": tok({**TRY_ME, "decision": "REFUSE"})}))
    with pytest.raises(m.MizanRefused):
        m.guard(lambda p: "paid", mode="enforce", keys=KEYS)("try-me")


def test_pinned_keys_never_fetch(tmp_path, monkeypatch):
    f = tmp_path / "mizan-keys.json"
    f.write_text(json.dumps(KEYS))
    monkeypatch.setenv("MIZAN_PINNED_KEYS", str(f))
    monkeypatch.setenv("MIZAN_PINNED_KEYS_SHA256", hashlib.sha256(f.read_bytes()).hexdigest())
    monkeypatch.setattr(m, "_req", lambda *a, **k: (_ for _ in ()).throw(AssertionError("fetched keys while pinned")))
    assert m.bind_token(tok(TRY_ME), subject="try-me")["decision"] == "ALLOW"
    monkeypatch.setenv("MIZAN_PINNED_KEYS_SHA256", "0" * 64)
    with pytest.raises(m.MizanError, match="does not match"):
        m.load_keys()


def _signed(msg, sk=SK):
    canon = json.dumps(msg, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return {"message": msg, "signature": b64u(sk.sign(canon))}


def test_attestation_expires_field_is_honoured():
    live = {"key_id": "test", "subject": "x", "met": True, "expires": int(time.time()) + 60}
    assert m.verify_message(_signed(live), keys=KEYS)["met"] is True
    with pytest.raises(m.MizanError, match="expired"):
        m.verify_message(_signed({**live, "expires": int(time.time()) - 1}), keys=KEYS)
    with pytest.raises(m.MizanError, match="expired"):
        m.verify_message(_signed({"key_id": "test", "expires_at": int(time.time()) - 1}), keys=KEYS)


def test_advise_never_holds_payment(monkeypatch):
    def slow(subject, rule=None, **kw):
        time.sleep(5)
        return {"decision": "ALLOW"}
    monkeypatch.setattr(m, "check", slow)
    seen = []
    g = m.guard(lambda p: "paid", mode="advise", keys=KEYS, on_verdict=seen.append)
    t0 = time.time()
    assert g("seller.example") == "paid" and time.time() - t0 < 2.0
    assert seen[0]["decision"] == "UNVERIFIABLE"
    g2 = m.guard(lambda p: "paid", mode="advise", keys=KEYS, advise_timeout=0.2)
    t0 = time.time()
    assert g2("seller.example") == "paid" and time.time() - t0 < 1.0
