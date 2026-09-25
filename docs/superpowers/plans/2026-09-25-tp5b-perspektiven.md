# TP5b Perspektiven: Stadtteilgrenzen, Ansicht-Modell, Scrollytelling-Seite — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die erzählende Seite `site/perspektiven.html` mit drei Kapiteln (Wohneigentum, Soziale Stellung, Gewerbe und Versorgung), gespeist aus dem Ansicht-Modell und den Ebenen-Daten von 5a — vorher der Datenschritt, der jede Adresse genau einem Stadtteil zuordnet (heutige Grenzen aus OSM), ohne den die Stadtteilebene unbrauchbar ist.

**Architecture:** (1) Pipeline: `werkzeuge/osm_stadtteile_laden.py` holt die 50 Stadtteilrelationen per Overpass, `pipeline/lib/stadtteile.py` setzt Ringe zusammen und macht Punkt-in-Polygon; `karte_export.gruppiere` vergibt den Stadtteil je Adresse, `schreibe_paket` schreibt `stadtteile.geojson` und die Kapitel-JSONs. (2) Browser: `site/js/ansicht.js` (reines Modell: Validierung, URL, Gruppen, Kennzahlen), `site/js/daten_ebenen.js` (lädt Ebenen/Layouts einmal, rechnet Werte je Einheit), vier Formen als reine SVG-String-Erzeuger in `site/js/formen/` (`balken`, `bubbles`, `rangliste`, `stadtteilkarte`), `site/js/perspektiven.js` bindet Scrollama an. (3) Karte versteht `?ansicht=` für die Ebenen Stadtteil/Straße/Hex. Alles ohne Bundler, ohne neue Abhängigkeiten außer Scrollama (lokal).

**Tech Stack:** Python 3.12 (json, csv, math, requests), pytest; ES-Module, node:test, MapLibre (nur Karte), Scrollama 3.2.0 (MIT, `site/vendor/scrollama.js`); SVG per Template-Strings.

**Spec:** `docs/superpowers/specs/2026-09-24-perspektiven-werkstatt-design.md` (§4, §5.4a, §6, §8, §9; §7 nur Schnittstellen)

## Global Constraints

- Deutsch mit korrekten Umlauten in Kommentaren, Texten, Commit-Nachrichten; Bezeichner deutsch wie im Bestand.
- Precision first: Jede Ansicht zeigt `N` (einbezogene Nennungen), `n_aus` (ausgeschlossen: unbestimmt/ungeprüft), die Zahl der Einheiten unter `min_n`, und die Abdeckung des Datenkerns aus `kennzahlen.json`. Einheiten unter `min_n` sind grau, nie eingefärbt. Nichts wird als gesichert dargestellt, was Vorschlag ist (Texte nennen `stellung_quelle`/`gewerbe_quelle`).
- Stadtteile sind **heutige Grenzen** (OSM, ODbL) — jede Karte/Legende/Doku sagt das („heutige Stadtteilgrenzen“). Adressen ohne Polygontreffer behalten den Straßen-Stadtteil mit `stadtteil_quelle=strasse`.
- Ansicht-Modell exakt wie Spec §4: Felder `daten | ebene | form | gruppen | kaufleute | unsicher | mass | bezug | min_n | filter | karte`; `daten ∈ stellung|gruppe|niveau|besitz|gewerbe`, `ebene ∈ adresse|strasse|stadtteil|hex`, `form ∈ karte|bubbles|balken|multiples|rangliste`, `mass ∈ anteil|dominant|mischung|dichte`, `kaufleute ∈ unbestimmt|angestellte|selbstaendige`. Zählfeld-Präfixe: `n_st_`, `n_gr_`, `n_gw_`, `n_gwa_`, `n_bs_`, `n_<niveau>`; Nenner `n_I` (Teil I), `n_III` (Teil III), `adressen`.
- `min_n`-Vorgaben: Straße 30, Hex 50, Stadtteil 200 (Spec §6.3). `dominant` nur bei Anteil ≥ 40 %. `mischung` = normierte Shannon-Entropie (log-Basis = Zahl der Gruppen), 0 bei einer Gruppe, 1 bei Gleichverteilung.
- Farben: Okabe-Ito für Gruppen (`#e69f00 #56b4e9 #009e73 #f0e442 #0072b2 #d55e00 #cc79a7 #000000`), sequenziell für Anteile (`#f7fbff → #08306b`, 5 Stufen), Grau `#c8c8c8` für unter `min_n`/ausgeschlossen.
- Layouts und SVG deterministisch (keine Zufallszahl); Formen sind reine Funktionen `zeige(ansicht, daten, optionen) → {svg, legende, zahlen}` (Strings/Objekte, kein DOM), damit node:test sie prüfen kann.
- Nur freigegebene Kapitel (`freigegeben: true`) werden ohne `?vorschau=1` gerendert; Kapiteltexte sind Platzhalter (Lorem ipsum erlaubt), bis der Projektleiter sie schreibt.
- Kein Playwright in diesem Plan (e2e bleibt deselektiert); Browser-Klicktest macht der Projektleiter.
- Keine neuen Python-Abhängigkeiten; im Browser nur Scrollama neu (lokal, Version in `site/vendor/README.md`).
- Tests: `python3 -m pytest -q -m "not e2e"`, `node --test site/tests/`, `node --test werkzeuge/tests/` — alle grün vor jedem Commit. `build/` und `site/daten/` sind nicht versioniert.
- Commits enden mit `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; Arbeit direkt auf `main`.
- Dev-Server: `python3 werkzeuge/serve.py 8765` (nie `python3 -m http.server`).

---

## Dateiübersicht

| Datei | Verantwortung |
|---|---|
| `werkzeuge/osm_stadtteile_laden.py` (neu) | Overpass → `build/osm_stadtteile.json` `{stand, quelle, stadtteile: {name: [[ [lon,lat],… ], …]}}` (Ringe) |
| `pipeline/lib/stadtteile.py` (neu) | `ringe_aus_relation(members)`, `punkt_in_ring`, `lade_stadtteile`, `Stadtteile.zuordnen(lat, lon) → name|None`, `stadtteile_geojson` |
| `kuratierung/stadtteile_osm.csv` (neu) | `osm_name, name, hinweis` — Namensabgleich (Margarethenhöhe → Margaretenhöhe, Kettwig/Burgaltendorf → leer) |
| `pipeline/lib/karte_export.py` | `gruppiere(..., stadtteile=)` setzt `stadtteil`/`stadtteil_quelle`; `schreibe_paket` schreibt `stadtteile.geojson`, `perspektiven/*.json`; Kennzahl `stadtteil_polygon` |
| `pipeline/06_karte_export.py` | lädt `build/osm_stadtteile.json` (Warnung, wenn fehlt) |
| `pipeline/lib/perspektiven.py` (neu) | `pruefe_kapitel(kapitel)` (Schema), `lade_kapitel(ordner)`, `kapitel_index` |
| `kuratierung/perspektiven/wohneigentum.json`, `stellung.json`, `gewerbe.json` (neu) | Kapitelinhalte (Schritte mit Ansichten) |
| `site/js/ansicht.js` (neu) | `STANDARD_ANSICHT`, `normalisiere`, `kodiere`/`dekodiere` (base64url), `gruppenSchluessel`, `kennzahlen(einheit, ansicht)`, `standardGruppen(daten, hauptgruppen)` |
| `site/js/daten_ebenen.js` (neu) | `ladeEbenen(lader)`, `werteJeEinheit(ansicht, ebenen)` |
| `site/js/formen/skalen.js` (neu) | `OKABE_ITO`, `SEQUENZ`, `farbeAnteil(wert)`, `formatProzent`, `esc` |
| `site/js/formen/balken.js`, `bubbles.js`, `rangliste.js`, `stadtteilkarte.js` (neu) | je `zeige(ansicht, daten, optionen) → {svg, legende, zahlen}` |
| `site/js/perspektiven.js` (neu), `site/perspektiven.html` (neu), `site/css/perspektiven.css` (neu) | Seite, Scrollama, Detailkasten, Links |
| `site/vendor/scrollama.js` (neu), `site/vendor/README.md` | Scrollama 3.2.0 MIT |
| `site/js/zustand.js`, `site/js/karte.js`, `site/js/app.js`, `site/js/daten.js` | `ansicht`-Parameter, Stadtteil-/Straßen-/Hex-Färbung, Legende |
| `site/index.html`, `site/js/start.js`, `site/ueber.html` | Kachel „Perspektiven“, Absatz |
| `docs/stadtteile.md` (neu), `docs/perspektiven.md` (neu), README | Doku |
| Tests | `tests/test_stadtteile.py`, `tests/test_perspektiven.py`, Erweiterungen `tests/test_karte_export.py`, `tests/test_ebenen.py`; `site/tests/ansicht.test.js`, `daten_ebenen.test.js`, `formen.test.js`, `perspektiven.test.js`, `zustand.test.js` |

---

### Task 1: Stadtteilgrenzen aus OSM — Ringe, Punkt-in-Polygon, Abruf

**Files:**
- Create: `pipeline/lib/stadtteile.py`, `werkzeuge/osm_stadtteile_laden.py`, `kuratierung/stadtteile_osm.csv`, `docs/stadtteile.md`
- Test: `tests/test_stadtteile.py`

**Interfaces:**
- Consumes: `pipeline.lib.io.projektwurzel`, `requests` (vorhanden), Muster aus `werkzeuge/osm_strassen_laden.py` (`_abrufen`, User-Agent).
- Produces: `ringe_aus_relation(members: list[dict]) -> list[list[list[float]]]` (äußere Ringe als `[[lon, lat], …]`, geschlossen: erster = letzter Punkt); `punkt_in_ring(lon, lat, ring) -> bool`; `class Stadtteile` mit `Stadtteile(daten: dict, abgleich: dict[str, str])`, `.zuordnen(lat, lon) -> str | None`, `.namen -> list[str]`, `.geojson() -> dict`; `lade_stadtteile(pfad_json, pfad_csv) -> Stadtteile`; Datei `build/osm_stadtteile.json` = `{"stand": "YYYY-MM-DD", "quelle": "OpenStreetMap, ODbL", "stadtteile": {osm_name: [ring, …]}}`.

- [ ] **Step 1: Failing tests schreiben**

```python
# tests/test_stadtteile.py
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
from pipeline.lib.stadtteile import Stadtteile, lade_stadtteile, punkt_in_ring, ringe_aus_relation

# Drei Wege bilden ein Quadrat (0,0)-(2,0)-(2,2)-(0,2); der zweite Weg ist verkehrt herum gespeichert.
W = lambda pts: {"type": "way", "role": "outer", "geometry": [{"lon": x, "lat": y} for x, y in pts]}
MEMBERS = [W([(0, 0), (2, 0), (2, 2)]), W([(0, 2), (2, 2)]), W([(0, 2), (0, 0)]), {"type": "node", "role": "admin_centre"}]


def test_ringe_aus_relation_verkettet_wege_unabhaengig_von_richtung():
    ringe = ringe_aus_relation(MEMBERS)
    assert len(ringe) == 1
    r = ringe[0]
    assert r[0] == r[-1] and len(r) == 5
    assert {tuple(p) for p in r} == {(0, 0), (2, 0), (2, 2), (0, 2)}


def test_ringe_aus_relation_mehrere_ringe_und_innen_ignoriert():
    m = MEMBERS + [W([(5, 5), (6, 5), (6, 6), (5, 6), (5, 5)]), dict(W([(0.5, 0.5), (1, 0.5), (1, 1), (0.5, 0.5)]), role="inner")]
    ringe = ringe_aus_relation(m)
    assert len(ringe) == 2                       # inner-Ringe (Enklaven) werden bewusst nicht ausgeschnitten (docs/stadtteile.md)


def test_ringe_aus_relation_offene_kette_ist_fehler():
    with pytest.raises(ValueError, match="nicht geschlossen"):
        ringe_aus_relation([W([(0, 0), (1, 0)]), W([(1, 0), (1, 1)])])


def test_punkt_in_ring():
    ring = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]
    assert punkt_in_ring(1, 1, ring) and not punkt_in_ring(3, 1, ring) and not punkt_in_ring(-1, 1, ring)
    assert punkt_in_ring(1, 1.999, ring) and not punkt_in_ring(1, 2.001, ring)


def test_stadtteile_zuordnen_mit_namensabgleich():
    daten = {"stand": "2026-09-26", "quelle": "OSM", "stadtteile": {
        "Margarethenhöhe": [[[7.0, 51.4], [7.1, 51.4], [7.1, 51.5], [7.0, 51.5], [7.0, 51.4]]],
        "Kettwig": [[[6.9, 51.3], [7.0, 51.3], [7.0, 51.4], [6.9, 51.4], [6.9, 51.3]]]}}
    st = Stadtteile(daten, {"Margarethenhöhe": "Margaretenhöhe", "Kettwig": ""})
    assert st.zuordnen(51.45, 7.05) == "Margaretenhöhe"      # umbenannt
    assert st.zuordnen(51.35, 6.95) is None                   # Kettwig 1936 nicht Essen → leer
    assert st.zuordnen(52.0, 7.0) is None                     # außerhalb
    assert st.namen == ["Margaretenhöhe"]
    g = st.geojson()
    assert g["type"] == "FeatureCollection" and [f["properties"]["id"] for f in g["features"]] == ["Margaretenhöhe"]
    assert g["features"][0]["geometry"]["type"] == "MultiPolygon" and g["features"][0]["properties"]["quelle"] == "OSM"


def test_lade_stadtteile(tmp_path):
    (tmp_path / "osm.json").write_text(json.dumps({"stand": "d", "quelle": "OSM", "stadtteile": {"Stadtkern": [[[7, 51], [7.1, 51], [7.1, 51.1], [7, 51.1], [7, 51]]]}}), encoding="utf-8")
    (tmp_path / "abgleich.csv").write_text("osm_name,name,hinweis\nStadtkern,Stadtkern,\n", encoding="utf-8")
    st = lade_stadtteile(tmp_path / "osm.json", tmp_path / "abgleich.csv")
    assert st.zuordnen(51.05, 7.05) == "Stadtkern"
```

- [ ] **Step 2: Tests laufen lassen — erwartet ImportError**

Run: `python3 -m pytest tests/test_stadtteile.py -q`
Expected: FAIL (ModuleNotFoundError: pipeline.lib.stadtteile)

- [ ] **Step 3: `pipeline/lib/stadtteile.py` schreiben**

```python
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
```

- [ ] **Step 4: Tests grün**

Run: `python3 -m pytest tests/test_stadtteile.py -q`
Expected: 6 passed

- [ ] **Step 5: Abrufskript `werkzeuge/osm_stadtteile_laden.py`**

```python
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
    out = {}
    for el in osm_json.get("elements", []):
        if el.get("type") != "relation":
            continue
        name = (el.get("tags", {}).get("name") or "").strip()
        if name:
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
```

Test dafür (an `tests/test_stadtteile.py` anhängen):

```python
def test_stadtteile_aus_overpass_json():
    from werkzeuge.osm_stadtteile_laden import stadtteile_aus
    osm = {"elements": [{"type": "relation", "tags": {"name": "Stadtkern"}, "members": MEMBERS}, {"type": "way", "id": 1}]}
    st = stadtteile_aus(osm)
    assert list(st) == ["Stadtkern"] and len(st["Stadtkern"]) == 1 and st["Stadtkern"][0][0] == st["Stadtkern"][0][-1]
```

- [ ] **Step 6: Namensabgleich `kuratierung/stadtteile_osm.csv`** — 50 Zeilen, Spalten `osm_name,name,hinweis`. Alle Namen identisch übernehmen außer: `Margarethenhöhe,Margaretenhöhe,Schreibung wie essener-strassen/Dickhoff`; `Kettwig,,erst 1975 nach Essen eingemeindet — 1936 keine Essener Adressen`; `Burgaltendorf,,erst 1970 eingemeindet`. Die 50 OSM-Namen: Altendorf, Altenessen-Nord, Altenessen-Süd, Bedingrade, Bergeborbeck, Bergerhausen, Bochold, Borbeck-Mitte, Bredeney, Burgaltendorf, Byfang, Dellwig, Fischlaken, Freisenbruch, Frillendorf, Frintrop, Frohnhausen, Fulerum, Gerschede, Haarzopf, Heidhausen, Heisingen, Holsterhausen, Horst, Huttrop, Karnap, Katernberg, Kettwig, Kray, Kupferdreh, Leithe, Margarethenhöhe, Nordviertel, Ostviertel, Rellinghausen, Rüttenscheid, Schonnebeck, Schuir, Schönebeck, Stadtkern, Stadtwald, Steele, Stoppenberg, Südostviertel, Südviertel, Vogelheim, Werden, Westviertel, Überruhr-Hinsel, Überruhr-Holthausen.

- [ ] **Step 7: Abruf ausführen** — `python3 werkzeuge/osm_stadtteile_laden.py`. Erwartet `{"stadtteile": 50, …}`. Bei HTTP 429/504: 90 s warten, wiederholen (max. 3-mal); bei anhaltendem Fehler Status `BLOCKED` mit Fehlertext melden (der Controller führt den Abruf dann selbst aus, wie bei den Straßenlinien in 5a). Prüfen: `python3 -c "import json;d=json.load(open('build/osm_stadtteile.json'));print(len(d['stadtteile']), sorted(d['stadtteile'])[:5])"`.

- [ ] **Step 8: `docs/stadtteile.md`** — Abschnitte: Quelle und Lizenz (OSM, Regionalschlüssel, Abrufdatum aus `build/osm_stadtteile.json`), Verfahren (Ringe, Strahlmethode, Bbox-Vorfilter), Namensabgleich (Tabelle der drei Abweichungen), Grenze („heutige Grenzen; Stadtteile 1936 waren anders geschnitten — Sternviertel, Eingemeindungen 1929“), Kennzeichnung, Wiederholung des Abrufs.

- [ ] **Step 9: Alle Tests, Commit**

```bash
python3 -m pytest -q -m "not e2e"
git add pipeline/lib/stadtteile.py werkzeuge/osm_stadtteile_laden.py kuratierung/stadtteile_osm.csv docs/stadtteile.md tests/test_stadtteile.py
git commit -m "feat(stadtteile): heutige Stadtteilgrenzen aus OSM, Ringe und Punkt-in-Polygon

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Stadtteil je Adresse im Export, `stadtteile.geojson`, saubere Stadtteilebene

**Files:**
- Modify: `pipeline/lib/karte_export.py` (`gruppiere`, `schreibe_paket`, `baue_kennzahlen`), `pipeline/06_karte_export.py`, `pipeline/lib/ebenen.py` (Docstring), `README.md` (Abschnitt „Datenkerne“ + Tabelle `site/daten`)
- Test: `tests/test_karte_export.py`, `tests/test_ebenen.py`

**Interfaces:**
- Consumes: `Stadtteile.zuordnen(lat, lon)`, `Stadtteile.geojson()` aus Task 1; `gruppiere(eintraege, regeln, eigentuemer, berufe, ohdab, gewerbe)` (bestehend, Signatur in `karte_export.py:85`).
- Produces: `gruppiere(..., stadtteile: Stadtteile | None = None)`: je Adresse `stadtteil` = Polygon-Treffer, sonst bisheriger Wert; neues Feld `stadtteil_quelle` ∈ `polygon | strasse | ""`; `schreibe_paket(..., stadtteile: Stadtteile | None = None)` schreibt `site/daten/stadtteile.geojson`; `punkt_feature` trägt `stadtteil` wie bisher (jetzt eindeutig); Kennzahl `stadtteil_polygon` (Prozent der verorteten Adressen mit Polygontreffer); `ebenen/stadtteile.json` enthält nur noch Einzelnamen + ggf. `ohne_stadtteil`.

- [ ] **Step 1: Failing test in `tests/test_karte_export.py` anhängen**

```python
def test_stadtteil_je_adresse_aus_polygon(tmp_path):
    from pipeline.lib.stadtteile import Stadtteile
    from pipeline.lib.karte_export import baue_kennzahlen, gruppiere, schreibe_paket
    from pipeline.lib.ebenen import aggregiere
    st = Stadtteile({"stand": "d", "quelle": "OSM", "stadtteile": {"Kray": [[[7.0, 51.4], [7.1, 51.4], [7.1, 51.5], [7.0, 51.5], [7.0, 51.4]]]}}, {})
    basis = dict(stufe="haus", strasse_norm="x", strasse_roh="X", Vorort="", lastname="N", firstname="", page="I-1", strasse_heute="X-Straße", schl_nr="00001", teil="I")
    e1 = dict(basis, id="1", lat="51.45", lon="7.05", hausnr="1", stadtteil="Kray; Steele")      # im Polygon → Kray
    e2 = dict(basis, id="2", lat="51.60", lon="7.05", hausnr="2", stadtteil="Kray; Steele")      # außerhalb → Straßen-Stadtteil bleibt
    a = gruppiere([e1, e2], [], None, stadtteile=st)
    by = {x["hausnr"]: x for x in a.values()}
    assert (by["1"]["stadtteil"], by["1"]["stadtteil_quelle"]) == ("Kray", "polygon")
    assert (by["2"]["stadtteil"], by["2"]["stadtteil_quelle"]) == ("Kray; Steele", "strasse")
    assert baue_kennzahlen([e1, e2], a, "2026-09-26")["stadtteil_polygon"] == 50.0
    ids = [u["id"] for u in aggregiere(a, "stadtteil")]
    assert ids == ["Kray", "Kray; Steele"]
    aus = tmp_path / "daten"
    schreibe_paket(aus, [e1, e2], [], [], "2026-09-26", kacheln=False, stadtteile=st, hauptgruppen=[])
    g = json.loads((aus / "stadtteile.geojson").read_text(encoding="utf-8"))
    assert g["features"][0]["properties"]["id"] == "Kray"
    ohne = gruppiere([e1], [], None)
    assert list(ohne.values())[0]["stadtteil_quelle"] == "strasse"
```

- [ ] **Step 2: Test läuft rot** — `python3 -m pytest tests/test_karte_export.py -q -k stadtteil_je_adresse` → TypeError (unerwartetes Argument `stadtteile`).

- [ ] **Step 3: Implementierung**

In `gruppiere`: Parameter `stadtteile: "Stadtteile | None" = None` ergänzen (Import `from pipeline.lib.stadtteile import Stadtteile`). Beim Anlegen einer Adresse (`a = adressen[aid] = dict(...)`):

```python
            strassen_st = e.get("stadtteil", "") or e.get("Vorort", "")
            poly = stadtteile.zuordnen(float(e["lat"]), float(e["lon"])) if stadtteile else None
            a = adressen[aid] = dict(id=aid, lat=float(e["lat"]), lon=float(e["lon"]), stufe=_stufe(e),
                                    stadtteil=poly or strassen_st, stadtteil_quelle="polygon" if poly else ("strasse" if strassen_st else ""),
                                    ...  # übrige Felder unverändert
```

In `baue_kennzahlen`: `stadtteil_polygon=_prozent(sum(1 for a in adressen.values() if a.get("stadtteil_quelle") == "polygon"), len(adressen))`.

In `schreibe_paket`: Parameter `stadtteile: "Stadtteile | None" = None`; `gruppiere(..., stadtteile=stadtteile)`; nach `hex.geojson`: `if stadtteile: _json(ausgabe / "stadtteile.geojson", stadtteile.geojson())`.

In `pipeline/06_karte_export.py` nach dem OSM-Straßen-Block:

```python
st_pfad = W / "build" / "osm_stadtteile.json"
if st_pfad.exists():
    stadtteile = lade_stadtteile(st_pfad, W / "kuratierung" / "stadtteile_osm.csv")
else:
    stadtteile = None
    print("build/osm_stadtteile.json fehlt — Stadtteil bleibt der Straßen-Stadtteil (werkzeuge/osm_stadtteile_laden.py)", file=sys.stderr)
```
und `schreibe_paket(..., stadtteile=stadtteile)`; Import `from pipeline.lib.stadtteile import lade_stadtteile`.

`punkt_feature` (Kachel-Eigenschaften): `stadtteil` bleibt; der bisherige Filter `["==", ["get", "stadtteil"], z.stadtteil]` in `site/js/karte.js` trifft damit genau einen Stadtteil (Verbesserung ohne Codeänderung — in `docs/stadtteile.md` vermerken).

- [ ] **Step 4: Tests grün, Export laufen lassen**

Run: `python3 -m pytest -q -m "not e2e"` → alle grün. Dann `python3 pipeline/06_karte_export.py` (≈ 2 min) und prüfen:
```bash
python3 -c "import json;k=json.load(open('site/daten/kennzahlen.json'));print(k['stadtteil_polygon']);d=json.load(open('site/daten/ebenen/stadtteile.json'));print(len(d),[u['id'] for u in d if ';' in u['id']][:5])"
```
Erwartet: `stadtteil_polygon` ≥ 99, Stadtteile ≈ 48–50, keine `;`-Kombinationen. Weicht es ab (viele Adressen außerhalb aller Polygone), Zahl und Beispiele im Report nennen — nicht still hinnehmen.

- [ ] **Step 5: README** — in „Datenkerne für Perspektiven und Werkstatt“ Absatz „Stadtteil je Adresse“ (Quelle, `stadtteil_quelle`, Kennzahl, heutige Grenzen); Tabelle `site/daten` Zeile `stadtteile.geojson`; Ablauf-Block `python3 werkzeuge/osm_stadtteile_laden.py`.

- [ ] **Step 6: Commit**

```bash
git add pipeline/lib/karte_export.py pipeline/06_karte_export.py pipeline/lib/ebenen.py README.md tests/test_karte_export.py
git commit -m "feat(export): genau ein Stadtteil je Adresse (heutige Grenzen), stadtteile.geojson, Kennzahl stadtteil_polygon

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Kapitel-Schema, Kapitel 1 „Wohneigentum“, Export der Kapitel

**Files:**
- Create: `pipeline/lib/perspektiven.py`, `kuratierung/perspektiven/wohneigentum.json`, `docs/perspektiven.md`
- Modify: `pipeline/lib/karte_export.py` (`schreibe_paket`), `pipeline/06_karte_export.py`
- Test: `tests/test_perspektiven.py`

**Interfaces:**
- Produces: `pruefe_kapitel(k: dict) -> list[str]` (Fehlerliste, leer = gültig), `lade_kapitel(ordner: Path) -> list[dict]` (sortiert nach `reihenfolge`), `kapitel_index(kapitel) -> list[dict]` (`id, titel, untertitel, freigegeben, reihenfolge`); `schreibe_paket(..., perspektiven: Path | None)` schreibt `site/daten/perspektiven/index.json` und `perspektiven/<id>.json`. Schema (Spec §6.2): `id, reihenfolge, titel, untertitel, freigegeben, einleitung, schritte[] {id, text, ansicht, hervorheben[], beschreibung}, grenzen, quellen[]`. Jede `ansicht` muss die Felder aus Global Constraints tragen; `mass=dichte` nur mit `daten=gewerbe`; `form=stadtteilkarte` ist in den Kapiteln der Name für `form=karte` mit `ebene=stadtteil` (Perspektiven-SVG) — das Schema erlaubt in `form` zusätzlich `stadtteilkarte`.

- [ ] **Step 1: Failing tests**

```python
# tests/test_perspektiven.py
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.perspektiven import kapitel_index, lade_kapitel, pruefe_kapitel

GUT = {"id": "wohneigentum", "reihenfolge": 1, "titel": "Wohneigentum 1936", "untertitel": "privat, industriell, genossenschaftlich, städtisch, kirchlich",
       "freigegeben": False, "einleitung": "Lorem ipsum.", "quellen": ["Teil II"], "grenzen": "Geprüft sind {besitz_geprueft} Adressen.",
       "schritte": [{"id": "anteile", "text": "Lorem.", "beschreibung": "Balken der acht Klassen.", "hervorheben": [],
                     "ansicht": {"daten": "besitz", "ebene": "stadtteil", "form": "balken", "gruppen": [{"name": "Privat", "aus": ["privatperson"], "farbe": "#e69f00"}],
                                 "kaufleute": "unbestimmt", "unsicher": False, "mass": "anteil", "bezug": "Privat", "min_n": 200, "filter": {}, "karte": None}}]}


def test_gueltiges_kapitel():
    assert pruefe_kapitel(GUT) == []


def test_fehler_werden_benannt():
    k = json.loads(json.dumps(GUT))
    k["schritte"][0]["ansicht"]["daten"] = "geld"; k["schritte"][0]["ansicht"]["bezug"] = "Fremd"; del k["titel"]
    k["schritte"].append({"id": "anteile", "text": "", "beschreibung": "", "hervorheben": [], "ansicht": dict(GUT["schritte"][0]["ansicht"], mass="dichte")})
    f = pruefe_kapitel(k)
    assert any("titel" in x for x in f) and any("daten" in x for x in f) and any("bezug" in x for x in f)
    assert any("doppelt" in x for x in f) and any("dichte" in x for x in f)


def test_lade_und_index(tmp_path):
    (tmp_path / "b.json").write_text(json.dumps(dict(GUT, id="b", reihenfolge=2)), encoding="utf-8")
    (tmp_path / "a.json").write_text(json.dumps(GUT), encoding="utf-8")
    ks = lade_kapitel(tmp_path)
    assert [k["id"] for k in ks] == ["wohneigentum", "b"]
    assert kapitel_index(ks)[0] == {"id": "wohneigentum", "titel": "Wohneigentum 1936", "untertitel": GUT["untertitel"], "freigegeben": False, "reihenfolge": 1}


def test_echte_kapitel_sind_gueltig():
    W = pathlib.Path(__file__).resolve().parents[1]
    for k in lade_kapitel(W / "kuratierung" / "perspektiven"):
        assert pruefe_kapitel(k) == [], k["id"]
```

- [ ] **Step 2: rot** — `python3 -m pytest tests/test_perspektiven.py -q` → ModuleNotFoundError.

- [ ] **Step 3: `pipeline/lib/perspektiven.py`**

```python
"""Kapitel der Perspektiven-Seite (Spec §6.2): Schema prüfen, laden, Index bauen. Inhalte: kuratierung/perspektiven/*.json."""
from __future__ import annotations

import json
from pathlib import Path

DATEN = ("stellung", "gruppe", "niveau", "besitz", "gewerbe")
EBENEN = ("adresse", "strasse", "stadtteil", "hex")
FORMEN = ("karte", "stadtteilkarte", "bubbles", "balken", "multiples", "rangliste")
MASSE = ("anteil", "dominant", "mischung", "dichte")
KAUFLEUTE = ("unbestimmt", "angestellte", "selbstaendige")
PFLICHT = ("id", "reihenfolge", "titel", "untertitel", "freigegeben", "einleitung", "schritte", "grenzen", "quellen")
PFLICHT_SCHRITT = ("id", "text", "ansicht", "hervorheben", "beschreibung")
PFLICHT_ANSICHT = ("daten", "ebene", "form", "gruppen", "kaufleute", "unsicher", "mass", "bezug", "min_n", "filter", "karte")


def pruefe_ansicht(a: dict, wo: str) -> list[str]:
    f = [f"{wo}: Ansicht ohne Feld {p!r}" for p in PFLICHT_ANSICHT if p not in a]
    if f:
        return f
    if a["daten"] not in DATEN: f.append(f"{wo}: daten {a['daten']!r} unbekannt")
    if a["ebene"] not in EBENEN: f.append(f"{wo}: ebene {a['ebene']!r} unbekannt")
    if a["form"] not in FORMEN: f.append(f"{wo}: form {a['form']!r} unbekannt")
    if a["mass"] not in MASSE: f.append(f"{wo}: mass {a['mass']!r} unbekannt")
    if a["kaufleute"] not in KAUFLEUTE: f.append(f"{wo}: kaufleute {a['kaufleute']!r} unbekannt")
    if a["mass"] == "dichte" and a["daten"] != "gewerbe": f.append(f"{wo}: mass dichte nur mit daten gewerbe")
    namen = [g.get("name") for g in a["gruppen"]]
    if len(set(namen)) != len(namen): f.append(f"{wo}: Gruppenname doppelt")
    for g in a["gruppen"]:
        if not g.get("name") or not isinstance(g.get("aus"), list) or not g.get("farbe"): f.append(f"{wo}: Gruppe unvollständig {g!r}")
    if a["mass"] in ("anteil", "dichte") and a["bezug"] not in namen: f.append(f"{wo}: bezug {a['bezug']!r} ist keine Gruppe")
    if not isinstance(a["min_n"], int) or a["min_n"] < 0: f.append(f"{wo}: min_n muss ganze Zahl ≥ 0 sein")
    return f


def pruefe_kapitel(k: dict) -> list[str]:
    f = [f"Kapitel ohne Feld {p!r}" for p in PFLICHT if p not in k]
    if f:
        return f
    ids = [s.get("id") for s in k["schritte"]]
    if len(set(ids)) != len(ids): f.append("Schritt-id doppelt")
    for s in k["schritte"]:
        wo = f"Schritt {s.get('id')!r}"
        f += [f"{wo}: ohne Feld {p!r}" for p in PFLICHT_SCHRITT if p not in s]
        if "ansicht" in s: f += pruefe_ansicht(s["ansicht"], wo)
    return f


def lade_kapitel(ordner: Path | str) -> list[dict]:
    ks = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(ordner).glob("*.json"))]
    return sorted(ks, key=lambda k: (k.get("reihenfolge", 999), k.get("id", "")))


def kapitel_index(kapitel: list[dict]) -> list[dict]:
    return [{"id": k["id"], "titel": k["titel"], "untertitel": k["untertitel"], "freigegeben": bool(k["freigegeben"]), "reihenfolge": k["reihenfolge"]} for k in kapitel]
```

- [ ] **Step 4: Kapitel 1 `kuratierung/perspektiven/wohneigentum.json`** — vollständig, Text als Platzhalter („Platzhaltertext: …“ mit ein bis zwei Sätzen, was hier stehen soll), `freigegeben: false`. Gruppenfarben aus `kuratierung/themen/besitz.json` übernehmen. Schritte (Spec §6.2 Kapitel 1):

```json
{
  "id": "wohneigentum", "reihenfolge": 1,
  "titel": "Wohneigentum 1936", "untertitel": "privat, industriell, genossenschaftlich, städtisch, kirchlich",
  "freigegeben": false,
  "einleitung": "Platzhaltertext: Teil II des Adressbuchs nennt zu jedem Haus den Eigentümer. Geprüft sind bisher die Körperschaften ab fünf Häusern und die größten Privatpersonen — das ist ein Ausschnitt, kein Gesamtbild.",
  "quellen": ["Adreßbuch Essen 1936, Teil II (Häuserbuch)", "Eigentümer-Kuratierung kuratierung/eigentuemer.csv"],
  "grenzen": "Von {adressen} verorteten Adressen tragen {besitz_geprueft} eine geprüfte Besitzklasse ({besitz_geprueft_prozent} %). Alle Anteile beziehen sich auf diese geprüften Adressen; die Karte zeigt heutige Stadtteilgrenzen. Erhebungsstand ist der Lauf des Jahres 1936; die Namen H–J fehlen in der Vorlage (Teil I), Teil II ist davon nicht betroffen.",
  "schritte": [
    {"id": "anteile", "text": "Platzhaltertext: Wie verteilen sich die geprüften Häuser auf die Besitzklassen?", "beschreibung": "Ein Balken mit acht farbigen Segmenten und einem grauen Segment „ungeprüft“.", "hervorheben": [],
     "ansicht": {"daten": "besitz", "ebene": "stadtteil", "form": "balken", "gruppen": [
        {"name": "Privatpersonen", "aus": ["privatperson"], "farbe": "#d97706"}, {"name": "Stadt und Staat", "aus": ["stadt_staat"], "farbe": "#1d4ed8"},
        {"name": "Bergbau", "aus": ["bergbau"], "farbe": "#111827"}, {"name": "Industrie", "aus": ["industrie"], "farbe": "#b91c1c"},
        {"name": "Genossenschaft und Siedlung", "aus": ["genossenschaft_siedlung"], "farbe": "#15803d"}, {"name": "Kirche und Stiftung", "aus": ["kirche_stiftung"], "farbe": "#7c3aed"},
        {"name": "Bank und Versicherung", "aus": ["bank_versicherung"], "farbe": "#0e7490"}, {"name": "Sonstige", "aus": ["sonstige", "gemischt"], "farbe": "#6b7280"}],
       "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Privatpersonen", "min_n": 0, "filter": {}, "karte": null}},
    {"id": "eigentuemer", "text": "Platzhaltertext: Die 101 geprüften Körperschaften und Großeigentümer als Kreise, Fläche nach Häuserzahl.", "beschreibung": "Bubbles der Eigentümer, gefärbt nach Klasse, gepackt je Klasse.", "hervorheben": ["Fried. Krupp AG", "Stadt Essen"],
     "ansicht": {"daten": "besitz", "ebene": "stadtteil", "form": "bubbles", "gruppen": "wie:anteile", "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Privatpersonen", "min_n": 0, "filter": {}, "karte": null}},
    {"id": "rangliste", "text": "Platzhaltertext: Die fünfzehn größten Eigentümer.", "beschreibung": "Rangliste mit Häuserzahl je Eigentümer.", "hervorheben": [],
     "ansicht": {"daten": "besitz", "ebene": "stadtteil", "form": "rangliste", "gruppen": "wie:anteile", "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Privatpersonen", "min_n": 0, "filter": {"top": 15}, "karte": null}},
    {"id": "karte-werkswohnungen", "text": "Platzhaltertext: Wo besaßen Zechen und Werke die Häuser?", "beschreibung": "Stadtteilkarte: Anteil Bergbau + Industrie an den geprüften Adressen; Stadtteile unter 50 geprüften Adressen grau.", "hervorheben": ["Karnap", "Altenessen-Nord"],
     "ansicht": {"daten": "besitz", "ebene": "stadtteil", "form": "stadtteilkarte", "gruppen": [{"name": "Zechen und Werke", "aus": ["bergbau", "industrie"], "farbe": "#111827"}, {"name": "übrige geprüfte", "aus": ["privatperson", "stadt_staat", "genossenschaft_siedlung", "kirche_stiftung", "bank_versicherung", "sonstige", "gemischt"], "farbe": "#c8c8c8"}],
       "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Zechen und Werke", "min_n": 50, "filter": {}, "karte": null}},
    {"id": "karte-genossenschaften", "text": "Platzhaltertext: Genossenschaften und Siedlungsgesellschaften.", "beschreibung": "Stadtteilkarte: Anteil Genossenschaft/Siedlung an den geprüften Adressen.", "hervorheben": ["Margaretenhöhe"],
     "ansicht": {"daten": "besitz", "ebene": "stadtteil", "form": "stadtteilkarte", "gruppen": [{"name": "Genossenschaft und Siedlung", "aus": ["genossenschaft_siedlung"], "farbe": "#15803d"}, {"name": "übrige geprüfte", "aus": ["privatperson", "stadt_staat", "bergbau", "industrie", "kirche_stiftung", "bank_versicherung", "sonstige", "gemischt"], "farbe": "#c8c8c8"}],
       "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Genossenschaft und Siedlung", "min_n": 50, "filter": {}, "karte": null}}
  ]
}
```

`"gruppen": "wie:anteile"` ist eine Kurzform: `lade_kapitel` löst sie beim Laden auf (Gruppen des Schritts mit dieser id kopieren); `pruefe_kapitel` prüft danach. Implementieren in `lade_kapitel`:

```python
def _loese_gruppen_auf(k: dict) -> dict:
    nach_id = {s["id"]: s for s in k.get("schritte", []) if "id" in s}
    for s in k.get("schritte", []):
        g = s.get("ansicht", {}).get("gruppen")
        if isinstance(g, str) and g.startswith("wie:"):
            s["ansicht"]["gruppen"] = json.loads(json.dumps(nach_id[g[4:]]["ansicht"]["gruppen"]))
    return k
```
und in `lade_kapitel`: `ks = [_loese_gruppen_auf(json.loads(...)) ...]`. Test dazu anhängen: Kapitel mit `"gruppen": "wie:anteile"` lädt mit kopierter Liste; unbekannte id → `KeyError`.

- [ ] **Step 5: Export** — in `schreibe_paket` Parameter `perspektiven: Path | None = None`; wenn gesetzt: `ks = lade_kapitel(perspektiven)`; für jedes `k`: `fehler = pruefe_kapitel(k)`; bei Fehlern `raise ValueError("kuratierung/perspektiven: " + "; ".join(fehler))`; `_json(ausgabe / "perspektiven" / "index.json", kapitel_index(ks))` und je Kapitel `_json(ausgabe / "perspektiven" / f"{k['id']}.json", k)`. In `06_karte_export.py`: `perspektiven=W / "kuratierung" / "perspektiven"` und `"perspektiven"` in die Liste der vorab gelöschten Unterordner. Test in `tests/test_karte_export.py`: `schreibe_paket(..., perspektiven=ordner_mit_GUT)` schreibt `perspektiven/index.json` mit einem Eintrag und `perspektiven/wohneigentum.json`; ungültiges Kapitel → `ValueError`.

- [ ] **Step 6: `docs/perspektiven.md`** — Schema mit allen Feldern und Werten, die Kurzform `wie:<schritt>`, Platzhalter in `grenzen` (`{adressen}`, `{besitz_geprueft}`, `{besitz_geprueft_prozent}`, `{berufe_geprueft}`, `{stellung_geprueft}`, `{stellung_vorschlag}`, `{stellung_unbestimmt}`, `{gewerbe_geprueft}`, `{gewerbe_entschieden}`, `{gewerbe_vorschlag}`, `{stadtteil_polygon}`, `{stand}` — alle aus `kennzahlen.json`, `*_prozent` = gerundet auf eine Stelle aus `besitz_geprueft / adressen`), Freigabe (`freigegeben`, `?vorschau=1`), Arbeitsablauf für den Projektleiter (JSON bearbeiten → Export → Seite).

- [ ] **Step 7: Tests, Commit**

```bash
python3 -m pytest -q -m "not e2e"
git add pipeline/lib/perspektiven.py kuratierung/perspektiven/wohneigentum.json docs/perspektiven.md pipeline/lib/karte_export.py pipeline/06_karte_export.py tests/test_perspektiven.py tests/test_karte_export.py
git commit -m "feat(perspektiven): Kapitel-Schema, Kapitel 1 Wohneigentum (Platzhaltertext), Export der Kapitel

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: `site/js/ansicht.js` — Modell, URL, Gruppen, Kennzahlen

**Files:**
- Create: `site/js/ansicht.js`
- Test: `site/tests/ansicht.test.js`

**Interfaces:**
- Produces (alle rein, ohne DOM):
  - `STANDARD_ANSICHT` (Object.freeze): `{daten:"stellung", ebene:"stadtteil", form:"karte", gruppen:[], kaufleute:"unbestimmt", unsicher:false, mass:"anteil", bezug:"", min_n:200, filter:{}, karte:null}`; `MIN_N = {strasse:30, hex:50, stadtteil:200, adresse:0}`.
  - `normalisiere(obj) → ansicht` (unbekannte Werte → Standard; `min_n` fehlt → `MIN_N[ebene]`; Gruppen ohne Farbe → Okabe-Ito in Reihenfolge; Gruppennamen dedupliziert durch Anhängen von „ 2“).
  - `kodiere(ansicht) → string` (base64url von JSON ohne Standardwerte), `dekodiere(string) → ansicht` (Fehler → `STANDARD_ANSICHT`).
  - `praefix(daten) → "n_st_"|"n_gr_"|"n_"|"n_bs_"|"n_gw_"`; `nenner(daten) → "n_I"|"adressen"|"n_III"`.
  - `schluesselDerEinheit(einheit, daten) → {schluessel: zahl}` (alle Zählfelder des Datenkerns ohne Präfix; bei `daten=stellung` und `kaufleute≠unbestimmt` wird `kaufleute` auf die Zielklasse addiert; bei `daten=niveau` und `unsicher=false` fällt `unsicher` in `n_aus`).
  - `kennzahlen(einheit, ansicht) → {N, n_aus, unter_min, anteile:{name: zahl}, wert, dominant, mischung, dichte}`: `N` = Summe der Zähler aller Gruppen; `n_aus` = Summe der Schlüssel, die in keiner Gruppe liegen, plus `unbestimmt`/`ungeprueft`/(`unsicher` wenn ausgeschlossen); `unter_min = N < min_n`; `anteile[name] = n_gruppe / N` (N=0 → 0); `wert` je `mass`: `anteil` → `anteile[bezug]`, `dominant` → Name der größten Gruppe wenn Anteil ≥ 0,4 sonst `"gemischt"`, `mischung` → normierte Entropie, `dichte` → `1000 * n_bezug / einheit.n_I` (nur gewerbe; `n_I=0` → null).
  - `standardGruppen(daten, hauptgruppen) → gruppen[]`: stellung → 9 Klassen je eine Gruppe (Farben wie `FARBEN_STELLUNG` in `werkzeuge/berufe.html`, `unbestimmt` nicht als Gruppe); besitz → 8 Klassen (Farben wie `themen/besitz.json`); gewerbe → 15 Branchen; gruppe → je Hauptgruppe eine Gruppe mit `kurz` als Name (Okabe-Ito zyklisch); niveau → 6 Niveaus.

- [ ] **Step 1: Failing tests `site/tests/ansicht.test.js`**

```js
import test from "node:test";
import assert from "node:assert/strict";
import { MIN_N, STANDARD_ANSICHT, dekodiere, kennzahlen, kodiere, normalisiere, praefix, schluesselDerEinheit, standardGruppen } from "../js/ansicht.js";

const G = [{ name: "Arbeiter", aus: ["arbeiter"], farbe: "#e69f00" }, { name: "Bürgertum", aus: ["beamte", "freie_berufe", "unternehmer", "angestellte"], farbe: "#0072b2" }];
const E = { id: "Katernberg", n_I: 100, n_st_arbeiter: 60, n_st_beamte: 5, n_st_angestellte: 5, n_st_selbstaendige: 10, n_st_kaufleute: 4, n_st_unbestimmt: 16, adressen: 40 };

test("normalisiere füllt Standard, min_n je Ebene, Farben und eindeutige Namen", () => {
  const a = normalisiere({ daten: "stellung", ebene: "strasse", form: "hüpf", gruppen: [{ name: "A", aus: ["arbeiter"] }, { name: "A", aus: ["beamte"] }] });
  assert.equal(a.form, "karte"); assert.equal(a.min_n, MIN_N.strasse);
  assert.deepEqual(a.gruppen.map((g) => g.name), ["A", "A 2"]);
  assert.equal(a.gruppen[0].farbe, "#e69f00"); assert.equal(a.gruppen[1].farbe, "#56b4e9");
  assert.deepEqual(normalisiere({}), STANDARD_ANSICHT);
});

test("kodiere/dekodiere Rundreise, Standardwerte fallen weg, Unsinn → Standard", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const s = kodiere(a);
  assert.match(s, /^[A-Za-z0-9_-]+$/);
  assert.deepEqual(dekodiere(s), a);
  assert.ok(!JSON.parse(Buffer.from(s.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString()).kaufleute);
  assert.deepEqual(dekodiere("%%%"), STANDARD_ANSICHT);
});

test("praefix und Schlüssel der Einheit, Kaufleute-Umschalten", () => {
  assert.equal(praefix("stellung"), "n_st_"); assert.equal(praefix("gewerbe"), "n_gw_"); assert.equal(praefix("niveau"), "n_");
  const a = normalisiere({ daten: "stellung", gruppen: G, bezug: "Arbeiter" });
  assert.deepEqual(schluesselDerEinheit(E, a), { arbeiter: 60, beamte: 5, angestellte: 5, selbstaendige: 10, kaufleute: 4, unbestimmt: 16 });
  const b = normalisiere({ daten: "stellung", gruppen: G, bezug: "Arbeiter", kaufleute: "angestellte" });
  assert.deepEqual(schluesselDerEinheit(E, b).angestellte, 9);
  assert.equal(schluesselDerEinheit(E, b).kaufleute, undefined);
});

test("kennzahlen: N, n_aus, Anteile, unter_min, dominant, mischung", () => {
  const a = normalisiere({ daten: "stellung", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const k = kennzahlen(E, a);
  assert.equal(k.N, 70); assert.equal(k.n_aus, 30);            // selbstaendige 10 + kaufleute 4 + unbestimmt 16
  assert.equal(k.anteile["Arbeiter"], 60 / 70); assert.equal(k.wert, 60 / 70); assert.equal(k.unter_min, false);
  assert.equal(k.dominant, "Arbeiter");
  const d = kennzahlen(E, normalisiere({ ...a, mass: "dominant", min_n: 200 }));
  assert.equal(d.unter_min, true); assert.equal(d.wert, "Arbeiter");
  const gleich = kennzahlen({ n_st_arbeiter: 10, n_st_beamte: 10 }, normalisiere({ daten: "stellung", gruppen: G, mass: "mischung", min_n: 0 }));
  assert.equal(gleich.mischung, 1); assert.equal(gleich.wert, 1);
  const eins = kennzahlen({ n_st_arbeiter: 10 }, normalisiere({ daten: "stellung", gruppen: G, mass: "mischung", min_n: 0 }));
  assert.equal(eins.mischung, 0);
  assert.equal(kennzahlen({ n_st_arbeiter: 3, n_st_beamte: 3 }, normalisiere({ daten: "stellung", gruppen: G, mass: "dominant", min_n: 0 })).wert, "gemischt");
  assert.equal(kennzahlen({}, a).N, 0); assert.equal(kennzahlen({}, a).wert, 0);
});

test("dichte nur für gewerbe: Betriebe je 1.000 Teil-I-Einträge", () => {
  const a = normalisiere({ daten: "gewerbe", gruppen: [{ name: "Lebensmittel", aus: ["lebensmittel"], farbe: "#000" }], bezug: "Lebensmittel", mass: "dichte", min_n: 0 });
  assert.equal(kennzahlen({ n_I: 500, n_gw_lebensmittel: 25, n_gw_bau: 5 }, a).wert, 50);
  assert.equal(kennzahlen({ n_I: 0, n_gw_lebensmittel: 25 }, a).wert, null);
});

test("standardGruppen je Datenkern", () => {
  assert.equal(standardGruppen("stellung").length, 8);
  assert.equal(standardGruppen("besitz").length, 8);
  assert.equal(standardGruppen("gewerbe").length, 15);
  const hg = { B21: { kurz: "Bergbau, Glas, Keramik" }, A10: { kurz: "Berufslose" } };
  assert.deepEqual(standardGruppen("gruppe", hg).map((g) => [g.name, g.aus]), [["Berufslose", ["A10"]], ["Bergbau, Glas, Keramik", ["B21"]]]);
});
```

- [ ] **Step 2: rot** — `node --test site/tests/ansicht.test.js` → Fehler (Modul fehlt).

- [ ] **Step 3: `site/js/ansicht.js`** — vollständig implementieren:

```js
// site/js/ansicht.js — Ansicht-Modell (Spec §4): eine Ansicht beschreibt eine Darstellung vollständig; Karte,
// Perspektiven und Werkstatt lesen und schreiben dasselbe Objekt. Rein, ohne DOM (node:test).
export const DATEN = ["stellung", "gruppe", "niveau", "besitz", "gewerbe"];
export const EBENEN = ["adresse", "strasse", "stadtteil", "hex"];
export const FORMEN = ["karte", "stadtteilkarte", "bubbles", "balken", "multiples", "rangliste"];
export const MASSE = ["anteil", "dominant", "mischung", "dichte"];
export const KAUFLEUTE = ["unbestimmt", "angestellte", "selbstaendige"];
export const MIN_N = Object.freeze({ adresse: 0, strasse: 30, hex: 50, stadtteil: 200 });
export const OKABE_ITO = ["#e69f00", "#56b4e9", "#009e73", "#f0e442", "#0072b2", "#d55e00", "#cc79a7", "#000000"];
export const STANDARD_ANSICHT = Object.freeze({ daten: "stellung", ebene: "stadtteil", form: "karte", gruppen: [], kaufleute: "unbestimmt", unsicher: false, mass: "anteil", bezug: "", min_n: 200, filter: {}, karte: null });
const PRAEFIX = { stellung: "n_st_", gruppe: "n_gr_", niveau: "n_", besitz: "n_bs_", gewerbe: "n_gw_" };
const NENNER = { stellung: "n_I", gruppe: "n_I", niveau: "n_I", besitz: "adressen", gewerbe: "n_III" };
const AUSGESCHLOSSEN = { stellung: ["unbestimmt"], gruppe: ["ungeprueft"], niveau: ["keins"], besitz: ["ungeprueft"], gewerbe: ["ungeprueft"] };
const NIVEAUS = ["helfer", "fachlich", "spezialist", "hochkomplex", "aufsicht", "fuehrung", "unsicher"];
const STELLUNG = { arbeiter: ["Arbeiter/Gehilfen (nach Schreibung)", "#e69f00"], angestellte: ["Angestellte", "#56b4e9"], beamte: ["Beamte", "#009e73"], selbstaendige: ["Selbständige", "#f0e442"], freie_berufe: ["Freie Berufe und Akademiker", "#0072b2"], unternehmer: ["Unternehmer und Leitende", "#d55e00"], ohne_erwerb: ["Ohne Erwerbsberuf", "#cc79a7"], kaufleute: ["Kaufleute (Stellung unbestimmt)", "#000000"] };
const BESITZ = { privatperson: ["Privatpersonen", "#d97706"], stadt_staat: ["Stadt und Staat", "#1d4ed8"], bergbau: ["Bergbau", "#111827"], industrie: ["Industrie", "#b91c1c"], genossenschaft_siedlung: ["Genossenschaft und Siedlung", "#15803d"], kirche_stiftung: ["Kirche und Stiftung", "#7c3aed"], bank_versicherung: ["Bank und Versicherung", "#0e7490"], sonstige: ["Sonstige", "#6b7280"] };
const GEWERBE = ["bergbau", "metall_maschinen", "bau", "holz_moebel", "textil_bekleidung", "lebensmittel", "handel", "gastgewerbe", "verkehr_bahn_post", "finanzen_recht", "verwaltung", "bildung_kultur_kirche", "gesundheit", "haus_reinigung", "sonstige"];
const GEWERBE_TEXT = { bergbau: "Bergbau und Kokerei", metall_maschinen: "Metall, Maschinen, Elektro", bau: "Bau", holz_moebel: "Holz und Möbel", textil_bekleidung: "Textil und Bekleidung", lebensmittel: "Lebensmittel und Genussmittel", handel: "Handel (übrige Waren)", gastgewerbe: "Gastgewerbe", verkehr_bahn_post: "Verkehr, Bahn, Post", finanzen_recht: "Banken, Versicherungen, Immobilien, Beratung", verwaltung: "Verwaltung, Polizei, Recht", bildung_kultur_kirche: "Bildung, Kultur, Medien, Kirche", gesundheit: "Gesundheit", haus_reinigung: "Haushalt, Reinigung, Körperpflege", sonstige: "Sonstige" };

const wahl = (w, erlaubt, standard) => (erlaubt.includes(w) ? w : standard);

export function normalisiere(obj) {
  const o = obj && typeof obj === "object" ? obj : {};
  const daten = wahl(o.daten, DATEN, STANDARD_ANSICHT.daten);
  const ebene = wahl(o.ebene, EBENEN, STANDARD_ANSICHT.ebene);
  const namen = new Set(); const gruppen = [];
  for (const [i, g] of (Array.isArray(o.gruppen) ? o.gruppen : []).entries()) {
    if (!g || typeof g !== "object" || !Array.isArray(g.aus)) continue;
    let name = String(g.name || `Gruppe ${i + 1}`); let n = 2;
    while (namen.has(name)) name = `${String(g.name || `Gruppe ${i + 1}`)} ${n++}`;
    namen.add(name);
    gruppen.push({ name, aus: g.aus.map(String), farbe: typeof g.farbe === "string" && g.farbe ? g.farbe : OKABE_ITO[gruppen.length % OKABE_ITO.length] });
  }
  const min_n = Number.isInteger(o.min_n) && o.min_n >= 0 ? o.min_n : MIN_N[ebene];
  return {
    daten, ebene, form: wahl(o.form, FORMEN, STANDARD_ANSICHT.form), gruppen,
    kaufleute: wahl(o.kaufleute, KAUFLEUTE, "unbestimmt"), unsicher: o.unsicher === true,
    mass: wahl(o.mass, MASSE, "anteil"), bezug: typeof o.bezug === "string" && namen.has(o.bezug) ? o.bezug : (gruppen[0]?.name || ""),
    min_n, filter: o.filter && typeof o.filter === "object" ? { ...o.filter } : {},
    karte: o.karte && typeof o.karte === "object" ? { zentrum: o.karte.zentrum, zoom: o.karte.zoom } : null,
  };
}

// base64url ohne Padding; Standardwerte werden weggelassen, damit Links kurz bleiben.
function b64(s) { return (typeof btoa === "function" ? btoa(unescape(encodeURIComponent(s))) : Buffer.from(s, "utf8").toString("base64")).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
function unb64(s) { const t = s.replace(/-/g, "+").replace(/_/g, "/"); return typeof atob === "function" ? decodeURIComponent(escape(atob(t))) : Buffer.from(t, "base64").toString("utf8"); }
export function kodiere(ansicht) {
  const a = normalisiere(ansicht); const kurz = {};
  for (const k of Object.keys(a)) if (JSON.stringify(a[k]) !== JSON.stringify(STANDARD_ANSICHT[k]) && !(k === "min_n" && a.min_n === MIN_N[a.ebene])) kurz[k] = a[k];
  return b64(JSON.stringify(kurz));
}
export function dekodiere(s) {
  try { return normalisiere(JSON.parse(unb64(String(s || "")))); } catch { return { ...STANDARD_ANSICHT }; }
}

export const praefix = (daten) => PRAEFIX[daten];
export const nenner = (daten) => NENNER[daten];

export function schluesselDerEinheit(einheit, ansicht) {
  const p = praefix(ansicht.daten); const out = {};
  for (const [k, v] of Object.entries(einheit || {})) {
    if (!k.startsWith(p)) continue;
    const s = k.slice(p.length);
    if (ansicht.daten === "niveau" && !NIVEAUS.includes(s)) continue;       // n_I, n_st_… sind keine Niveaus
    if (ansicht.daten === "gruppe" && p === "n_gr_") { /* alle Hauptgruppen */ }
    out[s] = (out[s] || 0) + v;
  }
  if (ansicht.daten === "stellung" && ansicht.kaufleute !== "unbestimmt" && out.kaufleute) { out[ansicht.kaufleute] = (out[ansicht.kaufleute] || 0) + out.kaufleute; delete out.kaufleute; }
  return out;
}

export function kennzahlen(einheit, ansicht) {
  const z = schluesselDerEinheit(einheit, ansicht); const inGruppe = new Set();
  const anteile = {}; const zaehler = {}; let N = 0;
  for (const g of ansicht.gruppen) { zaehler[g.name] = g.aus.reduce((s, k) => s + (z[k] || 0), 0); N += zaehler[g.name]; g.aus.forEach((k) => inGruppe.add(k)); }
  let n_aus = 0;
  for (const [k, v] of Object.entries(z)) if (!inGruppe.has(k)) n_aus += v;
  if (ansicht.daten === "niveau" && !ansicht.unsicher && inGruppe.has("unsicher")) { N -= z.unsicher || 0; n_aus += z.unsicher || 0; for (const g of ansicht.gruppen) if (g.aus.includes("unsicher")) zaehler[g.name] -= z.unsicher || 0; }
  for (const g of ansicht.gruppen) anteile[g.name] = N ? zaehler[g.name] / N : 0;
  const groesste = ansicht.gruppen.reduce((b, g) => (anteile[g.name] > (b ? anteile[b] : -1) ? g.name : b), null);
  const dominant = groesste && anteile[groesste] >= 0.4 ? groesste : "gemischt";
  const k = ansicht.gruppen.length; let h = 0;
  if (k > 1 && N) for (const g of ansicht.gruppen) { const p = anteile[g.name]; if (p > 0) h -= p * Math.log(p); }
  const mischung = k > 1 && N ? Math.min(1, h / Math.log(k)) : 0;
  const nI = einheit?.n_I || 0;
  const dichte = ansicht.daten === "gewerbe" ? (nI ? (1000 * (zaehler[ansicht.bezug] || 0)) / nI : null) : null;
  const wert = ansicht.mass === "anteil" ? (anteile[ansicht.bezug] ?? 0) : ansicht.mass === "dominant" ? dominant : ansicht.mass === "mischung" ? mischung : dichte;
  return { N, n_aus, unter_min: N < ansicht.min_n, anteile, zaehler, wert, dominant, mischung, dichte };
}

export function standardGruppen(daten, hauptgruppen = {}) {
  if (daten === "stellung") return Object.entries(STELLUNG).map(([k, [name, farbe]]) => ({ name, aus: [k], farbe }));
  if (daten === "besitz") return Object.entries(BESITZ).map(([k, [name, farbe]]) => ({ name, aus: k === "sonstige" ? ["sonstige", "gemischt"] : [k], farbe }));
  if (daten === "gewerbe") return GEWERBE.map((k, i) => ({ name: GEWERBE_TEXT[k], aus: [k], farbe: OKABE_ITO[i % OKABE_ITO.length] }));
  if (daten === "niveau") return NIVEAUS.slice(0, 6).map((k, i) => ({ name: k, aus: [k], farbe: OKABE_ITO[i] }));
  return Object.keys(hauptgruppen).sort().map((k, i) => ({ name: hauptgruppen[k].kurz || k, aus: [k], farbe: OKABE_ITO[i % OKABE_ITO.length] }));
}
```

- [ ] **Step 4: grün** — `node --test site/tests/ansicht.test.js`. Prüfen, dass die Erwartung `kennzahlen(E, a).n_aus === 30` stimmt (selbständige 10 + kaufleute 4 + unbestimmt 16); wenn der Test wegen der `gruppe`-Zeile (No-op) meckert, die Zeile entfernen.

- [ ] **Step 5: Commit**

```bash
git add site/js/ansicht.js site/tests/ansicht.test.js
git commit -m "feat(site): Ansicht-Modell — Validierung, base64url-URL, Gruppen, Kennzahlen (anteil, dominant, mischung, dichte)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: `site/js/daten_ebenen.js` — Laden und Werte je Einheit

**Files:**
- Create: `site/js/daten_ebenen.js`
- Modify: `site/js/daten.js` (Lader-Methoden `ebene(name)`, `layout(name)`, `hauptgruppen()`, `stadtteile()` → **Achtung:** `stadtteile()` existiert schon für `suche/stadtteile.json`; neue Methode heißt `stadtteilePolygone()` und lädt `stadtteile.geojson`; `perspektivenIndex()`, `kapitel(id)`)
- Test: `site/tests/daten_ebenen.test.js`, `site/tests/daten.test.js` (Ergänzung)

**Interfaces:**
- Consumes: `Lader` (`site/js/daten.js`), `kennzahlen`/`nenner` aus Task 4.
- Produces: `ladeEbenen(lader) → Promise<{strassen, stadtteile, hex, layout:{berufe, eigentuemer, gewerbe}, hauptgruppen, polygone, kennzahlen}>` (jede Datei einmal, fehlende → `[]`/`{}`/`null`); `einheiten(ebenen, ansicht) → Array` (Einheiten der `ansicht.ebene`; `adresse` → leer, Punkte bleiben der Karte); `werteJeEinheit(ansicht, ebenen) → [{id, name, lat, lon, N, n_aus, unter_min, wert, anteile, zaehler, dominant, mischung, dichte, n_I, adressen, n_III, rang_nord}]` (Straßen: `name` aus Einheit, Stadtteile: `name = id`, Hex: `name = id`); `zusammenfassung(werte) → {N, n_aus, unter_min, einheiten}` (Summen); `filterEinheiten(werte, ansicht.filter)` (Feld `stadtteil: [..]` filtert Straßen nach `stadtteil`, Stadtteile nach `id`; `top: n` kürzt nach `wert` absteigend).

- [ ] **Step 1: Failing tests**

```js
import test from "node:test";
import assert from "node:assert/strict";
import { Lader } from "../js/daten.js";
import { normalisiere } from "../js/ansicht.js";
import { einheiten, filterEinheiten, ladeEbenen, werteJeEinheit, zusammenfassung } from "../js/daten_ebenen.js";

const D = {
  "daten/ebenen/stadtteile.json": [{ id: "Katernberg", lat: 51.5, lon: 7.05, adressen: 40, n_I: 100, n_st_arbeiter: 70, n_st_beamte: 5, n_st_unbestimmt: 25, rang_nord: 1 },
                                   { id: "Südviertel", lat: 51.44, lon: 7.01, adressen: 30, n_I: 60, n_st_arbeiter: 10, n_st_beamte: 20, n_st_unbestimmt: 30, rang_nord: 2 }],
  "daten/ebenen/strassen.json": [{ id: "00001", name: "Aachener Straße", stadtteil: "Frohnhausen", adressen: 5, n_I: 20, n_st_arbeiter: 12, n_st_beamte: 2 }],
  "daten/hauptgruppen.json": { B21: { kurz: "Bergbau" } }, "daten/kennzahlen.json": { adressen: 70316 },
};
const fetchFake = async (u) => ({ ok: u in D, status: u in D ? 200 : 404, json: async () => D[u] });
const G = [{ name: "Arbeiter", aus: ["arbeiter"], farbe: "#e69f00" }, { name: "Beamte", aus: ["beamte"], farbe: "#009e73" }];

test("ladeEbenen lädt einmal und toleriert fehlende Dateien", async () => {
  const l = new Lader("daten/", fetchFake);
  const e = await ladeEbenen(l);
  assert.equal(e.stadtteile.length, 2); assert.equal(e.strassen.length, 1); assert.deepEqual(e.hex, []); assert.equal(e.polygone, null);
  assert.deepEqual(e.layout.berufe, null); assert.equal(e.kennzahlen.adressen, 70316);
});

test("werteJeEinheit rechnet je Einheit und markiert unter min_n", async () => {
  const e = await ladeEbenen(new Lader("daten/", fetchFake));
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const w = werteJeEinheit(a, e);
  assert.deepEqual(w.map((x) => [x.id, x.N, x.n_aus, x.unter_min, Math.round(x.wert * 100)]), [["Katernberg", 75, 25, false, 93], ["Südviertel", 30, 30, true, 33]]);
  assert.equal(w[0].name, "Katernberg"); assert.equal(w[0].rang_nord, 1);
  const s = werteJeEinheit(normalisiere({ ...a, ebene: "strasse", min_n: 10 }), e);
  assert.equal(s[0].name, "Aachener Straße"); assert.equal(s[0].N, 14);
  assert.deepEqual(einheiten(e, normalisiere({ ebene: "adresse" })), []);
  assert.deepEqual(zusammenfassung(w), { N: 105, n_aus: 55, unter_min: 1, einheiten: 2 });
});

test("filterEinheiten nach Stadtteil und top", async () => {
  const e = await ladeEbenen(new Lader("daten/", fetchFake));
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", gruppen: G, bezug: "Beamte", min_n: 0 });
  const w = werteJeEinheit(a, e);
  assert.deepEqual(filterEinheiten(w, { stadtteil: ["Südviertel"] }).map((x) => x.id), ["Südviertel"]);
  assert.deepEqual(filterEinheiten(w, { top: 1 }).map((x) => x.id), ["Südviertel"]);
  const s = werteJeEinheit(normalisiere({ ...a, ebene: "strasse" }), e);
  assert.deepEqual(filterEinheiten(s, { stadtteil: ["Frohnhausen"] }).length, 1);
  assert.deepEqual(filterEinheiten(s, { stadtteil: ["Steele"] }).length, 0);
});
```

- [ ] **Step 2: rot**, dann **Step 3: Implementierung**

`site/js/daten.js` ergänzen:
```js
  ebene(name) { return this.json(`ebenen/${name}.json`); }
  layout(name) { return this.json(`layout/${name}.json`); }
  hauptgruppen() { return this.json("hauptgruppen.json"); }
  stadtteilePolygone() { return this.json("stadtteile.geojson"); }
  perspektivenIndex() { return this.json("perspektiven/index.json"); }
  kapitel(id) { return this.json(`perspektiven/${id}.json`); }
```

`site/js/daten_ebenen.js`:
```js
// Lädt Ebenen, Layouts, Polygone und Kennzahlen einmal je Seite und rechnet Werte je Einheit aus einer Ansicht (Spec §6.3).
import { kennzahlen } from "./ansicht.js";

export async function ladeEbenen(lader) {
  const [strassen, stadtteile, hex, berufe, eigentuemer, gewerbe, hauptgruppen, polygone, kz] = await Promise.all([
    lader.ebene("strassen"), lader.ebene("stadtteile"), lader.ebene("hex"), lader.layout("berufe"), lader.layout("eigentuemer"), lader.layout("gewerbe"),
    lader.hauptgruppen(), lader.stadtteilePolygone(), lader.kennzahlen()]);
  return { strassen: strassen || [], stadtteile: stadtteile || [], hex: hex || [], layout: { berufe, eigentuemer, gewerbe }, hauptgruppen: hauptgruppen || {}, polygone, kennzahlen: kz || {} };
}

export function einheiten(ebenen, ansicht) {
  return ansicht.ebene === "strasse" ? ebenen.strassen : ansicht.ebene === "stadtteil" ? ebenen.stadtteile : ansicht.ebene === "hex" ? ebenen.hex : [];
}

export function werteJeEinheit(ansicht, ebenen) {
  return einheiten(ebenen, ansicht).map((u) => ({ id: u.id, name: u.name || u.id, lat: u.lat, lon: u.lon, stadtteil: u.stadtteil, rang_nord: u.rang_nord,
    n_I: u.n_I || 0, n_III: u.n_III || 0, adressen: u.adressen || 0, ...kennzahlen(u, ansicht) }));
}

export function zusammenfassung(werte) {
  return { N: werte.reduce((s, w) => s + w.N, 0), n_aus: werte.reduce((s, w) => s + w.n_aus, 0), unter_min: werte.filter((w) => w.unter_min).length, einheiten: werte.length };
}

export function filterEinheiten(werte, filter = {}) {
  let w = werte;
  if (Array.isArray(filter.stadtteil) && filter.stadtteil.length) w = w.filter((x) => filter.stadtteil.includes(x.stadtteil ?? x.id));
  if (Number.isInteger(filter.top) && filter.top > 0) w = [...w].filter((x) => !x.unter_min).sort((a, b) => (typeof b.wert === "number" ? b.wert : 0) - (typeof a.wert === "number" ? a.wert : 0)).slice(0, filter.top);
  return w;
}
```

- [ ] **Step 4: grün** — `node --test site/tests/`. Dann Commit:

```bash
git add site/js/daten_ebenen.js site/js/daten.js site/tests/daten_ebenen.test.js
git commit -m "feat(site): Ebenen-Lader und Werte je Einheit aus einer Ansicht

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Formen als reine SVG-Erzeuger — Skalen, Balken, Rangliste, Stadtteilkarte, Bubbles

**Files:**
- Create: `site/js/formen/skalen.js`, `site/js/formen/balken.js`, `site/js/formen/rangliste.js`, `site/js/formen/stadtteilkarte.js`, `site/js/formen/bubbles.js`
- Test: `site/tests/formen.test.js`

**Interfaces:**
- Consumes: `werteJeEinheit`, `zusammenfassung`, `filterEinheiten` (Task 5); Layout-Dateien (`kreise: [{id, n, gruppe, stellung?, art?, r, x, y}]`, `gruppen: [{gruppe, x, y, r}]`); `stadtteile.geojson`.
- Produces: jede Form exportiert `zeige(ansicht, daten, optionen) → {svg: string, legende: [{name, farbe, text}], zahlen: {N, n_aus, unter_min, einheiten, hinweis}}`, wobei `daten` = Ergebnis von `ladeEbenen` und `optionen = {breite, hoehe, hervorheben: [], titel}`. Jedes SVG-Element einer Einheit trägt `data-id="<id>"` und `class="einheit"` (+ `hervorgehoben`, `unter-min`), damit `perspektiven.js` Klick und Hover generisch anbinden kann. Skalen: `farbeAnteil(p) → Farbe` (5 Stufen `SEQUENZ = ["#f7fbff","#c6dbef","#6baed6","#2171b5","#08306b"]` bei 0–0,2, 0,2–0,4, 0,4–0,6, 0,6–0,8, ≥ 0,8), `GRAU = "#c8c8c8"`, `formatProzent(p) → "63 %"`, `formatZahl(n) → "1.234"` (de-DE), `esc(s)`.

- [ ] **Step 1: Failing tests (`site/tests/formen.test.js`)** — Fixtures wie in Task 5 (`D`) plus `daten/stadtteile.geojson` mit zwei Quadraten und `daten/layout/eigentuemer.json` mit drei Kreisen:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { Lader } from "../js/daten.js";
import { normalisiere } from "../js/ansicht.js";
import { ladeEbenen } from "../js/daten_ebenen.js";
import { farbeAnteil, formatProzent, formatZahl } from "../js/formen/skalen.js";
import * as balken from "../js/formen/balken.js";
import * as rangliste from "../js/formen/rangliste.js";
import * as stadtteilkarte from "../js/formen/stadtteilkarte.js";
import * as bubbles from "../js/formen/bubbles.js";

const Q = (x, y) => ({ type: "Feature", properties: { id: "", quelle: "OSM", stand: "d" }, geometry: { type: "MultiPolygon", coordinates: [[[[x, y], [x + 0.1, y], [x + 0.1, y + 0.1], [x, y + 0.1], [x, y]]]] } });
const D = {
  "daten/ebenen/stadtteile.json": [{ id: "Katernberg", lat: 51.5, lon: 7.05, adressen: 40, n_I: 100, n_st_arbeiter: 70, n_st_beamte: 5, n_st_unbestimmt: 25, rang_nord: 1, n_bs_bergbau: 20, n_bs_privatperson: 10, n_bs_ungeprueft: 10 },
                                   { id: "Südviertel", lat: 51.44, lon: 7.01, adressen: 30, n_I: 60, n_st_arbeiter: 10, n_st_beamte: 20, n_st_unbestimmt: 30, rang_nord: 2, n_bs_privatperson: 5, n_bs_ungeprueft: 25 }],
  "daten/stadtteile.geojson": { type: "FeatureCollection", features: [{ ...Q(7.0, 51.45), properties: { id: "Katernberg" } }, { ...Q(7.0, 51.4), properties: { id: "Südviertel" } }] },
  "daten/layout/eigentuemer.json": { kreise: [{ id: "Stadt Essen", n: 969, gruppe: "stadt_staat", r: 60, x: 0, y: 0 }, { id: "Fried. Krupp AG", n: 559, gruppe: "industrie", r: 45, x: 120, y: 0 }, { id: "X", n: 5, gruppe: "sonstige", r: 4, x: 0, y: 80 }], gruppen: [{ gruppe: "stadt_staat", x: 0, y: 0, r: 70 }] },
};
const fetchFake = async (u) => ({ ok: u in D, status: u in D ? 200 : 404, json: async () => D[u] });
const G = [{ name: "Arbeiter", aus: ["arbeiter"], farbe: "#e69f00" }, { name: "Beamte", aus: ["beamte"], farbe: "#009e73" }];
const daten = await ladeEbenen(new Lader("daten/", fetchFake));

test("Skalen", () => {
  assert.equal(farbeAnteil(0.1), "#f7fbff"); assert.equal(farbeAnteil(0.95), "#08306b"); assert.equal(farbeAnteil(0.4), "#6baed6");
  assert.equal(formatProzent(0.6333), "63 %"); assert.equal(formatZahl(70316), "70.316");
});

test("balken: Gesamtbalken mit Segmenten, unbestimmt grau, Zahlenzeile", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "balken", gruppen: G, bezug: "Arbeiter", min_n: 0 });
  const r = balken.zeige(a, daten, { breite: 600, hoehe: 200 });
  assert.match(r.svg, /^<svg/); assert.match(r.svg, /data-id="Arbeiter"/); assert.match(r.svg, /#c8c8c8/);
  assert.deepEqual(r.zahlen, { N: 105, n_aus: 55, unter_min: 0, einheiten: 2, hinweis: "105 Nennungen einbezogen, 55 ausgeschlossen (unbestimmt, ungeprüft)" });
  assert.equal(r.legende.length, 3); assert.equal(r.legende[2].name, "ausgeschlossen");
  const je = balken.zeige({ ...a, filter: { je_einheit: true } }, daten, { breite: 600, hoehe: 200 });
  assert.match(je.svg, /data-id="Katernberg"/); assert.match(je.svg, /data-id="Südviertel"/);
});

test("rangliste: sortiert nach Wert, unter min_n ans Ende und grau, hervorheben", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "rangliste", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const r = rangliste.zeige(a, daten, { breite: 600, hoehe: 300, hervorheben: ["Südviertel"] });
  const ids = [...r.svg.matchAll(/data-id="([^"]+)"/g)].map((m) => m[1]);
  assert.deepEqual(ids, ["Katernberg", "Südviertel"]);
  assert.match(r.svg, /class="einheit hervorgehoben"[^>]*data-id="Südviertel"|data-id="Südviertel"[^>]*class="einheit[^"]*hervorgehoben/);
  assert.match(r.svg, /unter-min/);
  assert.equal(r.zahlen.unter_min, 1);
});

test("stadtteilkarte: Pfade je Polygon, Farbe nach Anteil, grau unter min_n", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "stadtteilkarte", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const r = stadtteilkarte.zeige(a, daten, { breite: 500, hoehe: 500 });
  assert.equal((r.svg.match(/<path/g) || []).length, 2);
  assert.match(r.svg, /data-id="Katernberg"[^>]*fill="#08306b"|fill="#08306b"[^>]*data-id="Katernberg"/);
  assert.match(r.svg, /data-id="Südviertel"[^>]*fill="#c8c8c8"|fill="#c8c8c8"[^>]*data-id="Südviertel"/);
  assert.equal(r.legende[0].text, "0–20 %"); assert.equal(r.legende.at(-1).name, "unter 50 Nennungen");
  assert.match(r.zahlen.hinweis, /heutige Stadtteilgrenzen/);
  assert.equal(stadtteilkarte.zeige(a, { ...daten, polygone: null }, { breite: 500, hoehe: 500 }).svg, "");
});

test("bubbles: Kreise aus dem Layout, Farbe nach Gruppe, hervorheben, Skalierung in die Fläche", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", form: "bubbles", gruppen: [{ name: "Stadt", aus: ["stadt_staat"], farbe: "#1d4ed8" }, { name: "Industrie", aus: ["industrie"], farbe: "#b91c1c" }], min_n: 0 });
  const r = bubbles.zeige(a, daten, { breite: 400, hoehe: 400, hervorheben: ["Fried. Krupp AG"] });
  assert.equal((r.svg.match(/<circle class="einheit/g) || []).length, 3);
  assert.match(r.svg, /data-id="Stadt Essen"[^>]*fill="#1d4ed8"|fill="#1d4ed8"[^>]*data-id="Stadt Essen"/);
  assert.match(r.svg, /data-id="X"[^>]*fill="#c8c8c8"|fill="#c8c8c8"[^>]*data-id="X"/);   // in keiner Gruppe → grau
  assert.match(r.svg, /hervorgehoben/);
  assert.equal(r.zahlen.einheiten, 3);
  assert.equal(bubbles.zeige({ ...a, daten: "niveau" }, daten, { breite: 400, hoehe: 400 }).svg, "");   // kein Layout für niveau → leer
});
```

- [ ] **Step 2: rot**, **Step 3: Implementierung** — Kernstücke:

`skalen.js`:
```js
export const SEQUENZ = ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"];
export const GRAU = "#c8c8c8";
export const farbeAnteil = (p) => SEQUENZ[Math.min(4, Math.max(0, Math.floor((Number(p) || 0) * 5)))];
export const STUFEN_TEXT = ["0–20 %", "20–40 %", "40–60 %", "60–80 %", "80–100 %"];
export const formatProzent = (p) => `${Math.round((Number(p) || 0) * 100)} %`;
export const formatZahl = (n) => new Intl.NumberFormat("de-DE").format(Math.round(Number(n) || 0));
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const hinweisText = (z) => `${formatZahl(z.N)} Nennungen einbezogen, ${formatZahl(z.n_aus)} ausgeschlossen (unbestimmt, ungeprüft)`;
export function svgKopf(b, h) { return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${b} ${h}" width="${b}" height="${h}" role="img">`; }
```

`balken.js` — Gesamtbalken: Zahlen aus `zusammenfassung(werteJeEinheit(...))` **und** Summen je Gruppe (Summe `zaehler` über Einheiten) → Segmente proportional zu `N + n_aus`, letztes Segment grau „ausgeschlossen“; mit `filter.je_einheit` ein Balken je Einheit (sortiert nach `rang_nord`, sonst nach `wert` absteigend), Einheiten unter `min_n` als grauer Balken mit Text „unter min_n“. `legende` = Gruppen + `{name: "ausgeschlossen", farbe: GRAU, text: "unbestimmt/ungeprüft"}`.

`rangliste.js` — Zeilen mit `data-id`, Balkenlänge ∝ `wert` (bei `mass=anteil|mischung` 0–1, bei `dichte` relativ zum Maximum), Text `name`, `formatProzent(wert)` bzw. `formatZahl(wert)` + „ je 1.000“; Einheiten `unter_min` ans Ende mit `class="einheit unter-min"` und grau; `hervorheben` → Klasse `hervorgehoben` und fettes Label; `filter.top` respektieren (über `filterEinheiten`).

`stadtteilkarte.js` — Projektion: Bbox aller Polygone → lineare Abbildung in `breite × hoehe` mit 4 % Rand, `lat` gespiegelt, Breitengrad-Korrektur `x * cos(51.45°)` (einfache Plattkarte, ausreichend für die Stadt); je Feature `<path class="einheit" data-id="…" d="M…Z" fill="…" stroke="#fff">`, `fill = farbeAnteil(wert)` bei `mass=anteil`, Gruppenfarbe bei `dominant` (gemischt → GRAU), `SEQUENZ` bei `mischung`, `farbeAnteil(wert / max)` bei `dichte`; `unter_min` oder ohne Werte → GRAU; `hervorheben` → `stroke="#111" stroke-width="2"`; `legende` = fünf Stufen (`STUFEN_TEXT`) bzw. Gruppen + `{name: "unter <min_n> Nennungen", farbe: GRAU}`; `zahlen.hinweis` endet mit „ · heutige Stadtteilgrenzen (OSM)“; ohne `daten.polygone` → `{svg: "", legende: [], zahlen: {...hinweis: "Stadtteilgrenzen fehlen"}}`.

`bubbles.js` — Layout nach Datenkern: `besitz → daten.layout.eigentuemer`, `stellung|gruppe → daten.layout.berufe`, `gewerbe → daten.layout.gewerbe`, sonst leer. Zugehörigkeit zur Gruppe über das Feld des Layouts: besitz → `k.gruppe`, stellung → `k.stellung`, gruppe → `k.gruppe` (Hauptgruppe), gewerbe → `k.gruppe`; Kreis in keiner Gruppe → GRAU. Koordinaten des Layouts linear in die Fläche skalieren (Bbox aller Kreise inkl. Radius, 4 % Rand). `<circle class="einheit[ hervorgehoben]" data-id="…" cx cy r fill>` + `<title>` mit Name und `n`. `zahlen.einheiten` = Zahl der Kreise, `N` = Summe `n` in Gruppen, `n_aus` = Summe `n` außerhalb.

- [ ] **Step 4: grün** — `node --test site/tests/`; **Step 5: Commit**

```bash
git add site/js/formen site/tests/formen.test.js
git commit -m "feat(site): Formen als reine SVG-Erzeuger — Balken, Rangliste, Stadtteilkarte, Bubbles, Skalen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Perspektiven-Seite — Scrollama, Kapitel-Rendering, Detailkasten, Links

**Files:**
- Create: `site/vendor/scrollama.js`, `site/perspektiven.html`, `site/css/perspektiven.css`, `site/js/perspektiven.js`, `site/js/perspektiven_modell.js`
- Modify: `site/vendor/README.md`
- Test: `site/tests/perspektiven.test.js` (nur `perspektiven_modell.js`)

**Interfaces:**
- Consumes: Tasks 4–6; `Lader.perspektivenIndex()`, `Lader.kapitel(id)`, `Lader.kennzahlen()`.
- Produces (`perspektiven_modell.js`, rein): `sichtbareKapitel(index, vorschau: bool) → index[]`; `fuellePlatzhalter(text, kennzahlen) → string` (`{adressen}` usw. mit `formatZahl`, `{besitz_geprueft_prozent}` = `round1(100 * besitz_geprueft / adressen)`, unbekannte Platzhalter bleiben stehen); `linkKarte(ansicht) → "karte.html?ansicht=<kodiert>"`; `linkWerkstatt(ansicht) → "werkstatt.html?ansicht=<kodiert>"`; `formFuer(ansicht) → "balken"|"rangliste"|"stadtteilkarte"|"bubbles"` (`karte` mit `ebene=stadtteil` → `stadtteilkarte`; `multiples` → `balken` mit `je_einheit`); `detailText(einheit, ansicht) → {titel, zeilen: [string]}` (Name, `N`, Anteile je Gruppe als „Arbeiter 63 % (1.234)“, ausgeschlossen, Hinweis unter `min_n`).

- [ ] **Step 1: Scrollama vendoren** — `curl -sL https://cdn.jsdelivr.net/npm/scrollama@3.2.0/build/scrollama.min.js -o site/vendor/scrollama.js`; prüfen: Datei beginnt mit `!function` oder `(function`, ≈ 4,8 KB, enthält `scrollama`. In `site/vendor/README.md` Zeile: `scrollama.js — Scrollama 3.2.0, MIT, https://github.com/russellsamora/scrollama, abgerufen YYYY-MM-DD`. Die Datei setzt `window.scrollama` (UMD) — im Modul mit `const scrollama = window.scrollama` nutzen.

- [ ] **Step 2: Failing tests `site/tests/perspektiven.test.js`**

```js
import test from "node:test";
import assert from "node:assert/strict";
import { normalisiere } from "../js/ansicht.js";
import { detailText, formFuer, fuellePlatzhalter, linkKarte, sichtbareKapitel } from "../js/perspektiven_modell.js";

test("sichtbareKapitel nur freigegebene, mit vorschau alle", () => {
  const i = [{ id: "a", freigegeben: true }, { id: "b", freigegeben: false }];
  assert.deepEqual(sichtbareKapitel(i, false).map((k) => k.id), ["a"]);
  assert.deepEqual(sichtbareKapitel(i, true).map((k) => k.id), ["a", "b"]);
});

test("fuellePlatzhalter aus kennzahlen", () => {
  const kz = { adressen: 70316, besitz_geprueft: 7546, stellung_geprueft: 73.0, stand: "2026-09-25" };
  assert.equal(fuellePlatzhalter("{adressen} Adressen, {besitz_geprueft} geprüft ({besitz_geprueft_prozent} %), Stand {stand}, {nix}", kz), "70.316 Adressen, 7.546 geprüft (10,7 %), Stand 2026-09-25, {nix}");
  assert.equal(fuellePlatzhalter("{stellung_geprueft} %", kz), "73 %");
});

test("linkKarte kodiert die Ansicht, formFuer bildet ab", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", form: "karte" });
  assert.match(linkKarte(a), /^karte\.html\?ansicht=[A-Za-z0-9_-]+$/);
  assert.equal(formFuer(a), "stadtteilkarte");
  assert.equal(formFuer(normalisiere({ form: "multiples" })), "balken");
  assert.equal(formFuer(normalisiere({ form: "bubbles" })), "bubbles");
});

test("detailText", () => {
  const a = normalisiere({ daten: "stellung", gruppen: [{ name: "Arbeiter", aus: ["arbeiter"] }], bezug: "Arbeiter", min_n: 50 });
  const d = detailText({ id: "Katernberg", name: "Katernberg", N: 30, n_aus: 5, unter_min: true, anteile: { Arbeiter: 1 }, zaehler: { Arbeiter: 30 } }, a);
  assert.equal(d.titel, "Katernberg");
  assert.deepEqual(d.zeilen, ["30 Nennungen einbezogen, 5 ausgeschlossen", "Arbeiter 100 % (30)", "unter 50 Nennungen — Anteil nicht belastbar"]);
});
```

- [ ] **Step 3: `perspektiven_modell.js`** implementieren (Funktionen wie oben; `fuellePlatzhalter`: `text.replace(/\{(\w+)\}/g, (m, k) => …)`, Prozentwerte mit `toLocaleString("de-DE", {maximumFractionDigits: 1})`, ganze Zahlen mit `formatZahl`; `stellung_geprueft` 73.0 → „73“).

- [ ] **Step 4: `site/perspektiven.html`** — Grundgerüst:

```html
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Essen 1936 – Perspektiven</title>
<meta name="description" content="Wohneigentum, soziale Stellung und Gewerbe im Essener Adressbuch 1936 – erzählt in Grafiken und Karten.">
<link rel="stylesheet" href="css/stil.css"><link rel="stylesheet" href="css/perspektiven.css">
</head>
<body class="perspektiven">
<header class="kopf"><a class="logo" href="index.html">Essen 1936</a><nav><a href="karte.html">Karte</a> · <a href="ueber.html">Über das Projekt</a></nav></header>
<main id="main">
  <section class="einleitung"><h1>Perspektiven</h1><p id="einleitung"></p><ol id="inhalt" class="inhaltsverzeichnis"></ol></section>
  <div id="kapitel"></div>
</main>
<aside id="detail" class="detail" hidden aria-live="polite"></aside>
<footer>Quelle: Adreßbuch Essen 1936 (Scherl), Erfassung Verein für Computergenealogie · Stadtteilgrenzen: heutige Grenzen, © OpenStreetMap-Mitwirkende (ODbL) · <a href="impressum.html">Impressum</a></footer>
<script src="vendor/scrollama.js"></script>
<script type="module" src="js/perspektiven.js"></script>
</body></html>
```

Je Kapitel erzeugt `perspektiven.js` dieses Markup:
```html
<section class="kapitel" id="k-<id>">
  <header><h2>{titel}</h2><p class="untertitel">{untertitel}</p><p>{einleitung}</p></header>
  <div class="scrolly">
    <div class="grafik" aria-hidden="true"><div class="svg"></div><div class="legende"></div><div class="zahlen"></div></div>
    <div class="schritte">
      <article class="schritt" data-schritt="<schritt.id>" tabindex="0"><p>{text}</p><p class="sr-only">{beschreibung}</p>
        <p class="links"><a href="{linkKarte}">Auf der Karte öffnen</a> · <a href="{linkWerkstatt}">In der Werkstatt öffnen</a></p></article>
      …
    </div>
  </div>
  <section class="grenzen"><h3>Was die Zahlen zeigen – und was nicht</h3><p>{grenzen mit Platzhaltern gefüllt}</p><p class="quellen">Quellen: …</p></section>
</section>
```

- [ ] **Step 5: `site/js/perspektiven.js`**

```js
import { Lader } from "./daten.js";
import { normalisiere } from "./ansicht.js";
import { ladeEbenen, werteJeEinheit } from "./daten_ebenen.js";
import { esc } from "./formen/skalen.js";
import * as balken from "./formen/balken.js";
import * as rangliste from "./formen/rangliste.js";
import * as stadtteilkarte from "./formen/stadtteilkarte.js";
import * as bubbles from "./formen/bubbles.js";
import { detailText, formFuer, fuellePlatzhalter, linkKarte, linkWerkstatt, sichtbareKapitel } from "./perspektiven_modell.js";

const FORMEN = { balken, rangliste, stadtteilkarte, bubbles };
const lader = new Lader();
const vorschau = new URLSearchParams(location.search).get("vorschau") === "1";
const reduziert = matchMedia("(prefers-reduced-motion: reduce)").matches;

const daten = await ladeEbenen(lader);
const index = sichtbareKapitel((await lader.perspektivenIndex()) || [], vorschau);
document.getElementById("einleitung").textContent = fuellePlatzhalter("Drei Blicke auf das Adressbuch von 1936: {adressen} verortete Adressen, Stand {stand}. Jede Grafik nennt, wie viel geprüft ist und was ausgeschlossen bleibt.", daten.kennzahlen);
document.getElementById("inhalt").innerHTML = index.map((k) => `<li><a href="#k-${esc(k.id)}">${esc(k.titel)}</a>${k.freigegeben ? "" : " <small>(Vorschau)</small>"}</li>`).join("");

for (const eintrag of index) {
  const k = await lader.kapitel(eintrag.id);
  if (!k) continue;
  const sec = document.createElement("section"); sec.className = "kapitel"; sec.id = `k-${k.id}`;
  sec.innerHTML = kapitelHtml(k);
  document.getElementById("kapitel").appendChild(sec);
  bindeKapitel(sec, k);
}

function kapitelHtml(k) { /* Markup wie in Step 4, Texte mit esc(), grenzen mit fuellePlatzhalter(k.grenzen, daten.kennzahlen) */ }

function zeichne(sec, schritt) {
  const ansicht = normalisiere(schritt.ansicht);
  const form = FORMEN[formFuer(ansicht)];
  const grafik = sec.querySelector(".grafik");
  const breite = grafik.clientWidth || 600, hoehe = Math.max(320, Math.min(grafik.clientHeight || 500, 700));
  const r = form.zeige(ansicht, daten, { breite, hoehe, hervorheben: schritt.hervorheben || [], titel: schritt.beschreibung });
  const svg = grafik.querySelector(".svg");
  if (!reduziert) svg.classList.add("wechsel");                 // CSS-Transition ≤ 800 ms auf Kreisen/Pfaden
  svg.innerHTML = r.svg;
  grafik.querySelector(".legende").innerHTML = r.legende.map((l) => `<span><i style="background:${esc(l.farbe)}"></i>${esc(l.name)}${l.text ? ` <small>${esc(l.text)}</small>` : ""}</span>`).join("");
  grafik.querySelector(".zahlen").textContent = r.zahlen.hinweis + (r.zahlen.unter_min ? ` · ${r.zahlen.unter_min} Einheiten unter min_n` : "");
  grafik.setAttribute("aria-label", schritt.beschreibung || "");
  const werte = werteJeEinheit(ansicht, daten);
  svg.querySelectorAll(".einheit").forEach((el) => el.addEventListener("click", () => zeigeDetail(el.dataset.id, werte, ansicht, el.querySelector("title")?.textContent)));
}

function zeigeDetail(id, werte, ansicht, titelFallback) {
  const w = werte.find((x) => x.id === id);
  const d = w ? detailText(w, ansicht) : { titel: titelFallback || id, zeilen: [] };
  const box = document.getElementById("detail");
  box.innerHTML = `<button class="schliessen" aria-label="Schließen">✕</button><h4>${esc(d.titel)}</h4>${d.zeilen.map((z) => `<p>${esc(z)}</p>`).join("")}` +
    (ansicht.ebene === "stadtteil" && w ? `<p><a href="karte.html?stadtteil=${encodeURIComponent(id)}">Auf der Karte zeigen</a></p>` : "");
  box.hidden = false;
  box.querySelector(".schliessen").onclick = () => { box.hidden = true; };
}

function bindeKapitel(sec, k) {
  const schritte = Object.fromEntries(k.schritte.map((s) => [s.id, s]));
  const zeigeSchritt = (el) => { el.classList.add("aktiv"); zeichne(sec, schritte[el.dataset.schritt]); };
  sec.querySelectorAll(".schritt").forEach((el) => el.addEventListener("focus", () => zeigeSchritt(el)));
  if (window.scrollama) {
    const sc = window.scrollama();
    sc.setup({ step: `#${sec.id} .schritt`, offset: 0.6 }).onStepEnter((r) => { sec.querySelectorAll(".schritt").forEach((e) => e.classList.remove("aktiv")); zeigeSchritt(r.element); });
    addEventListener("resize", () => sc.resize());
  }
  zeigeSchritt(sec.querySelector(".schritt"));                  // Erstansicht, auch ohne Scrollen
}
```

CSS `site/css/perspektiven.css`: `.scrolly { display: grid; grid-template-columns: 40% 60%; gap: 24px }`, `.grafik { position: sticky; top: 16px; height: calc(100vh - 32px) }`, `.schritt { min-height: 60vh; padding: 16px; opacity: .45 }`, `.schritt.aktiv { opacity: 1 }`, mobil (`max-width: 899px`): Grafik `position: sticky; top: 0; height: 55vh; z-index: 0` und Schritte darüber mit `background: rgba(250,248,243,.92)`; `.svg.wechsel circle, .svg.wechsel path { transition: all .8s ease }`; `@media (prefers-reduced-motion: reduce) { .svg.wechsel * { transition: none } }`; `.legende span i { width: 12px; height: 12px; display: inline-block; margin-right: 4px }`; `.detail { position: fixed; right: 16px; bottom: 16px; background: #fff; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,.2); padding: 12px 16px; max-width: 320px; z-index: 5 }`; `.sr-only`-Klasse.

- [ ] **Step 6: Tests grün, Sichtprüfung** — `node --test site/tests/`; Dev-Server läuft (`python3 werkzeuge/serve.py 8765`), `http://localhost:8765/site/perspektiven.html?vorschau=1` im Report als Prüf-URL nennen (Klicktest macht der Projektleiter). Ohne `?vorschau=1` muss die Seite eine leere Kapitelliste mit Hinweis „Noch kein Kapitel freigegeben“ zeigen (im `else`-Fall von `index.length === 0` ins `#kapitel` schreiben).

- [ ] **Step 7: Commit**

```bash
git add site/vendor/scrollama.js site/vendor/README.md site/perspektiven.html site/css/perspektiven.css site/js/perspektiven.js site/js/perspektiven_modell.js site/tests/perspektiven.test.js
git commit -m "feat(site): Perspektiven-Seite mit Scrollama, Kapitel-Rendering, Detailkasten und Ansicht-Links

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Kapitel 2 „Soziale Stellung“ und Kapitel 3 „Gewerbe und Versorgung“

**Files:**
- Create: `kuratierung/perspektiven/stellung.json`, `kuratierung/perspektiven/gewerbe.json`
- Test: `tests/test_perspektiven.py::test_echte_kapitel_sind_gueltig` (bestehend) — beide müssen gültig sein

**Interfaces:** Consumes Schema aus Task 3; Formen aus Task 6 (`stadtteilkarte`, `rangliste`, `balken` mit `filter.je_einheit`, `bubbles`).

- [ ] **Step 1: `stellung.json`** — `reihenfolge: 2`, `freigegeben: false`, Platzhaltertexte; Standardgruppen der Stellung (8 Klassen, Farben wie `STELLUNG` in `ansicht.js`) als Gruppen des ersten Schritts, Kurzform `wie:anteile` danach. Schritte:
  1. `anteile`: `balken`, alle acht Klassen, `bezug: "Arbeiter/Gehilfen (nach Schreibung)"`, `min_n: 0`.
  2. `nord-sued`: `rangliste`, Gruppen `Arbeiter` = `[arbeiter]`, `übrige bestimmte` = `[angestellte, beamte, selbstaendige, freie_berufe, unternehmer, ohne_erwerb, kaufleute]`, `bezug: "Arbeiter"`, `min_n: 200`, `filter: {}`, `hervorheben: ["Katernberg", "Margaretenhöhe"]`; `beschreibung`: „Rangliste der Stadtteile nach Arbeiteranteil“.
  3. `karte-arbeiter`: `stadtteilkarte`, dieselben Gruppen, `min_n: 200`.
  4. `karte-buergertum`: `stadtteilkarte`, Gruppen `Bürgertum` = `[beamte, angestellte, freie_berufe, unternehmer]`, `übrige bestimmte` = Rest, `bezug: "Bürgertum"`, `min_n: 200`, `hervorheben: ["Huttrop", "Margaretenhöhe", "Südviertel"]`.
  5. `mischung`: `balken` mit `filter: {je_einheit: true, stadtteil: ["Stadtkern", "Südviertel", "Katernberg", "Margaretenhöhe"]}`, alle acht Klassen, `mass: "mischung"`, `min_n: 200`.
  6. `kaufleute-selbstaendig`: wie 4 mit `kaufleute: "selbstaendige"`; 7. `kaufleute-angestellt`: wie 4 mit `kaufleute: "angestellte"` und `Bürgertum` um `kaufleute`-Ziel erweitert — d. h. in 7 `Bürgertum = [beamte, angestellte, freie_berufe, unternehmer]` (Kaufleute fließen über das Umschalten in `angestellte`), in 6 fließen sie in `selbstaendige` (übrige).
  `grenzen`: „Von {adressen} Adressen … Stellung handgeprüft für {stellung_geprueft} % der Einträge, {stellung_vorschlag} % Automatik-Vorschlag, {stellung_unbestimmt} % unbestimmt oder ohne geprüften Beruf. Der Anteil „unbestimmt“ ist nicht zufällig verteilt: in bürgerlichen Vierteln sind seltene Berufsbezeichnungen häufiger und öfter noch ungeprüft. Klassen nach der Berufszählung 1933 / AVG 1911 (docs/stellung.md); „Arbeiter/Gehilfen (nach Schreibung)“ schließt bei manchen Handwerksberufen Inhaber ein. Heutige Stadtteilgrenzen.“
- [ ] **Step 2: `gewerbe.json`** — `reihenfolge: 3`. Schritte:
  1. `rubriken`: `bubbles`, 15 Branchen als Gruppen (Farben Okabe-Ito zyklisch, wie `standardGruppen("gewerbe")`), `hervorheben: ["Schneider für Herren", "Schankwirt"]`.
  2. `dichte`: `rangliste`, `daten: "gewerbe"`, Gruppen `alle Betriebe` = alle 15 Schlüssel, `bezug: "alle Betriebe"`, `mass: "dichte"`, `min_n: 200`, `beschreibung`: „Betriebe je 1.000 Teil-I-Einträge je Stadtteil“.
  3. `karte-lebensmittel`: `stadtteilkarte`, Gruppen `Lebensmittel` = `[lebensmittel]`, `übrige` = Rest, `bezug: "Lebensmittel"`, `mass: "dichte"`, `min_n: 200`.
  4. `geschaeftsstrassen`: `rangliste`, `ebene: "strasse"`, Gruppen wie 2, `mass: "dichte"`, `min_n: 30`, `filter: {top: 15}`.
  `grenzen`: „{gewerbe_geprueft} % der Betriebe handgeprüft, {gewerbe_entschieden} % nach dokumentierten Prinzipien entschieden, {gewerbe_vorschlag} % Wortregel (docs/gewerbe.md). Dichte = Betriebe je 1.000 Einwohnereinträge (Teil I) der Einheit; Teil III nennt Betriebe, nicht Beschäftigte.“
- [ ] **Step 3:** `python3 -m pytest tests/test_perspektiven.py -q` grün; `python3 pipeline/06_karte_export.py` (Kapitel landen in `site/daten/perspektiven/`); Sichtprüfung `?vorschau=1`.
- [ ] **Step 4: Commit** — `git add kuratierung/perspektiven/stellung.json kuratierung/perspektiven/gewerbe.json && git commit -m "feat(perspektiven): Kapitel 2 Soziale Stellung und 3 Gewerbe und Versorgung (Ansichten, Platzhaltertext)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"`

---

### Task 9: Karte versteht `?ansicht=` — Stadtteile, Straßen, Hex einfärben (Spec §8)

**Files:**
- Modify: `site/js/zustand.js`, `site/js/karte.js`, `site/js/app.js`, `site/js/sidebar.js` (nur Anzeige der Ansicht im Themenkopf), `site/css/stil.css`
- Test: `site/tests/zustand.test.js`

**Interfaces:**
- Consumes: `kodiere/dekodiere/normalisiere` (Task 4), `ladeEbenen/werteJeEinheit` (Task 5), `farbeAnteil/GRAU` (Task 6), PMTiles-Schichten `strassen` (Linien, Feld `id` = `schl_nr`/`1936:…`) und `hex` (Polygone, Feld `id`) aus 5a, `stadtteile.geojson` (Task 2).
- Produces: `STANDARD.ansicht = ""`; `liesZustand` liest `ansicht` als Roh-String (nicht dekodiert — Dekodieren macht `app.js`); `schreibeZustand` schreibt ihn unverändert. `Karte.setzeAnsicht(ansicht | null, werteMap: Map<id, {wert, unter_min, dominant, farbe}>)`: legt (einmalig) Quelle `stadtteile` (GeoJSON, `promoteId: "id"`) und Ebenen `stadtteile-flaeche` (fill), `strassen-linie` (line, Quelle `adressen`, source-layer `strassen`), `hex-flaeche` (fill, source-layer `hex`) an, alle `visibility: none`; bei Ansicht: passende Ebene sichtbar, Farbe per `feature-state` `farbe` (`["coalesce", ["feature-state", "farbe"], GRAU]`), Punkte gedimmt (`circle-opacity` 0,15) bei `ebene ≠ adresse`; ohne Ansicht alles zurück. Legende (`app.js::zeichneLegende`): bei Ansicht Gruppen/Stufen + `min_n` + `N`/ausgeschlossen + „Straßenlinien: heutige Führung“ bzw. „heutige Stadtteilgrenzen“. Sidebar-Themenkopf: „Ansicht: {daten} · {ebene} · {mass}“ + Link „In der Werkstatt öffnen“ (`werkstatt.html?ansicht=` — die Seite kommt in 5c; Link darf 404 sein, im Kopf als „(ab 5c)“ kennzeichnen).

- [ ] **Step 1: Tests `zustand.test.js` ergänzen**

```js
test("ansicht wird roh durchgereicht", () => {
  const z = liesZustand("?ansicht=eyJkYXRlbiI6ImJlc2l0eiJ9");
  assert.equal(z.ansicht, "eyJkYXRlbiI6ImJlc2l0eiJ9");
  assert.equal(schreibeZustand(z), "ansicht=eyJkYXRlbiI6ImJlc2l0eiJ9");
  assert.equal(liesZustand("").ansicht, "");
});
```

- [ ] **Step 2: Implementierung** — `zustand.js`: `ansicht: ""` in `STANDARD`, `ansicht: p.get("ansicht") || ""` in `liesZustand`. `karte.js`: in `_eigeneQuellen()` Quelle `stadtteile: { type: "geojson", data: DATEN + "stadtteile.geojson", promoteId: "id" }`; in `_eigeneEbenen()` die drei Ebenen (vor den Adress-Ebenen einfügen, damit Punkte oben liegen): `{ id: "stadtteile-flaeche", type: "fill", source: "stadtteile", layout: { visibility: "none" }, paint: { "fill-color": ["coalesce", ["feature-state", "farbe"], "#c8c8c8"], "fill-opacity": 0.55, "fill-outline-color": "#fff" } }`, `{ id: "strassen-linie", type: "line", source: "adressen", "source-layer": "strassen", layout: { visibility: "none" }, paint: { "line-color": ["coalesce", ["feature-state", "farbe"], "#c8c8c8"], "line-width": ["interpolate", ["linear"], ["zoom"], 11, 1.5, 15, 5] } }`, `{ id: "hex-flaeche", type: "fill", source: "adressen", "source-layer": "hex", layout: { visibility: "none" }, paint: { "fill-color": ["coalesce", ["feature-state", "farbe"], "#c8c8c8"], "fill-opacity": 0.6 } }`. Methode:

```js
  setzeAnsicht(ansicht, werte) {
    this.ansicht = ansicht; this.ansichtWerte = werte || new Map();
    const m = this.map; if (!m.getLayer("stadtteile-flaeche")) return;
    const ebene = ansicht ? ansicht.ebene : null;
    m.setLayoutProperty("stadtteile-flaeche", "visibility", ebene === "stadtteil" ? "visible" : "none");
    m.setLayoutProperty("strassen-linie", "visibility", ebene === "strasse" ? "visible" : "none");
    m.setLayoutProperty("hex-flaeche", "visibility", ebene === "hex" ? "visible" : "none");
    const quelle = ebene === "stadtteil" ? { source: "stadtteile" } : { source: "adressen", sourceLayer: ebene === "strasse" ? "strassen" : "hex" };
    if (ebene && ebene !== "adresse") {
      m.removeFeatureState(quelle);
      for (const [id, w] of this.ansichtWerte) m.setFeatureState({ ...quelle, id }, { farbe: w.farbe });
    }
    this._deckkraftSetzen();
  }
```
und in `_deckkraftSetzen`: Basisdeckkraft `0.15` statt `0.9`, wenn `this.ansicht && this.ansicht.ebene !== "adresse"`. In `ebenenAufsetzen()` zusätzlich `this.setzeAnsicht(this.ansicht, this.ansichtWerte)` (nach Stilwechsel neu anlegen). `app.js`: beim Start und bei Änderung von `zustand.ansicht` → `ansicht = zustand.ansicht ? normalisiere(dekodiere(zustand.ansicht)) : null`; `ebenen = await ladeEbenen(lader)` (lazy, einmal); `werte = werteJeEinheit(ansicht, ebenen)`; Map `id → {farbe}` mit `farbe = w.unter_min ? GRAU : mass === "dominant" ? (Gruppenfarbe von w.dominant oder GRAU) : farbeAnteil(mass === "dichte" ? w.wert / max : w.wert)`; `karte.setzeAnsicht(ansicht, map)`; Legende erweitern.
  Hex-IDs im Tile sind Strings `"q_r"`, Straßen-IDs Strings (`"00001"`) — `promoteId` ist für PMTiles-Schichten in 5a bereits über `id` gesetzt? Prüfen in `_eigeneQuellen()` (Quelle `adressen`: `promoteId` muss je source-layer gelten: `promoteId: { adressen: "id", strassen: "id", hex: "id" }`) — falls nur `"id"` gesetzt ist, auf die Objektform umstellen.

- [ ] **Step 3: Sichtprüfung** — `http://localhost:8765/site/karte.html?ansicht=<kodierte Ansicht aus Kapitel 2, Schritt karte-arbeiter>`: Stadtteile eingefärbt, Punkte gedimmt, Legende mit Stufen und Hinweis. Die kodierte Ansicht erzeugen mit `node -e "import('./site/js/ansicht.js').then(m=>console.log(m.kodiere({daten:'stellung',ebene:'stadtteil',form:'karte',gruppen:[{name:'Arbeiter',aus:['arbeiter'],farbe:'#e69f00'},{name:'übrige',aus:['angestellte','beamte','selbstaendige','freie_berufe','unternehmer','ohne_erwerb','kaufleute'],farbe:'#999'}],bezug:'Arbeiter',min_n:200})))"`; URL im Report nennen.

- [ ] **Step 4: Tests, Commit**

```bash
node --test site/tests/
git add site/js/zustand.js site/js/karte.js site/js/app.js site/js/sidebar.js site/css/stil.css site/tests/zustand.test.js
git commit -m "feat(karte): ?ansicht= färbt Stadtteile, Straßen und Hexfelder per feature-state, Legende mit min_n und Ausschluss

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Startseite, Über-Seite, Doku, Export, Journal

**Files:**
- Modify: `site/index.html`, `site/js/start.js`, `site/ueber.html`, `README.md`, `docs/perspektiven.md`, `docs/superpowers/specs/…` (nur Verweis „umgesetzt in 5b“ in §6 und §5.4a)
- Test: bestehende Suiten

- [ ] **Step 1: Startseite** — Kachel `<a class="kachel" href="perspektiven.html" id="kachel-perspektiven" hidden><b>Perspektiven</b><small>Wohneigentum, soziale Stellung, Gewerbe</small></a>`; `start.js`: `const p = await lader.perspektivenIndex(); if (p && p.some((k) => k.freigegeben)) document.getElementById("kachel-perspektiven").hidden = false;` (Spec §6.2: Kachel erst bei freigegebenem Kapitel). Solange kein Kapitel freigegeben ist, bleibt sie versteckt — in der Über-Seite steht der Absatz mit Link `perspektiven.html?vorschau=1` **nicht** (Vorschau ist Arbeitsmodus, nicht öffentlich); stattdessen ein Absatz „Perspektiven (in Arbeit)“ ohne Link, der die drei Kapitel nennt.
- [ ] **Step 2: README** — Abschnitt „Perspektiven (Teilprojekt 5b)“: Seitenaufbau, Ansicht-Format (Verweis Spec §4, `site/js/ansicht.js`), Kapitel-JSON (Verweis `docs/perspektiven.md`), Formen, Scrollama, Karte `?ansicht=`, Kennzeichnungen (heutige Stadtteilgrenzen, Quelle-Felder), Tests; Tabelle `site/daten` um `perspektiven/`, `stadtteile.geojson`; Ablauf-Block um `osm_stadtteile_laden.py`.
- [ ] **Step 3: Export und Kennzahlen** — `python3 pipeline/06_karte_export.py`; Kennzahlen (`stadtteil_polygon`, Stellung, Gewerbe) in README-Abschnitt „Kennzahlen“ aktualisieren.
- [ ] **Step 4: Alle Suiten** — `python3 -m pytest -q -m "not e2e"`, `node --test site/tests/`, `node --test werkzeuge/tests/`.
- [ ] **Step 5: Commit**

```bash
git add site/index.html site/js/start.js site/ueber.html README.md docs/perspektiven.md docs/superpowers/specs/2026-09-24-perspektiven-werkstatt-design.md
git commit -m "docs(perspektiven): Startseiten-Kachel, Über-Seite, README und Spec-Verweise für 5b

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

Journal-Eintrag (Vault `~/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Journal.md`) schreibt der Controller nach dem Abschluss-Review, nicht der Implementer.

---

## Self-Review (durchgeführt beim Schreiben)

- **Spec-Abdeckung:** §4 Ansicht-Modell → Task 4; §4.1 Kennzahlen → Task 4 (`kennzahlen`); §4.2 URL → Task 4 (`kodiere`), Task 9 (`zustand.ansicht`); Themen-Migration auf Ansicht-Format (§4.2 Absatz 2) → **nicht in 5b** (Themen bleiben im alten Format, `themen.js` unverändert; die Migration gehört zu 5c, wenn die Werkstatt Standardgruppen aus Themen liest — Ruling, in README vermerken); §5.4a → Tasks 1–2; §6.1 → Task 7 (Übergänge per CSS-Transition, reduced-motion, Tastatur/Fokus, Detailkasten, Links, Grenzen); §6.2 → Tasks 3, 8; §6.3 → Tasks 5–7 (`multiples` bewusst nicht gebaut, Spec sagt „erst in 5c“); §8 → Task 9 (Punkte bei `ebene=adresse` ungefärbt — Färbung der Punkte nach Ansicht folgt in 5c mit den Nutzergruppen); §9 pytest/node → in jeder Task, Playwright ausgeschlossen (Global Constraints).
- **Platzhalter-Scan:** Kapiteltexte sind absichtlich Platzhalter (Spec §6.2). `kapitelHtml` in Task 7 ist mit „Markup wie in Step 4“ beschrieben — das Markup steht in Step 4 vollständig; Formen in Task 6 sind als Verhalten + Testerwartung spezifiziert, die Tests legen Attribute, Klassen und Zahlen fest.
- **Typkonsistenz:** `zeige(ansicht, daten, optionen) → {svg, legende, zahlen}` in Task 6 und 7; `werteJeEinheit(ansicht, ebenen)` in Task 5, 7, 9; `kennzahlen(einheit, ansicht)` Rückgabefelder `N, n_aus, unter_min, anteile, zaehler, wert, dominant, mischung, dichte` in Tasks 4–7; `Lader.stadtteilePolygone()` (nicht `stadtteile()`, das existiert für die Suche) in Tasks 5–6, 9; `stadtteil_quelle` in Task 2 und README; `filter.je_einheit` und `filter.top`, `filter.stadtteil` in Tasks 5, 6, 8.
