"""Historical backtest of the same rules on Bitstamp BTC/EUR candles (public data,
no key). Stdlib only, so it runs on the Pi as well as on a PC.

Same costs as the live sim: decision on a closed candle, fill at the NEXT candle's
open plus half a spread, extra slippage and the taker fee; FIFO tax shadow ledger
(ledger.Book); every arm is liquidated and taxed at the end, buy-and-hold too (D26).

It never prints PASS: the rules are not locked yet (D22). It reports what the locked
rules would look at (D25, D26) so the confirmatory set can be chosen with eyes open.
"""

import json
import math
import os
import random
import time
import urllib.request

from . import strategies
from .journal import write_atomic
from .ledger import Book
from .sim import MIN_ORDER_EUR, rebalance_step

BITSTAMP = "https://www.bitstamp.net/api/v2/ohlc/%s/?step=%d&limit=1000&start=%d"
DAY = 86400
WEEK = 7 * DAY
HALF_SPREAD = 0.0002            # Kraken BTC/EUR is usually tighter; kept conservative
START = 1496275200              # 2017-06-01: first day every daily rule has its history
RANDOM_RUNS = 10000


# ---- data -----------------------------------------------------------------------

def fetch(pair, step, cache_dir, opener=urllib.request.urlopen, now=None):
    """All closed candles for `pair` at `step` seconds, cached on disk, oldest first."""
    now = now or time.time()
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "bitstamp-%s-%d.json" % (pair, step))
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
    start = rows[-1]["t"] + step if rows else 1300000000
    while start + step <= now:
        req = urllib.request.Request(BITSTAMP % (pair, step, start),
                                     headers={"User-Agent": "pitrader-backtest"})
        with opener(req, timeout=30) as r:
            got = json.loads(r.read().decode("utf-8"))["data"]["ohlc"]
        got = [{"t": int(g["timestamp"]), "o": float(g["open"]), "h": float(g["high"]),
                "l": float(g["low"]), "c": float(g["close"]), "v": float(g["volume"])}
               for g in got]
        got = [g for g in got if g["t"] >= start and g["t"] + step <= now]
        if not got:
            if rows:
                break
            start += 1000 * step        # before the pair existed: skip ahead
            continue
        rows.extend(got)
        start = got[-1]["t"] + step
        time.sleep(0.5)
    write_atomic(path, json.dumps(rows))
    return rows


# ---- target series --------------------------------------------------------------

def targets(s, candles):
    """Target weight after each candle (None = no opinion yet). Computed once over the
    whole history; equal to calling strategies.target on each prefix."""
    kind = s["type"]
    closes = [c["c"] for c in candles]
    n = len(candles)
    if kind == "ema_cross":
        f = strategies.ema(closes, s.get("fast", 50))
        sl = strategies.ema(closes, s.get("slow", 200))
        return [None if sl[i] is None else (1 if f[i] > sl[i] else 0) for i in range(n)]
    if kind == "momentum":
        lb = s.get("lookback", 90)
        return [None if i < lb else (1 if closes[i] > closes[i - lb] else 0) for i in range(n)]
    if kind == "donchian":
        e = s.get("entry", 20)
        path = strategies.donchian_path(candles, e, s.get("exit", 10))
        return [None if i < e else p for i, p in enumerate(path)]
    if kind == "crash_exit":
        return strategies.crash_exit_path(closes, s.get("drop", 0.25), s.get("high_days", 365),
                                          s.get("sma_days", 200))
    if kind in strategies.MONTHLY:
        out, cur = [None] * n, None
        for i in range(n):
            if strategies.is_month_end(candles[i]["t"]):
                cur = strategies.target(s, candles[:i + 1])
            out[i] = cur
        return out
    raise ValueError("no backtest for %s" % kind)


# ---- one arm --------------------------------------------------------------------

def run_arm(s, candles, cfg, start=START):
    """Replay one arm. Returns equity series, fills and the final book."""
    fee = cfg["taker_fee"]
    slip = cfg["extra_slippage_bps"] / 10000.0
    capital = cfg["capital_dkk"] / cfg["eur_dkk"]
    book = Book(capital)
    kind = s["type"]
    tgt = None if kind in ("buy_and_hold", "dca", "dip_dca") else targets(s, candles)
    closes = [c["c"] for c in candles]
    first = next(i for i, c in enumerate(candles) if c["t"] >= start)
    pending = None
    equity, fills, trips = [], [], []
    last_buy_t, buys, entry_cash = None, 0, None
    for i in range(first, len(candles)):
        c = candles[i]
        if pending:                                   # fill at this candle's open
            side, amount = pending
            pending = None
            if side == "buy":
                budget = min(amount, book.cash)
                if budget >= MIN_ORDER_EUR:
                    gross = budget / (1 + fee)
                    price = c["o"] * (1 + HALF_SPREAD + slip)
                    if book.qty <= 0:
                        entry_cash = book.cash
                    book.buy(gross / price, gross, gross * fee)
                    fills.append((c["t"], "buy", price))
            elif book.qty > 0:
                qty = book.qty * min(1.0, amount)
                price = c["o"] * (1 - HALF_SPREAD - slip)
                gross = qty * price
                book.sell(qty, gross, gross * fee, c["t"])
                fills.append((c["t"], "sell", price))
                if book.qty <= 1e-12 and entry_cash:
                    trips.append(book.cash / entry_cash - 1)
                    entry_cash = None
        equity.append((c["t"], book.value(c["c"])))
        if i == len(candles) - 1:
            break
        # decide on this closed candle
        if kind == "buy_and_hold":
            if not buys:
                pending, buys = ("buy", book.cash), 1
        elif kind in ("dca", "dip_dca"):
            if book.cash >= MIN_ORDER_EUR and (last_buy_t is None or c["t"] - last_buy_t >= WEEK):
                if kind == "dca" and buys >= s["weeks"]:
                    continue
                mult = 1
                if kind == "dip_dca":
                    mult = strategies.dip_multiplier(candles[max(0, i - 400):i + 1],
                                                     s.get("sma_days", 200), s.get("deep", 0.20))
                last_buy_t = c["t"]
                if mult:
                    pending, buys = ("buy", capital / s["weeks"] * mult), buys + 1
        else:
            want = tgt[i]
            if want is None:
                continue
            if kind in strategies.MONTHLY and not strategies.is_month_end(c["t"]):
                continue
            pending = rebalance_step(want, book.cash, book.qty, closes[i], s.get("band", 0.5))
    return {"equity": equity, "fills": fills, "trips": trips, "book": book,
            "last": candles[-1]}


# ---- statistics -----------------------------------------------------------------

def max_drawdown(values):
    peak, dd = 0.0, 0.0
    for v in values:
        peak = max(peak, v)
        if peak > 0:
            dd = max(dd, 1 - v / peak)
    return dd


def falls(series, depth=0.30):
    """(peak_t, trough_t, fall) for every peak-to-trough fall of at least `depth`
    before the price got back to its old peak."""
    out = []
    peak_t, peak, trough_t, trough = series[0][0], series[0][1], None, None
    for t, v in series:
        if v >= peak:
            if trough is not None and 1 - trough / peak >= depth:
                out.append((peak_t, trough_t, 1 - trough / peak))
            peak_t, peak, trough_t, trough = t, v, None, None
        elif trough is None or v < trough:
            trough_t, trough = t, v
    if trough is not None and 1 - trough / peak >= depth:
        out.append((peak_t, trough_t, 1 - trough / peak))
    return out


def value_at(series, t):
    """Equity at the last point at or before t."""
    lo, hi = 0, len(series) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if series[mid][0] <= t:
            lo = mid
        else:
            hi = mid - 1
    return series[lo][1]


def random_entry_p(candles, trips, arm_final, capital, cfg, start=START, runs=RANDOM_RUNS,
                   seed=1):
    """Share of `runs` random in/out strategies with the same number of round trips
    whose pre-tax final value is at least the arm's (lens/critic: 10,000 random
    strategies). Returns (p, median random final)."""
    if trips < 1:
        return None, None
    fee = cfg["taker_fee"]
    slip = cfg["extra_slippage_bps"] / 10000.0
    cost = (1 - HALF_SPREAD - slip) / (1 + HALF_SPREAD + slip) * (1 - fee) / (1 + fee)
    first = next(i for i, c in enumerate(candles) if c["t"] >= start)
    opens = [c["o"] for c in candles]
    days = range(first, len(candles) - 1)
    if 2 * trips > len(days):
        return None, None
    rng = random.Random(seed)
    ge, finals = 0, []
    for _ in range(runs):
        idx = sorted(rng.sample(days, 2 * trips))
        v = capital
        for k in range(0, len(idx), 2):
            v *= opens[idx[k + 1] + 1] / opens[idx[k] + 1] * cost
        finals.append(v)
        if v >= arm_final:
            ge += 1
    finals.sort()
    return (ge + 1) / float(runs + 1), finals[len(finals) // 2]


def holm(pvals):
    """Holm step-down adjusted p-values for {name: p}."""
    items = sorted((p, k) for k, p in pvals.items() if p is not None)
    m, out, run = len(items), {}, 0.0
    for rank, (p, k) in enumerate(items):
        run = max(run, min(1.0, (m - rank) * p))
        out[k] = run
    return out


# ---- the whole thing --------------------------------------------------------------

def run(cfg, cache_dir, out_dir, opener=urllib.request.urlopen, runs=RANDOM_RUNS):
    eur_dkk = cfg["eur_dkk"]
    capital = cfg["capital_dkk"] / eur_dkk
    data = {}
    for s in cfg["strategies"]:
        if s["pair"] != "XBTEUR":
            continue
        step = (s.get("interval", 1440) if s["type"] in ("ema_cross", "donchian", "momentum",
                "faber", "tsmom", "vol_target", "crash_exit") else 1440) * 60
        if step not in data:
            data[step] = fetch("btceur", step, cache_dir, opener)
    daily = data[DAY]
    arms = {}
    for s in cfg["strategies"]:
        if s["pair"] != "XBTEUR":
            continue
        step = DAY if s["type"] in ("buy_and_hold", "dca", "dip_dca") else s.get("interval", 1440) * 60
        candles = data[step]
        r = run_arm(s, candles, cfg)
        book, last = r["book"], r["last"]
        after = {name: book.after_tax_value(last["c"], cfg["taker_fee"], sc, last["t"]) * eur_dkk
                 for name, sc in cfg["tax_scenarios"].items()}
        final = book.value(last["c"])
        arms[s["id"]] = {
            "spec": s, "type": s["type"], "series": r["equity"], "trips": r["trips"],
            "final_dkk": final * eur_dkk, "after_tax_dkk": after,
            "max_dd": max_drawdown(v for _, v in r["equity"]),
            "fills": len(r["fills"]), "sells": book.sells, "fees_dkk": book.fees * eur_dkk,
            "candles": candles, "final_eur": final,
        }
    bh = arms["bh_btc"]
    bh_falls = falls(bh["series"])
    pvals = {}
    for sid, a in arms.items():
        k = len(a["trips"])
        a["round_trips"] = k
        a["fall_wins"] = []
        for p_t, t_t, depth in bh_falls:
            arm_r = value_at(a["series"], t_t) / value_at(a["series"], p_t) - 1
            bh_r = value_at(bh["series"], t_t) / value_at(bh["series"], p_t) - 1
            a["fall_wins"].append({"peak": iso(p_t), "trough": iso(t_t), "bh_fall_pct": -depth * 100,
                                   "arm_pct": arm_r * 100, "win": arm_r > bh_r})
        best = max(a["trips"]) if a["trips"] else None
        a["best_trip_pct"] = best * 100 if best is not None else None
        a["after_tax_wo_best_dkk"] = ({n: v / (1 + best) for n, v in a["after_tax_dkk"].items()}
                                      if best and best > 0 else a["after_tax_dkk"])
        if a["type"] in ("buy_and_hold", "dca", "dip_dca", "vol_target"):
            a["random_p"], a["random_median_dkk"] = None, None
        else:
            p, med = random_entry_p(a["candles"], k, a["final_eur"], capital, cfg, runs=runs)
            a["random_p"] = p
            a["random_median_dkk"] = med * eur_dkk if med else None
            pvals[sid] = p
    adj = holm(pvals)
    for sid, a in arms.items():
        a["holm_p"] = adj.get(sid)
        a["verdict"] = verdict(sid, a, arms)
    report = render(arms, bh_falls, daily, cfg, runs)
    os.makedirs(out_dir, exist_ok=True)
    write_atomic(os.path.join(out_dir, "report.md"), report)
    slim = {sid: {k: v for k, v in a.items() if k not in ("series", "candles", "spec")}
            for sid, a in arms.items()}
    write_atomic(os.path.join(out_dir, "results.json"), json.dumps(slim, indent=1, default=str))
    return arms, report


def verdict(sid, a, arms):
    """Unlocked reading of D25/D26. Never PASS (D22: rules not locked)."""
    if sid == "bh_btc":
        return "reference"
    ref = arms["dca_btc"] if a["type"] == "dip_dca" else arms["bh_btc"]
    if sid == "dca_btc":
        ref = arms["bh_btc"]
    beats = all(a["after_tax_dkk"][n] > ref["after_tax_dkk"][n] for n in a["after_tax_dkk"])
    dd_ok = a["max_dd"] <= ref["max_dd"]
    if not beats and not dd_ok:
        return "FAIL: lower after-tax and deeper drawdown than %s" % ref["spec"]["id"]
    if not beats:
        return "risk-better only (INCONCLUSIVE, D26)"
    if not dd_ok:
        return "FAIL: more after-tax but deeper drawdown than %s (D26)" % ref["spec"]["id"]
    misses = []
    k = a["round_trips"]
    if a["type"] == "donchian":
        if a["sells"] < 100:
            misses.append("<100 closed trades")
    elif a["type"] not in ("dca", "dip_dca") and k < 20:
        misses.append("only %d round trips (<20)" % k)
    if a["fall_wins"] and not all(f["win"] for f in a["fall_wins"]):
        misses.append("lost in a >=30% fall")
    if not all(a["after_tax_wo_best_dkk"][n] > ref["after_tax_dkk"][n] for n in a["after_tax_dkk"]):
        misses.append("not winning without best trade")
    if a.get("random_p") is not None and a["random_p"] >= 0.05:
        misses.append("random-entry p=%.3f" % a["random_p"])
    if misses:
        return "beats %s but INCONCLUSIVE: %s" % (ref["spec"]["id"], "; ".join(misses))
    return "PASS candidate (rules not locked, D22)"


def iso(ts):
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


def render(arms, bh_falls, daily, cfg, runs):
    first = next(c for c in daily if c["t"] >= START)
    last = daily[-1]
    years = (last["t"] - first["t"]) / (365.25 * DAY)
    lines = [
        "# Backtest BTC/EUR %s til %s (%.1f år)" % (iso(first["t"]), iso(last["t"]), years),
        "",
        "Data: Bitstamp BTC/EUR, offentlige candles. Omkostninger som i simulatoren: taker %.2f %%, "
        "%d bp ekstra slippage, %.2f %% halv spread, fill på næste candles åbning. Alle arme sælges og "
        "beskattes ved periodens slut, også buy-and-hold (D26). Skat: %s. Tab fremføres ikke "
        "mellem år (forsigtigt). %d tilfældige strategier pr. arm. Kursen startede på %.0f EUR og "
        "sluttede på %.0f EUR." % (cfg["taker_fee"] * 100, cfg["extra_slippage_bps"], HALF_SPREAD * 100,
                                  ", ".join("%s %d %%" % (n, sc["gain_rate"] * 100)
                                            for n, sc in cfg["tax_scenarios"].items()),
                                  runs, first["c"], last["c"]),
        "",
        "Ingen arm kan få PASS her: reglerne er ikke låst endnu (D22). \"PASS candidate\" betyder kun, "
        "at den ville klare de foreslåede krav.",
        "",
        "| Arm | Efter skat høj (DKK) | Efter skat lav | Før skat | Max DD | Round trips | Gebyrer | "
        "Tilfældig p | Holm p | Vurdering |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    order = sorted(arms.items(), key=lambda kv: -kv[1]["after_tax_dkk"].get("high", 0))
    for sid, a in order:
        lines.append("| %s | %.0f | %.0f | %.0f | %.1f %% | %d | %.0f | %s | %s | %s |" % (
            sid, a["after_tax_dkk"].get("high", 0), a["after_tax_dkk"].get("low", 0),
            a["final_dkk"], a["max_dd"] * 100, a["round_trips"], a["fees_dkk"],
            "-" if a["random_p"] is None else "%.3f" % a["random_p"],
            "-" if a["holm_p"] is None else "%.3f" % a["holm_p"], a["verdict"]))
    lines += ["", "## Fald på mindst 30 %% i BTC (%d stk.)" % len(bh_falls), "",
              "| Arm | " + " | ".join("%s→%s (%.0f %%)" % (iso(p), iso(t), -d * 100)
                                       for p, t, d in bh_falls) + " |",
              "|---|" + "---:|" * len(bh_falls)]
    for sid, a in order:
        lines.append("| %s | %s |" % (sid, " | ".join(
            "%.0f %%%s" % (f["arm_pct"], "" if not f["win"] else " ✓") for f in a["fall_wins"])))
    lines += ["", "✓ = faldt mindre end buy-and-hold i det fald.", ""]
    return "\n".join(lines) + "\n"
