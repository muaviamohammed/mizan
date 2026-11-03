# Governance

How the Counted Claim Standard changes.

## Who maintains it

The specification text in [`specs/`](./specs/) is maintained by Mizan Verification, Inc. Copyright © 2026 Mizan Verification, Inc. All rights reserved. Anyone may implement and verify against the standard free of charge ([`specs/LICENSE.md`](./specs/LICENSE.md)); no permission, account or fee is needed to build a conforming client, verifier or integration.

Code in `packages/`, `examples/` and `verify/` is Apache-2.0 and follows [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Proposing a change

1. **Open an issue** with the *Specification* form. Say what the text says now, what it should say, and why: a live reply that disagrees, an ambiguity, a case the text does not cover, or a new capability.
2. **Discussion happens on the issue,** in public. A proposal that changes wire format or a MUST rule includes the exact text and, where possible, a test vector or a runnable example.
3. **Pull requests to `specs/` are welcome** as a concrete form of a proposal. The maintainers may merge, rewrite or decline them; the reasoning is recorded on the issue.

## Versions

- The standard is versioned `MAJOR.MINOR`. Each published version is a git tag `spec-MAJOR.MINOR` with a GitHub release, and an entry in [`CHANGELOG.md`](./CHANGELOG.md).
- **MINOR** (1.0 → 1.1): additions and tightenings that keep every reply valid under the previous version verifiable. New optional fields, clarifications, stricter checks for relying parties.
- **MAJOR** (1.x → 2.0): a change that a conforming implementation of the previous version could not accept unchanged. Announced in an issue before publication, with the previous major supported in parallel for a stated window.
- **Published versions are never edited.** Errors are fixed in the next version. Every past version stays readable at its tag.
- **The live service and the text agree.** Where a live reply from `https://studio.mizan.market` and this text differ on a field name or value, the live reply and its OpenAPI document are authoritative and the difference is a bug in the text, fixed in the next version.

## Signing keys and the ledger

Changes to signing keys follow the published key ceremony ([`specs/signed-verdict.md`](./specs/signed-verdict.md)), never a pull request. The public ledger is append-only; no change to this repository alters a past entry.

## Security

Vulnerabilities are reported privately, never as a proposal: see [`SECURITY.md`](./SECURITY.md).
