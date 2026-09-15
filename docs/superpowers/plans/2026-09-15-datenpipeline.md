# Datenpipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aus `data/essen1936.csv` eine reproduzierbare Tabelle `build/eintraege.csv` erzeugen, in der jeder Eintrag der Teile I–III eine Koordinate mit Präzisionsstufe (`haus`, `strasse`, `landmarke`, `offen`) und die Herkunft seiner Straßenauflösung trägt.

**Architecture:** Fünf nummerierte Skripte in `pipeline/` lesen je die Ausgabe der vorigen Stufe aus `build/` und schreiben eine neue CSV. Die Logik liegt in reinen Funktionen unter `pipeline/lib/` (Normalisierung, Parser, Straßenindex, Nominatim-Client) und wird mit pytest getestet. Vom Menschen gepflegte Tabellen liegen in `kuratierung/` und werden versioniert; `build/` ist jederzeit löschbar.

**Tech Stack:** Python 3.12, Standardbibliothek (`csv`, `re`, `unicodedata`, `json`, `concurrent.futures`, `difflib`), `requests` 2.31, `pytest` 9. Lokale Nominatim-Instanz (Docker `mediagis/nominatim:4.4`, NRW-Extrakt) unter `http://localhost:8080`. Straßendatensatz `/home/christos/Projekte/essener-strassen/daten/` (strassen.csv, konkordanz_1936.csv, namen.csv).

**Spec:** `/home/christos/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Spec-1-Datenpipeline.md` (freigegeben 2026-09-15). Datenprofil: `Daten-Quelle.md` im selben Ordner.

## Global Constraints

- Quelle `data/essen1936.csv` ist schreibgeschützt; nie verändern, nie mit Komma-Trenner lesen. Einlesen ausschließlich mit `delimiter="\t"`, `quoting=csv.QUOTE_NONE`, `encoding="utf-8"`.
- Nur Teile I, II, III. Zeilen mit `page`-Präfix IV oder W werden verworfen und gezählt.
- Präzision vor Vollständigkeit: Automatik führt nur Eindeutiges zusammen; alles Unsichere bekommt `stufe=offen` oder `mehrdeutig=ja` mit `grund`, wird nie geraten.
- Präzisionsstufen genau: `haus`, `strasse`, `landmarke`, `offen`; `interpoliert` ist ein abgeschaltetes Experiment (nicht in diesem Plan).
- Herkunft der Straßenauflösung genau: `heutig`, `konkordanz`, `stadium`, `kuratiert`, `offen`.
- Zeitfenster für Namensstadien (Stufe d): `1930-01-01` bis `1937-12-31`; außerhalb nur mit `zeitlich_abweichend=ja`.
- Cache-Schlüssel enthält `SCHEMA_VERSION` und alle Anfrageparameter.
- Keine Extrapolation, keine Nachbarnummern-Suche.
- Alle CSV-Ausgaben: UTF-8, Komma-getrennt, `csv.QUOTE_MINIMAL`, Kopfzeile, `lineterminator="\n"`.
- Pfad zum Straßendatensatz nicht hart codieren: Umgebungsvariable `ESSENER_STRASSEN_DIR`, Standard `../essener-strassen/daten` relativ zur Projektwurzel.
- Keine absoluten Pfade auf `/home/christos` im Code (Projekt geht später auf GitHub).
- Commits nach jedem grünen Task; Commit-Nachrichten deutsch, Präfix `feat:`, `test:`, `chore:`, `docs:`; letzte Zeile `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `pyproject.toml` | Projektmetadaten, pytest-Konfiguration |
| `.gitignore` | `build/`, `data/*.csv`, `data/*.html`, `data/*_files/`, `__pycache__/`, `.pytest_cache/` |
| `README.md` | Kurzbeschreibung, Aufruf der Pipeline, Voraussetzungen |
| `pipeline/lib/__init__.py` | leer |
| `pipeline/lib/normalisierung.py` | `norm_strasse`, `norm_vorort`, `norm_stadtteil`, Konstanten `VORORTE` |
| `pipeline/lib/parser.py` | `Adresse`-Dataclass, `parse_adresse` |
| `pipeline/lib/konkordanz.py` | `Strassenindex` (lädt Straßendatensatz und Zuordnungstabelle, Auflösungsleiter, Vorschläge), `VORORT_STADTTEILE` |
| `pipeline/lib/nominatim.py` | `Client` mit JSONL-Cache, `Verortung`-Dataclass, `geokodiere` |
| `pipeline/lib/io.py` | `lies_csv`, `schreib_csv`, `projektwurzel`, `strassen_dir` |
| `pipeline/01_einlesen.py` | Quelle → `build/01_bereinigt.csv`, `build/dubletten.csv`, `build/01_ausgeschlossen.csv` |
| `pipeline/02_adresse_parsen.py` | → `build/02_geparst.csv` |
| `pipeline/03_strasse_aufloesen.py` | → `build/03_strassen.csv`, `build/03_aufgeloest.csv`, `build/strassen_vorschlaege.csv` |
| `pipeline/04_geokodieren.py` | → `build/04_geokodiert.csv`, `build/eintraege.csv` |
| `pipeline/05_bericht.py` | → `build/bericht.md`, `build/kontrollpunkte.geojson` |
| `kuratierung/zeilenkorrekturen.csv` | Reparatur defekter Zeilen und Vorort-Ausreißer, mit Beleg |
| `kuratierung/strassen_zuordnung.csv` | vom Menschen bestätigte Straßenzuordnungen |
| `kuratierung/landmarken.csv` | Koordinaten für Adressen ohne Hausnummer |
| `werkzeuge/kontrollkarte.html` | Wegwerf-Prüfkarte (Leaflet, liest `build/kontrollpunkte.geojson`) |
| `tests/test_normalisierung.py`, `tests/test_parser.py`, `tests/test_konkordanz.py`, `tests/test_nominatim.py`, `tests/test_einlesen.py`, `tests/test_bericht.py` | Tests |
| `tests/fixtures/` | kleine TSV/CSV-Fixtures |

---

### Task 0: Repository-Grundgerüst

**Files:**
- Create: `.gitignore`, `pyproject.toml`, `README.md`, `pipeline/__init__.py`, `pipeline/lib/__init__.py`, `pipeline/lib/io.py`, `tests/__init__.py`, `tests/test_io.py`, `kuratierung/.gitkeep`

**Interfaces:**
- Produces: `pipeline.lib.io.projektwurzel() -> pathlib.Path`, `strassen_dir() -> Path`, `lies_csv(pfad, delimiter=",") -> list[dict]`, `schreib_csv(pfad, zeilen: list[dict], felder: list[str]) -> None`.

- [ ] **Step 1: Git initialisieren und Grunddateien anlegen**

```bash
cd /home/christos/Projekte/AdressbuchEssen-v2
git init -b main
cat > .gitignore <<'EOF'
build/
data/*.csv
data/*.html
data/*_files/
__pycache__/
.pytest_cache/
*.pyc
EOF
cat > pyproject.toml <<'EOF'
[project]
name = "adressbuch-essen-1936"
version = "0.1.0"
description = "Datenpipeline zum Essener Adreßbuch 1936: Bereinigung, Adress-Parsing, Straßenauflösung, Geokodierung"
requires-python = ">=3.12"
dependencies = ["requests>=2.31"]

[project.optional-dependencies]
test = ["pytest>=8"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
EOF
cat > README.md <<'EOF'
# Adressbuch Essen 1936 — Datenpipeline (v2)

Erzeugt aus dem DES-Export des Essener Adreßbuchs 1936 (`data/essen1936.csv`, Tab-getrennt)
eine geokodierte Tabelle mit ausgewiesener Präzisionsstufe je Eintrag.

## Voraussetzungen
- Python ≥ 3.12, `pip install -e .[test]`
- Lokale Nominatim-Instanz unter `http://localhost:8080` (NRW-Extrakt)
- Straßendatensatz `essener-strassen` (Umgebungsvariable `ESSENER_STRASSEN_DIR`, Standard `../essener-strassen/daten`)

## Aufruf
```
python3 pipeline/01_einlesen.py
python3 pipeline/02_adresse_parsen.py
python3 pipeline/03_strasse_aufloesen.py
python3 pipeline/04_geokodieren.py
python3 pipeline/05_bericht.py
```
Ausgaben liegen in `build/` (löschbar). Vom Menschen gepflegte Tabellen in `kuratierung/`.
EOF
mkdir -p pipeline/lib tests/fixtures kuratierung werkzeuge
touch pipeline/__init__.py pipeline/lib/__init__.py tests/__init__.py kuratierung/.gitkeep
```

- [ ] **Step 2: Test für io schreiben**

`tests/test_io.py`:
```python
from pathlib import Path
from pipeline.lib import io


def test_projektwurzel_enthaelt_pyproject():
    assert (io.projektwurzel() / "pyproject.toml").exists()


def test_strassen_dir_aus_umgebung(monkeypatch, tmp_path):
    monkeypatch.setenv("ESSENER_STRASSEN_DIR", str(tmp_path))
    assert io.strassen_dir() == tmp_path


def test_csv_roundtrip(tmp_path):
    pfad = tmp_path / "x.csv"
    io.schreib_csv(pfad, [{"a": "1", "b": "ä,ö"}], ["a", "b"])
    assert io.lies_csv(pfad) == [{"a": "1", "b": "ä,ö"}]


def test_lies_tsv_ohne_quoting(tmp_path):
    pfad = tmp_path / "x.tsv"
    pfad.write_text('a\tb\n1\t"x\n', encoding="utf-8")
    assert io.lies_csv(pfad, delimiter="\t") == [{"a": "1", "b": '"x'}]
```

- [ ] **Step 3: Test laufen lassen, Fehlschlag prüfen**

Run: `pytest tests/test_io.py -v`
Expected: FAIL mit `ImportError` / `AttributeError`.

- [ ] **Step 4: io implementieren**

`pipeline/lib/io.py`:
```python
"""Ein- und Ausgabe: Pfade und CSV-Helfer."""
from __future__ import annotations

import csv
import os
from pathlib import Path

csv.field_size_limit(10**9)


def projektwurzel() -> Path:
    return Path(__file__).resolve().parents[2]


def strassen_dir() -> Path:
    env = os.environ.get("ESSENER_STRASSEN_DIR")
    if env:
        return Path(env)
    return (projektwurzel().parent / "essener-strassen" / "daten").resolve()


def lies_csv(pfad: Path | str, delimiter: str = ",") -> list[dict]:
    quoting = csv.QUOTE_NONE if delimiter == "\t" else csv.QUOTE_MINIMAL
    with open(pfad, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter, quoting=quoting))


def schreib_csv(pfad: Path | str, zeilen: list[dict], felder: list[str]) -> None:
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(zeilen)
```

- [ ] **Step 5: Tests grün prüfen**

Run: `pytest tests/test_io.py -v`
Expected: 4 PASS.

- [ ] **Step 6: Commit**

```bash
git add .gitignore pyproject.toml README.md pipeline tests kuratierung
git commit -m "chore: Projektgrundgerüst mit CSV-Helfern

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 1: Normalisierung von Straßennamen, Vororten und Stadtteilen

**Files:**
- Create: `pipeline/lib/normalisierung.py`
- Test: `tests/test_normalisierung.py`

**Interfaces:**
- Produces: `norm_strasse(text: str) -> str` (kleingeschrieben, `straße` ausgeschrieben, Einzelleerzeichen); `norm_vorort(text: str) -> tuple[str, bool]` (kanonischer Vorort oder Originaltext, ok-Flag); `norm_stadtteil(text: str) -> str`; Konstante `VORORTE: tuple[str, ...]` (12 Namen).

- [ ] **Step 1: Failing Tests schreiben**

`tests/test_normalisierung.py`:
```python
import pytest
from pipeline.lib.normalisierung import VORORTE, norm_stadtteil, norm_strasse, norm_vorort


@pytest.mark.parametrize("roh, erwartet", [
    ("Karlstr.", "karlstraße"),
    ("Bochumer Str.", "bochumer straße"),
    ("Heidhausener Straße", "heidhausener straße"),
    ("Rellinghauser Strasse", "rellinghauser straße"),
    ("  Steeler  Str. ", "steeler straße"),
    ("Kl. Hammerstr.", "kleine hammerstraße"),
    ("Gr. Hammerstr.", "große hammerstraße"),
    ("Kopstadtpl.", "kopstadtplatz"),
    ("Herm.-Göring-Str.", "herm.-göring-straße"),
    ("Am krausen Bäumchen", "am krausen bäumchen"),
    ("Hermann–Göring–Straße", "hermann-göring-straße"),
])
def test_norm_strasse(roh, erwartet):
    assert norm_strasse(roh) == erwartet


def test_norm_strasse_nfc():
    # "ä" als Kombinationszeichen (a + U+0308) muss zu NFC "ä" werden
    assert norm_strasse("Bäumchenweg") == "bäumchenweg"


def test_vororte_sind_zwoelf():
    assert len(VORORTE) == 12
    assert "Ueberruhr" in VORORTE and "Steele" in VORORTE


@pytest.mark.parametrize("roh, erwartet, ok", [
    ("Steele", "Steele", True),
    ("karnap", "Karnap", True),
    ("", "", True),
    ("Frillenburg", "Frillenburg", False),
    ("Überruhr", "Ueberruhr", True),
])
def test_norm_vorort(roh, erwartet, ok):
    assert norm_vorort(roh) == (erwartet, ok)


@pytest.mark.parametrize("roh, erwartet", [
    ("Stoppen- berg", "Stoppenberg"),
    ("Alten-essen-Süd", "Altenessen-Süd"),
    ("Ost-viertel", "Ostviertel"),
    ("Brenedey", "Bredeney"),
    ("Deltwig", "Dellwig"),
    ("Geschede", "Gerschede"),
    ("Schönnebeck", "Schonnebeck"),
    ("Schönebeck", "Schonnebeck"),
    ("Margarethenhöhe", "Margaretenhöhe"),
    ("Steele", "Steele"),
    ("Überruhr-Hinsel", "Überruhr-Hinsel"),
    ("Kettwig vor der Brücke", "Kettwig"),
])
def test_norm_stadtteil(roh, erwartet):
    assert norm_stadtteil(roh) == erwartet
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `pytest tests/test_normalisierung.py -v`
Expected: FAIL mit `ModuleNotFoundError`.

- [ ] **Step 3: Implementieren**

`pipeline/lib/normalisierung.py`:
```python
"""Normalisierung von Straßennamen, Vororten (Buch 1936) und Stadtteilen (Dickhoff/OSM)."""
from __future__ import annotations

import re
import unicodedata

VORORTE: tuple[str, ...] = (
    "Frillendorf", "Heidhausen", "Heisingen", "Karnap", "Katernberg", "Kray",
    "Kupferdreh", "Schonnebeck", "Steele", "Stoppenberg", "Ueberruhr", "Werden",
)
_VORORT_ALIAS = {v.lower(): v for v in VORORTE}
_VORORT_ALIAS.update({"überruhr": "Ueberruhr", "ueberruhr": "Ueberruhr"})

_TYPO = str.maketrans({"´": "'", "’": "'", "`": "'", " ": " ", "–": "-", "—": "-"})

_ERSETZUNGEN = [
    (re.compile(r"\bstr\.(?=\s|$)"), "straße"),          # "Bochumer str." → "bochumer straße"
    (re.compile(r"(?<=[a-zäöüß])str\.(?=\s|$)"), "straße"),  # "karlstr." → "karlstraße"
    (re.compile(r"strasse\b"), "straße"),
    (re.compile(r"\bpl\.(?=\s|$)"), "platz"),
    (re.compile(r"(?<=[a-zäöüß])pl\.(?=\s|$)"), "platz"),
    (re.compile(r"^kl\.\s+"), "kleine "),
    (re.compile(r"^gr\.\s+"), "große "),
]


def norm_strasse(text: str) -> str:
    s = unicodedata.normalize("NFC", text).translate(_TYPO).strip().lower()
    s = re.sub(r"\s+", " ", s)
    for muster, ersatz in _ERSETZUNGEN:
        s = muster.sub(ersatz, s)
    return s.strip()


def norm_vorort(text: str) -> tuple[str, bool]:
    t = unicodedata.normalize("NFC", text).strip()
    if not t:
        return "", True
    kanon = _VORORT_ALIAS.get(t.lower())
    if kanon is None:
        return t, False
    return kanon, True


_STADTTEIL_ALIAS = {
    "alten-essen-süd": "Altenessen-Süd",
    "ost-viertel": "Ostviertel",
    "brenedey": "Bredeney",
    "deltwig": "Dellwig",
    "geschede": "Gerschede",
    "schönnebeck": "Schonnebeck",
    "schönebeck": "Schonnebeck",
    "margarethenhöhe": "Margaretenhöhe",
    "stoppen- berg": "Stoppenberg",
    "stoppen-berg": "Stoppenberg",
    "kettwig vor der brücke": "Kettwig",
}


def norm_stadtteil(text: str) -> str:
    t = unicodedata.normalize("NFC", text).translate(_TYPO).strip()
    t = re.sub(r"\s+", " ", t)
    alias = _STADTTEIL_ALIAS.get(t.lower())
    if alias:
        return alias
    return t.replace("- ", "")
```

- [ ] **Step 4: Tests grün prüfen**

Run: `pytest tests/test_normalisierung.py -v`
Expected: alle PASS. Falls „Herm.-Göring-Str.“ scheitert: die zweite Regel (`(?<=[a-zäöüß])str\.`) greift nach „-“ nicht; Regel um `-` erweitern: `(?<=[a-zäöüß\-])`.

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/normalisierung.py tests/test_normalisierung.py
git commit -m "feat: Normalisierung von Straßen, Vororten und Stadtteilen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Adress-Parser

**Files:**
- Create: `pipeline/lib/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Produces: `@dataclass Adresse(strasse_roh: str, hausnr: str, hausnr_zusatz: str, hausnr_bis: str, lage: str, zusatz_frei: str, status: str)`; `parse_adresse(text: str) -> Adresse`; `status` ∈ `{"ok", "ohne_nummer", "leer", "unklar"}`. Alle Felder Strings, leer = `""`.

- [ ] **Step 1: Failing Tests schreiben**

`tests/test_parser.py`:
```python
import pytest
from pipeline.lib.parser import Adresse, parse_adresse


def a(**kw):
    basis = dict(strasse_roh="", hausnr="", hausnr_zusatz="", hausnr_bis="", lage="", zusatz_frei="", status="ok")
    basis.update(kw)
    return Adresse(**basis)


@pytest.mark.parametrize("text, erwartet", [
    ("Kraspothstr. 44", a(strasse_roh="Kraspothstr.", hausnr="44")),
    ("Kahrstr. 39D", a(strasse_roh="Kahrstr.", hausnr="39", hausnr_zusatz="d")),
    ("Lührmannstr. 24A", a(strasse_roh="Lührmannstr.", hausnr="24", hausnr_zusatz="a")),
    ("Arndtstr. 14 III", a(strasse_roh="Arndtstr.", hausnr="14", lage="III")),
    ("Schubertstr. 43 I.", a(strasse_roh="Schubertstr.", hausnr="43", lage="I")),
    ("Julienstr. 26 Iii", a(strasse_roh="Julienstr.", hausnr="26", lage="III")),
    ("Steeler Str. 12 Erdg.", a(strasse_roh="Steeler Str.", hausnr="12", lage="Erdg.")),
    ("Steeler Str. 12 Untg.", a(strasse_roh="Steeler Str.", hausnr="12", lage="Untg.")),
    ("Frohnhauser Str. 137-137A", a(strasse_roh="Frohnhauser Str.", hausnr="137", hausnr_bis="137a")),
    ("Koloniestr. 7-13", a(strasse_roh="Koloniestr.", hausnr="7", hausnr_bis="13")),
    ("Taborstr. 15A.15B.15C", a(strasse_roh="Taborstr.", hausnr="15", hausnr_zusatz="a", zusatz_frei="15B.15C")),
    ("Vogelheimer Str. Nr. 109", a(strasse_roh="Vogelheimer Str.", hausnr="109")),
    ("Laubenhof 1 Nr. 4", a(strasse_roh="Laubenhof", hausnr="1", zusatz_frei="Nr. 4")),
    ("Klosterstr. 1.3", a(strasse_roh="Klosterstr.", hausnr="1", zusatz_frei="3")),
    ("Hauptstr. 14 1/2", a(strasse_roh="Hauptstr.", hausnr="14", zusatz_frei="1/2")),
    ("Wächtlerstr., Lagerplatz", a(strasse_roh="Wächtlerstr.", zusatz_frei="Lagerplatz", status="ohne_nummer")),
    ("Börsenhaus", a(strasse_roh="Börsenhaus", status="ohne_nummer")),
    ("Alfredistraße ", a(strasse_roh="Alfredistraße", status="ohne_nummer")),
    ("", a(status="leer")),
    ("   ", a(status="leer")),
    ("II. Schichtstr., Zechengelände", a(strasse_roh="II. Schichtstr.", zusatz_frei="Zechengelände", status="ohne_nummer")),
    ("Am krausen Bäumchen 18", a(strasse_roh="Am krausen Bäumchen", hausnr="18")),
    ("Hstr. 12a", a(strasse_roh="Hstr.", hausnr="12", hausnr_zusatz="a")),
])
def test_parse_adresse(text, erwartet):
    assert parse_adresse(text) == erwartet


def test_unklar_wenn_zahl_vor_strasse():
    r = parse_adresse("12 Karlstr.")
    assert r.status == "unklar"
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `pytest tests/test_parser.py -v`
Expected: FAIL mit `ModuleNotFoundError`.

- [ ] **Step 3: Implementieren**

`pipeline/lib/parser.py`:
```python
"""Zerlegt das Feld `Adresse` in Straße, Hausnummer, Zusatz, Lage."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_ROEMISCH = {"i": "I", "ii": "II", "iii": "III", "iv": "IV", "v": "V"}
_LAGE_WORT = re.compile(r"^(erdg|untg|erdgesch|erdgeschoss|untergeschoss|hochpt|parterre)\.?$", re.I)


@dataclass(frozen=True)
class Adresse:
    strasse_roh: str
    hausnr: str
    hausnr_zusatz: str
    hausnr_bis: str
    lage: str
    zusatz_frei: str
    status: str


def _leer(status: str, strasse: str = "", zusatz: str = "") -> Adresse:
    return Adresse(strasse, "", "", "", "", zusatz, status)


def parse_adresse(text: str) -> Adresse:
    t = unicodedata.normalize("NFC", text or "").replace(" ", " ").strip()
    t = re.sub(r"\s+", " ", t)
    if not t:
        return _leer("leer")
    if re.match(r"^\d", t) and not re.match(r"^(I{1,3}|IV)\.\s", t):
        return _leer("unklar", strasse_roh_fallback(t))
    # Straße = alles vor der ersten Ziffer, die nicht Teil eines führenden "II." ist
    m = re.match(r"^(?P<strasse>(?:(?:I{1,3}|IV)\.\s)?[^\d]*?)(?:,\s*|\s+)(?:Nr\.\s*)?(?P<rest>\d.*)$", t)
    if not m:
        # keine Ziffer → ohne Nummer; Zusatz nach Komma abtrennen
        strasse, _, zusatz = t.partition(",")
        return _leer("ohne_nummer", strasse.strip(" ,"), zusatz.strip())
    strasse = m.group("strasse").strip(" ,")
    rest = m.group("rest")
    # Hausnummer + optionaler Buchstabe
    hm = re.match(r"^(?P<nr>\d+)\s?(?P<zus>[A-Za-z](?![a-zäöü]))?(?P<rest>.*)$", rest)
    hausnr = hm.group("nr")
    zusatz = (hm.group("zus") or "").lower()
    rest = hm.group("rest").strip()
    hausnr_bis = ""
    zusatz_frei_teile: list[str] = []
    lage = ""
    # Bereich "-13" / "-137A"
    bm = re.match(r"^-\s*(?P<bis>\d+\s?[A-Za-z]?)(?P<rest>.*)$", rest)
    if bm:
        hausnr_bis = bm.group("bis").replace(" ", "").lower()
        rest = bm.group("rest").strip()
    # Liste "15A.15B.15C" bzw. ".3"
    lm = re.match(r"^\.(?P<liste>\S+)(?P<rest>.*)$", rest)
    if lm:
        zusatz_frei_teile.append(lm.group("liste"))
        rest = lm.group("rest").strip()
    for tok in rest.split():
        tl = tok.rstrip(".").lower()
        if tl in _ROEMISCH and not lage:
            lage = _ROEMISCH[tl]
        elif _LAGE_WORT.match(tok) and not lage:
            lage = tok if tok.endswith(".") else tok + "."
        else:
            zusatz_frei_teile.append(tok)
    zusatz_frei = " ".join(zusatz_frei_teile).strip(" ,")
    return Adresse(strasse, hausnr, zusatz, hausnr_bis, lage, zusatz_frei, "ok")


def strasse_roh_fallback(t: str) -> str:
    return t
```

Hinweis für den Implementierer: `Untg.` und `Erdg.` müssen als `lage` genau so erscheinen wie im Test (`"Erdg."`, `"Untg."`); die Regel `tok if tok.endswith(".") else tok + "."` sichert das.

- [ ] **Step 4: Tests grün prüfen**

Run: `pytest tests/test_parser.py -v`
Expected: alle PASS. Bei Abweichungen einzelne Regex anpassen; keine Testerwartung ändern, sie stammen aus `Daten-Quelle.md`.

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/parser.py tests/test_parser.py
git commit -m "feat: Adress-Parser für Straße, Hausnummer, Zusatz und Lage

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Stufe 01 — Einlesen, Reparieren, Filtern, Dubletten

**Files:**
- Create: `pipeline/01_einlesen.py`, `pipeline/lib/einlesen.py`, `kuratierung/zeilenkorrekturen.csv`
- Test: `tests/test_einlesen.py`, `tests/fixtures/mini_quelle.tsv`, `tests/fixtures/mini_zeilenkorrekturen.csv`

**Interfaces:**
- Consumes: `io.lies_csv`, `io.schreib_csv`, `norm_vorort`.
- Produces: `einlesen.verarbeite(quelle_pfad, korrekturen_pfad) -> tuple[list[dict], list[dict], list[dict]]` = (bereinigt, dubletten, ausgeschlossen). Spalten von `bereinigt`: die 17 Quellspalten plus `teil`, `seite`, `dublette_von`, `vorort_ok`. `QUELLFELDER: list[str]` (17 Namen in Quellreihenfolge).
- Format `zeilenkorrekturen.csv`: `id,aktion,feld,neu,beleg`; `aktion` ∈ `{leerfeld_entfernen, setze_feld}`; bei `leerfeld_entfernen` ist `feld` der 0-basierte Index des zu löschenden leeren Feldes in der Rohzeile.

- [ ] **Step 1: Kuratierungstabelle anlegen**

`kuratierung/zeilenkorrekturen.csv`:
```csv
id,aktion,feld,neu,beleg
16692127,leerfeld_entfernen,4,,"Zeile 139349 hat 18 Felder; ein leeres Feld zu viel vor Adresse (Strauß, Witwe, Herskamp 23)"
17259959,leerfeld_entfernen,7,,"Zeile 194709 hat 18 Felder; ein leeres Feld zu viel vor Eigentümer (Höing, Bochumer Str. 114, Steele)"
```

- [ ] **Step 2: Fixtures und Failing Test schreiben**

`tests/fixtures/mini_quelle.tsv` (Tab-getrennt! beim Anlegen mit `printf` oder Editor auf echte Tabs achten):
```
page	lastname	firstname	Beruf o. ä.	Adresse	Ortsname	Ortskennung	Firmenname	Familienstand	Vorname Bezugsperson	Beruf Bezugsperson	Eigentümer	Funktionsträger	abweichender Wohnort	Vorort	Verwalter	id
I-551	Serogocki	Wladislaus	Invalide	Kraspothstr. 44	Essen	ESSSENJO31ML								Katernberg		16385477
I-551	Serogocki	Wladislaus	Invalide	Kraspothstr. 44	Essen	ESSSENJO31ML								Katernberg		16385478
II-040	Höing	A.	Bahnmstr. a. D.	Bochumer Str. 114	Essen	ESSSENJO31ML						Eigentümer			Steele		17259959
IV-003	Müller	August	Ratsherr	 	Essen	ESSSENJO31ML					ja				17915624
I-100	Test	Karl	Bergm.	Schulstr. 1 	Essen	ESSSENJO31ML								karnap		11111111
I-101	Test	Anna		Schulstr. 2	Essen	ESSSENJO31ML							 	Frillenburg		11111112
```
Die dritte Datenzeile (Höing) muss **18 Felder** haben: nach `ESSSENJO31ML` folgen fünf leere Felder, dann `Eigentümer`, dann zwei leere, `Steele`, ein leeres, `17259959`. Anlegen mit:
```bash
python3 - <<'EOF'
rows = [
 ["page","lastname","firstname","Beruf o. ä.","Adresse","Ortsname","Ortskennung","Firmenname","Familienstand","Vorname Bezugsperson","Beruf Bezugsperson","Eigentümer","Funktionsträger","abweichender Wohnort","Vorort","Verwalter","id"],
 ["I-551","Serogocki","Wladislaus","Invalide","Kraspothstr. 44","Essen","ESSSENJO31ML","","","","","","","","Katernberg","","16385477"],
 ["I-551","Serogocki","Wladislaus","Invalide","Kraspothstr. 44","Essen","ESSSENJO31ML","","","","","","","","Katernberg","","16385478"],
 ["II-040","Höing","A.","Bahnmstr. a. D.","Bochumer Str. 114","Essen","ESSSENJO31ML","","","","","","Eigentümer","","","Steele","","17259959"],
 ["IV-003","Müller","August","Ratsherr"," ","Essen","ESSSENJO31ML","","","","","","ja","","","","17915624"],
 ["I-100","Test","Karl","Bergm.","Schulstr. 1 ","Essen","ESSSENJO31ML","","","","","","","","karnap","","11111111"],
 ["I-101","Test","Anna","","Schulstr. 2","Essen","ESSSENJO31ML","","","","","",""," ","Frillenburg","","11111112"],
]
with open("tests/fixtures/mini_quelle.tsv","w",encoding="utf-8") as f:
    for r in rows: f.write("\t".join(r)+"\n")
EOF
```

`tests/fixtures/mini_zeilenkorrekturen.csv`:
```csv
id,aktion,feld,neu,beleg
17259959,leerfeld_entfernen,7,,Test
11111112,setze_feld,Vorort,Frillendorf,Test
```

`tests/test_einlesen.py`:
```python
from pathlib import Path
from pipeline.lib import einlesen

FIX = Path(__file__).parent / "fixtures"


def test_verarbeite_mini():
    bereinigt, dubletten, ausgeschlossen = einlesen.verarbeite(FIX / "mini_quelle.tsv", FIX / "mini_zeilenkorrekturen.csv")
    ids = [z["id"] for z in bereinigt]
    assert ids == ["16385477", "17259959", "11111111", "11111112"]
    assert dubletten == [{"id": "16385478", "dublette_von": "16385477"}]
    assert ausgeschlossen == [{"id": "17915624", "grund": "teil_IV_W"}]
    hoeing = bereinigt[1]
    assert hoeing["Eigentümer"] == "Eigentümer" and hoeing["Vorort"] == "Steele" and hoeing["teil"] == "II" and hoeing["seite"] == "40"
    karl = bereinigt[2]
    assert karl["Vorort"] == "Karnap" and karl["Adresse"] == "Schulstr. 1" and karl["vorort_ok"] == "ja"
    anna = bereinigt[3]
    assert anna["Vorort"] == "Frillendorf" and anna["abweichender Wohnort"] == ""


def test_unbekannter_vorort_bleibt_markiert(tmp_path):
    q = FIX / "mini_quelle.tsv"
    leer = tmp_path / "k.csv"
    leer.write_text("id,aktion,feld,neu,beleg\n", encoding="utf-8")
    bereinigt, _, _ = einlesen.verarbeite(q, leer)
    anna = [z for z in bereinigt if z["id"] == "11111112"][0]
    assert anna["Vorort"] == "Frillenburg" and anna["vorort_ok"] == "nein"


def test_zeile_mit_falscher_feldzahl_ohne_korrektur_wird_ausgeschlossen(tmp_path):
    q = FIX / "mini_quelle.tsv"
    leer = tmp_path / "k.csv"
    leer.write_text("id,aktion,feld,neu,beleg\n", encoding="utf-8")
    _, _, ausgeschlossen = einlesen.verarbeite(q, leer)
    assert {"id": "17259959", "grund": "feldzahl_18"} in ausgeschlossen
```

- [ ] **Step 3: Fehlschlag prüfen**

Run: `pytest tests/test_einlesen.py -v`
Expected: FAIL mit `ModuleNotFoundError`.

- [ ] **Step 4: Implementieren**

`pipeline/lib/einlesen.py`:
```python
"""Stufe 01: Quelle einlesen, Zeilen reparieren, Teile filtern, Dubletten markieren."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from pipeline.lib.io import lies_csv
from pipeline.lib.normalisierung import norm_vorort

QUELLFELDER = [
    "page", "lastname", "firstname", "Beruf o. ä.", "Adresse", "Ortsname", "Ortskennung",
    "Firmenname", "Familienstand", "Vorname Bezugsperson", "Beruf Bezugsperson", "Eigentümer",
    "Funktionsträger", "abweichender Wohnort", "Vorort", "Verwalter", "id",
]
ZUSATZFELDER = ["teil", "seite", "dublette_von", "vorort_ok"]
AUSGABEFELDER = QUELLFELDER + ZUSATZFELDER
ERLAUBTE_TEILE = {"I", "II", "III"}


def _lade_korrekturen(pfad: Path) -> dict[str, list[dict]]:
    k: dict[str, list[dict]] = {}
    for z in lies_csv(pfad):
        k.setdefault(z["id"], []).append(z)
    return k


def _rohzeilen(pfad: Path):
    with open(pfad, encoding="utf-8", newline="") as f:
        r = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        kopf = next(r)
        assert kopf == QUELLFELDER, f"unerwarteter Kopf: {kopf}"
        yield from r


def verarbeite(quelle: Path, korrekturen: Path) -> tuple[list[dict], list[dict], list[dict]]:
    korr = _lade_korrekturen(korrekturen)
    bereinigt: list[dict] = []
    dubletten: list[dict] = []
    ausgeschlossen: list[dict] = []
    gesehen: dict[tuple, str] = {}
    for roh in _rohzeilen(quelle):
        zid = roh[-1].strip() if roh else ""
        for k in korr.get(zid, []):
            if k["aktion"] == "leerfeld_entfernen":
                idx = int(k["feld"])
                if len(roh) > len(QUELLFELDER) and roh[idx].strip() == "":
                    del roh[idx]
        if len(roh) != len(QUELLFELDER):
            ausgeschlossen.append({"id": zid, "grund": f"feldzahl_{len(roh)}"})
            continue
        z = {f: v.strip() for f, v in zip(QUELLFELDER, roh)}
        for k in korr.get(zid, []):
            if k["aktion"] == "setze_feld":
                z[k["feld"]] = k["neu"]
        m = re.match(r"^(I{1,3}|IV|W)-(\d+)$", z["page"])
        teil = m.group(1) if m else ""
        if teil not in ERLAUBTE_TEILE:
            ausgeschlossen.append({"id": z["id"], "grund": "teil_IV_W" if teil in ("IV", "W") else "page_unlesbar"})
            continue
        z["teil"], z["seite"] = teil, str(int(m.group(2)))
        vorort, ok = norm_vorort(z["Vorort"])
        z["Vorort"], z["vorort_ok"] = vorort, "ja" if ok else "nein"
        schluessel = tuple(z[f] for f in QUELLFELDER if f != "id")
        if schluessel in gesehen:
            dubletten.append({"id": z["id"], "dublette_von": gesehen[schluessel]})
            continue
        gesehen[schluessel] = z["id"]
        z["dublette_von"] = ""
        bereinigt.append(z)
    return bereinigt, dubletten, ausgeschlossen
```

`pipeline/01_einlesen.py`:
```python
"""Stufe 01: data/essen1936.csv → build/01_bereinigt.csv, build/dubletten.csv, build/01_ausgeschlossen.csv"""
from pipeline.lib import einlesen
from pipeline.lib.io import projektwurzel, schreib_csv

W = projektwurzel()
bereinigt, dubletten, ausgeschlossen = einlesen.verarbeite(
    W / "data" / "essen1936.csv", W / "kuratierung" / "zeilenkorrekturen.csv")
schreib_csv(W / "build" / "01_bereinigt.csv", bereinigt, einlesen.AUSGABEFELDER)
schreib_csv(W / "build" / "dubletten.csv", dubletten, ["id", "dublette_von"])
schreib_csv(W / "build" / "01_ausgeschlossen.csv", ausgeschlossen, ["id", "grund"])
print(f"bereinigt {len(bereinigt)}  dubletten {len(dubletten)}  ausgeschlossen {len(ausgeschlossen)}")
```

- [ ] **Step 5: Tests grün prüfen**

Run: `pytest tests/test_einlesen.py -v`
Expected: 3 PASS.

- [ ] **Step 6: Auf der echten Quelle laufen lassen und Zahlen prüfen**

Run: `python3 pipeline/01_einlesen.py`
Expected (aus Daten-Quelle.md): ausgeschlossen = 1.786 (IV 1.749 + W 37), dubletten ≈ 152 (I 88 + II 57 + III 7; die IV-Dublette entfällt), bereinigt ≈ 240.666. Abweichungen > 5 Zeilen untersuchen, nicht hinnehmen.

- [ ] **Step 7: Commit**

```bash
git add pipeline/01_einlesen.py pipeline/lib/einlesen.py kuratierung/zeilenkorrekturen.csv tests/test_einlesen.py tests/fixtures
git commit -m "feat: Stufe 01 Einlesen mit Zeilenreparatur, Teilfilter und Dubletten

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Stufe 02 — Adresse parsen

**Files:**
- Create: `pipeline/02_adresse_parsen.py`
- Test: `tests/test_stufe02.py`

**Interfaces:**
- Consumes: `parse_adresse`, `norm_strasse`, `io`.
- Produces: `build/02_geparst.csv` = Spalten von `01_bereinigt.csv` plus `strasse_roh, strasse_norm, hausnr, hausnr_zusatz, hausnr_bis, lage, zusatz_frei, parse_status`. Funktion `pipeline.lib.stufen.parse_zeilen(zeilen: list[dict]) -> list[dict]` in neuer Datei `pipeline/lib/stufen.py`.

- [ ] **Step 1: Failing Test**

`tests/test_stufe02.py`:
```python
from pipeline.lib.stufen import parse_zeilen


def test_parse_zeilen_ergaenzt_felder():
    z = [{"id": "1", "Adresse": "Kahrstr. 39D II", "Vorort": ""}]
    out = parse_zeilen(z)
    assert out[0]["strasse_roh"] == "Kahrstr." and out[0]["strasse_norm"] == "kahrstraße"
    assert out[0]["hausnr"] == "39" and out[0]["hausnr_zusatz"] == "d" and out[0]["lage"] == "II"
    assert out[0]["parse_status"] == "ok"
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `pytest tests/test_stufe02.py -v` → FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implementieren**

`pipeline/lib/stufen.py`:
```python
"""Zeilenweise Anwendung der Bibliotheksfunktionen (Stufen 02 und 03)."""
from __future__ import annotations

from dataclasses import asdict

from pipeline.lib.normalisierung import norm_strasse
from pipeline.lib.parser import parse_adresse

PARSEFELDER = ["strasse_roh", "strasse_norm", "hausnr", "hausnr_zusatz", "hausnr_bis", "lage", "zusatz_frei", "parse_status"]


def parse_zeilen(zeilen: list[dict]) -> list[dict]:
    out = []
    for z in zeilen:
        a = parse_adresse(z.get("Adresse", ""))
        d = dict(z)
        d.update({k: v for k, v in asdict(a).items() if k != "status"})
        d["parse_status"] = a.status
        d["strasse_norm"] = norm_strasse(a.strasse_roh) if a.strasse_roh else ""
        out.append(d)
    return out
```

`pipeline/02_adresse_parsen.py`:
```python
"""Stufe 02: build/01_bereinigt.csv → build/02_geparst.csv"""
from collections import Counter
from pipeline.lib import einlesen
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv
from pipeline.lib.stufen import PARSEFELDER, parse_zeilen

W = projektwurzel()
zeilen = parse_zeilen(lies_csv(W / "build" / "01_bereinigt.csv"))
schreib_csv(W / "build" / "02_geparst.csv", zeilen, einlesen.AUSGABEFELDER + PARSEFELDER)
print(Counter(z["parse_status"] for z in zeilen))
```

- [ ] **Step 4: Tests grün, echten Lauf prüfen**

Run: `pytest tests/test_stufe02.py -v && python3 pipeline/02_adresse_parsen.py`
Expected: PASS; Counter ≈ ok 238.000+, ohne_nummer ≈ 550, leer ≈ 180 (IV/W-Zeilen fehlen bereits), unklar wenige. Jede `unklar`-Zeile stichprobenartig ansehen (`grep`), um Parserlücken zu erkennen; neue Fälle als Test in Task 2 ergänzen.

- [ ] **Step 5: Commit**

```bash
git add pipeline/02_adresse_parsen.py pipeline/lib/stufen.py tests/test_stufe02.py
git commit -m "feat: Stufe 02 Adresse parsen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Straßenindex mit Auflösungsleiter

**Files:**
- Create: `pipeline/lib/konkordanz.py`, `kuratierung/strassen_zuordnung.csv`
- Test: `tests/test_konkordanz.py`, `tests/fixtures/strassen/strassen.csv`, `tests/fixtures/strassen/konkordanz_1936.csv`, `tests/fixtures/strassen/namen.csv`, `tests/fixtures/strassen_zuordnung.csv`

**Interfaces:**
- Produces: `@dataclass Aufloesung(strasse_heute: str, schl_nr: str, stadtteil: str, herkunft: str, zeitlich_abweichend: str, mehrdeutig: str, kandidaten: str)`; `class Strassenindex` mit `__init__(self, strassen_dir: Path, zuordnung_pfad: Path)`, `aufloesen(self, strasse_norm: str, vorort: str) -> Aufloesung`, `vorschlaege(self, strasse_norm: str, n: int = 3) -> list[tuple[str, str, float]]` (Name im Datensatz, heutiges Lemma, Ähnlichkeit); Konstante `VORORT_STADTTEILE: dict[str, frozenset[str]]`; `FENSTER = ("1930-01-01", "1937-12-31")`.
- Format `strassen_zuordnung.csv`: `strasse_roh_norm,vorort,strasse_heute,schl_nr,beleg,bearbeiter,datum`.

- [ ] **Step 1: Fixtures anlegen**

`tests/fixtures/strassen/strassen.csv`:
```csv
schl_nr,lemma,stadtteile,strassenklasse,namensgruppe,verweis_auf,buchseite,status
00001,Karlstraße,Altenessen-Nord; Altenessen-Süd,Gemeindestraße,,,10,automatisch
00002,Hauptstraße,Kettwig,Gemeindestraße,,,11,automatisch
00003,Bredeneyer Straße,Bredeney; Werden,Gemeindestraße,,,12,automatisch
00004,Achternbergstraße,Kray,Gemeindestraße,,,13,automatisch
00005,Am Bilstein,Kettwig,Gemeindestraße,,,14,automatisch
00006,Am Richtenberg,Frohnhausen,Gemeindestraße,,,15,automatisch
00007,Bochumer Straße,Steele,Gemeindestraße,,,16,automatisch
00008,Schulstraße,Steele,Gemeindestraße,,,17,automatisch
00009,Schulstraße,Kray,Gemeindestraße,,,18,automatisch
00010,Goosestraße,Borbeck-Mitte,Gemeindestraße,,,19,automatisch
```

`tests/fixtures/strassen/konkordanz_1936.csv`:
```csv
stadtteil,ehemalig,heutig,schl_nr,datum_praezision,quelle,zusatz,eindeutig
Bredeney,Hermann-Göring-Straße,Bredeneyer Straße,00003,tag,Dickhoff 2015,,ja
Kray,Achtermbergstraße,Achternbergstraße,00004,tag,Dickhoff 2015,(Umb.),ja
Kettwig,Hochstraße,Am Bilstein,00005,tag,Dickhoff 2015,,nein
Frohnhausen,Frohnhauser Straße,Am Richtenberg,00006,tag,Dickhoff 2015,,nein
```

`tests/fixtures/strassen/namen.csv`:
```csv
schl_nr,stadium,gueltig_ab,datum_praezision,name,ist_urspruenglich
00003,1,1900,jahr,Bredeneyer Straße,richtig
00003,2,1933-07-13,tag,Hermann-Göring-Straße,falsch
00003,3,1945-06-01,tag,Bredeneyer Straße,falsch
00010,1,1900,jahr,Gusestraße,richtig
00010,2,1938-10-21,tag,Goosestraße,falsch
00001,1,1880,jahr,Carlstraße,richtig
00001,2,1910-01-01,tag,Karlstraße,falsch
```

`tests/fixtures/strassen_zuordnung.csv`:
```csv
strasse_roh_norm,vorort,strasse_heute,schl_nr,beleg,bearbeiter,datum
hstr.,Kray,Schulstraße,00009,Test,Test,2026-09-15
```

- [ ] **Step 2: Failing Tests**

`tests/test_konkordanz.py`:
```python
from pathlib import Path
import pytest
from pipeline.lib.konkordanz import VORORT_STADTTEILE, Strassenindex

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def idx():
    return Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv")


def test_heutig_eindeutig(idx):
    a = idx.aufloesen("bochumer straße", "Steele")
    assert (a.strasse_heute, a.schl_nr, a.herkunft, a.mehrdeutig) == ("Bochumer Straße", "00007", "heutig", "nein")


def test_heutig_mehrdeutig_ohne_vorort(idx):
    a = idx.aufloesen("schulstraße", "")
    assert a.herkunft == "heutig" and a.mehrdeutig == "ja" and a.strasse_heute == "" and "00008" in a.kandidaten and "00009" in a.kandidaten


def test_heutig_mehrdeutig_mit_vorort_aufgeloest(idx):
    a = idx.aufloesen("schulstraße", "Kray")
    assert (a.schl_nr, a.mehrdeutig, a.stadtteil) == ("00009", "nein", "Kray")


def test_konkordanz_eindeutig(idx):
    a = idx.aufloesen("hermann-göring-straße", "")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend) == ("Bredeneyer Straße", "konkordanz", "nein")


def test_konkordanz_nicht_eindeutig_bleibt_offen(idx):
    a = idx.aufloesen("hochstraße", "")
    assert a.herkunft == "konkordanz" and a.mehrdeutig == "ja" and a.strasse_heute == ""


def test_stadium_im_fenster(idx):
    # Gusestraße galt bis 1938-10-21 → Stadium gültig 1936 → stadium, nicht abweichend
    a = idx.aufloesen("gusestraße", "")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend) == ("Goosestraße", "stadium", "nein")


def test_stadium_ausserhalb_fenster(idx):
    # Carlstraße endete 1910 → weit vor 1930 → zeitlich_abweichend
    a = idx.aufloesen("carlstraße", "")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend) == ("Karlstraße", "stadium", "ja")


def test_kuratiert(idx):
    a = idx.aufloesen("hstr.", "Kray")
    assert (a.strasse_heute, a.schl_nr, a.herkunft) == ("Schulstraße", "00009", "kuratiert")


def test_offen(idx):
    a = idx.aufloesen("stadtwiese", "")
    assert a.herkunft == "offen" and a.strasse_heute == ""


def test_vorort_widerspruch_wird_nicht_still_aufgeloest(idx):
    # Bochumer Straße liegt in Steele; Vorort Kray widerspricht → mehrdeutig=ja mit Kandidat
    a = idx.aufloesen("bochumer straße", "Kray")
    assert a.mehrdeutig == "ja" and a.strasse_heute == "" and "00007" in a.kandidaten


def test_vorschlaege(idx):
    v = idx.vorschlaege("archternbergstraße")
    assert v[0][1] == "Achternbergstraße" and v[0][2] >= 0.85


def test_vorort_stadtteile_vollstaendig():
    assert set(VORORT_STADTTEILE) == {"Frillendorf", "Heidhausen", "Heisingen", "Karnap", "Katernberg", "Kray", "Kupferdreh", "Schonnebeck", "Steele", "Stoppenberg", "Ueberruhr", "Werden"}
    assert "Fischlaken" in VORORT_STADTTEILE["Heidhausen"]
```

- [ ] **Step 3: Fehlschlag prüfen**

Run: `pytest tests/test_konkordanz.py -v` → FAIL `ModuleNotFoundError`.

- [ ] **Step 4: Implementieren**

`pipeline/lib/konkordanz.py`:
```python
"""Straßenindex: löst normierte Straßennamen von 1936 auf heutige Straßen auf (Auflösungsleiter a–f)."""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path

from pipeline.lib.io import lies_csv
from pipeline.lib.normalisierung import norm_stadtteil, norm_strasse

FENSTER = ("1930-01-01", "1937-12-31")

# Vorort (Buch 1936, Stadtkreise vor 1929) → heutige Stadtteile (Dickhoff-Schreibweise).
# Grundlage: Eingemeindungen 1929; Zuordnung ist ein Prüfkriterium, kein Beleg. Bei Widerspruch
# wird nicht still aufgelöst, sondern mehrdeutig=ja gesetzt.
VORORT_STADTTEILE: dict[str, frozenset[str]] = {
    "Frillendorf": frozenset({"Frillendorf"}),
    "Heidhausen": frozenset({"Heidhausen", "Fischlaken"}),
    "Heisingen": frozenset({"Heisingen"}),
    "Karnap": frozenset({"Karnap"}),
    "Katernberg": frozenset({"Katernberg"}),
    "Kray": frozenset({"Kray", "Leithe"}),
    "Kupferdreh": frozenset({"Kupferdreh", "Byfang"}),
    "Schonnebeck": frozenset({"Schonnebeck"}),
    "Steele": frozenset({"Steele", "Freisenbruch", "Horst"}),
    "Stoppenberg": frozenset({"Stoppenberg"}),
    "Ueberruhr": frozenset({"Überruhr-Hinsel", "Überruhr-Holthausen"}),
    "Werden": frozenset({"Werden"}),
}


@dataclass(frozen=True)
class Aufloesung:
    strasse_heute: str
    schl_nr: str
    stadtteil: str
    herkunft: str
    zeitlich_abweichend: str = "nein"
    mehrdeutig: str = "nein"
    kandidaten: str = ""


OFFEN = Aufloesung("", "", "", "offen")


def _ohne_klammer(name: str) -> str:
    return re.sub(r"\s*\(.*?\)\s*", " ", name).strip()


class Strassenindex:
    def __init__(self, strassen_dir: Path, zuordnung_pfad: Path):
        self.strassen = {z["schl_nr"]: z for z in lies_csv(strassen_dir / "strassen.csv")}
        self.stadtteile = {s: [norm_stadtteil(t) for t in z["stadtteile"].split(";") if t.strip()]
                           for s, z in self.strassen.items()}
        self.heutig: dict[str, list[str]] = {}
        for s, z in self.strassen.items():
            self.heutig.setdefault(norm_strasse(z["lemma"]), []).append(s)
        self.konk: dict[str, list[dict]] = {}
        for z in lies_csv(strassen_dir / "konkordanz_1936.csv"):
            self.konk.setdefault(norm_strasse(z["ehemalig"]), []).append(z)
        namen = lies_csv(strassen_dir / "namen.csv")
        namen.sort(key=lambda z: (z["schl_nr"], int(z["stadium"])))
        self.stadien: dict[str, list[dict]] = {}
        for i, z in enumerate(namen):
            folge = namen[i + 1] if i + 1 < len(namen) and namen[i + 1]["schl_nr"] == z["schl_nr"] else None
            eintrag = dict(z, gueltig_bis=folge["gueltig_ab"] if folge else "9999")
            self.stadien.setdefault(norm_strasse(_ohne_klammer(z["name"])), []).append(eintrag)
        self.zuordnung: dict[tuple[str, str], dict] = {}
        if zuordnung_pfad.exists():
            for z in lies_csv(zuordnung_pfad):
                self.zuordnung[(norm_strasse(z["strasse_roh_norm"]), z["vorort"])] = z
        self._pool = sorted(set(self.stadien) | set(self.heutig))

    # --- Hilfen ---------------------------------------------------------------
    def _passt(self, schl_nr: str, vorort: str) -> bool:
        if not vorort:
            return True
        erlaubt = VORORT_STADTTEILE.get(vorort, frozenset())
        return any(t in erlaubt for t in self.stadtteile.get(schl_nr, []))

    def _fertig(self, schl_nr: str, herkunft: str, zeitlich: str = "nein") -> Aufloesung:
        s = self.strassen[schl_nr]
        return Aufloesung(s["lemma"], schl_nr, "; ".join(self.stadtteile[schl_nr]), herkunft, zeitlich, "nein")

    def _entscheide(self, kandidaten: list[str], vorort: str, herkunft: str, zeitlich: str = "nein") -> Aufloesung:
        kandidaten = list(dict.fromkeys(kandidaten))
        passend = [s for s in kandidaten if self._passt(s, vorort)]
        if len(passend) == 1:
            return self._fertig(passend[0], herkunft, zeitlich)
        return Aufloesung("", "", "", herkunft, zeitlich, "ja", ";".join(kandidaten))

    # --- Leiter ---------------------------------------------------------------
    def aufloesen(self, strasse_norm: str, vorort: str) -> Aufloesung:
        # e) Kuratierung schlägt alles, weil vom Menschen belegt
        z = self.zuordnung.get((strasse_norm, vorort)) or self.zuordnung.get((strasse_norm, ""))
        if z:
            return Aufloesung(z["strasse_heute"], z["schl_nr"], "; ".join(self.stadtteile.get(z["schl_nr"], [])), "kuratiert")
        # a) heutiger Name
        if strasse_norm in self.heutig:
            return self._entscheide(self.heutig[strasse_norm], vorort, "heutig")
        # b/c) Konkordanz 1936
        if strasse_norm in self.konk:
            zeilen = self.konk[strasse_norm]
            eindeutig = [z for z in zeilen if z["eindeutig"] == "ja"]
            if eindeutig:
                return self._entscheide([z["schl_nr"] for z in eindeutig], vorort, "konkordanz")
            if vorort:
                return self._entscheide([z["schl_nr"] for z in zeilen], vorort, "konkordanz")
            return Aufloesung("", "", "", "konkordanz", "nein", "ja", ";".join(z["schl_nr"] for z in zeilen))
        # d) anderes Namensstadium
        if strasse_norm in self.stadien:
            st = self.stadien[strasse_norm]
            im_fenster = [z for z in st if z["gueltig_ab"][:10] <= FENSTER[1] and z["gueltig_bis"][:10] >= FENSTER[0]]
            if im_fenster:
                return self._entscheide([z["schl_nr"] for z in im_fenster], vorort, "stadium", "nein")
            return self._entscheide([z["schl_nr"] for z in st], vorort, "stadium", "ja")
        return OFFEN

    def vorschlaege(self, strasse_norm: str, n: int = 3) -> list[tuple[str, str, float]]:
        out = []
        for kand in difflib.get_close_matches(strasse_norm, self._pool, n=n, cutoff=0.8):
            schl = (self.heutig.get(kand) or [z["schl_nr"] for z in self.stadien.get(kand, [])])[0]
            lemma = self.strassen.get(schl, {}).get("lemma", "")
            out.append((kand, lemma, round(difflib.SequenceMatcher(None, strasse_norm, kand).ratio(), 3)))
        return out
```

`kuratierung/strassen_zuordnung.csv` (nur Kopf, wird vom Menschen gefüllt):
```csv
strasse_roh_norm,vorort,strasse_heute,schl_nr,beleg,bearbeiter,datum
```

- [ ] **Step 5: Tests grün prüfen**

Run: `pytest tests/test_konkordanz.py -v`
Expected: alle PASS. Achtung bei `test_stadium_im_fenster`: `gueltig_ab` „1900“ (nur Jahr) muss als `"1900" <= "1937-12-31"` verglichen werden; Stringvergleich funktioniert, weil ISO-Präfixe sortierbar sind.

- [ ] **Step 6: Commit**

```bash
git add pipeline/lib/konkordanz.py kuratierung/strassen_zuordnung.csv tests/test_konkordanz.py tests/fixtures/strassen tests/fixtures/strassen_zuordnung.csv
git commit -m "feat: Straßenindex mit Auflösungsleiter und Vorschlägen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Stufe 03 — Straßen auflösen und Vorschlagsliste

**Files:**
- Create: `pipeline/03_strasse_aufloesen.py`
- Modify: `pipeline/lib/stufen.py` (Funktion `loese_strassen` ergänzen)
- Test: `tests/test_stufe03.py`

**Interfaces:**
- Consumes: `Strassenindex`, `Aufloesung`.
- Produces: `stufen.loese_strassen(zeilen, idx) -> tuple[list[dict], list[dict], list[dict]]` = (zeilen mit Feldern `strasse_heute, schl_nr, stadtteil, herkunft, zeitlich_abweichend, mehrdeutig, kandidaten`; Paartabelle `strassen` mit `strasse_norm, vorort, zeilen, beispiel, strasse_heute, schl_nr, stadtteil, herkunft, zeitlich_abweichend, mehrdeutig, kandidaten`; Vorschläge mit `strasse_norm, vorort, zeilen, beispiel, kandidat_1, lemma_1, aehnlichkeit_1, kandidat_2, lemma_2, aehnlichkeit_2, kandidat_3, lemma_3, aehnlichkeit_3`). Konstante `AUFLOESUNGSFELDER`.

- [ ] **Step 1: Failing Test**

`tests/test_stufe03.py`:
```python
from pathlib import Path
from pipeline.lib.konkordanz import Strassenindex
from pipeline.lib.stufen import loese_strassen

FIX = Path(__file__).parent / "fixtures"


def test_loese_strassen():
    idx = Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv")
    zeilen = [
        {"id": "1", "strasse_norm": "bochumer straße", "Vorort": "Steele", "Adresse": "Bochumer Str. 5"},
        {"id": "2", "strasse_norm": "bochumer straße", "Vorort": "Steele", "Adresse": "Bochumer Str. 7"},
        {"id": "3", "strasse_norm": "stadtwiese", "Vorort": "", "Adresse": "Stadtwiese 3"},
        {"id": "4", "strasse_norm": "archternbergstraße", "Vorort": "Kray", "Adresse": "Archternbergstr. 1"},
    ]
    out, paare, vorschlaege = loese_strassen(zeilen, idx)
    assert out[0]["strasse_heute"] == "Bochumer Straße" and out[1]["herkunft"] == "heutig"
    assert out[2]["herkunft"] == "offen"
    p = {(x["strasse_norm"], x["vorort"]): x for x in paare}
    assert p[("bochumer straße", "Steele")]["zeilen"] == "2"
    assert {v["strasse_norm"] for v in vorschlaege} == {"stadtwiese", "archternbergstraße"}
    v = [x for x in vorschlaege if x["strasse_norm"] == "archternbergstraße"][0]
    assert v["lemma_1"] == "Achternbergstraße" and v["zeilen"] == "1"
    assert vorschlaege[0]["zeilen"] >= vorschlaege[-1]["zeilen"]  # nach Zeilenzahl absteigend
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `pytest tests/test_stufe03.py -v` → FAIL `ImportError: cannot import name 'loese_strassen'`.

- [ ] **Step 3: Implementieren**

An `pipeline/lib/stufen.py` anhängen:
```python
from dataclasses import asdict as _asdict  # noqa: E402
from pipeline.lib.konkordanz import Strassenindex  # noqa: E402

AUFLOESUNGSFELDER = ["strasse_heute", "schl_nr", "stadtteil", "herkunft", "zeitlich_abweichend", "mehrdeutig", "kandidaten"]
PAARFELDER = ["strasse_norm", "vorort", "zeilen", "beispiel"] + AUFLOESUNGSFELDER
VORSCHLAGSFELDER = ["strasse_norm", "vorort", "zeilen", "beispiel"] + [
    f"{k}_{i}" for i in (1, 2, 3) for k in ("kandidat", "lemma", "aehnlichkeit")]


def loese_strassen(zeilen: list[dict], idx: Strassenindex) -> tuple[list[dict], list[dict], list[dict]]:
    paare: dict[tuple[str, str], dict] = {}
    for z in zeilen:
        k = (z["strasse_norm"], z["Vorort"])
        if k not in paare:
            a = idx.aufloesen(*k) if k[0] else None
            paare[k] = {"strasse_norm": k[0], "vorort": k[1], "zeilen": 0, "beispiel": z["Adresse"],
                        **({f: "" for f in AUFLOESUNGSFELDER} | ({"herkunft": "offen"} if a is None else _asdict(a)))}
        paare[k]["zeilen"] += 1
    out = []
    for z in zeilen:
        p = paare[(z["strasse_norm"], z["Vorort"])]
        d = dict(z)
        d.update({f: p[f] for f in AUFLOESUNGSFELDER})
        out.append(d)
    vorschlaege = []
    for p in paare.values():
        if p["herkunft"] == "offen" or p["mehrdeutig"] == "ja":
            v = {f: p[f] for f in ("strasse_norm", "vorort", "zeilen", "beispiel")}
            for i, (kand, lemma, sim) in enumerate(idx.vorschlaege(p["strasse_norm"]) if p["strasse_norm"] else [], start=1):
                v[f"kandidat_{i}"], v[f"lemma_{i}"], v[f"aehnlichkeit_{i}"] = kand, lemma, str(sim)
            vorschlaege.append({f: v.get(f, "") for f in VORSCHLAGSFELDER})
    vorschlaege.sort(key=lambda v: -int(v["zeilen"]))
    paarliste = sorted(paare.values(), key=lambda p: -p["zeilen"])
    for p in paarliste:
        p["zeilen"] = str(p["zeilen"])
    for v in vorschlaege:
        v["zeilen"] = str(v["zeilen"])
    return out, paarliste, vorschlaege
```

Achtung: Der Test vergleicht `zeilen` als String (`"2"`), und die Sortierung geschieht vor der Umwandlung. Die Vorschlagsliste enthält `zeilen` erst als int und wird nach der Sortierung in Strings umgewandelt; darum die beiden Schleifen am Ende.

`pipeline/03_strasse_aufloesen.py`:
```python
"""Stufe 03: build/02_geparst.csv → build/03_aufgeloest.csv, build/03_strassen.csv, build/strassen_vorschlaege.csv"""
from collections import Counter
from pipeline.lib import einlesen
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv, strassen_dir
from pipeline.lib.konkordanz import Strassenindex
from pipeline.lib.stufen import AUFLOESUNGSFELDER, PARSEFELDER, PAARFELDER, VORSCHLAGSFELDER, loese_strassen

W = projektwurzel()
idx = Strassenindex(strassen_dir(), W / "kuratierung" / "strassen_zuordnung.csv")
zeilen, paare, vorschlaege = loese_strassen(lies_csv(W / "build" / "02_geparst.csv"), idx)
schreib_csv(W / "build" / "03_aufgeloest.csv", zeilen, einlesen.AUSGABEFELDER + PARSEFELDER + AUFLOESUNGSFELDER)
schreib_csv(W / "build" / "03_strassen.csv", paare, PAARFELDER)
schreib_csv(W / "build" / "strassen_vorschlaege.csv", vorschlaege, VORSCHLAGSFELDER)
c = Counter((z["herkunft"], z["mehrdeutig"]) for z in zeilen)
for k, v in c.most_common():
    print(f"{k[0]:12s} mehrdeutig={k[1]:4s} {v:7d} {v / len(zeilen) * 100:5.1f}%")
```

- [ ] **Step 4: Tests grün, echten Lauf prüfen**

Run: `pytest tests/test_stufe03.py -v && python3 pipeline/03_strasse_aufloesen.py`
Expected: PASS; Verteilung in der Größenordnung der Messung (heutig ≈ 83 %, konkordanz ≈ 8–9 %, stadium ≈ 1–2 %, offen ≈ 6 %). `mehrdeutig=ja` ist neu und wird gezählt; wenn > 5 % der Zeilen, die Vorort-Stadtteil-Tabelle prüfen, bevor weitergegangen wird.

- [ ] **Step 5: Journal-Eintrag im Vault**

An `/home/christos/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Journal.md` unter einer Überschrift mit dem Datum des Laufs anhängen: drei Sätze mit den Zahlen aus Step 4 (Anteile heutig/konkordanz/stadium/offen/mehrdeutig, Anzahl Zeilen in `strassen_vorschlaege.csv`).

- [ ] **Step 6: Commit**

```bash
git add pipeline/03_strasse_aufloesen.py pipeline/lib/stufen.py tests/test_stufe03.py
git commit -m "feat: Stufe 03 Straßenauflösung mit Paartabelle und Vorschlagsliste

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Nominatim-Client mit Cache und Verortungslogik

**Files:**
- Create: `pipeline/lib/nominatim.py`, `kuratierung/landmarken.csv`
- Test: `tests/test_nominatim.py`

**Interfaces:**
- Produces: `SCHEMA_VERSION = "1"`; `@dataclass Verortung(lat: str, lon: str, stufe: str, grund: str, osm_type: str, osm_id: str, display_name: str, zusatz_ignoriert: str)`; `class Client(basis_url: str, cache_pfad: Path)` mit `suche(self, params: dict) -> list[dict]` (gecacht, Schlüssel = JSON von `{"v": SCHEMA_VERSION, **params}` sortiert) und `schliessen()`; `geokodiere(client, strasse_heute: str, hausnr: str, hausnr_zusatz: str, stadtteil: str, parse_status: str, strasse_roh: str, landmarken: list[dict]) -> Verortung`; `lade_landmarken(pfad) -> list[dict]`.
- `stadtteil` kommt als „A; B“ (Dickhoff-Liste) und wird gegen `address.suburb` (normalisiert mit `norm_stadtteil`) geprüft; leerer `stadtteil` = keine Prüfung.
- Format `landmarken.csv`: `muster,lat,lon,name,quelle` (Substring-Vergleich, kleingeschrieben, gegen `strasse_roh`).

- [ ] **Step 1: Failing Tests**

`tests/test_nominatim.py`:
```python
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
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `pytest tests/test_nominatim.py -v` → FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implementieren**

`pipeline/lib/nominatim.py`:
```python
"""Nominatim-Client mit JSONL-Cache und die Verortungsregeln (haus / strasse / landmarke / offen)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import requests

from pipeline.lib.io import lies_csv
from pipeline.lib.normalisierung import norm_stadtteil, norm_strasse

SCHEMA_VERSION = "1"
BASIS = {"format": "json", "addressdetails": "1", "countrycodes": "de", "limit": "5"}


@dataclass(frozen=True)
class Verortung:
    lat: str = ""
    lon: str = ""
    stufe: str = "offen"
    grund: str = ""
    osm_type: str = ""
    osm_id: str = ""
    display_name: str = ""
    zusatz_ignoriert: str = "nein"


class Client:
    def __init__(self, basis_url: str, cache_pfad: Path):
        self.url = basis_url.rstrip("/") + "/search"
        self.cache_pfad = Path(cache_pfad)
        self.cache: dict[str, list] = {}
        if self.cache_pfad.exists():
            with open(self.cache_pfad, encoding="utf-8") as f:
                for zeile in f:
                    d = json.loads(zeile)
                    self.cache[d["k"]] = d["v"]
        self.cache_pfad.parent.mkdir(parents=True, exist_ok=True)
        self._out = open(self.cache_pfad, "a", encoding="utf-8")

    def suche(self, params: dict) -> list[dict]:
        k = json.dumps({"v": SCHEMA_VERSION, **params}, sort_keys=True, ensure_ascii=False)
        if k in self.cache:
            return self.cache[k]
        r = requests.get(self.url, params={**BASIS, **params}, timeout=15)
        r.raise_for_status()
        v = r.json()
        self.cache[k] = v
        self._out.write(json.dumps({"k": k, "v": v}, ensure_ascii=False) + "\n")
        return v

    def schliessen(self) -> None:
        self._out.close()


def lade_landmarken(pfad: Path) -> list[dict]:
    return lies_csv(pfad) if Path(pfad).exists() else []


def _road_passt(t: dict, strasse_heute: str) -> bool:
    return norm_strasse(t.get("address", {}).get("road", "")) == norm_strasse(strasse_heute)


def _suburb(t: dict) -> str:
    return norm_stadtteil(t.get("address", {}).get("suburb", ""))


def _stadtteil_status(t: dict, stadtteil: str) -> str:
    """'ok' wenn Prüfung nicht möglich oder bestanden, sonst 'widerspruch'."""
    if not stadtteil:
        return "ok"
    erlaubt = {norm_stadtteil(s) for s in stadtteil.split(";") if s.strip()}
    sub = _suburb(t)
    if not sub:
        return "ok"
    return "ok" if sub in erlaubt else "widerspruch"


def _treffer(t: dict, stufe: str, grund: str = "", zusatz_ignoriert: str = "nein") -> Verortung:
    return Verortung(t["lat"], t["lon"], stufe, grund, t.get("osm_type", ""), str(t.get("osm_id", "")),
                     t.get("display_name", ""), zusatz_ignoriert)


def _hausebene(client, strasse_heute, hausnr, zusatz, stadtteil) -> Verortung | None:
    for z, ignoriert in ((zusatz, "nein"), ("", "ja")) if zusatz else (("", "nein"),):
        for t in client.suche({"street": f"{hausnr}{z} {strasse_heute}", "city": "Essen"}):
            adr = t.get("address", {})
            if adr.get("house_number", "").lower().replace(" ", "") not in {hausnr + z, hausnr}:
                continue
            if not _road_passt(t, strasse_heute):
                continue
            if _stadtteil_status(t, stadtteil) != "ok":
                continue
            return _treffer(t, "haus", "", ignoriert)
    return None


def _strassenebene(client, strasse_heute, stadtteil, grund="") -> Verortung:
    treffer = [t for t in client.suche({"street": strasse_heute, "city": "Essen"})
               if t.get("class") == "highway" and _road_passt(t, strasse_heute)]
    if not treffer:
        return Verortung(stufe="offen", grund="kein_treffer")
    passend = [t for t in treffer if _stadtteil_status(t, stadtteil) == "ok"]
    if stadtteil and not passend:
        return Verortung(stufe="offen", grund="stadtteil_widerspruch")
    suburbs = {_suburb(t) for t in passend}
    if len(suburbs) > 1 and not stadtteil:
        return Verortung(stufe="offen", grund="mehrdeutig_strasse")
    return _treffer(passend[0], "strasse", grund)


def geokodiere(client, strasse_heute: str, hausnr: str, hausnr_zusatz: str, stadtteil: str,
               parse_status: str, strasse_roh: str, landmarken: list[dict]) -> Verortung:
    if parse_status in ("ohne_nummer", "leer", "unklar") and not hausnr:
        roh = strasse_roh.lower()
        for lm in landmarken:
            if lm["muster"].lower() in roh:
                return Verortung(lm["lat"], lm["lon"], "landmarke", "", "", "", lm["name"])
        if not strasse_heute:
            return Verortung(stufe="offen", grund="ohne_nummer" if parse_status == "ohne_nummer" else "strasse_offen")
        return _strassenebene(client, strasse_heute, stadtteil, grund="ohne_nummer")
    if not strasse_heute:
        return Verortung(stufe="offen", grund="strasse_offen")
    haus = _hausebene(client, strasse_heute, hausnr, hausnr_zusatz, stadtteil)
    if haus:
        return haus
    return _strassenebene(client, strasse_heute, stadtteil)
```

`kuratierung/landmarken.csv` (nur Kopf; wird aus dem Bericht befüllt, jede Zeile mit Quelle):
```csv
muster,lat,lon,name,quelle
```

- [ ] **Step 4: Tests grün prüfen**

Run: `pytest tests/test_nominatim.py -v`
Expected: alle PASS. Bei `test_haus_verlangt_gleiche_nummer`: Der Fake liefert für „5 Bochumer Straße“ ein Haus Nr. 7; die Prüfung `house_number ∉ {hausnr+z, hausnr}` muss es verwerfen und auf Straßenebene fallen.

- [ ] **Step 5: Live-Rauchtest gegen die lokale Instanz**

```bash
python3 - <<'EOF'
from pathlib import Path
from pipeline.lib import nominatim as nm
c = nm.Client("http://localhost:8080", Path("build/cache/rauchtest.jsonl"))
print(nm.geokodiere(c, "Bochumer Straße", "114", "", "Steele", "ok", "Bochumer Str.", []))
print(nm.geokodiere(c, "Karlstraße", "31", "", "Altenessen-Nord; Altenessen-Süd", "ok", "Karlstr.", []))
print(nm.geokodiere(c, "Hauptstraße", "5", "", "", "ok", "Hauptstr.", []))
c.schliessen()
EOF
rm build/cache/rauchtest.jsonl
```
Expected: erste zwei `stufe='haus'`; dritte `offen` mit `mehrdeutig_strasse` oder `haus` in Kettwig, falls Nominatim nur Kettwig kennt (dann ist das korrekt: ohne Stadtteil darf ein eindeutiger Treffer akzeptiert werden).

- [ ] **Step 6: Commit**

```bash
git add pipeline/lib/nominatim.py kuratierung/landmarken.csv tests/test_nominatim.py
git commit -m "feat: Nominatim-Client mit Cache und Verortungsregeln

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Stufe 04 — Geokodieren

**Files:**
- Create: `pipeline/04_geokodieren.py`
- Modify: `pipeline/lib/stufen.py` (Funktion `geokodiere_zeilen`)
- Test: `tests/test_stufe04.py`

**Interfaces:**
- Consumes: `geokodiere`, `Client`, `lade_landmarken`.
- Produces: `stufen.geokodiere_zeilen(zeilen, client, landmarken, threads=8) -> tuple[list[dict], list[dict]]` = (Zeilen mit `lat, lon, stufe, grund, osm_type, osm_id, display_name, zusatz_ignoriert`; Adresstabelle mit `strasse_heute, hausnr, hausnr_zusatz, stadtteil, parse_status, strasse_roh, zeilen` + Verortungsfelder). Konstante `VERORTUNGSFELDER`. Adresse-Schlüssel = `(strasse_heute, hausnr, hausnr_zusatz, stadtteil, parse_status, strasse_roh)`.

- [ ] **Step 1: Failing Test**

`tests/test_stufe04.py`:
```python
from pipeline.lib.stufen import geokodiere_zeilen


class FakeClient:
    def __init__(self):
        self.n = 0

    def suche(self, params):
        self.n += 1
        if params["street"].startswith("5 "):
            return [{"lat": "1", "lon": "2", "osm_type": "way", "osm_id": "9", "class": "building", "type": "yes",
                     "display_name": "x", "address": {"house_number": "5", "road": "Bochumer Straße", "suburb": "Steele"}}]
        return []


def test_geokodiere_zeilen_dedupliziert_adressen():
    z = [dict(id=str(i), strasse_heute="Bochumer Straße", hausnr="5", hausnr_zusatz="", stadtteil="Steele",
              parse_status="ok", strasse_roh="Bochumer Str.") for i in range(3)]
    z.append(dict(id="x", strasse_heute="", hausnr="", hausnr_zusatz="", stadtteil="", parse_status="leer", strasse_roh=""))
    c = FakeClient()
    out, adressen = geokodiere_zeilen(z, c, [], threads=2)
    assert [o["stufe"] for o in out] == ["haus", "haus", "haus", "offen"]
    assert c.n == 1
    assert len(adressen) == 2 and adressen[0]["zeilen"] == "3"
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `pytest tests/test_stufe04.py -v` → FAIL `ImportError`.

- [ ] **Step 3: Implementieren**

An `pipeline/lib/stufen.py` anhängen:
```python
from concurrent.futures import ThreadPoolExecutor  # noqa: E402
from pipeline.lib.nominatim import Verortung, geokodiere  # noqa: E402

VERORTUNGSFELDER = ["lat", "lon", "stufe", "grund", "osm_type", "osm_id", "display_name", "zusatz_ignoriert"]
ADRESSSCHLUESSEL = ["strasse_heute", "hausnr", "hausnr_zusatz", "stadtteil", "parse_status", "strasse_roh"]
ADRESSFELDER = ADRESSSCHLUESSEL + ["zeilen"] + VERORTUNGSFELDER


def geokodiere_zeilen(zeilen: list[dict], client, landmarken: list[dict], threads: int = 8) -> tuple[list[dict], list[dict]]:
    gruppen: dict[tuple, int] = {}
    for z in zeilen:
        k = tuple(z[f] for f in ADRESSSCHLUESSEL)
        gruppen[k] = gruppen.get(k, 0) + 1
    schluessel = sorted(gruppen, key=lambda k: -gruppen[k])

    def arbeit(k: tuple) -> tuple[tuple, Verortung]:
        d = dict(zip(ADRESSSCHLUESSEL, k))
        return k, geokodiere(client, d["strasse_heute"], d["hausnr"], d["hausnr_zusatz"], d["stadtteil"],
                             d["parse_status"], d["strasse_roh"], landmarken)

    ergebnis: dict[tuple, Verortung] = {}
    with ThreadPoolExecutor(max_workers=threads) as ex:
        for k, v in ex.map(arbeit, schluessel):
            ergebnis[k] = v
    out = []
    for z in zeilen:
        v = ergebnis[tuple(z[f] for f in ADRESSSCHLUESSEL)]
        d = dict(z)
        d.update(_asdict(v))
        out.append(d)
    adressen = []
    for k in schluessel:
        a = dict(zip(ADRESSSCHLUESSEL, k))
        a["zeilen"] = str(gruppen[k])
        a.update(_asdict(ergebnis[k]))
        adressen.append(a)
    return out, adressen
```

Hinweis: `Client.suche` schreibt aus mehreren Threads in dieselbe Datei. In `nominatim.Client` ein `threading.Lock` um Cache-Lesen/Schreiben legen:
```python
import threading
# in __init__: self._lock = threading.Lock()
# in suche: Cache-Lookup und Schreiben jeweils innerhalb `with self._lock:`; die HTTP-Anfrage außerhalb.
```
Dazu in `tests/test_nominatim.py` keinen neuen Test; der Roundtrip-Test bleibt gültig.

`pipeline/04_geokodieren.py`:
```python
"""Stufe 04: build/03_aufgeloest.csv → build/04_geokodiert.csv (je Adresse), build/eintraege.csv (je Zeile)"""
import os
from collections import Counter
from pipeline.lib import einlesen
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv
from pipeline.lib.nominatim import Client, lade_landmarken
from pipeline.lib.stufen import ADRESSFELDER, AUFLOESUNGSFELDER, PARSEFELDER, VERORTUNGSFELDER, geokodiere_zeilen

W = projektwurzel()
client = Client(os.environ.get("NOMINATIM_URL", "http://localhost:8080"), W / "build" / "cache" / "nominatim.jsonl")
landmarken = lade_landmarken(W / "kuratierung" / "landmarken.csv")
zeilen, adressen = geokodiere_zeilen(lies_csv(W / "build" / "03_aufgeloest.csv"), client, landmarken, threads=8)
client.schliessen()
schreib_csv(W / "build" / "04_geokodiert.csv", adressen, ADRESSFELDER)
schreib_csv(W / "build" / "eintraege.csv", zeilen, einlesen.AUSGABEFELDER + PARSEFELDER + AUFLOESUNGSFELDER + VERORTUNGSFELDER)
c = Counter((z["stufe"], z["grund"]) for z in zeilen)
for k, v in c.most_common():
    print(f"{k[0]:10s} {k[1]:22s} {v:7d} {v / len(zeilen) * 100:5.1f}%")
```

- [ ] **Step 4: Tests grün, Probelauf auf Teilmenge**

Run: `pytest -q` (alle Tests grün), dann Probelauf auf 2.000 Zeilen:
```bash
head -2001 build/03_aufgeloest.csv > build/03_probe.csv
python3 - <<'EOF'
import os
os.environ.setdefault("NOMINATIM_URL", "http://localhost:8080")
from pathlib import Path
from pipeline.lib.io import lies_csv, projektwurzel
from pipeline.lib.nominatim import Client
from pipeline.lib.stufen import geokodiere_zeilen
from collections import Counter
W = projektwurzel()
c = Client("http://localhost:8080", W / "build/cache/nominatim.jsonl")
z, a = geokodiere_zeilen(lies_csv(W / "build/03_probe.csv"), c, [], threads=8)
c.schliessen()
print(Counter(x["stufe"] for x in z))
EOF
```
Expected: `haus` deutlich über 50 %, keine Exceptions. Danach Volllauf `python3 pipeline/04_geokodieren.py` (Dauer bei ~90.000 eindeutigen Adressen und lokaler Instanz: Größenordnung 30–60 Minuten; läuft mit `run_in_background`).

- [ ] **Step 5: Commit**

```bash
git add pipeline/04_geokodieren.py pipeline/lib/stufen.py pipeline/lib/nominatim.py tests/test_stufe04.py
git commit -m "feat: Stufe 04 Geokodierung je eindeutiger Adresse, parallel mit Cache

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Stufe 05 — Bericht und Kontrollpunkte

**Files:**
- Create: `pipeline/05_bericht.py`, `pipeline/lib/bericht.py`
- Test: `tests/test_bericht.py`

**Interfaces:**
- Consumes: `build/eintraege.csv`, `build/04_geokodiert.csv`, `build/03_strassen.csv`, `build/dubletten.csv`, `build/01_ausgeschlossen.csv`, `build/strassen_vorschlaege.csv`.
- Produces: `bericht.erzeuge(eintraege, adressen, strassen, dubletten, ausgeschlossen, vorschlaege) -> tuple[str, dict]` (Markdown, GeoJSON-Dict mit einer Zufallsstichprobe von 2.000 verorteten Adressen und Eigenschaften `stufe, herkunft, adresse, display_name`); Skript schreibt `build/bericht.md` und `build/kontrollpunkte.geojson`.

- [ ] **Step 1: Failing Test**

`tests/test_bericht.py`:
```python
from pipeline.lib.bericht import erzeuge


def test_bericht_enthaelt_kernzahlen():
    e = [dict(teil="I", stufe="haus", grund="", herkunft="heutig", parse_status="ok", mehrdeutig="nein"),
         dict(teil="I", stufe="offen", grund="kein_treffer", herkunft="heutig", parse_status="ok", mehrdeutig="nein"),
         dict(teil="II", stufe="strasse", grund="", herkunft="konkordanz", parse_status="ok", mehrdeutig="nein")]
    a = [dict(strasse_heute="A", hausnr="1", hausnr_zusatz="", stadtteil="", stufe="haus", lat="51.4", lon="7.0",
              display_name="x", zeilen="2", herkunft="", strasse_roh="A", grund="", parse_status="ok"),
         dict(strasse_heute="B", hausnr="2", hausnr_zusatz="", stadtteil="", stufe="offen", lat="", lon="",
              display_name="", zeilen="1", herkunft="", strasse_roh="B", grund="kein_treffer", parse_status="ok")]
    md, geo = erzeuge(e, a, strassen=[], dubletten=[{"id": "1", "dublette_von": "2"}], ausgeschlossen=[], vorschlaege=[])
    assert "| haus |" in md and "33,3" in md and "Dubletten: 1" in md
    assert geo["type"] == "FeatureCollection" and len(geo["features"]) == 1
    assert geo["features"][0]["geometry"]["coordinates"] == [7.0, 51.4]
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `pytest tests/test_bericht.py -v` → FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implementieren**

`pipeline/lib/bericht.py`:
```python
"""Stufe 05: Kennzahlen als Markdown und eine Kontrollstichprobe als GeoJSON."""
from __future__ import annotations

import random
from collections import Counter


def _pz(n: int, g: int) -> str:
    return f"{(n / g * 100 if g else 0):.1f}".replace(".", ",")


def _tabelle(titel: str, zaehler: Counter, gesamt: int) -> list[str]:
    z = [f"### {titel}", "", "| Wert | Zeilen | Anteil |", "|---|---:|---:|"]
    for k, v in zaehler.most_common():
        z.append(f"| {k} | {v} | {_pz(v, gesamt)} % |")
    return z + [""]


def erzeuge(eintraege, adressen, strassen, dubletten, ausgeschlossen, vorschlaege) -> tuple[str, dict]:
    g = len(eintraege)
    md = ["# Bericht Datenpipeline", "", f"Einträge (Teile I–III, ohne Dubletten): {g}",
          f"Ausgeschlossen: {len(ausgeschlossen)} — " + ", ".join(f"{k}: {v}" for k, v in Counter(x['grund'] for x in ausgeschlossen).items()),
          f"Dubletten: {len(dubletten)}", f"Eindeutige Adressen: {len(adressen)}",
          f"Offene/mehrdeutige Straßen in Vorschlagsliste: {len(vorschlaege)}", ""]
    md += _tabelle("Präzisionsstufe", Counter(e["stufe"] for e in eintraege), g)
    md += _tabelle("Gründe (nur offen)", Counter(e["grund"] for e in eintraege if e["stufe"] == "offen"), g)
    md += _tabelle("Herkunft der Straßenauflösung", Counter(e["herkunft"] for e in eintraege), g)
    md += _tabelle("Parse-Status", Counter(e["parse_status"] for e in eintraege), g)
    for teil in ("I", "II", "III"):
        sub = [e for e in eintraege if e["teil"] == teil]
        md += _tabelle(f"Präzisionsstufe Teil {teil} ({len(sub)} Zeilen)", Counter(e["stufe"] for e in sub), len(sub))
    offen = sorted((a for a in adressen if a["stufe"] == "offen"), key=lambda a: -int(a["zeilen"]))[:50]
    md += ["### Top 50 offene Adressen", "", "| Zeilen | Adresse | Stadtteil | Grund |", "|---:|---|---|---|"]
    md += [f"| {a['zeilen']} | {a['strasse_roh']} {a['hausnr']}{a['hausnr_zusatz']} | {a['stadtteil']} | {a['grund']} |" for a in offen]
    md.append("")
    verortet = [a for a in adressen if a["lat"]]
    random.seed(1936)
    probe = random.sample(verortet, min(2000, len(verortet)))
    geo = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(a["lon"]), float(a["lat"])]},
         "properties": {"stufe": a["stufe"], "herkunft": a.get("herkunft", ""),
                        "adresse": f"{a['strasse_roh']} {a['hausnr']}{a['hausnr_zusatz']}".strip(),
                        "stadtteil": a["stadtteil"], "display_name": a["display_name"], "zeilen": a["zeilen"]}}
        for a in probe]}
    return "\n".join(md), geo
```

`pipeline/05_bericht.py`:
```python
"""Stufe 05: Kennzahlen → build/bericht.md, Kontrollstichprobe → build/kontrollpunkte.geojson"""
import json
from pipeline.lib.bericht import erzeuge
from pipeline.lib.io import lies_csv, projektwurzel

W = projektwurzel()
B = W / "build"
adressen = lies_csv(B / "04_geokodiert.csv")
eintraege = lies_csv(B / "eintraege.csv")
herkunft = {}
for e in eintraege:
    herkunft.setdefault((e["strasse_heute"], e["hausnr"], e["hausnr_zusatz"], e["stadtteil"], e["parse_status"], e["strasse_roh"]), e["herkunft"])
for a in adressen:
    a["herkunft"] = herkunft.get((a["strasse_heute"], a["hausnr"], a["hausnr_zusatz"], a["stadtteil"], a["parse_status"], a["strasse_roh"]), "")
md, geo = erzeuge(eintraege, adressen, lies_csv(B / "03_strassen.csv"), lies_csv(B / "dubletten.csv"),
                  lies_csv(B / "01_ausgeschlossen.csv"), lies_csv(B / "strassen_vorschlaege.csv"))
(B / "bericht.md").write_text(md, encoding="utf-8")
(B / "kontrollpunkte.geojson").write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")
print(md[:1500])
```

- [ ] **Step 4: Tests grün, Bericht erzeugen**

Run: `pytest -q && python3 pipeline/05_bericht.py`
Expected: Bericht mit Stufenverteilung. Vergleich mit dem Referenzwert aus der Spec: verortet (haus + strasse + landmarke) in der Größenordnung 90 %, `haus` ≥ 69 %. Liegt `haus` deutlich darunter, zuerst `Gründe (nur offen)` und die Top 50 lesen; typische Ursache ist die Stadtteil-Prüfung (Dickhoff-Stadtteil ≠ OSM-suburb-Schreibung) → Alias in `norm_stadtteil` ergänzen, mit Test.

- [ ] **Step 5: Commit**

```bash
git add pipeline/05_bericht.py pipeline/lib/bericht.py tests/test_bericht.py
git commit -m "feat: Stufe 05 Bericht und Kontrollstichprobe

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Kontrollkarte (Wegwerf), Volllauf, Stichprobenprotokoll, Journal

**Files:**
- Create: `werkzeuge/kontrollkarte.html`, `werkzeuge/serve.py`, `docs/stichprobe.md`

**Interfaces:**
- Consumes: `build/kontrollpunkte.geojson`.
- Produces: nichts für spätere Tasks; Prüfergebnis fließt als Regeln/Tests/Kuratierungszeilen zurück.

- [ ] **Step 1: Kontrollkarte schreiben**

`werkzeuge/kontrollkarte.html` (Leaflet von cdnjs; Grundkarte OSM; optional Stadtplan 1935 der Stadt Essen als Overlay über den Export-Endpunkt):
```html
<!doctype html>
<html lang="de"><head><meta charset="utf-8"><title>Kontrollkarte Geokodierung</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>html,body,#karte{height:100%;margin:0}.legende{background:#fff;padding:6px;font:12px sans-serif}</style></head>
<body><div id="karte"></div>
<script>
const karte = L.map('karte').setView([51.455, 7.012], 12);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {attribution: '© OpenStreetMap'}).addTo(karte);
// Stadtplan 1935 (Stadt Essen, Rechte offen – nur zur Prüfung): dynamischer Export je Ausschnitt
const plan = L.imageOverlay('', [[0,0],[0,0]], {opacity: 0.7});
function ladePlan() {
  const b = karte.getBounds(), s = karte.getSize();
  const url = `https://geo.essen.de/arcgis/rest/services/historischerverein/Stadtplan_1935/MapServer/export?bbox=${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}&bboxSR=4326&imageSR=4326&size=${s.x},${s.y}&format=png&transparent=true&f=image`;
  plan.setUrl(url); plan.setBounds(b);
}
karte.on('moveend', () => { if (karte.hasLayer(plan)) ladePlan(); });
const farben = {haus: '#1a7f37', strasse: '#c77d00', landmarke: '#6f42c1'};
fetch('../build/kontrollpunkte.geojson').then(r => r.json()).then(g => {
  L.geoJSON(g, {pointToLayer: (f, ll) => L.circleMarker(ll, {radius: 5, color: farben[f.properties.stufe] || '#999', fillOpacity: .7}),
    onEachFeature: (f, l) => l.bindPopup(Object.entries(f.properties).map(([k, v]) => `<b>${k}</b>: ${v}`).join('<br>'))}).addTo(karte);
});
L.control.layers(null, {'Stadtplan 1935': plan}).addTo(karte);
karte.on('overlayadd', ladePlan);
const leg = L.control({position: 'bottomleft'}); leg.onAdd = () => { const d = L.DomUtil.create('div', 'legende'); d.innerHTML = 'grün = haus, orange = strasse, lila = landmarke'; return d; }; leg.addTo(karte);
</script></body></html>
```

`werkzeuge/serve.py`:
```python
"""Kleiner Server für die Kontrollkarte: python3 werkzeuge/serve.py → http://localhost:8765/werkzeuge/kontrollkarte.html"""
import http.server, os, sys
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
```

- [ ] **Step 2: Volllauf aller Stufen**

```bash
python3 pipeline/01_einlesen.py && python3 pipeline/02_adresse_parsen.py && python3 pipeline/03_strasse_aufloesen.py && python3 pipeline/04_geokodieren.py && python3 pipeline/05_bericht.py
```
Expected: durchläuft ohne Fehler; `build/bericht.md` vorhanden. Zweiter Lauf von 05 ergibt byte-gleiches `bericht.md` (`md5sum` vergleichen). Zweiter Lauf von 01–04 mit gefülltem Cache ergibt byte-gleiche `eintraege.csv`.

- [ ] **Step 3: Stichprobenprotokoll anlegen**

`docs/stichprobe.md`: Anleitung und Tabelle für die manuelle Prüfung aus der Spec (200 `haus`, 100 `strasse`). Erzeugung der Stichprobe:
```bash
python3 - <<'EOF'
import csv, random
from pipeline.lib.io import lies_csv, schreib_csv, projektwurzel
W = projektwurzel(); a = lies_csv(W / "build/04_geokodiert.csv")
random.seed(2026)
haus = random.sample([x for x in a if x["stufe"] == "haus"], 200)
strasse = random.sample([x for x in a if x["stufe"] == "strasse"], 100)
felder = ["stufe", "strasse_roh", "hausnr", "hausnr_zusatz", "stadtteil", "strasse_heute", "display_name", "lat", "lon", "urteil", "bemerkung"]
schreib_csv(W / "docs/stichprobe_2026.csv", [dict(x, urteil="", bemerkung="") for x in haus + strasse], felder)
EOF
```
Inhalt von `docs/stichprobe.md`:
```markdown
# Manuelle Stichprobe der Geokodierung

Datei: `docs/stichprobe_2026.csv` (200 × haus, 100 × strasse, Zufall mit Seed 2026).
Prüfung je Zeile: `display_name` und Koordinate gegen OSM und, bei Zweifel, gegen den Stadtplan 1935
(Kontrollkarte: `python3 werkzeuge/serve.py`, dann Stadtplan-Overlay einschalten).
`urteil` ∈ {richtig, falsche_strasse, falsche_nummer, falscher_stadtteil, unklar}; `bemerkung` frei.

Abnahmekriterium (Spec §6): haus → 0 falsche Straßen, ≤ 2 falsche Nummern; strasse → 0 falscher Stadtteil.
Jede Abweichung wird als Test (tests/), Regel (pipeline/lib/) oder Zeile in kuratierung/ nachgetragen.
```

- [ ] **Step 4: Journal und Vault aktualisieren**

An `/home/christos/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Journal.md` einen Eintrag mit Datum anhängen: Pipeline läuft durch; Kennzahlen aus `bericht.md` (Stufen-Anteile gesamt und je Teil, Zahl offener Straßen, Größe der Vorschlagsliste); Stichprobe erzeugt und wartet auf Prüfung durch den Projektleiter. In `KONTEXT.md` den Abschnitt „Aktueller Stand“ auf „Pipeline implementiert, Stichprobe offen“ setzen.

- [ ] **Step 5: Commit**

```bash
git add werkzeuge docs/stichprobe.md docs/stichprobe_2026.csv
git commit -m "feat: Kontrollkarte, Volllauf und Stichprobenprotokoll

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Nach dem Plan (nicht Teil der Tasks)

- Der Projektleiter prüft `docs/stichprobe_2026.csv`; Befunde werden als neue Tasks in einem Folgeplan aufgenommen.
- Kuratierung der Straßen-Vorschlagsliste (`build/strassen_vorschlaege.csv` → `kuratierung/strassen_zuordnung.csv`) beginnt mit den 40 häufigsten offenen Straßen; jede Zeile mit Beleg (Dickhoff-Seite oder Stadtplan 1935).
- Experiment Interpolation (Spec §5, Stufe 04) bekommt einen eigenen Plan, sobald die Stichprobe der Basisstufen abgenommen ist.
