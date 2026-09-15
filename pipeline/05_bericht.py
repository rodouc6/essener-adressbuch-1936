"""Stufe 05: Kennzahlen → build/bericht.md, Kontrollstichprobe → build/kontrollpunkte.geojson"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import json
from pipeline.lib.bericht import erzeuge
from pipeline.lib.io import lies_csv, projektwurzel

W = projektwurzel()
B = W / "build"
adressen = lies_csv(B / "04_geokodiert.csv")
eintraege = lies_csv(B / "eintraege.csv")
herkunft = {}
for e in eintraege:
    herkunft.setdefault((e["strasse_heute"], e["hausnr"], e["hausnr_zusatz"], e["stadtteil"], e["parse_status"], e["strasse_roh"]), e["herkunft"])
for a in adressen:
    a["herkunft"] = herkunft.get((a["strasse_heute"], a["hausnr"], a["hausnr_zusatz"], a["stadtteil"], a["parse_status"], a["strasse_roh"]), "")
md, geo = erzeuge(eintraege, adressen, lies_csv(B / "03_strassen.csv"), lies_csv(B / "dubletten.csv"),
                  lies_csv(B / "01_ausgeschlossen.csv"), lies_csv(B / "strassen_vorschlaege.csv"))
(B / "bericht.md").write_text(md, encoding="utf-8")
(B / "kontrollpunkte.geojson").write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")
print(md[:1500])
