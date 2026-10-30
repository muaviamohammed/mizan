// mizan-x402-guard.mjs — check before your agent pays. MIZAN's allocate-check inside the x402 payment step.
// Zero dependencies. Works with any paying fetch (x402-fetch's wrapFetchWithPayment, your own, anything).
//
//   import { guardFetch } from "https://mizan.market/skill/mizan-x402-guard.mjs";
//   const safeFetch = guardFetch(fetchWithPayment, { mode: "advise", onDecision: d => console.log(d.decision) });
//   const res = await safeFetch("https://seller.example/api/thing");   // checked, then paid
//
// One unpaid request returns HTTP 402 with the seller's terms (x402 `accepts`, including `payTo`). MIZAN runs the
// allocate-check on that payee and the seller's host, then:
//   mode "advise"  (default) the payment proceeds; the signed decision goes to onDecision and the X-Mizan-Decision header.
//   mode "enforce" the payment proceeds only on ALLOW; otherwise MizanRefused is thrown and nothing is paid.
// In enforce mode any network error is a REFUSE (fail closed). A decision is about the counterparty's credential,
// never advice about the purchase; you keep responsibility.
// On REFUSE the decision carries proof_request {url, forward}: send it to the seller; when they pass, your next check is ALLOW.

import { verifyReceipt } from "./mizan-receipt.mjs";

const STUDIO = "https://studio.mizan.market";

export class MizanRefused extends Error {
  constructor(decision) {
    super(`MIZAN refused payment to ${decision.subject}: ${(decision.reasons || []).slice(0, 2).join("; ") || "no ALLOW"}` +
          (decision.proof_request ? `. Ask them to prove it: ${decision.proof_request.url}` : ""));
    this.decision = decision;
    this.proofRequest = decision.proof_request || null;   // forward .forward or .url to the seller; re-check when it flips to PROVEN
  }
}

export async function check(subject, { amount = null, currency = "USDC", purpose = "x402 payment", policyId = null } = {}) {
  try {
    const r = await fetch(STUDIO + "/api/allocate-check", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent: subject, amount, currency, purpose, ...(policyId ? { policy_id: policyId } : {}) }),
    });
    return { ...(await r.json()), subject };
  } catch (e) {
    return { decision: "REFUSE", reasons: [`unverifiable: ${String(e).slice(0, 120)}`], subject };
  }
}

async function paymentTerms(url, init) {
  const r = await fetch(url, { method: (init && init.method) || "GET", headers: (init && init.headers) || {} });
  if (r.status !== 402) return null;
  let body = {};
  try { body = await r.json(); } catch (_) {}
  const first = (body.accepts || [])[0] || {};
  const mz = (first.extra && first.extra.mizan) || {};
  const declared = mz.credential || null;                                                        // MIZAN x402 extension v1
  const receipt = mz.receipt || r.headers.get("X-Mizan-Receipt") || null;                        // stapled proof (v2)
  return { payTo: first.payTo, network: first.network, declared, receipt };
}

export function guardFetch(payingFetch, { mode = "advise", onDecision = null, policyId = null, alsoCheckHost = true } = {}) {
  if (!["advise", "enforce"].includes(mode)) throw new Error('mode must be "advise" or "enforce"');
  return async function guarded(url, init = {}) {
    let terms;
    try { terms = await paymentTerms(url, init); } catch (e) { terms = { payTo: null, error: String(e) }; }
    if (terms === null) return payingFetch(url, init);            // no 402: nothing to pay
    // Stapled proof first: verified locally, zero calls to MIZAN. Bound to the payee (or host) or it does not count.
    if (terms.receipt) {
      for (const id of [terms.payTo, alsoCheckHost ? new URL(url).host : null].filter(Boolean)) {
        const v = await verifyReceipt(terms.receipt, { identity: id });
        if (v.allow) {
          const best = { decision: "ALLOW", stapled: true, subject: id, credential: v.credential, reasons: [], verified: v.reason, network: terms.network || null };
          if (onDecision) onDecision(best);
          const res = await payingFetch(url, init);
          try { res.headers.set("X-Mizan-Decision", "ALLOW"); } catch (_) {}
          return res;
        }
      }
    }
    const subjects = [];
    if (terms.payTo) subjects.push(terms.payTo);
    if (alsoCheckHost) subjects.push(new URL(url).host);
    const decisions = subjects.length ? await Promise.all(subjects.map(s => check(s, { policyId })))
                                      : [{ decision: "REFUSE", reasons: ["402 carried no payTo"], subject: url }];
    const best = decisions.find(d => d.decision === "ALLOW") || decisions[0];
    best.checked = subjects; best.network = terms.network || null;
    if (terms.declared) {
      // A seller-declared credential never grants ALLOW by itself (anyone can paste someone else's id);
      // it counts only through the payee or host check, which binds it to who is actually being paid.
      const dd = await check(String(terms.declared), { policyId });
      best.declaredBySeller = { credential: String(terms.declared), decision: dd.decision, counts: "only when the payee or host check resolves to it" };
    }
    if (onDecision) onDecision(best);
    if (mode === "enforce" && best.decision !== "ALLOW") throw new MizanRefused(best);
    // Advise mode on a REFUSE: pay, and tell the seller proof was requested (header carries the link, nothing else).
    const pr = best.decision !== "ALLOW" && best.proof_request ? best.proof_request.url : null;
    const init2 = pr ? { ...init, headers: { ...(init.headers || {}), "X-Mizan-Proof-Request": pr } } : init;
    const res = await payingFetch(url, init2);
    try { res.headers.set("X-Mizan-Decision", best.decision); } catch (_) {}   // immutable headers on some runtimes
    return res;
  };
}

export default guardFetch;
