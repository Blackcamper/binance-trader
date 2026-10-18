# Skeptic lens: honesty rules for the Pi paper-trading test

**Bottom line:** 14 days can only catch bugs. A script prints the verdict, and a PASS needs about two years of data.

## 1. Is 14 days meaningful?

No. Daily crypto moves are roughly 3% (ESTIMATE, no verified figure). Over 14 days, buy-and-hold swings about 11% (1 sigma, ESTIMATE), so the result mostly reflects market direction.

Days needed for t = 2, using N = (2 x sigma / edge)^2, sigma 3% per day (ESTIMATE):
- Edge 0.3% per day: about 400 days
- Edge 0.1% per day: about 3,600 days

At 0.3% per day, a 90-day run gives t of about 0.95, not significant.

**Implication:** 14 days shows only "runs correctly". A 90-day live run can reject a strategy, not confirm one. A PASS needs at least 2 years out-of-sample (ESTIMATE).

**Trades:** N = (2 x sigma_trade / edge_per_trade)^2; 5% spread and 1% edge (ESTIMATE) give 100.

## 2. Ways to fool yourself, with a guard for each

1. **Look-ahead:** forming candles or revised data. Guard: read only data stamped before decision time. The Pi Zero W has no real-time clock, so require NTP sync.
2. **Mid-test tweaking:** Guard: hash config at start; any change restarts the clock.
3. **Survivorship:** coins picked from today's top list. Guard: freeze universe on start date; include delisted coins.
4. **Optimistic fills:** Guard: next poll's price, worse side of bid/ask, plus taker fee and slippage fixed before start (ESTIMATE).
5. **Unfair baseline:** Guard: buy-and-hold gets the same cash inflows as DCA; both liquidated at end under the same tax rules.
6. **Best of N:** Guard: report all N (section 4).
7. **Hand-written verdict:** Guard: the script prints PASS, FAIL or INCONCLUSIVE from the locked rules.

Bailey et al.: "as long as the researcher tries more than one strategy configuration, overfitting is always present". On random-walk data with 8,800 parameter combinations, PBO is 55% ([SSRN, 27 Feb 2015](https://papers.ssrn.com/abstract=2326253); [full text](https://escholarship.org/content/qt4w1110bb/qt4w1110bb.pdf)).

## 3. Locked PASS/FAIL rules

PASS only if all hold. Missing data gives INCONCLUSIVE.

1. **Length:** at least 2 years out-of-sample. Reason: section 1.
2. **Trades:** at least 100 closed round trips. Reason: fewer stays within noise.
3. **Net beat:** after fees, slippage and tax, beats buy-and-hold and debt paydown on the same dates.
4. **Regimes:** backtest includes a benchmark fall of at least 30% (ESTIMATE), and the strategy beats buy-and-hold there. Reason: a rule that only saw rising prices is untested.
5. **Drawdown:** max drawdown no worse than buy-and-hold. Reason: a bigger hole is not a better return.
6. **Random entries:** net return in the top 1% of 1,000 random strategies with the same time in market and trade count. Reason: separates skill from luck.
7. **Data:** no gaps over 1% of polls (ESTIMATE). Reason: gaps hide bad trades.

## 4. Five strategies, one wins by luck

Chance at least one of 5 independent strategies beats buy-and-hold by luck at 5%: 1 - 0.95^5, about 23% (upper bound, since they share data). Fix: each needs p below 0.05 / 5 = 0.01 (Bonferroni).

Bailey et al.: with 5 years of data, "one can be misled by looking at even as few as 45 sample configurations" ([ScienceDaily, Apr 2014](https://sciencedaily.com/releases/2014/04/140410103005.htm); daily-frequency assumption NOT FOUND). Harvey, Liu and Zhu set t above 3.0 for new factors ([NBER w20592, Oct 2014](https://www.nber.org/papers/w20592)). White's Reality Check ([Econometrica, Sept 2000](https://users.ssc.wisc.edu/~bhansen/718/White2000.pdf)) is the formal bootstrap for many candidates. Report all five, never just the winner.

## Conflicts and improvements

- CONFLICTS WITH: none found in D1 to D21.
- IMPROVES: a 14-day run never prints PASS.
- IMPROVES: the 90-day live run is a rejection gate; PASS needs 2 years.
- IMPROVES: DCA gets a DCA buy-and-hold baseline, not lump sum.

## Confidence and open questions

- High: arithmetic and citations. Low: volatility (no source found).
- Open: Danish tax on buy-and-hold versus realised trades needs an accountant. Exchange history depth: NOT FOUND.
