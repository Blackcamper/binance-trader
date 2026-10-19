# S3 seed: find OTHER trading strategies to look into (2026-10-19)

Goal: Jakob wants a list of additional crypto trading strategies worth adding as arms in the paper-trading simulation, beyond what is already planned.

## Already planned (do NOT re-propose these as new; you may propose variants only if clearly different)
- Controls: lump-sum buy-and-hold, weekly DCA
- Daily EMA 50/200 crossover on BTC-EUR
- 4h Donchian 20/10 breakout on BTC-EUR (and on ETH-EUR)
- 90-day time-series momentum
- 50/50 BTC/ETH rebalance
- Baseline: "pay down debt" at ~5.76% APR

## Hard constraints
- Paper trading first; virtual 5,000 DKK (~670 EUR). Real money only if locked PASS rules are met: >=2 years out-of-sample backtest incl. a >=30% fall, >=100 closed trades, beats buy-and-hold AND debt paydown after fees and Danish tax, max drawdown <= buy-and-hold, top 1% vs 1,000 random-entry strategies, Bonferroni p<0.01.
- Live money (if ever): SPOT ONLY, no leverage, margin, futures or shorting. The simulation itself MAY test anything, but strategies that can never go live are low value.
- Runs on a Raspberry Pi Zero W (ARMv6, single core, 512 MB): one Python program, standard library only, polling every few minutes, closed candles only. No numpy/ML on the Pi. Heavy backtests run on a home PC.
- Data: PUBLIC market data only, no API keys. Venue: Kraken (EUR pairs; OHLC 4h/1d, ticker, order book depth). Bitvavo alternative. Binance historical data allowed for backtests only.
- Fees: Kraken taker ~0.40-0.80%, Bitvavo taker 0.25%; round trip roughly 0.5-1.6% + spread. Fees dominate high-turnover strategies.
- Danish tax: every sale/swap is a realisation; gains taxed as personal income up to ~53%, losses worth ~26%. This heavily penalises high turnover and favours low-turnover strategies.
- Textbook default parameters, no optimisation (overfitting risk).
- Legal and ethical only: no wash trading, front-running, manipulation, gambling.
