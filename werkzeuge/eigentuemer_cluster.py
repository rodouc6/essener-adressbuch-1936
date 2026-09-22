"""Eigentümer aus Teil II clustern (Teilprojekt 3, Spec §4).

Aufruf: python3 werkzeuge/eigentuemer_cluster.py [--min-haeuser 5]
Liest build/eintraege.csv, schreibt build/eigentuemer_vorschlag.csv und build/eigentuemer_belege.json
und legt fehlende Zeilen in kuratierung/eigentuemer.csv an (gesperrte Zeilen bleiben unberührt).
"""
from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.lib.io import lies_csv

# Rechtsformen: Buchschreibungen wie „A.G.“, „A. G.“, „A.-G.“, „AG.“, „A. -G.“ → ein Token.
RECHTSFORMEN: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\be\.?\s?g\.?\s?m\.?\s?b\.?\s?h\b\.?", re.I), "egmbh"),
    (re.compile(r"\bg\.?\s?m\.?\s?b\.?\s?h\b\.?", re.I), "gmbh"),
    (re.compile(r"\ba\.?\s?-?\s?g\b\.?", re.I), "ag"),
    (re.compile(r"\be\.\s?v\b\.?", re.I), "ev"),
    (re.compile(r"\bk\.\s?-?\s?g\b\.?", re.I), "kg"),
]
RECHTSFORM_TOKENS = {"egmbh", "gmbh", "ag", "ev", "kg", "ohg"}
ANZEIGE = {"egmbh": "eGmbH", "gmbh": "GmbH", "ag": "AG", "ev": "e. V.", "kg": "KG"}
STOPP = {"der", "die", "das", "und", "u", "von", "zu", "in", "für", "des"}

Katalog = dict


def lade_katalog(pfad: Path | str) -> Katalog:
    abk: dict[str, tuple[str, str]] = {}
    firmenwoerter: set[str] = set()
    for z in lies_csv(pfad):
        kurz, lang, kontext = (z.get("kurz") or "").strip().lower(), (z.get("lang") or "").strip().lower(), (z.get("kontext") or "").strip()
        if kurz:
            abk[kurz] = (lang, kontext)
        elif kontext == "firmenwort" and lang:
            firmenwoerter.add(lang)
    return dict(abk=abk, firmenwoerter=firmenwoerter)


def _rechtsformen(text: str) -> str:
    for muster, ersatz in RECHTSFORMEN:
        text = muster.sub(" " + ersatz + " ", text)
    return text


def normalisiere(name: str, katalog: Katalog) -> str:
    """Vergleichsschlüssel: klein, Rechtsformen vereinheitlicht, Abkürzungen (nur mit Punkt) aufgelöst,
    Komposita aus Firmenwörtern zusammengezogen, Interpunktion entfernt (Spec §4.2)."""
    t = unicodedata.normalize("NFKC", name).lower()
    t = _rechtsformen(t)
    t = t.replace(",", " ").replace("/", " ")
    roh = [x for x in re.split(r"\s+", t.strip()) if x]
    tokens: list[str] = []
    for i, tok in enumerate(roh):
        abgekuerzt = tok.endswith(".")
        kern = tok.strip(".-").lower()
        if not kern:
            continue
        eintrag = katalog["abk"].get(kern) if abgekuerzt else None
        if eintrag:
            lang, kontext = eintrag
            naechster = roh[i + 1].strip(".-") if i + 1 < len(roh) else ""
            if kontext == "firmenwort":
                folgt = katalog["abk"].get(naechster, (naechster, ""))[0] if roh[i + 1:] and roh[i + 1].endswith(".") else naechster
                if folgt in katalog["firmenwoerter"]:
                    kern = lang
            else:
                kern = lang
        tokens.append(kern)
    # Komposita: „bergwerks verein“ → „bergwerksverein“, wenn beide Teile Firmenwörter sind und das
    # zusammengesetzte Wort ebenfalls als Firmenwort geführt wird.
    out: list[str] = []
    for tok in tokens:
        if out and out[-1] in katalog["firmenwoerter"] and tok in katalog["firmenwoerter"] and (out[-1] + tok) in katalog["firmenwoerter"]:
            out[-1] = out[-1] + tok
        else:
            out.append(tok)
    return re.sub(r"[^\w\s]", "", " ".join(out)).strip()


def rechtsform_anzeige(name: str) -> str:
    """Auto-Name-Hilfe: Rechtsform im Anzeigenamen vereinheitlichen, Rest unverändert (Spec §4.4)."""
    t = name
    for muster, ersatz in RECHTSFORMEN:
        t = muster.sub(" " + ANZEIGE[ersatz] + " ", t)
    t = re.sub(r"\s*,\s*(AG|GmbH|eGmbH|KG|e\. V\.)\b", r" \1", t)
    return re.sub(r"\s+", " ", t).strip()
