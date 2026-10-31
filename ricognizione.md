# Ricognizione 2026-10-31 — note di lavoro (Fase 1)

Stato: **Fase 1 in corso**. Nessuna riga ancora scritta in `data/locali.csv` o
`data/fonti-menu.csv`. Questo file è il diario tecnico della ricognizione: cosa ho
interrogato, cosa ha risposto, cosa ho estratto e cosa resta aperto.

## 1. Metodo e accessibilità delle fonti

| Fonte | `curl` | `webfetch` | Note |
|---|---|---|---|
| Just Eat (`justeat.it`) | 200 ma HTML vuoto (Next.js, dati client-side) | ✅ testo renderizzato | Cloudflare blocca `chromium --headless` |
| TheFork (`thefork.it`) | 403 | ✅ testo renderizzato | nessun JSON-LD nel listing |
| PagineBianche (`paginebianche.it`) | ✅ 200 | ✅ | espone **JSON-LD `ItemList`** con nome, indirizzo, CAP, telefono, geo → parsabile |
| PagineGialle | 404 sulla URL di categoria | n.d. | da riprovare con URL di ricerca corretta |
| Glovo | timeout di rete | n.d. | da riprovare |

Conseguenze operative:

- **PagineBianche è la fonte di costruzione dell'universo**: si scarica con `curl`
  (rate limit 1 req/s) e si parsa il JSON-LD, senza consumo di contesto.
- **Just Eat e TheFork si leggono con `webfetch`**, una pagina per volta: costoso in
  token, quindi si usano per completare, non per costruire la lista base.
- API interne Just Eat (`cw-api.takeaway.com/api/v33|v32/restaurants`) → **404**, non
  percorribile senza reverse engineering del client.

## 2. Just Eat — `/domicilio/altamura`

La pagina dichiara 44 consegne nella zona 70022 ma ne mostra 20 (serve "Show more").
Tutte con indirizzo e CAP 70022, quindi dentro perimetro.

| Locale | Indirizzo | Rating |
|---|---|---|
| Sale e Pepe Take Away | Via Gravina 104 | 4.1 (1242) |
| Maninpasta | Via Monopoli 9 | 4.5 (747) |
| Ham. Hamburgheria | Via Golgota 86 | 4.4 (620) |
| Sapè Pizzeria Takeaway | Via IV Novembre 13 | 4.6 (523) |
| Fior di Pizza | Via Salvatore Quasimodo 36/38 | 4.6 (432) |
| Pizza & Core Pizzeria Napoletana | Via Centonze Antonia 2 | 4.8 (421) |
| Pizzeria Non Mi Dire | Via Lucera 29 | 4.5 (393) |
| Pizzeria Alta Pizza | Via San Gennaro 3B | 4.7 (327) |
| Tandem Food | Via delle Nazioni 15 | 4.6 (325) |
| Arte Pizza | Via Bergamo 61 | 4.1 (313) |
| Degù Ham | Via Bari 112 | 4.3 (310) |
| Nagoya Ristorante Fusion | Via Selva 192 | 4.4 (288) |
| Kebabberia Group | Via Pietro Colletta 6 | 4.2 (285) |
| Umami Pizzeria | Via Santeramo in Colle 48 | 4.6 (206) |
| Piada' La Piadineria Artigianale | Via Vittorio Veneto 47 | 4.3 (169) |
| Birbacco Pizzeria Hamburgeria | Via Caduti delle Foibe 15 | 4.8 (144) |
| Miura Pizza Lab | Piazza Giuseppe De Napoli 10 | 4.5 (137) |
| Sponzami | Piazza Mercadante 9 | 4.4 (119) |

Da `/area/70022-altamura` (vista con posizione diversa, 8 locali attivi al momento
della richiesta):

| Locale | Indirizzo | Rating |
|---|---|---|
| Kebabberia Group | Via Pietro Colletta 6 | 4.2 (280+) |
| Piada' La Piadineria Artigianale | Via Vittorio Veneto 47 | 4.4 (170+) |
| Degù Ham | Via Bari 112 | 4.3 (310+) |
| The Grill — Specialità Carne & Panini | (70022) | 4.0 (170+) |
| Shibumi Altamura — Fusion Restaurant | (70022) | 5.0 (4) |
| Tandem Food | Via delle Nazioni 15 | 4.6 (320+) |
| Salumeria Boccon di Vino | (70022) | 4.7 (21) |
| Bistrot del Borgo | Piazza Duomo 5 | 3.5 (79) |

## 3. TheFork — `altamura-c16199`

Il listing dichiara **78 ristoranti**, ma la pagina **mescola Matera** (Medina, Braci &
Abbracci, 900 Ristorante Casa Taccardi, Palazzo del Duca, Myricae, Fuoco di Vino,
Ristoteca dai Tosi, Quid Piccola Trattoria Murgiana, Prometeo, Osteria Oi Marí, Burro
Salato, Vitantonio Lombardo, ecc.). **Filtro obbligatorio su località/CAP**, non sulla
pagina: il perimetro non è garantito dal parametro geografico di TheFork.

Confermati ad Altamura (pagine 1):

| Locale | Indirizzo | Rating | Prezzo medio |
|---|---|---|---|
| Fior di Pizza | Via Salvatore Quasimodo | 9.5 (1056) | 15 € |
| Pamaro | Via Monte Rosa 14 | 8.9 (45) | 26 € |
| Osteria Mo è | Via Luca de Samuele Cagnazzi 27 | 9.2 (409) | 35 € |
| DODO sapori di pizza | Via Caduti di Nassirya 26 | 9.2 (109) | 19 € |
| Gusto d'Altura | Via Bari 110 | 9.8 (48) | 60 € |
| La Locanda di Alice | Piazza Marconi 4 | 9.1 (70) | 29 € |
| Mercadante Pizza e Cucina | Via Bruxelles 3 | 9.1 (490) | 25 € |
| Hostàrì, Osteria Moderna | Via Massimo D'Azeglio 6 | 9.1 (108) | 25 € |
| Villa di Bacco | Via Mura Megalitiche 53 | 9.0 (469) | 20 € |

Pagine 2-4 non ancora lette.

## 4. PagineBianche — categoria "Ristoranti ad Altamura"

Dichiarati **più di 200 risultati**, con promozioni di aziende vicine (Radimare a
Monopoli, 64 km). Pagina 1 completa, pagine successive scaricate ma non ancora parse.

Prima pagina (nome — categoria — indirizzo — telefono):

| Locale | Cat. | Indirizzo | Telefono |
|---|---|---|---|
| Pizzeria Vecchio Ponte | Ristoranti | Via Araldo di Crollalanza 27 | 080 3112339 |
| Mo è Osteria | Ristoranti | Via Desamuele Cagnazzi Luca 27 | 334 9406423 |
| Agriturismo Masseria Chinunno | Ristoranti | S.P. 18 km 8.3 | 080 3140185 |
| Binario 24 Ristorante | Ristoranti | Piazza Stazione 24 | 376 2566911 |
| Ristorante Pizzeria La Brace | Ristoranti | Via Brescia 54 | 080 3116148 |
| Kyklos S.r.l. | Ristoranti | Via Trentacapilli 42 | 333 6824163 — `web.kyklosaltamura.it` |
| Fior di Pizza | Ristoranti | Via Quasimodo Salvatore 36/38 | 080 4046733 |
| Villa di Bacco | Ristoranti | Via Mura Megalitiche 53 | 340 0593024 |
| HostàRì, Osteria Moderna | Ristoranti | Via D'Azeglio Massimo 6 | 080 6932019 |
| Dodo Sapori di Pizza | Ristoranti | Via Caduti di Nassiriya 26 | 333 7586819 |
| Gusto D'Altura | Ristoranti | Via Bari 110 | 376 2567744 |
| La Locanda di Alice | Ristoranti | Piazza Marconi Guglielmo 4 | 348 3598539 |
| Pamaro | Ristoranti | Via Monte Rosa 14 | 329 7847104 |
| 100 Metri Quadri | Ristoranti | Via Cassano 277 | 080 3141596 |
| Agriturismo Madonna dell'Assunta | Ristoranti | S.P. 235 Altamura-Gioia | 334 8413839 |
| Antica Osteria Pein Assutt | Trattorie e osterie | Corso Umberto I 56 | 080 3118313 |
| Antica Osteria Santa Chiara La Grotta | Trattorie e osterie | Via Santa Chiara 6 | 080 3102321 |
| Be-Steak House | Ristoranti | Via Caduti delle Foibe 50 | 334 8411121 |
| Binario 24 | Ristoranti | Piazza Stazione 24 | 080 2377922 |
| Bistrot del Borgo | Ristoranti | Piazza Duomo 5 | 080 8495984 |
| Black Pepper Comfort Food | Ristoranti | Via Matera 13 | 080 2223800 — `alteregoaltamura.it` |
| Braceria Casa del Vitello | Ristoranti | Via Santeramo 123 | 080 8097315 |
| Calvi Ristorante | Ristoranti | Via Bari 134 | 080 3142942 |
| CanarùTe | Ristoranti | Via Martiri 11 Settembre 2001 19 | 080 9140100 — IG `canarute_altamura` |
| Caseificio Sollecito | Ristoranti | Via Santa Teresa 17 | 080 3146151 |
| Des Artist | Ristoranti | Via Reno 3 | 080 3149957 |
| Devo Ristorante Pizzeria | Ristoranti | Viale Martiri 1799 129 | 080 8090032 |
| Dolce & Salato | Ristoranti | Via Reno 5/B | 080 2464481 |
| Dolce Stil Novo | Ristoranti | Viale Martiri 1799 79 | 080 8760895 |

Inizio pagina 2: Dulcamara (Via Monte Rosa 22, 080 3144403), Flavour (Via Quasimodo
Salvatore 15, 080 3142021), Gioja (Via Persio Orazio 66, 080 3031336), I Peccati dei
Fratelli Pisani, …

## 5. Anomalie e decisioni aperte

- **Perimetro**: TheFork e PagineBianche mescolano comuni a decine di km. Filtro
  obbligatorio su CAP 70022 e `addressLocality = Altamura`; l'omonimia "Altamura
  Pizza/Trattoria" negli USA è già esclusa per costruzione, ma le fonti SEO vanno
  comunque ignorate (vedi `AGENTS.md`).
- **Deduplica**: "Binario 24" compare due volte con numeri diversi (376 2566911 e
  080 2377922) → stesso locale, telefoni multipli. "Fior di Pizza", "Villa di Bacco",
  "Osteria Mo è", "Gusto d'Altura", "La Locanda di Alice", "Pamaro", "Dodo" compaiono su
  tutte e tre le fonti → una riga, tre fonti in Fase 2.
- **Masseria/agriturismi** (Chinunno, Madonna dell'Assunta): nel comune ma fuori centro,
  menu fisso, nessun delivery. Decisione del proprietario ancora da prendere: includere
  con categoria `altro` + nota, oppure escludere.
- **Paninoteche e panzerotterie** sono quasi assenti dalle piattaforme: lì l'universo
  va costruito con ricerca diretta (Instagram/web), non con Just Eat.

## 6. Esito Fase 1 — `data/locali.csv`

Chiusa il 2026-10-31 con **128 righe** (piano: 60-70 attese).

| Categoria | Righe |
|---|---|
| ristorante | 59 |
| pizzeria | 47 |
| paninoteca | 9 |
| forno-caffetteria | 4 |
| hamburgheria | 4 |
| panzerotteria | 3 |
| altro (agriturismi) | 2 |
| **Totale** | **128** |

Metodo:

- universo costruito su PagineBianche (categorie `ristorante`, `pizzeria`,
  `trattoria`, `osteria`, `pub`, `birreria`, `paninoteca`, `rosticceria`,
  `panificio`), filtrando `addressLocality = Altamura` e CAP `70022`;
- incrocio con Just Eat e TheFork per la colonna `piattaforme_delivery`;
- esclusi bar puri, caffetterie, pasticcerie, panifici senza consumo sul posto,
  caseifici, enoteche, laboratori;
- generatore riproducibile: `scripts/build_locali.py`.

Punti aperti da risolvere in Fase 2:

- **doppioni storici**: `pizzeria-ciccio-e-ciabatta` e "480 Gradi Storie di Gusto"
  condividono indirizzo e telefono; `binario-24` ha due telefoni; `fior-di-pizza`,
  `pizzeria-levante`, Dambrosio (3 sedi) e `sale-e-pepe` hanno più punti vendita —
  le righe sono state tenute separate, da confermare con i menu.
- **locali solo da PagineBianche e senza riscontri** (Clemente, Bolognese, Pugliese,
  Dafood, Wood, Porta Aurea, Puffo Golosone…): possibile insegna chiusa o rinominata.
- **indirizzi mancanti**: `the-grill`, `shibumi`, `forno-santa-caterina`.
- **categoria da confermare**: `A.R. Food & Consulting` escluso (catering),
  `Du'Lè`, `Popof`, `W & C`, `Lama`, `Mare e Sapori`, `Ziccardi` esclusi come
  rosticcerie/laboratori senza somministrazione — da rivalutare se aprono al pubblico.

## 7. Prossimi passi

1. Parse JSON-LD delle pagine PagineBianche già scaricate (ristorante 1-3, trattoria
   1-2, osteria 1-3, pub 1-4) + scaricare `pizzeria`, `paninoteca`, `panificio`,
   `birreria`, `rosticceria`.
2. Filtro CAP/località, deduplica, prima stesura di `data/locali.csv`.
3. Merge Just Eat + TheFork (pagine 2-4).
4. Fase 2: discovery fonti menu.

Snapshot grezzi in `raw/` (non versionati, cfr. `.gitignore`).
