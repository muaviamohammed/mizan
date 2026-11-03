# The requirement language (the bar)

The relying party writes the bar. Plain words are compiled into an exact, versioned rule, read back for confirmation, and fixed by hash before anyone is checked against it. Words the compiler cannot bind are listed, never guessed.

## Lifecycle

```
plain words ──compile──▶ requirement + shown_back + unmatched + hash      (free, no key)
            ──publish──▶ req_…@1  (immutable; a change is @2)              (API key, confirm: true)
            ──check────▶ ALLOW / REFUSE, clause by clause
```

| Step | Call | Key |
|---|---|---|
| Compile | `POST /api/requirements/compile {"text": "…"}` | No |
| Publish | `POST /api/requirements {"text": "…", "confirm": true, "name"?: "…"}` | Yes |
| Read | `GET /api/requirements/{ref}` | No |
| Check, published | `GET /api/check/{subject}?requirement=req_…@v&requirement_hash=…` | No |
| Check, inline | `POST /api/check {"agent": "…", "requirement": {…}}` | No |
| Who meets it | `GET /api/requirements/{ref}/meeting` (only subjects that opted in) | No |
| What a subject meets | `GET /api/requirements/met-by/{subject}` | No |

Base URL `https://studio.mizan.market`. Structured JSON schema: <https://studio.mizan.market/app/schemas/requirement-rule-v2.schema.json>.

## The object

```json
{
  "name": "pass@1 at least 60% over at least 50 tasks, company domain",
  "all_of": [
    { "profile": "model-evaluation@1", "min_rung": "RECORDED",
      "bar": { "min_pass_at_1": 60.0, "min_tasks": 50 } },
    { "identity": { "kinds_any": ["dns"] } }
  ],
  "any_of": []
}
```

- `all_of` clauses must all hold; `any_of` clauses, when present, need one.
- A **profile clause** names a measure with its major version, the lowest grade accepted (`min_rung`) and the measure's own bars (minimum score, minimum count, minimum age and so on).
- An **identity clause** requires the subject to have linked one of the listed identity kinds by proof of control (`GET /api/link/kinds`).
- A **pricing clause** requires a [price signal](./price-signal.md) tier or score: `{"pricing": {"min_tier": "B"}}` or `{"pricing": {"min_score": 60}}`.

## Examples (read back by the live compiler)

| Words | Read back |
|---|---|
| `pass@1 at least 60% over at least 50 tasks` | Pay only if ALL of: What a model really scores: recorded, first-try pass rate (pass@1) at least 60%, over at least 50 committed tasks. |
| `pass@1 at least 60% over at least 50 tasks, company domain` | … ; identity linked by one of: dns. |
| `sharpe at least 1.0 and max drawdown under 25%` | Pay only if ALL of: What it really earned: proven, Sharpe after costs at least 1, max drawdown at most 25%. |
| `proven for 6 months` | Pay only if ALL of: What it really earned: proven, credential at least 180 days old (counted from its mint). |

Run them yourself: [`examples/model-eval-bar`](../examples/model-eval-bar/), [`examples/marketplace-listing-gate`](../examples/marketplace-listing-gate/).

## Hash rule

`hash = SHA-256` over the requirement object exactly as returned, serialised as JSON with keys sorted, no spaces (separators `,` and `:`) and non-ASCII escaped. `name` is part of the hashed object, so the same bars under two names have two hashes; the publish reply returns the stored hash.

```python
hashlib.sha256(json.dumps(requirement, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
```

## One rule, every surface

A published rule `req_…@v` renders as bindings that all carry the same rule id and hash (`GET /api/requirements/{ref}/bindings`, one as text at `/bindings/{kind}.txt`):

| Binding | Hook |
|---|---|
| `release` | Payment rails, escrow, settlement: a hold pins the rule; release only on a live ALLOW. |
| `payment` | x402: `accepts[i].extra.mizan = {requirement, requirement_hash, check}`; the payer checks the payee against that exact rule. A seller's declared field never grants ALLOW alone. |
| `listing` | Marketplaces and leaderboards: ALLOW lists, REFUSE hides and carries the proof request. |
| `deploy` | Agent platforms: one setting, `MIZAN_REQUIRE=req_…@v#<hash>`. |
| `questionnaire` | Due diligence: one plain-words clause with the verify URL. |
| `contract` | Any code gate: the seven-field [code-gate message](./signed-verdict.md), verified with no call out. |
| `reliance` | A second requirer accepts the attestation instead of re-checking ([reliance](./reliance.md)). |

A verdict at any hook settles the same immutable version.

## Rules

1. Read `shown_back` before publishing. If it does not say what you meant, change the words and compile again.
2. A published rule is immutable; a change is a new version, and checks name the exact version.
3. The rule decides the lowest grade it accepts.
