# Check before you pay

Before an agent pays, hires or allocates to anyone, one free call returns a signed **ALLOW** or **REFUSE**. Proceed only on ALLOW, and only after the signature checks out against MIZAN's published key.

```bash
./check.sh                                   # curl + jq
node --experimental-strip-types check.ts     # TypeScript, Node 22.6+ (plain `node` on 23.6+)
python3 check.py                             # Python, stdlib (+ cryptography for the signature step)
python3 check.py seller.example              # anything: agent id, domain, wallet, endpoint, ERC-8004 id
```

Expected output (the default subject has a proven record):

```
subject:   mizan-flagship
decision:  ALLOW (proven, rung PROVEN)
signature: ✓ valid (key 2266fb495f83b0a0)
→ pay
```

A subject with nothing proven gets `REFUSE (no_record)`: unproven, which is not the same as false. With `POST /api/check {"agent": …, "amount": …}` a REFUSE also carries a `proof_request` you can forward to the other side; when it proves itself, your next check returns ALLOW.
