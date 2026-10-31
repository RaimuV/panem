#!/usr/bin/env python3
"""Estrae i siti web dichiarati nelle pagine categoria di PagineGialle (Altamura)
e li associa ai locali di data/locali.csv.

PagineGialle espone per alcuni esercizi un CTA con title="sito web - <nome>".
Niente scraping aggressivo: una richiesta per pagina categoria, 1 req/s.
"""
import csv
import difflib
import html
import os
import re
import subprocess
import time
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
CATS = ["ristoranti", "pizzerie", "trattorie", "osterie", "paninoteche",
        "hamburgerie", "pub", "birrerie", "rosticcerie", "panifici"]
SKIP = ("facebook.", "instagram.", "canva.com", "google.", "wa.me", "youtube.",
        "tiktok.", "linktr.ee", "paginegialle", "tripadvisor", "thefork", "justeat",
        "glovo", "menu.cooperto.it", "wixsite.com/website")


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).strip()


def tokens(s):
    return [t for t in norm(s).split() if len(t) >= 3]


def get(url):
    time.sleep(1.0)
    out = subprocess.run(["curl", "-sL", "-m", "25", "--compressed", "-A", UA,
                          "-H", "Accept-Language: it-IT,it;q=0.9", url],
                         capture_output=True, timeout=40).stdout
    return out.decode("utf-8", "ignore")


def harvest():
    found = {}
    for cat in CATS:
        url = f"https://www.paginegialle.it/puglia/altamura/{cat}.html"
        n = 0
        for page_no in range(1, 11):
            page = get(url)
            pairs = re.findall(r'title="sito web - ([^"]+)"[^>]*?href="([^"]+)"', page)
            n += len(pairs)
            for name, href in pairs:
                name = html.unescape(name).strip()
                href = href.strip()
                if any(s in href.lower() for s in SKIP):
                    continue
                found.setdefault(href, name)
            m = re.search(r'class="chip next-page-btn"[^>]*data-pageurl="([^"]+)"', page)
            if not m:
                break
            url = "https://www.paginegialle.it" + m.group(1)
        print(f"[pg] {cat}: {n} siti dichiarati")
    return found


def match(rows, sites):
    updates = []
    for url, name in sites.items():
        best, score = None, 0.0
        for r in rows:
            s = difflib.SequenceMatcher(None, norm(name), norm(r["nome"])).ratio()
            t = set(tokens(name))
            if t and t <= set(tokens(r["nome"])):
                s = max(s, 0.8)
            if s > score:
                best, score = r, s
        if best and score >= 0.72 and not best["sito"].strip():
            updates.append((best["id"], best["nome"], name, url, round(score, 2)))
    return updates


def main():
    path = os.path.join(ROOT, "data", "locali.csv")
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    sites = harvest()
    print(f"[pg] domini unici: {len(sites)}")
    updates = match(rows, sites)
    by_id = {r["id"]: r for r in rows}
    for lid, nome, found_name, url, score in updates:
        by_id[lid]["sito"] = url
        print(f"  {lid:32s} <- {url}  ({found_name} / {score})")
    unmatched = [u for u in sites if not any(u == x[3] for x in updates)]
    print("[pg] siti non associati:")
    for u in unmatched:
        print("   ", sites[u], "|", u)
    cols = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"[pg] locali con sito: {sum(1 for r in rows if r['sito'].strip())}/{len(rows)}")


if __name__ == "__main__":
    main()
