// Offline tests: the guard's binding rules, key pinning, message expiry, advise budget. Tokens are signed here with a throwaway key.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash, generateKeyPairSync, sign } from "node:crypto";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import * as m from "../src/index.ts";

const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const other = generateKeyPairSync("ed25519").privateKey;
const PUB = publicKey.export({ format: "der", type: "spki" }).subarray(12).toString("base64");
const KEYS = { keys: [{ key_id: "test", alg: "Ed25519", public_key_b64: PUB }] };
const H = "a".repeat(64);
const b64u = (b: Buffer | string) => Buffer.from(b).toString("base64url");
const tok = (pl: Record<string, unknown>, sk = privateKey) => {
  const h = b64u(JSON.stringify({ alg: "EdDSA", kid: "test", typ: "JWT" }));
  const p = b64u(JSON.stringify({ exp: Date.now() / 1000 + 3600, ...pl }));
  return `${h}.${p}.${b64u(sign(null, Buffer.from(`${h}.${p}`), sk))}`;
};
const TRY_ME = { sub: "track-btc-trend-4h-link2", subject_as_given: "track-btc-trend-4h-link2", subject_requested: "try-me", decision: "ALLOW" };

test("bindToken: a valid try-me ALLOW never passes for another payee", () => {
  assert.equal(m.bindToken(tok(TRY_ME), "try-me", { keys: KEYS }).decision, "ALLOW");
  assert.throws(() => m.bindToken(tok(TRY_ME), "evil-seller.example", { keys: KEYS }), /another payee/);
});

test("bindToken: a default-bar ALLOW never passes a guard pinned to a strict rule", () => {
  const dflt = tok({ subject_as_given: "seller.example", decision: "ALLOW" });
  assert.throws(() => m.bindToken(dflt, "seller.example", { keys: KEYS, requirementHash: H }), /pinned rule/);
  assert.ok(m.bindToken(tok({ subject_as_given: "seller.example", decision: "ALLOW", requirement_hash: H }), "seller.example", { keys: KEYS, requirementHash: H }));
});

test("bindToken: REFUSE, expired and foreign signatures are refused", () => {
  assert.throws(() => m.bindToken(tok({ ...TRY_ME, decision: "REFUSE" }), "try-me", { keys: KEYS }), /not ALLOW/);
  assert.throws(() => m.bindToken(tok({ ...TRY_ME, exp: 1 }), "try-me", { keys: KEYS }), /expired/);
  assert.throws(() => m.bindToken(tok(TRY_ME, other), "try-me", { keys: KEYS }), /does not verify/);
});

test("pinned keys: MIZAN_PINNED_KEYS file + sha256; never fetched; a wrong sha throws", async () => {
  const f = join(mkdtempSync(join(tmpdir(), "mz-")), "mizan-keys.json");
  writeFileSync(f, JSON.stringify(KEYS));
  process.env.MIZAN_PINNED_KEYS = f;
  process.env.MIZAN_PINNED_KEYS_SHA256 = createHash("sha256").update(JSON.stringify(KEYS)).digest("hex");
  const saved = globalThis.fetch;
  globalThis.fetch = (async () => { throw new Error("fetched keys while pinned"); }) as typeof fetch;
  try {
    assert.deepEqual(await m.loadKeys(), KEYS);
    process.env.MIZAN_PINNED_KEYS_SHA256 = "0".repeat(64);
    await assert.rejects(m.loadKeys(), /does not match/);
  } finally {
    globalThis.fetch = saved; delete process.env.MIZAN_PINNED_KEYS; delete process.env.MIZAN_PINNED_KEYS_SHA256;
  }
});

const canon = (o: unknown): string => o === null || typeof o !== "object" ? JSON.stringify(o)
  : Array.isArray(o) ? `[${o.map(canon).join(",")}]` : `{${Object.keys(o as object).sort().map((k) => `${JSON.stringify(k)}:${canon((o as any)[k])}`).join(",")}}`;
const signed = (message: any) => ({ message, signature: b64u(sign(null, Buffer.from(canon(message)), privateKey)) });

test("verifyMessage honours attestation `expires` as well as `expires_at`", () => {
  const now = Math.floor(Date.now() / 1000);
  assert.equal(m.verifyMessage(signed({ key_id: "test", met: true, expires: now + 60 }), KEYS).met, true);
  assert.throws(() => m.verifyMessage(signed({ key_id: "test", met: true, expires: now - 1 }), KEYS), /expired/);
  assert.throws(() => m.verifyMessage(signed({ key_id: "test", expires_at: now - 1 }), KEYS), /expired/);
});

test("guard advise never holds the payment past its budget", async () => {
  const saved = globalThis.fetch;
  globalThis.fetch = ((_u: any, init: any) => new Promise((_res, rej) => { const t = setTimeout(() => rej(new Error("slow")), 5000); init?.signal?.addEventListener("abort", () => { clearTimeout(t); rej(new Error("aborted")); }); })) as typeof fetch;
  try {
    const seen: string[] = [];
    const g = m.guard(async () => "paid", { mode: "advise", keys: KEYS, adviseTimeoutMs: 300, onVerdict: (v) => seen.push(v.decision) });
    const t0 = Date.now();
    assert.equal(await g("seller.example"), "paid");
    assert.ok(Date.now() - t0 < 1500);
    assert.deepEqual(seen, ["UNVERIFIABLE"]);
  } finally { globalThis.fetch = saved; }
});

test("guard enforce: a try-me token served for another payee is refused (forged route)", async () => {
  const saved = globalThis.fetch;
  globalThis.fetch = (async () => new Response(JSON.stringify({ decision: "ALLOW", token: tok(TRY_ME) }), { status: 200 })) as typeof fetch;
  try {
    const paid: string[] = [];
    const g = m.guard(async (p: string) => { paid.push(p); return "paid"; }, { mode: "enforce", keys: KEYS });
    await assert.rejects(g("evil-seller.example"), m.MizanRefused);
    assert.equal(await g("try-me"), "paid");
    assert.deepEqual(paid, ["try-me"]);
  } finally { globalThis.fetch = saved; }
});
