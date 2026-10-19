# S3 critic (Opus), 2026-10-19

Confidence: high on variants and statistics, medium on tax law.

## 1. Bottom line
22 items, about 3 new ideas: a slower trend filter, vol-scaled exposure, dip-weighted entry. Ten lenses sharing one model and seed are not independent evidence. Add at most one PASS-eligible arm.

## 2. Variants of planned arms
- **EMA 50/200 family:** A1, A2, A3. Keep A1 (monthly, lowest turnover); drop A2 and A3. A5 also belongs here (it re-enters on an SMA rule): exploratory only.
- **90-day TSMOM:** A4, E1. Drop both. The textbook TSMOM lookback is 12 months (Moskowitz-Ooi-Pedersen 2012), so change the planned lookback instead of adding an arm.
- **Donchian:** A6, B2, F1. Drop.
- **50/50 rebalance:** E3 (drop), D1 (exploratory).
- **DCA:** merge C1 and C2; drop C3.

## 3. Weak or data-mined evidence
- **Provenance test.** Parameters fixed before crypto existed are truly out-of-sample on BTC: Faber 2007, the 200-day SMA, Turtle 20/10 (daily, not the planned 4h). Parameters picked from BTC charts are in-sample: the 200-week SMA, halving windows (A7, 4 samples), MVRV-Z 0/3.5, Fear & Greed 25/75, positive-median months (G3) and A5's -25% trigger. Drop A7 and G1-G3. G2 also breaks the public-data rule.
- **B1's evidence is low, not medium.** The cited Sharpe >1.5 is for multi-coin trend plus vol targeting at up to 200% leverage. Lens 1 found no 1x source; arXiv 2603.23480 is one year at 1 bp costs.
- **B1 has no default.** The lenses span about 90 parameter combinations. BTC vol is mostly 40-80%, so a 20% target is a near-static 25-50% BTC holding and a 60% target is near buy-and-hold. Pre-register one set.
- **E1 picks SOL with hindsight**; SOL-EUR misses 2018. E2's factor is long-short.

## 4. Contradictions
- **G1 merges opposite rules.** Lens 6 buys at Fear & Greed <25; lens 10 exits there.
- **A5 is four specs.** Lenses use a -25% or -35% trigger, three different highs and three re-entry SMAs.
- **C3 is not buy-only.** It sells at RSI >60, and RSI rules are rejected elsewhere.
- **Minor.** F1 is ER(20) in the consolidation but ER(10) in lens 9. A3 cites Detzel for SMA(200), but the paper tested only 5-100 days.
- **F2 and F3 are implementation rules, not arms.** Use plain EUR: EURC adds issuer risk and a disposal.

## 5. Multiple testing and the 100-trade rule
- **Bonferroni threshold:** 0.05/m. That is 0.01 at 5 arms and 0.0033 at 15. Every backtested variant counts.
- **"Top 1% of 1,000 random" duplicates p<0.01.** Use 10,000 draws, p=(1+k)/(N+1), with Holm (same error control, more power).
- **Continuous-weight arms** (50/50, D1, B1) need random weight paths with matched mean weight and rebalance count.
- **The rule already blocks planned arms.** EMA 50/200 cannot reach 100 trades; TSMOM and 50/50 probably cannot. Only Donchian 4h can PASS, so the rule selects the worst tax profile.
- **Two tiers.** Confirmatory: at most 6 arms, PASS-eligible, Holm-counted. Exploratory: reported, never PASS this round; promotion needs a new lock and forward paper data.
- **Replacement rule.** Before any backtest, lock which arms are low-turnover (<25 round trips/yr). For those, replace "≥100 closed trades" with all four:
  1. at least 20 round trips over the full history, otherwise INCONCLUSIVE at best;
  2. beats buy-and-hold after fees and tax in each ≥30% fall separately (2018, 2022);
  3. still beats buy-and-hold without its best single trade;
  4. passes a matched random-entry test (same trade count and time in market) at the Holm level.

  If 1-3 pass and 4 fails: INCONCLUSIVE, keep paper trading. The tests are conjunctive, so false positives cannot rise. The cost is low power.
- **Buy-only arms are controls.** They have no closed trades and, under D1, become buy-and-hold once invested.

## 6. Danish tax
- **Rebalances do realise gains.** Each partial sale is a disposal. FIFO is skat.dk's default; the aktiv-for-aktiv alternative is unresolved. FIFO sells the oldest lots first, usually the cheapest, maximising realised gain; use it as the base case.
- **Crypto vol often rises in rallies** (Baur & Dimpfl 2018, verify). B1 may then trim winners taxed at ~53% and sell after crashes, where losses are worth ~26%.
- **Whipsaw is taxed at zero profit.** +100 then -100 leaves about 27 net tax.
- **Liquidate all arms at the end of the horizon, buy-and-hold included.** Paying down debt requires selling.
- **Debt hurdle.** If the interest is deductible, the after-tax hurdle is below 5.76% (verify).

## 7. Slots
- **Confirmatory:** A1.
- **Exploratory:** B1, A5, D1 (one spec each).
- **Control:** C1/C2.
- Drop the rest.

## Open questions
- FIFO or aktiv-for-aktiv? Is the 26% loss value right?
- Does Kraken XBTEUR history include 2014?
- 12-month TSMOM?
- Adopt the replacement rule before D22 locks the rules?
