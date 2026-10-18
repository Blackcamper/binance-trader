# S2 round 2: retail trading outcomes evidence (searched 2026-10-18)

## Q1 Academic day-trader outcomes
**Answer:** Taiwan: only about 13-15% of day traders earn abnormal returns net of fees in a typical year, and under 1% (top 1,000 of about 360,000 a year) are reliably profitable. Brazil: of 19,646 people starting index-futures day trading in 2013-15, 7.9% lasted 300+ sessions; of those, 3.0% had positive average net daily returns and 1.1% beat the Brazilian minimum wage.
- Barber, Lee, Liu, Odean, J. Financial Markets 18 (2014): working paper https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf (May 2011); journal record https://ideas.repec.org/a/eee/finmar/v18y2014icp1-24.html
- Chague, De-Losso, Giovannetti, "Day Trading for a Living?": secondary summary https://www.cxoadvisory.com/investing-expertise/day-trading-a-bust/ (June 2020 SSRN update).
- **Confidence:** High for "under 1% persistent" (journal-published). Medium for Brazil: working paper, read only via a summary. The Taiwan paper gives 13% in one section and 15% in another.
- Ryu (2012), KOSPI 200 futures, Investment Analysts Journal: domestic individuals "face substantial losses from day trading"; no percentages. https://doi.org/10.1080/10293523.2012.11082543 **Confidence:** Medium.
- "97% lost money" is not in the source; it is an inference from 3.0%.

## Q2 Crypto retail outcomes
**Answer:** BIS estimate: "an estimated 73-81% of retail investors have likely lost money on their initial investment" (2015-22, crypto app users in 95 countries). It is a back-of-envelope figure. Bloomberg describes the 81% as a hypothetical $100 monthly purchase from install.
- BIS Working Paper 1049 (14 Nov 2022): https://www.bis.org/publ/work1049.pdf. Bloomberg (Nov 2022): https://news.bloombergtax.com/crypto/about-75-of-retail-buyers-of-bitcoin-lost-money-bis-study-says
- BIS Bulletin 69 (20 Feb 2023): https://www.bis.org/publ/bisbull69.htm says only "a majority of crypto app users in nearly all economies made losses." No percentage.
- **Confidence:** Low-Medium. Estimate, not measured. Conflicts: "about 75%" vs 73-81% vs 81%; the bulletin's period is Aug-Dec 2022 (abstract) or Aug 2015-Dec 2022 (takeaways). RePEc lists an IMF Economic Review 74(2) version (June 2026), https://ideas.repec.org/p/bis/biswps/1049.html, not checked.
- FCA Cryptoasset Consumer Research 2025 Wave 6 (fieldwork 5 Aug-2 Sep 2025): https://www.fca.org.uk/publication/research-notes/cryptoasset-consumer-research-2025-wave-6.pdf. 8% of UK adults hold crypto (12% in 2024). Of holders, 62% report a net gain and 12% a net loss on paper value (979 owners). **Confidence:** Medium: online survey, unrealised values, rising-market year. Direction conflicts with BIS 2015-22 data; the period explains it.
- Cong, Li, Tang, Yang, "Crypto Wash Trading" (NBER w30783, Dec 2022; Management Science 2023): https://www.nber.org/papers/w30783. Wash trading "averaged over 70% of the reported volume" on unregulated exchanges. **Confidence:** High. Volume-based fee tiers and rankings from such venues are unreliable.
- ESMA: NOT FOUND for retail crypto outcomes. Searches returned 2018 CFD/binary-option rules and joint ESA warnings.
- Finanstilsynet (Denmark): NOT FOUND. Results were Norway's Finanstilsynet warnings about unauthorised platforms.

## Q3 Bot strategies (grid, DCA, trend)
**Answer:** No independent, peer-reviewed study of retail bots net of fees against buy-and-hold was found.
- Chen, Chen, Jang, arXiv:2506.11921 (13 Jun 2025), https://arxiv.org/abs/2506.11921: dynamic grid backtest, BTC/ETH on Binance, Jan 2021-Jul 2024. Fee = 0.08%, which is OKX's maker fee, not Binance's; no slippage. IRR "as high as 60-70%"; no buy-and-hold IRR in text; ETH not substantially above buy-and-hold; authors credit the bull market. **Confidence:** Low (preprint, backtest only).
- Barbon, "Catching Crypto Trends" (working paper, rev. 9 Apr 2025), https://abarbon.com/papers/catching-crypto-trends: trend strategy, Sharpe above 1.5, 10.8% alpha vs BTC, "net-of-fees" per abstract. Fee assumption and buy-and-hold figures not in fetched text. **Confidence:** Low.
- Vendor pages (Gainium, Spark.money, Forklog overviews): marketing, no verified track records. Not evidence.

## Q4 Round-trip cost, spot, lowest tier (pages undated)
- Binance: 0.10% maker/taker, 0.075% with BNB, https://www.binance.com/en/fee/schedule. Not in DeFiLlama's list of 29 MiCA providers for Denmark (17 Oct 2026), https://defillama.com/mica/denmark. Availability to Danish residents unverified.
- Bitvavo (EUR pairs): 0.15% maker / 0.25% taker, https://bitvavo.com/en/fees. MiCA-listed for Denmark.
- Kraken Pro: 0.40% maker / 0.80% taker (0.30/0.60 from $2.5K), https://www.kraken.com/features/fee-schedule. MiCA-listed.
- Spread: Kaiko (page dated 2023, data about May 2023), https://www.kaiko.com/resources/a-cheatsheet-for-bid-ask-spreads: BTC/ETH USDT spreads "extremely tight"; SOL/XRP 8+ bps on TUSD pairs. No current typical figure.
- Coinbase: NOT FOUND (fee pages unreadable). Slippage: NOT FOUND.
- Taker round trip: Bitvavo about 0.50% + spread; Kraken about 1.60%; Binance 0.20%. **Confidence:** Medium (official pages, undated).
- Fee dominance = trades per month x round-trip cost. At 0.5%: 4 round trips a month = 2%/month; 20 = 10%/month. Fees dominate when expected gross gain per round trip is below round-trip cost.

## Q5 Base rate: 5,000 to 200,000 DKK in 12 months
- Required: 40x = +3,900% in a year, about 36% compounded per month (40^(1/12) = 1.36).
- Base rate: NOT FOUND as hard data. The persistence studies (under 1% persistent; 1.1% beat minimum wage over 300+ sessions) imply such results are extremely rare. **Confidence:** Medium on direction, Low on rate.

## Conflicts and improvements
- CONFLICTS WITH: D5. The x40 stretch has no support in the evidence; treat it as a lottery, not a target.
- No conflict found with D1, D4 or D16.
- IMPROVES: Use the 300-session persistence rule from Chague as the minimum window for D13. Set a numeric bar: beat buy-and-hold after fees and tax over 300+ sessions, in both up and down markets.
- IMPROVES: Realisation-based tax favours buy-and-hold (tax deferred). The D13 test must compare realised, after-tax results.
- IMPROVES: Use MiCA-licensed venues for simulation data and fee assumptions only.
- Danish tax (Low confidence): financer.dk (13 Jul 2026), https://financer.dk/krypto/skat-af-kryptovaluta/, says gains are personal income at 37-53% and about 26% of losses are deductible. tax.dk (2026-2 guide) did not confirm the rates; 27%/42% not found. Verify with SKAT before using any tax figure.

## Open questions
- Coinbase fees; current spread and slippage data.
- Binance availability in Denmark.
- Journal status of Chague et al.; IMF Economic Review version of BIS WP 1049.
- Hard base rate for 12-month multiples.
- ESMA and Danish Finanstilsynet retail outcome data.
