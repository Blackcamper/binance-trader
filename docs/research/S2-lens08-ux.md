# S2 Lens 08: UX for Jakob (paper-trading dashboard)

**Bottom line:** One read-only screen on the Pi, reached over Tailscale, with one silent daily push and loud pushes only on faults. The PASS/FAIL rule must be fixed before day one.

## Recommendations

1. **One verdict row, then one row per strategy.** Top: `GO-LIVE ✗ FAIL (x of y checks)`. Then each strategy with ✓/✗ against buy-and-hold, after fees and tax, plus the DKK figure. He reads little, so a verdict beats a chart he has to interpret.

2. **Lock the rule before launch.** Store the criteria in a timestamped file and show the criteria version on screen. Changing the rule after seeing results is the likeliest self-deception. Gap: Ground Truth says "a meaningful period" with no length. NOT FOUND.

3. **Okabe-Ito blue and orange, always paired with a symbol.** Sky blue #56B4E9 (8.0:1 on #121417) for the best strategy's line, orange #E69F00 (8.2:1) dashed for buy-and-hold. Text in light grey #c9ced6 (11.7:1). Dark blue #0072B2 is only 3.6:1, so use it for fills, not text. Contrast ratios computed here, not sourced.

4. **Daily push via ntfy, faults at high priority.** One daily message at priority 2 (no sound). Faults at priority 4 (pop-over, long vibration). Tap opens the dashboard via `X-Click`. Source: docs.ntfy.sh/publish, fetched 18 Oct 2026. The docs say the topic is "essentially a password", so use a long random topic and an access token. Telegram alternative: about 1 message/s per chat, 20/min in groups, 429 errors beyond that (core.telegram.org/bots/faq, undated, fetched 18 Oct 2026). Telegram is richer; ntfy's priority levels map directly to "alert only on problems".

5. **Dead-man watchdog outside the Pi.** A dead Pi sends no alert of its own. Healthchecks.io's free Hobbyist plan covers 20 jobs (healthchecks.io/pricing, undated, footer "© 2015-2026"). Whether free-tier alerts reach ntfy or Telegram: NOT FOUND, check before relying on it. Uptime Kuma on TrueNAS is an option (ESTIMATE, not checked), but it shares the home power and internet.

6. **Phone access via Tailscale, no open ports.** Free Personal plan: up to 6 users, unlimited user devices, "free forever" (tailscale.com/pricing, undated). Its FAQ says the plan is "only suitable for non-commercial use". Fine for this personal project; revisit if the simulation becomes a business.

7. **Dyslexia-friendly layout.** Dyslexia Scotland (12 Sep 2025, dyslexiascotland.org.uk/dyslexia-friendly-typed-formats): plain sans-serif, at least 12pt with larger preferred, 1.5x line spacing, left-aligned, no full justification. It says nothing about dark mode. So: 16px+ body, no italics, and the same Auto/Light/Dark toggle as the morning board.

8. **Read-only phone.** No buttons that change the simulation or place orders. A stray tap should never touch the paper book, and this keeps D16 clean.

## Phone layout (one screen, placeholders only)

```
PAPER · DAY [n]/[N]            Pi ✓ 12:04
────────────────────────────────────────
GO-LIVE   ✗ FAIL   (x of y checks)
────────────────────────────────────────
Strategy     After fees+tax    vs hold
A [name]     +[###] kr         ✓ +[###]
B [name]     +[###] kr         ✗ -[###]
C [name]     +[###] kr         ✗ -[###]
Buy & hold   +[###] kr         reference
────────────────────────────────────────
[chart: best strategy solid blue,
 buy-and-hold dashed orange]
────────────────────────────────────────
Alerts: none ✓        (tap to expand)
```

## Human steps (unavoidable, listed per D3)

- Install ntfy and subscribe to the topic (once).
- Install Tailscale on phone and Pi, sign in (once).
- Healthchecks.io account and ping URL, if used (once).
- Save the dashboard to the phone home screen (once).
- Go-live yes/no decision, which is always yours (D13).

Normal days need zero action.

## Conflicts and gaps

- CONFLICTS WITH: none strict.
- "After tax" needs a tax value from the tax lens. NOT FOUND here.
- Keep any projection toward 200,000 DKK off the screen, per D5 "realism over hype". IMPROVES: the screen shows only measured results.

## Open questions

1. What is "a meaningful period": days, and minimum number of trades?
2. What margin over buy-and-hold, after fees and tax, counts as PASS?
3. ntfy or Telegram?
4. Is email an acceptable alert channel for the watchdog?
