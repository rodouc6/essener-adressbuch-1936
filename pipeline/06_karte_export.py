"""Stufe 06: Datenpaket der Karte → site/daten/ (PMTiles, Scherben, Suchindex, Kennzahlen, Zechen).

Aufruf: python3 pipeline/06_karte_export.py [--ohne-kacheln]
Voraussetzung: Stufen 01–05 gelaufen (build/eintraege.csv), tippecanoe installiert.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import datetime
import json
import shutil

from pipeline.lib.berufe import lade_ohdab
from pipeline.lib.io import lies_csv, projektwurzel
from pipeline.lib.karte_export import schreibe_paket
from pipeline.lib.merkmale import lade_regeln

W = projektwurzel()
kacheln = "--ohne-kacheln" not in sys.argv
if kacheln and shutil.which("tippecanoe") is None:
    sys.exit("tippecanoe nicht gefunden (oder --ohne-kacheln verwenden)")
zechen_pfad = W / "kuratierung" / "zechen.csv"
zechen = lies_csv(zechen_pfad) if zechen_pfad.exists() else []
faksimile_pfad = W / "kuratierung" / "faksimile_seiten.csv"
faksimile = lies_csv(faksimile_pfad) if faksimile_pfad.exists() else []
beispiele_pfad = W / "kuratierung" / "startseite_beispiele.csv"
beispiele = lies_csv(beispiele_pfad) if beispiele_pfad.exists() else []
eigentuemer_pfad = W / "kuratierung" / "eigentuemer.csv"
eigentuemer = lies_csv(eigentuemer_pfad) if eigentuemer_pfad.exists() else []
berufe_pfad = W / "kuratierung" / "berufe.csv"
berufe = lies_csv(berufe_pfad) if berufe_pfad.exists() else []
ohdab = lade_ohdab(W / "kuratierung" / "ohdab.csv") if berufe else {}
ziel = W / "site" / "daten"
# Alte Scherben und Indexdateien entfernen, damit keine verwaisten Dateien bleiben.
for unter in ("haus", "suche", "adressen", "themen"):
    shutil.rmtree(ziel / unter, ignore_errors=True)
k = schreibe_paket(ziel, lies_csv(W / "build" / "eintraege.csv"), lade_regeln(W / "kuratierung" / "merkmale"),
                   zechen, datetime.date.today().isoformat(), kacheln=kacheln, faksimile=faksimile, beispiele=beispiele,
                   themen=W / "kuratierung" / "themen", eigentuemer=eigentuemer, berufe=berufe, ohdab=ohdab)
print(json.dumps(k, ensure_ascii=False, indent=1))
