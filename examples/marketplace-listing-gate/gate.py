"""Marketplace listing gate: a candidate goes live only when its record meets the bar you wrote.
ALLOW lists; REFUSE hides and returns a proof request to send the seller."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..")); import _path  # noqa
from mizan_check import check, compile_rule

bar = compile_rule("pass@1 at least 60% over at least 20 tasks")
print("bar:", bar["shown_back"], "\nhash:", bar["hash"])
for candidate in ["model:openai/gpt-oss-20b", "unknown-agent.example"]:
    v = check(candidate, bar["requirement"])
    action = "LIST" if v["decision"] == "ALLOW" else "HIDE"
    print(f"{action}  {candidate:<28} {v['decision']}  {'bar met' if action == 'LIST' else 'proof request: ' + str((v.get('proof_request') or {}).get('url'))}")
