// The x402 guard against a stand-in seller on localhost: no wallet, no real payment (Node 20+).
//   node demo.mjs
// The seller answers 402 with x402 terms; the guard asks MIZAN about the payee, then:
//   advise  → pays and attaches the signed decision      enforce → pays only on ALLOW (fails closed)
import http from "node:http";
import { guardFetch } from "./mizan-x402-guard.mjs";
const srv = http.createServer((q, r) => { r.writeHead(402, {"Content-Type":"application/json"}); r.end(JSON.stringify({x402Version:1,accepts:[{scheme:"exact",network:"base",payTo:"0x000000000000000000000000000000000000dEaD",maxAmountRequired:"1000"}]})); }).listen(0);
const url = `http://localhost:${srv.address().port}/thing`;
let paid=0; const payingFetch = async (u,i)=>{paid++; return new Response("ok");};
for (const mode of ["advise","enforce"]) {
  const f = guardFetch(payingFetch, { mode, onDecision: d => console.log(mode, "decision:", d.decision, d.basis ?? "") });
  try { const r = await f(url); console.log(mode, "paid ->", await r.text(), r.headers?.get?.("X-Mizan-Decision")); } catch (e) { console.log(mode, "refused:", e.constructor.name, String(e.message).slice(0,100)); }
}
console.log("payments made:", paid); srv.close();
