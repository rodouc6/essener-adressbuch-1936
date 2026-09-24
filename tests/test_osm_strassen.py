import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from werkzeuge.osm_strassen_laden import _merge, linien_aus, overpass_abfrage

OSM = {"elements": [
    {"type": "way", "id": 1, "tags": {"highway": "residential", "name": "Grenzstraße"}, "geometry": [{"lat": 51.49, "lon": 7.06}, {"lat": 51.491, "lon": 7.061}]},
    {"type": "way", "id": 2, "tags": {"highway": "residential", "name": "Grenzstraße"}, "geometry": [{"lat": 51.491, "lon": 7.061}, {"lat": 51.492, "lon": 7.062}]},
    {"type": "way", "id": 3, "tags": {"highway": "footway", "name": "Grenzstraße"}, "geometry": [{"lat": 51.5, "lon": 7.0}, {"lat": 51.5, "lon": 7.001}]},
    {"type": "way", "id": 4, "tags": {"highway": "residential"}, "geometry": [{"lat": 51.5, "lon": 7.0}, {"lat": 51.5, "lon": 7.001}]},
    {"type": "way", "id": 5, "tags": {"highway": "primary", "name": "Altendorfer Straße"}, "geometry": [{"lat": 51.46, "lon": 6.99}]},
]}


def test_linien_je_name_ohne_fusswege_und_namenlose():
    l = linien_aus(OSM)
    assert list(l) == ["Altendorfer Straße", "Grenzstraße"]
    assert l["Grenzstraße"] == [[[7.06, 51.49], [7.061, 51.491]], [[7.061, 51.491], [7.062, 51.492]]]
    assert l["Altendorfer Straße"] == [[[6.99, 51.46]]]


def test_abfrage_nennt_essen_und_highway():
    q = overpass_abfrage()
    assert "62713" in q and "highway" in q and "out geom" in q


def test_abfrage_mit_bbox_und_area():
    # Review TP5a: die --halbieren-Bboxen (51.30–51.58 / 6.85–7.20) reichen über die Essener
    # Stadtgrenze hinaus; ohne die Area-Einschränkung könnten fremde, gleichnamige Straßensegmente
    # außerhalb Essens fälschlich mit erfasst werden. Beide Bbox-Abfragen filtern deshalb zusätzlich
    # auf area.essen — wie die ungeteilte Abfrage.
    q = overpass_abfrage((51.30, 6.85, 51.44, 7.20))
    assert "51.3" in q and "6.85" in q and "highway" in q and "out geom" in q
    assert "62713" in q and "area.essen" in q


def test_merge_dedupliziert_segmente_an_der_bbox_grenze():
    # Ein Way, der die Süd/Nord-Grenze berührt, kann in beiden Bbox-Abfragen auftauchen —
    # reine Konkatenation würde das Segment doppelt zählen.
    sued = {"Grenzstraße": [[[7.06, 51.44], [7.061, 51.441]]], "Nur Süd": [[[7.0, 51.3]]]}
    nord = {"Grenzstraße": [[[7.06, 51.44], [7.061, 51.441]]], "Nur Nord": [[[7.0, 51.5]]]}
    m = _merge(sued, nord)
    assert m["Grenzstraße"] == [[[7.06, 51.44], [7.061, 51.441]]]
    assert m["Nur Süd"] == [[[7.0, 51.3]]] and m["Nur Nord"] == [[[7.0, 51.5]]]
    assert list(m) == ["Grenzstraße", "Nur Nord", "Nur Süd"]
