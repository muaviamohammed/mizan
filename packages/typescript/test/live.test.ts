// Live tests against https://studio.mizan.market. Run: node --test test/
import { test } from "node:test";
import assert from "node:assert/strict";
import { bindToken, ruleHash, check, compileRule, guard, loadKeys, MizanRefused, verifyMessage, verifyToken } from "../src/index.ts";

const MODEL = "model:openai/gpt-oss-20b";
let keys: Awaited<ReturnType<typeof loadKeys>>;
test.before(async () => { keys = await loadKeys(); });

test("check try-me: signed ALLOW, token verifies offline", async () => {
  const d = await check("try-me");
  assert.equal(d.decision, "ALLOW");
  assert.equal(verifyToken(d.token, keys).decision, "ALLOW");
  assert.ok(["A", "B", "C", "D", "unrated"].includes(String(verifyMessage(d.pricing_message!, keys).tier)));
});

test("a tampered token is refused", async () => {
  const [h, p, s] = (await check("try-me")).token.split(".");
  assert.throws(() => verifyToken(`${h}.${p}.${[...s].reverse().join("")}`, keys));
});

test("a bar in plain words: ALLOW below the record, REFUSE above it", async () => {
  assert.equal((await check(MODEL, "pass@1 at least 60% over at least 20 tasks")).decision, "ALLOW");
  const r = await check(MODEL, "pass@1 at least 99% over at least 20 tasks");
  assert.equal(r.decision, "REFUSE");
  assert.equal(r.clauses![0].met, false);
});

test("compileRule reads the bar back with a hash", async () => {
  const c = await compileRule("pass@1 at least 60% over at least 20 tasks");
  assert.match(c.hash, /^[0-9a-f]{64}$/);
  assert.deepEqual(c.unmatched, []);
});

test("guard: enforce pays only on verified ALLOW, advise always pays", async () => {
  const seen: string[] = [];
  const enforce = guard(async (payee: string) => `paid ${payee}`, { mode: "enforce", onVerdict: (v) => seen.push(v.decision) });
  assert.equal(await enforce("try-me"), "paid try-me");
  await assert.rejects(enforce("unknown-seller.example"), MizanRefused);
  const advise = guard(async () => "paid", { mode: "advise", onVerdict: (v) => seen.push(v.decision) });
  assert.equal(await advise("unknown-seller.example"), "paid");
  assert.deepEqual(seen, ["ALLOW", "REFUSE", "REFUSE"]);
});

test("a live try-me ALLOW never authorises another payee", async () => {
  const t = (await check("try-me")).token;
  assert.equal(bindToken(t, "try-me", { keys }).decision, "ALLOW");
  assert.throws(() => bindToken(t, "unknown-seller.example", { keys }), /another payee/);
});

test("a live default-bar ALLOW never passes a guard pinned to a rule; the rule's own ALLOW does", async () => {
  const strict = await compileRule("pass@1 at least 60% over at least 20 tasks");
  const d = await check("try-me");
  const h = ruleHash(strict.requirement);   // the hash of the rule as this client sends it
  assert.throws(() => bindToken(d.token, "try-me", { keys, requirementHash: h }), /pinned rule/);
  const r = await check(MODEL, strict.requirement);
  assert.equal(bindToken(r.token, MODEL, { keys, requirementHash: h }).requirement_hash, h);
  const g = guard(async () => "paid", { mode: "enforce", rule: "pass@1 at least 60% over at least 20 tasks" });
  assert.equal(await g(MODEL), "paid");
  await assert.rejects(g("try-me"), MizanRefused);
});

test("the default verdict token (mzv1) of GET /api/check verifies offline; tampered, expired and another payee refused", async () => {
  const r = await fetch("https://studio.mizan.market/api/check/flagship");
  const v: any = await r.json();
  assert.ok(String(v.token).startsWith("mzv1."));
  const c = verifyToken(v.token, keys);
  assert.equal(c.decision, v.decision);
  assert.equal(c.typ, "mizan.verdict/1");
  const [a, b, s] = v.token.split(".");
  assert.throws(() => verifyToken(`${a}.${b}.${[...s].reverse().join("")}`, keys));
  assert.throws(() => verifyToken(v.token, keys, 4e9));
  if (v.decision === "ALLOW") {
    assert.equal(bindToken(v.token, "flagship", { keys }).decision, "ALLOW");
    assert.throws(() => bindToken(v.token, "someone-else", { keys }));
  }
});
