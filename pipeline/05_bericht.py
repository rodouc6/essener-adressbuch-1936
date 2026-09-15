"""Stufe 05: Kennzahlen → build/bericht.md, Kontrollstichprobe → build/kontrollpunkte.geojson"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import json
from pipeline.lib.bericht import erzeuge
from pipeline.lib.io import lies_csv, projektwurzel

W = projektwurzel()
B = W / "build"
# 04_geokodiert.csv trägt die Auflösungsfelder selbst im Schlüssel (ADRESSSCHLUESSEL),
# ein Hand-Join über die Einträge ist deshalb nicht mehr nötig.
adressen = lies_csv(B / "04_geokodiert.csv")
eintraege = lies_csv(B / "eintraege.csv")
statistik_pfad = B / "04_statistik.json"
statistik = json.loads(statistik_pfad.read_text(encoding="utf-8")) if statistik_pfad.exists() else None
md, geo = erzeuge(eintraege, adressen, lies_csv(B / "03_strassen.csv"), lies_csv(B / "dubletten.csv"),
                  lies_csv(B / "01_ausgeschlossen.csv"), lies_csv(B / "strassen_vorschlaege.csv"),
                  zuordnung=lies_csv(W / "kuratierung" / "strassen_zuordnung.csv"), statistik=statistik)
(B / "bericht.md").write_text(md, encoding="utf-8")
(B / "kontrollpunkte.geojson").write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")
print(md[:2000])
