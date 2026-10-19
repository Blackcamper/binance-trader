# S2-r3: Danish crypto tax, the tax return, and what it does to profit (research 2026-10-19)

Not tax advice. Follow-up to S2-r1 that resolves its open questions. Primary sources: skat.dk
"Beregn og oplys gevinst og tab på krypto" (modified 2026-10-14), skat.dk Q&A on crypto, Den
juridiske vejledning 2026-2 C.C.2.1.3.3.5.2 (tax.dk mirror), skm.dk rates 2026, skat.dk DAC8 page.

## Rules that apply to income year 2026

| Topic | Rule | Confidence |
|---|---|---|
| Gain | Personal income, no AM-bidrag. Sum of all gains goes in **rubrik 20 "Anden personlig indkomst"**. | High |
| Loss | Ligningsmæssigt fradrag only (Supreme Court SKM2025.541.HR). Sum of all losses goes in **rubrik 58 "Øvrige lønmodtagerudgifter"**. skat.dk: "Du kan få fradrag for tab, hvilket udgør 26 % af dit tab." Worth kommuneskat + kirkeskat only, not bundskat/mellemskat/topskat. | High |
| Netting | "Du skal opgøre gevinst og tab hver for sig." No netting between trades or coins. Only exception: held none, bought in one go, sold in batches in the same year with no buys in between. | High |
| Method | FIFO per coin, all exchanges and wallets as one pool. Aktiv-for-aktiv (SKM2019.67.SR) only applies if units can be identified, which fungible crypto cannot. Average cost is not allowed. | High |
| Fees | Trade fees are added to the cost and deducted from the sale price (SKM2022.300.SR). Transfer fees and tax software are not deductible. | High |
| DKK | Amounts in DKK. No named rate; use the day's rate (Nationalbanken/ECB). Swap: same value as sale price and new cost. | Medium |
| Swap coin-to-coin | Counts as a sale. | High |
| Small gains | No minimum. | Medium-high |
| EUR cash on exchange | Kursgevinstloven, capital income, 2,000 kr net bagatelgrænse per year. EUR is pegged, so in practice nil. | Medium-high |
| Undocumented cost | Cost is set to 0 kr, the whole sale is taxed. | High |
| Deadline | Årsopgørelse 1 May the year after (1 May 2027 for 2026). Forskudsopgørelse felt 250 (gain) and 449 (loss). | High |
| DAC8 | Exchanges report 2026 trades by 31 Jan 2027 (Kraken via Ireland). Not pre-filled; SKAT uses it to check. You still type rubrik 20/58 yourself. | High / medium |
| Næring | A bot trader is still a speculator in practice (SKM2023.170.LSR, SKM2022.300.SR). | Medium-high |

### Marginal rate on a gain, 2026 (kommuneskat 25.0 %, kirkeskat 0.7 %)

| Personal income | Rate on 1 extra kr of gain |
|---|---|
| Below 641,200 kr (e.g. salary 400,000) | ~37.7 % |
| 641,200 to 777,900 kr (mellemskat) | ~45.2 % |
| Above 777,900 kr (topskat) | ~52.7 % |
| Above 2,592,700 kr (toptopskat) | ~57.7 % |

A big gain can push income into the next bracket. Config scenarios `low` 37 % and `high` 53 %, loss 26 %, match this.

## Open points

1. **Rubrik 58 floor.** Ordinary employee expenses in rubrik 58 have a bundfradrag (about 7,000 kr). Not confirmed whether it also cuts crypto losses. If it does, small yearly losses are worth 0. Ask SKAT before going live.
2. **Law change coming.** Lovprogram 2026-27 lists a crypto bill for February 2027 to "gøre op med den asymmetriske beskatning af kryptoaktiver" (PwC summary). Skattelovrådet's 2024 model was lagerbeskatning as kapitalindkomst with loss netting. Earliest effect income year 2027. Rerun this note when the bill is out.
3. Binance stopped new EU sign-ups and new spot orders after 1 Jul 2026. Download any old Binance history now.

## What it does to profit

Gains are taxed at 37.7-52.7 % but losses only save ~26 %, and they cannot be netted. So after
tax, 1 kr of loss costs 0.74 kr while 1 kr of gain only keeps 0.62 kr (low) or 0.47 kr (high).
To break even after tax the year's gains must be:

- **1.17 x the losses** at 37 % (`low`)
- **1.57 x the losses** at 53 % (`high`)

Example: a trend strategy that wins 40 % of trades at +12 % and loses 60 % at -4 % makes +2.4 % per
trade before tax. After tax that is +1.2 % (low) or +0.5 % (high). With symmetric tax it would have
been +1.5 % / +1.1 %. Buy-and-hold has one sale and no losing trades, so it barely feels the
asymmetry. Strategies with many small losses (Donchian, EMA cross) are hit hardest, and the
comparison against buy-and-hold must be after this tax. The simulator does that now.

## How the simulator uses this

- `pitrader/ledger.py`: each sale is one disposal (FIFO cost incl. buy fee, proceeds after sell
  fee). Tax = sum of gains x gain_rate minus sum of losses x loss_value_rate. No netting.
- `pitrader/tax.py` + `python3 -m pitrader skat [--year 2026] [--strategy id] [--csv fil.csv]`:
  rubrik 20 and 58 amounts per strategy, estimated tax, every sale with dates, open holdings.
- `status.json` has `tax_return` per strategy for the current year, so Claude can answer from the
  status file.
- Simplifications: fixed EUR/DKK from the config, each strategy is its own pool (in real life one
  person has one FIFO pool per coin across everything), the narrow netting exception is not used
  (conservative), the rubrik 58 floor is not modelled.
