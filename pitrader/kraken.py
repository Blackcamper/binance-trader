"""Kraken public REST market data. No API key, GET requests only.

Docs: https://docs.kraken.com/api/docs/rest-api/get-ohlc-data
      https://docs.kraken.com/api/docs/rest-api/get-ticker-information
      https://docs.kraken.com/api/docs/rest-api/get-order-book
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.kraken.com/0/public/"
USER_AGENT = "pitrader/0.1 (paper trading, public data only)"


class MarketError(Exception):
    """Network failure or an error reported by Kraken."""


class Kraken:
    def __init__(self, request_gap=1.2, timeout=20, opener=None):
        self.request_gap = request_gap
        self.timeout = timeout
        self._opener = opener or urllib.request.urlopen
        self._last_call = 0.0
        self.calls = 0

    def _get(self, method, **params):
        wait = self._last_call + self.request_gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        url = BASE + method + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        self._last_call = time.monotonic()
        self.calls += 1
        try:
            with self._opener(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise MarketError("%s: %s" % (method, e))
        if body.get("error"):
            raise MarketError("%s: %s" % (method, ", ".join(body["error"])))
        return body["result"]

    @staticmethod
    def _only(result):
        keys = [k for k in result if k != "last"]
        if len(keys) != 1:
            raise MarketError("expected one pair in result, got %r" % keys)
        return result[keys[0]]

    def ticker(self, pair):
        """Return (bid, ask, last) as floats."""
        t = self._only(self._get("Ticker", pair=pair))
        return float(t["b"][0]), float(t["a"][0]), float(t["c"][0])

    def ohlc(self, pair, interval, now):
        """Return CLOSED candles only, oldest first, as dicts.

        Kraken's last row is the still-forming candle; it is dropped, and so is any
        row whose close time is not yet past `now` (lens 1: trade closed candles only).
        """
        rows = self._only(self._get("OHLC", pair=pair, interval=interval))
        return closed_candles(rows, interval, now)

    def depth(self, pair, count):
        """Return (bids, asks) as lists of (price, volume), best first."""
        book = self._only(self._get("Depth", pair=pair, count=count))
        bids = [(float(p), float(v)) for p, v, *_ in book["bids"]]
        asks = [(float(p), float(v)) for p, v, *_ in book["asks"]]
        return bids, asks

    def asset_pairs(self, pairs):
        return self._get("AssetPairs", pair=",".join(pairs))


def closed_candles(rows, interval, now):
    out = []
    for r in rows[:-1]:
        t = int(r[0])
        if t + interval * 60 > now:
            break
        out.append({"t": t, "o": float(r[1]), "h": float(r[2]), "l": float(r[3]),
                    "c": float(r[4]), "v": float(r[6])})
    return out
