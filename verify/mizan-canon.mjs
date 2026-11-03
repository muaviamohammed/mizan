// mizan-canon/1 in JavaScript, byte-identical to the Python reference:
//   json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
//
// Why a parser: JSON.parse turns 150.0 into 150, and JSON.stringify writes it back as "150",
// while the Python reference writes "150.0". Signatures and leaf hashes are over the Python
// bytes, so we keep every number exactly as the server wrote it. No dependencies.

export class RawNumber {
  constructor(text) { this.text = text; }
  valueOf() { return Number(this.text); }
  toString() { return this.text; }
  toJSON() { return Number(this.text); }
}

/** Parse JSON text, keeping numbers as RawNumber (their exact source text). */
export function parseRaw(text) {
  let i = 0;
  const ws = () => { while (i < text.length && " \t\n\r".includes(text[i])) i++; };
  const value = () => {
    ws();
    const c = text[i];
    if (c === "{") {
      i++; const o = {}; ws();
      if (text[i] === "}") { i++; return o; }
      for (;;) {
        ws(); const k = str(); ws();
        if (text[i++] !== ":") throw new SyntaxError("expected : at " + i);
        o[k] = value(); ws();
        if (text[i] === ",") { i++; continue; }
        if (text[i++] === "}") return o;
        throw new SyntaxError("expected , or } at " + i);
      }
    }
    if (c === "[") {
      i++; const a = []; ws();
      if (text[i] === "]") { i++; return a; }
      for (;;) {
        a.push(value()); ws();
        if (text[i] === ",") { i++; continue; }
        if (text[i++] === "]") return a;
        throw new SyntaxError("expected , or ] at " + i);
      }
    }
    if (c === '"') return str();
    if (text.startsWith("true", i)) { i += 4; return true; }
    if (text.startsWith("false", i)) { i += 5; return false; }
    if (text.startsWith("null", i)) { i += 4; return null; }
    const m = /^-?(0|[1-9]\d*)(\.\d+)?([eE][+-]?\d+)?/.exec(text.slice(i, i + 64));
    if (!m) throw new SyntaxError("unexpected token at " + i);
    i += m[0].length;
    return new RawNumber(m[0]);
  };
  const str = () => {
    const start = i;
    if (text[i++] !== '"') throw new SyntaxError("expected string at " + start);
    while (text[i] !== '"') { if (text[i] === "\\") i++; i++; if (i > text.length) throw new SyntaxError("unterminated string"); }
    i++;
    return JSON.parse(text.slice(start, i));
  };
  const v = value(); ws();
  if (i !== text.length) throw new SyntaxError("trailing data at " + i);
  return v;
}

/** Canonical text: keys sorted, no spaces, numbers exactly as parsed. */
export function canon(o) {
  if (o instanceof RawNumber) return o.text;
  if (o === null || typeof o !== "object") return JSON.stringify(o);
  if (Array.isArray(o)) return "[" + o.map(canon).join(",") + "]";
  return "{" + Object.keys(o).sort().map((k) => JSON.stringify(k) + ":" + canon(o[k])).join(",") + "}";
}

/** Fetch a URL and parse it with parseRaw. */
export const USER_AGENT = "mizan-verify/1 (+https://github.com/muaviamohammed/mizan)" +
  (globalThis.process?.env?.MIZAN_CI ? " ci" : "");

export async function fetchRaw(url, init = {}) {
  const headers = { "User-Agent": USER_AGENT, ...(init.headers || {}) };
  const res = await fetch(url, { ...init, headers });
  const text = await res.text();
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status} ${text.slice(0, 120)}`);
  return parseRaw(text);
}
