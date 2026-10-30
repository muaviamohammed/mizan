# VTR-1 requirement clauses (R-01 to R-41)

> **Source:** `GET https://studio.mizan.market/api/standard/clauses`, read 2026-10-30. Text reproduced verbatim under **CC BY 4.0** from *VTR-1: The Verifiable Track Record Standard* by Mohammad Muavia, Mizan Verification, Inc. (frozen 2026-08-01; [SSRN 7215664](https://ssrn.com/abstract=7215664)). The normative text is the published specification at <https://mizan.market/standard-spec/>; corrections are published at <https://mizan.market/errata/>. If this copy and the published text ever differ, the published text governs.

Keywords MUST, SHOULD and MAY are used as in RFC 2119.

| ID | Section | Level | Group | Requirement |
|---|---|---|---|---|
| R-01 | §2 | MUST | data | The verifier re-derives the data root from its own copy of the data and rejects on mismatch. |
| R-02 | §2 | MUST | data | The cost floor is checked by the conforming verifier. It SHOULD additionally be enforced in-circuit. |
| R-03 | §2 | MUST NOT | data | An issuer MAY commit costs above the floor but MUST NOT commit costs below it. |
| R-04 | §3 | MUST | levels | A credential declares exactly one conformance Level. |
| R-05 | §3 | MUST | levels | A Level I credential proves in-circuit: strategy-to-returns evaluation on the committed data, costs charged on every transaction, and the reported metrics. |
| R-06 | §3 | MUST | levels | A Level II credential additionally commits the trial ledger before evaluation, derives N from it, and recomputes the anti-overfitting statistics in-circuit. |
| R-07 | §3 | MUST NOT | levels | A credential does not report a subset of results that flatters the outcome. |
| R-08 | §3 | MUST | levels | A Level III credential additionally satisfies the pre-registration and forward-record requirements of §3. |
| R-09 | §3 | MUST NOT | levels | The strategy or model is not recoverable from the credential. |
| R-10 | §4 | MUST | verify | A conforming verifier performs every step of the verification procedure in §4. |
| R-11 | §4 | MUST | verify | The verifier returns a failure indication on any check that does not pass. |
| R-12 | §4 | MUST NOT | verify | The verifier does not require trust in the issuer at any step. |
| R-13 | §4 | SHOULD | verify | A verification implementation is distributable and runnable offline. |
| R-14 | §5 | MUST NOT | limits | A credential is not represented as predicting future returns. |
| R-15 | §5 | MUST | limits | A conforming implementation refuses a strategy whose result depends on fills the committed data cannot justify, or evaluates it under R-27 and discloses the assumptions made. High-frequency strategies are refused without exception. |
| R-16 | §5 | MUST | limits | A credential discloses whether it is a sealed backtest or a pre-registered forward record. |
| R-17 | §7 | MAY | gov | Anyone may implement this standard. |
| R-18 | §7 | MUST | gov | A party claiming conformance publishes, per credential: declared Level, era hash, committed data root, and a re-verifiable proof. |
| R-19 | §7 | MUST NOT | gov | A party does not describe a credential as conforming to a Level whose requirements it does not meet. |
| R-20 | §9 | MUST | repr | A conforming implementation discloses, on every credential, which strategy representation was used. |
| R-21 | §9 | MUST NOT | repr | An implementation does not silently substitute an expressible strategy for one it cannot express; it refuses, or discloses the substitution. |
| R-22 | §9 | MUST NOT | repr | An implementation does not imply arbitrary strategy expressiveness in its declared representation. |
| R-23 | §10 | MUST | sound | The implementation is sound against a submitter controlling their own inputs; its governance is sound against an issuer motivated to change what a past credential meant. |
| R-24 | §10 | MUST | sound | Any trial-padding residual the implementation does not detect is disclosed. Identical and exactly proportional candidates SHOULD be refused. |
| R-25 | §10 | SHOULD | sound | Corrections robust to decoy candidates are preferred over those that are not. |
| R-26 | §10 | MUST | sound | The declared annualization basis is bounded against the committed data window. |
| R-27 | §10 | MUST | sound | Path-dependent exit logic uses conservative fill assumptions, discloses them, and assumes no fill that cannot be justified from the committed data. |
| R-28 | §D.1 | MUST | math | All committed and re-derived statistics use deterministic fixed-point integer arithmetic at scale 10⁶; floating point is not used in the evaluated path. |
| R-29 | §D.1 | MUST | math | Verification equality is exact; no numerical tolerance is introduced. |
| R-30 | §D.2 | MUST | math | Population moments, standardised before third and fourth powers; raw kurtosis (3 for a normal); per-period Sharpe. |
| R-31 | §D.3 | MUST | math | PSR is the Bailey & López de Prado estimator as stated, with the radicand floored positive. |
| R-32 | §D.4 | MUST | math | SR₀ is the expected maximum of N trials as stated, evaluated via the log-tail branch for large N. |
| R-33 | §D.5 | MUST | math | Effective sample size under AR(1), one-sided: n_eff never exceeds n. |
| R-34 | §D.6 | MUST | math | DSR = PSR(SR₀) at n_eff; MinBTL rounded up, floored at 2. |
| R-35 | §D.7 | MUST | math | Annualisation is a reporting transformation only and does not enter any significance calculation. |
| R-36 | §5 | MUST NOT | limits | A credential is not represented as modelling capacity, market impact, or fill quality beyond the committed cost floor. |
| R-37 | §2, §4 | MUST | data | The gate policy is pinned by the era, published by the implementation, identical across credentials of a given Level and era, and not selectable by the prover per credential. |
| R-38 | §D.4 | MUST | math | σ_SR is the population standard deviation of the per-period Sharpe across the resolved trials of the committed ledger. |
| R-39 | §D.8 | MUST | math | Where PBO is computed, it uses the CSCV construction of D.8: contiguous equal sub-periods, all balanced partitions, split canonical and not prover-chosen. |
| R-40 | §E | MUST | math | Commitments use the constructions of Appendix E: SHA-256, domain-separated and index-bound leaves, promotion on odd levels. |
| R-41 | §8 | MUST | gov | An implementation publishes a route for reporting a suspected soundness break, and discloses confirmed breaks as era status under §6. |
