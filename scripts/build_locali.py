#!/usr/bin/env python3
"""Genera data/locali.csv (Fase 1) da lista curata + incrocio Just Eat/TheFork."""
import csv, json, unicodedata, re

D = "2026-10-31"

# Just Eat: slug locale su justeat.it/restaurants-<slug>/menu
JE = {
 "sale-e-pepe-take-away": "sale-e-pepe-take-away-altamura",
 "maninpasta": "maninpasta-altamura",
 "ham-hamburgheria": "ham-hamburgheria-altamura",
 "sape-pizzeria-takeaway": "sape-pizzeria-takeaway-altamura",
 "fior-di-pizza": "fior-di-pizza-altamura-70022",
 "pizza-e-core": "pizza-and-core-pizzeria-napoletana-altamura",
 "pizzeria-non-mi-dire": "pizzeria-non-mi-dire-altamura-70022",
 "pizzeria-alta-pizza": "pizzeria-alta-pizza-altamura",
 "tandem-food": "tandem-food-altamura",
 "arte-pizza": "arte-pizza-altamura",
 "degu-ham": "degu-ham-altamura",
 "nagoya": "nagoya-ristorante-fusion-altamura",
 "kebabberia-group": "kebabberia-group-altamura",
 "umami-pizzeria": "umami-pizzeria-altamura-70022",
 "piada-la-piadineria-artigianale": "piada-la-piadineria-artigianale-70022",
 "birbacco": "birbacco-pizzeria-hamburgeria-altamura",
 "miura-pizza-lab": "miura-pizza-lab-altamura",
 "sponzami": "sponzami-altamura-70022",
 "the-grill": "the-grill---specialita-carne-and-panini-70022",
 "shibumi": "shibumi-altamura---fusion-restaurant-70022",
 "salumeria-boccon-di-vino": "salumeria-boccon-di-vino-altamura",
 "bistrot-del-borgo": "bistrot-del-borgo-altamura",
}
# TheFork: slug ristorante
TF = {
 "fior-di-pizza": "fior-di-pizza-r813416",
 "pamaro": "pamaro-r869167",
 "mo-e-osteria": "osteria-mo-e-r552311",
 "dodo-sapori-di-pizza": "dodo-sapori-di-pizza-r858495",
 "gusto-d-altura": "gusto-d-altura-r860158",
 "la-locanda-di-alice": "la-locanda-di-alice-r850654",
 "mercadante-pizza-e-cucina": "mercadante-pizza-e-cucina-r705459",
 "hostari": "hostari-osteria-moderna-r810023",
 "villa-di-bacco": "villa-di-bacco-r500397",
}

# (id, nome, categoria, indirizzo, telefono, note)
R = [
 # --- pizzerie
 ("pizzeria-levante","Pizzeria Levante","pizzeria","Via Fiume 4/A","080 3101051","Due insegne: Via Fiume 4/A e Viale Martiri 1799 94/96 (stesso telefono)"),
 ("pizzeria-levante-martiri","Pizzeria Levante (Viale Martiri)","pizzeria","Viale Martiri 1799 94/96","080 3101051","Secondo punto vendita, vedi pizzeria-levante"),
 ("fior-di-pizza","Fior di Pizza","pizzeria","Via Salvatore Quasimodo 36/38","080 4046733","Seconda sede in Via Parisi 83"),
 ("fior-di-pizza-parisi","Fior di Pizza (Via Parisi)","pizzeria","Via Parisi 83","080 4046733","Seconda sede, stesso telefono"),
 ("pizza-e-core","Pizza & Core Pizzeria Napoletana","pizzeria","Via Centonze Antonia 2","080 8097283","Microsito proprio che rimanda a Just Eat"),
 ("pizzeria-non-mi-dire","Pizzeria Non Mi Dire","pizzeria","Via Lucera 29","","Solo piattaforme"),
 ("pizzeria-alta-pizza","Pizzeria Alta Pizza","pizzeria","Via San Gennaro 3B","","Solo piattaforme"),
 ("arte-pizza","Arte Pizza","pizzeria","Via Bergamo 61","","Solo piattaforme"),
 ("pizzeria-vecchio-ponte","Pizzeria Vecchio Ponte","pizzeria","Via Araldo di Crollalanza 27","080 3112339",""),
 ("mercadante-pizza-e-cucina","Mercadante Pizza e Cucina","pizzeria","Via Bruxelles 3","080 3116311","TheFork Insider"),
 ("dodo-sapori-di-pizza","DODO Sapori di Pizza","pizzeria","Via Caduti di Nassiriya 26","333 7586819",""),
 ("pizzeria-al-cantuccio","Pizzeria Al Cantuccio","pizzeria","Via Carlo Fiore 21","080 3105486",""),
 ("pizzeria-ciccio-e-ciabatta","Pizzeria Ciccio e Ciabatta","pizzeria","Via Selva 2/4","080 9675951","In PagineBianche anche come \"480 Gradi Storie di Gusto\", stesso indirizzo e telefono: probabile insegna cambiata"),
 ("pizzeria-dambrosio-piccinni","Pizzeria Dambrosio","pizzeria","Via Piccinni 16","080 3103183","Uno dei tre punti vendita Dambrosio"),
 ("pizzeria-dambrosio-selva","Pizzeria Dambrosio (Via Selva)","pizzeria","Via Selva 49","080 3140950","Uno dei tre punti vendita Dambrosio"),
 ("pizzeria-dambrosio-abetone","Pizzeria Dambrosio (Via Abetone)","pizzeria","Via Abetone 1/3","080 3140950","Uno dei tre punti vendita Dambrosio"),
 ("pizzeria-felici-capricci","Felici Capricci","pizzeria","Corso Vittorio Emanuele 20","080 3149328",""),
 ("pizzeria-forte","Pizzeria Forte Giuseppe","pizzeria","Piazza Madonna dei Martiri 22","080 3101614","Secondo indirizzo in Via Napoli 19"),
 ("pizzeria-il-pizzico","Pizzeria Il Pizzico","pizzeria","Via Castello 1","080 9672296","Anche come \"Il Pizzico di Loviglio\", Via Nola 3/A"),
 ("pizzeria-la-rotonda","La Rotonda","pizzeria","Viale Martiri 1799 145","080 3323946",""),
 ("pizzeria-la-voglia","La Voglia - Pizza e Co.","pizzeria","Via IV Novembre 13","351 9003524",""),
 ("pizzeria-maninpasta","Pizzeria Maninpasta","pizzeria","Via Monopoli 9","339 4546756",""),
 ("pizzeria-mercatale","Mercatale","pizzeria","Via Teatro Mercadante 48","379 1594559",""),
 ("pizzeria-miura","Miura Pizza Lab","pizzeria","Piazza De Napoli 10","","Solo piattaforme"),
 ("pizzeria-new-bietigheim","New Bietigheim","pizzeria","Via Santeramo 50/A","080 3112659",""),
 ("pizzeria-rosticceria-bietigheim","Pizzeria Rosticceria Bietigheim","pizzeria","Via Vincenzo Russo 15/17","080 3102499",""),
 ("pizzeria-nonna-tere","Nonna Tere'","pizzeria","Via Lama di Cervo 173","080 3849540",""),
 ("pizzeria-pizero","Pizero","pizzeria","Via Golgota 19","348 7287215",""),
 ("pizzeria-i-5-sensi","Pizzeria I 5 Sensi","pizzeria","Via Cavour 4","080 3113124",""),
 ("pizzeria-aldo-moro","Pizzeria Aldo Moro","pizzeria","Via Carpentino 39","080 3118899","Asporto e consegna"),
 ("pizzeria-alfredo","Pizzeria Alfredo","pizzeria","Corso Umberto I 26","080 3106237",""),
 ("pizzeria-antichi-sapori","Pizzeria Antichi Sapori e Fantasia","pizzeria","Via Selva 194","328 8243886",""),
 ("pizzeria-peach-pit","Pizzeria Peach Pit","pizzeria","Via Cilea 14","080 3111111",""),
 ("sale-e-pepe-take-away","Sale e Pepe Take Away","pizzeria","Via Gravina 104","080 3112659","In PagineBianche anche \"Sale & Pepe Pizzeria\", Via Carpentino 11"),
 ("sape-pizzeria-takeaway","Sapè Pizzeria Takeaway","pizzeria","Via IV Novembre 13","080 9950009","Microsito proprio che rimanda a Just Eat"),
 ("pizzeria-soel","Pizzeria Soel","pizzeria","Via delle Cappelle 28/D","327 5724509",""),
 ("pizzeria-spiga-doro","Pizzeria Spiga D'Oro","pizzeria","Via Pietro Colletta 224","080 3149130",""),
 ("umami-pizzeria","Umami Pizzeria","pizzeria","Via Santeramo 48","080 3520733",""),
 ("pizzeria-porta-aurea","Porta Aurea","pizzeria","Via Cassano 131","080 3115409",""),
 ("pizzeria-puffo-golosone","Puffo Golosone","pizzeria","Via La Carrera 154","080 6981591",""),
 ("pizzeria-pugliese","Pugliese","pizzeria","Via Corato 403","339 3880489",""),
 ("pizzeria-volosa","Volosa - Oltre la Pizza","pizzeria","Via Manfredonia 8","080 5678950",""),
 ("pizzeria-wood","Wood","pizzeria","Via Laudati Leopoldo 11","080 3102492",""),
 ("pizzeria-clemente","Clemente S.a.s.","pizzeria","Via Foscolo 66","080 3101093",""),
 ("pizzeria-bolognese","Bolognese","pizzeria","Via dell'Ortica 28","080 3114297",""),
 ("dafood","Dafood","pizzeria","Corso Vittorio Emanuele 118","080 2371996",""),
 ("kyklos","Kyklos Ristorante Pizzeria","ristorante","Via Trentacapilli 42","333 6824163","Sito proprio: web.kyklosaltamura.it"),
 ("100-metri-quadri","100 Metri Quadri","pizzeria","Via Cassano delle Murge 277","080 3141596",""),
 ("pizzeria-la-brace","Ristorante Pizzeria La Brace","ristorante","Via Brescia 54","327 4924109",""),
 ("pizzeria-birbacco","Birbacco Pizzeria Hamburgeria","hamburgheria","Via Caduti delle Foibe 15/17","080 3106980",""),
 ("kebabberia-group","Kebabberia Group","paninoteca","Via Pietro Colletta 6","344 6644601",""),
 ("devo","Devo Ristorante Pizzeria","ristorante","Viale Martiri 1799 129","080 8090032",""),
 ("binario-24","Binario 24 Ristorante","ristorante","Piazza Stazione 24","376 2566911","In PagineBianche anche con telefono 080 2377922"),
 # --- paninoteche / hamburgherie / panzerotterie
 ("ham-hamburgheria","Ham. Hamburgheria","hamburgheria","Via Golgota 86","",""),
 ("the-grill","The Grill - Specialità Carne & Panini","hamburgheria","","","Indirizzo da verificare"),
 ("degu-ham","Degù Ham","paninoteca","Via Bari 112","","Vedi anche \"Degu\", Via IV Novembre 120 (insegna collegata)"),
 ("sponzami","Sponzami","paninoteca","Piazza Mercadante 9","",""),
 ("piada-la-piadineria-artigianale","Piada' La Piadineria Artigianale","paninoteca","Via Vittorio Veneto 47","",""),
 ("panzerotteria-panze","Panzerotteria Panzè","panzerotteria","Via Bari 110","080 6454628","Microsito proprio che rimanda a Just Eat"),
 ("panzerotteria-stolfa","Panzerotteria Stolfa","panzerotteria","Strada Privata Zignago 16","080 2372341",""),
 ("il-panzerotto-re-umberto","Il Panzerotto Re Umberto I","panzerotteria","Corso Umberto I 36","080 3322480",""),
 ("osteria-artizen","Osteria Artizen Ristopub","paninoteca","Via Bari 192","080 3147101",""),
 ("sherwood-birreria","Sherwood Birreria","paninoteca","Via Caduti di Via Fani 3","080 3144975",""),
 ("bottega-del-luppolo","Bottega del Luppolo","paninoteca","Via Almirante 113","391 3042396",""),
 ("diplomatico-club","Diplomatico Club","paninoteca","Via dell'Asfodelo 76","080 6457722",""),
 ("midnites","Midnite's","paninoteca","Corso Umberto I 4/A","333 4083646",""),
 ("alterego-comfort-food","Alterego Comfort Food","hamburgheria","Via Alberobello 12","371 1955234","Vedi anche Black Pepper Comfort Food (alteregoaltamura.it)"),
 # --- ristoranti
 ("gioja","Gioja Ristorante","ristorante","Via Orazio Persio 66","080 3031336","TheFork Insider"),
 ("pamaro","Pamaro","ristorante","Via Monte Rosa 14","329 7847104",""),
 ("mo-e-osteria","Osteria Mo è","ristorante","Via Luca de Samuele Cagnazzi 27","334 9406423",""),
 ("gusto-d-altura","Gusto d'Altura","ristorante","Via Bari 110","376 2567744",""),
 ("la-locanda-di-alice","La Locanda di Alice","ristorante","Piazza Marconi 4","348 3598539",""),
 ("hostari","Hostàrì Osteria Moderna","ristorante","Via Massimo D'Azeglio 6","080 6932019",""),
 ("villa-di-bacco","Villa di Bacco","ristorante","Via Mura Megalitiche 53","340 0593024",""),
 ("dulcamara","Dulcamara","ristorante","Via Monte Rosa 22","080 3144403",""),
 ("flavour","Flavour","ristorante","Via Salvatore Quasimodo 15","080 3142021",""),
 ("origini","Origini Vino & Cucina","ristorante","Via IV Novembre 30/C","080 6457928",""),
 ("oltremura","Oltremura","ristorante","Via Orazio Persio 58","080 3106874",""),
 ("otto","Otto","ristorante","Via Cufra 73","080 9677030",""),
 ("oste","Ostè","ristorante","Via Selva 130","328 5808905",""),
 ("rubino-esperienze-di-gusto","Rubino Esperienze di Gusto","ristorante","Via Selva 97","080 9266401",""),
 ("stile-libero","Stile Libero","ristorante","Via Mura Megalitiche 1","080 3325581",""),
 ("tanamatta","Tanamatta","ristorante","Via Giannuzzi 36","392 3519972",""),
 ("u-mirre","U'Mirre","ristorante","Via Melodia 3","393 7341185",""),
 ("una-nicchia-di-sapori","Una Nicchia di Sapori","ristorante","Via XX Settembre 10","080 2376796",""),
 ("romana-bistrot","Romana Bistrot","ristorante","Via Marecchia 19","080 8839175",""),
 ("shodai","Shodai Sushi Bar","ristorante","Via Amedeo di Savoia 16","080 2123656",""),
 ("sushikom","Sushikom","ristorante","Via Gravina 3","328 8855687",""),
 ("sushitao","Sushitao","ristorante","Via Bari 110","348 0595518",""),
 ("nagoya","Nagoya Ristorante Fusion","ristorante","Via Selva 192","334 2529169",""),
 ("shibumi","Shibumi Fusion Restaurant","ristorante","","","Nuovo su Just Eat, indirizzo da verificare"),
 ("osteria-il-postaccio","Osteria Il Postaccio","ristorante","Via Belgrado 31","328 2144886",""),
 ("trattoria-federico-ii","Trattoria Federico II","ristorante","Via Luciani 3","080 3145699",""),
 ("trattoria-cenzino","Trattoria Rosticceria Cenzino","ristorante","Via Sant'Ambrogio 15","080 3117049",""),
 ("tre-archi","Tre Archi Trattoria Pizzeria Take Away","ristorante","Via San Michele 28","080 3115569",""),
 ("antica-osteria-pein-assutt","Antica Osteria Pein Assutt","ristorante","Corso Umberto I 56","080 3118313",""),
 ("antica-osteria-santa-chiara","Antica Osteria Santa Chiara La Grotta","ristorante","Via Santa Chiara 6","349 0930312",""),
 ("salumeria-boccondivino","Salumeria Boccondivino","ristorante","Via Santeramo 136","333 3226961","Su Just Eat come \"Salumeria Boccon di Vino\""),
 ("calvi","Calvi Ristorante","ristorante","Via Bari 134","340 7692750","Guida Michelin"),
 ("biancospino","Ristorante Biancospino","ristorante","Via Maestri del Lavoro 5","080 3102140","Anche \"Ristorante del Corso - Biancospino\", telefono 347 9992636"),
 ("braceria-casa-del-vitello","Braceria Casa del Vitello","ristorante","Via Santeramo 123","080 8097315",""),
 ("be-steak-house","Be-Steak House","ristorante","Via Caduti delle Foibe 50","334 8411121",""),
 ("meatico","Meatico","ristorante","Via Almirante 105/107","080 9025077",""),
 ("locanda-san-nicola","Locanda San Nicola","ristorante","Via Manfredi 25/27","080 3101055",""),
 ("malandri","Malandrì","ristorante","Via Filo Bisanzio 6","328 4448775",""),
 ("malanghino","Malanghino","ristorante","Via Bassano 38","335 6294144",""),
 ("dharma","Dharma","ristorante","Via Bainsizza 27","346 0754048",""),
 ("del-corso","Del Corso","ristorante","Corso Federico II di Svevia 53/A","391 1879697",""),
 ("ammorsi","Ammorsi","ristorante","Piazza Duomo","080 6926170",""),
 ("asfodelo","Asfodelo Ristorante","ristorante","SP157 km 3","349 1180347",""),
 ("la-bella-vita","La Bella Vita B&B Braceria","ristorante","Piazza Marconi 4","328 3229757",""),
 ("i-peccati-dei-fratelli-pisani","I Peccati dei Fratelli Pisani","ristorante","Corso Federico II di Svevia 53/A","080 9678447",""),
 ("il-teatro-del-gusto","Il Teatro del Gusto","ristorante","Piazza Mercadante 9","392 1819267",""),
 ("bistrot-del-borgo","Bistrot del Borgo","ristorante","Piazza Duomo 5","080 8495984",""),
 ("black-pepper","Black Pepper Comfort Food","ristorante","Via Matera 13","080 2223800","Sito: alteregoaltamura.it"),
 ("des-artist","Des Artist","ristorante","Via Reno 3","080 3149957",""),
 ("dolce-e-salato","Dolce & Salato","ristorante","Via Reno 5/B","080 2464481",""),
 ("dolce-stil-novo","Dolce Stil Novo","ristorante","Viale Martiri 1799 79","080 8760895",""),
 ("famiglia-fieschi","Famiglia Fieschi (Pancotto Cucina Altamurana)","ristorante","Via Bari 19","080 3142497",""),
 ("papilla","Papilla","ristorante","Via Locorotondo 11","080 3113449",""),
 ("canarute","CanarùTe","ristorante","Via Martiri 11 Settembre 2001 19","080 9140100",""),
 ("alla-povera-vita","Alla Povera Vita","ristorante","Piazza Marconi 4","080 4033769",""),
 # --- forni con somministrazione
 ("panificio-anselmo-maestri","Panificio Anselmo-Maestri Fornai","forno-caffetteria","Via Caduti di Nassiriya 180","080 3141179","Forno storico, in PagineBianche anche come ristorante"),
 ("panificio-del-lago","Panificio del Lago","forno-caffetteria","Via Matera 28","080 3112888",""),
 ("panificio-gusto-e-bonta","Panificio Gusto e Bontà","forno-caffetteria","Corso Umberto I 91","080 4117921",""),
 ("forno-santa-caterina","Antico Forno Santa Caterina dal 1306","forno-caffetteria","","","Segnalato da Tripadvisor, da verificare"),
 # --- agriturismi (fuori centro, menu fisso)
 ("masseria-chinunno","Agriturismo Masseria Chinunno","altro","SP 18 km 8.3","080 3140185","Fuori centro, menu fisso, no delivery"),
 ("madonna-dell-assunta","Agriturismo Madonna dell'Assunta","altro","SP 235 Altamura-Gioia del Colle","334 8413839","Fuori centro, menu fisso, no delivery"),
]

rows = []
seen = set()
for r in R:
    rid, nome, cat, via, tel, note = r
    if not nome:
        continue
    if rid in seen:
        raise SystemExit("id duplicato: " + rid)
    seen.add(rid)
    plat = []
    if rid in JE:
        plat.append("just-eat")
    if rid in TF:
        plat.append("thefork")
    nf = len(plat)
    rows.append({
        "id": rid, "nome": nome, "categoria": cat, "indirizzo": via,
        "telefono": tel, "sito": "",
        "piattaforme_delivery": ";".join(plat),
        "ha_menu_online": "si" if nf else "no",
        "n_fonti": nf, "note": note, "ultima_verifica": D,
    })

rows.sort(key=lambda r: (r["categoria"], r["nome"].lower()))
cols = ["id","nome","categoria","indirizzo","telefono","sito","piattaforme_delivery",
        "ha_menu_online","n_fonti","note","ultima_verifica"]
with open("data/locali.csv","w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

print("righe:", len(rows))
from collections import Counter
print(Counter(r["categoria"] for r in rows))
print("con piattaforma nota:", sum(1 for r in rows if r["n_fonti"]))
