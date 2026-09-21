"""Stufe 06: Datenpaket der Karte aus build/eintraege.csv (Spec docs/superpowers/specs/2026-09-21-basiskarte-design.md §5)."""
from __future__ import annotations

import hashlib
import re
import unicodedata

from pipeline.lib.stufen import ADRESSSCHLUESSEL

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"})
_NICHT_ZEICHEN = re.compile(r"[^a-z0-9 ]+")
_ETAGEN = {"erdg.": 0, "erdg": 0, "parterre.": 0, "parterre": 0, "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5}
ETAGE_OHNE = 99


def adress_id(eintrag: dict) -> str:
    """Stabile Adress-ID: SHA-1 über den ADRESSSCHLUESSEL, 12 Hex-Zeichen."""
    roh = "\x1f".join(eintrag.get(f, "") for f in ADRESSSCHLUESSEL)
    return hashlib.sha1(roh.encode("utf-8")).hexdigest()[:12]


def scherbe(aid: str) -> str:
    return aid[:2]


def falte(text: str) -> str:
    """Suchschlüssel: klein, Umlaute aufgelöst, Akzente entfernt, nur a–z, 0–9 und Leerzeichen."""
    t = (text or "").translate(_UMLAUTE).lower()
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = _NICHT_ZEICHEN.sub(" ", t)
    return " ".join(t.split())


def praefix2(text: str) -> str:
    """Scherbenname des Suchindex: die ersten zwei Zeichen des gefalteten Schlüssels, `_` wenn leer."""
    k = falte(text).replace(" ", "")
    return k[:2] if k else "_"


def etagen_rang(lage: str) -> int:
    return _ETAGEN.get((lage or "").strip().lower(), ETAGE_OHNE)


def sortiere_eintraege(eintraege: list[dict]) -> list[dict]:
    """Etage laut Buch zuerst (Erdg., I, II …), Einträge ohne Etage danach; innerhalb alphabetisch."""
    return sorted(eintraege, key=lambda e: (etagen_rang(e.get("lage", "")), falte(e.get("lastname", "")),
                                            falte(e.get("firstname", "")), e.get("id", "")))
