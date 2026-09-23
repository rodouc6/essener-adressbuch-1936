"""Kleiner Server für Kontrollkarte und Prüfwerkzeug.

    python3 werkzeuge/serve.py [port]   → http://localhost:8765/werkzeuge/pruefung.html

Liefert das Projektverzeichnis statisch aus und nimmt entgegen:

- POST /speichern/stichprobe_<name>.csv — die geprüfte Stichprobe als JSON ({"zeilen": [...]}).
  Geschrieben wird docs/stichprobe_<name>.csv mit den Spalten aus werkzeuge/stichprobe.py;
  `urteil` muss leer oder aus dem Vokabular von docs/stichprobe.md sein, sonst 400.
- POST /kuratierung/strassen_1935.csv — eine Zeile ({"zeile": {...}}) für die Punkte vom
  Stadtplan 1935; ersetzt eine vorhandene Zeile mit gleichem (strasse_roh_norm, vorort).
- POST /kuratierung/strassen_zuordnung.csv — eine Zeile für die Straßenzuordnung; ersetzt eine
  vorhandene Zeile mit gleichem (strasse_roh_norm, vorort, hausnr_von, hausnr_bis). Mit
  {"loesche_stadtplan": true} wird die Stadtplan-Zeile desselben Schlüssels entfernt.
  Mit {"loeschen": true} entfernt jeder der beiden Endpunkte die Zeile mit dem Schlüssel der
  übergebenen Zeile (Rücknahme einer Sichtung; Zeilen mit Hausnummernbereich nie).
- POST /kuratierung/eigentuemer.csv — mehrere Zeilen ({"zeilen": [...]}) der Eigentümer-Kuratierung;
  ersetzt nach Schlüssel `schreibweise`, setzt bearbeiter=christos und datum. 400 bei unbekannter
  Kategorie, leerem eigentuemer, geprueft ∉ {ja, leer}, unbekannter Schreibweise oder geprueft=ja
  ohne Kategorie.
- GET /reverse?lat=&lon= — Reverse-Geocoding über das lokale Nominatim (NOMINATIM_URL),
  liefert dessen JSON-Antwort weiter (Stadtteil-Vorschlag im Sichtungswerkzeug).
- GET mit Range-Header — Teilstücke für PMTiles (site/daten/adressen.pmtiles).
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import re
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.lib.eigentuemer import FELDER_KURATIERUNG, IDENTITAETEN, KATEGORIEN, lade_kuratierung
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv

FELDER = ["stufe", "strasse_roh", "hausnr", "hausnr_zusatz", "stadtteil", "strasse_heute",
          "display_name", "lat", "lon", "urteil", "bemerkung", "gruppe"]
URTEILE = {"", "richtig", "falsche_strasse", "falsche_nummer", "falscher_stadtteil", "unklar"}
_ZIEL = re.compile(r"^/speichern/(stichprobe_[A-Za-z0-9_-]+\.csv)$")
_KURATIERUNG = re.compile(r"^/kuratierung/(strassen_1935|strassen_zuordnung)\.csv$")

# Grober Rahmen um das Stadtgebiet: ein Klick außerhalb ist ein Versehen, kein Beleg.
ESSEN_RAHMEN = ((51.30, 51.58), (6.85, 7.20))
BEFUNDE = {"punkt", "nicht_gefunden"}
SCHLUESSEL_1935 = ("strasse_roh_norm", "vorort")
SCHLUESSEL_ZUORDNUNG = ("strasse_roh_norm", "vorort", "hausnr_von", "hausnr_bis")


def _in_essen(lat: str, lon: str) -> bool:
    try:
        la, lo = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    return ESSEN_RAHMEN[0][0] <= la <= ESSEN_RAHMEN[0][1] and ESSEN_RAHMEN[1][0] <= lo <= ESSEN_RAHMEN[1][1]


def pruefe_zeile(tabelle: str, z: dict) -> str:
    """Prüft eine Kuratierungszeile; gibt die Fehlermeldung zurück oder "" wenn in Ordnung."""
    if not isinstance(z, dict):
        return "Zeile fehlt"
    if not str(z.get("strasse_roh_norm", "")).strip() or not str(z.get("vorort", "")).strip():
        return "strasse_roh_norm und vorort sind Pflicht"
    if not str(z.get("beleg", z.get("bemerkung", ""))).strip() and tabelle == "strassen_zuordnung":
        return "beleg ist Pflicht"
    if tabelle == "strassen_1935":
        befund = str(z.get("befund", "")).strip()
        if befund not in BEFUNDE:
            return f"unbekannter befund: {befund!r}"
        if befund == "punkt" and not _in_essen(z.get("lat"), z.get("lon")):
            return "Koordinate fehlt oder liegt außerhalb Essens"
    else:
        if not str(z.get("strasse_heute", "")).strip() or not re.fullmatch(r"\d{5}", str(z.get("schl_nr", ""))):
            return "strasse_heute und fünfstellige schl_nr sind Pflicht"
    return ""


def upsert(pfad: pathlib.Path, zeile: dict, schluessel: tuple[str, ...]) -> int:
    """Ersetzt die Zeile mit gleichem Schlüssel oder hängt an; Spalten aus der Kopfzeile. Gibt die Zeilenzahl zurück."""
    zeilen = lies_csv(pfad)
    with open(pfad, encoding="utf-8", newline="") as f:
        felder = f.readline().rstrip("\r\n").split(",")
    k = tuple(str(zeile.get(f, "")).strip() for f in schluessel)
    zeilen = [z for z in zeilen if tuple(z.get(f, "").strip() for f in schluessel) != k]
    zeilen.append({f: str(zeile.get(f, "")).strip() for f in felder})
    schreib_csv(pfad, zeilen, felder)
    return len(zeilen)


def loesche(pfad: pathlib.Path, zeile: dict, schluessel: tuple[str, ...]) -> int:
    """Entfernt alle Zeilen mit dem Schlüssel der übergebenen Zeile. Gibt die Zahl der entfernten zurück."""
    if not pfad.exists():
        return 0
    zeilen = lies_csv(pfad)
    with open(pfad, encoding="utf-8", newline="") as f:
        felder = f.readline().rstrip("\r\n").split(",")
    k = tuple(str(zeile.get(f, "")).strip() for f in schluessel)
    rest = [z for z in zeilen if tuple(z.get(f, "").strip() for f in schluessel) != k]
    if len(rest) != len(zeilen):
        schreib_csv(pfad, rest, felder)
    return len(zeilen) - len(rest)


def pruefe_eigentuemer(z: dict, bekannt: set[str]) -> str:
    if not isinstance(z, dict):
        return "Zeile fehlt"
    s = str(z.get("schreibweise", "")).strip()
    if s not in bekannt:
        return f"unbekannte Schreibweise: {s}"
    if not str(z.get("eigentuemer", "")).strip():
        return "eigentuemer ist Pflicht"
    kat = str(z.get("kategorie", "")).strip()
    if kat and kat not in KATEGORIEN:
        return f"unbekannte Kategorie: {kat}"
    if str(z.get("geprueft", "")).strip() not in ("", "ja"):
        return "geprueft muss ja oder leer sein"
    if str(z.get("identitaet", "")).strip() not in IDENTITAETEN:
        return "identitaet muss sicher oder leer sein"
    if str(z.get("geprueft", "")).strip() == "ja" and not kat:
        return "geprueft=ja verlangt eine Kategorie"
    return ""


def upsert_viele(pfad: pathlib.Path, zeilen: list[dict], schluessel: str, felder: list[str]) -> int:
    """Ersetzt je Schlüsselwert die vorhandene Zeile an Ort und Stelle (Reihenfolge bleibt), hängt Neues an."""
    alt = lies_csv(pfad)
    index = {z[schluessel].strip(): i for i, z in enumerate(alt)}
    for z in zeilen:
        neu = {f: str(z.get(f, "")).strip() for f in felder}
        k = neu[schluessel]
        if k in index:
            alt[index[k]] = neu
        else:
            index[k] = len(alt); alt.append(neu)
    schreib_csv(pfad, alt, felder)
    return len(alt)


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

    def _json(self, code: int, daten) -> None:
        roh = json.dumps(daten, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)

    _RANGE = re.compile(r"^(\d*)-(\d*)$")

    def _range(self, pfad: str, spez: str) -> None:
        """Beantwortet einen Range-Request (pmtiles.js liest Kacheln stückweise)."""
        datei = pathlib.Path(self.translate_path(pfad))
        m = self._RANGE.match(spez)
        if not datei.is_file() or not m or (m.group(1) == "" and m.group(2) == ""):
            return self._antwort(416, "ungültiger Range")
        groesse = datei.stat().st_size
        if m.group(1) == "":                       # bytes=-N → letzte N Bytes
            start, ende = max(groesse - int(m.group(2)), 0), groesse - 1
        else:
            start = int(m.group(1))
            ende = int(m.group(2)) if m.group(2) else groesse - 1
        ende = min(ende, groesse - 1)
        if start > ende:
            return self._antwort(416, "Range außerhalb der Datei")
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(str(datei)))
        self.send_header("Content-Range", f"bytes {start}-{ende}/{groesse}")
        self.send_header("Content-Length", str(ende - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with open(datei, "rb") as f:
            f.seek(start)
            self.wfile.write(f.read(ende - start + 1))

    def do_GET(self) -> None:
        url = urllib.parse.urlparse(self.path)
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes=") and url.path != "/reverse":
            return self._range(url.path, rng[6:])
        if url.path != "/reverse":
            return super().do_GET()
        q = urllib.parse.parse_qs(url.query)
        lat, lon = q.get("lat", [""])[0], q.get("lon", [""])[0]
        if not _in_essen(lat, lon):
            return self._antwort(400, "lat/lon fehlen oder liegen außerhalb Essens")
        basis = os.environ.get("NOMINATIM_URL", "http://localhost:8080").rstrip("/")
        try:
            r = requests.get(f"{basis}/reverse", params={"format": "json", "lat": lat, "lon": lon,
                                                         "zoom": "16", "addressdetails": "1"}, timeout=5)
            r.raise_for_status()
            return self._json(200, r.json())
        except (requests.RequestException, ValueError) as e:
            return self._antwort(502, f"Nominatim nicht erreichbar: {e}")

    def do_POST(self) -> None:
        if self.path == "/kuratierung/eigentuemer.csv":
            return self._eigentuemer()
        k = _KURATIERUNG.match(self.path)
        if k:
            return self._kuratierung(k.group(1))
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

    def _kuratierung(self, tabelle: str) -> None:
        try:
            koerper = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            zeile = koerper["zeile"]
        except (ValueError, KeyError, TypeError):
            return self._antwort(400, "ungültiger Inhalt")
        pfad = self.wurzel / "kuratierung" / f"{tabelle}.csv"
        if not pfad.exists():
            return self._antwort(404, f"{tabelle}.csv fehlt")
        if koerper.get("loeschen"):
            # Rücknahme einer Sichtung: nur Zeilen ohne Hausnummernbereich (die schreibt das Werkzeug nie).
            if str(zeile.get("hausnr_von", "")).strip() or str(zeile.get("hausnr_bis", "")).strip():
                return self._antwort(400, "Bereichszeilen werden nur von Hand gelöscht")
            schl = SCHLUESSEL_1935 if tabelle == "strassen_1935" else SCHLUESSEL_ZUORDNUNG
            weg = loesche(pfad, {**zeile, "hausnr_von": "", "hausnr_bis": ""}, schl)
            return self._antwort(200 if weg else 404, f"{tabelle}.csv: {weg} Zeile(n) entfernt")
        fehler = pruefe_zeile(tabelle, zeile)
        if fehler:
            return self._antwort(400, fehler)
        if tabelle == "strassen_1935":
            n = upsert(pfad, zeile, SCHLUESSEL_1935)
            return self._antwort(200, f"{tabelle}.csv: {n} Zeilen")
        n = upsert(pfad, zeile, SCHLUESSEL_ZUORDNUNG)
        weg = 0
        if koerper.get("loesche_stadtplan"):
            weg = loesche(self.wurzel / "kuratierung" / "strassen_1935.csv", zeile, SCHLUESSEL_1935)
        return self._antwort(200, f"{tabelle}.csv: {n} Zeilen" + (f", {weg} Stadtplan-Zeile(n) entfernt" if weg else ""))

    def _eigentuemer(self) -> None:
        try:
            koerper = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            zeilen = koerper["zeilen"]
            assert isinstance(zeilen, list)
        except (ValueError, KeyError, TypeError, AssertionError):
            return self._antwort(400, "ungültiger Inhalt")
        pfad = self.wurzel / "kuratierung" / "eigentuemer.csv"
        if not pfad.exists():
            return self._antwort(404, "eigentuemer.csv fehlt")
        bekannt = set(lade_kuratierung(lies_csv(pfad)))
        for z in zeilen:
            fehler = pruefe_eigentuemer(z, bekannt)
            if fehler:
                return self._antwort(400, fehler)
        heute = datetime.date.today().isoformat()
        n = upsert_viele(pfad, [{**z, "bearbeiter": "christos", "datum": heute} for z in zeilen], "schreibweise", FELDER_KURATIERUNG)
        self._antwort(200, f"eigentuemer.csv: {n} Zeilen")

    def log_message(self, fmt, *args):  # nur Speichervorgänge und Fehler ins Terminal
        if self.command == "POST" or (len(args) > 1 and not str(args[1]).startswith(("2", "3"))):
            super().log_message(fmt, *args)


def main(port: int) -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"http://localhost:{port}/werkzeuge/pruefung.html  ·  /werkzeuge/sichtung.html  ·  /werkzeuge/eigentuemer.html  (Strg+C beendet)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
