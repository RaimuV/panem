#!/usr/bin/env bash
# Aggiornamento periodico del catalogo panem.
#   refresh.sh check   -> ricontrolla le fonti note (hash/HTTP), logga i cambi
#   refresh.sh full    -> ri-scarica e ri-estrae tutto (menu + prezzi)
# Uso da cron; lock per evitare esecuzioni sovrapposte.
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:-check}"
exec 9>/tmp/panem.lock
flock -n 9 || exit 0
mkdir -p raw
if [ "$mode" = "full" ]; then
  python3 scripts/panem.py scrape >> raw/refresh.log 2>&1
else
  python3 scripts/panem.py refresh >> raw/refresh.log 2>&1
fi
