// 60 seconds, no dependencies (Node 20+): check, then pay only on ALLOW.
const d = await (await fetch("https://studio.mizan.market/api/check/try-me")).json();
console.log(d.decision, d.grade ?? d.evidence_rung);   // ALLOW PROVEN (mizan.verdict/1; ?format=legacy for the previous shape)
console.log(d.explain ?? `${String(d.token).slice(0, 24)}…`);
if (d.decision !== "ALLOW") throw new Error("do not pay");
export {};
