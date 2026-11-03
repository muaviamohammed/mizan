"""A model-evaluation bar: the same counted record, two bars. Every attempt is counted, so the
score is first-try over all registered tasks, not the best of many tries."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..")); import _path  # noqa
from mizan_check import check

model = "model:openai/gpt-oss-20b"
for bar in ("pass@1 at least 60% over at least 20 tasks", "pass@1 at least 90% over at least 20 tasks"):
    v = check(model, rule=bar)
    c = v["clauses"][0]
    print(f"{v['decision']:<6} {bar:<45} grade {c['rung']}  {c['gap_step'] or ''}")
