"""Command line.

  python3 -m pitrader check            one-off test that Kraken answers from this machine
  python3 -m pitrader run              poll forever (what systemd runs)
  python3 -m pitrader once             a single poll, then exit
  python3 -m pitrader status           print the latest summary
  python3 -m pitrader skat [--year Y]  what the paper trades would mean for the tax return
"""

import argparse
import os
import sys
import time

from . import config, health, tax
from .kraken import Kraken, MarketError
from .sim import ConfigChanged, Simulator

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG = os.path.join(HERE, "config", "sim-v1.json")
DEFAULT_DATA = os.path.join(HERE, "data", "sim-v1")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pitrader")
    ap.add_argument("command", choices=["check", "run", "once", "status", "skat"])
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--data-dir", default=DEFAULT_DATA)
    ap.add_argument("--year", type=int, help="skat: income year (default this year)")
    ap.add_argument("--strategy", help="skat: one strategy id (default all)")
    ap.add_argument("--csv", help="skat: also write every sale to this CSV file")
    args = ap.parse_args(argv)

    if args.command == "status":
        path = os.path.join(args.data_dir, "summary.txt")
        if not os.path.exists(path):
            print("no status yet in %s" % args.data_dir)
            return 1
        with open(path, encoding="utf-8") as f:
            sys.stdout.write(f.read())
        return 0

    cfg = config.load(args.config)
    if args.command == "skat":
        return skat(cfg, args)
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


def skat(cfg, args):
    if not os.path.exists(os.path.join(args.data_dir, "journal.jsonl")):
        print("no journal in %s" % args.data_dir)
        return 1
    try:
        sim = Simulator(cfg, args.data_dir, market=None)
    except ConfigChanged as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 2
    year = args.year or time.gmtime().tm_year
    ids = [args.strategy] if args.strategy else list(sim.strats)
    unknown = [i for i in ids if i not in sim.strats]
    if unknown:
        print("unknown strategy: %s" % ", ".join(unknown), file=sys.stderr)
        return 2
    reports = [tax.year_report(sim.books[i], sim.strats[i], cfg, year) for i in ids]
    sys.stdout.write("\n".join(tax.render(r, cfg) for r in reports))
    if args.csv:
        tax.write_csv(reports, args.csv)
        print("CSV: %s" % args.csv)
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
