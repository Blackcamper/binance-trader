# S2 Lens 03: Cost and time (Raspberry Pi paper-trading)

Research date: 2026-10-18. DKK incl. 25% moms unless marked. NOT FOUND = not located. ESTIMATE = my calculation.

## Bottom line

**Found parts cost about 1,780 kr once, plus about 45-90 kr/year electricity, with zero software or dashboard licence cost.** **Stock is the bottleneck:** the cheapest boards are sold out or months away in Denmark.

## Suggestions

1. **Pi 5 4GB, otherwise Pi 5 8GB.** Pi 5 8GB is the only Danish price found (1,455 kr). Order early.
2. **Skip Pi Zero 2 W and Pi 4 2GB.** Zero 2 W has 512 MB RAM and a 54-week DK lead time. Pi 4 2GB is out of stock at [raspberrypi.dk](https://raspberrypi.dk/no/wp-json/wp/v2/product/217613).
3. **Official 27 W USB-C PSU (about 119 kr).** Matches Pi 5 power needs.
4. **High Endurance microSD 64 GB (202 kr).** Cheapest durable storage; batch database writes. Buy an SSD only if logs prove write-heavy.
5. **WebSocket feeds from Coinbase Exchange and Kraken, Bitvavo as cross-check.** No key; limits far above a few dozen pairs.
6. **Avoid Binance as primary feed.** EU limits from 1 July 2026; Denmark status NOT FOUND.
7. **Free dashboard and alerts.** Static page on the Pi, phone access via Tailscale Personal, alerts via Telegram.
8. **IMPROVES: week 1 on existing hardware.** Run on TrueNAS or Windows PC (D15) while the Pi ships. Marginal cost about 0 kr.

## Itemised hardware

| Item | Price | Source (seen 18 Oct 2026) | Status |
|---|---|---|---|
| Pi 5 8GB | 1,455 kr incl. (1,164 ex. moms) | [Farnell DK](https://dk.farnell.com/raspberry-pi/rpi5-8gb-single/rpi-5-board-2-4ghz-8gb-arm-cortex/dp/4256000) | Delivery from 29.10.2026; 13-week lead time (conflicting, verify). Sweden in stock at 2,149 SEK ([Electrokit](https://www.electrokit.com/produkt/raspberry-pi-5-8gb/)) |
| Pi 5 4GB | NOT FOUND | - | Official +$25 from 1 Apr 2026 ([Gigazine](https://www.gigazine.net/gsc_news/en/20260402-raspberry-pi-price-increases)) |
| 27 W USB-C PSU | about 119 kr (EUR 15.92 incl. VAT, DKK/EUR peg 7.46, ESTIMATE) | [raspberrypi.dk](https://raspberrypi.dk/en/product/raspberry-pi-power-supply-usb-c-eu-5v-5a-white/?clang=en) | In stock; updated 17 Oct 2026 |
| microSD SanDisk High Endurance 64 GB | 202 kr | [Proshop](https://www.proshop.dk/Hukommelseskort/SANDISK-High-Endurance-microSDSD-100MBs-64GB/2773175) | Out of stock |
| M.2 HAT+ (SSD option) | DK NOT FOUND; official "from $12" | [raspberrypi.com](https://www.raspberrypi.com/products/m2-hat-plus/) | - |
| SSD, case, shipping | NOT FOUND | - | - |
| **Found subtotal** | **about 1,776 kr** | ESTIMATE | Excludes case, shipping |

Real money, not part of the virtual 5,000 DKK (D1, D17).

## Power and electricity

- Pi 5 headless idle about 3.0 W; 4-core stress about 8.8 W ([raspberry.tips](https://raspberry.tips/en/faq/raspberry-pi-power-consumption-update-2026-all-models-compared), third party, undated; official NOT FOUND).
- Electricity tax 2026-27: 1 ore/kWh incl. moms, down from 90 ore in 2025 ([Bolius](https://www.bolius.dk/elafgiften-saenkes-til-et-minimum-i-2026-og-2027-saa-meget-betyder-det-for-din-elregning-100110)).
- Household average 2.61 kr/kWh incl. moms (12 months to Oct 2025, Forsyningstilsynet via Bolius). Current 2026 average NOT FOUND.
- Yearly, 24/7: idle (26 kWh) **44-69 kr**; ESTIMATE 4 W average (35 kWh) **59-92 kr**; full load 8.8 W (77 kWh) **130-201 kr**.

## Market data (public, no key)

| Venue | REST limit | WebSocket | Notes |
|---|---|---|---|
| [Coinbase Exchange](https://docs.cdp.coinbase.com/exchange/introduction/rate-limits-overview) | 10 req/s per IP, burst 15 | 8 req/s per IP; 100 client msgs/s | Undated |
| [Kraken](https://docs.kraken.com/api/docs/guides/spot-rest-ratelimits) | Counter max 15 (Starter), decays 0.33/s | wss://ws.kraken.com/v2 | Undated |
| [Bitvavo](https://docs.bitvavo.com/docs/rate-limits/) | 1,000 weight/min per IP; 15-min block if exceeded | 5,000 msgs/s per session | Ticker weight NOT FOUND |
| [Binance](https://developers.binance.com/docs/binance-spot-api-docs/websocket-api/rate-limits) | REST NOT FOUND; 300 WS connections per 5 min per IP | - | Denmark status NOT FOUND ([Cointelegraph](https://cointelegraph.com/news/binance-eu-service-limits-july-1-mica-effect)) |

- [Telegram Bot API](https://core.telegram.org/bots/faq): about 1 msg/s per chat. Free.
- [Tailscale Personal](https://tailscale.com/pricing): free, up to 6 users, **non-commercial use only**.

## Human steps (D3)

- Once: connect Pi; flash OS; paste Telegram token; log in to Tailscale. Recurring (ESTIMATE): check logs monthly.

## Time to first live results (ESTIMATE)

Hardware and OS 2-3 hours; code (collector, paper broker, benchmark, status page) 1-2 days. Live numbers 3-4 days after the Pi arrives.

## Open questions and conflicts

- No direct conflict with D1-D18.
- Is a week-1 run on TrueNAS or Windows PC (D15) acceptable?
- Tailscale Personal is non-commercial only; a paid plan is needed if the simulator earns money (D5). Price NOT FOUND.
