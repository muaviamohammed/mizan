// 60 seconds, no dependencies (Node 20+): check, then pay only on ALLOW.
const d = await (await fetch("https://studio.mizan.market/api/check/try-me")).json();
console.log(d.decision, d.evidence_rung);         // ALLOW PROVEN
console.log(d.explain);
if (d.decision !== "ALLOW") throw new Error("do not pay");
export {};
