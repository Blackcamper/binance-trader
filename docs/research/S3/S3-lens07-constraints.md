# S3 lens 07: constraint spotter (2026-10-19)

## Evidence
- Kraken order minimums: BTC 0.0001, ETH 0.01, EUR 5 EUR (support article, "last updated 6 Oct 2026"): https://support.kraken.com/articles/360001389303-overview-of-cryptocurrency-minimums
- Kraken blog on "new minimums" (BTC 0.001) is from Aug 2020, superseded. Do not use: https://blog.kraken.com/news/make-smaller-bitcoin-buys-with-krakens-new-updated-order-minimums
- EUR pair 24h volume (undated Coinranking snapshot): BTC/EUR ~$21.9M, ETH/EUR ~$10.0M, SOL/EUR ~$6.6M, XRP/EUR ~$4.3M. Source: https://coinranking.com/exchange/2Vu9j1PmUbx+kraken/markets?search=Eur&page=1

## Verdict
Order minimums are NOT binding at 670 EUR. Fees and Danish realisation tax are. Each sale or swap realises a gain, so turnover is the main filter.

| Family | Verdict | Constraint |
|---|---|---|
| Grid | BREAKS | Fees and tax: many round trips; spacing must exceed about 1.6% to pay |
| Mean reversion (4h RSI/Bollinger) | PARTLY | Tax: high trade count; fine on 1d |
| Momentum (time-series) | FITS | Low turnover (already planned) |
| Breakout (Donchian) | PARTLY | Tax: already planned |
| Market making | BREAKS | Polling every few minutes, order book latency |
| Cross-exchange arbitrage | BREAKS | Pi too slow; transfer lag; spreads below fees |
| Funding-rate carry | BREAKS | Spot-only: needs perps or shorts |
| DCA variants (buy-only) | FITS | No realisation until exit |
| Rebalancing (calendar/threshold) | PARTLY | Tax per rebalance; needs wide bands |
| Pairs (ETH/BTC ratio) | PARTLY | Two legs, two realisations |

## New suggestions (best fit)
1. **Accumulate-only dip buyer**: fixed EUR buy when BTC closes more than 20% below its 200-day SMA; never sells. Zero realisation before exit. Daily closes suit the Pi.
2. **Monthly TSMOM rotation BTC/ETH/SOL**: hold the single top 90-day performer, rebalance monthly (max 12 trades/year). Checks liquidity via SOL/EUR.
3. **Volatility-targeted BTC/EUR exposure**: monthly rebalance only when target differs by more than 15%. Caps turnover.

## Open questions
- Current BTC/ETH price levels were not verified, so the EUR size of the minimums is unconfirmed.
- The volume snapshot has no date. Check the Kraken AssetPairs/Ticker API before relying on it.
- The Pi's polling interval versus the 4h candle close needs a check.
