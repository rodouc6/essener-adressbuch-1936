import csv
import json
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

import pytest

from werkzeuge.serve import Handler, FELDER

KOPF = ["stufe", "strasse_roh", "hausnr", "hausnr_zusatz", "stadtteil", "strasse_heute",
        "display_name", "lat", "lon", "urteil", "bemerkung"]


@pytest.fixture
def server(tmp_path):
    (tmp_path / "docs").mkdir()
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
