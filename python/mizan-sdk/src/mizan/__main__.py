"""python -m mizan prove --from freqtrade result.zip --balance 10000 [--markets btc_4h,eth_4h] [--alias NAME] [--check-only]"""
import argparse, json, sys


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mizan", description="Prove the edge. Never reveal the model.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prove", help="import a record and mint (or just check) a credential")
    p.add_argument("source", nargs="?", default="-", help="file path, Hyperliquid address, or '-' for a positions CSV via --positions")
    p.add_argument("--from", dest="src", default="positions", choices=["positions", "hyperliquid", "freqtrade", "jesse", "quantconnect", "tradingview", "mt5", "ctrader", "fills"])
    p.add_argument("--markets", help="comma-separated catalogue keys (default: everything the record maps to)")
    p.add_argument("--interval", default="4h")
    p.add_argument("--balance", "--equity", dest="equity", type=float, help="starting balance / equity for sources that lack one")
    p.add_argument("--alias", default="IMPORTED-AGENT")
    p.add_argument("--check-only", action="store_true", help="free: verdict + exact price, nothing minted")
    p.add_argument("--api-key", help="mzn_… (or MIZAN_API_KEY)")
    p.add_argument("--out", default=".")
    k = sub.add_parser("key", help="create an API key for the signed-in account"); k.add_argument("--label", default="agent")
    m = sub.add_parser("markets", help="list catalogue markets")
    a = ap.parse_args(argv)
    import mizan
    if a.cmd == "markets":
        for key, v in mizan.catalog().items():
            print(f"{key:14s} {v.get('first','')} → {v.get('last','')}  {v.get('bars')} bars  {v.get('align_group','')}")
        return 0
    if a.cmd == "key":
        print(mizan.create_api_key(a.label)); return 0
    if a.api_key:
        mizan.login(api_key=a.api_key)
    mk = a.markets.split(",") if a.markets else None
    from . import importers as im
    if a.src == "positions":
        rows, markets = a.source, mk
        if not markets:
            sys.exit("positions CSV needs --markets")
        book = im.Book(markets, mizan._rows(rows, len(markets)), {"source": "positions"})
    elif a.src == "hyperliquid":
        book = im.hyperliquid(a.source, a.interval, mk)
    elif a.src == "freqtrade":
        book = im.freqtrade(a.source, a.interval, a.equity, markets=mk)
    elif a.src in ("quantconnect",):
        if not a.equity: sys.exit("--balance required")
        book = im.quantconnect(a.source, a.equity, a.interval, mk)
    elif a.src == "tradingview":
        if not a.equity: sys.exit("--equity required")
        book = im.tradingview(a.source, a.equity, a.interval, markets=mk)
    elif a.src in ("mt5", "ctrader"):
        if not a.equity: sys.exit("--equity required")
        book = im.mt5(a.source, a.equity, a.interval, mk)
    elif a.src == "jesse":
        book = im.trades_json(a.source, a.interval, a.equity or 1.0, mk)
    else:
        book = im.fills(a.source, a.equity or 1.0, a.interval, mk)
    print(json.dumps(book.report, indent=2), file=sys.stderr)
    if a.check_only:
        print(json.dumps(book.check_before_you_pay(), indent=2)); return 0
    cred = book.prove(alias=a.alias, out_dir=a.out)
    print(getattr(cred, "url", cred)); return 0


if __name__ == "__main__":
    sys.exit(main())
