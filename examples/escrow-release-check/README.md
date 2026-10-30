# Escrow release check (advise mode, fail-open)

Your escrow stays yours; MIZAN never holds or moves money. Before releasing a milestone payment, ask MIZAN about the payee and attach the signed answer to the release record.

| Mode | Verified ALLOW | REFUSE | MIZAN unreachable |
|---|---|---|---|
| `advise` (default) | release | release, answer attached, proof request forwarded | release, marked `UNVERIFIABLE` (fail-open) |
| `enforce` | release | hold | hold (fail-closed) |

```bash
python3 release.py               # or: node release.mjs
MIZAN_MODE=enforce python3 release.py
```

Output (advise):

```
esc_001  payee=mizan-flagship   released=True   mizan=ALLOW (proven, signature ✓)
esc_002  payee=seller.example   released=True   mizan=REFUSE (no_record, signature ✓)
         forward to payee: I'd like to pay you 500 USDC for an escrow milestone release. Before I do, prove your record with MIZAN: …
esc_003  payee=seller.example   released=True   mizan=UNVERIFIABLE (unverifiable, no signature)
```

Start in advise mode so nothing breaks while most payees are unproven. Move to enforce when your counterparties have records.
