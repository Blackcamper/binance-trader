# S3 lens 04: Security and risk (spot only, drawdown and tail risk)

Date of research: 2026-10-19. Confidence labels: H/M/L. Source dates are as shown in search results; several were not verified.

## New strategy suggestions

1. **BTC volatility targeting, cash leg in EUR**
   - Rule: on the last day of each week, compute 30-day realised vol. Hold BTC weight = min(1, target / realised vol), rebalance weekly, rest in EUR.
   - Defaults: target 20% annualised vol.
   - Reduces: drawdown in high-vol crashes.
   - Adds: weekly turnover (fees and Danish realisation tax); whipsaw in choppy markets.
   - Evidence: arXiv 2603.23480 (2026-03), 2024 test year only. At a 20% target, max drawdown was -15.8% (BTC-only benchmark) vs -18.6% (naive). The stablecoin signal is a secondary feature. Confidence: L (one out-of-sample year, daily data, 1 bp costs assumed).

2. **Monthly 10-month SMA timing (Faber-style)**
   - Rule: at month end, hold BTC if the close is above its 10-month SMA, otherwise hold EUR.
   - Defaults: 10-month SMA, monthly check.
   - Reduces: exposure during long bear markets; very low turnover (a few trades a year).
   - Adds: lags sharp V-shaped reversals; overlaps the planned daily EMA strategy.
   - Evidence: Faber (2007, SSRN) is a known reference, not fetched. Confidence: M (general knowledge, not verified in this session).

3. **Drawdown circuit breaker**
   - Rule: hold BTC. Sell all to EUR if the price is 25% below its all-time high. Re-enter when the weekly close is above the 50-day SMA.
   - Reduces: tail loss in a crash of 30% or more (the required test window).
   - Adds: realises losses and gains (tax); re-entry lag after a V-shaped recovery.
   - Evidence: none fetched. Reasoning from the design. Confidence: L.

4. **Chandelier (ATR) trailing stop on a buy-and-hold core**
   - Rule: stay long BTC. Exit when the close falls below the highest close since entry minus 3 x ATR(22). Re-enter on a close above that level.
   - Reduces: gap-down and slow-bleed losses.
   - Adds: whipsaw in ranges; stop slippage on gaps and during exchange outages.
   - Evidence: not fetched. Confidence: L.

5. **EURC (MiCA-compliant) as the cash leg instead of USDT**
   - Rule: the cash leg is EURC, or EUR itself, never USDT.
   - Reduces: depeg and legal risk on the cash leg.
   - Adds: EURC liquidity risk; yield is lower.
   - Evidence: KuCoin blog citing a Circle executive that only USDC, EURC and USDG comply with MiCA for EU access. Undated, not verified against the regulation (URL: https://www.kucoin.com/blog/mica-blocks-eu-access-major-stablecoins). Confidence: M on the claim, which should be checked against ESMA.

6. **Execution guard for exchange outages and spreads**
   - Rule: use limit orders only. Skip any trade if the Kraken spread is above 0.3% or the order book depth is below 5x order size. Retry on the next closed candle.
   - Reduces: slippage and failed fills during stress.
   - Adds: missed trades (tracking error vs arms without the guard).
   - Evidence: design reasoning. Fees in the seed are 0.4-0.8% taker. Confidence: M (reasoning only).

## Risks to note for every arm

- Stablecoin depeg: the cash leg must be EUR or a MiCA-compliant EUR stablecoin.
- Gaps: stops and trailing exits fill below the trigger on weekends and crash days.
- Exchange outage: no exit if the API is down. Use a manual kill switch.
- Whipsaw: trailing and vol-target arms can turn over often, which costs fees and triggers tax realisations.

## Conflicts with constraints

None found. Every arm above is spot-only, has a fixed default, and runs on closed candles or month ends. Items 1 and 3 may trade often; check turnover against the 100-trade PASS rule.

## Open questions

- Is the Danish tax treatment of each EUR/BTC switch confirmed as a realisation under the seed rules?
- Does Bitvavo list EURC? Kraken listing was not checked.
- Faber (2007) and the trailing-stop evidence need a proper source before the arms are locked.
