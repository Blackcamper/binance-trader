import hashlib
import hmac
import io
import json
import os
import shutil
import tempfile
import unittest

from pitrader import bitvavo, live

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(os.path.dirname(HERE), "config", "live-dry-v1.json")
DAY = 86400
T0 = 1483228800  # 2017-01-01


def daily(closes, t0=T0):
    return [{"t": t0 + i * DAY, "o": c, "h": c, "l": c, "c": c, "v": 1} for i, c in enumerate(closes)]


class FakeMarket:
    def __init__(self, candles, bid, ask):
        self.c, self.bid, self.ask, self.fail = candles, bid, ask, False

    def candles(self, market, interval, now):
        if self.fail:
            raise bitvavo.MarketError("down")
        return [c for c in self.c if c["t"] + DAY <= now]

    def book(self, market):
        return self.bid, self.ask


class TestBitvavo(unittest.TestCase):
    def test_signature_matches_reference(self):
        # same construction as Bitvavo's Python sample: ts + method + '/v2' + url + body
        body = '{"market":"BTC-EUR"}'
        want = hmac.new(b"s3cret", b'1700000000000POST/v2/order' + body.encode(),
                        hashlib.sha256).hexdigest()
        self.assertEqual(bitvavo.sign("s3cret", 1700000000000, "POST", "/order", body), want)

    def test_signed_headers_and_candle_order(self):
        seen = []

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def opener(req, timeout):
            seen.append(req)
            if "/candles" in req.full_url:
                # newest first; the newest one is still forming
                rows = [[(T0 + 2 * DAY) * 1000, "3", "3", "3", "3", "1"],
                        [(T0 + DAY) * 1000, "2", "2", "2", "2", "1"],
                        [T0 * 1000, "1", "1", "1", "1", "1"]]
                return Resp(json.dumps(rows).encode())
            return Resp(json.dumps([{"symbol": "EUR", "available": "10", "inOrder": "0"}]).encode())

        b = bitvavo.Bitvavo("k", "s", request_gap=0, opener=opener, clock=lambda: 1700000000.0)
        c = b.candles("BTC-EUR", "1d", T0 + 2 * DAY + 3600)
        self.assertEqual([x["c"] for x in c], [1.0, 2.0])
        self.assertEqual(b.balances(), {"EUR": (10.0, 0.0)})
        h = {k.lower(): v for k, v in seen[-1].header_items()}
        self.assertEqual(h["bitvavo-access-timestamp"], "1700000000000")
        self.assertEqual(h["bitvavo-access-signature"],
                         bitvavo.sign("s", 1700000000000, "GET", "/balance"))

    def test_fmt_has_no_exponent(self):
        self.assertEqual(bitvavo.fmt(0.00001), "0.00001")
        self.assertEqual(bitvavo.fmt(73000.0), "73000")


class TestLive(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.cfg = live.load_config(CFG)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def ex(self, market, now):
        return live.Executor(self.cfg, self.dir, market, clock=lambda: now[0])

    def test_refuses_live_mode(self):
        bad = dict(self.cfg, mode="live")
        with self.assertRaises(live.LiveConfigError):
            live.validate(bad)

    def test_buys_on_uptrend_and_replays(self):
        c = daily([100 + i for i in range(420)])
        now = [c[-1]["t"] + DAY + 3600]
        m = FakeMarket(c, 519.0, 520.0)
        st = self.ex(m, now).step({"position": "long"})
        self.assertEqual(st["target"], 1)
        self.assertGreater(st["qty"], 0)
        self.assertLess(st["eur"], 1)
        # a restart rebuilds the same state and does not buy again
        st2 = self.ex(m, now).step({"position": "long"})
        self.assertEqual(st2["orders_total"], 1)
        self.assertAlmostEqual(st2["qty"], st["qty"])

    def test_stop_file_halts_and_resume_needs_file_gone(self):
        c = daily([100 + i for i in range(420)])
        now = [c[-1]["t"] + DAY + 3600]
        open(os.path.join(self.dir, "STOP"), "w").close()
        st = self.ex(FakeMarket(c, 519.0, 520.0), now).step()
        self.assertEqual(st["halted"], "STOP file")
        self.assertEqual(st["orders_total"], 0)

    def test_error_streak_halts(self):
        c = daily([100 + i for i in range(420)])
        now = [c[-1]["t"] + DAY + 3600]
        m = FakeMarket(c, 519.0, 520.0)
        m.fail = True
        ex = self.ex(m, now)
        for _ in range(3):
            st = ex.step()
        self.assertIn("errors in a row", st["halted"])

    def test_loss_limit_sells_and_halts(self):
        c = daily([100 + i for i in range(420)])
        now = [c[-1]["t"] + DAY + 3600]
        m = FakeMarket(c, 519.0, 520.0)
        ex = self.ex(m, now)
        ex.step()
        m.bid, m.ask = 300.0, 301.0   # -42 %
        now[0] += 3600
        st = ex.step()
        self.assertTrue(st["halted"].startswith("loss limit"))
        self.assertEqual(st["qty"], 0)

    def test_disagreement_with_paper_halts_after_window(self):
        c = daily([100 + i for i in range(420)])
        now = [c[-1]["t"] + DAY + 3600]
        ex = self.ex(FakeMarket(c, 519.0, 520.0), now)
        ex.step({"position": "cash"})
        self.assertIsNone(ex.halted)
        now[0] += self.cfg["kill"]["max_disagree_s"] + 1
        st = ex.step({"position": "cash"})
        self.assertEqual(st["halted"], "disagrees with paper arm")

    def test_stale_candles_no_order(self):
        c = daily([100 + i for i in range(420)])
        now = [c[-1]["t"] + 5 * DAY]
        st = self.ex(FakeMarket(c, 519.0, 520.0), now).step()
        self.assertEqual(st["orders_total"], 0)
        self.assertIn("stale", st["message"])

    def test_round_price_never_crosses(self):
        self.assertEqual(live.round_price(73067.46, "buy"), 73067)
        self.assertEqual(live.round_price(73067.46, "sell"), 73068)


if __name__ == "__main__":
    unittest.main()
