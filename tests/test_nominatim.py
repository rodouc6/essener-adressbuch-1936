import json
from pathlib import Path
import pytest
from pipeline.lib import nominatim as nm


class FakeClient:
    def __init__(self, antworten):
        self.antworten = antworten
        self.aufrufe = []

    def suche(self, params):
        self.aufrufe.append(params)
        return self.antworten.get(params.get("street", ""), [])


HAUS = [{"lat": "51.45", "lon": "7.01", "osm_type": "way", "osm_id": "1", "class": "building", "type": "yes",
         "display_name": "5, Bochumer Straße, Steele, Essen",
         "address": {"house_number": "5", "road": "Bochumer Straße", "suburb": "Steele"}}]
STRASSE = [{"lat": "51.46", "lon": "7.02", "osm_type": "way", "osm_id": "2", "class": "highway", "type": "residential",
            "display_name": "Bochumer Straße, Steele, Essen", "address": {"road": "Bochumer Straße", "suburb": "Steele"}}]


def geo(client, **kw):
    basis = dict(strasse_heute="Bochumer Straße", hausnr="5", hausnr_zusatz="", stadtteil="Steele",
                 parse_status="ok", strasse_roh="Bochumer Str.", landmarken=[])
    basis.update(kw)
    return nm.geokodiere(client, **basis)


def test_haus_treffer():
    v = geo(FakeClient({"5 Bochumer Straße": HAUS}))
    assert (v.stufe, v.lat, v.lon, v.osm_id, v.grund) == ("haus", "51.45", "7.01", "1", "")


def test_haus_verlangt_gleiche_strasse():
    falsch = [dict(HAUS[0], address={"house_number": "5", "road": "Bochumer Platz", "suburb": "Steele"})]
    v = geo(FakeClient({"5 Bochumer Straße": falsch, "Bochumer Straße": STRASSE}))
    assert v.stufe == "strasse" and v.osm_id == "2"


def test_haus_verlangt_gleiche_nummer():
    falsch = [dict(HAUS[0], address={"house_number": "7", "road": "Bochumer Straße", "suburb": "Steele"})]
    v = geo(FakeClient({"5 Bochumer Straße": falsch, "Bochumer Straße": STRASSE}))
    assert v.stufe == "strasse"


def test_stadtteil_widerspruch_faellt_auf_offen():
    fremd = [dict(STRASSE[0], address={"road": "Bochumer Straße", "suburb": "Kray"})]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": fremd}))
    assert v.stufe == "offen" and v.grund == "stadtteil_widerspruch"


def test_mehrere_gleichnamige_strassen_ohne_stadtteil_offen():
    zwei = [STRASSE[0], dict(STRASSE[0], osm_id="3", address={"road": "Bochumer Straße", "suburb": "Kray"})]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": zwei}), stadtteil="")
    assert v.stufe == "offen" and v.grund == "mehrdeutig_strasse"


def test_mehrere_gleichnamige_mit_stadtteil_aufgeloest():
    zwei = [dict(STRASSE[0], osm_id="3", address={"road": "Bochumer Straße", "suburb": "Kray"}), STRASSE[0]]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": zwei}))
    assert v.stufe == "strasse" and v.osm_id == "2"


def test_zusatz_ignoriert():
    v = geo(FakeClient({"5a Bochumer Straße": [], "5 Bochumer Straße": HAUS}), hausnr_zusatz="a")
    assert v.stufe == "haus" and v.zusatz_ignoriert == "ja"


def test_kein_treffer():
    v = geo(FakeClient({}))
    assert v.stufe == "offen" and v.grund == "kein_treffer"


def test_strasse_offen_ohne_anfrage():
    c = FakeClient({})
    v = geo(c, strasse_heute="")
    assert v.stufe == "offen" and v.grund == "strasse_offen" and c.aufrufe == []


def test_ohne_nummer_mit_landmarke():
    lm = [{"muster": "börsenhaus", "lat": "51.4525", "lon": "7.0150", "name": "Haus der Technik", "quelle": "wikipedia"}]
    v = geo(FakeClient({}), strasse_heute="", hausnr="", parse_status="ohne_nummer", strasse_roh="Börsenhaus", landmarken=lm)
    assert (v.stufe, v.lat, v.display_name) == ("landmarke", "51.4525", "Haus der Technik")


def test_ohne_nummer_mit_strasse_gibt_strassenebene():
    v = geo(FakeClient({"Bochumer Straße": STRASSE}), hausnr="", parse_status="ohne_nummer")
    assert v.stufe == "strasse" and v.grund == "ohne_nummer"


def test_cache_roundtrip(tmp_path, monkeypatch):
    aufrufe = []

    def fake_get(url, params, timeout):
        aufrufe.append(params)
        class R:
            def raise_for_status(self): pass
            def json(self): return [{"lat": "1", "lon": "2"}]
        return R()
    monkeypatch.setattr(nm.requests, "get", fake_get)
    c = nm.Client("http://x", tmp_path / "cache.jsonl")
    assert c.suche({"street": "A", "city": "Essen"}) == [{"lat": "1", "lon": "2"}]
    assert c.suche({"street": "A", "city": "Essen"}) == [{"lat": "1", "lon": "2"}]
    c.schliessen()
    assert len(aufrufe) == 1
    c2 = nm.Client("http://x", tmp_path / "cache.jsonl")
    assert c2.suche({"city": "Essen", "street": "A"}) == [{"lat": "1", "lon": "2"}]
    assert len(aufrufe) == 1
    zeile = json.loads((tmp_path / "cache.jsonl").read_text().splitlines()[0])
    assert json.loads(zeile["k"])["v"] == nm.SCHEMA_VERSION
