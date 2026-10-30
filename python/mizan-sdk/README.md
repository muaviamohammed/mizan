# mizan-sdk (Python)

The MIZAN Python SDK. Standard library only; `pip install "mizan-sdk[verify]"` adds `cryptography` for offline Ed25519 checks.

```bash
pip install https://mizan.market/skill/mizan_sdk-0.8.0-py3-none-any.whl          # the published wheel
pip install "git+https://github.com/muaviamohammed/mizan#subdirectory=python/mizan-sdk"   # from this repo
```

```python
from mizan.x402guard import check, guard

d = check("mizan-flagship")             # one signed ALLOW or REFUSE, free, no key
print(d["decision"], d["basis"])

pay = guard(my_paying_get, mode="advise")   # inside an x402 payment; "enforce" pays only on ALLOW
```

| Module | What it does |
|---|---|
| `mizan.x402guard` | `check(subject)` and `guard(pay, mode=…)`: the check inside an x402 payment. Advise attaches the signed answer; enforce pays only on ALLOW and fails closed. |
| `mizan.gate` | `require_credential(...)`, `allocate_check(...)`, `verify_allocate_check(token)`: the gate a platform runs before listing, paying or allocating. Fails closed. |
| `mizan.receipt` | `verify_receipt(token)`: verify a signed receipt offline with the published key. |
| `mizan.staple` | Stapled receipts that verify with zero calls. |
| `mizan` | `prove(...)`, `verify(bundle)`, `find(...)`, `watch(...)`, `acts_for(...)`, `report_outcome(...)` and the rest of the API, plus the `mizan` CLI (`mizan check <subject>`, `mizan verify <file>`). |
| `mizan.importers` | Turn records exported from common platforms into positions for a private preview. |

Proving sends results or positions, never your model, code or prompts. The full API is described at [`openapi.json`](https://mizan.market/skill/openapi.json).

MIT licensed.
