"""Live tests against https://studio.mizan.market. Run: python3 -m pytest tests (or python3 tests/test_live.py)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import mizan_check as m  # noqa: E402

MODEL = "model:openai/gpt-oss-20b"


def test_check_try_me_signed_and_offline_verifiable():
    d = m.check("try-me")
    assert d["decision"] == "ALLOW" and d["evidence_rung"] in ("PROVEN", "RECORDED")
    assert m.verify_reply(d) is True
    assert m.verify_token(d["token"])["decision"] == "ALLOW"
    assert m.verify_message(d["pricing_message"])["tier"] in ("A", "B", "C", "D", "unrated")


def test_tampered_token_is_refused():
    t = m.check("try-me")["token"]
    h, p, s = t.split(".")
    try:
        m.verify_token(f"{h}.{p}.{s[::-1]}")
    except m.MizanError:
        return
    raise AssertionError("tampered token verified")


def test_rule_in_plain_words_allow_and_refuse():
    low = m.check(MODEL, rule="pass@1 at least 60% over at least 20 tasks")
    high = m.check(MODEL, rule="pass@1 at least 99% over at least 20 tasks")
    assert low["decision"] == "ALLOW" and high["decision"] == "REFUSE"
    assert high["clauses"][0]["met"] is False


def test_rule_hash_recomputes_locally():
    c = m.compile_rule("pass@1 at least 60% over at least 20 tasks")
    assert m.rule_hash(c["requirement"]) == c["hash"]


def test_guard_modes():
    seen = []
    enforce = m.guard(lambda payee, amt: ("paid", payee), mode="enforce", on_verdict=seen.append)
    assert enforce("try-me", 1) == ("paid", "try-me")
    try:
        enforce("unknown-seller.example", 1)
        raise AssertionError("enforce paid without ALLOW")
    except m.MizanRefused as e:
        assert e.verdict["decision"] == "REFUSE"
    advise = m.guard(lambda payee, amt: "paid", mode="advise", on_verdict=seen.append)
    assert advise("unknown-seller.example", 1) == "paid"
    assert [v["decision"] for v in seen] == ["ALLOW", "REFUSE", "REFUSE"]


def test_guard_fails_closed_when_unreachable():
    old = m.API
    m.API = "https://unreachable.invalid"
    try:
        g = m.guard(lambda *a: "paid", mode="enforce")
        try:
            g("try-me", 1)
            raise AssertionError("enforce paid while unreachable")
        except m.MizanRefused as e:
            assert e.verdict["decision"] == "UNVERIFIABLE"
        assert m.guard(lambda *a: "paid", mode="advise")("try-me", 1) == "paid"
    finally:
        m.API = old


def test_live_try_me_token_never_authorises_another_payee():
    t = m.check("try-me")["token"]
    assert m.bind_token(t, subject="try-me")["decision"] == "ALLOW"
    try:
        m.bind_token(t, subject="unknown-seller.example")
        raise AssertionError("a try-me ALLOW passed for another payee")
    except m.MizanError as e:
        assert "another payee" in str(e)


def test_live_default_bar_allow_never_passes_a_pinned_rule():
    strict = m.compile_rule("pass@1 at least 60% over at least 20 tasks")
    d = m.check("try-me")                                   # default bar: ALLOW, but about no rule
    try:
        m.bind_token(d["token"], subject="try-me", requirement_hash=strict["hash"])
        raise AssertionError("a default-bar ALLOW passed a pinned guard")
    except m.MizanError as e:
        assert "pinned rule" in str(e)
    r = m.check(MODEL, rule=strict["requirement"])          # the rule's own ALLOW carries its hash
    assert m.bind_token(r["token"], subject=MODEL, requirement_hash=strict["hash"])["requirement_hash"] == strict["hash"]


def test_live_guard_pinned_to_a_rule():
    words = "pass@1 at least 60% over at least 20 tasks"
    g = m.guard(lambda payee: "paid", mode="enforce", rule=words)
    assert g(MODEL) == "paid"
    try:
        g("try-me")   # try-me is ALLOW at the default bar but has no counted eval: REFUSE against this rule
        raise AssertionError("pinned guard paid on a different bar")
    except m.MizanRefused:
        pass


def test_enroll_requires_a_linked_origin():
    key = os.environ.get("MIZAN_TEST_KEY")
    if not key:
        return  # claiming creates a public identity; set MIZAN_TEST_KEY to run the payee path
    r = m.enroll(key, "https://api.example.com/v1/chat/completions")
    assert r.get("ok") is False and "link" in r.get("error", "")
    c = m.link_challenge(key, "https://api.example.com/v1/chat/completions")
    assert c["ok"] and c["nonce"] and "/.well-known/mizan-challenge" in c["how"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  ", name)
