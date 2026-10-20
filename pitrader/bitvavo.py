"""Bitvavo REST: public market data and signed account calls.

Docs: https://docs.bitvavo.com/docs/get-started/
      https://legacy-docs.bitvavo.com (field names, signature example)

Signature: hex HMAC-SHA256 of timestamp(ms) + METHOD + "/v2" + path + body, sent in
Bitvavo-Access-* headers. POST /order needs an integer operatorId.

The key is read from the environment (BITVAVO_KEY / BITVAVO_SECRET), never from a
file in the repo. It must have View + Trade only, never Withdraw (live plan, sec. 5).
"""

import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.bitvavo.com/v2"
USER_AGENT = "pitrader/0.1"
ACCESS_WINDOW_MS = 10000


class MarketError(Exception):
    """Network failure or an error reported by Bitvavo."""


def sign(secret, timestamp_ms, method, path, body=""):
    msg = "%d%s/v2%s%s" % (timestamp_ms, method, path, body)
    return hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


class Bitvavo:
    def __init__(self, key=None, secret=None, request_gap=0.5, timeout=20, opener=None,
                 clock=time.time):
        self.key = key
        self.secret = secret
        self.request_gap = request_gap
        self.timeout = timeout
        self._opener = opener or urllib.request.urlopen
        self._clock = clock
        self._last_call = 0.0
        self.calls = 0

    def _request(self, method, path, params=None, body=None, signed=False):
        wait = self._last_call + self.request_gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        if params:
            path = path + "?" + urllib.parse.urlencode(params)
        data = json.dumps(body, separators=(",", ":")) if body is not None else ""
        headers = {"User-Agent": USER_AGENT}
        if data:
            headers["Content-Type"] = "application/json"
        if signed:
            if not (self.key and self.secret):
                raise MarketError("no API key configured")
            ts = int(self._clock() * 1000)
            headers.update({
                "Bitvavo-Access-Key": self.key,
                "Bitvavo-Access-Timestamp": str(ts),
                "Bitvavo-Access-Signature": sign(self.secret, ts, method, path, data),
                "Bitvavo-Access-Window": str(ACCESS_WINDOW_MS),
            })
        req = urllib.request.Request(BASE + path, data=data.encode("utf-8") if data else None,
                                     headers=headers, method=method)
        self._last_call = time.monotonic()
        self.calls += 1
        try:
            with self._opener(req, timeout=self.timeout) as resp:
                out = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read().decode("utf-8"))
            except (ValueError, OSError):
                detail = str(e)
            raise MarketError("%s %s: %s" % (method, path, detail))
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise MarketError("%s %s: %s" % (method, path, e))
        if isinstance(out, dict) and "errorCode" in out:
            raise MarketError("%s %s: %s %s" % (method, path, out["errorCode"], out.get("error")))
        return out

    # ---- public

    def candles(self, market, interval, now, limit=1440):
        """Closed candles only, oldest first, as dicts like Kraken.ohlc."""
        rows = self._request("GET", "/%s/candles" % market,
                             {"interval": interval, "limit": limit})
        return closed_candles(rows, INTERVAL_SECONDS[interval], now)

    def book(self, market):
        """Return (bid, ask) as floats."""
        t = self._request("GET", "/ticker/book", {"market": market})
        return float(t["bid"]), float(t["ask"])

    # ---- signed

    def balances(self):
        """{symbol: (available, in_order)} for every non-zero balance."""
        rows = self._request("GET", "/balance", signed=True)
        return {r["symbol"]: (float(r["available"]), float(r["inOrder"])) for r in rows}

    def place_limit(self, market, side, amount, price, operator_id, client_order_id,
                    post_only=True):
        body = {"market": market, "side": side, "orderType": "limit",
                "amount": fmt(amount), "price": fmt(price), "postOnly": post_only,
                "operatorId": int(operator_id), "clientOrderId": client_order_id}
        return self._request("POST", "/order", body=body, signed=True)

    def order(self, market, order_id):
        return self._request("GET", "/order", {"market": market, "orderId": order_id},
                             signed=True)

    def cancel(self, market, order_id, operator_id):
        return self._request("DELETE", "/order", {"market": market, "orderId": order_id,
                                                  "operatorId": int(operator_id)}, signed=True)


INTERVAL_SECONDS = {"1h": 3600, "4h": 14400, "1d": 86400}


def closed_candles(rows, interval_s, now):
    """Bitvavo returns newest first, timestamps in ms; drop the still-forming one."""
    out = []
    for r in rows:
        t = int(r[0]) // 1000
        if t + interval_s > now:
            continue
        out.append({"t": t, "o": float(r[1]), "h": float(r[2]), "l": float(r[3]),
                    "c": float(r[4]), "v": float(r[5])})
    out.sort(key=lambda c: c["t"])
    return out


def fmt(x):
    """Plain decimal string without exponent; Bitvavo rejects 1e-05."""
    return ("%.8f" % x).rstrip("0").rstrip(".")
