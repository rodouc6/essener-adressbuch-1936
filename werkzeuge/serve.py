"""Kleiner Server für Kontrollkarte und Prüfwerkzeug.

    python3 werkzeuge/serve.py [port]   → http://localhost:8765/werkzeuge/pruefung.html

Liefert das Projektverzeichnis statisch aus und nimmt unter
POST /speichern/stichprobe_<seed>.csv die geprüfte Stichprobe als JSON
({"zeilen": [...]}) entgegen. Geschrieben wird docs/stichprobe_<seed>.csv mit den
Spalten aus werkzeuge/stichprobe.py; `urteil` muss leer oder aus dem Vokabular
von docs/stichprobe.md sein, sonst wird nichts geschrieben (400).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.lib.io import projektwurzel, schreib_csv

FELDER = ["stufe", "strasse_roh", "hausnr", "hausnr_zusatz", "stadtteil", "strasse_heute",
          "display_name", "lat", "lon", "urteil", "bemerkung"]
URTEILE = {"", "richtig", "falsche_strasse", "falsche_nummer", "falscher_stadtteil", "unklar"}
_ZIEL = re.compile(r"^/speichern/(stichprobe_\d+\.csv)$")


class Handler(SimpleHTTPRequestHandler):
    wurzel: pathlib.Path = projektwurzel()

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(self.wurzel), **kw)

    def _antwort(self, code: int, text: str) -> None:
        daten = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(daten)))
        self.end_headers()
        self.wfile.write(daten)

    def do_POST(self) -> None:
        m = _ZIEL.match(self.path)
        if not m:
            return self._antwort(404, "unbekanntes Ziel")
        try:
            koerper = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            zeilen = koerper["zeilen"]
            fremd = sorted({z.get("urteil", "") for z in zeilen} - URTEILE)
        except (ValueError, KeyError, TypeError, AttributeError):
            return self._antwort(400, "ungültiger Inhalt")
        if fremd:
            return self._antwort(400, f"unbekanntes Urteil: {', '.join(fremd)}")
        schreib_csv(self.wurzel / "docs" / m.group(1), zeilen, FELDER)
        self._antwort(200, f"{len(zeilen)} Zeilen gespeichert")

    def log_message(self, fmt, *args):  # nur Speichervorgänge und Fehler ins Terminal
        if self.command == "POST" or (len(args) > 1 and not str(args[1]).startswith(("2", "3"))):
            super().log_message(fmt, *args)


def main(port: int) -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"http://localhost:{port}/werkzeuge/pruefung.html  (Strg+C beendet)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
