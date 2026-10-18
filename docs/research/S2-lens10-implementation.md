# S2 lens 10 implementation — DONE (agent returned summary only; transcribed by orchestrator)
Recommendation: B — custom Python + ccxt + SQLite + static dark page. D13 needs fees, slippage, latency, tax and per-asset buy-and-hold; Freqtrade dry-run supplies none of these well.
- Freqtrade stable Docker image includes linux/arm64; docs: native ARM64 install unsupported, hyperopt not advised on a Pi. RAM/CPU NOT FOUND.
- Freqtrade dry-run market fills walk the book (capped 5% from price); limit orders fill on cross, no delay. Backtests assume no slippage, no tax; "market change" averages all pairs, not per-asset B&H. FreqUI can stop bot/force trades, no HTTPS, not for internet exposure. Multi-bot = one config/DB/port per bot (inference).
- ccxt free, 103 exchanges; ccxt.pro (watchTicker/watchOrderBook) is free part of CCXT (docs.ccxt.com/docs/pro).
Read-back/deploy: Pi writes daily JSON to pCloud via rclone + plain-text daily email; Claude reads via connectors; no open ports. Claude pushes to private GitHub repo; Pi systemd timer does `git pull --ff-only` + restart with read-only deploy key.
Human steps (one-time): flash OS, SSH key, deploy key, pCloud OAuth, SMTP app password, 5V/5A USB-C PSU.
Improves: limit-fill delay; per-asset B&H with identical fees; backtests on Windows PC/TrueNAS not the Pi; text labels, no red/green.
Open: RAM per bot ESTIMATE; which exchange serves keyless public data from DK (untested).
