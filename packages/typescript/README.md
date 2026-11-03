# mizan-check (TypeScript)

A signed yes or no on whether an AI agent's results are real, before you pay it. Zero runtime dependencies; Node 20+ (`fetch`, `node:crypto`).

```bash
npm install && npm run build        # emits dist/; or copy src/index.ts into your project
```

```ts
import { bindToken, check, guard, loadKeys, verifyToken } from "mizan-check";

const d = await check("try-me");                       // free, no key
const keys = await loadKeys();                         // MIZAN_PINNED_KEYS when set (never fetched), else fetched once
verifyToken(d.token, keys);                            // Ed25519 offline; throws if forged or expired
bindToken(d.token, "try-me", { keys });                // ...and ALLOW, about THIS payee; throws for anyone else

const bar = await check("model:openai/gpt-oss-20b", "pass@1 at least 60% over at least 20 tasks");
console.log(bar.decision, bar.clauses?.[0].gap_step);

const pay = guard(myPay, { mode: "enforce", onVerdict: console.log });  // or mode: "advise" (waits at most adviseTimeoutMs, default 1500)
await pay("try-me", 25);                               // throws MizanRefused unless an ALLOW verified and bound to this payee
const strict = guard(myPay, { mode: "enforce", rule: "pass@1 at least 60% over at least 20 tasks" }); // pinned to that rule
```

Pin the key file: `MIZAN_PINNED_KEYS=/path/to/mizan-keys.json` (or the JSON inline), optionally `MIZAN_PINNED_KEYS_SHA256`; or pass `{ keys }`.
A rule object is pinned by `ruleHash(rule)`, the hash of the rule exactly as this client sends it (JavaScript writes `60.0` as `60`, so it can differ from the hash `compileRule()` states).

Exports: `check`, `compileRule`, `ruleHash`, `verifyToken`, `bindToken`, `verifyMessage` (honours `expires_at` and `expires`), `loadKeys`, `pinnedKeys`, `guard`, `MizanRefused`, and the payee side `claim`, `linkChallenge`, `linkComplete`, `enroll`.

## Tests

```bash
npm test                            # offline binding/pinning tests, then live against https://studio.mizan.market
```

Licence: MIT.
