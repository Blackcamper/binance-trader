# S2 Lens 09: Edge cases for a 24/7 Pi paper trader

**Bottom line:** Expect power cuts, SD-card damage, dead-but-open sockets and API bans. Recover by replaying a journal, keep the Pi key-free, and make the simulation pessimistic. Confidence: high on exchange limits (from docs), medium on Pi hardware.

## Eight suggestions

1. **Journal state to an SSD, not the SD card.** Reason: power cuts mid-write corrupt SD cards; the Adafruit guide says the read-only overlay "won't always save you" from power problems. Mitigation: append-only journal of market events and simulated fills, fsync'd to a USB SSD. On boot, replay it, then REST-backfill the candle gap.

2. **Read-only root via Overlay File System.** Reason: the same guide says it makes systems "more resistant to unplanned power cuts." Mitigation: enable it in raspi-config, keep the journal on the SSD, run under systemd with `Restart=always`.

3. **Staleness watchdog, not just close events.** Reason: a Wi-Fi drop can leave a silent socket open. Bitvavo's sample reconnects after a fixed 5 s and documents no heartbeat or resync. Mitigation: if a pair is silent for N seconds (ESTIMATE: 30), reconnect with backoff and jitter, then refetch the full book (`getBook`). Use Ethernet (ESTIMATE, not checked).

4. **Rate limiter at about half the documented limit (ESTIMATE).** Reason: Binance escalates IP bans from 2 minutes to 3 days; Bitvavo blocks a key 1 minute on HTTP 429 (15 minutes per IP); Kraken's counter maximum is 15 to 20. Mitigation: honour `retryAfter` and `bitvavo-ratelimit-resetat`, never retry at once, use public endpoints only.

5. **Log undervoltage, alert on it.** Reason: `vcgencmd get_throttled` flags 0x1 (active) and 0x10000 (since boot); a 5V/2A supply still caused warnings under load. Mitigation: official PSU, poll every minute, alert when 0x1 is set.

6. **Refuse out-of-order timestamps.** Reason: NOT FOUND whether a Pi 5 keeps time without its RTC battery. Mitigation: chrony or systemd-timesyncd; reject events stamped before the last journal entry; alert if no NTP sync within 5 minutes of boot (ESTIMATE).

7. **Keep flash-crash ticks; do not filter them.** Reason: deleting outliers removes the moves that trigger stops, so paper results flatter. Nautilus stop logic "assumes a continuous move through the trigger." Mitigation: flag ticks more than X% from book mid (X ESTIMATE) but keep them; stops fill at the first available book level, not the trigger price.

8. **Book-walk fills with consumed size.** Reason: Nautilus's default lets each matching iteration use "the full recorded size," and "a print proves that liquidity existed momentarily." Mitigation: market orders walk the L2 book and consume size; residual fills one tick worse; limit orders fill only on trade-through; add 0.1 to 0.5 s latency (ESTIMATE, replace with measured round trip); charge fees on both legs (Bitvavo lowest tier, EUR markets: maker 0.15%, taker 0.25%). Measure spread from the book; the fee page does not give one.

## Self-heal vs alert

- **Self-heal, log only:** websocket reconnect, 429 backoff, gap backfill under 5 minutes (ESTIMATE), systemd restart, NTP resync.
- **Alert to phone, labelled in text ("FAIL", "WARN"), not colour alone:**
  - Dead-man's switch missed: the Pi cannot report its own outage, so it pings an external service every minute (not verified).
  - Any HTTP 418, or repeated 429 after backoff.
  - Held pair missing from exchange list: close the simulated position at last bid, flag "delisted".
  - Gap over 5 minutes with an open position (ESTIMATE).
  - Filesystem read-only or journal write error: critical.
  - Simulated equity jump over X% in one tick.
- **Unavoidable human steps (for D3):** replace SD or SSD, replace PSU, power-cycle after a failed boot.

## Conflicts, ideas, open questions

- CONFLICTS WITH: none.
- IMPROVES: external dead-man's switch. D18 has the Pi monitoring itself, which cannot detect its own outage.
- IMPROVES: no trading keys on the Pi, so a compromised device cannot trade.
- IMPROVES: deterministic replay, so a rebuilt simulator can be checked against the journal.
- Open: Binance market-stream keepalive (NOT FOUND); Kraken websocket heartbeat (not checked); DKK on Bitvavo (NOT FOUND).

## Sources (read 2026-10-18)

- docs.kraken.com/exchange/guides/rest/ratelimits (undated)
- developers.binance.com/docs/binance-spot-api-docs/websocket-api/rate-limits (modified 2026-10-16)
- docs.bitvavo.com/docs/rate-limits/ and /websocket-overview (undated)
- bitvavo.com/en/fees (undated)
- learn.adafruit.com/read-only-raspberry-pi/overview (edited 2024-03-08)
- peppe8o.com/raspberry-pi-undervoltage-detected/ (updated 2026-06-14)
- core-electronics.com.au/raspberry-pi-5-rtc-battery.html.md (undated)
- nautilustrader.io/docs/latest/concepts/backtesting/fill-prices-and-matching/ (undated)
