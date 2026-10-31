# AGENTS.md — panem

Istruzioni operative per l'agente OpenCode che lavora in questa cartella.

## Cos'è questo progetto

Catalogo delle fonti menu (siti, PDF, social, piattaforme di delivery) dei locali di
**Altamura (BA), CAP 70022**: ristoranti, pizzerie, paninoteche, panzerotterie,
hamburgherie, forni con somministrazione. Serve a valutare la fattibilità di un
aggregatore di menu locali.

Piano completo e schema dati: `PLAN.md`. Leggilo prima di iniziare qualsiasi fase.

## Regole non negoziabili

1. **Perimetro geografico**: solo esercizi con sede a Altamura, CAP 70022.
   Escludere gli omonimi negli USA ("Altamura Pizza" Hinsdale IL, "Altamura Trattoria"
   Doral FL) e i locali di comuni vicini (Gravina, Matera, Santeramo, Laterza) —
   a meno che il proprietario non allarghi esplicitamente il perimetro.
2. **Fonti spazzatura**: non usare come fonte menu i siti generati da AI/SEO
   (`menuwithpricesonline.com`, `menu-all.com`, `restaurants-us.com`, `menuweb.menu`,
   `piatti.menu`, `restaurants-info.com`). Sono inaffidabili. Al massimo sono indizi
   per trovare il sito vero.
3. **Piattaforme di terzi**: Just Eat, Glovo, TheFork si catalogano con
   `tipo_fonte` dedicato. Non copiare né ripubblicare i loro menu: si linka e si
   descrive la struttura (n categorie, prezzi sì/no, allergeni sì/no).
4. **Rispetto tecnico**: prima di fare richieste ripetute a un sito, controllare
   `robots.txt`. Rate limit: max 1 richiesta/secondo per dominio. Non aggirare
   protezioni anti-bot.
5. **Nessun dato inventato**: se una fonte non è verificabile, `note` lo dichiara.
   Un campo incerto vale `no` o `parziale`, mai un'ipotesi presentata come fatto.

## Come lavorare sui dati

- `data/locali.csv` = una riga per esercizio. La chiave è `id` (slug kebab-case,
  es. `pizzeria-levante`).
- `data/fonti-menu.csv` = una riga per **fonte**, collegata via `locale_id`.
  Un locale con menu su sito + PDF ha due righe.
- Deduplicazione: stesso `nome` normalizzato **e** stesso indirizzo **o** stesso
  telefono = stesso locale. Attenzione ai locali con più punti vendita.
- Prima di aggiungere una riga, controllare che non esista già.
- Ogni riga aggiornata porta `ultima_verifica` = data odierna (YYYY-MM-DD).
- Snapshot: quando consulti una fonte, salva l'output in
  `raw/YYYY-MM-DD-<locale-id>-<tipo>.<html|pdf|txt>` per ri-verifiche future.
  Non salvare immagini di menu senza necessità.

## Ordine di lavoro (fasi)

Vedi `PLAN.md`. Riassunto:

1. **Fase 1** — costruire l'universo dei locali (`locali.csv`)
2. **Fase 2** — per ogni locale trovare le fonti menu (`fonti-menu.csv`)
3. **Fase 3** — classificare le fonti (A/B/C/D) e lo scouting tecnico
4. **Fase 4** — scrivere `report.md` con copertura, gap e raccomandazioni

Non saltare la Fase 1: senza universo completo, il report è inutile.

## Cosa NON fare

- Non creare applicazioni, frontend o database: questo progetto produce **dati e un
  report**, non software. L'aggregatore è un progetto futuro e separato.
- Non installare dipendenze pesanti. Bastano `curl`, `python3`, `pdftotext`.
- Non committare snapshot di pagine che contengono dati personali o token.

## Consegna attesa per ogni fase

Alla fine di ogni fase: righe aggiornate nei CSV + una riga di stato in `report.md`
sezione "Avanzamento". Poi fermarsi e riportare al proprietario.
