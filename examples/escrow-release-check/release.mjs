// Escrow release check, advise mode, fail-open (Node 20+, no dependencies).
// MIZAN never holds or moves money: your escrow releases; MIZAN's signed answer is attached to the record.
// ADVISE: the release always proceeds; if MIZAN is unreachable within the timeout the record says
// "unverifiable" (fail-open). Set MIZAN_MODE=enforce to release only on a verified ALLOW (fail-closed).
//   node release.mjs
import { fetchRaw, loadKeys, verifySignedBody, DEFAULT_API } from "../../verify/js/mizan-verify.mjs";

const MODE = process.env.MIZAN_MODE || "advise";
const TIMEOUT_MS = 3000;

async function checkPayee(payee, amount, currency, api = DEFAULT_API) {
  try {
    const d = await fetchRaw(api + "/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent: payee, amount, currency, purpose: "escrow milestone release" }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    const sig = verifySignedBody(d, await loadKeys(api));
    return { decision: d.decision, basis: d.basis, signed: sig.ok, check_id: d.check_id, token: d.token,
             proof_request: d.proof_request?.forward ?? null };
  } catch (e) {
    return { decision: "UNVERIFIABLE", basis: "unverifiable", signed: null, error: String(e.cause?.code || e.message || e).slice(0, 120) };
  }
}

export async function releaseMilestone(escrowId, payee, amount, currency = "USDC", api = DEFAULT_API) {
  const mizan = await checkPayee(payee, amount, currency, api);
  const verifiedAllow = mizan.decision === "ALLOW" && mizan.signed === true;
  const released = MODE === "enforce" ? verifiedAllow : true;
  // your escrow release goes here, e.g. if (released) await escrow.release(escrowId)
  return { escrow: escrowId, payee, amount, currency, mode: MODE, released, mizan };
}

const cases = [
  ["esc_001", "mizan-flagship", 250, DEFAULT_API],
  ["esc_002", "seller.example", 500, DEFAULT_API],
  ["esc_003", "seller.example", 500, "https://unreachable.invalid"],
];
for (const [esc, payee, amount, api] of cases) {
  const r = await releaseMilestone(esc, payee, amount, "USDC", api);
  const m = r.mizan;
  const sig = m.signed === true ? "signature ✓" : m.signed === false ? "signature ✗" : "no signature";
  console.log(`${esc}  payee=${payee.padEnd(16)} released=${String(r.released).padEnd(5)}  mizan=${m.decision} (${m.basis}, ${sig})`);
  if (m.proof_request) console.log(`         forward to payee: ${m.proof_request.slice(0, 110)}…`);
  if (m.error) console.log(`         ${m.error}`);
}
