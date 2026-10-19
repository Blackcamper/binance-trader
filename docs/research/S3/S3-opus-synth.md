# S3 synthesis: ranked new arms (Opus, 2026-10-19)

Trade counts are estimates. Data for every arm: Kraken XBTEUR daily closes. Every arm is long BTC or EUR cash, never above 100%. Shared stdlib helpers: about 40 lines.

## Shortlist (ranked)

### 1. Volatility-targeted BTC, monthly, 1x cap
- **Rule:** on the first close of each month:
  ```
  sigma = stdev(ln returns, 30d) * sqrt(365)
  w = min(1, 0.60 / sigma)
  rebalance only if |w - w_held| >= 0.10
  ```
  The rest is held in EUR.
- **Parameters:** 30-day window per Moreira and Muir (2017). The 60% target is about BTC's long-run volatility, keeping exposure near buy-and-hold. Zarattini's 25% would hold about 40% BTC under a 1x cap and could not beat buy-and-hold.
- **Trades/yr:** 3-8.
- **New question:** does risk-based sizing beat the planned binary arms?
- **Failure mode:** it also cuts exposure in volatile rallies (2017, 2021) and reacts late to crashes inside a month.
- **Evidence:** Moreira and Muir (equities); Zarattini et al. (2025, leveraged); arXiv 2603.23480. Eight of ten lenses converge.
- **Confidence:** medium that it lowers drawdown, low-medium that it beats buy-and-hold net.
- **Check:** benchmark against a static blend at equal average exposure.
- **Effort:** about 40 lines, half a day.

### 2. Drawdown circuit breaker on a buy-and-hold core
- **Rule:** on each daily close:
  ```
  ref = max(close since max(t-365d, last_entry))
  IN  and close <= 0.75*ref -> sell all, go OUT
  OUT and close >  SMA200   -> buy all, go IN, set last_entry
  ```
  Resetting `ref` on re-entry prevents an instant re-exit.
- **Trades/yr:** 0-2 round trips.
- **New question:** is a crash-only exit enough? It targets the PASS drawdown and >=30% fall rules directly.
- **Failure mode:** it exits after the first 25% of a fall, re-entry lags V-shaped recoveries, and whipsaws around SMA200 trigger taxable sales.
- **Evidence:** four lenses converge; one blog backtest.
- **Confidence:** low-medium, but cheap and distinct.
- **Effort:** about 30 lines, half a day.

### 3. Faber 10-month SMA, checked monthly
- **Rule:** at each month-end close, hold BTC if the close is above the mean of the last 10 month-end closes, otherwise hold EUR. Trade only when the state flips.
- **Trades/yr:** 1-4 round trips.
- **New question:** after Danish tax, does a monthly check beat the planned daily and 4h trend arms?
- **Failure mode:** it takes the full hit of a crash inside a month. If its correlation with EMA 50/200 is above 0.9, drop one.
- **Evidence:** Faber (SSRN 962461, not tested on crypto); Detzel et al. 2018 (SMA filters cut BTC max drawdown from -89% to about -68%, gross).
- **Confidence:** medium on direction, low on net edge.
- **Effort:** about 20 lines, 3 hours.

### 4. SMA200-weighted DCA (buy-only)
- **Rule:** on the weekly DCA weekday:
  ```
  cash += c                       # c = DCA arm's weekly amount
  mm = close / SMA200
  k = 2 if mm < 0.8 else (1 if mm <= 1.0 else 0)
  buy min(cash, k*c)              # skip if under 5 EUR; never sell
  ```
- **Trades/yr:** 25-52 buys, no sells.
- **New question:** can DCA be improved with no realisations? Judge against weekly DCA.
- **Failure mode:** it piles up cash in long bull markets (2020-21, 2023-24) and runs out of reserve in long bears.
- **Evidence:** CXO and Detzel on SMA timing; lenses 07, 08 and 09.
- **Confidence:** low-medium.
- **Null test:** shuffle the multipliers k across weeks 1,000 times.
- **Effort:** about 30 lines, half a day.

## Maybe later
- Dual momentum BTC/ETH/EUR (Antonacci, 12-month, monthly), after the 50/50 results.
- 60/40 BTC/EUR with a 10-point band, as the benchmark for arm 1.
- Efficiency-ratio gate on Donchian, if Donchian whipsaws.
- Chandelier stop and rebuy ladder (siblings of arms 2 and 4).
- 12-month absolute momentum and SMA50/200 filters: replacements for planned arms, not additions.
- 200-week SMA (needs about 4 years of warm-up).
- Fear and Greed gate (data only from 2018).
- Zarattini multi-lookback (9 lookbacks, not textbook).

## Skip
- Grid, market making, arbitrage, funding carry: fees, latency or not spot.
- Short-horizon mean reversion and classic indicators (RSI-2, MACD, Bollinger, Ichimoku): fail after costs.
- Weekly cross-sectional top-N: 150+ swaps a year, survivorship bias.
- Turn-of-month, seasonality, halving cycle: turnover, in-sample fits, or 4 samples.
- MVRV-Z and order-book signals: no history without a key.
- Weekly RSI(14), daily volatility rebalancing: too few signals, or too much turnover.

## Infrastructure for all arms
- EUR as the cash leg, never USDT.
- Limit orders only; skip if spread >0.3% or depth <5x order.
- A tax engine with FIFO lots, annual netting (53% on gains, 26% on losses) and a hypothetical end-of-window liquidation for every arm, so all are compared after tax.

## Open issues
1. **D22:** no arm reaches 100 closed trades (arm 4 closes none). Relax the rule (for example, two crash regimes plus nulls matched on trades and exposure) or treat these arms as benchmarks.
2. **Bonferroni:** nine tested arms in total. Add arms 1 and 2 first; arm 4 is a separate family (against DCA).
3. **Kraken history:** archive depth for XBTEUR is unverified, and both 2018 and 2022 are needed.
4. **Textbook status:** does 60% count as textbook? Check Zarattini's defaults.
5. **DCA horizon:** 52 or 104 weeks for the 5,000 DKK?
