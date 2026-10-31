#!/usr/bin/env python3
"""panem — discovery fonti menu, estrazione prezzi, refresh periodico.

Uso:
  python3 scripts/panem.py discover   # trova i siti propri (varianti dominio + seed)
  python3 scripts/panem.py scrape     # scarica fonti e estrae menu/prezzi
  python3 scripts/panem.py refresh    # ricontrolla le fonti note, aggiorna hash/date
  python3 scripts/panem.py status     # riepilogo copertura

Scrive:
  data/locali.csv            (colonna sito aggiornata dal discover)
  data/fonti-menu.csv        (una riga per fonte)
  data/piatti.csv            (una riga per piatto+prezzo estratto)
  data/monitoraggio.csv      (hash/HTTP/date per il change detection)
  raw/YYYY-MM-DD-<id>-<tipo>.<ext>  (snapshot, gitignored)

Regole: max 1 richiesta/secondo per dominio, robots.txt rispettato, nessun
dato inventato (se non si estrae nulla la fonte resta con prezzi=no).
"""
import ast
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.robotparser
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(ROOT, "raw")
TODAY = date.today().isoformat()
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
DELAY = 1.0
MAX_MENU_PAGES = 4
MAX_PDFS = 3
TIMEOUT = 25

SPAM_DOMAINS = (
    "menuwithpricesonline", "menu-all", "restaurants-us", "menuweb.menu",
    "piatti.menu", "restaurants-info", "tripadvisor", "thefork", "justeat",
    "glovo", "facebook", "instagram", "google.", "youtube", "wikipedia",
    "paginebianche", "paginegialle", "opendi", "tuttocitta", "menu.cooperto.it",
)

SEEDS = {
    "pizzeria-levante": "https://www.pizzerialevante.it",
    "pizzeria-levante-martiri": "https://www.pizzerialevante.it",
    "degu-ham": "https://deguham.com",
    "pancaffe": "https://pancaffe.com",
    "kyklos": "https://web.kyklosaltamura.it",
    "pizza-e-core": "https://pizza-e-core-pizzeria-napoletana.it",
    "panzerotteria-panze": "https://panzealtamura.it",
    "black-pepper": "https://www.alteregoaltamura.it",
}

_last_hit = {}
_robots = {}


# ---------------------------------------------------------------- utilities
def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


def read_csv(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows, cols):
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def domain_of(url):
    m = re.match(r"https?://([^/]+)", url or "")
    return (m.group(1) if m else "").lower()


def polite(url):
    dom = domain_of(url)
    last = _last_hit.get(dom, 0)
    wait = DELAY - (time.time() - last)
    if wait > 0:
        time.sleep(wait)
    _last_hit[dom] = time.time()


def robots_ok(url):
    dom = domain_of(url)
    if dom not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"https://{dom}/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None
        _robots[dom] = rp
    rp = _robots[dom]
    return True if rp is None else rp.can_fetch(UA, url)


def fetch(url, binary=False):
    """GET con curl. Ritorna (status, final_url, body, content_type)."""
    polite(url)
    cmd = ["curl", "-sL", "-m", str(TIMEOUT), "--compressed", "-A", UA,
           "-H", "Accept-Language: it-IT,it;q=0.9", "-w", "\n@@%{http_code}@@%{content_type}@@%{url_effective}", url]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT + 10)
    except subprocess.TimeoutExpired:
        return 0, url, b"", ""
    raw = out.stdout
    marker = raw.rfind(b"\n@@")
    if marker < 0:
        return 0, url, b"", ""
    meta = raw[marker + 3:].decode("utf-8", "ignore").split("@@")
    body = raw[:marker]
    status = int(meta[0]) if meta and meta[0].isdigit() else 0
    ctype = meta[1] if len(meta) > 1 else ""
    final = meta[2] if len(meta) > 2 else url
    if not binary:
        return status, final, body.decode("utf-8", "ignore"), ctype
    return status, final, body, ctype


def save_raw(locale_id, kind, body, ext):
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, f"{TODAY}-{locale_id}-{kind}.{ext}")
    mode = "wb" if isinstance(body, bytes) else "w"
    with open(path, mode) as f:
        f.write(body)
    return path


def strip_tags(text):
    text = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>|</(p|div|li|tr|h[1-6]|section|article|td|th)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.split("\n")]
    return [l for l in lines if l]


def extract_headings(page):
    out = []
    for m in re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", page, re.S | re.I):
        txt = re.sub(r"<[^>]+>", " ", m)
        txt = re.sub(r"\s+", " ", html.unescape(txt)).strip()
        if txt:
            out.append(txt)
    return out


def extract_links(page, base):
    links = []
    for href, label in re.findall(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', page, re.S | re.I):
        label = re.sub(r"<[^>]+>", " ", label)
        label = re.sub(r"\s+", " ", html.unescape(label)).strip()
        low = (href + " " + label).lower()
        if re.search(r"menu|menù|carta|listino|prezzi|pdf", low):
            if href.startswith("/"):
                m = re.match(r"(https?://[^/]+)", base)
                href = (m.group(1) if m else base) + href
            elif not href.startswith("http"):
                href = base.rstrip("/") + "/" + href.lstrip("./")
            links.append((href, label))
    seen, out = set(), []
    for u, l in links:
        key = u.split("#")[0]
        if key in seen or any(s in key for s in SPAM_DOMAINS):
            continue
        if re.search(r"wp-json|oembed|\.css|\.js", key):
            continue
        seen.add(key)
        out.append((key, l))
    return out


# ---------------------------------------------------------------- JSON-LD
def jsonld_blocks(page):
    blocks = []
    for b in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        try:
            d = json.loads(b.strip())
        except Exception:
            continue
        stack = d if isinstance(d, list) else [d]
        while stack:
            x = stack.pop(0)
            if isinstance(x, list):
                stack.extend(x)
                continue
            if not isinstance(x, dict):
                continue
            blocks.append(x)
            for k in ("@graph", "hasMenu", "menu"):
                v = x.get(k)
                if isinstance(v, (dict, list)):
                    stack.extend(v if isinstance(v, list) else [v])
    return blocks


def menu_from_jsonld(blocks):
    """Ritorna (items, sezioni, has_menu_url). items = [(sezione, piatto, prezzo)]."""
    items, sections = [], []
    for x in blocks:
        t = x.get("@type")
        t = " ".join(t) if isinstance(t, list) else str(t)
        if "MenuSection" in t or "Menu" == t:
            name = x.get("name")
            if name:
                sections.append(str(name))
        if "MenuItem" in t:
            name = x.get("name")
            price = None
            off = x.get("offers")
            if isinstance(off, dict):
                price = off.get("price") or off.get("lowPrice")
            if price is None:
                price = x.get("price")
            if name and price is not None:
                items.append(("", str(name), str(price)))
    return items, sections


# ---------------------------------------------------------------- prezzi
PRICE_RE = re.compile(r"(?:€\s*)?(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:€|eur(?:o)?\b)", re.I)
PRICE_ANY = re.compile(r"€\s*(\d{1,3}(?:[.,]\d{1,2})?)|(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:€|eur(?:o)?\b)", re.I)
BARE_PRICE_RE = re.compile(r"^(?:€\s*)?(\d{1,3}(?:[.,]\d{1,2})?)\s*€?$")


def to_price(raw):
    try:
        v = float(str(raw).replace(",", ".").replace("€", "").strip())
    except ValueError:
        return None
    return v if 0.3 <= v <= 250 else None


def first_price(line):
    m = PRICE_ANY.search(line)
    if not m:
        return None
    raw = m.group(1) or m.group(2)
    return to_price(raw), m.start(), m.end()


def is_price_line(line):
    """Riga fatta solo di prezzi/separatori (es. '€5,50 · Menu €7,90')."""
    if not PRICE_ANY.search(line):
        return False
    rest = PRICE_ANY.sub("", line)
    rest = re.sub(r"menu|coperto|euro|€|\b(?:e|a|da|con|il|la)\b", "", rest, flags=re.I)
    rest = re.sub(r"[^A-Za-zÀ-ÿ]", "", rest)
    return len(rest) <= 6


def looks_like_section(line):
    s = line.strip()
    if not (2 <= len(s) <= 35) or re.search(r"\d", s):
        return False
    if PRICE_ANY.search(s):
        return False
    words = s.split()
    return (s.isupper() and len(words) <= 5) or (s.endswith(":") and len(words) <= 4)


def clean_name(name):
    name = re.sub(r"\s{2,}", " ", name).strip(" .-–—:|")
    return name


NOISE_NAMES = ("allergen", "titolo sintetico", "totale", "subtotale")


def good_name(name):
    if not (3 <= len(name) <= 70):
        return False
    low = name.lower()
    if any(n in low for n in NOISE_NAMES):
        return False
    if re.search(r"\d{3}[- ]\d{4,}", name):
        return False
    return bool(re.search(r"[A-Za-zÀ-ÿ]{3}", name))


def name_before(lines, i):
    for j in range(i - 1, max(-1, i - 4), -1):
        cand = clean_name(lines[j])
        if cand.startswith("+") or len(cand) < 6:
            continue
        if len(cand) > 55 or cand.count(",") >= 3:
            continue
        if re.match(r"^\d", cand) or "°" in cand:
            continue
        return cand
    return None


def parse_lines(lines, headings=()):
    """Estrae (sezione, piatto, prezzo) da righe di testo. Euristica prudente."""
    headings = {h.strip().lower() for h in headings}
    items, section = [], ""
    for i, line in enumerate(lines):
        if line.strip().lower() in headings or looks_like_section(line):
            section = line.strip(" :").capitalize()
            continue
        got = first_price(line)
        bare = False
        if got:
            price, a, b = got
        else:
            bm = BARE_PRICE_RE.match(line)
            if not bm:
                continue
            price, a, b, bare = to_price(bm.group(1)), 0, 0, True
        if not price:
            continue
        if bare or is_price_line(line):
            name = name_before(lines, i)
            if name and good_name(name):
                items.append((section, name, price))
            continue
        if len(line) > 120:
            continue
        name = clean_name(line[:a] + " " + line[b:])
        if good_name(name):
            items.append((section, name, price))
    return items


def pdf_text(body):
    try:
        import io
        from pypdf import PdfReader
    except ImportError:
        return []
    try:
        r = PdfReader(io.BytesIO(body))
        txt = "\n".join((p.extract_text() or "") for p in r.pages)
    except Exception:
        return []
    return [re.sub(r"\s+", " ", l).strip() for l in txt.split("\n") if l.strip()]


# ---------------------------------------------------------------- discover
def guess_domains(row):
    n = norm(row["nome"])
    cat = row["categoria"]
    out = []
    base = [n]
    if cat == "ristorante" and not n.startswith("ristorante"):
        base.append("ristorante" + n)
    if cat == "pizzeria" and not n.startswith("pizzeria"):
        base.append("pizzeria" + n)
    for b in base:
        for tld in (".it", ".com"):
            out.append(b + tld)
    if "altamura" not in n:
        out.append(n + "altamura.it")
    return list(dict.fromkeys(out))


def verify_site(row, url):
    status, final, body, _ = fetch(url)
    if not status or status >= 400 or len(body) < 500:
        return None
    low = body.lower()
    if "altamura" not in low:
        return None
    tokens = [t for t in re.split(r"[^a-z0-9]+", norm(row["nome"])) if len(t) >= 4]
    if tokens and not any(t in norm(body) for t in tokens[:3]):
        return None
    return final


def cmd_discover():
    rows = read_csv("locali.csv")
    for r in rows:
        if r["sito"].strip():
            continue
        if r["id"] in SEEDS:
            r["sito"] = SEEDS[r["id"]]
            continue
        for dom in guess_domains(r):
            final = verify_site(r, "https://" + dom)
            if final:
                r["sito"] = final
                print(f"[discover] {r['id']} -> {final}")
                break
    write_csv("locali.csv", rows, list(rows[0].keys()))
    n = sum(1 for r in rows if r["sito"].strip())
    print(f"[discover] locali con sito: {n}/{len(rows)}")


# ---------------------------------------------------------------- scrape
def platform_urls():
    """Slug Just Eat/TheFork dichiarati in build_locali.py."""
    path = os.path.join(ROOT, "scripts", "build_locali.py")
    src = open(path, encoding="utf-8").read()
    je, tf = {}, {}
    for name, target in (("JE", je), ("TF", tf)):
        m = re.search(rf"^{name} = (\{{.*?\n\}})", src, re.S | re.M)
        if m:
            target.update(ast.literal_eval(m.group(1)))
    out = []
    for lid, slug in je.items():
        out.append((lid, f"https://www.justeat.it/restaurants-{slug}/menu", "just-eat"))
    for lid, slug in tf.items():
        out.append((lid, f"https://www.thefork.it/ristorante/{slug}", "thefork"))
    return out


def content_sig(body):
    """Firma del contenuto: se ci sono piatti, hash dei piatti+prezzi; altrimenti del testo."""
    if isinstance(body, bytes):
        lines = pdf_text(body)
    else:
        lines = strip_tags(body)
    items = parse_lines(lines)
    if len(items) >= 3:
        sig = "\n".join(sorted(f"{norm(n)}|{p:.2f}" for _, n, p in items))
    else:
        sig = "\n".join(lines)
    return hashlib.sha256(sig.encode()).hexdigest()[:16]


def record_mon(monitor, changelog, url, status, body):
    blob = body if isinstance(body, bytes) else body.encode()
    h = content_sig(body)
    old = monitor.get(url)
    entry = {"url": url, "http_status": status, "content_hash": h, "bytes": len(blob),
             "ultima_verifica": TODAY,
             "ultima_modifica": (old or {}).get("ultima_modifica", TODAY),
             "note": "" if status == 200 else f"HTTP {status}"}
    if old and status == 200 and old.get("content_hash") != h:
        entry["ultima_modifica"] = TODAY
        entry["note"] = "contenuto cambiato"
        changelog.append((TODAY, url))
    monitor[url] = entry


def scrape_locale(row, fonti, piatti, monitor, changelog):
    lid = row["id"]
    site = row["sito"].strip()
    if not site:
        return
    status, final, page, ctype = fetch(site)
    record_mon(monitor, changelog, site, status, page)
    if status != 200 or not page:
        fonti.append({"locale_id": lid, "url": site, "tipo_fonte": "sito-proprio", "classe": "D",
                      "prezzi": "no", "allergeni": "no", "categorie_menu": "", "accessibilita_tecnica": "bloccato",
                      "note": f"HTTP {status}", "ultima_verifica": TODAY})
        return
    save_raw(lid, "home", page, "html")
    blocks = jsonld_blocks(page)
    ld_items, ld_sections = menu_from_jsonld(blocks)
    allergens = "si" if re.search(r"allergen", page, re.I) else "no"

    candidates = extract_links(page, final)[:MAX_MENU_PAGES + MAX_PDFS]
    menu_pages = [(u, l) for u, l in candidates if not u.lower().endswith(".pdf")]
    pdfs = [(u, l) for u, l in candidates if u.lower().endswith(".pdf")]
    if not menu_pages and not pdfs and not ld_items:
        base = final.rstrip("/")
        for suffix in ("/menu", "/menu/", "/il-menu", "/carta", "/men%C3%B9", "/menu.pdf"):
            st, fu, body, _ = fetch(base + suffix)
            if st == 200 and len(body) > 800 and not body.lstrip().startswith("%PDF"):
                if re.search(r"menu|carta|listino", body, re.I):
                    menu_pages.append((base + suffix, "fallback"))
                    break

    sources = []
    if ld_items:
        sources.append(("sito-proprio", final, "statico", ld_items, ld_sections, "JSON-LD Menu"))
    home_items = [i for i in parse_lines(strip_tags(page), extract_headings(page)) if i[2] >= 1]
    if len(home_items) >= 5:
        sources.append(("sito-proprio", final, "statico", home_items, [], "menu in home"))
    for u, label in menu_pages[:MAX_MENU_PAGES]:
        if not robots_ok(u):
            continue
        st, fu, body, _ = fetch(u)
        record_mon(monitor, changelog, u, st, body)
        if st != 200 or len(body) < 500:
            continue
        save_raw(lid, "menu-" + str(len(sources)), body, "html")
        items = parse_lines(strip_tags(body), extract_headings(body))
        if items:
            sources.append(("sito-proprio", u, "statico", items, [], ""))
    for u, label in pdfs[:MAX_PDFS]:
        if not robots_ok(u):
            continue
        st, fu, body, _ = fetch(u, binary=True)
        if st != 200 or len(body) < 1000:
            continue
        save_raw(lid, "menu-" + str(len(sources)), body, "pdf")
        items = parse_lines(pdf_text(body))
        if items:
            sources.append(("pdf", u, "statico", items, [], ""))

    if not sources:
        cls = "C" if re.search(r"\.(jpg|jpeg|png|webp)", page, re.I) and re.search(r"menu", page, re.I) else "D"
        fonti.append({"locale_id": lid, "url": site, "tipo_fonte": "sito-proprio", "classe": cls,
                      "prezzi": "no", "allergeni": allergens, "categorie_menu": "", "accessibilita_tecnica": "statico",
                      "note": "nessun menu con prezzi estraibile dalla home", "ultima_verifica": TODAY})
        return

    seen = set()
    for tipo, url, access, items, sections, note in sources:
        clean = []
        for sec, name, price in items:
            key = (norm(name), round(float(price), 2))
            if key in seen:
                continue
            seen.add(key)
            clean.append((sec, name, price))
        if not clean:
            continue
        with_price = len(clean)
        cls = "B" if tipo == "pdf" else "A"
        cats = ";".join(dict.fromkeys(s for s, _, _ in clean if s))[:200]
        fonti.append({"locale_id": lid, "url": url, "tipo_fonte": tipo, "classe": cls,
                      "prezzi": "si" if with_price >= 5 else "parziale",
                      "allergeni": allergens, "categorie_menu": cats,
                      "accessibilita_tecnica": access, "note": note, "ultima_verifica": TODAY})
        for sec, name, price in clean:
            piatti.append({"locale_id": lid, "fonte_url": url, "sezione": sec, "piatto": name,
                           "prezzo": f"{float(price):.2f}", "valuta": "EUR", "ultima_verifica": TODAY})


def cmd_scrape():
    locali = read_csv("locali.csv")
    fonti = {}
    monitor = {r["url"]: r for r in read_csv("monitoraggio.csv")}
    new_fonti, new_piatti = [], []
    changelog = []
    for row in locali:
        print(f"[scrape] {row['id']} {row['sito']}", flush=True)
        scrape_locale(row, new_fonti, new_piatti, monitor, changelog)
    # platform (solo catalogazione, nessun prezzo: sono bloccate/JS)
    for lid, url, tipo in platform_urls():
        st, _, body, _ = fetch(url)
        record_mon(monitor, changelog, url, st, body)
        if (lid, url) not in fonti:
            new_fonti.append({"locale_id": lid, "url": url, "tipo_fonte": tipo, "classe": "D",
                              "prezzi": "no", "allergeni": "no", "categorie_menu": "",
                              "accessibilita_tecnica": "bloccato" if st in (0, 403, 429) else "js",
                              "note": f"HTTP {st}; menu non estraibile senza browser",
                              "ultima_verifica": TODAY})

    all_fonti = [f for f in new_fonti if (f["locale_id"], f["url"]) not in fonti]
    for r in all_fonti:
        r.setdefault("ultima_verifica", TODAY)
    write_csv("fonti-menu.csv", all_fonti, ["locale_id","url","tipo_fonte","classe","prezzi","allergeni",
                                            "categorie_menu","accessibilita_tecnica","note","ultima_verifica"])
    seen_p = set()
    dedup = []
    for p in new_piatti:
        k = (p["locale_id"], p["fonte_url"], norm(p["piatto"]), p["prezzo"])
        if k in seen_p:
            continue
        seen_p.add(k)
        dedup.append(p)
    new_piatti = dedup
    write_csv("piatti.csv", new_piatti,
              ["locale_id","fonte_url","sezione","piatto","prezzo","valuta","ultima_verifica"])
    mon_all = list(monitor.values())
    for r in mon_all:
        r.setdefault("ultima_modifica", TODAY)
    write_csv("monitoraggio.csv", mon_all,
              ["url","http_status","content_hash","bytes","ultima_verifica","ultima_modifica","note"])
    update_locali_counters(all_fonti)
    if changelog:
        path = os.path.join(DATA, "changelog.csv")
        new = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["data", "url"])
            w.writerows(changelog)
    print(f"[scrape] fonti: {len(all_fonti)}  piatti: {len(new_piatti)}  cambiate: {len(changelog)}")


def update_locali_counters(fonti):
    locali = read_csv("locali.csv")
    by = {}
    for f in fonti:
        by.setdefault(f["locale_id"], []).append(f)
    for r in locali:
        fs = by.get(r["id"], [])
        r["n_fonti"] = str(len(fs))
        r["ha_menu_online"] = "si" if fs else "no"
        if fs and not r["sito"].strip():
            own = [f["url"] for f in fs if f["tipo_fonte"] in ("sito-proprio", "pdf")]
            if own:
                r["sito"] = own[0]
        plat = {f["tipo_fonte"] for f in fs if f["tipo_fonte"] in ("just-eat", "glovo", "thefork")}
        if plat:
            r["piattaforme_delivery"] = ";".join(sorted(plat))
    write_csv("locali.csv", locali, list(locali[0].keys()))


# ---------------------------------------------------------------- refresh
def cmd_refresh():
    """Ricontrolla le fonti note: aggiorna data e segnala cambi di contenuto."""
    fonti = read_csv("fonti-menu.csv")
    mon = {r["url"]: r for r in read_csv("monitoraggio.csv")}
    changed = []
    for url, old in mon.items():
        if any(s in url for s in ("justeat.it", "thefork.it", "glovo")):
            continue
        st, final, body, ctype = fetch(url, binary=url.lower().endswith(".pdf"))
        blob = body if isinstance(body, bytes) else body.encode()
        h = content_sig(body)
        old["ultima_verifica"] = TODAY
        old["http_status"] = st
        old["bytes"] = len(blob)
        if st != 200:
            old["note"] = f"HTTP {st}"
        elif h != old.get("content_hash"):
            old["note"] = "contenuto cambiato"
            old["content_hash"] = h
            old["ultima_modifica"] = TODAY
            changed.append(url)
        else:
            old["note"] = ""
    for f in fonti:
        if f["url"] in mon:
            f["ultima_verifica"] = TODAY
    write_csv("monitoraggio.csv", list(mon.values()),
              ["url","http_status","content_hash","bytes","ultima_verifica","ultima_modifica","note"])
    write_csv("fonti-menu.csv", fonti, list(fonti[0].keys()) if fonti else
              ["locale_id","url","tipo_fonte","classe","prezzi","allergeni","categorie_menu",
               "accessibilita_tecnica","note","ultima_verifica"])
    if changed:
        path = os.path.join(DATA, "changelog.csv")
        new = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["data", "url"])
            for u in changed:
                w.writerow([TODAY, u])
    print(f"[refresh] controllate {len(mon)} fonti, cambiate {len(changed)}")
    for u in changed:
        print("  cambiata:", u)


# ---------------------------------------------------------------- status
def cmd_status():
    locali = read_csv("locali.csv")
    fonti = read_csv("fonti-menu.csv")
    piatti = read_csv("piatti.csv")
    print(f"locali: {len(locali)}  con sito: {sum(1 for r in locali if r['sito'].strip())}")
    print(f"fonti: {len(fonti)}  piatti estratti: {len(piatti)}")
    from collections import Counter
    print("classi:", dict(Counter(f["classe"] for f in fonti)))
    print("tipo:", dict(Counter(f["tipo_fonte"] for f in fonti)))
    withp = {p["locale_id"] for p in piatti}
    print(f"locali con prezzi: {len(withp)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"discover": cmd_discover, "scrape": cmd_scrape, "refresh": cmd_refresh, "status": cmd_status}[cmd]()
