# binance-trader

Paper-trading simulation (no real money) of simple crypto strategies on a Raspberry Pi Zero W.
Virtual 5,000 DKK, live public market data, results after fees, slippage and Danish tax, compared with buy-and-hold.

**Status (2026-10-18):** research done; Pi simulator (`pitrader/`) written and tested offline, not yet run against live Kraken data.

## Where to start (for a new Claude chat)
- `docs/GROUND-TRUTH.md` — all decisions (D13–D23 are this project; D1–D12 came from an earlier idea round).
- `docs/research/CONSOLIDATED-S2-v1.md` — summary of the research.
- `docs/research/S2-*.md` — the individual research reports.

## Pi simulator
- Code: `pitrader/` (Python 3 standard library only), config: `config/sim-v1.json` (locked per run).
- Setup on the Pi: `docs/PI-SETUP.md`. Tests: `python3 -m unittest discover -s tests`.
- Tax return view: `python3 -m pitrader skat --year 2026` prints rubrik 20 (gains) and rubrik 58 (losses) per strategy; add `--csv sales.csv` for every sale. Rules: `docs/research/S2-r3-skat-selvangivelse.md`.

## Ground rules (short)
- Simulation first. No real money until a strategy passes the locked go-live rules.
- 14 days = system check only. Then multi-year backtest + up to ~90 days live sim.
- Public market data only, no API keys on the Pi.
- Jakob asks Claude in the app for status; the Pi publishes results Claude can read.
