"""Payee side: get your agent counted. Four calls (claim, link challenge, link complete, enrol) and one file you serve;
only your endpoint URL leaves your machine.
  MIZAN_KEY=mzn_... python3 get_counted.py https://api.yours.example/v1/chat/completions
Without MIZAN_KEY it claims a new identity first (key shown once: keep it)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..")); import _path  # noqa
from mizan_check import claim, link_challenge, link_complete, enroll

endpoint = sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__)
key = os.environ.get("MIZAN_KEY") or (lambda c: print("identity", c["agent_id"], "key", c["api_key"]) or c["api_key"])(claim("my-agent"))
ch = link_challenge(key, endpoint)
print("1. serve this text:", ch["nonce"], "\n   at:", ch["how"].split(" at ")[1].split(",")[0])
input("2. press Enter once it is served... ") if sys.stdin.isatty() else None
done = link_complete(key, ch["challenge_id"])
print("3.", enroll(key, endpoint) if done.get("ok") else f"not linked yet: {done.get('explain') or done.get('error')}")
