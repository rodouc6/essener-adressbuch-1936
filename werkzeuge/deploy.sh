#!/usr/bin/env bash
# Veröffentlicht site/ (inkl. des nicht versionierten Datenpakets site/daten/) als einzelnen
# Schnappschuss auf den Branch gh-pages. Der Branch hat keine Historie: jeder Aufruf ersetzt
# den vorigen Stand (Force-Push), damit das Datenvolumen nicht in der Git-Historie wächst.
# GitHub Pages wird auf „Deploy from a branch: gh-pages / (root)“ eingestellt.
#
# Aufruf: werkzeuge/deploy.sh [--nur-bauen]   (--nur-bauen: Commit erzeugen, nicht pushen)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# 1. Sicherungen: sauberer Arbeitsbaum, Datenpaket vorhanden, Stadtplan-Ebene gesperrt.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "Arbeitsbaum hat uncommittete Änderungen – erst committen." >&2; exit 1
fi
for f in site/daten/kennzahlen.json site/daten/adressen.pmtiles site/daten/zechen.geojson; do
  [ -f "$f" ] || { echo "$f fehlt – zuerst python3 pipeline/06_karte_export.py ausführen." >&2; exit 1; }
done
# Stadtplan 1935: Nutzung von der Stadt Essen am 2026-10-07 genehmigt (live über die Export-Schnittstelle);
# PLAN_FREIGEGEBEN darf seither true sein, die frühere Deploy-Sperre entfällt.

# 2. Baum aus site/ in einem temporären Index aufbauen (ohne Tests, Node-Paketdatei und das
#    Roh-GeoJSON, das nur tippecanoe braucht). --force, weil site/daten/ in .gitignore steht.
export GIT_INDEX_FILE
GIT_INDEX_FILE="$(mktemp)"
rm -f "$GIT_INDEX_FILE"   # git will eine leere Datei nicht als Index lesen; der Pfad genügt
trap 'rm -f "$GIT_INDEX_FILE"' EXIT
git add --force -- site ':!site/tests' ':!site/package.json' ':!site/daten/adressen.geojson' ':!site/daten/hex.geojson' ':!site/daten/strassen.geojson'
quelle="$(git rev-parse --short HEAD)"

# 3. Cache-Busting (werkzeuge/versioniere.py): Skript- und Stil-URLs, Import-Map und konfig.js im
#    Schnappschuss tragen den Commit als Marke; der Arbeitsbaum bleibt unverändert.
module="$(cd site && find js -name '*.js' | sort | tr '\n' ' ')"
for datei in site/*.html; do
  blob="$(python3 werkzeuge/versioniere.py html "$quelle" $module < "$datei" | git hash-object -w --stdin)"
  git update-index --cacheinfo "100644,$blob,$datei"
done
blob="$(python3 werkzeuge/versioniere.py konfig "$quelle" < site/js/konfig.js | git hash-object -w --stdin)"
git update-index --cacheinfo "100644,$blob,site/js/konfig.js"
baum="$(git write-tree --prefix=site/)"
stand="$(python3 -c 'import json;print(json.load(open("site/daten/kennzahlen.json"))["stand"])')"
commit="$(git commit-tree "$baum" -m "Pages-Schnappschuss von main@$quelle, Datenstand $stand")"
echo "Schnappschuss $commit (Baum $baum, main@$quelle, Datenstand $stand)"

if [ "${1:-}" = "--nur-bauen" ]; then
  git update-ref refs/heads/gh-pages "$commit"
  echo "Lokaler Branch gh-pages gesetzt, nicht gepusht."
  exit 0
fi
git push --force origin "$commit:refs/heads/gh-pages"
git update-ref refs/heads/gh-pages "$commit"
echo "gh-pages aktualisiert."
