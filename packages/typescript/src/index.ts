// mizan-check: a signed yes or no on whether an AI agent's results are real, before you pay it.
// Thin, dependency-free client for the public MIZAN API. Node 20+ (built-in fetch and node:crypto).
//
//   import { check, verifyToken, guard } from "mizan-check";
//   const d = await check("try-me");            // free, no key
//   verifyToken(d.token, await loadKeys());     // Ed25519, offline; throws if forged or expired
import { createPublicKey, verify } from "node:crypto";

export const API = process.env.MIZAN_API ?? "https://studio.mizan.market";
const UA = "mizan-check-ts/0.1.0 (+https://github.com/muaviamohammed/mizan)";

export type Decision = "ALLOW" | "REFUSE";
export type Grade = "DECLARED" | "RECORDED" | "PROVEN";
export type Rule = string | Record<string, unknown>;

export interface CheckReply {
  decision: Decision;
  evidence_rung: Grade | null;
  explain: string;
  token: string;
  check_id: string;
  next: unknown;
  clauses?: { clause: unknown; met: boolean; rung: Grade | null; threshold: unknown; gap_step: string | null }[];
  requirement?: { id: string | null; version: number | null; hash: string; shown_back: string };
  proof_request?: { url: string; forward: string } | null;
  price_signal?: { version: string; score_0_100: number | null; tier: string; limit_units: number | null };
  pricing_message?: SignedMessage;
  [k: string]: unknown;
}

export interface SignedMessage { message: Record<string, unknown> & { key_id: string; expires_at?: number }; signature: string }
export interface Keys { keys: { key_id: string; alg: string; public_key_b64?: string }[] }

export class MizanError extends Error {}
export class MizanRefused extends Error {
  verdict: Verdict;
  constructor(verdict: Verdict) {
    super(`MIZAN: ${verdict.decision} for ${verdict.subject}: ${verdict.explain ?? verdict.error ?? "no verified ALLOW"}`);
    this.verdict = verdict;
  }
}

async function req(method: string, path: string, body?: unknown, key?: string, timeoutMs = 20_000): Promise<any> {
  const headers: Record<string, string> = { "User-Agent": UA, Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (key) headers.Authorization = `Bearer ${key}`;
  let res: Response;
  try {
    res = await fetch(API + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(timeoutMs) });
  } catch (e) {
    throw new MizanError(`unreachable: ${String(e).slice(0, 160)}`);
  }
  if (res.status >= 500) throw new MizanError(`HTTP ${res.status} on ${path}: service unavailable`);
  try { return await res.json(); } catch { throw new MizanError(`HTTP ${res.status} on ${path}`); }
}

/** Plain words in, an exact rule back: {requirement, shown_back, unmatched, hash, publishable}. Free, no key. */
export const compileRule = (words: string) => req("POST", "/api/requirements/compile", { text: words });

/**
 * One signed ALLOW or REFUSE. rule: undefined (default bar), a published id "req_…@v",
 * plain words (compiled first), or a rule object from compileRule().requirement.
 */
export async function check(subject: string, rule?: Rule, opts: { amount?: number; currency?: string; key?: string; timeoutMs?: number } = {}): Promise<CheckReply> {
  const s = encodeURIComponent(subject).replace(/%3A/g, ":").replace(/%40/g, "@");
  let d: any;
  if (rule === undefined && opts.amount === undefined) d = await req("GET", `/api/check/${s}`, undefined, opts.key, opts.timeoutMs);
  else if (typeof rule === "string" && rule.startsWith("req_")) d = await req("GET", `/api/check/${s}?requirement=${encodeURIComponent(rule)}`, undefined, opts.key, opts.timeoutMs);
  else {
    let requirement = rule;
    if (typeof rule === "string") {
      const c = await compileRule(rule);
      if (!c.requirement || (c.unmatched ?? []).length) throw new MizanError(`rule not understood: ${JSON.stringify(c.unmatched ?? c.refusal)}`);
      requirement = c.requirement;
    }
    d = await req("POST", "/api/check", { agent: subject, requirement, amount: opts.amount, currency: opts.currency ?? "USD" }, opts.key, opts.timeoutMs);
  }
  if (!d || !("decision" in d)) throw new MizanError(d?.explain ?? d?.error ?? "no decision in reply");
  return d as CheckReply;
}

// ------------------------------------------------------------------ offline verification

let cachedKeys: Keys | null = null;
/** The published keys: https://studio.mizan.market/.well-known/mizan-keys.json */
export async function loadKeys(refresh = false): Promise<Keys> {
  if (!cachedKeys || refresh) cachedKeys = await req("GET", "/.well-known/mizan-keys.json");
  return cachedKeys!;
}

const SPKI = Buffer.from("302a300506032b6570032100", "hex");
function ed25519(keys: Keys, keyId: string, message: Buffer, sig: Buffer): boolean {
  const k = keys.keys.find((x) => x.alg === "Ed25519" && x.key_id === keyId);
  if (!k?.public_key_b64) return false;
  const pub = createPublicKey({ key: Buffer.concat([SPKI, Buffer.from(k.public_key_b64, "base64")]), format: "der", type: "spki" });
  return verify(null, message, pub, sig);
}
const b64u = (s: string) => Buffer.from(s.replace(/-/g, "+").replace(/_/g, "/"), "base64");

/** Verify a check token (compact JWS, EdDSA) offline. Returns the payload; throws if forged or expired. */
export function verifyToken(token: string, keys: Keys, now = Date.now() / 1000): Record<string, any> {
  const [h, p, s] = token.split(".");
  let header: any, payload: any;
  try { header = JSON.parse(b64u(h).toString()); payload = JSON.parse(b64u(p).toString()); } catch { throw new MizanError("not a MIZAN token"); }
  if (header.alg !== "EdDSA" || !ed25519(keys, header.kid, Buffer.from(`${h}.${p}`), b64u(s))) throw new MizanError("signature does not verify against the published key");
  if ((payload.exp ?? 0) < now) throw new MizanError("token expired");
  return payload;
}

const canon = (o: unknown): string =>
  o === null || typeof o !== "object" ? JSON.stringify(o).replace(/[\u007f-￿]/g, (c) => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"))
  : Array.isArray(o) ? `[${o.map(canon).join(",")}]`
  : `{${Object.keys(o as object).sort().map((k) => `${JSON.stringify(k)}:${canon((o as any)[k])}`).join(",")}}`;

/** Verify {message, signature}: pricing_message, contract_message, attestation. Integer fields only (as served). */
export function verifyMessage(signed: SignedMessage, keys: Keys, now = Date.now() / 1000) {
  const m = signed.message;
  if (!ed25519(keys, m.key_id, Buffer.from(canon(m)), b64u(signed.signature))) throw new MizanError("signature does not verify against the published key");
  if (m.expires_at !== undefined && m.expires_at < now) throw new MizanError("message expired");
  return m;
}

// ------------------------------------------------------------------ in your payment path

export interface Verdict { subject: string; decision: Decision | "UNVERIFIABLE"; tokenVerified: boolean; explain?: string; error?: string; token?: string; proofRequest?: unknown; reply?: CheckReply }

/**
 * Wrap your own pay(payee, ...args). MIZAN never holds or moves the money.
 * advise : always pays; the verdict goes to onVerdict for your log.
 * enforce: pays only on an ALLOW whose token verifies offline; REFUSE, error, timeout,
 *          bad signature or expiry throw MizanRefused and nothing is paid (fail-closed).
 */
export function guard<A extends unknown[], R>(pay: (payee: string, ...args: A) => R | Promise<R>,
  { mode = "advise", rule, onVerdict, timeoutMs = 5_000 }: { mode?: "advise" | "enforce"; rule?: Rule; onVerdict?: (v: Verdict) => void; timeoutMs?: number } = {}) {
  return async (payee: string, ...args: A): Promise<R> => {
    let v: Verdict;
    try {
      const reply = await check(payee, rule, { timeoutMs });
      const ok = !!reply.token && !!verifyToken(reply.token, await loadKeys());
      v = { subject: payee, decision: reply.decision, tokenVerified: ok, explain: reply.explain, token: reply.token, proofRequest: reply.proof_request, reply };
    } catch (e) {
      v = { subject: payee, decision: "UNVERIFIABLE", tokenVerified: false, error: String((e as Error).message ?? e).slice(0, 200) };
    }
    onVerdict?.(v);
    if (mode === "enforce" && !(v.decision === "ALLOW" && v.tokenVerified)) throw new MizanRefused(v);
    return pay(payee, ...args);
  };
}

// ------------------------------------------------------------------ payee side: get counted

/** Claim an identity: {agent_id, api_key (shown once), listing}. No account, no email. */
export const claim = (name: string) => req("POST", "/api/agents/claim", { name });
/** Prove you control an endpoint's origin: serve reply.nonce at https://<host>/.well-known/mizan-challenge. */
export const linkChallenge = (key: string, endpoint: string) => req("POST", "/api/link/challenge", { identifier: endpoint }, key);
/** Finish the link once the nonce is served. */
export const linkComplete = (key: string, challengeId: string) => req("POST", "/api/link/complete", { challenge_id: challengeId }, key);
/** Enrol a linked endpoint for counted evaluation. adapter: openai (chat completions), mcp or a2a. */
export const enroll = (key: string, url: string, o: { adapter?: "openai" | "mcp" | "a2a"; model?: string; label?: string } = {}) =>
  req("POST", "/api/eval/enroll", { url, adapter: o.adapter ?? "openai", ...(o.model ? { model: o.model } : {}), ...(o.label ? { label: o.label } : {}) }, key);
