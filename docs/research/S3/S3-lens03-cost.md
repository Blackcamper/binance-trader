# S3 lens 03: cost / turnover minimiser (2026-10-19)

Fee+tax drag estimates assume ~0.6% per side (Kraken taker plus spread), 53% marginal tax on realised gains, and gains that are realised at each exit. These are my estimates, not measured results.

## 1. Monthly 10-month SMA regime filter (BTC-EUR)
- Rule: at each month-end close, hold BTC if close > 10-month SMA, otherwise hold EUR cash. Re-check monthly only.
- Trades: about 2-4 round trips/year.
- Drag: about 2-4% fees per year, plus tax on realised gains only at exits.
- Evidence: Faber, "A Quantitative Approach to Tactical Asset Allocation" (SSRN 962461, 2007). Multi-asset result, not BTC-specific, and not re-verified in this session. Confidence: medium for the general idea, low for BTC.

## 2. 200-week SMA regime filter (BTC-EUR, monthly)
- Rule: hold BTC while month-end close > 200-week SMA, otherwise cash.
- Trades: about 1-2 round trips/year.
- Drag: about 1-2% fees per year.
- Evidence: https://coinedition.com/bitcoin-trades-above-200-week-ma-that-historically-delivered-113-returns/ (updated 2026-06-18). It cites buyer-below-MA statistics only, with no backtest, trade count or above-MA drawdown. Confidence: low.

## 3. Drawdown circuit breaker on a buy-and-hold core
- Rule: hold BTC. Move to cash after a 35% drawdown from the all-time high, measured on monthly closes. Re-enter when price closes above the 200-week SMA.
- Trades: about 0-2 round trips/year.
- Drag: about 0.5-1% fees per year, plus tax only in drawdown years.
- Evidence: none found in this session. Confidence: low. Its value depends on the 30%+ fall test in the PASS rules.

## 4. Wide-band threshold rebalancing (BTC vs EUR cash)
- Rule: target 50% BTC. Rebalance only when the BTC weight leaves the 40-60% band, checked daily.
- Trades: about 2-6 round trips/year in typical markets.
- Drag: about 2-6% fees per year.
- Evidence: https://blog.shrimpy.io/blog/the-best-threshold-for-cryptocurrency-rebalancing-strategies. Backtest covers 2017-2019 and is vendor-published. It reports median outperformance vs HODL at 15% threshold, with no drawdown or trade count. Confidence: low.

## 5. Vol-targeted exposure with monthly updates and 20% bands
- Rule: target BTC weight = min(1, 40% / 30-day realised vol). Adjust only if the weight moves more than 20 points, checked monthly.
- Trades: about 3-6 rebalances/year.
- Drag: about 2-4% fees per year.
- Evidence: no direct backtest found in this session. Confidence: low. Plausible drawdown reduction is an estimate.

## 6. Halving-cycle exposure (BTC-EUR, monthly)
- Rule: hold BTC from 12 months after a halving until 18 months after it, otherwise cash.
- Trades: about 1 round trip per year.
- Drag: about 1% fees per year.
- Evidence: only TradingView community scripts (https://www.tradingview.com/script/A7JZflyG/), with no date and no out-of-sample testing. Confidence: very low. Only 4 cycles exist, so this is the most overfitting-prone idea.

## Constraint notes
- Only 4 halving cycles and about 16 years of BTC data limit the PASS sample size. Monthly strategies will rarely reach the 100-trade requirement. This is a direct conflict with the PASS rules, but it is expected for this lens.
- Idea 1 can be expressed on spot only. No conflicts with the live-money rules.

## Open questions
- Does the 30%+ fall requirement mean an out-of-sample test window of at least 2 years is enough for monthly signals?
- Danish tax: is there a realisation timing or allowance rule that makes a single annual exit window materially cheaper? To be checked.
- Sample size: at 2-4 trades/year, meeting the 100-trade PASS rule would need a very long history, so the PASS rule may need a cost-lens exception.
