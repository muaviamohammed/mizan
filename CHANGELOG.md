# Changelog

Changes to the Counted Claim Standard (`specs/`) and to the clients in `packages/`. The standard is versioned `MAJOR.MINOR` as described in [`GOVERNANCE.md`](./GOVERNANCE.md); each published version is a git tag `spec-MAJOR.MINOR`.

## Counted Claim Standard 1.1 · 2026-11-03

Tag: `spec-1.1`. Backward compatible with 1.0: every 1.0 reply still verifies; 1.1 tightens what a relying party MUST check before paying.

- **Signed verdict.** Token payloads name the subject exactly as given (`subject_as_given`) and, when an alias was resolved, as requested (`subject_requested`). A check against a rule carries `requirement`, `requirement_ref` and `requirement_hash`.
- **Signed verdict, offline verification.** Step 4 now requires that the token is about the payee being paid (`sub`, `subject_as_given` or `subject_requested`), and, with a pinned rule, that `requirement_hash` equals the pinned hash. An ALLOW about anyone else, at the default bar, or against another rule, never satisfies a payment.
- **Price signal.** The requirers input never counts the subject's own identity; check history counts only checks made by proven identities other than the subject.
- **Check API.** On REFUSE for an uncounted subject, `integrate` lists the calls to get counted: claim an identity, link the endpoint's origin, enrol it.

Clients (`mizan-check` 0.2.0, Python and TypeScript):

- `guard()` binds every token it acts on to the payee and, when given, the pinned rule; `bind_token()` / `bindToken()` expose the same checks.
- Key pinning: `MIZAN_PINNED_KEYS` and `MIZAN_PINNED_KEYS_SHA256`, or `keys=` / `{ keys }`, so nothing is fetched at decision time. See [`verify/`](./verify/#pin-the-keys).
- Offline tests for token binding and key pinning in both clients.

## Counted Claim Standard 1.0 · 2026-11-03

Text: [`specs/` at 31b3001](https://github.com/muaviamohammed/mizan/tree/31b3001/specs).

- First publication: the counted claim and its six parts (result, measure, count, proof, bar, verdict), evidence grades, the check API, signed verdicts, the requirement language, the price signal, disputes, reliance and the public ledger.
