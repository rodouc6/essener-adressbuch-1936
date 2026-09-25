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
                      "vorschlag_grund", "bearbeiter", "datum", "hinweis", "stellung", "stellung_geprueft"]
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
STATUS = ("ruhestand", "invalide", "witwe", "gewerbe")
OHDAB_FEHLT = "kuratierung/ohdab.csv fehlt — zuerst python3 werkzeuge/ohdab_laden.py ausführen"

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"})
_NICHT_ZEICHEN = re.compile(r"[^a-z0-9 ]+")
# Geschlechtszusätze der Normbezeichnung: „Lehrer/in“, „Bergmann/-frau“, „Technische/r“, „Arbeiter/in - ungelernte/r“
_GESCHLECHT = re.compile(r"/-?(innen|in|frau|r|e)\b")
_TRENNER = re.compile(r"\s+-\s+")
# Klammerzusätze ab drei Zeichen („(mittl. Dienst)“, „(Büro)“; „(er)“ aus „Beamt(er/in)“ bleibt) und
# Alternativen einer Mehrfachnorm, getrennt durch „, “ oder „ / “.
_KLAMMER = re.compile(r"\s*\((?=[^)]{3,})[^)]*\)")
# Geschlechtszusatz in Klammern: „Beamt(er/in)“ → „Beamter“, „Angestellt(e/in)“ → „Angestellte“.
_KLAMMER_GESCHLECHT = re.compile(r"\((er|e)/in\)")
_ALTERNATIVE = re.compile(r",\s+|\s+/\s+")


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
    return falte_form(_GESCHLECHT.sub("", _KLAMMER_GESCHLECHT.sub(r"\1", z.get("norm") or "")))


def formen_von(z: dict) -> list[str]:
    """Gefaltete Vergleichsformen eines OhdAB-Items: männliche und weibliche Form, Normbezeichnung ohne
    Geschlechtszusatz und ohne „ - “-Zusatz, dazu die Norm ohne Klammerzusatz („Bankbeamt(er/in) (mittl.
    Dienst)“ → „bankbeamter“, auch für männliche/weibliche Form) und jede Alternative einer Mehrfachnorm („Wächter/in, Aufseher/in“,
    „Rektor/in / Präsident/in“); ohne Dubletten, Reihenfolge stabil."""
    basis = _GESCHLECHT.sub("", _KLAMMER_GESCHLECHT.sub(r"\1", z.get("norm") or ""))
    norm = _TRENNER.sub(" ", basis)
    extra = [_KLAMMER.sub("", f) for f in (norm, z.get("maennlich") or "", z.get("weiblich") or "")]
    # Alternativen nur ohne „ - “-Zusatz und wenn jeder Teil großgeschrieben beginnt („Lehrer/in, akadem.“
    # ist ein Zusatz, keine Alternative; „Sänger/in - Volkstümlich, Volksmusiker/in“ bleibt ein Ganzes).
    teile = _ALTERNATIVE.split(extra[0])
    if len(teile) > 1 and not _TRENNER.search(basis) and all(t[:1].isupper() for t in teile):
        extra += teile
    out: list[str] = []
    for f in (z.get("maennlich"), z.get("weiblich"), norm, *extra):
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


def zuordnung(eintrag: dict, kuratierung: dict[str, dict], ohdab: dict[str, dict]) -> dict | None:
    """Nur geprüfte Schreibweisen mit gültiger ohdab_id (Spec §6.1); eine geprüfte ID, die im Schnappschuss
    fehlt, ist ein Fehler, kein stiller Ausfall."""
    s = (eintrag.get("Beruf o. ä.") or "").strip()
    z = kuratierung.get(s) if s else None
    if not z or z.get("geprueft") != "ja" or not z.get("ohdab_id"):
        return None
    o = ohdab.get(z["ohdab_id"])
    if o is None:
        raise ValueError(f"kuratierung/berufe.csv: {s!r} ist geprüft, aber ohdab_id {z['ohdab_id']!r} fehlt im Schnappschuss")
    niveau = "unsicher" if z.get("niveau_unsicher") == "ja" else o["niveau"]
    norm = o["maennlich"] or o["norm"]
    from pipeline.lib.stellung import stellung_export, stellung_quelle   # lokal: stellung.py importiert berufe.py
    return dict(beruf=z["beruf"], ohdab=z["ohdab_id"], niveau=niveau, gattung=o["gattung"], gattung_id=o["gattung_id"],
               status=z.get("status", ""), norm=norm, stellung=stellung_export(z), stellung_quelle=stellung_quelle(z))
