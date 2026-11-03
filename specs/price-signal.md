# The price signal

Beside every verdict, a signed, versioned price signal: a score out of 100, a tier (A, B, C, D or unrated) and a relative capacity multiplier. It is computed from the record alone by a published function anyone re-runs. MIZAN prices the record, never the asset; partners lend and insure. MIZAN never holds money.

Live page: <https://mizan.market/pricing-signal/> · exact function, hash and worked examples: `GET https://studio.mizan.market/api/pricing/function`.

## Calls

| Call | Returns |
|---|---|
| `GET /api/pricing/function` | `version`, `function_hash`, the `spec` (weights), plain words, worked examples. |
| `GET /api/pricing/{subject}[?requirement=req_…@v&requirement_hash=…]` | The signal for a subject, optionally scoped to a published rule. |
| `POST /api/pricing/verify {"message", "signature"}` | Verifies a price message. |
| every check reply | `price_signal` and `pricing_message`. |

`price_signal` carries `version, function_hash, score_0_100, tier, limit_units, confidence, inputs_used, caveats`.

## The function, in plain words

Only record fields enter: what was counted and its kind, the evidence grade, the bars met, the record's age, who already requires it, how recent checks went, the measures the record carries, and disputes on it. Nothing about the asset, the market or the future.

| Component | Up to | How |
|---|---|---|
| Grade | 30 | PROVEN 30 · RECORDED 18 · DECLARED 6 |
| Count | 25 | rising with log10 of the count, saturating at 10,000 |
| Age | 15 | linear, one year saturates |
| Bars met | 10 | share of the bar's clauses met |
| Requirers | 10 | 2.5 per requirer that proved a key or identity; never an anonymous claim or a test identity |
| Check history | 10 | ALLOW share of the last 90 days; neutral 5 when there is none |

Adjustments: drawdown over 25% −5 · worst bar under −15% −5 · pass@1 up to +5 · open disputes filed by an authenticated party −3 each, to −9 · upheld disputes −5 each, to −15. An overturned verdict, where MIZAN was wrong, never lowers the subject's score; an anonymous filing never counts. A REFUSE caps the score at 39 and the tier at D.

Tiers: **A** at 80 · **B** at 60 · **C** at 40 · **D** below.

## Unrated, never zero

No evidence grade, no known count, or fewer than 30 counts gives `unrated`, with the missing input named in `caveats`. An unknown is never scored as zero.

## Relative, never a currency

`limit_units` is a multiplier a partner applies to its own base line: A 1.0 · B 0.5 · C 0.25 · D 0.1 · unrated 0. It is not an amount, not a rate and not an offer.

## Versioning

`function_hash` = SHA-256 over the spec serialised with keys sorted, no spaces, ASCII. Every change is a new version with a new hash, written to the public ledger as a `pricing_function` entry, so a quote is tied to the version in force. Recompute any signal from the public reply fields; it must match.

## Requiring a tier

Add a pricing clause to a rule: `{"pricing": {"min_tier": "B"}}` or `{"pricing": {"min_score": 60}}`. Every binding of the rule honours it.

## Reading it offline

`pricing_message` is nine fields in canonical JSON with an Ed25519 signature ([signed verdict](./signed-verdict.md#2-signed-messages-code-gate-attestation-price)). Verify the signature, check `expires_at`, the `subject`, and the `function_hash` you accept, then apply your own bar to `tier` and `score_0_100`.

A price signal reads the record as it stands. It is not a forecast, not a rating of an asset and not an offer; the relying party keeps responsibility.
