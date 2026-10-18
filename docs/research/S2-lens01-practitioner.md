# S2 Practitioner lens: strategies for the Pi Zero W simulation

**Bottom line:** Run two controls and four textbook trend or breakout rules on public spot candles. A 14-day run tests the plumbing, not the edge.

## Strategies (spot, long-only)

| # | Strategy | Plain rule | Defaults | Timeframe, pair | Trades 14 d | Trades 90 d |
|---|---|---|---|---|---|---|
| C1 | Buy-and-hold (control) | Buy once, never sell | none | 1d, BTC-EUR | 1 (exact) | 1 (exact) |
| C2 | DCA (control) | Split 5,000 DKK equally into weekly buys | 7-day step | 1d, BTC-EUR | 2 (3 if day 14 counts) | 13 (exact) |
| S1 | EMA crossover | Buy when EMA50 closes above EMA200; sell when below | 50 / 200 | 1d, BTC-EUR | ESTIMATE 0-1 | ESTIMATE 0-2 |
| S2 | Donchian breakout | Buy above the 20-candle high; sell below the 10-candle low | 20 / 10 | 4h, BTC-EUR | ESTIMATE 1-5 | ESTIMATE 5-25 |
| S3 | Time-series momentum | Hold BTC while 90-day return is positive, else cash | 90 days | 1d, BTC-EUR | ESTIMATE 0-1 | ESTIMATE 1-4 |
| S4 | Donchian, ETH leg | Same as S2 | 20 / 10 | 4h, ETH-EUR | ESTIMATE 1-5 | ESTIMATE 5-25 |

ESTIMATE means judgement, not measurement. Count trades on historical data before deploying.

## Data feed

- **Primary: Kraken.** `GET https://api.kraken.com/0/public/OHLC`, no key. Intervals include 240 (4h) and 1440 (1d); up to 720 recent candles. Rate limit: NOT FOUND. https://docs.kraken.com/api-reference/market-data/get-ohlc-data (read 18 Oct 2026). Verify the pair name (XBTEUR expected).
- **Alternative: Bitvavo.** `GET /{market}/candles`, public. Intervals include 4h and 1d; max 1440 candles. Public rate limits: NOT FOUND. https://docs.bitvavo.com/docs/rest-api/get-candlestick-data/ (read 18 Oct 2026).
- **Coinbase: fallback only.** No 4h granularity; max 300 candles per request. https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles
- **Binance: excluded.** Crowdfund Insider (June 2026) reports a withdrawn MiCA bid (24 June 2026) and EU service limits from 1 July 2026. Denmark not named: NOT FOUND. https://www.crowdfundinsider.com/2026/06/288066-binance-to-limit-crypto-services-for-eu-users-after-withdrawing-mica-license-bid-in-greece/

## Fees and hardware

- Keep the 0.8% taker assumption. Kraken's base taker is disputed: 0.40% (Bitsgap, 13 Sep 2026, https://bitsgap.com/blog/kraken-trading-fees-explained-what-it-costs) versus 0.80% (DataWallet, updated 24 Aug 2026, https://www.datawallet.com/crypto/kraken-fees-explained). Kraken's own fee page: NOT FOUND.
- Bitvavo's cheapest rate (0% maker, 0.02% taker) needs a 25M EUR volume tier. Standard tier: NOT FOUND.
- Pi Zero W: BCM2835, one core at 1 GHz, 512 MB RAM (https://www.sparkfun.com/raspberry-pi-zero-w.html, date NOT FOUND). ARMv6 and Python version: NOT FOUND; check `python3 --version` on the device.

## Practitioner tips

1. **Trade on closed candles only.** Kraken's last row is still forming and can change before close.
2. **Poll every few minutes, but compute only when a candle closes.** Use `since` and store the last closed timestamp; fewer calls keep the Pi and API calm.
3. **Read 14 days as wiring, not edge.** S1 may fire zero times; day 14 proves feed, logs and fills work. Judge trend rules at 90+ days.
4. **Fix textbook parameters before day 1; never retune live.** Tuning after seeing results is overfitting.
5. **Use Kraken for 4h, not Coinbase.** Coinbase's 300-candle pages would take many calls to build 4h bars.

Warm-up: Kraken's 720-candle cap covers every rule (4h about 120 days; 1d about 2 years).

## Open questions

- MiCA status of these feeds for any future live use: NOT FOUND.
- DKK pairs: NOT FOUND. Fallback: EUR pairs plus a logged EUR/DKK rate.
- Is 200,000 DKK in 12 months (D5) reachable? No evidence found; none of these rules is expected to get there.
