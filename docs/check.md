[← README](../README.md) · [Check](./check.md) · [How it works](./how-it-works.md) · [Get counted](./get-counted.md) · [Payment path](./payment-path.md) · [FAQ](./faq.md)

# Check before you pay: 60 seconds, free, no key

```bash
curl -s https://studio.mizan.market/api/check/try-me
# {"decision": "ALLOW", "evidence_rung": "PROVEN", "token": "eyJhbGciOiJFZERTQSIs…", "explain": "…", "next": {…}, …}
```

```python
import json, urllib.request

d = json.load(urllib.request.urlopen("https://studio.mizan.market/api/check/try-me"))
print(d["decision"], d["evidence_rung"])      # ALLOW PROVEN
if d["decision"] != "ALLOW":
    raise SystemExit("do not pay")
```

```ts
const d = await (await fetch("https://studio.mizan.market/api/check/try-me")).json();
console.log(d.decision, d.evidence_rung);     // ALLOW PROVEN
if (d.decision !== "ALLOW") throw new Error("do not pay");
```

`try-me` is MIZAN's sandbox subject: a stable, proven record every integrator checks first. Replace it with whoever you are about to pay: an agent id, a domain, an API, MCP or A2A endpoint, a model (`model:<org>/<name>`), or a wallet. Every reply is signed; [`verify/`](../verify/) checks the signature on your machine without calling MIZAN.

Now set your own bar, in plain words:

```python
from mizan_check import check            # pip install "git+https://github.com/muaviamohammed/mizan#subdirectory=packages/python"

d = check("model:openai/gpt-oss-20b", rule="pass@1 at least 60% over at least 20 tasks")
print(d["decision"], d["requirement"]["shown_back"])
```
