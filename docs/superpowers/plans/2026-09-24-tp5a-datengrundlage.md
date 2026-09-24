# TP5a Datengrundlage: Stellung, Gruppen, Gewerbe, Ebenen, Layouts — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Datengrundlage für Perspektiven (5b) und Werkstatt (5c): Klassifikation „Soziale Stellung“ und Berufsgruppen je Beruf, Gewerberubriken aus Teil III, Zählfelder je Adresse/Straße/Stadtteil/Hexzelle, deterministische Bubble-Layouts, OSM-Straßenlinien — alles mit Vorschlag + Handprüfung, nichts Ungeprüftes im Export.

**Architecture:** Drei neue reine Module in `pipeline/lib/` (`stellung.py`, `gruppen.py`, `gewerbe.py`) liefern Vokabulare und deterministische Vorschlagsregeln; drei kleine CLI-Skripte in `werkzeuge/` schreiben Kuratierungstabellen (Upsert, der Mensch entscheidet im Browser). Ein generisches Tabellenwerkzeug (`werkzeuge/zuordnung.html` + `js/zuordnung_modell.js`) prüft Gruppen und Gewerbe; das Berufe-Werkzeug bekommt die Stellung. `pipeline/lib/ebenen.py` (Hexraster, Zählfelder, Aggregation) und `pipeline/lib/layout.py` (Kreispackung, Beeswarm) hängen an Stufe 06; `werkzeuge/osm_strassen_laden.py` holt Straßenlinien per Overpass nach `build/`.

**Tech Stack:** Python 3.12 (csv, json, re, math, requests), http.server (Dev-Server), tippecanoe (Mehrschicht-PMTiles), ES-Module ohne Bundler, pytest, node:test.

**Spec:** `docs/superpowers/specs/2026-09-24-perspektiven-werkstatt-design.md` (§4–§5, §9)

## Global Constraints

- Deutsch mit korrekten Umlauten in Kommentaren, Texten, Commit-Nachrichten; Bezeichner deutsch wie im Bestand.
- Precision first: In den Export gehen Stellung nur mit `geprueft=ja` **und** `stellung_geprueft=ja`, Gruppe/Rubrik nur mit `geprueft=ja`; alles andere zählt als `unbestimmt` bzw. `ungeprueft`. Die Automatik setzt nie `geprueft`/`stellung_geprueft`.
- Sperrregel Berufe unverändert: `geprueft=ja` oder `bearbeiter≠berufe_vorschlag` → Berufszuordnung wird nicht überschrieben. `stellung` darf die Stellungs-Automatik überall füllen, wo `stellung_geprueft` leer ist.
- Vokabulare exakt: Stellung `arbeiter | angestellte | beamte | selbstaendige | freie_berufe | unternehmer | ohne_erwerb | kaufleute | unbestimmt`; Gruppen `bergbau | metall_maschinen | bau | holz_moebel | textil_bekleidung | lebensmittel | handel | gastgewerbe | verkehr_bahn_post | verwaltung | bildung_kultur_kirche | gesundheit | haus_reinigung | sonstige`; Art `handwerk | handel | gastgewerbe | dienstleistung | industrie | freier_beruf | sonstige`.
- Zählfeld-Präfixe exakt: `n_st_` (Stellung), `n_gr_` (Berufsgruppe, Teil I), `n_gw_` (Gewerbegruppe, Teil III), `n_gwa_` (Gewerbeart), `n_bs_` (Besitzklasse je Adresse), `n_<niveau>` (bestehend).
- Hexraster: Kantenlänge 120 m, spitze Ecke oben („pointy-top“), lokale Projektion um (51.45, 7.01); Zellen-ID `"<q>_<r>"`.
- Layouts deterministisch: keine Zufallszahl, sortiert nach Größe absteigend, dann nach Schlüssel; Test prüft Reproduzierbarkeit und Überlappungsfreiheit.
- CSV über `pipeline.lib.io.lies_csv`/`schreib_csv`; JSON kompakt über `karte_export._json`. `build/` und `site/daten/` sind nicht versioniert.
- Keine neuen Python-Abhängigkeiten (requests und rapidfuzz sind vorhanden); keine neuen JS-Abhängigkeiten.
- Tests: `python3 -m pytest -q`, `node --test werkzeuge/tests/`, `node --test site/tests/`. Alle grün vor jedem Commit.
- Commits enden mit `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; Arbeit direkt auf `main`.

---

## Dateiübersicht

| Datei | Verantwortung |
|---|---|
| `pipeline/lib/stellung.py` (neu) | `STELLUNGEN`, `stellung_vorschlag(zeile, item, regeln)`, `stellung_export(zeile)` |
| `pipeline/lib/gruppen.py` (neu) | `GRUPPEN`, `gruppe_vorschlag(item)`, `FELDER_GRUPPEN`, `lade_gruppen` |
| `pipeline/lib/gewerbe.py` (neu) | `ARTEN`, `rubrik_von(firmenname)`, `gewerbe_vorschlag(rubrik)`, `FELDER_GEWERBE`, `lade_gewerbe` |
| `pipeline/lib/berufe.py` | `FELDER_KURATIERUNG` + `stellung`, `stellung_geprueft`; `zuordnung()` liefert `stellung`, `gattung_id` |
| `werkzeuge/stellung_vorschlag.py` (neu) | füllt `stellung` in `kuratierung/berufe.csv` |
| `werkzeuge/gruppen_vorschlag.py` (neu) | schreibt `kuratierung/gruppen.csv` (je OhdAB-Item aus berufe.csv) |
| `werkzeuge/gewerbe_vorschlag.py` (neu) | schreibt `kuratierung/gewerbe.csv` (je Rubrik aus Teil III) |
| `werkzeuge/js/zuordnung_modell.js` (neu), `werkzeuge/zuordnung.html` (neu) | generisches Prüfwerkzeug für gruppen.csv und gewerbe.csv |
| `werkzeuge/js/berufe_modell.js`, `werkzeuge/berufe.html` | Stellung setzen/prüfen, Filter „Stellung offen“ |
| `werkzeuge/serve.py` | Stellung in `POST /kuratierung/berufe.csv`; `POST /kuratierung/gruppen.csv`, `POST /kuratierung/gewerbe.csv` |
| `pipeline/lib/ebenen.py` (neu) | Hexraster, `zaehlfelder`, Aggregation je Straße/Stadtteil/Hex |
| `pipeline/lib/layout.py` (neu) | `packe_kreise`, `packe_gruppen`, `beeswarm` |
| `werkzeuge/osm_strassen_laden.py` (neu) | Overpass → `build/osm_strassen.geojson` |
| `pipeline/lib/karte_export.py`, `pipeline/06_karte_export.py` | Gattung/Stellung/Gruppe/Gewerbe an Einträgen, Zählfelder, `ebenen/`, `layout/`, Schichten `strassen`/`hex`, Kennzahlen |
| `docs/stellung.md` (neu), `README.md` | Regeln, Grenzfälle, Datenkerne |
| Tests | `tests/test_stellung.py`, `tests/test_gruppen.py`, `tests/test_gewerbe.py`, `tests/test_ebenen.py`, `tests/test_layout.py`, `tests/test_osm_strassen.py`, Erweiterungen in `tests/test_berufe.py`, `tests/test_serve.py`, `tests/test_karte_export.py`, `werkzeuge/tests/zuordnung_modell.test.js`, `werkzeuge/tests/berufe_modell.test.js` |

---

### Task 1: Modul `stellung.py` — Vokabular und Vorschlagsregeln

**Files:**
- Create: `pipeline/lib/stellung.py`
- Test: `tests/test_stellung.py`

**Interfaces:**
- Consumes: `pipeline.lib.berufe.falte_form`, `pipeline.lib.merkmale.Regel`, `merkmale_fuer`.
- Produces: `STELLUNGEN: dict[str, str]` (Schlüssel → Anzeigetext, Reihenfolge wie Spec), `stellung_vorschlag(zeile: dict, item: dict | None, regeln: list[Regel]) -> tuple[str, str]` (Klasse, Grund), `stellung_export(zeile: dict) -> str` (Klasse für den Export oder `"unbestimmt"`).

- [ ] **Step 1: Test schreiben**

```python
# tests/test_stellung.py
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.merkmale import Regel
from pipeline.lib.stellung import STELLUNGEN, stellung_export, stellung_vorschlag

REGELN = [Regel("Beruf o. ä.", "praefix", "Dr.", "akademiker"), Regel("Beruf o. ä.", "praefix", "Dipl.", "akademiker")]


def item(norm, niveau="fachlich", gattung="Berufe im Berg- und Tagebau – fachlich ausgerichtete Tätigkeiten", gattung_id="B 21112"):
    return dict(ohdab_id="X", norm=norm, maennlich="", weiblich="", niveau=niveau, gattung_id=gattung_id, gattung=gattung)


def zeile(schreibweise, status="", beruf=""):
    return dict(schreibweise=schreibweise, status=status, beruf=beruf or schreibweise)


def test_vokabular():
    assert list(STELLUNGEN) == ["arbeiter", "angestellte", "beamte", "selbstaendige", "freie_berufe", "unternehmer",
                                "ohne_erwerb", "kaufleute", "unbestimmt"]


def test_regeln_in_reihenfolge():
    assert stellung_vorschlag(zeile("Bergm. i. R.", status="ruhestand"), item("Bergmann/-frau"), REGELN) == ("ohne_erwerb", "status")
    assert stellung_vorschlag(zeile("Invalide", status="invalide"), item("Invalide/Invalidin", "keins", "Invalide", "A 10200"), REGELN) == ("ohne_erwerb", "status")
    assert stellung_vorschlag(zeile("Berufslos"), item("Berufslose/r", "keins", "Berufslose", "A 10100"), REGELN) == ("ohne_erwerb", "item A 1")
    assert stellung_vorschlag(zeile("Bäckerei", status="gewerbe"), item("Bäcker/in"), REGELN) == ("selbstaendige", "gewerbe")
    assert stellung_vorschlag(zeile("Bäckermstr."), item("Bäckermeister/in", "aufsicht", "Aufsichtskräfte – Lebensmittel"), REGELN) == ("selbstaendige", "handwerksmeister")
    assert stellung_vorschlag(zeile("Werkmstr."), item("Werkmeister/in", "aufsicht", "Aufsichtskräfte – Produktion"), REGELN) == ("angestellte", "betriebsmeister")
    assert stellung_vorschlag(zeile("Dr. med."), item("Arzt/Ärztin", "hochkomplex", "Ärzte"), REGELN) == ("freie_berufe", "akademiker")
    assert stellung_vorschlag(zeile("Rechtsanwalt"), item("Rechtsanwalt/-anwältin", "hochkomplex", "Rechtsberatung"), REGELN) == ("freie_berufe", "freier beruf")
    assert stellung_vorschlag(zeile("Fabrikant"), item("Fabrikant/in", "fuehrung", "Geschäftsführer/innen und Vorstände"), REGELN) == ("unternehmer", "unternehmer")
    assert stellung_vorschlag(zeile("Direktor"), item("Direktor/in", "fuehrung", "Geschäftsführer/innen und Vorstände – hoch komplexe Tätigkeiten"), REGELN) == ("unternehmer", "unternehmer")
    assert stellung_vorschlag(zeile("Kfm."), item("Kaufmann/-frau", "fachlich", "Kaufleute im Handel"), REGELN) == ("kaufleute", "kaufmann")
    assert stellung_vorschlag(zeile("kfm. Angest."), item("Kaufmännische/r Angestellte/r", "fachlich", "Kaufleute"), REGELN) == ("angestellte", "angestellte")
    assert stellung_vorschlag(zeile("Reichsbahnbeamt."), item("Bahnbeamt(er/in) (mittl. Dienst)", "fachlich", "Eisenbahnverkehrsbetrieb"), REGELN) == ("beamte", "beamte")
    assert stellung_vorschlag(zeile("Lehrer"), item("Lehrer/in", "hochkomplex", "Lehrkräfte in der Sekundarstufe"), REGELN) == ("beamte", "beamte")
    assert stellung_vorschlag(zeile("Lokomotivführer"), item("Lokomotivführer/in", "fachlich", "Triebfahrzeugführer"), REGELN) == ("beamte", "beamte")
    assert stellung_vorschlag(zeile("Steiger"), item("Steiger/in", "spezialist", "Berufe im Berg- und Tagebau – komplexe Spezialistentätigkeiten"), REGELN) == ("angestellte", "angestellte")
    assert stellung_vorschlag(zeile("Techniker"), item("Techniker/in", "spezialist", "Maschinenbau"), REGELN) == ("angestellte", "angestellte")
    assert stellung_vorschlag(zeile("Gastwirt"), item("Gastwirt/in", "fachlich", "Gastronomie"), REGELN) == ("selbstaendige", "selbstaendig")
    assert stellung_vorschlag(zeile("Kolonialwarenhändler"), item("Kolonialwarenhändler/in", "fachlich", "Handel"), REGELN) == ("selbstaendige", "selbstaendig")
    assert stellung_vorschlag(zeile("Bergm."), item("Bergmann/-frau"), REGELN) == ("arbeiter", "niveau fachlich")
    assert stellung_vorschlag(zeile("Arbeiter"), item("Arbeiter/in - allgemein", "helfer", "Produktion"), REGELN) == ("arbeiter", "niveau helfer")
    assert stellung_vorschlag(zeile("Musiker"), item("Musiker/in", "keins", "Musik"), REGELN) == ("unbestimmt", "")
    assert stellung_vorschlag(zeile("Xyz"), None, REGELN) == ("unbestimmt", "")


def test_export_nur_doppelt_geprueft():
    assert stellung_export(dict(geprueft="ja", stellung="arbeiter", stellung_geprueft="ja")) == "arbeiter"
    assert stellung_export(dict(geprueft="ja", stellung="arbeiter", stellung_geprueft="")) == "unbestimmt"
    assert stellung_export(dict(geprueft="", stellung="arbeiter", stellung_geprueft="ja")) == "unbestimmt"
    assert stellung_export(dict(geprueft="ja", stellung="", stellung_geprueft="ja")) == "unbestimmt"
```

- [ ] **Step 2: Test laufen lassen — erwartet ImportError**

Run: `python3 -m pytest tests/test_stellung.py -q`
Expected: FAIL (`ModuleNotFoundError: pipeline.lib.stellung`)

- [ ] **Step 3: Modul schreiben**

```python
# pipeline/lib/stellung.py
"""Soziale Stellung je Berufsschreibweise (Teilprojekt 5, Spec §5.1) — Vokabular, Vorschlagsregeln, Exportregel.

Vorbild ist die „Stellung im Beruf“ der Berufszählungen 1933/1939. Die Regeln liefern nur Vorschläge; entschieden
wird im Werkzeug (`stellung_geprueft=ja`). Reihenfolge der Regeln = Reihenfolge in `stellung_vorschlag`; die
Doku in docs/stellung.md beschreibt jede Regel mit Beispielen.
"""
from __future__ import annotations

import re

from pipeline.lib.berufe import falte_form
from pipeline.lib.merkmale import Regel, merkmale_fuer

STELLUNGEN = {
    "arbeiter": "Arbeiter",
    "angestellte": "Angestellte",
    "beamte": "Beamte",
    "selbstaendige": "Selbständige (Handwerk, Handel, Gastgewerbe)",
    "freie_berufe": "Freie Berufe und Akademiker",
    "unternehmer": "Unternehmer und Leitende",
    "ohne_erwerb": "Ohne Erwerbsberuf",
    "kaufleute": "Kaufleute (Stellung unbestimmt)",
    "unbestimmt": "unbestimmt",
}
UNBESTIMMT = "unbestimmt"

# Meister im Handwerk (selbständig) — Stamm vor „meister“/„mstr.“; alle anderen Meister (Werk-, Betriebs-,
# Fahr-, Zug-, Bahnmeister …) sind betriebliche Vorgesetzte, also Angestellte.
_HANDWERK = ("bäcker", "metzger", "schlachter", "fleischer", "konditor", "schneider", "schuhmacher", "friseur", "maler",
             "anstreicher", "tischler", "schreiner", "schlosser", "klempner", "installateur", "dachdecker", "schmied",
             "maurer", "zimmer", "stukkateur", "glaser", "sattler", "polsterer", "tapezier", "uhrmacher", "gold",
             "buchbinder", "drucker", "gärtner", "fuhr", "elektro", "schornsteinfeger", "kürschner", "hut", "korb",
             "stellmacher", "wagner", "böttcher", "küfer", "müller", "mühlen", "brauer", "gerber", "seiler", "töpfer",
             "ofensetzer", "steinmetz", "bildhauer", "graveur", "optiker", "mechaniker", "fotograf")
_MEISTER = re.compile(r"(meister(in)?|mstr\.?)$", re.I)
_FREIE = re.compile(r"arzt|ärzt|zahnarzt|dentist|tierarzt|apotheker|rechtsanwalt|anwalt|notar|architekt|patentanwalt|"
                    r"wirtschaftsprüfer|steuerberater|bücherrevisor|schriftsteller|künstler|kunstmaler|bildhauer/in$", re.I)
_UNTERNEHMER = re.compile(r"fabrikant|fabrikbesitzer|direktor|generaldirektor|vorstand|geschäftsführer|inhaber|unternehmer|"
                          r"prokurist|bergwerksbesitzer|gutsbesitzer|hausbesitzer|rentier", re.I)
_BEAMTE = re.compile(r"beamt|sekretär|inspektor|assistent|amtmann|\brat\b|rätin|lehrer|schaffner|zugführer|lokomotivführer|"
                     r"briefträger|postbote|polizei|schutzmann|wachtmeister|zoll|richter|pfarrer|pastor|geistlich|"
                     r"oberst|major|hauptmann|offizier|förster|gerichtsvollzieher|\(.*dienst\)", re.I)
_ANGESTELLTE = re.compile(r"angestellt|buchhalter|kontorist|techniker|ingenieur|steiger|zeichner|verkäufer|handlungsgehilf|"
                          r"kassierer|vertreter|reisender|bürogehilf|stenotypist|laborant|chemiker|betriebsführer|"
                          r"abteilungsleiter|filialleiter|disponent|expedient|magazinverwalter|werkführer|obersteiger", re.I)
_SELBSTAENDIGE = re.compile(r"händler|handel|wirt(in)?$|gastwirt|schankwirt|krämer|fuhrmann|kaufmann/-frau -|kaufmann/-frau \(|"
                            r"hausierer|agent|makler|kommissionär|verleger|drogist|hebamme|masseur|heilpraktiker|"
                            r"landwirt|bauer|kötter|pächter|fischer|schiffer", re.I)


def _norm(item: dict | None) -> str:
    return (item or {}).get("norm", "")


def _text(zeile: dict, item: dict | None) -> str:
    """Prüftext = Normbezeichnung + Gattung + aufgelöster Beruf (Schreibweise selbst nur für Meister/Titel)."""
    return " | ".join(x for x in (_norm(item), (item or {}).get("gattung", ""), zeile.get("beruf", "")) if x)


def stellung_vorschlag(zeile: dict, item: dict | None, regeln: list[Regel]) -> tuple[str, str]:
    """(Klasse, Grund) nach der ersten treffenden Regel; ohne Treffer („unbestimmt“, „“)."""
    status = [s.strip() for s in (zeile.get("status") or "").split(";") if s.strip()]
    text = _text(zeile, item)
    schreibweise = zeile.get("schreibweise", "")
    if any(s in ("ruhestand", "invalide", "witwe") for s in status):
        return "ohne_erwerb", "status"
    if (item or {}).get("gattung_id", "").startswith("A 1"):
        return "ohne_erwerb", "item A 1"
    if "gewerbe" in status:
        return "selbstaendige", "gewerbe"
    if _MEISTER.search(schreibweise) or _MEISTER.search(_norm(item)):
        stamm = falte_form(schreibweise or _norm(item))
        return ("selbstaendige", "handwerksmeister") if any(h in stamm for h in _HANDWERK) else ("angestellte", "betriebsmeister")
    if "akademiker" in merkmale_fuer({"Beruf o. ä.": schreibweise}, regeln):
        return "freie_berufe", "akademiker"
    if _FREIE.search(_norm(item)):
        return "freie_berufe", "freier beruf"
    if _UNTERNEHMER.search(text):
        return "unternehmer", "unternehmer"
    if falte_form(_norm(item)) in ("kaufmann/ frau", "kaufmann frau", "kaufmann") or falte_form(_norm(item)).startswith("kaufmann frau"):
        if not re.search(r"angest|beamt", text, re.I):
            return "kaufleute", "kaufmann"
    if _ANGESTELLTE.search(text) and not _BEAMTE.search(_norm(item)):
        return "angestellte", "angestellte"
    if _BEAMTE.search(text):
        return "beamte", "beamte"
    if _SELBSTAENDIGE.search(_norm(item)):
        return "selbstaendige", "selbstaendig"
    niveau = (item or {}).get("niveau", "")
    if niveau in ("spezialist", "aufsicht") or (item or {}).get("gattung", "").startswith("Aufsichtskräfte"):
        return "angestellte", "angestellte"
    if niveau in ("helfer", "fachlich"):
        return "arbeiter", f"niveau {niveau}"
    return UNBESTIMMT, ""


def stellung_export(zeile: dict) -> str:
    """Export nur, wenn Beruf und Stellung geprüft sind (Spec §5.1); sonst „unbestimmt“."""
    if zeile.get("geprueft") == "ja" and zeile.get("stellung_geprueft") == "ja" and zeile.get("stellung") in STELLUNGEN:
        return zeile["stellung"]
    return UNBESTIMMT
```

Hinweis für den Implementierer: `falte_form("Kaufmann/-frau")` ergibt `"kaufmann frau"` (Bindestrich → Leerzeichen, „/“ entfernt). Der Kaufleute-Vergleich in der Vorlage ist absichtlich tolerant formuliert; vereinfache ihn auf `falte_form(_norm(item)) == "kaufmann frau"`, wenn der Test damit grün wird.

- [ ] **Step 4: Test laufen lassen**

Run: `python3 -m pytest tests/test_stellung.py -q`
Expected: PASS. Falls eine Regel-Reihenfolge einen Fall falsch trifft (z. B. „Direktor“ von `_BEAMTE`-`\brat\b` nicht betroffen, „Steiger“ von `_ANGESTELLTE` vor Niveau): Regeln nachziehen, nicht den Test.

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/stellung.py tests/test_stellung.py
git commit -m "feat(stellung): Vokabular und Vorschlagsregeln für die soziale Stellung

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: `berufe.py` — neue Spalten, `zuordnung()` liefert Stellung und Gattungs-ID; `stellung_vorschlag.py`

**Files:**
- Modify: `pipeline/lib/berufe.py:14-15` (FELDER_KURATIERUNG), `:113-126` (zuordnung)
- Create: `werkzeuge/stellung_vorschlag.py`
- Test: `tests/test_berufe.py`, `tests/test_stellung.py`

**Interfaces:**
- Produces: `FELDER_KURATIERUNG = [..., "hinweis", "stellung", "stellung_geprueft"]`; `zuordnung()` gibt zusätzlich `stellung` (per `stellung_export`) und `gattung_id`; `werkzeuge.stellung_vorschlag.ergaenze_stellung(zeilen, ohdab, regeln) -> tuple[list[dict], dict]` (Zeilen, Kennzahlen je Grund).

- [ ] **Step 1: Tests ergänzen**

In `tests/test_berufe.py` an `test_zuordnung_nur_geprueft` anhängen:

```python
    from pipeline.lib.berufe import FELDER_KURATIERUNG
    assert FELDER_KURATIERUNG[-2:] == ["stellung", "stellung_geprueft"]
    k2 = lade_kuratierung([dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja", stellung="arbeiter", stellung_geprueft="ja"),
                           dict(schreibweise="Lehrer", beruf="Lehrer", status="", ohdab_id="B 84124-120", niveau_unsicher="", geprueft="ja", stellung="beamte", stellung_geprueft="")])
    z = zuordnung({"Beruf o. ä.": "Bergm."}, k2, o)
    assert z["stellung"] == "arbeiter" and z["gattung_id"] == "B 21112"
    assert zuordnung({"Beruf o. ä.": "Lehrer"}, k2, o)["stellung"] == "unbestimmt"
```

In `tests/test_stellung.py` anhängen:

```python
def test_ergaenze_stellung_fuellt_nur_ungeprueft():
    from werkzeuge.stellung_vorschlag import ergaenze_stellung
    ohdab = {"B 21112-100": item("Bergmann/-frau"), "B 84124-120": item("Lehrer/in", "hochkomplex", "Lehrkräfte")}
    zeilen = [dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", geprueft="ja", stellung="", stellung_geprueft=""),
              dict(schreibweise="Lehrer", beruf="Lehrer", status="", ohdab_id="B 84124-120", geprueft="ja", stellung="freie_berufe", stellung_geprueft="ja"),
              dict(schreibweise="Kfm", beruf="Kfm", status="", ohdab_id="", geprueft="", stellung="", stellung_geprueft="")]
    neu, kenn = ergaenze_stellung(zeilen, ohdab, REGELN)
    assert [z["stellung"] for z in neu] == ["arbeiter", "freie_berufe", "unbestimmt"]
    assert [z["stellung_geprueft"] for z in neu] == ["", "ja", ""]
    assert kenn == {"niveau fachlich": 1, "ohne": 1, "geprueft": 1}
```

- [ ] **Step 2: Tests laufen lassen — erwartet FAIL**

Run: `python3 -m pytest tests/test_berufe.py tests/test_stellung.py -q`
Expected: FAIL (`FELDER_KURATIERUNG` endet mit `hinweis`; `KeyError: 'stellung'`; ImportError)

- [ ] **Step 3: `berufe.py` ändern**

```python
FELDER_KURATIERUNG = ["schreibweise", "nennungen", "beruf", "status", "ohdab_id", "niveau_unsicher", "geprueft",
                      "vorschlag_grund", "bearbeiter", "datum", "hinweis", "stellung", "stellung_geprueft"]
```

und in `zuordnung()` das Rückgabe-dict erweitern (Import oben: `from pipeline.lib.stellung import stellung_export` — Achtung Kreisimport: `stellung.py` importiert `falte_form` aus `berufe.py`; darum den Import in `zuordnung()` lokal setzen):

```python
    from pipeline.lib.stellung import stellung_export   # lokal: stellung.py importiert berufe.py
    return dict(beruf=z["beruf"], ohdab=z["ohdab_id"], niveau=niveau, gattung=o["gattung"], gattung_id=o["gattung_id"],
                status=z.get("status", ""), norm=norm, stellung=stellung_export(z))
```

- [ ] **Step 4: `werkzeuge/stellung_vorschlag.py` schreiben**

```python
"""Vorschlag der sozialen Stellung je Berufsschreibweise (Teilprojekt 5a, Spec §5.1).

Aufruf: python3 werkzeuge/stellung_vorschlag.py [--wurzel PFAD]
Liest kuratierung/berufe.csv, kuratierung/ohdab.csv, kuratierung/merkmale/*.csv; schreibt kuratierung/berufe.csv
mit gefüllter Spalte `stellung`, wo `stellung_geprueft` leer ist. `stellung_geprueft` setzt nur der Mensch.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import json
from collections import Counter
from pathlib import Path

from pipeline.lib.berufe import FELDER_KURATIERUNG, lade_ohdab
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv
from pipeline.lib.merkmale import Regel, lade_regeln
from pipeline.lib.stellung import stellung_vorschlag


def ergaenze_stellung(zeilen: list[dict], ohdab: dict[str, dict], regeln: list[Regel]) -> tuple[list[dict], dict]:
    """Geprüfte Stellung bleibt; sonst Vorschlag. Kennzahlen: Grund → Zeilen („ohne“ = unbestimmt, „geprueft“ = belassen)."""
    out, kenn = [], Counter()
    for z in zeilen:
        z = {k: (v or "") for k, v in z.items()}
        if z.get("stellung_geprueft") == "ja" and z.get("stellung"):
            kenn["geprueft"] += 1
        else:
            klasse, grund = stellung_vorschlag(z, ohdab.get(z.get("ohdab_id", "")), regeln)
            z["stellung"], z["stellung_geprueft"] = klasse, ""
            kenn[grund or "ohne"] += 1
        out.append(z)
    return out, dict(kenn)


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wurzel", default=None)
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    pfad = W / "kuratierung" / "berufe.csv"
    neu, kenn = ergaenze_stellung(lies_csv(pfad), lade_ohdab(W / "kuratierung" / "ohdab.csv"), lade_regeln(W / "kuratierung" / "merkmale"))
    schreib_csv(pfad, neu, FELDER_KURATIERUNG)
    print(json.dumps(kenn, ensure_ascii=False, indent=1))
    return kenn


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Tests laufen lassen**

Run: `python3 -m pytest tests/test_berufe.py tests/test_stellung.py tests/test_berufe_vorschlag.py tests/test_serve.py -q`
Expected: PASS (der Server schreibt mit `FELDER_BERUFE`, neue Spalten kommen leer hinzu).

- [ ] **Step 6: Auf den echten Daten laufen lassen und Verteilung prüfen**

Run: `python3 werkzeuge/stellung_vorschlag.py && python3 -c "import csv,collections;print(collections.Counter(z['stellung'] for z in csv.DictReader(open('kuratierung/berufe.csv',encoding='utf-8'))))"`
Expected: Kennzahlen je Grund; `unbestimmt` deutlich unter 20 % der Zeilen. Zehn Stichproben je Klasse mit `grep` ansehen; offensichtliche Regel-Fehler (z. B. „Direktor“ als Beamter) in `stellung.py` korrigieren und Test um den Fall erweitern. `kuratierung/berufe.csv` wird in diesem Task **noch nicht** committet (Handprüfung folgt) — nur, wenn die Verteilung plausibel ist, als eigener Daten-Commit.

- [ ] **Step 7: Commit**

```bash
git add pipeline/lib/berufe.py werkzeuge/stellung_vorschlag.py tests/test_berufe.py tests/test_stellung.py
git commit -m "feat(stellung): Spalten stellung/stellung_geprueft, Vorschlagsskript, Export nur doppelt geprüft

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
git add kuratierung/berufe.csv
git commit -m "data(berufe): Stellungsvorschläge der Automatik (stellung_geprueft leer)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Stellung im Dev-Server und im Berufe-Werkzeug

**Files:**
- Modify: `werkzeuge/serve.py:139-159` (pruefe_berufe), `:329-349` (_berufe)
- Modify: `werkzeuge/js/berufe_modell.js:3` (CSV_FELDER), `:47-50` (baueModell), neue Funktionen
- Modify: `werkzeuge/berufe.html` (Kopf, Filter, Tasten)
- Test: `tests/test_serve.py`, `werkzeuge/tests/berufe_modell.test.js`

**Interfaces:**
- Consumes: `pipeline.lib.stellung.STELLUNGEN`.
- Produces: `setzeStellung(m, s, klasse) -> Zeile[]` (setzt `stellung` und `stellung_geprueft="ja"`), `schalteStellungGeprueft(m, s) -> Zeile[]`, Modellfelder `stellung`, `stellung_geprueft`, `fortschritt(m).stellungGeprueft`.

- [ ] **Step 1: Server-Test ergänzen** (`tests/test_serve.py`, nach `test_berufe_post_validiert`)

```python
def test_berufe_post_stellung(server):
    url, wurzel = server
    z = dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja", hinweis="",
             stellung="arbeiter", stellung_geprueft="ja")
    post(url + "/kuratierung/berufe.csv", {"zeilen": [z]})
    zeilen = {x["schreibweise"]: x for x in csv.DictReader(open(wurzel / "kuratierung" / "berufe.csv", encoding="utf-8"))}
    assert zeilen["Bergm."]["stellung"] == "arbeiter" and zeilen["Bergm."]["stellung_geprueft"] == "ja"
    with pytest.raises(urllib.error.HTTPError) as e:
        post(url + "/kuratierung/berufe.csv", {"zeilen": [dict(z, stellung="adel")]})
    assert e.value.code == 400 and "Stellung" in e.value.read().decode()
    with pytest.raises(urllib.error.HTTPError) as e:
        post(url + "/kuratierung/berufe.csv", {"zeilen": [dict(z, stellung="", stellung_geprueft="ja")]})
    assert e.value.code == 400
```

Prüfe vorher, wie das `server`-Fixture `url`/`wurzel` liefert (Zeilen 40–62) und passe das Entpacken an.

- [ ] **Step 2: Modell-Test ergänzen** (`werkzeuge/tests/berufe_modell.test.js`)

```js
test("Stellung setzen prüft sie; Schalter nimmt die Prüfung zurück", () => {
  const m = frisch();
  const g = setzeStellung(m, "Bergm.", "arbeiter");
  assert.equal(g.length, 1); assert.equal(g[0].stellung, "arbeiter"); assert.equal(g[0].stellung_geprueft, "ja");
  assert.deepEqual(schalteStellungGeprueft(m, "Bergm.").map((z) => z.stellung_geprueft), [""]);
  assert.deepEqual(setzeStellung(m, "Bergm.", "adel"), []);
  assert.equal(fortschritt(m).stellungGeprueft, 0);
  setzeStellung(m, "Arbeiter", "arbeiter");
  assert.equal(fortschritt(m).stellungGeprueft, 1);
  assert.equal(Object.keys(zumSpeichern(m.zeilen.get("Bergm."))).includes("stellung_geprueft"), true);
});
```

Import oben um `setzeStellung, schalteStellungGeprueft` ergänzen; in `K` jede Zeile um `stellung: "", stellung_geprueft: ""` ergänzen (Bergm.: `stellung: "arbeiter"`).

- [ ] **Step 3: Tests laufen lassen — erwartet FAIL**

Run: `python3 -m pytest tests/test_serve.py -q -k stellung; node --test werkzeuge/tests/`

- [ ] **Step 4: Server**

In `serve.py` Import ergänzen: `from pipeline.lib.stellung import STELLUNGEN`. In `pruefe_berufe` vor `return ""`:

```python
    st = str(z.get("stellung", "")).strip()
    if st and st not in STELLUNGEN:
        return f"unbekannte Stellung: {st}"
    if str(z.get("stellung_geprueft", "")).strip() not in ("", "ja"):
        return "stellung_geprueft muss ja oder leer sein"
    if str(z.get("stellung_geprueft", "")).strip() == "ja" and not st:
        return "stellung_geprueft=ja verlangt eine Stellung"
```

In `_berufe` die Feldliste des Werkzeugs erweitern: `("beruf", "status", "ohdab_id", "niveau_unsicher", "geprueft", "hinweis", "stellung", "stellung_geprueft")`. Docstring des Moduls (Zeile 21–24) um die Stellungsregeln ergänzen.

- [ ] **Step 5: Modell**

`CSV_FELDER` um `"stellung", "stellung_geprueft"` erweitern; `export const STELLUNGEN = ["arbeiter", "angestellte", "beamte", "selbstaendige", "freie_berufe", "unternehmer", "ohne_erwerb", "kaufleute", "unbestimmt"];` In `baueModell` je Zeile `stellung: (k.stellung || "").trim(), stellung_geprueft: k.stellung_geprueft || ""`. Neue Funktionen:

```js
export function setzeStellung(m, s, klasse) {
  if (!STELLUNGEN.includes(klasse)) return [];
  return aendere(m, s, { stellung: klasse, stellung_geprueft: "ja" });
}
export function schalteStellungGeprueft(m, s) {
  const z = m.zeilen.get(s); if (!z || !z.stellung) return [];
  return aendere(m, s, { stellung_geprueft: z.stellung_geprueft === "ja" ? "" : "ja" });
}
```

`fortschritt` um `stellungGeprueft: l.filter((z) => z.stellung_geprueft === "ja").length` erweitern.

- [ ] **Step 6: Werkzeug**

In `berufe.html`: im Kopf nach `#niveau` ein `<select id="stellung" title="Ziffern 1–9">` mit den neun Klassen (Text aus einer Konstante `STELLUNG_TEXT` wie in `STELLUNGEN` in stellung.py, Reihenfolge = Zifferntaste) und `<button id="stellung-geprueft" title="Taste T">Stellung geprüft <kbd>T</kbd></button>`; im Filterblock `<label><input type="checkbox" id="nur-stellung"> Stellung offen</label>` (Filter: `z.stellung_geprueft !== "ja"`; dabei die Status-Radio-Logik unverändert lassen). `zeichneAktiv`: `select.value = z.stellung || "unbestimmt"`, `aria-pressed` auf dem Button. Ereignisse: `change` am Select → `speichere(setzeStellung(m, aktiv, value)); zeichne();`; Klick/Taste `t` → `schalteStellungGeprueft`; Tasten `1`–`9` → `setzeStellung(m, aktiv, STELLUNGEN[k-1])` und danach `naechsterOffener(vorher)` **nur**, wenn der Filter „Stellung offen“ aktiv ist (sonst `zeichne()`). Fortschrittszeile ergänzen: `· Stellung: ${f.stellungGeprueft} geprüft`. Listenpunkt: bei aktivem Filter „Stellung offen“ Farbe des Punkts nach Stellung statt Niveau (`FARBEN_STELLUNG`, neun Okabe-Ito-nahe Farben, `unbestimmt` grau).

- [ ] **Step 7: Tests und Handprobe**

Run: `python3 -m pytest tests/test_serve.py -q; node --test werkzeuge/tests/`
Dann Dev-Server (läuft bereits auf 8765; nach Server-Änderung neu starten) und `http://localhost:8765/werkzeuge/berufe.html` öffnen: Ziffer setzt Klasse, Zeile springt weiter, CSV enthält `stellung_geprueft=ja`.

- [ ] **Step 8: Commit**

```bash
git add werkzeuge/serve.py werkzeuge/js/berufe_modell.js werkzeuge/berufe.html tests/test_serve.py werkzeuge/tests/berufe_modell.test.js
git commit -m "feat(werkzeuge/berufe): Stellung prüfen (Zifferntasten, Filter „Stellung offen“, Server-Validierung)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Modul `gruppen.py` und `gruppen_vorschlag.py`

**Files:**
- Create: `pipeline/lib/gruppen.py`, `werkzeuge/gruppen_vorschlag.py`
- Test: `tests/test_gruppen.py`

**Interfaces:**
- Produces: `GRUPPEN: dict[str, str]` (14 Schlüssel → Anzeige), `FELDER_GRUPPEN = ["ohdab_id", "norm", "nennungen", "gruppe", "geprueft", "bearbeiter", "datum", "hinweis"]`, `gruppe_vorschlag(item) -> str`, `lade_gruppen(zeilen) -> dict[str, dict]` (ohdab_id → Zeile), `gruppe_export(zeile) -> str` (`gruppe` wenn `geprueft=ja`, sonst `"ungeprueft"`), `werkzeuge.gruppen_vorschlag.baue_gruppen(berufe, ohdab, alt, datum) -> list[dict]`.

- [ ] **Step 1: Test**

```python
# tests/test_gruppen.py
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.gruppen import FELDER_GRUPPEN, GRUPPEN, gruppe_export, gruppe_vorschlag, lade_gruppen
from werkzeuge.gruppen_vorschlag import baue_gruppen


def item(norm, gattung):
    return dict(norm=norm, gattung=gattung, niveau="fachlich", gattung_id="B 1")


def test_vokabular():
    assert list(GRUPPEN) == ["bergbau", "metall_maschinen", "bau", "holz_moebel", "textil_bekleidung", "lebensmittel", "handel",
                             "gastgewerbe", "verkehr_bahn_post", "verwaltung", "bildung_kultur_kirche", "gesundheit", "haus_reinigung", "sonstige"]
    assert FELDER_GRUPPEN == ["ohdab_id", "norm", "nennungen", "gruppe", "geprueft", "bearbeiter", "datum", "hinweis"]


def test_vorschlag_aus_gattung_und_norm():
    assert gruppe_vorschlag(item("Bergmann/-frau", "Berufe im Berg- und Tagebau – fachlich")) == "bergbau"
    assert gruppe_vorschlag(item("Kokereiarbeiter/in", "Berufe in der Kokerei")) == "bergbau"
    assert gruppe_vorschlag(item("Schlosser/in", "Berufe im Metallbau")) == "metall_maschinen"
    assert gruppe_vorschlag(item("Maurer/in", "Berufe im Hochbau")) == "bau"
    assert gruppe_vorschlag(item("Tischler/in", "Berufe in der Holz- und Möbelherstellung")) == "holz_moebel"
    assert gruppe_vorschlag(item("Schneider/in", "Berufe in der Bekleidungs-, Hut- und Mützenherstellung")) == "textil_bekleidung"
    assert gruppe_vorschlag(item("Bäcker/in", "Berufe in der Backwarenherstellung")) == "lebensmittel"
    assert gruppe_vorschlag(item("Kaufmann/-frau", "Kaufleute im Handel")) == "handel"
    assert gruppe_vorschlag(item("Gastwirt/in", "Berufe in der Gastronomie")) == "gastgewerbe"
    assert gruppe_vorschlag(item("Lokomotivführer/in", "Triebfahrzeugführer/innen im Eisenbahnverkehr")) == "verkehr_bahn_post"
    assert gruppe_vorschlag(item("Postbote/-botin", "Berufe für Post- und Zustelldienste")) == "verkehr_bahn_post"
    assert gruppe_vorschlag(item("Stadtsekretär/in", "Berufe in der öffentlichen Verwaltung")) == "verwaltung"
    assert gruppe_vorschlag(item("Lehrer/in", "Lehrkräfte in der Sekundarstufe")) == "bildung_kultur_kirche"
    assert gruppe_vorschlag(item("Pfarrer/in", "Theologen und Seelsorger")) == "bildung_kultur_kirche"
    assert gruppe_vorschlag(item("Arzt/Ärztin", "Ärzte/Ärztinnen")) == "gesundheit"
    assert gruppe_vorschlag(item("Hebamme", "Berufe in der Geburtshilfe")) == "gesundheit"
    assert gruppe_vorschlag(item("Hausangestellte/r", "Hauswirtschaftliche Berufe")) == "haus_reinigung"
    assert gruppe_vorschlag(item("Invalide/Invalidin", "Invalide")) == "sonstige"


def test_export_und_baue():
    assert gruppe_export(dict(gruppe="bergbau", geprueft="ja")) == "bergbau"
    assert gruppe_export(dict(gruppe="bergbau", geprueft="")) == "ungeprueft"
    berufe = [dict(schreibweise="Bergm.", nennungen="9", ohdab_id="B 21112-100", geprueft="ja"),
              dict(schreibweise="Bergarb.", nennungen="4", ohdab_id="B 21112-100", geprueft="ja"),
              dict(schreibweise="Kfm", nennungen="3", ohdab_id="", geprueft="")]
    ohdab = {"B 21112-100": dict(item("Bergmann/-frau", "Berufe im Berg- und Tagebau"), ohdab_id="B 21112-100")}
    alt = [dict(ohdab_id="B 21112-100", norm="Bergmann/-frau", nennungen="1", gruppe="metall_maschinen", geprueft="ja", bearbeiter="christos", datum="2026-09-25", hinweis="")]
    neu = baue_gruppen(berufe, ohdab, alt, "2026-09-26")
    assert neu == [dict(ohdab_id="B 21112-100", norm="Bergmann/-frau", nennungen="13", gruppe="metall_maschinen", geprueft="ja", bearbeiter="christos", datum="2026-09-25", hinweis="")]
    neu2 = baue_gruppen(berufe, ohdab, [], "2026-09-26")
    assert neu2[0]["gruppe"] == "bergbau" and neu2[0]["geprueft"] == "" and neu2[0]["bearbeiter"] == "gruppen_vorschlag"
    assert list(lade_gruppen(neu2)) == ["B 21112-100"]
```

- [ ] **Step 2: Test laufen lassen — erwartet ImportError**

Run: `python3 -m pytest tests/test_gruppen.py -q`

- [ ] **Step 3: Modul**

```python
# pipeline/lib/gruppen.py
"""Berufsgruppen (Branche) je OhdAB-Item (Teilprojekt 5a, Spec §5.2): Vokabular, Vorschlag aus Gattung/Norm, Export."""
from __future__ import annotations

import re

GRUPPEN = {
    "bergbau": "Bergbau und Kokerei",
    "metall_maschinen": "Metall, Maschinen, Elektro",
    "bau": "Bau",
    "holz_moebel": "Holz und Möbel",
    "textil_bekleidung": "Textil und Bekleidung",
    "lebensmittel": "Lebensmittel",
    "handel": "Handel",
    "gastgewerbe": "Gastgewerbe",
    "verkehr_bahn_post": "Verkehr, Bahn, Post",
    "verwaltung": "Verwaltung, Polizei, Recht",
    "bildung_kultur_kirche": "Bildung, Kultur, Kirche",
    "gesundheit": "Gesundheit",
    "haus_reinigung": "Haushalt und Reinigung",
    "sonstige": "Sonstige",
}
UNGEPRUEFT = "ungeprueft"
FELDER_GRUPPEN = ["ohdab_id", "norm", "nennungen", "gruppe", "geprueft", "bearbeiter", "datum", "hinweis"]
AUTOMATIK = "gruppen_vorschlag"

# Reihenfolge = Priorität; geprüft wird Gattung + Norm.
_REGELN = [
    ("bergbau", r"berg- und tagebau|bergbau|kokerei|sprengtechnik|grube|zeche|hauer|steiger"),
    ("verkehr_bahn_post", r"eisenbahn|bahn|post|zustell|triebfahrzeug|fahrzeugführ|kraftfahr|straßenbahn|schiff|verkehr|lager|fuhr"),
    ("verwaltung", r"öffentliche verwaltung|polizei|justiz|recht|steuer|zoll|verwaltungs|sekretär|beamt|gericht|feuerwehr|militär|soldat"),
    ("bildung_kultur_kirche", r"lehrkr|lehrer|erzieh|hochschul|wissenschaft|theolog|seelsorg|pfarrer|kirche|kunst|musik|schauspiel|bibliothek|schriftsteller|journalist|redakt"),
    ("gesundheit", r"ärzt|arzt|apothek|geburtshilf|hebamme|pflege|krankenpfleg|heilpraktik|zahn|masseur|gesundheit|dentist|tierarzt"),
    ("gastgewerbe", r"gastronomie|gastwirt|schankwirt|hotel|kellner|koch|köchin|pension"),
    ("lebensmittel", r"backwaren|bäcker|konditor|fleisch|metzger|schlachter|lebensmittel|getränke|brau|molkerei|müller|mühle|nahrungsmittel"),
    ("handel", r"kaufleute|handel|verkauf|händler|kaufmann|verkäufer|drogist|kommission|makler|agent"),
    ("textil_bekleidung", r"bekleidung|textil|schneider|näh|weber|spinn|schuh|hut|kürschner|wäsche|sattler|polster"),
    ("holz_moebel", r"holz|möbel|tischler|schreiner|zimmer|drechsler|böttcher|stellmacher|korb"),
    ("bau", r"hochbau|tiefbau|bau|maurer|dachdeck|maler|anstreich|glaser|stukkat|installat|klempner|schornstein|fliesen|ofensetz"),
    ("metall_maschinen", r"metall|maschinen|schlosser|dreher|schweiß|gießer|hütten|walz|schmied|elektr|mechanik|monteur|heizer|kessel|anlagen|produktion|fabrik|technik|ingenieur|chem"),
    ("haus_reinigung", r"hauswirtschaft|hausangestellt|dienstmädchen|reinigung|wäscher|plätt|hausmeister|portier|wächter"),
]


def gruppe_vorschlag(item: dict) -> str:
    text = f"{item.get('gattung', '')} | {item.get('norm', '')}".lower()
    for gruppe, muster in _REGELN:
        if re.search(muster, text):
            return gruppe
    return "sonstige"


def lade_gruppen(zeilen: list[dict]) -> dict[str, dict]:
    return {z["ohdab_id"].strip(): {k: (v or "").strip() for k, v in z.items()} for z in zeilen if (z.get("ohdab_id") or "").strip()}


def gruppe_export(zeile: dict | None) -> str:
    if zeile and zeile.get("geprueft") == "ja" and zeile.get("gruppe") in GRUPPEN:
        return zeile["gruppe"]
    return UNGEPRUEFT
```

Hinweis: Die Regel-Reihenfolge ist absichtlich so, dass „Bergbau“ vor „Verkehr“ (Lager/Fuhr) und „Handel“ nach Gastgewerbe/Lebensmittel greift. Läuft ein Test-Fall in die falsche Gruppe, Muster verfeinern (z. B. Wortgrenzen), nicht den Test ändern.

- [ ] **Step 4: Skript**

```python
# werkzeuge/gruppen_vorschlag.py
"""Berufsgruppe je OhdAB-Item, das in kuratierung/berufe.csv geprüft vorkommt (Teilprojekt 5a, Spec §5.2).

Aufruf: python3 werkzeuge/gruppen_vorschlag.py [--wurzel PFAD]
Schreibt kuratierung/gruppen.csv (Upsert je ohdab_id: geprüfte Zeilen bleiben, nennungen wird nachgeführt).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import datetime
import json
from collections import defaultdict
from pathlib import Path

from pipeline.lib.berufe import lade_ohdab
from pipeline.lib.gruppen import AUTOMATIK, FELDER_GRUPPEN, gruppe_vorschlag, lade_gruppen
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv


def baue_gruppen(berufe: list[dict], ohdab: dict[str, dict], alt: list[dict], datum: str) -> list[dict]:
    nennungen: dict[str, int] = defaultdict(int)
    for z in berufe:
        oid = (z.get("ohdab_id") or "").strip()
        if oid and z.get("geprueft") == "ja" and oid in ohdab:
            nennungen[oid] += int(z.get("nennungen") or 0)
    bekannt = lade_gruppen(alt)
    out = []
    for oid in sorted(nennungen, key=lambda o: (-nennungen[o], o)):
        z = bekannt.get(oid)
        if z and z.get("geprueft") == "ja":
            out.append(dict(z, nennungen=str(nennungen[oid])))
        else:
            out.append(dict(ohdab_id=oid, norm=ohdab[oid]["norm"], nennungen=str(nennungen[oid]), gruppe=gruppe_vorschlag(ohdab[oid]),
                            geprueft="", bearbeiter=AUTOMATIK, datum=datum, hinweis=(z or {}).get("hinweis", "")))
    return out


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wurzel", default=None)
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    pfad = W / "kuratierung" / "gruppen.csv"
    alt = lies_csv(pfad) if pfad.exists() else []
    neu = baue_gruppen(lies_csv(W / "kuratierung" / "berufe.csv"), lade_ohdab(W / "kuratierung" / "ohdab.csv"), alt, datetime.date.today().isoformat())
    schreib_csv(pfad, neu, FELDER_GRUPPEN)
    k = dict(items=len(neu), geprueft=sum(z["geprueft"] == "ja" for z in neu))
    print(json.dumps(k, ensure_ascii=False)); return k


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Tests, echter Lauf, Commit**

Run: `python3 -m pytest tests/test_gruppen.py -q && python3 werkzeuge/gruppen_vorschlag.py`
Expected: PASS; ≈ 1.000 Zeilen in `kuratierung/gruppen.csv`; Verteilung mit `cut -d, -f4 kuratierung/gruppen.csv | sort | uniq -c` ansehen — `sonstige` unter 15 %.

```bash
git add pipeline/lib/gruppen.py werkzeuge/gruppen_vorschlag.py tests/test_gruppen.py kuratierung/gruppen.csv
git commit -m "feat(gruppen): Berufsgruppen je OhdAB-Item mit Vorschlag aus Gattung und Norm

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Modul `gewerbe.py` und `gewerbe_vorschlag.py` (Teil III)

**Files:**
- Create: `pipeline/lib/gewerbe.py`, `werkzeuge/gewerbe_vorschlag.py`
- Test: `tests/test_gewerbe.py`

**Interfaces:**
- Produces: `ARTEN: dict[str, str]`, `FELDER_GEWERBE = ["rubrik", "betriebe", "gruppe", "art", "geprueft", "bearbeiter", "datum", "hinweis"]`, `rubrik_von(firmenname) -> tuple[str, str]` (Firma ohne Suffix, Rubrik), `gewerbe_vorschlag(rubrik) -> tuple[str, str]` (Gruppe, Art), `lade_gewerbe(zeilen) -> dict[str, dict]` (Rubrik → Zeile), `gewerbe_export(zeile) -> tuple[str, str]` (Gruppe, Art oder `("ungeprueft", "ungeprueft")`), `betriebsschluessel(eintrag) -> str`, `werkzeuge.gewerbe_vorschlag.baue_gewerbe(eintraege, alt, datum) -> list[dict]`.

- [ ] **Step 1: Test**

```python
# tests/test_gewerbe.py
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.gewerbe import ARTEN, FELDER_GEWERBE, betriebsschluessel, gewerbe_export, gewerbe_vorschlag, lade_gewerbe, rubrik_von
from werkzeuge.gewerbe_vorschlag import baue_gewerbe


def test_rubrik_aus_firmenname():
    assert rubrik_von("M. Jäger, Althandlung") == ("M. Jäger", "Althandlung")
    assert rubrik_von("Fritz Loosen, Architekt") == ("Fritz Loosen", "Architekt")
    assert rubrik_von("Müller & Co., G.m.b.H., Kohlen") == ("Müller & Co., G.m.b.H.", "Kohlen")
    assert rubrik_von("Ohne Suffix") == ("Ohne Suffix", "")
    assert rubrik_von("") == ("", "")


def test_vorschlag():
    assert list(ARTEN) == ["handwerk", "handel", "gastgewerbe", "dienstleistung", "industrie", "freier_beruf", "sonstige"]
    assert gewerbe_vorschlag("Bäcker") == ("lebensmittel", "handwerk")
    assert gewerbe_vorschlag("Kolonialwaren") == ("lebensmittel", "handel")
    assert gewerbe_vorschlag("Schankwirt") == ("gastgewerbe", "gastgewerbe")
    assert gewerbe_vorschlag("Schneider für Herren") == ("textil_bekleidung", "handwerk")
    assert gewerbe_vorschlag("Architekt") == ("bau", "freier_beruf")
    assert gewerbe_vorschlag("Fuhrgeschäft") == ("verkehr_bahn_post", "dienstleistung")
    assert gewerbe_vorschlag("Hebamme") == ("gesundheit", "freier_beruf")
    assert gewerbe_vorschlag("Eisenwaren") == ("handel", "handel")
    assert gewerbe_vorschlag("Maschinenfabrik") == ("metall_maschinen", "industrie")
    assert gewerbe_vorschlag("Bergwerks- und Hüttenbedarf") == ("bergbau", "handel")
    assert gewerbe_vorschlag("Xyz") == ("sonstige", "sonstige")


def test_export_schluessel_und_baue():
    assert gewerbe_export(dict(gruppe="lebensmittel", art="handwerk", geprueft="ja")) == ("lebensmittel", "handwerk")
    assert gewerbe_export(dict(gruppe="lebensmittel", art="handwerk", geprueft="")) == ("ungeprueft", "ungeprueft")
    assert gewerbe_export(None) == ("ungeprueft", "ungeprueft")
    e = dict(Firmenname="M. Jäger, Althandlung", strasse_norm="brüningstraße", hausnr="13", Vorort="")
    assert betriebsschluessel(e) == "m jaeger|brüningstraße|13|"
    eintraege = [dict(teil="III", Firmenname="A, Bäcker"), dict(teil="III", Firmenname="B, Bäcker"), dict(teil="III", Firmenname="C, Kohlen"),
                 dict(teil="I", Firmenname="D, Bäcker"), dict(teil="III", Firmenname="Ohne")]
    alt = [dict(rubrik="Bäcker", betriebe="1", gruppe="handel", art="handel", geprueft="ja", bearbeiter="christos", datum="d", hinweis="")]
    neu = baue_gewerbe(eintraege, alt, "2026-09-26")
    assert [(z["rubrik"], z["betriebe"], z["gruppe"], z["art"], z["geprueft"]) for z in neu] == [("Bäcker", "2", "handel", "handel", "ja"), ("Kohlen", "1", "handel", "handel", "")]
    assert list(lade_gewerbe(neu)) == ["Bäcker", "Kohlen"]
```

- [ ] **Step 2: Test laufen lassen — erwartet ImportError**

- [ ] **Step 3: Modul**

```python
# pipeline/lib/gewerbe.py
"""Gewerberubriken aus Teil III (Teilprojekt 5a, Spec §5.3). Die Rubrik steht nicht in einer eigenen Spalte, sondern
als Suffix hinter dem letzten Komma des Firmennamens („M. Jäger, Althandlung“)."""
from __future__ import annotations

import re

from pipeline.lib.gruppen import GRUPPEN  # noqa: F401 — gleiche Gruppen wie Teil I, damit beide vergleichbar sind
from pipeline.lib.berufe import falte_form

ARTEN = {"handwerk": "Handwerk", "handel": "Handel", "gastgewerbe": "Gastgewerbe", "dienstleistung": "Dienstleistung",
         "industrie": "Industrie", "freier_beruf": "Freier Beruf", "sonstige": "Sonstige"}
UNGEPRUEFT = "ungeprueft"
FELDER_GEWERBE = ["rubrik", "betriebe", "gruppe", "art", "geprueft", "bearbeiter", "datum", "hinweis"]
AUTOMATIK = "gewerbe_vorschlag"


def rubrik_von(firmenname: str) -> tuple[str, str]:
    """(Firma ohne Suffix, Rubrik). Ohne Komma keine Rubrik."""
    f = (firmenname or "").strip()
    if "," not in f:
        return f, ""
    firma, rubrik = f.rsplit(",", 1)
    return firma.strip(), rubrik.strip()


# (Gruppe, Art, Muster) — erste Regel gewinnt; Art-Regeln nach Wortform am Ende.
_REGELN = [
    ("bergbau", "handel", r"bergwerks|hütten|grubenholz"),
    ("gesundheit", "freier_beruf", r"arzt|ärzt|zahn|dentist|hebamme|heilpraktik|masseur|tierarzt"),
    ("gesundheit", "handel", r"apotheke|drogen|sanitäts|optik"),
    ("bau", "freier_beruf", r"architekt|vermessung|landmesser|ingenieurbüro|ingenieur"),
    ("bau", "handwerk", r"baugeschäft|bauunternehm|dachdeck|maler|anstreich|maurer|zimmer|glaser|klempner|installat|stukkat|fliesen|ofensetz|schornstein|bauklempner"),
    ("bau", "handel", r"baustoff|baumaterial|zement|kalk"),
    ("gastgewerbe", "gastgewerbe", r"schankwirt|gastwirt|gaststätte|restaurant|hotel|café|kaffee|pension|wirtschaft"),
    ("lebensmittel", "handwerk", r"bäcker|konditor|metzger|fleischer|schlachter|brot$|brauerei|molkerei|mühle"),
    ("lebensmittel", "handel", r"lebensmittel|kolonialwaren|feinkost|gemüse|obst|südfrüchte|kartoffel|eier|butter|milch|fisch|geflügel|bier|wein|spirituosen|tabak|zigar|delikatess|süßwaren|landesprodukte|futtermittel|furage|mehl"),
    ("textil_bekleidung", "handwerk", r"schneider|schuhmacher|putz|kürschner|hut|sattler|polster|dekorateur|näh|wäscherei|heißmangel|plätt"),
    ("textil_bekleidung", "handel", r"kleidung|ausstattung|textil|manufaktur|schuhwaren|strumpf|wäsche|stoffe|tuch"),
    ("holz_moebel", "handwerk", r"tischler|schreiner|drechsler|böttcher|stellmacher|korb|einrahm"),
    ("holz_moebel", "handel", r"möbel|holz"),
    ("verkehr_bahn_post", "dienstleistung", r"fuhr|transport|spedition|automobilverm|kraftwagen|taxi|schiff|umzug|lagerhaus"),
    ("metall_maschinen", "industrie", r"fabrik|werk$|werke|gießerei|walzwerk|hütte$|apparatebau|maschinenbau|stahlbau"),
    ("metall_maschinen", "handwerk", r"schlosser|schmied|dreher|mechanik|elektr|installation|reparatur|lackier|klempner|uhrmacher|gold|silber|graveur|feinmechanik"),
    ("handel", "handel", r"eisenwaren|handlung|waren|handel|geschäft|bedarf|artikel|großhandel|vertrieb|verkauf|kohlen|farben|papier|schreib|bücher|buchhandlung|fahrräder|automobil|reifen"),
    ("bildung_kultur_kirche", "freier_beruf", r"musiklehr|lehrer|unterricht|schule|künstler|maler$|bildhauer|fotograf|schriftsteller|verlag|zeitung|buchdruck|druckerei"),
    ("verwaltung", "freier_beruf", r"rechtsanwalt|anwalt|notar|steuerberat|bücherrevisor|wirtschaftsprüf|auskunft|patent"),
    ("verwaltung", "dienstleistung", r"immobilien|hypothek|versicherung|bank|sparkasse|makler|agentur|vertretung"),
    ("haus_reinigung", "dienstleistung", r"reinigung|friseur|bad|wäscherei|bestattung|beerdigung|gärtner|gartenbau|blumen"),
]
_HANDWERK_ENDUNG = re.compile(r"(meister|ei)$", re.I)


def gewerbe_vorschlag(rubrik: str) -> tuple[str, str]:
    t = (rubrik or "").lower()
    for gruppe, art, muster in _REGELN:
        if re.search(muster, t):
            return gruppe, art
    if _HANDWERK_ENDUNG.search(t):
        return "sonstige", "handwerk"
    return "sonstige", "sonstige"


def lade_gewerbe(zeilen: list[dict]) -> dict[str, dict]:
    return {z["rubrik"].strip(): {k: (v or "").strip() for k, v in z.items()} for z in zeilen if (z.get("rubrik") or "").strip()}


def gewerbe_export(zeile: dict | None) -> tuple[str, str]:
    if zeile and zeile.get("geprueft") == "ja" and zeile.get("gruppe") in GRUPPEN and zeile.get("art") in ARTEN:
        return zeile["gruppe"], zeile["art"]
    return UNGEPRUEFT, UNGEPRUEFT


def betriebsschluessel(eintrag: dict) -> str:
    """Derselbe Betrieb unter mehreren Rubriken: gleiche Firma (ohne Suffix, gefaltet) an gleicher Adresse."""
    firma, _ = rubrik_von(eintrag.get("Firmenname", ""))
    return "|".join([falte_form(firma), eintrag.get("strasse_norm", ""), eintrag.get("hausnr", ""), eintrag.get("Vorort", "")])
```

Die Reihenfolge der Regeln ist so gewählt, dass spezifische Muster (Bergwerksbedarf, Architekt, Bäcker) vor generischen („handlung“, „waren“) greifen. Fällt ein Testfall falsch, Muster ergänzen oder umsortieren.

- [ ] **Step 4: Skript**

```python
# werkzeuge/gewerbe_vorschlag.py
"""Gewerberubriken aus Teil III → kuratierung/gewerbe.csv (Teilprojekt 5a, Spec §5.3).

Aufruf: python3 werkzeuge/gewerbe_vorschlag.py [--wurzel PFAD]
Upsert je Rubrik: geprüfte Zeilen bleiben (betriebe wird nachgeführt), sonst Vorschlag.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import datetime
import json
from collections import Counter
from pathlib import Path

from pipeline.lib.gewerbe import AUTOMATIK, FELDER_GEWERBE, gewerbe_vorschlag, lade_gewerbe, rubrik_von
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv


def baue_gewerbe(eintraege: list[dict], alt: list[dict], datum: str) -> list[dict]:
    betriebe = Counter(rubrik_von(e.get("Firmenname", ""))[1] for e in eintraege if e.get("teil") == "III")
    betriebe.pop("", None)
    bekannt = lade_gewerbe(alt)
    out = []
    for rubrik in sorted(betriebe, key=lambda r: (-betriebe[r], r)):
        z = bekannt.get(rubrik)
        if z and z.get("geprueft") == "ja":
            out.append(dict(z, betriebe=str(betriebe[rubrik])))
        else:
            gruppe, art = gewerbe_vorschlag(rubrik)
            out.append(dict(rubrik=rubrik, betriebe=str(betriebe[rubrik]), gruppe=gruppe, art=art, geprueft="",
                            bearbeiter=AUTOMATIK, datum=datum, hinweis=(z or {}).get("hinweis", "")))
    return out


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wurzel", default=None)
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    pfad = W / "kuratierung" / "gewerbe.csv"
    alt = lies_csv(pfad) if pfad.exists() else []
    neu = baue_gewerbe(lies_csv(W / "build" / "eintraege.csv"), alt, datetime.date.today().isoformat())
    schreib_csv(pfad, neu, FELDER_GEWERBE)
    k = dict(rubriken=len(neu), betriebe=sum(int(z["betriebe"]) for z in neu), geprueft=sum(z["geprueft"] == "ja" for z in neu))
    print(json.dumps(k, ensure_ascii=False)); return k


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Tests, echter Lauf, Commit**

Run: `python3 -m pytest tests/test_gewerbe.py -q && python3 werkzeuge/gewerbe_vorschlag.py`
Expected: 849 Rubriken, 18.864 Betriebe. Verteilung `sonstige` prüfen (< 20 %).

```bash
git add pipeline/lib/gewerbe.py werkzeuge/gewerbe_vorschlag.py tests/test_gewerbe.py kuratierung/gewerbe.csv
git commit -m "feat(gewerbe): Rubriken aus Teil III mit Vorschlag für Gruppe und Art

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Generisches Prüfwerkzeug `zuordnung.html` (Gruppen und Gewerbe) + Server-Endpunkte

**Files:**
- Create: `werkzeuge/js/zuordnung_modell.js`, `werkzeuge/zuordnung.html`
- Modify: `werkzeuge/serve.py` (Docstring, `do_POST`, neue Methode `_zuordnung`)
- Test: `werkzeuge/tests/zuordnung_modell.test.js`, `tests/test_serve.py`

**Interfaces:**
- Consumes: `GRUPPEN`, `ARTEN`, `FELDER_GRUPPEN`, `FELDER_GEWERBE`, `lade_gruppen`, `lade_gewerbe`.
- Produces: `POST /kuratierung/gruppen.csv` und `POST /kuratierung/gewerbe.csv` (`{"zeilen": [...]}`, Upsert nach `ohdab_id` bzw. `rubrik`, setzt `bearbeiter=christos`, `datum`; 400 bei unbekanntem Schlüssel, unbekanntem Vokabular, `geprueft` ∉ {ja, leer}, `geprueft=ja` mit leerem Feld). JS: `baueModell(zeilen, konfig)`, `liste(m)`, `setzeFeld(m, schluessel, feld, wert)`, `setzeGeprueft(m, schluessel, ja)`, `rueckgaengig(m)`, `fortschritt(m)`, `zumSpeichern(z, konfig)`; `KONFIG = { gruppen: {...}, gewerbe: {...} }`.

- [ ] **Step 1: JS-Test**

```js
// werkzeuge/tests/zuordnung_modell.test.js
import test from "node:test";
import assert from "node:assert/strict";
import { KONFIG, baueModell, fortschritt, liste, rueckgaengig, setzeFeld, setzeGeprueft, zumSpeichern } from "../js/zuordnung_modell.js";

const Z = [
  { rubrik: "Bäcker", betriebe: "536", gruppe: "lebensmittel", art: "handwerk", geprueft: "", bearbeiter: "gewerbe_vorschlag", datum: "", hinweis: "" },
  { rubrik: "Schankwirt", betriebe: "904", gruppe: "gastgewerbe", art: "gastgewerbe", geprueft: "ja", bearbeiter: "christos", datum: "", hinweis: "" },
];

test("Konfiguration, Liste nach Menge, Felder mit Vokabular", () => {
  const m = baueModell(Z, KONFIG.gewerbe);
  assert.deepEqual(liste(m).map((z) => z.schluessel), ["Schankwirt", "Bäcker"]);
  assert.deepEqual(KONFIG.gewerbe.felder.map((f) => f.name), ["gruppe", "art"]);
  assert.equal(KONFIG.gruppen.schluessel, "ohdab_id");
  assert.deepEqual(setzeFeld(m, "Bäcker", "art", "adel"), []);              // unbekanntes Vokabular
  assert.deepEqual(setzeFeld(m, "Bäcker", "art", "handel").map((z) => z.art), ["handel"]);
  assert.deepEqual(fortschritt(m), { geprueft: 1, gesamt: 2, mengeGeprueft: 904, mengeGesamt: 1440 });
});

test("geprüft nur mit gefüllten Feldern; Rückgängig; Speichern nur CSV-Felder", () => {
  const m = baueModell([{ ...Z[0], gruppe: "" }], KONFIG.gewerbe);
  assert.deepEqual(setzeGeprueft(m, "Bäcker", true), []);
  setzeFeld(m, "Bäcker", "gruppe", "lebensmittel");
  assert.deepEqual(setzeGeprueft(m, "Bäcker", true).map((z) => z.geprueft), ["ja"]);
  assert.deepEqual(rueckgaengig(m).map((z) => z.geprueft), [""]);
  const s = zumSpeichern(m.zeilen.get("Bäcker"), KONFIG.gewerbe);
  assert.deepEqual(Object.keys(s), ["rubrik", "gruppe", "art", "geprueft", "hinweis"]);
});
```

- [ ] **Step 2: Test laufen lassen — erwartet FAIL** (`node --test werkzeuge/tests/`)

- [ ] **Step 3: Modell**

```js
// werkzeuge/js/zuordnung_modell.js — Zustand des generischen Zuordnungswerkzeugs (Gruppen je OhdAB-Item, Gewerbe je
// Rubrik): eine Zeile je Schlüssel, ein oder zwei Felder mit festem Vokabular, geprüft-Schalter. Ohne DOM (node:test).
const GRUPPEN = ["bergbau", "metall_maschinen", "bau", "holz_moebel", "textil_bekleidung", "lebensmittel", "handel", "gastgewerbe",
  "verkehr_bahn_post", "verwaltung", "bildung_kultur_kirche", "gesundheit", "haus_reinigung", "sonstige"];
const ARTEN = ["handwerk", "handel", "gastgewerbe", "dienstleistung", "industrie", "freier_beruf", "sonstige"];
export const KONFIG = {
  gruppen: { datei: "gruppen.csv", schluessel: "ohdab_id", anzeige: "norm", menge: "nennungen", titel: "Berufsgruppen je OhdAB-Item",
    felder: [{ name: "gruppe", vokabular: GRUPPEN }] },
  gewerbe: { datei: "gewerbe.csv", schluessel: "rubrik", anzeige: "rubrik", menge: "betriebe", titel: "Gewerberubriken (Teil III)",
    felder: [{ name: "gruppe", vokabular: GRUPPEN }, { name: "art", vokabular: ARTEN }] },
};
const VERLAUF_MAX = 30;

export function baueModell(zeilen, konfig) {
  const m = { konfig, zeilen: new Map(), verlauf: [] };
  for (const k of zeilen) {
    const s = (k[konfig.schluessel] || "").trim();
    if (!s) continue;
    const z = { schluessel: s, anzeige: (k[konfig.anzeige] || "").trim(), menge: Number(k[konfig.menge]) || 0, geprueft: k.geprueft || "",
      hinweis: k.hinweis || "", bearbeiter: (k.bearbeiter || "").trim() };
    for (const f of konfig.felder) z[f.name] = (k[f.name] || "").trim();
    m.zeilen.set(s, z);
  }
  return m;
}

export function liste(m) {
  return [...m.zeilen.values()].sort((a, b) => b.menge - a.menge || a.schluessel.localeCompare(b.schluessel, "de"));
}

function merke(m) {
  m.verlauf.push(new Map([...m.zeilen].map(([k, z]) => [k, { ...z }])));
  if (m.verlauf.length > VERLAUF_MAX) m.verlauf.shift();
}

function aendere(m, s, werte) {
  const z = m.zeilen.get(s);
  if (!z || Object.entries(werte).every(([k, v]) => z[k] === v)) return [];
  merke(m); Object.assign(z, werte); return [z];
}

export function setzeFeld(m, s, feld, wert) {
  const f = m.konfig.felder.find((x) => x.name === feld);
  if (!f || !f.vokabular.includes(wert)) return [];
  return aendere(m, s, { [feld]: wert });
}

export function setzeGeprueft(m, s, ja) {
  const z = m.zeilen.get(s);
  if (!z || (ja && m.konfig.felder.some((f) => !z[f.name]))) return [];
  return aendere(m, s, { geprueft: ja ? "ja" : "" });
}

export function setzeHinweis(m, s, text) { return aendere(m, s, { hinweis: text }); }

export function rueckgaengig(m) {
  const alt = m.verlauf.pop();
  if (!alt) return null;
  const geaendert = [];
  for (const [k, z] of alt) {
    const jetzt = m.zeilen.get(k);
    if (!jetzt || Object.keys(z).some((f) => jetzt[f] !== z[f])) { m.zeilen.set(k, z); geaendert.push(z); }
  }
  return geaendert;
}

export function fortschritt(m) {
  const l = [...m.zeilen.values()], g = l.filter((z) => z.geprueft === "ja");
  return { geprueft: g.length, gesamt: l.length, mengeGeprueft: g.reduce((s, z) => s + z.menge, 0), mengeGesamt: l.reduce((s, z) => s + z.menge, 0) };
}

export function zumSpeichern(z, konfig) {
  const out = { [konfig.schluessel]: z.schluessel };
  for (const f of konfig.felder) out[f.name] = z[f.name];
  out.geprueft = z.geprueft; out.hinweis = z.hinweis;
  return out;
}
```

- [ ] **Step 4: Seite**

`werkzeuge/zuordnung.html`, Aufbau wie `berufe.html` (Stil übernehmen, `csvLesen`, `zeigeBanner`, `speichere` mit Promise-Kette und Sperre **wörtlich** kopieren; Speicherpfad `/kuratierung/${konfig.datei}`). Konfiguration aus `new URLSearchParams(location.search).get("tabelle")` (`gruppen` | `gewerbe`; sonst Banner „?tabelle=gruppen|gewerbe“). Links: Suchfeld, Radio ungeprüft/geprüft/alle, Fortschritt, Liste (Anzeige + Menge, geprüfte grau). Rechts: Kopf mit Schlüssel/Anzeige/Menge, je Feld ein `<select>` mit dem Vokabular (leerer Eintrag „–“), Button „Geprüft (G)“, „Rückgängig (Z)“, Hinweis-Input. Tastatur: Ziffern `1`–`9` setzen das **erste** Feld (Index in `vokabular`), Umschalt+Ziffer das zweite; `G` prüft und springt zur nächsten offenen Zeile (Logik `naechsterOffener` aus berufe.html übernehmen); Pfeiltasten. Beim Laden `../kuratierung/<datei>` lesen; bei `gruppen` zusätzlich `../kuratierung/berufe.csv` laden und je Item die Schreibweisen mit Nennungen als Belegtabelle zeigen (Spalten Schreibweise, Nennungen, Beruf).

- [ ] **Step 5: Server-Test** (`tests/test_serve.py`; im `server`-Fixture zwei Dateien anlegen)

```python
KOPF_GRUPPEN = "ohdab_id,norm,nennungen,gruppe,geprueft,bearbeiter,datum,hinweis"
KOPF_GEWERBE = "rubrik,betriebe,gruppe,art,geprueft,bearbeiter,datum,hinweis"
# im Fixture:
    (tmp_path / "kuratierung" / "gruppen.csv").write_text(KOPF_GRUPPEN + "\nB 21112-100,Bergmann/-frau,9,bergbau,,gruppen_vorschlag,2026-09-26,\n", encoding="utf-8")
    (tmp_path / "kuratierung" / "gewerbe.csv").write_text(KOPF_GEWERBE + "\nBäcker,536,lebensmittel,handwerk,,gewerbe_vorschlag,2026-09-26,\n", encoding="utf-8")


def test_zuordnung_post_gruppen_und_gewerbe(server):
    url, wurzel = server
    post(url + "/kuratierung/gruppen.csv", {"zeilen": [dict(ohdab_id="B 21112-100", gruppe="bergbau", geprueft="ja", hinweis="")]})
    g = list(csv.DictReader(open(wurzel / "kuratierung" / "gruppen.csv", encoding="utf-8")))
    assert g[0]["geprueft"] == "ja" and g[0]["bearbeiter"] == "christos" and g[0]["nennungen"] == "9" and g[0]["norm"] == "Bergmann/-frau"
    post(url + "/kuratierung/gewerbe.csv", {"zeilen": [dict(rubrik="Bäcker", gruppe="lebensmittel", art="handel", geprueft="ja", hinweis="x")]})
    w = list(csv.DictReader(open(wurzel / "kuratierung" / "gewerbe.csv", encoding="utf-8")))
    assert (w[0]["art"], w[0]["hinweis"], w[0]["betriebe"]) == ("handel", "x", "536")
    for kaputt in (dict(ohdab_id="B 0", gruppe="bergbau"), dict(ohdab_id="B 21112-100", gruppe="adel"), dict(ohdab_id="B 21112-100", gruppe="", geprueft="ja")):
        with pytest.raises(urllib.error.HTTPError) as e:
            post(url + "/kuratierung/gruppen.csv", {"zeilen": [kaputt]})
        assert e.value.code == 400
    with pytest.raises(urllib.error.HTTPError) as e:
        post(url + "/kuratierung/gewerbe.csv", {"zeilen": [dict(rubrik="Bäcker", gruppe="lebensmittel", art="adel")]})
    assert e.value.code == 400
```

- [ ] **Step 6: Server**

Imports: `from pipeline.lib.gruppen import FELDER_GRUPPEN, GRUPPEN, lade_gruppen` und `from pipeline.lib.gewerbe import ARTEN, FELDER_GEWERBE, lade_gewerbe`. Tabellenbeschreibung und Handler:

```python
ZUORDNUNGEN = {
    "gruppen": dict(felder=FELDER_GRUPPEN, schluessel="ohdab_id", lade=lade_gruppen, vokabular={"gruppe": GRUPPEN}),
    "gewerbe": dict(felder=FELDER_GEWERBE, schluessel="rubrik", lade=lade_gewerbe, vokabular={"gruppe": GRUPPEN, "art": ARTEN}),
}


def pruefe_zuordnung(z: dict, bekannt: set[str], schluessel: str, vokabular: dict[str, dict]) -> str:
    if not isinstance(z, dict):
        return "Zeile fehlt"
    k = str(z.get(schluessel, "")).strip()
    if k not in bekannt:
        return f"unbekannter Schlüssel: {k}"
    for feld, vok in vokabular.items():
        w = str(z.get(feld, "")).strip()
        if w and w not in vok:
            return f"unbekannter Wert für {feld}: {w}"
    if str(z.get("geprueft", "")).strip() not in ("", "ja"):
        return "geprueft muss ja oder leer sein"
    if str(z.get("geprueft", "")).strip() == "ja" and any(not str(z.get(f, "")).strip() for f in vokabular):
        return "geprueft=ja verlangt alle Felder"
    return ""
```

In `do_POST` vor dem `_KURATIERUNG`-Match: `m = re.fullmatch(r"/kuratierung/(gruppen|gewerbe)\.csv", self.path); if m: return self._zuordnung(m.group(1))`. Methode:

```python
    def _zuordnung(self, tabelle: str) -> None:
        t = ZUORDNUNGEN[tabelle]
        try:
            koerper = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            zeilen = koerper["zeilen"]; assert isinstance(zeilen, list)
        except (ValueError, KeyError, TypeError, AssertionError):
            return self._antwort(400, "ungültiger Inhalt")
        pfad = self.wurzel / "kuratierung" / f"{tabelle}.csv"
        if not pfad.exists():
            return self._antwort(404, f"{tabelle}.csv fehlt")
        alt = t["lade"](lies_csv(pfad))
        for z in zeilen:
            fehler = pruefe_zuordnung(z, set(alt), t["schluessel"], t["vokabular"])
            if fehler:
                return self._antwort(400, fehler)
        heute = datetime.date.today().isoformat()
        voll = [dict(alt[str(z[t["schluessel"]]).strip()], **{k: str(z.get(k, "")).strip() for k in (*t["vokabular"], "geprueft", "hinweis")},
                     bearbeiter="christos", datum=heute) for z in zeilen]
        n = upsert_viele(pfad, voll, t["schluessel"], t["felder"])
        self._antwort(200, f"{tabelle}.csv: {n} Zeilen")
```

Docstring des Moduls um die beiden Endpunkte ergänzen; `main()`-Ausgabe um `/werkzeuge/zuordnung.html?tabelle=gruppen` ergänzen.

- [ ] **Step 7: Tests und Handprobe**

Run: `python3 -m pytest tests/test_serve.py -q; node --test werkzeuge/tests/`
Dev-Server neu starten; `http://localhost:8765/werkzeuge/zuordnung.html?tabelle=gewerbe` und `?tabelle=gruppen` öffnen; je eine Zeile prüfen, CSV kontrollieren.

- [ ] **Step 8: Commit**

```bash
git add werkzeuge/js/zuordnung_modell.js werkzeuge/zuordnung.html werkzeuge/serve.py werkzeuge/tests/zuordnung_modell.test.js tests/test_serve.py
git commit -m "feat(werkzeuge/zuordnung): generisches Prüfwerkzeug für Berufsgruppen und Gewerberubriken

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Modul `ebenen.py` — Hexraster, Zählfelder, Aggregation

**Files:**
- Create: `pipeline/lib/ebenen.py`
- Test: `tests/test_ebenen.py`

**Interfaces:**
- Consumes: Adressen-Dict aus `karte_export.gruppiere()` (Felder `id, lat, lon, stadtteil, strasse_heute, hausnr, besitz, eintraege[]`; je Eintrag `teil`, `_beruf` (mit `niveau`, `stellung`, `gruppe`), `_gewerbe` (mit `gruppe`, `art`, `schluessel`), `schl_nr`, `strasse_roh`, `Vorort`) — `_gewerbe` und `gruppe` in `_beruf` liefert Task 9.
- Produces: `HEX_KANTE = 120.0`, `ZENTRUM = (51.45, 7.01)`, `hex_zelle(lat, lon) -> tuple[int, int]`, `hex_polygon(q, r) -> list[list[float]]` (7 Punkte lon/lat, geschlossen), `hex_id(q, r) -> str`, `zaehlfelder(a: dict) -> dict[str, int]` (Zählfelder **einer Adresse**), `strassenschluessel(a) -> tuple[str, str]` (Schlüssel, Name), `aggregiere(adressen, ebene) -> list[dict]` mit `ebene ∈ {"strasse", "stadtteil", "hex"}`.

- [ ] **Step 1: Test**

```python
# tests/test_ebenen.py
import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.ebenen import HEX_KANTE, aggregiere, hex_id, hex_polygon, hex_zelle, strassenschluessel, zaehlfelder


def _im_polygon(lon, lat, poly):
    innen = False
    for i in range(len(poly) - 1):
        (x1, y1), (x2, y2) = poly[i], poly[i + 1]
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            innen = not innen
    return innen


def test_hexzelle_enthaelt_punkt_und_ist_eindeutig():
    punkte = [(51.45, 7.01), (51.4501, 7.0101), (51.50, 6.95), (51.40, 7.10), (51.4512345, 7.0123456)]
    for lat, lon in punkte:
        q, r = hex_zelle(lat, lon)
        assert _im_polygon(lon, lat, hex_polygon(q, r)), (lat, lon, q, r)
    assert hex_zelle(51.45, 7.01) == (0, 0) and hex_id(0, 0) == "0_0" and hex_id(-3, 12) == "-3_12"
    poly = hex_polygon(0, 0)
    assert len(poly) == 7 and poly[0] == poly[-1]
    # Kantenlänge ≈ 120 m: Abstand gegenüberliegender Ecken = 2 · Kante
    (x1, y1), (x2, y2) = poly[0], poly[3]
    dy = (y2 - y1) * 111_320; dx = (x2 - x1) * 111_320 * math.cos(math.radians(51.45))
    assert abs(math.hypot(dx, dy) - 2 * HEX_KANTE) < 1.0


def _adresse(i, lat, lon, strasse="Grenzstraße", schl="00464", stadtteil="Katernberg", besitz="ungeprueft", eintraege=()):
    return dict(id=str(i), lat=lat, lon=lon, stadtteil=stadtteil, strasse_heute=strasse, hausnr="1", besitz=besitz,
                eintraege=[dict(teil=t, schl_nr=schl, strasse_roh="Grenzstr.", Vorort=stadtteil, _beruf=b, _gewerbe=g) for t, b, g in eintraege])


def test_zaehlfelder_und_aggregation():
    b1 = dict(niveau="fachlich", stellung="arbeiter", gruppe="bergbau")
    b2 = dict(niveau="unsicher", stellung="unbestimmt", gruppe="ungeprueft")
    g1 = dict(gruppe="lebensmittel", art="handwerk", schluessel="a|x|1|")
    a1 = _adresse(1, 51.45, 7.01, besitz="privatperson", eintraege=[("I", b1, None), ("I", b1, None), ("I", b2, None), ("II", None, None), ("III", None, g1), ("III", None, g1)])
    a2 = _adresse(2, 51.4501, 7.0101, besitz="bergbau", eintraege=[("I", b1, None), ("I", None, None)])
    a3 = _adresse(3, 51.40, 7.10, strasse="Heckstraße", schl="01226", stadtteil="Werden", eintraege=[("I", b2, None)])
    z = zaehlfelder(a1)
    assert z == {"n_I": 3, "n_II": 1, "n_III": 2, "n_fachlich": 2, "n_unsicher": 1, "n_st_arbeiter": 2, "n_st_unbestimmt": 1,
                 "n_gr_bergbau": 2, "n_gr_ungeprueft": 1, "n_gw_lebensmittel": 1, "n_gwa_handwerk": 1, "n_bs_privatperson": 1}
    assert zaehlfelder(a2)["n_st_unbestimmt"] == 1        # Eintrag ohne geprüften Beruf zählt als unbestimmt
    adressen = {a["id"]: a for a in (a1, a2, a3)}
    st = aggregiere(adressen, "strasse")
    assert [s["id"] for s in st] == ["00464", "01226"]
    assert st[0] == {"id": "00464", "name": "Grenzstraße", "stadtteil": "Katernberg", "adressen": 2, "n_I": 5, "n_II": 1, "n_III": 2,
                     "n_fachlich": 3, "n_unsicher": 1, "n_st_arbeiter": 3, "n_st_unbestimmt": 2, "n_gr_bergbau": 3, "n_gr_ungeprueft": 2,
                     "n_gw_lebensmittel": 1, "n_gwa_handwerk": 1, "n_bs_privatperson": 1, "n_bs_bergbau": 1}
    sd = aggregiere(adressen, "stadtteil")
    assert [s["id"] for s in sd] == ["Katernberg", "Werden"] and sd[0]["lat"] == round((51.45 + 51.4501) / 2, 5) and sd[0]["rang_nord"] == 1 and sd[1]["rang_nord"] == 2
    hx = aggregiere(adressen, "hex")
    assert sum(h["adressen"] for h in hx) == 3 and all(h["id"] == hex_id(*hex_zelle(h["lat"], h["lon"])) for h in hx)
    assert strassenschluessel(_adresse(9, 51.4, 7.0, strasse="", schl="")) == ("1936:Grenzstr.|Katernberg", "Grenzstr. (1936)")
```

- [ ] **Step 2: Test laufen lassen — erwartet ImportError**

- [ ] **Step 3: Modul**

```python
# pipeline/lib/ebenen.py
"""Aggregationsebenen für Perspektiven und Werkstatt (Teilprojekt 5a, Spec §4.1, §5.4): Zählfelder je Adresse,
Summen je Straße, Stadtteil und Hexzelle. Der Browser addiert nur noch Zählfelder — hier wird gezählt.

Hexraster: „pointy-top“, Kantenlänge 120 m, lokale äquirektangulare Projektion um ZENTRUM (Essen); Zellen-ID „q_r“
in Axialkoordinaten. Genau genug für ein Stadtgebiet von ±15 km.
"""
from __future__ import annotations

import math
from collections import defaultdict

HEX_KANTE = 120.0
ZENTRUM = (51.45, 7.01)
_M_JE_GRAD = 111_320.0
_COS = math.cos(math.radians(ZENTRUM[0]))
EBENEN = ("strasse", "stadtteil", "hex")


def _xy(lat: float, lon: float) -> tuple[float, float]:
    return (lon - ZENTRUM[1]) * _M_JE_GRAD * _COS, (lat - ZENTRUM[0]) * _M_JE_GRAD


def _lonlat(x: float, y: float) -> list[float]:
    return [round(x / (_M_JE_GRAD * _COS) + ZENTRUM[1], 6), round(y / _M_JE_GRAD + ZENTRUM[0], 6)]


def hex_zelle(lat: float, lon: float) -> tuple[int, int]:
    """Axialkoordinaten (q, r) der Zelle, die den Punkt enthält (Cube-Rundung)."""
    x, y = _xy(lat, lon)
    qf = (math.sqrt(3) / 3 * x - 1 / 3 * y) / HEX_KANTE
    rf = (2 / 3 * y) / HEX_KANTE
    sf = -qf - rf
    q, r, s = round(qf), round(rf), round(sf)
    dq, dr, ds = abs(q - qf), abs(r - rf), abs(s - sf)
    if dq > dr and dq > ds:
        q = -r - s
    elif dr > ds:
        r = -q - s
    return int(q), int(r)


def hex_mitte(q: int, r: int) -> tuple[float, float]:
    return HEX_KANTE * math.sqrt(3) * (q + r / 2), HEX_KANTE * 1.5 * r


def hex_polygon(q: int, r: int) -> list[list[float]]:
    """Sechs Ecken (lon, lat) plus Schlusspunkt, gegen den Uhrzeigersinn ab der Ecke rechts oben."""
    cx, cy = hex_mitte(q, r)
    ecken = [_lonlat(cx + HEX_KANTE * math.cos(math.radians(60 * i + 30)), cy + HEX_KANTE * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    return ecken + [ecken[0]]


def hex_id(q: int, r: int) -> str:
    return f"{q}_{r}"


def zaehlfelder(a: dict) -> dict[str, int]:
    """Zählfelder einer Adresse: Teile, Niveau (wie bisher), Stellung, Berufsgruppe (Teil I), Gewerbegruppe und -art
    (Teil III, je Betrieb einmal), Besitzklasse (je Adresse). Teil-I-Einträge ohne geprüften Beruf zählen bei Stellung
    und Gruppe als unbestimmt/ungeprüft — der Nenner bleibt sichtbar."""
    n: dict[str, int] = defaultdict(int)
    gesehen: set[tuple[str, str]] = set()   # (Betrieb, Gruppe/Art): derselbe Betrieb zählt je Gruppe nur einmal (Spec §5.3)
    for e in a["eintraege"]:
        n["n_" + e["teil"]] += 1
        if e["teil"] == "I":
            b = e.get("_beruf") or {}
            if b:
                n["n_" + b["niveau"]] += 1
            n["n_st_" + b.get("stellung", "unbestimmt")] += 1
            n["n_gr_" + b.get("gruppe", "ungeprueft")] += 1
        elif e["teil"] == "III" and e.get("_gewerbe"):
            g = e["_gewerbe"]
            if (g["schluessel"], "g:" + g["gruppe"]) not in gesehen:
                gesehen.add((g["schluessel"], "g:" + g["gruppe"]))
                n["n_gw_" + g["gruppe"]] += 1
            if (g["schluessel"], "a:" + g["art"]) not in gesehen:
                gesehen.add((g["schluessel"], "a:" + g["art"]))
                n["n_gwa_" + g["art"]] += 1
    n["n_bs_" + a.get("besitz", "ungeprueft")] += 1
    return {k: v for k, v in n.items() if v}


def strassenschluessel(a: dict) -> tuple[str, str]:
    """Heutige Straße über die fünfstellige schl_nr (Dickhoff); sonst die 1936er Schreibung mit Vorort."""
    e0 = a["eintraege"][0] if a["eintraege"] else {}
    schl = (e0.get("schl_nr") or "").strip()
    if a.get("strasse_heute") and schl:
        return schl, a["strasse_heute"]
    roh, vorort = (e0.get("strasse_roh") or "").strip(), (e0.get("Vorort") or a.get("stadtteil") or "").strip()
    return f"1936:{roh}|{vorort}", f"{roh} (1936)"


def aggregiere(adressen: dict[str, dict], ebene: str) -> list[dict]:
    """Summen der Zählfelder je Einheit; Straße: id = Schlüssel, name, stadtteil (häufigster); Stadtteil: id = Name,
    lat/lon (Mittel), rang_nord (1 = nördlichster); Hex: id, lat/lon der Zellmitte. Sortiert nach id."""
    if ebene not in EBENEN:
        raise ValueError(f"unbekannte Ebene {ebene!r}")
    einheiten: dict[str, dict] = {}
    for a in adressen.values():
        if ebene == "strasse":
            k, name = strassenschluessel(a)
            u = einheiten.setdefault(k, dict(id=k, name=name, _st=defaultdict(int), adressen=0, _lat=0.0, _lon=0.0))
            u["_st"][a.get("stadtteil", "")] += 1
        elif ebene == "stadtteil":
            k = a.get("stadtteil", "")
            if not k:
                continue
            u = einheiten.setdefault(k, dict(id=k, adressen=0, _lat=0.0, _lon=0.0))
        else:
            q, r = hex_zelle(a["lat"], a["lon"])
            k = hex_id(q, r)
            u = einheiten.setdefault(k, dict(id=k, adressen=0, _lat=0.0, _lon=0.0, _qr=(q, r)))
        u["adressen"] += 1
        u["_lat"] += a["lat"]; u["_lon"] += a["lon"]
        for f, v in zaehlfelder(a).items():
            u[f] = u.get(f, 0) + v
    out = []
    for u in einheiten.values():
        n = u["adressen"]
        if ebene == "strasse":
            u["stadtteil"] = max(u.pop("_st").items(), key=lambda x: (x[1], x[0]))[0]
            u.pop("_lat"); u.pop("_lon")
        elif ebene == "stadtteil":
            u["lat"], u["lon"] = round(u.pop("_lat") / n, 5), round(u.pop("_lon") / n, 5)
        else:
            u.pop("_lat"); u.pop("_lon")
            u["lon"], u["lat"] = _lonlat(*hex_mitte(*u.pop("_qr")))
        out.append(u)
    out.sort(key=lambda u: u["id"])
    if ebene == "stadtteil":
        for i, u in enumerate(sorted(out, key=lambda u: -u["lat"]), 1):
            u["rang_nord"] = i
    return out
```

Hinweis: Die Sortierung der Zählfeld-Schlüssel im Test-Vergleich ist unerheblich (dict-Gleichheit). Bei `test_hexzelle…` Toleranz 1 m; falls die Ecke-zu-Ecke-Prüfung wegen Rundung auf 6 Dezimalen knapp scheitert, Toleranz auf 2 m heben, nicht die Geometrie ändern.

- [ ] **Step 4: Test laufen lassen, Commit**

Run: `python3 -m pytest tests/test_ebenen.py -q`

```bash
git add pipeline/lib/ebenen.py tests/test_ebenen.py
git commit -m "feat(ebenen): Hexraster, Zählfelder je Adresse, Aggregation je Straße/Stadtteil/Hex

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Modul `layout.py` — deterministische Kreispackung und Beeswarm

**Files:**
- Create: `pipeline/lib/layout.py`
- Test: `tests/test_layout.py`

**Interfaces:**
- Produces: `radius(wert, max_wert, max_r=60.0) -> float` (Fläche ∝ Wert, min 2), `packe_kreise(kreise: list[dict]) -> list[dict]` (Eingabe `{id, r}`, Ausgabe zusätzlich `x, y`, Reihenfolge der Eingabe bleibt), `packe_gruppen(kreise: list[dict], abstand=12.0) -> tuple[list[dict], list[dict]]` (Eingabe `{id, r, gruppe}`; Ausgabe Kreise mit `x, y` und Gruppenkreise `{gruppe, x, y, r}`), `beeswarm(kreise: list[dict], spalten: list[str], breite=80.0) -> list[dict]` (Eingabe `{id, r, spalte}`; Ausgabe `x, y`; y entlang der Spalte, x = Spaltenindex·Abstand ± Versatz), `ueberlappen(kreise) -> list[tuple[str, str]]`.

- [ ] **Step 1: Test**

```python
# tests/test_layout.py
import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.layout import beeswarm, packe_gruppen, packe_kreise, radius, ueberlappen


def kreise(n, seed_werte=None):
    werte = seed_werte or [((i * 7919) % 97) + 1 for i in range(n)]
    return [dict(id=f"k{i}", r=radius(w, max(werte))) for i, w in enumerate(werte)]


def test_radius_flaeche_proportional():
    assert radius(100, 100) == 60.0 and abs(radius(25, 100) - 30.0) < 1e-9 and radius(0, 100) == 2.0


def test_packung_deterministisch_und_ueberlappungsfrei():
    k = kreise(300)
    a, b = packe_kreise(k), packe_kreise([dict(x) for x in k])
    assert [x["id"] for x in a] == [x["id"] for x in k]
    assert [(x["x"], x["y"]) for x in a] == [(x["x"], x["y"]) for x in b]
    assert ueberlappen(a) == []
    assert all(math.hypot(x["x"], x["y"]) < 1500 for x in a)          # kompakt, nicht in einer Reihe
    assert packe_kreise([]) == []


def test_gruppen_packung():
    k = [dict(x, gruppe=("a", "b", "c")[i % 3]) for i, x in enumerate(kreise(90))]
    kr, gr = packe_gruppen(k)
    assert ueberlappen(kr) == [] and {g["gruppe"] for g in gr} == {"a", "b", "c"}
    for g in gr:                                                       # jeder Kreis liegt in seinem Gruppenkreis
        for x in kr:
            if x["gruppe"] == g["gruppe"]:
                assert math.hypot(x["x"] - g["x"], x["y"] - g["y"]) + x["r"] <= g["r"] + 1e-6
    assert ueberlappen([dict(id=g["gruppe"], r=g["r"], x=g["x"], y=g["y"]) for g in gr]) == []


def test_beeswarm_spalten():
    k = [dict(x, spalte=("helfer", "fachlich", "hochkomplex")[i % 3]) for i, x in enumerate(kreise(120))]
    out = beeswarm(k, ["helfer", "fachlich", "hochkomplex"], breite=80.0)
    assert ueberlappen(out) == []
    for x in out:
        mitte = ["helfer", "fachlich", "hochkomplex"].index(x["spalte"]) * 200.0
        assert abs(x["x"] - mitte) + x["r"] <= 80.0 + 1e-6               # bleibt im Band
    assert out == beeswarm([dict(x) for x in k], ["helfer", "fachlich", "hochkomplex"], breite=80.0)


def test_ueberlappen_findet_paare():
    assert ueberlappen([dict(id="a", r=5, x=0, y=0), dict(id="b", r=5, x=8, y=0), dict(id="c", r=1, x=50, y=0)]) == [("a", "b")]
```

- [ ] **Step 2: Test laufen lassen — erwartet ImportError**

- [ ] **Step 3: Modul**

```python
# pipeline/lib/layout.py
"""Deterministische Bubble-Layouts (Teilprojekt 5a, Spec §5.4): Kreispackung per Spiralsuche, Gruppenpackung,
Beeswarm je Spalte. Keine Zufallszahl, keine Simulation — gleiche Eingabe, gleiche Koordinaten. Einheiten sind
abstrakte Pixel; die Seite skaliert."""
from __future__ import annotations

import math

MIN_R = 2.0


def radius(wert: float, max_wert: float, max_r: float = 60.0) -> float:
    if wert <= 0 or max_wert <= 0:
        return MIN_R
    return max(MIN_R, round(max_r * math.sqrt(wert / max_wert), 3))


def ueberlappen(kreise: list[dict]) -> list[tuple[str, str]]:
    paare = []
    for i, a in enumerate(kreise):
        for b in kreise[i + 1:]:
            if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) < a["r"] + b["r"] - 1e-6:
                paare.append((a["id"], b["id"]))
    return paare


class _Raster:
    """Nachbarschaftsgitter für schnelle Überlappungsprüfung."""

    def __init__(self, zelle: float):
        self.zelle = max(zelle, 1.0)
        self.zellen: dict[tuple[int, int], list[dict]] = {}

    def _k(self, x: float, y: float) -> tuple[int, int]:
        return int(math.floor(x / self.zelle)), int(math.floor(y / self.zelle))

    def frei(self, x: float, y: float, r: float, abstand: float) -> bool:
        kx, ky = self._k(x, y)
        reich = int(math.ceil((r + abstand) / self.zelle)) + 1
        for i in range(kx - reich, kx + reich + 1):
            for j in range(ky - reich, ky + reich + 1):
                for o in self.zellen.get((i, j), ()):
                    if math.hypot(o["x"] - x, o["y"] - y) < o["r"] + r + abstand:
                        return False
        return True

    def lege(self, k: dict) -> None:
        self.zellen.setdefault(self._k(k["x"], k["y"]), []).append(k)


def _spirale(schritt: float):
    """Punkte auf einer archimedischen Spirale ab dem Ursprung, deterministisch."""
    t = 0.0
    yield 0.0, 0.0
    while True:
        t += schritt / max(1.0, 0.5 * t)
        yield 0.5 * t * math.cos(t), 0.5 * t * math.sin(t)


def _packe(kreise: list[dict], abstand: float, cx: float = 0.0, cy: float = 0.0) -> None:
    if not kreise:
        return
    reihenfolge = sorted(kreise, key=lambda k: (-k["r"], str(k["id"])))
    raster = _Raster(2 * max(k["r"] for k in kreise) + abstand)
    for k in reihenfolge:
        for x, y in _spirale(max(k["r"], 1.0)):
            if raster.frei(cx + x, cy + y, k["r"], abstand):
                k["x"], k["y"] = round(cx + x, 2), round(cy + y, 2)
                raster.lege(k)
                break


def packe_kreise(kreise: list[dict], abstand: float = 1.0) -> list[dict]:
    """Kreise {id, r} → mit x, y; größte zuerst um den Ursprung, Reihenfolge der Liste bleibt."""
    out = [dict(k) for k in kreise]
    _packe(out, abstand)
    return out


def packe_gruppen(kreise: list[dict], abstand: float = 12.0) -> tuple[list[dict], list[dict]]:
    """Erst jede Gruppe für sich packen, dann die Gruppenkreise packen und die Mitglieder verschieben."""
    gruppen: dict[str, list[dict]] = {}
    out = [dict(k) for k in kreise]
    for k in out:
        gruppen.setdefault(k["gruppe"], []).append(k)
    huellen = []
    for g, mitglieder in sorted(gruppen.items()):
        _packe(mitglieder, 1.0)
        r = max(math.hypot(k["x"], k["y"]) + k["r"] for k in mitglieder)
        huellen.append(dict(id=g, gruppe=g, r=round(r + abstand / 2, 2)))
    _packe(huellen, abstand)
    for h in huellen:
        for k in gruppen[h["gruppe"]]:
            k["x"], k["y"] = round(k["x"] + h["x"], 2), round(k["y"] + h["y"], 2)
    return out, [dict(gruppe=h["gruppe"], x=h["x"], y=h["y"], r=h["r"]) for h in huellen]


def beeswarm(kreise: list[dict], spalten: list[str], breite: float = 80.0, spaltenabstand: float = 200.0) -> list[dict]:
    """Je Spalte: Kreise nach Größe absteigend, y vom Ursprung nach außen (abwechselnd ±), x innerhalb des Bands
    (Mitte zuerst, dann nach außen), erste freie Stelle gewinnt."""
    out = [dict(k) for k in kreise]
    je_spalte: dict[str, list[dict]] = {}
    for k in out:
        je_spalte.setdefault(k["spalte"], []).append(k)
    for i, s in enumerate(spalten):
        mitte = i * spaltenabstand
        gelegt: list[dict] = []
        for k in sorted(je_spalte.get(s, []), key=lambda k: (-k["r"], str(k["id"]))):
            versaetze = [0.0] + [v * d for v in (0.25, 0.5, 0.75, 1.0) for d in (1, -1)]
            gefunden = False
            y = 0.0
            while not gefunden:
                for vz in (1, -1):
                    for v in versaetze:
                        x = mitte + v * (breite - k["r"])
                        if abs(x - mitte) + k["r"] > breite + 1e-9:
                            continue
                        if all(math.hypot(o["x"] - x, o["y"] - vz * y) >= o["r"] + k["r"] + 1.0 for o in gelegt):
                            k["x"], k["y"] = round(x, 2), round(vz * y, 2)
                            gelegt.append(k); gefunden = True
                            break
                    if gefunden:
                        break
                y += 1.0
    return out
```

- [ ] **Step 4: Test laufen lassen; Laufzeit prüfen**

Run: `python3 -m pytest tests/test_layout.py -q --durations=3`
Expected: PASS; 300 Kreise unter 2 s. Falls `_spirale` zu grob ist (Überlappung), `schritt` verkleinern; falls zu langsam, Rasterzelle anpassen. Für 1.000 Kreise muss die Packung unter 20 s bleiben (einmal mit `kreise(1000)` von Hand messen, nicht als Test).

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/layout.py tests/test_layout.py
git commit -m "feat(layout): deterministische Kreispackung, Gruppenpackung und Beeswarm

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Stufe 06 — Gruppe/Gewerbe an den Einträgen, Zählfelder, `ebenen/`, `layout/`, Kennzahlen

**Files:**
- Modify: `pipeline/lib/karte_export.py` (`gruppiere`, `punkt_feature`, `eintrag_kurz`, `baue_kennzahlen`, `schreibe_paket`), `pipeline/06_karte_export.py`
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Consumes: `lade_gruppen`, `gruppe_export` (Task 4); `lade_gewerbe`, `gewerbe_export`, `rubrik_von`, `betriebsschluessel` (Task 5); `aggregiere`, `zaehlfelder` (Task 7); `radius`, `packe_gruppen`, `beeswarm` (Task 8); `zuordnung()` liefert `stellung`, `gattung_id` (Task 2).
- Produces: `gruppiere(..., gruppen=None, gewerbe=None)`; je Eintrag `_beruf["gruppe"]` und für Teil III `_gewerbe = {rubrik, firma, gruppe, art, schluessel}`; `eintrag_kurz` mit `gattung`, `stellung`, `gruppe`, `rubrik`, `gewerbe_gruppe`, `gewerbe_art`; `punkt_feature` mit allen Zählfeldern aus `zaehlfelder`; `baue_layouts(adressen, gruppen, gewerbe) -> dict[str, dict]`; Dateien `ebenen/strassen.json`, `ebenen/stadtteile.json`, `ebenen/hex.json`, `layout/berufe.json`, `layout/eigentuemer.json`, `layout/gewerbe.json`; Kennzahlen `stellung_geprueft`, `stellung_unbestimmt`, `gruppen_geprueft`, `gewerbe_geprueft` (Prozent).

- [ ] **Step 1: Test** (an `tests/test_karte_export.py` anhängen)

```python
def test_gruppen_gewerbe_zaehlfelder_ebenen_layouts(tmp_path):
    from pipeline.lib.berufe import lade_ohdab, lade_kuratierung as lade_berufe
    from pipeline.lib.gewerbe import lade_gewerbe
    from pipeline.lib.gruppen import lade_gruppen
    from pipeline.lib.karte_export import baue_kennzahlen, baue_layouts, eintrag_kurz, gruppiere, punkt_feature, schreibe_paket
    from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); o = lade_ohdab(p)
    b = lade_berufe([dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja", stellung="arbeiter", stellung_geprueft="ja"),
                     dict(schreibweise="Lehrer", beruf="Lehrer", status="", ohdab_id="B 84124-120", niveau_unsicher="", geprueft="ja", stellung="beamte", stellung_geprueft="")])
    gr = lade_gruppen([dict(ohdab_id="B 21112-100", norm="Bergmann/-frau", nennungen="9", gruppe="bergbau", geprueft="ja"),
                       dict(ohdab_id="B 84124-120", norm="Lehrer/in", nennungen="2", gruppe="bildung_kultur_kirche", geprueft="")])
    gw = lade_gewerbe([dict(rubrik="Bäcker", betriebe="2", gruppe="lebensmittel", art="handwerk", geprueft="ja"),
                       dict(rubrik="Kohlen", betriebe="1", gruppe="handel", art="handel", geprueft="")])
    basis = dict(stufe="haus", lat="51.45", lon="7.01", strasse_norm="x", strasse_roh="X", hausnr="1", Vorort="", stadtteil="Kray", lastname="N", firstname="", page="I-1",
                 strasse_heute="X-Straße", schl_nr="00001")
    def e(i, teil, beruf="", firma="", hausnr="1"):
        return dict(basis, id=str(i), teil=teil, hausnr=hausnr, Firmenname=firma, **{"Beruf o. ä.": beruf})
    eintraege = [e(1, "I", "Bergm."), e(2, "I", "Lehrer"), e(3, "I", "Kfm."), e(4, "II", "Lehrer"),
                 e(5, "III", firma="A. Meier, Bäcker"), e(6, "III", firma="A. Meier, Kohlen"), e(7, "III", firma="B. Kraus, Bäcker"),
                 e(8, "I", "Bergm.", hausnr="2")]
    a = gruppiere(eintraege, [], None, berufe=b, ohdab=o, gruppen=gr, gewerbe=gw)
    haus1 = next(x for x in a.values() if x["hausnr"] == "1")
    k = {x["id"]: eintrag_kurz(x, []) for x in haus1["eintraege"]}
    assert (k["1"]["stellung"], k["1"]["gruppe"], k["1"]["gattung"]) == ("arbeiter", "bergbau", "Berufe im Berg- und Tagebau – fachlich ausgerichtete Tätigkeiten")
    assert (k["2"]["stellung"], k["2"]["gruppe"]) == ("unbestimmt", "ungeprueft")        # Stellung nicht geprüft, Gruppe nicht geprüft
    assert (k["5"]["rubrik"], k["5"]["gewerbe_gruppe"], k["5"]["gewerbe_art"], k["5"]["firma"]) == ("Bäcker", "lebensmittel", "handwerk", "A. Meier, Bäcker")
    assert (k["6"]["gewerbe_gruppe"], k["6"]["gewerbe_art"]) == ("ungeprueft", "ungeprueft")
    assert k["3"]["stellung"] == "" and k["3"]["gruppe"] == ""                          # ohne geprüften Beruf: leer im Eintrag …
    p1 = punkt_feature(haus1)["properties"]
    assert p1["n_st_arbeiter"] == 1 and p1["n_st_unbestimmt"] == 2 and p1["n_gr_bergbau"] == 1 and p1["n_gr_ungeprueft"] == 2   # … aber gezählt als unbestimmt
    assert p1["n_gw_lebensmittel"] == 2 and p1["n_gwa_handwerk"] == 2 and p1["n_gw_ungeprueft"] == 1 and p1["n_bs_ungeprueft"] == 1
    lay = baue_layouts(a, gr, gw)
    assert [x["id"] for x in lay["berufe"]["kreise"]] == ["B 21112-100", "B 84124-120"]
    bm = lay["berufe"]["kreise"][0]
    assert bm["norm"] == "Bergmann" and bm["n"] == 2 and bm["niveau"] == "fachlich" and bm["stellung"] == "arbeiter" and bm["gruppe"] == "bergbau"
    assert {"x", "y", "r"} <= set(bm) and {"x", "y"} <= set(bm["niveau_xy"]) and [g["gruppe"] for g in lay["berufe"]["gruppen"]] == ["bergbau", "ungeprueft"]
    assert lay["gewerbe"]["kreise"][0] == dict(lay["gewerbe"]["kreise"][0], id="Bäcker", n=2, gruppe="lebensmittel", art="handwerk")
    assert lay["eigentuemer"]["kreise"] == []
    kz = baue_kennzahlen(eintraege, a, "2026-09-26")
    assert kz["stellung_geprueft"] == 50.0 and kz["stellung_unbestimmt"] == 50.0 and kz["gruppen_geprueft"] == 50.0 and kz["gewerbe_geprueft"] == 66.7
    aus = tmp_path / "daten"
    schreibe_paket(aus, eintraege, [], [], "2026-09-26", kacheln=False, berufe=list(b.values()), ohdab=o, gruppen=list(gr.values()), gewerbe=list(gw.values()))
    st = json.loads((aus / "ebenen" / "strassen.json").read_text(encoding="utf-8"))
    assert st[0]["id"] == "00001" and st[0]["n_st_arbeiter"] == 2 and st[0]["adressen"] == 2
    assert (aus / "ebenen" / "stadtteile.json").exists() and (aus / "ebenen" / "hex.json").exists()
    assert json.loads((aus / "layout" / "berufe.json").read_text(encoding="utf-8"))["kreise"][0]["id"] == "B 21112-100"
```

`json` oben in der Testdatei importieren, falls noch nicht geschehen.

- [ ] **Step 2: Test laufen lassen — erwartet FAIL** (`gruppiere() got an unexpected keyword argument 'gruppen'`)

- [ ] **Step 3: `karte_export.py` ändern**

Imports ergänzen:

```python
from pipeline.lib.ebenen import EBENEN, aggregiere, hex_polygon, hex_zelle, zaehlfelder
from pipeline.lib.gewerbe import betriebsschluessel, gewerbe_export, lade_gewerbe, rubrik_von
from pipeline.lib.gruppen import gruppe_export, lade_gruppen
from pipeline.lib.layout import beeswarm, packe_gruppen, radius
from pipeline.lib.stellung import STELLUNGEN
```

`gruppiere(...)`: Signatur um `gruppen: dict[str, dict] | None = None, gewerbe: dict[str, dict] | None = None` erweitern. Nach der Berufszuordnung je Eintrag:

```python
        beruf = berufszuordnung(e, berufe, ohdab) if berufe and e.get("teil") in ("I", "II") else None
        if beruf:
            beruf["gruppe"] = gruppe_export((gruppen or {}).get(beruf["ohdab"]))
        gew = None
        if e.get("teil") == "III" and e.get("Firmenname"):
            firma, rubrik = rubrik_von(e["Firmenname"])
            if rubrik:
                g, art = gewerbe_export((gewerbe or {}).get(rubrik))
                gew = dict(rubrik=rubrik, firma=firma, gruppe=g, art=art, schluessel=betriebsschluessel(e))
        e = dict(e, _merkmale=..., _beruf=beruf, _gewerbe=gew)
```

`punkt_feature`: die bisherige Zählung (`n_I/II/III`, `n_<niveau>`) durch `p.update(zaehlfelder(a))` ersetzen; `n_I`, `n_II`, `n_III` mit 0 vorbelegen, damit sie immer vorhanden sind; Merkmale bleiben.

`eintrag_kurz`: ergänzen `gattung=b.get("gattung", "")`, `stellung=b.get("stellung", "")`, `gruppe=b.get("gruppe", "")`, sowie `g = e.get("_gewerbe") or {}` → `rubrik=g.get("rubrik", "")`, `gewerbe_gruppe=g.get("gruppe", "")`, `gewerbe_art=g.get("art", "")`. `firma` bleibt der volle Firmenname (mit Suffix).

Neue Funktion:

```python
def baue_layouts(adressen: dict[str, dict], gruppen: dict[str, dict], gewerbe: dict[str, dict]) -> dict[str, dict]:
    """Vorberechnete Bubble-Layouts (Spec §5.4): Berufsnormen (Gruppenpackung nach Berufsgruppe + Beeswarm nach Niveau),
    identifizierte Eigentümer (Packung nach Klasse), Gewerberubriken (Packung nach Gruppe). Stellung und Gruppe je Norm =
    Mehrheit über die Einträge (Nennungen), damit ein Item nur eine Farbe trägt; „unbestimmt“ zählt mit."""
    normen: dict[str, dict] = {}
    st: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    eig: dict[str, dict] = {}
    rub: dict[str, dict] = {}
    betriebe: set[tuple[str, str]] = set()
    for a in adressen.values():
        for e in a["eintraege"]:
            b = e.get("_beruf")
            if b and e["teil"] == "I":
                n = normen.setdefault(b["ohdab"], dict(id=b["ohdab"], norm=b["norm"], n=0, niveau=b["niveau"], gruppe=b["gruppe"]))
                n["n"] += 1
                st[b["ohdab"]][b["stellung"]] += 1
            if e.get("_eigentuemer") and e.get("_identitaet"):
                x = eig.setdefault(e["_eigentuemer"], dict(id=e["_eigentuemer"], n=0, gruppe=e["_kategorie"], haeuser=set()))
                x["haeuser"].add(a["id"])
            g = e.get("_gewerbe")
            if g and (g["schluessel"], g["rubrik"]) not in betriebe:      # je Rubrik zählt ein Betrieb einmal
                betriebe.add((g["schluessel"], g["rubrik"]))
                r = rub.setdefault(g["rubrik"], dict(id=g["rubrik"], n=0, gruppe=g["gruppe"], art=g["art"]))
                r["n"] += 1
    for x in eig.values():
        x["n"] = len(x.pop("haeuser"))
    for n in normen.values():
        n["stellung"] = max(st[n["id"]].items(), key=lambda kv: (kv[1], kv[0]))[0]

    def layout(kreise: list[dict]) -> dict:
        kreise = sorted(kreise, key=lambda k: (-k["n"], k["id"]))
        mx = max((k["n"] for k in kreise), default=0)
        for k in kreise:
            k["r"] = radius(k["n"], mx)
        gepackt, huellen = packe_gruppen(kreise) if kreise else ([], [])
        return dict(kreise=gepackt, gruppen=huellen)

    berufe = layout(list(normen.values()))
    niveaus = [*NIVEAUS_REIHE, "unsicher"]
    bees = {k["id"]: k for k in beeswarm([dict(id=k["id"], r=k["r"], spalte=k["niveau"]) for k in berufe["kreise"]], niveaus)}
    for k in berufe["kreise"]:
        k["niveau_xy"] = dict(x=bees[k["id"]]["x"], y=bees[k["id"]]["y"])
    berufe["niveaus"] = niveaus
    return dict(berufe=berufe, eigentuemer=layout(list(eig.values())), gewerbe=layout(list(rub.values())))
```

Dazu am Modulanfang `NIVEAUS_REIHE = ["helfer", "fachlich", "spezialist", "hochkomplex", "aufsicht", "fuehrung", "keins"]`.

`baue_kennzahlen`: ergänzen

```python
    teil_iii = [e for a in adressen.values() for e in a["eintraege"] if e["teil"] == "III" and e.get("_gewerbe")]
    mit_beruf = [e for e in teil_i if e.get("_beruf")]
    ...
                stellung_geprueft=_prozent(sum(1 for e in mit_beruf if e["_beruf"]["stellung"] != "unbestimmt"), len(teil_i)),
                stellung_unbestimmt=_prozent(sum(1 for e in teil_i if not e.get("_beruf") or e["_beruf"]["stellung"] == "unbestimmt"), len(teil_i)),
                gruppen_geprueft=_prozent(sum(1 for e in mit_beruf if e["_beruf"]["gruppe"] != "ungeprueft"), len(teil_i)),
                gewerbe_geprueft=_prozent(sum(1 for e in teil_iii if e["_gewerbe"]["gruppe"] != "ungeprueft"), len(teil_iii)),
```

mit `def _prozent(z, n): return round(100 * z / (n or 1), 1)`. Im Test: 4 Teil-I-Einträge, 2 mit geprüfter Stellung → 50,0; unbestimmt (Lehrer + Kfm.) → 50,0; Gruppe geprüft nur Bergmann (2) → 50,0; Gewerbe 2 von 3 → 66,7.

`schreibe_paket`: Parameter `gruppen: list[dict] | None = None, gewerbe: list[dict] | None = None`; `gruppiere(..., gruppen=lade_gruppen(gruppen or []), gewerbe=lade_gewerbe(gewerbe or []))`; nach den Suchindizes:

```python
    for ebene in EBENEN:
        _json(ausgabe / "ebenen" / f"{ {'strasse': 'strassen', 'stadtteil': 'stadtteile', 'hex': 'hex'}[ebene] }.json", aggregiere(adressen, ebene))
    for name, inhalt in baue_layouts(adressen, lade_gruppen(gruppen or []), lade_gewerbe(gewerbe or [])).items():
        _json(ausgabe / "layout" / f"{name}.json", inhalt)
```

`06_karte_export.py`: `gruppen.csv` und `gewerbe.csv` wie `berufe.csv` laden und durchreichen; `("haus", "suche", "adressen", "themen", "ebenen", "layout")` aufräumen.

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: PASS, auch die bestehenden Tests (`punkt_feature` liefert dieselben `n_*`-Felder wie vorher plus die neuen).

- [ ] **Step 5: Echter Export ohne Kacheln, Plausibilität**

Run: `python3 pipeline/06_karte_export.py --ohne-kacheln && python3 -c "import json;d=json.load(open('site/daten/kennzahlen.json'));print({k:d[k] for k in ('stellung_geprueft','stellung_unbestimmt','gruppen_geprueft','gewerbe_geprueft')});l=json.load(open('site/daten/layout/berufe.json'));print(len(l['kreise']), len(l['gruppen']))"`
Expected: Layout mit ≈ 850 Kreisen; Laufzeit der Layouts unter 30 s (sonst Task 8 nachjustieren); `ls -la site/daten/ebenen site/daten/layout` zeigt Dateien im einstelligen MB-Bereich.

- [ ] **Step 6: Commit**

```bash
git add pipeline/lib/karte_export.py pipeline/06_karte_export.py tests/test_karte_export.py
git commit -m "feat(export): Stellung, Gruppen und Gewerbe an Einträgen, Zählfelder je Ebene, Bubble-Layouts, Kennzahlen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: OSM-Straßenlinien und Kachelschichten `strassen` / `hex`

**Files:**
- Create: `werkzeuge/osm_strassen_laden.py`, `docs/osm_strassen.md`
- Modify: `pipeline/lib/karte_export.py` (`tippecanoe_befehl`, `schreibe_paket`), `pipeline/06_karte_export.py`, `.gitignore` (prüfen: `build/` ist bereits ignoriert)
- Test: `tests/test_osm_strassen.py`, `tests/test_karte_export.py`

**Interfaces:**
- Produces: `werkzeuge.osm_strassen_laden.overpass_abfrage() -> str`, `linien_aus(osm_json: dict) -> dict[str, list[list[list[float]]]]` (Straßenname → Liste von Linien (lon/lat)), `main()` schreibt `build/osm_strassen.json` (`{"stand": "<ISO-Datum>", "linien": {...}}`); `karte_export.strassen_features(strassen: list[dict], linien: dict) -> list[dict]` (GeoJSON-Features MultiLineString mit `id` = Straßenschlüssel und `name`; nur Straßen mit heutigem Namen und Linie), `hex_features(hex: list[dict]) -> list[dict]` (Polygone mit `id`); `tippecanoe_befehl(ausgabe: Path, pmtiles: Path) -> list[str]` mit `-L adressen:… -L strassen:… -L hex:…`.

- [ ] **Step 1: Test für den Overpass-Leser**

```python
# tests/test_osm_strassen.py
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from werkzeuge.osm_strassen_laden import linien_aus, overpass_abfrage

OSM = {"elements": [
    {"type": "way", "id": 1, "tags": {"highway": "residential", "name": "Grenzstraße"}, "geometry": [{"lat": 51.49, "lon": 7.06}, {"lat": 51.491, "lon": 7.061}]},
    {"type": "way", "id": 2, "tags": {"highway": "residential", "name": "Grenzstraße"}, "geometry": [{"lat": 51.491, "lon": 7.061}, {"lat": 51.492, "lon": 7.062}]},
    {"type": "way", "id": 3, "tags": {"highway": "footway", "name": "Grenzstraße"}, "geometry": [{"lat": 51.5, "lon": 7.0}, {"lat": 51.5, "lon": 7.001}]},
    {"type": "way", "id": 4, "tags": {"highway": "residential"}, "geometry": [{"lat": 51.5, "lon": 7.0}, {"lat": 51.5, "lon": 7.001}]},
    {"type": "way", "id": 5, "tags": {"highway": "primary", "name": "Altendorfer Straße"}, "geometry": [{"lat": 51.46, "lon": 6.99}]},
]}


def test_linien_je_name_ohne_fusswege_und_namenlose():
    l = linien_aus(OSM)
    assert list(l) == ["Altendorfer Straße", "Grenzstraße"]
    assert l["Grenzstraße"] == [[[7.06, 51.49], [7.061, 51.491]], [[7.061, 51.491], [7.062, 51.492]]]
    assert l["Altendorfer Straße"] == [[[6.99, 51.46]]]


def test_abfrage_nennt_essen_und_highway():
    q = overpass_abfrage()
    assert "62713" in q and "highway" in q and "out geom" in q
```

- [ ] **Step 2: Test laufen lassen — erwartet ImportError**

- [ ] **Step 3: Skript**

```python
# werkzeuge/osm_strassen_laden.py
"""Heutige Straßenlinien Essens aus OpenStreetMap (Overpass) → build/osm_strassen.json (Teilprojekt 5a, Spec §5.4).

Aufruf: python3 werkzeuge/osm_strassen_laden.py [--url https://overpass-api.de/api/interpreter] [--wurzel PFAD]
Nur benannte Fahrstraßen (highway ohne footway/path/steps/cycleway/track/service ohne Namen); je Name alle Segmente.
Die Linien sind die HEUTIGE Führung — die Karte kennzeichnet das (docs/osm_strassen.md). Lizenz: ODbL, © OpenStreetMap-Mitwirkende.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import argparse
import datetime
import json
from collections import defaultdict
from pathlib import Path

import requests

from pipeline.lib.io import projektwurzel

ESSEN_RELATION = 62713          # OSM-Relation der Stadt Essen; Area-ID = 3600000000 + Relation
_AUSSEN = {"footway", "path", "steps", "cycleway", "track", "bridleway", "corridor", "platform", "construction", "proposed"}


def overpass_abfrage() -> str:
    return (f"[out:json][timeout:180];area({3600000000 + ESSEN_RELATION})->.essen;"
            "way[\"highway\"][\"name\"](area.essen);out geom;")


def linien_aus(osm_json: dict) -> dict[str, list[list[list[float]]]]:
    linien: dict[str, list] = defaultdict(list)
    for el in osm_json.get("elements", []):
        if el.get("type") != "way":
            continue
        tags = el.get("tags", {})
        name = (tags.get("name") or "").strip()
        if not name or tags.get("highway") in _AUSSEN:
            continue
        linien[name].append([[p["lon"], p["lat"]] for p in el.get("geometry", [])])
    return dict(sorted(linien.items()))


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="https://overpass-api.de/api/interpreter")
    ap.add_argument("--wurzel", default=None)
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    r = requests.post(a.url, data={"data": overpass_abfrage()}, timeout=300)
    r.raise_for_status()
    linien = linien_aus(r.json())
    ziel = W / "build" / "osm_strassen.json"
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(json.dumps(dict(stand=datetime.date.today().isoformat(), linien=linien), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    k = dict(strassen=len(linien), segmente=sum(len(v) for v in linien.values()))
    print(json.dumps(k)); return k


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Export-Test ergänzen** (`tests/test_karte_export.py`)

```python
def test_strassen_und_hex_features_und_kachelbefehl(tmp_path):
    from pipeline.lib.karte_export import hex_features, strassen_features, tippecanoe_befehl
    strassen = [dict(id="00464", name="Grenzstraße", stadtteil="Katernberg", adressen=2, n_I=5),
                dict(id="1936:Alt|Kray", name="Alt (1936)", stadtteil="Kray", adressen=1, n_I=1),
                dict(id="00001", name="Ohne Linie", stadtteil="Kray", adressen=1, n_I=1)]
    linien = {"Grenzstraße": [[[7.06, 51.49], [7.061, 51.491]]]}
    f = strassen_features(strassen, linien)
    assert len(f) == 1 and f[0]["geometry"] == {"type": "MultiLineString", "coordinates": linien["Grenzstraße"]}
    assert f[0]["properties"] == {"id": "00464", "name": "Grenzstraße", "stadtteil": "Katernberg"} and f[0]["id"] == 464
    h = hex_features([dict(id="0_0", lat=51.45, lon=7.01, adressen=3, n_I=4)])
    assert h[0]["geometry"]["type"] == "Polygon" and len(h[0]["geometry"]["coordinates"][0]) == 7 and h[0]["properties"] == {"id": "0_0"}
    cmd = tippecanoe_befehl(tmp_path, tmp_path / "a.pmtiles")
    assert "-L" in cmd and any(x.startswith("adressen:") for x in cmd) and any(x.startswith("strassen:") for x in cmd) and any(x.startswith("hex:") for x in cmd)
    assert "--layer=adressen" not in cmd
```

Hinweis: Kachel-Features tragen die Zählfelder **nicht** (Farbe kommt per `feature-state` aus `ebenen/*.json`, Spec §5.4); numerische Feature-`id` (int aus `schl_nr`) für Straßen, Hex bekommt `promoteId` über `properties.id` in der Karte (5b/5c).

- [ ] **Step 5: `karte_export.py` ergänzen**

```python
def strassen_features(strassen: list[dict], linien: dict[str, list]) -> list[dict]:
    """Nur heutige Straßen (fünfstellige schl_nr) mit OSM-Linie; Feature-id = int(schl_nr) für feature-state."""
    out = []
    for s in strassen:
        if not s["id"].isdigit() or s["name"] not in linien:
            continue
        out.append({"type": "Feature", "id": int(s["id"]), "geometry": {"type": "MultiLineString", "coordinates": linien[s["name"]]},
                    "properties": {"id": s["id"], "name": s["name"], "stadtteil": s.get("stadtteil", "")}})
    return out


def hex_features(hexe: list[dict]) -> list[dict]:
    out = []
    for h in hexe:
        q, r = (int(x) for x in h["id"].split("_"))
        out.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [hex_polygon(q, r)]}, "properties": {"id": h["id"]}})
    return out


def tippecanoe_befehl(ausgabe: Path, pmtiles: Path) -> list[str]:
    return ["tippecanoe", "-o", str(pmtiles), "--force", "--minimum-zoom=9", "--maximum-zoom=15", "--drop-densest-as-needed",
            "--extend-zooms-if-still-dropping", "--no-feature-limit", "--no-tile-size-limit", "--quiet",
            "-L", f"adressen:{ausgabe / 'adressen.geojson'}", "-L", f"strassen:{ausgabe / 'strassen.geojson'}", "-L", f"hex:{ausgabe / 'hex.geojson'}"]
```

In `schreibe_paket`: Parameter `osm_linien: dict | None = None`; vor dem tippecanoe-Aufruf `strassen.geojson` (aus `aggregiere(adressen, "strasse")` + `osm_linien or {}`) und `hex.geojson` schreiben; `tippecanoe_befehl(ausgabe, ausgabe / "adressen.pmtiles")`. Bestehenden Test `test_schreibe_paket_mit_kacheln` an die neue Signatur anpassen. Kennzahl `strassen_mit_linie` (Anzahl Straßen-Features) in `baue_kennzahlen` ergänzen — dazu die Anzahl als Parameter durchreichen oder in `schreibe_paket` nach `baue_kennzahlen` ins dict setzen (`kennzahlen["strassen_mit_linie"] = len(sf)`).

`06_karte_export.py`: `build/osm_strassen.json` laden, falls vorhanden (`osm_linien = json.load(...)["linien"]`), sonst Warnung auf stderr „build/osm_strassen.json fehlt — Straßenschicht bleibt leer (werkzeuge/osm_strassen_laden.py)“.

- [ ] **Step 6: Doku `docs/osm_strassen.md`**

Kurz: Quelle (Overpass, Relation 62713), Filter, Datum des Abrufs (aus `build/osm_strassen.json`), Lizenz ODbL mit Attributionspflicht (Karte zeigt „© OpenStreetMap-Mitwirkende“ bereits über die Grundkarte; die Legende der Straßenschicht sagt „Straßenlinien: heutige Führung (OSM)“), Grenzen: verschwundene Straßen ohne Linie, Namensgleichheit heutiger Straßen ist in Essen eindeutig (Umbenennungen 1937 nach Eingemeindung), Zahl der Straßen mit/ohne Linie aus `kennzahlen.json`.

- [ ] **Step 7: Abruf, Export mit Kacheln, Tests, Commit**

Run: `python3 werkzeuge/osm_strassen_laden.py && python3 pipeline/06_karte_export.py && python3 -m pytest -q`
Expected: einige tausend Straßen; `kennzahlen.json` `strassen_mit_linie` ≥ 3.500 (von ≈ 4.500 heutigen); PMTiles mit drei Schichten (`tippecanoe` Ausgabe oder `pmtiles show site/daten/adressen.pmtiles`, falls installiert). Karte im Browser prüfen: Punkte unverändert sichtbar.

```bash
git add werkzeuge/osm_strassen_laden.py docs/osm_strassen.md pipeline/lib/karte_export.py pipeline/06_karte_export.py tests/test_osm_strassen.py tests/test_karte_export.py
git commit -m "feat(export): Straßenlinien aus OSM und Hexraster als Kachelschichten

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: Dokumentation — `docs/stellung.md`, README, Journal

**Files:**
- Create: `docs/stellung.md`
- Modify: `README.md` (Abschnitt „Berufe“ ergänzen, neuer Abschnitt „Datenkerne für Perspektiven und Werkstatt (Teilprojekt 5a)“, Tabelle `site/daten/`)

- [ ] **Step 1: `docs/stellung.md`**

Inhalt: Zweck (Stellung im Beruf nach Berufszählung 1933/39 als Vorbild; keine Statusskala, kein Score); die neun Klassen mit Anzeigetext; die Regeln in der Reihenfolge aus `stellung.py` mit je zwei Beispielen (Schreibweise → Klasse, Grund); Grenzfälle (Steiger/Werkmeister = Angestellte, Bäckermeister = Selbständige, Lehrer = Beamte, Ingenieur ohne Titel = Angestellte, Dipl.-Ing. = Akademiker, Gewerbeformen = Selbständige, Kaufleute eigene Klasse); Prüfregel (`stellung_geprueft`); Exportregel; Kennzahlen; Kaufleute-Experiment in der Werkstatt (Spec §4). Zahlen aus dem echten Lauf von Task 2 Schritt 6 eintragen (Verteilung der Vorschläge).

- [ ] **Step 2: README**

- Abschnitt „Berufe“: Spalten `stellung`, `stellung_geprueft`; Werkzeug-Tasten; `werkzeuge/stellung_vorschlag.py`.
- Neuer Abschnitt mit: `kuratierung/gruppen.csv`, `kuratierung/gewerbe.csv` (Spalten, Vokabulare, Werkzeug `zuordnung.html?tabelle=…`), Rubrik-Herkunft (Suffix im Firmenname, 849 Rubriken), Dublettenregel, Zählfeld-Präfixe, Ebenen (`ebenen/strassen.json`, `stadtteile.json`, `hex.json` mit Feldern), Layouts (`layout/*.json`: `kreise[{id, n, r, x, y, …}]`, `gruppen[{gruppe, x, y, r}]`, `niveau_xy`), Kachelschichten `strassen`/`hex` (feature-state, heutige Linien), OSM-Abruf, Kennzahlen.
- Ablauf-Block:

```text
python3 werkzeuge/stellung_vorschlag.py        # Stellung je Schreibweise vorschlagen → berufe.html (Ziffern, T)
python3 werkzeuge/gruppen_vorschlag.py         # Berufsgruppen je Item → zuordnung.html?tabelle=gruppen
python3 werkzeuge/gewerbe_vorschlag.py         # Rubriken Teil III → zuordnung.html?tabelle=gewerbe
python3 werkzeuge/osm_strassen_laden.py        # Straßenlinien (Overpass) → build/osm_strassen.json
python3 pipeline/06_karte_export.py            # Ebenen, Layouts, Schichten, Kennzahlen
```

- [ ] **Step 3: Journal** (Vault `~/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Journal.md`): Eintrag „TP5a Datengrundlage“ mit Kennzahlen des Exports (Stellung/Gruppen/Gewerbe-Abdeckung vor der Handprüfung), Straßen mit Linie, Layout-Größen; Hinweis, dass die Handprüfung (Stellung, Gruppen, Gewerbe) jetzt ansteht.

- [ ] **Step 4: Commit**

```bash
git add docs/stellung.md README.md
git commit -m "docs(tp5a): soziale Stellung, Datenkerne, Ebenen und Layouts dokumentiert

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Reihenfolge und Abhängigkeiten

1 → 2 → 3 (Stellung); 4, 5 unabhängig (nach 1 wegen `falte_form`-Import nur in 5); 6 nach 4+5; 7, 8 unabhängig; 9 nach 2, 4, 5, 7, 8; 10 nach 7, 9; 11 zuletzt. Nach Task 9 kann Christos mit der Handprüfung beginnen (Stellung im Berufe-Werkzeug, Gruppen und Gewerbe im Zuordnungswerkzeug); der Export läuft danach erneut.

## Nicht in diesem Plan

Perspektiven-Seite, Werkstatt, Ansicht-Modell im Browser (`site/js/ansicht.js`), Kartenschichten im Frontend, Themen-Migration — das sind die Pläne 5b und 5c. Die Kachelschichten `strassen`/`hex` werden hier nur erzeugt, noch nicht gezeichnet.
