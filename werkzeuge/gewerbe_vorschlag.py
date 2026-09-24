"""Gewerberubriken aus Teil III → kuratierung/gewerbe.csv (Teilprojekt 5a, Spec §5.3).

Aufruf: python3 werkzeuge/gewerbe_vorschlag.py [--wurzel PFAD]
Upsert je Rubrik: geprüfte Zeilen bleiben (betriebe wird nachgeführt), sonst Vorschlag.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import datetime
import json
from collections import Counter
from pathlib import Path

from pipeline.lib.gewerbe import AUTOMATIK, FELDER_GEWERBE, gewerbe_vorschlag, lade_gewerbe, rubrik_von
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv


def baue_gewerbe(eintraege: list[dict], alt: list[dict], datum: str) -> list[dict]:
    betriebe = Counter(rubrik_von(e.get("Firmenname", ""))[1] for e in eintraege if e.get("teil") == "III")
    betriebe.pop("", None)
    bekannt = lade_gewerbe(alt)
    out = []
    for rubrik in sorted(betriebe, key=lambda r: (-betriebe[r], r)):
        z = bekannt.get(rubrik)
        if z and z.get("geprueft") == "ja":
            out.append(dict(z, betriebe=str(betriebe[rubrik])))
        else:
            gruppe, art = gewerbe_vorschlag(rubrik)
            out.append(dict(rubrik=rubrik, betriebe=str(betriebe[rubrik]), gruppe=gruppe, art=art, geprueft="",
                            bearbeiter=AUTOMATIK, datum=datum, hinweis=(z or {}).get("hinweis", "")))
    return out


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wurzel", default=None)
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    pfad = W / "kuratierung" / "gewerbe.csv"
    alt = lies_csv(pfad) if pfad.exists() else []
    neu = baue_gewerbe(lies_csv(W / "build" / "eintraege.csv"), alt, datetime.date.today().isoformat())
    schreib_csv(pfad, neu, FELDER_GEWERBE)
    k = dict(rubriken=len(neu), betriebe=sum(int(z["betriebe"]) for z in neu), geprueft=sum(z["geprueft"] == "ja" for z in neu))
    print(json.dumps(k, ensure_ascii=False)); return k


if __name__ == "__main__":
    main()
