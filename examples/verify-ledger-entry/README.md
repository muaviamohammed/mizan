# Verify a ledger entry

Nothing here trusts MIZAN. For any entry of the public ledger:

1. **Recompute** the entry: `SHA-256(0x00 ‖ canon(leaf))` must equal its `leaf_hash`.
2. **Fold** the audit path up to the ledger head (RFC 6962 / RFC 9162 inclusion proof).
3. **Check** the head's Ed25519 signature against the published key.
4. **Stamp coverage:** the entry is covered by an outside timestamp once an anchored checkpoint's size exceeds its index.

```bash
node verify.mjs          # the newest entry
node verify.mjs 388      # entry #388
open index.html          # the same, in your browser (WebCrypto Ed25519)
```

```
✓ Entry #388 recomputed from its contents: 67572788212054ef…
✓ Folded 9 hashes up to the ledger head 7962aac8a4f00124… (481 entries)
✓ Head signature checked against MIZAN's published key (2266fb495f83b0a0)
✓ Covered by an outside timestamp authority's stamp at 2026-10-30 16:05 UTC
Nothing here asked you to trust MIZAN. Your machine did the math.
```

(Head, size and stamp time move as the ledger grows.) Byte-level rules: [`specs/ledger.md`](../../specs/ledger.md). Library: [`verify/js/mizan-verify.mjs`](../../verify/js/mizan-verify.mjs).
