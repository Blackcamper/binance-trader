"""Scoring of the Haiku news diary (paper only, no money, no orders).

A scheduled Claude task writes one file per US trading day to the public branch
`nyheds-dagbog` (journal/YYYY-MM-DD.json): up to three stock picks from a fixed
universe, or none. The Pi copies that branch into data/nyheder/journal in its
hourly sync and this module scores every pick afterwards with public daily prices.

Rules locked 2026-10-20 (Jakob chose "Start nu"):
  entry  = open of the first US session that starts after the file was written
  exit   = close after 1, 5 and 20 sessions; 5 is the main horizon
  cost   = 0.5 % per round trip (brokerage + FX at Nordnet/Saxo), on the pick only
  excess = pick return - QQQ return over the same sessions
  luck   = pick excess - average excess of the whole universe on that day
  PASS   = >= 100 picks scored at 5 sessions, mean excess > 0 with t > 2,
           and mean luck-adjusted excess > 0. Anything else is not PASS.
"""

import datetime
import json
import math
import os
import time
import urllib.error
import urllib.request

UNIVERSE = (
    "AAPL MSFT NVDA AMD INTC AVGO QCOM TSM ASML ARM MU GOOGL META AMZN TSLA NFLX ORCL CRM "
    "ADBE PLTR SMCI DELL IBM CSCO NVO LLY JPM V MA XOM BA DIS KO WMT COST UBER SHOP COIN MSTR SAP"
).split()
BENCH = "QQQ"
HORIZONS = (1, 5, 20)
MAIN = 5
COST = 0.005
PASS_MIN = 100
US_OPEN_UTC = (13, 30)       # 9:30 New York in summer; a file written later waits a session
PRICE_MAX_AGE = 6 * 3600
USER_AGENT = "pitrader/0.1 (paper scoring, public data only)"


class PriceError(Exception):
    """No usable daily prices for a ticker."""


def _get(url, opener, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def yahoo_daily(ticker, start, opener=urllib.request.urlopen):
    """[(date, open, close)] for sessions from `start` (a date) until now."""
    p1 = int(time.mktime((start - datetime.timedelta(days=7)).timetuple()))
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=%d&period2=%d"
           "&interval=1d&includePrePost=false" % (ticker, p1, int(time.time()) + 86400))
    data = json.loads(_get(url, opener))
    res = (data.get("chart") or {}).get("result") or []
    if not res:
        raise PriceError("%s: no chart result" % ticker)
    r = res[0]
    offset = (r.get("meta") or {}).get("gmtoffset", -14400)
    q = r["indicators"]["quote"][0]
    rows = []
    for t, o, c in zip(r.get("timestamp") or [], q.get("open") or [], q.get("close") or []):
        if o is None or c is None:
            continue
        rows.append((datetime.datetime.fromtimestamp(t + offset, datetime.timezone.utc).date(), float(o), float(c)))
    return rows


def stooq_daily(ticker, start, opener=urllib.request.urlopen):
    url = "https://stooq.com/q/d/l/?s=%s.us&i=d&d1=%s" % (
        ticker.lower(), (start - datetime.timedelta(days=7)).strftime("%Y%m%d"))
    rows = []
    for line in _get(url, opener).splitlines()[1:]:
        f = line.split(",")
        if len(f) < 5:
            continue
        try:
            rows.append((datetime.date.fromisoformat(f[0]), float(f[1]), float(f[4])))
        except ValueError:
            continue
    if not rows:
        raise PriceError("%s: stooq gave no rows" % ticker)
    return rows


def prices(ticker, start, cache_dir, opener=urllib.request.urlopen, now=None):
    """Daily bars with a file cache, Yahoo first and Stooq as fallback."""
    now = time.time() if now is None else now
    path = os.path.join(cache_dir, ticker + ".json")
    if os.path.exists(path) and now - os.path.getmtime(path) < PRICE_MAX_AGE:
        with open(path, encoding="utf-8") as f:
            cached = json.load(f)
        if cached["start"] <= start.isoformat():
            return [(datetime.date.fromisoformat(d), o, c) for d, o, c in cached["rows"]]
    errors = []
    for source in (yahoo_daily, stooq_daily):
        try:
            rows = source(ticker, start, opener)
            break
        except (PriceError, urllib.error.URLError, OSError, ValueError, KeyError) as e:
            errors.append("%s: %s" % (source.__name__, e))
    else:
        raise PriceError("; ".join(errors))
    os.makedirs(cache_dir, exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump({"start": start.isoformat(), "rows": [(d.isoformat(), o, c) for d, o, c in rows]}, f)
    os.replace(path + ".tmp", path)
    return rows


def load_journal(journal_dir):
    days = []
    if not os.path.isdir(journal_dir):
        return days
    for name in sorted(os.listdir(journal_dir)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(journal_dir, name), encoding="utf-8") as f:
                days.append(json.load(f))
        except (OSError, ValueError):
            days.append({"date": name[:-5], "broken": True, "picks": []})
    return days


def entry_date(day):
    """First calendar date whose US session may be used for entry."""
    d = datetime.date.fromisoformat(day["date"])
    written = day.get("written_utc")
    if written:
        w = datetime.datetime.strptime(written[:16], "%Y-%m-%dT%H:%M")
        if w.date() > d or (w.date() == d and (w.hour, w.minute) >= US_OPEN_UTC):
            return w.date() + datetime.timedelta(days=1)
        return max(d, w.date())
    return d


def window_return(rows, start, h, cost=0.0):
    """Open of the first session on/after `start` to the close h sessions later."""
    idx = next((i for i, r in enumerate(rows) if r[0] >= start), None)
    if idx is None or idx + h - 1 >= len(rows):
        return None
    return rows[idx + h - 1][2] / rows[idx][1] - 1.0 - cost


def _stats(xs):
    n = len(xs)
    if n == 0:
        return {"n": 0, "mean": None, "t": None}
    m = sum(xs) / n
    if n < 2:
        return {"n": n, "mean": m, "t": None}
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return {"n": n, "mean": m, "t": (m / (sd / math.sqrt(n))) if sd > 0 else None}


def score(days, get_rows):
    """Score every pick. get_rows(ticker, start_date) -> bars or raises PriceError."""
    picks, problems = [], []
    cache = {}
    first = min((entry_date(d) for d in days if not d.get("broken")), default=None)

    def rows_for(t):
        if t not in cache:
            try:
                cache[t] = get_rows(t, first)
            except PriceError as e:
                cache[t] = None
                problems.append(str(e))
        return cache[t]

    for day in days:
        if day.get("broken"):
            problems.append("%s: journal file unreadable" % day["date"])
            continue
        start = entry_date(day)
        for p in day.get("picks") or []:
            t = (p.get("ticker") or "").upper()
            row = {"date": day["date"], "ticker": t, "confidence": p.get("confidence"),
                   "reason": (p.get("reason") or "")[:160]}
            if t not in UNIVERSE:
                row["invalid"] = "not in universe"
                picks.append(row)
                continue
            bars, bench = rows_for(t), rows_for(BENCH)
            for h in HORIZONS:
                if not bars or not bench:
                    continue
                r = window_return(bars, start, h, COST)
                q = window_return(bench, start, h)
                if r is None or q is None:
                    continue
                uni = [window_return(rows_for(u), start, h) for u in UNIVERSE if rows_for(u)]
                uni = [u - q for u in uni if u is not None]
                row["ret%d" % h] = r
                row["ex%d" % h] = r - q
                if uni:
                    row["luck%d" % h] = (r - q) - sum(uni) / len(uni)
            picks.append(row)

    summary = {}
    for h in HORIZONS:
        summary[h] = {"excess": _stats([p["ex%d" % h] for p in picks if "ex%d" % h in p]),
                      "vs_universe": _stats([p["luck%d" % h] for p in picks if "luck%d" % h in p])}
    m = summary[MAIN]
    ex, lk = m["excess"], m["vs_universe"]
    if ex["n"] < PASS_MIN:
        verdict = "VENTER (%d/%d picks scoret)" % (ex["n"], PASS_MIN)
    elif ex["mean"] > 0 and (ex["t"] or 0) > 2 and (lk["mean"] or 0) > 0:
        verdict = "PASS"
    else:
        verdict = "FAIL"
    return {"picks": picks, "summary": summary, "verdict": verdict,
            "days": len(days), "days_with_picks": sum(1 for d in days if d.get("picks")),
            "problems": sorted(set(problems))}


def _pct(x):
    return "-" if x is None else "%+.2f %%" % (100 * x)


def report(result, now_utc):
    lines = ["# Haiku-nyhedsdagbog (kun papir)", "",
             "Opdateret %s UTC. Dage logget: %d, dage med køb: %d." % (
                 now_utc, result["days"], result["days_with_picks"]),
             "", "**Status: %s**" % result["verdict"], "",
             "| Horisont | Picks | Merafkast vs QQQ efter 0,5 % | t | vs. hele listen |",
             "|---|---|---|---|---|"]
    for h in HORIZONS:
        ex, lk = result["summary"][h]["excess"], result["summary"][h]["vs_universe"]
        t = "-" if ex["t"] is None else "%.2f" % ex["t"]
        lines.append("| %d dag%s | %d | %s | %s | %s |" % (
            h, "" if h == 1 else "e", ex["n"], _pct(ex["mean"]), t, _pct(lk["mean"])))
    lines += ["", "PASS kræver mindst %d picks ved 5 dage, merafkast > 0 med t > 2 og bedre end "
              "gennemsnittet af hele listen. Overlappende 5-dages perioder gør t lidt for optimistisk." % PASS_MIN,
              "", "## Seneste picks", "", "| Dato | Aktie | Sikkerhed | 5 dage vs QQQ | Begrundelse |",
              "|---|---|---|---|---|"]
    for p in result["picks"][-15:][::-1]:
        lines.append("| %s | %s | %s | %s | %s |" % (
            p["date"], p["ticker"], p.get("confidence") or "-",
            p.get("invalid") or _pct(p.get("ex5")), p["reason"].replace("|", "/")))
    if result["problems"]:
        lines += ["", "## Problemer", ""] + ["- " + x for x in result["problems"][:20]]
    return "\n".join(lines) + "\n"


def run(base_dir, opener=urllib.request.urlopen, force=False):
    """Score data/nyheder/journal into score.md / score.json; skip if nothing is due."""
    journal_dir = os.path.join(base_dir, "journal")
    out_md = os.path.join(base_dir, "score.md")
    days = load_journal(journal_dir)
    if not days:
        return None
    newest = max(os.path.getmtime(os.path.join(journal_dir, n)) for n in os.listdir(journal_dir))
    if (not force and os.path.exists(out_md) and os.path.getmtime(out_md) > newest
            and time.time() - os.path.getmtime(out_md) < PRICE_MAX_AGE):
        return None
    cache_dir = os.path.join(base_dir, "prices")
    result = score(days, lambda t, start: prices(t, start, cache_dir, opener))
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
    text = report(result, now)
    for path, body in ((out_md, text), (os.path.join(base_dir, "score.json"),
                                        json.dumps(result, indent=1, default=str))):
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(path + ".tmp", path)
    return text
