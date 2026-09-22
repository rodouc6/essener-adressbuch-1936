# Eigentümer-Kuratierung und Besitz-Ebene — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eigentümer aus Teil II zu kanonischen Eigentümern mit Kategorie zusammenführen (Automatik + Browser-Werkzeug) und als Thema „Besitz“ mit Hausansicht und Suche auf die Karte bringen.

**Architecture:** Ein Python-Skript (`werkzeuge/eigentuemer_cluster.py`) normalisiert und clustert die Schreibweisen und schreibt Vorschläge; das Browser-Werkzeug (`werkzeuge/eigentuemer.html` + reines Modul `werkzeuge/js/eigentuemer_modell.js`) speichert Entscheidungen über einen neuen POST-Endpunkt in `werkzeuge/serve.py` nach `kuratierung/eigentuemer.csv`; Stufe 06 (`pipeline/lib/karte_export.py`) hängt kanonischen Eigentümer und Kategorie an die Teil-II-Einträge, schreibt das Punktattribut `besitz`, den Eigentümer-Suchindex und das Thema; das Frontend bekommt die Farbart `kategorien`, die Vorschlagsart `eigentuemer` und die Zeile in der Hausansicht.

**Tech Stack:** Python 3.12 (csv, json, rapidfuzz), http.server (bestehender Dev-Server), ES-Module ohne Bundler, MapLibre-Ausdrücke, Leaflet (Werkzeug), pytest, node:test, Playwright (e2e).

**Spec:** `docs/superpowers/specs/2026-09-22-eigentuemer-design.md`

## Global Constraints

- Sprache: Deutsch mit korrekten Umlauten in Code-Kommentaren, Texten, Commit-Nachrichten; Bezeichner deutsch wie im Bestand (`schreibweise`, `eigentuemer`, `geprueft`).
- Precision first: nichts Ungeprüftes erscheint auf der Karte als gesichert; Automatik führt nur bei Complete-Linkage ≥ 0,92 zusammen; Grenzfälle 0,75–0,92 nur als Vorschlag.
- `kuratierung/eigentuemer.csv`-Zeilen mit `geprueft=ja` **oder** `bearbeiter≠eigentuemer_cluster` werden von der Automatik nie überschrieben (Präzisierung der Spec §4: auch vom Menschen angefasste, noch nicht als geprüft markierte Zeilen bleiben erhalten).
- Kategorien exakt: `stadt_staat | bergbau | industrie | genossenschaft_siedlung | kirche_stiftung | bank_versicherung | privatperson | sonstige`; auf der Karte zusätzlich `gemischt` und `ungeprueft`.
- CSV über `pipeline.lib.io.lies_csv`/`schreib_csv` (UTF-8, `\n`); JSON kompakt über `karte_export._json`.
- Keine neuen Frontend-Abhängigkeiten in `site/`; Leaflet im Werkzeug wie in `werkzeuge/pruefung.html` von cdnjs.
- Tests: `python3 -m pytest -q` (Rauchtests aus), `node --test site/tests/`, `node --test werkzeuge/tests/`, e2e `python3 -m pytest tests/e2e -q -m e2e`.
- Commits enden mit `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; Arbeit direkt auf `main` (Projektkonvention, Nutzer arbeitet auf main).
- `site/daten/` ist nicht versioniert; Thema-Definitionen liegen in `kuratierung/themen/` und werden von Stufe 06 kopiert.

---

## Dateiübersicht

| Datei | Verantwortung |
|---|---|
| `pipeline/lib/eigentuemer.py` (neu) | Gemeinsame Konstanten und Helfer: `KATEGORIEN`, `AUTOMATIK`, `schreibweise_von(eintrag)`, `lade_kuratierung(zeilen)` |
| `werkzeuge/eigentuemer_cluster.py` (neu) | Normalisierung, Clustering, Auto-Name, Vorschlags-/Belege-Ausgabe, Aktualisierung der Kuratierungsdatei, CLI |
| `kuratierung/eigentuemer_abkuerzungen.csv` (neu) | Abkürzungskatalog (`kurz, lang, kontext, beleg`) und Firmenwörter (`kontext=firmenwort`, `kurz` leer) |
| `kuratierung/eigentuemer.csv` (neu, von der Automatik angelegt) | Entscheidungen je Schreibweise |
| `kuratierung/themen/besitz.json` (neu) | Thema „Besitz“ |
| `werkzeuge/serve.py` | `POST /kuratierung/eigentuemer.csv` |
| `werkzeuge/js/eigentuemer_modell.js` (neu) | Zustand des Werkzeugs: Eigentümerliste, Aktionen, Rückgängig, Fortschritt |
| `werkzeuge/tests/eigentuemer_modell.test.js` (neu) | node-Tests des Modells |
| `werkzeuge/eigentuemer.html` (neu) | Oberfläche des Werkzeugs |
| `pipeline/lib/karte_export.py` | Eigentümer-Zuordnung, `besitz`, `eintrag_kurz`-Felder, Eigentümerindex, Kennzahlen |
| `pipeline/06_karte_export.py` | liest `kuratierung/eigentuemer.csv` |
| `site/js/kategorien.js` (neu) | Anzeigenamen der Kategorien |
| `site/js/themen.js`, `site/js/app.js`, `site/js/suche.js`, `site/js/zustand.js`, `site/js/daten.js`, `site/js/sidebar.js`, `site/js/popup.js` | Farbart `kategorien`, Legende, Vorschlagsart `eigentuemer`, URL-Zustand, Hausansicht, Eigentümerliste |
| `tests/test_eigentuemer_cluster.py`, `tests/test_serve.py`, `tests/test_karte_export.py`, `site/tests/themen.test.js`, `site/tests/suche.test.js`, `site/tests/popup.test.js`, `site/tests/zustand.test.js`, `tests/e2e/test_site.py` | Tests |
| `README.md`, `site/ueber.html`, Vault-Journal | Doku |

---

### Task 1: Gemeinsame Helfer und Abkürzungskatalog

**Files:**
- Create: `pipeline/lib/eigentuemer.py`
- Create: `kuratierung/eigentuemer_abkuerzungen.csv`
- Create: `tests/test_eigentuemer.py`
- Modify: `pyproject.toml:6` (rapidfuzz als Abhängigkeit)

**Interfaces:**
- Produces: `KATEGORIEN: dict[str, str]` (Schlüssel → Anzeigename, 8 Einträge), `AUTOMATIK = "eigentuemer_cluster"`, `FELDER_KURATIERUNG: list[str]`, `schreibweise_von(e: dict) -> tuple[str, str]` (Schreibweise, Art `koerperschaft|person`, oder `("", "")` bei leerem Eigentümer), `lade_kuratierung(zeilen: list[dict]) -> dict[str, dict]` (Schreibweise → Zeile, getrimmt), `gesperrt(z: dict) -> bool`.

- [ ] **Step 1: Failing tests schreiben**

```python
# tests/test_eigentuemer.py
from pipeline.lib.eigentuemer import (AUTOMATIK, FELDER_KURATIERUNG, KATEGORIEN, gesperrt,
                                      lade_kuratierung, schreibweise_von)


def test_kategorien_vollstaendig():
    assert list(KATEGORIEN) == ["stadt_staat", "bergbau", "industrie", "genossenschaft_siedlung",
                                "kirche_stiftung", "bank_versicherung", "privatperson", "sonstige"]
    assert KATEGORIEN["genossenschaft_siedlung"] == "Genossenschaft/Siedlung"


def test_schreibweise_von():
    assert schreibweise_von({"Firmenname": " Fried. Krupp A.G. ", "lastname": "", "firstname": ""}) == ("Fried. Krupp A.G.", "koerperschaft")
    assert schreibweise_von({"Firmenname": "", "lastname": "Schmidt", "firstname": "Wilh."}) == ("Schmidt, Wilh.", "person")
    assert schreibweise_von({"Firmenname": "", "lastname": "Schmidt", "firstname": ""}) == ("Schmidt", "person")
    assert schreibweise_von({"Firmenname": "", "lastname": "", "firstname": ""}) == ("", "")


def test_lade_kuratierung_und_sperre():
    zeilen = [dict(schreibweise=" Stadt Essen ", eigentuemer="Stadt Essen", geprueft="ja", bearbeiter="christos"),
              dict(schreibweise="Fried. Krupp A.G.", eigentuemer="Fried. Krupp AG", geprueft="", bearbeiter=AUTOMATIK),
              dict(schreibweise="Fried. Krupp AG.", eigentuemer="Krupp", geprueft="", bearbeiter="christos")]
    k = lade_kuratierung(zeilen)
    assert set(k) == {"Stadt Essen", "Fried. Krupp A.G.", "Fried. Krupp AG."}
    assert gesperrt(k["Stadt Essen"]) is True          # geprüft
    assert gesperrt(k["Fried. Krupp A.G."]) is False   # Automatik, ungeprüft
    assert gesperrt(k["Fried. Krupp AG."]) is True     # vom Menschen angefasst
    assert FELDER_KURATIERUNG == ["schreibweise", "art", "eigentuemer", "kategorie", "geprueft", "bearbeiter", "datum", "hinweis"]
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag prüfen**

Run: `python3 -m pytest tests/test_eigentuemer.py -q`
Expected: FAIL mit `ModuleNotFoundError: pipeline.lib.eigentuemer`

- [ ] **Step 3: Modul schreiben**

```python
# pipeline/lib/eigentuemer.py
"""Gemeinsames für Eigentümer-Kuratierung (Teilprojekt 3): Kategorien, Schlüssel, Sperre.

Der Eigentümername steht in Teil II bei Körperschaften in `Firmenname`, bei Personen in
`lastname`/`firstname`; die Spalte `Eigentümer` trägt nur die Rolle (Spec §1).
"""
from __future__ import annotations

KATEGORIEN = {
    "stadt_staat": "Stadt/Staat/Reich",
    "bergbau": "Bergbau",
    "industrie": "Industrie",
    "genossenschaft_siedlung": "Genossenschaft/Siedlung",
    "kirche_stiftung": "Kirche/Stiftung",
    "bank_versicherung": "Bank/Versicherung",
    "privatperson": "Privatperson",
    "sonstige": "Sonstige",
}
AUTOMATIK = "eigentuemer_cluster"
FELDER_KURATIERUNG = ["schreibweise", "art", "eigentuemer", "kategorie", "geprueft", "bearbeiter", "datum", "hinweis"]


def schreibweise_von(e: dict) -> tuple[str, str]:
    """(Schreibweise, Art) eines Teil-II-Eintrags; Personen als „Nachname, Vorname“."""
    firma = (e.get("Firmenname") or "").strip()
    if firma:
        return firma, "koerperschaft"
    nach, vor = (e.get("lastname") or "").strip(), (e.get("firstname") or "").strip()
    if not nach:
        return "", ""
    return (f"{nach}, {vor}" if vor else nach), "person"


def lade_kuratierung(zeilen: list[dict]) -> dict[str, dict]:
    """kuratierung/eigentuemer.csv als Schreibweise → Zeile (Werte getrimmt)."""
    out: dict[str, dict] = {}
    for z in zeilen:
        z = {k: (v or "").strip() for k, v in z.items()}
        if z.get("schreibweise"):
            out[z["schreibweise"]] = z
    return out


def gesperrt(z: dict) -> bool:
    """Die Automatik darf eine Zeile nur überschreiben, wenn sie ungeprüft ist und zuletzt von ihr selbst stammt."""
    return z.get("geprueft") == "ja" or (z.get("bearbeiter") or AUTOMATIK) != AUTOMATIK
```

- [ ] **Step 4: Abkürzungskatalog anlegen**

`kuratierung/eigentuemer_abkuerzungen.csv` (Startbestand aus dem v1-Katalog `AdressbuchEssen1936/v2/analyse/koerperschaften/abkuerzungen_firmen.csv`, Zeilen mit Expansion, plus Firmenwörter und Komposita; `kontext` leer = immer, `firmenwort` = nur vor einem Firmenwort; Zeilen mit `kurz` leer und `kontext=firmenwort` definieren die Firmenwörter):

```csv
kurz,lang,kontext,beleg
fried,friedrich,,v1-Katalog geprüft
friedr,friedrich,,v1-Katalog geprüft
bergw,bergwerks,,v1-Katalog geprüft
bergwerksver,bergwerksverein,,v1-Katalog geprüft
gew,gewerkschaft,,v1-Katalog geprüft
gewerksch,gewerkschaft,,v1-Katalog geprüft
ess,essener,,v1-Katalog geprüft
mülh,mülheimer,,v1-Katalog geprüft
dtsch,deutsche,,v1-Katalog geprüft
dtsche,deutsche,,v1-Katalog geprüft
gebr,gebrüder,,v1-Katalog geprüft
ges,gesellschaft,,v1-Katalog geprüft
nachf,nachfolger,,v1-Katalog geprüft
wwe,witwe,,v1-Katalog geprüft
stahlw,stahlwerke,,v1-Katalog geprüft
ver,vereinigte,firmenwort,"v1-Befund: „Ver.“ heißt zu 16 % „Verein“, daher nur vor Firmenwort"
verein,vereinigte,firmenwort,"nur mit Punkt (Abkürzung) und vor Firmenwort; „Verein“ ohne Punkt bleibt"
,stahlwerke,firmenwort,Firmenwort
,bergwerke,firmenwort,Firmenwort
,bergwerks,firmenwort,Firmenwort
,bergwerksverein,firmenwort,Firmenwort
,hütten,firmenwort,Firmenwort
,hüttenwerke,firmenwort,Firmenwort
,glanzstoff,firmenwort,Firmenwort
,kesselwerke,firmenwort,Firmenwort
,gesellschaft,firmenwort,Firmenwort
,verein,firmenwort,Firmenwort
,steinkohlen,firmenwort,Firmenwort
,bergwerk,firmenwort,Firmenwort
,werke,firmenwort,Firmenwort
```

- [ ] **Step 5: rapidfuzz eintragen**

In `pyproject.toml` Zeile 6: `dependencies = ["requests>=2.31", "rapidfuzz>=3.0"]`.

- [ ] **Step 6: Tests laufen lassen**

Run: `python3 -m pytest tests/test_eigentuemer.py -q`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add pipeline/lib/eigentuemer.py kuratierung/eigentuemer_abkuerzungen.csv tests/test_eigentuemer.py pyproject.toml
git commit -m "feat(eigentuemer): gemeinsame Helfer (Kategorien, Schreibweise, Sperre) und Abkürzungskatalog

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Normalisierung zum Vergleichsschlüssel

**Files:**
- Create: `werkzeuge/eigentuemer_cluster.py`
- Create: `tests/test_eigentuemer_cluster.py`

**Interfaces:**
- Produces: `lade_katalog(pfad) -> Katalog` mit `Katalog = dict(abk: dict[str, tuple[str, str]], firmenwoerter: set[str])`; `normalisiere(name: str, katalog: Katalog) -> str`; `rechtsform_anzeige(name: str) -> str` (Auto-Name-Hilfe: `A.G.`-Varianten → `AG`, `G.m.b.H.` → `GmbH`, `e.G.m.b.H.` → `eGmbH`); `RECHTSFORMEN: list[tuple[re.Pattern, str]]`.

- [ ] **Step 1: Failing tests**

```python
# tests/test_eigentuemer_cluster.py
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from werkzeuge.eigentuemer_cluster import lade_katalog, normalisiere, rechtsform_anzeige

W = pathlib.Path(__file__).resolve().parents[1]
KAT = lade_katalog(W / "kuratierung" / "eigentuemer_abkuerzungen.csv")


def test_rechtsformen():
    for s in ("Fried. Krupp A.G.", "Fried. Krupp A. G.", "Fried. Krupp A.-G.", "Fried. Krupp AG.", "Fried. Krupp, A. -G.", "Fried. Krupp AG"):
        assert normalisiere(s, KAT) == "friedrich krupp ag", s
    assert normalisiere("Bau- u. Sparverein e.G.m.b.H.", KAT) == normalisiere("Bau- u. Sparverein e. G. m. b. H.", KAT)
    assert normalisiere("Wohnungsbau G.m.b.H.", KAT).endswith(" gmbh")
    assert normalisiere("Kath. Kirchengemeinde St. Josef", KAT) == "kath kirchengemeinde st josef"


def test_abkuerzungen_und_ver_regel():
    assert normalisiere("Gew. Math. Stinnes", KAT) == "gewerkschaft math stinnes"
    assert normalisiere("Gewerksch. Viktoria Mathias", KAT) == normalisiere("Gewerkschaft Viktoria Mathias", KAT)
    assert normalisiere("Ver. Stahlw. A.G.", KAT) == normalisiere("Vereinigte Stahlwerke A.-G.", KAT) == "vereinigte stahlwerke ag"
    # „Ver.“ ohne Firmenwort bleibt „ver“ (kann „Verein“ heißen)
    assert normalisiere("Ver. Kirchengemeinde", KAT) == "ver kirchengemeinde"
    # „Verein“ ohne Punkt ist keine Abkürzung
    assert normalisiere("Bergbau Verein Essen", KAT) == "bergbau verein essen"


def test_kompositum():
    assert normalisiere("Mülh. Bergw. Verein", KAT) == normalisiere("Mülheimer Bergwerksverein", KAT) == "mülheimer bergwerksverein"
    assert normalisiere("Ess. Bergw. Verein König Wilhelm", KAT) == "essener bergwerksverein könig wilhelm"


def test_rechtsform_anzeige():
    assert rechtsform_anzeige("Fried. Krupp A. -G.") == "Fried. Krupp AG"
    assert rechtsform_anzeige("Fried. Krupp, A.G.") == "Fried. Krupp AG"
    assert rechtsform_anzeige("Sparverein e. G. m. b. H.") == "Sparverein eGmbH"
    assert rechtsform_anzeige("Stadt Essen") == "Stadt Essen"
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `python3 -m pytest tests/test_eigentuemer_cluster.py -q`
Expected: FAIL mit `ModuleNotFoundError: werkzeuge.eigentuemer_cluster`

- [ ] **Step 3: Normalisierung implementieren**

```python
# werkzeuge/eigentuemer_cluster.py
"""Eigentümer aus Teil II clustern (Teilprojekt 3, Spec §4).

Aufruf: python3 werkzeuge/eigentuemer_cluster.py [--min-haeuser 5]
Liest build/eintraege.csv, schreibt build/eigentuemer_vorschlag.csv und build/eigentuemer_belege.json
und legt fehlende Zeilen in kuratierung/eigentuemer.csv an (gesperrte Zeilen bleiben unberührt).
"""
from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.lib.io import lies_csv

# Rechtsformen: Buchschreibungen wie „A.G.“, „A. G.“, „A.-G.“, „AG.“, „A. -G.“ → ein Token.
RECHTSFORMEN: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\be\.?\s?g\.?\s?m\.?\s?b\.?\s?h\b\.?", re.I), "egmbh"),
    (re.compile(r"\bg\.?\s?m\.?\s?b\.?\s?h\b\.?", re.I), "gmbh"),
    (re.compile(r"\ba\.?\s?-?\s?g\b\.?", re.I), "ag"),
    (re.compile(r"\be\.\s?v\b\.?", re.I), "ev"),
    (re.compile(r"\bk\.\s?-?\s?g\b\.?", re.I), "kg"),
]
RECHTSFORM_TOKENS = {"egmbh", "gmbh", "ag", "ev", "kg", "ohg"}
ANZEIGE = {"egmbh": "eGmbH", "gmbh": "GmbH", "ag": "AG", "ev": "e. V.", "kg": "KG"}
STOPP = {"der", "die", "das", "und", "u", "von", "zu", "in", "für", "des"}

Katalog = dict


def lade_katalog(pfad: Path | str) -> Katalog:
    abk: dict[str, tuple[str, str]] = {}
    firmenwoerter: set[str] = set()
    for z in lies_csv(pfad):
        kurz, lang, kontext = (z.get("kurz") or "").strip().lower(), (z.get("lang") or "").strip().lower(), (z.get("kontext") or "").strip()
        if kurz:
            abk[kurz] = (lang, kontext)
        elif kontext == "firmenwort" and lang:
            firmenwoerter.add(lang)
    return dict(abk=abk, firmenwoerter=firmenwoerter)


def _rechtsformen(text: str) -> str:
    for muster, ersatz in RECHTSFORMEN:
        text = muster.sub(" " + ersatz + " ", text)
    return text


def normalisiere(name: str, katalog: Katalog) -> str:
    """Vergleichsschlüssel: klein, Rechtsformen vereinheitlicht, Abkürzungen (nur mit Punkt) aufgelöst,
    Komposita aus Firmenwörtern zusammengezogen, Interpunktion entfernt (Spec §4.2)."""
    t = unicodedata.normalize("NFKC", name).lower()
    t = _rechtsformen(t)
    t = t.replace(",", " ").replace("/", " ")
    roh = [x for x in re.split(r"\s+", t.strip()) if x]
    tokens: list[str] = []
    for i, tok in enumerate(roh):
        abgekuerzt = tok.endswith(".")
        kern = tok.strip(".-").lower()
        if not kern:
            continue
        eintrag = katalog["abk"].get(kern) if abgekuerzt else None
        if eintrag:
            lang, kontext = eintrag
            naechster = roh[i + 1].strip(".-") if i + 1 < len(roh) else ""
            if kontext == "firmenwort":
                folgt = katalog["abk"].get(naechster, (naechster, ""))[0] if roh[i + 1:] and roh[i + 1].endswith(".") else naechster
                if folgt in katalog["firmenwoerter"]:
                    kern = lang
            else:
                kern = lang
        tokens.append(kern)
    # Komposita: „bergwerks verein“ → „bergwerksverein“, wenn beide Teile Firmenwörter sind und das
    # zusammengesetzte Wort ebenfalls als Firmenwort geführt wird.
    out: list[str] = []
    for tok in tokens:
        if out and out[-1] in katalog["firmenwoerter"] and tok in katalog["firmenwoerter"] and (out[-1] + tok) in katalog["firmenwoerter"]:
            out[-1] = out[-1] + tok
        else:
            out.append(tok)
    return re.sub(r"[^\w\s]", "", " ".join(out)).strip()


def rechtsform_anzeige(name: str) -> str:
    """Auto-Name-Hilfe: Rechtsform im Anzeigenamen vereinheitlichen, Rest unverändert (Spec §4.4)."""
    t = name
    for muster, ersatz in RECHTSFORMEN:
        t = muster.sub(" " + ANZEIGE[ersatz] + " ", t)
    t = re.sub(r"\s*,\s*(AG|GmbH|eGmbH|KG|e\. V\.)\b", r" \1", t)
    return re.sub(r"\s+", " ", t).strip()
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_eigentuemer_cluster.py -q`
Expected: 4 passed. Falls `test_kompositum` scheitert, prüfen, ob `bergwerks` + `verein` → `bergwerksverein` alle drei im Katalog als Firmenwort stehen (Task 1 Step 4).

- [ ] **Step 5: Commit**

```bash
git add werkzeuge/eigentuemer_cluster.py tests/test_eigentuemer_cluster.py
git commit -m "feat(eigentuemer): Normalisierung der Schreibweisen (Rechtsformen, Abkürzungskatalog, Ver.-Regel, Komposita)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Clustering, Auto-Name, Vorschläge

**Files:**
- Modify: `werkzeuge/eigentuemer_cluster.py`
- Modify: `tests/test_eigentuemer_cluster.py`

**Interfaces:**
- Consumes: `normalisiere`, `rechtsform_anzeige`, `RECHTSFORM_TOKENS`, `STOPP`.
- Produces: `cluster_id(schluessel: str) -> str` (sha1-Hex, 10 Zeichen); `clustere(zaehler: dict[str, int], katalog, schwelle=0.92, vorschlag_ab=0.75) -> list[dict]` mit Cluster-Dicts `{id, name, schluessel, mitglieder: list[tuple[str, int]] (nach Anzahl absteigend), haeuser: int, aehnlichkeit: float, vorschlag_fuer: str}` sortiert nach `haeuser` absteigend; `auto_name(mitglieder) -> str`.

- [ ] **Step 1: Failing tests anhängen**

```python
# tests/test_eigentuemer_cluster.py (anhängen)
from werkzeuge.eigentuemer_cluster import auto_name, cluster_id, clustere


def test_clustere_krupp_zusammen_pfarreien_getrennt():
    z = {"Fried. Krupp A.G.": 257, "Fried. Krupp A. G.": 181, "Fried. Krupp A.-G.": 79, "Friedr. Krupp A.G.": 40,
         "Fried. Krupp AG": 9, "Frau-Margarete-Krupp-Stiftung": 31,
         "Kath. Kirchengemeinde St. Josef": 12, "Kath. Kirchengemeinde St. Andreas": 8,
         "Stadt Essen": 1027}
    c = clustere(z, KAT)
    namen = {x["name"]: x for x in c}
    krupp = namen["Fried. Krupp AG"]
    assert [m[0] for m in krupp["mitglieder"]] == ["Fried. Krupp A.G.", "Fried. Krupp A. G.", "Fried. Krupp A.-G.", "Friedr. Krupp A.G.", "Fried. Krupp AG"]
    assert krupp["haeuser"] == 566 and krupp["aehnlichkeit"] == 1.0
    assert "Frau-Margarete-Krupp-Stiftung" in namen                     # nicht mit Krupp AG verschmolzen
    assert "Kath. Kirchengemeinde St. Josef" in namen and "Kath. Kirchengemeinde St. Andreas" in namen
    assert c[0]["name"] == "Stadt Essen"                                 # nach Häusern sortiert
    assert krupp["id"] == cluster_id("friedrich krupp ag") and len(krupp["id"]) == 10


def test_clustere_grenzfall_wird_vorschlag():
    # Gleicher Block „gewerkschaft“; Token-Set-Ähnlichkeit zwischen 0,75 und 0,92 → kein Merge, aber Vorschlag
    z = {"Gewerkschaft Viktoria Mathias": 79, "Gewerksch. Viktoria Mathias": 67, "Gewerkschaft Viktoria Mathias Schacht 3": 4}
    c = clustere(z, KAT)
    gross = next(x for x in c if x["haeuser"] == 146)
    klein = next(x for x in c if x["haeuser"] == 4)
    assert len(gross["mitglieder"]) == 2 and gross["vorschlag_fuer"] == ""
    assert klein["vorschlag_fuer"] == gross["id"]


def test_clustere_complete_linkage_keine_kette():
    # a~b und b~c ähnlich, a~c nicht → höchstens zwei zusammen, nie alle drei
    z = {"Bauverein Essen Nord": 5, "Bauverein Essen Nord West": 5, "Bauverein Essen West Süd": 5}
    c = clustere(z, KAT, schwelle=0.8, vorschlag_ab=0.5)
    assert max(len(x["mitglieder"]) for x in c) <= 2


def test_auto_name():
    assert auto_name([("Fried. Krupp A.G.", 257), ("Fried. Krupp A. G.", 181)]) == "Fried. Krupp AG"
    assert auto_name([("Stadt Essen", 3)]) == "Stadt Essen"
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `python3 -m pytest tests/test_eigentuemer_cluster.py -q`
Expected: FAIL mit `ImportError: cannot import name 'auto_name'`

- [ ] **Step 3: Clustering implementieren** (an `werkzeuge/eigentuemer_cluster.py` anhängen)

```python
from rapidfuzz import fuzz


def cluster_id(schluessel: str) -> str:
    return hashlib.sha1(schluessel.encode("utf-8")).hexdigest()[:10]


def auto_name(mitglieder: list[tuple[str, int]]) -> str:
    """Häufigste Schreibweise mit vereinheitlichter Rechtsform (Spec §4.4)."""
    return rechtsform_anzeige(max(mitglieder, key=lambda m: (m[1], -len(m[0])))[0])


def _block(schluessel: str) -> str:
    for tok in schluessel.split():
        if tok not in RECHTSFORM_TOKENS and tok not in STOPP:
            return tok
    return schluessel


def _sim(a: str, b: str) -> float:
    return fuzz.token_set_ratio(a, b) / 100.0


def clustere(zaehler: dict[str, int], katalog: Katalog, schwelle: float = 0.92, vorschlag_ab: float = 0.75) -> list[dict]:
    """Schreibweise → Anzahl zu Clustern (Spec §4.3): exakt gleicher Schlüssel, dann Complete-Linkage
    innerhalb eines Blocks (erstes signifikantes Token); Grenzfälle als vorschlag_fuer."""
    # 1. exakte Gruppen
    gruppen: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for s, n in zaehler.items():
        gruppen[normalisiere(s, katalog)].append((s, n))
    cluster: list[dict] = [dict(schluessel=[k], mitglieder=sorted(m, key=lambda x: (-x[1], x[0])), aehnlichkeit=1.0)
                           for k, m in gruppen.items()]
    # 2. Complete-Linkage je Block
    bloecke: dict[str, list[dict]] = defaultdict(list)
    for c in cluster:
        bloecke[_block(c["schluessel"][0])].append(c)
    fertig: list[dict] = []
    for block in bloecke.values():
        aktiv = list(block)
        while True:
            bestes = None
            for i in range(len(aktiv)):
                for j in range(i + 1, len(aktiv)):
                    mn = min(_sim(a, b) for a in aktiv[i]["schluessel"] for b in aktiv[j]["schluessel"])
                    if mn >= schwelle and (bestes is None or mn > bestes[0]):
                        bestes = (mn, i, j)
            if bestes is None:
                break
            mn, i, j = bestes
            a, b = aktiv[i], aktiv[j]
            neu = dict(schluessel=a["schluessel"] + b["schluessel"],
                       mitglieder=sorted(a["mitglieder"] + b["mitglieder"], key=lambda x: (-x[1], x[0])),
                       aehnlichkeit=min(a["aehnlichkeit"], b["aehnlichkeit"], mn))
            aktiv = [c for k, c in enumerate(aktiv) if k not in (i, j)] + [neu]
        for c in aktiv:
            c["haeuser"] = sum(n for _, n in c["mitglieder"])
            c["name"] = auto_name(c["mitglieder"])
            c["id"] = cluster_id(normalisiere(c["mitglieder"][0][0], katalog))
            c["vorschlag_fuer"] = ""
        # 3. Grenzfälle: kleinerer Cluster → Vorschlag auf den größeren mit der höchsten Ähnlichkeit
        for i in range(len(aktiv)):
            for j in range(len(aktiv)):
                if i == j:
                    continue
                klein, gross = aktiv[i], aktiv[j]
                if (gross["haeuser"], gross["name"]) <= (klein["haeuser"], klein["name"]):
                    continue
                mx = max(_sim(a, b) for a in klein["schluessel"] for b in gross["schluessel"])
                if vorschlag_ab <= mx < schwelle and mx > klein.get("_vorschlag_sim", 0.0):
                    klein["vorschlag_fuer"], klein["_vorschlag_sim"] = gross["id"], mx
        fertig.extend(aktiv)
    for c in fertig:
        c.pop("_vorschlag_sim", None)
        c["schluessel"] = c["schluessel"][0]
        c["aehnlichkeit"] = round(c["aehnlichkeit"], 3)
    return sorted(fertig, key=lambda c: (-c["haeuser"], c["name"]))
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_eigentuemer_cluster.py -q`
Expected: 8 passed. Falls `test_clustere_grenzfall_wird_vorschlag` scheitert, weil die Ähnlichkeit ≥ 0,92 ist (Token-Set-Ratio ist bei Teilmengen großzügig): Testdaten so ändern, dass das dritte Mitglied „Gewerkschaft Viktoria Mathias, Zeche Schacht 3“ heißt, und die tatsächliche Zahl mit `python3 -c "from rapidfuzz import fuzz; print(fuzz.token_set_ratio('gewerkschaft viktoria mathias','gewerkschaft viktoria mathias zeche schacht 3'))"` prüfen; liegt sie weiterhin ≥ 92, in `_sim` `fuzz.token_sort_ratio` statt `token_set_ratio` verwenden (Spec-Nachtrag im Commit nennen).

- [ ] **Step 5: Commit**

```bash
git add werkzeuge/eigentuemer_cluster.py tests/test_eigentuemer_cluster.py
git commit -m "feat(eigentuemer): Clustering mit Complete-Linkage je Block, Grenzfälle als Vorschlag, Auto-Name

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Skript-Lauf: Vorschlag, Belege, Kuratierungsdatei, CLI

**Files:**
- Modify: `werkzeuge/eigentuemer_cluster.py`
- Modify: `tests/test_eigentuemer_cluster.py`
- Modify: `.gitignore` (nichts nötig: `build/` ist ignoriert)

**Interfaces:**
- Consumes: `clustere`, `schreibweise_von`, `lade_kuratierung`, `gesperrt`, `AUTOMATIK`, `FELDER_KURATIERUNG`.
- Produces: `sammle(eintraege: list[dict]) -> tuple[dict[str,int], dict[str,int], dict[str, list[dict]]]` (Zähler Körperschaften, Zähler Personen, Belege je Schreibweise); `vorschlagszeilen(cluster, personen, min_haeuser) -> list[dict]` (Spalten wie Spec §3.1); `aktualisiere_kuratierung(alt: list[dict], vorschlag: list[dict], datum: str) -> list[dict]`; `main(argv) -> dict` (Kennzahlen).

- [ ] **Step 1: Failing tests anhängen**

```python
# tests/test_eigentuemer_cluster.py (anhängen)
import json
from pipeline.lib.eigentuemer import AUTOMATIK
from werkzeuge.eigentuemer_cluster import aktualisiere_kuratierung, main, sammle, vorschlagszeilen


def _z(**k):
    z = dict(teil="II", id="1", Firmenname="", lastname="", firstname="", Adresse="", strasse_roh="Grenzstr.", hausnr="1",
             hausnr_zusatz="", stadtteil="Katernberg", Verwalter="", page="II-001", lat="51.49", lon="7.06", stufe="haus")
    z.update(k); return z


def test_sammle_trennt_und_belegt():
    e = [_z(id="1", Firmenname="Stadt Essen"), _z(id="2", Firmenname="Stadt Essen", hausnr="2"),
         _z(id="3", lastname="Schmidt", firstname="Wilh."), _z(id="4", teil="I", lastname="Nicht", firstname="Teil II"),
         _z(id="5", lat="", lon="", stufe="offen", Firmenname="Stadt Essen")]
    k, p, belege = sammle(e)
    assert k == {"Stadt Essen": 3} and p == {"Schmidt, Wilh.": 1}
    assert [b["id"] for b in belege["Stadt Essen"]] == ["1", "2", "5"]
    assert belege["Stadt Essen"][0] == dict(id="1", adresse="Grenzstr. 1", stadtteil="Katernberg", verwalter="", seite="II-001", lat=51.49, lon=7.06, stufe="haus")
    assert belege["Stadt Essen"][2]["lat"] is None


def test_vorschlagszeilen_und_pruefpflicht():
    c = clustere({"Fried. Krupp A.G.": 6, "Fried. Krupp AG": 1, "Klein GmbH": 2}, KAT)
    z = vorschlagszeilen(c, {"Schmidt, Wilh.": 7, "Meier, Karl": 2}, min_haeuser=5)
    by = {x["schreibweise"]: x for x in z}
    assert by["Fried. Krupp A.G."]["pruefpflichtig"] == "ja" and by["Fried. Krupp AG"]["pruefpflichtig"] == "ja"
    assert by["Klein GmbH"]["pruefpflichtig"] == "nein"
    assert by["Schmidt, Wilh."] == dict(schreibweise="Schmidt, Wilh.", art="person", anzahl="7", cluster_id=cluster_id("Schmidt, Wilh."),
                                        cluster_name="Schmidt, Wilh.", aehnlichkeit="1.0", vorschlag_fuer="", pruefpflichtig="ja")
    assert by["Meier, Karl"]["pruefpflichtig"] == "nein"
    assert [x["schreibweise"] for x in z][:2] == ["Schmidt, Wilh.", "Fried. Krupp A.G."]   # nach Häusern absteigend


def test_aktualisiere_kuratierung_sperre():
    alt = [dict(schreibweise="Stadt Essen", art="koerperschaft", eigentuemer="Stadt Essen", kategorie="stadt_staat", geprueft="ja", bearbeiter="christos", datum="2026-09-20", hinweis=""),
           dict(schreibweise="Fried. Krupp A.G.", art="koerperschaft", eigentuemer="Altname", kategorie="industrie", geprueft="", bearbeiter=AUTOMATIK, datum="2026-09-20", hinweis="x"),
           dict(schreibweise="Fried. Krupp AG.", art="koerperschaft", eigentuemer="Krupp", kategorie="", geprueft="", bearbeiter="christos", datum="2026-09-21", hinweis=""),
           dict(schreibweise="Weg GmbH", art="koerperschaft", eigentuemer="Weg GmbH", kategorie="", geprueft="", bearbeiter=AUTOMATIK, datum="2026-09-20", hinweis="")]
    vorschlag = [dict(schreibweise="Stadt Essen", art="koerperschaft", cluster_name="Stadt Essen (neu)"),
                 dict(schreibweise="Fried. Krupp A.G.", art="koerperschaft", cluster_name="Fried. Krupp AG"),
                 dict(schreibweise="Fried. Krupp AG.", art="koerperschaft", cluster_name="Fried. Krupp AG"),
                 dict(schreibweise="Schmidt, Wilh.", art="person", cluster_name="Schmidt, Wilh.")]
    neu = {z["schreibweise"]: z for z in aktualisiere_kuratierung(alt, vorschlag, "2026-09-22")}
    assert neu["Stadt Essen"]["eigentuemer"] == "Stadt Essen"                       # geprüft: unverändert
    assert neu["Fried. Krupp A.G."]["eigentuemer"] == "Fried. Krupp AG"             # Automatik-Zeile: neuer Vorschlag
    assert neu["Fried. Krupp A.G."]["kategorie"] == "industrie" and neu["Fried. Krupp A.G."]["hinweis"] == "x"  # Kategorie/Hinweis bleiben
    assert neu["Fried. Krupp A.G."]["datum"] == "2026-09-22"
    assert neu["Fried. Krupp AG."]["eigentuemer"] == "Krupp"                        # vom Menschen angefasst: bleibt
    assert neu["Schmidt, Wilh."] == dict(schreibweise="Schmidt, Wilh.", art="person", eigentuemer="Schmidt, Wilh.", kategorie="privatperson", geprueft="", bearbeiter=AUTOMATIK, datum="2026-09-22", hinweis="")
    assert neu["Weg GmbH"]["eigentuemer"] == "Weg GmbH"                              # verwaist: bleibt stehen
    assert list(neu) == ["Stadt Essen", "Fried. Krupp A.G.", "Fried. Krupp AG.", "Weg GmbH", "Schmidt, Wilh."]  # alte Reihenfolge, Neues hinten


def test_main_schreibt_dateien(tmp_path):
    (tmp_path / "build").mkdir(); (tmp_path / "kuratierung").mkdir()
    import shutil; shutil.copy(W / "kuratierung" / "eigentuemer_abkuerzungen.csv", tmp_path / "kuratierung")
    from pipeline.lib.io import schreib_csv
    e = [_z(id="1", Firmenname="Stadt Essen"), _z(id="2", lastname="Schmidt", firstname="Wilh.")]
    schreib_csv(tmp_path / "build" / "eintraege.csv", e, list(e[0]))
    k = main(["--min-haeuser", "1", "--wurzel", str(tmp_path)])
    assert k["koerperschaften"] == 1 and k["personen"] == 1 and k["pruefpflichtig"] == 2
    assert (tmp_path / "build" / "eigentuemer_vorschlag.csv").exists()
    belege = json.loads((tmp_path / "build" / "eigentuemer_belege.json").read_text(encoding="utf-8"))
    assert belege["Stadt Essen"][0]["id"] == "1"
    kur = lies_csv_test(tmp_path / "kuratierung" / "eigentuemer.csv")
    assert [z["schreibweise"] for z in kur] == ["Stadt Essen", "Schmidt, Wilh."]
    assert kur[1]["kategorie"] == "privatperson"


def lies_csv_test(p):
    from pipeline.lib.io import lies_csv
    return lies_csv(p)
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `python3 -m pytest tests/test_eigentuemer_cluster.py -q`
Expected: FAIL mit `ImportError: cannot import name 'aktualisiere_kuratierung'`

- [ ] **Step 3: Implementieren** (anhängen)

```python
import argparse
import datetime
import json

from pipeline.lib.eigentuemer import AUTOMATIK, FELDER_KURATIERUNG, gesperrt, lade_kuratierung, schreibweise_von
from pipeline.lib.io import projektwurzel, schreib_csv

VORSCHLAG_FELDER = ["schreibweise", "art", "anzahl", "cluster_id", "cluster_name", "aehnlichkeit", "vorschlag_fuer", "pruefpflichtig"]


def _zahl(v: str):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def sammle(eintraege: list[dict]) -> tuple[dict[str, int], dict[str, int], dict[str, list[dict]]]:
    """Teil-II-Zeilen → (Zähler Körperschaften, Zähler Personen, Belege je Schreibweise, Spec §3.2)."""
    koerper: dict[str, int] = defaultdict(int)
    personen: dict[str, int] = defaultdict(int)
    belege: dict[str, list[dict]] = defaultdict(list)
    for e in eintraege:
        if e.get("teil") != "II":
            continue
        s, art = schreibweise_von(e)
        if not s:
            continue
        (koerper if art == "koerperschaft" else personen)[s] += 1
        nr = ((e.get("hausnr") or "") + (e.get("hausnr_zusatz") or "")).strip()
        belege[s].append(dict(id=e.get("id", ""), adresse=" ".join(x for x in (e.get("strasse_roh", ""), nr) if x),
                              stadtteil=e.get("stadtteil", "") or e.get("Vorort", ""), verwalter=e.get("Verwalter", ""),
                              seite=e.get("page", ""), lat=_zahl(e.get("lat")), lon=_zahl(e.get("lon")), stufe=e.get("stufe", "")))
    return dict(koerper), dict(personen), dict(belege)


def vorschlagszeilen(cluster: list[dict], personen: dict[str, int], min_haeuser: int) -> list[dict]:
    zeilen: list[dict] = []
    for c in cluster:
        for s, n in c["mitglieder"]:
            zeilen.append(dict(schreibweise=s, art="koerperschaft", anzahl=str(n), cluster_id=c["id"], cluster_name=c["name"],
                               aehnlichkeit=str(c["aehnlichkeit"]), vorschlag_fuer=c["vorschlag_fuer"],
                               pruefpflichtig="ja" if c["haeuser"] >= min_haeuser else "nein", _haeuser=c["haeuser"]))
    for s, n in personen.items():
        zeilen.append(dict(schreibweise=s, art="person", anzahl=str(n), cluster_id=cluster_id(s), cluster_name=s,
                           aehnlichkeit="1.0", vorschlag_fuer="", pruefpflichtig="ja" if n >= min_haeuser else "nein", _haeuser=n))
    zeilen.sort(key=lambda z: (-z["_haeuser"], z["cluster_name"], -int(z["anzahl"]), z["schreibweise"]))
    for z in zeilen:
        z.pop("_haeuser")
    return zeilen


def aktualisiere_kuratierung(alt: list[dict], vorschlag: list[dict], datum: str) -> list[dict]:
    """Gesperrte Zeilen (geprüft oder vom Menschen angefasst) bleiben; Automatik-Zeilen bekommen den neuen
    Vorschlag (Kategorie und Hinweis bleiben); Fehlendes wird angehängt; Verwaistes bleibt stehen."""
    bekannt = lade_kuratierung(alt)
    out: list[dict] = [dict(z) for z in alt]
    index = {z["schreibweise"].strip(): i for i, z in enumerate(out)}
    for v in vorschlag:
        s = v["schreibweise"]
        if s in bekannt:
            if gesperrt(bekannt[s]):
                continue
            z = out[index[s]]
            if z.get("eigentuemer", "").strip() != v["cluster_name"]:
                z.update(eigentuemer=v["cluster_name"], datum=datum)
        else:
            out.append(dict(schreibweise=s, art=v["art"], eigentuemer=v["cluster_name"],
                            kategorie="privatperson" if v["art"] == "person" else "", geprueft="",
                            bearbeiter=AUTOMATIK, datum=datum, hinweis=""))
    return out


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-haeuser", type=int, default=5)
    ap.add_argument("--wurzel", default=None, help="Projektwurzel (Tests)")
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    katalog = lade_katalog(W / "kuratierung" / "eigentuemer_abkuerzungen.csv")
    koerper, personen, belege = sammle(lies_csv(W / "build" / "eintraege.csv"))
    cluster = clustere(koerper, katalog)
    vorschlag = vorschlagszeilen(cluster, personen, a.min_haeuser)
    schreib_csv(W / "build" / "eigentuemer_vorschlag.csv", vorschlag, VORSCHLAG_FELDER)
    (W / "build" / "eigentuemer_belege.json").write_text(json.dumps(belege, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    pfad = W / "kuratierung" / "eigentuemer.csv"
    alt = lies_csv(pfad) if pfad.exists() else []
    neu = aktualisiere_kuratierung(alt, vorschlag, datetime.date.today().isoformat())
    schreib_csv(pfad, neu, FELDER_KURATIERUNG)
    k = dict(koerperschaften=len(cluster), schreibweisen=len(koerper), personen=len(personen),
             pruefpflichtig=sum(1 for c in cluster if c["haeuser"] >= a.min_haeuser) + sum(1 for n in personen.values() if n >= a.min_haeuser),
             pruefpflichtig_koerperschaften=sum(1 for c in cluster if c["haeuser"] >= a.min_haeuser),
             haeuser_pruefpflichtig=sum(c["haeuser"] for c in cluster if c["haeuser"] >= a.min_haeuser),
             haeuser_koerperschaften=sum(koerper.values()), vorschlaege=sum(1 for c in cluster if c["vorschlag_fuer"]),
             kuratierung_zeilen=len(neu))
    print(json.dumps(k, ensure_ascii=False, indent=1))
    return k


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_eigentuemer_cluster.py tests/test_eigentuemer.py -q`
Expected: 12 passed

- [ ] **Step 5: Auf echten Daten laufen lassen und Zahlen notieren**

Run: `python3 werkzeuge/eigentuemer_cluster.py`
Expected: JSON mit `koerperschaften` (< 2261), `pruefpflichtig_koerperschaften` in der Größenordnung 100–160, `haeuser_pruefpflichtig` ≈ 3.900–4.500. Die Zahlen in die Commit-Nachricht schreiben. Stichprobe: `grep -c "" kuratierung/eigentuemer.csv` und die ersten 40 Zeilen von `build/eigentuemer_vorschlag.csv` ansehen — Krupp-Varianten müssen einen Cluster bilden; falls „Frau-Margarete-Krupp-Stiftung“ darin steckt, Schwelle nicht senken, sondern Befund in den Bericht schreiben (Spec: nur Sicheres).

- [ ] **Step 6: Commit** (inkl. der neuen `kuratierung/eigentuemer.csv`)

```bash
git add werkzeuge/eigentuemer_cluster.py tests/test_eigentuemer_cluster.py kuratierung/eigentuemer.csv
git commit -m "feat(eigentuemer): Skriptlauf — Vorschläge, Belege, Anlage/Aktualisierung von kuratierung/eigentuemer.csv mit Sperre; erster Lauf: <n> Cluster, <m> prüfpflichtig

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Server-Endpunkt `POST /kuratierung/eigentuemer.csv`

**Files:**
- Modify: `werkzeuge/serve.py:1-48` (Doku, Konstanten), `werkzeuge/serve.py:173-176` (`do_POST`), neue Methode `_eigentuemer`
- Modify: `tests/test_serve.py`

**Interfaces:**
- Consumes: `KATEGORIEN`, `FELDER_KURATIERUNG`, `lade_kuratierung` aus `pipeline.lib.eigentuemer`.
- Produces: `pruefe_eigentuemer(z: dict, bekannt: set[str]) -> str` (Fehlertext oder ""); `upsert_viele(pfad, zeilen, schluessel: str, felder) -> int`; Endpunkt nimmt `{"zeilen": [...]}`, setzt `bearbeiter="christos"`, `datum` = heute, antwortet `200 "eigentuemer.csv: n Zeilen"`.

- [ ] **Step 1: Failing tests anhängen**

```python
# tests/test_serve.py (anhängen; Fixture `server` um die Datei erweitern, siehe Step 3)
KOPF_EIGENTUEMER = "schreibweise,art,eigentuemer,kategorie,geprueft,bearbeiter,datum,hinweis"


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
```

In der Fixture `server` nach der `strassen_zuordnung.csv`-Zeile ergänzen:

```python
    (tmp_path / "kuratierung" / "eigentuemer.csv").write_text(
        KOPF_EIGENTUEMER + "\nStadt Essen,koerperschaft,Stadt Essen,stadt_staat,,eigentuemer_cluster,2026-09-22,\n"
        "Fried. Krupp A.G.,koerperschaft,Fried. Krupp AG,,,eigentuemer_cluster,2026-09-22,\n"
        "Fried. Krupp AG.,koerperschaft,Fried. Krupp AG,,,eigentuemer_cluster,2026-09-22,\n", encoding="utf-8")
```

(`KOPF_EIGENTUEMER` oberhalb der Fixture definieren.)

- [ ] **Step 2: Fehlschlag prüfen**

Run: `python3 -m pytest tests/test_serve.py -q`
Expected: 2 FAIL mit HTTP 404 „unbekanntes Ziel“ bzw. AssertionError

- [ ] **Step 3: Endpunkt implementieren**

In `werkzeuge/serve.py`:

Doku-Kopf (nach der Zeile zu `strassen_zuordnung.csv`) ergänzen:
```
- POST /kuratierung/eigentuemer.csv — mehrere Zeilen ({"zeilen": [...]}) der Eigentümer-Kuratierung;
  ersetzt nach Schlüssel `schreibweise`, setzt bearbeiter=christos und datum. 400 bei unbekannter
  Kategorie, leerem eigentuemer, geprueft ∉ {ja, leer} oder unbekannter Schreibweise.
```

Import ergänzen: `from pipeline.lib.eigentuemer import FELDER_KURATIERUNG, KATEGORIEN, lade_kuratierung` und `import datetime`.

Nach `loesche()` einfügen:

```python
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
```

In `do_POST` vor `k = _KURATIERUNG.match(self.path)`:
```python
        if self.path == "/kuratierung/eigentuemer.csv":
            return self._eigentuemer()
```

Neue Methode in `Handler` (vor `log_message`):
```python
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
```

`main()`-Ausgabe um `/werkzeuge/eigentuemer.html` ergänzen.

- [ ] **Step 4: Tests**

Run: `python3 -m pytest tests/test_serve.py -q`
Expected: alle bestehenden + 2 neue passed

- [ ] **Step 5: Commit**

```bash
git add werkzeuge/serve.py tests/test_serve.py
git commit -m "feat(eigentuemer): Endpunkt POST /kuratierung/eigentuemer.csv (Mehrfach-Upsert nach Schreibweise, Validierung)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Modell des Werkzeugs (reines Modul + node-Tests)

**Files:**
- Create: `werkzeuge/js/eigentuemer_modell.js`
- Create: `werkzeuge/tests/eigentuemer_modell.test.js`

**Interfaces:**
- Produces (alle Funktionen exportiert, Modell = `{ zeilen: Map<schreibweise, Zeile>, vorschlag: Map<schreibweise, VZeile>, verlauf: Array<Map> }`):
  - `baueModell(vorschlagZeilen: Array<object>, kuratierungZeilen: Array<object>) -> Modell` — Zeile = `{schreibweise, art, eigentuemer, kategorie, geprueft, hinweis, anzahl: number, cluster_id, pruefpflichtig: bool, verwaist: bool}`.
  - `eigentuemerListe(m) -> Array<{name, art, kategorie, haeuser, schreibweisen: Array<Zeile>, geprueft: bool, pruefpflichtig: bool, vorschlaege: Array<{zeile, aehnlichkeit}>}>` sortiert nach `haeuser` absteigend.
  - Aktionen geben `Array<Zeile>` (geänderte Zeilen zum Speichern) zurück und legen vorher einen Verlaufseintrag an: `setzeKategorie(m, name, kategorie)`, `benenne(m, alt, neu)`, `abspalten(m, schreibweise)`, `zusammenfuehren(m, quelle, ziel)`, `uebernehmeVorschlag(m, schreibweise, ziel)`, `setzeGeprueft(m, name, ja: bool)`, `setzeHinweis(m, name, text)`.
  - `rueckgaengig(m) -> Array<Zeile> | null` (stellt den letzten Verlaufseintrag her, liefert alle Zeilen, die sich dadurch ändern), `fortschritt(m) -> {geprueft, gesamt, haeuserGeprueft, haeuserGesamt}` (nur prüfpflichtige), `zumSpeichern(zeile) -> object` (nur CSV-Felder).

- [ ] **Step 1: Failing tests**

```js
// werkzeuge/tests/eigentuemer_modell.test.js
import test from "node:test";
import assert from "node:assert/strict";
import { abspalten, baueModell, benenne, eigentuemerListe, fortschritt, rueckgaengig, setzeGeprueft,
         setzeKategorie, uebernehmeVorschlag, zumSpeichern, zusammenfuehren } from "../js/eigentuemer_modell.js";

const V = [
  { schreibweise: "Fried. Krupp A.G.", art: "koerperschaft", anzahl: "6", cluster_id: "k1", cluster_name: "Fried. Krupp AG", aehnlichkeit: "1.0", vorschlag_fuer: "", pruefpflichtig: "ja" },
  { schreibweise: "Fried. Krupp AG.", art: "koerperschaft", anzahl: "1", cluster_id: "k1", cluster_name: "Fried. Krupp AG", aehnlichkeit: "1.0", vorschlag_fuer: "", pruefpflichtig: "ja" },
  { schreibweise: "Krupp Stiftung", art: "koerperschaft", anzahl: "2", cluster_id: "k2", cluster_name: "Krupp Stiftung", aehnlichkeit: "1.0", vorschlag_fuer: "k1", pruefpflichtig: "nein" },
  { schreibweise: "Stadt Essen", art: "koerperschaft", anzahl: "9", cluster_id: "s1", cluster_name: "Stadt Essen", aehnlichkeit: "1.0", vorschlag_fuer: "", pruefpflichtig: "ja" },
];
const K = [
  { schreibweise: "Fried. Krupp A.G.", art: "koerperschaft", eigentuemer: "Fried. Krupp AG", kategorie: "", geprueft: "", bearbeiter: "eigentuemer_cluster", datum: "", hinweis: "" },
  { schreibweise: "Fried. Krupp AG.", art: "koerperschaft", eigentuemer: "Fried. Krupp AG", kategorie: "", geprueft: "", bearbeiter: "eigentuemer_cluster", datum: "", hinweis: "" },
  { schreibweise: "Krupp Stiftung", art: "koerperschaft", eigentuemer: "Krupp Stiftung", kategorie: "", geprueft: "", bearbeiter: "eigentuemer_cluster", datum: "", hinweis: "" },
  { schreibweise: "Stadt Essen", art: "koerperschaft", eigentuemer: "Stadt Essen", kategorie: "stadt_staat", geprueft: "ja", bearbeiter: "christos", datum: "2026-09-22", hinweis: "" },
  { schreibweise: "Alt GmbH", art: "koerperschaft", eigentuemer: "Alt GmbH", kategorie: "", geprueft: "", bearbeiter: "eigentuemer_cluster", datum: "", hinweis: "" },
];
const frisch = () => baueModell(V, K);

test("baueModell und Liste", () => {
  const m = frisch();
  const l = eigentuemerListe(m);
  assert.deepEqual(l.map((e) => [e.name, e.haeuser, e.geprueft, e.pruefpflichtig]),
    [["Stadt Essen", 9, true, true], ["Fried. Krupp AG", 7, false, true], ["Krupp Stiftung", 2, false, false], ["Alt GmbH", 0, false, false]]);
  assert.equal(m.zeilen.get("Alt GmbH").verwaist, true);
  const krupp = l[1];
  assert.deepEqual(krupp.schreibweisen.map((z) => z.schreibweise), ["Fried. Krupp A.G.", "Fried. Krupp AG."]);
  assert.deepEqual(krupp.vorschlaege.map((v) => [v.zeile.schreibweise, v.aehnlichkeit]), [["Krupp Stiftung", 1.0]]);
  assert.deepEqual(fortschritt(m), { geprueft: 1, gesamt: 2, haeuserGeprueft: 9, haeuserGesamt: 16 });
});

test("Kategorie, Name, geprüft gelten für alle Schreibweisen", () => {
  const m = frisch();
  const g = setzeKategorie(m, "Fried. Krupp AG", "industrie");
  assert.deepEqual(g.map((z) => z.schreibweise), ["Fried. Krupp A.G.", "Fried. Krupp AG."]);
  assert.equal(m.zeilen.get("Fried. Krupp AG.").kategorie, "industrie");
  benenne(m, "Fried. Krupp AG", "Friedrich Krupp AG");
  assert.equal(eigentuemerListe(m)[1].name, "Friedrich Krupp AG");
  const p = setzeGeprueft(m, "Friedrich Krupp AG", true);
  assert.equal(p.length, 2);
  assert.deepEqual(fortschritt(m), { geprueft: 2, gesamt: 2, haeuserGeprueft: 16, haeuserGesamt: 16 });
  assert.deepEqual(zumSpeichern(m.zeilen.get("Fried. Krupp A.G.")),
    { schreibweise: "Fried. Krupp A.G.", art: "koerperschaft", eigentuemer: "Friedrich Krupp AG", kategorie: "industrie", geprueft: "ja", hinweis: "" });
});

test("abspalten, zusammenführen, Vorschlag übernehmen", () => {
  const m = frisch();
  const a = abspalten(m, "Fried. Krupp AG.");
  assert.deepEqual(a.map((z) => [z.schreibweise, z.eigentuemer, z.geprueft]), [["Fried. Krupp AG.", "Fried. Krupp AG.", ""]]);
  assert.equal(eigentuemerListe(m).length, 5);
  const z = zusammenfuehren(m, "Fried. Krupp AG.", "Fried. Krupp AG");
  assert.deepEqual(z.map((x) => x.eigentuemer), ["Fried. Krupp AG"]);
  setzeKategorie(m, "Fried. Krupp AG", "industrie");
  const u = uebernehmeVorschlag(m, "Krupp Stiftung", "Fried. Krupp AG");
  assert.deepEqual(u.map((x) => [x.schreibweise, x.eigentuemer, x.kategorie, x.geprueft]), [["Krupp Stiftung", "Fried. Krupp AG", "industrie", ""]]);
  assert.equal(eigentuemerListe(m)[1].haeuser, 9);
  // Zusammenführen hebt „geprüft“ des Ziels auf, weil sich sein Bestand geändert hat
  setzeGeprueft(m, "Fried. Krupp AG", true);
  abspalten(m, "Krupp Stiftung");
  assert.equal(eigentuemerListe(m).find((e) => e.name === "Fried. Krupp AG").geprueft, false);
});

test("rückgängig stellt den vorigen Stand her und liefert die geänderten Zeilen", () => {
  const m = frisch();
  setzeKategorie(m, "Fried. Krupp AG", "industrie");
  abspalten(m, "Fried. Krupp AG.");
  let r = rueckgaengig(m);
  assert.deepEqual(r.map((z) => [z.schreibweise, z.eigentuemer]), [["Fried. Krupp AG.", "Fried. Krupp AG"]]);
  r = rueckgaengig(m);
  assert.deepEqual(r.map((z) => z.kategorie), ["", ""]);
  assert.equal(rueckgaengig(m), null);
});
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `node --test werkzeuge/tests/`
Expected: FAIL mit `Cannot find module '../js/eigentuemer_modell.js'`

- [ ] **Step 3: Modul implementieren**

```js
// werkzeuge/js/eigentuemer_modell.js
// Zustand des Eigentümer-Werkzeugs (Spec §5): eine Zeile je Schreibweise; ein „Eigentümer“ ist die Menge
// der Zeilen mit gleichem eigentuemer-Wert. Aktionen liefern die geänderten Zeilen zum Speichern.
const CSV_FELDER = ["schreibweise", "art", "eigentuemer", "kategorie", "geprueft", "hinweis"];
const VERLAUF_MAX = 20;

export function baueModell(vorschlagZeilen, kuratierungZeilen) {
  const vorschlag = new Map(vorschlagZeilen.map((v) => [v.schreibweise.trim(), v]));
  const zeilen = new Map();
  for (const k of kuratierungZeilen) {
    const s = k.schreibweise.trim();
    const v = vorschlag.get(s);
    zeilen.set(s, { schreibweise: s, art: k.art || (v && v.art) || "", eigentuemer: (k.eigentuemer || "").trim() || s,
      kategorie: k.kategorie || "", geprueft: k.geprueft || "", hinweis: k.hinweis || "",
      anzahl: v ? Number(v.anzahl) : 0, cluster_id: v ? v.cluster_id : "", pruefpflichtig: !!v && v.pruefpflichtig === "ja", verwaist: !v });
  }
  return { zeilen, vorschlag, verlauf: [] };
}

function gruppen(m) {
  const g = new Map();
  for (const z of m.zeilen.values()) {
    if (!g.has(z.eigentuemer)) g.set(z.eigentuemer, []);
    g.get(z.eigentuemer).push(z);
  }
  return g;
}

export function eigentuemerListe(m) {
  const g = gruppen(m);
  const idsVon = new Map([...g].map(([name, zs]) => [name, new Set(zs.map((z) => z.cluster_id))]));
  const liste = [...g].map(([name, zs]) => {
    zs.sort((a, b) => b.anzahl - a.anzahl || a.schreibweise.localeCompare(b.schreibweise, "de"));
    const ids = idsVon.get(name);
    const vorschlaege = [];
    for (const z of m.zeilen.values()) {
      const v = m.vorschlag.get(z.schreibweise);
      if (z.eigentuemer !== name && v && v.vorschlag_fuer && ids.has(v.vorschlag_fuer)) vorschlaege.push({ zeile: z, aehnlichkeit: Number(v.aehnlichkeit) });
    }
    vorschlaege.sort((a, b) => b.aehnlichkeit - a.aehnlichkeit || b.zeile.anzahl - a.zeile.anzahl);
    return { name, art: zs[0].art, kategorie: zs[0].kategorie, haeuser: zs.reduce((s, z) => s + z.anzahl, 0), schreibweisen: zs,
      geprueft: zs.every((z) => z.geprueft === "ja"), pruefpflichtig: zs.some((z) => z.pruefpflichtig), vorschlaege };
  });
  return liste.sort((a, b) => b.haeuser - a.haeuser || a.name.localeCompare(b.name, "de"));
}

function merke(m) {
  m.verlauf.push(new Map([...m.zeilen].map(([k, z]) => [k, { ...z }])));
  if (m.verlauf.length > VERLAUF_MAX) m.verlauf.shift();
}

function zeilenVon(m, name) { return [...m.zeilen.values()].filter((z) => z.eigentuemer === name); }

// Bestand eines Eigentümers hat sich geändert → nicht mehr „geprüft“ (der Mensch sieht ihn noch einmal an)
function entpruefe(zs) { for (const z of zs) z.geprueft = ""; return zs; }

export function setzeKategorie(m, name, kategorie) {
  merke(m);
  const zs = zeilenVon(m, name);
  for (const z of zs) z.kategorie = kategorie;
  return zs;
}

export function benenne(m, alt, neu) {
  neu = neu.trim();
  if (!neu || neu === alt) return [];
  merke(m);
  const zs = zeilenVon(m, alt);
  for (const z of zs) z.eigentuemer = neu;
  return zs;
}

export function setzeGeprueft(m, name, ja) {
  merke(m);
  const zs = zeilenVon(m, name);
  for (const z of zs) z.geprueft = ja ? "ja" : "";
  return zs;
}

export function setzeHinweis(m, name, text) {
  merke(m);
  const zs = zeilenVon(m, name);
  for (const z of zs) z.hinweis = text;
  return zs;
}

export function abspalten(m, schreibweise) {
  const z = m.zeilen.get(schreibweise);
  if (!z) return [];
  merke(m);
  const rest = zeilenVon(m, z.eigentuemer).filter((x) => x !== z);
  z.eigentuemer = schreibweise; z.geprueft = ""; z.kategorie = z.art === "person" ? "privatperson" : "";
  return [z, ...entpruefe(rest)];
}

export function zusammenfuehren(m, quelle, ziel) {
  if (quelle === ziel) return [];
  const zielZeilen = zeilenVon(m, ziel);
  if (!zielZeilen.length) return [];
  merke(m);
  const kat = zielZeilen[0].kategorie;
  const zs = zeilenVon(m, quelle);
  for (const z of zs) { z.eigentuemer = ziel; z.kategorie = kat; z.geprueft = ""; }
  return [...zs, ...entpruefe(zielZeilen)];
}

export function uebernehmeVorschlag(m, schreibweise, ziel) {
  const z = m.zeilen.get(schreibweise);
  if (!z) return [];
  return zusammenfuehren(m, z.eigentuemer, ziel).filter((x) => x === z || x.eigentuemer === ziel);
}

export function rueckgaengig(m) {
  const alt = m.verlauf.pop();
  if (!alt) return null;
  const geaendert = [];
  for (const [k, z] of alt) {
    const jetzt = m.zeilen.get(k);
    if (!jetzt || CSV_FELDER.some((f) => jetzt[f] !== z[f])) { m.zeilen.set(k, z); geaendert.push(z); }
  }
  return geaendert;
}

export function fortschritt(m) {
  const l = eigentuemerListe(m).filter((e) => e.pruefpflichtig);
  return { geprueft: l.filter((e) => e.geprueft).length, gesamt: l.length,
    haeuserGeprueft: l.filter((e) => e.geprueft).reduce((s, e) => s + e.haeuser, 0), haeuserGesamt: l.reduce((s, e) => s + e.haeuser, 0) };
}

export function zumSpeichern(z) { return Object.fromEntries(CSV_FELDER.map((f) => [f, z[f]])); }
```

- [ ] **Step 4: Tests**

Run: `node --test werkzeuge/tests/`
Expected: 4 passed. Hinweis zu `uebernehmeVorschlag`: liefert die Vorschlagszeile plus die entprüften Zielzeilen; im Test steht nur die Vorschlagszeile, weil das Ziel dort noch ungeprüft ist und `entpruefe` nichts ändert — trotzdem werden Zielzeilen zurückgegeben (Speichern ist idempotent). Falls der Test deshalb scheitert: Erwartung im Test auf `u.filter((x) => x.schreibweise === "Krupp Stiftung")` einschränken.

- [ ] **Step 5: Commit**

```bash
git add werkzeuge/js/eigentuemer_modell.js werkzeuge/tests/eigentuemer_modell.test.js
git commit -m "feat(eigentuemer): Modell des Werkzeugs (Liste, Aktionen, Rückgängig, Fortschritt) mit node-Tests

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Oberfläche `werkzeuge/eigentuemer.html`

**Files:**
- Create: `werkzeuge/eigentuemer.html`

**Interfaces:**
- Consumes: Modell aus Task 6; Endpunkt aus Task 5; Dateien `../build/eigentuemer_vorschlag.csv`, `../build/eigentuemer_belege.json`, `../kuratierung/eigentuemer.csv`; `KATEGORIEN` (im HTML dupliziert als Konstante, Reihenfolge wie `pipeline/lib/eigentuemer.py`).

- [ ] **Step 1: Seite schreiben**

```html
<!doctype html>
<html lang="de"><head><meta charset="utf-8"><title>Eigentümer-Kuratierung</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="anonymous">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin="anonymous"></script>
<!-- SRI-Hashes = offizielle Angaben von leafletjs.com für 1.9.4; lädt Leaflet nicht (Konsole: integrity), Hash gegen unpkg prüfen -->
<style>
  body { margin: 0; font: 14px system-ui, sans-serif; color: #1f2937; display: grid; grid-template-columns: 380px 1fr; height: 100vh; }
  #links { border-right: 1px solid #ddd; display: flex; flex-direction: column; min-height: 0; }
  #links .kopf { padding: 10px 12px; border-bottom: 1px solid #eee; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
  #links input[type=search] { flex: 1 1 100%; padding: 6px; }
  #liste { overflow: auto; flex: 1; }
  .ez { padding: 6px 12px; border-bottom: 1px solid #f1f1f1; cursor: pointer; display: flex; gap: 8px; align-items: center; }
  .ez.aktiv { background: #eef2ff; } .ez.geprueft { color: #6b7280; }
  .punkt { width: 10px; height: 10px; border-radius: 50%; background: #d1d5db; flex: none; }
  .ez b { flex: 1; font-weight: 500; } .ez small { color: #6b7280; }
  #rechts { display: grid; grid-template-rows: auto auto 1fr; min-height: 0; }
  #kopf { padding: 12px 16px; border-bottom: 1px solid #eee; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  #name { font-size: 18px; font-weight: 600; padding: 4px 6px; border: 1px solid #ddd; border-radius: 6px; min-width: 320px; }
  .kats button { margin: 0 2px; } .kats button[aria-pressed=true] { background: #1d4ed8; color: #fff; }
  #mitte { padding: 12px 16px; overflow: auto; border-bottom: 1px solid #eee; display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  #unten { display: grid; grid-template-columns: 1fr 1fr; min-height: 0; }
  #belege { overflow: auto; padding: 8px 16px; } #karte { min-height: 200px; }
  table { border-collapse: collapse; width: 100%; } td, th { padding: 3px 6px; border-bottom: 1px solid #f1f1f1; text-align: left; font-size: 13px; }
  .sw { display: flex; gap: 6px; align-items: center; padding: 2px 0; } .sw span { flex: 1; } .sw small { color: #6b7280; }
  .sw button, .vs button { font-size: 12px; }
  #banner { position: fixed; bottom: 12px; right: 12px; background: #b91c1c; color: #fff; padding: 8px 12px; border-radius: 6px; display: none; }
  #zusammen { width: 100%; padding: 6px; } #zusammen-liste div { padding: 3px 6px; cursor: pointer; } #zusammen-liste div:hover { background: #eef2ff; }
  kbd { border: 1px solid #ccc; border-radius: 3px; padding: 0 4px; font-size: 11px; }
</style></head>
<body>
<div id="links">
  <div class="kopf">
    <input type="search" id="filter" placeholder="Eigentümer suchen …">
    <label><input type="radio" name="status" value="offen" checked> offen</label>
    <label><input type="radio" name="status" value="geprueft"> geprüft</label>
    <label><input type="radio" name="status" value="alle"> alle</label>
    <label><input type="checkbox" id="nur-pflicht" checked> nur ≥ Untergrenze</label>
    <select id="art"><option value="">Körperschaften + Personen</option><option value="koerperschaft">Körperschaften</option><option value="person">Personen</option></select>
    <div id="fortschritt" style="flex-basis:100%;color:#6b7280"></div>
  </div>
  <div id="liste"></div>
</div>
<div id="rechts">
  <div id="kopf">
    <input id="name" title="Name ändern (Enter)">
    <span id="haeuser"></span>
    <span class="kats" id="kats"></span>
    <button id="geprueft" title="Taste G">Geprüft <kbd>G</kbd></button>
    <button id="rueck" title="Taste Z">Rückgängig <kbd>Z</kbd></button>
    <input id="hinweis" placeholder="Hinweis" style="flex:1 1 200px">
  </div>
  <div id="mitte">
    <div><h4 style="margin:0 0 6px">Schreibweisen</h4><div id="schreibweisen"></div>
      <h4 style="margin:12px 0 6px">Gehört vielleicht dazu</h4><div id="vorschlaege" class="vs"></div></div>
    <div><h4 style="margin:0 0 6px">Zusammenführen mit …</h4><input id="zusammen" placeholder="anderen Eigentümer suchen"><div id="zusammen-liste"></div></div>
  </div>
  <div id="unten"><div id="belege"></div><div id="karte"></div></div>
</div>
<div id="banner"></div>
<script type="module">
import { abspalten, baueModell, benenne, eigentuemerListe, fortschritt, rueckgaengig, setzeGeprueft, setzeHinweis,
         setzeKategorie, uebernehmeVorschlag, zumSpeichern, zusammenfuehren } from "./js/eigentuemer_modell.js";

const KATEGORIEN = { stadt_staat: "Stadt/Staat/Reich", bergbau: "Bergbau", industrie: "Industrie", genossenschaft_siedlung: "Genossenschaft/Siedlung",
  kirche_stiftung: "Kirche/Stiftung", bank_versicherung: "Bank/Versicherung", privatperson: "Privatperson", sonstige: "Sonstige" };
const FARBEN = { stadt_staat: "#1d4ed8", bergbau: "#111827", industrie: "#b91c1c", genossenschaft_siedlung: "#15803d", kirche_stiftung: "#7c3aed",
  bank_versicherung: "#0e7490", privatperson: "#d97706", sonstige: "#6b7280" };
const DIGIBIB = "https://www.digibib.genealogy.net/viewer/image/857439804_1936/";
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// CSV-Leser für RFC-4180 (Anführungszeichen, Kommas in Feldern, \n in Feldern)
function csvLesen(text) {
  const zeilen = []; let feld = "", zeile = [], q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { feld += '"'; i++; } else q = false; } else feld += c; }
    else if (c === '"') q = true;
    else if (c === ",") { zeile.push(feld); feld = ""; }
    else if (c === "\n") { zeile.push(feld); zeilen.push(zeile); zeile = []; feld = ""; }
    else if (c !== "\r") feld += c;
  }
  if (feld || zeile.length) { zeile.push(feld); zeilen.push(zeile); }
  const kopf = zeilen.shift();
  return zeilen.filter((z) => z.length > 1 || z[0]).map((z) => Object.fromEntries(kopf.map((k, i) => [k, z[i] ?? ""])));
}

const [vText, kText, belege] = await Promise.all([
  fetch("../build/eigentuemer_vorschlag.csv").then((r) => { if (!r.ok) throw new Error("build/eigentuemer_vorschlag.csv fehlt — zuerst werkzeuge/eigentuemer_cluster.py ausführen"); return r.text(); }),
  fetch("../kuratierung/eigentuemer.csv").then((r) => { if (!r.ok) throw new Error("kuratierung/eigentuemer.csv fehlt"); return r.text(); }),
  fetch("../build/eigentuemer_belege.json").then((r) => r.ok ? r.json() : {}),
]).catch((e) => { zeigeBanner(e.message); throw e; });
const m = baueModell(csvLesen(vText), csvLesen(kText));
let aktiv = null;   // Name des aktiven Eigentümers
const karte = L.map("karte").setView([51.455, 7.01], 11);
L.tileLayer("https://tiles.openfreemap.org/styles/positron/512/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap, OpenFreeMap" }).addTo(karte);
let marker = L.layerGroup().addTo(karte);

function zeigeBanner(text) { const b = document.getElementById("banner"); b.textContent = text; b.style.display = "block"; setTimeout(() => (b.style.display = "none"), 6000); }

async function speichere(zeilen) {
  if (!zeilen.length) return;
  const r = await fetch("/kuratierung/eigentuemer.csv", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ zeilen: zeilen.map(zumSpeichern) }) });
  if (!r.ok) { zeigeBanner("Speichern fehlgeschlagen: " + (await r.text())); const z = rueckgaengig(m); if (z) zeichne(); }
}

function gefiltert() {
  const status = document.querySelector("input[name=status]:checked").value;
  const nurPflicht = document.getElementById("nur-pflicht").checked;
  const art = document.getElementById("art").value;
  const q = document.getElementById("filter").value.trim().toLowerCase();
  return eigentuemerListe(m).filter((e) => (status === "alle" || (status === "geprueft") === e.geprueft) && (!nurPflicht || e.pruefpflichtig)
    && (!art || e.art === art) && (!q || e.name.toLowerCase().includes(q) || e.schreibweisen.some((z) => z.schreibweise.toLowerCase().includes(q))));
}

function zeichneListe() {
  const l = gefiltert();
  document.getElementById("liste").innerHTML = l.map((e) => `<div class="ez${e.name === aktiv ? " aktiv" : ""}${e.geprueft ? " geprueft" : ""}" data-name="${esc(e.name)}">` +
    `<span class="punkt" style="background:${FARBEN[e.kategorie] || "#d1d5db"}"></span><b>${esc(e.name)}</b><small>${e.haeuser} H · ${e.schreibweisen.length} S</small></div>`).join("");
  const f = fortschritt(m);
  document.getElementById("fortschritt").textContent = `${f.geprueft} von ${f.gesamt} geprüft · ${f.haeuserGeprueft.toLocaleString("de-DE")} von ${f.haeuserGesamt.toLocaleString("de-DE")} Häusern`;
}

function zeichneAktiv() {
  const e = eigentuemerListe(m).find((x) => x.name === aktiv);
  if (!e) { document.getElementById("kopf").style.visibility = "hidden"; return; }
  document.getElementById("kopf").style.visibility = "visible";
  document.getElementById("name").value = e.name;
  document.getElementById("haeuser").textContent = `${e.haeuser} Häuser · ${e.art === "person" ? "Person" : "Körperschaft"}${e.geprueft ? " · geprüft" : ""}`;
  document.getElementById("hinweis").value = e.schreibweisen[0].hinweis;
  document.getElementById("kats").innerHTML = Object.entries(KATEGORIEN).map(([k, t], i) => `<button data-kat="${k}" aria-pressed="${e.kategorie === k}">${i + 1} ${esc(t)}</button>`).join("");
  document.getElementById("schreibweisen").innerHTML = e.art === "person" ? `<small>${esc(e.name)} · ${e.haeuser} Häuser</small>` :
    e.schreibweisen.map((z) => `<div class="sw"><span>${esc(z.schreibweise)}${z.verwaist ? " <small>(verwaist)</small>" : ""}</span><small>${z.anzahl}</small>` +
      (e.schreibweisen.length > 1 ? `<button data-ab="${esc(z.schreibweise)}" title="abspalten">×</button>` : "") + `</div>`).join("");
  document.getElementById("vorschlaege").innerHTML = e.vorschlaege.length ? e.vorschlaege.map((v) =>
    `<div class="sw"><span>${esc(v.zeile.schreibweise)} <small>(jetzt: ${esc(v.zeile.eigentuemer)})</small></span><small>${v.zeile.anzahl} · ${v.aehnlichkeit.toFixed(2)}</small><button data-plus="${esc(v.zeile.schreibweise)}">+</button></div>`).join("") : "<small>keine</small>";
  // Belege
  const b = e.schreibweisen.flatMap((z) => (belege[z.schreibweise] || []).map((h) => ({ ...h, sw: z.schreibweise })));
  document.getElementById("belege").innerHTML = `<table><tr><th>Adresse</th><th>Stadtteil</th><th>Verwalter</th><th>Schreibweise</th><th>Seite</th></tr>` +
    b.slice(0, 400).map((h) => `<tr><td>${esc(h.adresse)}</td><td>${esc(h.stadtteil)}</td><td>${esc(h.verwalter)}</td><td>${esc(h.sw)}</td><td><a href="${DIGIBIB}" target="_blank" rel="noopener">${esc(h.seite)}</a></td></tr>`).join("") +
    (b.length > 400 ? `<tr><td colspan="5">… ${b.length - 400} weitere</td></tr>` : "") + `</table>`;
  marker.clearLayers();
  const punkte = b.filter((h) => h.lat != null && h.lon != null);
  for (const h of punkte) L.circleMarker([h.lat, h.lon], { radius: 4, color: FARBEN[e.kategorie] || "#1d4ed8", fillOpacity: .7, weight: 1 }).bindTooltip(h.adresse).addTo(marker);
  if (punkte.length) karte.fitBounds(L.latLngBounds(punkte.map((h) => [h.lat, h.lon])).pad(0.2), { maxZoom: 15 });
  zeichneZusammen();
}

function zeichneZusammen() {
  const q = document.getElementById("zusammen").value.trim().toLowerCase();
  const el = document.getElementById("zusammen-liste");
  if (!q || !aktiv) { el.innerHTML = ""; return; }
  const l = eigentuemerListe(m).filter((e) => e.name !== aktiv && e.name.toLowerCase().includes(q)).slice(0, 12);
  el.innerHTML = l.map((e) => `<div data-ziel="${esc(e.name)}">${esc(e.name)} <small>${e.haeuser} H · ${esc(KATEGORIEN[e.kategorie] || "ohne Kategorie")}</small></div>`).join("");
}

function zeichne() { zeichneListe(); zeichneAktiv(); }

function waehle(name) { aktiv = name; document.getElementById("zusammen").value = ""; zeichne(); }

function naechsterOffener() {
  const l = gefiltert();
  const i = l.findIndex((e) => e.name === aktiv);
  const n = l.slice(i + 1).find((e) => !e.geprueft) || l.find((e) => !e.geprueft);
  if (n) waehle(n.name); else zeichne();
}

// Ereignisse
document.getElementById("liste").addEventListener("click", (ev) => { const z = ev.target.closest("[data-name]"); if (z) waehle(z.dataset.name); });
for (const id of ["filter", "nur-pflicht", "art"]) document.getElementById(id).addEventListener("input", zeichneListe);
document.querySelectorAll("input[name=status]").forEach((r) => r.addEventListener("change", zeichneListe));
document.getElementById("kats").addEventListener("click", (ev) => { const b = ev.target.closest("[data-kat]"); if (b) { speichere(setzeKategorie(m, aktiv, b.dataset.kat)); zeichne(); } });
document.getElementById("name").addEventListener("keydown", (ev) => { if (ev.key === "Enter") { const neu = ev.target.value; const g = benenne(m, aktiv, neu); if (g.length) { aktiv = neu.trim(); speichere(g); zeichne(); } } });
document.getElementById("hinweis").addEventListener("change", (ev) => speichere(setzeHinweis(m, aktiv, ev.target.value)));
document.getElementById("geprueft").addEventListener("click", () => { const e = eigentuemerListe(m).find((x) => x.name === aktiv); speichere(setzeGeprueft(m, aktiv, !e.geprueft)); if (!e.geprueft) naechsterOffener(); else zeichne(); });
document.getElementById("rueck").addEventListener("click", () => { const z = rueckgaengig(m); if (z) { speichere(z); if (!eigentuemerListe(m).some((e) => e.name === aktiv)) aktiv = z[0]?.eigentuemer || null; zeichne(); } });
document.getElementById("schreibweisen").addEventListener("click", (ev) => { const b = ev.target.closest("[data-ab]"); if (b) { speichere(abspalten(m, b.dataset.ab)); zeichne(); } });
document.getElementById("vorschlaege").addEventListener("click", (ev) => { const b = ev.target.closest("[data-plus]"); if (b) { speichere(uebernehmeVorschlag(m, b.dataset.plus, aktiv)); zeichne(); } });
document.getElementById("zusammen").addEventListener("input", zeichneZusammen);
document.getElementById("zusammen-liste").addEventListener("click", (ev) => { const z = ev.target.closest("[data-ziel]"); if (z) { const ziel = z.dataset.ziel; speichere(zusammenfuehren(m, aktiv, ziel)); waehle(ziel); } });
document.addEventListener("keydown", (ev) => {
  if (ev.target.matches("input, select, textarea")) return;
  const k = Object.keys(KATEGORIEN)[Number(ev.key) - 1];
  if (k && aktiv) { speichere(setzeKategorie(m, aktiv, k)); zeichne(); }
  else if (ev.key.toLowerCase() === "g" && aktiv) document.getElementById("geprueft").click();
  else if (ev.key.toLowerCase() === "z") document.getElementById("rueck").click();
});

const erster = gefiltert()[0];
if (erster) waehle(erster.name); else zeichne();
</script>
</body></html>
```

- [ ] **Step 2: Manuell prüfen**

Server läuft (`python3 werkzeuge/serve.py 8765`). `http://localhost:8765/werkzeuge/eigentuemer.html` öffnen (im VS-Code-Browser oder extern). Prüfen: Liste zeigt prüfpflichtige Eigentümer nach Häusern; Klick auf „Stadt Essen“ → Belege und Karte; Taste `1` → Kategorie gesetzt, `kuratierung/eigentuemer.csv` per `git diff --stat` verändert (nur die Zeilen des Eigentümers, `bearbeiter=christos`); `G` → geprüft, Sprung zum nächsten; `Z` → rückgängig. Bei Krupp eine Schreibweise mit `×` abspalten und über „Zusammenführen mit …“ wieder anhängen.

Automatisierter Rauchtest mit Playwright (im Scratchpad, nicht versioniert), falls kein Browser zur Hand:
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); s = b.new_page(viewport={"width": 1400, "height": 900})
    fehler = []; s.on("pageerror", lambda e: fehler.append(str(e)))
    s.goto("http://localhost:8765/werkzeuge/eigentuemer.html"); s.wait_for_selector(".ez")
    print(s.locator("#fortschritt").inner_text()); print(fehler)
    s.screenshot(path="eigentuemer.png"); b.close()
```
Erwartung: keine `pageerror`, Fortschrittszeile mit Zahlen.

- [ ] **Step 3: Nach der Probe die Teständerungen in `kuratierung/eigentuemer.csv` zurücknehmen**

Run: `git checkout kuratierung/eigentuemer.csv` (Probe-Klicks nicht committen; der Nutzer kuratiert selbst).

- [ ] **Step 4: Commit**

```bash
git add werkzeuge/eigentuemer.html
git commit -m "feat(eigentuemer): Browser-Werkzeug zur Kuratierung (Liste, Kategorie-Tasten, Abspalten, Zusammenführen, Vorschläge, Belege mit Karte, Speichern über serve.py)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Export — Zuordnung, `besitz`, Eigentümerindex, Kennzahlen, Thema

**Files:**
- Modify: `pipeline/lib/karte_export.py:70-120` (`gruppiere`, `punkt_feature`, `eintrag_kurz`), neue Funktionen `baue_eigentuemerindex`, Anpassung `baue_kennzahlen`, `schreibe_paket`
- Modify: `pipeline/06_karte_export.py:22-31`
- Create: `kuratierung/themen/besitz.json`
- Modify: `tests/test_karte_export.py`

**Interfaces:**
- Consumes: `lade_kuratierung`, `schreibweise_von` aus `pipeline.lib.eigentuemer`.
- Produces: `gruppiere(eintraege, regeln, eigentuemer: dict[str, dict] | None = None)` hängt an Teil-II-Einträge `_eigentuemer` (kanonisch, "" wenn ungeprüft), `_kategorie` ("" wenn ungeprüft) an; Adresse bekommt `besitz` (Kategorie | `gemischt` | `ungeprueft`); `punkt_feature` schreibt `besitz`; `eintrag_kurz` liefert zusätzlich `eigentuemer_kanon`, `kategorie`; `baue_eigentuemerindex(adressen) -> tuple[list[list], dict[str, dict[str, list[list]]]]` (Liste `[schluessel, name, haeuser, kategorie]` nach Häusern absteigend; Scherben `praefix2(name)` → name → `[[adress_id, n]]`); `baue_kennzahlen` ergänzt `besitz_geprueft` (Adressen mit `besitz` ∉ {ungeprueft}) und `eigentuemer_geprueft` (Zahl der kanonischen Namen); `schreibe_paket(..., eigentuemer: list[dict] | None = None)`.

- [ ] **Step 1: Failing tests anhängen**

```python
# tests/test_karte_export.py (anhängen)
from pipeline.lib.karte_export import baue_eigentuemerindex, baue_kennzahlen, schreibe_paket


def _kur(**k):
    z = dict(schreibweise="", art="koerperschaft", eigentuemer="", kategorie="", geprueft="", bearbeiter="christos", datum="", hinweis="")
    z.update(k); return z


EIG = [_kur(schreibweise="Fried. Krupp A.G.", eigentuemer="Fried. Krupp AG", kategorie="industrie", geprueft="ja"),
       _kur(schreibweise="Fried. Krupp AG.", eigentuemer="Fried. Krupp AG", kategorie="industrie", geprueft="ja"),
       _kur(schreibweise="Stadt Essen", eigentuemer="Stadt Essen", kategorie="stadt_staat", geprueft="ja"),
       _kur(schreibweise="Bauverein GmbH", eigentuemer="Bauverein GmbH", kategorie="genossenschaft_siedlung", geprueft="")]  # ungeprüft


def test_gruppiere_besitz():
    from pipeline.lib.eigentuemer import lade_kuratierung
    e = [_v(id="1", teil="II", hausnr="1", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="2", teil="II", hausnr="1", **{"Firmenname": "Fried. Krupp AG."}),            # gleiche Adresse, gleicher Eigentümer
         _v(id="3", teil="II", hausnr="2", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="4", teil="II", hausnr="2", **{"Firmenname": "Stadt Essen"}),                 # zwei Kategorien → gemischt
         _v(id="5", teil="II", hausnr="3", **{"Firmenname": "Bauverein GmbH"}),              # ungeprüft
         _v(id="6", teil="II", hausnr="4", lastname="Schmidt", firstname="Wilh."),            # nicht in der Tabelle
         _v(id="7", teil="I", hausnr="4")]
    a = gruppiere(e, [], lade_kuratierung(EIG))
    by = {x["hausnr"]: x for x in a.values()}
    assert by["1"]["besitz"] == "industrie" and by["2"]["besitz"] == "gemischt"
    assert by["3"]["besitz"] == "ungeprueft" and by["4"]["besitz"] == "ungeprueft"
    k = eintrag_kurz(by["1"]["eintraege"][0], [])
    assert k["eigentuemer_kanon"] == "Fried. Krupp AG" and k["kategorie"] == "industrie"
    assert eintrag_kurz(by["3"]["eintraege"][0], [])["eigentuemer_kanon"] == ""
    assert eintrag_kurz(by["4"]["eintraege"][1], [])["kategorie"] == ""           # Teil I: nie
    assert punkt_feature(by["2"])["properties"]["besitz"] == "gemischt"
    # ohne Tabelle: alles ungeprüft
    assert all(x["besitz"] == "ungeprueft" for x in gruppiere(e, []).values())


def test_eigentuemerindex_und_kennzahlen():
    from pipeline.lib.eigentuemer import lade_kuratierung
    e = [_v(id="1", teil="II", hausnr="1", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="2", teil="II", hausnr="2", **{"Firmenname": "Fried. Krupp AG."}),
         _v(id="3", teil="II", hausnr="2", **{"Firmenname": "Fried. Krupp AG."}),
         _v(id="4", teil="II", hausnr="3", **{"Firmenname": "Stadt Essen"}),
         _v(id="5", teil="II", hausnr="4", **{"Firmenname": "Bauverein GmbH"})]
    a = gruppiere(e, [], lade_kuratierung(EIG))
    liste, scherben = baue_eigentuemerindex(a)
    assert liste == [["fried krupp ag", "Fried. Krupp AG", 2, "industrie"], ["stadt essen", "Stadt Essen", 1, "stadt_staat"]]
    ids = {x["hausnr"]: x["id"] for x in a.values()}
    assert scherben["fr"]["Fried. Krupp AG"] == sorted([[ids["1"], 1], [ids["2"], 2]])
    assert "Bauverein GmbH" not in str(scherben)
    kz = baue_kennzahlen(e, a, "2026-09-22")
    assert kz["besitz_geprueft"] == 3 and kz["eigentuemer_geprueft"] == 2


def test_schreibe_paket_mit_eigentuemer(tmp_path):
    e = [_v(id="1", teil="II", hausnr="1", **{"Firmenname": "Stadt Essen"})]
    schreibe_paket(tmp_path, e, [], [], "2026-09-22", kacheln=False, eigentuemer=EIG)
    assert json.loads((tmp_path / "suche" / "eigentuemer.json").read_text(encoding="utf-8")) == [["stadt essen", "Stadt Essen", 1, "stadt_staat"]]
    assert (tmp_path / "suche" / "eigentuemer" / "st.json").exists()
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: FAIL mit `ImportError: cannot import name 'baue_eigentuemerindex'`

- [ ] **Step 3: Export implementieren**

In `pipeline/lib/karte_export.py`:

Import ergänzen: `from pipeline.lib.eigentuemer import schreibweise_von`.

`gruppiere` ersetzen durch:
```python
def _besitz(eintraege: list[dict]) -> str:
    kats = {e["_kategorie"] for e in eintraege if e.get("teil") == "II" and e.get("_kategorie")}
    if not kats:
        return "ungeprueft"
    return kats.pop() if len(kats) == 1 else "gemischt"


def gruppiere(eintraege: list[dict], regeln: list[Regel], eigentuemer: dict[str, dict] | None = None) -> dict[str, dict]:
    """Verortete Einträge je Adresse bündeln; Einträge sortiert, Merkmale und (Teil II) geprüfter
    Eigentümer angehängt; `besitz` je Adresse = Kategorie | gemischt | ungeprueft (Spec §6.1)."""
    gruppen: dict[str, dict] = {}
    eigentuemer = eigentuemer or {}
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
        kanon, kat = "", ""
        if e.get("teil") == "II":
            s, _ = schreibweise_von(e)
            z = eigentuemer.get(s)
            if z and z.get("geprueft") == "ja" and z.get("kategorie"):
                kanon, kat = z["eigentuemer"], z["kategorie"]
        e = dict(e, _merkmale=merkmale_fuer(e, regeln), _eigentuemer=kanon, _kategorie=kat)
        a["eintraege"].append(e)
    for a in gruppen.values():
        a["eintraege"] = sortiere_eintraege(a["eintraege"])
        a["besitz"] = _besitz(a["eintraege"])
    return gruppen
```

In `punkt_feature`: `nummer_unsicher=a["nummer_unsicher"], besitz=a.get("besitz", "ungeprueft"), n_I=0, ...`.

In `eintrag_kurz`: nach `wohnort=...` ergänzen `eigentuemer_kanon=e.get("_eigentuemer", ""), kategorie=e.get("_kategorie", ""),`.

Nach `baue_berufsindex` einfügen:
```python
def baue_eigentuemerindex(adressen: dict[str, dict]) -> tuple[list[list], dict[str, dict[str, list[list]]]]:
    """Eigentümerindex (nur geprüfte, Spec §6.4): (Liste [Schlüssel, Name, Häuser, Kategorie] nach Häusern
    absteigend, Scherbe praefix2(Name) → Name → [[Adress-ID, Zähler]])."""
    zaehler: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    kategorie: dict[str, str] = {}
    for a in adressen.values():
        for e in a["eintraege"]:
            if e.get("_eigentuemer"):
                zaehler[e["_eigentuemer"]][a["id"]] += 1
                kategorie[e["_eigentuemer"]] = e["_kategorie"]
    liste = sorted([[falte(n), n, len(z), kategorie[n]] for n, z in zaehler.items()], key=lambda x: (-x[2], x[0]))
    scherben: dict[str, dict[str, list[list]]] = defaultdict(dict)
    for n, z in zaehler.items():
        scherben[praefix2(n)][n] = sorted([[aid, k] for aid, k in z.items()])
    return liste, dict(scherben)
```

In `baue_kennzahlen` das `return dict(...)` ergänzen um:
```python
                besitz_geprueft=sum(1 for a in adressen.values() if a.get("besitz", "ungeprueft") != "ungeprueft"),
                eigentuemer_geprueft=len({e["_eigentuemer"] for a in adressen.values() for e in a["eintraege"] if e.get("_eigentuemer")}),
```

`schreibe_paket`: Signatur um `eigentuemer: list[dict] | None = None` erweitern; `adressen = gruppiere(eintraege, regeln, lade_kuratierung(eigentuemer or []))` (Import `lade_kuratierung` ergänzen); nach dem Berufsindex:
```python
    liste, scherben = baue_eigentuemerindex(adressen)
    _json(ausgabe / "suche" / "eigentuemer.json", liste)
    for name, inhalt in scherben.items():
        _json(ausgabe / "suche" / "eigentuemer" / f"{name}.json", inhalt)
```

In `pipeline/06_karte_export.py`: 
```python
eigentuemer_pfad = W / "kuratierung" / "eigentuemer.csv"
eigentuemer = lies_csv(eigentuemer_pfad) if eigentuemer_pfad.exists() else []
```
und `schreibe_paket(..., themen=W / "kuratierung" / "themen", eigentuemer=eigentuemer)`.

- [ ] **Step 4: Thema anlegen**

`kuratierung/themen/besitz.json`:
```json
{
  "id": "besitz",
  "titel": "Besitz",
  "text": "Häuser nach Art des Eigentümers laut Teil II. Farbig nur Adressen, deren Eigentümer von Hand geprüft wurde; alle anderen grau.",
  "grundlage": "Eigentümer-Kuratierung kuratierung/eigentuemer.csv (Automatik + Handprüfung), Stand: in Arbeit",
  "freigegeben": false,
  "filter": {"ebenen": ["II"]},
  "farbe": {"art": "kategorien", "feld": "besitz", "werte": {
    "stadt_staat": "#1d4ed8", "bergbau": "#111827", "industrie": "#b91c1c", "genossenschaft_siedlung": "#15803d",
    "kirche_stiftung": "#7c3aed", "bank_versicherung": "#0e7490", "privatperson": "#d97706", "sonstige": "#6b7280", "gemischt": "#9a3412"},
    "sonst": "#c8c8c8"},
  "zusatz": {"zechen": true, "eigentuemerliste": true},
  "legende": "Farbe = Kategorie des geprüften Eigentümers",
  "darstellung": "punkte"
}
```

- [ ] **Step 5: Tests und Export**

Run: `python3 -m pytest -q`
Expected: alle passed (bisher 299 + neue).
Run: `python3 pipeline/06_karte_export.py` — Kennzahlen zeigen `besitz_geprueft` (0, solange nichts geprüft ist) und `site/daten/suche/eigentuemer.json` existiert (leere Liste `[]`), `site/daten/themen/besitz.json` liegt vor.

- [ ] **Step 6: Commit**

```bash
git add pipeline/lib/karte_export.py pipeline/06_karte_export.py kuratierung/themen/besitz.json tests/test_karte_export.py
git commit -m "feat(eigentuemer): Stufe 06 — geprüfte Eigentümer an Teil-II-Einträge, Punktattribut besitz, Eigentümer-Suchindex, Kennzahlen, Thema Besitz

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Frontend — Farbart `kategorien`, Legende, Hausansicht

**Files:**
- Create: `site/js/kategorien.js`
- Modify: `site/js/themen.js:1-11`, `site/js/app.js:227-241` (Legende), `site/js/popup.js:51-54` (`eintragHtml`)
- Modify: `site/tests/themen.test.js`, `site/tests/popup.test.js`

**Interfaces:**
- Produces: `KATEGORIEN` (JS-Objekt, Schlüssel → Anzeigename, plus `gemischt: "mehrere Kategorien"`, `ungeprueft: "ungeprüft"`); `farbregel(thema)` liefert bei `art === "kategorien"` `{ merkmal: null, ausdruck: ["match", ["get", feld], k1, c1, …, sonst], kategorien: werte, sonst }`.

- [ ] **Step 1: Failing tests**

`site/tests/themen.test.js` anhängen:
```js
test("farbregel kategorien → match-Ausdruck", () => {
  const r = farbregel({ filter: {}, farbe: { art: "kategorien", feld: "besitz", werte: { industrie: "#b91c1c", stadt_staat: "#1d4ed8" }, sonst: "#ccc" } });
  assert.equal(r.merkmal, null);
  assert.deepEqual(r.ausdruck, ["match", ["get", "besitz"], "industrie", "#b91c1c", "stadt_staat", "#1d4ed8", "#ccc"]);
  assert.deepEqual(r.kategorien, { industrie: "#b91c1c", stadt_staat: "#1d4ed8" });
});
```

`site/tests/popup.test.js` anhängen (bestehende Importe prüfen: `hausHtml` muss importiert sein):
```js
test("Hausansicht zeigt geprüften Eigentümer mit Kategorie, sonst nur Buchschreibung", () => {
  const eig = { id: "a1", stufe: "haus", strasse_heute: "Lattenkamp", hausnr: "25", stadtteil: "Katernberg", historisch: "Grenzstr. 25", n_I: 0, n_II: 2, n_III: 0 };
  const e = [{ id: "1", teil: "II", seite: "II-1", name: "", vorname: "", firma: "Fried. Krupp A.G.", eigentuemer: "Eigentümer", eigentuemer_kanon: "Fried. Krupp AG", kategorie: "industrie", flags: [], merkmale: [] },
             { id: "2", teil: "II", seite: "II-1", name: "", vorname: "", firma: "Bauverein GmbH", eigentuemer: "Eigentümer", eigentuemer_kanon: "", kategorie: "", flags: [], merkmale: [] }];
  const h = hausHtml(eig, e);
  assert.match(h, /Zugeordnet<\/span> Fried\. Krupp AG · Industrie/);
  assert.match(h, /Firma<\/span> Fried\. Krupp A\.G\./);
  assert.equal((h.match(/Zugeordnet/g) || []).length, 1);
});
```

- [ ] **Step 2: Fehlschlag prüfen**

Run: `node --test site/tests/`
Expected: 2 FAIL

- [ ] **Step 3: Implementieren**

`site/js/kategorien.js`:
```js
// Anzeigenamen der Eigentümer-Kategorien (Spec §3.3); Schlüssel wie pipeline/lib/eigentuemer.py.
export const KATEGORIEN = {
  stadt_staat: "Stadt/Staat/Reich", bergbau: "Bergbau", industrie: "Industrie", genossenschaft_siedlung: "Genossenschaft/Siedlung",
  kirche_stiftung: "Kirche/Stiftung", bank_versicherung: "Bank/Versicherung", privatperson: "Privatperson", sonstige: "Sonstige",
  gemischt: "mehrere Kategorien", ungeprueft: "ungeprüft",
};
```

`site/js/themen.js`, in `farbregel` vor `return null;`:
```js
  if (f.art === "kategorien") {
    const paare = Object.entries(f.werte || {}).flatMap(([k, farbe]) => [k, farbe]);
    return { merkmal: null, ausdruck: ["match", ["get", f.feld], ...paare, f.sonst || "#c8c8c8"], kategorien: f.werte || {}, sonst: f.sonst || "#c8c8c8" };
  }
```

`site/js/app.js`, Legende: Import `import { KATEGORIEN } from "./kategorien.js";` und in `zeichneLegende` nach dem `skala`-Zweig:
```js
    } else if (farbe.art === "kategorien") {
      html += `<div class="zeile"><b>${themaAktiv.legende}</b></div>`;
      for (const [k, c] of Object.entries(farbe.werte)) html += `<div class="zeile"><span class="punkt" style="background:${c}"></span> ${KATEGORIEN[k] || k}</div>`;
      html += `<div class="zeile"><span class="punkt" style="background:${farbe.sonst || "#c8c8c8"}"></span> ${KATEGORIEN.ungeprueft}</div>`;
    }
```

`site/js/popup.js`, `eintragHtml`: Import `import { KATEGORIEN } from "./kategorien.js";`; in der `felder`-Liste nach `["Eigentümer", e.eigentuemer]` einfügen:
```js
    ["Zugeordnet", e.eigentuemer_kanon ? `${e.eigentuemer_kanon} · ${KATEGORIEN[e.kategorie] || e.kategorie}` : ""],
```

- [ ] **Step 4: Tests**

Run: `node --test site/tests/`
Expected: alle passed

- [ ] **Step 5: Commit**

```bash
git add site/js/kategorien.js site/js/themen.js site/js/app.js site/js/popup.js site/tests/themen.test.js site/tests/popup.test.js
git commit -m "feat(karte): Farbart kategorien (match-Ausdruck, Legende je Kategorie) und geprüfter Eigentümer in der Hausansicht

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Frontend — Vorschlagsart „Eigentümer“, URL-Zustand, Größte Eigentümer

**Files:**
- Modify: `site/js/daten.js:41-42` (Lader), `site/js/suche.js` (Gruppe + Treffer), `site/js/zustand.js:3-5,30` (`eigentuemer`), `site/js/sidebar.js:32,113-119` (Gruppe, Themenkopf-Liste), `site/js/app.js:100,143-147,254-256,290-296` (Zustandswechsel, Vorschlagswahl, Export-Dateiname, Start)
- Modify: `site/tests/suche.test.js`, `site/tests/zustand.test.js`

**Interfaces:**
- Consumes: `suche/eigentuemer.json` (`[schluessel, name, haeuser, kategorie]`), `suche/eigentuemer/<praefix>.json`.
- Produces: `Lader.eigentuemer()`, `Lader.eigentuemerScherbe(praefix)`; `vorschlaege()` liefert zusätzlich `eigentuemer: [{art:"eigentuemer", text, untertitel, name}]`, `gesamt_eigentuemer`; `treffer({art:"eigentuemer", name})`; Zustand `eigentuemer: ""`; `sidebar.zeigeThema(thema, groesste)` rendert bei `groesste` (Array `[schluessel, name, haeuser, kategorie]`) den Block „Größte Eigentümer“ mit `data-eigentuemer`.

- [ ] **Step 1: Failing tests**

`site/tests/suche.test.js`: in `DATEIEN` ergänzen
```js
  "daten/suche/eigentuemer.json": [["fried krupp ag", "Fried. Krupp AG", 2, "industrie"], ["stadt essen", "Stadt Essen", 1, "stadt_staat"]],
  "daten/suche/eigentuemer/fr.json": { "Fried. Krupp AG": [["a1", 1], ["b2", 2]] },
```
und anhängen:
```js
test("Vorschlagsart Eigentümer und Treffermenge", async () => {
  const l = lader();
  const v = await vorschlaege("fried", l);
  assert.deepEqual(v.eigentuemer, [{ art: "eigentuemer", text: "Fried. Krupp AG", untertitel: "2 Häuser · Industrie", name: "Fried. Krupp AG" }]);
  assert.equal(v.gesamt_eigentuemer, 1);
  const t = await treffer({ art: "eigentuemer", name: "Fried. Krupp AG" }, l);
  assert.deepEqual(t.adressIds, ["a1", "b2"]);
  assert.equal(t.zaehler.get("b2"), 2);
});
```

`site/tests/zustand.test.js` anhängen:
```js
test("eigentuemer im Zustand", () => {
  const z = liesZustand("?eigentuemer=Fried.+Krupp+AG");
  assert.equal(z.eigentuemer, "Fried. Krupp AG");
  assert.equal(schreibeZustand({ ...STANDARD, eigentuemer: "Stadt Essen" }), "eigentuemer=Stadt+Essen");
});
```
(Importe `liesZustand, schreibeZustand, STANDARD` in der Testdatei prüfen.)

- [ ] **Step 2: Fehlschlag prüfen**

Run: `node --test site/tests/`
Expected: 2 FAIL

- [ ] **Step 3: Implementieren**

`site/js/daten.js` (nach `berufe()`):
```js
  eigentuemer() { return this.json("suche/eigentuemer.json"); }
  eigentuemerScherbe(praefix) { return this.json(`suche/eigentuemer/${praefix}.json`); }
```

`site/js/suche.js`: Import `import { KATEGORIEN } from "./kategorien.js";`; `MAX` um `eigentuemer: 3`; in `vorschlaege`: `leer` um `eigentuemer: [], gesamt_eigentuemer: 0`; Laden um `lader.eigentuemer()` ergänzen (`const [namen, firmen, strassen, berufe, eigentuemer] = await Promise.all([..., lader.eigentuemer()])`); 
```js
  const alleE = (eigentuemer || []).filter((z) => z[0].startsWith(k))
    .map((z) => ({ art: "eigentuemer", text: z[1], untertitel: `${z[2]} Häuser · ${KATEGORIEN[z[3]] || z[3]}`, name: z[1] }));
```
im Rückgabeobjekt `eigentuemer: alle.eigentuemer ? alleE : alleE.slice(0, MAX.eigentuemer)`, `gesamt` um `alleE.length`, `gesamt_eigentuemer: alleE.length`. In `treffer`:
```js
  } else if (auswahl.art === "eigentuemer") {
    const s = await lader.eigentuemerScherbe(praefix2(auswahl.name));
    for (const [a, n] of (s && s[auswahl.name]) || []) zaehler.set(a, n);
```

`site/js/zustand.js`: `STANDARD` um `eigentuemer: ""` (nach `beruf`); `liesZustand` um `eigentuemer: p.get("eigentuemer") || "",`.

`site/js/sidebar.js`: Gruppenliste in `setzeVorschlaege` um `["eigentuemer", "Eigentümer"]` erweitern; `zeigeThema(thema, groesste = null)`: nach dem Thema-HTML, wenn `groesste && groesste.length`:
```js
    if (groesste && groesste.length) {
      this.themenkopf.insertAdjacentHTML("beforeend", `<div class="gruppe">Größte Eigentümer</div><div class="eigentuemerliste">` +
        groesste.slice(0, 30).map((z) => `<button class="themaknopf" data-eigentuemer="${esc(z[1])}">${esc(z[1])} <small>${z[2]}</small></button>`).join("") + `</div>`);
      this.themenkopf.querySelectorAll("[data-eigentuemer]").forEach((b) => b.addEventListener("click", () => this.a.onZustand({ q: "", beruf: "", eigentuemer: b.dataset.eigentuemer, id: "" })));
    }
```

`site/js/app.js`:
- `setzeZustand`: Zeile 100 ersetzen durch
```js
  if (alt.beruf !== zustand.beruf || alt.eigentuemer !== zustand.eigentuemer) {
    auswahl = zustand.beruf ? { art: "beruf", beruf: zustand.beruf } : zustand.eigentuemer ? { art: "eigentuemer", name: zustand.eigentuemer } : null;
    await sucheAusfuehren();
  }
```
- `wendeThemaAn`: `sidebar.zeigeThema(t, t && t.zusatz && t.zusatz.eigentuemerliste ? await lader.eigentuemer() : null);`
- `waehleVorschlag`: nach der `beruf`-Zeile `if (v.art === "eigentuemer") return setzeZustand({ q: "", beruf: "", eigentuemer: v.name }, true);` und in der `beruf`-Zeile `eigentuemer: ""` mitsetzen: `setzeZustand({ q: "", eigentuemer: "", beruf: v.beruf }, true)`.
- `exportiere`: Dateiname `(zustand.q || zustand.beruf || zustand.eigentuemer || "treffer")`.
- `start()`: `if (zustand.beruf) ... else if (zustand.eigentuemer) auswahl = { art: "eigentuemer", name: zustand.eigentuemer }; else if (zustand.q) ...`.
- Suchfeld-Leeren und `sucheAusText`: beim Setzen von `q` auch `beruf: "", eigentuemer: ""` mitgeben, damit alte Filter nicht hängen bleiben (`setzeZustand({ q, id: "", beruf: "", eigentuemer: "" }, true, true)` in `sucheAusText`; beim Leeren ebenso).

- [ ] **Step 4: Tests + Rauchprobe**

Run: `node --test site/tests/` → alle passed. Dann `python3 pipeline/06_karte_export.py`, Server neu laden, `http://localhost:8765/site/karte.html?thema=besitz` öffnen: Legende zeigt die Kategorien, Punkte grau (noch nichts geprüft), Themenkopf ohne Liste (leer). Keine Konsolenfehler.

- [ ] **Step 5: Commit**

```bash
git add site/js/daten.js site/js/suche.js site/js/zustand.js site/js/sidebar.js site/js/app.js site/tests/suche.test.js site/tests/zustand.test.js
git commit -m "feat(karte): Suche nach kanonischen Eigentümern (Vorschlagsart, URL-Zustand eigentuemer=) und Liste der größten Eigentümer im Thema Besitz

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: e2e-Rauchtest, Doku, Journal

**Files:**
- Modify: `tests/e2e/test_site.py`
- Modify: `README.md` (Abschnitt „Karte“: Eigentümer-Kuratierung; Tabelle `site/daten/`-Struktur um `suche/eigentuemer*`; Themenformat um `kategorien`)
- Modify: `site/ueber.html` (Abschnitt „Stand des Projekts“ → Eigentümer-Kuratierung in Arbeit, Hinweis auf grau = ungeprüft)
- Modify: Vault `~/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Journal.md`

- [ ] **Step 1: e2e-Test anhängen**

```python
# tests/e2e/test_site.py (anhängen)
def test_thema_besitz_legende_und_hausansicht(basis, browser):
    """Thema Besitz: Legende zeigt Kategorien; ein Haus mit geprüftem Eigentümer zeigt „Zugeordnet“."""
    import json
    s = _seite(browser)
    s.goto(basis + "karte.html?thema=besitz")
    s.wait_for_selector("#legende .zeile")
    legende = s.locator("#legende").inner_text()
    assert "Industrie" in legende and "ungeprüft" in legende
    liste = json.loads((W / "site" / "daten" / "suche" / "eigentuemer.json").read_text(encoding="utf-8"))
    if not liste:
        pytest.skip("noch kein geprüfter Eigentümer im Datenpaket")
    name = liste[0][1]
    s.goto(basis + "karte.html?thema=besitz&eigentuemer=" + name)
    s.wait_for_selector(".treffer")
    s.locator(".treffer").first.click()
    s.wait_for_selector(".eintrag")
    assert "Zugeordnet" in s.locator("#inhalt").inner_text()
    assert s.fehler == []
```

- [ ] **Step 2: e2e laufen lassen**

Run: `python3 -m pytest tests/e2e -q -m e2e`
Expected: bisherige 4 + 1 passed (oder skipped, solange nichts geprüft ist — dann eine Testzeile in `kuratierung/eigentuemer.csv` mit `geprueft=ja` setzen, Export neu laufen lassen, Test ausführen, Zeile wieder zurücknehmen).

- [ ] **Step 3: README**

Im Abschnitt „Karte (Teilprojekt 2)“ nach dem Deploy-Block einen Abschnitt einfügen:

```markdown
## Eigentümer (Teilprojekt 3)

Eigentümer aus Teil II werden zu kanonischen Eigentümern mit Kategorie zusammengeführt
(Spec `docs/superpowers/specs/2026-09-22-eigentuemer-design.md`).

```
python3 werkzeuge/eigentuemer_cluster.py [--min-haeuser 5]   # Vorschläge → build/, legt kuratierung/eigentuemer.csv an
python3 werkzeuge/serve.py 8765                              # dann http://localhost:8765/werkzeuge/eigentuemer.html
python3 pipeline/06_karte_export.py                          # geprüfte Zuordnungen in die Karte (Thema „Besitz“)
```

`kuratierung/eigentuemer.csv`: eine Zeile je Schreibweise (`schreibweise, art, eigentuemer, kategorie,
geprueft, bearbeiter, datum, hinweis`). Die Automatik überschreibt nur Zeilen, die ungeprüft sind und
`bearbeiter=eigentuemer_cluster` tragen; alles, was das Werkzeug gespeichert hat, bleibt. Kategorien:
`stadt_staat, bergbau, industrie, genossenschaft_siedlung, kirche_stiftung, bank_versicherung,
privatperson, sonstige`. Abkürzungskatalog: `kuratierung/eigentuemer_abkuerzungen.csv`. Auf der Karte
zählt nur `geprueft=ja`: Punktattribut `besitz` (Kategorie | `gemischt` | `ungeprueft`), Hausansicht
„Zugeordnet“, Suche nach kanonischem Namen (`eigentuemer=` in der URL). Tests: `node --test werkzeuge/tests/`.
```

Tabelle der `site/daten/`-Struktur um `suche/eigentuemer.json`, `suche/eigentuemer/<xx>.json` ergänzen; URL-Tabelle um `eigentuemer`; Themenformat: „`farbe` (eine Farbe | Kategorien (`art: kategorien`, `feld`, `werte`, `sonst`) | Skala …)“.

- [ ] **Step 4: Über-Seite**

In `site/ueber.html` im Abschnitt „Stand des Projekts“ den Satz „In Arbeit: Zusammenführung der Schreibweisen von Eigentümern …“ ersetzen durch: „In Arbeit: die Eigentümer aus Teil II werden zu kanonischen Eigentümern mit Kategorie zusammengeführt (Thema „Besitz“; farbig sind nur von Hand geprüfte Zuordnungen, alles andere grau). Danach die Auflösung der Berufsabkürzungen.“

- [ ] **Step 5: Journal**

An `Journal.md` anhängen: Datum, „TP3 Eigentümer: Werkzeug in Betrieb“ mit den Zahlen aus Task 4 Step 5 (Cluster, prüfpflichtig, abgedeckte Häuser), der Entscheidung Untergrenze 5 auf Cluster-Ebene, Complete-Linkage 0,92 / Vorschlag ab 0,75 und der Sperrregel.

- [ ] **Step 6: Vollständiger Testlauf und Commit**

Run: `python3 -m pytest -q && node --test site/tests/ && node --test werkzeuge/tests/`
Expected: alles grün.

```bash
git add tests/e2e/test_site.py README.md site/ueber.html
git commit -m "docs(eigentuemer): README-Abschnitt Teilprojekt 3, Über-Seite, e2e-Rauchtest Thema Besitz

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
git push origin main
```

---

## Self-Review

- **Spec-Abdeckung:** §3.1–3.4 → Tasks 1, 4; §4.1–4.5 → Tasks 2–4; §5.1 → Tasks 6–7; §5.2 → Task 5; §6.1 → Task 8; §6.2 → Tasks 8–9; §6.3 → Task 9; §6.4 → Tasks 8, 10; §7 Tests → in jedem Task, e2e Task 11; §8 Abnahme (Über-Seite, Journal) → Task 11. Die eigentliche Kuratierung (≈ 150 Cluster von Hand) ist Nutzerarbeit und kein Plan-Task.
- **Platzhalter:** keine; Zahlen in Commit-Nachricht Task 4 werden beim Lauf eingesetzt (`<n>`, `<m>` sind Anweisungen an den Implementierer, keine offenen Punkte).
- **Typkonsistenz:** `schreibweise_von` (Task 1) wird in Task 4 und 8 gleich benutzt; `lade_kuratierung` liefert Dict nach Schreibweise (Tasks 1, 5, 8); Vorschlagsspalten (Task 4) = Felder, die `baueModell` (Task 6) und `csvLesen` (Task 7) lesen; `zumSpeichern` liefert genau die Felder, die `pruefe_eigentuemer` (Task 5) prüft; `farbregel().kategorien`/`sonst` (Task 9) werden in `zeichneLegende` als `farbe.werte`/`farbe.sonst` aus dem Thema gelesen (Themenobjekt, nicht Regel — bewusst, weil `zeichneLegende` bereits `themaAktiv.farbe` nutzt); Suchindex-Zeilenformat `[schluessel, name, haeuser, kategorie]` (Task 8) = Leser in Task 10.
