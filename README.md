# panem

Catalogo delle fonti menu dei locali di **Altamura (BA, 70022)** — ristoranti, pizzerie,
paninoteche e affini — come base dati per un futuro aggregatore di menu.

Il progetto nasce con un obiettivo preciso: capire **chi ha davvero un menu online**,
**dove** sta (sito proprio, PDF, social, piattaforma di delivery) e **quanto è estraibile**
in modo automatico. Il valore non è l'elenco in sé, ma la mappa delle fonti e dei buchi.

## Stato

Fase 1 chiusa (129 locali). Fase 2-3 avviate: 81 fonti censite su 58 locali, 17 con
prezzi estratti (1.187 righe in `data/piatti.csv`). Dettaglio e gap in `report.md`.

Aggiornamento automatico (cron): check giornaliero dell'hash dei menu + ri-scrape
settimanale. Comandi manuali:

```bash
python3 scripts/panem.py discover   # cerca i siti propri mancanti
python3 scripts/panem.py scrape     # scarica fonti, estrae menu e prezzi
python3 scripts/panem.py refresh    # ricontrolla le fonti note (cambi -> changelog)
python3 scripts/panem.py status     # copertura
python3 scripts/panem.py check      # validazione CSV: exit 1 se FK/contatori incoerenti
```

## Struttura

```
panem/
├── AGENTS.md            # contesto e regole per l'agente OpenCode
├── PLAN.md              # piano a fasi, schema dati, criteri di classificazione
├── data/
│   ├── locali.csv       # 1 riga per esercizio (universo deduplicato)
│   ├── fonti-menu.csv   # 1 riga per fonte menu (un locale può averne più)
│   ├── piatti.csv       # 1 riga per piatto+prezzo estratto
│   ├── monitoraggio.csv # hash/HTTP per il change detection
│   └── changelog.csv    # fonti cambiate rilevate dal refresh
├── scripts/
│   ├── panem.py             # discover / scrape / refresh / status / check
│   ├── harvest_paginegialle.py  # discovery siti da PagineGialle
│   └── refresh.sh           # wrapper cron (check | full), valida e pusha i dati
├── raw/                 # snapshot HTML/PDF consultati (gitignored)
└── report.md            # sintesi: copertura, classi, gap, note tecniche
```

## Come si usa

Da questa cartella:

```bash
opencode
```

L'agente legge `AGENTS.md` (contesto operativo) e `PLAN.md` (cosa fare). Il primo comando
utile è "esegui la Fase 2".

## Principi

- **Solo Altamura 70022.** Gli omonimi (Altamura Pizza di Hinsdale IL, Altamura Trattoria
  di Doral FL) vanno esclusi.
- **Le piattaforme di terzi si catalogano, non si copiano.** Just Eat e simili sono fonti
  legittime da linkare e descrivere; i loro menu non si ripubblicano.
- **Meglio un buco dichiarato che un dato inventato.** Se una fonte non è verificabile,
  lo si scrive.
