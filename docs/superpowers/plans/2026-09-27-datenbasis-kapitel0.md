# Schlaglichter Schritt 1: Kapitel 0 „Die Datenbasis“, Trichter-Form, Ausschluss-Benennung, Kapiteltexte — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Schlaglichter-Seite bekommt ein Kapitel 0 mit Trichter-Grafiken zur Datenbasis, jedes Fachkapitel eine Datenbasis-Zeile und einen konkret benannten Ausschluss, und alle vier Kapitel bekommen Textentwürfe zur Handprüfung.

**Architecture:** Der Export (`pipeline/lib/karte_export.py`) liefert zusätzliche absolute Kennzahlen; das Kapitel-Schema (`pipeline/lib/perspektiven.py`) kennt die Ansicht `daten: kennzahlen` + `form: trichter` sowie die Kapitelfelder `datenbasis`, `datenbasis_schritt`, `ausschluss`. Im Browser zeichnet eine neue reine SVG-Form `site/js/formen/trichter.js` aus `kennzahlen.json`; `perspektiven.js` schaltet vor `normalisiere` auf diesen Pfad um. Alle Texte stehen in `kuratierung/perspektiven/*.json`.

**Tech Stack:** Python ≥ 3.12 + pytest (Pipeline), ES-Module + `node --test` (Site, ohne DOM), Scrollama (vorhanden), kein Build-Schritt.

**Spec:** `docs/superpowers/specs/2026-09-27-datenbasis-kapitel0-design.md`

## Global Constraints

- Präzision vor Vollständigkeit: keine Zahl im Text ohne Platzhalter oder Nachrechnung; unbekannte Platzhalter bleiben sichtbar stehen (`fuellePlatzhalter`).
- Alle Formen bleiben reine Zeichenkettenerzeuger (kein DOM), damit `node --test site/tests/` sie prüft.
- Bestehende Schlüssel in `kennzahlen.json` bleiben unverändert (nur Ergänzungen).
- Kapitel bleiben `freigegeben: false`; Freigabe setzt der Projektleiter selbst.
- Codenamen bleiben `perspektiven` (Dateien, Ordner), nach außen heißt die Seite „Schlaglichter“.
- Texte: erzählerisch, 60–100 Wörter je Schritt, Fachbegriffe erklärt; Methode und Belege nur in `grenzen` und Kapitel 0 (Spec §1).
- Kein Seitenbild der Vorlage (Bildrechte offen), nur Link in die DigiBib.
- Tests: `python3 -m pytest -q` (420 grün vor Beginn) und `cd site && node --test tests/` (86 grün vor Beginn) müssen nach jeder Task grün sein.
- Commits mit `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Review Focus

1. **Alter Export im Browser** (kennzahlen.json ohne die neuen Schlüssel): der Trichter darf kein `NaN` zeichnen; fehlende Stufe → Wert „—“, Breite 0. Test in Task 3.
2. **Erste Stufe 0** (leerer Datensatz): keine Division durch null, alle Breiten 0, Prozent „0 %“. Test in Task 3.
3. **Segmentsumme größer als die Stufe** (Kuratierungsfehler): Segmente werden auf die Stufenbreite begrenzt, nichts läuft über den Balken hinaus. Test in Task 3.
4. **Link „Datenbasis ›“, wenn Kapitel 0 nicht sichtbar ist** (freigegebenes Fachkapitel, Kapitel 0 noch nicht freigegeben, ohne `?vorschau=1`): der Link zeigt ins Leere → Link nur rendern, wenn Kapitel 0 im sichtbaren Index steht. Test in Task 4.
5. **Trichter-Ansicht ohne `kennzahlen`-Kopplung** (`daten: kennzahlen` mit `form: balken`): der Export muss abbrechen, nicht still einen leeren Balken schreiben. Test in Task 2.

---

### Task 1: Absolute Kennzahlen im Export

**Files:**
- Modify: `pipeline/lib/karte_export.py:474-505` (`baue_kennzahlen`)
- Test: `tests/test_karte_export.py:172-178` (`test_kennzahlen`) und ein neuer Test

**Interfaces:**
- Produces: `baue_kennzahlen(...)` liefert zusätzlich `eintraege`, `eintraege_I`, `eintraege_II`, `eintraege_III`, `stufe_haus`, `stufe_strasse`, `stufe_stadtplan`, `stufe_offen`, `besitz_hand`, `teil_i_n`, `beruf_geprueft_n`, `stellung_hand_n`, `stellung_vorschlag_n`, `stellung_unbestimmt_n`, `betriebe_n`, `gewerbe_hand_n`, `gewerbe_claude_n`, `gewerbe_regel_n` (alle `int`).

- [ ] **Step 1: Failing test erweitern**

In `tests/test_karte_export.py` den Test `test_kennzahlen` um diese Zeilen ergänzen (nach der letzten `assert`):

```python
    # absolute Zähler für die Trichter der Schlaglichter (Spec 2026-09-27 §3.4)
    assert (k["eintraege"], k["eintraege_I"], k["eintraege_II"], k["eintraege_III"]) == (4, 2, 1, 1)
    assert (k["stufe_haus"], k["stufe_strasse"], k["stufe_stadtplan"], k["stufe_offen"]) == (2, 1, 0, 1)
    assert k["stufe_haus"] + k["stufe_strasse"] + k["stufe_stadtplan"] + k["stufe_offen"] == k["eintraege"]
    assert k["besitz_hand"] == k["besitz_geprueft"] - k["besitz_regel"]
    # ohne _beruf/_gewerbe: alles unbestimmt bzw. keine Betriebe
    assert (k["teil_i_n"], k["beruf_geprueft_n"], k["stellung_hand_n"], k["stellung_vorschlag_n"], k["stellung_unbestimmt_n"]) == (2, 0, 0, 0, 2)
    assert (k["betriebe_n"], k["gewerbe_hand_n"], k["gewerbe_claude_n"], k["gewerbe_regel_n"]) == (0, 0, 0, 0)
```

Und einen neuen Test direkt darunter:

```python
def test_kennzahlen_absolut_stellung_und_gewerbe():
    e = [_v(id="1", teil="I"), _v(id="2", teil="I"), _v(id="3", teil="I"), _v(id="4", teil="III"), _v(id="5", teil="III")]
    a = gruppiere(e, [])
    eintraege = [x for adr in a.values() for x in adr["eintraege"]]
    by = {x["id"]: x for x in eintraege}
    by["1"]["_beruf"] = {"stellung": "arbeiter", "stellung_quelle": "hand"}
    by["2"]["_beruf"] = {"stellung": "angestellte", "stellung_quelle": "vorschlag"}
    by["3"]["_beruf"] = {"stellung": "unbestimmt", "stellung_quelle": "hand"}      # handgeprüft, aber unbestimmt
    by["4"]["_gewerbe"] = {"quelle": "hand"}
    by["5"]["_gewerbe"] = {"quelle": "vorschlag"}
    k = baue_kennzahlen(e, a, "2026-09-27")
    assert (k["teil_i_n"], k["beruf_geprueft_n"]) == (3, 3)
    assert (k["stellung_hand_n"], k["stellung_vorschlag_n"], k["stellung_unbestimmt_n"]) == (1, 1, 1)
    assert (k["betriebe_n"], k["gewerbe_hand_n"], k["gewerbe_claude_n"], k["gewerbe_regel_n"]) == (2, 1, 0, 1)
    # Summen: die drei Stellung-Zähler ergeben alle Teil-I-Einträge, die Gewerbe-Zähler alle Betriebe
    assert k["stellung_hand_n"] + k["stellung_vorschlag_n"] + k["stellung_unbestimmt_n"] == k["teil_i_n"]
    assert k["gewerbe_hand_n"] + k["gewerbe_claude_n"] + k["gewerbe_regel_n"] == k["betriebe_n"]
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag sehen**

Run: `python3 -m pytest tests/test_karte_export.py -q -k kennzahlen`
Expected: FAIL mit `KeyError: 'eintraege'`

- [ ] **Step 3: `baue_kennzahlen` erweitern**

In `pipeline/lib/karte_export.py` in `baue_kennzahlen` vor dem `return dict(` die Zähler berechnen und im `dict(...)` ergänzen. Ersetze den Block ab `mit_beruf = [...]` bis zum Ende der Funktion durch:

```python
    mit_beruf = [e for e in teil_i if e.get("_beruf")]
    st_hand = sum(1 for e in mit_beruf if e["_beruf"].get("stellung_quelle") == "hand" and e["_beruf"]["stellung"] != "unbestimmt")
    st_vorschlag = sum(1 for e in mit_beruf if e["_beruf"].get("stellung_quelle") == "vorschlag" and e["_beruf"]["stellung"] != "unbestimmt")
    st_unbestimmt = sum(1 for e in teil_i if not e.get("_beruf") or e["_beruf"]["stellung"] == "unbestimmt")
    gw_hand = sum(1 for e in teil_iii if e["_gewerbe"].get("quelle") == "hand")
    gw_claude = sum(1 for e in teil_iii if e["_gewerbe"].get("quelle") == "claude")
    gw_regel = sum(1 for e in teil_iii if e["_gewerbe"].get("quelle") == "vorschlag")
    besitz_geprueft = sum(1 for a in adressen.values() if a.get("besitz", "ungeprueft") != "ungeprueft")
    besitz_regel = sum(1 for a in adressen.values() if a.get("besitz_pruefung") == "regel")
    return dict(eintraege_je_teil=dict(sorted(je_teil.items())),
                stufen={s: round(100 * je_stufe[s] / n, 1) for s in STUFEN},
                verortet=sum(je_stufe[s] for s in STUFEN[:3]), offen=je_stufe["offen"],
                adressen=len(adressen), stand=datum,
                # absolute Zähler für die Trichter der Schlaglichter (Kapitel 0): Zeilen je Teil und Stufe
                eintraege=len(eintraege), eintraege_I=je_teil["I"], eintraege_II=je_teil["II"], eintraege_III=je_teil["III"],
                stufe_haus=je_stufe["haus"], stufe_strasse=je_stufe["strasse"], stufe_stadtplan=je_stufe["stadtplan"], stufe_offen=je_stufe["offen"],
                besitz_geprueft=besitz_geprueft,
                besitz_spanne=sum(1 for a in adressen.values() if a.get("besitz_quelle") == "spanne"),
                besitz_nummer=sum(1 for a in adressen.values() if a.get("besitz_quelle") == "nummer"),
                besitz_regel=besitz_regel,
                besitz_hand=besitz_geprueft - besitz_regel,
                eigentuemer_geprueft=len({e["_eigentuemer"] for a in adressen.values() for e in a["eintraege"] if e.get("_eigentuemer")}),
                berufe_geprueft=round(100 * len(mit_beruf) / (len(teil_i) or 1), 1),
                berufe_schreibweisen_geprueft=len({e["Beruf o. ä."] for e in teil_i if e.get("_beruf")}),
                # Drei disjunkte Anteile (Summe 100): von Hand bestimmt, Vorschlag bestimmt, unbestimmt (auch
                # nach Handprüfung) oder ohne geprüften Beruf. Handgeprüft-unbestimmt zählte sonst doppelt.
                stellung_geprueft=_prozent(st_hand, len(teil_i)),
                stellung_vorschlag=_prozent(st_vorschlag, len(teil_i)),
                stellung_unbestimmt=_prozent(st_unbestimmt, len(teil_i)),
                teil_i_n=len(teil_i), beruf_geprueft_n=len(mit_beruf),
                stellung_hand_n=st_hand, stellung_vorschlag_n=st_vorschlag, stellung_unbestimmt_n=st_unbestimmt,
                gewerbe_geprueft=_prozent(gw_hand, len(teil_iii)),
                gewerbe_entschieden=_prozent(gw_claude, len(teil_iii)),
                gewerbe_vorschlag=_prozent(gw_regel, len(teil_iii)),
                betriebe_n=len(teil_iii), gewerbe_hand_n=gw_hand, gewerbe_claude_n=gw_claude, gewerbe_regel_n=gw_regel,
                stadtteil_polygon=_prozent(sum(1 for a in adressen.values() if a.get("stadtteil_quelle") == "polygon"), len(adressen)))
```

Hinweis: `je_stufe` ist ein `defaultdict(int)`, fehlende Stufen liefern 0; `je_teil["I"]` ebenso. `STUFEN` ist `("haus", "strasse", "stadtplan", "offen")` (bereits in der Datei).

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_karte_export.py -q`
Expected: alle PASS (die bestehenden Kennzahl-Asserts mit `besitz_geprueft` usw. bleiben gültig, weil die Formeln unverändert sind).

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/karte_export.py tests/test_karte_export.py
git commit -m "feat(export): absolute Kennzahlen für die Trichter der Schlaglichter (Zeilen je Stufe, Besitz von Hand, Stellung und Gewerbe je Quelle)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Kapitel-Schema — Trichter-Ansicht, `datenbasis`, `ausschluss`, Kennzahlen-Bezug im Export

**Files:**
- Modify: `pipeline/lib/perspektiven.py` (ganze Datei, 66 Zeilen)
- Modify: `pipeline/lib/karte_export.py:717-725` (`schreibe_paket`, Kapitel-Export)
- Test: `tests/test_perspektiven.py`, `tests/test_karte_export.py`

**Interfaces:**
- Produces: `pruefe_ansicht(a, wo)` akzeptiert `{"daten": "kennzahlen", "form": "trichter", "stufen": [...], "erklaerungen": {...}}`; `pruefe_kapitel(k)` verlangt `datenbasis`, `datenbasis_schritt`, `ausschluss` für Kapitel mit mindestens einer Nicht-Trichter-Ansicht; `stufen_schluessel(k) -> list[str]`; `pruefe_kennzahlen_bezug(k, kennzahlen) -> list[str]`.
- Consumes: Kennzahlen-Schlüssel aus Task 1.

- [ ] **Step 1: Failing tests schreiben**

In `tests/test_perspektiven.py` das `GUT`-Kapitel um die drei neuen Felder erweitern (im dict nach `"grenzen": ...`):

```python
       "datenbasis": "{besitz_geprueft} von {adressen} Adressen mit Besitzklasse.", "datenbasis_schritt": "besitz",
       "ausschluss": "ohne Eigentümerangabe oder Eigentümer nicht zugeordnet",
```

Neue Tests am Ende der Datei:

```python
TRICHTER = {"daten": "kennzahlen", "form": "trichter",
            "stufen": [{"name": "Zeilen", "aus": "eintraege", "farbe": "#94a3b8"},
                       {"name": "verortet", "aus": "verortet", "farbe": "#1d4ed8",
                        "segmente": [{"name": "hausgenau", "aus": "stufe_haus", "farbe": "#1d4ed8"},
                                     {"name": "per Regel", "aus": "stufe_strasse", "farbe": "#60a5fa", "muster": "schraffur"}]}],
            "erklaerungen": {"verortet": "Zeilen mit Punkt auf der Karte."}}
KAP0 = {"id": "datenbasis", "reihenfolge": 0, "titel": "Die Datenbasis", "untertitel": "Vom Buch zur Karte", "freigegeben": False,
        "einleitung": "x", "quellen": [], "grenzen": "y", "datenbasis": "", "datenbasis_schritt": "", "ausschluss": "",
        "schritte": [{"id": "weg", "text": "t", "beschreibung": "b", "hervorheben": [], "ansicht": TRICHTER}]}


def test_trichter_ansicht_gueltig():
    from pipeline.lib.perspektiven import pruefe_ansicht
    assert pruefe_ansicht(TRICHTER, "S") == []
    assert pruefe_kapitel(KAP0) == []          # Kapitel 0 braucht keine datenbasis/ausschluss-Texte


def test_trichter_fehler():
    from pipeline.lib.perspektiven import pruefe_ansicht
    assert any("nur mit form trichter" in x for x in pruefe_ansicht(dict(TRICHTER, form="balken"), "S"))
    assert any("nur mit form trichter" in x for x in pruefe_ansicht(dict(GUT["schritte"][0]["ansicht"], form="trichter"), "S"))
    assert any("ohne stufen" in x for x in pruefe_ansicht(dict(TRICHTER, stufen=[]), "S"))
    doppelt = json.loads(json.dumps(TRICHTER)); doppelt["stufen"][1]["segmente"][0]["name"] = "Zeilen"
    assert any("doppelt" in x for x in pruefe_ansicht(doppelt, "S"))
    muster = json.loads(json.dumps(TRICHTER)); muster["stufen"][1]["segmente"][1]["muster"] = "punkte"
    assert any("muster" in x for x in pruefe_ansicht(muster, "S"))
    unvoll = json.loads(json.dumps(TRICHTER)); del unvoll["stufen"][0]["aus"]
    assert any("unvollständig" in x for x in pruefe_ansicht(unvoll, "S"))


def test_fachkapitel_braucht_datenbasis_und_ausschluss():
    k = json.loads(json.dumps(GUT)); del k["datenbasis"]; del k["ausschluss"]; del k["datenbasis_schritt"]
    f = pruefe_kapitel(k)
    assert any("datenbasis" in x for x in f) and any("ausschluss" in x for x in f)
    k = json.loads(json.dumps(GUT)); k["datenbasis"] = ""
    assert any("datenbasis" in x for x in pruefe_kapitel(k))         # leer ist bei Fachkapiteln ein Fehler


def test_kennzahlen_bezug():
    from pipeline.lib.perspektiven import pruefe_kennzahlen_bezug, stufen_schluessel
    assert stufen_schluessel(KAP0) == ["eintraege", "verortet", "stufe_haus", "stufe_strasse"]
    assert pruefe_kennzahlen_bezug(KAP0, {"eintraege": 1, "verortet": 1, "stufe_haus": 1, "stufe_strasse": 1}) == []
    f = pruefe_kennzahlen_bezug(KAP0, {"eintraege": 1})
    assert any("verortet" in x for x in f) and any("stufe_haus" in x for x in f)
    assert pruefe_kennzahlen_bezug(GUT, {}) == []                   # keine Trichter → nichts zu prüfen
```

In `tests/test_karte_export.py` einen Test ergänzen, der den Export-Abbruch prüft (nach `test_kennzahlen_absolut_stellung_und_gewerbe`):

```python
def test_export_bricht_bei_unbekannter_trichter_kennzahl_ab(tmp_path):
    import pytest
    k = {"id": "datenbasis", "reihenfolge": 0, "titel": "D", "untertitel": "u", "freigegeben": False, "einleitung": "x", "quellen": [],
         "grenzen": "y", "datenbasis": "", "datenbasis_schritt": "", "ausschluss": "",
         "schritte": [{"id": "weg", "text": "t", "beschreibung": "b", "hervorheben": [],
                       "ansicht": {"daten": "kennzahlen", "form": "trichter", "stufen": [{"name": "Z", "aus": "gibt_es_nicht", "farbe": "#000"}]}}]}
    ordner = tmp_path / "perspektiven"; ordner.mkdir()
    (ordner / "datenbasis.json").write_text(json.dumps(k), encoding="utf-8")
    e = [_v(id="1", teil="I")]
    with pytest.raises(ValueError, match="gibt_es_nicht"):
        schreibe_paket(tmp_path / "site", e, [], [], "2026-09-27", kacheln=False, perspektiven=ordner)
```

(Signatur wie im bestehenden `test_schreibe_paket`: `schreibe_paket(ausgabe, eintraege, landmarken, zechen, datum, kacheln=..., perspektiven=...)`.)

- [ ] **Step 2: Tests laufen lassen, Fehlschlag sehen**

Run: `python3 -m pytest tests/test_perspektiven.py tests/test_karte_export.py -q`
Expected: FAIL (ImportError `pruefe_kennzahlen_bezug`, Fehlertexte bei `test_trichter_ansicht_gueltig`).

- [ ] **Step 3: Schema implementieren**

`pipeline/lib/perspektiven.py` — Konstanten und `pruefe_ansicht` ersetzen:

```python
DATEN = ("stellung", "gruppe", "niveau", "besitz", "gewerbe")
EBENEN = ("adresse", "strasse", "stadtteil", "hex")
FORMEN = ("karte", "stadtteilkarte", "bubbles", "balken", "multiples", "rangliste")
MASSE = ("anteil", "dominant", "mischung", "dichte")
KAUFLEUTE = ("unbestimmt", "angestellte", "selbstaendige")
MUSTER = ("schraffur",)
PFLICHT = ("id", "reihenfolge", "titel", "untertitel", "freigegeben", "einleitung", "schritte", "grenzen", "quellen",
           "datenbasis", "datenbasis_schritt", "ausschluss")
PFLICHT_SCHRITT = ("id", "text", "ansicht", "hervorheben", "beschreibung")
PFLICHT_ANSICHT = ("daten", "ebene", "form", "gruppen", "kaufleute", "unsicher", "mass", "bezug", "min_n", "filter", "karte")


def ist_trichter(a: dict) -> bool:
    return a.get("daten") == "kennzahlen" or a.get("form") == "trichter"


def pruefe_trichter(a: dict, wo: str) -> list[str]:
    """Trichter (Spec 2026-09-27 §3.1): `daten: kennzahlen` nur mit `form: trichter` und umgekehrt; `stufen` nicht
    leer; jede Stufe und jedes Segment mit name, aus (Kennzahl-Schlüssel), farbe; Namen eindeutig; muster nur schraffur."""
    if a.get("daten") != "kennzahlen" or a.get("form") != "trichter":
        return [f"{wo}: daten kennzahlen nur mit form trichter und umgekehrt"]
    stufen = a.get("stufen")
    if not isinstance(stufen, list) or not stufen:
        return [f"{wo}: trichter ohne stufen"]
    f: list[str] = []
    namen: list = []
    for s in stufen:
        segmente = s.get("segmente", []) if isinstance(s, dict) else []
        if not isinstance(segmente, list):
            f.append(f"{wo}: segmente muss eine Liste sein"); segmente = []
        for x in [s, *segmente]:
            if not isinstance(x, dict) or not x.get("name") or not isinstance(x.get("aus"), str) or not x.get("aus") or not x.get("farbe"):
                f.append(f"{wo}: Stufe unvollständig {x!r}")
                continue
            if x.get("muster") is not None and x["muster"] not in MUSTER: f.append(f"{wo}: muster {x['muster']!r} unbekannt")
            namen.append(x["name"])
    if len(set(namen)) != len(namen): f.append(f"{wo}: Stufenname doppelt")
    if not isinstance(a.get("erklaerungen", {}), dict): f.append(f"{wo}: erklaerungen muss ein Objekt sein")
    return f


def pruefe_ansicht(a: dict, wo: str) -> list[str]:
    if ist_trichter(a):
        return pruefe_trichter(a, wo)
    f = [f"{wo}: Ansicht ohne Feld {p!r}" for p in PFLICHT_ANSICHT if p not in a]
    if f:
        return f
    if a["daten"] not in DATEN: f.append(f"{wo}: daten {a['daten']!r} unbekannt")
    if a["ebene"] not in EBENEN: f.append(f"{wo}: ebene {a['ebene']!r} unbekannt")
    if a["form"] not in FORMEN: f.append(f"{wo}: form {a['form']!r} unbekannt")
    if a["mass"] not in MASSE: f.append(f"{wo}: mass {a['mass']!r} unbekannt")
    if a["kaufleute"] not in KAUFLEUTE: f.append(f"{wo}: kaufleute {a['kaufleute']!r} unbekannt")
    if a["mass"] == "dichte" and a["daten"] != "gewerbe": f.append(f"{wo}: mass dichte nur mit daten gewerbe")
    namen = [g.get("name") for g in a["gruppen"]]
    if len(set(namen)) != len(namen): f.append(f"{wo}: Gruppenname doppelt")
    for g in a["gruppen"]:
        if not g.get("name") or not isinstance(g.get("aus"), list) or not g.get("farbe"): f.append(f"{wo}: Gruppe unvollständig {g!r}")
    if a["mass"] in ("anteil", "dichte") and a["bezug"] not in namen: f.append(f"{wo}: bezug {a['bezug']!r} ist keine Gruppe")
    if not isinstance(a["min_n"], int) or a["min_n"] < 0: f.append(f"{wo}: min_n muss ganze Zahl ≥ 0 sein")
    return f


def pruefe_kapitel(k: dict) -> list[str]:
    f = [f"Kapitel ohne Feld {p!r}" for p in PFLICHT if p not in k]
    if "schritte" not in k:
        return f
    ids = [s.get("id") for s in k["schritte"]]
    if len(set(ids)) != len(ids): f.append("Schritt-id doppelt")
    for s in k["schritte"]:
        wo = f"Schritt {s.get('id')!r}"
        f += [f"{wo}: ohne Feld {p!r}" for p in PFLICHT_SCHRITT if p not in s]
        if "ansicht" in s: f += pruefe_ansicht(s["ansicht"], wo)
    # Fachkapitel (mindestens eine Ansicht auf Ebenen-Daten) müssen Datenbasis und Ausschluss benennen;
    # Kapitel 0 (nur Trichter) darf die Felder leer lassen.
    fach = any("ansicht" in s and not ist_trichter(s["ansicht"]) for s in k["schritte"])
    if fach:
        for p in ("datenbasis", "datenbasis_schritt", "ausschluss"):
            if not k.get(p): f.append(f"Fachkapitel ohne {p}")
    return f


def stufen_schluessel(k: dict) -> list[str]:
    """Alle Kennzahl-Schlüssel (`aus`) der Trichter-Ansichten eines Kapitels, in Reihenfolge, mit Dubletten."""
    out: list[str] = []
    for s in k.get("schritte", []):
        a = s.get("ansicht", {})
        if not ist_trichter(a): continue
        for st in a.get("stufen", []):
            out.append(st.get("aus", ""))
            out += [x.get("aus", "") for x in st.get("segmente", []) or []]
    return out


def pruefe_kennzahlen_bezug(k: dict, kennzahlen: dict) -> list[str]:
    """Jeder `aus`-Schlüssel eines Trichters muss in kennzahlen.json stehen — sonst zeichnete die Seite einen leeren Balken."""
    return [f"Kapitel {k.get('id')!r}: Kennzahl {aus!r} fehlt" for aus in stufen_schluessel(k) if aus not in kennzahlen]
```

`lade_kapitel`, `_loese_gruppen_auf`, `kapitel_index` bleiben unverändert (`_loese_gruppen_auf` ignoriert Trichter, weil `gruppen` dort fehlt — `s.get("ansicht", {}).get("gruppen")` ist `None`).

`pipeline/lib/karte_export.py` — Import ergänzen (Zeile 19):

```python
from pipeline.lib.perspektiven import kapitel_index, lade_kapitel, pruefe_kapitel, pruefe_kennzahlen_bezug
```

und in `schreibe_paket` den Kapitel-Block (ab `if perspektiven is not None:`) so ändern, dass nach `pruefe_kapitel` auch der Kennzahlen-Bezug geprüft wird:

```python
    if perspektiven is not None:
        ks = lade_kapitel(perspektiven)
        for k in ks:
            fehler = pruefe_kapitel(k) + pruefe_kennzahlen_bezug(k, kennzahlen)
            if fehler:
                raise ValueError("kuratierung/perspektiven: " + "; ".join(fehler))
        _json(ausgabe / "perspektiven" / "index.json", kapitel_index(ks))
        for k in ks:
            _json(ausgabe / "perspektiven" / f"{k['id']}.json", k)
```

(Den bestehenden Block vorher lesen — Zeilen 717–725 — und die Schleifenform beibehalten, nur `+ pruefe_kennzahlen_bezug(k, kennzahlen)` ergänzen.)

- [ ] **Step 4: Bestehende Kapitel-JSONs minimal nachziehen**

`test_echte_kapitel_sind_gueltig` schlägt jetzt fehl, weil die drei Fachkapitel `datenbasis`, `datenbasis_schritt`, `ausschluss` nicht haben. In `kuratierung/perspektiven/wohneigentum.json`, `stellung.json`, `gewerbe.json` jeweils nach der Zeile `"freigegeben": false,` einfügen (die endgültigen Texte kommen in Task 6):

wohneigentum.json:
```json
  "datenbasis": "{besitz_geprueft} von {adressen} verorteten Adressen tragen eine Besitzklasse ({besitz_geprueft_prozent} %), {besitz_hand} davon von Hand geprüft, {besitz_regel} nur per Regel.",
  "datenbasis_schritt": "besitz",
  "ausschluss": "ohne Eigentümerangabe oder Eigentümer nicht zugeordnet",
```
stellung.json:
```json
  "datenbasis": "{stellung_hand_n} von {teil_i_n} Einwohnereinträgen mit von Hand bestimmter Stellung ({stellung_geprueft} %), {stellung_vorschlag_n} nach Vorschlag der Automatik ({stellung_vorschlag} %), {stellung_unbestimmt_n} unbestimmt ({stellung_unbestimmt} %).",
  "datenbasis_schritt": "stellung",
  "ausschluss": "Beruf ungeprüft oder Stellung unbestimmt",
```
gewerbe.json:
```json
  "datenbasis": "{betriebe_n} verortete Betriebe aus Teil III; Branche bei {gewerbe_hand_n} von Hand ({gewerbe_geprueft} %), bei {gewerbe_claude_n} nach dokumentierten Prinzipien ({gewerbe_entschieden} %), bei {gewerbe_regel_n} per Wortregel ({gewerbe_vorschlag} %).",
  "datenbasis_schritt": "gewerbe",
  "ausschluss": "Rubrik ohne Branche",
```

- [ ] **Step 5: Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS.

- [ ] **Step 6: Commit**

```bash
git add pipeline/lib/perspektiven.py pipeline/lib/karte_export.py tests/test_perspektiven.py tests/test_karte_export.py kuratierung/perspektiven/
git commit -m "feat(perspektiven): Schema — Trichter-Ansicht (daten kennzahlen), Kapitelfelder datenbasis/ausschluss, Kennzahlen-Bezug im Export geprüft

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Form `trichter.js`

**Files:**
- Create: `site/js/formen/trichter.js`
- Modify: `site/js/formen/skalen.js` (Export `schraffurDefs`, `schraffurId`)
- Test: `site/tests/formen.test.js`

**Interfaces:**
- Produces: `trichter.zeige(ansicht, daten, optionen) → { svg, legende, zahlen, werte }` mit `daten.kennzahlen` als Quelle. `werte` ist die Liste der Einheiten `{ id, name, wert, basis, basisName, anteil, erklaerung, muster }` (Stufen ohne Segmente und alle Segmente), die die Seite für den Detailkasten braucht. `legende`: `[{ name, farbe, text, muster }]`. `zahlen`: `{ N: <erste Stufe>, n_aus: 0, unter_min: 0, einheiten, hinweis: "Stand <stand>" }`.
- `skalen.schraffurId(schluessel) → "schraffur-<schluessel>"`, `skalen.schraffurDefs([{ id, farbe }]) → "<defs>…</defs>"`.

- [ ] **Step 1: Failing test schreiben**

In `site/tests/formen.test.js` Import ergänzen: `import * as trichter from "../js/formen/trichter.js";` und diese Tests anhängen:

```js
const KZ = { eintraege: 1000, verortet: 800, adressen: 300, stufe_haus: 500, stufe_strasse: 300, stand: "2026-09-27" };
const T = { daten: "kennzahlen", form: "trichter",
  stufen: [{ name: "Zeilen", aus: "eintraege", farbe: "#94a3b8" },
           { name: "verortet", aus: "verortet", farbe: "#1d4ed8", segmente: [
             { name: "hausgenau", aus: "stufe_haus", farbe: "#1d4ed8" },
             { name: "straßengenau", aus: "stufe_strasse", farbe: "#60a5fa", muster: "schraffur" }] },
           { name: "Adressen", aus: "adressen", farbe: "#1d4ed8" }],
  erklaerungen: { verortet: "Zeilen mit Punkt auf der Karte." } };

test("trichter: Breiten proportional zur ersten Stufe, Segmente, Schraffur, Einheiten", () => {
  const r = trichter.zeige(T, { kennzahlen: KZ }, { breite: 600, hoehe: 300 });
  assert.match(r.svg, /^<svg/);
  // Stufe ohne Segmente ist selbst die Einheit; Stufe mit Segmenten trägt die Segmente als Einheiten
  assert.match(r.svg, /class="einheit" data-id="eintraege"/);
  assert.match(r.svg, /class="einheit" data-id="stufe_haus"/);
  assert.match(r.svg, /class="einheit" data-id="stufe_strasse"/);
  assert.ok(!/data-id="verortet"/.test(r.svg), "Stufe mit Segmenten ist keine eigene Einheit");
  // Breiten: verortet = 80 % der Zeilen, hausgenau 5/8 davon
  const b = (id) => Number(r.svg.match(new RegExp(`data-id="${id}"[^>]*width="([\\d.]+)"`))[1]);
  assert.ok(Math.abs(b("stufe_haus") / b("eintraege") - 0.5) < 0.01);
  assert.ok(Math.abs(b("stufe_strasse") / b("eintraege") - 0.3) < 0.01);
  assert.match(r.svg, /<pattern id="schraffur-stufe_strasse"/); assert.match(r.svg, /fill="url\(#schraffur-stufe_strasse\)"/);
  assert.match(r.svg, /800 von 1\.000 \(80 %\)/); assert.match(r.svg, /300 von 1\.000 \(30 %\)/);
  assert.deepEqual(r.zahlen, { N: 1000, n_aus: 0, unter_min: 0, einheiten: 4, hinweis: "Stand 2026-09-27" });
  assert.deepEqual(r.legende.map((l) => [l.name, l.muster || ""]), [["hausgenau", ""], ["straßengenau", "schraffur"]]);
  const v = r.werte.find((w) => w.id === "stufe_strasse");
  assert.deepEqual([v.name, v.wert, v.basis, v.basisName, v.muster], ["straßengenau", 300, 1000, "Zeilen", "schraffur"]);
  assert.equal(r.werte.find((w) => w.id === "eintraege").erklaerung, "");
});

test("trichter: fehlende Kennzahl, erste Stufe 0 und übergroße Segmente brechen nichts", () => {
  // Review Focus 1: alter Export ohne Schlüssel → „—“, Breite 0, kein NaN
  const alt = trichter.zeige(T, { kennzahlen: { eintraege: 1000 } }, { breite: 600, hoehe: 300 });
  assert.ok(!/NaN/.test(alt.svg)); assert.match(alt.svg, /—/);
  assert.equal(alt.werte.find((w) => w.id === "adressen").wert, null);
  // Review Focus 2: erste Stufe 0
  const leer = trichter.zeige(T, { kennzahlen: { eintraege: 0, verortet: 0, adressen: 0, stufe_haus: 0, stufe_strasse: 0 } }, { breite: 600, hoehe: 300 });
  assert.ok(!/NaN/.test(leer.svg)); assert.match(leer.svg, /0 von 0 \(0 %\)/);
  // Review Focus 3: Segmente größer als die Stufe → auf die Stufenbreite begrenzt
  const gross = trichter.zeige(T, { kennzahlen: { ...KZ, stufe_haus: 900, stufe_strasse: 900 } }, { breite: 600, hoehe: 300 });
  const b = (svg, id) => Number(svg.match(new RegExp(`data-id="${id}"[^>]*width="([\\d.]+)"`))[1]);
  assert.ok(b(gross.svg, "stufe_haus") + b(gross.svg, "stufe_strasse") <= b(gross.svg, "eintraege") * 0.8 + 0.01);
});
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag sehen**

Run: `cd site && node --test tests/formen.test.js`
Expected: FAIL (Modul `../js/formen/trichter.js` nicht gefunden).

- [ ] **Step 3: Schraffur-Helfer in `skalen.js`**

Am Ende von `site/js/formen/skalen.js` anhängen:

```js
// Schraffur für Anteile, die nicht von Hand geprüft sind (Regel, Vorschlag): ein diagonales Muster in
// der Farbe des Segments. Die id enthält den Kennzahl-Schlüssel, damit mehrere Bühnen auf einer Seite
// (ein Kapitel je Bühne) sich nicht die Muster überschreiben.
export const schraffurId = (schluessel) => `schraffur-${String(schluessel).replace(/[^\w-]/g, "_")}`;
export function schraffurDefs(muster) {
  if (!muster.length) return "";
  return "<defs>" + muster.map(({ id, farbe }) =>
    `<pattern id="${esc(id)}" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">`
    + `<rect width="6" height="6" fill="#fff"/><rect width="3" height="6" fill="${esc(farbe)}"/></pattern>`).join("") + "</defs>";
}
```

- [ ] **Step 4: `trichter.js` schreiben**

`site/js/formen/trichter.js`:

```js
// site/js/formen/trichter.js — Trichter aus Kennzahlen (Kapitel 0 „Die Datenbasis“, Spec 2026-09-27 §3):
// Stufen als Balken untereinander, Breite proportional zur ersten Stufe; eine Stufe darf Segmente tragen
// (Hand / Regel / Vorschlag), schraffiert, wo nichts von Hand geprüft ist. Rein, ohne DOM.
import { esc, formatProzent, formatZahl, r2, schraffurDefs, schraffurId, svgKopf } from "./skalen.js";

const RAND = 8;
const BESCHRIFTUNG = 0.32;      // Anteil der Breite für den Stufennamen
const WERTSPALTE = 150;         // Platz für „x von y (z %)“
const ZEILE_MAX = 56;

// Wert einer Kennzahl oder null, wenn sie fehlt (alter Export) — null wird nie gerechnet, nur angezeigt.
const wertVon = (kz, aus) => (typeof kz[aus] === "number" && Number.isFinite(kz[aus]) ? kz[aus] : null);
const anteil = (wert, basis) => (wert === null || !basis ? 0 : wert / basis);
const wertText = (wert, basis, erste) => wert === null ? "—" : erste ? formatZahl(wert) : `${formatZahl(wert)} von ${formatZahl(basis)} (${formatProzent(anteil(wert, basis))})`;

export function zeige(ansicht, daten, optionen = {}) {
  const breite = optionen.breite || 600;
  const hoehe = optionen.hoehe || 300;
  const kz = (daten && daten.kennzahlen) || {};
  const stufen = Array.isArray(ansicht.stufen) ? ansicht.stufen : [];
  const erklaerungen = ansicht.erklaerungen || {};
  const basis = stufen.length ? wertVon(kz, stufen[0].aus) : null;
  const basisName = stufen.length ? stufen[0].name : "";
  const oben = optionen.titel ? 30 : RAND;
  const zeile = Math.min(ZEILE_MAX, Math.max(18, (hoehe - oben - RAND) / Math.max(1, stufen.length)));
  const beschriftung = Math.min(200, breite * BESCHRIFTUNG);
  const maxBreite = Math.max(10, breite - beschriftung - WERTSPALTE - RAND);
  const werte = [];
  const legende = [];
  const muster = [];
  const teile = [];
  if (optionen.titel) teile.push(`<text x="${RAND}" y="18" class="titel">${esc(optionen.titel)}</text>`);

  stufen.forEach((s, i) => {
    const wert = wertVon(kz, s.aus);
    const y = oben + i * zeile;
    const h = Math.max(6, zeile - 8);
    const b = basis ? Math.min(maxBreite, maxBreite * anteil(wert, basis)) : 0;
    const segmente = Array.isArray(s.segmente) ? s.segmente : [];
    teile.push(`<text x="${RAND}" y="${r2(y + h / 2 + 4)}" class="name">${esc(s.name)}</text>`);
    teile.push(`<text x="${r2(beschriftung + b + 6)}" y="${r2(y + h / 2 + 4)}" class="wert">${esc(wertText(wert, basis, i === 0))}</text>`);
    if (!segmente.length) {
      werte.push({ id: s.aus, name: s.name, wert, basis, basisName, anteil: anteil(wert, basis), erklaerung: erklaerungen[s.aus] || "", muster: s.muster || "" });
      teile.push(`<rect class="einheit" data-id="${esc(s.aus)}" x="${r2(beschriftung)}" y="${r2(y)}" width="${r2(b)}" height="${r2(h)}" fill="${esc(s.farbe)}"><title>${esc(`${s.name}: ${wertText(wert, basis, i === 0)}`)}</title></rect>`);
      return;
    }
    // Stufe mit Segmenten: ein blasser Grund in Stufenbreite, darauf die Segmente als Einheiten. Die
    // Segmentbreiten sind auf die Stufenbreite begrenzt — ein Kuratierungsfehler darf nicht überlaufen.
    teile.push(`<rect class="grund" x="${r2(beschriftung)}" y="${r2(y)}" width="${r2(b)}" height="${r2(h)}" fill="${esc(s.farbe)}" opacity=".25"></rect>`);
    let x = beschriftung;
    for (const seg of segmente) {
      const sw = wertVon(kz, seg.aus);
      const sb = Math.max(0, Math.min(beschriftung + b - x, maxBreite * anteil(sw, basis)));
      let fill = seg.farbe;
      if (seg.muster === "schraffur") { const id = schraffurId(seg.aus); muster.push({ id, farbe: seg.farbe }); fill = `url(#${id})`; }
      werte.push({ id: seg.aus, name: seg.name, wert: sw, basis, basisName, anteil: anteil(sw, basis), erklaerung: erklaerungen[seg.aus] || "", muster: seg.muster || "" });
      legende.push({ name: seg.name, farbe: seg.farbe, text: seg.muster === "schraffur" ? "nicht von Hand geprüft" : seg.name, muster: seg.muster || "" });
      teile.push(`<rect class="einheit" data-id="${esc(seg.aus)}" x="${r2(x)}" y="${r2(y)}" width="${r2(sb)}" height="${r2(h)}" fill="${esc(fill)}"><title>${esc(`${seg.name}: ${wertText(sw, basis, false)}`)}</title></rect>`);
      x += sb;
    }
  });
  const svg = svgKopf(breite, hoehe) + schraffurDefs(muster) + teile.join("") + "</svg>";
  const zahlen = { N: basis || 0, n_aus: 0, unter_min: 0, einheiten: werte.length, hinweis: `Stand ${kz.stand || "unbekannt"}` };
  return { svg, legende, zahlen, werte };
}
```

`esc` in `skalen.js` ersetzt `(` nicht — `url(#…)` bleibt deshalb als Attributwert intakt (die id enthält nach `schraffurId` nur `\w` und `-`).

- [ ] **Step 5: Tests laufen lassen**

Run: `cd site && node --test tests/`
Expected: alle PASS. Falls die Breitenprüfung an der Rundung von `r2` scheitert: Toleranz 0.01 ist großzügig genug für zweistellige Rundung bei Breiten > 100 px; sonst `maxBreite` prüfen.

- [ ] **Step 6: Commit**

```bash
git add site/js/formen/trichter.js site/js/formen/skalen.js site/tests/formen.test.js
git commit -m "feat(schlaglichter): Form trichter — Stufen aus Kennzahlen, Segmente, Schraffur für nicht handgeprüfte Anteile

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Modell — `formFuer`, Detailkasten für Stufen, Ausschluss-Text, Datenbasis-Link, `besitz_hand_prozent`

**Files:**
- Modify: `site/js/perspektiven_modell.js` (`PROZENT_BASIS`, `formFuer`, `detailTextGruppe`, neu `detailTextStufe`, `datenbasisLink`)
- Modify: `site/js/formen/balken.js` (`ausschlussText` in Legende und Segment-Titel)
- Test: `site/tests/perspektiven.test.js`, `site/tests/formen.test.js`

**Interfaces:**
- Produces: `formFuer({form:"trichter"}) → "trichter"`; `detailTextStufe(w) → { titel, zeilen }`; `detailTextGruppe(name, werte, ansicht, ausschlussText = "")`; `datenbasisLink(kapitel, index) → string | null` (Anker `#s-datenbasis-<schritt>` oder null, wenn Kapitel `datenbasis` nicht im Index); `balken.zeige(..., { ausschlussText })`.
- Consumes: `werte`-Objekte aus Task 3.

- [ ] **Step 1: Failing tests schreiben**

In `site/tests/perspektiven.test.js` den Import um `datenbasisLink, detailTextStufe` erweitern und anhängen:

```js
test("formFuer trichter, besitz_hand_prozent, Detail zu einer Trichter-Stufe", () => {
  assert.equal(formFuer({ daten: "kennzahlen", form: "trichter" }), "trichter");
  const kz = { adressen: 70316, besitz_hand: 31914 };
  assert.equal(fuellePlatzhalter("{besitz_hand_prozent} %", kz), "45,4 %");
  const d = detailTextStufe({ id: "stufe_strasse", name: "straßengenau", wert: 300, basis: 1000, basisName: "Zeilen", anteil: 0.3, erklaerung: "Straße bekannt, Nummer nicht.", muster: "schraffur" });
  assert.equal(d.titel, "straßengenau");
  assert.deepEqual(d.zeilen, ["300 von 1.000 Zeilen (30 %)", "Straße bekannt, Nummer nicht.", "nicht von Hand geprüft (schraffiert)"]);
  const fehlt = detailTextStufe({ id: "x", name: "Adressen", wert: null, basis: 1000, basisName: "Zeilen", anteil: 0, erklaerung: "", muster: "" });
  assert.deepEqual(fehlt.zeilen, ["Kennzahl im Export nicht vorhanden"]);
});

test("detailTextGruppe nennt den Ausschluss des Kapitels", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", form: "balken", gruppen: [{ name: "Privat", aus: ["privatperson"], farbe: "#000" }], bezug: "Privat" });
  const werte = [{ id: "K", N: 90, n_aus: 10, zaehler: { Privat: 90 } }];
  assert.equal(detailTextGruppe("ausgeschlossen", werte, a).zeilen[0], "10 Nennungen ausgeschlossen (unbestimmt, ungeprüft), 90 einbezogen");
  assert.equal(detailTextGruppe("ausgeschlossen", werte, a, "ohne Eigentümerangabe").zeilen[0], "10 Nennungen ausgeschlossen (ohne Eigentümerangabe), 90 einbezogen");
});

test("datenbasisLink nur, wenn Kapitel 0 sichtbar ist", () => {
  const k = { id: "wohneigentum", datenbasis: "x", datenbasis_schritt: "besitz" };
  assert.equal(datenbasisLink(k, [{ id: "datenbasis" }, { id: "wohneigentum" }]), "#s-datenbasis-besitz");
  assert.equal(datenbasisLink(k, [{ id: "wohneigentum" }]), null);          // Review Focus 4
  assert.equal(datenbasisLink({ id: "x", datenbasis: "", datenbasis_schritt: "" }, [{ id: "datenbasis" }]), null);
});
```

In `site/tests/formen.test.js` nach dem Test „balken: Gesamtbalken …“ anhängen:

```js
test("balken: ausschlussText ersetzt „unbestimmt/ungeprüft“ in Legende und Segmenttitel", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "balken", gruppen: G, bezug: "Arbeiter", min_n: 0 });
  const r = balken.zeige(a, daten, { breite: 600, hoehe: 200, ausschlussText: "Beruf ungeprüft oder Stellung unbestimmt" });
  assert.equal(r.legende[2].text, "Beruf ungeprüft oder Stellung unbestimmt");
  assert.match(r.svg, /<title>Beruf ungeprüft oder Stellung unbestimmt: 55<\/title>/);
  const ohne = balken.zeige(a, daten, { breite: 600, hoehe: 200 });
  assert.equal(ohne.legende[2].text, "unbestimmt/ungeprüft");
});
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag sehen**

Run: `cd site && node --test tests/`
Expected: FAIL (`detailTextStufe`/`datenbasisLink` nicht exportiert, Legendentext unverändert).

- [ ] **Step 3: Modell erweitern**

`site/js/perspektiven_modell.js`:

`PROZENT_BASIS` ändern:
```js
export const PROZENT_BASIS = ["besitz_geprueft", "besitz_hand"];
```

`formFuer` — erste Zeile nach `const form = ansicht && ansicht.form;` ergänzen:
```js
  if (form === "trichter") return "trichter";
```

`detailTextGruppe` — Signatur und Ausschluss-Zeile ändern:
```js
export function detailTextGruppe(name, werte, ansicht, ausschlussText = "") {
  const g = (ansicht?.gruppen || []).find((x) => x.name === name);
  if (!g && name !== "ausgeschlossen") return null;
  const N = werte.reduce((s, w) => s + (w.N || 0), 0);
  const n_aus = werte.reduce((s, w) => s + (w.n_aus || 0), 0);
  if (!g) return { titel: "ausgeschlossen", zeilen: [`${formatZahl(n_aus)} Nennungen ausgeschlossen (${ausschlussText || "unbestimmt, ungeprüft"}), ${formatZahl(N)} einbezogen`] };
```
(Rest der Funktion unverändert.)

Neue Funktionen nach `detailTextGruppe`:
```js
// Detailkasten zu einer Trichter-Stufe (Kapitel 0): Wert und Anteil an der ersten Stufe, Erklärtext,
// Hinweis bei Schraffur. Fehlt die Kennzahl im Export, steht das da — keine erfundene Null.
export function detailTextStufe(w) {
  const e = w || {};
  if (e.wert === null || e.wert === undefined) return { titel: String(e.name || e.id || ""), zeilen: ["Kennzahl im Export nicht vorhanden"] };
  const zeilen = [`${formatZahl(e.wert)} von ${formatZahl(e.basis)} ${e.basisName || ""} (${formatProzent(e.anteil || 0)})`.replace("  ", " ")];
  if (e.erklaerung) zeilen.push(e.erklaerung);
  if (e.muster === "schraffur") zeilen.push("nicht von Hand geprüft (schraffiert)");
  return { titel: String(e.name || e.id || ""), zeilen };
}

// Anker der Datenbasis-Zeile eines Fachkapitels auf den passenden Schritt in Kapitel 0 — nur, wenn
// Kapitel 0 überhaupt sichtbar ist (sonst zeigte der Link ins Leere).
export function datenbasisLink(kapitel, index) {
  const k = kapitel || {};
  if (!k.datenbasis || !k.datenbasis_schritt) return null;
  if (!(index || []).some((e) => e.id === "datenbasis")) return null;
  return `#s-datenbasis-${k.datenbasis_schritt}`;
}
```

`site/js/formen/balken.js`:

`segmente(...)` und `balkenZeile(...)` bekommen den Ausschluss-Namen für den Segment-Titel: In `balkenZeile` die Zeile `const titel = ...` ersetzen durch
```js
    const titel = `${seg.id === "ausgeschlossen" && seg.text ? seg.text : seg.id}: ${formatZahl(seg.wert)}${seg.regel > 0 ? `, ${regelText(seg.regel)}` : ""}`;
```
In `segmente(ansicht, zaehler, n_aus, regel = 0, ausschlussText = "")` das graue Segment so anlegen:
```js
  s.push({ id: "ausgeschlossen", wert: n_aus || 0, farbe: GRAU, regel: 0, text: ausschlussText });
```
In `zeige`: `const ausschluss = optionen.ausschlussText || "";` nach `hervor`, die Legende mit
```js
    { name: "ausgeschlossen", farbe: GRAU, text: ausschluss || "unbestimmt/ungeprüft" }];
```
und alle drei `segmente(...)`-Aufrufe um das letzte Argument `ausschluss` ergänzen (je-Einheit-Zweig: `segmente(ansicht, w.zaehler, w.n_aus, w.regel, ausschluss)`; Gesamtbalken: `segmente(ansicht, zaehler, zahlen.n_aus, regel, ausschluss)`; die Prozent-Schleife: `segmente(ansicht, zaehler, zahlen.n_aus, 0, ausschluss)`).

- [ ] **Step 4: Tests laufen lassen**

Run: `cd site && node --test tests/`
Expected: alle PASS.

- [ ] **Step 5: Commit**

```bash
git add site/js/perspektiven_modell.js site/js/formen/balken.js site/tests/perspektiven.test.js site/tests/formen.test.js
git commit -m "feat(schlaglichter): Modell — Trichter-Detail, Ausschluss-Text je Kapitel, Datenbasis-Link, besitz_hand_prozent

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Seite — Trichter zeichnen, Datenbasis-Zeile, Ausschluss durchreichen, CSS

**Files:**
- Modify: `site/js/perspektiven.js`
- Modify: `site/css/perspektiven.css`

Keine Node-Tests (Browsercode); Sichtprüfung im Browser ist Teil dieser Task.

- [ ] **Step 1: Trichter-Import und Formentabelle**

In `site/js/perspektiven.js`:
```js
import * as trichter from "./formen/trichter.js";
import { datenbasisLink, detailLage, detailText, detailTextGruppe, detailTextStufe, detailZustand, DETAIL_ZU, formFuer, fuellePlatzhalter, linkKarte, linkWerkstatt, sichtbareKapitel, zeichenflaeche } from "./perspektiven_modell.js";

const FORMEN = { balken, rangliste, stadtteilkarte, bubbles, trichter };
const istTrichter = (a) => !!a && (a.form === "trichter" || a.daten === "kennzahlen");
```

- [ ] **Step 2: Index für den Datenbasis-Link merken**

In `seiteAufbauen` nach `const index = sichtbareKapitel(...)` die Variable auf Modulebene verfügbar machen: oben `let sichtbar = [];` deklarieren und nach der Zeile `sichtbar = index;` setzen. In der Schleife `bindeKapitel(sec, k)` bleibt.

- [ ] **Step 3: `kapitelHtml` — Trichter-Schritte ohne Links, Schritt-ids, Datenbasis-Zeile**

`kapitelHtml(k)` ersetzen:
```js
function kapitelHtml(k) {
  const schritte = (Array.isArray(k.schritte) ? k.schritte : []).map((s) => {
    const kopf = `<article class="schritt" id="s-${esc(k.id)}-${esc(s.id)}" data-schritt="${esc(s.id)}" tabindex="0"><p>${esc(s.text)}</p><p class="sr-only">${esc(s.beschreibung || "")}</p>`;
    // Trichter zeigen Kennzahlen, keine Einheiten der Karte — Karten- und Werkstattlink ergäben nichts.
    if (istTrichter(s.ansicht)) return `${kopf}</article>`;
    const a = normalisiere(s.ansicht);
    return `${kopf}<p class="links"><a href="${esc(linkKarte(a))}">Auf der Karte öffnen</a> · <a href="${esc(linkWerkstatt(a))}">In der Werkstatt öffnen</a></p></article>`;
  }).join("");
  const quellen = (Array.isArray(k.quellen) ? k.quellen : []).map((q) => esc(q)).join(" · ");
  const link = datenbasisLink(k, sichtbar);
  const datenbasis = k.datenbasis
    ? `<p class="datenbasis">${esc(fuellePlatzhalter(k.datenbasis, daten.kennzahlen))}${link ? ` <a href="${esc(link)}">Datenbasis ›</a>` : ""}</p>` : "";
  return `<header><h2>${esc(k.titel)}</h2><p class="untertitel">${esc(k.untertitel || "")}</p>${datenbasis}<p>${esc(k.einleitung || "")}</p></header>`
    + `<div class="scrolly">`
    + `<div class="grafik"><div class="buehne"><div class="titel" aria-hidden="true"></div><div class="svg" aria-hidden="true"></div><div class="legende" aria-hidden="true"></div><div class="zahlen"></div></div></div>`
    + `<div class="schritte">${schritte}</div>`
    + `</div>`
    + `<section class="grenzen"><h3>Was die Zahlen zeigen – und was nicht</h3>`
    + `<p>${esc(fuellePlatzhalter(k.grenzen || "", daten.kennzahlen))}</p>`
    + (quellen ? `<p class="quellen">Quellen: ${quellen}</p>` : "")
    + `</section>`;
}
```

- [ ] **Step 4: `zeichne` — Trichterpfad, Ausschluss-Option, Zahlenzeile**

In `zeichne(sec, schritt)` (das Kapitel `k` wird gebraucht: Signatur auf `zeichne(sec, schritt, k)` erweitern und in `bindeKapitel` den Aufruf `zeichne(sec, schritte[el.dataset.schritt], k)` anpassen):

```js
function zeichne(sec, schritt, k) {
  if (!schritt) return;
  melde("schrittwechsel");
  const trichterSchritt = istTrichter(schritt.ansicht);
  const ansicht = trichterSchritt ? schritt.ansicht : normalisiere(schritt.ansicht);
  if (!trichterSchritt && schritt.ansicht && schritt.ansicht.form === "multiples") ansicht.filter = { ...ansicht.filter, je_einheit: true };
  const form = FORMEN[formFuer(ansicht)];
  const buehne = sec.querySelector(".buehne");
  const svg = buehne.querySelector(".svg");
  const legende = buehne.querySelector(".legende");
  const zahlen = buehne.querySelector(".zahlen");
  const optionen = { hervorheben: schritt.hervorheben || [], ausschlussText: (k && k.ausschluss) || "" };
  buehne.querySelector(".titel").textContent = schritt.beschreibung || "";
  const vorab = form.zeige(ansicht, daten, { ...zeichenflaeche(svg.clientWidth, svg.clientHeight), ...optionen });
  legende.innerHTML = legendeHtml(vorab.legende);
  zahlen.textContent = trichterSchritt ? vorab.zahlen.hinweis : zahlenText(vorab, ansicht);
  const r = form.zeige(ansicht, daten, { ...zeichenflaeche(svg.clientWidth, svg.clientHeight), ...optionen });
  svg.innerHTML = r.svg;
  if (!reduziert) {
    svg.classList.add("blass");
    requestAnimationFrame(() => requestAnimationFrame(() => svg.classList.remove("blass")));
  }
  svg.setAttribute("aria-label", schritt.beschreibung || "");
  gezeigt = { werte: trichterSchritt ? r.werte : werteJeEinheit(ansicht, daten), ansicht, svg, trichter: trichterSchritt, ausschluss: optionen.ausschlussText };
  svg.querySelectorAll(".einheit").forEach((el) => {
    const zeile = el.dataset.zeile || "";
    el.addEventListener("click", () => melde("klick", el.dataset.id, zeile, el.getBoundingClientRect()));
    if (!schweben) return;
    el.addEventListener("mouseenter", () => melde("schweben", el.dataset.id, zeile, el.getBoundingClientRect()));
    el.addEventListener("mouseleave", () => melde("verlassen", el.dataset.id, zeile));
  });
}
```
Die Modulvariable `gezeigt` initial auf `{ werte: [], ansicht: null, svg: null, trichter: false, ausschluss: "" }` setzen.

`legendeHtml` — Schraffur in der Legende:
```js
function legendeHtml(legende) {
  return legende.map((l) => {
    const stil = l.muster === "schraffur" ? `background: repeating-linear-gradient(45deg, ${esc(l.farbe)} 0 3px, #fff 3px 6px)` : `background:${esc(l.farbe)}`;
    return `<span><i style="${stil}"></i>${esc(l.name)}${l.text && l.text !== l.name ? ` <small>${esc(l.text)}</small>` : ""}</span>`;
  }).join("");
}
```

`zeichneDetail` — Trichter-Zweig und Ausschluss-Text:
```js
  const w = werte.find((x) => x.id === detail.id);
  const d = gezeigt.trichter ? (w ? detailTextStufe(w) : { titel: detail.id, zeilen: [] })
    : w ? detailText(w, ansicht)
    : (detailTextGruppe(detail.id, filterEinheiten(werte, ansicht.filter), ansicht, gezeigt.ausschluss) || { titel: detail.id, zeilen: zeile ? [zeile] : [] });
```
Der Kartenlink bleibt an `ansicht.ebene === "stadtteil" && w` gebunden; bei Trichtern ist `ansicht.ebene` undefiniert, der Link erscheint also nicht.

- [ ] **Step 5: CSS**

In `site/css/perspektiven.css` nach `.kapitel > header .untertitel { … }` ergänzen:
```css
.kapitel > header .datenbasis { font-size: 14px; color: var(--grau); margin: 0 0 12px; padding-left: 10px; border-left: 3px solid var(--rand); }
.kapitel > header .datenbasis a { white-space: nowrap; }
.buehne svg .grund { pointer-events: none; }
```

- [ ] **Step 6: Sichtprüfung**

Run: `python3 pipeline/06_karte_export.py --ohne-kacheln` (schreibt die neuen Kennzahlen und Kapitel), dann `python3 werkzeuge/serve.py 8765` und `http://localhost:8765/site/schlaglichter.html?vorschau=1` öffnen. Prüfen: Kapitel 0 fehlt noch (kommt in Task 6) — die drei Fachkapitel zeigen die Datenbasis-Zeile ohne Link (Kapitel 0 nicht im Index), das graue Segment trägt im Hover und im Detailkasten den Kapiteltext, Konsole ohne Fehler. `cd site && node --test tests/` grün.

- [ ] **Step 7: Commit**

```bash
git add site/js/perspektiven.js site/css/perspektiven.css
git commit -m "feat(schlaglichter): Seite zeichnet Trichter, Datenbasis-Zeile mit Link in Kapitel 0, Ausschluss-Text je Kapitel

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Kapitel 0 „Die Datenbasis“ anlegen

**Files:**
- Create: `kuratierung/perspektiven/datenbasis.json`
- Test: `tests/test_perspektiven.py::test_echte_kapitel_sind_gueltig` (bestehend), Export-Lauf

- [ ] **Step 1: Kapitel schreiben**

`kuratierung/perspektiven/datenbasis.json`:

```json
{
  "id": "datenbasis", "reihenfolge": 0,
  "titel": "Die Datenbasis", "untertitel": "Vom Adreßbuch 1936 zur Karte",
  "freigegeben": false,
  "datenbasis": "", "datenbasis_schritt": "", "ausschluss": "",
  "einleitung": "Jedes Schlaglicht auf dieser Seite beruht auf demselben Buch: dem Essener Adreßbuch von 1936. Bevor die Kapitel Häuser, Berufe und Betriebe zeigen, erklärt dieses Kapitel, was in dem Buch steht, wie es zur Tabelle und von der Tabelle auf die Karte wurde, und wie groß der Ausschnitt ist, den jedes Kapitel wirklich sieht. Die Trichter zeigen bei jedem Schritt, wie viel vom Ganzen übrig bleibt.",
  "quellen": [
    "Essener Adreßbuch 1936. Unter Benutzung amtlicher Quellen. Essen: August Scherl, Deutsche Adreßbuch-Gesellschaft, 1936 (Stadtarchiv Essen; Deutsche Nationalbibliothek Leipzig, ZC 2510)",
    "Digitalisat: Digitale Bibliothek des Vereins für Computergenealogie, https://www.digibib.genealogy.net/viewer/image/857439804_1936/",
    "Transkription: DES-Projekt „Adressbuch Essen 1936“, Verein für Computergenealogie, abgeschlossen 2020",
    "Straßennamen: Essener Straßennamen (Dickhoff 2015), Datensatz DOI 10.5281/zenodo.22757900",
    "Stadtplan von Groß-Essen 1935, Stadt Essen / Historischer Verein (ArcGIS-Dienst geo.essen.de)",
    "Berufe: Ontologie historischer, deutschsprachiger Amts- und Berufsbezeichnungen (OhdAB), Moeller/Uni Halle, FactGrid, CC BY 4.0"
  ],
  "grenzen": "In Teil I fehlen die Seiten 186 bis 258, also alle Nachnamen mit H, I und J, geschätzt 23.000 Personen; sie fehlen schon in der Vorlage der Transkription, nicht erst hier. Straßen, Häuser und Firmen mit diesen Anfangsbuchstaben sind vollständig. Der Erhebungsstand liegt im Lauf des Jahres 1936; die Umbenennungen von 1937 sind noch nicht enthalten. Die Lizenz der Transkription ist noch nicht geklärt (Anfrage beim Verein für Computergenealogie). Stadtteilgrenzen sind die heutigen (OpenStreetMap, ODbL), Straßenlinien folgen der heutigen Führung. Von {eintraege} Zeilen sind {verortet} verortet ({stufe_offen} nicht), verteilt auf {adressen} Adressen. Stand {stand}.",
  "schritte": [
    {"id": "vorlage",
     "text": "Das Essener Adreßbuch 1936 erschien im Verlag August Scherl, 1.198 Seiten stark, mit einem Stadtplan von Groß-Essen als Beilage. Es hat drei Teile mit Adressen: das alphabetische Einwohnerverzeichnis (Teil I), das Häuserbuch mit den Eigentümern je Haus (Teil II) und das Branchenverzeichnis der Betriebe (Teil III). Behörden und Innungen (Teile IV und W) stehen ohne Adresse im Buch und bleiben hier außen vor. Der Verein für Computergenealogie hat das Buch Zeile für Zeile abgeschrieben.",
     "beschreibung": "Trichter: Zeilen der Transkription je Buchteil — Einwohner, Häuser und Eigentümer, Betriebe.",
     "hervorheben": [],
     "ansicht": {"daten": "kennzahlen", "form": "trichter",
       "stufen": [
         {"name": "Zeilen der Teile I bis III", "aus": "eintraege", "farbe": "#94a3b8"},
         {"name": "Teil I: Einwohner", "aus": "eintraege_I", "farbe": "#1d4ed8"},
         {"name": "Teil II: Häuser und Eigentümer", "aus": "eintraege_II", "farbe": "#ca8a04"},
         {"name": "Teil III: Betriebe", "aus": "eintraege_III", "farbe": "#c2410c"}],
       "erklaerungen": {
         "eintraege": "Jede Zeile der Transkription ist ein Eintrag des Buches: eine Person, ein Haus mit Eigentümer oder ein Betrieb.",
         "eintraege_I": "Haushaltsvorstände mit Beruf und Adresse. Die Namen H bis J fehlen in der Vorlage.",
         "eintraege_II": "Ein Eintrag je Haus, mit dem Eigentümer; Eigentümer vieler Häuser stehen oft einmal je Straßenseite.",
         "eintraege_III": "Betriebe nach Branchen, mit Firmenname und Adresse."}}},
    {"id": "weg",
     "text": "Vom Buch zur Karte sind es vier Schritte. Die gescannten Seiten liegen in der Digitalen Bibliothek des Vereins; Freiwillige haben sie im Daten-Eingabe-System abgeschrieben; daraus wurde eine Tabelle. Unsere Pipeline zerlegt jede Adresse in Straße und Hausnummer, findet die heutige Straße über den Datensatz der Essener Straßennamen und den Stadtplan von 1935, sucht die Hausnummer im heutigen Kartenmaterial und vermerkt zu jeder Zeile, wie genau der Punkt sitzt. Die Regel lautet: lieber nicht verortet als falsch.",
     "beschreibung": "Trichter: alle Zeilen, davon verortet — hausgenau, straßengenau oder am Stadtplan 1935 gesetzt — und die Zahl der Adressen auf der Karte.",
     "hervorheben": [],
     "ansicht": {"daten": "kennzahlen", "form": "trichter",
       "stufen": [
         {"name": "Zeilen der Teile I bis III", "aus": "eintraege", "farbe": "#94a3b8"},
         {"name": "verortet", "aus": "verortet", "farbe": "#1d4ed8",
          "segmente": [
            {"name": "hausgenau", "aus": "stufe_haus", "farbe": "#1d4ed8"},
            {"name": "straßengenau", "aus": "stufe_strasse", "farbe": "#60a5fa"},
            {"name": "Stadtplan 1935", "aus": "stufe_stadtplan", "farbe": "#93c5fd"}]},
         {"name": "Adressen auf der Karte", "aus": "adressen", "farbe": "#1d4ed8"}],
       "erklaerungen": {
         "eintraege": "Alle Zeilen der Teile I bis III.",
         "stufe_haus": "Die heutige Hausnummer wurde gefunden; der Punkt sitzt auf dem Haus.",
         "stufe_strasse": "Die Straße ist bekannt, die Hausnummer nicht auffindbar oder nicht verlässlich; der Punkt liegt an der Straße.",
         "stufe_stadtplan": "Die Straße gibt es heute nicht mehr; der Punkt wurde von Hand am Stadtplan von 1935 gesetzt.",
         "adressen": "Mehrere Zeilen teilen sich eine Adresse: alle Bewohner eines Hauses, sein Eigentümer und die Betriebe darin."}}},
    {"id": "besitz",
     "text": "Teil II nennt zu jedem Haus den Eigentümer, in wechselnder Schreibweise: „Fried. Krupp A.-G.“ und „Krupp, Fried., A.G.“ sind derselbe Konzern. Wir haben die Schreibweisen zusammengeführt und jedem Eigentümer eine Klasse gegeben, von Privatperson bis Bergbau. Von Hand geprüft sind alle Körperschaften ab fünf Häusern und die größten Privatpersonen. Wo eine Person ohne Firmennamen als Eigentümer steht, gilt sie per Regel als Privatperson; dieser Anteil ist in allen Grafiken schraffiert, damit niemand ihn für handgeprüft hält.",
     "beschreibung": "Trichter: verortete Adressen, davon mit Besitzklasse — von Hand geprüft oder per Regel.",
     "hervorheben": [],
     "ansicht": {"daten": "kennzahlen", "form": "trichter",
       "stufen": [
         {"name": "Adressen auf der Karte", "aus": "adressen", "farbe": "#94a3b8"},
         {"name": "mit Besitzklasse", "aus": "besitz_geprueft", "farbe": "#d97706",
          "segmente": [
            {"name": "von Hand geprüft", "aus": "besitz_hand", "farbe": "#d97706"},
            {"name": "per Regel: Person ohne Firmenname → Privatperson", "aus": "besitz_regel", "farbe": "#d97706", "muster": "schraffur"}]}],
       "erklaerungen": {
         "adressen": "Alle verorteten Adressen der Teile I bis III.",
         "besitz_hand": "Eigentümer von Hand einer Klasse zugeordnet; Körperschaften ab fünf Häusern vollständig.",
         "besitz_regel": "Eigentümer ist eine Person ohne Firmennamen; die Klasse Privatperson folgt aus dieser Regel, nicht aus einer Prüfung des Einzelfalls."}}},
    {"id": "stellung",
     "text": "Teil I nennt zu fast jedem Eintrag einen Beruf, meist abgekürzt: „Bergm.“, „Kfm.“, „Inval.“. Ein Katalog löst die Abkürzungen auf, und jede häufige Schreibweise wurde von Hand einem Eintrag der OhdAB zugeordnet, einer Ontologie historischer Berufsbezeichnungen. Daraus leiten wir die soziale Stellung ab: Arbeiter, Angestellte, Beamte, Selbständige und weitere, nach der Rechtslage der Zeit. Wo die Automatik nur einen Vorschlag gemacht hat, ist das schraffiert; wo die Bezeichnung nichts hergibt, bleibt die Stellung unbestimmt.",
     "beschreibung": "Trichter: Einwohnereinträge, davon mit geprüftem Beruf, davon Stellung von Hand bestimmt, nach Vorschlag oder unbestimmt.",
     "hervorheben": [],
     "ansicht": {"daten": "kennzahlen", "form": "trichter",
       "stufen": [
         {"name": "Einwohnereinträge (Teil I, verortet)", "aus": "teil_i_n", "farbe": "#94a3b8"},
         {"name": "Beruf einem OhdAB-Eintrag zugeordnet", "aus": "beruf_geprueft_n", "farbe": "#1d4ed8"},
         {"name": "soziale Stellung", "aus": "teil_i_n", "farbe": "#e69f00",
          "segmente": [
            {"name": "von Hand bestimmt", "aus": "stellung_hand_n", "farbe": "#e69f00"},
            {"name": "Vorschlag der Automatik", "aus": "stellung_vorschlag_n", "farbe": "#e69f00", "muster": "schraffur"},
            {"name": "unbestimmt oder Beruf ungeprüft", "aus": "stellung_unbestimmt_n", "farbe": "#c8c8c8"}]}],
       "erklaerungen": {
         "teil_i_n": "Alle verorteten Einträge des Einwohnerverzeichnisses.",
         "beruf_geprueft_n": "Die Berufsangabe ist von Hand einem Eintrag der OhdAB zugeordnet.",
         "stellung_hand_n": "Die Stellung wurde je Berufsschreibweise von Hand entschieden (Berufszählung 1933, Angestelltenversicherungsgesetz 1911).",
         "stellung_vorschlag_n": "Die Stellung stammt aus einer Wortregel und wurde nicht von Hand geprüft.",
         "stellung_unbestimmt_n": "Die Bezeichnung lässt die Stellung offen (etwa „Friseur“ ohne Zusatz) oder der Beruf ist noch nicht geprüft."}}},
    {"id": "gewerbe",
     "text": "Teil III führt die Betriebe nach Rubriken, von „Bäcker“ bis „Zigarren“. Jede Rubrik haben wir einer Branche und einer Betriebsform zugeordnet. Die großen Rubriken sind von Hand entschieden; die mittleren nach dokumentierten Prinzipien, etwa dass ein Zulieferer zur belieferten Branche zählt; die vielen kleinen über eine Wortregel. Auch hier zeigt die Schraffur, was nicht von Hand geprüft ist.",
     "beschreibung": "Trichter: verortete Betriebe, Branche von Hand, nach Prinzipien oder per Wortregel zugeordnet.",
     "hervorheben": [],
     "ansicht": {"daten": "kennzahlen", "form": "trichter",
       "stufen": [
         {"name": "Betriebe (Teil III, verortet)", "aus": "betriebe_n", "farbe": "#94a3b8"},
         {"name": "Branche zugeordnet", "aus": "betriebe_n", "farbe": "#c2410c",
          "segmente": [
            {"name": "von Hand", "aus": "gewerbe_hand_n", "farbe": "#c2410c"},
            {"name": "nach dokumentierten Prinzipien", "aus": "gewerbe_claude_n", "farbe": "#c2410c", "muster": "schraffur"},
            {"name": "per Wortregel", "aus": "gewerbe_regel_n", "farbe": "#f59e0b", "muster": "schraffur"}]}],
       "erklaerungen": {
         "betriebe_n": "Alle verorteten Einträge des Branchenverzeichnisses.",
         "gewerbe_hand_n": "Rubriken, die der Projektleiter selbst zugeordnet hat (die größten, rund zwei Drittel der Betriebe).",
         "gewerbe_claude_n": "Rubriken, die nach den in docs/gewerbe.md festgehaltenen Prinzipien zugeordnet wurden.",
         "gewerbe_regel_n": "Rubriken, deren Branche eine Wortregel aus dem Rubriknamen ableitet."}}}
  ]
}
```

- [ ] **Step 2: Schema-Test und Export laufen lassen**

Run: `python3 -m pytest tests/test_perspektiven.py -q && python3 pipeline/06_karte_export.py --ohne-kacheln`
Expected: Tests PASS; Export läuft ohne `ValueError` durch (alle `aus`-Schlüssel existieren seit Task 1).

- [ ] **Step 3: Sichtprüfung**

`python3 werkzeuge/serve.py 8765`, `http://localhost:8765/site/schlaglichter.html?vorschau=1`: Kapitel 0 steht zuerst, fünf Trichter zeichnen, Schraffur sichtbar, Hover und Klick zeigen den Detailkasten ohne Kartenlink, die Datenbasis-Zeilen der Fachkapitel tragen jetzt den Link „Datenbasis ›“, der zum passenden Schritt in Kapitel 0 springt und dessen Trichter zeigt.

- [ ] **Step 4: Commit**

```bash
git add kuratierung/perspektiven/datenbasis.json
git commit -m "feat(schlaglichter): Kapitel 0 „Die Datenbasis“ — fünf Trichter von der Vorlage bis zu den drei Datenkernen (Textentwurf, nicht freigegeben)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Texte der Kapitel 1 bis 3 und Wortlaut „mit Besitzklasse“

**Files:**
- Modify: `kuratierung/perspektiven/wohneigentum.json`, `stellung.json`, `gewerbe.json` (Textfelder; Ansichten unverändert)
- Modify: `site/js/formen/balken.js` (`regelText`), `site/js/formen/skalen.js` (`nennerText`)
- Modify: `site/ueber.html` (Sozialscore-Satz, Kennzahlenblock, Berufszahlen)
- Test: bestehende Node-Tests (Textkonstanten), Nachrechnung per Skript

Alle Zahlen im Text sind am 2026-09-27 gegen `site/daten/ebenen/stadtteile.json`, `ebenen/strassen.json`, `layout/eigentuemer.json`, `layout/gewerbe.json` nachgerechnet (Werte unten in Step 1). Vor dem Commit Step 4 erneut rechnen; weichen Werte ab, Text anpassen.

- [ ] **Step 1: Nachrechnungs-Skript anlegen und laufen lassen**

`werkzeuge/perspektiven_zahlen.py` (versioniert, damit der Projektleiter es nach jeder Prüfrunde wiederholen kann):

```python
"""Rechnet die Zahlen nach, die die Texte der Schlaglichter nennen — gegen site/daten/ebenen und layout.
Aufruf: python3 werkzeuge/perspektiven_zahlen.py. Kein Test, ein Prüfblatt."""
import json, pathlib
W = pathlib.Path(__file__).resolve().parents[1] / "site" / "daten"
st = json.loads((W / "ebenen" / "stadtteile.json").read_text())
sr = json.loads((W / "ebenen" / "strassen.json").read_text())
kz = json.loads((W / "kennzahlen.json").read_text())
S = lambda k: sum(x.get(k, 0) for x in st)

def rang(zaehler, nenner, min_n=50, rev=True, n=5):
    r = []
    for x in st:
        d = sum(x.get(k, 0) for k in nenner)
        if d < min_n: continue
        z = sum(x.get(k, 0) for k in zaehler)
        r.append((x["id"], z, d, round(100 * z / d, 1)))
    return sorted(r, key=lambda t: t[3], reverse=rev)[:n]

BS = ["n_bs_privatperson", "n_bs_stadt_staat", "n_bs_bergbau", "n_bs_industrie", "n_bs_genossenschaft_siedlung", "n_bs_kirche_stiftung", "n_bs_bank_versicherung", "n_bs_sonstige", "n_bs_gemischt"]
ST = ["n_st_arbeiter", "n_st_angestellte", "n_st_beamte", "n_st_selbstaendige", "n_st_freie_berufe", "n_st_unternehmer", "n_st_kaufleute", "n_st_ohne_erwerb"]
print("Kennzahlen:", {k: kz[k] for k in ("adressen", "besitz_geprueft", "besitz_hand", "besitz_regel", "teil_i_n", "stellung_hand_n", "stellung_unbestimmt_n", "betriebe_n")})
print("Besitz gesamt:", {k: S(k) for k in BS}, "ungeprüft", S("n_bs_ungeprueft"))
print("Privat oben:", rang(["n_bs_privatperson"], BS)); print("Privat unten:", rang(["n_bs_privatperson"], BS, rev=False))
print("Zechen+Werke:", rang(["n_bs_bergbau", "n_bs_industrie"], BS)); print("Genossenschaft:", rang(["n_bs_genossenschaft_siedlung"], BS))
print("Stiftung:", rang(["n_bs_kirche_stiftung"], BS, n=2))
print("Stellung gesamt:", {k: S(k) for k in ST}, "unbestimmt", S("n_st_unbestimmt"), "Teil I", S("n_I"))
print("Arbeiter oben:", rang(["n_st_arbeiter"], ST, 200)); print("Arbeiter unten:", rang(["n_st_arbeiter"], ST, 200, rev=False))
print("Bürgertum:", rang(["n_st_beamte", "n_st_angestellte", "n_st_freie_berufe", "n_st_unternehmer"], ST, 200))
print("unbestimmt oben:", rang(["n_st_unbestimmt"], ST + ["n_st_unbestimmt"], 200)); print("unbestimmt unten:", rang(["n_st_unbestimmt"], ST + ["n_st_unbestimmt"], 200, rev=False))
GW = [k for k in st[0] if k.startswith("n_gw_")]
print("Gewerbe je Branche:", sorted(((k, S(k)) for k in GW), key=lambda t: -t[1]), "Betriebe", S("n_III"))
d = sorted(((x["id"], round(1000 * x.get("n_III", 0) / x["n_I"]), x.get("n_III", 0)) for x in st if x["n_I"] >= 200), key=lambda t: -t[1])
print("Dichte oben:", d[:5], "unten:", d[-4:])
l = sorted(((x["id"], round(1000 * x.get("n_gw_lebensmittel", 0) / x["n_I"], 1)) for x in st if x["n_I"] >= 200), key=lambda t: -t[1])
print("Lebensmittel oben:", l[:5], "unten:", l[-3:])
g = sorted(((x["name"], x.get("n_III", 0), x.get("n_I", 0), round(1000 * x.get("n_III", 0) / x["n_I"])) for x in sr if x.get("n_I", 0) >= 30), key=lambda t: -t[3])
print("Geschäftsstraßen nach Dichte:", g[:6])
print("Geschäftsstraßen nach Zahl:", sorted(((x["name"], x.get("n_III", 0)) for x in sr), key=lambda t: -t[1])[:5])
for name in ("eigentuemer", "gewerbe"):
    kreise = json.loads((W / "layout" / f"{name}.json").read_text())["kreise"]
    print(name, len(kreise), [(k["id"], k["n"], k["gruppe"]) for k in sorted(kreise, key=lambda k: -k["n"])[:10]])
```

Run: `python3 werkzeuge/perspektiven_zahlen.py`
Expected (Stand 2026-09-27, Basis der Texte in Step 2):
- Besitz: Privat 40.800, Industrie 8.365, Bergbau 5.428, Genossenschaft 5.321, Stadt 2.552, Kirche/Stiftung 1.079; Privat oben Frintrop 93 %, unten Margaretenhöhe 0,7 %, Vogelheim 19 %, Karnap 25 %; Zechen+Werke Rellinghausen 66 %, Vogelheim 58 %, Katernberg 57 %, Karnap 53 %; Genossenschaft Huttrop 38 %, Fulerum 32 %, Bergeborbeck 28 %; Stiftung Margaretenhöhe 98 %.
- Eigentümer-Layout 287 Kreise; Krupp 3.351, VSt 2.386, Stadt Essen 2.069, Hoesch 1.545, EBV König Wilhelm 925, GBAG 867, Stinnes 725, Bergm. Siedlung Essen Nord 719, Margarethe Krupp-Stiftung 707.
- Stellung: Arbeiter 74.635, ohne Erwerb 15.664, Angestellte 12.604, Selbständige 11.934, Beamte 10.444, Kaufleute 5.057, freie Berufe 2.348, Unternehmer 1.364; unbestimmt 39.118 von 173.168. Arbeiter oben Vogelheim 77 %, Schonnebeck 74 %, Karnap 73 %; unten Margaretenhöhe 20 %, Huttrop 28 %, Stadtwald 28 %, Südviertel 28 %. Bürgertum Margaretenhöhe 56 %, Huttrop 48 %, Stadtwald 44 %. Unbestimmt Stadtkern 39 %, Südviertel 35 %; Schonnebeck 14 %, Karnap 14 %.
- Gewerbe: Lebensmittel 3.951, Textil/Bekleidung 2.961, Bau 2.385, Metall 1.311, Gastgewerbe 1.298; 18.052 Betriebe; Rubriken Schneider für Herren 906, Schankwirt 863, Maler 703, Schuhmacher 669. Dichte Stadtkern 343, Südviertel 210, Rüttenscheid 165; unten Leithe 24, Bergeborbeck 34. Lebensmittel Westviertel 62, Stadtkern 49; Margaretenhöhe 7,7. Straßen nach Dichte Limbecker Straße 756 (62 Betriebe auf 82 Einwohnereinträge), Kettwiger Straße 568 (138/243); nach Zahl Rüttenscheider Straße 389, Steeler Straße 362.

- [ ] **Step 2: Texte in die drei Kapitel schreiben**

Nur die genannten Felder ersetzen; `ansicht`-Objekte, `id`, `reihenfolge`, `hervorheben` bleiben. Die Zeile `"datenbasis"`, `"datenbasis_schritt"`, `"ausschluss"` aus Task 2 bleiben.

**wohneigentum.json** — `untertitel`, `einleitung`, `grenzen`, je Schritt `text` und `beschreibung`:

```json
  "untertitel": "Wem gehörten die Häuser? Privat, Zechen und Werke, Genossenschaften, Stadt, Stiftungen",
  "einleitung": "Das Häuserbuch des Adressbuchs nennt zu jedem Haus den Eigentümer. Daraus lässt sich lesen, wie das Wohnen in Essen organisiert war: Wo standen die Einzelhäuser von Privatleuten, wo die Kolonien der Zechen und Stahlwerke, wo die Siedlungen der Genossenschaften? Das Kapitel zeigt die Klassen im Ganzen, die großen Eigentümer, und dann Stadtteil für Stadtteil.",
  "grenzen": "Von {adressen} verorteten Adressen tragen {besitz_geprueft} eine Besitzklasse ({besitz_geprueft_prozent} %). Von Hand geprüft sind {besitz_hand} davon: alle Körperschaften ab fünf Häusern und die größten Privatpersonen. {besitz_regel} Adressen sind nur über die Regel „Person ohne Firmenname → Privatperson“ klassifiziert; in den Grafiken sind sie an den Privatpersonen schraffiert ausgewiesen. {besitz_spanne} Adressen haben ihre Klasse über eine Hausnummernspanne des Häuserbuchs („2–84 E. …“ steht einmal je Straßenseite, die Häuser dazwischen sind im Buch nicht einzeln dem Eigentümer zugeschrieben) und {besitz_nummer} über die Zeile derselben Hausnummer in anderer Schreibung. Alle Anteile beziehen sich auf die Adressen mit Besitzklasse; ausgeschlossen sind Adressen ohne Eigentümerangabe und solche, deren Eigentümer noch keiner Klasse zugeordnet ist. Die Karten zeigen heutige Stadtteilgrenzen. Erhebungsstand ist der Lauf des Jahres 1936; die Namenslücke H–J betrifft nur Teil I, das Häuserbuch ist vollständig.",
```
Schritte:
```json
    {"id": "anteile", "text": "Fast zwei Drittel der Häuser mit bekannter Klasse gehörten Privatpersonen. Das übrige Drittel teilen sich Industrie, Bergbau und Genossenschaften zu ähnlichen Teilen, dahinter Stadt und Staat, Kirchen und Stiftungen, Banken. Der schraffierte Teil der Privatpersonen ist nicht von Hand geprüft: Dort steht im Buch eine Person ohne Firmennamen als Eigentümer, und die Regel macht daraus eine Privatperson. Das graue Segment sind Adressen, für die das Buch keinen Eigentümer nennt oder deren Eigentümer noch keiner Klasse zugeordnet ist.", "beschreibung": "Ein Balken mit acht farbigen Segmenten der Besitzklassen und einem grauen Segment für Adressen ohne zugeordneten Eigentümer.", ...},
    {"id": "eigentuemer", "text": "Die großen Eigentümer als Kreise, die Fläche nach der Zahl der Häuser. Die Firma Krupp führt mit über dreitausend Häusern, dahinter die Vereinigten Stahlwerke, die Stadt Essen und Hoesch. Dann folgen die Zechengesellschaften: der Essener Bergwerks-Verein König Wilhelm, die Gelsenkirchener Bergwerks-AG, die Gewerkschaft Mathias Stinnes. Die Bergmannssiedlung Essen-Nord und der Allbau stehen für die Genossenschaften, die Margarethe-Krupp-Stiftung für die Margaretenhöhe. Ein Klick auf einen Kreis nennt die Häuserzahl.", "beschreibung": "Bubbles der von Hand geprüften Eigentümer, gefärbt nach Klasse, gepackt je Klasse; Fläche nach Häuserzahl.", ...},
    {"id": "rangliste", "text": "Wo gehörten die Häuser den Leuten selbst? Die Rangliste ordnet die Stadtteile nach dem Anteil der Privatpersonen. Oben stehen die dörflich gebliebenen Ränder wie Frintrop, Überruhr-Holthausen und Byfang, dazu das bürgerliche Rüttenscheid mit seinen Mietshäusern in privater Hand. Ganz unten die Margaretenhöhe, die fast vollständig der Stiftung gehört, und die Zechenstadtteile im Norden: Vogelheim, Karnap, Katernberg.", "beschreibung": "Rangliste der Stadtteile nach dem Anteil der Adressen in Privatbesitz; Stadtteile unter 50 Adressen mit Besitzklasse grau.", ...},
    {"id": "karte-werkswohnungen", "text": "Zechen und Werke bauten für ihre Belegschaften. In Rellinghausen gehören zwei Drittel der Häuser mit bekannter Klasse dem Bergbau oder der Industrie: die Kolonie der Gelsenkirchener Bergwerks-AG und der Essener Steinkohlenbergwerke an Silberbank-, Finefrau- und Schatzreichstraße. Vogelheim, Katernberg und Karnap liegen bei über der Hälfte. Im Süden und in den bürgerlichen Vierteln spielen Werkswohnungen kaum eine Rolle.", "beschreibung": "Stadtteilkarte: Anteil der Adressen im Besitz von Bergbau und Industrie an den Adressen mit Besitzklasse; Stadtteile unter 50 solcher Adressen grau.", ...},
    {"id": "karte-genossenschaften", "text": "Genossenschaften und Siedlungsgesellschaften bauten dort, wo nach dem Ersten Weltkrieg Wohnungen fehlten und Bauland frei war: am stärksten in Huttrop, wo mehr als jedes dritte Haus mit bekannter Klasse ihnen gehört, dann in Fulerum und Bergeborbeck. Die Margaretenhöhe erscheint hier nicht: Ihre Häuser gehören der Margarethe-Krupp-Stiftung und zählen als Stiftung, nicht als Genossenschaft.", "beschreibung": "Stadtteilkarte: Anteil der Adressen im Besitz von Genossenschaften und Siedlungsgesellschaften an den Adressen mit Besitzklasse; Stadtteile unter 50 solcher Adressen grau.", ...}
```

**stellung.json**:

```json
  "untertitel": "Arbeiter, Angestellte, Beamte, Bürgertum: Wer wohnte wo?",
  "einleitung": "Das Einwohnerverzeichnis nennt zu jedem Haushaltsvorstand einen Beruf. Aus der Berufsbezeichnung leiten wir eine soziale Stellung ab, so wie die Berufszählung von 1933 sie unterschied: Arbeiter, Angestellte, Beamte, Selbständige, freie Berufe, Unternehmer und Menschen ohne Erwerbsberuf, etwa Invaliden und Witwen. Die Kaufleute bleiben eine eigene Gruppe, weil „Kaufmann“ im Adressbuch vom Ladeninhaber bis zum Prokuristen alles sein kann. Das Kapitel zeigt die Anteile im Ganzen und dann, wie scharf die Stadt geteilt war.",
  "grenzen": "Grundlage sind {teil_i_n} verortete Einträge des Einwohnerverzeichnisses. Für {stellung_hand_n} davon ({stellung_geprueft} %) ist die Stellung je Berufsschreibweise von Hand bestimmt, für {stellung_vorschlag_n} ({stellung_vorschlag} %) stammt sie aus einer Wortregel ohne Handprüfung (in den Grafiken schraffiert), {stellung_unbestimmt_n} ({stellung_unbestimmt} %) bleiben unbestimmt, weil die Bezeichnung die Stellung offenlässt oder der Beruf noch nicht geprüft ist. Dieser Anteil ist nicht zufällig verteilt: In bürgerlichen Vierteln sind seltene Berufsbezeichnungen häufiger und öfter noch ungeprüft (Stadtkern 39 %, Schonnebeck 14 %). „Arbeiter/Gehilfen (nach Schreibung)“ schließt bei Handwerksberufen ohne Meister- oder Gehilfenzusatz auch Inhaber ein; ein Abgleich mit dem Branchenverzeichnis steht noch aus. Die Klassen folgen der Berufszählung 1933 und dem Angestelltenversicherungsgesetz von 1911 (docs/stellung.md). Die Namen H bis J fehlen in der Vorlage. Heutige Stadtteilgrenzen.",
```
Schritte:
```json
    {"id": "anteile", "text": "Essen war 1936 eine Arbeiterstadt: Mehr als jeder zweite Haushaltsvorstand mit bestimmter Stellung war Arbeiter oder Gehilfe. Es folgen die Menschen ohne Erwerbsberuf, vor allem Invaliden und Witwen, dann Angestellte, Selbständige und Beamte in ähnlicher Größe. Freie Berufe und Unternehmer sind klein. Das graue Segment sind Einträge, deren Beruf noch nicht geprüft ist oder deren Bezeichnung die Stellung offenlässt.", "beschreibung": "Ein Balken mit acht farbigen Segmenten der Stellungsklassen und einem grauen Segment für unbestimmte Einträge.", ...},
    {"id": "nord-sued", "text": "Die Rangliste ordnet die Stadtteile nach dem Arbeiteranteil, und sie liest sich wie eine Karte von Nord nach Süd. Oben Vogelheim, Schonnebeck und Karnap mit über siebzig Prozent, die Zechenstadtteile des Nordens. Unten die Margaretenhöhe mit einem Fünftel, dann Huttrop, Stadtwald, Südviertel und Rüttenscheid. Zwischen dem höchsten und dem niedrigsten Wert liegen mehr als fünfzig Prozentpunkte.", "beschreibung": "Rangliste der Stadtteile nach dem Anteil der Arbeiter an den Einträgen mit bestimmter Stellung; Stadtteile unter 200 solchen Einträgen grau.", ...},
    {"id": "karte-arbeiter", "text": "Dieselben Zahlen auf der Karte zeigen die Teilung der Stadt: ein dunkler Norden entlang der Zechen von Bergeborbeck bis Katernberg, ein heller Süden von Rüttenscheid bis Bredeney. Die Emscherzone im Norden und die Ruhrhöhen im Süden waren schon 1936 zwei verschiedene Städte.", "beschreibung": "Stadtteilkarte: Arbeiteranteil an den Einträgen mit bestimmter Stellung; Stadtteile unter 200 solchen Einträgen grau.", ...},
    {"id": "karte-buergertum", "text": "Das Spiegelbild: Beamte, Angestellte, freie Berufe und Unternehmer zusammengenommen. Auf der Margaretenhöhe stellen sie mehr als die Hälfte, in Huttrop fast die Hälfte, in Stadtwald, Rüttenscheid und Südviertel gut vierzig Prozent. Die Margaretenhöhe war als Gartenstadt der Krupp-Stiftung für Beamte und Angestellte gedacht, und so wohnte man dort auch.", "beschreibung": "Stadtteilkarte: Anteil von Beamten, Angestellten, freien Berufen und Unternehmern an den Einträgen mit bestimmter Stellung; Stadtteile unter 200 solchen Einträgen grau.", ...},
    {"id": "mischung", "text": "Vier Stadtteile im Vergleich, jeder als eigener Balken. Katernberg ist fast einfarbig: Arbeiter, dazu Invaliden und Witwen. Der Stadtkern und das Südviertel sind gemischt, mit Selbständigen, Kaufleuten und Angestellten. Die Margaretenhöhe kippt zur anderen Seite. Die Zahl neben jedem Balken misst die Mischung: null wäre eine einzige Klasse, eins wären alle Klassen gleich stark.", "beschreibung": "Gestapelte Anteile der acht Klassen je Stadtteil für Stadtkern, Südviertel, Katernberg und Margaretenhöhe; der Mischungsgrad steht als Zahl neben jedem Balken.", ...},
    {"id": "kaufleute-angestellt", "text": "Eine Probe aufs Exempel: Zählt man die Kaufleute zu den Angestellten, wächst das Bürgertum sichtbar, vor allem im Stadtkern und im Südviertel, wo die Kaufleute wohnten. Zählte man sie zu den Selbständigen, änderte sich die Karte nicht, denn Selbständige gehören hier nicht zum Bürgertum. Die Entscheidung, was ein „Kaufmann“ war, verschiebt das Bild also nur an einer Stelle, aber dort deutlich.", "beschreibung": "Stadtteilkarte wie „Bürgertum“, die Kaufleute den Angestellten zugeschlagen.", ...}
```

**gewerbe.json**:

```json
  "untertitel": "Handwerk, Handel und Gastwirtschaft: Wo die Stadt versorgt wurde",
  "einleitung": "Das Branchenverzeichnis führt die Betriebe Essens unter Rubriken von „Bäcker“ bis „Zigarren“. Wir haben die Rubriken fünfzehn Branchen zugeordnet. Das Kapitel zeigt, welche Branchen die Stadt prägten, wo Betriebe dicht standen und wo dünn, und welche Straßen die Geschäftsstraßen waren. Gezählt werden Betriebe, nicht Beschäftigte: Der Kiosk und die Kruppsche Gussstahlfabrik sind hier je ein Eintrag.",
  "grenzen": "Grundlage sind {betriebe_n} verortete Betriebe des Branchenverzeichnisses. Die Branche ist bei {gewerbe_hand_n} von ihnen ({gewerbe_geprueft} %) von Hand zugeordnet, bei {gewerbe_claude_n} ({gewerbe_entschieden} %) nach den in docs/gewerbe.md festgehaltenen Prinzipien und bei {gewerbe_regel_n} ({gewerbe_vorschlag} %) per Wortregel aus dem Rubriknamen. Dichte heißt hier: Betriebe je 1.000 Einträge des Einwohnerverzeichnisses derselben Einheit; sie misst die Nähe von Versorgung und Bewohnern, nicht die Größe der Betriebe. Ausgeschlossen sind Rubriken ohne Branche. Die Namenslücke H–J betrifft das Branchenverzeichnis nicht. Heutige Stadtteilgrenzen; Straßenlinien in heutiger Führung.",
```
Schritte:
```json
    {"id": "rubriken", "text": "Jede Rubrik ein Kreis, die Fläche nach der Zahl der Betriebe, die Farbe nach Branche. Die größten Kreise sind Handwerk und Alltagsversorgung: Herrenschneider und Schankwirte an der Spitze mit je fast neunhundert Betrieben, dann Maler, Schuhmacher, Lebensmittelgeschäfte, Kolonialwarenläden, Friseure, Bäcker und Metzger. Die Lebensmittelbranche ist mit fast viertausend Betrieben die größte, gefolgt von Textil und Bekleidung und dem Bau.", "beschreibung": "Bubbles der Rubriken, gefärbt nach Branche, gepackt je Branche; Fläche nach Zahl der Betriebe.", ...},
    {"id": "dichte", "text": "Wo standen die meisten Betriebe je tausend Einwohnereinträge? Im Stadtkern mehr als dreihundert, im Südviertel gut zweihundert, in Rüttenscheid, im Westviertel und in Werden um die hundertsechzig. Am dünnen Ende liegen Leithe, Bergeborbeck, Freisenbruch und Vogelheim mit weniger als fünfzig. Die Zechenkolonien wurden bewohnt, aber die Geschäfte lagen anderswo.", "beschreibung": "Rangliste der Stadtteile nach Betrieben je 1.000 Einträgen des Einwohnerverzeichnisses; Stadtteile unter 200 solchen Einträgen grau.", ...},
    {"id": "karte-lebensmittel", "text": "Die Lebensmittelversorgung allein: Bäcker, Metzger, Kolonialwaren, Milch, Obst und Gemüse. Am dichtesten im Westviertel und im Stadtkern, dann Südviertel, Werden und Steele, die alten Zentren. Die Margaretenhöhe hat die wenigsten Lebensmittelbetriebe je Einwohnereintrag: Die Gartenstadt war zum Wohnen gebaut, eingekauft wurde am Marktplatz und außerhalb.", "beschreibung": "Stadtteilkarte: Lebensmittelbetriebe je 1.000 Einträge des Einwohnerverzeichnisses; Stadtteile unter 200 solchen Einträgen grau.", ...},
    {"id": "geschaeftsstrassen", "text": "Die fünfzehn dichtesten Geschäftsstraßen, gemessen an Betrieben je Einwohnereintrag. Vorn liegt die Limbecker Straße, wo auf 82 Einwohnereinträge 62 Betriebe kamen, dann Rathenaustraße, Juliusstraße und die Kettwiger Straße mit 138 Betrieben. Nach der reinen Zahl führen dagegen die langen Ausfallstraßen, Rüttenscheider und Steeler Straße; dort verteilen sich die Läden auf viele Wohnhäuser.", "beschreibung": "Rangliste der Straßen nach Betrieben je 1.000 Einträgen des Einwohnerverzeichnisses, die fünfzehn dichtesten; Straßen unter 30 solchen Einträgen grau.", ...}
```

- [ ] **Step 3: Wortlaut in Code und Über-Seite**

`site/js/formen/balken.js` — `regelText` bleibt inhaltlich, die Formulierung „klassifiziert“ ist schon richtig. `site/js/formen/skalen.js` — `nennerText`: `"geprüften Adressen"` → `"Adressen mit Besitzklasse"`. Danach in `site/tests/formen.test.js` und `site/tests/perspektiven.test.js` mit `grep -n "geprüften Adressen" site/tests/*.js` die Erwartungen anpassen.

`site/ueber.html`:
- Im Absatz `#stand`: den Satz „Geplant: ein Sozialscore je Straße aus den Berufen.“ ersetzen durch „In Arbeit: die Schlaglichter (Kapitel zu Datenbasis, Wohneigentum, sozialer Stellung, Gewerbe) und eine Werkstatt für eigene Ansichten.“
- Im Kennzahlenblock (Script unten): `[kz.besitz_geprueft, "Adressen mit geprüftem Eigentümer"]` → `[kz.besitz_geprueft, "Adressen mit Besitzklasse"], [kz.besitz_hand, "davon von Hand geprüft"]`.
- Im Absatz `#berufe`: die Zahlen „1.537 Schreibweisen, das sind 97,8 % aller Berufsnennungen mit mindestens fünf Belegen; die übrigen 440 Schreibweisen (2,2 %)“ sind ein älterer Stand mit anderem Nenner. Ersetzen durch einen Satz ohne feste Zahl, der die Kennzahl unten nennt: „jede Zuordnung wurde von Hand entschieden; der Anteil der Einwohnereinträge mit geprüftem Beruf steht in den Kennzahlen unten (‚Einwohner mit geprüftem Beruf‘), die übrigen Schreibweisen blieben mangels passendem Eintrag oder wegen unklarer Bedeutung offen.“
- Im Absatz `#eigentuemer`: „Farbig sind auf der Karte nur geprüfte Zuordnungen, alle anderen Häuser grau.“ → „Farbig sind auf der Karte Adressen mit Besitzklasse; per Regel klassifizierte Privatpersonen sind als solche gekennzeichnet, alle übrigen Häuser grau.“
- Im Absatz `#schlaglichter`: „in drei Kapiteln“ → „in vier Kapiteln: Datenbasis, Wohneigentum, soziale Stellung, Gewerbe und Versorgung“.

- [ ] **Step 4: Nachrechnen, Tests, Export, Sichtprüfung**

Run: `python3 werkzeuge/perspektiven_zahlen.py` (Werte mit Step 1 vergleichen), `python3 -m pytest -q`, `cd site && node --test tests/`, `python3 pipeline/06_karte_export.py --ohne-kacheln`, Seite mit `?vorschau=1` lesen: jeder Platzhalter gefüllt (kein `{…}` im Text), jede genannte Zahl in der Grafik daneben wiederzufinden.

- [ ] **Step 5: Commit**

```bash
git add kuratierung/perspektiven/ werkzeuge/perspektiven_zahlen.py site/js/formen/skalen.js site/tests/ site/ueber.html
git commit -m "feat(schlaglichter): Textentwürfe der Kapitel 1–3, Wortlaut „mit Besitzklasse“, Über-Seite ohne Sozialscore; Prüfblatt perspektiven_zahlen.py

Zahlen nachgerechnet gegen ebenen/stadtteile.json, ebenen/strassen.json, layout/*.json (Stand 2026-09-27).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Dokumentation

**Files:**
- Modify: `docs/perspektiven.md` (Schema, Platzhalter, Kapitel 0)
- Modify: `README.md` (Kennzahlen-Abschnitt, Ausgabetabelle)
- Modify: `~/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Journal.md`

- [ ] **Step 1: `docs/perspektiven.md`**

Kopfzeile „Stand“ auf 2026-09-27 mit vier Kapiteln (Datenbasis, Wohneigentum, Soziale Stellung, Gewerbe und Versorgung). In der Tabelle der Kapitel-Pflichtfelder drei Zeilen ergänzen:

```markdown
| `datenbasis` | str | Unterzeile unter dem Titel mit Platzhaltern; Pflicht (nicht leer) für Fachkapitel, leer in Kapitel 0 |
| `datenbasis_schritt` | str | Schritt-id in Kapitel 0, auf die „Datenbasis ›“ verweist (Anker `#s-datenbasis-<id>`); Link nur, wenn Kapitel 0 sichtbar ist |
| `ausschluss` | str | Text für das graue Segment (Legende, Hover, Detailkasten), z. B. „ohne Eigentümerangabe oder Eigentümer nicht zugeordnet“ |
```

Neuer Abschnitt nach „Gruppen und die Kurzform `wie:`“:

```markdown
## Trichter-Ansicht (`daten: "kennzahlen"`, `form: "trichter"`)

Kapitel 0 „Die Datenbasis“ zeichnet keine Ebenen, sondern Kennzahlen aus `site/daten/kennzahlen.json`.
Die Ansicht trägt statt `gruppen` eine Liste `stufen`, jede mit `name`, `aus` (Schlüssel in kennzahlen.json),
`farbe`, optional `segmente` (gleiche Felder, keine weitere Verschachtelung) und `muster: "schraffur"` für
Anteile, die nicht von Hand geprüft sind; `erklaerungen` ordnet Schlüsseln den Text des Detailkastens zu.
`daten: kennzahlen` ist nur mit `form: trichter` zulässig und umgekehrt; `ebene`, `mass`, `bezug`, `min_n`,
`kaufleute`, `unsicher`, `filter`, `karte` entfallen. `pruefe_ansicht` prüft Struktur und Namen; ob jeder
`aus`-Schlüssel existiert, prüft der Export (`pruefe_kennzahlen_bezug`) und bricht sonst mit `ValueError` ab.
Die Form (`site/js/formen/trichter.js`) zeichnet Stufen als Balken untereinander, Breite proportional zur
ersten Stufe, Beschriftung „x von y (z %)“; Segmente teilen ihre Stufe und sind auf deren Breite begrenzt.
Fehlt eine Kennzahl (alter Export), zeigt die Stufe „—“. Trichter-Schritte haben keinen Karten- und
Werkstattlink. Absolute Kennzahlen dafür: `eintraege`, `eintraege_I/II/III`, `stufe_haus/strasse/stadtplan/offen`,
`besitz_hand`, `teil_i_n`, `beruf_geprueft_n`, `stellung_hand_n/vorschlag_n/unbestimmt_n`, `betriebe_n`,
`gewerbe_hand_n/claude_n/regel_n`.
```

Im Abschnitt „Platzhalter in `grenzen`“: Liste um die neuen Kennzahlen ergänzen, `PROZENT_BASIS` jetzt `besitz_geprueft` und `besitz_hand`, Hinweis, dass `datenbasis` dieselben Platzhalter nutzt.

- [ ] **Step 2: README**

Im Abschnitt „Kennzahlen (`site/daten/kennzahlen.json`)“ einen Absatz anhängen:

```markdown
Seit 2026-09-27 zusätzlich absolute Zähler für die Trichter von Kapitel 0 der Schlaglichter: `eintraege`,
`eintraege_I/II/III`, `stufe_haus/strasse/stadtplan/offen`, `besitz_hand` (= `besitz_geprueft − besitz_regel`),
`teil_i_n`, `beruf_geprueft_n`, `stellung_hand_n/vorschlag_n/unbestimmt_n` (Summe = `teil_i_n`), `betriebe_n`,
`gewerbe_hand_n/claude_n/regel_n` (Summe = `betriebe_n`). Wortlaut: `besitz_geprueft` heißt nach außen
„Adressen mit Besitzklasse“; „von Hand geprüft“ ist nur `besitz_hand`. Prüfblatt für die Zahlen in den
Kapiteltexten: `python3 werkzeuge/perspektiven_zahlen.py`.
```

In der Ausgabetabelle die Zeile `perspektiven/index.json` ergänzen um „vier Kapitel, Kapitel 0 Datenbasis mit Trichtern“.

- [ ] **Step 3: Journal**

Anhängen:

```markdown
## 2026-09-27 — Schlaglichter Schritt 1: Kapitel 0, Trichter, Ausschluss, Texte

Spec `2026-09-27-datenbasis-kapitel0-design.md`, Plan gleichen Datums. Umgesetzt: absolute Kennzahlen im
Export; Kapitel-Schema mit Trichter-Ansicht (`daten: kennzahlen`), Feldern `datenbasis`, `datenbasis_schritt`,
`ausschluss`; Form `trichter.js` mit Schraffur für nicht handgeprüfte Anteile; Datenbasis-Zeile je
Fachkapitel mit Link in Kapitel 0 (nur, wenn es sichtbar ist); graues Segment heißt je Kapitel konkret.
Kapitel 0 „Die Datenbasis“ mit fünf Trichtern (Vorlage, Weg, Besitz, Stellung, Gewerbe). Texte aller vier
Kapitel als Entwurf, Zahlen mit `werkzeuge/perspektiven_zahlen.py` nachgerechnet. Wortlaut: „mit Besitzklasse“
statt „geprüft“, „von Hand geprüft“ nur ohne Regel; Über-Seite ohne Sozialscore-Satz. Alles `freigegeben:
false` bis zur Handprüfung durch Christos.
```

- [ ] **Step 4: Tests und Commit**

Run: `python3 -m pytest -q && (cd site && node --test tests/)`
Expected: alle PASS.

```bash
git add docs/perspektiven.md README.md
git commit -m "docs(perspektiven): Trichter-Ansicht, Kapitelfelder datenbasis/ausschluss, absolute Kennzahlen, Kapitel 0

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```
