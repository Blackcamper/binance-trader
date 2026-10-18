# binance-trader

Paper-trading simulation (no real money) of simple crypto strategies on a Raspberry Pi Zero W.
Virtual 5,000 DKK, live public market data, results after fees, slippage and Danish tax, compared with buy-and-hold.

**Status (2026-10-18):** research done (12 Haiku agents), Opus review running, code not written yet.

## Where to start (for a new Claude chat)
- `docs/GROUND-TRUTH.md` — all decisions (D13–D23 are this project; D1–D12 came from an earlier idea round).
- `docs/research/CONSOLIDATED-S2-v1.md` — summary of the research.
- `docs/research/S2-*.md` — the individual research reports.

## Ground rules (short)
- Simulation first. No real money until a strategy passes the locked go-live rules.
- 14 days = system check only. Then multi-year backtest + up to ~90 days live sim.
- Public market data only, no API keys on the Pi.
- Jakob asks Claude in the app for status; the Pi publishes results Claude can read.
