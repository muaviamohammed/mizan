[← README](../README.md) · [Check](./check.md) · [How it works](./how-it-works.md) · [Get counted](./get-counted.md) · [Payment path](./payment-path.md) · [FAQ](./faq.md)

# In your payment path

You choose the failure mode.

| Mode | On ALLOW | On REFUSE, timeout, error, bad signature, expiry, wrong payee, wrong rule |
|---|---|---|
| **advise** | pays, logs the signed verdict | pays, logs the verdict or "unverifiable". Waits at most 1.5 s for MIZAN (configurable). |
| **enforce** | pays only if the token verifies **and** is about this payee **and** (with a pinned rule) about that rule | does not pay (fail-closed) |

```python
from mizan_check import guard
pay = guard(release_escrow, mode="advise", on_verdict=audit_log)   # later: mode="enforce"
pay = guard(release_escrow, mode="enforce", rule="req_…@v#<hash>") # pinned: an ALLOW against any other bar never pays
```

The guard checks every token it acts on: Ed25519 signature against the key file, `exp` in the future, `decision` = `ALLOW`, `sub` / `subject_as_given` / `subject_requested` equal to the payee being paid, and `requirement_hash` equal to the pinned rule. Pin the key file so nothing is fetched at decision time: [`verify/`](../verify/#pin-the-keys).

The hosted release guard does enforce on MIZAN's side: a hold pins one exact rule version and hash; release is authorized only on a live ALLOW against it; REFUSE, timeout, error, expiry, cancel or a second release attempt return a signed denial; one authorization per hold, redeemable once. MIZAN never holds or moves the money ([rules](https://studio.mizan.market/api/release/program)). Response time and time to a first ALLOW are measured live: <https://mizan.market/service-level/>.

## Where it plugs in

One rule, written once, enforced at every hook with the same id and the same hash.

| Hook | Who | How | Run it |
|---|---|---|---|
| **Release guard** | escrow, payment rails, settlement | a hold releases only on a signed ALLOW | [`examples/escrow-release-guard`](../examples/escrow-release-guard/) |
| **x402 payment field** | agents paying for APIs | check the `payTo` in the 402 terms; `accepts[i].extra.mizan` names the bar | [`examples/x402-payment-check`](../examples/x402-payment-check/) |
| **Marketplace listing** | agent marketplaces, leaderboards | ALLOW lists, REFUSE hides and returns a proof request | [`examples/marketplace-listing-gate`](../examples/marketplace-listing-gate/) |
| **Platform deploy** | agent platforms and frameworks | one setting: `MIZAN_REQUIRE=req_…@v#<hash>` | [`specs/requirement-language.md`](../specs/requirement-language.md#one-rule-every-surface) |
| **Questionnaire** | allocators, insurers, enterprise buyers | one plain-words clause with a verify link | [`specs/requirement-language.md`](../specs/requirement-language.md#one-rule-every-surface) |
| **Code gate** | contracts, configs, CI | a seven-field signed message, verified with no call out | [`specs/signed-verdict.md`](../specs/signed-verdict.md) |
| **Agent hire** | agents hiring agents | check, keep the token as the reason you hired | [`examples/agent-hire`](../examples/agent-hire/) |
| **Model evaluation bar** | buyers of models | first-try score over every counted task | [`examples/model-eval-bar`](../examples/model-eval-bar/) |

Also over MCP (`claude mcp add --transport http mizan https://studio.mizan.market/mcp`, see [`packages/mcp`](../packages/mcp/)), A2A (`https://studio.mizan.market/a2a`) and OpenAPI (<https://mizan.market/skill/openapi.json>).
