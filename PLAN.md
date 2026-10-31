# PLAN — panem

Piano operativo concordato il 2026-10-31.

## Obiettivo

Costruire il catalogo delle fonti menu dei locali di Altamura (BA) per valutare la
fattibilità di un aggregatore di menu. Risultato: `data/locali.csv`,
`data/fonti-menu.csv`, `report.md`.

## Decisioni prese

- **Perimetro fonti**: si includono anche i locali il cui menu esiste solo su
  piattaforme di terzi (Just Eat, Glovo, TheFork), ma sempre **etichettati** come tali.
- **Profondità**: catalogo fonti + struttura. **Non** si estraggono i singoli piatti.
- **Output**: CSV per la revisione + `report.md` per la lettura. Niente JSON, niente DB.

## Schema `data/locali.csv`

| Campo | Descrizione | Valori |
|---|---|---|
| `id` | chiave, slug kebab-case | `pizzeria-levante` |
| `nome` | nome commerciale | testo |
| `categoria` | tipo di esercizio | `pizzeria` \| `paninoteca` \| `ristorante` \| `panzerotteria` \| `hamburgheria` \| `forno-caffetteria` \| `altro` |
| `indirizzo` | via e civico | testo |
| `telefono` | numero principale | formato E.164 o locale |
| `sito` | sito proprio, se esiste | URL o vuoto |
| `piattaforme_delivery` | piattaforme dove è presente | lista separata da `;` |
| `ha_menu_online` | esiste almeno una fonte menu | `si` \| `no` |
| `n_fonti` | numero fonti trovate | intero |
| `note` | ambiguità, dubbi, segnalazioni | testo |
| `ultima_verifica` | data ultimo controllo | `YYYY-MM-DD` |

## Schema `data/fonti-menu.csv`

| Campo | Descrizione | Valori |
|---|---|---|
| `locale_id` | FK verso `locali.csv` | slug |
| `url` | URL della fonte | URL |
| `tipo_fonte` | dove sta il menu | `sito-proprio` \| `pdf` \| `microsito-delivery` \| `just-eat` \| `glovo` \| `thefork` \| `instagram` \| `facebook` \| `google-maps` |
| `classe` | estraibilità | `A` \| `B` \| `C` \| `D` |
| `prezzi` | i prezzi sono presenti | `si` \| `no` \| `parziale` |
| `allergeni` | allergeni dichiarati | `si` \| `no` \| `parziale` |
| `categorie_menu` | sezioni presenti | es. `antipasti;pizze;bevande` |
| `accessibilita_tecnica` | come si legge la fonte | `statico` \| `js` \| `api` \| `bloccato` |
| `note` | dettagli (CMS, JSON-LD, anomalie) | testo |
| `ultima_verifica` | data ultimo controllo | `YYYY-MM-DD` |

### Classi di estraibilità

- **A** — HTML strutturato: piatti e prezzi nel DOM, estraibili con un parser
- **B** — PDF con testo selezionabile: estraibile con `pdftotext`
- **C** — solo immagine o social (foto del menu, Instagram highlight): serve OCR o lavoro manuale
- **D** — solo piattaforma di terzi, nessun menu proprio

## Fasi

### Fase 1 — Universo dei locali

Fonti per costruire la lista (in quest'ordine):

1. Just Eat — `justeat.it/domicilio/altamura` e `/area/70022-altamura` (~44 locali)
2. TheFork — `thefork.com/restaurants/altamura-c16199`
3. PagineGialle / PagineBianche / Opendi (~49 "ristoranti", include chi non fa delivery)
4. Glovo — `glovoapp.com/it/it/altamura`
5. Instagram / ricerca web per le paninoteche (spesso assenti dalle piattaforme)

Per ognuno: normalizzare nome, categoria, indirizzo, telefono. Deduplicare.
**Esito atteso**: 60-70 righe in `locali.csv`.

### Fase 2 — Discovery delle fonti menu

Catena di priorità per ogni locale:

1. sito proprio → cerca `/menu`, `/menù`, link "Menu" in home
2. PDF (spesso linkato da home o da footer)
3. microsito delivery (es. `nome-locale.it` che punta a Just Eat)
4. Just Eat / Glovo / TheFork
5. Instagram / Facebook (menu in bio, highlight "Menu", post pinnato)
6. Google Maps (foto del menu caricate dai clienti: ultima risorsa, classe C)

**Esito**: righe in `fonti-menu.csv`, una per fonte trovata.

### Fase 3 — Classificazione e scouting tecnico

Per ogni fonte: assegnare `classe`, compilare `prezzi`, `allergeni`,
`categorie_menu`, `accessibilita_tecnica`. Per i siti propri annotare in `note`:
CMS rilevato (WordPress, Wix, Shopify…), presenza di JSON-LD `Restaurant`/`hasMenu`,
eventuali blocchi.

Questa fase produce l'informazione più utile per l'aggregatore: **quanti menu sono
recuperabili in automatico** e con quale tecnica.

### Fase 4 — Report

`report.md` con:

- copertura per categoria (quante pizzerie hanno menu online vs. no)
- distribuzione delle classi A/B/C/D
- **gap**: locali senza alcun menu online (target commerciale dell'aggregatore)
- anomalie: siti morti, menu vecchi, PDF non aggiornati
- raccomandazioni tecniche: quali fonti conviene parsare, quali richiedono accordi

## Vincoli e rischi

- **Google Maps**: senza Places API l'universo non è garantito al 100%. Mitigazione:
  saturare con Just Eat + TheFork + PagineGialle + Instagram; Maps solo per spot check.
- **Copertura Just Eat** è la più ricca ma è di terzi: utile per il censimento, non
  come base del prodotto.
- **Menu non aggiornati** sono la norma: la data di verifica è un campo obbligatorio.
- **Tempi**: ~1 ora di lavoro agentico complessivo, escluso l'eventuale controllo manuale
  su Maps.
