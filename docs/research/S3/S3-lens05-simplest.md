# S3 lens 05: simplest strategies (stdlib, 1-2 params, daily/4h Kraken OHLC)

Searched 2026-10-19. Trades/yr figures are my estimates unless marked "source".

## 1. BTC-EUR daily close vs SMA(50), long/cash
- Rule: at daily close, if close > SMA50 hold BTC, else hold EUR. One param (50).
- Data: Kraken XBT/EUR 1d closes.
- Trades/yr: ~3-6 round trips (estimate).
- Evidence: Grayscale, "The Trend Is Your Friend", updated 2023-08-09, https://research.grayscale.com/reports/the-trend-is-your-friend-managing-bitcoins-volatility-with-momentum-signals . Sample 2012-01 to 2023-07. Sharpe 1.9 vs 1.3 buy-and-hold; trade counts and fees not reported. Confidence: LOW-MEDIUM (industry report, likely no fees, no drawdown figures).
- Note: close to the planned EMA 50/200 but a single filter, not a crossover.

## 2. BTC-EUR price vs SMA(200) on/off (daily)
- Rule: hold if close > SMA200, else cash. One param.
- Evidence: Detzel, Liu, Strauss, Zhou, Zhu, "Bitcoin: Predictability and Profitability Via Technical Analysis", Jan 2018, reviewed by CXO Advisory 2018-03-01, https://www.cxoadvisory.com/currency-trading/timing-bitcoin-with-smas/ . Tested 5-100 day SMAs, 2010-07 to 2017-12: max drawdown cut from -89.5% to about -66% to -70%. Gross only, no trade counts. Confidence: MEDIUM for direction, LOW for net edge.
- Not tested: 200-day exact (paper tested 5-100 only). Flag as extrapolation.

## 3. Volatility-targeted BTC exposure (daily)
- Rule: weight = min(1, 0.25 / annualised 90-day stdev of daily returns); rebalance daily. Cap at 100% (no leverage).
- Data: Kraken daily closes.
- Trades/yr: many small rebalances; high turnover, bad for DK tax (estimate).
- Evidence: Zarattini, Pagani, Barbon, "Catching Crypto Trends", Apr 2025, via CXO Advisory 2025-05-29, https://www.cxoadvisory.com/technical-trading/crypto-asset-trend-following-strategies/ . Paper uses 25% target vol with 200% leverage cap; the 1x-capped variant is my adaptation. Confidence: MEDIUM (paper), LOW (adaptation).

## 4. Multi-lookback close breakout, daily trailing stop (Zarattini 2025)
- Rule: long when close > max close of lookback L; exit when close < trailing stop = max(prior stop, midpoint of max/min close over L). Equal-weight across lookbacks.
- Trades/yr: low for long lookbacks (estimate).
- Evidence: same 2025 paper; costs tested 0.10/0.25/0.50%. Paywalled excerpt, no performance numbers. Confidence: MEDIUM-LOW.
- Note: daily, not Donchian 4h; uses 9 lookbacks, so not textbook.

## 5. Bitcoin 20/100 SMA crossover (daily)
- Rule: long when SMA20 > SMA100. Two params.
- Evidence: Grayscale 2023 (above). Sharpe 1.7 vs 1.3 buy-and-hold, 2012-2023. Confidence: LOW-MEDIUM. Overlaps the EMA crossover; include only if a second crossover is wanted.

## Not verified (no search done)
- Faber 10-month SMA monthly timing (Faber 2007, SSRN). Monthly candles can be built from Kraken 1d. Did not check the paper.

## CONFLICTS WITH constraints
- CONFLICTS WITH: "Textbook default parameters" for #4 (9 lookbacks plus midpoints).
- CONFLICTS WITH: spot-only, no leverage for #3 as published (200% leverage cap); only the 1x-capped form is live-legal.
- CONFLICTS WITH: Danish tax / turnover for #3 (daily rebalances realise gains often).
- None for #1 and #2 on rules; both are fee-sensitive and need the net backtest.

## Open questions
- Net-of-fee, net-of-tax results for #1 and #2 on Kraken EUR data.
- Whether a single SMA filter counts as a "variant" of the planned EMA 50/200 under the seed.
