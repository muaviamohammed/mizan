// Verify one ledger entry on your machine: recompute it, fold it to the signed head (RFC 6962),
// check the head's Ed25519 signature against the published key. Node 20+, no dependencies.
//   node verify-entry.mjs [index]        (default: the newest entry)
import { fetchRaw, verifyEntry, DEFAULT_API } from "./mizan-verify.mjs";
const head = await fetchRaw(DEFAULT_API + "/api/log/head");
const ix = process.argv[2] ? Number(process.argv[2]) : Number(head.size) - 1;
const { ok, lines } = await verifyEntry(ix);
console.log(lines.join("\n"));
console.log(ok ? "Nothing here asked you to trust MIZAN. Your machine did the math." : "VERIFICATION FAILED");
process.exit(ok ? 0 : 1);
