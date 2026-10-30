#!/bin/sh
# Fails if the tree contains anything that must never be published: keys, tokens, private paths,
# private IPs, env files, unexpected email addresses, or names of private mechanisms.
set -u
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
FILES=$(git ls-files 2>/dev/null || find . -type f -not -path './.git/*')
fail=0
hit() { echo "LEAK [$1]:"; echo "$2" | sed 's/^/   /'; fail=1; }
scan() { # label, extended regex, extra grep flags
  out=$(echo "$FILES" | grep -v -e '^\.github/scripts/leak-scan\.sh$' -e 'package-lock\.json$' -e '^LICENSE-SPEC$' \
        | xargs grep -n -I -E $3 "$2" 2>/dev/null | head -20)
  [ -n "$out" ] && hit "$1" "$out"
}
scan "private key block"   '-----BEGIN [A-Z ]*PRIVATE KEY-----' ''
scan "MIZAN API key"       'mzn_[A-Za-z0-9]{16,}' ''
scan "GitHub token"        'gh[pousr]_[A-Za-z0-9]{30,}' ''
scan "AWS key"             'AKIA[0-9A-Z]{16}' ''
scan "Slack/Telegram/OpenAI/Anthropic token" '(xox[baprs]-[A-Za-z0-9-]{10,}|[0-9]{8,10}:AA[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9]{32,}|sk-ant-[A-Za-z0-9_-]{20,})' ''
scan "hex secret assignment" '(secret|private_key|privkey|password|api_key)["'"'"' ]*[:=] *["'"'"'][0-9a-fA-F]{32,}' '-i'
scan "local path"          '(/Users/[a-z]|/home/[a-z]+/|C:\\\\Users\\\\|/private/tmp/|founder_desk|mizan-proof)' ''
scan "private IP"          '(\b10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b|\b192\.168\.[0-9]{1,3}\.[0-9]{1,3}\b|\b172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}\b)' ''
scan "private mechanism name" '(nullifier|moment aggregation|rail attestation|log quorum|counted runtime|PROBATUM|reglog|regbind)' '-i'
emails=$(echo "$FILES" | grep -v -e 'package-lock\.json$' -e '^LICENSE-SPEC$' | xargs grep -h -o -I -E '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' 2>/dev/null \
         | sort -u | grep -v -x -e 'muavia@mizan.market' -e 'git@github.com' -e 'noreply@anthropic.com')
[ -n "$emails" ] && hit "unexpected email" "$emails"
envs=$(echo "$FILES" | grep -E '(^|/)\.env($|\.)|\.pem$|\.key$|id_rsa|id_ed25519')
[ -n "$envs" ] && hit "secret-bearing file" "$envs"
[ $fail -eq 0 ] && echo "leak scan: clean ($(echo "$FILES" | wc -l | tr -d ' ') files)"
exit $fail
