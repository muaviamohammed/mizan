"""Pin a requirement: write your bar in plain words, read it back, and pin its hash.

Compiling is free and needs no key. Nothing is published: publishing (POST /api/requirements with
confirm: true) needs an API key and is a separate, deliberate step. This example never does it.

    python3 pin.py ["your bar in plain words"]
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "verify", "python"))
from mizan_verify import DEFAULT_API, get_json  # noqa: E402

text = sys.argv[1] if len(sys.argv) > 1 else "only agents proven for 6 months, forward only, with a verified company domain"
c = get_json(DEFAULT_API + "/api/requirements/compile", {"text": text})

# The hash rule (returned by the API): SHA-256 over the requirement object exactly as returned,
# keys sorted, separators ',' and ':', non-ASCII escaped.
local = hashlib.sha256(json.dumps(c["requirement"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()

print(f"your words:  {text}")
print(f"read back:   {c['shown_back']}")
print(f"unmatched:   {c['unmatched'] or 'none (every word was used)'}")
print(f"hash (API):  {c['hash']}")
print(f"hash (here): {local}  {'✓ match' if local == c['hash'] else '✗ MISMATCH'}")

again = get_json(DEFAULT_API + "/api/requirements/compile", {"text": text})
print(f"recompiled:  {'✓ same hash, deterministic' if again['hash'] == c['hash'] else '✗ hash changed'}")
print(f"\npin this in your code: REQUIREMENT_SHA256 = \"{local}\"")
print("publish only when the read-back says what you meant:", c["publish"]["call"], "(API key, confirm: true)")
if c["unmatched"]:
    print("some words were not used: edit them and compile again before you pin or publish")
sys.exit(0 if local == c["hash"] == again["hash"] and not c["unmatched"] else 1)
