"""Stufe 04: build/03_aufgeloest.csv → build/04_geokodiert.csv (je Adresse), build/eintraege.csv (je Zeile)"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import os
from collections import Counter
from pipeline.lib import einlesen
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv
from pipeline.lib.nominatim import Client, lade_landmarken
from pipeline.lib.stufen import ADRESSFELDER, AUFLOESUNGSFELDER, PARSEFELDER, VERORTUNGSFELDER, geokodiere_zeilen

W = projektwurzel()
client = Client(os.environ.get("NOMINATIM_URL", "http://localhost:8080"), W / "build" / "cache" / "nominatim.jsonl")
landmarken = lade_landmarken(W / "kuratierung" / "landmarken.csv")
zeilen, adressen = geokodiere_zeilen(lies_csv(W / "build" / "03_aufgeloest.csv"), client, landmarken, threads=8)
client.schliessen()
schreib_csv(W / "build" / "04_geokodiert.csv", adressen, ADRESSFELDER)
schreib_csv(W / "build" / "eintraege.csv", zeilen, einlesen.AUSGABEFELDER + PARSEFELDER + AUFLOESUNGSFELDER + VERORTUNGSFELDER)
c = Counter((z["stufe"], z["grund"]) for z in zeilen)
for k, v in c.most_common():
    print(f"{k[0]:10s} {k[1]:22s} {v:7d} {v / len(zeilen) * 100:5.1f}%")
