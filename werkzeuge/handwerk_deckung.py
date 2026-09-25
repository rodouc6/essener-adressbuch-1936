"""Deckungstabelle Handwerksberufe: Teil-III-Betriebe gegen Inhaber-Kennzeichnungen in Teil I (docs/stellung.md, Weg 3).

Aufruf: python3 werkzeuge/handwerk_deckung.py [--wurzel PFAD]
Liest kuratierung/berufe.csv und kuratierung/gewerbe.csv; schreibt
  build/handwerk_deckung.json   — für werkzeuge/berufe.html (Kennzahl je Schreibweise)
  docs/stellung_deckung.md      — prüfbare Tabelle mit den getroffenen Rubriken
Nach jeder Handprüfungsrunde neu ausführen: „offen“ und „inhaber“ folgen der Spalte `stellung`.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import datetime as dt
import json
from pathlib import Path

from pipeline.lib.deckung import MIN_OFFEN, SCHWELLE, deckung
from pipeline.lib.io import lies_csv, projektwurzel


def markdown(zeilen: list[dict], datum: str) -> str:
    kopf = [
        "# Deckung Handwerksberufe: Teil III gegen Teil I",
        "",
        f"Erzeugt von `werkzeuge/handwerk_deckung.py` am {datum} — nicht von Hand bearbeiten. Grundlage der Handprüfung",
        "der sozialen Stellung nach Weg 3 (`docs/stellung.md`, Grenzfälle).",
        "",
        "Je Berufsfamilie: **offen** = Nennungen ohne Meister-/Gewerbezusatz mit Stellung `arbeiter`/`unbestimmt`;",
        "**Inhaber** = Nennungen mit Stellung `selbstaendige`; **Betriebe** = Betriebe der genannten Rubriken in Teil III;",
        "**Lücke** = Betriebe − Inhaber (mindestens 0) = Betriebe, die kein gekennzeichneter Eintrag erklärt;",
        "**Quote** = Lücke / offen = Anteil der offenen Nennungen, der mindestens Inhaber sein muss.",
        f"Empfehlung: Quote < {SCHWELLE:.0%} → `arbeiter` bestätigen; sonst `unbestimmt` bis zum Adressabgleich Teil I ↔ Teil III.",
        f"Aufgenommen sind Familien mit Betrieben in Teil III und Inhaberform in Teil I oder ≥ {MIN_OFFEN} offenen Nennungen.",
        "Die Zuordnung Rubrik ↔ Beruf ist eine Heuristik (erstes Wort der Rubrik, Synonyme wie Tischler/Schreiner);",
        "Quoten über 100 % heißen: mehr unerklärte Betriebe als offene Nennungen — die Familie ist zu eng gefasst.",
        "",
        "| Familie | offen | Inhaber | Betriebe | Lücke | Quote | Empfehlung | Rubriken (Teil III) | offene Schreibweisen |",
        "|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    zeilen_md = []
    for r in zeilen:
        quote = "–" if r["quote"] is None else f"{r['quote']:.0%}"
        zeilen_md.append(f"| {r['familie']} | {r['offen']} | {r['inhaber']} | {r['betriebe']} | {r['luecke']} | {quote} | {r['empfehlung'] or '–'} "
                         f"| {', '.join(r['rubriken'])} | {', '.join(r['schreibweisen_offen'])} |")
    return "\n".join(kopf + zeilen_md) + "\n"


def main(argv: list[str] | None = None) -> list[dict]:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wurzel", default=None)
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    zeilen = deckung(lies_csv(W / "kuratierung" / "berufe.csv"), lies_csv(W / "kuratierung" / "gewerbe.csv"))
    (W / "build").mkdir(exist_ok=True)
    familien = {r["familie"]: {k: v for k, v in r.items() if k != "schreibweisen_offen"} for r in zeilen}
    schreibweisen = {s: r["familie"] for r in zeilen for s in r["schreibweisen_offen"]}
    (W / "build" / "handwerk_deckung.json").write_text(json.dumps({"familien": familien, "schreibweisen": schreibweisen}, ensure_ascii=False, indent=1), encoding="utf-8")
    (W / "docs" / "stellung_deckung.md").write_text(markdown(zeilen, dt.date.today().isoformat()), encoding="utf-8")
    n_off = sum(1 for r in zeilen if r["empfehlung"] == "unbestimmt")
    print(json.dumps({"familien": len(zeilen), "empfehlung_unbestimmt": n_off, "nennungen_offen": sum(r["offen"] for r in zeilen)}, ensure_ascii=False))
    return zeilen


if __name__ == "__main__":
    main()
