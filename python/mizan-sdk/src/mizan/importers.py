"""mizan.importers — turn what a trading agent already has into MIZAN positions. The agent uploads nothing by hand.

Sources (all return a Book: rows × markets on the catalogue calendar, plus an honest `report`):
    hyperliquid(address)                 public fills + account value, no key
    freqtrade(path)                      backtest-result .json / .zip (also Jesse-style trade lists via trades_json)
    quantconnect(path, starting_cash)    LEAN backtest result JSON (Orders) or orders CSV
    tradingview(path, equity)            Strategy Tester "List of Trades" CSV export
    mt5(path, equity)                    MetaTrader 5 / cTrader HTML or CSV report (Deals table)
    fills(path_or_rows, equity)          any CSV/JSON of fills: time, symbol, side, size, price
    intervals(trades, markets)           the core: [{market, start, end, leverage}] → rows

Rules (no lookahead): row i is the move from bar-close i to bar-close i+1 and carries the exposure held AT close i.
A trade that opens after close i first counts on row i+1. Exposure = signed notional ÷ account equity at that time.

Honest limits (returned in every report, say them to the user):
  * The credential runs on the FULL catalogue window. Bars before the first trade and after the last are flat (0),
    which is scored as zero return — a short record therefore reads as low CAGR and will usually be refused.
    This is engine law today (no sub-window); the report shows `active_bars` vs `bars`.
  * Only markets in the MIZAN catalogue can be proven; exposure elsewhere is dropped and listed under `unmapped`.
  * Imported fills prove what the statement says, not what a broker filled: provenance is FILLS_IMPORTED, not exchange-bound.
  * Equity is taken from the source where it has it (Hyperliquid account value) else from `equity`/`starting_balance` you pass.
"""
from __future__ import annotations
import bisect, csv, io, json, os, re, time, urllib.request, zipfile
from dataclasses import dataclass, field

from . import BASE, MizanError, catalog as _catalog

_CAL: dict = {}
_UA = {"User-Agent": "mizan-sdk-importers/0.1"}


# ── calendar ────────────────────────────────────────────────────────────────
def calendar(key: str) -> dict:
    """Bar opens/closes (unix s) and closes (price) for a catalogue market, cached in memory."""
    if key in _CAL:
        return _CAL[key]
    cat = _catalog()
    if key not in cat:
        raise MizanError(f"unknown market '{key}'")
    r = urllib.request.Request(f"{BASE}/api/catalog/{key}.csv", headers=_UA)
    txt = urllib.request.urlopen(r, timeout=120).read().decode()
    rows = list(csv.DictReader(io.StringIO(txt)))
    secs = int(cat[key].get("interval_secs") or 0) or _infer_interval(rows)
    opens = [int(float(x["date"])) if str(x["date"]).replace(".", "").isdigit() else _parse_ts(x["date"]) for x in rows]
    closes = [o + secs for o in opens]
    px = [float(x["close"]) for x in rows]
    _CAL[key] = {"key": key, "opens": opens, "closes": closes, "close_px": px, "interval_secs": secs,
                 "bars": len(rows), "align_group": cat[key].get("align_group")}
    return _CAL[key]


def _infer_interval(rows) -> int:
    a, b = rows[0]["date"], rows[1]["date"]
    ta = int(float(a)) if str(a).replace(".", "").isdigit() else _parse_ts(a)
    tb = int(float(b)) if str(b).replace(".", "").isdigit() else _parse_ts(b)
    return tb - ta


def _parse_ts(s) -> int:
    """ISO-8601 / 'YYYY-MM-DD HH:MM' / unix s or ms → unix seconds (UTC)."""
    if s is None:
        raise MizanError("empty timestamp")
    if isinstance(s, (int, float)):
        return int(s / 1000) if s > 1e11 else int(s)
    s = str(s).strip()
    if re.fullmatch(r"\d{9,13}(\.\d+)?", s):
        v = float(s); return int(v / 1000) if v > 1e11 else int(v)
    s = s.replace("Z", "").replace("T", " ")
    s = re.sub(r"[+-]\d{2}:?\d{2}$", "", s)
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M"):
        try:
            import calendar as _c, datetime as _d
            return int(_c.timegm(_d.datetime.strptime(s, fmt).timetuple()))
        except ValueError:
            continue
    raise MizanError(f"unrecognised timestamp: {s!r}")


# ── symbol mapping ──────────────────────────────────────────────────────────
_STRIP = re.compile(r"(/USDT:USDT|/USDC:USDC|/USDT|/USD|/USDC|-USDT-SWAP|-USDT|-USD|-PERP|PERP|USDT|USDC|USD|\.P|\.US)$", re.I)


def map_symbol(sym: str, interval: str = "4h", cat: dict | None = None, cls: str | None = None) -> str | None:
    """'BTC/USDT:USDT' / 'BTCUSDT' / 'BTC-PERP' / 'kBONK' → catalogue key or None. cls='crypto'|'us' restricts the class,
    so a perp called ENA never maps to the US stock ENA."""
    cat = cat or _catalog()
    s = str(sym).strip()
    ok = lambda k: k in cat and (cls is None or str(cat[k].get("cls", "")).startswith(cls))
    if ok(s):
        return s
    base = _STRIP.sub("", s).strip().lstrip("k").lower()
    base = base.split(":")[0]
    for k in (f"{base}_{interval}", f"{base}_4h", f"{base}_1d", base, f"us_{base}"):
        if ok(k):
            return k
    return None


# ── the book ────────────────────────────────────────────────────────────────
@dataclass
class Book:
    markets: list[str]
    rows: list[list[int]]                      # bars-1 rows × K ints, signed leverage ×100
    report: dict = field(default_factory=dict)

    @property
    def gross_cap(self) -> float:
        return max((sum(abs(x) for x in r) for r in self.rows), default=0) / 100

    @property
    def leverages(self) -> list[list[float]]:
        """rows as floats (1.0 = 100% long), the unit mizan.prove() takes."""
        return [[x / 100 for x in r] for r in self.rows]

    def prove(self, alias: str = "IMPORTED-AGENT", **kw):
        from . import prove
        return prove(self.leverages, self.markets, alias=alias, gross_cap=max(1.0, self.gross_cap), **kw)

    def check_before_you_pay(self, **kw):
        from . import check_before_you_pay
        return check_before_you_pay(self.leverages, self.markets, gross_cap_x100=int(round(max(1.0, self.gross_cap) * 100)), **kw)

    def to_csv(self, path: str) -> str:
        cal = calendar(self.markets[0])
        with open(path, "w") as f:
            f.write("date," + ",".join(self.markets) + "\n")
            for i, r in enumerate(self.rows):
                f.write(time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(cal["closes"][i])) + "," + ",".join(f"{x/100:.4f}" for x in r) + "\n")
        return path


def _step_at(steps: list[tuple[int, float]], t: int) -> float:
    """steps sorted by time: value in force at time t (last change ≤ t), else 0."""
    i = bisect.bisect_right(steps, (t, float("inf")))
    return steps[i - 1][1] if i else 0.0


def from_steps(steps_by_market: dict[str, list[tuple[int, float]]], markets: list[str] | None = None, max_lev: float = 10.0) -> Book:
    """steps: market → [(unix_s, leverage_after)], sorted. Samples each market at every catalogue bar close.
    If markets is None, all mapped markets are used; ones on a different calendar are dropped (reported)."""
    explicit = markets is not None
    markets = markets or sorted(steps_by_market)
    if not markets:
        raise MizanError("no catalogue markets in this record (see report['unmapped'])")
    dropped = []
    groups: dict[str, list[str]] = {}
    for m in markets:
        groups.setdefault(calendar(m)["align_group"], []).append(m)
    if len(groups) != 1:
        if explicit:
            raise MizanError(f"markets in one book must share a calendar; got align groups {sorted(groups)}")
        keep = max(groups.values(), key=lambda ms: (len(ms), sum(len(steps_by_market.get(m, [])) for m in ms)))
        dropped = [m for m in markets if m not in keep]
        markets = keep
    cal = calendar(markets[0])
    closes = cal["closes"][:-1]                       # row i ↔ exposure at close i
    rows, clipped = [], 0
    for t in closes:
        r = []
        for m in markets:
            v = _step_at(steps_by_market.get(m, []), t)
            if abs(v) > max_lev:
                clipped += 1; v = max_lev if v > 0 else -max_lev
            r.append(int(round(v * 100)))
        rows.append(r)
    active = [i for i, r in enumerate(rows) if any(r)]
    rep = {"bars": cal["bars"], "rows": len(rows), "markets": markets,
           "active_bars": len(active),
           "active_from": time.strftime("%Y-%m-%d", time.gmtime(closes[active[0]])) if active else None,
           "active_to": time.strftime("%Y-%m-%d", time.gmtime(closes[active[-1]])) if active else None,
           "window": f"{time.strftime('%Y-%m-%d', time.gmtime(closes[0]))} → {time.strftime('%Y-%m-%d', time.gmtime(closes[-1]))}",
           "clipped_to_max_lev": clipped, "dropped_other_calendar": dropped,
           "honest": ["The credential runs on the full catalogue window; flat bars outside your record score as zero return, so a short record reads as low CAGR and is usually refused.",
                      "Only catalogue markets are proven; other exposure was dropped (report['unmapped']).",
                      "Imported fills prove what the statement says, not what a broker filled (provenance FILLS_IMPORTED)."]}
    if active and len(active) < 0.25 * len(rows):
        rep["warning"] = f"only {len(active)} of {len(rows)} bars have exposure ({100*len(active)/len(rows):.0f}%); expect the full-window gate to refuse this."
    return Book(markets, rows, rep)


def intervals(trades: list[dict], markets: list[str] | None = None, interval: str = "4h", cls: str | None = None) -> Book:
    """Core. trades: [{market|symbol, start, end, leverage}] with leverage = signed notional ÷ equity (+long/−short).
    Overlapping trades in one market add. `end` None = still open."""
    cat = _catalog()
    deltas: dict[str, list[tuple[int, float]]] = {}
    unmapped: dict[str, int] = {}
    for tr in trades:
        m = tr.get("market") or map_symbol(tr.get("symbol", ""), interval, cat, cls)
        if not m or m not in cat:
            unmapped[str(tr.get("symbol") or tr.get("market"))] = unmapped.get(str(tr.get("symbol") or tr.get("market")), 0) + 1
            continue
        lev = float(tr["leverage"])
        s = _parse_ts(tr["start"]); e = _parse_ts(tr["end"]) if tr.get("end") not in (None, "") else None
        deltas.setdefault(m, []).append((s, lev))
        if e is not None:
            deltas[m].append((e, -lev))
    steps = {}
    for m, ds in deltas.items():
        ds.sort(); cur = 0.0; out = []
        for t, d in ds:
            cur += d; out.append((t, round(cur, 6)))
        steps[m] = out
    book = from_steps(steps, markets or sorted(steps))
    book.report["unmapped"] = unmapped
    book.report["trades"] = len(trades)
    return book


# ── Hyperliquid ─────────────────────────────────────────────────────────────
HL_INFO = "https://api.hyperliquid.xyz/info"


def _hl(body: dict):
    r = urllib.request.Request(HL_INFO, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **_UA})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())


def hyperliquid(address: str, interval: str = "4h", markets: list[str] | None = None, start: str | int | None = None,
                max_pages: int = 100, fills: list[dict] | None = None, equity: list[tuple] | float | None = None) -> Book:
    """Perp fills → signed size per coin → notional at catalogue closes ÷ account value → leverage. Public API, no key.
    Account value is interpolated from the address's `portfolio` history (perpAllTime, coarse); say so."""
    address = address.strip()
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", address):
        raise MizanError("address must be 0x… (40 hex)")
    t0 = (_parse_ts(start) * 1000) if start else 0
    pages = 0
    if fills is None:
        fills = []
        while pages < max_pages:
            chunk = _hl({"type": "userFillsByTime", "user": address, "startTime": t0})
            fills += chunk; pages += 1
            if len(chunk) < 2000:
                break
            t0 = max(int(f["time"]) for f in chunk) + 1
    fills = sorted(fills, key=lambda f: (int(f["time"]), int(f.get("tid", 0))))
    # account value series (Hyperliquid keeps only the last ~10,000 fills per address; older history needs your own export)
    if isinstance(equity, (int, float)):
        eq = [(0, float(equity))]
    elif equity:
        eq = sorted((_parse_ts(t), float(v)) for t, v in equity)
    else:
        pf = dict(_hl({"type": "portfolio", "user": address}))
        hist = (pf.get("perpAllTime") or pf.get("allTime") or {}).get("accountValueHistory") or []
        eq = sorted((int(t) // 1000, float(v)) for t, v in hist if float(v) > 0)
    if not eq:
        raise MizanError("no account-value history for this address; pass equity=")
    cat = _catalog()
    size: dict[str, float] = {}
    steps: dict[str, list[tuple[int, float]]] = {}
    unmapped: dict[str, float] = {}
    cals: dict[str, dict] = {}
    for f in fills:
        coin = f["coin"]; t = int(f["time"]) // 1000
        sz = float(f["sz"]) * (1 if f["side"] == "B" else -1)
        size[coin] = float(f.get("startPosition", size.get(coin, 0.0))) + sz
        m = map_symbol(coin, interval, cat, cls="crypto")
        if not m:
            unmapped[coin] = unmapped.get(coin, 0.0) + abs(sz * float(f["px"]))
            continue
        cal = cals.setdefault(m, calendar(m))
        j = bisect.bisect_right(cal["closes"], t) - 1
        px = cal["close_px"][max(0, j)] if j >= 0 else float(f["px"])
        e = _step_at(eq, t) or eq[0][1]
        steps.setdefault(m, []).append((t, size[coin] * px / e))
    book = from_steps(steps, markets or sorted(steps))
    first_fill = time.strftime("%Y-%m-%d", time.gmtime(int(fills[0]["time"]) // 1000)) if fills else None
    last_fill = time.strftime("%Y-%m-%d", time.gmtime(int(fills[-1]["time"]) // 1000)) if fills else None
    book.report.update({"source": "hyperliquid", "address": address, "fills": len(fills), "pages": pages,
                        "fills_span": f"{first_fill} → {last_fill}", "api_limit": "Hyperliquid returns at most the last ~10,000 fills per address.",
                        "unmapped_notional": {k: round(v, 2) for k, v in sorted(unmapped.items(), key=lambda kv: -kv[1])[:20]},
                        "equity_points": len(eq), "provenance": "FILLS_IMPORTED",
                        "note": "Leverage uses Hyperliquid's own account-value history (sparse) and MIZAN catalogue closes (Binance), not Hyperliquid marks."})
    return book


# ── Freqtrade / Jesse ───────────────────────────────────────────────────────
def freqtrade(path: str, interval: str = "4h", starting_balance: float | None = None, strategy: str | None = None,
              markets: list[str] | None = None) -> Book:
    """freqtrade backtesting result (.json or the .zip it writes). Leverage = stake × leverage ÷ starting balance (constant)."""
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            name = [n for n in z.namelist() if n.endswith(".json") and not n.endswith(".meta.json")][0]
            data = json.loads(z.read(name))
    else:
        data = json.load(open(path))
    strat = data.get("strategy") or {}
    if not strat:
        raise MizanError("not a freqtrade backtest result (no 'strategy' key)")
    name = strategy or next(iter(strat))
    s = strat[name]
    bal = starting_balance or float(s.get("starting_balance") or s.get("dry_run_wallet") or 0) or None
    if not bal:
        raise MizanError("pass starting_balance (the result file has none)")
    trades = []
    for t in s.get("trades", []):
        lev = float(t.get("stake_amount", 0)) * float(t.get("leverage", 1) or 1) / bal
        if t.get("is_short"):
            lev = -lev
        trades.append({"symbol": t["pair"], "start": t["open_date"], "end": t.get("close_date"), "leverage": lev})
    book = intervals(trades, markets, interval, cls="crypto")
    book.report.update({"source": "freqtrade", "strategy": name, "starting_balance": bal, "provenance": "BACKTEST_IMPORTED"})
    return book


def trades_json(path_or_list, interval: str = "4h", equity: float = 1.0, markets: list[str] | None = None,
                keys: dict | None = None) -> Book:
    """Jesse / generic trade list. keys maps your names → {symbol,start,end,qty,entry_price,side}. Leverage = qty×entry ÷ equity."""
    k = {"symbol": "symbol", "start": "opened_at", "end": "closed_at", "qty": "qty", "price": "entry_price", "side": "type", **(keys or {})}
    rows = json.load(open(path_or_list)) if isinstance(path_or_list, str) else path_or_list
    trades = []
    for t in rows:
        lev = abs(float(t[k["qty"]])) * float(t[k["price"]]) / equity
        if str(t.get(k["side"], "long")).lower().startswith(("short", "sell", "s")):
            lev = -lev
        trades.append({"symbol": t[k["symbol"]], "start": t[k["start"]], "end": t.get(k["end"]), "leverage": lev})
    book = intervals(trades, markets, interval)
    book.report.update({"source": "trades_json", "equity": equity})
    return book


# ── fills (generic, QuantConnect, TradingView, MT5) ─────────────────────────
def fills(rows_or_path, equity: float | list[tuple] = 1.0, interval: str = "4h", markets: list[str] | None = None,
          keys: dict | None = None) -> Book:
    """Any fills table: time, symbol, side (buy/sell or signed), size, price → running signed notional ÷ equity.
    equity: a constant, or [(time, equity)] to interpolate."""
    k = {"time": "time", "symbol": "symbol", "side": "side", "size": "size", "price": "price", **(keys or {})}
    if isinstance(rows_or_path, str):
        txt = open(rows_or_path).read()
        rows = json.loads(txt) if txt.lstrip()[:1] in "[{" else list(csv.DictReader(io.StringIO(txt)))
        if isinstance(rows, dict):
            rows = rows.get("fills") or rows.get("orders") or list(rows.values())[0]
    else:
        rows = rows_or_path
    eq = sorted((_parse_ts(t), float(v)) for t, v in equity) if isinstance(equity, list) else None
    cat = _catalog()
    ev = []
    for r in rows:
        t = _parse_ts(r[k["time"]]); sym = r[k["symbol"]]
        qty = float(r[k["size"]]); side = str(r.get(k["side"], "")).lower()
        if side.startswith(("sell", "s", "short", "a")) or side in ("-1",):
            qty = -abs(qty)
        elif side:
            qty = abs(qty)
        ev.append((t, sym, qty, float(r[k["price"]])))
    ev.sort()
    pos: dict[str, float] = {}; steps: dict[str, list] = {}; unmapped: dict[str, int] = {}
    for t, sym, qty, px in ev:
        m = map_symbol(sym, interval, cat)
        if not m:
            unmapped[sym] = unmapped.get(sym, 0) + 1; continue
        pos[m] = pos.get(m, 0.0) + qty
        e = (_step_at(eq, t) or eq[0][1]) if eq else float(equity)
        steps.setdefault(m, []).append((t, pos[m] * px / e))
    book = from_steps(steps, markets or sorted(steps))
    book.report.update({"source": "fills", "fills": len(ev), "unmapped": unmapped, "provenance": "FILLS_IMPORTED"})
    return book


def quantconnect(path: str, starting_cash: float, interval: str = "4h", markets: list[str] | None = None) -> Book:
    """LEAN backtest result JSON (the `Orders` map) or an orders CSV (Time, Symbol, Quantity, Price, Status)."""
    txt = open(path).read()
    if txt.lstrip().startswith("{"):
        d = json.loads(txt); orders = d.get("Orders") or d.get("orders") or {}
        rows = [{"time": o.get("LastFillTime") or o.get("Time") or o.get("time"), "symbol": (o.get("Symbol") or {}).get("Value") if isinstance(o.get("Symbol"), dict) else o.get("Symbol") or o.get("symbol"),
                 "size": o.get("Quantity") or o.get("quantity"), "price": o.get("Price") or o.get("price"), "side": ""}
                for o in (orders.values() if isinstance(orders, dict) else orders) if str(o.get("Status", o.get("status", 3))) in ("3", "Filled", "filled")]
    else:
        rows = [{"time": r.get("Time") or r.get("time"), "symbol": r.get("Symbol") or r.get("symbol"), "size": r.get("Quantity") or r.get("quantity"),
                 "price": r.get("Price") or r.get("price"), "side": ""} for r in csv.DictReader(io.StringIO(txt))]
    book = fills(rows, starting_cash, interval, markets)
    book.report.update({"source": "quantconnect", "starting_cash": starting_cash, "provenance": "BACKTEST_IMPORTED"})
    return book


def tradingview(path: str, equity: float, interval: str = "4h", symbol: str | None = None, markets: list[str] | None = None) -> Book:
    """TradingView Strategy Tester → 'List of Trades' export (CSV/XLSX-as-CSV). Columns: Trade #, Type, Signal, Date/Time, Price, Contracts."""
    rows = list(csv.DictReader(open(path, newline="")))
    sym = symbol or os.path.basename(path).split("_")[0]
    ev = []
    for r in rows:
        typ = str(r.get("Type") or r.get("type") or "").lower()
        if not typ:
            continue
        qty = abs(float(str(r.get("Contracts") or r.get("Quantity") or 1).replace(",", "")))
        px = float(str(r.get("Price") or r.get("Price USD") or 0).replace(",", "")) or 0.0
        t = r.get("Date/Time") or r.get("Date") or r.get("time")
        long_ = "long" in typ; entry = "entry" in typ
        signed = qty if (long_ == entry) else -qty
        ev.append({"time": t, "symbol": sym, "size": signed, "price": px, "side": ""})
    book = fills(ev, equity, interval, markets)
    book.report.update({"source": "tradingview", "symbol": sym, "equity": equity, "provenance": "BACKTEST_IMPORTED"})
    return book


def mt5(path: str, equity: float, interval: str = "1d", markets: list[str] | None = None) -> Book:
    """MetaTrader 5 Strategy Tester / account report (HTML or CSV): the Deals table (Time, Symbol, Type, Direction, Volume, Price)."""
    txt = open(path, encoding="utf-8", errors="ignore").read()
    if "<table" in txt.lower() or "<tr" in txt.lower():
        cells = [[re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
                 for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", txt, re.S | re.I)]
        hdr_i = next((i for i, c in enumerate(cells) if c and "Symbol" in c and ("Volume" in c or "Direction" in c)), None)
        if hdr_i is None:
            raise MizanError("no Deals table found in this report")
        hdr = cells[hdr_i]; rows = [dict(zip(hdr, c)) for c in cells[hdr_i + 1:] if len(c) >= len(hdr) - 1]
    else:
        rows = list(csv.DictReader(io.StringIO(txt)))
    ev = []
    for r in rows:
        sym = r.get("Symbol") or ""; vol = r.get("Volume") or r.get("Lots") or ""; px = r.get("Price") or ""
        if not sym or not vol or not px:
            continue
        typ = (r.get("Type") or "").lower(); direction = (r.get("Direction") or "").lower()
        try:
            q = float(str(vol).replace(" ", "").split("/")[0]); p = float(str(px).replace(" ", "").replace(",", ""))
        except ValueError:
            continue
        signed = q if typ.startswith("buy") else -q
        if direction.startswith("out"):
            pass  # a closing deal already carries the opposite type
        ev.append({"time": r.get("Time") or r.get("Open time"), "symbol": sym, "size": signed, "price": p, "side": ""})
    book = fills(ev, equity, interval, markets)
    book.report.update({"source": "mt5", "equity": equity, "note": "Volume is in lots as reported; scale `equity` to the same unit (e.g. lots × contract size)."})
    return book


SOURCES = {"hyperliquid": hyperliquid, "freqtrade": freqtrade, "jesse": trades_json, "quantconnect": quantconnect,
           "tradingview": tradingview, "mt5": mt5, "ctrader": mt5, "fills": fills}
