"""Bergbau-Gruppen je Berufsnorm (Spec 2026-09-28 §2.2/§2.3): kuratierte Tabelle kuratierung/merkmale/bergbau.csv
(Spalten beruf, gruppe, geprueft, bearbeiter, datum, hinweis). `beruf` ist die Norm aus berufe.csv, nicht die
Schreibweise. Keine OhdAB-Hauptgruppe: B21 enthält Techniker, Ingenieure, Glas und Keramik."""
from __future__ import annotations

GRUPPEN = ("belegschaft", "aufsicht", "leitung", "invaliden")
# Rang bei mehreren Gruppen im Haus (Adressfeld `bergbau`, Thema auf der Karte): die kleinen Gruppen
# verschwänden sonst unter der Belegschaft.
RANG = ("leitung", "aufsicht", "belegschaft", "invaliden")
NAMEN = {"belegschaft": "Belegschaft", "aufsicht": "Aufsicht", "leitung": "Leitung und Beamte", "invaliden": "Berginvaliden"}


def lade_bergbau(zeilen: list[dict]) -> dict[str, str]:
    """Norm → Gruppe. Laut bei leerer Norm, unbekannter Gruppe oder doppelter Norm — eine stille Auslassung
    hieße, Bergleute unbemerkt aus dem Kapitel zu verlieren."""
    out: dict[str, str] = {}
    for z in zeilen:
        beruf = (z.get("beruf") or "").strip()
        gruppe = (z.get("gruppe") or "").strip()
        if not beruf:
            raise ValueError("bergbau.csv: beruf fehlt")
        if gruppe not in GRUPPEN:
            raise ValueError(f"bergbau.csv: gruppe {gruppe!r} für {beruf!r} unbekannt (erlaubt: {GRUPPEN})")
        if beruf in out:
            raise ValueError(f"bergbau.csv: Norm {beruf!r} doppelt")
        out[beruf] = gruppe
    return out


def pruefe_gegen_berufe(tabelle: dict[str, str], berufe_zeilen: list[dict]) -> list[str]:
    """Normen der Tabelle, die in berufe.csv (Spalte beruf) nicht vorkommen — sie zählten nie."""
    normen = {(z.get("beruf") or "").strip() for z in berufe_zeilen}
    return sorted(n for n in tabelle if n not in normen)


def rang_gruppe(zaehl: dict) -> str | None:
    """Höchste vorhandene Gruppe nach RANG aus den Zählfeldern n_bb_<gruppe>; None ohne Bergbau-Eintrag."""
    for g in RANG:
        if zaehl.get(f"n_bb_{g}", 0) > 0:
            return g
    return None
