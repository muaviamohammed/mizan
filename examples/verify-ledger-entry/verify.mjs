#!/usr/bin/env node
// Verify one entry of MIZAN's public ledger on your own machine (Node 20+, no dependencies).
//   node verify.mjs          # the newest entry
//   node verify.mjs 388      # entry #388
// The entry is recomputed from its contents, folded up to the signed head (RFC 6962), and the
// head's Ed25519 signature is checked against the published key. Nothing trusts MIZAN.
import { verifyEntry, fetchRaw, DEFAULT_API } from "../../verify/js/mizan-verify.mjs";

const API = process.env.MIZAN_API || DEFAULT_API;
let ix = process.argv[2];
if (ix === undefined) ix = Number((await fetchRaw(API + "/api/log/head")).size) - 1;

const { ok, lines } = await verifyEntry(Number(ix), API);
console.log(lines.join("\n"));
console.log(ok ? "Nothing here asked you to trust MIZAN. Your machine did the math." : "VERIFICATION FAILED");
process.exit(ok ? 0 : 1);
