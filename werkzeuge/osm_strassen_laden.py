"""Heutige Straßenlinien Essens aus OpenStreetMap (Overpass) → build/osm_strassen.json (Teilprojekt 5a, Spec §5.4).

Aufruf: python3 werkzeuge/osm_strassen_laden.py [--url https://overpass-api.de/api/interpreter] [--wurzel PFAD] [--halbieren]
Nur benannte Fahrstraßen (highway ohne footway/path/steps/cycleway/track/service ohne Namen); je Name alle Segmente.
Die Linien sind die HEUTIGE Führung — die Karte kennzeichnet das (docs/osm_strassen.md). Lizenz: ODbL, © OpenStreetMap-Mitwirkende.
Mit --halbieren wird die Essen-Area-Abfrage durch zwei Bounding-Box-Abfragen (Nord/Süd) ersetzt und
zusammengeführt — nur nötig, wenn die einteilige Abfrage am Overpass-Server-Timeout scheitert.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import datetime
import json
from collections import defaultdict
from pathlib import Path

import requests

from pipeline.lib.io import projektwurzel

ESSEN_RELATION = 62713          # OSM-Relation der Stadt Essen; Area-ID = 3600000000 + Relation
_AUSSEN = {"footway", "path", "steps", "cycleway", "track", "bridleway", "corridor", "platform", "construction", "proposed"}
# Essener Stadtgebiet grob in zwei Hälften (Süd/Nord); nur für --halbieren.
_BBOX_SUED = (51.30, 6.85, 51.44, 7.20)
_BBOX_NORD = (51.44, 6.85, 51.58, 7.20)


def overpass_abfrage(bbox: tuple[float, float, float, float] | None = None) -> str:
    if bbox is None:
        return (f"[out:json][timeout:300];area({3600000000 + ESSEN_RELATION})->.essen;"
                "way[\"highway\"][\"name\"](area.essen);out geom;")
    s, w, n, o = bbox
    return f"[out:json][timeout:300];way[\"highway\"][\"name\"]({s},{w},{n},{o});out geom;"


def linien_aus(osm_json: dict) -> dict[str, list[list[list[float]]]]:
    linien: dict[str, list] = defaultdict(list)
    for el in osm_json.get("elements", []):
        if el.get("type") != "way":
            continue
        tags = el.get("tags", {})
        name = (tags.get("name") or "").strip()
        if not name or tags.get("highway") in _AUSSEN:
            continue
        linien[name].append([[p["lon"], p["lat"]] for p in el.get("geometry", [])])
    return dict(sorted(linien.items()))


def _merge(a: dict[str, list], b: dict[str, list]) -> dict[str, list]:
    merged: dict[str, list] = defaultdict(list)
    for d in (a, b):
        for name, segmente in d.items():
            merged[name].extend(segmente)
    return dict(sorted(merged.items()))


def _abrufen(url: str, query: str, headers: dict) -> dict:
    r = requests.post(url, data={"data": query}, headers=headers, timeout=600)
    r.raise_for_status()
    return r.json()


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="https://overpass-api.de/api/interpreter")
    ap.add_argument("--wurzel", default=None)
    ap.add_argument("--halbieren", action="store_true", help="Abfrage in zwei Bounding-Box-Hälften (Nord/Süd) teilen")
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    headers = {"User-Agent": "essener-adressbuch-1936/1.0 (+https://github.com/rodouc6/essener-adressbuch-1936)"}
    if a.halbieren:
        sued = linien_aus(_abrufen(a.url, overpass_abfrage(_BBOX_SUED), headers))
        nord = linien_aus(_abrufen(a.url, overpass_abfrage(_BBOX_NORD), headers))
        linien = _merge(sued, nord)
    else:
        linien = linien_aus(_abrufen(a.url, overpass_abfrage(), headers))
    ziel = W / "build" / "osm_strassen.json"
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(json.dumps(dict(stand=datetime.date.today().isoformat(), linien=linien), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    k = dict(strassen=len(linien), segmente=sum(len(v) for v in linien.values()))
    print(json.dumps(k)); return k


if __name__ == "__main__":
    main()
