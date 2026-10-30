# Requirement language

The buyer writes the bar. A requirement is plain words compiled into a versioned rule, read back for confirmation, and fixed by hash before anyone is checked against it. Words the compiler cannot bind are listed, never guessed.

## Lifecycle

```
plain words ──compile──▶ requirement object + shown_back + unmatched + hash
            ──confirm──▶ publish (API key, confirm: true) ──▶ req_…@1  (immutable; edits make @2)
            ──check────▶ check(subject, requirement="req_…@1") ──▶ ALLOW / REFUSE, clause by clause
```

| Step | Call | Key needed |
|---|---|---|
| Compile | `POST https://studio.mizan.market/api/requirements/compile {"text": "…"}` | No |
| Publish | `POST https://studio.mizan.market/api/requirements {"text": "…", "confirm": true, "name"?: "…"}` | Yes (`Authorization: Bearer mzn_…`) |
| Read | `GET https://studio.mizan.market/api/requirements/{ref}` | No |
| Check | `GET https://studio.mizan.market/api/check/{subject}?requirement=req_…@1`, `POST /api/check {"agent": "…", "requirement": "req_…@1"}` or MCP `check(agent, requirement=…)` | No |
| Who meets it | `GET https://studio.mizan.market/api/requirements/{ref}/meeting` | No |

## The object

```json
{
  "name": "only agents proven for 6 months, forward only, with a verified company domain",
  "all_of": [
    { "profile": "earned-performance@1", "min_rung": "PROVEN",
      "bar": { "min_age_days": 180, "forward_only": true } },
    { "identity": { "kinds_any": ["dns"] } }
  ],
  "any_of": []
}
```

- `all_of` clauses must all hold; `any_of` clauses, when present, need one to hold.
- A **profile clause** names a claim profile with its version (`profile@major`), the lowest acceptable rung (`min_rung`) and the profile's own bars.
- An **identity clause** requires the subject to have linked one of the listed identity kinds by proof of control (`GET https://studio.mizan.market/api/link/kinds`).
- Profiles and their bars: `GET https://studio.mizan.market/api/profiles`.

The compile reply also returns `shown_back` (the rule read back in plain words), `unmatched` (words that were not used) and `publishable`.

## Hash rule

`hash = SHA-256` over the requirement object exactly as returned, serialised as JSON with keys sorted, no spaces (separators `,` and `:`) and **non-ASCII escaped** (`\uXXXX`). `name` is part of the hashed object, so the same bars under two names have two hashes. Python:

```python
hashlib.sha256(json.dumps(requirement, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
```

[`examples/pin-a-requirement`](../examples/pin-a-requirement/) recomputes the hash locally in Python and JavaScript, checks that compiling is deterministic, and prints the value to pin in your code.

## Rules

1. Read `shown_back` before publishing. If it does not say what you meant, edit the words and compile again.
2. A published requirement is immutable. A change is a new version; checks name the exact version (`req_…@N`).
3. A requirement decides the rung it accepts. Without a requirement, ALLOW needs a passing credential in good standing for the subject.
