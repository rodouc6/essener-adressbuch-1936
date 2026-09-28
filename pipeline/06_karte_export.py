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
from pipeline.lib.stadtteile import lade_stadtteile

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
hauptgruppen = lies_csv(W / "kuratierung" / "hauptgruppen.csv")   # Bezeichnungen der OhdAB-Hauptgruppen (Spec §5.2)
gewerbe_pfad = W / "kuratierung" / "gewerbe.csv"
gewerbe = lies_csv(gewerbe_pfad) if gewerbe_pfad.exists() else []
bergbau_pfad = W / "kuratierung" / "merkmale" / "bergbau.csv"
bergbau = lies_csv(bergbau_pfad) if bergbau_pfad.exists() else []
osm_pfad = W / "build" / "osm_strassen.json"
if osm_pfad.exists():
    osm_linien = json.loads(osm_pfad.read_text(encoding="utf-8"))["linien"]
else:
    osm_linien = {}
    print("build/osm_strassen.json fehlt — Straßenschicht bleibt leer (werkzeuge/osm_strassen_laden.py)", file=sys.stderr)
st_pfad = W / "build" / "osm_stadtteile.json"
if st_pfad.exists():
    stadtteile = lade_stadtteile(st_pfad, W / "kuratierung" / "stadtteile_osm.csv")
else:
    stadtteile = None
    print("build/osm_stadtteile.json fehlt — Stadtteil bleibt der Straßen-Stadtteil (werkzeuge/osm_stadtteile_laden.py)", file=sys.stderr)
ziel = W / "site" / "daten"
# Alte Scherben und Indexdateien entfernen, damit keine verwaisten Dateien bleiben.
for unter in ("haus", "suche", "adressen", "themen", "ebenen", "layout", "perspektiven", "herkunft"):
    shutil.rmtree(ziel / unter, ignore_errors=True)
k = schreibe_paket(ziel, lies_csv(W / "build" / "eintraege.csv"), lade_regeln(W / "kuratierung" / "merkmale"),
                   zechen, datetime.date.today().isoformat(), kacheln=kacheln, faksimile=faksimile, beispiele=beispiele,
                   themen=W / "kuratierung" / "themen", eigentuemer=eigentuemer, berufe=berufe, ohdab=ohdab,
                   hauptgruppen=hauptgruppen, gewerbe=gewerbe, osm_linien=osm_linien, stadtteile=stadtteile,
                   perspektiven=W / "kuratierung" / "perspektiven", bergbau=bergbau)
print(json.dumps(k, ensure_ascii=False, indent=1))
