# S3 Lens 10: Implementation realist (2026-10-19)

## Data verification
- Kraken OHLCVT bulk archive: each pair from its first trade through 30 June 2026. CSV, no header, fields timestamp, open, high, low, close, volume, trades. Intervals include 1440 (daily) and 240 (4h). Intervals with no trades are omitted. Source: https://support.kraken.com/hc/en-us/articles/360047124832-Downloadable-historical-OHLCVT-Open-High-Low-Close-Volume-Trades-data. EUR pairs are not named on the page; confirm XBTEUR coverage before relying on it.
- Kraken has no historical order book or trade-level bulk download. The Depth endpoint is a live snapshot only (up to 500 levels). L3 needs auth. Source: https://docs.kraken.com/exchange/guides/general/historical-data.md
- Kraken REST OHLC: 720 candles per call, no auth, IP rate limits. Daily candles cover about 720 days per call, so the live Pi endpoint can use the same interval as the backtest.
- Not verified in this pass: data.binance.vision BTCEUR depth (Binance EUR pairs are thin and start late) and CryptoDataDownload.

## New suggestions (all spot, all daily or weekly candles)

1. **Volatility-targeted BTC (monthly)**. Rule: at the first close of each month, hold BTC weight = min(1, 60% / 30-day realised vol), rest in EUR cash. Data: Kraken OHLCVT XBTEUR 1440 (or Binance BTCEUR daily). Live: Kraken OHLC interval=1440. Backtestable: YES. Trades/yr: about 12-24 rebalances. Confidence: medium-high. Likely fails the 100-trade rule.

2. **Dual momentum BTC vs cash (monthly)**. Rule: at month end, hold BTC if its 12-month return is above 0, else EUR cash. Data: Kraken XBTEUR 1440. Live: Kraken OHLC 1440. Backtestable: YES. Trades/yr: 0-2. Confidence: medium. Structurally distinct from the 90-day momentum arm (monthly switch to cash), but close enough that Jakob may view it as a variant.

3. **Drawdown-stop trend filter (weekly)**. Rule: exit to EUR when the daily close is 25% below the 252-day high. Re-enter when the weekly close is above the 200-day SMA. Data: Kraken XBTEUR 1440. Live: Kraken OHLC 1440. Backtestable: YES, and the 2018 and 2022 drawdowns can be tested directly. Trades/yr: 1-4. Confidence: medium-high for the max-drawdown criterion.

4. **Weekly RSI(14) dip buying**. Rule: buy when weekly RSI < 30, sell when RSI > 60. Data: Kraken XBTEUR 10080 (weekly). Live: Kraken OHLC 10080. Backtestable: YES. Trades/yr: 2-5. Confidence: low. Sample size is too small for the 100-trade and Bonferroni criteria.

5. **Calendar seasonality (monthly)**. Rule: hold BTC in months with positive historical median return, EUR otherwise. Data: Kraken XBTEUR 1440 from 2013. Live: Kraken OHLC 1440. Backtestable: YES, but in-sample only. Trades/yr: 4-8. Confidence: low. Heavy multiple-testing risk; flag as a likely overfit control.

6. **Fear and Greed regime gate (daily)**. Rule: hold BTC when the index is above 25, else EUR. Data: alternative.me Fear and Greed index, daily from 2018 (free, unverified in this pass). Live: same public API. Backtestable: YES, but only about 8 years and one source. Trades/yr: 2-10. Confidence: low. Index is a derived, non-tradable-venue signal; provenance risk.

## Backtest NO (flag)
- Order book imbalance / spread strategies: no free historical L2 depth on Kraken. Live snapshot only. Backtest NO.
- On-chain (MVRV, exchange flows): free history is partial and often rate-limited. Backtest NO for honest 5-year coverage.

## Conflicts and open questions
- CONFLICTS WITH: ">=100 closed trades" PASS rule. Suggestions 1-5 produce fewer than 100 trades in 5 years. Either relax the criterion for low-turnover strategies or accept they cannot pass live.
- Open: confirm XBTEUR history depth in the Kraken archive (first trade 2013-2014 for XBT/USD, EUR start later). Binance BTCEUR history probably starts after 2019, which breaks the 5-year requirement.
- Open: the >=30% fall test needs 2018 or 2022 in the window. Kraken EUR data covers both.
