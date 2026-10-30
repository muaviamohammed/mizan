// Check before you pay: one signed ALLOW or REFUSE, verified on this machine before any money moves.
//   node --experimental-strip-types check.ts [subject]      (Node 22.6+; plain `node` on Node 23.6+)
import { fetchRaw, loadKeys, verifySignedBody } from "../../verify/js/mizan-verify.mjs";

const API = "https://studio.mizan.market";
const subject = process.argv[2] ?? "mizan-flagship";

const decision: any = await fetchRaw(`${API}/api/check/${encodeURIComponent(subject)}`);
const signature = verifySignedBody(decision, await loadKeys(API));

console.log(`subject:   ${subject}`);
console.log(`decision:  ${decision.decision} (${decision.basis}, rung ${decision.evidence_rung ?? "none"})`);
console.log(`signature: ${signature.ok ? "✓ valid" : "✗ INVALID"} (key ${signature.key_id})`);

if (!signature.ok) throw new Error("unsigned or tampered answer: do not pay");
if (decision.decision === "ALLOW") {
  console.log("→ pay");                      // your payment call goes here
} else {
  console.log("→ hold payment");
  for (const r of decision.reasons ?? []) console.log(`   reason: ${r}`);
}
