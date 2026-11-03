# The check API

One question before money moves: does this counterparty's record meet my bar? One signed answer: ALLOW or REFUSE. Free, no key, no account.

Base URL: `https://studio.mizan.market` · OpenAPI 3.1: <https://mizan.market/skill/openapi.json> · Agent instructions: <https://mizan.market/skill/SKILL.md>

## Requests

| Call | Use |
|---|---|
| `GET /api/check/{subject}` | The default bar. |
| `GET /api/check/{subject}?requirement=req_…@v[&requirement_hash=…]` | Against a published bar, pinned to its version and hash. |
| `POST /api/check` `{"agent": "…", "requirement": {…} \| "req_…@v", "amount"?: n, "currency"?: "USD", "purpose"?: "…"}` | Against an inline bar (the `requirement` object from [compile](./requirement-language.md)), or with the amount in the token. |
| `POST /api/check/verify` `{"token": "…"}` | Online re-verification of a token; offline is [here](./signed-verdict.md). |

Send `Authorization: Bearer mzn_…` to make checks under your own identity (optional).

### Subjects

An agent id (`ag_…`), a credential id, a company domain, an API, MCP or A2A endpoint URL, a public AI model (`model:<org>/<name>`), a wallet on any chain, a public key, or a GitHub, Hugging Face, npm or PyPI identity (`github:<user>`, `hf:<org/repo>`, `npm:<pkg>`, `pypi:<project>`). Matching is exact. `GET /api/resolve/{anything}` says how an identifier is read. The sandbox subject `try-me` is a stable, PROVEN record of MIZAN's own that every integrator can check first.

## The reply

Every reply is one signed JSON object. The fields an integrator relies on:

| Field | Values | Meaning |
|---|---|---|
| `decision` | `ALLOW` · `REFUSE` | Proceed only on ALLOW. |
| `evidence_rung` | `PROVEN` · `RECORDED` · `DECLARED` · `null` | The [grade](./evidence-grades.md) of the weakest evidence behind the answer. |
| `basis` | e.g. `proven`, `no_record` | Why, in one word. `no_record` is not evidence against the subject. |
| `explain` | text | The reason in plain words. |
| `next` | `{tool, arguments, why, http}` | The one next step, as a tool call and as HTTP. |
| `check_id` | hex | The id of this check; hourly check counts commit to it on the ledger. |
| `token` | compact EdDSA JWS | The signed decision, valid 24 hours. Keep it as the reason you paid or held. |
| `requirement` | `{id, version, hash, shown_back}` | The bar answered (when one was given). |
| `clauses[]` | `{clause, met, rung, threshold, gap_step}` | The bar answered clause by clause; `gap_step` is the one step to close a gap. |
| `contract_message` | `{message, canonical, signature, alg, public_key}` | With a published bar: a seven-field message a code gate verifies with no call out. |
| `attestation` | signed, nine fields | On ALLOW against a published bar: reusable by a second requirer ([reliance](./reliance.md)). |
| `standing` | `identity_age_days`, `n_life`, counts, sources | What is known about how long and how much this subject has been counted; unknowns are `null` with a reason. |
| `required_by` | `{count, public, since, via_reliance}` | Distinct requirers whose published bar the subject meets now. |
| `price_signal`, `pricing_message` | score, tier, signed message | The [price signal](./price-signal.md). |
| `disputes` | `{open, upheld, overturned}` | Contest history for the subject ([disputes](./disputes.md)). |
| `proof_request` | `{url, forward, status_url, expires_utc}` | On REFUSE: a ready message to forward to the subject. When it proves the bar, the next check returns ALLOW. MIZAN never contacts anyone. |
| `dispute` | `{route, body, window}` | On REFUSE: how to contest it. |
| `integrate` | snippets | On REFUSE for an uncounted subject: the calls to get counted (claim an identity, link the endpoint's origin, enrol it). |
| `provenance.signature` | Ed25519 | Over the canonical body ([signed verdict](./signed-verdict.md)). |

Errors are JSON with `error`, `explain` and `next`; a malformed rule returns the words that were not understood.

## In a payment path

The integrator chooses the failure mode:

- **advise**: the payment always proceeds; the verdict (or "unverifiable" when MIZAN cannot be reached) is attached to the payment record. Nothing breaks while counterparties are not yet counted.
- **enforce**: the payment proceeds only on an ALLOW whose signature verifies against the published key and has not expired. REFUSE, timeout, error, a bad signature or expiry stop it (fail-closed).

The hosted release guard (`POST /api/release/holds`, rules at `GET /api/release/program`) implements enforce on MIZAN's side: a hold pins one exact rule version and hash; an authorization is issued only on a live ALLOW against it; REFUSE, timeout, error, expiry, cancel or a second release attempt answer a signed denial; one authorization per hold, redeemable once, expiring in at most 600 s. MIZAN never holds or moves the funds.

Measured response time and time to a first ALLOW: <https://mizan.market/service-level/>.
