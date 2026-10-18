# S2 Lens 5: Simplest version (Pi paper trading)

**Bottom line:** One standard-library Python script on the Pi polls one public EUR market every 5 minutes, runs buy-and-hold, DCA and one trend rule side by side, logs to CSV, rewrites one static page and sends one daily push. Endpoints are doc-verified only. Fee and tax numbers are NOT settled.

**Verification status (2026-10-18):** Sandbox calls to the exchange hosts were refused at the proxy (403). Nothing is live-tested; the first Pi run is the test.

## Suggestions

1. **One script, Python 3 standard library only, run by cron `*/5 * * * *`.** No pip, no key, no database; it reads its CSV on start, so a reboot loses nothing.

2. **Price and spread: Kraken public Ticker.** `GET https://api.kraken.com/0/public/Ticker?pair=XBTEUR`; use `b[0]` (bid) and `a[0]` (ask). Doc: https://docs.kraken.com/api/docs/rest-api/get-ticker-information (fetched 2026-10-18). Pair name XBTEUR is NOT FOUND in the fetched docs; confirm once via `https://api.kraken.com/0/public/AssetPairs` (https://docs.kraken.com/api/docs/rest-api/get-tradable-asset-pairs). Public rate limit: NOT FOUND (keyed-counter docs: https://docs.kraken.com/api/docs/guides/spot-rest-ratelimits). Three calls per 5 minutes is far below any tier (ESTIMATE).

3. **Slippage: Kraken public Depth, `count=50`.** `GET https://api.kraken.com/0/public/Depth?pair=XBTEUR&count=50` (default 100, max 500). Walk the book for the order size; use the volume-weighted fill. Doc: https://docs.kraken.com/api/docs/rest-api/get-order-book.

4. **Trend history: Kraken public OHLC, `interval=1440`.** `GET https://api.kraken.com/0/public/OHLC?pair=XBTEUR&interval=1440` returns up to 720 daily candles, enough for a 50-day or 200-day average. Doc: https://docs.kraken.com/api/docs/rest-api/get-ohlc-data.

5. **Three strategies plus benchmark, same ticks, same costs.**
   - Buy-and-hold: all 5,000 DKK bought on the first tick.
   - DCA: 500 DKK every 7 days (cadence is a design choice).
   - Trend: long while price is above its 50-day average, cash otherwise.
   Reason: each rule fits in one sentence.

6. **Fill and cost assumptions (bake these in).**
   - Decide on tick N; fill at tick N+1 at the depth-walked ask (buy) or bid (sell). Reason: no fill at an untradeable price.
   - Taker fee 0.80%, the conservative choice. Source: https://www.kraken.com/features/fee-schedule (fetched 2026-10-18): Tier 1 ($0+) maker 0.40%, taker 0.80%. CONFLICT: third-party reviews cite 0.25% and 0.40%. Check the live table before trusting either.
   - Simulate in EUR and convert to DKK at the fixed 7.46038 DKK per EUR, the ERM II central rate in the ECB press release of 17 Jan 2000 (https://www.ecb.europa.eu/press/pr/date/2000/html/pr000117.de.html). Reason: no FX feed. Band 7.29252 to 7.62824 is my arithmetic (plus or minus 2.25%).

7. **Output: CSV, one static page, one daily push.** Each tick appends a row per strategy (time, bid, ask, position, cash, equity DKK, fees). The page is dark with light grey text; blue and orange, plus tick and cross, instead of red and green (Jakob is red-green colour-blind). Daily push: `curl -d "..." https://ntfy.sh/<long-random-topic>`; the topic name is the only secret (https://docs.ntfy.sh/publish/, fetched 2026-10-18). Rate limit NOT FOUND.

8. **Tax: one config value, realised gains only.** Sources conflict. tax.dk DJV 2026-2 (https://tax.dk/jv/cc/C_C_2_1_3_3_5_1.htm, fetched 2026-10-18): speculation gains are personal income, realisation principle, no FIFO mentioned. financer.dk (https://financer.dk/krypto/skat-af-kryptovaluta/, 2026): FIFO, 37 to 53%. The 27%/42% scale (https://www.skagenonline.dk/faq/er-bitcoin-lagerbeskattet, labelled 2024) is for share income. Show pre-tax and after-tax equity. Rate and loss rule: NEEDS CONFIRMATION by an accountant.

## Next three upgrades, in order

1. **Backfill and backtest on day 1.** Run the strategies over the 720 daily candles so the page has history at once. Reason: a backtest can rule a strategy out; it cannot confirm one.
2. **Risk columns.** Max drawdown, trade count and fees as % of equity per strategy. Reason: buy-and-hold also has a drawdown, so a fair comparison needs it.
3. **Second feed as a sanity check.** Coinbase Exchange public: 10 requests/s per IP, bursts to 15 (https://docs.cdp.coinbase.com/exchange/rest-api/rate-limits, no date shown). Reason: flags bad ticks. Fee table NOT FOUND.

Binance fallback weights: ticker/price 2, klines 2, depth (limit up to 100) 5; IP limit NOT FOUND (https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints).

## Human steps (D3), all once

- Flash Pi OS, set Wi-Fi and power.
- Confirm the XBTEUR pair name and the live fee table.
- Install the ntfy app and subscribe to the private topic.
- Pick phone access (home LAN or a VPN).
- Confirm the tax rule with an accountant before any real-money decision.

## Flags

- CONFLICTS WITH: none found against D1 to D18.
- Unverified live: all endpoints. Fee and tax figures conflict across sources.
