"""Gemeinsames für die Berufs-Kuratierung (Teilprojekt 4): OhdAB-Schnappschuss, Niveaus, Status, Sperre.

Spec docs/superpowers/specs/2026-09-23-berufe-design.md. Die Berufsangabe steht in `Beruf o. ä.`
(Teil I Einwohner, Teil II Eigentümer). Zuordnung je Schreibweise auf ein OhdAB-Schlüssel-Item.
"""
from __future__ import annotations

import re
from pathlib import Path

from pipeline.lib.io import lies_csv

AUTOMATIK = "berufe_vorschlag"
FELDER_KURATIERUNG = ["schreibweise", "nennungen", "beruf", "status", "ohdab_id", "niveau_unsicher", "geprueft",
                      "vorschlag_grund", "bearbeiter", "datum", "hinweis"]
FELDER_OHDAB = ["ohdab_id", "qid", "norm", "maennlich", "weiblich", "niveau", "gattung_id", "gattung"]
# Anforderungsniveau (KldB-Systematik, OhdAB P911) → Schlüssel; Anzeigetext für Karte und Werkzeug.
NIVEAUS = {
    "helfer": "Helfer-/Anlerntätigkeit",
    "fachlich": "Fachliche Tätigkeit",
    "spezialist": "Komplexe Spezialistentätigkeit",
    "hochkomplex": "Hoch komplexe Tätigkeit",
    "aufsicht": "Aufsichtskraft",
    "fuehrung": "Führungskraft",
    "keins": "ohne Niveau",
}
NIVEAU_LABELS = {
    "Tätigkeitsprofil Helfer- und Anlerntätigkeiten": "helfer",
    "Fachliche Tätigkeiten": "fachlich",
    "Komplexe Spezialistentätigkeit": "spezialist",
    "Hoch komplexe Tätigkeiten": "hochkomplex",
    "Tätigkeitsprofil Aufsichtskräfte": "aufsicht",
    "Tätigkeitsprofil Führungskräfte": "fuehrung",
}
# Zusätze, die keinen Beruf bezeichnen (Spec §3.3); mehrere je Zeile mit „;“.
STATUS = ("ruhestand", "invalide", "witwe")
OHDAB_FEHLT = "kuratierung/ohdab.csv fehlt — zuerst python3 werkzeuge/ohdab_laden.py ausführen"

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"})
_NICHT_ZEICHEN = re.compile(r"[^a-z0-9 ]+")
# Geschlechtszusätze der Normbezeichnung: „Lehrer/in“, „Bergmann/-frau“, „Technische/r“, „Arbeiter/in - ungelernte/r“
_GESCHLECHT = re.compile(r"/-?(innen|in|frau|r|e)\b")
_TRENNER = re.compile(r"\s+-\s+")


def niveau_schluessel(label: str) -> str:
    """FactGrid-Label des Anforderungsniveaus → Schlüssel; Unbekanntes und Leeres → „keins“."""
    return NIVEAU_LABELS.get((label or "").strip(), "keins")


def falte_form(text: str) -> str:
    """Vergleichsschlüssel: klein, Umlaute aufgelöst, Bindestrich = Leerzeichen, nur a–z, 0–9, Leerzeichen."""
    t = (text or "").replace("-", " ").translate(_UMLAUTE).lower()
    return " ".join(_NICHT_ZEICHEN.sub(" ", t).split())


def norm_form(z: dict) -> str:
    """Gefaltete Normbezeichnung ohne Geschlechtszusatz, aber MIT Qualifizierung („Landwirt/in im
    Nebenerwerb“ → „landwirt im nebenerwerb“). Damit lässt sich ein unqualifiziertes Item erkennen."""
    return falte_form(_GESCHLECHT.sub("", z.get("norm") or ""))


def formen_von(z: dict) -> list[str]:
    """Gefaltete Vergleichsformen eines OhdAB-Items: männliche und weibliche Form, Normbezeichnung ohne
    Geschlechtszusatz und ohne „ - “-Zusatz; ohne Dubletten, Reihenfolge stabil."""
    norm = _TRENNER.sub(" ", _GESCHLECHT.sub("", z.get("norm") or ""))
    out: list[str] = []
    for f in (z.get("maennlich"), z.get("weiblich"), norm):
        k = falte_form(f or "")
        if k and k not in out:
            out.append(k)
    return out


def lade_ohdab(pfad: Path | str) -> dict[str, dict]:
    """kuratierung/ohdab.csv als ohdab_id → Zeile; fehlt die Datei, klare Meldung (kein stiller Rückfall)."""
    pfad = Path(pfad)
    if not pfad.exists():
        raise FileNotFoundError(OHDAB_FEHLT)
    return {z["ohdab_id"].strip(): {k: (v or "").strip() for k, v in z.items()} for z in lies_csv(pfad) if z.get("ohdab_id")}


def lade_kuratierung(zeilen: list[dict]) -> dict[str, dict]:
    """kuratierung/berufe.csv als Schreibweise → Zeile (Werte getrimmt)."""
    out: dict[str, dict] = {}
    for z in zeilen:
        z = {k: (v or "").strip() for k, v in z.items()}
        if z.get("schreibweise"):
            out[z["schreibweise"]] = z
    return out


def gesperrt(z: dict) -> bool:
    """Die Automatik darf eine Zeile nur überschreiben, wenn sie ungeprüft ist und zuletzt von ihr selbst stammt."""
    return z.get("geprueft") == "ja" or (z.get("bearbeiter") or AUTOMATIK) != AUTOMATIK
