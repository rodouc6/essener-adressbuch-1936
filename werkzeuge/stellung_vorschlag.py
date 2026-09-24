"""Vorschlag der sozialen Stellung je Berufsschreibweise (Teilprojekt 5a, Spec §5.1).

Aufruf: python3 werkzeuge/stellung_vorschlag.py [--wurzel PFAD]
Liest kuratierung/berufe.csv, kuratierung/ohdab.csv, kuratierung/merkmale/*.csv; schreibt kuratierung/berufe.csv
mit gefüllter Spalte `stellung`, wo `stellung_geprueft` leer ist. `stellung_geprueft` setzt nur der Mensch.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import json
from collections import Counter
from pathlib import Path

from pipeline.lib.berufe import FELDER_KURATIERUNG, lade_ohdab
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv
from pipeline.lib.merkmale import Regel, lade_regeln
from pipeline.lib.stellung import stellung_vorschlag


def ergaenze_stellung(zeilen: list[dict], ohdab: dict[str, dict], regeln: list[Regel]) -> tuple[list[dict], dict]:
    """Geprüfte Stellung bleibt; sonst Vorschlag. Kennzahlen: Grund → Zeilen („ohne“ = unbestimmt, „geprueft“ = belassen)."""
    out, kenn = [], Counter()
    for z in zeilen:
        z = {k: (v or "") for k, v in z.items()}
        if z.get("stellung_geprueft") == "ja":
            kenn["geprueft"] += 1
        else:
            klasse, grund = stellung_vorschlag(z, ohdab.get(z.get("ohdab_id", "")), regeln)
            z["stellung"], z["stellung_geprueft"] = klasse, ""
            kenn[grund or "ohne"] += 1
        out.append(z)
    return out, dict(kenn)


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wurzel", default=None)
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    pfad = W / "kuratierung" / "berufe.csv"
    neu, kenn = ergaenze_stellung(lies_csv(pfad), lade_ohdab(W / "kuratierung" / "ohdab.csv"), lade_regeln(W / "kuratierung" / "merkmale"))
    schreib_csv(pfad, neu, FELDER_KURATIERUNG)
    print(json.dumps(kenn, ensure_ascii=False, indent=1))
    return kenn


if __name__ == "__main__":
    main()
