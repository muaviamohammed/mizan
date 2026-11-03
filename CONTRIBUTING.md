# Contributing

Thank you for helping. This repository holds the public side of MIZAN: the specification, thin clients, examples and offline verifiers. The service itself runs at `https://studio.mizan.market`.

## What we welcome

- **Integrations and examples** for a payment rail, marketplace, agent framework or language that is not here yet. Keep examples short (under 20 lines of logic), runnable against the live API with no key, and add them to [`examples/run-all.sh`](./examples/run-all.sh).
- **Verifier ports** (Go, Rust, Java, ...) of [`verify/`](./verify/): a token check and a ledger-entry check that match the reference output byte for byte.
- **Specification issues**: anywhere `specs/` disagrees with a live reply, is ambiguous, or could be read two ways. Use the *Specification* issue form.
- **Bug reports** with the exact request, the reply's `check_id` and the time (UTC).

## Rules

1. Every number or claim in a document links to something a reader can run or fetch. No hardcoded live counts.
2. Examples run against the live API and pass `sh examples/run-all.sh` before review.
3. Code is Apache-2.0. By contributing code you agree it is licensed under Apache-2.0. Changes to `specs/` are proposals: MIZAN maintains the specification text.
4. Never commit keys, tokens, personal data or binaries.

## Development

```bash
sh examples/run-all.sh                                     # everything, live
python3 packages/python/tests/test_live.py                 # Python client
cd packages/typescript && npm install && npm test          # TypeScript client
```

Questions: open a discussion issue, or write to the contact on <https://mizan.market/contact/>.
