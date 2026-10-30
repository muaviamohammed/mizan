# Pin a requirement

The buyer writes the bar. Compile plain words into a rule, read it back, recompute its hash on your machine and pin that hash in your code, so the bar you check against is exactly the bar you read.

```bash
python3 pin.py                                   # or: node pin.mjs
python3 pin.py "only agents proven for 6 months, forward only, with a verified company domain"
```

```
read back:   Pay only if ALL of: What it really earned: proven, forward record after the Bitcoin seal of at least 180 days, forward record only (hindsight excluded); identity linked by one of: dns.
unmatched:   none (every word was used)
hash (API):  d515aac10ad460a5…
hash (here): d515aac10ad460a5…  ✓ match
recompiled:  ✓ same hash, deterministic
```

The script exits non-zero if any word was not used; edit the words and compile again. **Nothing is published.** Publishing (`POST /api/requirements` with `confirm: true`) needs an API key and is a deliberate, separate step; a published requirement is immutable and checked by reference (`req_…@1`). Rules: [`specs/requirement-language.md`](../../specs/requirement-language.md).
