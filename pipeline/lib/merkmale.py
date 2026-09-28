"""Merkmale je Eintrag aus kuratierten Tabellen (kuratierung/merkmale/*.csv).

Ein Merkmal ist ein Kennwort wie `akademiker` oder `bergbau`. Es entsteht nur aus einer
Tabelle mit Beleg; ohne Tabelle gibt es kein Merkmal (Precision first). Spalten:
feld, art (exakt | praefix | regex), muster, merkmal, beleg, bearbeiter, datum.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pipeline.lib.io import lies_csv

ARTEN = {"exakt", "praefix", "regex"}


@dataclass(frozen=True)
class Regel:
    feld: str
    art: str
    muster: str
    merkmal: str


def lade_regeln(ordner: Path) -> list[Regel]:
    regeln: list[Regel] = []
    for pfad in sorted(Path(ordner).glob("*.csv")):
        if pfad.name == "bergbau.csv":     # Gruppen-Tabelle (pipeline/lib/bergbau.py), keine Merkmalsregel
            continue
        for z in lies_csv(pfad):
            if z["art"] not in ARTEN:
                raise ValueError(f"{pfad.name}: unbekannte Art {z['art']!r} (erlaubt: {sorted(ARTEN)})")
            if not z["muster"] or not z["merkmal"]:
                raise ValueError(f"{pfad.name}: muster und merkmal müssen gefüllt sein")
            # Validiere Regex-Muster beim Laden
            if z["art"] == "regex":
                try:
                    re.compile(z["muster"])
                except re.error as e:
                    raise ValueError(f"{pfad.name}: ungültiger regulärer Ausdruck {z['muster']!r}: {e}")
            if not z.get("beleg"):
                raise ValueError(f"{pfad.name}: beleg fehlt für Merkmal {z['merkmal']!r} (Precision first — jedes Merkmal braucht einen Beleg)")
            regeln.append(Regel(z["feld"], z["art"], z["muster"], z["merkmal"]))
    return regeln


def _trifft(regel: Regel, wert: str) -> bool:
    if regel.art == "exakt":
        return wert == regel.muster
    if regel.art == "praefix":
        return wert.startswith(regel.muster)
    return re.search(regel.muster, wert) is not None


def merkmale_fuer(eintrag: dict, regeln: list[Regel]) -> list[str]:
    """Sortierte Merkmale ohne Dubletten; leere Felder treffen nie."""
    gefunden = set()
    for r in regeln:
        wert = (eintrag.get(r.feld) or "").strip()
        if wert and _trifft(r, wert):
            gefunden.add(r.merkmal)
    return sorted(gefunden)
