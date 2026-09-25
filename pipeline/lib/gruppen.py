"""Berufsgruppen = OhdAB-Hauptgruppen (Teilprojekt 5a, Spec §5.2, geändert 2026-09-25).

Die 14 handkuratierten Branchen sind verworfen: Die Berufsbezeichnung nennt die Tätigkeit, nicht den Betrieb, und
selbst gezogene Grenzen erzeugten Verlegenheitszuordnungen. Die Gruppe eines Eintrags ist seine OhdAB-Hauptgruppe
(KldB-2010-Hierarchie: Bereich → Hauptgruppe → Gruppe → Gattung), abgeleitet aus `gattung_id` — ohne Handprüfung.
`kuratierung/hauptgruppen.csv` liefert nur die Bezeichnungen.
"""
from __future__ import annotations

import re

UNGEPRUEFT = "ungeprueft"     # Einträge ohne geprüften Beruf: der Nenner bleibt sichtbar
FELDER_HAUPTGRUPPEN = ["hauptgruppe", "bezeichnung", "kurz", "bereich", "quelle"]
_ID = re.compile(r"^\s*([AB])?\s*(\d{2})(\d)?")


def hauptgruppe(gattung_id: str) -> str:
    """„B 21112“ → „B21“; „A 10200“ → „A10“; eine OhdAB-Zeile ohne Buchstaben („94243“) gilt als B."""
    m = _ID.match(gattung_id or "")
    if not m:
        return UNGEPRUEFT
    return (m.group(1) or "B") + m.group(2)


def gruppe3(gattung_id: str) -> str:
    """Dreistellige Gruppe: „B 21112“ → „B211“ (Berg-, Tagebau und Sprengtechnik)."""
    m = _ID.match(gattung_id or "")
    if not m or not m.group(3):
        return UNGEPRUEFT
    return (m.group(1) or "B") + m.group(2) + m.group(3)


def lade_hauptgruppen(zeilen: list[dict]) -> dict[str, dict]:
    return {z["hauptgruppe"].strip(): {k: (v or "").strip() for k, v in z.items()} for z in zeilen if (z.get("hauptgruppe") or "").strip()}


def fehlende_bezeichnungen(ohdab: dict[str, dict], hauptgruppen: dict[str, dict]) -> set[str]:
    """Hauptgruppen des OhdAB-Schnappschusses ohne Zeile in hauptgruppen.csv — der Export bricht dann ab."""
    return {hauptgruppe(o.get("gattung_id", "")) for o in ohdab.values()} - set(hauptgruppen) - {UNGEPRUEFT}
