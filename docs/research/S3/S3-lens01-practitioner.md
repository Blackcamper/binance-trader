# S3 lens 01: practitioner strategies (2026-10-19)

Only strategies NOT in SEED.md. Parameters marked "verify" were not confirmed from the source text.

## 1. Volatility-adjusted trend following (BTC, ETH; daily)
- Rule: long when close is above a trailing volatility-scaled band (ATR-based trailing stop, sized to a volatility target); otherwise flat. Exact multiplier and lookback: verify in paper.
- Turnover: about 4-12 trades/yr (verify). Spot-only: yes (long/flat).
- Evidence: Zarattini, Pagani, Barbon, "Catching Crypto Trends", SSRN, 2025. https://abarbon.com/papers/catching-crypto-trends (retrieved 2026-10-19). Confidence: Medium. Authors are practitioners at a firm, so possible promotional bias; replicate on Binance data.

## 2. Cross-sectional crypto momentum (top-N by market cap, monthly rebalance)
- Rule: each month, hold the top 10 coins by trailing 3-week/12-month return (spot, equal weight); exit losers. Lookback and N: verify against paper.
- Turnover: about 12-24 rebalances/yr, high fee and tax load. Spot-only: yes on Kraken EUR, but liquidity filter needed for small altcoins.
- Evidence: Liu, Tsyvinski, Wu, "Common Risk Factors in Cryptocurrency", Journal of Finance, 2022 (NBER w24877, 2018 working paper). https://www.nber.org/papers/w24877.pdf. Confidence: Medium-High for existence of the factor; Low for net profit after Kraken fees and Danish tax.
- Note: differs from the 90-day time-series momentum in SEED (cross-sectional, not per-asset).

## 3. 200-week moving average, weekly close (BTC-EUR)
- Rule: hold BTC when weekly close is above the 200-week SMA; flat otherwise. Textbook default: 200 weeks.
- Turnover: about 0-2 trades/yr. Spot-only: yes.
- Evidence: practitioner commentary only, e.g. K33 Research, "Returning to the 200w MA", https://k33.com/research/articles/returning-to-the-200w-ma (undated in search; verify). No peer-reviewed backtest found. Confidence: Low. Needs about 4 years of data before the first signal.

## Not sourced (no URL found, do not add without a source)
- Volatility targeting overlay on BTC/ETH: no crypto-specific source located in this search.

## Summary
Only 3 strategies with usable sources. Strategy 2 likely needs a multi-coin universe, outside the BTC/ETH framing of SEED.

Open questions: exact parameters for strategy 1 (read the SSRN PDF); whether Kraken EUR liquidity supports strategy 2 altcoins; K33 article date.
