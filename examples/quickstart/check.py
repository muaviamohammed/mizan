# 60 seconds, standard library only: check, then pay only on ALLOW.
import json, urllib.request

d = json.load(urllib.request.urlopen("https://studio.mizan.market/api/check/try-me"))
print(d["decision"], d["evidence_rung"])          # ALLOW PROVEN
print(d["explain"])
if d["decision"] != "ALLOW":
    raise SystemExit("do not pay")
