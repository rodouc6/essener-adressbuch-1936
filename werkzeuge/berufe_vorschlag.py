"""Vorschläge für die Berufs-Kuratierung (Teilprojekt 4, Spec §4).

Aufruf: python3 werkzeuge/berufe_vorschlag.py [--min-nennungen 5] [--llm] [--wurzel PFAD]
Liest build/eintraege.csv, kuratierung/ohdab.csv, kuratierung/berufe_abkuerzungen.csv, kuratierung/berufe.csv;
schreibt kuratierung/berufe.csv (Upsert, Sperrregel), build/berufe_belege.json, build/berufe_kandidaten.json.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import datetime
import json
import re
from collections import defaultdict
from pathlib import Path

from pipeline.lib.berufe import (AUTOMATIK, FELDER_KURATIERUNG, STATUS, falte_form, formen_von, gesperrt,
                                 lade_kuratierung, lade_ohdab)
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv

# Status-Zusätze (Spec §3.3): als eigenes Wort (Wortanfang), nicht mitten im Wort („Berginval.“ bleibt dem Katalog).
STATUS_MUSTER = [
    ("ruhestand", re.compile(r"(?<![\wäöüÄÖÜ])(i\.\s?R\.|a\.\s?D\.|Pens\.|Pensionär(in)?|Rentner(in)?|Ruhest\.)(?![\wäöüÄÖÜ])")),
    ("invalide", re.compile(r"(?<![\wäöüÄÖÜ])(Inval\.|Invalide|Invalidin)(?![\wäöüÄÖÜ])")),
    ("witwe", re.compile(r"(?<![\wäöüÄÖÜ])(Ww\.|Wwe\.|Witwe)(?![\wäöüÄÖÜ])")),
]
_REST = re.compile(r"^[\s,;]+|[\s,;]+$")


def zerlege(schreibweise: str) -> tuple[str, list[str]]:
    """Status-Zusätze abtrennen → (Kern, Statusliste in STATUS-Reihenfolge)."""
    kern = schreibweise or ""
    gefunden: list[str] = []
    for status, muster in STATUS_MUSTER:
        if muster.search(kern):
            gefunden.append(status)
            kern = muster.sub(" ", kern)
    kern = _REST.sub("", " ".join(kern.split()))
    return kern, [s for s in STATUS if s in gefunden]


def lade_katalog(pfad: Path | str) -> dict[str, tuple[str, str]]:
    """kurz → (lang, status). `status` optional (z. B. Berginval. → Bergmann + invalide)."""
    out: dict[str, tuple[str, str]] = {}
    for z in lies_csv(pfad):
        kurz, lang = (z.get("kurz") or "").strip(), (z.get("lang") or "").strip()
        if kurz and lang:
            out[kurz] = (lang, (z.get("status") or "").strip())
    return out


def loese_auf(kern: str, katalog: dict[str, tuple[str, str]]) -> tuple[str, list[str], bool]:
    """Ganze Folge aus dem Katalog zuerst, sonst wortweise; Wörter mit Punkt, die der Katalog nicht kennt,
    bleiben stehen und machen das Ergebnis unvollständig (kein Exakt-Abgleich, Spec §4 Schritt 2)."""
    status: list[str] = []
    if kern in katalog:
        lang, st = katalog[kern]
        return lang, ([st] if st else []), True
    woerter, vollstaendig = [], True
    for w in kern.split():
        if w in katalog:
            lang, st = katalog[w]
            woerter.append(lang)
            if st and st not in status:
                status.append(st)
        else:
            if w.endswith(".") and w not in ("u.",):
                vollstaendig = False
            woerter.append(w)
    return " ".join(woerter), status, vollstaendig
