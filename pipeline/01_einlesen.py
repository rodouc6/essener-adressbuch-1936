"""Stufe 01: data/essen1936.csv → build/01_bereinigt.csv, build/dubletten.csv, build/01_ausgeschlossen.csv"""
from pipeline.lib import einlesen
from pipeline.lib.io import projektwurzel, schreib_csv

W = projektwurzel()
bereinigt, dubletten, ausgeschlossen = einlesen.verarbeite(
    W / "data" / "essen1936.csv", W / "kuratierung" / "zeilenkorrekturen.csv")
schreib_csv(W / "build" / "01_bereinigt.csv", bereinigt, einlesen.AUSGABEFELDER)
schreib_csv(W / "build" / "dubletten.csv", dubletten, ["id", "dublette_von"])
schreib_csv(W / "build" / "01_ausgeschlossen.csv", ausgeschlossen, ["id", "grund"])
print(f"bereinigt {len(bereinigt)}  dubletten {len(dubletten)}  ausgeschlossen {len(ausgeschlossen)}")
