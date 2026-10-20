# Haiku-nyhedsdagbog (kun papir)

Denne gren indeholder én fil pr. US-handelsdag i `journal/`, skrevet af en planlagt Claude-kørsel kl. 14:20 dansk tid.
Fire Haiku-agenter læser dagens nyheder, og en Haiku-dommer vælger 0-3 aktier (eller ingen) fra en fast liste.

Ingen handler, ingen penge, ingen nøgler. Raspberry Pi'en henter grenen hver time og scorer valgene mod QQQ
og mod gennemsnittet af hele listen (`pitrader/news.py` på `pi-live`). Resultatet ligger som `nyheder.md` i status-repoet.
