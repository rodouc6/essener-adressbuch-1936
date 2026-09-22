import csv
import json
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

import pytest

from werkzeuge.serve import Handler, FELDER

KOPF = ["stufe", "strasse_roh", "hausnr", "hausnr_zusatz", "stadtteil", "strasse_heute",
        "display_name", "lat", "lon", "urteil", "bemerkung", "gruppe"]


KOPF_1935 = "strasse_roh_norm,vorort,befund,lat,lon,name_im_plan,stadtteil,bemerkung,bearbeiter,datum"
KOPF_ZUORDNUNG = "strasse_roh_norm,vorort,strasse_heute,schl_nr,hausnr_von,hausnr_bis,nummer_unsicher,beleg,bearbeiter,datum"
KOPF_EIGENTUEMER = "schreibweise,art,eigentuemer,kategorie,geprueft,bearbeiter,datum,hinweis"


@pytest.fixture
def server(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "kuratierung").mkdir()
    (tmp_path / "kuratierung" / "strassen_1935.csv").write_text(KOPF_1935 + "\n", encoding="utf-8")
    (tmp_path / "kuratierung" / "strassen_zuordnung.csv").write_text(
        KOPF_ZUORDNUNG + "\n" + 'x,Kray,Y,00001,1,9,nein,"Bereich, bleibt",T,2026-09-15\n', encoding="utf-8")
    (tmp_path / "kuratierung" / "eigentuemer.csv").write_text(
        KOPF_EIGENTUEMER + "\nStadt Essen,koerperschaft,Stadt Essen,stadt_staat,,eigentuemer_cluster,2026-09-22,\n"
        "Fried. Krupp A.G.,koerperschaft,Fried. Krupp AG,,,eigentuemer_cluster,2026-09-22,\n"
        "Fried. Krupp AG.,koerperschaft,Fried. Krupp AG,,,eigentuemer_cluster,2026-09-22,\n", encoding="utf-8")
    ziel = tmp_path / "docs" / "stichprobe_7.csv"
    with open(ziel, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=KOPF, lineterminator="\n")
        w.writeheader()
        w.writerow(dict.fromkeys(KOPF, "") | {"stufe": "haus", "hausnr": "1", "lat": "51.4", "lon": "7.0"})
    Handler.wurzel = tmp_path
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", ziel
    srv.shutdown()
    srv.server_close()


def post(url, daten):
    req = urllib.request.Request(url, data=json.dumps(daten).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req)


def test_get_liefert_statische_datei(server):
    url, ziel = server
    with urllib.request.urlopen(url + "/docs/stichprobe_7.csv") as r:
        assert r.status == 200 and r.read().decode().startswith("stufe,strasse_roh")


def test_post_schreibt_urteile_ohne_spaltenverlust(server):
    url, ziel = server
    zeile = dict.fromkeys(KOPF, "") | {"stufe": "haus", "hausnr": "1", "lat": "51.4", "lon": "7.0",
                                       "urteil": "falsche_nummer", "bemerkung": "Nr. 3 lag hier"}
    with post(url + "/speichern/stichprobe_7.csv", {"zeilen": [zeile]}) as r:
        assert r.status == 200
    with open(ziel, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0].keys()) == KOPF
    assert rows[0]["urteil"] == "falsche_nummer" and rows[0]["bemerkung"] == "Nr. 3 lag hier"
    assert rows[0]["lat"] == "51.4"


def test_post_lehnt_unbekanntes_urteil_ab(server):
    url, ziel = server
    zeile = dict.fromkeys(KOPF, "") | {"urteil": "vielleicht"}
    with pytest.raises(urllib.error.HTTPError) as e:
        post(url + "/speichern/stichprobe_7.csv", {"zeilen": [zeile]})
    assert e.value.code == 400
    assert "stufe,strasse_roh" in ziel.read_text(encoding="utf-8")  # unverändert


def test_post_lehnt_fremden_dateinamen_ab(server):
    url, ziel = server
    with pytest.raises(urllib.error.HTTPError) as e:
        post(url + "/speichern/../pyproject.toml", {"zeilen": []})
    assert e.value.code in (400, 404)


def lies(pfad):
    with open(pfad, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_stadtplan_zeile_wird_angefuegt_und_ersetzt(server):
    url, ziel = server
    pfad = ziel.parent.parent / "kuratierung" / "strassen_1935.csv"
    z = {"strasse_roh_norm": "stadtwiese", "vorort": "Kernstadt", "befund": "punkt", "lat": "51.46", "lon": "7.01",
         "name_im_plan": "Stadtwiese", "stadtteil": "Stadtkern", "bemerkung": "", "bearbeiter": "T", "datum": "2026-09-16"}
    with post(url + "/kuratierung/strassen_1935.csv", {"zeile": z}) as r:
        assert r.status == 200
    with post(url + "/kuratierung/strassen_1935.csv", {"zeile": dict(z, lat="51.47", fremd="x")}) as r:
        assert r.status == 200
    rows = lies(pfad)
    assert len(rows) == 1 and rows[0]["lat"] == "51.47" and list(rows[0]) == KOPF_1935.split(",")


def test_stadtplan_lehnt_befund_und_koordinate_ab(server):
    url, ziel = server
    basis = {"strasse_roh_norm": "a", "vorort": "Kernstadt", "bearbeiter": "T", "datum": "2026-09-16"}
    for z in (dict(basis, befund="vielleicht"), dict(basis, befund="punkt", lat="52.5", lon="13.4"),
              dict(basis, befund="punkt", lat="", lon=""), dict(basis, vorort="", befund="nicht_gefunden")):
        with pytest.raises(urllib.error.HTTPError) as e:
            post(url + "/kuratierung/strassen_1935.csv", {"zeile": z})
        assert e.value.code == 400
    with post(url + "/kuratierung/strassen_1935.csv", {"zeile": dict(basis, befund="nicht_gefunden")}) as r:
        assert r.status == 200


def test_zuordnung_wird_angefuegt_und_entfernt_stadtplanzeile(server):
    url, ziel = server
    kur = ziel.parent.parent / "kuratierung"
    (kur / "strassen_1935.csv").write_text(KOPF_1935 + "\nprovinzialstraße,Kernstadt,nicht_gefunden,,,,,,T,2026-09-16\n", encoding="utf-8")
    z = {"strasse_roh_norm": "provinzialstraße", "vorort": "Kernstadt", "strasse_heute": "Gelsenkirchener Straße",
         "schl_nr": "01004", "beleg": "Stadtplan 1935 zeigt den Namen", "bearbeiter": "T", "datum": "2026-09-16"}
    with pytest.raises(urllib.error.HTTPError) as e:
        post(url + "/kuratierung/strassen_zuordnung.csv", {"zeile": dict(z, schl_nr="1004")})
    assert e.value.code == 400
    with post(url + "/kuratierung/strassen_zuordnung.csv", {"zeile": z, "loesche_stadtplan": True}) as r:
        assert r.status == 200
    rows = lies(kur / "strassen_zuordnung.csv")
    assert [r["strasse_roh_norm"] for r in rows] == ["x", "provinzialstraße"]
    assert rows[0]["beleg"] == "Bereich, bleibt" and rows[1]["hausnr_von"] == ""
    assert lies(kur / "strassen_1935.csv") == []


def test_reverse_proxy(server, monkeypatch):
    url, ziel = server
    import werkzeuge.serve as sv

    class R:
        def raise_for_status(self): pass
        def json(self): return {"address": {"suburb": "Stadtkern"}}

    monkeypatch.setattr(sv.requests, "get", lambda *a, **kw: R())
    with urllib.request.urlopen(url + "/reverse?lat=51.45&lon=7.01") as r:
        assert json.loads(r.read())["address"]["suburb"] == "Stadtkern"
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(url + "/reverse?lat=1&lon=2")
    assert e.value.code == 400


def test_loeschen_nimmt_sichtung_zurueck_aber_keine_bereichszeile(server):
    url, ziel = server
    kur = ziel.parent.parent / "kuratierung"
    z = {"strasse_roh_norm": "kortstraße", "vorort": "Kray", "strasse_heute": "Korthover Weg", "schl_nr": "01792",
         "beleg": "Versehen", "bearbeiter": "T", "datum": "2026-09-17"}
    with post(url + "/kuratierung/strassen_zuordnung.csv", {"zeile": z}) as r:
        assert r.status == 200
    with post(url + "/kuratierung/strassen_zuordnung.csv", {"zeile": {"strasse_roh_norm": "kortstraße", "vorort": "Kray"}, "loeschen": True}) as r:
        assert r.status == 200
    assert [r["strasse_roh_norm"] for r in lies(kur / "strassen_zuordnung.csv")] == ["x"]
    with pytest.raises(urllib.error.HTTPError) as e:   # Bereichszeile x/Kray 1–9 bleibt
        post(url + "/kuratierung/strassen_zuordnung.csv", {"zeile": {"strasse_roh_norm": "x", "vorort": "Kray", "hausnr_von": "1", "hausnr_bis": "9"}, "loeschen": True})
    assert e.value.code == 400
    with pytest.raises(urllib.error.HTTPError) as e:   # ohne Bereich trifft der Schlüssel die Bereichszeile nicht
        post(url + "/kuratierung/strassen_zuordnung.csv", {"zeile": {"strasse_roh_norm": "x", "vorort": "Kray"}, "loeschen": True})
    assert e.value.code == 404 and len(lies(kur / "strassen_zuordnung.csv")) == 1


def test_eigentuemer_post_ersetzt_nach_schluessel(server):
    url, _ = server
    wurzel = Handler.wurzel
    zeilen = [dict(schreibweise="Fried. Krupp A.G.", art="koerperschaft", eigentuemer="Fried. Krupp AG", kategorie="industrie", geprueft="ja", hinweis=""),
              dict(schreibweise="Fried. Krupp AG.", art="koerperschaft", eigentuemer="Fried. Krupp AG", kategorie="industrie", geprueft="", hinweis="Punkt")]
    with post(url + "/kuratierung/eigentuemer.csv", {"zeilen": zeilen}) as r:
        assert r.status == 200 and r.read().decode() == "eigentuemer.csv: 3 Zeilen"
    rows = {z["schreibweise"]: z for z in csv.DictReader(open(wurzel / "kuratierung" / "eigentuemer.csv", encoding="utf-8", newline=""))}
    assert rows["Fried. Krupp A.G."]["bearbeiter"] == "christos" and len(rows["Fried. Krupp A.G."]["datum"]) == 10
    assert rows["Fried. Krupp A.G."]["geprueft"] == "ja" and rows["Stadt Essen"]["eigentuemer"] == "Stadt Essen"
    assert rows["Fried. Krupp AG."]["hinweis"] == "Punkt"


def test_eigentuemer_post_validiert(server):
    url, _ = server
    def fehler(zeile):
        with pytest.raises(urllib.error.HTTPError) as e:
            post(url + "/kuratierung/eigentuemer.csv", {"zeilen": [zeile]})
        return e.value.code, e.value.read().decode()
    basis = dict(schreibweise="Stadt Essen", art="koerperschaft", eigentuemer="Stadt Essen", kategorie="stadt_staat", geprueft="", hinweis="")
    assert fehler({**basis, "kategorie": "adel"}) == (400, "unbekannte Kategorie: adel")
    assert fehler({**basis, "eigentuemer": " "}) == (400, "eigentuemer ist Pflicht")
    assert fehler({**basis, "geprueft": "vielleicht"}) == (400, "geprueft muss ja oder leer sein")
    assert fehler({**basis, "schreibweise": "Gibt es nicht"}) == (400, "unbekannte Schreibweise: Gibt es nicht")
    with pytest.raises(urllib.error.HTTPError) as e:
        post(url + "/kuratierung/eigentuemer.csv", {"zeile": basis})
    assert e.value.code == 400
