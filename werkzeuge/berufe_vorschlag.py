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

from rapidfuzz import fuzz, process

from pipeline.lib.berufe import (AUTOMATIK, FELDER_KURATIERUNG, STATUS, falte_form, formen_von, gesperrt,
                                 lade_kuratierung, lade_ohdab)
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv

# Status-Zusätze (Spec §3.3): als eigenes Wort (Wortanfang), nicht mitten im Wort („Berginval.“ bleibt dem Katalog).
STATUS_MUSTER = [
    ("ruhestand", re.compile(r"(?<![\wäöüÄÖÜ])(i\.\s?R\.|a\.\s?D\.|Pensionär(in)?|Pension\.|Pens\.|Rentner(in)?|Rentenempf\.|Rentn\.|Rent\.|Ruhest\.)(?![\wäöüÄÖÜ])")),
    ("invalide", re.compile(r"(?<![\wäöüÄÖÜ])(Invalide|Invalidin|Invalid\.|Inval\.|Inval)(?![\wäöüÄÖÜ])")),
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


# Nur-Status-Schreibweisen („Invalide“, „Pensionär“, „Rentner“, „Witwe“): OhdAB-Item des Status
# (Spec §3.3). IDs aus dem Schnappschuss kuratierung/ohdab.csv (Stand 2026-09-23):
# grep -i ",Invalide/Invalidin," / ",Rentner/in," / ",Witwe/r," kuratierung/ohdab.csv.
STATUS_ITEMS = {
    "invalide": "A 10200-502",   # Invalide/Invalidin
    "ruhestand": "A 10300-529",  # Rentner/in
    "witwe": "A 21200-502",      # Witwe/r
}
SCHWELLE = 0.90


def formen_index(ohdab: dict[str, dict]) -> dict[str, list[str]]:
    idx: dict[str, list[str]] = defaultdict(list)
    for oid, z in ohdab.items():
        for f in formen_von(z):
            if oid not in idx[f]:
                idx[f].append(oid)
    return dict(idx)


def waehle(ids: list[str], ohdab: dict[str, dict]) -> str:
    """Mehrdeutig → kürzeste Normbezeichnung, bei Gleichstand kleinste ID (Spec §4 Schritt 3)."""
    return sorted(ids, key=lambda i: (len(ohdab[i]["norm"]), i))[0] if ids else ""


def exakt(beruf: str, index: dict[str, list[str]]) -> list[str]:
    return list(index.get(falte_form(beruf), []))


def aehnlich(beruf: str, index: dict[str, list[str]], schwelle: float = SCHWELLE, n: int = 20) -> list[tuple[str, float]]:
    """RapidFuzz ratio auf den gefalteten Formen; je ID der beste Wert; absteigend; nur ≥ schwelle."""
    k = falte_form(beruf)
    if not k:
        return []
    best: dict[str, float] = {}
    for form, wert, _ in process.extract(k, list(index), scorer=fuzz.ratio, limit=n * 5, score_cutoff=schwelle * 100):
        for oid in index[form]:
            best[oid] = max(best.get(oid, 0.0), wert / 100)
    return sorted(best.items(), key=lambda x: (-x[1], x[0]))[:n]


def vorschlag_fuer(schreibweise: str, katalog: dict[str, tuple[str, str]], ohdab: dict[str, dict], index: dict[str, list[str]]) -> dict:
    """Spec §4 Schritte 1–4; LLM-Reserve läuft getrennt (Task 5).

    Nur-Status-Zweig (`beruf` leer, `status` gesetzt): zuerst die Original-Schreibweise
    (getrimmt) exakt gegen den Formenindex abgleichen — trifft z. B. „Pensionär“ oder
    „Rentner“ direkt ein OhdAB-Item, ist das genauer als das pauschale STATUS_ITEMS-Item
    (Ruling des Controllers, Task 3). Erst ohne Treffer fällt die Automatik auf STATUS_ITEMS
    zurück (Grund „status“).
    """
    kern, status = zerlege(schreibweise)
    beruf, kat_status, vollstaendig = loese_auf(kern, katalog)
    status = [s for s in STATUS if s in status or s in kat_status]
    gruende: list[str] = []
    if beruf != kern:
        gruende.append("katalog")
    kandidaten: list[list] = []
    oid = ""
    if not beruf and status:
        roh = (schreibweise or "").strip()
        ids = exakt(roh, index)
        if ids:
            oid = waehle(ids, ohdab)
            beruf = ohdab[oid]["maennlich"] or ohdab[oid]["norm"]
            gruende.append("status; exakt")
            kandidaten = [[i, "exakt", 1.0] for i in sorted(ids, key=lambda i: (len(ohdab[i]["norm"]), i))]
        else:
            kandidat = STATUS_ITEMS.get(status[0], "")
            oid = kandidat if kandidat in ohdab else ""
            if oid:
                beruf = ohdab[oid]["maennlich"] or ohdab[oid]["norm"]
                gruende.append("status")
    elif beruf and vollstaendig:
        ids = exakt(beruf, index)
        if ids:
            oid = waehle(ids, ohdab)
            gruende.append("exakt")
            kandidaten = [[i, "exakt", 1.0] for i in sorted(ids, key=lambda i: (len(ohdab[i]["norm"]), i))]
    if beruf and not oid:
        aehn = aehnlich(beruf, index)
        if aehn:
            oid = aehn[0][0]
            gruende.append(f"aehnlich {aehn[0][1]:.2f}")
        kandidaten = [[i, "aehnlich", round(w, 2)] for i, w in aehn]
    return dict(beruf=beruf, status=";".join(status), ohdab_id=oid, grund="; ".join(gruende) if oid else "", kandidaten=kandidaten)


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
