# S3 lens 02: skeptic (2026-10-19)

Scope: popular strategies that fail after fees, tax and out-of-sample tests. Seed-listed strategies excluded.

1. **Connors RSI-2 / RSI mean reversion (crypto)**: SKIP. Reason: 0 of 13 famous rules passed all five gates on 6 years of crypto data with taker fees and slippage. Rule: RSI(2) below 10 buy, above 65 sell. Source: https://dev.to/tessen/we-graded-13-famous-trading-strategies-on-6-years-of-data-all-13-failed-1aci (undated, year not shown; vendor blog). Confidence: medium-low.

2. **Bollinger breakout (20, 2 sd)**: SKIP as a separate arm. Reason: closest to passing (4 of 5 gates) in the same test, but it is a near-duplicate of the planned Donchian breakout. Source: same dev.to article. Confidence: low-medium.

3. **Short-horizon crypto mean reversion, ML-ranked (15-min)**: SKIP. Reason: gross edge about 1.3 bp per trade against about 5 bp maker and 10-20 bp taker round trip; no pair clears the maker band. Also needs ML and sub-hourly data, so it cannot run on the Pi. Source: https://arxiv.org/pdf/2608.21888 (sample to 2026-08-08, holdout out-of-sample). Confidence: high for the cost conclusion.

4. **Social-sentiment signals (Bitcoin)**: SKIP. Reason: the best-known studies are old (Garcia and Schweitzer, 2015: https://arxiv.org/pdf/1506.01513) and I found no recent net-of-fee, out-of-sample result. Confidence: low (absence of evidence).

5. **Fibonacci retracement, MACD, Stochastic, Ichimoku**: SKIP. Reason: none of these passed the same 13-strategy test; no independent survival evidence found. Source: same dev.to article. Confidence: low.

6. **Triangular or cross-exchange arbitrage (spot)**: SKIP. Reason: two or three legs of 0.25-0.80% fees exceed typical spreads, and the strategy cannot be executed reliably with public data and no API keys. Source: reasoning from SEED fee figures; arXiv 2002.12274 not read in full. Confidence: medium.

7. **Monthly volatility-targeted long-only trend (BTC/ETH)**: WORTH TESTING as a low-turnover variant. Reason: trend beat mean reversion in the same test, and monthly rebalancing suits the Danish realisation tax. Overlaps the planned 90-day momentum, so keep it only if its cadence and sizing differ. Source: dev.to article above. Confidence: low-medium.

Summary: almost every popular indicator-based rule failed net of costs. The only candidates that survive scrutiny are low-turnover trend variants.

CONFLICTS WITH: none directly. Grid bots were not tested in the sources found; they are skipped on reasoning alone (fees per rung, inventory risk in trends).

Open questions: Hull repository paper on technical rules in Bitcoin (not read); grid-bot out-of-sample evidence not found; the dev.to article's year and author independence are unverified.
