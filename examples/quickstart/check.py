# 60 seconds, standard library only: check, then pay only on ALLOW.
import json, urllib.request

d = json.load(urllib.request.urlopen("https://studio.mizan.market/api/check/try-me"))
print(d["decision"], d.get("grade") or d.get("evidence_rung"))   # ALLOW PROVEN (mizan.verdict/1; ?format=legacy for the previous shape)
print(d.get("explain") or d.get("token", "")[:24] + "…")
if d["decision"] != "ALLOW":
    raise SystemExit("do not pay")
