# S2-r1: Danish crypto tax and MiCA exchanges (research 2026-10-18)

Not tax advice. Binding answers from SKAT (bindende svar) are the route for a specific case.

## Q1. Gains: income type, rate, taxable events

- **Answer:** Speculative gains are personal income (PSL § 3(1)), not capital income. They are taxed like salary, without the 8% AM-bidrag. The page says the tax can reach "op til 53 %", depending on personal circumstances. A gain is taxed only when realised (sale or exchange). Unsold holdings are not taxed. Speculation requires intent to resell for profit at acquisition (SL § 5(1)(a)).
- **Coin-to-coin:** Taxable. Paying with one crypto for another is a disposal of the first (and an acquisition of the second).
- **Sources:** skat.dk FAQ, modified 24 Aug 2026, https://skat.dk/borger/aktier-og-andre-vaerdipapirer/skat-paa-krypto-kend-reglerne-saa-du-undgaar-et-skattesmaek/spoergsmaal-og-svar-om-kryptovaluta ; skat.dk calculation page, modified 14 Oct 2026 per page metadata, https://skat.dk/borger/aktier-og-andre-vaerdipapirer/skat-paa-krypto-kend-reglerne-saa-du-undgaar-et-skattesmaek/beregn-og-oplys-gevinst-og-tab-paa-krypto ; Den juridiske vejledning 2025-1 (JV), C.C.2.1.3.3.3 https://tax.dk/jv-2025-1/cc/C_C_2_1_3_3_3.htm and C.C.2.1.3.3.5.2 https://tax.dk/jv-2025-1/cc/C_C_2_1_3_3_5_2.htm
- **Confidence:** High on income type and taxable events. Medium on the rate: the page gives only "op til 53 %" and I did not check the 2026 tax scale. JV 2025-1 is not the 2026 version.

## Q2. Losses: deductibility and asymmetry

- **Answer:** A speculative loss is a ligningsmæssigt fradrag from taxable income. It cannot be deducted within personal income and cannot offset other personal income (JV C.C.2.1.3.3.3, citing SKM2024.160.LSR). It needs a speculative purchase, a real disposal, and a trading loss. Rug pulls, scam transfers and exchange bankruptcies were not deductible (SKM2023.586.SR, SKM2021.513.SR, SKM2024.25.SR).
- **Value:** skat.dk states "Du kan få fradrag for tab, hvilket udgør 26 % af dit tab." The same page gives the top gain rate as up to 53%. The page does not explain how the 26% relates to the rubrik 58 entry.
- **Netting:** Each trade is assessed separately. The one exception: if you hold none of a coin, buy several units, and sell them in batches within the same income year without buying more in between, losses can be netted against gains. Netting across different coins is not allowed.
- **Reporting:** Gains go in rubrik 20 ("Anden personlig indkomst"). Losses go in rubrik 58 ("Øvrige lønmodtagerudgifter").
- **Asymmetry:** Yes, per the sources. Gains are taxed at personal-income rates trade by trade. Losses get a fradrag at the stated 26% value, with narrow netting. No general symmetry rule exists.
- **Sources:** skat.dk calculation page (above); skat.dk FAQ (above); JV C.C.2.1.3.3.3 and C.C.2.1.3.3.5.2 (above)
- **Confidence:** High on the no-netting rule. Low on the 26% value (conflict to resolve).

## Q3. Calculation, records, reporting, DAC8

- **Method:** The calculation page says FIFO applies "som udgangspunkt", with all wallets and exchanges combined per coin. Average cost is not mentioned as accepted. The JV says FIFO applies separately per crypto type, but it names aktiv-for-aktiv (SKM2019.67.SR) as the main rule and FIFO as the exception where units cannot be identified. These are inconsistent. Conflict to resolve.
- **Records:** Keep orders, purchases, sales and payments for every income year with trading. An undocumented deposit gets a cost basis of 0 kr, so the whole sale is taxed (SKM2024.219.SKTST). Documented internal transfers are excluded from FIFO.
- **Reporting:** Årsopgørelse deadline 1 May of the year after the sale. Forskudsopgørelse fields: 250 (gains) and 449 (losses). Earlier unreported years must be corrected.
- **DAC8:** Lov nr. 409 af 29.04.2025 amends skatteindberetningsloven. Crypto reporting (§ 23a) applies from 1 Jan 2026, with some provisions from 1 Jan 2028 (lovguiden: https://www.lovguiden.dk/loven/lov-nr-409-af-29-04-2025). KPMG (17 Oct 2025): reporting applies to transactions from 1 Jan 2026, first exchange 2027 (https://kpmg.com/us/en/taxnewsflash/news/2025/10/denmark-reporting-obligations-crypto-service-providers.html). Initial reporting is due January 2027 (regfollower: https://regfollower.com/denmark-adopts-dac8-crypto-asset-reporting-rules/).
- **Scope conflict:** Lovguiden says the minister "may require" CASP reporting. KPMG says it covers CASPs operating in Denmark and those serving users domiciled in Denmark. This matters for exchanges outside Denmark.
- **Confidence:** High that DAC8 is live from 2026 transactions. Medium on scope.

## Q4. Sole trader (enkeltmandsvirksomhed) and næring

- **Answer:** Frequent trading does not by itself make it næring. The test is a professional, extensive and systematic activity. Education and experience count (SKM2024.287.LSR: a very large number of trades did not change the result). SKM2023.170.LSR: high-volume trading in 2017–18 was speculation. SKM2021.291.SR: a "Nej" to business status.
- **If næring:** SL § 4 applies, gains and losses are netted (nettoprincip), and trading stock is assessed case by case. Speculation is settled trade by trade, and annual trades cannot be combined (JV C.C.2.1.3.3.5.4).
- **Company holding crypto:** Shareholders of a company that invests in crypto were not business traders (SKM2022.300.SR).
- **NOT FOUND:** Sole-trader mechanics, AM-bidrag, VAT and bookkeeping for crypto. JV 2025-1 C.C.2.1.3.3.5.4 has no sole-proprietorship section.
- **Sources:** https://tax.dk/jv-2025-1/cc/C_C_2_1_3_3_5_4.htm ; https://www.lovguiden.dk/dokument/skatteraadet/31-05-2021-naeringsvurdering-af-personlig-handel-med-kryptovaluta
- **Confidence:** Medium on the test. Low on sole-trader treatment.

## Q5. MiCA-authorised exchanges, fees, warnings

- **Denmark:** Competent authority is Finanstilsynet. The MiCA transitional period ended 1 July 2026 (https://schjodt.com/news/mica-transitional-period-comes-to-an-end). The lovguiden timeline page failed to load and was not retried.

| Exchange | MiCA status | Spot maker / taker, lowest tier | Source |
|---|---|---|---|
| Kraken | Ireland, Central Bank of Ireland (tech-insider, Jul 2026); not seen in the ESMA extract | 0.40% / 0.80% (USD schedule, undated) | https://www.kraken.com/features/fee-schedule |
| Coinbase | Luxembourg, CSSF; register entry 20/06/2025 | 0.25% / 0.50% EU/UK entry rate (announced 16 Sep 2026) | https://www.coinbase.com/blog/were-lowering-fees-for-many-active-traders-on-coinbase-advanced |
| Bitvavo | Netherlands, AFM (tech-insider); register row truncated | 0.15% / 0.25% (EUR markets, €0+ tier, undated); SEPA deposit free | https://www.bitvavo.com/en/fees |
| Bitpanda | Germany BaFin, also Austria FMA and Malta MFSA (tech-insider) | 0.10% / 0.15% from aggregator only (page blocked) | https://tradersunion.com/brokers/crypto/view/bitpanda/fees/ |
| Binance | Not authorised. Withdrew its Greek application 24 Jun 2026. From 1 Jul 2026 it stopped new registrations and named FR, IT, ES and PL as affected | NOT FOUND | https://www.crowdfundinsider.com/2026/06/288066-binance-to-limit-crypto-services-for-eu-users-after-withdrawing-mica-license-bid-in-greece/ |

- **Danish CASPs:** The ESMA extract lists 7 Danish entities: GC Exchange, Penning Financial Services, Northstake, Lunar Block, SafeLynx, Coinify and Januar (dates Sep 2025 to Jun 2026). Schjodt names 4. Conflict. Source: https://www.moneyviz.it/it/interim-micar-register/casps.md (truncated, no snapshot date).
- **Finanstilsynet warnings:** The search turned up a Danish warning on Bybit (Sep 2024, financial instruments). The page did not load. Tech-insider lists Bybit EU as MiCA-authorised (Austria FMA). Conflict to check. A full Danish exchange-warning list: NOT FOUND.
- **Confidence:** Medium on Coinbase, Bitvavo and Danish CASP entries. Low on Kraken, Bitpanda and the Bybit warning. Check https://www.esma.europa.eu registers directly before relying on any of them.

## Conflicts with Ground Truth

- No Ground Truth decision (D1, D4, D5, D6, D13, D14, D16, D17) is contradicted.
- D14 is supported: DAC8 reaches users domiciled in Denmark.

## IMPROVES

- Model the after-tax result trade by trade in the paper-trading simulation, with FIFO and a loss-deduction scenario at 26% and at 53%.
- Ask SKAT for a binding answer on the 26% loss value before any live trading.

## Open questions

1. Is the 26% loss value correct for rubrik 58, and what is its marginal effect?
2. FIFO versus aktiv-for-aktiv: which applies?
3. Sole-trader treatment: AM-bidrag, VAT, bookkeeping.
4. Does Binance serve Danish residents after 1 Jul 2026?
5. Bitpanda official fees, Coinbase retail fees, and Kraken EUR fees.
6. Current JV version (2026-1) not checked.
