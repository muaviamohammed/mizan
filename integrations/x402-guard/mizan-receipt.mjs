// mizan-receipt.mjs — verify a stapled MIZAN proof locally. Zero calls to MIZAN at decision time.
//
//   import { verifyReceipt } from "https://mizan.market/skill/mizan-receipt.mjs";
//   const r = await verifyReceipt(receipt, { identity: payTo });   // r.allow === true → proven, bound to payTo
//
// A seller gets its receipt from GET https://studio.mizan.market/api/staple/<identity it is paid as> (24 h) and
// attaches it: X-Mizan-Receipt header, x402 accepts[i].extra.mizan.receipt, agent card, or /.well-known/mizan.json.
// ALLOW only if: Ed25519 signature verifies against a pinned MIZAN key, not expired, verdict PASS, status good,
// and the identity you are paying is listed in `bind`. A receipt shown by anyone else is never an ALLOW.
// Optional revocation check: { checkRevocation: true } fetches the signed CRL once per hour.
// Uses WebCrypto Ed25519 (Node 20+, current browsers). A decision about a credential, never advice.

export const KEYS = { "2266fb495f83b0a0": "DldoufXTa30rmfQINo1q6yAAF68Wk2qfG1A7c3OJ8yw=" };   // mizan.market/.well-known/mizan-keys.json
const STUDIO = "https://studio.mizan.market";
let _crl = null, _crlAt = 0;

const b64uToBytes = s => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4)), c => c.charCodeAt(0));
const b64ToBytes = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const norm = s => { s = String(s || "").trim(); return s.toLowerCase().startsWith("0x") ? s.toLowerCase() : s; };

async function revoked(sub) {
  if (!_crl || Date.now() - _crlAt > 3600e3) {
    try { _crl = await (await fetch(STUDIO + "/api/crl")).json(); _crlAt = Date.now(); } catch (_) { return null; }
  }
  return (_crl.revoked || []).some(r => r.credential === sub);
}

export async function verifyReceipt(token, { identity = "", keys = KEYS, checkRevocation = false, now = Date.now() / 1000 } = {}) {
  const no = (reason, payload = null) => ({ allow: false, reason, payload });
  let h, p, s, header, payload;
  try { [h, p, s] = String(token || "").trim().split("."); header = JSON.parse(new TextDecoder().decode(b64uToBytes(h))); payload = JSON.parse(new TextDecoder().decode(b64uToBytes(p))); }
  catch (_) { return no("malformed receipt"); }
  const pub = keys[header.kid];
  if (!pub) return no("unknown key id " + header.kid + " (refresh keys from mizan-keys.json)", payload);
  try {
    const key = await crypto.subtle.importKey("raw", b64ToBytes(pub), { name: "Ed25519" }, false, ["verify"]);
    const ok = await crypto.subtle.verify({ name: "Ed25519" }, key, b64uToBytes(s), new TextEncoder().encode(h + "." + p));
    if (!ok) return no("signature does not verify", payload);
  } catch (e) { return no("cannot verify Ed25519 here: " + String(e).slice(0, 80), payload); }
  if (!(payload.exp > now)) return no("expired", payload);
  if (payload.verdict !== "PASS" || payload.status !== "good") return no("not a PASS in good standing", payload);
  if (!identity) return no("no identity given: pass the wallet, host or agent id you are paying", payload);
  if (!(payload.bind || []).map(norm).includes(norm(identity))) return no("receipt is not bound to " + identity + ": never an ALLOW for someone else", payload);
  if (checkRevocation && (await revoked(payload.sub))) return no("credential revoked", payload);
  return { allow: true, reason: "proven · verified locally · bound to " + identity, credential: payload.sub, expires: payload.exp, payload };
}

export default verifyReceipt;
