"""Stufe 01: Quelle einlesen, Zeilen reparieren, Teile filtern, Dubletten markieren."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from pipeline.lib.io import lies_csv
from pipeline.lib.normalisierung import norm_vorort

QUELLFELDER = [
    "page", "lastname", "firstname", "Beruf o. ä.", "Adresse", "Ortsname", "Ortskennung",
    "Firmenname", "Familienstand", "Vorname Bezugsperson", "Beruf Bezugsperson", "Eigentümer",
    "Funktionsträger", "abweichender Wohnort", "Vorort", "Verwalter", "id",
]
ZUSATZFELDER = ["teil", "seite", "dublette_von", "vorort_ok"]
AUSGABEFELDER = QUELLFELDER + ZUSATZFELDER
ERLAUBTE_TEILE = {"I", "II", "III"}


def _lade_korrekturen(pfad: Path) -> dict[str, list[dict]]:
    """Lädt die Kuratierungstabelle und gruppiert die Korrekturen nach id."""
    k: dict[str, list[dict]] = {}
    for z in lies_csv(pfad):
        k.setdefault(z["id"], []).append(z)
    return k


def _rohzeilen(pfad: Path):
    """Liest die Quelldatei tabgetrennt ein und liefert die Rohzeilen (ohne Kopfzeile)."""
    with open(pfad, encoding="utf-8", newline="") as f:
        r = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        kopf = next(r)
        assert kopf == QUELLFELDER, f"unerwarteter Kopf: {kopf}"
        yield from r


def verarbeite(quelle: Path, korrekturen: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """Liest die Quelle ein, repariert kuratierte Zeilen, filtert auf die Teile I-III
    und markiert Dubletten. Gibt (bereinigt, dubletten, ausgeschlossen) zurück."""
    korr = _lade_korrekturen(korrekturen)
    bereinigt: list[dict] = []
    dubletten: list[dict] = []
    ausgeschlossen: list[dict] = []
    gesehen: dict[tuple, str] = {}
    for roh in _rohzeilen(quelle):
        zid = roh[-1].strip() if roh else ""
        for k in korr.get(zid, []):
            if k["aktion"] == "leerfeld_entfernen":
                idx = int(k["feld"])
                if len(roh) > len(QUELLFELDER) and roh[idx].strip() == "":
                    del roh[idx]
        if len(roh) != len(QUELLFELDER):
            ausgeschlossen.append({"id": zid, "grund": f"feldzahl_{len(roh)}"})
            continue
        z = {f: v.strip() for f, v in zip(QUELLFELDER, roh)}
        for k in korr.get(zid, []):
            if k["aktion"] == "setze_feld":
                z[k["feld"]] = k["neu"]
        m = re.match(r"^(I{1,3}|IV|W)-(\d+)$", z["page"])
        teil = m.group(1) if m else ""
        if teil not in ERLAUBTE_TEILE:
            ausgeschlossen.append({"id": z["id"], "grund": "teil_IV_W" if teil in ("IV", "W") else "page_unlesbar"})
            continue
        z["teil"], z["seite"] = teil, str(int(m.group(2)))
        vorort, ok = norm_vorort(z["Vorort"])
        z["Vorort"], z["vorort_ok"] = vorort, "ja" if ok else "nein"
        schluessel = tuple(z[f] for f in QUELLFELDER if f != "id")
        if schluessel in gesehen:
            dubletten.append({"id": z["id"], "dublette_von": gesehen[schluessel]})
            continue
        gesehen[schluessel] = z["id"]
        z["dublette_von"] = ""
        bereinigt.append(z)
    return bereinigt, dubletten, ausgeschlossen
