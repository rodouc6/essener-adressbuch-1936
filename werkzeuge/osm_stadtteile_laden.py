"""Heutige Stadtteilgrenzen Essens aus OpenStreetMap (Overpass) → build/osm_stadtteile.json (Spec §5.4a).

Aufruf: python3 werkzeuge/osm_stadtteile_laden.py [--url https://overpass-api.de/api/interpreter] [--wurzel PFAD]
Relationen boundary=administrative, admin_level=10 innerhalb des Regionalschlüssels 051130000000 (Stadt Essen).
Lizenz: ODbL, © OpenStreetMap-Mitwirkende. Bei 429/504 mit Wartezeit wiederholen (wie osm_strassen_laden.py).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import datetime
import json
from pathlib import Path

import requests

from pipeline.lib.io import projektwurzel
from pipeline.lib.stadtteile import ringe_aus_relation

ABFRAGE = ('[out:json][timeout:120];area["de:regionalschluessel"="051130000000"]->.e;'
           'relation["boundary"="administrative"]["admin_level"="10"](area.e);out geom;')
KOPF = {"User-Agent": "essener-adressbuch-1936 (Forschungsprojekt; Kontakt siehe Repository)"}


def stadtteile_aus(osm_json: dict) -> dict[str, list]:
    """Wandelt die Overpass-Relationen in Ringe um. Prüft nebenbei die Annahme aus docs/stadtteile.md,
    dass keine Essener Relation `inner`-Mitglieder (Enklaven) hat — falls doch, Warnung auf stderr mit
    Relationsname, damit das bei jedem Abruf auffällt statt still ignoriert zu werden."""
    out = {}
    for el in osm_json.get("elements", []):
        if el.get("type") != "relation":
            continue
        name = (el.get("tags", {}).get("name") or "").strip()
        if not name:
            continue
        innen = sum(1 for m in el.get("members", []) if m.get("role") == "inner")
        if innen:
            print(f"WARNUNG: Relation {name!r} hat {innen} inner-Mitglied(er) — Enklave nicht ausgeschnitten (docs/stadtteile.md)", file=sys.stderr)
        out[name] = ringe_aus_relation(el.get("members", []))
    return dict(sorted(out.items()))


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="https://overpass-api.de/api/interpreter")
    ap.add_argument("--wurzel", default=None)
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    r = requests.post(a.url, data={"data": ABFRAGE}, headers=KOPF, timeout=300)
    r.raise_for_status()
    st = stadtteile_aus(r.json())
    if len(st) < 40:
        raise SystemExit(f"nur {len(st)} Stadtteile erhalten — Overpass unvollständig? Abbruch, nichts geschrieben")
    (W / "build").mkdir(exist_ok=True)
    paket = {"stand": datetime.date.today().isoformat(), "quelle": "OpenStreetMap (ODbL), boundary=administrative admin_level=10", "stadtteile": st}
    (W / "build" / "osm_stadtteile.json").write_text(json.dumps(paket, ensure_ascii=False), encoding="utf-8")
    k = {"stadtteile": len(st), "ringe": sum(len(v) for v in st.values())}
    print(json.dumps(k, ensure_ascii=False)); return k


if __name__ == "__main__":
    main()
