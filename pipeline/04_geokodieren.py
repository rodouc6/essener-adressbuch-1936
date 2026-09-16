"""Stufe 04: build/03_aufgeloest.csv → build/04_geokodiert.csv (je Adresse), build/eintraege.csv (je Zeile)"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import json
import os
from collections import Counter
from pipeline.lib import einlesen
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv
from pipeline.lib.konkordanz import lade_stadtplan_1935
from pipeline.lib.nominatim import Client, lade_landmarken
from pipeline.lib.stufen import ADRESSFELDER, AUFLOESUNGSFELDER, PARSEFELDER, VERORTUNGSFELDER, geokodiere_zeilen

W = projektwurzel()
client = Client(os.environ.get("NOMINATIM_URL", "http://localhost:8080"), W / "build" / "cache" / "nominatim.jsonl")
try:
    landmarken = lade_landmarken(W / "kuratierung" / "landmarken.csv")
    stadtplan = lade_stadtplan_1935(W / "kuratierung" / "strassen_1935.csv")
    zeilen, adressen = geokodiere_zeilen(lies_csv(W / "build" / "03_aufgeloest.csv"), client, landmarken, threads=8,
                                         stadtplan=stadtplan)
finally:
    client.schliessen()
statistik = {"cache_treffer": client.treffer, "cache_anfragen": client.anfragen}
(W / "build" / "04_statistik.json").write_text(json.dumps(statistik, ensure_ascii=False), encoding="utf-8")
schreib_csv(W / "build" / "04_geokodiert.csv", adressen, ADRESSFELDER)
schreib_csv(W / "build" / "eintraege.csv", zeilen, einlesen.AUSGABEFELDER + PARSEFELDER + AUFLOESUNGSFELDER + VERORTUNGSFELDER)
c = Counter((z["stufe"], z["grund"]) for z in zeilen)
for k, v in c.most_common():
    print(f"{k[0]:10s} {k[1]:22s} {v:7d} {v / len(zeilen) * 100:5.1f}%")
fehler = sum(1 for a in adressen if a["grund"] == "fehler")
print(f"Fehler: {fehler} Adressen")
print(f"Cache-Treffer: {statistik['cache_treffer']} von {statistik['cache_anfragen']} Anfragen")
