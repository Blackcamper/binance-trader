"""US stocks paper run (virtual money only): the same textbook rules as the crypto arms,
on daily bars of US shares and ETFs, valued in DKK.

Separate run from sim-v2 with its own config hash and data folder, so the crypto run
is never touched. Stdlib only; public daily bars from Yahoo, Stooq as fallback.

Live: there is no order book to walk for shares, so each hour the run is replayed from
its fixed start date over the freshly fetched daily bars: decision on a closed daily
bar, fill at the next session's open plus half a spread and slippage. Replaying the
split-adjusted history handles share splits for free. Every decision is also written
to an append-only journal, and a replay that disagrees with a journaled decision is
reported as a mismatch, so the history cannot quietly change under the run.

Costs (assumption, check against the real broker): brokerage fee_rate with a DKK
minimum plus fx_fee for USD conversion, on both sides. Tax: Danish share income
(aktieindkomst) on realised gains, FIFO in DKK at the day's USD/DKK rate (ledger.Book).
QQQ/SPY are taxed like shares here for simplicity; a Dane would really hold a
positive-listed EU ETF (lager tax), so they are a reference index, not a plan.
"""

import calendar
import datetime
import json
import math
import os
import time
import urllib.error
import urllib.request

from . import backtest, strategies
from .config import fingerprint
from .journal import Journal, append_line, write_atomic
from .ledger import Book

DAY = 86400
FX = "USDDKK"                     # USD priced in DKK
YAHOO = {FX: "DKK=X"}
STOOQ = {FX: "usddkk"}
CLOSE_UTC = (21, 30)              # 16:00 New York is 20:00/21:00 UTC; plus a margin
MAX_AGE = 6 * 3600
WARMUP_BARS = 450                 # enough for EMA 200, 13 month-ends and the EWMA
MIN_HISTORY = 280                 # bars before a ticker's backtest may start
RULE_TYPES = ("buy_and_hold", "faber", "tsmom", "ema_cross", "vol_target", "donchian",
              "momentum", "crash_exit")
USER_AGENT = "pitrader/0.1 (paper trading, public data only)"


class DataError(Exception):
    """No usable daily bars for a symbol."""


class ConfigChanged(RuntimeError):
    pass


# ---- config ---------------------------------------------------------------------

def arms(cfg):
    """One arm per ticker and rule, id like faber_nvda."""
    out = []
    for tk in cfg["tickers"]:
        for r in cfg["rules"]:
            if r["type"] not in RULE_TYPES:
                raise ValueError("unknown rule type for stocks: %r" % r["type"])
            s = dict(r)
            s["ticker"] = tk
            s["id"] = "%s_%s" % (short(r["type"]), tk.lower())
            out.append(s)
    return out


def short(kind):
    return {"buy_and_hold": "bh", "ema_cross": "ema", "vol_target": "voltgt",
            "tsmom": "tsmom12"}.get(kind, kind)


def load_config(path):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    for key in ("run_name", "start_date", "capital_dkk", "tickers", "rules", "fee_rate",
                "fee_min_dkk", "fx_fee", "half_spread", "extra_slippage_bps", "tax_scenarios"):
        if key not in cfg:
            raise ValueError("missing stocks config key: %s" % key)
    arms(cfg)
    return cfg


# ---- data -----------------------------------------------------------------------

def _get(url, opener, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def yahoo_rows(symbol, period1, opener):
    """[[date, o, h, l, c, v]] from Yahoo's chart API, split-adjusted, not dividend-adjusted."""
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=%d&period2=%d"
           "&interval=1d&includePrePost=false" % (YAHOO.get(symbol, symbol), period1,
                                                  int(time.time()) + DAY))
    data = json.loads(_get(url, opener))
    res = (data.get("chart") or {}).get("result") or []
    if not res:
        raise DataError("%s: no chart result" % symbol)
    r = res[0]
    offset = (r.get("meta") or {}).get("gmtoffset", -14400)
    q = r["indicators"]["quote"][0]
    cols = [q.get(k) or [] for k in ("open", "high", "low", "close", "volume")]
    rows = []
    for i, t in enumerate(r.get("timestamp") or []):
        o, h, l, c, v = (col[i] if i < len(col) else None for col in cols)
        if None in (o, h, l, c) or c <= 0:
            continue
        row = [time.strftime("%Y-%m-%d", time.gmtime(t + offset)),
               float(o), float(h), float(l), float(c), float(v or 0)]
        if rows and rows[-1][0] == row[0]:
            rows[-1] = row
        else:
            rows.append(row)
    if not rows:
        raise DataError("%s: yahoo gave no rows" % symbol)
    return rows


def stooq_rows(symbol, opener):
    code = STOOQ.get(symbol, symbol.lower() + ".us")
    rows = []
    for line in _get("https://stooq.com/q/d/l/?s=%s&i=d" % code, opener).splitlines()[1:]:
        f = line.strip().split(",")
        if len(f) < 5:
            continue
        try:
            datetime.date.fromisoformat(f[0])
            rows.append([f[0], float(f[1]), float(f[2]), float(f[3]), float(f[4]),
                         float(f[5]) if len(f) > 5 and f[5] else 0.0])
        except ValueError:
            continue
    if not rows:
        raise DataError("%s: stooq gave no rows" % symbol)
    return rows


def closed_only(rows, now):
    """Drop a bar whose US session has not closed yet."""
    out = []
    for r in rows:
        y, m, d = (int(x) for x in r[0].split("-"))
        if calendar.timegm((y, m, d, CLOSE_UTC[0], CLOSE_UTC[1], 0)) > now:
            break
        out.append(r)
    return out


def load_rows(symbol, cache_dir, opener=urllib.request.urlopen, now=None):
    """All closed daily bars for `symbol`, cached on disk. Returns (rows, source, error)."""
    now = time.time() if now is None else now
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "%s.json" % symbol)
    cached = None
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                cached = json.load(f)
        except (OSError, ValueError):
            cached = None
    if cached and now - cached["fetched"] < MAX_AGE:
        return closed_only(cached["rows"], now), cached["source"], None
    rows, source, errors = None, None, []
    if cached and cached["source"] == "yahoo" and cached["rows"]:
        # incremental: the last two weeks again; a changed close means a split, so refetch all
        last = cached["rows"][-10:]
        y, m, d = (int(x) for x in last[0][0].split("-"))
        try:
            new = yahoo_rows(symbol, calendar.timegm((y, m, d, 0, 0, 0)), opener)
            old = {r[0]: r[4] for r in last}
            if all(abs(r[4] / old[r[0]] - 1) < 0.002 for r in new if r[0] in old):
                keep = [r for r in cached["rows"] if r[0] < new[0][0]]
                rows, source = keep + new, "yahoo"
        except (DataError, urllib.error.URLError, OSError, ValueError, KeyError, IndexError) as e:
            errors.append("yahoo update: %s" % e)
    if rows is None:
        for name, fn in (("yahoo", lambda: yahoo_rows(symbol, 0, opener)),
                         ("stooq", lambda: stooq_rows(symbol, opener))):
            try:
                rows, source = fn(), name
                break
            except (DataError, urllib.error.URLError, OSError, ValueError, KeyError,
                    IndexError) as e:
                errors.append("%s: %s" % (name, e))
    if rows is None:
        if cached:
            return closed_only(cached["rows"], now), cached["source"], "; ".join(errors)
        raise DataError("%s: %s" % (symbol, "; ".join(errors)))
    write_atomic(path, json.dumps({"fetched": now, "source": source, "rows": rows}))
    return closed_only(rows, now), source, ("; ".join(errors) or None)


# ---- candles --------------------------------------------------------------------

def stamp(date):
    y, m, d = (int(x) for x in date.split("-"))
    return calendar.timegm((y, m, d, 0, 0, 0))


def month_left_is_weekend(date):
    """True when every calendar day after `date` in its month is a Saturday or Sunday."""
    y, m, d = (int(x) for x in date.split("-"))
    last = calendar.monthrange(y, m)[1]
    return all(calendar.weekday(y, m, k) >= 5 for k in range(d + 1, last + 1))


def candles_from(rows):
    """Daily bars as strategy candles. The last session of each month is stamped on the
    month's last calendar day, so strategies.is_month_end marks it although US markets
    are shut at weekends. The newest bar counts as month end only when the rest of the
    month is weekend (a holiday on the last weekday is caught one session late)."""
    out = []
    for i, r in enumerate(rows):
        nxt = rows[i + 1][0] if i + 1 < len(rows) else None
        me = (nxt[:7] != r[0][:7]) if nxt else month_left_is_weekend(r[0])
        t = stamp(r[0])
        if me:
            y, m = int(r[0][:4]), int(r[0][5:7])
            t = calendar.timegm((y, m, calendar.monthrange(y, m)[1], 0, 0, 0))
        out.append({"t": t, "d": r[0], "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]})
    return out


def fx_series(fx_rows, dates):
    """USD/DKK for each date: that day's close, else the last one before it, else the
    first one known (flagged)."""
    out, j, last, early = [], 0, None, 0
    first = fx_rows[0][4]
    for d in dates:
        while j < len(fx_rows) and fx_rows[j][0] <= d:
            last = fx_rows[j][4]
            j += 1
        if last is None:
            early += 1
        out.append(last if last is not None else first)
    return out, early


# ---- targets --------------------------------------------------------------------

def targets(s, candles):
    """Target weight after each candle. Monthly rules are computed in one pass (the
    generic prefix version is far too slow on the Pi for 25 years of bars); they equal
    strategies.faber / tsmom / vol_target on each prefix."""
    kind = s["type"]
    if kind not in strategies.MONTHLY:
        return backtest.targets(s, candles)
    n = len(candles)
    out, cur = [None] * n, None
    months = []
    a = 1.0 / (1.0 + s.get("com", 60))
    var = None
    for i, c in enumerate(candles):
        if i:
            r = math.log(c["c"] / candles[i - 1]["c"])
            var = r * r if var is None else (1 - a) * var + a * r * r
        if strategies.is_month_end(c["t"]):
            months.append(c["c"])
            if kind == "faber":
                k = s.get("months", 10)
                if len(months) >= k:
                    cur = 1 if months[-1] > sum(months[-k:]) / k else 0
            elif kind == "tsmom":
                k = s.get("months", 12)
                if len(months) > k:
                    cur = 1 if months[-1] > months[-1 - k] else 0
            elif i + 1 >= s.get("com", 60) + 2 and var:
                vol = math.sqrt(var * s.get("periods", 252))
                cur = min(1.0, s.get("target_vol", 0.20) / vol)
        out[i] = cur
    return out


# ---- one arm --------------------------------------------------------------------

def broker_fee(gross, cfg):
    return max(cfg["fee_min_dkk"], gross * cfg["fee_rate"]) + gross * cfg["fx_fee"]


def gross_for_budget(budget, cfg):
    """Largest trade value whose value plus fees fits in `budget` DKK."""
    r, m, x = cfg["fee_rate"], cfg["fee_min_dkk"], cfg["fx_fee"]
    g = budget / (1 + r + x)
    if g * r < m:
        g = (budget - m) / (1 + x)
    return max(g, 0.0)


def tax_on(net, sc):
    """Danish share income tax on a year's positive net gain: gain_rate up to
    threshold_dkk, rate_above over it (or gain_rate on all without a threshold)."""
    cut = sc.get("threshold_dkk")
    if cut is None or net <= cut:
        return net * sc["gain_rate"]
    return cut * sc["gain_rate"] + (net - cut) * sc["rate_above"]


def run_arm(s, candles, fx, cfg, first, decide_last=False, tax=None, tgt=None):
    """Replay one arm from candle index `first`. Prices are USD, the book is DKK.
    decide_last (live): also decide on the newest bar, so the order for the next
    session is journaled before that session opens.

    tax (a scenario): each year's net realised gain is taxed at the first session of the
    next year and the tax leaves the arm's cash (it may go below zero, like a bill paid
    later from the arm's own money); a net loss is carried forward, as Danish listed-share
    losses are. The result then has after_tax = liquidation value after the final sale,
    its tax, and the leftover loss valued at loss_value_rate."""
    slip = cfg["half_spread"] + cfg["extra_slippage_bps"] / 10000.0
    book = Book(float(cfg["capital_dkk"]))
    kind = s["type"]
    if tgt is None and kind != "buy_and_hold":
        tgt = targets(s, candles)
    pending, bought = None, False
    equity, fills, trips, decisions = [], [], [], []
    entry_cash = None
    carry, paid, year = 0.0, 0.0, None
    for i in range(first, len(candles)):
        c = candles[i]
        y = time.gmtime(c["t"]).tm_year
        if tax and year is not None and y != year:
            net = book.realised.get(year, 0.0) + carry
            if net > 0:
                due = tax_on(net, tax)
                book.cash -= due
                paid += due
                carry = 0.0
            else:
                carry = net
        year = y
        if pending:
            side, amount = pending
            pending = None
            if side == "buy":
                gross = gross_for_budget(min(amount, book.cash), cfg)
                if gross >= 1.0:
                    price = c["o"] * (1 + slip)
                    if book.qty <= 0:
                        entry_cash = book.cash
                    book.buy(gross / (price * fx[i]), gross, broker_fee(gross, cfg))
                    fills.append({"d": c["d"], "side": "buy", "usd": price, "dkk": gross})
            elif book.qty > 0:
                qty = book.qty * min(1.0, amount)
                price = c["o"] * (1 - slip)
                gross = qty * price * fx[i]
                book.sell(qty, gross, min(broker_fee(gross, cfg), gross), c["t"])
                fills.append({"d": c["d"], "side": "sell", "usd": price, "dkk": gross})
                if book.qty <= 1e-12 and entry_cash:
                    trips.append(book.cash / entry_cash - 1)
                    entry_cash = None
        equity.append((c["t"], book.value(c["c"] * fx[i])))
        if i == len(candles) - 1 and not decide_last:
            break
        if kind == "buy_and_hold":
            if not bought:
                pending, bought = ("buy", book.cash), True
        else:
            want = tgt[i]
            if want is None:
                continue
            if kind in strategies.MONTHLY and not strategies.is_month_end(c["t"]):
                continue
            pending = backtest.rebalance_step(want, max(book.cash, 0.0), book.qty,
                                              c["c"] * fx[i], s.get("band", 0.5))
        if pending:
            decisions.append({"sid": s["id"], "d": c["d"], "side": pending[0]})
    out = {"equity": equity, "fills": fills, "trips": trips, "book": book,
           "decisions": decisions, "pending": pending, "tax_paid": paid}
    if tax and year is not None:
        price = candles[-1]["c"] * fx[-1]
        gross = book.qty * price
        fee = min(broker_fee(gross, cfg), gross) if book.qty > 0 else 0.0
        net = book.realised.get(year, 0.0) + gross - fee - book.cost_basis() + carry
        final = book.cash + gross - fee
        out["after_tax"] = final - tax_on(net, tax) if net > 0 else final - net * tax["loss_value_rate"]
    return out


def after_tax(s, candles, fx, cfg, first, tgt=None):
    """{scenario: after-tax liquidation DKK}, one taxed replay per scenario."""
    return {name: run_arm(s, candles, fx, cfg, first, tax=sc, tgt=tgt)["after_tax"]
            for name, sc in cfg["tax_scenarios"].items()}


# ---- shared data load --------------------------------------------------------------

def load_all(cfg, cache_dir, opener, now):
    """{ticker: (candles, fx list, fx_early)}, plus problems."""
    problems = []
    fx_rows, _src, err = load_rows(FX, cache_dir, opener, now)
    if err:
        problems.append("%s: %s" % (FX, err))
    data = {}
    for tk in cfg["tickers"]:
        try:
            rows, _src, err = load_rows(tk, cache_dir, opener, now)
        except DataError as e:
            problems.append(str(e))
            continue
        if err:
            problems.append("%s: %s" % (tk, err))
        candles = candles_from(rows)
        fx, early = fx_series(fx_rows, [c["d"] for c in candles])
        data[tk] = (candles, fx, early)
    return data, problems


# ---- live run ---------------------------------------------------------------------

def live(cfg, data_dir, cache_dir, opener=urllib.request.urlopen, now=None):
    """One hourly pass of the live paper run. Writes status.json and summary.txt."""
    now = time.time() if now is None else now
    os.makedirs(data_dir, exist_ok=True)
    h = fingerprint(cfg)
    start_path = os.path.join(data_dir, "start.json")
    if os.path.exists(start_path):
        with open(start_path, encoding="utf-8") as f:
            started = json.load(f)
        if started["hash"] != h:
            raise ConfigChanged("stocks config hash %s differs from this run's %s; use a new "
                                "--data-dir for a new run" % (h, started["hash"]))
    else:
        started = {"hash": h, "run": cfg["run_name"], "start_date": cfg["start_date"],
                   "created_utc": iso(now)}
        write_atomic(start_path, json.dumps(started, indent=1))

    data, problems = load_all(cfg, cache_dir, opener, now)
    journal = Journal(os.path.join(data_dir, "decisions.jsonl"))
    seen = {(e["sid"], e["d"], e["side"]) for e in journal.read()}
    start_t = stamp(cfg["start_date"])
    rows, mismatches, last_date = [], [], None
    for s in arms(cfg):
        if s["ticker"] not in data:
            continue
        candles, fx, _ = data[s["ticker"]]
        first = next((i for i, c in enumerate(candles) if stamp(c["d"]) >= start_t), None)
        if first is None:
            continue                       # run not started yet
        lo = max(0, first - WARMUP_BARS)
        r = run_arm(s, candles[lo:], fx[lo:], cfg, first - lo, decide_last=True)
        produced = {(d["sid"], d["d"], d["side"]) for d in r["decisions"]}
        for d in r["decisions"]:
            key = (d["sid"], d["d"], d["side"])
            if key not in seen:
                journal.append(dict(d, logged_utc=iso(now)))
                seen.add(key)
        mismatches += ["%s %s %s" % k for k in seen if k[0] == s["id"] and k not in produced]
        book, last = r["book"], candles[-1]
        last_date = last["d"]
        price_dkk = last["c"] * fx[-1]
        value = book.value(price_dkk)
        cap = cfg["capital_dkk"]
        at = after_tax(s, candles[lo:], fx[lo:], cfg, first - lo)
        rows.append({
            "id": s["id"], "type": s["type"], "ticker": s["ticker"],
            "position": "long" if book.qty > 0 else "cash",
            "weight": round(book.qty * price_dkk / value, 3) if value else 0,
            "equity_dkk": round(value, 2), "return_pct": round((value / cap - 1) * 100, 2),
            "after_tax_liquidation_dkk": {k: round(v, 2) for k, v in at.items()},
            "fees_dkk": round(book.fees, 2), "buys": book.buys, "sells": book.sells,
            "max_drawdown_pct": round(backtest.max_drawdown(v for _, v in r["equity"]) * 100, 2),
            "pending": r["pending"][0] if r["pending"] else None,
            "last_close_usd": last["c"], "last_bar": last["d"],
        })
    days = (now - start_t) / 86400.0
    status = {
        "heartbeat_utc": iso(now), "run": cfg["run_name"], "config_hash": h,
        "start_date": cfg["start_date"], "day": max(0, int(days) + 1),
        "phase": ("not started: first bars after %s" % cfg["start_date"] if not rows else
                  "system check (day 1-14): wiring and bugs only" if days < 14 else
                  "live sim: can reject a strategy, cannot confirm one"),
        "verdict": "NONE: the live run never prints PASS (D21, D22).",
        "last_bar": last_date,
        "usd_dkk": round(data[next(iter(data))][1][-1], 4) if data else None,
        "assumptions": {k: cfg[k] for k in ("capital_dkk", "fee_rate", "fee_min_dkk", "fx_fee",
                                            "half_spread", "extra_slippage_bps",
                                            "tax_scenarios")},
        "problems": problems, "replay_mismatches": sorted(mismatches)[:20],
        "strategies": rows,
    }
    write_atomic(os.path.join(data_dir, "status.json"), json.dumps(status, indent=1, sort_keys=True))
    write_atomic(os.path.join(data_dir, "summary.txt"), summary_text(status))
    if rows and last_date:
        ids = [s["id"] for s in arms(cfg)]
        eq = {r["id"]: "%.2f" % r["equity_dkk"] for r in rows}
        path = os.path.join(data_dir, "equity.csv")
        prev = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                lines = f.read().splitlines()
            prev = lines[-1].split(",")[0] if len(lines) > 1 else None
        else:
            append_line(path, "date," + ",".join(ids) + "\n")
        if prev != last_date:
            append_line(path, last_date + "," + ",".join(eq.get(i, "") for i in ids) + "\n")
    return status


def summary_text(st):
    lines = ["pitrader stocks  run %s  config %s" % (st["run"], st["config_hash"]),
             "Heartbeat: %s   Day %d   %s" % (st["heartbeat_utc"], st["day"], st["phase"]),
             "Last daily bar: %s   USD/DKK %s" % (st["last_bar"], st["usd_dkk"]),
             "Verdict: %s" % st["verdict"]]
    for p in st["problems"]:
        lines.append("WARN data: %s" % p[:200])
    if st["replay_mismatches"]:
        lines.append("WARN replay differs from journaled decisions: %s"
                     % ", ".join(st["replay_mismatches"][:5]))
    if st["strategies"]:
        lines += ["", "%-14s %-5s %-5s %11s %8s %13s %13s %7s %6s %7s" % (
            "strategy", "tick", "pos", "equity DKK", "return", "after tax hi", "after tax lo",
            "fees", "trades", "max DD")]
        for r in st["strategies"]:
            at = r["after_tax_liquidation_dkk"]
            lines.append("%-14s %-5s %-5s %11.2f %7.2f%% %13.2f %13.2f %7.2f %6d %6.2f%%" % (
                r["id"], r["ticker"], r["position"], r["equity_dkk"], r["return_pct"],
                at.get("high", 0.0), at.get("low", 0.0), r["fees_dkk"], r["buys"] + r["sells"],
                r["max_drawdown_pct"]))
    return "\n".join(lines) + "\n"


# ---- historical backtest ------------------------------------------------------------

def run_backtest(cfg, cache_dir, out_dir, opener=urllib.request.urlopen, runs=backtest.RANDOM_RUNS,
                 now=None):
    """Every arm over each ticker's full history from backtest_start (or once the ticker
    has MIN_HISTORY bars). Never prints PASS (D22)."""
    now = time.time() if now is None else now
    data, problems = load_all(cfg, cache_dir, opener, now)
    bt_start = stamp(cfg.get("backtest_start", "2000-01-01"))
    rcfg = {"taker_fee": cfg["fee_rate"] + cfg["fx_fee"],
            "extra_slippage_bps": cfg["extra_slippage_bps"]}
    res, pvals, periods = {}, {}, {}
    for tk, (candles, fx, early) in data.items():
        first = next((i for i, c in enumerate(candles)
                      if i >= MIN_HISTORY and stamp(c["d"]) >= bt_start), None)
        if first is None or len(candles) - first < 250:
            problems.append("%s: too little history for a backtest" % tk)
            continue
        periods[tk] = (candles[first]["d"], candles[-1]["d"], candles[first]["c"], candles[-1]["c"])
        if early > first:
            problems.append("%s: USD/DKK missing before %s, first known rate used"
                            % (tk, candles[early]["d"]))
        dkk = [dict(c, o=c["o"] * fx[i]) for i, c in enumerate(candles)]
        for s in arms(cfg):
            if s["ticker"] != tk:
                continue
            tgt = None if s["type"] == "buy_and_hold" else targets(s, candles)
            r = run_arm(s, candles, fx, cfg, first, tgt=tgt)
            book, last = r["book"], candles[-1]
            final = book.value(last["c"] * fx[-1])
            a = {"id": s["id"], "ticker": tk, "type": s["type"], "series": r["equity"],
                 "trips": r["trips"], "final_dkk": final, "sells": book.sells,
                 "after_tax_dkk": after_tax(s, candles, fx, cfg, first, tgt),
                 "max_dd": backtest.max_drawdown(v for _, v in r["equity"]),
                 "fees_dkk": book.fees, "round_trips": len(r["trips"]),
                 "random_p": None, "random_median_dkk": None}
            if s["type"] not in ("buy_and_hold", "vol_target"):
                p, med = backtest.random_entry_p(dkk, len(r["trips"]), final,
                                                 float(cfg["capital_dkk"]), rcfg,
                                                 start=candles[first]["t"], runs=runs)
                a["random_p"], a["random_median_dkk"] = p, med
                pvals[s["id"]] = p
            res[s["id"]] = a
        # fall test against this ticker's buy-and-hold, then drop the equity series so
        # 25 years x 13 tickers fit in the Pi's 512 MB
        mine = [a for a in res.values() if a["ticker"] == tk]
        bh = res.get("bh_%s" % tk.lower())
        bh_falls = backtest.falls(bh["series"]) if bh else []
        for a in mine:
            a["fall_wins"] = []
            for p_t, t_t, depth in bh_falls:
                ar, br = (change(x["series"], p_t, t_t) for x in (a, bh))
                a["fall_wins"].append({"peak": iso_d(p_t), "trough": iso_d(t_t),
                                       "bh_fall_pct": -depth * 100, "arm_pct": ar * 100,
                                       "win": ar > br})
        for a in mine:
            del a["series"]
    adj = backtest.holm(pvals)
    for sid, a in res.items():
        a["holm_p"] = adj.get(sid)
        bh = res.get("bh_%s" % a["ticker"].lower())
        best = max(a["trips"]) if a["trips"] else None
        a["after_tax_wo_best_dkk"] = ({n: v / (1 + best) for n, v in a["after_tax_dkk"].items()}
                                      if best and best > 0 else a["after_tax_dkk"])
        a["verdict"] = verdict(a, bh)
    report = render(res, periods, problems, cfg, runs, len(pvals))
    os.makedirs(out_dir, exist_ok=True)
    write_atomic(os.path.join(out_dir, "report.md"), report)
    write_atomic(os.path.join(out_dir, "results.json"), json.dumps(res, indent=1, default=str))
    return res, report


def change(series, t0, t1):
    """Return from t0 to t1; -100 % once an arm is wiped out (fees can eat the last kroner)."""
    v0 = backtest.value_at(series, t0)
    return backtest.value_at(series, t1) / v0 - 1 if v0 > 0 else -1.0


def verdict(a, bh):
    """Unlocked reading of D25/D26 against the same ticker's buy-and-hold, with the
    Holm-adjusted random-entry p (many stocks x rules = many chances of luck)."""
    if a["type"] == "buy_and_hold":
        return "reference"
    if not bh:
        return "no buy-and-hold to compare"
    beats = all(a["after_tax_dkk"][n] > bh["after_tax_dkk"][n] for n in a["after_tax_dkk"])
    dd_ok = a["max_dd"] <= bh["max_dd"]
    if not beats and not dd_ok:
        return "FAIL: lower after-tax and deeper drawdown than buy-and-hold"
    if not beats:
        return "risk-better only (INCONCLUSIVE, D26)"
    if not dd_ok:
        return "FAIL: more after-tax but deeper drawdown than buy-and-hold (D26)"
    misses = []
    if a["type"] == "donchian":
        if a["sells"] < 100:
            misses.append("<100 closed trades")
    elif a["round_trips"] < 20:
        misses.append("only %d round trips (<20)" % a["round_trips"])
    if a["fall_wins"] and not all(f["win"] for f in a["fall_wins"]):
        misses.append("lost in a >=30% fall")
    if not all(a["after_tax_wo_best_dkk"][n] > bh["after_tax_dkk"][n] for n in a["after_tax_dkk"]):
        misses.append("not winning without best trade")
    if a.get("holm_p") is not None and a["holm_p"] >= 0.05:
        misses.append("Holm p=%.3f" % a["holm_p"])
    if misses:
        return "beats B&H but INCONCLUSIVE: %s" % "; ".join(misses)
    return "PASS candidate (rules not locked, D22)"


def cagr(final, cap, days):
    return ((final / cap) ** (365.25 / days) - 1) * 100 if days > 0 and final > 0 else -100.0


def render(res, periods, problems, cfg, runs, family):
    cap = cfg["capital_dkk"]
    lines = [
        "# Backtest US-aktier i DKK",
        "",
        "Data: daglige kurser fra Yahoo (Stooq som reserve), split-justeret, uden udbytte. "
        "USD/DKK pr. dag. Beslutning på dagens lukkekurs, handel på næste dags åbning. "
        "Omkostninger: kurtage %.2f %% (min %.0f kr), valutaveksling %.2f %%, halv spread "
        "%.2f %%, %d bp slippage, begge veje. Skat (aktieindkomst, FIFO i DKK): årets "
        "nettogevinst beskattes ved nytår og betales af armens egne penge, tab fremføres; "
        "høj = 42 %% på alt og resterende tab er intet værd, lav = 27 %% op til %.0f kr om året "
        "og 42 %% over, resterende tab værd 27 %%. Alt sælges og beskattes ved slut, også "
        "buy-and-hold, som derfor betaler det meste i 42 %%-trinnet. QQQ/SPY er beskattet "
        "som aktier her; i virkeligheden ville en dansker købe en positivliste-ETF med "
        "lagerskat." % (
            cfg["fee_rate"] * 100, cfg["fee_min_dkk"], cfg["fx_fee"] * 100,
            cfg["half_spread"] * 100, cfg["extra_slippage_bps"],
            cfg["tax_scenarios"].get("low", {}).get("threshold_dkk", 0)),
        "",
        "Ingen arm kan få PASS her: reglerne er ikke låst (D22). %d regel-arme testes på én gang, "
        "så tilfældig-p er Holm-korrigeret over alle %d (%d tilfældige strategier pr. arm). Jo "
        "flere aktier, jo flere vil se gode ud af held alene." % (family, family, runs),
        "",
    ]
    if problems:
        lines += ["## Problemer", ""] + ["- %s" % p for p in problems] + [""]
    for tk, (d0, d1, p0, p1) in periods.items():
        days = stamp(d1) - stamp(d0)
        lines += ["## %s %s til %s (%.1f år, %.2f → %.2f USD)" % (
            tk, d0, d1, days / (365.25 * DAY), p0, p1), "",
            "| Arm | Efter skat høj | Efter skat lav | Før skat | CAGR før skat | Max DD | "
            "Round trips | Fald ≥30 % klaret | Gebyrer | Holm p | Vurdering |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
        mine = sorted((a for a in res.values() if a["ticker"] == tk),
                      key=lambda a: -a["after_tax_dkk"].get("high", 0))
        for a in mine:
            lines.append("| %s | %.0f | %.0f | %.0f | %.1f %% | %.1f %% | %d | %s | %.0f | %s | %s |" % (
                a["id"], a["after_tax_dkk"].get("high", 0), a["after_tax_dkk"].get("low", 0),
                a["final_dkk"], cagr(a["final_dkk"], cap, days / 86400.0), a["max_dd"] * 100,
                a["round_trips"], "-" if a["type"] == "buy_and_hold" else "%d/%d" % (
                    sum(f["win"] for f in a["fall_wins"]), len(a["fall_wins"])), a["fees_dkk"],
                "-" if a["holm_p"] is None else "%.3f" % a["holm_p"], a["verdict"]))
        lines.append("")
    return "\n".join(lines) + "\n"


def iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def iso_d(ts):
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


def backtest_due(out_dir, every_days, now=None):
    now = time.time() if now is None else now
    path = os.path.join(out_dir, "report.md")
    return not os.path.exists(path) or now - os.path.getmtime(path) > every_days * DAY
