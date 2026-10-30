# ERC-8004

MIZAN serves its verdicts in ERC-8004's own shapes and issues EIP-712 receipts any EVM contract can check.

| What | Where |
|---|---|
| Reputation feedback shape (signed; PASS 100, NOT SIGNIFICANT 50, FAIL 0; never an opinion score) | `GET https://studio.mizan.market/api/erc8004/feedback/{subject}` |
| Validation shape | `GET https://studio.mizan.market/api/erc8004/validation/{subject}` |
| Registration file | <https://mizan.market/.well-known/agent-registration.json> |
| On-chain receipt check | [`MizanProof.sol`](./MizanProof.sol): `MizanProof.isProven(subject, receipt, signature)`, one `ecrecover`, no oracle, nothing deployed by MIZAN |
| Get a receipt | `GET https://studio.mizan.market/api/staple/{address}` (field `eip712[]`) |
| Signer | `eip712-receipt` in <https://studio.mizan.market/.well-known/mizan-keys.json> |

Receipts last 24 hours and state a fact about an identity; they authorise nothing. The feedback and validation readers return `"onchain": false`: they are served over HTTPS in the standard's shapes, not posted to a registry contract.

`MizanProof.sol` is MIT-licensed; import it into your own contract.
