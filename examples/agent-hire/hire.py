"""Agent-to-agent hire: the hiring agent sets its bar, checks the candidate, keeps the signed token
as the reason it hired, and verifies that token on its own machine before committing."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..")); import _path  # noqa
from mizan_check import bind_token, check, compile_rule

candidate = "model:openai/gpt-oss-20b"
bar = compile_rule("pass@1 at least 60% over at least 20 tasks")
v = check(candidate, rule=bar["requirement"])
# Ed25519 against the published key, unexpired, ALLOW, about this candidate and this exact bar; raises otherwise
claims = bind_token(v["token"], subject=candidate, requirement_hash=bar["hash"]) if v["decision"] == "ALLOW" else {"check_id": v["check_id"], "exp": "-"}
print(f"{candidate}: {v['decision']} at grade {v['evidence_rung']}")
print("rule as read back:", v["requirement"]["shown_back"])
print(f"token signed, check {claims['check_id']}, valid until {claims['exp']}")
print("hire" if v["decision"] == "ALLOW" else "do not hire")
