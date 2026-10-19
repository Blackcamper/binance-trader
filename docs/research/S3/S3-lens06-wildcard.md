# S3 lens 06: wild-card strategies (2026-10-19)

Scope: new ideas only, not in SEED.md. Evidence is thin; treat every item as a hypothesis for the simulation, not a finding.

## 1. BTC-EUR turn-of-month, long-only
- Rule: hold BTC-EUR from the close 2 trading days before month-end to the close 3 days into the new month; cash otherwise.
- Data: Kraken OHLC 1d (free, no key).
- Trades: about 12 round trips/yr (about 24 swaps).
- Evidence: https://quantifiedstrategies.substack.com/p/bitcoin-the-end-of-month-effect (undated blog, backtest details not shown). Academic seasonality study: https://uia.brage.unit.no/uia-xmlui/handle/11250/3082734 (not read in full).
- Confidence: low. Fees on 24 swaps are a real drag.

## 2. Weekly cross-sectional 2-week momentum, top-N coins (N=3 of top 10 on Kraken EUR)
- Rule: rank by 2-week return, hold the top 3 equal-weight, rebalance weekly.
- Data: Kraken OHLC 1d for each EUR pair.
- Trades: about 150+ swaps/yr. High turnover.
- Evidence: https://arxiv.org/pdf/2510.14435 (v4, 2026-03-21). Weekly 2-week momentum long-short spread 0.026/week (t=3.89), post-2020 0.021 (t=3.70). Gross, not net of fees or tax, and long-short, not long-only.
- Confidence: medium on the signal, low on net viability.
- CONFLICTS WITH: fee and Danish tax constraints (turnover).

## 3. BTC monthly MVRV-Z filter
- Rule: at month-end, hold BTC if MVRV-Z < 0; sell to cash if MVRV-Z > 3.5.
- Data: MVRV needs realized cap, which is not on Kraken. Public chart sources exist, but the free-API route is unverified.
- Trades: about 2-4 per yr.
- Evidence: https://k33.com/research/archive/articles/using-market-value-to-realized-value-to-estimate-market-tops-and-bottoms (date not shown).
- Confidence: low-medium. Data availability is the main blocker.

## 4. Fear and Greed spot filter
- Rule: buy BTC-EUR when the index is below 25 and sell when above 75; otherwise cash.
- Data: alternative.me Fear and Greed API (public, no key; verify before use).
- Trades: about 4-8 per yr.
- Evidence: https://sentimentrader.com/blog/when-not-to-own-bitcoin-part-ii (sentiment-regime article, undated, not verified).
- Confidence: low.

## 5. ETH/BTC ratio trend filter (not the 50/50 rebalance)
- Rule: hold ETH-EUR when ETH/BTC closes above its 200-day SMA, otherwise hold BTC-EUR; check weekly.
- Data: Kraken OHLC 1d for both pairs.
- Trades: about 4-6 per yr.
- Evidence: none read. Idea only.
- Confidence: very low. Close to the planned 50/50 arm, so it may be a variant.

## Open questions
- Confirm free MVRV or on-chain feed without a key (idea 3).
- Net-of-fee and net-of-tax backtests for ideas 1 and 2 on the PC.
