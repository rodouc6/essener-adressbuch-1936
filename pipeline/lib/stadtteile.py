"""Heutige Stadtteilgrenzen Essens (OSM, admin_level 10) → genau ein Stadtteil je Adresse (Spec §5.4a).

Die Grenzen sind die HEUTIGEN (ODbL, © OpenStreetMap-Mitwirkende); Perspektiven, Karte und Doku sagen das.
Ringe entstehen aus den `outer`-Wegen der Relation (Verkettung über gleiche Endpunkte, Richtung egal);
`inner`-Ringe (Enklaven) werden nicht ausgeschnitten — in Essen gibt es keine (docs/stadtteile.md).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


def ringe_aus_relation(members: list[dict]) -> list[list[list[float]]]:
    """Äußere Ringe einer OSM-Relation aus den Weg-Geometrien (Overpass `out geom`), jeder Ring geschlossen."""
    wege = [[[p["lon"], p["lat"]] for p in m.get("geometry", [])] for m in members
            if m.get("type") == "way" and m.get("role", "outer") == "outer" and m.get("geometry")]
    ringe: list[list[list[float]]] = []
    offen = [w for w in wege if w]
    while offen:
        ring = list(offen.pop(0))
        while ring[0] != ring[-1]:
            ende = ring[-1]
            for i, w in enumerate(offen):
                if w[0] == ende:
                    ring.extend(w[1:]); offen.pop(i); break
                if w[-1] == ende:
                    ring.extend(list(reversed(w))[1:]); offen.pop(i); break
            else:
                raise ValueError(f"Ring nicht geschlossen bei {ende}")
        ringe.append(ring)
    return ringe


def punkt_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    """Strahlmethode (even-odd); Punkte exakt auf der Kante zählen nicht sicher — für Adressen unerheblich."""
    innen = False
    n = len(ring)
    for i in range(n - 1):
        x1, y1 = ring[i]; x2, y2 = ring[i + 1]
        if (y1 > lat) != (y2 > lat):
            x = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lon < x:
                innen = not innen
    return innen


class Stadtteile:
    def __init__(self, daten: dict, abgleich: dict[str, str]):
        self.stand, self.quelle = daten.get("stand", ""), daten.get("quelle", "")
        self._polys: dict[str, list[list[list[float]]]] = {}
        for osm_name, ringe in daten.get("stadtteile", {}).items():
            name = abgleich.get(osm_name, osm_name)
            if name:                                  # leer = gehörte 1936 nicht zu Essen
                self._polys.setdefault(name, []).extend(ringe)
        self._bbox = {n: (min(p[0] for r in rs for p in r), min(p[1] for r in rs for p in r),
                          max(p[0] for r in rs for p in r), max(p[1] for r in rs for p in r)) for n, rs in self._polys.items()}

    @property
    def namen(self) -> list[str]:
        return sorted(self._polys)

    def zuordnen(self, lat: float, lon: float) -> str | None:
        for name in self.namen:
            w, s, o, n = self._bbox[name]
            if not (w <= lon <= o and s <= lat <= n):
                continue
            if any(punkt_in_ring(lon, lat, r) for r in self._polys[name]):
                return name
        return None

    def geojson(self) -> dict:
        return {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"id": n, "quelle": self.quelle, "stand": self.stand},
             "geometry": {"type": "MultiPolygon", "coordinates": [[r] for r in self._polys[n]]}} for n in self.namen]}


def lade_abgleich(pfad: Path | str) -> dict[str, str]:
    with open(pfad, encoding="utf-8", newline="") as f:
        return {z["osm_name"].strip(): (z.get("name") or "").strip() for z in csv.DictReader(f) if z.get("osm_name")}


def lade_stadtteile(pfad_json: Path | str, pfad_csv: Path | str) -> Stadtteile:
    return Stadtteile(json.loads(Path(pfad_json).read_text(encoding="utf-8")), lade_abgleich(pfad_csv))
