# Opsætning af simulatoren på Raspberry Pi Zero W

Simulatoren er ét Python-program uden eksterne pakker. Den bruger kun Krakens offentlige markedsdata, har ingen API-nøgler og handler kun med virtuelle 5.000 kr.

## Engangs-trin (dig)

1. Flash **Raspberry Pi OS Lite (32-bit)** med Raspberry Pi Imager. Sæt Wi-Fi, brugernavn `pi` og SSH-nøgle i Imager.
2. Log ind med SSH og tjek: `python3 --version` (skal være 3.7 eller nyere) og `timedatectl` (skal vise `System clock synchronized: yes`).
3. Hent koden: `git clone https://github.com/Blackcamper/binance-trader.git ~/binance-trader` (privat repo: brug en read-only deploy key).
4. Test forbindelsen til Kraken: `cd ~/binance-trader && python3 -m pitrader check`. Den skal slutte med `OK` og vise bid/ask for XBTEUR og ETHEUR.
5. Start tjenesten:
   ```
   sudo cp deploy/pitrader.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now pitrader
   ```
6. Se status: `python3 -m pitrader status` eller `journalctl -u pitrader -f`.

## Hvad den gør

- Poller hvert 5. minut. Indikatorer regnes kun på lukkede candles (4h og 1d).
- En beslutning fyldes først ved næste poll, til ask (køb) eller bid (salg) efter at have gået ordrebogen igennem, plus 0,8 % gebyr og 5 bp ekstra slippage.
- Hver strategi har sin egen virtuelle konto på 5.000 kr.: buy-and-hold BTC og ETH, ugentlig DCA, EMA 50/200, Donchian 20/10 på BTC og ETH, 90-dages momentum.
- Skat beregnes som skyggeregnskab (FIFO, gevinst 53 % eller 37 %, tab værd 26 %). Satserne skal bekræftes af SKAT eller en revisor før en rigtig beslutning.
- Uden NTP-synkroniseret ur handler den ikke (Pi Zero har intet batteriur).

## Filer (i `data/sim-v1/`)

| Fil | Indhold |
|---|---|
| `journal.jsonl` | Alle ordrer og fills, append-only. Kontiene genopbygges fra den ved genstart. |
| `status.json` | Heartbeat, helbred og alle strategiers tal. Det er den, statuskanalen skal sende videre. |
| `summary.txt` | Samme som ren tekst. |
| `equity.csv` | Egenkapital pr. strategi ved hver poll. |

## Låst konfiguration

`config/sim-v1.json` er låst for kørslen. Ændrer du den, nægter programmet at fortsætte (det er reglen fra D22). En ny konfiguration kræver en ny `--data-dir`, altså en ny kørsel fra dag 1.

## Hvis SD-kortet skal skånes

Læg data på en USB-disk: tilføj `--data-dir /mnt/usb/sim-v1` til `ExecStart` i servicefilen.
