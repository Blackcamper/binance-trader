"""Textbook rules with fixed defaults (lens 1). No tuning.

Each signal rule takes closed candles (oldest first) and returns the position it
wants now: 1 = fully long, 0 = all cash, None = not enough history yet.
"""


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
    return pos


def momentum(candles, lookback=90):
    """Hold while the close is above the close `lookback` candles ago."""
    if len(candles) <= lookback:
        return None
    return 1 if candles[-1]["c"] > candles[-1 - lookback]["c"] else 0


SIGNALS = {
    "ema_cross": lambda c, s: ema_cross(c, s.get("fast", 50), s.get("slow", 200)),
    "donchian": lambda c, s: donchian(c, s.get("entry", 20), s.get("exit", 10)),
    "momentum": lambda c, s: momentum(c, s.get("lookback", 90)),
}


def target(strategy, candles):
    return SIGNALS[strategy["type"]](candles, strategy)
