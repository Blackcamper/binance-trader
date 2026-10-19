"""The simulation engine: one poll every few minutes, decisions on closed candles,
fills one poll later at the depth-walked bid/ask plus fee and extra slippage."""

import json
import os
import time

from . import __version__, config, strategies
from .journal import Journal, append_line, write_atomic
from .kraken import MarketError
from .ledger import Book, walk_buy, walk_sell

WEEK = 7 * 86400
MIN_ORDER_EUR = 1.0


class ConfigChanged(RuntimeError):
    pass


class Simulator:
    def __init__(self, cfg, data_dir, market, clock=time.time, health=None):
        self.cfg = cfg
        self.data_dir = data_dir
        self.market = market
        self.clock = clock
        self.health = health or (lambda: {"ntp_synced": None, "throttled": None})
        self.hash = config.fingerprint(cfg)
        self.fee = cfg["taker_fee"]
        self.slip = cfg["extra_slippage_bps"] / 10000.0
        self.capital_eur = cfg["capital_dkk"] / cfg["eur_dkk"]
        self.strats = {s["id"]: s for s in cfg["strategies"]}
        os.makedirs(data_dir, exist_ok=True)
        self.journal = Journal(os.path.join(data_dir, "journal.jsonl"))
        self.runtime_path = os.path.join(data_dir, "runtime.json")
        self._reset_state()
        self._load()

    # ---- state -------------------------------------------------------------

    def _reset_state(self):
        self.start_t = None
        self.books = {sid: Book(self.capital_eur) for sid in self.strats}
        self.pending = {}
        self.orders = {sid: [] for sid in self.strats}   # order times, for DCA / B&H
        self.trades = {sid: [] for sid in self.strats}   # fills, for the status file
        self.candles = {}                                # (pair, interval) -> closed candles

    def _load(self):
        events = self.journal.read()
        if not events:
            self._record({"e": "start", "t": int(self.clock()), "hash": self.hash,
                          "run": self.cfg["run_name"], "version": __version__})
        elif events[0].get("hash") != self.hash:
            raise ConfigChanged(
                "config hash %s differs from this run's %s; the config is locked for a run. "
                "Use a new --data-dir to start a new run." % (self.hash, events[0].get("hash")))
        else:
            for ev in events:
                self._apply(ev)
        self.runtime = self._read_runtime()

    def _read_runtime(self):
        try:
            with open(self.runtime_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"polls_ok": 0, "polls_failed": 0, "consecutive_failures": 0,
                    "last_ok_poll": None, "peak": {}, "max_dd": {}, "errors": []}

    def _record(self, ev):
        self.journal.append(ev)
        self._apply(ev)

    def _apply(self, ev):
        kind = ev["e"]
        if kind == "start":
            self.start_t = ev["t"]
        elif kind == "order":
            self.pending[ev["sid"]] = ev
            self.orders[ev["sid"]].append(ev["t"])
        elif kind == "fill":
            book = self.books[ev["sid"]]
            if ev["side"] == "buy":
                book.buy(ev["qty"], ev["gross"], ev["fee"])
            else:
                book.sell(ev["qty"], ev["gross"], ev["fee"], ev["t"])
            self.pending.pop(ev["sid"], None)
            self.trades[ev["sid"]].append(ev)
        elif kind == "cancel":
            self.pending.pop(ev["sid"], None)
        elif kind == "skip":
            self.orders[ev["sid"]].append(ev["t"])

    # ---- one poll ----------------------------------------------------------

    def poll(self):
        now = int(self.clock())
        health = self.health()
        trading_ok = self._clock_ok(health, now)
        try:
            prices = {p: self.market.ticker(p) for p in config.pairs(self.cfg)}
            if trading_ok:
                self._fill_pending(now)
                self._decide(now)
        except MarketError as e:
            self.runtime["polls_failed"] += 1
            self.runtime["consecutive_failures"] += 1
            self._error(now, str(e))
            self._write_status(now, health, None, trading_ok)
            return False
        self.runtime["polls_ok"] += 1
        self.runtime["consecutive_failures"] = 0
        self.runtime["last_ok_poll"] = now
        self._write_status(now, health, prices, trading_ok)
        return True

    def _clock_ok(self, health, now):
        if health.get("ntp_synced") is False and self.cfg.get("require_ntp", True):
            return False
        return time.gmtime(now).tm_year >= 2026

    def _error(self, now, msg):
        errs = self.runtime.setdefault("errors", [])
        errs.append({"t": now, "msg": msg[:300]})
        del errs[:-10]

    def _fill_pending(self, now):
        for sid, order in sorted(self.pending.items()):
            if order["t"] >= now:
                continue                      # never fill on the poll that decided
            book = self.books[sid]
            pair = self.strats[sid]["pair"]
            if order["side"] == "buy":
                budget = min(order["budget_eur"], book.cash)
                if budget < MIN_ORDER_EUR:
                    self._record({"e": "cancel", "t": now, "sid": sid, "why": "no cash"})
                    continue
                _, asks = self.market.depth(pair, self.cfg["depth_count"])
                qty, gross, fee, price, thin = walk_buy(asks, budget, self.fee, self.slip)
            else:
                if book.qty <= 0:
                    self._record({"e": "cancel", "t": now, "sid": sid, "why": "nothing held"})
                    continue
                bids, _ = self.market.depth(pair, self.cfg["depth_count"])
                sell_qty = book.qty * min(1.0, order.get("frac", 1.0))
                qty, gross, fee, price, thin = walk_sell(bids, sell_qty, self.fee, self.slip)
            self._record({"e": "fill", "t": now, "sid": sid, "side": order["side"],
                          "qty": qty, "gross": gross, "fee": fee, "price": price,
                          "thin_book": thin})

    def _closed(self, pair, interval, now):
        key = (pair, interval)
        known = self.candles.get(key)
        # the next candle closes at last_open + 2 intervals; fetch only once it can exist
        if not known or now >= known[-1]["t"] + 2 * interval * 60:
            self.candles[key] = self.market.ohlc(pair, interval, now)
        return self.candles[key]

    def _decide(self, now):
        for sid, s in self.strats.items():
            if sid in self.pending:
                continue
            book = self.books[sid]
            kind = s["type"]
            if kind == "buy_and_hold":
                if not self.orders[sid]:
                    self._order(now, sid, "buy", book.cash, "initial buy")
            elif kind == "dca":
                n = len(self.orders[sid])
                if n < s["weeks"] and (n == 0 or now - self.orders[sid][-1] >= WEEK):
                    self._order(now, sid, "buy", self.capital_eur / s["weeks"],
                                "DCA buy %d/%d" % (n + 1, s["weeks"]))
            elif kind == "dip_dca":
                n = len(self.orders[sid])
                if book.cash < MIN_ORDER_EUR or (n and now - self.orders[sid][-1] < WEEK):
                    continue
                candles = self._closed(s["pair"], 1440, now)
                mult = strategies.dip_multiplier(candles, s.get("sma_days", 200),
                                                 s.get("deep", 0.20))
                if mult is None:
                    continue
                if mult == 0:
                    # skipped weeks still count as a week, so the cadence stays weekly
                    self._record({"e": "skip", "t": now, "sid": sid, "why": "above 200d avg"})
                    continue
                self._order(now, sid, "buy", self.capital_eur / s["weeks"] * mult,
                            "dip DCA %dx" % mult, candles[-1]["t"])
            else:
                candles = self._closed(s["pair"], s["interval"], now)
                want = strategies.target(s, candles)
                if want is None:
                    continue
                self._rebalance(now, sid, s, book, candles, want)

    def _rebalance(self, now, sid, s, book, candles, want):
        """Move the holding toward `want` (share of equity in the coin). The current
        share is valued at the decision candle's close, which for monthly rules is the
        month-end close, so price drift inside the month never triggers a trade."""
        ref = candles[-1]
        if s["type"] in strategies.MONTHLY:
            ref = strategies.through_month_end(candles)[-1]
        step = rebalance_step(want, book.cash, book.qty, ref["c"], s.get("band", 0.5))
        if step is None:
            return
        side, amount = step
        reason = "target %.0f%%" % (want * 100)
        if side == "buy":
            self._order(now, sid, "buy", amount, reason, ref["t"])
        else:
            self._order(now, sid, "sell", None, reason, ref["t"], frac=amount)

    def _order(self, now, sid, side, budget_eur, reason, candle=None, frac=None):
        ev = {"e": "order", "t": now, "sid": sid, "side": side, "reason": reason}
        if budget_eur is not None:
            ev["budget_eur"] = budget_eur
        if frac is not None and frac < 1.0:
            ev["frac"] = frac
        if candle is not None:
            ev["candle"] = candle
        self._record(ev)

    # ---- reporting ---------------------------------------------------------

    def snapshot(self, now, prices):
        eur_dkk = self.cfg["eur_dkk"]
        cap = self.cfg["capital_dkk"]
        days = (now - self.start_t) / 86400.0
        rows = []
        for sid, s in self.strats.items():
            book = self.books[sid]
            bid = prices[s["pair"]][0]
            value = book.value(bid) * eur_dkk
            peak = max(self.runtime["peak"].get(sid, cap), value)
            self.runtime["peak"][sid] = peak
            dd = 1 - value / peak
            max_dd = max(self.runtime["max_dd"].get(sid, 0.0), dd)
            self.runtime["max_dd"][sid] = max_dd
            after = {name: round(book.after_tax_value(bid, self.fee, sc, now) * eur_dkk, 2)
                     for name, sc in self.cfg["tax_scenarios"].items()}
            rows.append({
                "id": sid, "type": s["type"], "pair": s["pair"],
                "position": "long" if book.qty > 0 else "cash",
                "qty": round(book.qty, 8),
                "cash_dkk": round(book.cash * eur_dkk, 2),
                "equity_dkk": round(value, 2),
                "return_pct": round((value / cap - 1) * 100, 2),
                "after_tax_liquidation_dkk": after,
                "fees_dkk": round(book.fees * eur_dkk, 2),
                "buys": book.buys, "sells": book.sells,
                "max_drawdown_pct": round(max_dd * 100, 2),
                "pending": self.pending[sid]["side"] if sid in self.pending else None,
            })
        debt = self.cfg["debt_baseline"]
        rate = debt["apr"] * (1 - debt["interest_deduction_rate"])
        return rows, round(cap * (1 + rate) ** (days / 365.0), 2), days

    def _write_status(self, now, health, prices, trading_ok):
        rt = self.runtime
        days = (now - self.start_t) / 86400.0
        expected = max(1, int((now - self.start_t) / self.cfg["poll_seconds"]) + 1)
        status = {
            "heartbeat_utc": iso(now), "heartbeat": now,
            "run": self.cfg["run_name"], "config_hash": self.hash, "version": __version__,
            "started_utc": iso(self.start_t), "day": int(days) + 1,
            "phase": phase(days),
            "verdict": "NONE: this live simulation never prints PASS. PASS needs the locked "
                       "rules on a 2+ year backtest (D21, D22). Live sim can only reject.",
            "health": {
                "trading_enabled": trading_ok, "ntp_synced": health.get("ntp_synced"),
                "throttled": health.get("throttled"),
                "polls_ok": rt["polls_ok"], "polls_failed": rt["polls_failed"],
                "consecutive_failures": rt["consecutive_failures"],
                "missed_poll_pct": round(max(0.0, 1 - rt["polls_ok"] / expected) * 100, 2),
                "last_ok_poll_utc": iso(rt["last_ok_poll"]),
                "recent_errors": rt.get("errors", []),
            },
            "assumptions": {
                "capital_dkk": self.cfg["capital_dkk"], "eur_dkk": self.cfg["eur_dkk"],
                "taker_fee": self.fee, "extra_slippage_bps": self.cfg["extra_slippage_bps"],
                "tax_scenarios": self.cfg["tax_scenarios"],
                "debt_apr": self.cfg["debt_baseline"]["apr"],
            },
        }
        if prices is not None:
            rows, debt, _ = self.snapshot(now, prices)
            status["prices_eur"] = {p: {"bid": b, "ask": a} for p, (b, a, _l) in prices.items()}
            status["strategies"] = rows
            status["baseline_debt_paydown_dkk"] = debt
            self._append_equity(now, rows)
        else:
            status["stale"] = True
        write_atomic(os.path.join(self.data_dir, "status.json"),
                     json.dumps(status, indent=1, sort_keys=True))
        write_atomic(os.path.join(self.data_dir, "summary.txt"), summary_text(status))
        write_atomic(self.runtime_path, json.dumps(rt, sort_keys=True))

    def _append_equity(self, now, rows):
        path = os.path.join(self.data_dir, "equity.csv")
        if not os.path.exists(path):
            append_line(path, "utc," + ",".join(r["id"] for r in rows) + "\n")
        append_line(path, iso(now) + "," + ",".join("%.2f" % r["equity_dkk"] for r in rows) + "\n")


def rebalance_step(want, cash, qty, price, band):
    """What to do to move from the current share in the coin toward `want`.
    Returns ("buy", budget_eur), ("sell", fraction_of_holding) or None. Binary rules
    use band 0.5, so they only trade on a real flip; vol_target uses its 10-pt band."""
    equity = cash + qty * price
    held = qty * price / equity if equity > 0 else 0.0
    if abs(want - held) < band:
        return None
    if want > held:
        budget = cash if want >= 0.999 else min(cash, (want - held) * equity)
        return ("buy", budget) if budget >= MIN_ORDER_EUR else None
    if qty <= 0:
        return None
    return ("sell", 1.0 if want <= 0.001 else (held - want) / held)


def iso(ts):
    if ts is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def phase(days):
    if days < 14:
        return "system check (day 1-14): wiring and bugs only, results mean nothing yet"
    return "live sim: can reject a strategy, cannot confirm one"


def summary_text(st):
    lines = [
        "pitrader %s  run %s  config %s" % (st["version"], st["run"], st["config_hash"]),
        "Heartbeat: %s   Day %d   %s" % (st["heartbeat_utc"], st["day"], st["phase"]),
        "Verdict: %s" % st["verdict"],
    ]
    h = st["health"]
    lines.append("Health: trading %s, NTP %s, throttled %s, polls ok %d / failed %d, "
                 "missed %.2f%%" % ("ON" if h["trading_enabled"] else "OFF (clock not synced)",
                                    h["ntp_synced"], h["throttled"], h["polls_ok"],
                                    h["polls_failed"], h["missed_poll_pct"]))
    if st.get("stale"):
        lines.append("WARN: market data unavailable on this poll; last error: %s"
                     % (h["recent_errors"][-1]["msg"] if h["recent_errors"] else "?"))
    else:
        lines.append("")
        lines.append("%-14s %-8s %-5s %11s %8s %13s %13s %8s %6s %7s" % (
            "strategy", "pair", "pos", "equity DKK", "return", "after tax hi",
            "after tax lo", "fees", "trades", "max DD"))
        for r in st["strategies"]:
            at = r["after_tax_liquidation_dkk"]
            lines.append("%-14s %-8s %-5s %11.2f %7.2f%% %13.2f %13.2f %8.2f %6d %6.2f%%" % (
                r["id"], r["pair"], r["position"], r["equity_dkk"], r["return_pct"],
                at.get("high", 0.0), at.get("low", 0.0), r["fees_dkk"],
                r["buys"] + r["sells"], r["max_drawdown_pct"]))
        lines.append("Baseline, pay down %.2f%% debt instead: %.2f DKK"
                     % (st["assumptions"]["debt_apr"] * 100, st["baseline_debt_paydown_dkk"]))
    return "\n".join(lines) + "\n"
