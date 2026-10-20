"""Executor for one arm on Bitvavo. Dry run only for now (D13: no real money before
a locked PASS; live plan /mnt/project-files/research/live-plan/LIVE-PLAN.md).

One `step()` per run (a systemd timer or TrueNAS cron calls it hourly):
  1. kill-switch checks (STOP file, halted state, error streak, order count)
  2. signal from Bitvavo daily candles, same rule code as the paper sim
  3. compare with the Pi's paper arm when its status.json is available
  4. plan a post-only limit order at the touch, check price and size limits
  5. dry run: journal the plan and assume a conservative fill (other side of the
     book, taker fee), so the shadow account can be compared with the paper arm

Everything is appended to live-journal.jsonl; state is rebuilt from it on start.
"""

import json
import math
import os
import time
import uuid

from . import strategies
from .config import fingerprint
from .journal import Journal, write_atomic

MIN_ORDER_EUR = 5.0
# rules whose target is 0 or 1; vol_target (fractional) needs rebalancing logic first
BINARY = ("faber", "tsmom", "ema_cross", "crash_exit", "donchian", "momentum")
DAY = 86400

REQUIRED = ("run_name", "mode", "market", "strategy", "cap_eur", "taker_fee",
            "maker_fee", "operator_id", "kill")


class LiveConfigError(ValueError):
    pass


def load_config(path):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    validate(cfg)
    return cfg


def validate(cfg):
    for key in REQUIRED:
        if key not in cfg:
            raise LiveConfigError("missing live config key: %s" % key)
    if cfg["mode"] != "dry":
        raise LiveConfigError("only mode 'dry' is allowed: D13 says no real money "
                              "before a locked PASS")
    if cfg["market"] not in cfg["kill"].get("allowed_markets", []):
        raise LiveConfigError("market %s is not in kill.allowed_markets" % cfg["market"])
    if cfg["strategy"].get("type") not in BINARY:
        raise LiveConfigError("only all-in/all-out rules are supported, not %r"
                              % cfg["strategy"].get("type"))
    if not 0 < cfg["cap_eur"] <= cfg["kill"]["max_cap_eur"]:
        raise LiveConfigError("cap_eur must be above 0 and at most kill.max_cap_eur")


class Executor:
    def __init__(self, cfg, data_dir, market, clock=time.time):
        self.cfg = cfg
        self.data_dir = data_dir
        self.market = market
        self.clock = clock
        self.kill = cfg["kill"]
        self.hash = fingerprint(cfg)
        os.makedirs(data_dir, exist_ok=True)
        self.journal = Journal(os.path.join(data_dir, "live-journal.jsonl"))
        self.stop_path = os.path.join(data_dir, "STOP")
        self._replay()

    # ---- state ---------------------------------------------------------------

    def _replay(self):
        self.eur = self.qty = 0.0
        self.start_eur = None
        self.halted = None
        self.orders = []          # times of planned orders
        self.errors = 0
        self.disagree_since = None
        self.last_target = None
        events = self.journal.read()
        if not events:
            self._record({"e": "start", "t": self.clock(), "hash": self.hash,
                          "mode": self.cfg["mode"], "eur": self.cfg["cap_eur"]})
            return
        if events[0]["hash"] != self.hash:
            raise LiveConfigError("live config changed since this run started; "
                                  "start a new data dir")
        for ev in events:
            self._apply(ev)

    def _record(self, ev):
        self.journal.append(ev)
        self._apply(ev)

    def _apply(self, ev):
        e = ev["e"]
        if e == "start":
            self.eur = self.start_eur = ev["eur"]
        elif e == "fill":
            if ev["side"] == "buy":
                self.eur -= ev["eur"] + ev["fee_eur"]
                self.qty += ev["qty"]
            else:
                self.qty -= ev["qty"]
                self.eur += ev["eur"] - ev["fee_eur"]
        elif e == "order":
            self.orders.append(ev["t"])
        elif e == "halt":
            self.halted = ev["why"]
        elif e == "resume":
            self.halted = None
            self.errors = 0
        elif e == "error":
            self.errors += 1
        elif e == "ok":
            self.errors = 0
        elif e == "target":
            self.last_target = ev["want"]
        elif e == "disagree":
            self.disagree_since = ev.get("since")

    def resume(self, who):
        self._record({"e": "resume", "t": self.clock(), "who": who})

    # ---- one run -------------------------------------------------------------

    def step(self, paper=None):
        """paper: the Pi's arm row from status.json ({'position': 'long'|'cash', ...})
        or None when it is not available."""
        now = self.clock()
        if os.path.exists(self.stop_path) and not self.halted:
            self._record({"e": "halt", "t": now, "why": "STOP file"})
        if self.halted:
            return self._status(now, None, "halted: %s" % self.halted)

        try:
            candles = self.market.candles(self.cfg["market"], "1d", now)
            bid, ask = self.market.book(self.cfg["market"])
        except Exception as e:  # network or exchange error; never trade on it
            self._record({"e": "error", "t": now, "msg": str(e)[:300]})
            if self.errors >= self.kill["max_consecutive_errors"]:
                self._record({"e": "halt", "t": now,
                              "why": "%d errors in a row" % self.errors})
            return self._status(now, None, "error: %s" % e)
        self._record({"e": "ok", "t": now})

        if not candles or now - candles[-1]["t"] > self.kill["max_candle_age_s"]:
            return self._status(now, (bid, ask), "stale candles: no orders")

        value = self.eur + self.qty * bid
        if value <= self.start_eur * (1 - self.kill["max_loss_frac"]):
            if self.qty > 0:
                self._plan(now, "sell", self.qty, bid, ask, "loss limit")
            self._record({"e": "halt", "t": now, "why": "loss limit %.0f%%"
                          % (self.kill["max_loss_frac"] * 100)})
            return self._status(now, (bid, ask), "halted: loss limit")

        want = strategies.target(self.cfg["strategy"], candles)
        if want is None:
            return self._status(now, (bid, ask), "not enough history")
        if want != self.last_target:
            self._record({"e": "target", "t": now, "want": want})

        msg = self._check_paper(now, want, paper)
        if self.halted:
            return self._status(now, (bid, ask), msg)

        holding = self.qty * bid / value if value > 0 else 0.0
        if want >= 0.5 and holding < 0.5 and self.eur >= MIN_ORDER_EUR:
            qty = self.eur / (ask * (1 + self.cfg["taker_fee"]))
            self._plan(now, "buy", qty, bid, ask, "target %.0f%%" % (want * 100))
        elif want < 0.5 and self.qty * bid >= MIN_ORDER_EUR:
            self._plan(now, "sell", self.qty, bid, ask, "target %.0f%%" % (want * 100))
        return self._status(now, (bid, ask), msg or "ok")

    def _check_paper(self, now, want, paper):
        if paper is None:
            return "paper arm not available"
        paper_long = paper.get("position") == "long" or paper.get("pending") == "buy"
        if paper.get("pending") == "sell":
            paper_long = False
        if paper_long == (want >= 0.5):
            if self.disagree_since is not None:
                self._record({"e": "disagree", "t": now, "since": None})
            return None
        if self.disagree_since is None:
            self._record({"e": "disagree", "t": now, "since": now})
        elif now - self.disagree_since > self.kill["max_disagree_s"]:
            self._record({"e": "halt", "t": now, "why": "disagrees with paper arm"})
        return "disagrees with paper arm since %s" % iso(self.disagree_since)

    def _plan(self, now, side, qty, bid, ask, reason):
        """Plan a post-only limit at our side of the book; refuse anything outside the
        limits. Dry run: assume it fills at the other side with the taker fee."""
        today = [t for t in self.orders if t > now - DAY]
        if len(today) >= self.kill["max_orders_per_day"]:
            self._record({"e": "halt", "t": now, "why": "too many orders in 24 h"})
            return
        price = round_price(bid if side == "buy" else ask, side)
        mid = (bid + ask) / 2
        if abs(price / mid - 1) > self.kill["max_price_dev"]:
            self._record({"e": "refused", "t": now, "why": "price %.2f too far from mid %.2f"
                          % (price, mid)})
            return
        notional = qty * price
        if notional > self.cfg["cap_eur"] * (1 + self.kill["max_price_dev"]) \
                and side == "buy":
            self._record({"e": "refused", "t": now, "why": "order %.2f EUR above cap"
                          % notional})
            return
        cid = str(uuid.uuid4())
        self._record({"e": "order", "t": now, "side": side, "qty": round(qty, 8),
                      "price": price, "post_only": True, "client_order_id": cid,
                      "reason": reason, "mode": self.cfg["mode"]})
        fill_price = ask if side == "buy" else bid
        eur = qty * fill_price
        self._record({"e": "fill", "t": now, "side": side, "qty": qty, "price": fill_price,
                      "eur": eur, "fee_eur": eur * self.cfg["taker_fee"],
                      "client_order_id": cid, "assumed": True})

    def _status(self, now, book, msg):
        st = {"heartbeat_utc": iso(now), "heartbeat": now, "run": self.cfg["run_name"],
              "mode": self.cfg["mode"], "config_hash": self.hash, "market": self.cfg["market"],
              "halted": self.halted, "message": msg, "eur": round(self.eur, 2),
              "qty": round(self.qty, 8), "target": self.last_target,
              "orders_total": len(self.orders), "consecutive_errors": self.errors}
        if book:
            st["bid"], st["ask"] = book
            st["equity_eur"] = round(self.eur + self.qty * book[0], 2)
            st["return_pct"] = round((st["equity_eur"] / self.start_eur - 1) * 100, 2)
        write_atomic(os.path.join(self.data_dir, "live-status.json"),
                     json.dumps(st, indent=1, sort_keys=True))
        return st


def round_price(p, side):
    """Bitvavo allows at most 5 significant digits on prices. Round a buy down and a
    sell up, so a post-only order never crosses the book."""
    digits = 5 - int(math.floor(math.log10(abs(p)))) - 1
    f = 10 ** digits
    return (math.floor(p * f) if side == "buy" else math.ceil(p * f)) / f


def paper_arm(path, arm_id):
    """The arm row from the Pi's status.json, or None if missing or unreadable."""
    try:
        with open(path, encoding="utf-8") as f:
            st = json.load(f)
    except (OSError, ValueError):
        return None
    for row in st.get("strategies", []):
        if row.get("id") == arm_id:
            return row
    return None


def iso(t):
    if t is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
