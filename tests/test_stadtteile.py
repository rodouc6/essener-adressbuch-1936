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


def test_stadtteile_aus_overpass_json():
    from werkzeuge.osm_stadtteile_laden import stadtteile_aus
    osm = {"elements": [{"type": "relation", "tags": {"name": "Stadtkern"}, "members": MEMBERS}, {"type": "way", "id": 1}]}
    st = stadtteile_aus(osm)
    assert list(st) == ["Stadtkern"] and len(st["Stadtkern"]) == 1 and st["Stadtkern"][0][0] == st["Stadtkern"][0][-1]
