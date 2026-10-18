import copy
import io
import json
import math
import os
import shutil
import tempfile
import unittest

from pitrader import config, strategies
from pitrader.kraken import Kraken, MarketError, closed_candles
from pitrader.ledger import Book, walk_buy, walk_sell
from pitrader.sim import ConfigChanged, Simulator

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = config.load(os.path.join(HERE, "..", "config", "sim-v1.json"))
T0 = 1792800000  # 2026-10-23 UTC, a day boundary


class FakeMarket:
    """Deterministic market: price follows a function of time, book is 0.1% wide."""

    def __init__(self, price_fn):
        self.price_fn = price_fn
        self.now = T0
        self.fail = False
        self.calls = []

    def _p(self, pair, t):
        base = self.price_fn(t)
        return base if pair == "XBTEUR" else base / 25.0

    def ticker(self, pair):
        self.calls.append("ticker")
        if self.fail:
            raise MarketError("EService:Unavailable")
        p = self._p(pair, self.now)
        return p * 0.9995, p * 1.0005, p

    def depth(self, pair, count):
        self.calls.append("depth")
        p = self._p(pair, self.now)
        bids = [(p * (0.9995 - i * 0.0001), 0.05) for i in range(count)]
        asks = [(p * (1.0005 + i * 0.0001), 0.05) for i in range(count)]
        return bids, asks

    def ohlc(self, pair, interval, now):
        self.calls.append("ohlc")
        step = interval * 60
        last_open = (now // step) * step
        rows = []
        for k in range(720, -1, -1):          # 720 closed + the forming one
            t = last_open - k * step
            o, c = self._p(pair, t), self._p(pair, t + step)
            rows.append([t, o, max(o, c), min(o, c), c, c, 1.0, 1])
        return closed_candles(rows, interval, now)


def rising(t):
    return 50000 * math.exp((t - T0) / (86400 * 365) * 0.5)


def wave(t):
    return 50000 * (1 + 0.3 * math.sin((t - T0) / (86400 * 30)))


def read_status(d):
    with open(os.path.join(d, "status.json")) as f:
        return json.load(f)


class Clock:
    def __init__(self, market):
        self.market = market

    def __call__(self):
        return self.market.now


def make(tmp, market, cfg=CFG, health=None):
    return Simulator(cfg, tmp, market, clock=Clock(market),
                     health=health or (lambda: {"ntp_synced": True, "throttled": "0x0"}))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)


class TestIndicators(unittest.TestCase):
    def test_ema_constant_series(self):
        e = strategies.ema([2.0] * 10, 3)
        self.assertIsNone(e[1])
        self.assertAlmostEqual(e[-1], 2.0)

    def c(self, closes):
        return [{"t": i, "o": x, "h": x, "l": x, "c": x, "v": 1} for i, x in enumerate(closes)]

    def test_ema_cross_needs_history(self):
        self.assertIsNone(strategies.ema_cross(self.c([1.0] * 199)))
        self.assertEqual(strategies.ema_cross(self.c(list(range(1, 300)))), 1)
        self.assertEqual(strategies.ema_cross(self.c(list(range(300, 1, -1)))), 0)

    def test_donchian_enters_and_exits(self):
        flat = [100.0] * 25
        self.assertEqual(strategies.donchian(self.c(flat + [101.0])), 1)
        self.assertEqual(strategies.donchian(self.c(flat + [101.0, 102.0, 99.0])), 0)
        self.assertEqual(strategies.donchian(self.c(flat)), 0)

    def test_momentum(self):
        self.assertEqual(strategies.momentum(self.c([1.0] * 90 + [2.0]), 90), 1)
        self.assertEqual(strategies.momentum(self.c([2.0] * 90 + [1.0]), 90), 0)
        self.assertIsNone(strategies.momentum(self.c([1.0] * 90), 90))


class TestKraken(unittest.TestCase):
    def test_forming_candle_dropped(self):
        rows = [[0, "1", "1", "1", "1", "1", "1", 1], [240 * 60, "2", "2", "2", "2", "2", "2", 1]]
        self.assertEqual(len(closed_candles(rows, 240, 240 * 60 + 10)), 1)
        self.assertEqual(closed_candles(rows, 240, 100), [])

    def test_parses_kraken_payloads(self):
        payloads = {
            "Ticker": {"error": [], "result": {"XXBTZEUR": {
                "a": ["60001.0", "1", "1.000"], "b": ["59999.0", "2", "2.000"],
                "c": ["60000.0", "0.1"]}}},
            "Depth": {"error": [], "result": {"XXBTZEUR": {
                "asks": [["60001.0", "0.5", 1]], "bids": [["59999.0", "0.7", 1]]}}},
            "OHLC": {"error": [], "result": {"XXBTZEUR": [
                [T0 - 2 * 14400, "1", "2", "0.5", "1.5", "1.2", "10", 5],
                [T0 - 14400, "1.5", "2", "1", "1.8", "1.6", "10", 5]], "last": T0 - 14400}},
            "Bad": {"error": ["EAPI:Rate limit exceeded"]},
        }

        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def opener(req, timeout):
            method = req.full_url.split("/public/")[1].split("?")[0]
            return Resp(json.dumps(payloads[method]).encode())

        k = Kraken(request_gap=0, opener=opener)
        self.assertEqual(k.ticker("XBTEUR"), (59999.0, 60001.0, 60000.0))
        self.assertEqual(k.depth("XBTEUR", 10), ([(59999.0, 0.7)], [(60001.0, 0.5)]))
        candles = k.ohlc("XBTEUR", 240, T0)
        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0]["c"], 1.5)
        with self.assertRaises(MarketError):
            k._get("Bad")


class TestLedger(unittest.TestCase):
    def test_walk_buy_spends_budget_including_fee(self):
        asks = [(100.0, 1.0), (101.0, 1.0)]
        qty, gross, fee, price, thin = walk_buy(asks, 150.0, 0.008, 0.0)
        self.assertAlmostEqual(gross + fee, 150.0)
        self.assertGreater(price, 100.0)          # walked into the second level
        self.assertFalse(thin)

    def test_walk_sell_thin_book_penalised(self):
        qty, gross, fee, price, thin = walk_sell([(100.0, 0.5)], 1.0, 0.0, 0.0)
        self.assertTrue(thin)
        self.assertAlmostEqual(gross, 50 + 49.5)

    def test_fifo_and_tax(self):
        b = Book(1000.0)
        b.buy(1.0, 400.0, 0.0)
        b.buy(1.0, 500.0, 0.0)
        b.sell(1.0, 600.0, 0.0, T0)             # FIFO: cost 400 -> gain 200
        self.assertAlmostEqual(b.realised[2026], 200.0)
        sc = {"gain_rate": 0.5, "loss_value_rate": 0.25}
        # open lot cost 500, bid 300 -> unrealised -200 nets the year to 0
        self.assertAlmostEqual(b.tax(300.0, 0.0, sc, T0), 0.0)
        # next year: gain 200 taxed in 2026, loss 200 in 2027 worth only 25%
        self.assertAlmostEqual(b.tax(300.0, 0.0, sc, T0 + 400 * 86400), 100.0 - 50.0)


class TestSimulator(Base):
    def run_days(self, sim, market, days, step=300):
        end = market.now + days * 86400
        while market.now < end:
            sim.poll()
            market.now += step

    def test_fills_happen_one_poll_after_decision(self):
        m = FakeMarket(rising)
        sim = make(self.tmp, m)
        sim.poll()
        self.assertIn("bh_btc", sim.pending)
        self.assertEqual(sim.books["bh_btc"].qty, 0)
        m.now += 300
        sim.poll()
        self.assertNotIn("bh_btc", sim.pending)
        self.assertGreater(sim.books["bh_btc"].qty, 0)
        fill = sim.trades["bh_btc"][0]
        self.assertGreater(fill["price"], rising(m.now))    # paid above mid
        self.assertAlmostEqual(fill["fee"] / fill["gross"], CFG["taker_fee"])

    def test_full_run_and_replay_matches(self):
        m = FakeMarket(wave)
        sim = make(self.tmp, m)
        self.run_days(sim, m, 60, step=3600)
        trades = sum(b.buys + b.sells for b in sim.books.values())
        self.assertGreater(trades, 10)
        self.assertEqual(len(sim.orders["dca_btc"]), 9)       # weekly over 60 days
        self.assertEqual(sim.books["bh_btc"].buys, 1)
        self.assertEqual(sim.books["bh_btc"].sells, 0)
        # restart from the journal: identical books
        again = make(self.tmp, m)
        for sid in sim.books:
            a, b = sim.books[sid], again.books[sid]
            self.assertAlmostEqual(a.cash, b.cash, places=9)
            self.assertAlmostEqual(a.qty, b.qty, places=12)
            self.assertEqual(a.realised, b.realised)
        st = read_status(self.tmp)
        self.assertEqual(st["phase"][:8], "live sim")
        self.assertNotIn("PASS", st["verdict"].replace("never prints PASS", "").replace(
            "PASS needs", ""))
        self.assertEqual(len(st["strategies"]), len(CFG["strategies"]))
        for r in st["strategies"]:
            self.assertGreater(r["equity_dkk"], 0)
        with open(os.path.join(self.tmp, "summary.txt")) as f:
            self.assertIn("Baseline, pay down", f.read())

    def test_costs_make_flat_market_lose(self):
        m = FakeMarket(lambda t: 50000.0)
        sim = make(self.tmp, m)
        self.run_days(sim, m, 1)
        st = read_status(self.tmp)
        bh = [r for r in st["strategies"] if r["id"] == "bh_btc"][0]
        self.assertLess(bh["equity_dkk"], 5000)
        self.assertGreater(bh["fees_dkk"], 39)                # 0.8% of 5,000
        self.assertLess(bh["after_tax_liquidation_dkk"]["high"], bh["equity_dkk"])

    def test_config_change_refused(self):
        m = FakeMarket(rising)
        make(self.tmp, m).poll()
        changed = copy.deepcopy(CFG)
        changed["taker_fee"] = 0.004
        with self.assertRaises(ConfigChanged):
            make(self.tmp, m, cfg=changed)

    def test_no_trading_without_ntp(self):
        m = FakeMarket(rising)
        sim = make(self.tmp, m, health=lambda: {"ntp_synced": False, "throttled": None})
        sim.poll()
        self.assertEqual(sim.pending, {})
        st = read_status(self.tmp)
        self.assertFalse(st["health"]["trading_enabled"])

    def test_outage_is_reported_not_fatal(self):
        m = FakeMarket(rising)
        sim = make(self.tmp, m)
        m.fail = True
        self.assertFalse(sim.poll())
        st = read_status(self.tmp)
        self.assertTrue(st["stale"])
        self.assertEqual(st["health"]["consecutive_failures"], 1)
        m.fail = False
        m.now += 300
        self.assertTrue(sim.poll())

    def test_torn_last_journal_line_ignored(self):
        m = FakeMarket(rising)
        sim = make(self.tmp, m)
        sim.poll()
        with open(sim.journal.path, "a") as f:
            f.write('{"e":"fill","t":')
        again = make(self.tmp, m)
        self.assertIn("bh_btc", again.pending)

    def test_ohlc_fetched_only_when_a_candle_can_close(self):
        m = FakeMarket(rising)
        sim = make(self.tmp, m)
        sim.poll()
        first = m.calls.count("ohlc")
        m.now += 300
        sim.poll()
        self.assertEqual(m.calls.count("ohlc"), first)


if __name__ == "__main__":
    unittest.main()
