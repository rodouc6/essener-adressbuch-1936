"""Zieht die manuelle Kontrollstichprobe (Spec §6) aus build/04_geokodiert.csv.

Aufruf: python3 werkzeuge/stichprobe.py [seed]

Gezogen werden 200 Adressen der Stufe `haus` und 100 der Stufe `strasse`, mit festem
Seed und aus einer sortierten Grundmenge — derselbe Lauf ergibt dieselbe Stichprobe.
Die Spalten `urteil` und `bemerkung` bleiben leer und werden von Hand gefüllt
(Vokabular siehe docs/stichprobe.md).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import random

from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv

FELDER = ["stufe", "strasse_roh", "hausnr", "hausnr_zusatz", "stadtteil", "strasse_heute",
          "display_name", "lat", "lon", "urteil", "bemerkung"]
UMFANG = {"haus": 200, "strasse": 100}

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
W = projektwurzel()
adressen = lies_csv(W / "build" / "04_geokodiert.csv")

probe: list[dict] = []
for stufe, n in UMFANG.items():
    grundmenge = sorted((a for a in adressen if a["stufe"] == stufe),
                        key=lambda a: (a["strasse_heute"], a["hausnr"], a["hausnr_zusatz"], a["strasse_roh"]))
    random.seed(seed)
    for a in random.sample(grundmenge, min(n, len(grundmenge))):
        probe.append({**{f: a.get(f, "") for f in FELDER}, "urteil": "", "bemerkung": ""})
    print(f"{stufe}: {min(n, len(grundmenge))} von {len(grundmenge)} gezogen")

ziel = W / "docs" / f"stichprobe_{seed}.csv"
schreib_csv(ziel, probe, FELDER)
print(f"geschrieben: {ziel.relative_to(W)} ({len(probe)} Zeilen)")
