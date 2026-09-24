"""Berufsgruppe je OhdAB-Item, das in kuratierung/berufe.csv geprüft vorkommt (Teilprojekt 5a, Spec §5.2).

Aufruf: python3 werkzeuge/gruppen_vorschlag.py [--wurzel PFAD]
Schreibt kuratierung/gruppen.csv (Upsert je ohdab_id: geprüfte Zeilen bleiben, nennungen wird nachgeführt).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import datetime
import json
from collections import defaultdict
from pathlib import Path

from pipeline.lib.berufe import lade_ohdab
from pipeline.lib.gruppen import AUTOMATIK, FELDER_GRUPPEN, gruppe_vorschlag, lade_gruppen
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv


def baue_gruppen(berufe: list[dict], ohdab: dict[str, dict], alt: list[dict], datum: str) -> list[dict]:
    nennungen: dict[str, int] = defaultdict(int)
    for z in berufe:
        oid = (z.get("ohdab_id") or "").strip()
        if oid and z.get("geprueft") == "ja" and oid in ohdab:
            nennungen[oid] += int(z.get("nennungen") or 0)
    bekannt = lade_gruppen(alt)
    out = []
    for oid in sorted(nennungen, key=lambda o: (-nennungen[o], o)):
        z = bekannt.get(oid)
        if z and z.get("geprueft") == "ja":
            out.append(dict(z, nennungen=str(nennungen[oid])))
        else:
            out.append(dict(ohdab_id=oid, norm=ohdab[oid]["norm"], nennungen=str(nennungen[oid]), gruppe=gruppe_vorschlag(ohdab[oid]),
                            geprueft="", bearbeiter=AUTOMATIK, datum=datum, hinweis=(z or {}).get("hinweis", "")))
    return out


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wurzel", default=None)
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    pfad = W / "kuratierung" / "gruppen.csv"
    alt = lies_csv(pfad) if pfad.exists() else []
    neu = baue_gruppen(lies_csv(W / "kuratierung" / "berufe.csv"), lade_ohdab(W / "kuratierung" / "ohdab.csv"), alt, datetime.date.today().isoformat())
    schreib_csv(pfad, neu, FELDER_GRUPPEN)
    k = dict(items=len(neu), geprueft=sum(z["geprueft"] == "ja" for z in neu))
    print(json.dumps(k, ensure_ascii=False)); return k


if __name__ == "__main__":
    main()
