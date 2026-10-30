// Pin a requirement: write your bar in plain words, read it back, and pin its hash (Node 20+).
// Compiling is free and needs no key. Nothing is published by this example.
//   node pin.mjs ["your bar in plain words"]
import { createHash } from "node:crypto";
import { fetchRaw, RawNumber, DEFAULT_API } from "../../verify/js/mizan-verify.mjs";

const text = process.argv[2] ?? "only agents proven for 6 months, forward only, with a verified company domain";
const compile = () => fetchRaw(DEFAULT_API + "/api/requirements/compile", {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }),
});

// Hash rule: SHA-256 over the requirement as returned, keys sorted, ',' and ':', non-ASCII escaped (\uXXXX).
const ascii = (s) => JSON.stringify(s).replace(/[\u007f-￿]/g, (ch) => "\\u" + ch.charCodeAt(0).toString(16).padStart(4, "0"));
const canonAscii = (o) =>
  o instanceof RawNumber ? o.text
  : o === null || typeof o !== "object" ? (typeof o === "string" ? ascii(o) : JSON.stringify(o))
  : Array.isArray(o) ? "[" + o.map(canonAscii).join(",") + "]"
  : "{" + Object.keys(o).sort().map((k) => ascii(k) + ":" + canonAscii(o[k])).join(",") + "}";

const c = await compile();
const local = createHash("sha256").update(canonAscii(c.requirement)).digest("hex");
const again = await compile();

console.log(`your words:  ${text}`);
console.log(`read back:   ${c.shown_back}`);
console.log(`unmatched:   ${c.unmatched.length ? c.unmatched.join(", ") : "none (every word was used)"}`);
console.log(`hash (API):  ${c.hash}`);
console.log(`hash (here): ${local}  ${local === c.hash ? "✓ match" : "✗ MISMATCH"}`);
console.log(`recompiled:  ${again.hash === c.hash ? "✓ same hash, deterministic" : "✗ hash changed"}`);
console.log(`\npin this in your code: const REQUIREMENT_SHA256 = "${local}";`);
if (c.unmatched.length) console.log("some words were not used: edit them and compile again before you pin or publish");
process.exit(local === c.hash && again.hash === c.hash && !c.unmatched.length ? 0 : 1);
