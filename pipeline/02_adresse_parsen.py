"""Stufe 02: build/01_bereinigt.csv → build/02_geparst.csv"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from collections import Counter
from pipeline.lib import einlesen
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv
from pipeline.lib.stufen import PARSEFELDER, parse_zeilen

W = projektwurzel()
zeilen = parse_zeilen(lies_csv(W / "build" / "01_bereinigt.csv"))
schreib_csv(W / "build" / "02_geparst.csv", zeilen, einlesen.AUSGABEFELDER + PARSEFELDER)
print(Counter(z["parse_status"] for z in zeilen))
