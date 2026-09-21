# Basiskarte (Teilprojekt 2) — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Statische, suchzentrierte Webkarte des Adressbuchs Essen 1936 (Teile I–III) mit Präzisionsstufe je Adresse, Sidebar/Bottom-Sheet, URL-Zustand, Themen-Mechanik und Zechen-Ebene.

**Architecture:** Eine neue Pipeline-Stufe 06 (`pipeline/06_karte_export.py`, Logik in `pipeline/lib/karte_export.py` und `pipeline/lib/merkmale.py`) erzeugt aus `build/eintraege.csv` ein Datenpaket unter `site/daten/` (PMTiles mit einem Punkt je Adresse, Eintrags-Scherben, Suchindex, Kennzahlen, Zechen, Themen). Das Frontend unter `site/` ist framework-frei (ES-Module, MapLibre GL, pmtiles.js lokal), alle Zustände liegen in der URL. Reine Logik (Schlüsselfaltung, URL-Zustand, Suche, CSV) sind DOM-freie Module mit `node --test`; die Seite wird mit Playwright geraucht.

**Tech Stack:** Python 3.12, pytest, tippecanoe 2.80, MapLibre GL JS 4.7.1, pmtiles.js 3.x, OpenFreeMap (positron/liberty), Node 20 (`node --test`), Playwright (Python) für Rauchtests.

**Spec:** `docs/superpowers/specs/2026-09-21-basiskarte-design.md`

## Global Constraints

- Sprache in Code-Kommentaren, Bezeichnern, Doku, Oberfläche: Deutsch mit korrekten Umlauten (wie in Stufen 01–05).
- Precision first: Präzisionsstufe (`haus` / `strasse` / `stadtplan`) an jeder Stelle sichtbar (Popup, Liste, Detail, Legende); keine Fuzzy-Suche; keine Punkte entlang von Straßen verteilen.
- Popup nur Basisinformationen; Seite und Faksimile nur in der Sidebar.
- Ein Punkt je Adresse; Ebenenfarbe nur bei genau einer aktiven Ebene (Einwohner `#1d4ed8`, Eigentümer `#ca8a04`, Gewerbe `#c2410c`), sonst neutral `#1f2937`.
- Keine CDN-Abhängigkeit: MapLibre und pmtiles.js unter `site/vendor/`.
- Grundkarte Positron Standard, Liberty umschaltbar; Stadtplan 1935 nur bei `PLAN_FREIGEGEBEN = true` in `site/js/konfig.js`, Abruf in EPSG:3857 (`bboxSR=3857&imageSR=3857`).
- Commits: Präfixe `feat:`/`fix:`/`docs:`/`test:` wie bisher, Abschluss `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- Tests laufen mit `python3 -m pytest -q` (Python) und `node --test site/tests/` (JS); beide müssen vor jedem Commit grün sein.
- Bestehende Helfer nutzen: `pipeline/lib/io.py` (`lies_csv`, `schreib_csv`, `projektwurzel`), `pipeline/lib/stufen.py` (`ADRESSSCHLUESSEL`).

---

## Dateistruktur

**Pipeline (Python)**

| Datei | Verantwortung |
|---|---|
| `pipeline/lib/merkmale.py` | Merkmalstabellen laden, Merkmale je Eintrag bestimmen |
| `pipeline/lib/karte_export.py` | Adress-ID, Schlüsselfaltung, Etagensortierung, Adresspunkte, Scherben, Suchindex, Kennzahlen, Zechen-GeoJSON, tippecanoe-Aufruf |
| `pipeline/06_karte_export.py` | Orchestrierung: liest `build/eintraege.csv`, schreibt `site/daten/` |
| `werkzeuge/serve.py` | zusätzlich HTTP-Range-Requests (PMTiles) |
| `werkzeuge/zechen_wikipedia.py` | einmaliger Abruf der Wikipedia-Zechenliste → `kuratierung/zechen.csv` |
| `kuratierung/merkmale/akademiker.csv` | Titelliste für das erste Thema (Freigabe durch Projektleiter) |
| `kuratierung/zechen.csv` | geprüfte Zechen mit Koordinaten und Betriebsjahren |
| `tests/test_merkmale.py`, `tests/test_karte_export.py`, `tests/test_serve_range.py` | Tests |

**Frontend (`site/`)**

| Datei | Verantwortung |
|---|---|
| `index.html`, `karte.html`, `ueber.html`, `impressum.html` | Seiten |
| `css/stil.css` | Layout Sidebar/Sheet, Pills, Listen, Popup, Legende |
| `js/konfig.js` | Konstanten: Stil-URLs, Farben, `PLAN_FREIGEGEBEN`, Stadtplan-URL |
| `js/schluessel.js` | `falte(text)` (Spiegel von Python), `praefix2(text)` |
| `js/zustand.js` | URL-Zustand: `liesZustand(search)`, `schreibeZustand(z)`, Standardwerte |
| `js/daten.js` | Laden und Cachen von Scherben, Indexdateien, Kennzahlen, Themen |
| `js/suche.js` | `vorschlaege(q, lader)`, `treffer(auswahl, lader)` |
| `js/karte.js` | MapLibre: Quellen, Ebenen, Stilwechsel, Feature-State, Popup, Stadtplan, Zechen |
| `js/sidebar.js` | Zustände Suche/Filter, Liste, Hausansicht, Sheet-Stufen, Themenkopf |
| `js/themen.js` | Thema laden, Filter und Farbregel ableiten |
| `js/exportcsv.js` | CSV-Erzeugung aus Treffern |
| `js/app.js` | Verdrahtung `karte.html` |
| `js/start.js` | Verdrahtung `index.html` |
| `bilder/kreis-gestrichelt.png`, `bilder/zeche.png` | Icons (SDF bzw. Symbol) |
| `daten/` | Ausgabe von Stufe 06 (committet) |
| `daten/themen/akademiker.json` | erstes Thema |
| `vendor/` | maplibre-gl.js, maplibre-gl.css, pmtiles.js |
| `tests/*.test.js` | `node --test` |
| `tests/e2e/test_site.py` (Repo-`tests/`) | Playwright-Rauchtests |

---

### Task 1: Range-Requests in `werkzeuge/serve.py`

pmtiles.js liest Kacheln über HTTP-Range. `SimpleHTTPRequestHandler` kennt das nicht.

**Files:**
- Modify: `werkzeuge/serve.py` (Klasse `Handler`, Methode `do_GET`)
- Test: `tests/test_serve_range.py`

**Interfaces:**
- Produces: `Handler.do_GET` beantwortet `Range: bytes=a-b` mit 206, `Content-Range`, `Accept-Ranges: bytes`; ohne Range unverändert.

- [ ] **Step 1: Failing test schreiben**

```python
# tests/test_serve_range.py
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
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `python3 -m pytest tests/test_serve_range.py -q`
Expected: 2 FAIL (Status 200 statt 206, `Content-Range` fehlt), 1 PASS.

- [ ] **Step 3: Range in `do_GET` umsetzen**

In `werkzeuge/serve.py` in `Handler.do_GET` direkt nach `url = urllib.parse.urlparse(self.path)` einfügen:

```python
        rng = self.headers.get("Range")
        if rng and rng.startswith("bytes=") and url.path != "/reverse":
            return self._range(url.path, rng[6:])
```

und als neue Methode der Klasse:

```python
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
```

Im Docstring des Moduls die Zeile ergänzen: `- GET mit Range-Header — Teilstücke für PMTiles (site/daten/adressen.pmtiles).`

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_serve_range.py tests/test_serve.py -q`
Expected: alle PASS.

- [ ] **Step 5: Commit**

```bash
git add werkzeuge/serve.py tests/test_serve_range.py
git commit -m "feat: Range-Requests in serve.py für PMTiles

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Merkmale aus kuratierten Tabellen

**Files:**
- Create: `pipeline/lib/merkmale.py`
- Create: `kuratierung/merkmale/akademiker.csv`
- Create: `tests/fixtures/merkmale/test.csv`
- Test: `tests/test_merkmale.py`

**Interfaces:**
- Produces: `lade_regeln(ordner: Path) -> list[Regel]`; `Regel(feld: str, art: str, muster: str, merkmal: str)`, `art ∈ {"exakt", "praefix", "regex"}`; `merkmale_fuer(eintrag: dict, regeln: list[Regel]) -> list[str]` (sortiert, ohne Dubletten). Tabellenspalten: `feld,art,muster,merkmal,beleg,bearbeiter,datum`.

- [ ] **Step 1: Fixture und failing test**

`tests/fixtures/merkmale/test.csv`:

```csv
feld,art,muster,merkmal,beleg,bearbeiter,datum
Beruf o. ä.,praefix,Dr.,akademiker,Titel im Berufsfeld,Test,2026-09-21
firstname,praefix,Dr.,akademiker,Titel im Vornamensfeld,Test,2026-09-21
Beruf o. ä.,exakt,Bergm.,bergbau,Abkürzung Bergmann,Test,2026-09-21
Beruf o. ä.,regex,^Hauer\b,bergbau,Hauer,Test,2026-09-21
```

`tests/test_merkmale.py`:

```python
import pathlib

from pipeline.lib.merkmale import Regel, lade_regeln, merkmale_fuer

FIX = pathlib.Path(__file__).parent / "fixtures" / "merkmale"


def test_lade_regeln_liest_alle_tabellen():
    regeln = lade_regeln(FIX)
    assert len(regeln) == 4
    assert regeln[0] == Regel(feld="Beruf o. ä.", art="praefix", muster="Dr.", merkmal="akademiker")


def test_merkmale_praefix_exakt_regex():
    regeln = lade_regeln(FIX)
    assert merkmale_fuer({"Beruf o. ä.": "Dr. med.", "firstname": "Karl"}, regeln) == ["akademiker"]
    assert merkmale_fuer({"Beruf o. ä.": "Bergm.", "firstname": ""}, regeln) == ["bergbau"]
    assert merkmale_fuer({"Beruf o. ä.": "Hauer u. Dr.", "firstname": "Dr. Fritz"}, regeln) == ["akademiker", "bergbau"]
    assert merkmale_fuer({"Beruf o. ä.": "Bergmann", "firstname": ""}, regeln) == []


def test_unbekannte_art_wird_abgewiesen(tmp_path):
    (tmp_path / "x.csv").write_text("feld,art,muster,merkmal,beleg,bearbeiter,datum\nBeruf o. ä.,fuzzy,Dr,akademiker,,,\n", encoding="utf-8")
    try:
        lade_regeln(tmp_path)
    except ValueError as e:
        assert "fuzzy" in str(e)
    else:
        raise AssertionError("ValueError erwartet")
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `python3 -m pytest tests/test_merkmale.py -q`
Expected: FAIL mit `ModuleNotFoundError: pipeline.lib.merkmale`.

- [ ] **Step 3: Modul schreiben**

```python
# pipeline/lib/merkmale.py
"""Merkmale je Eintrag aus kuratierten Tabellen (kuratierung/merkmale/*.csv).

Ein Merkmal ist ein Kennwort wie `akademiker` oder `bergbau`. Es entsteht nur aus einer
Tabelle mit Beleg; ohne Tabelle gibt es kein Merkmal (Precision first). Spalten:
feld, art (exakt | praefix | regex), muster, merkmal, beleg, bearbeiter, datum.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pipeline.lib.io import lies_csv

ARTEN = {"exakt", "praefix", "regex"}


@dataclass(frozen=True)
class Regel:
    feld: str
    art: str
    muster: str
    merkmal: str


def lade_regeln(ordner: Path) -> list[Regel]:
    regeln: list[Regel] = []
    for pfad in sorted(Path(ordner).glob("*.csv")):
        for z in lies_csv(pfad):
            if z["art"] not in ARTEN:
                raise ValueError(f"{pfad.name}: unbekannte Art {z['art']!r} (erlaubt: {sorted(ARTEN)})")
            if not z["muster"] or not z["merkmal"]:
                raise ValueError(f"{pfad.name}: muster und merkmal müssen gefüllt sein")
            regeln.append(Regel(z["feld"], z["art"], z["muster"], z["merkmal"]))
    return regeln


def _trifft(regel: Regel, wert: str) -> bool:
    if regel.art == "exakt":
        return wert == regel.muster
    if regel.art == "praefix":
        return wert.startswith(regel.muster)
    return re.search(regel.muster, wert) is not None


def merkmale_fuer(eintrag: dict, regeln: list[Regel]) -> list[str]:
    """Sortierte Merkmale ohne Dubletten; leere Felder treffen nie."""
    gefunden = set()
    for r in regeln:
        wert = (eintrag.get(r.feld) or "").strip()
        if wert and _trifft(r, wert):
            gefunden.add(r.merkmal)
    return sorted(gefunden)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_merkmale.py -q`
Expected: 3 PASS.

- [ ] **Step 5: Titelliste anlegen**

`kuratierung/merkmale/akademiker.csv` (Entwurf; Freigabe durch den Projektleiter ist Voraussetzung für `freigegeben: true` im Thema, Task 14):

```csv
feld,art,muster,merkmal,beleg,bearbeiter,datum
firstname,praefix,Dr.,akademiker,Doktortitel vor dem Vornamen (Buchkonvention),Claude,2026-09-21
firstname,praefix,Prof.,akademiker,Professorentitel vor dem Vornamen,Claude,2026-09-21
firstname,praefix,Dipl.-,akademiker,Diplomtitel vor dem Vornamen,Claude,2026-09-21
Beruf o. ä.,praefix,Dr.,akademiker,Doktortitel im Berufsfeld,Claude,2026-09-21
Beruf o. ä.,praefix,Prof.,akademiker,Professorentitel im Berufsfeld,Claude,2026-09-21
Beruf o. ä.,praefix,Dipl.-,akademiker,Diplomtitel im Berufsfeld,Claude,2026-09-21
Beruf o. ä.,regex,^(Studienrat|Studienrätin|Oberstudienrat|Studiendir|Apotheker|Rechtsanw|Zahnarzt|Tierarzt|Arzt|Ärztin)\b,akademiker,akademische Berufe laut Buchschreibung,Claude,2026-09-21
```

Vor dem Anlegen mit einem Einzeiler prüfen, welche Präfixe im Buch tatsächlich vorkommen, und die Liste danach anpassen (die Regex-Zeile nur mit Schreibungen, die es gibt):

```bash
python3 -c "
import csv,collections
c=collections.Counter()
for r in csv.DictReader(open('build/eintraege.csv')):
    for f in ('firstname','Beruf o. ä.'):
        v=r[f]
        if v.startswith(('Dr','Prof','Dipl')): c[(f,v.split()[0])]+=1
print(c.most_common(30))"
```

- [ ] **Step 6: Commit**

```bash
git add pipeline/lib/merkmale.py tests/test_merkmale.py tests/fixtures/merkmale/test.csv kuratierung/merkmale/akademiker.csv
git commit -m "feat: Merkmale je Eintrag aus kuratierten Tabellen (Titelliste Akademiker als Entwurf)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Grundfunktionen des Kartenexports

**Files:**
- Create: `pipeline/lib/karte_export.py`
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Produces: `adress_id(eintrag: dict) -> str` (12 Hex-Zeichen, SHA-1 über `ADRESSSCHLUESSEL`), `falte(text: str) -> str`, `praefix2(text: str) -> str`, `etagen_rang(lage: str) -> int`, `sortiere_eintraege(eintraege: list[dict]) -> list[dict]`, `scherbe(adress_id: str) -> str` (erste zwei Zeichen).

- [ ] **Step 1: Failing tests**

```python
# tests/test_karte_export.py
from pipeline.lib.karte_export import (adress_id, etagen_rang, falte, praefix2, scherbe,
                                       sortiere_eintraege)
from pipeline.lib.stufen import ADRESSSCHLUESSEL


def _e(**k):
    z = {f: "" for f in ADRESSSCHLUESSEL}
    z.update(lastname="", firstname="", lage="", teil="I", id="1")
    z.update(k)
    return z


def test_adress_id_haengt_nur_am_schluessel():
    a = _e(strasse_heute="Lattenkamp", hausnr="25", stadtteil="Katernberg", lastname="Sepeur")
    b = _e(strasse_heute="Lattenkamp", hausnr="25", stadtteil="Katernberg", lastname="Kowalski")
    c = _e(strasse_heute="Lattenkamp", hausnr="27", stadtteil="Katernberg")
    assert adress_id(a) == adress_id(b) != adress_id(c)
    assert len(adress_id(a)) == 12 and scherbe(adress_id(a)) == adress_id(a)[:2]


def test_falte_und_praefix():
    assert falte("Grenzstraße") == "grenzstrasse"
    assert falte("Müller-Lüdenscheidt, Ä.") == "mueller luedenscheidt ae"
    assert falte("  St.  Ännchen ") == "st aennchen"
    assert praefix2("Sepeur") == "se" and praefix2("Ö") == "oe" and praefix2("") == "_"


def test_etagen_rang_und_sortierung():
    assert etagen_rang("Erdg.") < etagen_rang("I") < etagen_rang("II") < etagen_rang("III") < etagen_rang("")
    assert etagen_rang("parterre.") == etagen_rang("Erdg.")
    e = [_e(lastname="Zander", lage=""), _e(lastname="Meier", lage="II"), _e(lastname="Adam", lage=""),
         _e(lastname="Kunz", lage="Erdg."), _e(lastname="Berg", lage="II")]
    assert [x["lastname"] for x in sortiere_eintraege(e)] == ["Kunz", "Berg", "Meier", "Adam", "Zander"]
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: FAIL, `ModuleNotFoundError`.

- [ ] **Step 3: Modul anlegen**

```python
# pipeline/lib/karte_export.py
"""Stufe 06: Datenpaket der Karte aus build/eintraege.csv (Spec docs/superpowers/specs/2026-09-21-basiskarte-design.md §5)."""
from __future__ import annotations

import hashlib
import re
import unicodedata

from pipeline.lib.stufen import ADRESSSCHLUESSEL

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"})
_NICHT_ZEICHEN = re.compile(r"[^a-z0-9 ]+")
_ETAGEN = {"erdg.": 0, "erdg": 0, "parterre.": 0, "parterre": 0, "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5}
ETAGE_OHNE = 99


def adress_id(eintrag: dict) -> str:
    """Stabile Adress-ID: SHA-1 über den ADRESSSCHLUESSEL, 12 Hex-Zeichen."""
    roh = "\x1f".join(eintrag.get(f, "") for f in ADRESSSCHLUESSEL)
    return hashlib.sha1(roh.encode("utf-8")).hexdigest()[:12]


def scherbe(aid: str) -> str:
    return aid[:2]


def falte(text: str) -> str:
    """Suchschlüssel: klein, Umlaute aufgelöst, Akzente entfernt, nur a–z, 0–9 und Leerzeichen."""
    t = (text or "").translate(_UMLAUTE).lower()
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = _NICHT_ZEICHEN.sub(" ", t)
    return " ".join(t.split())


def praefix2(text: str) -> str:
    """Scherbenname des Suchindex: die ersten zwei Zeichen des gefalteten Schlüssels, `_` wenn leer."""
    k = falte(text).replace(" ", "")
    return k[:2] if k else "_"


def etagen_rang(lage: str) -> int:
    return _ETAGEN.get((lage or "").strip().lower(), ETAGE_OHNE)


def sortiere_eintraege(eintraege: list[dict]) -> list[dict]:
    """Etage laut Buch zuerst (Erdg., I, II …), Einträge ohne Etage danach; innerhalb alphabetisch."""
    return sorted(eintraege, key=lambda e: (etagen_rang(e.get("lage", "")), falte(e.get("lastname", "")),
                                            falte(e.get("firstname", "")), e.get("id", "")))
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/karte_export.py tests/test_karte_export.py
git commit -m "feat: Kartenexport — Adress-ID, Schlüsselfaltung, Etagensortierung

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Adresspunkte und Eintrags-Scherben

**Files:**
- Modify: `pipeline/lib/karte_export.py`
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Consumes: `adress_id`, `sortiere_eintraege`, `scherbe`, `merkmale_fuer` (Task 2).
- Produces:
  - `gruppiere(eintraege: list[dict], regeln: list[Regel]) -> dict[str, Adresse]` mit `Adresse = dict(id, lat, lon, stufe, stadtteil, strasse_heute, hausnr, hausnr_zusatz, historisch, nummer_unsicher, eintraege: list[dict])`; nur Einträge mit `stufe in {"haus","strasse"}` und Koordinaten. `stufe` der Adresse ist `stadtplan`, wenn `herkunft == "stadtplan_1935"`.
  - `punkt_feature(a: Adresse) -> dict` (GeoJSON-Feature mit `n_I, n_II, n_III, m_<merkmal>`).
  - `eintrag_kurz(e: dict) -> dict` (Felder für Scherben: `id, teil, seite, name, vorname, beruf, etage, stand, bezug_vorname, bezug_beruf, firma, eigentuemer, verwalter, wohnort, flags, merkmale`).
  - `baue_scherben(adressen: dict[str, Adresse]) -> dict[str, dict[str, list[dict]]]` (Scherbenname → Adress-ID → Einträge).

- [ ] **Step 1: Failing tests**

An `tests/test_karte_export.py` anhängen:

```python
from pipeline.lib.karte_export import baue_scherben, eintrag_kurz, gruppiere, punkt_feature
from pipeline.lib.merkmale import Regel

REGELN = [Regel("Beruf o. ä.", "praefix", "Dr.", "akademiker")]


def _v(**k):
    """Verorteter Eintrag mit sinnvollen Standardwerten."""
    z = _e(strasse_heute="Lattenkamp", hausnr="25", stadtteil="Katernberg", strasse_roh="Grenzstr.",
           Vorort="Katernberg", herkunft="konkordanz", lat="51.49", lon="7.06", stufe="haus", page="I-551",
           seite="551", **{"Beruf o. ä.": "Bergm.", "Familienstand": "", "Vorname Bezugsperson": "",
                            "Beruf Bezugsperson": "", "Firmenname": "", "Eigentümer": "", "Verwalter": "",
                            "abweichender Wohnort": "", "zeitlich_abweichend": "nein", "mehrdeutig": "nein",
                            "grund_mehrdeutig": "", "nummer_unsicher": "nein"})
    z.update(k)
    return z


def test_gruppiere_zaehlt_teile_und_merkmale():
    e = [_v(id="1", lastname="Sepeur", teil="I"), _v(id="2", lastname="Zeche", teil="II"),
         _v(id="3", lastname="Meier", teil="III", **{"Beruf o. ä.": "Dr. med."}),
         _v(id="4", lastname="Offen", stufe="offen", lat="", lon=""),
         _v(id="5", lastname="Anders", hausnr="27")]
    adressen = gruppiere(e, REGELN)
    assert len(adressen) == 2
    a = adressen[adress_id(e[0])]
    assert [x["id"] for x in a["eintraege"]] == ["3", "1", "2"]  # Etage fehlt überall → alphabetisch
    f = punkt_feature(a)
    assert f["geometry"]["coordinates"] == [7.06, 51.49]
    p = f["properties"]
    assert (p["n_I"], p["n_II"], p["n_III"], p["m_akademiker"]) == (1, 1, 1, 1)
    assert p["stufe"] == "haus" and p["historisch"] == "Grenzstr. 25, Katernberg"
    assert p["strasse_heute"] == "Lattenkamp" and p["hausnr"] == "25" and p["stadtteil"] == "Katernberg"


def test_stadtplan_punkt_bekommt_stufe_stadtplan():
    e = [_v(id="1", stufe="strasse", herkunft="stadtplan_1935", strasse_heute="", hausnr="12",
            strasse_roh="Matthiasstr.", Vorort="")]
    a = next(iter(gruppiere(e, []).values()))
    p = punkt_feature(a)["properties"]
    assert p["stufe"] == "stadtplan" and p["historisch"] == "Matthiasstr. 12" and p["strasse_heute"] == ""


def test_eintrag_kurz_und_scherben():
    e = _v(id="7", lastname="Sepeur", firstname="Wilh.", teil="I", lage="II", nummer_unsicher="ja",
           **{"Beruf o. ä.": "Dr. Bergm.", "Familienstand": "Wwe."})
    k = eintrag_kurz(e, ["akademiker"])
    assert k == {"id": "7", "teil": "I", "seite": "I-551", "name": "Sepeur", "vorname": "Wilh.",
                 "beruf": "Dr. Bergm.", "etage": "II", "stand": "Wwe.", "bezug_vorname": "", "bezug_beruf": "",
                 "firma": "", "eigentuemer": "", "verwalter": "", "wohnort": "", "flags": ["nummer_unsicher"],
                 "merkmale": ["akademiker"]}
    adressen = gruppiere([e], REGELN)
    sch = baue_scherben(adressen)
    aid = adress_id(e)
    assert list(sch) == [aid[:2]] and sch[aid[:2]][aid][0]["name"] == "Sepeur"
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: ImportError für `gruppiere`.

- [ ] **Step 3: Funktionen ergänzen**

An `pipeline/lib/karte_export.py` anhängen:

```python
from collections import defaultdict

from pipeline.lib.merkmale import Regel, merkmale_fuer

VERORTET = {"haus", "strasse"}
FLAGS = ["nummer_unsicher", "zeitlich_abweichend", "mehrdeutig"]


def _historisch(e: dict) -> str:
    """Buchschreibung der Adresse: Straße, Hausnummer (mit Zusatz), Vorort."""
    nr = (e.get("hausnr", "") + (e.get("hausnr_zusatz", "") or "")).strip()
    kopf = " ".join(x for x in (e.get("strasse_roh", ""), nr) if x)
    return f"{kopf}, {e['Vorort']}" if e.get("Vorort") else kopf


def _stufe(e: dict) -> str:
    return "stadtplan" if e.get("herkunft") == "stadtplan_1935" else e["stufe"]


def gruppiere(eintraege: list[dict], regeln: list[Regel]) -> dict[str, dict]:
    """Verortete Einträge je Adresse bündeln; Einträge sortiert, Merkmale angehängt."""
    gruppen: dict[str, dict] = {}
    for e in eintraege:
        if e.get("stufe") not in VERORTET or not e.get("lat") or not e.get("lon"):
            continue
        aid = adress_id(e)
        a = gruppen.get(aid)
        if a is None:
            a = gruppen[aid] = dict(id=aid, lat=float(e["lat"]), lon=float(e["lon"]), stufe=_stufe(e),
                                    stadtteil=e.get("stadtteil", "") or e.get("Vorort", ""),
                                    strasse_heute=e.get("strasse_heute", ""), hausnr=e.get("hausnr", ""),
                                    hausnr_zusatz=e.get("hausnr_zusatz", ""), historisch=_historisch(e),
                                    nummer_unsicher=e.get("nummer_unsicher", "nein"), eintraege=[])
        e = dict(e, _merkmale=merkmale_fuer(e, regeln))
        a["eintraege"].append(e)
    for a in gruppen.values():
        a["eintraege"] = sortiere_eintraege(a["eintraege"])
    return gruppen


def punkt_feature(a: dict) -> dict:
    p = dict(id=a["id"], stufe=a["stufe"], stadtteil=a["stadtteil"], strasse_heute=a["strasse_heute"],
             hausnr=a["hausnr"] + (a["hausnr_zusatz"] or ""), historisch=a["historisch"],
             nummer_unsicher=a["nummer_unsicher"], n_I=0, n_II=0, n_III=0)
    merkmale: dict[str, int] = defaultdict(int)
    for e in a["eintraege"]:
        p["n_" + e["teil"]] += 1
        for m in e["_merkmale"]:
            merkmale[m] += 1
    p.update({f"m_{m}": n for m, n in sorted(merkmale.items())})
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [a["lon"], a["lat"]]},
            "properties": p}


def eintrag_kurz(e: dict, merkmale: list[str]) -> dict:
    return dict(id=e["id"], teil=e["teil"], seite=e.get("page", ""), name=e.get("lastname", ""),
                vorname=e.get("firstname", ""), beruf=e.get("Beruf o. ä.", ""), etage=e.get("lage", ""),
                stand=e.get("Familienstand", ""), bezug_vorname=e.get("Vorname Bezugsperson", ""),
                bezug_beruf=e.get("Beruf Bezugsperson", ""), firma=e.get("Firmenname", ""),
                eigentuemer=e.get("Eigentümer", ""), verwalter=e.get("Verwalter", ""),
                wohnort=e.get("abweichender Wohnort", ""),
                flags=[f for f in FLAGS if e.get(f) == "ja"], merkmale=list(merkmale))


def baue_scherben(adressen: dict[str, dict]) -> dict[str, dict[str, list[dict]]]:
    scherben: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    for aid, a in adressen.items():
        scherben[scherbe(aid)][aid] = [eintrag_kurz(e, e["_merkmale"]) for e in a["eintraege"]]
    return dict(scherben)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/karte_export.py tests/test_karte_export.py
git commit -m "feat: Kartenexport — Adresspunkte und Eintrags-Scherben

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Suchindex (Namen, Firmen, Straßen, Berufe, Stadtteile)

**Files:**
- Modify: `pipeline/lib/karte_export.py`
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Consumes: `gruppiere`-Ergebnis (`dict[str, Adresse]`), `falte`, `praefix2`.
- Produces:
  - `baue_namensindex(adressen) -> dict[str, list[list]]`: Scherbe (`praefix2(Nachname)`) → Zeilen `[schluessel, nachname, vorname, beruf, adresse_anzeige, eintrags_id, adress_id, teil]`; alle Teile I–III mit Nachname.
  - `baue_firmenindex(adressen) -> dict[str, list[list]]`: Scherbe (`praefix2(Firmenname)`) → `[schluessel, firmenname, adresse_anzeige, eintrags_id, adress_id]`.
  - `baue_strassenindex(adressen) -> list[dict]`: je (Anzeigename, Vorort/Stadtteil) `dict(schluessel, name, art="heute"|"1936", ort, zeilen, adressen=[ids])`.
  - `baue_berufsindex(adressen) -> tuple[list[list], dict[str, dict[str, list[list]]]]`: Liste `[schluessel, schreibung, zeilen]` und Scherbe (`praefix2(schreibung)`) → Schreibung → `[[adress_id, zaehler], …]`.
  - `baue_stadtteile(adressen) -> list[dict]`: `dict(name, lat, lon, zeilen)` (Mittelwert der Koordinaten).
  - `anzeige_adresse(a: Adresse) -> str`: heutige Adresse als Text, bei Stadtplan-Punkt die historische mit Zusatz „(Stadtplan 1935)“.

- [ ] **Step 1: Failing tests**

Anhängen an `tests/test_karte_export.py`:

```python
from pipeline.lib.karte_export import (anzeige_adresse, baue_berufsindex, baue_firmenindex,
                                       baue_namensindex, baue_stadtteile, baue_strassenindex)


def _adressen():
    e = [_v(id="1", lastname="Sepeur", firstname="Wilh.", teil="I"),
         _v(id="2", lastname="Sepeur", firstname="Anna", teil="I", hausnr="27"),
         _v(id="3", lastname="Jäger", firstname="M.", teil="III", Firmenname="M. Jäger, Althandlung",
            **{"Beruf o. ä.": ""}),
         _v(id="4", lastname="Ost", teil="I", strasse_heute="Bochumer Straße", hausnr="5", stadtteil="Steele",
            strasse_roh="Bochumer Str.", Vorort="Steele", lat="51.45", lon="7.08", **{"Beruf o. ä.": "Hauer"})]
    return gruppiere(e, [])


def test_namens_und_firmenindex():
    n = baue_namensindex(_adressen())
    assert sorted(n) == ["ja", "os", "se"]
    assert n["se"][0][:5] == ["sepeur anna", "Sepeur", "Anna", "Bergm.", "Lattenkamp 27, Katernberg"]
    assert n["se"][1][5:] == ["1", adress_id(_v(id="1")), "I"]
    f = baue_firmenindex(_adressen())
    assert list(f) == ["mj"] and f["mj"][0][:2] == ["m jaeger althandlung", "M. Jäger, Althandlung"]


def test_strassenindex_heute_und_1936():
    s = baue_strassenindex(_adressen())
    namen = {(x["name"], x["art"], x["ort"]): x for x in s}
    assert namen[("Lattenkamp", "heute", "Katernberg")]["zeilen"] == 3
    assert len(namen[("Lattenkamp", "heute", "Katernberg")]["adressen"]) == 2
    assert namen[("Grenzstr.", "1936", "Katernberg")]["zeilen"] == 3
    assert namen[("Bochumer Str.", "1936", "Steele")]["schluessel"] == "bochumer str"


def test_berufsindex_und_stadtteile():
    liste, scherben = baue_berufsindex(_adressen())
    assert liste[0] == ["bergm", "Bergm.", 2] and ["hauer", "Hauer", 1] in liste
    assert sorted(scherben["be"]["Bergm."]) == sorted([[adress_id(_v(id="1")), 1], [adress_id(_v(id="2", hausnr="27")), 1]])
    st = baue_stadtteile(_adressen())
    assert [x["name"] for x in st] == ["Katernberg", "Steele"] and st[0]["zeilen"] == 3
    assert st[0]["lat"] == 51.49 and st[1]["lon"] == 7.08


def test_anzeige_adresse_stadtplan():
    a = next(iter(gruppiere([_v(id="1", herkunft="stadtplan_1935", stufe="strasse", strasse_heute="",
                                strasse_roh="Matthiasstr.", Vorort="")], []).values()))
    assert anzeige_adresse(a) == "Matthiasstr. 25 (Stadtplan 1935)"
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: ImportError.

- [ ] **Step 3: Indexfunktionen ergänzen**

Anhängen an `pipeline/lib/karte_export.py`:

```python
def anzeige_adresse(a: dict) -> str:
    if a["stufe"] == "stadtplan" or not a["strasse_heute"]:
        return f"{a['historisch']} (Stadtplan 1935)"
    nr = a["hausnr"] + (a["hausnr_zusatz"] or "")
    kopf = f"{a['strasse_heute']} {nr}".strip()
    return f"{kopf}, {a['stadtteil']}" if a["stadtteil"] else kopf


def baue_namensindex(adressen: dict[str, dict]) -> dict[str, list[list]]:
    idx: dict[str, list[list]] = defaultdict(list)
    for a in adressen.values():
        anz = anzeige_adresse(a)
        for e in a["eintraege"]:
            nach = e.get("lastname", "")
            if not nach:
                continue
            k = falte(f"{nach} {e.get('firstname', '')}")
            idx[praefix2(nach)].append([k, nach, e.get("firstname", ""), e.get("Beruf o. ä.", ""), anz,
                                        e["id"], a["id"], e["teil"]])
    return {s: sorted(z) for s, z in idx.items()}


def baue_firmenindex(adressen: dict[str, dict]) -> dict[str, list[list]]:
    idx: dict[str, list[list]] = defaultdict(list)
    for a in adressen.values():
        anz = anzeige_adresse(a)
        for e in a["eintraege"]:
            firma = e.get("Firmenname", "")
            if firma:
                idx[praefix2(firma)].append([falte(firma), firma, anz, e["id"], a["id"]])
    return {s: sorted(z) for s, z in idx.items()}


def baue_strassenindex(adressen: dict[str, dict]) -> list[dict]:
    gruppen: dict[tuple, dict] = {}
    for a in adressen.values():
        n = len(a["eintraege"])
        ort = a["stadtteil"]
        paare = [(a["strasse_heute"], "heute", ort)] if a["strasse_heute"] else []
        roh = a["eintraege"][0].get("strasse_roh", "")
        vorort = a["eintraege"][0].get("Vorort", "") or ort
        if roh:
            paare.append((roh, "1936", vorort))
        for name, art, o in paare:
            g = gruppen.setdefault((name, art, o), dict(schluessel=falte(name), name=name, art=art, ort=o,
                                                        zeilen=0, adressen=[]))
            g["zeilen"] += n
            g["adressen"].append(a["id"])
    return sorted(gruppen.values(), key=lambda g: (g["schluessel"], g["art"], g["ort"]))


def baue_berufsindex(adressen: dict[str, dict]) -> tuple[list[list], dict[str, dict[str, list[list]]]]:
    zaehler: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for a in adressen.values():
        for e in a["eintraege"]:
            b = e.get("Beruf o. ä.", "")
            if b:
                zaehler[b][a["id"]] += 1
    liste = sorted([[falte(b), b, sum(z.values())] for b, z in zaehler.items()])
    scherben: dict[str, dict[str, list[list]]] = defaultdict(dict)
    for b, z in zaehler.items():
        scherben[praefix2(b)][b] = sorted([[aid, n] for aid, n in z.items()])
    return liste, dict(scherben)


def baue_stadtteile(adressen: dict[str, dict]) -> list[dict]:
    summen: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0, 0])  # lat, lon, adressen, zeilen
    for a in adressen.values():
        if not a["stadtteil"]:
            continue
        s = summen[a["stadtteil"]]
        s[0] += a["lat"]; s[1] += a["lon"]; s[2] += 1; s[3] += len(a["eintraege"])
    return [dict(name=n, lat=round(s[0] / s[2], 5), lon=round(s[1] / s[2], 5), zeilen=s[3])
            for n, s in sorted(summen.items())]
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: 10 PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/karte_export.py tests/test_karte_export.py
git commit -m "feat: Kartenexport — Suchindex für Namen, Firmen, Straßen, Berufe, Stadtteile

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Kennzahlen, Zechen-GeoJSON, tippecanoe und Stufe 06

**Files:**
- Modify: `pipeline/lib/karte_export.py`
- Create: `pipeline/06_karte_export.py`
- Create: `tests/fixtures/zechen.csv`
- Test: `tests/test_karte_export.py`
- Modify: `.gitignore` (Zwischen-GeoJSON ausschließen)

**Interfaces:**
- Consumes: alles aus Task 3–5; `lies_csv`, `schreib_csv`, `projektwurzel`.
- Produces:
  - `baue_kennzahlen(eintraege: list[dict], adressen: dict, datum: str) -> dict` mit `eintraege_je_teil`, `verortet`, `stufen` (Anteile in Prozent, eine Nachkommastelle), `offen`, `adressen`, `stand`.
  - `zechen_geojson(zeilen: list[dict]) -> dict` (nur Zeilen mit lat/lon; Eigenschaften `name, stadtteil, betrieb_von, betrieb_bis, quelle, aktiv_1936`).
  - `tippecanoe_befehl(geojson: Path, pmtiles: Path) -> list[str]`.
  - `schreibe_paket(ausgabe: Path, eintraege, regeln, zechen, datum) -> dict` (schreibt alle Dateien, gibt Kennzahlen zurück).
- Ausgabeordner: `site/daten/` mit `adressen.geojson` (Zwischenprodukt, nicht committet), `adressen.pmtiles`, `haus/<xx>.json`, `suche/namen/<ab>.json`, `suche/firmen/<ab>.json`, `suche/strassen.json`, `suche/berufe.json`, `suche/berufe/<ab>.json`, `suche/stadtteile.json`, `zechen.geojson`, `kennzahlen.json`.

- [ ] **Step 1: Fixture und failing tests**

`tests/fixtures/zechen.csv`:

```csv
name,stadtteil,lat,lon,betrieb_von,betrieb_bis,quelle,bearbeiter,datum
Zeche Zollverein,Katernberg,51.4861,7.0447,1851,1986,https://de.wikipedia.org/wiki/Zeche_Zollverein,Test,2026-09-21
Zeche Alt,Werden,51.39,7.0,1800,1900,https://de.wikipedia.org/wiki/Zeche_Alt,Test,2026-09-21
Zeche Ohne,Kray,,,1900,1950,,Test,2026-09-21
```

Anhängen an `tests/test_karte_export.py`:

```python
import json, pathlib, shutil

import pytest

from pipeline.lib.karte_export import baue_kennzahlen, schreibe_paket, tippecanoe_befehl, zechen_geojson
from pipeline.lib.io import lies_csv

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_kennzahlen():
    e = [_v(id="1", teil="I"), _v(id="2", teil="II"), _v(id="3", teil="I", stufe="strasse"),
         _v(id="4", teil="III", stufe="offen", lat="", lon="")]
    k = baue_kennzahlen(e, gruppiere(e, []), "2026-09-21")
    assert k["eintraege_je_teil"] == {"I": 2, "II": 1, "III": 1}
    assert k["stufen"] == {"haus": 50.0, "strasse": 25.0, "stadtplan": 0.0, "offen": 25.0}
    assert k["verortet"] == 3 and k["offen"] == 1 and k["adressen"] == 2 and k["stand"] == "2026-09-21"


def test_zechen_geojson_laesst_zeilen_ohne_koordinaten_weg():
    g = zechen_geojson(lies_csv(FIX / "zechen.csv"))
    assert [f["properties"]["name"] for f in g["features"]] == ["Zeche Zollverein", "Zeche Alt"]
    p = g["features"][0]["properties"]
    assert p["aktiv_1936"] is True and g["features"][1]["properties"]["aktiv_1936"] is False
    assert g["features"][0]["geometry"]["coordinates"] == [7.0447, 51.4861]


def test_tippecanoe_befehl():
    b = tippecanoe_befehl(pathlib.Path("a.geojson"), pathlib.Path("a.pmtiles"))
    assert b[0] == "tippecanoe" and "-o" in b and "a.pmtiles" in b and "--maximum-zoom=15" in b


def test_schreibe_paket(tmp_path):
    e = [_v(id="1", lastname="Sepeur", firstname="Wilh.", teil="I"), _v(id="2", lastname="Jäger", teil="III",
         Firmenname="M. Jäger, Althandlung")]
    k = schreibe_paket(tmp_path, e, [], lies_csv(FIX / "zechen.csv"), "2026-09-21", kacheln=False)
    aid = adress_id(e[0])
    assert json.loads((tmp_path / "haus" / f"{aid[:2]}.json").read_text())[aid][0]["name"] == "Jäger"
    assert (tmp_path / "suche" / "namen" / "se.json").exists()
    assert (tmp_path / "suche" / "firmen" / "mj.json").exists()
    assert json.loads((tmp_path / "suche" / "strassen.json").read_text())[0]["name"] in ("Grenzstr.", "Lattenkamp")
    assert json.loads((tmp_path / "kennzahlen.json").read_text()) == k
    assert len(json.loads((tmp_path / "zechen.geojson").read_text())["features"]) == 2
    geo = json.loads((tmp_path / "adressen.geojson").read_text())
    assert geo["features"][0]["properties"]["n_I"] == 1


@pytest.mark.skipif(shutil.which("tippecanoe") is None, reason="tippecanoe nicht installiert")
def test_schreibe_paket_mit_kacheln(tmp_path):
    e = [_v(id="1", lastname="Sepeur", teil="I")]
    schreibe_paket(tmp_path, e, [], [], "2026-09-21", kacheln=True)
    assert (tmp_path / "adressen.pmtiles").stat().st_size > 100
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: ImportError.

- [ ] **Step 3: Funktionen und Skript schreiben**

Anhängen an `pipeline/lib/karte_export.py`:

```python
import json
import subprocess
from pathlib import Path

STUFEN = ["haus", "strasse", "stadtplan", "offen"]


def baue_kennzahlen(eintraege: list[dict], adressen: dict[str, dict], datum: str) -> dict:
    je_teil: dict[str, int] = defaultdict(int)
    je_stufe: dict[str, int] = defaultdict(int)
    for e in eintraege:
        je_teil[e["teil"]] += 1
        s = _stufe(e) if e.get("stufe") in VERORTET else "offen"
        je_stufe[s] += 1
    n = len(eintraege) or 1
    return dict(eintraege_je_teil=dict(sorted(je_teil.items())),
                stufen={s: round(100 * je_stufe[s] / n, 1) for s in STUFEN},
                verortet=sum(je_stufe[s] for s in STUFEN[:3]), offen=je_stufe["offen"],
                adressen=len(adressen), stand=datum)


def zechen_geojson(zeilen: list[dict]) -> dict:
    features = []
    for z in zeilen:
        if not z.get("lat") or not z.get("lon"):
            continue
        von, bis = int(z["betrieb_von"] or 0), int(z["betrieb_bis"] or 9999)
        features.append({"type": "Feature",
                         "geometry": {"type": "Point", "coordinates": [float(z["lon"]), float(z["lat"])]},
                         "properties": dict(name=z["name"], stadtteil=z.get("stadtteil", ""),
                                            betrieb_von=z["betrieb_von"], betrieb_bis=z["betrieb_bis"],
                                            quelle=z.get("quelle", ""), aktiv_1936=von <= 1936 <= bis)})
    return {"type": "FeatureCollection", "features": features}


def tippecanoe_befehl(geojson: Path, pmtiles: Path) -> list[str]:
    return ["tippecanoe", "-o", str(pmtiles), "--force", "--layer=adressen", "--minimum-zoom=9",
            "--maximum-zoom=15", "--drop-densest-as-needed", "--extend-zooms-if-still-dropping",
            "--no-feature-limit", "--no-tile-size-limit", "--quiet", str(geojson)]


def _json(pfad: Path, daten) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def schreibe_paket(ausgabe: Path, eintraege: list[dict], regeln: list[Regel], zechen: list[dict],
                   datum: str, kacheln: bool = True) -> dict:
    """Schreibt das komplette Datenpaket nach `ausgabe` (site/daten) und gibt die Kennzahlen zurück."""
    ausgabe = Path(ausgabe)
    adressen = gruppiere(eintraege, regeln)
    geo = {"type": "FeatureCollection", "features": [punkt_feature(a) for a in adressen.values()]}
    _json(ausgabe / "adressen.geojson", geo)
    if kacheln:
        subprocess.run(tippecanoe_befehl(ausgabe / "adressen.geojson", ausgabe / "adressen.pmtiles"), check=True)
    for name, inhalt in baue_scherben(adressen).items():
        _json(ausgabe / "haus" / f"{name}.json", inhalt)
    for name, zeilen in baue_namensindex(adressen).items():
        _json(ausgabe / "suche" / "namen" / f"{name}.json", zeilen)
    for name, zeilen in baue_firmenindex(adressen).items():
        _json(ausgabe / "suche" / "firmen" / f"{name}.json", zeilen)
    _json(ausgabe / "suche" / "strassen.json", baue_strassenindex(adressen))
    liste, scherben = baue_berufsindex(adressen)
    _json(ausgabe / "suche" / "berufe.json", liste)
    for name, inhalt in scherben.items():
        _json(ausgabe / "suche" / "berufe" / f"{name}.json", inhalt)
    _json(ausgabe / "suche" / "stadtteile.json", baue_stadtteile(adressen))
    _json(ausgabe / "zechen.geojson", zechen_geojson(zechen))
    kennzahlen = baue_kennzahlen(eintraege, adressen, datum)
    _json(ausgabe / "kennzahlen.json", kennzahlen)
    return kennzahlen
```

`pipeline/06_karte_export.py`:

```python
"""Stufe 06: Datenpaket der Karte → site/daten/ (PMTiles, Scherben, Suchindex, Kennzahlen, Zechen).

Aufruf: python3 pipeline/06_karte_export.py [--ohne-kacheln]
Voraussetzung: Stufen 01–05 gelaufen (build/eintraege.csv), tippecanoe installiert.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import datetime
import json
import shutil

from pipeline.lib.io import lies_csv, projektwurzel
from pipeline.lib.karte_export import schreibe_paket
from pipeline.lib.merkmale import lade_regeln

W = projektwurzel()
kacheln = "--ohne-kacheln" not in sys.argv
if kacheln and shutil.which("tippecanoe") is None:
    sys.exit("tippecanoe nicht gefunden (oder --ohne-kacheln verwenden)")
zechen_pfad = W / "kuratierung" / "zechen.csv"
zechen = lies_csv(zechen_pfad) if zechen_pfad.exists() else []
ziel = W / "site" / "daten"
# Alte Scherben und Indexdateien entfernen, damit keine verwaisten Dateien bleiben.
for unter in ("haus", "suche"):
    shutil.rmtree(ziel / unter, ignore_errors=True)
k = schreibe_paket(ziel, lies_csv(W / "build" / "eintraege.csv"), lade_regeln(W / "kuratierung" / "merkmale"),
                   zechen, datetime.date.today().isoformat(), kacheln=kacheln)
print(json.dumps(k, ensure_ascii=False, indent=1))
```

`.gitignore` ergänzen um `site/daten/adressen.geojson`.

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_karte_export.py tests/test_merkmale.py -q`
Expected: alle PASS (Kachel-Test läuft, weil tippecanoe installiert ist).

- [ ] **Step 5: Echten Lauf machen und Größen prüfen**

Run: `python3 pipeline/06_karte_export.py && du -sh site/daten/adressen.pmtiles site/daten/haus site/daten/suche && ls site/daten/haus | wc -l`
Expected: PMTiles unter 10 MB, 256 Scherben, Kennzahlen mit `haus` ≈ 64 %. Wenn PMTiles größer als 10 MB: in `tippecanoe_befehl` `--maximum-zoom=14` setzen und erneut laufen lassen.

- [ ] **Step 6: Commit**

```bash
git add pipeline/lib/karte_export.py pipeline/06_karte_export.py tests/test_karte_export.py tests/fixtures/zechen.csv .gitignore site/daten
git commit -m "feat: Stufe 06 Kartenexport — PMTiles, Scherben, Suchindex, Kennzahlen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Zechen aus Wikipedia → `kuratierung/zechen.csv`

**Files:**
- Create: `werkzeuge/zechen_wikipedia.py`
- Create: `kuratierung/zechen.csv`
- Test: `tests/test_zechen_wikipedia.py`

**Interfaces:**
- Produces: `parse_zechen(wikitext: str) -> list[dict]` (Felder wie `kuratierung/zechen.csv`: `name, stadtteil, lat, lon, betrieb_von, betrieb_bis, quelle, bearbeiter, datum`), `main()` lädt `https://de.wikipedia.org/w/api.php?action=parse&page=Liste_von_Bergwerken_in_Essen&prop=wikitext&format=json` und schreibt die CSV nur, wenn sie nicht existiert (`--neu` erzwingt), damit Handprüfungen nicht überschrieben werden.

- [ ] **Step 1: Failing test mit Wikitext-Ausschnitt**

```python
# tests/test_zechen_wikipedia.py
from werkzeuge.zechen_wikipedia import parse_zechen

WIKI = """
{| class="wikitable sortable"
! Name !! Stadtteil !! Betrieb !! Koordinaten
|-
| [[Zeche Zollverein]] || [[Essen-Katernberg|Katernberg]] || 1851–1986 || {{Coordinate|text=DMS|NS=51.4861|EW=7.0447|type=landmark|region=DE-NW|name=Zollverein}}
|-
| [[Zeche Alt]] || Werden || 1800–1900 ||
|}
"""


def test_parse_zechen_liest_name_stadtteil_jahre_koordinaten():
    z = parse_zechen(WIKI)
    assert z[0]["name"] == "Zeche Zollverein" and z[0]["stadtteil"] == "Katernberg"
    assert (z[0]["betrieb_von"], z[0]["betrieb_bis"]) == ("1851", "1986")
    assert (z[0]["lat"], z[0]["lon"]) == ("51.4861", "7.0447")
    assert z[0]["quelle"] == "https://de.wikipedia.org/wiki/Zeche_Zollverein"
    assert z[1]["name"] == "Zeche Alt" and z[1]["lat"] == "" and z[1]["stadtteil"] == "Werden"
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `python3 -m pytest tests/test_zechen_wikipedia.py -q`
Expected: ModuleNotFoundError.

- [ ] **Step 3: Werkzeug schreiben**

```python
# werkzeuge/zechen_wikipedia.py
"""Zechen Essens aus der Wikipedia-Liste → kuratierung/zechen.csv (einmalig, danach Handprüfung).

    python3 werkzeuge/zechen_wikipedia.py [--neu]

Die Tabelle wird nicht überschrieben, wenn sie existiert (Handprüfungen bleiben erhalten); --neu erzwingt.
Zeilen ohne Koordinaten bleiben in der CSV, damit sie von Hand ergänzt werden können; Stufe 06 lässt sie weg.
"""
from __future__ import annotations

import datetime
import pathlib
import re
import sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.io import projektwurzel, schreib_csv

SEITE = "Liste_von_Bergwerken_in_Essen"
API = "https://de.wikipedia.org/w/api.php"
FELDER = ["name", "stadtteil", "lat", "lon", "betrieb_von", "betrieb_bis", "quelle", "bearbeiter", "datum"]
_LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_JAHRE = re.compile(r"(\d{4})\s*[–-]\s*(\d{4})?")
_KOORD = re.compile(r"NS=([\d.]+)\|EW=([\d.]+)")


def _text(zelle: str) -> str:
    """Wikilink-Anzeigetext, sonst der bereinigte Zelleninhalt."""
    m = _LINK.search(zelle)
    if m:
        return (m.group(2) or m.group(1)).strip()
    return re.sub(r"'{2,}|<[^>]+>", "", zelle).strip()


def _ziel(zelle: str) -> str:
    m = _LINK.search(zelle)
    return m.group(1).strip().replace(" ", "_") if m else ""


def parse_zechen(wikitext: str) -> list[dict]:
    zechen = []
    for zeile in wikitext.split("|-"):
        zellen = [z.strip() for z in re.split(r"\n\|\s*|\s\|\|\s", "\n" + zeile.strip()) if z.strip()]
        zellen = [z for z in zellen if not z.startswith(("{|", "!", "}"))]
        if len(zellen) < 3 or "Zeche" not in zellen[0]:
            continue
        jahre = _JAHRE.search(zellen[2]) if len(zellen) > 2 else None
        koord = _KOORD.search(zeile)
        ziel = _ziel(zellen[0])
        zechen.append(dict(name=_text(zellen[0]), stadtteil=_text(zellen[1]) if len(zellen) > 1 else "",
                           lat=koord.group(1) if koord else "", lon=koord.group(2) if koord else "",
                           betrieb_von=jahre.group(1) if jahre else "", betrieb_bis=(jahre.group(2) or "") if jahre else "",
                           quelle=f"https://de.wikipedia.org/wiki/{ziel}" if ziel else "",
                           bearbeiter="wikipedia", datum=datetime.date.today().isoformat()))
    return zechen


def main() -> None:
    ziel = projektwurzel() / "kuratierung" / "zechen.csv"
    if ziel.exists() and "--neu" not in sys.argv:
        sys.exit(f"{ziel} existiert, --neu zum Überschreiben")
    r = requests.get(API, params=dict(action="parse", page=SEITE, prop="wikitext", format="json"),
                     headers={"User-Agent": "essener-adressbuch-1936 (Zechenliste)"}, timeout=30)
    r.raise_for_status()
    zechen = parse_zechen(r.json()["parse"]["wikitext"]["*"])
    schreib_csv(ziel, zechen, FELDER)
    print(f"{len(zechen)} Zechen, {sum(1 for z in zechen if z['lat'])} mit Koordinaten → {ziel}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Test laufen lassen**

Run: `python3 -m pytest tests/test_zechen_wikipedia.py -q`
Expected: PASS. Falls die Zellentrennung an der echten Seite scheitert (Tabellenformat weicht ab), den Wikitext mit `python3 -c` herunterladen, im Scratchpad ansehen und die Regexe anpassen; der Test bleibt die Vorgabe.

- [ ] **Step 5: Echten Abruf, Sichtprüfung, Nacharbeit**

Run: `python3 werkzeuge/zechen_wikipedia.py && python3 -c "import csv;z=list(csv.DictReader(open('kuratierung/zechen.csv')));print(len(z), sum(1 for x in z if x['lat']));print([x['name'] for x in z if not x['lat']])"`

Für Zechen ohne Koordinaten oder Jahre: Wikipedia-Artikel der Zeche öffnen, Werte eintragen, `bearbeiter` auf den Namen des Prüfenden setzen. Zechen, die 1936 nicht in Betrieb waren, bleiben in der Datei (die Karte zeigt sie nur auf Wunsch). Ergebnis dem Projektleiter zur Freigabe melden.

- [ ] **Step 6: Commit**

```bash
git add werkzeuge/zechen_wikipedia.py tests/test_zechen_wikipedia.py kuratierung/zechen.csv
git commit -m "feat: Zechenliste aus Wikipedia als kuratierte Tabelle

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Frontend-Gerüst — vendor, Konfiguration, Schlüsselfaltung, URL-Zustand

**Files:**
- Create: `site/vendor/maplibre-gl.js`, `site/vendor/maplibre-gl.css`, `site/vendor/pmtiles.js`, `site/vendor/README.md`
- Create: `site/js/konfig.js`, `site/js/schluessel.js`, `site/js/zustand.js`
- Test: `site/tests/schluessel.test.js`, `site/tests/zustand.test.js`

**Interfaces:**
- Produces:
  - `konfig.js`: `export const STILE = {positron: "https://tiles.openfreemap.org/styles/positron", liberty: "https://tiles.openfreemap.org/styles/liberty"}`, `FARBEN = {I:"#1d4ed8", II:"#ca8a04", III:"#c2410c", neutral:"#1f2937", treffer:"#dc2626", auswahl:"#111827"}`, `PLAN_FREIGEGEBEN = false`, `STADTPLAN_EXPORT = "https://geo.essen.de/arcgis/rest/services/historischerverein/Stadtplan_1935/MapServer/export"`, `ESSEN_MITTE = [7.0131, 51.4556]`, `DES_PROJEKT = "https://des.genealogy.net/essen1936/"`, `DATEN = "daten/"`.
  - `schluessel.js`: `falte(text) -> string` (identisch zu Python `falte`), `praefix2(text) -> string`.
  - `zustand.js`: `STANDARD = {q:"", ebene:["I","II","III"], stadtteil:"", praez:["haus","strasse","stadtplan"], beruf:"", thema:"", id:"", karte:"positron", plan:0, zechen:0, z:null, c:null}`; `liesZustand(search: string) -> Zustand`; `schreibeZustand(z: Zustand) -> string` (Query-String ohne `?`, nur Abweichungen vom Standard, Schlüssel alphabetisch); `zustandGleich(a, b) -> boolean`.

- [ ] **Step 1: Bibliotheken lokal ablegen**

```bash
mkdir -p site/vendor site/js site/tests site/css site/bilder site/daten/themen
curl -sSL -o site/vendor/maplibre-gl.js  https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js
curl -sSL -o site/vendor/maplibre-gl.css https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css
curl -sSL -o site/vendor/pmtiles.js      https://unpkg.com/pmtiles@3.2.1/dist/pmtiles.js
head -c 300 site/vendor/pmtiles.js; grep -c . site/vendor/maplibre-gl.js
```

`site/vendor/README.md`:

```markdown
# Fremdbibliotheken

| Datei | Version | Lizenz | Quelle |
|---|---|---|---|
| maplibre-gl.js, maplibre-gl.css | 4.7.1 | BSD-3-Clause | https://github.com/maplibre/maplibre-gl-js |
| pmtiles.js | 3.2.1 | BSD-3-Clause | https://github.com/protomaps/PMTiles |

Lokal abgelegt, damit die Seite ohne CDN läuft (Datenschutz, Reproduzierbarkeit).
```

- [ ] **Step 2: Failing tests für `schluessel.js` und `zustand.js`**

`site/tests/schluessel.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { falte, praefix2 } from "../js/schluessel.js";

test("falte spiegelt die Python-Funktion", () => {
  assert.equal(falte("Grenzstraße"), "grenzstrasse");
  assert.equal(falte("Müller-Lüdenscheidt, Ä."), "mueller luedenscheidt ae");
  assert.equal(falte("  St.  Ännchen "), "st aennchen");
  assert.equal(falte(""), "");
});

test("praefix2", () => {
  assert.equal(praefix2("Sepeur"), "se");
  assert.equal(praefix2("Ö"), "oe");
  assert.equal(praefix2("M. Jäger"), "mj");
  assert.equal(praefix2(""), "_");
});
```

`site/tests/zustand.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { STANDARD, liesZustand, schreibeZustand, zustandGleich } from "../js/zustand.js";

test("leerer Query ergibt Standard", () => {
  assert.deepEqual(liesZustand(""), STANDARD);
  assert.deepEqual(liesZustand("?"), STANDARD);
});

test("Parameter werden gelesen und getippt", () => {
  const z = liesZustand("?q=Sepeur&ebene=I,II&praez=haus&plan=0.5&zechen=1&z=15.2&c=7.06,51.49&id=abc&karte=liberty");
  assert.equal(z.q, "Sepeur");
  assert.deepEqual(z.ebene, ["I", "II"]);
  assert.deepEqual(z.praez, ["haus"]);
  assert.equal(z.plan, 0.5);
  assert.equal(z.zechen, 1);
  assert.equal(z.z, 15.2);
  assert.deepEqual(z.c, [7.06, 51.49]);
  assert.equal(z.id, "abc");
  assert.equal(z.karte, "liberty");
});

test("ungültige Werte fallen auf Standard zurück", () => {
  const z = liesZustand("?ebene=X,I&karte=bunt&plan=7&c=a,b&z=abc");
  assert.deepEqual(z.ebene, ["I"]);
  assert.equal(z.karte, "positron");
  assert.equal(z.plan, 1);
  assert.equal(z.c, null);
  assert.equal(z.z, null);
});

test("schreibeZustand lässt Standardwerte weg und sortiert", () => {
  assert.equal(schreibeZustand(STANDARD), "");
  const s = schreibeZustand({ ...STANDARD, q: "Grenzstr. Katernberg", ebene: ["I"], c: [7.06, 51.49], z: 15 });
  assert.equal(s, "c=7.06,51.49&ebene=I&q=Grenzstr.+Katernberg&z=15");
  assert.deepEqual(liesZustand("?" + s), { ...STANDARD, q: "Grenzstr. Katernberg", ebene: ["I"], c: [7.06, 51.49], z: 15 });
});

test("zustandGleich vergleicht tief", () => {
  assert.ok(zustandGleich(liesZustand("?ebene=I,II"), { ...STANDARD, ebene: ["I", "II"] }));
  assert.ok(!zustandGleich(STANDARD, { ...STANDARD, q: "x" }));
});
```

- [ ] **Step 3: Tests laufen lassen, müssen fehlschlagen**

Run: `node --test site/tests/`
Expected: Fehler „Cannot find module“.

- [ ] **Step 4: Module schreiben**

`site/js/konfig.js`:

```js
// Konstanten der Karte. PLAN_FREIGEGEBEN erst auf true setzen, wenn die Rechte am Stadtplan 1935 geklärt sind.
export const STILE = {
  positron: "https://tiles.openfreemap.org/styles/positron",
  liberty: "https://tiles.openfreemap.org/styles/liberty",
};
export const FARBEN = { I: "#1d4ed8", II: "#ca8a04", III: "#c2410c", neutral: "#1f2937", treffer: "#dc2626", auswahl: "#111827" };
export const EBENEN = { I: "Einwohner", II: "Eigentümer", III: "Gewerbe" };
export const PRAEZISION = {
  haus: "hausgenau verortet",
  strasse: "Straße bekannt, Hausnummer nicht verortbar",
  stadtplan: "Punkt vom Stadtplan 1935, Straße heute verschwunden",
};
export const PLAN_FREIGEGEBEN = false;
export const STADTPLAN_EXPORT = "https://geo.essen.de/arcgis/rest/services/historischerverein/Stadtplan_1935/MapServer/export";
export const ESSEN_MITTE = [7.0131, 51.4556];
export const DES_PROJEKT = "https://des.genealogy.net/essen1936/";
export const DATEN = "daten/";
```

`site/js/schluessel.js`:

```js
// Suchschlüssel, identisch zu pipeline/lib/karte_export.py falte(): klein, Umlaute aufgelöst,
// Akzente entfernt, nur a–z, 0–9 und einzelne Leerzeichen.
const UMLAUTE = { ä: "ae", ö: "oe", ü: "ue", ß: "ss" };

export function falte(text) {
  let t = (text || "").toLowerCase().replace(/[äöüß]/g, (c) => UMLAUTE[c]);
  t = t.normalize("NFKD").replace(/[^\x00-\x7f]/g, "");
  t = t.replace(/[^a-z0-9 ]+/g, " ");
  return t.split(/\s+/).filter(Boolean).join(" ");
}

export function praefix2(text) {
  const k = falte(text).replace(/ /g, "");
  return k ? k.slice(0, 2) : "_";
}
```

`site/js/zustand.js`:

```js
// Der gesamte Zustand der Kartenseite liegt in der URL (Spec §4): reproduzierbare Links.
export const STANDARD = Object.freeze({
  q: "", ebene: ["I", "II", "III"], stadtteil: "", praez: ["haus", "strasse", "stadtplan"], beruf: "",
  thema: "", id: "", karte: "positron", plan: 0, zechen: 0, z: null, c: null,
});
const EBENEN = ["I", "II", "III"];
const PRAEZ = ["haus", "strasse", "stadtplan"];
const KARTEN = ["positron", "liberty"];

function liste(wert, erlaubt, standard) {
  if (wert === null) return [...standard];
  const l = wert.split(",").filter((x) => erlaubt.includes(x));
  return l.length ? l : [...standard];
}

function zahl(wert, min, max, standard) {
  if (wert === null) return standard;
  const n = Number(wert);
  if (Number.isNaN(n)) return standard;
  return Math.min(Math.max(n, min), max);
}

export function liesZustand(search) {
  const p = new URLSearchParams((search || "").replace(/^\?/, ""));
  const c = p.get("c") ? p.get("c").split(",").map(Number) : null;
  return {
    q: p.get("q") || "",
    ebene: liste(p.get("ebene"), EBENEN, STANDARD.ebene),
    stadtteil: p.get("stadtteil") || "",
    praez: liste(p.get("praez"), PRAEZ, STANDARD.praez),
    beruf: p.get("beruf") || "",
    thema: p.get("thema") || "",
    id: p.get("id") || "",
    karte: KARTEN.includes(p.get("karte")) ? p.get("karte") : STANDARD.karte,
    plan: zahl(p.get("plan"), 0, 1, 0),
    zechen: p.get("zechen") === "1" ? 1 : 0,
    z: p.get("z") !== null && !Number.isNaN(Number(p.get("z"))) ? Number(p.get("z")) : null,
    c: c && c.length === 2 && c.every((x) => !Number.isNaN(x)) ? c : null,
  };
}

function gleich(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function schreibeZustand(z) {
  const p = new URLSearchParams();
  for (const k of Object.keys(STANDARD).sort()) {
    const w = z[k];
    if (gleich(w, STANDARD[k]) || w === null || w === "") continue;
    p.set(k, Array.isArray(w) ? w.join(",") : String(w));
  }
  // URLSearchParams kodiert Kommas als %2C; für lesbare Links (c=7.06,51.49) zurücknehmen.
  return p.toString().replace(/%2C/g, ",");
}

export function zustandGleich(a, b) {
  return schreibeZustand(a) === schreibeZustand(b);
}
```

- [ ] **Step 5: Tests laufen lassen**

Run: `node --test site/tests/`
Expected: alle PASS. Zusätzlich Gleichheit mit Python prüfen:

```bash
python3 -c "from pipeline.lib.karte_export import falte; print(falte('Müller-Lüdenscheidt, Ä.'), '|', falte('Straße 1a/2'))"
node -e "import('./site/js/schluessel.js').then(m => console.log(m.falte('Müller-Lüdenscheidt, Ä.'), '|', m.falte('Straße 1a/2')))"
```

Expected: beide Zeilen identisch (`mueller luedenscheidt ae | strasse 1a 2`).

- [ ] **Step 6: Commit**

```bash
git add site/vendor site/js/konfig.js site/js/schluessel.js site/js/zustand.js site/tests
git commit -m "feat: Frontend-Gerüst — Bibliotheken lokal, Konfiguration, Schlüsselfaltung, URL-Zustand

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Datenzugriff und Suche (`daten.js`, `suche.js`)

**Files:**
- Create: `site/js/daten.js`, `site/js/suche.js`
- Test: `site/tests/suche.test.js`

**Interfaces:**
- Consumes: `falte`, `praefix2`, `DATEN`.
- Produces:
  - `daten.js`: `class Lader { constructor(basis = DATEN, fetchFn = fetch) }` mit `async json(pfad)` (Cache je Pfad; 404 → `null`), `async scherbe(adressId) -> Array|null` (Einträge des Hauses), `async namen(praefix)`, `async firmen(praefix)`, `async berufeScherbe(praefix)`, `async strassen()`, `async berufe()`, `async stadtteile()`, `async kennzahlen()`, `async thema(id)`.
  - `suche.js`: `async vorschlaege(q, lader) -> {personen: [...], strassen: [...], firmen: [...], berufe: [...]}` (je Gruppe maximal 5/3/3/3 plus `gesamt`), Elemente: Person `{art:"person", text, untertitel, eintragId, adressId}`, Straße `{art:"strasse", text, untertitel, adressen, name}`, Firma `{art:"firma", text, untertitel, eintragId, adressId}`, Beruf `{art:"beruf", text, untertitel, beruf}`; `async treffer(auswahl, lader) -> {adressIds: string[], zaehler: Map<adressId, n>, personen: Array|null, hinweisHJ: boolean}`; `hinweisHJ(q) -> boolean`.

- [ ] **Step 1: Failing tests mit Fake-Fetch**

`site/tests/suche.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { Lader } from "../js/daten.js";
import { vorschlaege, treffer, hinweisHJ } from "../js/suche.js";

const DATEIEN = {
  "daten/suche/namen/se.json": [
    ["sepeur anna", "Sepeur", "Anna", "Bergm.", "Lattenkamp 27, Katernberg", "2", "b2", "I"],
    ["sepeur wilh", "Sepeur", "Wilh.", "Bergm.", "Lattenkamp 25, Katernberg", "1", "a1", "I"],
    ["seppelt karl", "Seppelt", "Karl", "Kfm.", "Viehofer Str. 3", "3", "c3", "I"],
  ],
  "daten/suche/firmen/se.json": [["sepp soehne kohlen", "Sepp & Söhne, Kohlen", "Viehofer Str. 3", "9", "c3"]],
  "daten/suche/strassen.json": [
    { schluessel: "grenzstr", name: "Grenzstr.", art: "1936", ort: "Katernberg", zeilen: 3, adressen: ["a1", "b2"] },
    { schluessel: "lattenkamp", name: "Lattenkamp", art: "heute", ort: "Katernberg", zeilen: 3, adressen: ["a1", "b2"] },
  ],
  "daten/suche/berufe.json": [["bergm", "Bergm.", 2], ["kfm", "Kfm.", 1]],
  "daten/suche/berufe/be.json": { "Bergm.": [["a1", 1], ["b2", 1]] },
};
const fetchFake = async (url) => ({
  ok: url in DATEIEN, status: url in DATEIEN ? 200 : 404, json: async () => DATEIEN[url],
});
const lader = () => new Lader("daten/", fetchFake);

test("Lader cached und liefert null bei 404", async () => {
  const l = lader();
  assert.equal(await l.namen("xx"), null);
  const a = await l.namen("se"); const b = await l.namen("se");
  assert.equal(a, b);
});

test("vorschlaege gruppiert und begrenzt", async () => {
  const v = await vorschlaege("Sep", lader());
  assert.deepEqual(v.personen.map((p) => p.text), ["Sepeur, Anna", "Sepeur, Wilh.", "Seppelt, Karl"]);
  assert.equal(v.personen[1].adressId, "a1");
  assert.equal(v.firmen[0].text, "Sepp & Söhne, Kohlen");
  assert.deepEqual(v.strassen, []);
  assert.equal(v.gesamt, 4);
});

test("vorschlaege Nachname Vorname und Straße 1936", async () => {
  const v = await vorschlaege("sepeur w", lader());
  assert.deepEqual(v.personen.map((p) => p.text), ["Sepeur, Wilh."]);
  const s = await vorschlaege("Grenz", lader());
  assert.equal(s.strassen[0].text, "Grenzstr. (Katernberg)");
  assert.equal(s.strassen[0].untertitel, "Name 1936 · 3 Einträge");
  const b = await vorschlaege("berg", lader());
  assert.equal(b.berufe[0].text, "Bergm.");
});

test("treffer für Straße, Beruf und Person", async () => {
  const s = await treffer({ art: "strasse", adressen: ["a1", "b2"], name: "Lattenkamp" }, lader());
  assert.deepEqual(s.adressIds, ["a1", "b2"]);
  const b = await treffer({ art: "beruf", beruf: "Bergm." }, lader());
  assert.deepEqual([...b.zaehler.entries()], [["a1", 1], ["b2", 1]]);
  const p = await treffer({ art: "person", q: "Sepeur" }, lader());
  assert.deepEqual(p.adressIds, ["b2", "a1"]);
  assert.equal(p.personen.length, 2);
});

test("Hinweis auf Lücke H–J", async () => {
  assert.ok(hinweisHJ("Hoffmann"));
  assert.ok(hinweisHJ("jäger"));
  assert.ok(!hinweisHJ("Sepeur"));
  const t = await treffer({ art: "person", q: "Hoffmann" }, lader());
  assert.equal(t.hinweisHJ, true);
  assert.deepEqual(t.adressIds, []);
});
```

- [ ] **Step 2: Tests laufen lassen, müssen fehlschlagen**

Run: `node --test site/tests/suche.test.js`
Expected: „Cannot find module“.

- [ ] **Step 3: Module schreiben**

`site/js/daten.js`:

```js
import { DATEN } from "./konfig.js";

// Lädt Dateien des Datenpakets und hält sie im Speicher. Ein 404 (Scherbe existiert nicht) ist
// kein Fehler, sondern "keine Daten" → null.
export class Lader {
  constructor(basis = DATEN, fetchFn = (u) => fetch(u)) {
    this.basis = basis;
    this.fetchFn = fetchFn;
    this.cache = new Map();
  }

  async json(pfad) {
    const url = this.basis + pfad;
    if (!this.cache.has(url)) {
      this.cache.set(url, (async () => {
        const r = await this.fetchFn(url);
        if (!r.ok) {
          if (r.status === 404) return null;
          throw new Error(`Laden fehlgeschlagen: ${url} (${r.status})`);
        }
        return r.json();
      })());
    }
    return this.cache.get(url);
  }

  async scherbe(adressId) {
    const s = await this.json(`haus/${adressId.slice(0, 2)}.json`);
    return s && s[adressId] ? s[adressId] : null;
  }
  namen(praefix) { return this.json(`suche/namen/${praefix}.json`); }
  firmen(praefix) { return this.json(`suche/firmen/${praefix}.json`); }
  berufeScherbe(praefix) { return this.json(`suche/berufe/${praefix}.json`); }
  strassen() { return this.json("suche/strassen.json"); }
  berufe() { return this.json("suche/berufe.json"); }
  stadtteile() { return this.json("suche/stadtteile.json"); }
  kennzahlen() { return this.json("kennzahlen.json"); }
  thema(id) { return this.json(`themen/${id}.json`); }
}
```

`site/js/suche.js`:

```js
import { falte, praefix2 } from "./schluessel.js";

const MAX = { personen: 5, strassen: 3, firmen: 3, berufe: 3 };

export function hinweisHJ(q) {
  const k = falte(q);
  return /^[hij]/.test(k);
}

function person(z) {
  return { art: "person", text: `${z[1]}, ${z[2]}`.replace(/, $/, ""), untertitel: [z[3], z[4]].filter(Boolean).join(" · "),
           eintragId: z[5], adressId: z[6], teil: z[7], q: z[1] };
}

function strasse(s) {
  const art = s.art === "1936" ? "Name 1936" : "heutiger Name";
  return { art: "strasse", text: `${s.name} (${s.ort})`, untertitel: `${art} · ${s.zeilen} Einträge`,
           adressen: s.adressen, name: s.name };
}

export async function vorschlaege(q, lader) {
  const k = falte(q);
  const leer = { personen: [], strassen: [], firmen: [], berufe: [], gesamt: 0 };
  if (k.length < 2) return leer;
  const [namen, firmen, strassen, berufe] = await Promise.all([
    lader.namen(praefix2(k)), lader.firmen(praefix2(k)), lader.strassen(), lader.berufe()]);
  const alleP = (namen || []).filter((z) => z[0].startsWith(k)).map(person);
  const alleS = (strassen || []).filter((s) => s.schluessel.startsWith(k)).map(strasse);
  const alleF = (firmen || []).filter((z) => z[0].startsWith(k))
    .map((z) => ({ art: "firma", text: z[1], untertitel: z[2], eintragId: z[3], adressId: z[4] }));
  const alleB = (berufe || []).filter((z) => z[0].startsWith(k))
    .map((z) => ({ art: "beruf", text: z[1], untertitel: `${z[2]} Einträge`, beruf: z[1] }));
  return {
    personen: alleP.slice(0, MAX.personen), strassen: alleS.slice(0, MAX.strassen),
    firmen: alleF.slice(0, MAX.firmen), berufe: alleB.slice(0, MAX.berufe),
    gesamt: alleP.length + alleS.length + alleF.length + alleB.length,
  };
}

// Auswahl → Treffermenge. adressIds sind die Häuser, die die Karte hervorhebt; zaehler zählt
// Einträge je Haus; personen ist nur bei Namenssuche gefüllt (Liste zeigt dann Personen).
export async function treffer(auswahl, lader) {
  const zaehler = new Map();
  let personen = null;
  let hinweis = false;
  if (auswahl.art === "strasse") {
    for (const a of auswahl.adressen) zaehler.set(a, (zaehler.get(a) || 0) + 1);
  } else if (auswahl.art === "beruf") {
    const s = await lader.berufeScherbe(praefix2(auswahl.beruf));
    for (const [a, n] of (s && s[auswahl.beruf]) || []) zaehler.set(a, n);
  } else if (auswahl.art === "person") {
    const k = falte(auswahl.q);
    const namen = (await lader.namen(praefix2(k))) || [];
    personen = namen.filter((z) => z[0].startsWith(k)).map(person);
    for (const p of personen) zaehler.set(p.adressId, (zaehler.get(p.adressId) || 0) + 1);
    hinweis = personen.length === 0 && hinweisHJ(auswahl.q);
  } else if (auswahl.art === "firma") {
    zaehler.set(auswahl.adressId, 1);
  }
  return { adressIds: [...zaehler.keys()], zaehler, personen, hinweisHJ: hinweis };
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/`
Expected: alle PASS.

- [ ] **Step 5: Commit**

```bash
git add site/js/daten.js site/js/suche.js site/tests/suche.test.js
git commit -m "feat: Datenzugriff und Suche mit Sofortvorschlägen (DOM-frei, getestet)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Karte (`karte.js`) — Quellen, Ebenen, Stilwechsel, Feature-State, Popup

**Files:**
- Create: `site/js/karte.js`, `site/bilder/kreis-gestrichelt.svg`, `site/bilder/zeche.svg`
- Create: `site/karte.html` (erste Fassung, nur Karte), `site/css/stil.css` (Grundlayout)
- Test: Sichtprüfung im Browser über `serve.py`; automatische Prüfung folgt in Task 15 (Playwright).

**Interfaces:**
- Consumes: `konfig.js`, `zustand.js` (Zustandsobjekt).
- Produces: `class Karte { constructor(container, zustand, ereignisse) }` mit
  - `ereignisse = { onKlick(adressId, lngLat), onBewegt(z, c), onHover(adressId|null, lngLat) }`;
  - `async bereit()`; `setzeStil(name)` (ruft danach `ebenenAufsetzen()`), `setzeFilter(zustand)` (Ebenen, Stadtteil, Präzision, Merkmal aus Thema), `setzeTreffer(adressIds: string[]|null)` (Feature-State `treffer`), `setzeAuswahl(adressId|null)`, `setzeFarbe(regel)` (Themenfarbe, siehe Task 13), `setzePlan(deckkraft)`, `setzeZechen(an)`, `fliegeZu(lngLat, zoom)`, `passeEin(adressIds)` (Bounding-Box aus geladenen Features, Rückfall: kein Zoom), `zeigePopup(lngLat, html)`, `schliessePopup()`.
- Ebenen-IDs: `adressen-haus` (circle), `adressen-ungenau` (symbol, SDF-Icon `kreis-gestrichelt`), `adressen-auswahl` (circle, Ring), `zechen` (symbol), `stadtplan-1935` (raster).

- [ ] **Step 1: Icons anlegen**

`site/bilder/kreis-gestrichelt.svg` (wird beim Laden zu einem SDF-Image gerastert):

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="26" fill="none" stroke="#000" stroke-width="7" stroke-dasharray="11 9" stroke-linecap="round"/>
</svg>
```

`site/bilder/zeche.svg` (Schlägel und Eisen, schematisch):

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <g stroke="#111" stroke-width="5" stroke-linecap="round" fill="none">
    <line x1="10" y1="38" x2="30" y2="14"/><line x1="24" y1="8" x2="36" y2="20"/>
    <line x1="38" y1="38" x2="18" y2="14"/><line x1="12" y1="20" x2="24" y2="8"/>
  </g>
</svg>
```

- [ ] **Step 2: `karte.js` schreiben**

```js
import { STILE, FARBEN, STADTPLAN_EXPORT, ESSEN_MITTE, DATEN } from "./konfig.js";

const RADIUS = ["interpolate", ["linear"], ["ln", ["max", ["var", "n"], 1]], 0, 4, Math.log(100), 10];

function summeAktiv(ebenen) {
  // Summe der Einträge über die aktiven Ebenen als Ausdruck
  return ["+", ...ebenen.map((e) => ["coalesce", ["get", `n_${e}`], 0])];
}

async function ladeIcon(map, name, url, sdf) {
  const img = new Image(64, 64);
  await new Promise((ok, nein) => { img.onload = ok; img.onerror = nein; img.src = url; });
  if (!map.hasImage(name)) map.addImage(name, img, { sdf, pixelRatio: 2 });
}

export class Karte {
  constructor(container, zustand, ereignisse) {
    this.ereignisse = ereignisse;
    this.zustand = zustand;
    this.farbe = null;          // Themenfarbregel (Task 13) oder null
    this.treffer = new Set();
    this.auswahl = null;
    this.protokoll = new pmtiles.Protocol();
    maplibregl.addProtocol("pmtiles", this.protokoll.tile);
    this.map = new maplibregl.Map({
      container, style: STILE[zustand.karte], center: zustand.c || ESSEN_MITTE, zoom: zustand.z ?? 11,
      minZoom: 9, maxZoom: 18, attributionControl: { compact: true },
    });
    this.map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    this.map.addControl(new maplibregl.GeolocateControl({ trackUserLocation: false }), "top-right");
    this.map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");
    this.popup = new maplibregl.Popup({ closeButton: true, maxWidth: "320px", offset: 10 });
    this._bereit = new Promise((ok) => this.map.once("load", ok)).then(() => this.ebenenAufsetzen());
    this.map.on("moveend", () => {
      const c = this.map.getCenter();
      ereignisse.onBewegt(Math.round(this.map.getZoom() * 100) / 100, [+c.lng.toFixed(5), +c.lat.toFixed(5)]);
    });
  }

  bereit() { return this._bereit; }

  async ebenenAufsetzen() {
    const m = this.map;
    await ladeIcon(m, "kreis-gestrichelt", "bilder/kreis-gestrichelt.svg", true);
    await ladeIcon(m, "zeche", "bilder/zeche.svg", false);
    if (!m.getSource("adressen")) {
      m.addSource("adressen", { type: "vector", url: `pmtiles://${new URL(DATEN + "adressen.pmtiles", location.href)}`, promoteId: "id" });
      m.addSource("zechen", { type: "geojson", data: DATEN + "zechen.geojson" });
      m.addSource("stadtplan-1935", {
        type: "raster", tileSize: 256, minzoom: 10, maxzoom: 17,
        tiles: [`${STADTPLAN_EXPORT}?bbox={bbox-epsg-3857}&bboxSR=3857&imageSR=3857&size=256,256&format=png32&transparent=true&f=image`],
        attribution: "Stadtplan 1935: Stadt Essen / Historischer Verein",
      });
    }
    const sl = "adressen";
    m.addLayer({ id: "stadtplan-1935", type: "raster", source: "stadtplan-1935",
                 layout: { visibility: "none" }, paint: { "raster-opacity": 0 } });
    m.addLayer({ id: "adressen-haus", type: "circle", source: "adressen", "source-layer": sl,
                 filter: ["==", ["get", "stufe"], "haus"], paint: { "circle-stroke-width": 0 } });
    m.addLayer({ id: "adressen-ungenau", type: "symbol", source: "adressen", "source-layer": sl,
                 filter: ["!=", ["get", "stufe"], "haus"],
                 layout: { "icon-image": "kreis-gestrichelt", "icon-allow-overlap": true, "icon-ignore-placement": true } });
    m.addLayer({ id: "adressen-auswahl", type: "circle", source: "adressen", "source-layer": sl,
                 filter: ["==", ["get", "id"], ""],
                 paint: { "circle-radius": 14, "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": FARBEN.auswahl, "circle-stroke-width": 3 } });
    m.addLayer({ id: "zechen", type: "symbol", source: "zechen", filter: ["==", ["get", "aktiv_1936"], true],
                 layout: { visibility: "none", "icon-image": "zeche", "icon-size": 0.6, "text-field": ["get", "name"],
                           "text-size": 11, "text-offset": [0, 1.4], "text-anchor": "top", "icon-allow-overlap": true },
                 paint: { "text-halo-color": "#fff", "text-halo-width": 1.5 } });
    for (const id of ["adressen-haus", "adressen-ungenau"]) {
      m.on("click", id, (e) => this.ereignisse.onKlick(e.features[0].properties.id, e.lngLat));
      m.on("mouseenter", id, (e) => { m.getCanvas().style.cursor = "pointer"; this.ereignisse.onHover(e.features[0].properties.id, e.lngLat); });
      m.on("mouseleave", id, () => { m.getCanvas().style.cursor = ""; this.ereignisse.onHover(null, null); });
    }
    m.on("click", "zechen", (e) => {
      const p = e.features[0].properties;
      this.zeigePopup(e.lngLat, `<b>${p.name}</b><br>${p.stadtteil || ""}<br>in Betrieb ${p.betrieb_von}–${p.betrieb_bis}` +
        (p.quelle ? `<br><a href="${p.quelle}" target="_blank" rel="noopener">Wikipedia</a>` : ""));
    });
    this.setzeFilter(this.zustand);
    this.setzePlan(this.zustand.plan);
    this.setzeZechen(this.zustand.zechen);
    this.setzeTreffer(this.treffer.size ? [...this.treffer] : null);
    this.setzeAuswahl(this.auswahl);
  }

  setzeStil(name) {
    this.map.setStyle(STILE[name]);
    this._bereit = new Promise((ok) => this.map.once("style.load", ok)).then(() => this.ebenenAufsetzen());
    return this._bereit;
  }

  // Farbe und Größe aus Zustand + Themenregel ableiten und auf beide Adressebenen legen.
  setzeFilter(z) {
    this.zustand = z;
    const m = this.map;
    const n = summeAktiv(z.ebene);
    const bedingungen = [[">", n, 0], ["in", ["get", "stufe"], ["literal", z.praez]]];
    if (z.stadtteil) bedingungen.push(["==", ["get", "stadtteil"], z.stadtteil]);
    if (this.farbe && this.farbe.merkmal) bedingungen.push([">", ["coalesce", ["get", `m_${this.farbe.merkmal}`], 0], 0]);
    bedingungen.push(["any", [">=", ["zoom"], 12], [">=", n, 5]]);   // Stadtansicht nicht zulaufen lassen
    const grund = this.farbe ? this.farbe.ausdruck : (z.ebene.length === 1 ? FARBEN[z.ebene[0]] : FARBEN.neutral);
    const farbe = ["case", ["boolean", ["feature-state", "treffer"], false], FARBEN.treffer, grund];
    const radius = ["let", "n", n, RADIUS];
    m.setFilter("adressen-haus", ["all", ["==", ["get", "stufe"], "haus"], ...bedingungen]);
    m.setFilter("adressen-ungenau", ["all", ["!=", ["get", "stufe"], "haus"], ...bedingungen]);
    m.setPaintProperty("adressen-haus", "circle-color", farbe);
    m.setPaintProperty("adressen-haus", "circle-radius", radius);
    m.setPaintProperty("adressen-ungenau", "icon-color", farbe);
    m.setLayoutProperty("adressen-ungenau", "icon-size", ["/", ["let", "n", n, RADIUS], 16]);
    this._deckkraftSetzen();
  }

  // Ohne Treffermenge sind alle Punkte voll sichtbar; mit Treffermenge nur die Treffer, der Rest gedimmt.
  _deckkraftSetzen() {
    const d = this.treffer.size ? ["case", ["boolean", ["feature-state", "treffer"], false], 0.9, 0.25] : 0.9;
    this.map.setPaintProperty("adressen-haus", "circle-opacity", d);
    this.map.setPaintProperty("adressen-ungenau", "icon-opacity", d);
  }

  setzeFarbe(regel) { this.farbe = regel; this.setzeFilter(this.zustand); }

  // Treffer per Feature-State: alle bisherigen zurücksetzen, neue setzen, Rest dimmen.
  setzeTreffer(adressIds) {
    const m = this.map;
    if (!m.getSource("adressen")) return;
    m.removeFeatureState({ source: "adressen", sourceLayer: "adressen" });
    this.treffer = new Set(adressIds || []);
    for (const id of this.treffer) m.setFeatureState({ source: "adressen", sourceLayer: "adressen", id }, { treffer: true });
    this._deckkraftSetzen();
  }

  setzeAuswahl(adressId) {
    this.auswahl = adressId;
    if (this.map.getLayer("adressen-auswahl")) this.map.setFilter("adressen-auswahl", ["==", ["get", "id"], adressId || ""]);
  }

  setzePlan(deckkraft) {
    if (!this.map.getLayer("stadtplan-1935")) return;
    this.map.setLayoutProperty("stadtplan-1935", "visibility", deckkraft > 0 ? "visible" : "none");
    this.map.setPaintProperty("stadtplan-1935", "raster-opacity", deckkraft);
  }

  setzeZechen(an) {
    if (this.map.getLayer("zechen")) this.map.setLayoutProperty("zechen", "visibility", an ? "visible" : "none");
  }

  fliegeZu(lngLat, zoom = 16) { this.map.flyTo({ center: lngLat, zoom: Math.max(this.map.getZoom(), zoom), duration: 600 }); }

  // Auf die geladenen Treffer einpassen; nicht geladene Kacheln kennen wir nicht → dann kein Zoom.
  passeEin(adressIds) {
    const ids = new Set(adressIds);
    const f = this.map.querySourceFeatures("adressen", { sourceLayer: "adressen" }).filter((x) => ids.has(x.properties.id));
    if (!f.length) return false;
    const b = new maplibregl.LngLatBounds();
    for (const x of f) b.extend(x.geometry.coordinates);
    this.map.fitBounds(b, { padding: 60, maxZoom: 16, duration: 600 });
    return true;
  }

  // Koordinate eines Punktes aus den geladenen Kacheln (für die Liste → Karte-Kopplung).
  position(adressId) {
    const f = this.map.querySourceFeatures("adressen", { sourceLayer: "adressen", filter: ["==", ["get", "id"], adressId] });
    return f.length ? f[0].geometry.coordinates : null;
  }

  zeigePopup(lngLat, html) { this.popup.setLngLat(lngLat).setHTML(html).addTo(this.map); }
  schliessePopup() { this.popup.remove(); }
}
```

Hinweis zur Größe der Strichel-Icons: `icon-size` ist ein Faktor auf das 64-px-Bild bei `pixelRatio: 2` (32 px logisch, Radius 16 px); `radius/16` ergibt denselben Radius wie die gefüllten Kreise. Wenn die Ringe sichtbar größer wirken als die Kreise, den Teiler auf 14 setzen und im Browser vergleichen.

- [ ] **Step 3: `karte.html` und `stil.css` (Grundlayout)**

`site/karte.html`:

```html
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Essen 1936 – Karte</title>
<link rel="stylesheet" href="vendor/maplibre-gl.css">
<link rel="stylesheet" href="css/stil.css">
</head>
<body class="kartenseite">
<a class="logo" href="index.html">Essen 1936</a>
<aside id="sidebar" class="sidebar" data-stufe="halb" aria-label="Suche und Ergebnisse">
  <div class="griff" id="griff" role="button" aria-label="Ergebnisse ein- oder ausklappen"></div>
  <div id="themenkopf" hidden></div>
  <div class="suchfeld">
    <input id="suche" type="search" placeholder="Name, Straße, Firma, Beruf …" autocomplete="off" aria-label="Suche">
    <button id="suche-leeren" type="button" aria-label="Suche leeren" hidden>✕</button>
    <div id="vorschlaege" class="vorschlaege" hidden></div>
  </div>
  <div class="pills" id="pills"></div>
  <div id="inhalt" class="inhalt"></div>
</aside>
<div id="karte" class="karte"></div>
<div id="steuerung" class="steuerung"></div>
<div id="legende" class="legende"></div>
<div class="vermerk" id="vermerk"></div>
<script src="vendor/maplibre-gl.js"></script>
<script src="vendor/pmtiles.js"></script>
<script type="module" src="js/app.js"></script>
</body>
</html>
```

`site/css/stil.css` (Grundlayout; Details der Sidebar in Task 11):

```css
:root { --blau: #1d4ed8; --gold: #ca8a04; --rot: #c2410c; --neutral: #1f2937; --rand: #d8d4cc; --papier: #faf8f3; --text: #1f2328; --grau: #6b7280; --breite-sidebar: 360px; }
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; color: var(--text); background: var(--papier); }
a { color: var(--blau); }
.kartenseite { overflow: hidden; }
.karte { position: fixed; inset: 0; }
.logo { position: fixed; top: 10px; left: 10px; z-index: 5; background: #fff; padding: 6px 10px; border-radius: 8px; text-decoration: none; font-weight: 700; color: var(--text); box-shadow: 0 1px 4px rgba(0,0,0,.2); }
.sidebar { position: fixed; z-index: 4; background: #fff; display: flex; flex-direction: column; box-shadow: 0 0 12px rgba(0,0,0,.2); }
.griff { display: none; }
.suchfeld { position: relative; padding: 10px 12px 6px; }
.suchfeld input { width: 100%; padding: 10px 36px 10px 12px; border: 1px solid var(--rand); border-radius: 8px; font-size: 16px; }
.suchfeld button { position: absolute; right: 18px; top: 16px; border: 0; background: none; font-size: 16px; cursor: pointer; }
.vorschlaege { position: absolute; left: 12px; right: 12px; top: 52px; background: #fff; border: 1px solid var(--rand); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,.15); z-index: 6; max-height: 60vh; overflow: auto; }
.vorschlaege .gruppe { padding: 6px 10px 2px; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: var(--grau); }
.vorschlaege .eintrag { padding: 6px 10px; cursor: pointer; border-top: 1px solid #f1f1f1; min-height: 44px; }
.vorschlaege .eintrag:hover, .vorschlaege .eintrag.aktiv { background: #eef2ff; }
.vorschlaege small { display: block; color: var(--grau); }
.pills { display: flex; gap: 6px; flex-wrap: wrap; padding: 4px 12px 8px; }
.pill { border: 1px solid #999; background: #fff; border-radius: 16px; padding: 6px 12px; font-size: 13px; cursor: pointer; min-height: 32px; }
.pill[aria-pressed="true"] { color: #fff; border-color: transparent; }
.pill.I[aria-pressed="true"] { background: var(--blau); } .pill.II[aria-pressed="true"] { background: var(--gold); } .pill.III[aria-pressed="true"] { background: var(--rot); }
.inhalt { flex: 1; overflow: auto; padding: 0 12px 12px; }
.steuerung { position: fixed; z-index: 4; right: 10px; top: 110px; display: flex; flex-direction: column; gap: 6px; }
.steuerung button, .steuerung label { background: #fff; border: 1px solid var(--rand); border-radius: 6px; padding: 6px 8px; font-size: 12px; cursor: pointer; min-height: 32px; }
.legende { position: fixed; z-index: 4; right: 10px; bottom: 28px; background: #fff; border-radius: 8px; padding: 8px 10px; font-size: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.2); max-width: 220px; }
.legende .zeile { display: flex; align-items: center; gap: 6px; margin: 2px 0; }
.legende .punkt { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.legende .punkt.ungenau { background: none !important; border: 2px dashed currentColor; }
.vermerk { position: fixed; z-index: 4; left: 10px; bottom: 6px; font-size: 11px; color: var(--grau); background: rgba(255,255,255,.8); padding: 2px 6px; border-radius: 4px; }
.maplibregl-popup-content { font-size: 13px; line-height: 1.35; padding: 10px 12px; }

@media (min-width: 900px) {
  .sidebar { top: 0; bottom: 0; left: 0; width: var(--breite-sidebar); }
  .logo { left: calc(var(--breite-sidebar) + 10px); }
  .suchfeld { padding-top: 14px; }
}
@media (max-width: 899px) {
  .sidebar { left: 0; right: 0; bottom: 0; border-radius: 14px 14px 0 0; transition: height .2s; }
  .sidebar[data-stufe="griff"] { height: 120px; }
  .sidebar[data-stufe="halb"] { height: 45vh; }
  .sidebar[data-stufe="voll"] { height: 92vh; }
  .griff { display: block; width: 40px; height: 5px; border-radius: 3px; background: #bbb; margin: 8px auto 0; cursor: grab; }
  .steuerung { top: 60px; }
  .legende { display: none; }
  .legende.offen { display: block; bottom: auto; top: 60px; right: 56px; }
  .vermerk { display: none; }
}
```

- [ ] **Step 4: Minimal-`app.js` für die Sichtprüfung**

`site/js/app.js` (wird in Task 11 vollständig):

```js
import { Karte } from "./karte.js";
import { liesZustand } from "./zustand.js";

const zustand = liesZustand(location.search);
const karte = new Karte("karte", zustand, {
  onKlick: (id, lngLat) => karte.zeigePopup(lngLat, `<b>${id}</b>`),
  onBewegt: () => {},
  onHover: () => {},
});
await karte.bereit();
window.karte = karte;
```

Run: `python3 werkzeuge/serve.py 8765` (falls nicht läuft) und `http://localhost:8765/site/karte.html?z=14&c=7.045,51.486` öffnen.
Expected: Positron-Karte, blaue Kreise und gestrichelte Ringe in Katernberg, Klick zeigt die Adress-ID; `?karte=liberty` zeigt Liberty; Konsole ohne Fehler. Mit Playwright prüfen, wenn kein Browser zur Hand:

```bash
python3 - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); s = b.new_page(viewport={"width": 1200, "height": 800})
    fehler = []; s.on("pageerror", lambda e: fehler.append(str(e)))
    s.goto("http://localhost:8765/site/karte.html?z=15&c=7.045,51.486"); s.wait_for_timeout(4000)
    print("Fehler:", fehler); print("Punkte:", s.evaluate("karte.map.queryRenderedFeatures({layers:['adressen-haus','adressen-ungenau']}).length"))
    s.screenshot(path="/tmp/claude-1000/karte.png"); b.close()
PY
```

Expected: `Fehler: []`, Punkte > 50.

- [ ] **Step 5: Commit**

```bash
git add site/js/karte.js site/js/app.js site/karte.html site/css/stil.css site/bilder
git commit -m "feat: Kartenkomponente — PMTiles-Punkte, Strichel-Icons, Stilwechsel, Feature-State, Stadtplan, Zechen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: Sidebar, Popup-Inhalte, Filter und Verdrahtung (`sidebar.js`, `popup.js`, `app.js`)

**Files:**
- Create: `site/js/popup.js` (HTML-Erzeugung für Popup und Hausansicht, DOM-frei), `site/js/sidebar.js`, `site/js/app.js` (vollständig)
- Modify: `site/css/stil.css` (Listen, Detail, Filter)
- Test: `site/tests/popup.test.js`

**Interfaces:**
- Consumes: `Karte`, `Lader`, `vorschlaege`, `treffer`, `liesZustand`/`schreibeZustand`, `FARBEN`, `EBENEN`, `PRAEZISION`, `DES_PROJEKT`.
- Produces:
  - `popup.js`: `esc(text)`, `popupHtml(eig, eintraege, kompakt) -> string` (eig = Punkteigenschaften aus der Kachel; Namen nach Etage in Scherbenreihenfolge; Klickbare Namen mit `data-eintrag`), `hausHtml(eig, eintraege) -> string` (Hausansicht mit Gruppen je Teil, jedem Eintrag `id="e-<id>"`, Seite und Faksimile-Link), `trefferzeileHtml(t) -> string`, `praezisionText(stufe)`, `faksimileUrl(seite) -> string`.
  - `sidebar.js`: `class Sidebar { constructor(el, lader, aktionen) }` mit `aktionen = { onZustand(patch), onHausWaehlen(adressId), onEintragWaehlen(eintragId, adressId), onVorschlag(v), onZurueck(), onExport() }`; Methoden `zeigeSuche(zustand)`, `zeigeTreffer(zustand, ergebnis, adressEigenschaften)`, `zeigeHaus(eig, eintraege, hervorgehoben)`, `zeigeThema(thema|null)`, `setzeStufe("griff"|"halb"|"voll")`, `setzeVorschlaege(gruppen|null)`, `setzeFilteroptionen(stadtteile, berufe)`.
  - `app.js`: verbindet alles; hält `zustand`, schreibt URL (`replaceState` bei Filter/Karte, `pushState` bei Suche/Haus), reagiert auf `popstate`.

- [ ] **Step 1: Failing tests für `popup.js`**

`site/tests/popup.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { popupHtml, hausHtml, faksimileUrl, praezisionText, esc } from "../js/popup.js";

const EIG = { id: "a1", stufe: "strasse", strasse_heute: "Lattenkamp", hausnr: "25", stadtteil: "Katernberg",
              historisch: "Grenzstr. 25, Katernberg", n_I: 2, n_II: 1, n_III: 0, nummer_unsicher: "nein" };
const E = [
  { id: "1", teil: "I", seite: "I-551", name: "Sepeur", vorname: "Wilh.", beruf: "Bergm.", etage: "Erdg.", stand: "", flags: [], merkmale: [] },
  { id: "2", teil: "I", seite: "I-402", name: "Kowalski", vorname: "Jos.", beruf: "Hauer", etage: "", stand: "Wwe.", flags: ["nummer_unsicher"], merkmale: [] },
  { id: "3", teil: "II", seite: "II-088", name: "Zeche Zollverein", vorname: "", beruf: "", etage: "", stand: "", eigentuemer: "Eigentümer", flags: [], merkmale: [] },
];

test("esc entschärft HTML", () => {
  assert.equal(esc("<b>&\"'"), "&lt;b&gt;&amp;&quot;&#39;");
});

test("popupHtml: heutige und historische Adresse, Präzision, Namen ohne Seiten", () => {
  const h = popupHtml(EIG, E, false);
  assert.match(h, /Lattenkamp 25, Katernberg/);
  assert.match(h, /historische Adresse: Grenzstr\. 25, Katernberg/);
  assert.match(h, /Straße bekannt, Hausnummer nicht verortbar/);
  assert.match(h, /2 Einwohner · 1 Eigentümer/);
  assert.ok(h.indexOf("Sepeur") < h.indexOf("Kowalski"), "Etage Erdg. vor ohne Etage");
  assert.match(h, /data-eintrag="2"/);
  assert.doesNotMatch(h, /I-551/);
});

test("popupHtml kompakt zeigt höchstens drei Namen", () => {
  const h = popupHtml(EIG, E, true);
  assert.match(h, /alle 3 im Detail/);
});

test("hausHtml gruppiert nach Teil und verlinkt das Faksimile", () => {
  const h = hausHtml(EIG, E);
  assert.match(h, /Einwohner \(2\)/);
  assert.match(h, /Eigentümer \(1\)/);
  assert.match(h, /id="e-1"/);
  assert.match(h, /Seite I-551/);
  assert.match(h, new RegExp(faksimileUrl("I-551").replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  assert.match(h, /Hausnummer unsicher/);
});

test("praezisionText und faksimileUrl", () => {
  assert.equal(praezisionText("haus"), "hausgenau verortet");
  assert.match(faksimileUrl("I-551"), /^https:\/\//);
});
```

- [ ] **Step 2: Tests laufen lassen, müssen fehlschlagen**

Run: `node --test site/tests/popup.test.js`
Expected: „Cannot find module“.

- [ ] **Step 3: `popup.js` schreiben**

```js
import { EBENEN, PRAEZISION, DES_PROJEKT } from "./konfig.js";

export function esc(t) {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export function praezisionText(stufe) { return PRAEZISION[stufe] || stufe; }

// Bis der DES-Spike eine seitengenaue URL liefert, führt der Link zur Projektseite; die Seite
// steht daneben, damit man sie dort aufschlagen kann.
export function faksimileUrl(seite) { return DES_PROJEKT + "#" + encodeURIComponent(seite || ""); }

const FLAGTEXT = { nummer_unsicher: "Hausnummer unsicher (Straße neu gezählt)", zeitlich_abweichend: "Straßenname zeitlich abweichend belegt", mehrdeutig: "Zuordnung mehrdeutig" };

export function heutigeAdresse(eig) {
  if (!eig.strasse_heute) return `${eig.historisch} (Stadtplan 1935)`;
  return `${eig.strasse_heute} ${eig.hausnr || ""}`.trim() + (eig.stadtteil ? `, ${eig.stadtteil}` : "");
}

function zaehlerText(eig) {
  return ["I", "II", "III"].filter((t) => eig[`n_${t}`] > 0).map((t) => `${eig[`n_${t}`]} ${EBENEN[t]}`).join(" · ");
}

function nameZeile(e) {
  const name = e.firma && e.teil === "III" ? e.firma : [e.name, e.vorname].filter(Boolean).join(", ");
  const rest = [e.beruf, e.stand].filter(Boolean).join(", ");
  return `<b>${esc(name)}</b>${rest ? ` · ${esc(rest)}` : ""}${e.etage ? ` <span class="etage">${esc(e.etage)}</span>` : ""}`;
}

export function popupHtml(eig, eintraege, kompakt) {
  const max = kompakt ? 3 : 12;
  const zeilen = eintraege.slice(0, max).map((e) => `<div class="pname" data-eintrag="${esc(e.id)}">${nameZeile(e)}</div>`);
  if (eintraege.length > max) zeilen.push(`<div class="pmehr" data-mehr="1">alle ${eintraege.length} im Detail ›</div>`);
  return `<div class="popup-kopf"><b>${esc(heutigeAdresse(eig))}</b>` +
    (eig.strasse_heute ? `<div class="hist">historische Adresse: ${esc(eig.historisch)}</div>` : "") +
    `<div class="praez praez-${esc(eig.stufe)}">${esc(praezisionText(eig.stufe))}</div>` +
    `<div class="zaehler">${esc(zaehlerText(eig))}</div></div>` +
    `<div class="popup-namen">${zeilen.join("")}</div>`;
}

function eintragHtml(e) {
  const felder = [["Beruf", e.beruf], ["Etage laut Buch", e.etage], ["Stand", e.stand],
    ["Bezugsperson", [e.bezug_vorname, e.bezug_beruf].filter(Boolean).join(", ")], ["Firma", e.firma],
    ["Eigentümer", e.eigentuemer], ["Verwalter", e.verwalter], ["Wohnort", e.wohnort]]
    .filter(([, w]) => w).map(([k, w]) => `<div><span class="k">${k}</span> ${esc(w)}</div>`).join("");
  const flags = (e.flags || []).map((f) => `<div class="flag">${esc(FLAGTEXT[f] || f)}</div>`).join("");
  return `<div class="eintrag" id="e-${esc(e.id)}"><div class="ename">${nameZeile(e)}</div>${felder}${flags}` +
    `<div class="quelle">Seite ${esc(e.seite)} · <a href="${faksimileUrl(e.seite)}" target="_blank" rel="noopener">Faksimile beim CompGen</a></div></div>`;
}

export function hausHtml(eig, eintraege) {
  const gruppen = ["I", "II", "III"].map((t) => {
    const l = eintraege.filter((e) => e.teil === t);
    return l.length ? `<h3>${EBENEN[t]} (${l.length})</h3>${l.map(eintragHtml).join("")}` : "";
  }).join("");
  return `<div class="haus-kopf"><h2>${esc(heutigeAdresse(eig))}</h2>` +
    (eig.strasse_heute ? `<div class="hist">historische Adresse: ${esc(eig.historisch)}</div>` : "") +
    `<div class="praez praez-${esc(eig.stufe)}">${esc(praezisionText(eig.stufe))}</div>` +
    (eig.nummer_unsicher === "ja" ? `<div class="flag">${FLAGTEXT.nummer_unsicher}</div>` : "") +
    `</div>${gruppen}`;
}

export function trefferzeileHtml(t) {
  // t = { adressId, titel, untertitel, stufe, n, eintragId? }
  const kenn = t.stufe === "haus" ? "" : `<span class="kenn">${t.stufe === "stadtplan" ? "Stadtplan 1935" : "nur Straße"}</span>`;
  return `<div class="treffer" data-adresse="${esc(t.adressId)}"${t.eintragId ? ` data-eintrag="${esc(t.eintragId)}"` : ""}>` +
    `<b>${esc(t.titel)}</b>${kenn}<small>${esc(t.untertitel)}</small></div>`;
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/`
Expected: alle PASS.

- [ ] **Step 5: `sidebar.js` schreiben**

```js
import { EBENEN } from "./konfig.js";
import { esc, hausHtml, trefferzeileHtml, heutigeAdresse } from "./popup.js";

const STUFEN = ["griff", "halb", "voll"];

export class Sidebar {
  constructor(el, lader, aktionen) {
    this.el = el; this.lader = lader; this.a = aktionen;
    this.inhalt = el.querySelector("#inhalt");
    this.pills = el.querySelector("#pills");
    this.vorschlaegeEl = el.querySelector("#vorschlaege");
    this.themenkopf = el.querySelector("#themenkopf");
    this.suche = el.querySelector("#suche");
    this.stadtteile = []; this.berufe = [];
    el.querySelector("#griff").addEventListener("click", () => this.naechsteStufe());
    this.inhalt.addEventListener("click", (ev) => this._klick(ev));
    this.vorschlaegeEl.addEventListener("click", (ev) => {
      const e = ev.target.closest("[data-index]");
      if (e) this.a.onVorschlag(this._vorschlagListe[+e.dataset.index]);
    });
  }

  setzeStufe(s) { this.el.dataset.stufe = s; }
  naechsteStufe() { const i = STUFEN.indexOf(this.el.dataset.stufe); this.setzeStufe(STUFEN[(i + 1) % STUFEN.length]); }
  setzeFilteroptionen(stadtteile, berufe) { this.stadtteile = stadtteile || []; this.berufe = berufe || []; }

  setzeVorschlaege(g) {
    if (!g || g.gesamt === 0) { this.vorschlaegeEl.hidden = true; this._vorschlagListe = []; return; }
    const liste = []; let html = "";
    for (const [k, titel] of [["personen", "Personen"], ["strassen", "Straßen"], ["firmen", "Firmen"], ["berufe", "Berufe"]]) {
      if (!g[k].length) continue;
      html += `<div class="gruppe">${titel}</div>`;
      for (const v of g[k]) {
        html += `<div class="eintrag" data-index="${liste.length}">${esc(v.text)}<small>${esc(v.untertitel)}</small></div>`;
        liste.push(v);
      }
    }
    this._vorschlagListe = liste; this.vorschlaegeEl.innerHTML = html; this.vorschlaegeEl.hidden = false;
  }

  _pillsHtml(z) {
    return ["I", "II", "III"].map((t) =>
      `<button class="pill ${t}" data-ebene="${t}" aria-pressed="${z.ebene.includes(t)}">${EBENEN[t]}</button>`).join("");
  }

  _filterHtml(z) {
    const st = ['<option value="">alle Stadtteile</option>', ...this.stadtteile.map((s) =>
      `<option value="${esc(s.name)}"${z.stadtteil === s.name ? " selected" : ""}>${esc(s.name)} (${s.zeilen})</option>`)].join("");
    const pr = [["haus", "hausgenau"], ["strasse", "nur Straße"], ["stadtplan", "Stadtplan 1935"]].map(([k, t]) =>
      `<label><input type="checkbox" data-praez="${k}"${z.praez.includes(k) ? " checked" : ""}> ${t}</label>`).join("");
    return `<details class="filter" ${z.stadtteil || z.beruf || z.praez.length < 3 ? "open" : ""}><summary>Filter</summary>
      <label>Stadtteil <select data-filter="stadtteil">${st}</select></label>
      <div class="praez-filter">Präzision ${pr}</div>
      <label>Beruf / Zweig <input type="text" data-filter="beruf" list="berufsliste" value="${esc(z.beruf)}" placeholder="z. B. Bergm."></label>
      <datalist id="berufsliste">${this.berufe.slice(0, 2000).map((b) => `<option value="${esc(b[1])}">${b[2]}</option>`).join("")}</datalist>
      </details>`;
  }

  zeigeSuche(z) {
    this.pills.innerHTML = this._pillsHtml(z);
    this.inhalt.innerHTML = this._filterHtml(z) +
      `<div class="hinweis">Tippe einen Namen, eine Straße, eine Firma oder einen Beruf. Die Namen H bis J fehlen in der Vorlage.</div>` +
      `<div class="themenliste" id="themenliste"></div>`;
    this._filterEreignisse(z);
  }

  // ergebnis: aus suche.treffer(); eig: Map adressId → Punkteigenschaften (soweit geladen)
  zeigeTreffer(z, ergebnis, eig, titel) {
    this.pills.innerHTML = this._pillsHtml(z);
    const n = ergebnis.personen ? ergebnis.personen.length : [...ergebnis.zaehler.values()].reduce((a, b) => a + b, 0);
    let html = this._filterHtml(z) + `<div class="kopf"><b>${n} Treffer</b> · ${ergebnis.adressIds.length} Häuser` +
      `<button class="export" data-export="1">CSV</button></div>`;
    if (ergebnis.hinweisHJ) html += `<div class="hinweis warn">Keine Treffer. Die Namen H bis J fehlen in der Vorlage (Seiten 186–258 des Teils I). Straßen und Firmen sind nicht betroffen.</div>`;
    const zeilen = ergebnis.personen
      ? ergebnis.personen.map((p) => ({ adressId: p.adressId, eintragId: p.eintragId, titel: p.text, untertitel: p.untertitel, stufe: (eig.get(p.adressId) || {}).stufe || "haus" }))
      : ergebnis.adressIds.map((id) => { const e = eig.get(id) || {}; return { adressId: id, titel: e.historisch ? heutigeAdresse(e) : id, untertitel: `${ergebnis.zaehler.get(id)} Einträge${e.historisch ? " · " + e.historisch : ""}`, stufe: e.stufe || "haus" }; });
    this._alleZeilen = zeilen; this._gezeigt = 0;
    html += `<div class="liste" id="liste"></div><button class="mehr" data-mehr="1" hidden>weitere 50</button>`;
    this.inhalt.innerHTML = html;
    this._filterEreignisse(z);
    this._mehrZeilen();
    if (ergebnis.adressIds.length >= 500) this._verteilung(ergebnis, eig);
  }

  _mehrZeilen() {
    const liste = this.inhalt.querySelector("#liste");
    const teil = this._alleZeilen.slice(this._gezeigt, this._gezeigt + 50);
    liste.insertAdjacentHTML("beforeend", teil.map(trefferzeileHtml).join(""));
    this._gezeigt += teil.length;
    this.inhalt.querySelector("[data-mehr]").hidden = this._gezeigt >= this._alleZeilen.length;
  }

  _verteilung(ergebnis, eig) {
    const je = new Map();
    for (const id of ergebnis.adressIds) { const s = (eig.get(id) || {}).stadtteil || "unbekannt"; je.set(s, (je.get(s) || 0) + ergebnis.zaehler.get(id)); }
    const top = [...je.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([s, n]) => `${esc(s)} ${n}`).join(" · ");
    this.inhalt.querySelector(".kopf").insertAdjacentHTML("afterend", `<div class="verteilung">Nach Stadtteil: ${top}</div>`);
  }

  zeigeHaus(eig, eintraege, hervorgehoben) {
    this.inhalt.innerHTML = `<button class="zurueck" data-zurueck="1">‹ zurück</button>` + hausHtml(eig, eintraege);
    if (hervorgehoben) {
      const e = this.inhalt.querySelector(`#e-${CSS.escape(hervorgehoben)}`);
      if (e) { e.classList.add("hervor"); e.scrollIntoView({ block: "center" }); }
    }
    this.setzeStufe("voll");
  }

  zeigeThema(thema) {
    if (!thema) { this.themenkopf.hidden = true; this.themenkopf.innerHTML = ""; return; }
    this.themenkopf.innerHTML = `<div class="thema"><b>${esc(thema.titel)}</b><p>${esc(thema.text)}</p><small>${esc(thema.grundlage)}</small>` +
      `<button data-thema-aus="1">Thema verlassen</button></div>`;
    this.themenkopf.hidden = false;
  }

  zeigeThemenliste(themen) {
    const el = this.inhalt.querySelector("#themenliste");
    if (!el || !themen.length) return;
    el.innerHTML = `<div class="gruppe">Themen</div>` + themen.map((t) => `<button class="themaknopf" data-thema="${esc(t.id)}">${esc(t.titel)}</button>`).join("");
  }

  _filterEreignisse(z) {
    this.pills.querySelectorAll("[data-ebene]").forEach((b) => b.addEventListener("click", () => {
      const e = b.dataset.ebene; const neu = z.ebene.includes(e) ? z.ebene.filter((x) => x !== e) : [...z.ebene, e];
      if (neu.length) this.a.onZustand({ ebene: ["I", "II", "III"].filter((x) => neu.includes(x)) });
    }));
    const sel = this.inhalt.querySelector('[data-filter="stadtteil"]');
    if (sel) sel.addEventListener("change", () => this.a.onZustand({ stadtteil: sel.value }));
    this.inhalt.querySelectorAll("[data-praez]").forEach((c) => c.addEventListener("change", () => {
      const praez = [...this.inhalt.querySelectorAll("[data-praez]:checked")].map((x) => x.dataset.praez);
      if (praez.length) this.a.onZustand({ praez });
    }));
    const beruf = this.inhalt.querySelector('[data-filter="beruf"]');
    if (beruf) beruf.addEventListener("change", () => this.a.onZustand({ beruf: beruf.value.trim() }));
  }

  _klick(ev) {
    const t = ev.target;
    if (t.closest("[data-zurueck]")) return this.a.onZurueck();
    if (t.closest("[data-mehr]")) return this._mehrZeilen();
    if (t.closest("[data-export]")) return this.a.onExport();
    const th = t.closest("[data-thema]"); if (th) return this.a.onZustand({ thema: th.dataset.thema });
    const z = t.closest(".treffer");
    if (z) return z.dataset.eintrag ? this.a.onEintragWaehlen(z.dataset.eintrag, z.dataset.adresse) : this.a.onHausWaehlen(z.dataset.adresse);
  }
}
```

Ergänzung in `stil.css`:

```css
.filter { border: 1px solid var(--rand); border-radius: 8px; padding: 6px 10px; margin-bottom: 8px; font-size: 13px; }
.filter summary { cursor: pointer; font-weight: 600; }
.filter label { display: block; margin: 6px 0; }
.filter select, .filter input[type=text] { width: 100%; padding: 6px; border: 1px solid var(--rand); border-radius: 6px; font-size: 14px; }
.praez-filter label { display: inline-block; margin-right: 8px; }
.hinweis { font-size: 13px; color: var(--grau); margin: 8px 0; }
.hinweis.warn { background: #fff7e0; border-left: 3px solid #d4a017; padding: 6px 10px; color: var(--text); }
.kopf { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--rand); }
.kopf .export { margin-left: auto; font-size: 12px; }
.verteilung { font-size: 12px; color: var(--grau); padding: 4px 0 8px; }
.treffer { padding: 8px 4px; border-bottom: 1px solid #f0f0f0; cursor: pointer; min-height: 44px; }
.treffer:hover { background: #f5f7ff; }
.treffer b { display: block; } .treffer small { color: var(--grau); }
.kenn { font-size: 10px; border: 1px dashed #777; border-radius: 3px; padding: 0 4px; margin-left: 6px; color: #555; }
.mehr, .zurueck, .themaknopf, .thema button { display: block; margin: 8px 0; padding: 8px 12px; border: 1px solid var(--rand); border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; }
.haus-kopf h2 { font-size: 17px; margin: 6px 0 2px; }
.hist { color: var(--grau); font-size: 13px; }
.praez { font-size: 12px; margin-top: 2px; } .praez-strasse, .praez-stadtplan { color: #92400e; }
.flag { font-size: 12px; color: #92400e; }
h3 { font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: var(--grau); margin: 14px 0 4px; }
.eintrag { padding: 8px 6px; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
.eintrag.hervor { background: #eef2ff; border-left: 3px solid var(--blau); }
.eintrag .k { color: var(--grau); }
.quelle { font-size: 12px; color: var(--grau); margin-top: 4px; }
.etage { font-size: 11px; background: #eee; border-radius: 3px; padding: 0 4px; }
.pname { padding: 3px 0; cursor: pointer; } .pname:hover { text-decoration: underline; }
.pmehr { color: var(--blau); cursor: pointer; padding-top: 4px; }
.thema { background: #eef2ff; border-radius: 8px; padding: 8px 12px; margin: 10px 12px 0; font-size: 13px; }
```

- [ ] **Step 6: `app.js` vollständig**

```js
import { Karte } from "./karte.js";
import { Lader } from "./daten.js";
import { Sidebar } from "./sidebar.js";
import { vorschlaege, treffer } from "./suche.js";
import { liesZustand, schreibeZustand } from "./zustand.js";
import { popupHtml } from "./popup.js";
import { FARBEN, PLAN_FREIGEGEBEN, STILE } from "./konfig.js";
import { ladeThema, themenListe } from "./themen.js";
import { csvAusTreffern, herunterladen } from "./exportcsv.js";

const lader = new Lader();
let zustand = liesZustand(location.search);
let ergebnis = null;              // aktuelle Treffermenge
let auswahl = null;               // { art, ... } der Suche
const eigCache = new Map();       // adressId → Punkteigenschaften aus Kacheln
const mobil = () => matchMedia("(max-width: 899px)").matches;

const sidebar = new Sidebar(document.getElementById("sidebar"), lader, {
  onZustand: (patch) => setzeZustand(patch, false),
  onHausWaehlen: (id) => oeffneHaus(id, null),
  onEintragWaehlen: (eid, id) => oeffneHaus(id, eid),
  onVorschlag: (v) => waehleVorschlag(v),
  onZurueck: () => history.back(),
  onExport: () => exportiere(),
});
const karte = new Karte("karte", zustand, {
  onKlick: (id, lngLat) => klickPunkt(id, lngLat),
  onBewegt: (z, c) => setzeZustand({ z, c }, false, true),
  onHover: () => {},
});

function eigVon(id) {
  if (!eigCache.has(id)) {
    const f = karte.map.querySourceFeatures("adressen", { sourceLayer: "adressen", filter: ["==", ["get", "id"], id] });
    if (f.length) eigCache.set(id, f[0].properties);
  }
  return eigCache.get(id) || null;
}

function schreibeUrl(push) {
  const q = schreibeZustand(zustand);
  const url = location.pathname + (q ? "?" + q : "");
  if (push) history.pushState(zustand, "", url); else history.replaceState(zustand, "", url);
}

async function setzeZustand(patch, push, nurKarte = false) {
  const alt = zustand;
  zustand = { ...zustand, ...patch };
  schreibeUrl(push);
  if (nurKarte) return;
  if (alt.karte !== zustand.karte) await karte.setzeStil(zustand.karte);
  if (alt.thema !== zustand.thema) await wendeThemaAn();
  karte.setzeFilter(zustand);
  karte.setzePlan(zustand.plan); karte.setzeZechen(zustand.zechen);
  if (alt.beruf !== zustand.beruf) { auswahl = zustand.beruf ? { art: "beruf", beruf: zustand.beruf } : null; await sucheAusfuehren(); }
  else zeigeInhalt();
  zeichneSteuerung(); zeichneLegende();
}

async function wendeThemaAn() {
  const t = zustand.thema ? await ladeThema(lader, zustand.thema) : null;
  sidebar.zeigeThema(t);
  karte.setzeFarbe(t ? t.farbregel : null);
  if (t && t.zusatz && t.zusatz.zechen && !zustand.zechen) zustand = { ...zustand, zechen: 1 };
  if (t && t.ebenen) zustand = { ...zustand, ebene: t.ebenen };
}

function zeigeInhalt() {
  if (ergebnis) sidebar.zeigeTreffer(zustand, ergebnis, eigMap(ergebnis.adressIds), zustand.q);
  else { sidebar.zeigeSuche(zustand); themenListe(lader).then((l) => sidebar.zeigeThemenliste(l)); }
}

function eigMap(ids) { const m = new Map(); for (const id of ids) { const e = eigVon(id); if (e) m.set(id, e); } return m; }

async function sucheAusfuehren() {
  if (!auswahl) { ergebnis = null; karte.setzeTreffer(null); zeigeInhalt(); return; }
  ergebnis = await treffer(auswahl, lader);
  karte.setzeTreffer(ergebnis.adressIds);
  if (!karte.passeEin(ergebnis.adressIds) && ergebnis.adressIds.length) {
    // Kacheln der Treffer noch nicht geladen: einmal warten und erneut versuchen
    karte.map.once("idle", () => { karte.passeEin(ergebnis.adressIds); zeigeInhalt(); });
  }
  zeigeInhalt();
  sidebar.setzeStufe("halb");
}

async function waehleVorschlag(v) {
  sidebar.setzeVorschlaege(null);
  sidebar.suche.value = v.text;
  if (v.art === "person" || v.art === "firma") { setzeZustand({ q: v.text, id: v.adressId }, true, true); return oeffneHaus(v.adressId, v.eintragId); }
  if (v.art === "beruf") return setzeZustand({ q: "", beruf: v.beruf }, true);
  auswahl = v;
  setzeZustand({ q: v.text, id: "" }, true, true);
  await sucheAusfuehren();
}

async function sucheAusText(q) {
  // Enter ohne Vorschlagsauswahl: Personensuche über den Text, Straßen über exakten Namen.
  auswahl = { art: "person", q };
  setzeZustand({ q, id: "" }, true, true);
  await sucheAusfuehren();
}

async function oeffneHaus(id, eintragId) {
  const [eig, eintraege] = [eigVon(id), await lader.scherbe(id)];
  if (!eintraege) return;
  const e = eig || { id, stufe: "haus", historisch: "", strasse_heute: "", hausnr: "", stadtteil: "", n_I: 0, n_II: 0, n_III: 0 };
  // id in der URL: Adress-ID, bei hervorgehobenem Eintrag "adressId.eintragId"
  setzeZustand({ id: eintragId ? `${id}.${eintragId}` : id }, true, true);
  karte.setzeAuswahl(id);
  const pos = karte.position(id);
  if (pos) karte.fliegeZu(pos);
  sidebar.zeigeHaus(e, eintraege, eintragId);
}

async function klickPunkt(id, lngLat) {
  const eig = eigVon(id); const eintraege = await lader.scherbe(id);
  if (!eig || !eintraege) return;
  karte.setzeAuswahl(id);
  karte.zeigePopup(lngLat, popupHtml(eig, eintraege, mobil()));
  const el = karte.popup.getElement();
  el.querySelectorAll("[data-eintrag]").forEach((n) => n.addEventListener("click", () => oeffneHaus(id, n.dataset.eintrag)));
  el.querySelectorAll("[data-mehr]").forEach((n) => n.addEventListener("click", () => oeffneHaus(id, null)));
}

function zeichneSteuerung() {
  const s = document.getElementById("steuerung");
  s.innerHTML = `<button data-karte="1">Grundkarte: ${zustand.karte === "positron" ? "dezent" : "detailliert"}</button>` +
    `<button data-zechen="1" aria-pressed="${!!zustand.zechen}">Zechen ${zustand.zechen ? "aus" : "an"}</button>` +
    (PLAN_FREIGEGEBEN ? `<label>Stadtplan 1935 <input type="range" min="0" max="1" step="0.1" value="${zustand.plan}" data-plan="1"></label>` : "") +
    (mobil() ? `<button data-legende="1">Legende</button>` : "");
  s.querySelector("[data-karte]").onclick = () => setzeZustand({ karte: zustand.karte === "positron" ? "liberty" : "positron" }, false);
  s.querySelector("[data-zechen]").onclick = () => setzeZustand({ zechen: zustand.zechen ? 0 : 1 }, false);
  const p = s.querySelector("[data-plan]"); if (p) p.oninput = () => setzeZustand({ plan: +p.value }, false);
  const l = s.querySelector("[data-legende]"); if (l) l.onclick = () => document.getElementById("legende").classList.toggle("offen");
}

function zeichneLegende() {
  const f = zustand.ebene.length === 1 ? FARBEN[zustand.ebene[0]] : FARBEN.neutral;
  document.getElementById("legende").innerHTML =
    `<div class="zeile"><span class="punkt" style="background:${f}"></span> hausgenau</div>` +
    `<div class="zeile"><span class="punkt ungenau" style="color:${f}"></span> nur straßengenau / Stadtplan 1935</div>` +
    `<div class="zeile"><span class="punkt" style="background:${FARBEN.treffer}"></span> Suchtreffer</div>` +
    `<div class="zeile">Größe = Zahl der Einträge</div>`;
}

async function exportiere() {
  if (!ergebnis) return;
  const csv = await csvAusTreffern(ergebnis, lader, eigMap(ergebnis.adressIds));
  herunterladen(csv, `essen1936-${(zustand.q || zustand.beruf || "treffer").replace(/[^\w]+/g, "_")}.csv`);
}

// Suchfeld
let timer = null;
sidebar.suche.value = zustand.q;
sidebar.suche.addEventListener("input", () => {
  clearTimeout(timer);
  document.getElementById("suche-leeren").hidden = !sidebar.suche.value;
  timer = setTimeout(async () => sidebar.setzeVorschlaege(await vorschlaege(sidebar.suche.value, lader)), 120);
});
sidebar.suche.addEventListener("keydown", (ev) => { if (ev.key === "Enter") { sidebar.setzeVorschlaege(null); sucheAusText(sidebar.suche.value.trim()); } });
document.getElementById("suche-leeren").addEventListener("click", () => { sidebar.suche.value = ""; auswahl = null; setzeZustand({ q: "", id: "" }, true, true); sucheAusfuehren(); });
document.addEventListener("click", (ev) => { if (!ev.target.closest(".suchfeld")) sidebar.setzeVorschlaege(null); });
window.addEventListener("popstate", async () => { zustand = liesZustand(location.search); sidebar.suche.value = zustand.q; await start(); });

async function start() {
  await karte.bereit();
  const [st, be, kz] = await Promise.all([lader.stadtteile(), lader.berufe(), lader.kennzahlen()]);
  sidebar.setzeFilteroptionen(st, be);
  if (kz) document.getElementById("vermerk").textContent = `Work in progress · Datenstand ${kz.stand} · ${kz.stufen.haus} % hausgenau`;
  await wendeThemaAn();
  karte.setzeFilter(zustand); karte.setzePlan(zustand.plan); karte.setzeZechen(zustand.zechen);
  zeichneSteuerung(); zeichneLegende();
  if (zustand.beruf) auswahl = { art: "beruf", beruf: zustand.beruf };
  else if (zustand.q) auswahl = { art: "person", q: zustand.q };
  else auswahl = null;
  await sucheAusfuehren();
  if (zustand.id) {
    const [aid, eid] = zustand.id.split(".");   // "adressId" oder "adressId.eintragId"
    oeffneHaus(aid, eid || null);
  }
  sidebar.setzeStufe(mobil() ? (zustand.q ? "halb" : "griff") : "halb");
}
karte.map.on("sourcedata", (e) => { if (e.sourceId === "adressen" && e.isSourceLoaded) eigCache.clear(); });
await start();
window.karte = karte;
```

`app.js` importiert `themen.js` und `exportcsv.js`, die erst in Task 12 und 13 entstehen. Damit die Sichtprüfung hier schon läuft, beide zunächst als Stummel anlegen (werden dort ersetzt):

```js
// site/js/themen.js (Stummel, Task 12 ersetzt ihn)
export async function ladeThema() { return null; }
export async function themenListe() { return []; }
```

```js
// site/js/exportcsv.js (Stummel, Task 13 ersetzt ihn)
export async function csvAusTreffern() { return ""; }
export function herunterladen() {}
```

- [ ] **Step 7: Sichtprüfung**

`http://localhost:8765/site/karte.html` öffnen und prüfen: Suche „Sep“ zeigt Vorschläge; Auswahl „Sepeur, Wilh.“ fliegt zum Haus und öffnet die Hausansicht mit hervorgehobenem Eintrag; „Grenzstr.“ als Straße zeigt Trefferliste und rote Punkte; Beruf „Bergm.“ hebt tausende Punkte hervor, Liste zeigt 50 mit „weitere 50“; Ebenen-Pill „Eigentümer“ allein färbt gold; Zurück-Taste des Browsers führt zur vorigen Ansicht; Handy-Viewport (390 px) zeigt das Sheet, Griff wechselt die Stufen. `node --test site/tests/` bleibt grün.

- [ ] **Step 8: Commit**

```bash
git add site/js/popup.js site/js/sidebar.js site/js/app.js site/js/themen.js site/js/exportcsv.js site/css/stil.css site/tests/popup.test.js
git commit -m "feat: Sidebar und Popup — Suche, Trefferliste, Hausansicht, Filter, URL-Verlauf

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 12: Themen (`themen.js`, erstes Thema „Akademiker“)

**Files:**
- Create: `site/js/themen.js`, `site/daten/themen/index.json`, `site/daten/themen/akademiker.json`
- Test: `site/tests/themen.test.js`

**Interfaces:**
- Consumes: `Lader.thema(id)`, `Lader.json("themen/index.json")`, `FARBEN`.
- Produces: `farbregel(thema) -> {merkmal, ausdruck}|null` (MapLibre-Farbausdruck; `farbe.art ∈ {"einfach","skala"}`), `async ladeThema(lader, id) -> Thema|null` (mit `farbregel` und `ebenen` angehängt), `async themenListe(lader) -> [{id, titel}]` (nur `freigegeben: true`).
- Themenformat (`themen/<id>.json`): `{ "id", "titel", "text", "grundlage", "freigegeben": bool, "filter": {"merkmal": "akademiker", "ebenen": ["I"]}, "farbe": {"art": "einfach", "wert": "#7c3aed"} | {"art": "skala", "merkmal": "schicht", "stufen": [[0,"#..."],[1,"#..."]]}, "zusatz": {"zechen": false}, "legende": "Text", "darstellung": "punkte" }`.

- [ ] **Step 1: Failing tests**

`site/tests/themen.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { farbregel, ladeThema, themenListe } from "../js/themen.js";
import { Lader } from "../js/daten.js";

const AK = { id: "akademiker", titel: "Akademiker", text: "…", grundlage: "Titelliste", freigegeben: true,
  filter: { merkmal: "akademiker", ebenen: ["I"] }, farbe: { art: "einfach", wert: "#7c3aed" }, zusatz: { zechen: false }, legende: "lila = Akademiker", darstellung: "punkte" };
const DATEIEN = { "daten/themen/akademiker.json": AK, "daten/themen/index.json": [{ id: "akademiker", titel: "Akademiker", freigegeben: true }, { id: "bergbau", titel: "Bergbau", freigegeben: false }] };
const fetchFake = async (u) => ({ ok: u in DATEIEN, status: u in DATEIEN ? 200 : 404, json: async () => DATEIEN[u] });

test("farbregel einfach und skala", () => {
  assert.deepEqual(farbregel(AK), { merkmal: "akademiker", ausdruck: "#7c3aed" });
  const s = farbregel({ filter: {}, farbe: { art: "skala", merkmal: "schicht", stufen: [[0, "#000"], [2, "#fff"]] } });
  assert.equal(s.merkmal, "schicht");
  assert.equal(s.ausdruck[0], "interpolate");
  assert.equal(farbregel({ filter: {} }), null);
});

test("ladeThema hängt farbregel und ebenen an, unbekannt → null", async () => {
  const l = new Lader("daten/", fetchFake);
  const t = await ladeThema(l, "akademiker");
  assert.equal(t.farbregel.merkmal, "akademiker");
  assert.deepEqual(t.ebenen, ["I"]);
  assert.equal(await ladeThema(l, "gibtsnicht"), null);
});

test("themenListe nur freigegebene", async () => {
  assert.deepEqual(await themenListe(new Lader("daten/", fetchFake)), [{ id: "akademiker", titel: "Akademiker" }]);
});
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `node --test site/tests/themen.test.js`
Expected: „Cannot find module“.

- [ ] **Step 3: Modul und Themendateien**

`site/js/themen.js`:

```js
// Ein Thema ist eine Voreinstellung: Merkmalsfilter, Farbregel, Zusatzebenen, Text (Spec §8).
export function farbregel(thema) {
  const f = thema.farbe;
  if (!f) return null;
  if (f.art === "einfach") return { merkmal: thema.filter?.merkmal || null, ausdruck: f.wert };
  if (f.art === "skala") {
    const stufen = f.stufen.flatMap(([w, farbe]) => [w, farbe]);
    return { merkmal: f.merkmal, ausdruck: ["interpolate", ["linear"], ["coalesce", ["get", `m_${f.merkmal}`], 0], ...stufen] };
  }
  return null;
}

export async function ladeThema(lader, id) {
  const t = await lader.thema(id);
  if (!t) return null;
  return { ...t, farbregel: farbregel(t), ebenen: t.filter?.ebenen || null };
}

export async function themenListe(lader) {
  const l = (await lader.json("themen/index.json")) || [];
  return l.filter((t) => t.freigegeben).map((t) => ({ id: t.id, titel: t.titel }));
}
```

`site/daten/themen/index.json`:

```json
[{"id": "akademiker", "titel": "Akademiker", "freigegeben": false}]
```

`site/daten/themen/akademiker.json`:

```json
{
  "id": "akademiker",
  "titel": "Akademiker",
  "text": "Einträge mit akademischem Titel (Dr., Prof., Dipl.-Ing.) oder akademischem Beruf laut Buchschreibung.",
  "grundlage": "Titelliste kuratierung/merkmale/akademiker.csv, geprüft am: noch offen",
  "freigegeben": false,
  "filter": {"merkmal": "akademiker", "ebenen": ["I"]},
  "farbe": {"art": "einfach", "wert": "#7c3aed"},
  "zusatz": {"zechen": false},
  "legende": "lila = Eintrag mit akademischem Titel",
  "darstellung": "punkte"
}
```

`freigegeben` bleibt `false`, bis der Projektleiter die Titelliste abgenommen hat; dann `true` in beiden Dateien und das Prüfdatum in `grundlage` eintragen. Auch nicht freigegebene Themen lassen sich über `?thema=akademiker` ansehen (zur Prüfung), sie erscheinen nur nicht in Liste und Startseite.

- [ ] **Step 4: Tests und Sichtprüfung**

Run: `node --test site/tests/`
Expected: alle PASS. Danach `http://localhost:8765/site/karte.html?thema=akademiker` öffnen: lila Punkte nur dort, wo `m_akademiker > 0`; Themenkopf mit „Thema verlassen“ (Klick entfernt `thema=` aus der URL; in `app.js` den Knopf verdrahten: `this.themenkopf.querySelector("[data-thema-aus]")` → `onZustand({thema: ""})`; das gehört in `Sidebar.zeigeThema`, dort ergänzen:

```js
    this.themenkopf.querySelector("[data-thema-aus]").addEventListener("click", () => this.a.onZustand({ thema: "" }));
```

- [ ] **Step 5: Commit**

```bash
git add site/js/themen.js site/js/sidebar.js site/daten/themen site/tests/themen.test.js
git commit -m "feat: Themen-Mechanik mit erstem Thema Akademiker (nicht freigegeben)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 13: CSV-Export (`exportcsv.js`)

**Files:**
- Create: `site/js/exportcsv.js`
- Test: `site/tests/exportcsv.test.js`

**Interfaces:**
- Consumes: `ergebnis` aus `treffer()`, `Lader.scherbe`, `eig`-Map.
- Produces: `csvZeile(felder) -> string` (RFC-4180-Quoting), `async csvAusTreffern(ergebnis, lader, eig, maxEintraege = 5000) -> string` (mit BOM; bis `maxEintraege` Einträge vollständig, sonst Adressebene), `herunterladen(text, dateiname)` (Blob-Download, nur im Browser).

- [ ] **Step 1: Failing tests**

`site/tests/exportcsv.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { csvZeile, csvAusTreffern } from "../js/exportcsv.js";
import { Lader } from "../js/daten.js";

const DATEIEN = { "daten/haus/a1.json": { a1: [
  { id: "1", teil: "I", seite: "I-551", name: "Sepeur", vorname: "Wilh.", beruf: "Bergm.", etage: "", stand: "", flags: [], merkmale: [] },
  { id: "2", teil: "II", seite: "II-1", name: "Zeche \"Z\"", vorname: "", beruf: "", etage: "", stand: "", flags: ["nummer_unsicher"], merkmale: [] } ] } };
const l = new Lader("daten/", async (u) => ({ ok: u in DATEIEN, status: u in DATEIEN ? 200 : 404, json: async () => DATEIEN[u] }));
const EIG = new Map([["a1", { id: "a1", stufe: "haus", strasse_heute: "Lattenkamp", hausnr: "25", stadtteil: "Katernberg", historisch: "Grenzstr. 25, Katernberg" }]]);

test("csvZeile quotet Komma, Anführungszeichen und Zeilenumbruch", () => {
  assert.equal(csvZeile(["a", "b,c", 'd"e', "f\ng"]), 'a,"b,c","d""e","f\ng"');
});

test("vollständiger Export bis zur Grenze", async () => {
  const csv = await csvAusTreffern({ adressIds: ["a1"], zaehler: new Map([["a1", 2]]), personen: null }, l, EIG);
  const zeilen = csv.split("\r\n");
  assert.ok(zeilen[0].startsWith("﻿"));
  assert.equal(zeilen[0].replace("﻿", ""), "eintrag_id,teil,seite,name,vorname,beruf,etage,stand,adresse_heute,adresse_1936,stadtteil,praezision,flags,adress_id");
  assert.equal(zeilen[1], "1,I,I-551,Sepeur,Wilh.,Bergm.,,,\"Lattenkamp 25, Katernberg\",\"Grenzstr. 25, Katernberg\",Katernberg,haus,,a1");
  assert.match(zeilen[2], /"Zeche ""Z"""/);
});

test("über der Grenze nur Adressebene", async () => {
  const csv = await csvAusTreffern({ adressIds: ["a1"], zaehler: new Map([["a1", 2]]), personen: null }, l, EIG, 1);
  assert.equal(csv.split("\r\n")[0].replace("﻿", ""), "adress_id,adresse_heute,adresse_1936,stadtteil,praezision,eintraege");
  assert.equal(csv.split("\r\n")[1], "a1,\"Lattenkamp 25, Katernberg\",\"Grenzstr. 25, Katernberg\",Katernberg,haus,2");
});
```

- [ ] **Step 2: Test laufen lassen, muss fehlschlagen**

Run: `node --test site/tests/exportcsv.test.js`

- [ ] **Step 3: Modul schreiben**

```js
import { heutigeAdresse } from "./popup.js";

export function csvZeile(felder) {
  return felder.map((f) => { const s = String(f ?? ""); return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; }).join(",");
}

const KOPF_E = ["eintrag_id", "teil", "seite", "name", "vorname", "beruf", "etage", "stand", "adresse_heute", "adresse_1936", "stadtteil", "praezision", "flags", "adress_id"];
const KOPF_A = ["adress_id", "adresse_heute", "adresse_1936", "stadtteil", "praezision", "eintraege"];

export async function csvAusTreffern(ergebnis, lader, eig, maxEintraege = 5000) {
  const gesamt = [...ergebnis.zaehler.values()].reduce((a, b) => a + b, 0);
  const zeilen = [];
  const adr = (id) => { const e = eig.get(id) || {}; return [e.historisch ? heutigeAdresse(e) : "", e.historisch || "", e.stadtteil || "", e.stufe || ""]; };
  if (gesamt <= maxEintraege) {
    zeilen.push(csvZeile(KOPF_E));
    const nurIds = ergebnis.personen ? new Set(ergebnis.personen.map((p) => p.eintragId)) : null;
    for (const id of ergebnis.adressIds) {
      const eintraege = (await lader.scherbe(id)) || [];
      for (const e of eintraege) {
        if (nurIds && !nurIds.has(e.id)) continue;
        zeilen.push(csvZeile([e.id, e.teil, e.seite, e.name, e.vorname, e.beruf, e.etage, e.stand, ...adr(id), (e.flags || []).join(";"), id]));
      }
    }
  } else {
    zeilen.push(csvZeile(KOPF_A));
    for (const id of ergebnis.adressIds) zeilen.push(csvZeile([id, ...adr(id), ergebnis.zaehler.get(id)]));
  }
  return "﻿" + zeilen.join("\r\n") + "\r\n";
}

export function herunterladen(text, dateiname) {
  const blob = new Blob([text], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = dateiname; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/`
Expected: alle PASS. Sichtprüfung: Suche „Grenzstr.“, Knopf „CSV“ lädt eine Datei, die sich in LibreOffice mit Umlauten öffnet.

- [ ] **Step 5: Commit**

```bash
git add site/js/exportcsv.js site/tests/exportcsv.test.js
git commit -m "feat: CSV-Export der Treffer (vollständig bis 5.000, sonst Adressebene)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 14: Startseite (`index.html`, `start.js`)

**Files:**
- Create: `site/index.html`, `site/js/start.js`, `site/bilder/banner-1935.jpg`
- Modify: `site/css/stil.css`

**Interfaces:**
- Consumes: `Lader`, `vorschlaege`, `themenListe`, `hinweisHJ`.
- Produces: Startseite mit Suchleiste (Vorschläge wie auf der Kartenseite), Zahlenzeile aus `kennzahlen.json`, Kacheln, Hinweiszeile H–J; Auswahl navigiert zu `karte.html?…` mit denselben Parametern wie `waehleVorschlag` in `app.js`.

- [ ] **Step 1: Banner erzeugen**

Ausschnitt des Stadtplans 1935 vom ArcGIS-Dienst als Platzhalter, bis das Digitalisat des Projektleiters vorliegt (Rechte: nur intern verwenden, vor Veröffentlichung ersetzen oder freigeben lassen):

```bash
curl -sS -o site/bilder/banner-1935.jpg "https://geo.essen.de/arcgis/rest/services/historischerverein/Stadtplan_1935/MapServer/export?bbox=778000,6705500,784000,6707500&bboxSR=3857&imageSR=3857&size=1800,600&format=jpg&f=image"
python3 -c "from PIL import Image; im=Image.open('site/bilder/banner-1935.jpg'); print(im.size)" 2>/dev/null || file site/bilder/banner-1935.jpg
```

Expected: JPEG 1800×600 mit Innenstadt (Kettwiger Straße, Hauptbahnhof). Ist die Datei leer oder ein Fehlerbild, `bbox` nach Osten oder Westen verschieben (Schritt 1000 m).

- [ ] **Step 2: `index.html`**

```html
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Essen 1936 – Das Adressbuch auf der Karte</title>
<meta name="description" content="Das Essener Adressbuch von 1936 auf der Karte: Einwohner, Hauseigentümer und Gewerbe suchen und verorten.">
<link rel="stylesheet" href="css/stil.css">
</head>
<body class="startseite">
<header class="banner" style="background-image:url('bilder/banner-1935.jpg')">
  <div class="banner-text"><h1>Essen 1936</h1><p>Das Adressbuch auf der Karte</p></div>
</header>
<main>
  <div class="suchkasten">
    <div class="suchfeld">
      <input id="suche" type="search" placeholder="Name, Straße, Firma, Beruf …" autocomplete="off" aria-label="Suche" autofocus>
      <div id="vorschlaege" class="vorschlaege" hidden></div>
    </div>
    <p class="hinweis" id="hinweis-hj" hidden>Die Namen H bis J fehlen in der Vorlage (Seiten 186–258). Straßen und Firmen sind nicht betroffen.</p>
  </div>
  <div class="zahlen" id="zahlen"></div>
  <nav class="kacheln" id="kacheln">
    <a class="kachel" href="karte.html"><b>Karte öffnen</b><small>alle Ebenen, ohne Suche</small></a>
    <a class="kachel" href="karte.html#stadtteil" id="kachel-stadtteil"><b>Stadtteil wählen</b><small>Katernberg, Steele, Werden …</small></a>
    <a class="kachel" href="karte.html?zechen=1&z=11"><b>Zechen und Krupp</b><small>Werke 1936 und ihr Umfeld</small></a>
    <a class="kachel kachel-thema" id="kachel-thema" hidden><b></b><small></small></a>
  </nav>
  <p class="luecke">Die Namen H bis J fehlen in der Vorlage. Wer dort sucht, findet nichts, nicht weil es nichts gab. <a href="ueber.html#luecken">Mehr dazu</a></p>
</main>
<footer><a href="ueber.html">Über das Projekt</a> · Quelle: Adreßbuch Essen 1936 (Scherl), Erfassung Verein für Computergenealogie · <a href="impressum.html">Impressum</a></footer>
<script type="module" src="js/start.js"></script>
</body>
</html>
```

- [ ] **Step 3: `start.js`**

```js
import { Lader } from "./daten.js";
import { vorschlaege, hinweisHJ } from "./suche.js";
import { themenListe } from "./themen.js";
import { esc } from "./popup.js";
import { schreibeZustand, STANDARD } from "./zustand.js";

const lader = new Lader();
const suche = document.getElementById("suche");
const box = document.getElementById("vorschlaege");
let liste = [];

function zielUrl(v) {
  let z;
  if (v.art === "person" || v.art === "firma") z = { ...STANDARD, q: v.text, id: v.adressId + (v.eintragId ? "." + v.eintragId : "") };
  else if (v.art === "beruf") z = { ...STANDARD, beruf: v.beruf };
  else z = { ...STANDARD, q: v.text };
  return "karte.html?" + schreibeZustand(z);
}

function zeige(g) {
  liste = [];
  if (!g || g.gesamt === 0) { box.hidden = true; return; }
  let html = "";
  for (const [k, titel] of [["personen", "Personen"], ["strassen", "Straßen"], ["firmen", "Firmen"], ["berufe", "Berufe"]]) {
    if (!g[k].length) continue;
    html += `<div class="gruppe">${titel}</div>`;
    for (const v of g[k]) { html += `<a class="eintrag" href="${zielUrl(v)}">${esc(v.text)}<small>${esc(v.untertitel)}</small></a>`; liste.push(v); }
  }
  box.innerHTML = html; box.hidden = false;
}

let timer = null;
suche.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const g = await vorschlaege(suche.value, lader);
    zeige(g);
    document.getElementById("hinweis-hj").hidden = !(g.personen.length === 0 && hinweisHJ(suche.value) && suche.value.length >= 2);
  }, 120);
});
suche.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && suche.value.trim()) location.href = "karte.html?" + schreibeZustand({ ...STANDARD, q: suche.value.trim() });
});
document.addEventListener("click", (ev) => { if (!ev.target.closest(".suchfeld")) box.hidden = true; });

const kz = await lader.kennzahlen();
if (kz) {
  const t = kz.eintraege_je_teil;
  const verortet = (kz.stufen.haus + kz.stufen.strasse + kz.stufen.stadtplan).toFixed(0);
  document.getElementById("zahlen").innerHTML = [[t.I, "Einwohner"], [t.II, "Häuser"], [t.III, "Firmen"], [verortet + " %", "verortet"]]
    .map(([n, l]) => `<div><b>${typeof n === "number" ? n.toLocaleString("de-DE") : n}</b><small>${l}</small></div>`).join("");
}
const st = await lader.stadtteile();
if (st) {
  const k = document.getElementById("kachel-stadtteil");
  k.href = "#"; k.addEventListener("click", (ev) => {
    ev.preventDefault();
    k.outerHTML = `<div class="kachel"><b>Stadtteil</b><select id="st-wahl"><option value="">wählen …</option>${st.map((s) => `<option value="${esc(s.name)}">${esc(s.name)} (${s.zeilen})</option>`).join("")}</select></div>`;
    document.getElementById("st-wahl").addEventListener("change", (e) => { if (e.target.value) location.href = "karte.html?" + schreibeZustand({ ...STANDARD, stadtteil: e.target.value, z: 14, c: [st.find((s) => s.name === e.target.value).lon, st.find((s) => s.name === e.target.value).lat] }); });
  });
}
const themen = await themenListe(lader);
if (themen.length) {
  const k = document.getElementById("kachel-thema");
  k.href = "karte.html?thema=" + encodeURIComponent(themen[0].id);
  k.querySelector("b").textContent = themen[0].titel; k.querySelector("small").textContent = "Thema";
  k.hidden = false;
}
```

- [ ] **Step 4: CSS für die Startseite**

An `stil.css` anhängen:

```css
.startseite main { max-width: 760px; margin: 0 auto; padding: 0 16px 24px; }
.banner { height: 240px; background-size: cover; background-position: center; position: relative; }
.banner-text { position: absolute; left: 0; right: 0; bottom: 0; padding: 16px; background: linear-gradient(transparent, rgba(250,248,243,.95)); }
.banner-text h1 { margin: 0; font-size: 34px; } .banner-text p { margin: 0; color: #444; }
.suchkasten { margin-top: -22px; background: #fff; border-radius: 12px; box-shadow: 0 3px 14px rgba(0,0,0,.18); padding: 8px 8px 4px; position: relative; z-index: 2; }
.suchkasten .suchfeld { padding: 4px; }
.suchkasten .vorschlaege .eintrag { display: block; text-decoration: none; color: var(--text); }
.zahlen { display: flex; gap: 20px; justify-content: center; margin: 22px 0 14px; flex-wrap: wrap; }
.zahlen div { text-align: center; } .zahlen b { font-size: 22px; display: block; } .zahlen small { color: var(--grau); }
.kacheln { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.kachel { display: block; background: #fff; border: 1px solid var(--rand); border-radius: 10px; padding: 12px 14px; text-decoration: none; color: var(--text); min-height: 64px; }
.kachel b { display: block; } .kachel small { color: var(--grau); }
.kachel select { width: 100%; margin-top: 4px; font-size: 14px; }
.luecke { background: #fff7e0; border-left: 3px solid #d4a017; padding: 8px 12px; font-size: 14px; margin-top: 18px; }
footer { text-align: center; font-size: 12px; color: var(--grau); padding: 16px; }
@media (max-width: 520px) { .kacheln { grid-template-columns: 1fr; } .banner { height: 160px; } .banner-text h1 { font-size: 26px; } }
```

- [ ] **Step 5: Sichtprüfung**

`http://localhost:8765/site/index.html`: Banner, Suche mit Vorschlägen (Vorschläge sind Links auf `karte.html?…`), Zahlenzeile mit Tausenderpunkten, vier Kacheln (die vierte bleibt verborgen, solange kein Thema freigegeben ist), Hinweis H–J bei „Hoff“. Handy-Viewport 390 px: eine Spalte, kein horizontales Scrollen. `node --test site/tests/` grün.

- [ ] **Step 6: Commit**

```bash
git add site/index.html site/js/start.js site/css/stil.css site/bilder/banner-1935.jpg
git commit -m "feat: Startseite mit Suchleiste, Kennzahlen und Einstiegskacheln

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 15: Über-Seite, Impressum, Playwright-Rauchtests, Doku

**Files:**
- Create: `site/ueber.html`, `site/impressum.html`, `tests/e2e/test_site.py`, `tests/e2e/__init__.py`
- Modify: `README.md`, `docs/sichtung.md` (Verweis auf Range), `pyproject.toml` (optional-dependency `e2e = ["playwright"]`)
- Create: `.github/workflows/pages.yml`

**Interfaces:**
- Rauchtests starten `werkzeuge/serve.py` auf einem freien Port in einem Subprozess und laufen mit `python3 -m pytest tests/e2e -q -m e2e`; ohne `-m e2e` werden sie übersprungen (Marker in `pyproject.toml` registrieren).

- [ ] **Step 1: `ueber.html` und `impressum.html`**

`site/ueber.html` (Kennzahlen werden von `js/ueber.js` eingesetzt; Text steht statisch):

```html
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Über das Projekt – Essen 1936</title><link rel="stylesheet" href="css/stil.css"></head>
<body class="textseite">
<main>
<p><a href="index.html">‹ Startseite</a></p>
<h1>Über das Projekt</h1>
<p>Diese Karte zeigt das <em>Adreßbuch der Stadt Essen 1936</em> (Verlag Scherl) auf der heutigen Stadtkarte. Grundlage ist die Erfassung des Vereins für Computergenealogie (DES-Projekt <a href="https://des.genealogy.net/essen1936/" rel="noopener">essen1936</a>). Die Karte ist <strong>work in progress</strong>; Stand und Kennzahlen unten.</p>
<h2 id="quelle">Quelle und Teile</h2>
<p>Teil I Einwohner, Teil II Häuser und Eigentümer, Teil III Gewerbe. Behörden (IV) und Innungen (W) sind nicht kartiert.</p>
<div class="zahlen" id="zahlen"></div>
<h2 id="luecken">Lücken</h2>
<p>In Teil I fehlen die Seiten 186–258, also alle Nachnamen mit <strong>H, I und J</strong> (geschätzt 23.000 Personen). Sie sind in der Vorlage nicht erfasst; ein Nachtrag ist beim Verein für Computergenealogie angefragt. Straßen, Häuser und Firmen mit diesen Anfangsbuchstaben sind vollständig.</p>
<h2 id="praezision">Präzision der Verortung</h2>
<p>Jede Adresse trägt eine Stufe: <b>hausgenau</b> (heutige Hausnummer gefunden), <b>nur straßengenau</b> (Straße bekannt, Nummer nicht auffindbar; der Punkt liegt an der Straße, nicht am Haus, gestrichelt dargestellt) oder <b>Stadtplan 1935</b> (Straße verschwunden, Punkt von Hand am Stadtplan von 1935 gesetzt). Straßen wurden über den Datensatz <a href="https://doi.org/10.5281/zenodo.22757900" rel="noopener">Essener Straßennamen (Dickhoff 2015)</a> und den Stadtplan 1935 der Stadt Essen aufgelöst. Umbenannte und neu gezählte Straßen sind gekennzeichnet; wo die Hausnummer nicht belastbar ist, steht das im Eintrag. Regel: lieber „nicht verortet“ als falsch.</p>
<h2 id="methode">Methode und Code</h2>
<p>Pipeline und Kuratierungstabellen liegen offen im Repository <a href="https://github.com/rodouc6/essener-adressbuch-1936" rel="noopener">essener-adressbuch-1936</a>; die Entscheidungen zur Straßenauflösung sind dort dokumentiert.</p>
</main>
<footer><a href="index.html">Startseite</a> · <a href="karte.html">Karte</a> · <a href="impressum.html">Impressum</a></footer>
<script type="module">
import { Lader } from "./js/daten.js";
const kz = await new Lader().kennzahlen();
if (kz) document.getElementById("zahlen").innerHTML = [[kz.eintraege_je_teil.I, "Einwohner"], [kz.eintraege_je_teil.II, "Häuser"], [kz.eintraege_je_teil.III, "Firmen"],
  [kz.stufen.haus + " %", "hausgenau"], [kz.stufen.strasse + " %", "straßengenau"], [kz.stufen.stadtplan + " %", "Stadtplan 1935"], [kz.stufen.offen + " %", "nicht verortet"], [kz.stand, "Datenstand"]]
  .map(([n, l]) => `<div><b>${typeof n === "number" ? n.toLocaleString("de-DE") : n}</b><small>${l}</small></div>`).join("");
</script>
</body>
</html>
```

`site/impressum.html` nach dem Muster von `~/Projekte/wuppertal-kartenprojekt-zwangsarbeit-unternehmen/impressum.html` (Angaben des Projektleiters übernehmen, Absätze: Verantwortlich, Kartendaten OpenStreetMap/OpenFreeMap, Stadtplan 1935 Stadt Essen, Quelle CompGen, Datenschutz: keine Cookies, keine Analytik, beim Laden der Grundkarte wird die IP an OpenFreeMap übertragen). CSS-Ergänzung:

```css
.textseite main { max-width: 720px; margin: 0 auto; padding: 16px; line-height: 1.5; }
.textseite h1 { font-size: 28px; } .textseite h2 { font-size: 18px; margin-top: 24px; }
```

- [ ] **Step 2: Playwright-Rauchtests (failing, bis die Seiten stehen)**

`tests/e2e/test_site.py`:

```python
"""Rauchtests der Seite: python3 -m pytest tests/e2e -q -m e2e (braucht playwright + chromium und site/daten)."""
import pathlib, socket, subprocess, sys, time

import pytest

pytestmark = pytest.mark.e2e
W = pathlib.Path(__file__).resolve().parents[2]


def _freier_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


@pytest.fixture(scope="module")
def basis():
    if not (W / "site" / "daten" / "adressen.pmtiles").exists():
        pytest.skip("site/daten fehlt (Stufe 06 nicht gelaufen)")
    port = _freier_port()
    p = subprocess.Popen([sys.executable, str(W / "werkzeuge" / "serve.py"), str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    yield f"http://127.0.0.1:{port}/site/"
    p.terminate()


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _seite(browser, breite=1200):
    s = browser.new_page(viewport={"width": breite, "height": 800})
    s.fehler = []
    s.on("pageerror", lambda e: s.fehler.append(str(e)))
    return s


def test_startseite_sucht_und_verlinkt(basis, browser):
    s = _seite(browser)
    s.goto(basis + "index.html")
    s.fill("#suche", "Sep")
    s.wait_for_selector("#vorschlaege .eintrag", timeout=5000)
    assert "Personen" in s.inner_text("#vorschlaege")
    assert s.get_attribute("#vorschlaege .eintrag", "href").startswith("karte.html?")
    assert s.fehler == []


def test_kartenseite_zeigt_punkte_und_hausansicht(basis, browser):
    s = _seite(browser)
    s.goto(basis + "karte.html?z=15&c=7.045,51.486")
    s.wait_for_function("window.karte && karte.map.loaded()", timeout=15000)
    s.wait_for_timeout(1500)
    n = s.evaluate("karte.map.queryRenderedFeatures({layers:['adressen-haus','adressen-ungenau']}).length")
    assert n > 20
    s.fill("#suche", "Sepeur")
    s.wait_for_selector("#vorschlaege .eintrag", timeout=5000)
    s.click("#vorschlaege .eintrag")
    s.wait_for_selector(".haus-kopf", timeout=8000)
    assert "historische Adresse" in s.inner_text("#inhalt")
    assert "Faksimile" in s.inner_text("#inhalt")
    assert "id=" in s.url
    assert s.fehler == []


def test_urlzustand_und_stilwechsel(basis, browser):
    s = _seite(browser)
    s.goto(basis + "karte.html?ebene=II&karte=liberty&z=14&c=7.01,51.45")
    s.wait_for_function("window.karte && karte.map.loaded()", timeout=15000)
    assert s.get_attribute(".pill.II", "aria-pressed") == "true"
    assert s.get_attribute(".pill.I", "aria-pressed") == "false"
    s.click("#steuerung [data-karte]")
    s.wait_for_timeout(2500)
    assert "karte=liberty" not in s.url
    assert s.evaluate("!!karte.map.getLayer('adressen-haus')")
    assert s.fehler == []


def test_mobil_sheet(basis, browser):
    s = _seite(browser, breite=390)
    s.goto(basis + "karte.html")
    s.wait_for_function("window.karte && karte.map.loaded()", timeout=15000)
    assert s.get_attribute("#sidebar", "data-stufe") == "griff"
    s.click("#griff")
    assert s.get_attribute("#sidebar", "data-stufe") == "halb"
    assert s.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert s.fehler == []
```

`pyproject.toml` ergänzen:

```toml
[project.optional-dependencies]
test = ["pytest>=8"]
e2e = ["playwright>=1.45"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
markers = ["e2e: Rauchtests im Browser (Server + Playwright)"]
addopts = "-m 'not e2e'"
```

- [ ] **Step 3: Rauchtests laufen lassen**

Run: `python3 -m pytest tests/e2e -q -m e2e`
Expected: 4 PASS. Bei Fehlern die Meldung lesen (Konsolenfehler stehen in `s.fehler`), beheben, erneut laufen lassen. Danach `python3 -m pytest -q` (ohne e2e) und `node --test site/tests/` grün.

- [ ] **Step 4: GitHub Pages**

`.github/workflows/pages.yml`:

```yaml
name: Pages
on:
  push:
    branches: [main]
    paths: ["site/**"]
  workflow_dispatch:
permissions: { contents: read, pages: write, id-token: write }
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: { name: github-pages, url: "${{ steps.deployment.outputs.page_url }}" }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/upload-pages-artifact@v3
        with: { path: site }
      - id: deployment
        uses: actions/deploy-pages@v4
```

Solange das Repo privat ist, läuft Pages nur mit GitHub Pro; der Workflow bleibt bis zur Veröffentlichung inaktiv (Repo-Einstellung Pages → Source „GitHub Actions“ erst dann setzen). Lokal bleibt `serve.py` der Weg.

- [ ] **Step 5: README und Doku**

In `README.md` einen Abschnitt „Karte (Teilprojekt 2)“ ergänzen: Aufruf `python3 pipeline/06_karte_export.py`, lokale Ansicht `python3 werkzeuge/serve.py 8765` → `http://localhost:8765/site/`, Tests (`node --test site/tests/`, `pytest -m e2e`), Struktur von `site/daten/`, URL-Parameter (Tabelle aus Spec §4), Themenformat (Spec §8), Hinweis `PLAN_FREIGEGEBEN`. Vokabular-Tabelle um `stadtplan` als Präzisionsstufe der Karte ergänzen (Pipeline-Stufe bleibt `strasse` mit herkunft `stadtplan_1935`).

- [ ] **Step 6: Commit**

```bash
git add site/ueber.html site/impressum.html site/css/stil.css tests/e2e pyproject.toml .github/workflows/pages.yml README.md
git commit -m "feat: Über-Seite, Impressum, Playwright-Rauchtests, Pages-Workflow, Doku

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Reihenfolge und Abnahmen

1. Tasks 1–7 (Pipeline) sind unabhängig vom Frontend und liefern `site/daten/`; Task 7 braucht Netz und eine Sichtprüfung der Zechen.
2. Tasks 8–13 bauen das Frontend; Task 11 importiert `themen.js` und `exportcsv.js` aus Task 12/13, deshalb werden in Task 11 zwei Stummel angelegt (siehe Task 11, Step 6) und dort ersetzt.
3. Task 14–15 Startseite, Textseiten, Rauchtests, Pages.
4. Abnahmen durch den Projektleiter: Titelliste Akademiker (Task 2/12), Zechenliste (Task 7), Impressumstext (Task 15), Banner-Ersatz und `PLAN_FREIGEGEBEN` nach Rechteklärung.
