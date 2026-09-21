"""Stufe 06: Datenpaket der Karte → site/daten/ (PMTiles, Scherben, Suchindex, Kennzahlen, Zechen).

Aufruf: python3 pipeline/06_karte_export.py [--ohne-kacheln]
Voraussetzung: Stufen 01–05 gelaufen (build/eintraege.csv), tippecanoe installiert.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import datetime
import json
import shutil

from pipeline.lib.io import lies_csv, projektwurzel
from pipeline.lib.karte_export import schreibe_paket
from pipeline.lib.merkmale import lade_regeln

W = projektwurzel()
kacheln = "--ohne-kacheln" not in sys.argv
if kacheln and shutil.which("tippecanoe") is None:
    sys.exit("tippecanoe nicht gefunden (oder --ohne-kacheln verwenden)")
zechen_pfad = W / "kuratierung" / "zechen.csv"
zechen = lies_csv(zechen_pfad) if zechen_pfad.exists() else []
ziel = W / "site" / "daten"
# Alte Scherben und Indexdateien entfernen, damit keine verwaisten Dateien bleiben.
for unter in ("haus", "suche", "adressen"):
    shutil.rmtree(ziel / unter, ignore_errors=True)
k = schreibe_paket(ziel, lies_csv(W / "build" / "eintraege.csv"), lade_regeln(W / "kuratierung" / "merkmale"),
                   zechen, datetime.date.today().isoformat(), kacheln=kacheln)
print(json.dumps(k, ensure_ascii=False, indent=1))
