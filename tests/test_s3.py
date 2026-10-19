import json
import math
import os
import shutil
import tempfile
import unittest

from pitrader import backtest, config, llm, strategies
from pitrader.sim import Simulator, rebalance_step

HERE = os.path.dirname(os.path.abspath(__file__))
DAY = 86400
T0 = 1483228800  # 2017-01-01


def daily(closes, t0=T0):
    return [{"t": t0 + i * DAY, "o": c, "h": c, "l": c, "c": c, "v": 1} for i, c in enumerate(closes)]


class TestS3Rules(unittest.TestCase):
    def test_month_end(self):
        self.assertTrue(strategies.is_month_end(1485820800))   # 2017-01-31
        self.assertFalse(strategies.is_month_end(1485734400))  # 2017-01-30

    def test_faber_and_tsmom(self):
        up = daily([100 + i for i in range(420)])
        down = daily([600 - i for i in range(420)])
        self.assertEqual(strategies.faber(up), 1)
        self.assertEqual(strategies.faber(down), 0)
        self.assertEqual(strategies.tsmom(up), 1)
        self.assertEqual(strategies.tsmom(down), 0)
        self.assertIsNone(strategies.tsmom(daily([1.0] * 200)))

    def test_monthly_target_fixed_inside_month(self):
        c = daily([100 + i for i in range(420)])
        cut = strategies.through_month_end(c)
        self.assertTrue(strategies.is_month_end(cut[-1]["t"]))
        # a crash after the month end does not change the monthly answer
        crashed = c[:len(cut)] + daily([1.0] * 5, cut[-1]["t"] + DAY)
        self.assertEqual(strategies.faber(crashed), strategies.faber(c[:len(cut)]))

    def test_vol_target_caps_at_one_and_scales(self):
        calm = daily([100 * (1.0005 ** i) for i in range(200)])
        self.assertEqual(strategies.vol_target(calm), 1.0)
        wild = daily([100 * (1.08 if i % 2 else 0.93) ** (i % 2) * (1 + 0.0001 * i) for i in range(200)])
        w = strategies.vol_target(wild)
        self.assertTrue(0 < w < 1, w)

    def test_crash_exit_and_reentry(self):
        closes = [100.0] * 210 + [74.0] * 5          # -26 % from the high: out
        self.assertEqual(strategies.crash_exit(daily(closes)), 0)
        closes += [120.0] * 3                        # back above the 200-day average: in
        self.assertEqual(strategies.crash_exit(daily(closes)), 1)
        self.assertEqual(strategies.crash_exit(daily([100.0] * 210 + [80.0])), 1)

    def test_dip_multiplier(self):
        base = [100.0] * 200
        self.assertEqual(strategies.dip_multiplier(daily(base + [120.0])), 0)
        self.assertEqual(strategies.dip_multiplier(daily(base + [90.0])), 1)
        self.assertEqual(strategies.dip_multiplier(daily(base + [70.0])), 2)

    def test_rebalance_step(self):
        self.assertEqual(rebalance_step(1, 100.0, 0.0, 10.0, 0.5), ("buy", 100.0))
        self.assertIsNone(rebalance_step(1, 0.5, 10.0, 10.0, 0.5))
        self.assertEqual(rebalance_step(0, 0.0, 10.0, 10.0, 0.5), ("sell", 1.0))
        self.assertIsNone(rebalance_step(0.95, 0.0, 10.0, 10.0, 0.10))     # inside band
        side, frac = rebalance_step(0.6, 0.0, 10.0, 10.0, 0.10)
        self.assertEqual(side, "sell")
        self.assertAlmostEqual(frac, 0.4)


class TestBacktest(unittest.TestCase):
    def setUp(self):
        self.cfg = config.load(os.path.join(HERE, "..", "config", "sim-v2.json"))

    def test_paths_match_prefix_calls(self):
        closes = [100 * (1 + 0.3 * math.sin(i / 40.0)) for i in range(700)]
        c = daily(closes)
        for s in self.cfg["strategies"]:
            if s["pair"] != "XBTEUR" or s["type"] in ("buy_and_hold", "dca", "dip_dca", "donchian"):
                continue
            tg = backtest.targets(s, c)
            for i in (450, 520, 699):
                self.assertEqual(tg[i] is None, strategies.target(s, c[:i + 1]) is None, s["id"])
                if tg[i] is not None and s["type"] not in strategies.MONTHLY:
                    self.assertEqual(tg[i], strategies.target(s, c[:i + 1]), s["id"])

    def test_flat_market_costs_and_falls(self):
        c = daily([100.0] * 1300)
        s = {"id": "x", "type": "buy_and_hold", "pair": "XBTEUR"}
        r = backtest.run_arm(s, c, self.cfg, start=T0 + 500 * DAY)
        self.assertLess(r["book"].value(100.0), self.cfg["capital_dkk"] / self.cfg["eur_dkk"])
        series = [(i, v) for i, v in enumerate([100, 60, 80, 120, 70, 130])]
        self.assertEqual([round(f[2], 2) for f in backtest.falls(series)], [0.4, 0.42])

    def test_holm(self):
        adj = backtest.holm({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(adj["a"], 0.03)
        self.assertAlmostEqual(adj["c"], 0.06)
        self.assertAlmostEqual(adj["b"], 0.06)


class TestLLM(unittest.TestCase):
    def test_summary_written_even_when_model_is_down(self):
        d = tempfile.mkdtemp()
        try:
            with open(os.path.join(d, "status.json"), "w") as f:
                json.dump({"day": 2, "strategies": [], "health": {}, "assumptions": {}}, f)

            def down(req, timeout):
                raise OSError("no route")
            out = llm.daily_summary(d, {"url": "http://x", "model": "m"}, opener=down)
            self.assertFalse(out["llm_ok"])
            self.assertTrue(os.path.exists(os.path.join(d, "llm-summary.json")))
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main()
