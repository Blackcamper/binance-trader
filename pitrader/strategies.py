"""Textbook rules with fixed defaults (lens 1). No tuning.

Each signal rule takes closed candles (oldest first) and returns the position it
wants now as a weight: 1 = fully long, 0 = all cash, in between = that share of
equity in the coin (vol_target only), None = not enough history yet.
"""

import math
import time


def ema(values, n):
    """EMA seeded with the SMA of the first n values. Returns a list aligned to values
    (None until the seed is available)."""
    out = [None] * len(values)
    if len(values) < n:
        return out
    k = 2.0 / (n + 1)
    e = sum(values[:n]) / n
    out[n - 1] = e
    for i in range(n, len(values)):
        e = values[i] * k + e * (1 - k)
        out[i] = e
    return out


def ema_cross(candles, fast=50, slow=200):
    """Long while EMA(fast) is above EMA(slow) on the daily close."""
    closes = [c["c"] for c in candles]
    if len(closes) < slow:
        return None
    f = ema(closes, fast)[-1]
    s = ema(closes, slow)[-1]
    return 1 if f > s else 0


def donchian(candles, entry=20, exit=10):
    """Buy when the close breaks above the prior `entry`-candle high; sell when it
    breaks below the prior `exit`-candle low. Stateful, so it is replayed over the
    whole history to know whether the rule is in a trade right now."""
    if len(candles) <= entry:
        return None
    return donchian_path(candles, entry, exit)[-1]


def donchian_path(candles, entry=20, exit=10):
    """Position after each candle (0 before there is enough history)."""
    out = [0] * len(candles)
    pos = 0
    start = max(entry, exit)
    for i in range(start, len(candles)):
        close = candles[i]["c"]
        if pos == 0:
            upper = max(c["h"] for c in candles[i - entry:i])
            if close > upper:
                pos = 1
        else:
            lower = min(c["l"] for c in candles[i - exit:i])
            if close < lower:
                pos = 0
        out[i] = pos
    return out


def momentum(candles, lookback=90):
    """Hold while the close is above the close `lookback` candles ago."""
    if len(candles) <= lookback:
        return None
    return 1 if candles[-1]["c"] > candles[-1 - lookback]["c"] else 0


# ---- S3 arms (D24). Daily candles. Monthly rules decide on the last closed
# month-end candle only, so their target is fixed for the whole next month.

DAY = 86400


def is_month_end(t):
    return time.gmtime(t).tm_mon != time.gmtime(t + DAY).tm_mon


def through_month_end(candles):
    """Candles up to and including the last closed month-end day."""
    for i in range(len(candles) - 1, -1, -1):
        if is_month_end(candles[i]["t"]):
            return candles[:i + 1]
    return []


def month_closes(candles):
    return [c["c"] for c in candles if is_month_end(c["t"])]


def sma(values, n):
    if len(values) < n:
        return None
    return sum(values[-n:]) / float(n)


def faber(candles, months=10):
    """Faber 2007: at month end, hold while the close is above the average of the
    last `months` month-end closes."""
    m = month_closes(through_month_end(candles))
    if len(m) < months:
        return None
    return 1 if m[-1] > sum(m[-months:]) / months else 0


def tsmom(candles, months=12):
    """Time-series momentum (Moskowitz-Ooi-Pedersen 2012): at month end, hold while
    the close is above the close `months` month-ends earlier."""
    m = month_closes(through_month_end(candles))
    if len(m) <= months:
        return None
    return 1 if m[-1] > m[-1 - months] else 0


def ewma_vol(closes, com=60, periods=365):
    """Annualised EWMA volatility of daily log returns, centre of mass `com` days."""
    if len(closes) < com + 2:
        return None
    a = 1.0 / (1.0 + com)
    var = None
    for i in range(1, len(closes)):
        r = math.log(closes[i] / closes[i - 1])
        var = r * r if var is None else (1 - a) * var + a * r * r
    return math.sqrt(var * periods)


def vol_target(candles, target=0.40, com=60):
    """Weight = min(1, target / EWMA vol), set at month end (D24 arm 1)."""
    hist = through_month_end(candles)
    v = ewma_vol([c["c"] for c in hist], com)
    if not v:
        return None
    return min(1.0, target / v)


def crash_exit(candles, drop=0.25, high_days=365, sma_days=200):
    """Hold BTC; sell all when the close is `drop` below the highest close of the last
    `high_days`; buy back when the close is above the `sma_days` average; the high
    restarts at re-entry (D24 arm 3, exploratory). Replayed over the history."""
    closes = [c["c"] for c in candles]
    if len(closes) < sma_days:
        return None
    return crash_exit_path(closes, drop, high_days, sma_days)[-1]


def crash_exit_path(closes, drop=0.25, high_days=365, sma_days=200):
    """Position after each close (None before `sma_days` of history). O(n) apart from
    the window max, which only rescans when the old high leaves the window."""
    out = [None] * len(closes)
    pos = 1
    since = 0                       # index where the current holding period began
    hi = hi_i = None
    run_sum = sum(closes[:sma_days - 1])
    for i in range(sma_days - 1, len(closes)):
        c = closes[i]
        run_sum += c
        if i >= sma_days:
            run_sum -= closes[i - sma_days]
        lo = max(since, i - high_days + 1)
        if hi is None or hi_i < lo:
            hi_i = max(range(lo, i + 1), key=lambda k: closes[k])
            hi = closes[hi_i]
        elif c >= hi:
            hi, hi_i = c, i
        if pos == 1:
            if c <= hi * (1 - drop):
                pos = 0
        elif c > run_sum / sma_days:
            pos = 1
            since = i
            hi, hi_i = c, i
        out[i] = pos
    return out


def dip_multiplier(candles, sma_days=200, deep=0.20):
    """Weekly DCA size vs the 200-day average: 2x when the close is more than `deep`
    below it, 1x when 0-`deep` below, 0x when above (D24 arm 4)."""
    closes = [c["c"] for c in candles]
    avg = sma(closes, sma_days)
    if avg is None:
        return None
    gap = closes[-1] / avg - 1
    if gap < -deep:
        return 2
    if gap < 0:
        return 1
    return 0


SIGNALS = {
    "ema_cross": lambda c, s: ema_cross(c, s.get("fast", 50), s.get("slow", 200)),
    "donchian": lambda c, s: donchian(c, s.get("entry", 20), s.get("exit", 10)),
    "momentum": lambda c, s: momentum(c, s.get("lookback", 90)),
    "faber": lambda c, s: faber(c, s.get("months", 10)),
    "tsmom": lambda c, s: tsmom(c, s.get("months", 12)),
    "vol_target": lambda c, s: vol_target(c, s.get("target_vol", 0.40), s.get("com", 60)),
    "crash_exit": lambda c, s: crash_exit(c, s.get("drop", 0.25), s.get("high_days", 365),
                                          s.get("sma_days", 200)),
}

# Rules that only change their mind at a month end; the simulator values the
# current holding at that month-end close so drift inside the month never trades.
MONTHLY = ("faber", "tsmom", "vol_target")


def target(strategy, candles):
    return SIGNALS[strategy["type"]](candles, strategy)
