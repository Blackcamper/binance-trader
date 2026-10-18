# S2 lens 07: constraint spotter

**Bottom line:** Only spot, rule-based, low-trade strategies pass D1, D3, D4 and D16. Most sales are taxed as personal income, so trade count drives tax.

## 1. Danish tax (read 18 Oct 2026)

- **Crypto is property, but speculation is the default.** Sale gains are tax-free only if not speculation or business (SL §5(1)(a)). Skatterådet treats crypto "as a rule" as speculation (SKM2024.25.SR). Source: https://tax.dk/jv/cc/C_C_2_1_3_3_5_2.htm
- **Speculation gains are personal income** (PSL §3(1)), not the 27/42% share scale. Intent, not holding period, is the test.
- **Bundskat 12.01% (2026):** https://skat.dk/hjaelp/bundskat-mellemskat-topskat-og-toptopskat. Combined marginal rate: **ESTIMATE 37–52%**, not verified.
- **Losses:** deductible only from a real sale. No deduction for rug-pull or fraud losses (SKM2023.586.SR). Netting against other income: **NOT FOUND**, summaries conflict.
- **Each swap is a realisation** (SKM2023.306.SR). Partial sales use FIFO per coin. Undocumented acquisitions cost 0 kr.
- **Staking and rewards** are taxed on allocation at value (SKM2023.68.SR), not on sale.
- **Professional trading** can be business income (SL §4). Threshold: **NOT FOUND**.
- **Futures/CFD-type contracts** fall under lagerprincip as capital income (SKM2022.300.SR, as summarised). Futures specifically: **NOT FOUND**.
- **DAC8:** transactions reportable from 1 Jan 2026, first exchange 2027. Source: https://kpmg.com/us/en/taxnewsflash/news/2025/10/denmark-reporting-obligations-crypto-service-providers.html

## 2. Return needed (computed)

- 5,000 to 200,000 DKK = x40, or +3,900% in 12 months.
- Monthly equivalent: 40^(1/12) = 1.360, so **+36.0% every month, pre-tax**.
- Gross needed if gain is taxed once at the end, rate t: (200,000 - 5,000t)/(1 - t). At t=0.40: 330,000 DKK (66x). Range about 63x to 82x for t=0.37 to 0.52 (ESTIMATE rates).
- Realistic benchmark returns: **NOT FOUND**. Only loss-rate evidence: BIS working paper, via https://www.advisor.ca/investments/market-insights/most-retail-investors-lose-on-bitcoin-trades-bis/ (14 Nov 2022). It estimates 73–81% of retail investors lose on initial bitcoin purchases. No day-trader figure.
- **Verdict:** nothing sourced supports x40. Use monthly after-fee, after-tax return as the sim metric.

## 3. Fees and access

- Kraken Pro Tier 1 (undated page): maker 0.40%, taker 0.80%. Instant/recurring buys: 1%. Source: https://www.kraken.com/features/fee-schedule
- Taker round trip = 1.6% = 80 DKK on 5,000 DKK fully deployed (arithmetic). Grid spacing must beat round-trip fee plus slippage (slippage: NOT FOUND).
- MiCA list (aggregator, 17 Oct 2026): 29 licensed exchanges cover Denmark, including Kraken, Coinbase, Bitpanda, Bitvavo, eToro. Binance absent; Danish availability **NOT FOUND**. Source: https://defillama.com/mica/denmark
- Kraken permits bots, no stated restrictions (8 Aug 2025): https://support.kraken.com/ar/articles/360001373983

## 4. Approach verdicts

| Approach | Breaks | Verdict |
|---|---|---|
| Manual day trading | D3 (human judgement per trade); D14 (every sale taxed) | DROP |
| Grid bot (spot) | D3 partly (range reset is a human step); D14 many realisations; fee hurdle | SIM-ONLY |
| DCA bot (spot) | None on Pro fees; recurring product at 1% breaks D13 fee assumption | KEEP (control) |
| Trend bot (spot, long-only) | D14 whipsaw tax drag; 0.80% per flip | KEEP |
| Arbitrage | D1 (capital split); D14 (transfers, swaps); 0.80% per leg | SIM-ONLY (sim overstates fills) |
| Copy trading | D3 (leader choice); D16 if CFD (terms NOT CHECKED); D13 selection bias | SIM-ONLY |
| Staking | D14 (tax on allocation, cash needed); lock-ups | SIM-ONLY |
| Futures / leverage | D16 (live); possible lagerprincip | SIM-ONLY, never live |
| Memecoin sniping | D4 (rug pulls, scams); D14 (losses not deductible) | DROP |
| Commercial bot | D1 (paid from the 5,000); D4 (unknown code, unverified claims) | DROP |

**Passing set for the sim:** buy-and-hold control (added), DCA control, trend-following spot bot, grid bot (sim only).

## 5. Conflicts and improvements

- CONFLICTS WITH: D1, if a commercial bot is bought from the 5,000 DKK.
- CONFLICTS WITH (tension): D5 x40 stretch versus "realism over hype".
- IMPROVES: buy-and-hold control carries notional tax at period end, else deferred tax flatters it.
- IMPROVES: book tax per realisation (FIFO per coin); tax-reserve line on the phone dashboard.
- IMPROVES: fill at bid/ask with taker/maker fees, not mid price; flag high trade counts for a business-status check.
- Unavoidable human steps (D3): KYC, bank transfers, API keys, withdrawal approvals, annual SKAT declaration.

## 6. Open questions

- Exact marginal rate and AM-bidrag applicability for speculation gains.
- Loss netting: one summary says SKM2024.160.LSR bars offset against other personal income. Confirm via binding answer (bindende svar).
- Futures under lagerprincip; business-status threshold; Kraken public data reachable from a Danish Pi (untested); D13's "meaningful period" undefined.
