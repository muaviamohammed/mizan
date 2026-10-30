# FAQ

**Is checking free?** Yes. No key, no account. `GET https://studio.mizan.market/api/check/{subject}`.

**What can I check?** An agent id, a credential id, a company domain, an API, MCP or A2A endpoint, a wallet, an ERC-8004 id, a public key, or a GitHub, Hugging Face, npm or PyPI identity. Matching is exact.

**What does REFUSE with basis `no_record` mean?** Nothing is proven for that subject yet. It is not evidence of anything. The reply carries a proof request you can forward; when the subject proves itself, your next check returns ALLOW.

**Does MIZAN hold the money?** No. MIZAN never holds, routes or releases funds. Your escrow, contract or platform does, on a signed answer.

**Do I have to trust MIZAN?** No. Every answer is signed with a published key and verifies offline; every entry folds to a signed, externally stamped head; every credential re-verifies with a published verifier binary. See [`verify/`](../verify/).

**Is the prover open source?** No. The standard (VTR-1, CC BY 4.0), the specifications, the SDKs, the integrations and the examples are open. The verifier is published as binaries with SHA-256 sums. The prover is private.

**Does proving reveal my model or code?** No. A PROVEN claim is a zero-knowledge proof; the verifier learns the verdict and the disclosed metrics only.

**How many proofs, refusals and checks are there?** Read them live, never from a document: `GET https://studio.mizan.market/api/public/stats`.

**What if I disagree with a verdict?** Verdicts are reported exactly as issued and published, refusals included. Open an issue for a spec question; report a suspected flaw in verification privately (see [`SECURITY.md`](../SECURITY.md)).
