# Nye strategier at teste i simuleringen (S3, 2026-10-19)

Grundlag: 10 Haiku-vinkler med websøgning, derefter Opus som kritiker, syntetiserer og uddyber. Alle råfiler ligger i samme mappe (`S3-lens01..10-*.md`, `CONSOLIDATED-S3-v1.md`, `S3-opus-critic.md`, `S3-opus-synth.md`, `S3-opus-expand.md`). Bindende rammer: `SEED.md` (spot, ingen gearing, Pi Zero stdlib, Kraken EUR, dansk realisationsskat).

## Kort konklusion
De 22 idéer fra første runde koger ned til tre ægte nye ting: et langsommere trendfilter, risikostyret positionsstørrelse og dyk-vægtet opsparing. Resten er varianter af de arme, der allerede er planlagt. Al kryptoforskning, vi fandt, viser det samme mønster: filtrene giver lavere drawdown og bedre Sharpe, men lavere rå afkast end buy-and-hold. Ingen kilde viser netto-overskud efter Kraken-gebyrer (0,4-0,8 %) og dansk skat.

## Top 4 nye arme (rangeret)

### 1. Volatilitetsstyret BTC (risk-targeting, maks 100 %)
- Regel: andel BTC = min(1, 40 % / realiseret vol), vol = EWMA med 60 dages tyngdepunkt (Moskowitz-Ooi-Pedersen 2012 standard). Tjek månedligt; handl kun når målandelen har flyttet sig ≥ 10 procentpoint. Resten i EUR.
- Handler/år: ca. 3-8. Data: Kraken daglige lukkekurser.
- Hvad den tester: om man skal styre *hvor meget* man ejer, ikke kun *om* man ejer. Alle planlagte arme er alt-eller-intet.
- Evidens: Zarattini/Pagani/Barbon "Catching Crypto Trends" (SSRN 5209907, 2025, working paper): BTC 2015-2025, Sharpe 1,56, max DD 19 %, men med op til 200 % gearing og kun 0,10 % gebyr. Ved 0,50 % gebyr falder afkastet næsten til det halve. Intet resultat med 100 %-loft er publiceret. Tillid: middel for lavere drawdown, lav for at slå buy-and-hold.
- Fejlmode: ejer typisk kun 40-70 % BTC i tyrmarked og halter efter.
- Skat: hver nedjustering er et salg og dermed en realisation.
- Indsats: ca. 30 linjer Python.

### 2. Faber 10-måneders gennemsnit (månedligt trendfilter)
- Regel: sidste handelsdag i måneden: luk > gennemsnit af de 10 seneste månedslukninger → hold BTC, ellers EUR.
- Handler/år: 1-4 round trips.
- Hvad den tester: om et langsomt, månedligt filter klarer sig bedre efter skat end de planlagte daglige/4t-arme.
- Hvorfor den er stærk: parameteren blev fastlagt i 2007, før Bitcoin fandtes, så den er ægte out-of-sample på krypto (den eneste kandidat, kritikeren godkender som "bekræftende" arm). Evidens: Faber 2007 (aktier, brutto). Detzel m.fl. (Financial Management 2021) på BTC 2010-2017: drawdown fra -89 % til ca. -68 %, men lavere afkast end buy-and-hold. Tillid: middel for retning, lav for netto-fordel.
- Indsats: ca. 20 linjer.

### 3. Krak-nødbremse på en buy-and-hold-kerne
- Regel: hold BTC; sælg alt når lukkekursen er 25 % under 365-dages top; køb tilbage når lukket er over 200-dages gennemsnit; nulstil toppen ved genkøb.
- Handler/år: 0-2.
- Hvad den tester: direkte PASS-kravet om drawdown og ≥ 30 % fald.
- Advarsel: -25 % er valgt ud fra BTC-grafer, ikke fra en ældre kilde, så den er "in-sample". Ingen primær backtest fundet. Kun som udforskende arm.
- Indsats: ca. 25 linjer.

### 4. Dyk-vægtet DCA (kun køb)
- Regel: ugentlig opsparing; køb 2x beløbet når kursen er > 20 % under 200-dages gennemsnit, 1x når den er 0-20 % under, 0x når den er over (pengene venter i EUR).
- Sælger aldrig, så ingen skat før exit. Sammenlignes med almindelig ugentlig DCA, ikke med engangskøb.
- Tillid: lav-middel. Indsats: ca. 20 linjer.

## Ændring i stedet for ny arm
- 90-dages momentum → 12-måneders momentum. 12 måneder er lærebogs-standarden (Moskowitz-Ooi-Pedersen 2012). "Dual momentum" og "månedlig rotation" fra brainstormen er reelt samme arm.

## Måske senere
- BTC/ETH/SOL-rotation: hold den bedste 12-måneders performer, EUR hvis alle er negative (≤ 12 handler/år).
- 60/40 BTC/EUR med 10-points bånd (tæt på den planlagte 50/50-arm).
- Volatilitetsskaleret 12-måneders momentum med 2012-standarderne.
- "Chop-filter" (efficiency ratio) oven på Donchian. Ingen kilde.

## Droppes (kort grund)
- Grid-bots, market making, arbitrage: gebyrer og skat æder kanten; kræver ordrebog/hastighed.
- Funding-rate carry: kræver futures (ikke spot).
- Kortsigtet mean reversion (RSI-2, Bollinger, MACD, Ichimoku): brutto ca. 0,013 % pr. handel mod 0,1-0,8 % i omkostning (arXiv 2608.21888); 0 af 13 klassiske regler bestod i en uafhængig test.
- Halving-timing, 200-ugers gennemsnit, MVRV, Fear & Greed, kalender/månedseffekter: parametre fundet ved at kigge på BTC's egen historik (overfitting), og/eller ingen gratis historiske data.
- Ordrebogs-signaler: ingen gratis historisk ordrebog, så ingen ærlig backtest.
- Ugentlig cross-sectional momentum blandt top-10 coins: 150+ handler/år, skatten dræber den.

## Beslutninger der skal tages før reglerne låses (D22)
1. Kravet "≥ 100 lukkede handler" kan ingen lavfrekvent arm nå. Det rammer også de planlagte EMA 50/200, momentum og 50/50, så kun Donchian 4t kan bestå, og den har den værste skatteprofil. Forslag (kritikeren): for lavfrekvente arme i stedet ≥ 20 round trips, skal vinde i hvert ≥ 30 %-fald for sig, skal stadig vinde uden sin bedste enkelthandel, og skal slå 10.000 tilfældige strategier med samme antal handler. Ellers er dommen INCONCLUSIVE.
2. Hvad betyder "slår buy-and-hold"? Højere afkast efter skat, eller samme afkast med mindre drawdown? Al evidens peger på, at filtrene kun kan vinde på det sidste.
3. Flere arme gør det sværere at bestå (Bonferroni). Forslag: maks 6 "bekræftende" arme med Holm-korrektion; resten markeres som udforskende og kan aldrig give PASS alene.

## Data-tjek
- Kraken API: første XBTEUR-handel 2013-09-10, så 2014-, 2018- og 2022-faldene kan dækkes. Om bulk-arkivet (OHLCVT til 30. juni 2026) indeholder XBTEUR, er ikke bekræftet.
- Binance EUR-par først fra januar 2020, for kort alene.
- Kraken minimumsordrer (BTC 0,0001, ETH 0,01; Kraken support 6. okt 2026) er ikke et problem ved 5.000 kr.
- Fælles infrastruktur for alle arme: kun EUR som kontantben (ingen USDT), spread/dybde-vagt før fill, FIFO-skattemotor der tvangssælger alt ved testens slutning (også for buy-and-hold).
