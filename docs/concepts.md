# Concepts

## Every result is someone's best try

A model's score, an agent's success rate, a track record: each is the best of a number of tries only the seller knows. Payment rails prove that an agent paid and that someone authorised it. None of them says whether the result being paid for was earned. MIZAN counts the tries registered before their outcomes, proves the result without revealing the method, checks it against the buyer's own bar, and returns one signed ALLOW or REFUSE that anyone can re-check offline.

## The second ledger

The first ledger records what was done: payments, transfers, settlements. The second ledger records **what was tried**, registered before any outcome existed, so a result can be weighed against everything behind it. MIZAN's ledger is append-only and public; every entry folds to a signed head; checkpoints are stamped hourly by two outside timestamp authorities and by Bitcoin. MIZAN cannot rewrite its past without it showing. See [`specs/ledger.md`](../specs/ledger.md).

## The counted claim

Six parts, every time: **result**, **measure**, **count**, **evidence**, **requirement**, **verdict**. See [`specs/counted-claim.md`](../specs/counted-claim.md).

## The evidence ladder

**DECLARED** (they say so) · **RECORDED** (logged and timestamped, source named) · **PROVEN** (checked by math). A lower rung is never dressed as a higher one; DECLARED never produces ALLOW. See [`specs/evidence-ladder.md`](../specs/evidence-ladder.md).

## The buyer writes the bar

A requirement is the buyer's own words, compiled into a versioned rule, read back, hashed and fixed before anyone is checked. Words that cannot be bound are listed, never guessed. See [`specs/requirement-language.md`](../specs/requirement-language.md).

## Prove without revealing

A PROVEN claim is a zero-knowledge proof: the verifier learns the verdict and the disclosed metrics, never the model, code, prompts or strategy behind them. Proving starts with a free private preview; the method never leaves its owner's machine.

## Refusals are published

A pass is worth something only because a fail is possible and visible. Refusals are published beside passes, MIZAN's own included: <https://mizan.market/research/the-gate-refused-its-maker/>.

## Neutral

Checks are free. No fee depends on a verdict. MIZAN never holds, routes or releases funds; your escrow, contract or platform does, on a signed answer.
