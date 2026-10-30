# How the in-browser ledger check works

The home page of <https://mizan.market> lets anyone click a ledger row and verify it in the browser. [`examples/verify-ledger-entry`](../examples/verify-ledger-entry/) is the same logic as a standalone page (`index.html`) and a Node script (`verify.mjs`). This is what it does, step by step.

## 0 · Fetch

```
GET https://studio.mizan.market/api/log/proof/{i}
→ { index, size, leaf, leaf_hash, path[], root, head: { size, root, ts, alg, log, signature, anchor } }
GET https://studio.mizan.market/.well-known/mizan-keys.json
```

CORS is open on both, so the page needs no proxy.

## 1 · `canon()`: the exact bytes

```js
function canon(o) {
  if (o instanceof RawNumber) return o.text;                       // numbers exactly as the server wrote them
  if (o === null || typeof o !== "object") return JSON.stringify(o);
  if (Array.isArray(o)) return "[" + o.map(canon).join(",") + "]";
  return "{" + Object.keys(o).sort().map(k => JSON.stringify(k) + ":" + canon(o[k])).join(",") + "}";
}
```

Keys sorted, no spaces, UTF-8, non-ASCII left as is. This matches the reference `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` byte for byte **only if numbers keep their source text**: `JSON.parse` turns `150.0` into `150`. The example pages parse with a small number-preserving parser (`parseRaw`), and with it every entry on the ledger verifies. A `canon()` built on plain `JSON.parse` fails on entries whose payload carries a whole-number float, such as an amount of `150.0`.

## 2 · The entry, recomputed

Remove `index` and `leaf_hash` from `leaf`, then:

```
leaf_hash = SHA-256( 0x00 ‖ canon(leaf) )
```

It must equal the `leaf_hash` the server sent. A single changed character in the entry changes this hash.

## 3 · The RFC 6962 fold

The audit `path` proves the entry sits at index `i` of a tree of `size` leaves whose root is `head.root`:

```js
let fn = i, sn = size - 1, r = leaf_hash;
for (const p of path) {
  if ((fn & 1) || fn === sn) {                 // the sibling is on the left
    r = SHA256(0x01 ‖ p ‖ r);
    if (!(fn & 1)) while (!((fn & 1) || fn === 0)) { fn >>= 1; sn >>= 1; }
  } else {                                     // the sibling is on the right
    r = SHA256(0x01 ‖ r ‖ p);
  }
  fn >>= 1; sn >>= 1;
}
ok = (sn === 0) && hex(r) === head.root;
```

This is the inclusion-proof algorithm of RFC 9162 §2.1.3.2, with RFC 6962's `0x00` leaf and `0x01` node prefixes so a leaf can never be passed off as a node.

## 4 · The Ed25519 head signature

```js
core = { alg, log, root, size, ts }              // from head
crypto.subtle.verify({ name: "Ed25519" }, publishedKey, base64(head.signature.sig_b64), utf8(canon(core)))
```

The key is the `Ed25519` entry in `mizan-keys.json` whose `key_id` matches `head.signature.key_id`. Browsers without WebCrypto Ed25519 say so instead of guessing; `node verify.mjs` checks the same signature with `node:crypto`.

## 5 · The stamp coverage rule

```js
covered = head.anchor.rfc3161_time_utc && head.anchor.head_size > i
```

An entry is covered by an outside timestamp once an anchored checkpoint's size exceeds its index. A newer entry is covered by the next hourly checkpoint. The operative time of an entry is the stamp of the first covering checkpoint (the later of the two RFC 3161 times when both exist), never the entry's own `ts`. To check the stamp itself, see [`specs/ledger.md`](../specs/ledger.md#operative-time).

## What this proves, and what it does not

It proves the entry you see is the entry in the signed ledger, unchanged, at that position, under a head MIZAN signed with its published key, and (once covered) that it existed by the stamped time. It does not prove the claim inside the entry is true beyond its rung: a RECORDED entry is a record, not a proof. For a PROVEN credential, run the verifier: [`verify/`](../verify/).
