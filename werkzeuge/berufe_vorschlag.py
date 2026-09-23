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
                                 lade_kuratierung, lade_ohdab, norm_form)
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv

# Status-Zusätze (Spec §3.3): als eigenes Wort (Wortanfang), nicht mitten im Wort („Berginval.“ bleibt dem Katalog).
STATUS_MUSTER = [
    ("ruhestand", re.compile(r"(?<![\wäöüÄÖÜ])(i\.\s?R\.|a\.\s?D\.|Pensionär(in)?|Pension\.|Pens\.|Rentner(in)?|Rentenempf\.|Rentn\.|Rent\.|Ruhest\.)(?![\wäöüÄÖÜ])")),
    ("invalide", re.compile(r"(?<![\wäöüÄÖÜ])(Invalide|Invalidin|Invalid\.|Inval\.|Inv\.|Inval)(?![\wäöüÄÖÜ])")),
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


def waehle(ids: list[str], ohdab: dict[str, dict], beruf: str = "") -> str:
    """Mehrdeutig → zuerst Items, deren Normbezeichnung (ohne Geschlechtszusatz) genau dem Beruf
    entspricht, also ohne Qualifizierung wie „im Nebenerwerb“, „ - Bergbau“, „(kaufmännisches
    Geschäft)“; danach kürzeste Normbezeichnung, bei Gleichstand kleinste ID (Spec §4 Schritt 3).

    Ohne `beruf` bleibt es beim alten Verhalten (kürzeste Norm zuerst)."""
    if not ids:
        return ""
    k = falte_form(beruf)
    return sorted(ids, key=lambda i: (not (k and norm_form(ohdab[i]) == k), len(ohdab[i]["norm"]), i))[0]


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
            oid = waehle(ids, ohdab, roh)
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
            oid = waehle(ids, ohdab, beruf)
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


def sammle(eintraege: list[dict]) -> tuple[dict[str, int], dict[str, list[dict]]]:
    """Nennungen je Schreibweise (Teil I+II) und bis zu 5 Belege (Teil I bevorzugt, verschiedene Adressen)."""
    nennungen: dict[str, int] = defaultdict(int)
    belege: dict[str, list[dict]] = defaultdict(list)
    adressen: dict[str, set[str]] = defaultdict(set)
    for e in sorted(eintraege, key=lambda e: e.get("teil") != "I"):
        if e.get("teil") not in ("I", "II"):
            continue
        s = (e.get("Beruf o. ä.") or "").strip()
        if not s:
            continue
        nennungen[s] += 1
        nr = ((e.get("hausnr") or "") + (e.get("hausnr_zusatz") or "")).strip()
        adresse = " ".join(x for x in (e.get("strasse_roh", ""), nr) if x)
        if e.get("Vorort"):
            adresse += f", {e['Vorort']}"
        if len(belege[s]) < 5 and adresse not in adressen[s]:
            adressen[s].add(adresse)
            name = ", ".join(x for x in ((e.get("lastname") or "").strip(), (e.get("firstname") or "").strip()) if x)
            belege[s].append(dict(name=name, adresse=adresse, teil=e["teil"], seite=e.get("page", "")))
    return dict(nennungen), dict(belege)


def aktualisiere_kuratierung(alt: list[dict], vorschlaege: dict[str, dict], nennungen: dict[str, int], datum: str,
                             min_nennungen: int) -> list[dict]:
    """Gesperrte Zeilen: nur `nennungen` nachführen. Automatik-Zeilen: Vorschlag übernehmen (hinweis bleibt),
    datum nur bei Änderung. Neue Zeilen nur ab der Untergrenze. Verwaistes bleibt stehen."""
    bekannt = lade_kuratierung(alt)
    out = [dict(z) for z in alt]
    index = {z["schreibweise"].strip(): i for i, z in enumerate(out)}
    for s, v in vorschlaege.items():
        n = str(nennungen.get(s, 0))
        if s in bekannt:
            z = out[index[s]]
            z["nennungen"] = n
            if gesperrt(bekannt[s]):
                continue
            neu = dict(beruf=v["beruf"], status=v["status"], ohdab_id=v["ohdab_id"], vorschlag_grund=v["grund"])
            if any(z.get(k, "") != w for k, w in neu.items()):
                z.update(neu, datum=datum)
        elif nennungen.get(s, 0) >= min_nennungen:
            out.append(dict(schreibweise=s, nennungen=n, beruf=v["beruf"], status=v["status"], ohdab_id=v["ohdab_id"],
                            niveau_unsicher="", geprueft="", vorschlag_grund=v["grund"], bearbeiter=AUTOMATIK, datum=datum, hinweis=""))
    return out


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-nennungen", type=int, default=5)
    ap.add_argument("--llm", action="store_true", help="LLM-Reserve für Zeilen ohne Vorschlag (Task 5)")
    ap.add_argument("--wurzel", default=None, help="Projektwurzel (Tests)")
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    ohdab = lade_ohdab(W / "kuratierung" / "ohdab.csv")
    index = formen_index(ohdab)
    katalog = lade_katalog(W / "kuratierung" / "berufe_abkuerzungen.csv")
    nennungen, belege = sammle(lies_csv(W / "build" / "eintraege.csv"))
    pfad = W / "kuratierung" / "berufe.csv"
    alt = lies_csv(pfad) if pfad.exists() else []
    bekannt = lade_kuratierung(alt)
    relevant = sorted(s for s in nennungen if nennungen[s] >= a.min_nennungen or s in bekannt)
    vorschlaege = {s: vorschlag_fuer(s, katalog, ohdab, index) for s in relevant}
    neu = aktualisiere_kuratierung(alt, vorschlaege, nennungen, datetime.date.today().isoformat(), a.min_nennungen)
    if a.llm:
        from werkzeuge.berufe_llm import ergaenze_llm   # Task 5
        neu = ergaenze_llm(neu, belege, ohdab, index, datetime.date.today().isoformat())
    schreib_csv(pfad, neu, FELDER_KURATIERUNG)
    (W / "build").mkdir(exist_ok=True)
    (W / "build" / "berufe_belege.json").write_text(json.dumps({s: belege.get(s, []) for s in relevant}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (W / "build" / "berufe_kandidaten.json").write_text(json.dumps({s: v["kandidaten"] for s, v in vorschlaege.items()}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    gruende: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for z in neu:
        g = (z.get("vorschlag_grund") or "").split(" ")[0].rstrip(";") or "ohne"
        gruende[g][0] += 1; gruende[g][1] += int(z.get("nennungen") or 0)
    k = dict(schreibweisen=len(relevant), zeilen=len(neu), nennungen=sum(nennungen[s] for s in relevant),
             gruende={g: dict(werte=w, nennungen=n) for g, (w, n) in sorted(gruende.items())})
    print(json.dumps(k, ensure_ascii=False, indent=1))
    return k


if __name__ == "__main__":
    main()
