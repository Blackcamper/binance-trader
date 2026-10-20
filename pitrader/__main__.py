"""Command line.

  python3 -m pitrader check            one-off test that Kraken answers from this machine
  python3 -m pitrader run              poll forever (what systemd runs)
  python3 -m pitrader once             a single poll, then exit
  python3 -m pitrader status           print the latest summary
  python3 -m pitrader llm-summary      daily status text from the NAS model (own timer)
  python3 -m pitrader backtest         historical backtest on Bitstamp BTC/EUR
  python3 -m pitrader live-dry         one dry-run step of the Bitvavo executor (no orders sent)
  python3 -m pitrader live-resume      clear a kill-switch halt after a human has looked
"""

import argparse
import os
import sys
import time

from . import backtest, config, health, live, llm
from .bitvavo import Bitvavo
from .kraken import Kraken, MarketError
from .sim import ConfigChanged, Simulator

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG = os.path.join(HERE, "config", "sim-v2.json")
DEFAULT_DATA = os.path.join(HERE, "data", "sim-v2")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pitrader")
    ap.add_argument("command", choices=["check", "run", "once", "status", "llm-summary", "backtest",
                                       "live-dry", "live-resume"])
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--data-dir", default=DEFAULT_DATA)
    ap.add_argument("--llm-config", default=os.path.join(HERE, "config", "llm.json"))
    ap.add_argument("--runs", type=int, default=backtest.RANDOM_RUNS,
                    help="random strategies per arm in the backtest")
    ap.add_argument("--live-config", default=os.path.join(HERE, "config", "live-dry-v1.json"))
    ap.add_argument("--live-data-dir", default=os.path.join(HERE, "data", "live-dry-v1"))
    ap.add_argument("--paper-status", default=os.path.join(DEFAULT_DATA, "status.json"),
                    help="the Pi's status.json, to compare signals with the paper arm")
    args = ap.parse_args(argv)

    if args.command in ("live-dry", "live-resume"):
        return run_live(args)

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


def run_live(args):
    try:
        cfg = live.load_config(args.live_config)
        ex = live.Executor(cfg, args.live_data_dir, Bitvavo())
    except live.LiveConfigError as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 2
    if args.command == "live-resume":
        if os.path.exists(ex.stop_path):
            print("REFUSED: remove %s first" % ex.stop_path, file=sys.stderr)
            return 2
        ex.resume("cli")
        print("resumed")
        return 0
    st = ex.step(live.paper_arm(args.paper_status, cfg.get("paper_arm")))
    print("%s %s target=%s eur=%.2f qty=%.8f halted=%s" % (
        st["heartbeat_utc"], st["message"], st["target"], st["eur"], st["qty"], st["halted"]))
    return 1 if st["halted"] else 0


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
