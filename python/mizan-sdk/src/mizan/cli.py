"""mizan — the command line for the answer a machine cannot fake.

  mizan verify <file|address>      free: run the gate on your record, see every check, nothing minted
  mizan verify <src> --prove       mint the credential for real (needs an API key; real proofs run on the GPU prover)
  mizan check <agent>              before you pay: ALLOW or REFUSE, signed, with every check
  mizan me                         your listing and state on the agent registry (needs an API key)
  mizan markets                    the canonical markets a record can be proven on

Sources for verify are detected automatically:
  0x… (40 hex)        Hyperliquid account          *.zip   Freqtrade backtest result
  *.html / *.htm      MetaTrader 5 / cTrader report *.json  QuantConnect (Orders) or Jesse trades
  *.csv               TradingView "List of trades", a fills CSV (time, side, price, qty), or a positions CSV (--markets)
Override with --from. Exit code: 0 pass / ALLOW, 1 refuse / REFUSE, 2 error. Usable in CI.
A credential attests to the honesty of a record, never to future returns. The method never leaves your machine:
only one position per bar is sent.
"""
import argparse, json, os, re, sys

STUDIO = "https://studio.mizan.market"
SITE = "https://mizan.market"


# ── presentation ──────────────────────────────────────────────────────────────
class _C:
    on = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    def _w(code):
        return lambda s: f"\033[{code}m{s}\033[0m" if _C.on else str(s)
    bold, dim, green, red, amber, navy = _w("1"), _w("2"), _w("32"), _w("31"), _w("33"), _w("34")


def _rule(title=""):
    w = 64
    if not title:
        return _C.dim("─" * w)
    return _C.dim("── ") + _C.bold(title) + " " + _C.dim("─" * max(2, w - len(title) - 4))


def _fmt(v, unit=""):
    if v is None:
        return "—"
    if isinstance(v, float):
        v = int(v) if v == int(v) else round(v, 2)
    return f"{v}{unit if unit not in ('',) else ''}"


# ── source detection ──────────────────────────────────────────────────────────
def detect(source: str) -> str:
    s = source.strip()
    if re.fullmatch(r"0x[0-9a-fA-F]{40}", s):
        return "hyperliquid"
    low = s.lower()
    if low.endswith(".zip"):
        return "freqtrade"
    if low.endswith((".html", ".htm")):
        return "mt5"
    if low.endswith(".json"):
        try:
            head = open(s, "r", errors="ignore").read(4000)
        except OSError:
            return "jesse"
        return "quantconnect" if ('"Orders"' in head or '"orders"' in head or "TotalPerformance" in head) else "jesse"
    if low.endswith((".csv", ".tsv", ".txt")):
        try:
            head = open(s, "r", errors="ignore").readline().lower()
        except OSError:
            return "positions"
        if "trade #" in head or ("type" in head and "signal" in head):
            return "tradingview"
        if any(k in head for k in ("side", "qty", "quantity")) and "price" in head:
            return "fills"
        return "positions"
    return "positions"


def _book(a):
    import mizan
    from . import importers as im
    src = a.src if a.src != "auto" else detect(a.source)
    mk = a.markets.split(",") if a.markets else None
    if src == "positions":
        if not mk:
            raise SystemExit(_C.red("a positions file needs --markets (see: mizan markets)"))
        rows = open(a.source).read().split() if os.path.exists(a.source) else a.source
        return src, im.Book(mk, mizan._rows(rows, len(mk)), {"source": "positions"})
    if src == "hyperliquid":
        return src, im.hyperliquid(a.source, a.interval, mk)
    if src == "freqtrade":
        return src, im.freqtrade(a.source, a.interval, a.equity, markets=mk)
    if src == "quantconnect":
        if not a.equity: raise SystemExit(_C.red("QuantConnect needs --balance"))
        return src, im.quantconnect(a.source, a.equity, a.interval, mk)
    if src == "tradingview":
        if not a.equity: raise SystemExit(_C.red("TradingView needs --balance"))
        return src, im.tradingview(a.source, a.equity, a.interval, markets=mk)
    if src in ("mt5", "ctrader"):
        if not a.equity: raise SystemExit(_C.red("MT5 / cTrader needs --balance"))
        return src, im.mt5(a.source, a.equity, a.interval, mk)
    if src == "jesse":
        return src, im.trades_json(a.source, a.interval, a.equity or 1.0, mk)
    return src, im.fills(a.source, a.equity or 1.0, a.interval, mk)


# ── verify ────────────────────────────────────────────────────────────────────
def _print_verdict(r: dict, src: str, book) -> int:
    f = r.get("forensic") or {}
    passed = bool(r.get("gate_pass") if "gate_pass" in r else f.get("passed"))
    print()
    print(_C.bold("MIZAN") + _C.dim("  ·  the answer a machine cannot fake"))
    print(_rule())
    rep = getattr(book, "report", {}) or {}
    mk = rep.get("markets") or getattr(book, "markets", None)
    print(f"  source   {src}" + (f"   markets {', '.join(mk) if isinstance(mk, list) else mk}" if mk else ""))
    print(f"  bars     {r.get('n_periods', '—')}   gate class {f.get('gate_class', '—')}")
    print()
    verdict = _C.green(_C.bold("  PASS  would clear the gate")) if passed else _C.red(_C.bold("  REFUSE  would not clear the gate"))
    print(verdict)
    print(f"  Sharpe {_fmt(r.get('sharpe'))}   CAGR {_fmt(r.get('cagr'))}%   max drawdown {_fmt(r.get('maxdd'))}%")
    print()
    print(_rule("every gate, the same for everyone"))
    for g in f.get("gates", []):
        ok = g.get("pass")
        mark = _C.green("✓") if ok else _C.red("✗")
        if "threshold" in g:
            line = f"  {mark} {g.get('label',''):44.44s} {_fmt(g.get('value'))}{g.get('unit','') if g.get('unit','') not in ('',) else ''}  {_C.dim(g.get('kind','')+' '+_fmt(g.get('threshold')))}"
        else:
            line = f"  {mark} {g.get('label','')}"
        print(line)
    fails = [g for g in f.get("gates", []) if not g.get("pass") and "threshold" in g]
    if fails:
        print()
        print(_rule("what would pass"))
        for g in fails:
            print(f"  {g.get('label','')}: needs {g.get('kind','')} {_fmt(g.get('threshold'))}{g.get('unit','')}, you have {_fmt(g.get('value'))}{g.get('unit','')}")
    print()
    print(_rule())
    if r.get("attempt_counted"):
        print(_C.dim(f"  This attempt was counted for identity {r.get('identity_hash','')} and will show on any credential it mints."))
    print(_C.dim("  Free preview. Nothing minted, nothing charged, your method never left this machine."))
    if passed:
        print("  Mint it for real:  " + _C.bold("mizan verify <same source> --prove") + _C.dim("   (API key: mizan key, or MIZAN_API_KEY)"))
    else:
        print(_C.dim("  A refusal at preview is private. A minted refusal is published, like ours."))
    print()
    return 0 if passed else 1


def cmd_verify(a) -> int:
    import mizan
    if a.api_key or os.environ.get("MIZAN_API_KEY"):
        mizan.login(api_key=a.api_key or os.environ["MIZAN_API_KEY"])
    src, book = _book(a)
    if a.prove:
        cred = book.prove(alias=a.alias, out_dir=a.out)
        url = getattr(cred, "url", None)
        print(_C.bold("Minting started.") + (f"  {url}" if url else f"  {cred}"))
        print(_C.dim("Your credential page, badge and listing appear there when the proof completes; a refusal is published too."))
        return 0
    r = book.check_before_you_pay()
    if a.json:
        print(json.dumps({k: v for k, v in r.items() if k != "provenance"}, indent=2))
        return 0 if r.get("gate_pass") else 1
    if r.get("error"):
        print(_C.red("error: ") + str(r["error"])); return 2
    return _print_verdict(r, src, book)


# ── check ─────────────────────────────────────────────────────────────────────
def cmd_check(a) -> int:
    import mizan
    body = {"agent": a.agent}
    if a.amount is not None: body["amount"] = a.amount
    if a.currency: body["currency"] = a.currency
    if a.policy_id: body["policy_id"] = a.policy_id
    if a.require_forward: body["require_forward"] = True
    try:
        r = mizan._req("/api/allocate-check", body)
    except Exception as e:  # fail closed
        print(_C.red("REFUSE") + f"  unverifiable (network or server error): {str(e)[:120]}")
        return 1
    if a.json:
        print(json.dumps({k: v for k, v in r.items() if k != "provenance"}, indent=2))
        return 0 if r.get("decision") == "ALLOW" else 1
    dec = r.get("decision", "REFUSE")
    print()
    print(_C.bold("MIZAN") + _C.dim("  ·  before money moves"))
    print(_rule())
    print(f"  {a.agent}")
    print((_C.green(_C.bold("  ALLOW")) if dec == "ALLOW" else _C.red(_C.bold("  REFUSE"))) + _C.dim("   a decision about the credential, never advice"))
    print()
    for c in r.get("checks", []):
        mark = _C.green("✓") if c.get("ok") else _C.red("✗")
        print(f"  {mark} {c.get('check',''):34.34s} {_C.dim(str(c.get('detail',''))[:60])}")
    if dec != "ALLOW" and r.get("reasons"):
        print()
        for x in r["reasons"][:4]:
            print("  " + _C.amber("reason ") + str(x))
    if r.get("token"):
        print()
        print(_C.dim("  signed token (keep it, valid 24 h, verify offline):"))
        print("  " + str(r["token"])[:72] + "…")
    print(_rule())
    print(_C.dim(f"  Same answer at {SITE}/scan/ and over MCP: {STUDIO}/mcp"))
    print()
    return 0 if dec == "ALLOW" else 1


# ── me / markets / key ────────────────────────────────────────────────────────
def cmd_me(a) -> int:
    import mizan
    key = a.api_key or os.environ.get("MIZAN_API_KEY")
    if not key:
        print("needs an API key: mizan key  (or MIZAN_API_KEY)"); return 2
    mizan.login(api_key=key)
    r = mizan._req("/api/agents/me")
    st = r.get("state", "?")
    col = {"PROVEN": _C.green, "REFUSED": _C.red}.get(st, _C.dim)
    print(f"\n  {_C.bold(r.get('name',''))}  {col(st)}\n  {r.get('listing','')}\n  next: {r.get('next_step','')}\n")
    return 0


# ── staple / doctor ───────────────────────────────────────────────────────────
def cmd_staple(a) -> int:
    import urllib.request, json as _j
    try:
        with urllib.request.urlopen(urllib.request.Request(f"{STUDIO}/api/staple/{a.identity}", headers={"User-Agent": "mizan-cli"}), timeout=30) as r:
            d = _j.loads(r.read())
    except urllib.error.HTTPError as e:
        d = _j.loads(e.read() or b"{}")
    if a.json:
        print(_j.dumps(d, indent=1)); return 0 if d.get("ok") else 1
    if not d.get("ok"):
        print(f"\n  {_C.red('NO RECEIPT')}  {a.identity}\n  {'; '.join(d.get('reasons') or [d.get('error','')])}\n  next: {d.get('next','')}\n"); return 1
    t = d["receipt"]
    print(f"\n  {_C.green('STAPLED')}  {a.identity}  ·  {d['payload']['sub']}  ·  {d['bytes']} bytes  ·  refresh before {d['refresh_before_utc']}\n")
    print(_C.dim("  attach one of these, then buyers verify locally with zero calls to MIZAN:\n"))
    print(f"  HTTP header      X-Mizan-Receipt: {t[:48]}…")
    print(f"  x402 terms       accepts[i].extra.mizan = {{\"receipt\": \"{t[:24]}…\"}}")
    print(f"  well-known       /.well-known/mizan.json = {{\"receipt\": \"{t[:24]}…\", \"refresh\": \"{STUDIO}/api/staple/{a.identity}\"}}")
    print(f"  automatic        app.use(mizanStaple({{ identity: \"{a.identity}\" }}))  ·  or Python: MizanStaple(app, identity=\"{a.identity}\")\n")
    if a.out:
        open(a.out, "w").write(t); print(_C.dim(f"  receipt written to {a.out}\n"))
    return 0


def cmd_doctor(a) -> int:
    root = os.path.abspath(a.path or ".")
    found = []
    def has(name):
        return os.path.exists(os.path.join(root, name))
    def text(name):
        try: return open(os.path.join(root, name)).read()
        except Exception: return ""
    pkg = text("package.json"); req = text("requirements.txt") + text("pyproject.toml")
    if "x402" in pkg or "x402" in req: found.append(("x402 payments", "pay = guardFetch(fetchWithPayment, { mode: \"advise\" })  // import { guardFetch } from \"https://mizan.market/skill/mizan-x402-guard.mjs\"" if pkg else "pay = guard(my_paying_get)  # from mizan.x402guard import guard"))
    if "express" in pkg or "hono" in pkg: found.append(("selling over HTTP", "app.use(mizanStaple({ identity: \"<wallet you are paid at>\" }))  // import { mizanStaple } from \"https://mizan.market/skill/mizan-staple.mjs\""))
    if "fastapi" in req or "starlette" in req: found.append(("selling over HTTP", "MizanStaple(app, identity=\"<wallet you are paid at>\")  # from mizan.staple import MizanStaple"))
    if "langchain" in req or "crewai" in req or "langchain" in pkg: found.append(("agent framework", "tools += mizan_tools()  # pip install mizan-agent-tools"))
    if "@modelcontextprotocol" in pkg or "mcp" in req: found.append(("MCP", "claude mcp add --transport http mizan https://studio.mizan.market/mcp"))
    if has("index.html") or "react" in pkg or "next" in pkg: found.append(("a site that lists agents", "<span data-mizan-agent=\"<agent id>\"></span><script src=\"https://mizan.market/skill/mizan-label.js\" defer></script>"))
    print(f"\n  {_C.bold('mizan doctor')}  {root}\n")
    if not found:
        print("  Nothing specific detected. The one line for any agent:\n  claude mcp add --transport http mizan https://studio.mizan.market/mcp\n"); return 0
    for what, line in found:
        print(f"  {_C.green('+')} {what}\n    {line}\n")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="mizan", description="The answer a machine cannot fake. Prove the claim. Never reveal the method.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify", help="free check of your record against the gate; --prove to mint")
    v.add_argument("source", help="file path or Hyperliquid address (0x…)")
    v.add_argument("--from", dest="src", default="auto", choices=["auto", "positions", "hyperliquid", "freqtrade", "jesse", "quantconnect", "tradingview", "mt5", "ctrader", "fills"])
    v.add_argument("--markets", help="comma-separated catalogue keys (mizan markets)")
    v.add_argument("--interval", default="4h")
    v.add_argument("--balance", "--equity", dest="equity", type=float)
    v.add_argument("--prove", action="store_true", help="mint for real (needs an API key)")
    v.add_argument("--alias", default="IMPORTED-AGENT")
    v.add_argument("--out", default=".")
    v.add_argument("--api-key")
    v.add_argument("--json", action="store_true")
    c = sub.add_parser("check", help="before you pay: ALLOW or REFUSE, signed")
    c.add_argument("agent", help="credential id, alias, wallet, ERC-8004 id, agent-card URL or registry id (ag_…)")
    c.add_argument("--amount", type=float); c.add_argument("--currency", default="USD")
    c.add_argument("--policy-id"); c.add_argument("--require-forward", action="store_true")
    c.add_argument("--json", action="store_true")
    m = sub.add_parser("me", help="your listing on the agent registry"); m.add_argument("--api-key")
    sub.add_parser("markets", help="canonical markets")
    k = sub.add_parser("key", help="create an API key for the signed-in account"); k.add_argument("--label", default="agent")
    p = sub.add_parser("prove", help="(legacy) python -m mizan prove …"); p.add_argument("rest", nargs=argparse.REMAINDER)
    st = sub.add_parser("staple", help="get a signed receipt for the identity you are paid as; buyers verify it with zero calls to MIZAN")
    st.add_argument("identity", help="the wallet, host, agent id or credential id you are paid as"); st.add_argument("--out"); st.add_argument("--json", action="store_true")
    dr = sub.add_parser("doctor", help="find the one line to add to this project"); dr.add_argument("path", nargs="?")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "verify": return cmd_verify(a)
        if a.cmd == "check": return cmd_check(a)
        if a.cmd == "me": return cmd_me(a)
        if a.cmd == "staple": return cmd_staple(a)
        if a.cmd == "doctor": return cmd_doctor(a)
        import mizan
        if a.cmd == "markets":
            for key, val in mizan.catalog().items():
                print(f"{key:14s} {val.get('first','')} → {val.get('last','')}  {val.get('bars')} bars")
            return 0
        if a.cmd == "key":
            print(mizan.create_api_key(a.label)); return 0
        if a.cmd == "prove":
            from .__main__ import main as legacy
            return legacy(["prove"] + a.rest)
    except SystemExit:
        raise
    except Exception as e:
        print(_C.red("error: ") + str(e)[:300]); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
