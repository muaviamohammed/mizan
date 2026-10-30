# Contributing

Thank you for helping make proof before payment a default.

## What lives here

- **Specifications** (`specs/`, CC BY 4.0). The frozen VTR-1 text is never edited; corrections ship as errata and changes as a new version. Propose changes with the **Spec change** issue template.
- **SDKs and integrations** (`typescript/`, `python/`, `integrations/`, MIT). Bug fixes, new framework integrations and new language clients are welcome.
- **Examples and verification** (`examples/`, `verify/`, MIT). Every example must run against the public API with no key; CI runs them all.

The prover is not in this repository and is not open source.

## Ground rules

1. **Every claim true.** Docs state what is live as live and what is not as not. Numbers are read live from an endpoint or left out.
2. **Public endpoints only.** Examples and tests use `https://studio.mizan.market` without keys. Nothing in CI publishes, mints or writes on anyone's behalf.
3. **No secrets.** Never commit keys, tokens, `.env` files or personal data. CI scans every push.
4. **Verify, don't trust.** New verification code ships with a test that recomputes from public data.
5. **Small pull requests**, one change each, with a clear description of what changed and how you tested it.

## Running the checks

```bash
sh examples/run-all.sh                                                  # every example, live
(cd typescript/packages/sdk && npm ci && npm run typecheck && npm test)
(cd integrations/elizaos && npm ci && npx tsc --noEmit && npx vitest run test/plugin.test.ts)
(cd python/mizan-agent-tools && pip install -e ".[test]" && pytest -q)
```

## Releases

Package releases (npm, PyPI, the MCP registry) are made by the maintainers only. Do not push tags.
