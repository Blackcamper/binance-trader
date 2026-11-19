import calendar
import datetime
import io
import json
import os
import random
import shutil
import tempfile
import unittest
import urllib.parse
import zlib

from pitrader import stocks, strategies

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(os.path.dirname(HERE), "config", "stocks-v1.json")


def weekdays(start, end):
    d, out = start, []
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += datetime.timedelta(days=1)
    return out


def fake_series(seed, start=datetime.date(1997, 1, 2), end=datetime.date(2026, 11, 20), p=20.0):
    rng = random.Random(seed)
    rows = []
    for d in weekdays(start, end):
        o = p
        p = max(0.5, p * (1 + rng.gauss(0.0006, 0.025)))
        rows.append((d, o, max(o, p) * 1.01, min(o, p) * 0.99, p))
    return rows


class FakeYahoo:
    """Serves the chart API shape for any symbol; FX is a slow walk around 6.5."""

    def __init__(self, split_after=None):
        self.calls = []
        self.series = {}
        self.split_after = split_after

    def rows(self, sym):
        if sym not in self.series:
            self.series[sym] = fake_series(zlib.crc32(sym.encode()) % 1000, p=6.5 if sym == "DKK=X" else 20.0)
        return self.series[sym]

    def __call__(self, req, timeout=None):
        url = req.full_url
        self.calls.append(url)
        if "stooq" in url:
            raise OSError("stooq down in tests")
        sym = urllib.parse.unquote(url.split("/chart/")[1].split("?")[0])
        q = urllib.parse.parse_qs(url.split("?")[1])
        p1 = int(q["period1"][0])
        ts, o, h, l, c, v = [], [], [], [], [], []
        for d, oo, hh, ll, cc in self.rows(sym):
            t = calendar.timegm((d.year, d.month, d.day, 13, 30, 0))
            if t < p1 or t > self.now:
                continue
            f = 0.5 if self.split_after and d <= self.split_after else 1.0
            ts.append(t)
            o.append(oo * f), h.append(hh * f), l.append(ll * f), c.append(cc * f), v.append(1000)
        body = {"chart": {"result": [{"meta": {"gmtoffset": -14400}, "timestamp": ts,
                                      "indicators": {"quote": [{"open": o, "high": h, "low": l,
                                                                "close": c, "volume": v}]}}]}}
        return io.BytesIO(json.dumps(body).encode())


def utc(y, m, d, hh=0, mm=0):
    return calendar.timegm((y, m, d, hh, mm, 0))


class TestStockData(unittest.TestCase):
    def test_month_end_stamp_on_weekend(self):
        rows = [["2026-01-29", 1, 1, 1, 1, 0], ["2026-01-30", 1, 1, 1, 2, 0],
                ["2026-02-02", 1, 1, 1, 3, 0]]
        c = stocks.candles_from(rows)
        self.assertFalse(strategies.is_month_end(c[0]["t"]))
        self.assertTrue(strategies.is_month_end(c[1]["t"]))     # Fri 30th = last session
        self.assertEqual(c[1]["d"], "2026-01-30")
        # newest bar: month end only when the rest of the month is weekend
        self.assertTrue(strategies.is_month_end(stocks.candles_from(rows[:2])[-1]["t"]))
        self.assertFalse(strategies.is_month_end(stocks.candles_from(rows[:1])[-1]["t"]))

    def test_open_session_is_dropped(self):
        rows = [["2026-10-29", 1, 1, 1, 1, 0], ["2026-10-30", 1, 1, 1, 1, 0]]
        self.assertEqual(len(stocks.closed_only(rows, utc(2026, 10, 30, 18))), 1)
        self.assertEqual(len(stocks.closed_only(rows, utc(2026, 10, 30, 22))), 2)

    def test_fx_series_carries_forward(self):
        fx = [["2026-01-02", 0, 0, 0, 6.4, 0], ["2026-01-06", 0, 0, 0, 6.6, 0]]
        out, early = stocks.fx_series(fx, ["2026-01-01", "2026-01-05", "2026-01-06"])
        self.assertEqual(out, [6.4, 6.4, 6.6])
        self.assertEqual(early, 1)

    def test_fees_fit_budget(self):
        cfg = stocks.load_config(CFG)
        for budget in (50.0, 1000.0, 5000.0, 20000.0):
            g = stocks.gross_for_budget(budget, cfg)
            self.assertAlmostEqual(g + stocks.broker_fee(g, cfg), budget, places=6)
        self.assertEqual(stocks.broker_fee(1000.0, cfg), 7.0 + 2.5)   # minimum fee binds

    def test_split_triggers_full_refetch(self):
        tmp = tempfile.mkdtemp()
        try:
            y = FakeYahoo()
            y.now = utc(2026, 9, 1, 22)
            rows, _, _ = stocks.load_rows("NVDA", tmp, y, now=y.now)
            before = rows[0][4]
            y.split_after = datetime.date(2026, 9, 10)       # 2:1 split shows up later
            y.now = utc(2026, 9, 20, 22)
            rows, _, _ = stocks.load_rows("NVDA", tmp, y, now=y.now)
            self.assertAlmostEqual(rows[0][4], before * 0.5)  # history re-adjusted
            self.assertIn("period1=0", y.calls[-1])
        finally:
            shutil.rmtree(tmp)


class TestStockRules(unittest.TestCase):
    def test_fast_monthly_targets_match_strategies(self):
        rows = [[d.isoformat(), o, h, l, c, 0] for d, o, h, l, c in fake_series(3)[:1500]]
        candles = stocks.candles_from(rows)
        for s in ({"type": "faber", "months": 10}, {"type": "tsmom", "months": 12},
                  {"type": "vol_target", "target_vol": 0.4, "com": 60, "periods": 365}):
            fast = stocks.targets(s, candles)
            for i in range(300, 1500):
                if strategies.is_month_end(candles[i]["t"]):
                    slow = strategies.target(s, candles[:i + 1])
                    if s["type"] == "vol_target":
                        self.assertAlmostEqual(fast[i], slow, places=9)
                    else:
                        self.assertEqual(fast[i], slow, (s, i))

    def test_tax_progression(self):
        sc = {"gain_rate": 0.27, "threshold_dkk": 1000, "rate_above": 0.42}
        self.assertAlmostEqual(stocks.tax_on(500, sc), 135)
        self.assertAlmostEqual(stocks.tax_on(2000, sc), 270 + 420)
        self.assertAlmostEqual(stocks.tax_on(2000, {"gain_rate": 0.42}), 840)

    def test_yearly_tax_and_loss_carry(self):
        cfg = stocks.load_config(CFG)
        cfg.update(fee_rate=0.0, fee_min_dkk=0.0, fx_fee=0.0, half_spread=0.0,
                   extra_slippage_bps=0)
        rows = [["2025-12-29", 10, 10, 10, 10, 0], ["2025-12-30", 10, 10, 10, 20, 0],
                ["2025-12-31", 20, 20, 20, 20, 0], ["2026-01-02", 20, 20, 20, 20, 0],
                ["2026-01-05", 20, 20, 20, 20, 0]]
        c = stocks.candles_from(rows)
        fx = [1.0] * len(c)
        sc = {"gain_rate": 0.5, "loss_value_rate": 0.0}
        # in on the 30th at 10, out on the 31st at 20: 5000 gain in 2025, 2500 tax in Jan
        tgt = [1, 0, 0, 0, 0]
        s = {"id": "x", "type": "ema_cross"}
        r = stocks.run_arm(s, c, fx, cfg, 0, tax=sc, tgt=tgt)
        self.assertAlmostEqual(r["tax_paid"], 2500)
        self.assertAlmostEqual(r["after_tax"], 7500)
        # buy-and-hold pays nothing until the final sale
        bh = stocks.run_arm({"id": "b", "type": "buy_and_hold"}, c, fx, cfg, 0, tax=sc)
        self.assertEqual(bh["tax_paid"], 0)
        self.assertAlmostEqual(bh["after_tax"], 10000 - 5000 * 0.5)

    def test_arm_ids(self):
        ids = [a["id"] for a in stocks.arms(stocks.load_config(CFG))]
        self.assertIn("bh_nvda", ids)
        self.assertIn("faber_amd", ids)
        self.assertEqual(len(ids), len(set(ids)))


class TestStockRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cfg = stocks.load_config(CFG)
        self.cfg["tickers"] = ["NVDA", "SPY"]
        self.y = FakeYahoo()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def live(self, now):
        self.y.now = now
        return stocks.live(self.cfg, os.path.join(self.tmp, "run"), os.path.join(self.tmp, "c"),
                           self.y, now=now)

    def test_live_run(self):
        st = self.live(utc(2026, 10, 30, 22))
        self.assertTrue(st["phase"].startswith("not started"))
        st = self.live(utc(2026, 11, 2, 22))            # first session closed: orders only
        bh = next(r for r in st["strategies"] if r["id"] == "bh_nvda")
        self.assertEqual(bh["pending"], "buy")
        self.assertEqual(bh["buys"], 0)
        journal = os.path.join(self.tmp, "run", "decisions.jsonl")
        with open(journal) as f:
            self.assertIn('"bh_nvda"', f.read())
        st = self.live(utc(2026, 11, 20, 22))
        bh = next(r for r in st["strategies"] if r["id"] == "bh_nvda")
        self.assertEqual(bh["buys"], 1)
        self.assertEqual(bh["position"], "long")
        self.assertEqual(st["replay_mismatches"], [])
        self.assertTrue(st["phase"].startswith("live sim"))
        with open(os.path.join(self.tmp, "run", "summary.txt")) as f:
            self.assertIn("bh_nvda", f.read())
        # a forged journal entry the replay never makes is reported
        with open(journal, "a") as f:
            f.write('{"sid":"bh_spy","d":"2026-11-10","side":"sell"}\n')
        st = self.live(utc(2026, 11, 20, 23))
        self.assertEqual(st["replay_mismatches"], ["bh_spy 2026-11-10 sell"])

    def test_no_data_still_writes_status(self):
        def down(req, timeout=None):
            raise OSError("network down")
        st = stocks.live(self.cfg, os.path.join(self.tmp, "run"), os.path.join(self.tmp, "c"),
                         down, now=utc(2026, 11, 5, 22))
        self.assertEqual(st["strategies"], [])
        self.assertIn("network down", st["problems"][0])

    def test_config_is_locked(self):
        self.live(utc(2026, 11, 3, 22))
        self.cfg["fee_rate"] = 0.001
        with self.assertRaises(stocks.ConfigChanged):
            self.live(utc(2026, 11, 4, 22))

    def test_backtest(self):
        self.y.now = utc(2026, 10, 29, 22)
        res, report = stocks.run_backtest(self.cfg, os.path.join(self.tmp, "c"),
                                          os.path.join(self.tmp, "bt"), self.y, runs=50,
                                          now=self.y.now)
        self.assertEqual(len(res), 12)
        self.assertEqual(res["bh_nvda"]["verdict"], "reference")
        self.assertGreater(res["donchian_spy"]["round_trips"], 20)
        self.assertIsNotNone(res["faber_nvda"]["holm_p"])
        self.assertIn("## NVDA 2000-01-03", report)


if __name__ == "__main__":
    unittest.main()
