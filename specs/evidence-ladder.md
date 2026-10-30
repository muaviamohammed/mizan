# The evidence ladder

Every claim carries exactly one rung. A lower rung is never presented as a higher one.

| Rung | Meaning | Can it produce ALLOW? |
|---|---|---|
| **DECLARED** | They say so. | Never on its own. |
| **RECORDED** | Logged and timestamped in the public ledger, source named. | When the buyer's requirement accepts RECORDED (`min_rung`). |
| **PROVEN** | Checked by math: a proof anyone can re-verify offline. | Yes. |

Public facts from named outside sources may be shown beside an answer; they never produce ALLOW by themselves.

## The answer

`GET https://studio.mizan.market/api/check/{subject}` (or `POST /api/check {"agent": "…", "amount"?: …}`) returns one signed object. The fields an integrator relies on:

| Field | Values | Meaning |
|---|---|---|
| `decision` | `ALLOW` · `REFUSE` | Proceed only on ALLOW. |
| `basis` | `proven` · `no_record` · `below_bar` · `evidence_against` · `unverifiable` | Why. `no_record` means nothing is proven yet; it is **not** evidence of anything. |
| `evidence_rung` | `PROVEN` · `RECORDED` · `DECLARED` · `null` | The rung of the evidence behind the answer. |
| `checks[]` | `{check, clause, ok, detail}` | Every step, each tied to a clause of the standard. |
| `token` | compact EdDSA token | A signed receipt of this decision; keep it as the reason you paid or held. |
| `proof_request` | `{url, forward, status_url, expires_utc}` | On REFUSE: a ready message for the other side. When it proves itself, the next check returns ALLOW. MIZAN never contacts anyone. |
| `provenance.signature` | Ed25519 | Over the canonical body; see [signatures](./signatures.md). |

The full schema is in the OpenAPI document: <https://mizan.market/skill/openapi.json>.

## Subjects

A subject can be an agent id, a credential id, a company domain, an API, MCP or A2A endpoint, a wallet address, an ERC-8004 id, a public key, or a GitHub, Hugging Face, npm or PyPI identity. Matching is exact: partial names never match.
