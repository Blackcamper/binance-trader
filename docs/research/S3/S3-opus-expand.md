# S3 expander (Opus), 2026-10-19
Primary sources read where reachable. NOT FOUND = searched, not confirmed.

## 1. Volatility targeting: primary evidence
- **Zarattini, Pagani, Barbon, "Catching Crypto Trends"**: SSRN 5209907 (written 2025-04-08, posted 2025-05-06, revised 2025-10-02); SFI RP 25-80. Working paper, not peer-reviewed. PDF: https://concretumgroup.com/wp-content/uploads/2026/02/Catching-Crypto-Trends.pdf
  - BTC sample 2015-01-01 to 2025-03-19. Donchian close breakouts with lookbacks 5/10/20/30/60/90/150/250/360 d. The stop is max(prior stop, channel midpoint). Lookbacks are equal-weighted. Size = 25% / 90-day vol (also called "3-month"), **cap 200%**, resized daily.
  - BTC combo, gross (Table 1): CAGR 30%, vol 17%, Sharpe 1.58, MDD 19%. Net of 10 bps with a 20% vol-rebalance band (Table 3): CAGR 30%, Sharpe 1.56, MDD 19%. The headline "Sharpe >1.5, alpha 10.8%" is the **20-coin rotation** (CAGR 18%, MDD 11%), not BTC.
  - Costs tested: 10/25/50 bps (cost base undefined). At 50 bps the 5-day model's CAGR falls from 34% to 18%. No 1x-capped result; average allocation NOT FOUND. Trades: 292 (5d) down to 5 (360d) in about 10 years. Internal inconsistencies (MAR, Sortino).
  - Implication: 10 bps is 4-8x below Kraken taker. BTC buy-and-hold CAGR over the window was about 73% (my estimate, $315 to $84k): it wins on Sharpe/MDD, not raw return.
- **Bloomberg "Crypto Insights: the impact of volatility targeting"** (industry, ©2021; author/date NOT FOUND): https://assets.bbhub.io/professional/sites/10/Crypto-Insights-The-Impact-of-Volatility-Targeting.pdf. BTC 2017 to Oct 2021, untargeted: return 136%, vol 93%, MDD -83%. **40% target: 78%/49%/-52%**; 20% target: 38%/24%/-30%. Return/vol 1.47 to 1.56-1.61. Costs, lookback, cap NOT FOUND.
- **Harvey et al. 2018**, *J. Portfolio Mgmt* 45(1):14-33 (60+ assets, **no crypto**): https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf. Raises Sharpe for risk assets (US equities 0.40 to 0.48-0.51), cuts the left tail. EWMA half-life 20-90 d; under 1 to about 5 round trips/yr.
- **Peer-reviewed crypto work is cross-sectional only.** Grobys et al. 2025, *FMPM* 39(4):443-476, DOI 10.1007/s11408-025-00474-9: volatility management mitigates crypto momentum crashes (numbers NOT FOUND). Yang 2025, *FRL* 85, DOI 10.1016/j.frl.2025.107879: risk-managed crypto momentum, weekly return 3.18% to 3.47%, Sharpe 1.12 to 1.42; cost details NOT FOUND. A peer-reviewed long-only BTC volatility-targeting study: NOT FOUND.
- **Downgrades.** arXiv 2603.23480 is a stablecoin copula paper (volatility targeting is a side test); arXiv 2602.11708 is 6h long-short, not spot.
- **Textbook default**: Moskowitz, Ooi, Pedersen, *JFE* 104 (2012) 228-250: 40% annualised target, EWMA vol (centre of mass 60 d), sign of 12-month return, 1-month hold.

## 2. Long-term SMA filters and the circuit breaker
- **Faber**, SSRN 962461, *J. Wealth Mgmt* Spring 2007; 2013 update (revised 2014-03-03). Rule: month-end close vs 10-month SMA, cash in 90-day T-bills. S&P 500, 1901-2012: 10.2% vs 9.3%, vol 12.0% vs 17.9%, MDD -50.3% vs -83.5%. Five assets 1973-2012: MDD -9.5% vs -46.0%. **Gross**: "Calculations ignore trading frictions and tax implications" (https://www.cxoadvisory.com/?p=1115, 2013-08-16). 3-4 round trips/yr. No crypto.
- **Detzel, Liu, Strauss, Zhou, Zhu**: working paper Jan 2018, published in *Financial Management* 50(1):107-137 (2021), DOI 10.1111/fima.12310. Daily close vs 5/10/20/50/100-day SMA, cash earns T-bills, 2010-07-18 to 2017-12-12 (https://www.cxoadvisory.com/currency-trading/timing-bitcoin-with-smas/). **Gross** results:
  - excess return 203-216% vs 224% for buy-and-hold;
  - Sharpe 2.2-2.6 vs 2.0;
  - MDD -66.4% to -70.3% vs -89.5%;
  - break-even switching cost 1.1% (5d) to 4.5% (100d).

  200-day NOT tested; no true out-of-sample (split halves only).
- **Hudson & Urquhart**, *Annals of OR* 297(1), 2021, DOI 10.1007/s10479-019-03357-1. 14,919 rules, data to 2017-12, out-of-sample H1 2018. Break-even costs are mostly above 50 bps. Few rules beat buy-and-hold on raw return; more beat it on Sortino/Calmar. Best BTC rule: no positive out-of-sample return.
- **Deprez & Frömmel**, *IREF* 93:858-874, 2024, DOI 10.1016/j.iref.2024.05.003. 75,360 rules with costs and a data-mining correction. Beats buy-and-hold out-of-sample "especially risk-return wise"; parameters NOT FOUND.
- **Circuit breaker (-25% from the high)**: no primary backtest FOUND.
  - Theory: Kaminski & Lo, *J. Fin. Markets* 18 (2014) 234-254 (https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf). Stops add value only under momentum or regime switching; they destroy it under random walk or mean reversion.
  - Crypto stop-loss evidence is cross-sectional only: Sadaqat & Butt, *JBEF* 39 (2023) (147 coins, 2015-01 to 2022-06); Kaya & Mostowfi, *FRL* 46 (2022).

## 3. Families the lenses missed (spot, low turnover, public OHLC)
1. **Volatility-scaled TSMOM (Moskowitz-Ooi-Pedersen)**: 12-month sign, 40%/EWMA-60 sizing, 1x cap, monthly, 20% band. All parameters are published (meets "textbook defaults"). Merges planned TSMOM with B1.
2. **TIPP/CPPI drawdown floor**: exposure = m × (V − F), with floor F = k × the running peak of V. Targets "MDD ≤ buy-and-hold" directly. Estep & Kritzman 1988 (JPM), Black & Perold 1992 (JEDC): not fetched. Gap risk: Cont & Tankov 2009, *Math. Finance* (https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9965.2009.00377.x). Crypto evidence NOT FOUND. No textbook m or k (conflicts with the defaults rule).
3. **Low-volatility selection plus stop-loss** (Kaya & Mostowfi 2022): low-vol coins, 6-12-month lookback and hold. Needs a multi-coin EUR universe; sample only 2017-01 to 2021-06.

## 4. Kraken XBTEUR depth
- Public Trades endpoint (no key), XXBTZEUR since=0, fetched 2026-10-19. First trade: unix 1378856827 = **2013-09-10 23:47 UTC at €97.00**. By 2014-01-01, trades come every few minutes (€539).
- Archive page (updated 2026-10-12): "each pair from its first trade on Kraken through 30 June 2026", quarterly zips; pairs not listed. Inference: XBTEUR starts 2013-09-10. NOT verified inside the archive (proxy blocked download).
- Binance EUR pairs began January 2020 (crowdfundinsider).

## 5. Cross-cutting flag
Every crypto source wins on Sharpe/MDD but loses on raw return (Detzel 203-216% vs 224%, Bloomberg 78% vs 136%, Zarattini 30% vs about 73%). If "beats buy-and-hold" means raw return, these families likely fail; if risk-adjusted, they lead. Decide before locking D22.
