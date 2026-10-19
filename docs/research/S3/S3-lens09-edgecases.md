# S3 lens 09: edge cases (regime-robust strategies), 2026-10-19

Sources are search-snippet level only; pages were not fetched in full.

## 1. Volatility-targeted BTC spot exposure
- Rule: daily close; realised vol 30d (close-to-close, annualised). Target 50% vol. Weight = min(1, 0.5 / realised_vol). Rebalance only when weight differs by >10 pts (band). Hold EUR for the remainder.
- Best regime: long trends with calm drawdowns. Worst: fast crashes, where vol spikes late and the cut comes after the fall (March 2020, FTX Nov 2022).
- Failure mode: whipsaw in sideways chop, and rebalancing sales are taxable realisations.
- Trades/yr: about 10-30 with bands.
- Evidence: https://arxiv.org/pdf/2602.11708 (2026, adaptive crypto trend-following; medium-low, abstract only).

## 2. Drawdown-triggered cash exit (crash breaker)
- Rule: exit to EUR when BTC-EUR daily close is 25% below its 365-day high. Re-enter when close is back above the 200-day SMA.
- Best regime: 2022 bear, Aug 2024 flash crash (exits happen before the lows for slow bears).
- Worst regime: V-shaped recoveries (March 2020), where re-entry lags.
- Failure mode: a single exit-and-reentry in a sideways market is a realisation for little gain.
- Trades/yr: 0-2.
- Evidence: https://ungeracademy.com/blog/the-bitcoin-trading-strategy-that-survived-2022-only-3-lines-of-code (2022-era; low-medium, one-author backtest). Close to the planned EMA 50/200 cross, so treat as a variant.

## 3. Efficiency-ratio chop gate
- Rule: 10-day Kaufman efficiency ratio on daily closes. Only allow the Donchian 4h breakout when ER >= 0.3, otherwise stay in EUR.
- Best regime: trending. Worst: choppy 2018-19 and 2023, where the gate still lets through some breakouts.
- Failure mode: gating cuts both fake and real breakouts. The gate is an overlay on a planned strategy, not a standalone.
- Trades/yr: fewer than the base strategy.
- Evidence: no direct source found in this search; low confidence.

## 4. Drawdown-scaled value averaging (buy-only)
- Rule: weekly. Target a portfolio value that rises 2% per month; buy the shortfall in EUR, sell nothing.
- Best regime: sideways and bear markets, where it accumulates cheaply.
- Worst regime: long bear markets with no recovery; capital runs out.
- Failure mode: no sales means no Danish tax realisations, but capital requirements are open-ended. Set a hard cap at the 5,000 DKK paper budget.
- Trades/yr: about 50 buys.
- Evidence: https://arxiv.org/ar5iv/2009.12155 (2020, decade of crypto trend-following; low-medium, only the abstract was checked).

## Conflicts and open questions
- CONFLICTS WITH: "at least 100 closed trades" in the PASS rules. Strategies 2 and 4 will not reach 100 closed trades in 2 years. Is a looser trade count acceptable for them?
- CONFLICTS WITH: "Textbook default parameters". Strategy 3's 0.3 threshold and strategy 1's 50% target are conventional, not sourced.
- Open: is there a reliable public proxy for exchange-stress events (FTX-type) on Kraken or Bitvavo data?
