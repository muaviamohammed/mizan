# mizan-check (TypeScript)

A signed yes or no on whether an AI agent's results are real, before you pay it. Zero runtime dependencies; Node 20+ (`fetch`, `node:crypto`).

```bash
npm install && npm run build        # emits dist/; or copy src/index.ts into your project
```

```ts
import { check, guard, loadKeys, verifyToken } from "mizan-check";

const d = await check("try-me");                       // free, no key
verifyToken(d.token, await loadKeys());                // Ed25519 offline; throws if forged or expired

const bar = await check("model:openai/gpt-oss-20b", "pass@1 at least 60% over at least 20 tasks");
console.log(bar.decision, bar.clauses?.[0].gap_step);

const pay = guard(myPay, { mode: "enforce", onVerdict: console.log });  // or mode: "advise"
await pay("try-me", 25);                               // throws MizanRefused unless a verified ALLOW
```

Exports: `check`, `compileRule`, `verifyToken`, `verifyMessage`, `loadKeys`, `guard`, `MizanRefused`, and the payee side `claim`, `linkChallenge`, `linkComplete`, `enroll`.

## Tests

```bash
npm test                            # live, against https://studio.mizan.market
```

Licence: Apache-2.0.
