# panem

Catalogo delle fonti menu dei locali di **Altamura (BA, 70022)** — ristoranti, pizzerie,
paninoteche e affini — come base dati per un futuro aggregatore di menu.

Il progetto nasce con un obiettivo preciso: capire **chi ha davvero un menu online**,
**dove** sta (sito proprio, PDF, social, piattaforma di delivery) e **quanto è estraibile**
in modo automatico. Il valore non è l'elenco in sé, ma la mappa delle fonti e dei buchi.

## Stato

Fase 0 completata (schema e perimetro definiti). Le fasi 1-4 sono descritte in `PLAN.md`
e non sono ancora state eseguite: `data/` contiene solo le intestazioni.

## Struttura

```
panem/
├── AGENTS.md            # contesto e regole per l'agente OpenCode
├── PLAN.md              # piano a fasi, schema dati, criteri di classificazione
├── data/
│   ├── locali.csv       # 1 riga per esercizio (universo deduplicato)
│   └── fonti-menu.csv   # 1 riga per fonte menu (un locale può averne più)
├── raw/                 # snapshot HTML/PDF consultati, per ri-verifiche
└── report.md            # sintesi: copertura, classi, gap, note tecniche
```

## Come si usa

Da questa cartella:

```bash
opencode
```

L'agente legge `AGENTS.md` (contesto operativo) e `PLAN.md` (cosa fare). Il primo comando
utile è "esegui la Fase 1".

## Principi

- **Solo Altamura 70022.** Gli omonimi (Altamura Pizza di Hinsdale IL, Altamura Trattoria
  di Doral FL) vanno esclusi.
- **Le piattaforme di terzi si catalogano, non si copiano.** Just Eat e simili sono fonti
  legittime da linkare e descrivere; i loro menu non si ripubblicano.
- **Meglio un buco dichiarato che un dato inventato.** Se una fonte non è verificabile,
  lo si scrive.
