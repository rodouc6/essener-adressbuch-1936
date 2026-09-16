"""Stufe 03: build/02_geparst.csv → build/03_aufgeloest.csv, build/03_strassen.csv, build/strassen_vorschlaege.csv"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from collections import Counter
from pipeline.lib import einlesen
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv, strassen_dir
from pipeline.lib.konkordanz import Strassenindex
from pipeline.lib.stufen import AUFLOESUNGSFELDER, PARSEFELDER, PAARFELDER, VORSCHLAGSFELDER, loese_strassen

W = projektwurzel()
idx = Strassenindex(strassen_dir(), W / "kuratierung" / "strassen_zuordnung.csv", W / "kuratierung" / "strassen_1935.csv")
zeilen, paare, vorschlaege = loese_strassen(lies_csv(W / "build" / "02_geparst.csv"), idx)
schreib_csv(W / "build" / "03_aufgeloest.csv", zeilen, einlesen.AUSGABEFELDER + PARSEFELDER + AUFLOESUNGSFELDER)
schreib_csv(W / "build" / "03_strassen.csv", paare, PAARFELDER)
schreib_csv(W / "build" / "strassen_vorschlaege.csv", vorschlaege, VORSCHLAGSFELDER)
c = Counter((z["herkunft"], z["mehrdeutig"]) for z in zeilen)
for k, v in c.most_common():
    print(f"{k[0]:12s} mehrdeutig={k[1]:4s} {v:7d} {v / len(zeilen) * 100:5.1f}%")
