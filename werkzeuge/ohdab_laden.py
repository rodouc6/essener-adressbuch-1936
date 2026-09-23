"""OhdAB-Schnappschuss von FactGrid (SPARQL) → kuratierung/ohdab.csv (Spec §3.1).

Aufruf: python3 werkzeuge/ohdab_laden.py [--ziel kuratierung/ohdab.csv]
Quelle: Ontologie historischer, deutschsprachiger Amts- und Berufsbezeichnungen (Moeller, Uni Halle),
publiziert auf FactGrid, CC BY 4.0. Bei Netzfehler bleibt ein vorhandener Schnappschuss unverändert.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import csv
import io
import urllib.error
import urllib.parse
import urllib.request

from pipeline.lib.berufe import FELDER_OHDAB, niveau_schluessel
from pipeline.lib.io import projektwurzel, schreib_csv

ENDPUNKT = "https://database.factgrid.de/sparql"
# P904 OhdAB ID, P914 Normbezeichnung, P889/P888 männliche/weibliche Form, P911 Anforderungsniveau, P1007 Kategorie
ABFRAGE = """
SELECT ?i ?id ?norm ?m ?w ?nivLabel ?kat WHERE {
  ?i wdt:P904 ?id . ?i wdt:P914 ?norm . FILTER(LANG(?norm)="de" || LANG(?norm)="")
  OPTIONAL { ?i wdt:P889 ?m } OPTIONAL { ?i wdt:P888 ?w } OPTIONAL { ?i wdt:P911 ?niv }
  OPTIONAL { ?i wdt:P1007 ?k . ?k rdfs:label ?kat FILTER(LANG(?kat)="de") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de". }
}"""


def hole(endpunkt: str = ENDPUNKT, timeout: int = 300) -> str:
    url = endpunkt + "?" + urllib.parse.urlencode({"query": ABFRAGE})
    req = urllib.request.Request(url, headers={"Accept": "text/csv", "User-Agent": "essener-adressbuch-1936 (ohdab_laden.py)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def zeilen_aus(csv_text: str) -> list[dict]:
    """SPARQL-CSV → Schnappschuss-Zeilen; je ohdab_id genau eine (erste gewinnt), sortiert nach ohdab_id.
    gattung_id = Teil der ID vor dem Bindestrich; gattung = Kategorielabel ohne „<ID>: “-Präfix."""
    gesehen: dict[str, dict] = {}
    for r in csv.DictReader(io.StringIO(csv_text)):
        oid = (r.get("id") or "").strip()
        if not oid or oid in gesehen:
            continue
        gattung_id = oid.split("-")[0].strip()
        kat = (r.get("kat") or "").strip()
        if kat.startswith(gattung_id + ":"):
            kat = kat[len(gattung_id) + 1:].strip()
        gesehen[oid] = dict(ohdab_id=oid, qid=(r.get("i") or "").rsplit("/", 1)[-1], norm=(r.get("norm") or "").strip(),
                            maennlich=(r.get("m") or "").strip(), weiblich=(r.get("w") or "").strip(),
                            niveau=niveau_schluessel(r.get("nivLabel") or ""), gattung_id=gattung_id, gattung=kat)
    return [gesehen[k] for k in sorted(gesehen)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ziel", default=None)
    a = ap.parse_args(argv)
    ziel = pathlib.Path(a.ziel) if a.ziel else projektwurzel() / "kuratierung" / "ohdab.csv"
    try:
        text = hole()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"FactGrid nicht erreichbar ({e}); {ziel} bleibt unverändert", file=sys.stderr)
        return 1
    zeilen = zeilen_aus(text)
    if len(zeilen) < 40000:
        print(f"nur {len(zeilen)} Items erhalten (erwartet ≈ 46.000) — Abbruch, {ziel} bleibt unverändert", file=sys.stderr)
        return 1
    schreib_csv(ziel, zeilen, FELDER_OHDAB)
    print(f"{len(zeilen)} OhdAB-Items → {ziel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
