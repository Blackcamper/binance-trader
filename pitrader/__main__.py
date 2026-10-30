"""Command line.

  python3 -m pitrader check            one-off test that Kraken answers from this machine
  python3 -m pitrader run              poll forever (what systemd runs)
  python3 -m pitrader once             a single poll, then exit
  python3 -m pitrader status           print the latest summary
  python3 -m pitrader llm-summary      daily status text from the NAS model (own timer)
  python3 -m pitrader backtest         historical backtest on Bitstamp BTC/EUR
  python3 -m pitrader stocks           one pass of the US stocks paper run (hourly timer);
                                       also the stocks backtest when it is a week old
  python3 -m pitrader stocks-backtest  historical backtest of the stock arms now
"""

import argparse
import os
import sys
import time

from . import backtest, config, health, llm, stocks
from .kraken import Kraken, MarketError
from .sim import ConfigChanged, Simulator

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG = os.path.join(HERE, "config", "sim-v2.json")
DEFAULT_DATA = os.path.join(HERE, "data", "sim-v2")
STOCKS_CONFIG = os.path.join(HERE, "config", "stocks-v1.json")
STOCKS_DATA = os.path.join(HERE, "data", "stocks-v1")
STOCKS_CACHE = os.path.join(HERE, "data", "stockhist")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pitrader")
    ap.add_argument("command", choices=["check", "run", "once", "status", "llm-summary", "backtest",
                                        "stocks", "stocks-backtest"])
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--data-dir", default=DEFAULT_DATA)
    ap.add_argument("--stocks-config", default=STOCKS_CONFIG)
    ap.add_argument("--stocks-data", default=STOCKS_DATA)
    ap.add_argument("--llm-config", default=os.path.join(HERE, "config", "llm.json"))
    ap.add_argument("--runs", type=int, default=backtest.RANDOM_RUNS,
                    help="random strategies per arm in the backtest")
    args = ap.parse_args(argv)

    if args.command == "status":
        path = os.path.join(args.data_dir, "summary.txt")
        if not os.path.exists(path):
            print("no status yet in %s" % args.data_dir)
            return 1
        with open(path, encoding="utf-8") as f:
            sys.stdout.write(f.read())
        return 0

    if args.command == "llm-summary":
        out = llm.daily_summary(args.data_dir, llm.load_settings(args.llm_config))
        print(out["text"] if out["llm_ok"] else "model did not answer; facts written without text")
        return 0

    if args.command in ("stocks", "stocks-backtest"):
        return run_stocks(args)

    cfg = config.load(args.config)
    if args.command == "backtest":
        _, report = backtest.run(cfg, os.path.join(HERE, "data", "hist"),
                                 os.path.join(args.data_dir, "backtest"), runs=args.runs)
        sys.stdout.write(report)
        return 0

    market = Kraken(request_gap=cfg.get("request_gap_seconds", 1.2))

    if args.command == "check":
        return check(cfg, market)

    try:
        sim = Simulator(cfg, args.data_dir, market, health=health.check)
    except ConfigChanged as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 2

    if args.command == "once":
        ok = sim.poll()
        with open(os.path.join(args.data_dir, "summary.txt"), encoding="utf-8") as f:
            sys.stdout.write(f.read())
        return 0 if ok else 1

    period = cfg["poll_seconds"]
    while True:
        ok = sim.poll()
        fails = sim.runtime["consecutive_failures"]
        # back off when the exchange keeps failing, up to 4 poll periods
        wait = period if ok else period * min(2 ** (fails - 1), 4)
        # align to the period boundary so polls land just after candle closes
        now = time.time()
        time.sleep(wait - (now % period) + 5 if ok else wait)


def run_stocks(args):
    cfg = stocks.load_config(args.stocks_config)
    out = os.path.join(args.stocks_data, "backtest")
    if args.command == "stocks":
        try:
            st = stocks.live(cfg, args.stocks_data, STOCKS_CACHE)
        except stocks.ConfigChanged as e:
            print("REFUSED: %s" % e, file=sys.stderr)
            return 2
        sys.stdout.write(stocks.summary_text(st))
        if not stocks.backtest_due(out, cfg.get("backtest_every_days", 7)):
            return 0
    _, report = stocks.run_backtest(cfg, STOCKS_CACHE, out, runs=args.runs)
    if args.command == "stocks-backtest":
        sys.stdout.write(report)
    return 0


def check(cfg, market):
    status = 0
    print("health:", health.check())
    try:
        found = market.asset_pairs(config.pairs(cfg))
        for key, info in sorted(found.items()):
            print("pair %s altname=%s ordermin=%s" % (key, info.get("altname"), info.get("ordermin")))
    except MarketError as e:
        print("FAIL AssetPairs:", e)
        status = 1
    for pair in config.pairs(cfg):
        try:
            bid, ask, last = market.ticker(pair)
            print("ticker %s bid=%.2f ask=%.2f spread=%.3f%%" % (pair, bid, ask, (ask - bid) / bid * 100))
            candles = market.ohlc(pair, 240, time.time())
            print("ohlc %s 4h: %d closed candles, last open %s UTC" % (
                pair, len(candles), time.strftime("%Y-%m-%d %H:%M", time.gmtime(candles[-1]["t"]))))
        except (MarketError, IndexError) as e:
            print("FAIL %s: %s" % (pair, e))
            status = 1
    print("OK" if status == 0 else "FAIL")
    return status


if __name__ == "__main__":
    sys.exit(main())
