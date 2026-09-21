import pathlib, threading, urllib.request
from http.server import ThreadingHTTPServer

import pytest

import werkzeuge.serve as serve


@pytest.fixture
def server(tmp_path):
    (tmp_path / "k.bin").write_bytes(bytes(range(256)))

    class H(serve.Handler):
        wurzel = tmp_path

    s = ThreadingHTTPServer(("127.0.0.1", 0), H)
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{s.server_address[1]}"
    s.shutdown()


def test_range_liefert_teilstueck(server):
    req = urllib.request.Request(server + "/k.bin", headers={"Range": "bytes=10-19"})
    with urllib.request.urlopen(req) as r:
        assert r.status == 206
        assert r.headers["Content-Range"] == "bytes 10-19/256"
        assert r.headers["Accept-Ranges"] == "bytes"
        assert r.read() == bytes(range(10, 20))


def test_range_offenes_ende(server):
    req = urllib.request.Request(server + "/k.bin", headers={"Range": "bytes=250-"})
    with urllib.request.urlopen(req) as r:
        assert r.status == 206 and r.read() == bytes(range(250, 256))


def test_ohne_range_ganze_datei(server):
    with urllib.request.urlopen(server + "/k.bin") as r:
        assert r.status == 200 and len(r.read()) == 256
