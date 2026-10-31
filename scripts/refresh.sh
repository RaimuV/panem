#!/usr/bin/env bash
# Aggiornamento periodico del catalogo panem.
#   refresh.sh check   -> ricontrolla le fonti note (hash/HTTP), logga i cambi
#   refresh.sh full    -> ri-scarica e ri-estrae tutto (menu + prezzi)
# Uso da cron; lock per evitare esecuzioni sovrapposte.
#
# Dopo lo scrape: valida i CSV (panem.py check) e, se tutto torna e i dati sono
# cambiati, committa e pusha data/ così il server non resta l'unico ad avere i
# dati nuovi. Se la validazione fallisce non si pubblica nulla.
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:-check}"
exec 9>/tmp/panem.lock
flock -n 9 || exit 0
mkdir -p raw

log() { echo "[$(date -Is)] $*" >> raw/refresh.log; }

if [ "$mode" = "full" ]; then
  python3 scripts/panem.py scrape >> raw/refresh.log 2>&1
else
  python3 scripts/panem.py refresh >> raw/refresh.log 2>&1
fi

# 1. validazione: dati incoerenti (FK rotte, contatori, campi fuori schema) = niente push
if ! python3 scripts/panem.py check >> raw/refresh.log 2>&1; then
  log "check fallito: dati aggiornati ma NON pubblicati"
  exit 1
fi

# 2. pubblicazione, solo se data/ è cambiato
if [ -z "$(git status --porcelain data/)" ]; then
  log "nessuna modifica nei dati"
  exit 0
fi

if ! git config user.email >/dev/null 2>&1; then
  log "git user.email non configurato: commit saltato (dati restano locali)"
  exit 0
fi

if git add data/ && git commit -q -m "refresh automatico $(date +%F)" >> raw/refresh.log 2>&1; then
  log "commit creato"
else
  log "commit fallito"
  exit 1
fi

if git push -q >> raw/refresh.log 2>&1; then
  log "push ok"
else
  log "push fallito: commit locale, verrà ritentato al prossimo giro"
  exit 1
fi
