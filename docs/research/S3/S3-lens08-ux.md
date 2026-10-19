DONE (partial evidence depth; 2 searches, sources not fully fetched)

# Lens 08: User experience. New strategy suggestions

Filter: Jakob spends ~20 min/week, so each arm must be explainable in one sentence, produce few trades, and give a clear reason for each trade. None of these duplicates the seed list (EMA 50/200, Donchian, 90-day momentum, 50/50 rebalance, DCA, lump sum, debt paydown).

1. **Value-averaging DCA (200-day deviation)**
   - Plain: "Invest the same monthly amount, but invest double when BTC is more than 20% below its 200-day average, and skip the month when it is above."
   - Default: monthly check on the 1d close; buy 2x / 1x / 0x by deviation band.
   - Summary line: "Oct: BTC -23% vs 200d avg, bought 2x (EUR 80)."
   - Trades/yr: ~12-15. Evidence: https://www.cxoadvisory.com/currency-trading/timing-bitcoin-with-smas/ (undated, confidence low-medium).

2. **Monthly 12-month absolute momentum, cash otherwise**
   - Plain: "Hold BTC only if its price is higher than 12 months ago; otherwise hold EUR."
   - Trades/yr: 0-2. Summary: "Still in BTC (+41% over 12m)." Overlaps with the 90-day momentum arm in signal family, so treat as a variant only if the 90-day arm is dropped. Evidence: https://www.monash.edu/business/monash-centre-for-financial-studies/our-research/all-projects/investment-strategy/trend-following-strategies-for-crypto-investors (date not verified, confidence medium).

3. **Rebalancing band (60/40 BTC/EUR)**
   - Plain: "Keep 60% in BTC; only trade when it drifts more than 10 points from target."
   - Trades/yr: 2-6. Summary: "Drift 64/36, no trade." Very easy to sanity-check.

4. **Drawdown rebuy ladder**
   - Plain: "Buy a fixed slice after each further 15% fall from the 90-day high."
   - Trades/yr: under 4 in a normal year. Summary: "BTC -30% from high, bought slice 2 of 3."

5. **Monthly volatility-scaled BTC exposure**
   - Plain: "Hold more BTC when recent volatility is low, less when high, rebalancing monthly."
   - Trades/yr: 12. Summary: "Vol 38%, exposure 55%." Risk: explanation is harder than others. Confidence low.

Caveats: Evidence was thin. Search returned mostly blogs and QuantConnect backtests, not peer-reviewed UX studies. Trades/yr are estimates, not backtested.
