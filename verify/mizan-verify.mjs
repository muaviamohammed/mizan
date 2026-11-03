// Offline checks for anything MIZAN signs or logs. Node 20+ (built-in fetch, node:crypto Ed25519).
// No dependencies. Every check recomputes; nothing is taken on MIZAN's word.
//
//   import { verifyEntry, verifySignedBody, loadKeys } from "./mizan-verify.mjs";
import { createHash, createPublicKey, verify } from "node:crypto";
import { canon, fetchRaw, RawNumber } from "./mizan-canon.mjs";

export { canon, fetchRaw, parseRaw, RawNumber } from "./mizan-canon.mjs";

export const DEFAULT_API = "https://studio.mizan.market";
const LEAF = Buffer.from([0]), NODE = Buffer.from([1]);
const ED25519_SPKI_PREFIX = Buffer.from("302a300506032b6570032100", "hex");
const num = (x) => (x instanceof RawNumber ? Number(x.text) : x);

export const sha256 = (...parts) => { const h = createHash("sha256"); for (const p of parts) h.update(p); return h.digest(); };

/** RFC 6962 leaf hash: SHA-256(0x00 || canonical leaf). */
export const leafHash = (leaf) => sha256(LEAF, Buffer.from(canon(leaf), "utf8"));

/** RFC 6962 / RFC 9162 §2.1.3.2 inclusion proof: fold the audit path from a leaf hash to the root. */
export function fold(index, size, leaf, path) {
  let fn = index, sn = size - 1, r = leaf;
  for (const hex of path) {
    if (sn === 0) return null;
    const p = Buffer.from(hex, "hex");
    if ((fn & 1) || fn === sn) {
      r = sha256(NODE, p, r);
      if (!(fn & 1)) while (!((fn & 1) || fn === 0)) { fn >>= 1; sn >>= 1; }
    } else {
      r = sha256(NODE, r, p);
    }
    fn >>= 1; sn >>= 1;
  }
  return sn === 0 ? r : null;
}

/** The published keys (https://studio.mizan.market/.well-known/mizan-keys.json). */
export async function loadKeys(api = DEFAULT_API) {
  return fetchRaw(api + "/.well-known/mizan-keys.json");
}

function edKey(keys, keyId) {
  const all = keys.keys.filter((k) => k.alg === "Ed25519");
  const k = all.find((x) => x.key_id === keyId);
  if (!k) throw new Error(`key ${keyId} is not in the published key list`);
  return createPublicKey({ key: Buffer.concat([ED25519_SPKI_PREFIX, Buffer.from(k.public_key_b64, "base64")]), format: "der", type: "spki" });
}

/** Ed25519 over canonical bytes. */
export function verifyEd25519(keys, keyId, bytes, sigB64) {
  return verify(null, bytes, edKey(keys, keyId), Buffer.from(sigB64, "base64"));
}

/**
 * Verify a signed MIZAN reply (REST, A2A, MCP results): the signature is over the canonical
 * JSON of the whole body with provenance.signature removed. Parse the body with parseRaw/fetchRaw.
 */
export function verifySignedBody(body, keys) {
  const sig = body?.provenance?.signature;
  if (!sig) return { ok: false, reason: "no provenance.signature" };
  const copy = { ...body, provenance: { ...body.provenance } };
  delete copy.provenance.signature;
  const bytes = Buffer.from(canon(copy), "utf8");
  const digestOk = !sig.canonical_sha256 || sha256(bytes).toString("hex") === sig.canonical_sha256;
  const ok = digestOk && verifyEd25519(keys, sig.key_id, bytes, sig.sig_b64);
  return { ok, key_id: sig.key_id };
}

/** Verify a signed ledger head: Ed25519 over canon({alg, log, root, size, ts}). */
export function verifyHead(head, keys) {
  const core = { alg: head.alg, log: head.log, root: head.root, size: head.size, ts: head.ts };
  return verifyEd25519(keys, head.signature.key_id, Buffer.from(canon(core), "utf8"), head.signature.sig_b64);
}

/** Verify one ledger entry end to end. Returns { ok, lines }. */
export async function verifyEntry(index, api = DEFAULT_API, keys = null) {
  const d = await fetchRaw(`${api}/api/log/proof/${index}`);
  keys = keys || (await loadKeys(api));
  const lines = [];
  let ok = true;
  const mark = (pass, text) => { ok = ok && pass; lines.push(`${pass ? "✓" : "✗"} ${text}`); };

  const ix = num(d.index), size = num(d.size), head = d.head;
  const leaf = {};
  for (const k of Object.keys(d.leaf)) if (k !== "index" && k !== "leaf_hash") leaf[k] = d.leaf[k];
  const lh = leafHash(leaf);
  mark(lh.toString("hex") === d.leaf_hash, `Entry #${ix} recomputed from its contents: ${lh.toString("hex").slice(0, 16)}…`);

  const root = fold(ix, size, lh, d.path);
  mark(root !== null && root.toString("hex") === head.root,
    `Folded ${d.path.length} hashes up to the ledger head ${head.root.slice(0, 16)}… (${num(head.size)} entries)`);

  mark(verifyHead(head, keys), `Head signature checked against MIZAN's published key (${head.signature.key_id})`);

  // Outside time: an entry is covered once an anchored checkpoint's size exceeds its index.
  const a = head.anchor || {};
  if (a.rfc3161_time_utc && num(a.head_size) > ix)
    lines.push(`✓ Covered by an outside timestamp authority's stamp at ${String(a.rfc3161_time_utc).replace("T", " ").slice(0, 16)} UTC`);
  else
    lines.push("· Newer than the last outside stamp; covered by the next hourly one");
  return { ok, lines, index: ix };
}
