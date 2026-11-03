// Live tests against https://studio.mizan.market. Run: node --test test/
import { test } from "node:test";
import assert from "node:assert/strict";
import { check, compileRule, guard, loadKeys, MizanRefused, verifyMessage, verifyToken } from "../src/index.ts";

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
