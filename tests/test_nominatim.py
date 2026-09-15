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


def adr(**kw):
    """Adressblock einer OSM-Antwort; city=Essen ist die Voraussetzung jedes Treffers."""
    basis = {"road": "Bochumer Straße", "suburb": "Steele", "city": "Essen"}
    basis.update(kw)
    return {k: v for k, v in basis.items() if v is not None}


HAUS = [{"lat": "51.45", "lon": "7.01", "osm_type": "way", "osm_id": "1", "class": "building", "type": "yes",
         "display_name": "5, Bochumer Straße, Steele, Essen",
         "address": adr(house_number="5")}]
STRASSE = [{"lat": "51.46", "lon": "7.02", "osm_type": "way", "osm_id": "2", "class": "highway", "type": "residential",
            "display_name": "Bochumer Straße, Steele, Essen", "address": adr()}]


def geo(client, **kw):
    basis = dict(strasse_heute="Bochumer Straße", hausnr="5", hausnr_zusatz="", stadtteil="Steele",
                 parse_status="ok", strasse_roh="Bochumer Str.", landmarken=[])
    basis.update(kw)
    return nm.geokodiere(client, **basis)


def test_haus_treffer():
    v = geo(FakeClient({"5 Bochumer Straße": HAUS}))
    assert (v.stufe, v.lat, v.lon, v.osm_id, v.grund) == ("haus", "51.45", "7.01", "1", "")


def test_haus_verlangt_gleiche_strasse():
    falsch = [dict(HAUS[0], address=adr(house_number="5", road="Bochumer Platz"))]
    v = geo(FakeClient({"5 Bochumer Straße": falsch, "Bochumer Straße": STRASSE}))
    assert v.stufe == "strasse" and v.osm_id == "2"


def test_haus_verlangt_gleiche_nummer():
    falsch = [dict(HAUS[0], address=adr(house_number="7"))]
    v = geo(FakeClient({"5 Bochumer Straße": falsch, "Bochumer Straße": STRASSE}))
    assert v.stufe == "strasse"


def test_stadtteil_widerspruch_faellt_auf_offen():
    fremd = [dict(STRASSE[0], address=adr(suburb="Kray"))]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": fremd}))
    assert v.stufe == "offen" and v.grund == "stadtteil_widerspruch"


def test_mehrere_gleichnamige_strassen_ohne_stadtteil_offen():
    zwei = [STRASSE[0], dict(STRASSE[0], osm_id="3", address=adr(suburb="Kray"))]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": zwei}), stadtteil="")
    assert v.stufe == "offen" and v.grund == "mehrdeutig_strasse"


def test_mehrere_gleichnamige_mit_stadtteil_aufgeloest():
    zwei = [dict(STRASSE[0], osm_id="3", address=adr(suburb="Kray")), STRASSE[0]]
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


def test_haus_treffer_ueber_neighbourhood():
    treffer = [dict(HAUS[0], address=adr(house_number="5", neighbourhood="Steele", suburb="Altenessen"))]
    v = geo(FakeClient({"5 Bochumer Straße": treffer}), stadtteil="Steele")
    assert v.stufe == "haus"


def test_kettwig_ohne_stadtteil_wird_abgelehnt():
    kettwig = [dict(STRASSE[0], address=adr(suburb="Kettwig vor der Brücke"))]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": kettwig}), stadtteil="")
    assert v.stufe == "offen" and v.grund == "kein_treffer"


def test_kettwig_auch_mit_stadtteil_nicht_akzeptiert():
    """Kettwig gehörte 1936 nicht zu Essen — auch eine Dickhoff-Liste mit Kettwig
    darf den Kettwiger Abschnitt nicht legitimieren; das Nicht-Kettwig-Segment
    derselben Straße wird bevorzugt."""
    zwei = [dict(STRASSE[0], osm_id="7", address=adr(suburb="Kettwig vor der Brücke")),
            dict(STRASSE[0], osm_id="8", address=adr(suburb="Werden"))]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": zwei}), stadtteil="Kettwig; Werden")
    assert v.stufe == "strasse" and v.osm_id == "8"


def test_kettwig_allein_bleibt_widerspruch_trotz_liste():
    kettwig = [dict(STRASSE[0], address=adr(suburb="Kettwig vor der Brücke"))]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": kettwig}), stadtteil="Kettwig; Werden")
    assert v.stufe == "offen" and v.grund == "stadtteil_widerspruch"


def test_burgaltendorf_ist_widerspruch():
    burg = [dict(STRASSE[0], address=adr(suburb="Burgaltendorf"))]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": burg}), stadtteil="Burgaltendorf")
    assert v.stufe == "offen" and v.grund == "stadtteil_widerspruch"


def test_zusatz_gross_matcht_osm_klein():
    mit = [dict(HAUS[0], address=adr(house_number="5A"))]
    v = geo(FakeClient({"5a Bochumer Straße": mit}), hausnr_zusatz="A")
    assert v.stufe == "haus" and v.zusatz_ignoriert == "nein"


# --- Fixes aus dem Gesamt-Review 2026-09-15 ---------------------------------


def test_fremde_stadt_wird_verworfen_hausebene():
    """address.city muss Essen sein: ein Gelsenkirchener Treffer zählt nicht."""
    fremd = [dict(HAUS[0], address=adr(house_number="5", suburb="Rotthausen", city="Gelsenkirchen"))]
    v = geo(FakeClient({"5 Bochumer Straße": fremd}), stadtteil="")
    assert v.stufe == "offen" and v.grund == "kein_treffer"


def test_fremde_stadt_wird_verworfen_strassenebene():
    fremd = [dict(STRASSE[0], address=adr(suburb="Rotthausen", city="Gelsenkirchen"))]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": fremd}), stadtteil="")
    assert v.stufe == "offen" and v.grund == "kein_treffer"


def test_town_essen_gilt_auch():
    treffer = [dict(HAUS[0], address=adr(house_number="5", city=None, town="Essen"))]
    v = geo(FakeClient({"5 Bochumer Straße": treffer}))
    assert v.stufe == "haus"


def test_ohne_stadtfeld_wird_verworfen():
    ohne = [dict(HAUS[0], address=adr(house_number="5", city=None))]
    v = geo(FakeClient({"5 Bochumer Straße": ohne}), stadtteil="")
    assert v.stufe == "offen" and v.grund == "kein_treffer"


def test_ortsteil_vor_bindestrich_passt():
    """OSM nennt oft nur "Altenessen", Dickhoff "Altenessen-Nord"."""
    treffer = [dict(HAUS[0], address=adr(house_number="5", suburb="Altenessen"))]
    v = geo(FakeClient({"5 Bochumer Straße": treffer}), stadtteil="Altenessen-Nord; Altenessen-Süd")
    assert v.stufe == "haus"


def test_village_und_hamlet_sind_ortsfelder():
    """Schuir erscheint in OSM als village, nicht als suburb."""
    treffer = [dict(HAUS[0], address=adr(house_number="5", suburb=None, village="Schuir"))]
    v = geo(FakeClient({"5 Bochumer Straße": treffer}), stadtteil="Schuir; Bredeney")
    assert v.stufe == "haus"


def test_treffer_ohne_ortsfeld_ist_widerspruch():
    """Bekannter Stadtteil, aber die Antwort nennt keinen Ort → nicht still akzeptieren."""
    ohne = [dict(STRASSE[0], address=adr(suburb=None))]
    v = geo(FakeClient({"5 Bochumer Straße": [], "Bochumer Straße": ohne}), stadtteil="Steele")
    assert v.stufe == "offen" and v.grund == "stadtteil_widerspruch"


def test_treffer_ohne_ortsfeld_ohne_stadtteil_bleibt_ok():
    ohne = [dict(HAUS[0], address=adr(house_number="5", suburb=None))]
    v = geo(FakeClient({"5 Bochumer Straße": ohne}), stadtteil="")
    assert v.stufe == "haus"


def test_zusatz_erstpass_akzeptiert_nur_mit_zusatz():
    """Erster Pass mit Zusatz "a" darf die nackte Hausnummer 5 nicht als Treffer nehmen."""
    c = FakeClient({"5a Bochumer Straße": HAUS, "5 Bochumer Straße": HAUS})
    v = geo(c, hausnr_zusatz="a")
    assert v.stufe == "haus" and v.zusatz_ignoriert == "ja"
    assert [a["street"] for a in c.aufrufe] == ["5a Bochumer Straße", "5 Bochumer Straße"]


def test_zweitpass_akzeptiert_keinen_fremden_zusatz():
    """Ohne Zusatz zählt nur die nackte Nummer, nicht "5b"."""
    fremd = [dict(HAUS[0], address=adr(house_number="5b"))]
    v = geo(FakeClient({"5 Bochumer Straße": fremd}), stadtteil="")
    assert v.stufe == "offen" and v.grund == "kein_treffer"


def test_landmarke_nur_als_ganzes_wort():
    """"post" darf nicht in "Postneubau" greifen."""
    lm = [{"muster": "post", "lat": "51.4", "lon": "7.0", "name": "Hauptpost", "quelle": "x"}]
    v = geo(FakeClient({}), strasse_heute="", hausnr="", parse_status="ohne_nummer",
            strasse_roh="1. Postneubau a. Hbf.", landmarken=lm)
    assert v.stufe == "offen" and v.grund == "ohne_nummer"


def test_landmarke_greift_bei_ganzem_wort():
    lm = [{"muster": "hauptbahnhof", "lat": "51.4", "lon": "7.0", "name": "Hauptbahnhof", "quelle": "x"}]
    v = geo(FakeClient({}), strasse_heute="", hausnr="", parse_status="ohne_nummer",
            strasse_roh="Am Hauptbahnhof", landmarken=lm)
    assert v.stufe == "landmarke"


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


def test_cache_schluessel_enthaelt_basis(tmp_path, monkeypatch):
    """Ändern sich die Basisparameter (z. B. limit), wird der alte Cache ungültig."""
    monkeypatch.setattr(nm.requests, "get", lambda *a, **k: None)
    c = nm.Client("http://x", tmp_path / "cache.jsonl")
    schluessel = json.loads(c._schluessel({"street": "A", "city": "Essen"}))
    c.schliessen()
    for feld, wert in nm.BASIS.items():
        assert schluessel[feld] == wert
