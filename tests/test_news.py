import datetime
import json
import os
import shutil
import tempfile
import unittest

from pitrader import news

D = datetime.date


def bars(start, opens_closes):
    out, d = [], start
    for o, c in opens_closes:
        while d.weekday() >= 5:
            d += datetime.timedelta(days=1)
        out.append((d, o, c))
        d += datetime.timedelta(days=1)
    return out


class TestNewsScore(unittest.TestCase):
    def test_entry_waits_a_session_when_written_after_open(self):
        self.assertEqual(news.entry_date({"date": "2026-10-21", "written_utc": "2026-10-21T12:20Z"}), D(2026, 10, 21))
        self.assertEqual(news.entry_date({"date": "2026-10-21", "written_utc": "2026-10-21T14:05Z"}), D(2026, 10, 22))

    def test_window_return_open_to_close_with_cost(self):
        rows = bars(D(2026, 10, 21), [(100, 101), (101, 102), (102, 110)])
        self.assertAlmostEqual(news.window_return(rows, D(2026, 10, 21), 3, 0.005), 0.095)
        self.assertIsNone(news.window_return(rows, D(2026, 10, 21), 5))

    def test_score_excess_luck_and_verdict(self):
        flat = bars(D(2026, 10, 1), [(100, 100)] * 40)
        up = bars(D(2026, 10, 1), [(100, 100)] * 10 + [(100, 120)] * 30)
        prices = {t: flat for t in news.UNIVERSE + [news.BENCH]}
        prices["NVDA"] = up

        def get(t, start):
            if t == "SAP":
                raise news.PriceError("SAP: down")
            return prices[t]

        days = [{"date": "2026-10-15", "written_utc": "2026-10-15T12:00Z",
                 "picks": [{"ticker": "NVDA", "confidence": 3, "reason": "x"}]},
                {"date": "2026-10-16", "written_utc": "2026-10-16T12:00Z",
                 "picks": [{"ticker": "FAKE", "reason": "y"}]},
                {"date": "2026-10-19", "written_utc": "2026-10-19T12:00Z", "picks": []}]
        r = news.score(days, get)
        nv = r["picks"][0]
        self.assertAlmostEqual(nv["ex1"], 0.195)
        self.assertGreater(nv["luck5"], 0)
        self.assertEqual(r["picks"][1]["invalid"], "not in universe")
        self.assertTrue(r["verdict"].startswith("VENTER"))
        self.assertIn("SAP: down", r["problems"])
        self.assertIn("**Status: VENTER", news.report(r, "now"))

    def test_run_reads_journal_and_writes_report(self):
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "journal"))
            with open(os.path.join(tmp, "journal", "2026-10-21.json"), "w") as f:
                json.dump({"date": "2026-10-21", "picks": []}, f)

            def offline(req, timeout=0):
                raise OSError("offline")

            text = news.run(tmp, opener=offline)
            self.assertIn("Dage logget: 1", text)
            self.assertIsNone(news.run(tmp, opener=offline))   # nothing new
        finally:
            shutil.rmtree(tmp)

    def test_yahoo_parser(self):
        body = json.dumps({"chart": {"result": [{"meta": {"gmtoffset": -14400},
                                                 "timestamp": [1761053400, 1761139800],
                                                 "indicators": {"quote": [{"open": [10.0, None], "close": [11.0, 12.0]}]}}]}})

        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return body.encode()

        rows = news.yahoo_daily("NVDA", D(2025, 10, 21), opener=lambda req, timeout=0: Resp())
        self.assertEqual(rows, [(D(2025, 10, 21), 10.0, 11.0)])


if __name__ == "__main__":
    unittest.main()
