# S3 consolidated: new strategy candidates (10 Haiku lenses, 2026-10-19)
Seed + constraints: SEED.md. Full lens outputs: S3-lens01..10-*.md. Evidence is mostly thin (search snippets, vendor blogs); few primary sources read in full.

## Theme A. Low-turnover regime filters (long BTC or EUR cash)
- A1 Monthly 10-month SMA timing (Faber 2007, not re-verified). 0-4 trades/yr. Lenses 3, 4.
- A2 200-week SMA on weekly BTC (K33, coinedition; no backtest). 0-2 trades/yr. Lenses 1, 3.
- A3 Daily close vs SMA(50) or SMA(200), long/cash (Grayscale 2023 Sharpe 1.9 vs 1.3 gross; Detzel et al. 2018 DD -89% -> ~-68% gross). Lens 5. Possible variant of planned EMA 50/200.
- A4 12-month absolute / dual momentum vs EUR cash, monthly. 0-2 trades/yr. Lenses 8, 10. Variant of planned 90-day TSMOM.
- A5 Drawdown circuit breaker: exit at -25% from 252-day high/ATH, re-enter above 50-day or weekly 200 SMA. 1-4 trades/yr. Lenses 3, 4, 9, 10 (four lenses converge).
- A6 Chandelier ATR(22)x3 trailing stop on BTC core. Lens 4. Low evidence.
- A7 Halving-cycle timing. ~1 trade/yr. Lens 3. TradingView script only, very few samples (4 halvings).

## Theme B. Volatility targeting / sizing (strongest convergence: lenses 1, 2, 3, 4, 5, 7, 9, 10)
- B1 Weight = min(1, target/realised vol), target 20-50% annualised, 30-90 day vol, monthly or weekly rebalance only when target drifts >15-20%. ~3-24 trades/yr. Evidence: Zarattini, Pagani, Barbon "Catching Crypto Trends" (2025, net of fees per abstract, Sharpe >1.5; published version uses up to 200% leverage, only 1x cap is live-legal); arXiv 2603.23480 (one OOS year). Confidence medium.
- B2 Vol-adjusted trend following (Zarattini/Barbon: multi-lookback breakout + trailing stop). Conflicts "textbook defaults" (9 lookbacks).

## Theme C. Buy-only / accumulation variants (no realisation until exit: tax-friendly)
- C1 Value-averaging DCA vs 200-day SMA: 2x when >20% below, skip/1x when above. Lenses 7, 8, 9.
- C2 Drawdown rebuy ladder: buy a slice after each further 15% fall from 90-day high. Lens 8.
- C3 Weekly RSI(14) dip buying. Lens 10. Low evidence.
- Note: compare against plain weekly DCA, not lump sum.

## Theme D. Rebalancing
- D1 60/40 BTC/EUR with 10-point drift band. 2-6 trades/yr. Lenses 3, 8. Each sale is a realisation.
- (50/50 BTC/ETH already planned.)

## Theme E. Rotation / cross-section
- E1 Monthly rotation BTC/ETH/SOL: hold the top 90-day performer (or EUR if all negative). <=12 trades/yr. Lens 7.
- E2 Cross-sectional momentum top-10 coins (Liu, Tsyvinski, Wu, J. Finance 2022; arXiv 2510.14435 weekly t=3.89 gross). 12-150+ swaps/yr. Turnover too high for DK tax at weekly cadence.
- E3 ETH/BTC 200-day trend filter. Lens 6. No evidence; close to 50/50 arm.

## Theme F. Filters / overlays on existing arms
- F1 Efficiency-ratio chop gate on Donchian (skip entries when ER(20)<0.3). Lens 9. No direct source.
- F2 Execution guard: limit only, skip if spread >0.3% or depth <5x order. Lens 4. Infrastructure, not an arm.
- F3 EUR (or MiCA-compliant EURC) as cash leg, never USDT. Lens 4.

## Theme G. Alternative data (backtest-weak)
- G1 Fear & Greed gate (history only from 2018, API unverified). Lenses 6, 10.
- G2 MVRV-Z monthly filter (no free key-less historical source verified). Lens 6.
- G3 Turn-of-month / calendar seasonality (low evidence, overfit risk). Lenses 6, 10.

## Rejected by lenses (SKIP)
Grid bots, market making, cross-exchange arbitrage, funding-rate carry (not spot), short-horizon mean reversion (gross ~1.3 bp/trade vs 10-80 bp cost, arXiv 2608.21888), RSI-2/MACD/Bollinger/Ichimoku (0/13 classic rules passed in one vendor test), social sentiment, Fibonacci, order-book imbalance (no free historical L2).

## Cross-cutting conflicts / flags
1. PASS rule ">=100 closed trades" is unreachable for most low-turnover arms (2-12 trades/yr). Lenses 3, 4, 9, 10 all flag this. Needs a decision before rules are locked (D22).
2. Kraken XBTEUR history depth in the OHLCVT archive (to 30 Jun 2026) unverified; Binance BTCEUR likely only from ~2019-2020.
3. Kraken minimums not binding (BTC 0.0001, ETH 0.01, EUR 5; Kraken support 6 Oct 2026). Liquidity fine for BTC/ETH/SOL/XRP EUR.
4. Adding many arms raises Bonferroni bar (p<0.01 with 5 arms). More arms = harder to PASS any.
