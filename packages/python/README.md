# mizan-check (Python)

A signed yes or no on whether an AI agent's results are real, before you pay it. Standard library plus `cryptography` for offline signature checks.

```bash
pip install "git+https://github.com/muaviamohammed/mizan#subdirectory=packages/python"
```

## Payer side

```python
from mizan_check import check, verify_token, guard

d = check("try-me")                                   # free, no key
print(d["decision"], d["evidence_rung"])              # ALLOW PROVEN
verify_token(d["token"])                              # Ed25519 offline; raises if forged or expired

# your bar, in plain words, compiled and answered clause by clause
d = check("model:openai/gpt-oss-20b", rule="pass@1 at least 60% over at least 20 tasks")

# in your payment path: advise (always pays, logs the verdict) or enforce (pays only on a verified ALLOW)
pay = guard(my_pay_function, mode="enforce", on_verdict=print)
pay("try-me", 25)                                     # raises MizanRefused on REFUSE, timeout or bad signature
```

| Function | Does |
|---|---|
| `check(subject, rule=None, *, amount=None, key=None)` | `rule`: a published id `req_…@v`, plain words, or a rule object. Returns the signed reply. |
| `compile_rule(words)` / `rule_hash(requirement)` | Read a bar back; recompute its hash locally. |
| `verify_token(token)` | Offline Ed25519 check of the check token, plus expiry. Returns the payload. |
| `verify_message({message, signature})` | Offline check of a code-gate message, attestation or price message. |
| `verify_reply(body)` | Offline check of the signature on any JSON reply. |
| `guard(pay, mode="advise"\|"enforce", rule=None, on_verdict=None)` | Wrap your own pay function. MIZAN never holds or moves money. |

## Payee side: get counted

```python
from mizan_check import claim, link_challenge, link_complete, enroll

me = claim("my-agent")                                # {agent_id, api_key (shown once)}
ch = link_challenge(me["api_key"], "https://api.yours.example/v1/chat/completions")
# serve ch["nonce"] at https://api.yours.example/.well-known/mizan-challenge, then:
link_complete(me["api_key"], ch["challenge_id"])
enroll(me["api_key"], "https://api.yours.example/v1/chat/completions", adapter="openai")
```

What leaves your machine: the endpoint URL and the answers your endpoint gives to sealed tasks. What never does: your prompts, weights or code. MIZAN chooses when to run; every try is counted, pass or fail.

## Tests

```bash
python3 tests/test_live.py          # or: python3 -m pytest tests
```

Licence: Apache-2.0.
