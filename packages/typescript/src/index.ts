// mizan-check: a signed yes or no on whether an AI agent's results are real, before you pay it.
// Thin, dependency-free client for the public MIZAN API. Node 20+ (built-in fetch and node:crypto).
//
//   import { check, verifyToken, bindToken, guard } from "mizan-check";
//   const d = await check("try-me");                       // free, no key
//   verifyToken(d.token, await loadKeys());                // Ed25519, offline; throws if forged or expired
//   bindToken(d.token, "try-me", { keys: await loadKeys() }); // ...and ALLOW, about THIS subject (what guard() requires)
import { createHash, createPublicKey, verify } from "node:crypto";
import { readFileSync } from "node:fs";

export const API = process.env.MIZAN_API ?? "https://studio.mizan.market";
const UA = "mizan-check-ts/0.2.0 (+https://github.com/muaviamohammed/mizan)";

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

export interface SignedMessage { message: Record<string, unknown> & { key_id: string; expires_at?: number; expires?: number }; signature: string }
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
/** Pinned keys from MIZAN_PINNED_KEYS (a path to your copy of mizan-keys.json, or that JSON inline), checked against
 *  MIZAN_PINNED_KEYS_SHA256 when set (a mismatch throws). null when not pinned. */
export function pinnedKeys(): Keys | null {
  const env = (process.env.MIZAN_PINNED_KEYS ?? "").trim();
  if (!env) return null;
  const raw = env.startsWith("{") ? Buffer.from(env) : readFileSync(env.replace(/^~(?=\/)/, process.env.HOME ?? "~"));
  const want = (process.env.MIZAN_PINNED_KEYS_SHA256 ?? "").trim().toLowerCase();
  if (want && createHash("sha256").update(raw).digest("hex") !== want) throw new MizanError("MIZAN_PINNED_KEYS does not match MIZAN_PINNED_KEYS_SHA256: refusing to trust it");
  return JSON.parse(raw.toString());
}
/**
 * The keys every verification here uses.
 * Pinned (recommended in production): MIZAN_PINNED_KEYS = a copy of https://studio.mizan.market/.well-known/mizan-keys.json
 * (path or inline JSON), optionally MIZAN_PINNED_KEYS_SHA256 = its sha256. When pinned, keys are NEVER fetched.
 * Default (no pin): FETCHED once per process from that URL over HTTPS, which trusts the network path at fetch time.
 */
export async function loadKeys(refresh = false): Promise<Keys> {
  const pinned = pinnedKeys();
  if (pinned) return pinned;
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

/**
 * verifyToken, then the binding guard() needs. Returns the payload; throws MizanError unless ALL hold: the signature verifies
 * and the token is unexpired; decision is ALLOW; it is about `subject` (sub, subject_as_given or subject_requested equals the
 * payee); and, when a rule is pinned, requirement_hash equals it. A token for one payee never authorises another; a default-bar
 * ALLOW never satisfies a guard pinned to a stricter rule.
 */
export function bindToken(token: string, subject: string, o: { keys: Keys; requirementHash?: string | null; now?: number }): Record<string, any> {
  const p = verifyToken(token, o.keys, o.now);
  if (p.decision !== "ALLOW") throw new MizanError(`the signed decision is ${p.decision}, not ALLOW`);
  const norm = (x: unknown) => { const s = String(x ?? "").trim(); return s.toLowerCase().startsWith("0x") ? s.toLowerCase() : s; };
  const want = norm(subject);
  const have = ["sub", "subject_as_given", "subject_requested"].map((k) => norm(p[k])).filter(Boolean);
  // the server stores at most 120 characters of a subject: a longer payee matches only that full stored prefix
  if (!want || !have.some((h) => want === h || (h.length >= 120 && want.length > h.length && want.startsWith(h))))
    throw new MizanError(`the token is about ${JSON.stringify(have)}, not ${subject}: never an ALLOW for another payee`);
  if (o.requirementHash) {
    const got = p.requirement_hash ?? (p.requirement && typeof p.requirement === "object" ? p.requirement.hash : undefined);
    if (String(got ?? "").toLowerCase() !== o.requirementHash.toLowerCase()) throw new MizanError("the token is not about the pinned rule (requirement_hash differs or is absent)");
  }
  return p;
}

const canon = (o: unknown): string =>
  o === null || typeof o !== "object" ? JSON.stringify(o).replace(/[\u007f-￿]/g, (c) => "\\u" + c.charCodeAt(0).toString(16).padStart(4, "0"))
  : Array.isArray(o) ? `[${o.map(canon).join(",")}]`
  : `{${Object.keys(o as object).sort().map((k) => `${JSON.stringify(k)}:${canon((o as any)[k])}`).join(",")}}`;

/**
 * The hash of a rule object exactly as this client sends it: SHA-256 over canonical JSON (keys sorted, no spaces, non-ASCII
 * escaped). Note: JavaScript re-serialises 60.0 as 60, so a compiled rule sent from here can hash differently from the hash
 * compileRule() states (computed over 60.0); the guard therefore pins the hash of what it sends.
 */
export const ruleHash = (rule: unknown): string => createHash("sha256").update(canon(rule)).digest("hex");

/** Verify {message, signature}: pricing_message, contract_message, attestation. Integer fields only (as served).
 *  Throws if the signature fails or the message expired (expires_at, or expires on attestations). */
export function verifyMessage(signed: SignedMessage, keys: Keys, now = Date.now() / 1000) {
  const m = signed.message;
  if (!ed25519(keys, m.key_id, Buffer.from(canon(m)), b64u(signed.signature))) throw new MizanError("signature does not verify against the published key");
  // pricing and contract messages carry expires_at; attestations carry expires. Either one ends validity.
  for (const f of ["expires_at", "expires"] as const)
    if (f in m && !(typeof m[f] === "number" && (m[f] as number) >= now)) throw new MizanError("message expired");
  return m;
}

// ------------------------------------------------------------------ in your payment path

export interface Verdict { subject: string; decision: Decision | "UNVERIFIABLE"; tokenVerified: boolean; explain?: string; error?: string; notVerifiedBecause?: string; token?: string; proofRequest?: unknown; reply?: CheckReply }

/**
 * Wrap your own pay(payee, ...args). MIZAN never holds or moves the money.
 * enforce: pays only when the signed token verifies here AND names this payee AND says ALLOW AND is unexpired AND (when a rule
 *          is pinned) carries that rule's hash. Anything else, a network error or a timeout included, throws MizanRefused
 *          and nothing is paid (fail-closed).
 * advise : always pays; the verdict (or UNVERIFIABLE) goes to onVerdict. The payment waits at most adviseTimeoutMs
 *          (default 1500) for MIZAN.
 * rule: undefined (default bar), "req_…@v#<hash>" (pinned by hash), "req_…@v" (bound by its signed ref), plain words (compiled
 *       once; the hash of the rule as sent is pinned) or a rule object (pinned by ruleHash(rule) unless requirementHash is given).
 * keys: pinned keys (the mizan-keys.json object). Default loadKeys(): MIZAN_PINNED_KEYS when set (never fetched), else fetched once.
 */
export function guard<A extends unknown[], R>(pay: (payee: string, ...args: A) => R | Promise<R>,
  { mode = "advise", rule, requirementHash, onVerdict, keys, timeoutMs = 5_000, adviseTimeoutMs = 1_500 }:
  { mode?: "advise" | "enforce"; rule?: Rule; requirementHash?: string; onVerdict?: (v: Verdict) => void; keys?: Keys; timeoutMs?: number; adviseTimeoutMs?: number } = {}) {
  let pinnedHash = requirementHash ?? null, pinnedRef: string | null = null, theRule: Rule | undefined = rule;
  let ready: Promise<void> | null = null;
  const prepare = async () => {
    if (typeof theRule === "string" && theRule.startsWith("req_")) {
      const [ref, h] = theRule.split("#");
      theRule = ref; pinnedHash = pinnedHash ?? (h ? h.trim().toLowerCase() : null); if (!pinnedHash) pinnedRef = ref;
    } else if (typeof theRule === "string") {
      const c = await compileRule(theRule);
      if (!c.requirement || (c.unmatched ?? []).length) throw new MizanError(`rule not understood: ${JSON.stringify(c.unmatched ?? c.refusal)}`);
      theRule = c.requirement; pinnedHash = pinnedHash ?? ruleHash(c.requirement);
    } else if (theRule && !pinnedHash) pinnedHash = ruleHash(theRule);
  };
  const decide = async (payee: string): Promise<Verdict> => {
    try {
      await (ready ??= prepare());
      const reply = await check(payee, theRule, { timeoutMs: mode === "advise" ? adviseTimeoutMs : timeoutMs });
      const v: Verdict = { subject: payee, decision: reply.decision, tokenVerified: false, explain: reply.explain, token: reply.token, proofRequest: reply.proof_request, reply };
      try {
        const p = bindToken(reply.token, payee, { keys: keys ?? await loadKeys(), requirementHash: pinnedHash });
        if (pinnedRef && (p.requirement_ref ?? `${p.requirement?.id}@${p.requirement?.version}`) !== pinnedRef) throw new MizanError(`the token is not about ${pinnedRef}`);
        v.tokenVerified = true;
      } catch (e) { v.notVerifiedBecause = String((e as Error).message ?? e).slice(0, 200); }
      return v;
    } catch (e) {
      return { subject: payee, decision: "UNVERIFIABLE", tokenVerified: false, error: String((e as Error).message ?? e).slice(0, 200) };
    }
  };
  return async (payee: string, ...args: A): Promise<R> => {
    let v: Verdict;
    if (mode === "advise") {
      let timer: ReturnType<typeof setTimeout> | undefined;
      const late = new Promise<Verdict>((res) => { timer = setTimeout(() => res({ subject: payee, decision: "UNVERIFIABLE", tokenVerified: false, error: `no answer within ${adviseTimeoutMs} ms; paid without waiting` }), adviseTimeoutMs); });
      v = await Promise.race([decide(payee), late]);
      clearTimeout(timer);
    } else v = await decide(payee);
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
