# Report — panem

Aggiornato: 2026-10-31 (Fase 1 chiusa; Fase 2-3 avviate con pipeline automatica)

## Avanzamento

| Fase | Stato | Note |
|---|---|---|
| 0 — Schema e perimetro | ✅ completata | decisioni in `PLAN.md` |
| 1 — Universo dei locali | ✅ completata | 129 righe in `locali.csv` |
| 2 — Discovery fonti menu | 🟡 parziale | 81 fonti censite, 58 locali coperti su 129 |
| 3 — Classificazione e scouting | 🟡 parziale | classi A/B/C/D assegnate, prezzi estratti dove possibile |
| 4 — Report | 🟡 prima stesura | questo file |

Pipeline riproducibile: `scripts/panem.py` (`discover`, `scrape`, `refresh`, `status`)
+ `scripts/harvest_paginegialle.py`. Aggiornamento automatico via cron (vedi in fondo).

## Copertura

| Metrica | Valore |
|---|---|
| Locali censiti | 129 |
| Locali con sito proprio trovato | 38 |
| Locali con almeno una fonte menu | 58 |
| Locali con prezzi estratti | 17 |
| Fonti censite | 81 (36 sito proprio, 14 PDF, 22 Just Eat, 9 TheFork) |
| Piatti/prezzi estratti | 1.187 |

Per categoria (locali con almeno una fonte): ristoranti 24, pizzerie 22,
paninoteche 5, hamburgherie 3, panzerotterie 2, forni 1, altro 1.

Nota integrità (2026-10-31): corrette 5 FK rotte in `fonti-menu.csv` che puntavano a
id inesistenti (`birbacco`, `maninpasta`, `miura-pizza-lab`, `salumeria-boccon-di-vino`
→ id reali; `tandem-food` era un locale mancante, ora aggiunto a `locali.csv`).
Aggiunto il controllo FK/contatori: `locali.csv` e `piatti.csv` ora sono coerenti.

## Distribuzione classi di estraibilità

| Classe | Significato | Fonti |
|---|---|---|
| A | HTML strutturato, prezzi nel DOM | 15 |
| B | PDF testuale | 14 |
| C | immagine / social / menu dietro JS | 10 |
| D | solo piattaforma o fonte bloccata | 42 |

## Dati estratti (locali con prezzi)

| Locale | Piatti | Prezzo min | Mediana | Max |
|---|---|---|---|---|
| Pizzeria Levante (+ sede Martiri) | 180 | 1,00 | 7,50 | 45,00 |
| Porta Aurea | 152 | 3,00 | 11,00 | 55,00 |
| DODO Sapori di Pizza | 140 | 1,00 | 7,50 | 18,00 |
| Pizza & Core | 90 | 1,00 | 7,75 | 40,00 |
| Hostàrì | 68 | 1,50 | 20,00 | 120,00 |
| Sponzami | 65 | 1,50 | 10,00 | 19,00 |
| Miura Pizza Lab | 61 | 1,00 | 10,00 | 13,00 |
| New Bietigheim / Bietigheim | 57 | 3,50 | 10,00 | 15,00 |
| Gusto d'Altura | 27 | 3,00 | 20,00 | 40,00 |
| Kebabberia Group | 26 | 3,00 | 5,25 | 7,90 |
| Degù Ham | 23 | 1,50 | 7,00 | 13,00 |
| Del Corso | 18 | 4,00 | 7,50 | 70,00 |
| Ristorante Biancospino | 18 | 2,00 | 10,50 | 81,00 |
| Diplomatico Club | 13 | 2,00 | 6,00 | 14,00 |
| Panificio del Lago | 12 | 2,40 | 29,00 | 80,00 |

I dati piatto-per-piatto sono in `data/piatti.csv` (locale, fonte, sezione, piatto,
prezzo, data di verifica).

## Gap — locali senza alcuna fonte censita

71 locali su 129. Sono i candidati commerciali dell'aggregatore (nessuna fonte nota,
quindi nessuna concorrenza diretta sul menu online). La maggior parte sono ristoranti
e pizzerie senza sito proprio e presenti solo su directory.

## Anomalie

- **Siti morti / irraggiungibili**: `panzerottoreumberto1.it`, `pizzeriaciccioeciabatta.it`,
  `pizzeriailpizzico.it`, `locandasannicola.it`, `meaticoaltamura.com`, `shodai.it`.
- **Siti "in manutenzione"**: `villadibacco.com`, `trearchi.it`.
- **Menu dietro splash/JS** (nessun prezzo nel DOM statico): `romanabistrotaltamura.it`,
  `stileliberoaltamura.it` (menu su `/menu/?menuSlug=...`), `osteriamoe.com`, `kyklos`.
- **Piattaforme bloccate**: Just Eat (Cloudflare 403, anche con browser), TheFork (403),
  Glovo. Non sono estraibili in automatico senza accordo o browser autenticato.
- **Motori di ricerca inutilizzabili** da questo IP: Bing/Google/DuckDuckGo restituiscono
  risultati spazzatura o captcha. Discovery basata su PagineGialle + varianti di dominio.

## Raccomandazioni tecniche

1. **Parsare siti propri + PDF funziona** (29 fonti su 81 con prezzi in chiaro). Costo
   marginale di aggiornamento quasi nullo: è la base solida del catalogo.
2. **Le piattaforme di terzi vanno trattate come catalogo, non come fonte prezzi**:
   link e presenza sì, menu no (bloccate e comunque non ripubblicabili).
3. **Aggiornamento**: check giornaliero dell'hash dei menu (`refresh.sh check`, ~45 s) e
   ri-scrape completo settimanale (`refresh.sh full`, ~3 min). I cambi finiscono in
   `data/changelog.csv`; `ultima_verifica` e `ultima_modifica` sono per fonte.
4. **Prossimi passi utili**: (a) passare il browser sulle 10 fonti classe C per capire
   se il menu è recuperabile; (b) trovare i siti mancanti dei 71 locali scoperti;
   (c) decidere il perimetro prodotto (solo Altamura? menu+prezzi? ordinabilità?).

## Aggiornamento automatico

Gira **sul server** (`/home/xenoserver/PROJECTS/panem`), non sulla copia di lavoro:

```
17 3 * * *   /home/xenoserver/PROJECTS/panem/scripts/refresh.sh check   # hash/HTTP
40 3 * * 1   /home/xenoserver/PROJECTS/panem/scripts/refresh.sh full    # ri-estrazione
```

Log: `raw/refresh.log` (gitignored). Lock: `/tmp/panem.lock`.

⚠️ `refresh.sh` aggiorna `data/` ma **non committa né pusha**: i dati nuovi restano sul
server finché non si fa commit a mano. Da sistemare (commit+push condizionale in coda
allo script, dopo aver verificato identità git e chiave di scrittura sul server).
