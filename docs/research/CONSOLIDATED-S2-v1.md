# S2 consolidated — crypto paper-trading sim on Pi Zero W (12 Haiku agents), 2026-10-18
Full outputs: S2-lens01..10-*.md, S2-r1-tax-exchanges.md, S2-r2-evidence.md. GROUND-TRUTH.md v7 is binding (D13–D23 for this stream).

## A. Convergence
1. **Custom lightweight Python, not Freqtrade** (lens 10, 5; D20 Pi Zero W ARMv6/512 MB). Stdlib (or pure-Python) only on the Pi. Compute on closed candles only (lens 1).
2. **Public data, no API keys on the Pi** (lens 4, 9, 5). Feed: **Kraken public OHLC/Ticker/Depth primary** (4h + 1d, 720-candle cap per call), Bitvavo alternative, Coinbase fallback (no 4h). **Binance excluded for live**: withdrew MiCA bid 24 Jun 2026, EU limits from 1 Jul 2026, not on Danish MiCA list (r1, lens 1, 3, 7) — public historical data may still be used for backtests.
3. **Strategies (textbook defaults, no optimisation)** (lens 1): controls = buy-and-hold (lump sum) + weekly DCA (with its own DCA-B&H baseline, lens 2); S1 daily EMA 50/200 crossover BTC-EUR; S2 4h Donchian 20/10 breakout BTC-EUR; S3 90-day time-series momentum; S4 = S2 on ETH-EUR. Optional cheap arms: 50/50 BTC/ETH rebalance (lens 6). Extra baseline: "pay down debt" at ~5.76% ÅOP (lens 6; Nationalbanken avg new consumer credit May 2026).
4. **Realistic fills**: decide on candle close N, fill at next tick's depth-walked bid/ask, not last/mid; taker fee 0.8% assumed (conservative; Kraken 0.40/0.80 vs 0.25/0.40 conflict); add latency; limit orders only on trade-through (lens 5, 9, 10).
5. **Danish tax shadow ledger** (r1, lens 6, 7): gains = personal income up to ~53% (no AM-bidrag); losses = ligningsmæssigt fradrag worth ~26%; every sale/swap is a realisation; FIFO default (aktiv-for-aktiv ambiguity). Model per-trade tax; give buy-and-hold notional tax at period end for fairness. Make rates config values; scenarios 26%/53%. Needs SKAT/accountant confirmation before any live decision.
6. **Honesty rules** (lens 2, r2): 14 days = wiring/bug check only, NEVER prints PASS. 90-day live run is a REJECTION gate only. PASS needs ≥2 years out-of-sample historical backtest incl. a ≥30% market fall, ≥100 closed trades, beats B&H AND debt-paydown after fees+tax, max drawdown ≤ B&H, top 1% vs 1,000 random-entry strategies, data gaps <1%; with 5 strategies use p<0.01 (Bonferroni). States: PASS / FAIL / INCONCLUSIVE. Rules locked + versioned before start (D22).
7. **Robustness on the Pi** (lens 9, 4, 8): append-only journal, fsync, replay on boot, REST backfill of gaps; systemd restart; NTP required (Pi Zero has no RTC — gate trading until time synced); staleness watchdog per pair; rate-limit backoff (Binance bans escalate; Kraken counter); log undervoltage (vcgencmd get_throttled); SSH keys only, UFW deny inbound, no port forwarding; heartbeat so "Pi silent since X" can be reported (D23).
8. **Heavy work off the Pi**: multi-year backtests + random-entry bootstrap run elsewhere (lens 3, 10).

## B. Reporting channel (D23) — open technical choice
- Claude's pCloud connector can list/info/upload/public-link but has **no read/download tool** (orchestrator check of tool list) → reading a JSON needs a public link + WebFetch (exposes data) → weak.
- Gmail connector CAN read messages → Pi emails a daily plain-text+JSON summary (SMTP app password on Pi).
- GitHub: Claude's workspace reaches GitHub (git/gh); Pi could push a status JSON to a private repo; same repo deploys code via `git pull --ff-only` (lens 10). Unknown whether Jakob has a GitHub account.
- Claude's cloud workspace cannot reach exchange APIs; Jakob's PC is linked via a file bridge (list/stage/commit files; NO shell) → Claude can pull files from a connected PC folder into its workspace and run backtests there.

## C. Conflicts / flags
- 14-day run will likely show 0 EMA trades (lens 1) → reinforces "wiring check only".
- Tax rules partly unverified (26% loss value, FIFO vs aktiv-for-aktiv) → config + scenario, flag.
- Historical data depth: Kraken OHLC API 720 candles max per call; multi-year history needs bulk files (e.g. Kraken downloadable OHLCVT, data.binance.vision) — NOT verified.
- Python version / OS support for ARMv6 Pi Zero W on current Raspberry Pi OS: NOT FOUND.
- D5 ×40 stretch: no evidence any rule gets there; sim's honest job is to say so.
