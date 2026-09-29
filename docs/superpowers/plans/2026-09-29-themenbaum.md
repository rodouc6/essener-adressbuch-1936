# Themenbaum Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jedes Thema zeigt in der Sidebar einen Baum aus Oberkategorien (Kästchen = Farbschalter, Pfeil = Klappliste) und Einzelbezeichnungen als Pills, die einen typisierten Vergleich (`eig:`/`norm:`, bis fünf) starten; das Thema Berufe färbt nach Stellung; die Legende rechts unten erklärt nur noch Zeichen.

**Architecture:** Die Pipeline exportiert je Thema mit `baum: true` eine Liste `themen/<id>_liste.json` (Oberkategorie → Einträge mit Schlüssel, Name, Häuserzahl) und das Hausfeld `stellung`. Im Browser wird `eigentuemer` zu `vergleich` (typisierte Schlüssel, alte URLs werden migriert), `treffer()` baut Gruppen je Schlüssel, ein neues DOM-freies Modul `themenbaum.js` rendert Baum und Pills, `sidebar.js` hängt die Ereignisse an, `app.js` verliert die Schalter aus der Legende.

**Tech Stack:** Python 3 / pytest (Pipeline), ES-Module ohne Bundler, MapLibre GL 4.7.1, node:test, Playwright (Sichtprüfung).

**Spec:** `docs/superpowers/specs/2026-09-29-themenbaum-design.md`

## Global Constraints

- Höchstens **fünf** Schlüssel im Vergleich (`MAX_VERGLEICH = 5` in `zustand.js`); Schlüsselform `eig:<Name>` oder `norm:<ohdab_id>`; URL `vergleich=a|b` (Trenner `|`); alte Parameter `eigentuemer=` und `ohdab=` werden beim Lesen migriert und nie mehr geschrieben.
- Palette `FARBEN.gruppen = ["#dc2626", "#2563eb", "#16a34a", "#7c3aed", "#f59e0b"]`, Farbe hängt am Platz.
- Klapplisten: je Oberkategorie die 15 häufigsten, dann „alle n anzeigen“; genau eine Oberkategorie offen; Klappzustand nicht in der URL.
- Stellung: neun Klassen `arbeiter, angestellte, beamte, selbstaendige, freie_berufe, unternehmer, kaufleute, ohne_erwerb, unbestimmt` plus `gemischt`, `ungeprueft`; Vorschläge der Automatik zählen mit; Anteil handgeprüft wird berechnet, nie geschätzt.
- Farben Stellung: `arbeiter #e69f00, angestellte #56b4e9, beamte #009e73, selbstaendige #f0e442, freie_berufe #0072b2, unternehmer #d55e00, ohne_erwerb #cc79a7, kaufleute #4b5563, unbestimmt #9ca3af, gemischt #a16207`, `sonst #c8c8c8`.
- Ungleich-Satz in der Vergleichsleiste, wenn größte Gruppe > 10 × kleinste Gruppe (nur Gruppen mit > 0 Häusern).
- Legende rechts unten ohne Kästchen, ohne Gruppen, ohne Themensätze.
- Commits auf Deutsch, Abschluss `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; kein Push; `PLAN_FREIGEGEBEN` bleibt `false`.
- Testbefehle: `node --test site/tests/*.test.js` und `python3 -m pytest -q`. Datenpaket: `python3 pipeline/06_karte_export.py` (≈ 1 min plus tippecanoe).

## Review Focus

1. Alter Link `?eigentuemer=Fried.+Krupp+AG|Stadt+Essen&ohdab=B+21112-100`: erwartet `vergleich = ["eig:Fried. Krupp AG", "eig:Stadt Essen", "norm:B 21112-100"]`, geschriebene URL nur mit `vergleich=` — Test in Task 4.
2. Schlüssel `norm:X`, der im Normindex fehlt (alter Link nach Kuratierungsänderung): erwartet Gruppe mit Name `X` und null Häusern, andere Gruppen normal — Test in Task 5.
3. Haus mit zwei Bewohnern verschiedener Stellung (1:1) und einem ungeprüften: erwartet `stellung = gemischt`; Haus nur mit ungeprüften: `ungeprueft`; Vorschlag zählt wie Hand — Test in Task 1.
4. Oberkategorie ohne Einträge in der Liste (z. B. `gemischt`, oder eine Stellung, deren Normen alle 0 Häuser haben): erwartet Zeile mit Kästchen und Zahl, ohne Pfeil, kein Fehler — Test in Task 7.
5. Bergbau: Norm, deren Bezeichnungen in zwei Gruppen liegen („Berginvalide“ → Bergmann): erwartet genau eine Gruppe (die mit den meisten Nennungen), der Schlüssel erscheint nur einmal — Test in Task 2.

---

### Task 1: Hausfeld `stellung` in der Pipeline

**Files:**
- Modify: `pipeline/lib/karte_export.py` (nach `_niveau`, Z. 258–273; `gruppiere` Z. 246; `punkt_feature` Z. 276–294)
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Produces: `_stellung(eintraege: list[dict]) -> tuple[str, dict[str, int]]`; Adressfelder `a["stellung"]`, `a["n_stellung"]`; Punktfeld `properties["stellung"]`.

- [ ] **Step 1: Write the failing test** (ans Ende von `tests/test_karte_export.py`)

```python
def test_stellung_je_adresse_mehrheit_gemischt_ungeprueft():
    """Spec Themenbaum §4: Mehrheitsstellung der geprüften Bewohner; Vorschlag zählt wie Hand; 1:1 → gemischt; nichts geprüft → ungeprueft."""
    from pipeline.lib.karte_export import _stellung, punkt_feature
    def b(st, q="hand"):
        return dict(teil="I", _beruf=dict(stellung=st, stellung_quelle=q, niveau="fachlich"), _merkmale=[])
    ohne = dict(teil="I", _beruf=None, _merkmale=[])
    assert _stellung([b("arbeiter"), b("arbeiter", "vorschlag"), b("beamte"), ohne]) == ("arbeiter", {"arbeiter": 2, "beamte": 1})
    assert _stellung([b("arbeiter"), b("beamte"), ohne]) == ("gemischt", {"arbeiter": 1, "beamte": 1})
    assert _stellung([ohne, dict(teil="II", _beruf=dict(stellung="arbeiter", stellung_quelle="hand"), _merkmale=[])]) == ("ungeprueft", {})
    a = dict(id="x", lat=51.4, lon=7.0, stufe="haus", stadtteil="Kray", strasse_heute="A", hausnr="1", hausnr_zusatz="", historisch="A 1",
             nummer_unsicher="nein", eintraege=[b("arbeiter"), b("arbeiter", "vorschlag"), b("beamte")], besitz="ungeprueft", niveau="fachlich")
    a["stellung"], a["n_stellung"] = _stellung(a["eintraege"])
    assert punkt_feature(a)["properties"]["stellung"] == "arbeiter"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_karte_export.py -k stellung_je_adresse`
Expected: FAIL with `ImportError: cannot import name '_stellung'`

- [ ] **Step 3: Write minimal implementation**

In `karte_export.py` nach `_niveau`:

```python
def _stellung(eintraege: list[dict]) -> tuple[str, dict[str, int]]:
    """Punktattribut je Adresse (Spec Themenbaum §4): nur Teil I mit geprüftem Beruf; Vorschläge der Automatik
    zählen wie Handentscheidungen; eine Klasse mit mehr als der Hälfte → Klasse; sonst gemischt; nichts
    geprüft → ungeprueft."""
    n: dict[str, int] = defaultdict(int)
    for e in eintraege:
        if e.get("teil") == "I" and e.get("_beruf"):
            n[e["_beruf"].get("stellung") or UNBESTIMMT] += 1
    gesamt = sum(n.values())
    if not gesamt:
        return "ungeprueft", {}
    beste, anzahl = max(n.items(), key=lambda x: x[1])
    return (beste if anzahl * 2 > gesamt else "gemischt"), dict(n)
```

Import ergänzen: `from pipeline.lib.stellung import STELLUNGEN, UNBESTIMMT`. In `gruppiere` nach `a["niveau"], a["n_niveau"] = _niveau(a["eintraege"])`: `a["stellung"], a["n_stellung"] = _stellung(a["eintraege"])`. In `punkt_feature` in `p = dict(...)`: `stellung=a.get("stellung", "ungeprueft"),` hinter `niveau=…`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_karte_export.py -k stellung_je_adresse`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/karte_export.py tests/test_karte_export.py
git commit -m "feat(pipeline): Hausfeld stellung — Mehrheitsstellung der geprüften Bewohner, Vorschläge zählen mit, 1:1 gemischt (Themenbaum §4)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Themenlisten-Export (`themen/<id>_liste.json`)

**Files:**
- Modify: `pipeline/lib/karte_export.py` (neue Funktionen nach `baue_eigentuemerindex`, Z. ~475; `schreibe_paket` nach dem Eigentümerindex, Z. ~1025)
- Modify: `README.md` Dateiliste (nach `themen/<id>.pmtiles`)
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Consumes: `baue_eigentuemerindex(adressen)` → `(liste [[schluessel, name, haeuser, kategorie]], scherben)`; Adressfelder `besitz`, `stellung`, Einträge `_beruf` mit `ohdab`, `norm`, `stellung`, `stellung_quelle`, `bergbau`; `zaehlfelder(a)`.
- Produces: `baue_themen_listen(adressen) -> dict[str, dict]` mit Schlüsseln `besitz`, `bergbau`, `berufe`; Dateiformat `{"oberkategorien": [{"id", "name", "adressen", "eintraege": [{"schluessel", "name", "adressen"}]}], "gemischt": int, "ungeprueft": int, "handgeprueft_anteil": float|None}`. Einträge je Oberkategorie nach `adressen` absteigend, dann Name; Oberkategorien in fester Reihenfolge (`OBERKATEGORIEN`).

- [ ] **Step 1: Write the failing test**

```python
def test_themen_listen_besitz_bergbau_berufe():
    """Spec Themenbaum §6: je Thema Oberkategorie → Einträge (Schlüssel, Name, Häuser); ein OhdAB-Schlüssel steht in genau einer
    Bergbau-Gruppe (die mit den meisten Nennungen) und bei genau einer Stellung; Anteil handgeprüft nach Nennungen."""
    from pipeline.lib.karte_export import baue_themen_listen
    def haus(i, eintraege, **f):
        a = dict(id=f"h{i}", lat=51.4, lon=7.0, stufe="haus", stadtteil="Kray", strasse_heute="A", hausnr=str(i), hausnr_zusatz="", historisch=f"A {i}",
                 nummer_unsicher="nein", eintraege=eintraege, besitz="ungeprueft", besitz_quelle="", besitz_eigentuemer="", stellung="ungeprueft")
        a.update(f)
        return a
    def p(ohdab, norm, st, q="hand", bb=None):
        b = dict(ohdab=ohdab, norm=norm, stellung=st, stellung_quelle=q, niveau="fachlich")
        if bb:
            b["bergbau"] = bb
        return dict(teil="I", _beruf=b, _merkmale=[], _eigentuemer="", _identitaet=False, _kategorie="")
    def eig(name, kat):
        return dict(teil="II", _beruf=None, _merkmale=[], _eigentuemer=name, _identitaet=True, _kategorie=kat)
    adressen = {a["id"]: a for a in [
        haus(1, [p("B1", "Bergmann", "arbeiter", bb="belegschaft"), p("B1", "Bergmann", "arbeiter", "vorschlag", bb="invaliden"), eig("Krupp", "industrie")], besitz="industrie", besitz_quelle="eintrag", stellung="arbeiter"),
        haus(2, [p("B1", "Bergmann", "arbeiter", bb="belegschaft"), p("S1", "Steiger", "angestellte", bb="aufsicht")], stellung="gemischt"),
        haus(3, [p("S1", "Steiger", "angestellte", bb="aufsicht"), eig("Stadt Essen", "stadt_staat")], besitz="stadt_staat", besitz_quelle="eintrag", stellung="angestellte"),
        haus(4, [dict(teil="I", _beruf=None, _merkmale=[], _eigentuemer="", _identitaet=False, _kategorie="")], besitz="industrie", besitz_quelle="spanne", besitz_eigentuemer="Krupp"),
    ]}
    L = baue_themen_listen(adressen)
    bs = {o["id"]: o for o in L["besitz"]["oberkategorien"]}
    assert bs["industrie"]["adressen"] == 2 and bs["industrie"]["eintraege"] == [dict(schluessel="eig:Krupp", name="Krupp", adressen=2)]
    assert bs["stadt_staat"]["eintraege"] == [dict(schluessel="eig:Stadt Essen", name="Stadt Essen", adressen=1)]
    assert bs["privatperson"]["adressen"] == 0 and bs["privatperson"]["eintraege"] == []
    assert L["besitz"]["ungeprueft"] == 1 and L["besitz"]["handgeprueft_anteil"] is None
    bb = {o["id"]: o for o in L["bergbau"]["oberkategorien"]}
    assert [o["id"] for o in L["bergbau"]["oberkategorien"]] == ["leitung", "aufsicht", "belegschaft", "invaliden"]
    assert bb["belegschaft"]["adressen"] == 2 and bb["belegschaft"]["eintraege"] == [dict(schluessel="norm:B1", name="Bergmann", adressen=2)]
    assert bb["invaliden"]["adressen"] == 1 and bb["invaliden"]["eintraege"] == []          # Bergmann steht nur einmal: 2 Nennungen Belegschaft, 1 Invaliden
    assert bb["aufsicht"]["eintraege"] == [dict(schluessel="norm:S1", name="Steiger", adressen=2)]
    st = {o["id"]: o for o in L["berufe"]["oberkategorien"]}
    assert [o["id"] for o in L["berufe"]["oberkategorien"]][:3] == ["arbeiter", "angestellte", "beamte"]
    assert st["arbeiter"]["adressen"] == 2 and st["arbeiter"]["eintraege"][0]["schluessel"] == "norm:B1"
    assert st["angestellte"]["eintraege"] == [dict(schluessel="norm:S1", name="Steiger", adressen=2)]
    assert L["berufe"]["gemischt"] == 1 and L["berufe"]["ungeprueft"] == 1
    assert L["berufe"]["handgeprueft_anteil"] == 0.8      # 4 von 5 Nennungen mit geprüftem Beruf sind handgeprüft
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_karte_export.py -k themen_listen`
Expected: FAIL with `ImportError: cannot import name 'baue_themen_listen'`

- [ ] **Step 3: Write minimal implementation**

Nach `baue_eigentuemerindex` in `karte_export.py`:

```python
from pipeline.lib.bergbau import NAMEN as BB_NAMEN, RANG as BB_RANG      # oben bei den Importen ergänzen
from pipeline.lib.eigentuemer import KATEGORIEN as BESITZ_KATEGORIEN     # dito

# Oberkategorien je Thema mit Baum (Spec Themenbaum §6) in fester Reihenfolge; gemischt/ungeprueft stehen daneben.
OBERKATEGORIEN = {
    "besitz": [(k, BESITZ_KATEGORIEN[k]) for k in ("stadt_staat", "bergbau", "industrie", "genossenschaft_siedlung", "kirche_stiftung", "bank_versicherung", "privatperson", "sonstige")],
    "bergbau": [(k, BB_NAMEN[k]) for k in BB_RANG],
    "berufe": [(k, STELLUNGEN[k]) for k in ("arbeiter", "angestellte", "beamte", "selbstaendige", "freie_berufe", "unternehmer", "kaufleute", "ohne_erwerb", "unbestimmt")],
}


def _liste(thema: str, je_kat: dict[str, dict[str, dict]], adressen_je_kat: dict[str, int], gemischt: int, ungeprueft: int,
           handgeprueft_anteil: float | None) -> dict:
    """je_kat: Oberkategorie → Schlüssel → dict(name, adressen). Einträge nach Häusern absteigend, dann Name."""
    ober = []
    for k, name in OBERKATEGORIEN[thema]:
        eintraege = sorted(je_kat.get(k, {}).values(), key=lambda e: (-e["adressen"], e["name"]))
        ober.append(dict(id=k, name=name, adressen=adressen_je_kat.get(k, 0), eintraege=eintraege))
    return dict(oberkategorien=ober, gemischt=gemischt, ungeprueft=ungeprueft, handgeprueft_anteil=handgeprueft_anteil)


def _normen_je_kategorie(adressen: dict[str, dict], kategorie_von) -> dict[str, dict[str, dict]]:
    """OhdAB-Schlüssel → (Häuser, Name, Nennungen je Oberkategorie); jeder Schlüssel landet in der Oberkategorie mit
    den meisten Nennungen (Review Focus 5: „Berginvalide“-Bezeichnungen hängen an der Norm Bergmann). kategorie_von(b)
    liefert die Oberkategorie eines Berufsdatensatzes oder None (zählt dann nicht)."""
    haeuser: dict[str, set[str]] = defaultdict(set)
    nennungen: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    namen: dict[str, str] = {}
    for a in adressen.values():
        for e in a["eintraege"]:
            b = e.get("_beruf")
            if e.get("teil") != "I" or not b:
                continue
            k = kategorie_von(b)
            if not k:
                continue
            haeuser[b["ohdab"]].add(a["id"])
            nennungen[b["ohdab"]][k] += 1
            namen[b["ohdab"]] = b["norm"]
    je_kat: dict[str, dict[str, dict]] = defaultdict(dict)
    for o, je in nennungen.items():
        k = max(je.items(), key=lambda x: (x[1], x[0]))[0]
        je_kat[k][o] = dict(schluessel=f"norm:{o}", name=namen[o], adressen=len(haeuser[o]))
    return je_kat


def baue_themen_listen(adressen: dict[str, dict]) -> dict[str, dict]:
    """Klapplisten der Themen Besitz, Bergbau, Berufe (Spec Themenbaum §6): Oberkategorie → Einzelbezeichnungen mit
    Schlüssel (eig:<Name> | norm:<ohdab_id>), Name und Häuserzahl; Zahl je Oberkategorie = Häuser, die sie tragen."""
    aus: dict[str, dict] = {}
    # Besitz: Klasse je Adresse (inkl. Spannen), Eigentümer aus dem Eigentümerindex nach Kategorie
    liste, _ = baue_eigentuemerindex(adressen)
    je_kat: dict[str, dict[str, dict]] = defaultdict(dict)
    for _, name, haeuser, kat in liste:
        je_kat[kat][f"eig:{name}"] = dict(schluessel=f"eig:{name}", name=name, adressen=haeuser)
    je_klasse: dict[str, int] = defaultdict(int)
    for a in adressen.values():
        je_klasse[a.get("besitz", "ungeprueft")] += 1
    aus["besitz"] = _liste("besitz", je_kat, je_klasse, je_klasse.get("gemischt", 0), je_klasse.get("ungeprueft", 0), None)
    # Bergbau: Häuser je Gruppe = n_bb_<g> > 0; Normen je Gruppe nach den meisten Nennungen
    je_gruppe: dict[str, int] = defaultdict(int)
    for a in adressen.values():
        z = zaehlfelder(a)
        for g in BB_RANG:
            if z.get(f"n_bb_{g}", 0) > 0:
                je_gruppe[g] += 1
    aus["bergbau"] = _liste("bergbau", _normen_je_kategorie(adressen, lambda b: b.get("bergbau")), je_gruppe, 0, 0, None)
    # Berufe: Häuser je Stellung = mindestens ein geprüfter Bewohner dieser Stellung; Anteil handgeprüft nach Nennungen
    je_st: dict[str, int] = defaultdict(int)
    hand = geprueft = 0
    for a in adressen.values():
        klassen = set()
        for e in a["eintraege"]:
            b = e.get("_beruf")
            if e.get("teil") == "I" and b:
                klassen.add(b.get("stellung") or UNBESTIMMT)
                geprueft += 1
                hand += b.get("stellung_quelle") == "hand"
        for k in klassen:
            je_st[k] += 1
    gemischt = sum(1 for a in adressen.values() if a.get("stellung") == "gemischt")
    ungeprueft = sum(1 for a in adressen.values() if a.get("stellung", "ungeprueft") == "ungeprueft")
    anteil = round(hand / geprueft, 3) if geprueft else None
    aus["berufe"] = _liste("berufe", _normen_je_kategorie(adressen, lambda b: b.get("stellung") or UNBESTIMMT), je_st, gemischt, ungeprueft, anteil)
    return aus
```

In `schreibe_paket` nach der Eigentümerindex-Schleife:

```python
    for name, inhalt in baue_themen_listen(adressen).items():
        _json(ausgabe / "themen" / f"{name}_liste.json", inhalt)
```

README-Dateiliste ergänzen: `themen/<id>_liste.json` — Klappliste des Themenbaums (Oberkategorie → Einzelbezeichnungen mit Schlüssel `eig:`/`norm:` und Häuserzahl; `handgeprueft_anteil` nur bei Berufen).

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_karte_export.py -k themen_listen`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/karte_export.py tests/test_karte_export.py README.md
git commit -m "feat(pipeline): Themenlisten themen/<id>_liste.json — Oberkategorie → Einzelbezeichnungen mit Schlüssel eig:/norm: und Häuserzahl; Bergbau-Norm in genau einer Gruppe; Anteil handgeprüft (Themenbaum §6)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Thema Berufe auf Stellung, `baum: true`, Datenpaket

**Files:**
- Modify: `kuratierung/themen/berufe.json`, `kuratierung/themen/besitz.json`, `kuratierung/themen/bergbau.json`
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Produces: Themen-JSON mit `baum: true`; Berufe `farbe.feld = "stellung"`, `schalter.feld = "stellung"`, elf Klassen; `zusatz.eigentuemerliste` entfällt.

- [ ] **Step 1: Write the failing test**

```python
def test_themen_definitionen_tragen_baum_und_berufe_faerben_nach_stellung():
    """Spec Themenbaum §4/§6: Berufe färben nach Stellung (neun Klassen + gemischt + ungeprueft); drei Themen mit Baum."""
    themen = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in Path("kuratierung/themen").glob("*.json")}
    b = themen["berufe"]
    assert b["farbe"]["feld"] == "stellung" and b["schalter"]["feld"] == "stellung"
    assert b["schalter"]["klassen"] == ["arbeiter", "angestellte", "beamte", "selbstaendige", "freie_berufe", "unternehmer", "kaufleute", "ohne_erwerb", "unbestimmt", "gemischt", "ungeprueft"]
    assert set(b["farbe"]["werte"]) == set(b["schalter"]["klassen"]) - {"ungeprueft"}
    assert b["farbe"]["werte"]["kaufleute"] == "#4b5563" and b["farbe"]["sonst"] == "#c8c8c8"
    assert all(themen[t].get("baum") is True for t in ("besitz", "bergbau", "berufe"))
    assert "eigentuemerliste" not in themen["besitz"].get("zusatz", {})
    assert all("Kästchen" not in themen[t]["text"] for t in ("besitz", "bergbau", "berufe"))
```

(`json` und `Path` sind in der Testdatei bereits importiert; sonst `import json` / `from pathlib import Path` ergänzen.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_karte_export.py -k themen_definitionen`
Expected: FAIL with `AssertionError` (`feld == "niveau"`)

- [ ] **Step 3: Write the theme definitions**

`kuratierung/themen/berufe.json`:

```json
{
  "id": "berufe",
  "titel": "Berufe",
  "text": "Häuser nach der sozialen Stellung ihrer Bewohner (Teil I), abgeleitet aus dem Beruf: Mehrheit der geprüften Bewohner je Haus, bei Gleichstand „gemischt“, ohne geprüften Beruf grau. Stellung nach Rechtslage der Zeit; Vorschläge der Automatik zählen mit und sind in Hausansicht und Popup gekennzeichnet. „Kaufleute“ ohne Zusatz bleiben eigene Klasse: Angestellter oder Selbständiger ist aus der Bezeichnung nicht zu entscheiden.",
  "grundlage": "Berufs-Kuratierung kuratierung/berufe.csv (Abkürzungskatalog + Handprüfung) gegen die OhdAB (Moeller/Uni Halle, FactGrid, CC BY 4.0), Stellung je Schreibweise nach Berufszählung 1933 und Angestelltenversicherungsgesetz 1911 (docs/stellung.md), Stand 2026-09-24",
  "freigegeben": true,
  "baum": true,
  "filter": { "ebenen": ["I"] },
  "farbe": {
    "art": "kategorien",
    "feld": "stellung",
    "werte": {
      "arbeiter": "#e69f00", "angestellte": "#56b4e9", "beamte": "#009e73", "selbstaendige": "#f0e442",
      "freie_berufe": "#0072b2", "unternehmer": "#d55e00", "kaufleute": "#4b5563", "ohne_erwerb": "#cc79a7",
      "unbestimmt": "#9ca3af", "gemischt": "#a16207"
    },
    "sonst": "#c8c8c8"
  },
  "legende": "Farbe = Mehrheitsstellung der geprüften Bewohner",
  "darstellung": "punkte",
  "schalter": {
    "feld": "stellung",
    "klassen": ["arbeiter", "angestellte", "beamte", "selbstaendige", "freie_berufe", "unternehmer", "kaufleute", "ohne_erwerb", "unbestimmt", "gemischt", "ungeprueft"]
  }
}
```

`besitz.json`: `"baum": true` nach `"freigegeben"`; `zusatz` wird `{ "zechen": true }`; `text` ohne den letzten Satz („Die Kästchen …“), stattdessen: „Die Kästchen schalten Kategorien ab und zu; der Pfeil öffnet die größten Eigentümer der Kategorie.“ — **nein**: der Satz über Kästchen entfällt ganz (Test prüft „Kästchen“ nicht im Text). Endtext: „Häuser nach Art des Eigentümers laut Teil II, einschließlich der Häuser aus Hausnummernspannen („2–84 E. …“), die im Adressbuch keine eigene Zeile haben. Farbig nur Adressen, deren Eigentümer von Hand geprüft wurde; alle anderen grau.“
`bergbau.json`: `"baum": true`; `text`: „Adressen mit Bergbau-Berufen laut Teil I, nach Gruppe: Belegschaft, Aufsicht, Leitung und Beamte, Berginvaliden. Bei mehreren Gruppen im Haus zählt die höchste.“

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_karte_export.py -k themen_definitionen`
Expected: PASS

- [ ] **Step 5: Run the full pytest suite and rebuild the data package**

Run: `python3 -m pytest -q` — Expected: alle grün (bisher 456 + 3 neue).
Run: `python3 pipeline/06_karte_export.py > /tmp/claude-1000/-home-christos-Projekte-essener-adressbuch-1936/b3aa79af-56cd-447b-949b-094a6606f536/scratchpad/export.log 2>&1; tail -3 …/export.log; ls -la site/daten/themen/`
Expected: `besitz_liste.json`, `bergbau_liste.json`, `berufe_liste.json` vorhanden; `berufe.pmtiles` neu. Dann: `python3 -c "import json; L=json.load(open('site/daten/themen/berufe_liste.json')); print(L['handgeprueft_anteil'], [(o['id'], o['adressen'], len(o['eintraege'])) for o in L['oberkategorien']])"` — Expected: Anteil zwischen 0 und 1, neun Oberkategorien, `arbeiter` mit den meisten Einträgen. Die Zahl aus `bergbau_liste.json` mit 38 Einträgen gesamt (Spec §1) gegenprüfen: `python3 -c "import json; L=json.load(open('site/daten/themen/bergbau_liste.json')); print(sum(len(o['eintraege']) for o in L['oberkategorien']))"` — Expected: 38 (Abweichung um wenige ist möglich, wenn Normen nur in Teil II vorkommen; dann Zahl in der Spec anpassen und im Ledger vermerken).

- [ ] **Step 6: Commit**

```bash
git add kuratierung/themen tests/test_karte_export.py
git commit -m "feat(themen): Berufe färben nach Stellung (neun Klassen, Vorschläge zählen mit); baum: true für Besitz, Bergbau, Berufe; Legendensatz aus den Thementexten

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Zustand `vergleich` mit Migration

**Files:**
- Modify: `site/js/zustand.js`
- Test: `site/tests/zustand.test.js`

**Interfaces:**
- Produces: `STANDARD.vergleich = []` (Felder `eigentuemer` und `ohdab` entfallen aus `STANDARD`), `export const MAX_VERGLEICH = 5`, `export function schluesselliste(wert) -> string[]`, `export function schluessel(s) -> {typ, wert}`; `liesZustand` migriert `eigentuemer=` und `ohdab=`; `schreibeZustand` schreibt `vergleich` mit `|`.

- [ ] **Step 1: Write the failing tests** (die zwei bestehenden Tests zu `eigentuemer` in `zustand.test.js` ersetzen)

```js
import { MAX_VERGLEICH, schluesselliste, schluessel } from "../js/zustand.js";

test("vergleich: typisierte Schlüssel, |-Liste, Dubletten, Kappung auf fünf, unbekannter Typ fällt weg", () => {
  assert.deepEqual(liesZustand("?vergleich=eig:Fried.+Krupp+AG").vergleich, ["eig:Fried. Krupp AG"]);
  assert.deepEqual(liesZustand("?vergleich=eig:Fried.+Krupp+AG|norm:B+21112-100").vergleich, ["eig:Fried. Krupp AG", "norm:B 21112-100"]);
  assert.deepEqual(liesZustand("?vergleich=eig:A|eig:A|eig:B|eig:C|eig:D|eig:E|eig:F").vergleich, ["eig:A", "eig:B", "eig:C", "eig:D", "eig:E"]);
  assert.deepEqual(liesZustand("?vergleich=rub:X|quatsch|eig:|+").vergleich, []);
  assert.equal(MAX_VERGLEICH, 5);
  assert.deepEqual(schluesselliste(["norm:B 1", " norm:B 1 ", "eig:x"]), ["norm:B 1", "eig:x"]);
  assert.deepEqual(schluesselliste(null), []);
  assert.deepEqual(schluessel("norm:B 21112-100"), { typ: "norm", wert: "B 21112-100" });
  assert.deepEqual(schluessel("eig:Fa. Müller: Söhne"), { typ: "eig", wert: "Fa. Müller: Söhne" });   // nur der erste Doppelpunkt trennt
});

test("alte URL-Parameter eigentuemer= und ohdab= werden zu vergleich migriert und nie mehr geschrieben (Review Focus 1)", () => {
  const z = liesZustand("?eigentuemer=Fried.+Krupp+AG|Stadt+Essen&ohdab=B+21112-100");
  assert.deepEqual(z.vergleich, ["eig:Fried. Krupp AG", "eig:Stadt Essen", "norm:B 21112-100"]);
  assert.equal(z.eigentuemer, undefined); assert.equal(z.ohdab, undefined);
  assert.equal(schreibeZustand(z), "vergleich=eig:Fried.+Krupp+AG|eig:Stadt+Essen|norm:B+21112-100");
  assert.deepEqual(liesZustand("?" + schreibeZustand(z)).vergleich, z.vergleich);
  // vergleich= hat Vorrang vor den alten Parametern
  assert.deepEqual(liesZustand("?vergleich=eig:A&eigentuemer=B").vergleich, ["eig:A"]);
  assert.equal(schreibeZustand(STANDARD), "");
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test site/tests/zustand.test.js`
Expected: FAIL — `MAX_VERGLEICH`/`schluesselliste` nicht exportiert (SyntaxError beim Import).

- [ ] **Step 3: Write minimal implementation** (`zustand.js`)

```js
export const STANDARD = Object.freeze({
  q: "", ebene: ["I", "II", "III"], stadtteil: "", praez: ["haus", "strasse", "stadtplan"], beruf: "", vergleich: [],
  thema: "", klassen: "", id: "", karte: "positron", plan: 0, zechen: 0, z: null, c: null,
  ansicht: "",
});
// … liste/zahl unverändert …

// Vergleich (Spec Themenbaum §3): höchstens fünf typisierte Schlüssel eig:<Name> | norm:<ohdab_id>, Trenner |.
export const MAX_VERGLEICH = 5;
const TYPEN = ["eig", "norm"];
export function schluessel(s) {
  const i = String(s).indexOf(":");
  return i < 0 ? { typ: "", wert: String(s) } : { typ: s.slice(0, i), wert: s.slice(i + 1) };
}
export function schluesselliste(wert) {
  if (!wert) return [];
  const aus = [];
  for (const t of Array.isArray(wert) ? wert : String(wert).split("|")) {
    const s = String(t).trim();
    const { typ, wert: w } = schluessel(s);
    if (TYPEN.includes(typ) && w.trim() && !aus.includes(s)) aus.push(s);
  }
  return aus.slice(0, MAX_VERGLEICH);
}
// Alte Links (eigentuemer=a|b, ohdab=id) werden gelesen, aber nicht mehr geschrieben.
function vergleichAus(p) {
  const neu = schluesselliste(p.get("vergleich"));
  if (neu.length) return neu;
  const alt = [...(p.get("eigentuemer") || "").split("|").filter((n) => n.trim()).map((n) => `eig:${n.trim()}`)];
  if (p.get("ohdab")) alt.push(`norm:${p.get("ohdab")}`);
  return schluesselliste(alt);
}
```

In `liesZustand`: `eigentuemer:`- und `ohdab:`-Zeilen streichen, `vergleich: vergleichAus(p),` einsetzen. In `schreibeZustand`: `w.join(k === "vergleich" ? "|" : ",")`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test site/tests/zustand.test.js`
Expected: PASS (alle Tests der Datei)

- [ ] **Step 5: Commit** (die Suite ist jetzt in `app.js`/`sidebar.js` gebrochen, weil `MAX_EIGENTUEMER`/`namensliste` fehlen — das ist Task 8; Node-Tests importieren `app.js` nicht, `node --test site/tests/*.test.js` bleibt grün.)

```bash
git add site/js/zustand.js site/tests/zustand.test.js
git commit -m "feat(zustand): vergleich mit typisierten Schlüsseln eig:/norm: (max. 5, Trenner |); eigentuemer= und ohdab= werden migriert (Themenbaum §3)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Suche: Art `vergleich`

**Files:**
- Modify: `site/js/suche.js` (Z. 60–95, `treffer`)
- Test: `site/tests/suche.test.js`

**Interfaces:**
- Consumes: `schluessel(s)` aus `zustand.js`; `lader.eigentuemerScherbe`, `lader.berufeNorm()`, `lader.berufeNormScherbe`.
- Produces: `treffer({ art: "vergleich", schluessel: string[] }, lader)` → `gruppen: [{ schluessel, name, farbe, adressIds, zaehler }]`; die Arten `eigentuemer` und `ohdab` in `treffer()` entfallen (Vorschlagsarten in `vorschlaege()` bleiben).

- [ ] **Step 1: Write the failing tests** (in `suche.test.js` die drei Tests „treffer mit mehreren Eigentümern“, „alte Auswahlform {name}“ und „Treffer für ohdab“ ersetzen; den Eigentümer-Vorschlagstest auf `treffer({ art: "vergleich", schluessel: ["eig:Fried. Krupp AG"] })` umstellen)

```js
test("treffer vergleich: Gruppen je Schlüssel in Reihenfolge mit Farbe; eig: über die Eigentümerscherbe, norm: über Normindex + Normscherbe", async () => {
  const geladen = []; const l = new Lader("daten/", async (u) => { geladen.push(u); return fetchFake(u); });
  const t = await treffer({ art: "vergleich", schluessel: ["eig:Fried. Krupp AG", "norm:B 21112-100", "eig:Stadt Essen"] }, l);
  assert.deepEqual(t.gruppen.map((g) => [g.schluessel, g.name, g.farbe, g.adressIds]), [
    ["eig:Fried. Krupp AG", "Fried. Krupp AG", "#dc2626", ["a1", "b2"]],
    ["norm:B 21112-100", "Bergmann", "#2563eb", ["a1", "b2"]],
    ["eig:Stadt Essen", "Stadt Essen", "#16a34a", ["b2", "c3"]]]);
  assert.deepEqual(t.adressIds, ["a1", "b2", "c3"]);
  assert.equal(t.zaehler.get("b2"), 4);                    // 2 Krupp + 1 Bergmann + 1 Stadt
  assert.equal(t.gruppen[1].zaehler.get("a1"), 2);
  assert.equal(geladen.filter((u) => u.includes("berufe_norm/")).length, 1);
});

test("treffer vergleich: unbekannte Norm → Gruppe mit Schlüssel als Name und null Häusern; andere Gruppen normal (Review Focus 2)", async () => {
  const t = await treffer({ art: "vergleich", schluessel: ["norm:X 999", "eig:Stadt Essen"] }, lader());
  assert.deepEqual(t.gruppen.map((g) => [g.name, g.adressIds]), [["X 999", []], ["Stadt Essen", ["b2", "c3"]]]);
  assert.equal((await treffer({ art: "beruf", beruf: "Bergm." }, lader())).gruppen, null);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test site/tests/suche.test.js`
Expected: FAIL — `t.gruppen` ist `null` (Art unbekannt).

- [ ] **Step 3: Write minimal implementation** (`suche.js`: die Zweige `eigentuemer` und `ohdab` durch diesen ersetzen; `import { schluessel } from "./zustand.js";` ergänzen)

```js
  } else if (auswahl.art === "vergleich") {
    // Vergleich (Spec Themenbaum §3): je Schlüssel eine Gruppe mit Farbe nach Platz; die Gesamtmenge ist die Vereinigung.
    gruppen = [];
    let normen = null;
    for (const [i, s] of (auswahl.schluessel || []).entries()) {
      const { typ, wert } = schluessel(s);
      let name = wert, z = new Map();
      if (typ === "eig") {
        const sch = await lader.eigentuemerScherbe(praefix2(wert));
        z = new Map((sch && sch[wert]) || []);
      } else if (typ === "norm") {
        normen = normen || (await lader.berufeNorm()) || [];
        const eintrag = normen.find((n) => n[2] === wert);
        if (eintrag) {
          name = eintrag[1];
          const sch = await lader.berufeNormScherbe(praefix2(name));
          z = new Map((sch && sch[wert]) || []);
        }
      }
      for (const [a, n] of z) zaehler.set(a, (zaehler.get(a) || 0) + n);
      gruppen.push({ schluessel: s, name, farbe: FARBEN.gruppen[i % FARBEN.gruppen.length], adressIds: [...z.keys()], zaehler: z });
    }
  }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test site/tests/suche.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add site/js/suche.js site/tests/suche.test.js
git commit -m "feat(suche): Art vergleich — Gruppen je Schlüssel (eig: Eigentümerscherbe, norm: Normindex + Normscherbe), unbekannte Norm leer statt Fehler

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Vergleichsleiste mit Grundgesamtheit und Ungleich-Satz

**Files:**
- Modify: `site/js/vergleich.js` (`vergleichsleisteHtml`)
- Test: `site/tests/vergleich.test.js`

**Interfaces:**
- Consumes: Gruppen mit `schluessel` (Task 5).
- Produces: `vergleichsleisteHtml(gruppen, eig)` mit `data-weg="<schluessel>"`, `export function grundgesamtheitSaetze(gruppen) -> string[]`, `export function ungleichSatz(gruppen) -> string|null`.

- [ ] **Step 1: Write the failing tests** (Fixture `G` um `schluessel` ergänzen: `"eig:Krupp"`, `"eig:Stadt"`, `"eig:Stinnes"`; im bestehenden Leisten-Test `data-eig-weg="Krupp"` → `data-weg="eig:Krupp"`)

```js
import { grundgesamtheitSaetze, ungleichSatz } from "../js/vergleich.js";

test("grundgesamtheitSaetze: je vorhandenem Typ ein Satz; norm nennt Teil I und die Lücke H–J", () => {
  assert.deepEqual(grundgesamtheitSaetze(G), ["Eigentümer: auch Häuser aus Sammelzeilen des Adressbuchs („2–84 E. …“)."]);
  const n = [{ schluessel: "norm:B 1", name: "Bergmann", farbe: "#000", adressIds: ["a"], zaehler: new Map([["a", 1]]) }];
  assert.deepEqual(grundgesamtheitSaetze(n), ["Berufe: Einträge des Einwohnerverzeichnisses mit geprüftem Beruf; die Namen H bis J fehlen in der Vorlage."]);
  assert.equal(grundgesamtheitSaetze([...n, G[0]]).length, 2);
});

test("ungleichSatz: nur wenn größte > 10 × kleinste Gruppe (Gruppen mit 0 Häusern zählen nicht)", () => {
  const g = (n, name) => ({ schluessel: `norm:${name}`, name, farbe: "#000", adressIds: Array.from({ length: n }, (_, i) => `${name}${i}`), zaehler: new Map() });
  assert.equal(ungleichSatz([g(100, "A"), g(20, "B")]), null);
  assert.equal(ungleichSatz([g(1200, "A"), g(100, "B"), g(0, "C")]), "Die Gruppen sind sehr ungleich groß (1.200 gegen 100 Häuser); Punkte zeigen Vorkommen, keine Anteile.");
  assert.equal(ungleichSatz([g(5, "A")]), null);
  assert.match(vergleichsleisteHtml([g(1200, "A"), g(100, "B")], new Map()), /class="zeile klein">Die Gruppen sind sehr ungleich/);
  assert.match(vergleichsleisteHtml(G, EIG), /Sammelzeilen des Adressbuchs/);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test site/tests/vergleich.test.js`
Expected: FAIL — Exporte fehlen.

- [ ] **Step 3: Write minimal implementation**

```js
import { schluessel } from "./zustand.js";

const GRUNDGESAMTHEIT = {
  norm: "Berufe: Einträge des Einwohnerverzeichnisses mit geprüftem Beruf; die Namen H bis J fehlen in der Vorlage.",
  eig: "Eigentümer: auch Häuser aus Sammelzeilen des Adressbuchs („2–84 E. …“).",
};
export function grundgesamtheitSaetze(gruppen) {
  const typen = [...new Set(gruppen.map((g) => schluessel(g.schluessel || "").typ))];
  return ["norm", "eig"].filter((t) => typen.includes(t)).map((t) => GRUNDGESAMTHEIT[t]);
}
const zahl = (n) => n.toLocaleString("de-DE");
export function ungleichSatz(gruppen) {
  const n = gruppen.map((g) => g.adressIds.length).filter((x) => x > 0);
  if (n.length < 2) return null;
  const max = Math.max(...n), min = Math.min(...n);
  if (max <= 10 * min) return null;
  return `Die Gruppen sind sehr ungleich groß (${zahl(max)} gegen ${zahl(min)} Häuser); Punkte zeigen Vorkommen, keine Anteile.`;
}
```

In `vergleichsleisteHtml`: Entfernen-Knopf `data-weg="${esc(g.schluessel)}"`, bei `norm:` ein `title` mit dem Schlüssel am Namen (`<b title="${esc(g.schluessel)}">`); nach `ring`: `grundgesamtheitSaetze(gruppen).map((s) => `<div class="zeile klein">${esc(s)}</div>`).join("")` und `const u = ungleichSatz(gruppen); if (u) … <div class="zeile klein">${esc(u)}</div>`. Ring-Text: „mit mehreren gewählten Gruppen (Ring)“.

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test site/tests/vergleich.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add site/js/vergleich.js site/tests/vergleich.test.js
git commit -m "feat(vergleich): Leiste nennt Grundgesamtheit je Schlüsseltyp und warnt bei Gruppen über Faktor 10; Entfernen über Schlüssel

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Modul `themenbaum.js` (DOM-frei)

**Files:**
- Create: `site/js/themenbaum.js`
- Modify: `site/js/kategorien.js` (`STELLUNGEN`, `anzeigeFuer("stellung")`)
- Test: `site/tests/themenbaum.test.js`, `site/tests/kategorien.test.js`

**Interfaces:**
- Consumes: `schalterKlassen(thema, klassen)` aus `themen.js`; `anzeigeFuer(feld)`; Liste aus Task 2.
- Produces: `baumHtml(thema, liste, { klassen, vergleich, farben, offen, alle })` → HTML-String. Marker: Kästchen `input[data-klasse="<id>"]`, Pfeil `button[data-auf="<id>"]` (nur mit Einträgen), Pill `button.pill-s[data-schluessel="<s>"][aria-pressed]`, „alle n anzeigen“ `button[data-alle="<id>"]`; Kopf `kopfHtml(thema)` mit `button[data-thema-aus]`; `grundlageHtml(thema)`. `PILLS_KURZ = 15`.

- [ ] **Step 1: Write the failing tests**

`site/tests/kategorien.test.js` ergänzen:

```js
import { STELLUNGEN } from "../js/kategorien.js";
test("STELLUNGEN: neun Klassen plus gemischt/ungeprüft, anzeigeFuer('stellung')", () => {
  assert.equal(STELLUNGEN.kaufleute, "Kaufleute (Stellung unbestimmt)");
  assert.equal(STELLUNGEN.gemischt, "mehrere Stellungen"); assert.equal(STELLUNGEN.ungeprueft, "ungeprüft");
  assert.equal(anzeigeFuer("stellung"), STELLUNGEN);
});
```

`site/tests/themenbaum.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { baumHtml, kopfHtml, grundlageHtml, PILLS_KURZ } from "../js/themenbaum.js";

const T = { id: "besitz", titel: "Besitz", text: "Häuser nach Art des Eigentümers.", grundlage: "eigentuemer.csv",
  farbe: { art: "kategorien", feld: "besitz", werte: { bergbau: "#111827", privatperson: "#d97706", gemischt: "#9a3412" }, sonst: "#c8c8c8" },
  schalter: { feld: "besitz", klassen: ["bergbau", "privatperson", "gemischt", "ungeprueft"] } };
const eintraege = (n, p) => Array.from({ length: n }, (_, i) => ({ schluessel: `eig:${p}${i}`, name: `${p}${i}`, adressen: 100 - i }));
const L = { oberkategorien: [
    { id: "bergbau", name: "Bergbau", adressen: 2, eintraege: eintraege(2, "Zeche ") },
    { id: "privatperson", name: "Privatperson", adressen: 300, eintraege: eintraege(20, "P") }],
  gemischt: 4, ungeprueft: 9, handgeprueft_anteil: null };
const opt = { klassen: "", vergleich: [], farben: ["#dc2626", "#2563eb"], offen: null, alle: null };

test("baumHtml: eine Zeile je Schalterklasse mit Kästchen, Farbpunkt, Name, Zahl; Pfeil nur mit Einträgen (Review Focus 4)", () => {
  const h = baumHtml(T, L, opt);
  assert.match(h, /<input type="checkbox" data-klasse="bergbau" checked><span class="punkt" style="background:#111827"><\/span> Bergbau <small>2<\/small>/);
  assert.match(h, /data-auf="bergbau"/); assert.match(h, /data-auf="privatperson"/);
  assert.doesNotMatch(h, /data-auf="gemischt"/); assert.doesNotMatch(h, /data-auf="ungeprueft"/);
  assert.match(h, /data-klasse="gemischt" checked>.*mehrere Kategorien <small>4<\/small>/);
  assert.match(h, /data-klasse="ungeprueft" checked>.*ungeprüft <small>9<\/small>/);
  assert.doesNotMatch(h, /pill-s/);                                  // nichts offen → keine Pills
});

test("baumHtml: Kästchen folgen klassen=; offene Kategorie zeigt 15 Pills mit Zahl und „alle n anzeigen“; alle=id zeigt alle", () => {
  const h = baumHtml(T, L, { ...opt, klassen: "privatperson", offen: "privatperson" });
  assert.match(h, /data-klasse="bergbau">/); assert.match(h, /data-klasse="privatperson" checked>/);
  assert.equal((h.match(/class="pill-s"/g) || []).length, PILLS_KURZ);
  assert.match(h, /<button class="pill-s" data-schluessel="eig:P0" aria-pressed="false">P0 <small>100<\/small><\/button>/);
  assert.match(h, /<button class="alle" data-alle="privatperson">alle 20 anzeigen<\/button>/);
  assert.match(h, /<button class="auf" data-auf="privatperson" aria-expanded="true">/);
  const v = baumHtml(T, L, { ...opt, offen: "privatperson", alle: "privatperson" });
  assert.equal((v.match(/class="pill-s/g) || []).length, 20); assert.doesNotMatch(v, /data-alle=/);
  assert.equal((baumHtml(T, L, { ...opt, offen: "bergbau" }).match(/class="pill-s/g) || []).length, 2);
});

test("baumHtml: gewählte Schlüssel sind gefüllt in ihrer Platzfarbe, Tooltip je Zustand", () => {
  const h = baumHtml(T, L, { ...opt, offen: "bergbau", vergleich: ["eig:X", "eig:Zeche 1"] });
  assert.match(h, /data-schluessel="eig:Zeche 1" aria-pressed="true" style="background:#2563eb;border-color:#2563eb;color:#fff" title="aus dem Vergleich entfernen"/);
  assert.match(h, /data-schluessel="eig:Zeche 0" aria-pressed="false" title="zum Vergleich hinzufügen"/);
  assert.match(baumHtml(T, L, { ...opt, offen: "bergbau" }), /data-schluessel="eig:Zeche 0" aria-pressed="false" title="alle Häuser: Zeche 0"/);
});

test("baumHtml ohne Liste (altes Datenpaket): Zeilen ohne Zahl und ohne Pfeil; Bergbau nimmt schalter.namen", () => {
  const h = baumHtml(T, null, opt);
  assert.match(h, /data-klasse="bergbau" checked>.*Bergbau<\/label>/); assert.doesNotMatch(h, /data-auf=/);
  const BB = { id: "bergbau", farbe: { art: "kategorien", feld: "bergbau", werte: { leitung: "#7c3aed" } }, schalter: { praefix: "n_bb_", klassen: ["leitung"], namen: { leitung: "Leitung und Beamte" } } };
  assert.match(baumHtml(BB, null, opt), /Leitung und Beamte/);
});

test("kopfHtml und grundlageHtml", () => {
  assert.equal(kopfHtml(T), `<div class="thema"><b>Besitz</b><p>Häuser nach Art des Eigentümers.</p><button data-thema-aus="1">Thema verlassen</button></div>`);
  assert.equal(grundlageHtml(T), `<small class="grundlage">eigentuemer.csv</small>`);
  assert.equal(grundlageHtml({ ...T, grundlage: "" }), "");
});

test("baumHtml Berufe: Anteil handgeprüft als Zeile unter dem Baum", () => {
  const B = { id: "berufe", farbe: { art: "kategorien", feld: "stellung", werte: { arbeiter: "#e69f00" } }, schalter: { feld: "stellung", klassen: ["arbeiter", "ungeprueft"] } };
  const h = baumHtml(B, { oberkategorien: [{ id: "arbeiter", name: "Arbeiter", adressen: 10, eintraege: [] }], gemischt: 0, ungeprueft: 1, handgeprueft_anteil: 0.437 }, opt);
  assert.match(h, /<div class="zeile klein">Stellung handgeprüft bei 44 % der Nennungen, sonst Vorschlag der Automatik.<\/div>/);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test site/tests/themenbaum.test.js site/tests/kategorien.test.js`
Expected: FAIL — Modul `themenbaum.js` fehlt; `STELLUNGEN` nicht exportiert.

- [ ] **Step 3: Write minimal implementation**

`kategorien.js` ergänzen:

```js
// Anzeigenamen der Stellung (Spec Themenbaum §4); Schlüssel wie pipeline/lib/stellung.py.
export const STELLUNGEN = {
  arbeiter: "Arbeiter", angestellte: "Angestellte", beamte: "Beamte", selbstaendige: "Selbständige (Handwerk, Handel, Gastgewerbe)",
  freie_berufe: "Freie Berufe und Akademiker", unternehmer: "Unternehmer und Leitende", kaufleute: "Kaufleute (Stellung unbestimmt)",
  ohne_erwerb: "Ohne Erwerbsberuf", unbestimmt: "unbestimmt", gemischt: "mehrere Stellungen", ungeprueft: "ungeprüft",
};
const ANZEIGE_JE_FELD = { besitz: KATEGORIEN, niveau: NIVEAUS, stellung: STELLUNGEN };
```

`site/js/themenbaum.js`:

```js
// Themenbaum in der Sidebar (Spec Themenbaum §2): Oberkategorien als Zeilen (Kästchen = Farbschalter, Pfeil = Klappliste),
// darunter Einzelbezeichnungen als Pills, die einen Vergleich starten. Reine HTML-Funktionen ohne DOM.
import { esc } from "./popup.js";
import { schalterKlassen } from "./themen.js";
import { anzeigeFuer } from "./kategorien.js";

export const PILLS_KURZ = 15;
const TOOLTIP = { gemischt: "mehrere Klassen im Haus, keine mit Mehrheit", ungeprueft: "kein geprüfter Wert für dieses Haus",
  unbestimmt: "Bezeichnung lässt die Stellung offen (z. B. „Friseur“ ohne Zusatz)", kaufleute: "„Kaufmann“ ohne Zusatz: Angestellter oder Selbständiger, aus der Bezeichnung nicht zu entscheiden" };

export function kopfHtml(thema) {
  return `<div class="thema"><b>${esc(thema.titel)}</b><p>${esc(thema.text)}</p><button data-thema-aus="1">Thema verlassen</button></div>`;
}
export function grundlageHtml(thema) { return thema.grundlage ? `<small class="grundlage">${esc(thema.grundlage)}</small>` : ""; }

function pill(e, vergleich, farben) {
  const i = vergleich.indexOf(e.schluessel);
  const stil = i >= 0 ? ` style="background:${esc(farben[i])};border-color:${esc(farben[i])};color:#fff"` : "";
  const titel = i >= 0 ? "aus dem Vergleich entfernen" : vergleich.length ? "zum Vergleich hinzufügen" : `alle Häuser: ${e.name}`;
  return `<button class="pill-s" data-schluessel="${esc(e.schluessel)}" aria-pressed="${i >= 0}"${stil} title="${esc(titel)}">${esc(e.name)} <small>${e.adressen}</small></button>`;
}

// opt: { klassen (URL-String), vergleich (Schlüssel), farben, offen (Oberkategorie-ID | null), alle (ID, deren Liste voll gezeigt wird | null) }
export function baumHtml(thema, liste, opt) {
  const an = new Set(schalterKlassen(thema, opt.klassen || ""));
  const namen = anzeigeFuer(thema.farbe?.feld);
  const werte = thema.farbe?.werte || {}, sonst = thema.farbe?.sonst || "#c8c8c8";
  const ober = new Map((liste?.oberkategorien || []).map((o) => [o.id, o]));
  let html = `<div class="baum">`;
  for (const k of thema.schalter?.klassen || []) {
    const o = ober.get(k);
    const zahl = o ? o.adressen : k === "gemischt" && liste ? liste.gemischt : k === "ungeprueft" && liste ? liste.ungeprueft : null;
    const name = thema.schalter?.namen?.[k] || namen[k] || k;
    const tip = TOOLTIP[k] ? ` title="${esc(TOOLTIP[k])}"` : "";
    const auf = o && o.eintraege.length;
    const offen = auf && opt.offen === k;
    html += `<div class="zeile ober"><label class="schalter"${tip}><input type="checkbox" data-klasse="${esc(k)}"${an.has(k) ? " checked" : ""}><span class="punkt" style="background:${esc(werte[k] || sonst)}"></span> ${esc(name)}${zahl == null ? "" : ` <small>${zahl}</small>`}</label>` +
      (auf ? `<button class="auf" data-auf="${esc(k)}" aria-expanded="${!!offen}" aria-label="${offen ? "zuklappen" : "aufklappen"}">${offen ? "▾" : "▸"}</button>` : "") + `</div>`;
    if (offen) {
      const voll = opt.alle === k;
      const teil = voll ? o.eintraege : o.eintraege.slice(0, PILLS_KURZ);
      html += `<div class="pills-s">${teil.map((e) => pill(e, opt.vergleich || [], opt.farben || [])).join("")}` +
        (voll || o.eintraege.length <= PILLS_KURZ ? "" : `<button class="alle" data-alle="${esc(k)}">alle ${o.eintraege.length} anzeigen</button>`) + `</div>`;
    }
  }
  if (liste && typeof liste.handgeprueft_anteil === "number") {
    html += `<div class="zeile klein">Stellung handgeprüft bei ${Math.round(liste.handgeprueft_anteil * 100)} % der Nennungen, sonst Vorschlag der Automatik.</div>`;
  }
  return html + `</div>`;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test site/tests/themenbaum.test.js site/tests/kategorien.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add site/js/themenbaum.js site/js/kategorien.js site/tests/themenbaum.test.js site/tests/kategorien.test.js
git commit -m "feat(karte): Modul themenbaum — Oberkategorien mit Kästchen, Zahl und Klapppfeil, Pills mit Vergleichsfarbe, 15 + alle n; STELLUNGEN in kategorien.js

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Sidebar, App und Legende umstellen

**Files:**
- Modify: `site/js/sidebar.js` (`zeigeThema`, `markiereEigentuemer` → `markiereVergleich`, `_klick`, `_filterEreignisse`, `zeigeThemenliste`)
- Modify: `site/js/app.js` (Importe; `eigentuemerWaehlen` → `vergleichWaehlen`; `setzeZustand`; `wendeThemaAn`; `sucheAusfuehren`; `waehleVorschlag`; `exportiere`; Suchfeld-Init; `popstate`; `start`; `zeichneLegende`; `klickPunkt`/`oeffneHaus`)
- Modify: `site/js/daten.js` (`themaListe(id)`)
- Modify: `site/css/stil.css`
- Test: `site/tests/daten.test.js` (nur `themaListe`); der Rest ist DOM-gebunden und wird in Task 11 per Playwright geprüft.

**Interfaces:**
- Consumes: `baumHtml/kopfHtml/grundlageHtml` (Task 7), `schluesselliste/MAX_VERGLEICH/schluessel` (Task 4), `treffer` Art `vergleich` (Task 5).
- Produces: Sidebar-Aktionen `onVergleich(schluessel, umschalten)`, `onKlassen(klassenString)`; `Sidebar.zeigeThema(thema, liste, vergleich, farben)`; `Sidebar.markiereVergleich(vergleich, farben)`; `Sidebar.baumZustand = { offen, alle }`.

- [ ] **Step 1: Write the failing test** (`daten.test.js`)

```js
test("themaListe lädt themen/<id>_liste.json, null wenn es sie nicht gibt", async () => {
  const l = new Lader("daten/", async (u) => ({ ok: u === "daten/themen/besitz_liste.json", status: 200, json: async () => ({ oberkategorien: [] }) }));
  assert.deepEqual(await l.themaListe("besitz"), { oberkategorien: [] });
  assert.equal(await l.themaListe("bergbau"), null);
});
```

Run: `node --test site/tests/daten.test.js` — Expected: FAIL (`themaListe is not a function`). Dann in `daten.js`: `themaListe(id) { return this.json(`themen/${id}_liste.json`); }` — Run erneut — Expected: PASS.

- [ ] **Step 2: sidebar.js umbauen**

```js
import { baumHtml, kopfHtml, grundlageHtml } from "./themenbaum.js";
// im Konstruktor:
    this.baumZustand = { offen: null, alle: null };
    this.themenkopf.addEventListener("click", (ev) => this._themenKlick(ev));
    this.themenkopf.addEventListener("change", (ev) => {
      const cb = ev.target.closest("[data-klasse]"); if (!cb) return;
      const alle = this._thema.schalter.klassen;
      const an = alle.filter((k) => this.themenkopf.querySelector(`[data-klasse="${CSS.escape(k)}"]`).checked);
      this.a.onKlassen(an.length === alle.length ? "" : an.length ? an.join(",") : "keine");
    });

  // Themenkopf (Spec Themenbaum §2): Kopf, Baum (Kästchen = Schalter, Pfeil = Klappliste, Pills = Vergleich), Grundlage.
  zeigeThema(thema, liste = null, vergleich = [], farben = [], klassen = "") {
    this._thema = thema; this._liste = liste; this._vergleich = vergleich; this._farben = farben; this._klassen = klassen;
    if (!thema) { this.themenkopf.hidden = true; this.themenkopf.innerHTML = ""; this.baumZustand = { offen: null, alle: null }; return; }
    this._baumZeichnen();
    this.themenkopf.hidden = false;
  }
  _baumZeichnen() {
    const t = this._thema;
    const baum = t.schalter ? baumHtml(t, this._liste, { klassen: this._klassen, vergleich: this._vergleich, farben: this._farben, ...this.baumZustand }) : "";
    this.themenkopf.innerHTML = kopfHtml(t) + baum + grundlageHtml(t);
  }
  markiereVergleich(vergleich, farben) { this._vergleich = vergleich; this._farben = farben; if (this._thema) this._baumZeichnen(); }
  setzeKlassen(klassen) { this._klassen = klassen; if (this._thema) this._baumZeichnen(); }
  _themenKlick(ev) {
    const t = ev.target;
    if (t.closest("[data-thema-aus]")) return this.a.onZustand({ thema: "" });
    const auf = t.closest("[data-auf]"); if (auf) { const k = auf.dataset.auf; this.baumZustand = { offen: this.baumZustand.offen === k ? null : k, alle: null }; return this._baumZeichnen(); }
    const alle = t.closest("[data-alle]"); if (alle) { this.baumZustand.alle = alle.dataset.alle; return this._baumZeichnen(); }
    const s = t.closest("[data-schluessel]"); if (s) return this.a.onVergleich(s.dataset.schluessel, true);
  }
```

`markiereEigentuemer` entfällt. In `_klick`: `[data-eig-weg]` → `const weg = t.closest("[data-weg]"); if (weg) return this.a.onVergleich(weg.dataset.weg, true);` und `[data-eigentuemer]` → `const s = t.closest("[data-schluessel]"); if (s) return this.a.onVergleich(s.dataset.schluessel, false);`. In `_filterEreignisse` Beruf-Filter: `this.a.onZustand({ beruf: beruf.value.trim(), vergleich: [] })`. `zeigeThemenliste(themen, aktiv = "")`: `aria-pressed="${t.id === aktiv}"` je Knopf. `setzeVorschlaege(g, plus)`: Plus bei `k === "eigentuemer" || k === "berufe"` und `v.art !== "beruf"`.

- [ ] **Step 3: app.js umbauen**

Importe: `import { liesZustand, schreibeZustand, MAX_VERGLEICH, schluesselliste, schluessel } from "./zustand.js";` (`anzeigeFuer`-Import und `mehrfachZahl` bleiben für die Legende nötig: `mehrfachZahl` ja, `anzeigeFuer` nein).

```js
const sidebar = new Sidebar(…, {
  …,
  onVergleich: (s, umschalten) => vergleichWaehlen(s, umschalten),
  onKlassen: (klassen) => setzeZustand({ klassen }, false),
});

// Vergleich (Spec Themenbaum §3): Schlüssel anhängen, bei umschalten=true einen gewählten entfernen; höchstens MAX_VERGLEICH.
function vergleichWaehlen(s, umschalten) {
  const alt = zustand.vergleich;
  let neu;
  if (alt.includes(s)) { if (!umschalten) return; neu = alt.filter((x) => x !== s); }
  else if (alt.length >= MAX_VERGLEICH) { sidebar.zeigeHinweis(`Höchstens ${MAX_VERGLEICH} Gruppen gleichzeitig.`); return; }
  else neu = [...alt, s];
  sidebar.setzeVorschlaege(null);
  setzeZustand({ vergleich: neu, q: "", beruf: "", id: "" }, true);
}
function knopfTitel(s) {
  if (zustand.vergleich.includes(s)) return "bereits im Vergleich";
  return zustand.vergleich.length ? "zum Vergleich hinzufügen" : "alle Häuser dieser Gruppe";
}
```

`setzeZustand`: `zustand = { ...zustand, ...patch, vergleich: schluesselliste(patch.vergleich === undefined ? zustand.vergleich : patch.vergleich) };`; Klassenwechsel: `if (alt.thema !== zustand.thema) await wendeThemaAn(); else if (alt.klassen !== zustand.klassen) { themaAktiv = await ladeThema(lader, zustand.thema, zustand.klassen); karte.setzeFarbe(themaAktiv ? themaAktiv.farbregel : null); sidebar.setzeKlassen(zustand.klassen); }`; Suchbedingung: `if (alt.beruf !== zustand.beruf || alt.vergleich.join("|") !== zustand.vergleich.join("|"))` mit `auswahl = zustand.beruf ? { art: "beruf", beruf: zustand.beruf } : zustand.vergleich.length ? { art: "vergleich", schluessel: zustand.vergleich } : null;` und Suchfeld: bei genau einem Schlüssel wird der Name nach `sucheAusfuehren()` aus `ergebnis.gruppen[0].name` gesetzt (siehe unten), sonst leer.

`wendeThemaAn`: `sidebar.zeigeThema(t, t && t.baum ? await lader.themaListe(t.id) : null, zustand.vergleich, FARBEN.gruppen, zustand.klassen);` (Zeile mit `eigentuemerliste` ersetzen).

`sucheAusfuehren`: erste Zeile `sidebar.markiereVergleich(zustand.vergleich, FARBEN.gruppen);`; nach `ergebnis = await treffer(…)`: `if (ergebnis.gruppen && ergebnis.gruppen.length === 1 && !zustand.q) sidebar.suche.value = ergebnis.gruppen[0].name; document.getElementById("suche-leeren").hidden = !sidebar.suche.value;`.

`waehleVorschlag`: `if (v.art === "eigentuemer") return vergleichWaehlen(`eig:${v.name}`, false); if (v.art === "ohdab") return vergleichWaehlen(`norm:${v.ohdab}`, false);`; die übrigen Patches `eigentuemer: [] , ohdab: ""` → `vergleich: []`. `sucheAusText`, „suche-leeren“, `exportiere` (Dateiname: `zustand.vergleich.length > 1 ? "essen1936-vergleich.csv" : … (zustand.q || zustand.beruf || (ergebnis.gruppen && ergebnis.gruppen[0].name) || "treffer")`), Suchfeld-Init und `popstate` (`sidebar.suche.value = zustand.q || ""` — der Gruppenname kommt nach der Suche), `start` (`auswahl = … zustand.vergleich.length ? { art: "vergleich", schluessel: zustand.vergleich } …`; der `ohdab`-Zweig und `ohdabName` entfallen). `oeffneHaus`/`klickPunkt`: `[data-eigentuemer]` → `[data-schluessel]`, `n.title = knopfTitel(n.dataset.schluessel)`, Klick `vergleichWaehlen(n.dataset.schluessel, false)`. `themenListe(lader).then((l) => sidebar.zeigeThemenliste(l, zustand.thema))`.

`zeichneLegende` — der Themenblock (`if (themaAktiv && themaAktiv.farbe) { … }`) wird auf `einfach` und `skala` gekürzt (Themen ohne Baum, z. B. Akademiker); `kategorien` zeichnet nichts mehr. Der Rest:

```js
  const f = zustand.ebene.length === 1 ? FARBEN[zustand.ebene[0]] : FARBEN.neutral;
  html += `<div class="zeile"><span class="punkt" style="background:${f}"></span> hausgenau</div>` +
    `<div class="zeile"><span class="punkt ungenau" style="color:${f}"></span> nur straßengenau / Stadtplan 1935</div>`;
  if (ergebnis && ergebnis.gruppen) { if (mehrfachZahl(ergebnis.gruppen)) html += `<div class="zeile"><span class="punkt ring"></span> in mehreren Gruppen</div>`; }
  else if (ergebnis) html += `<div class="zeile"><span class="punkt" style="background:${FARBEN.treffer}"></span> Suchtreffer</div>`;
  html += `<div class="zeile">Größe = Zahl der Einträge</div>`;
  document.getElementById("legende").innerHTML = html;
```

(Der `[data-klasse]`-Handler am Ende entfällt; der Sammelzeilen-Satz steht jetzt in der Vergleichsleiste.)

- [ ] **Step 4: CSS** (`stil.css`, `.eigentuemerliste`-Regeln ersetzen)

```css
.baum { padding: 4px 12px 6px; }
.baum .ober { display: flex; align-items: center; gap: 4px; margin: 2px 0; font-size: 13px; }
.baum .ober label.schalter { display: flex; align-items: center; gap: 6px; flex: 1; cursor: pointer; min-height: 26px; }
.baum .ober input { margin: 0; } .baum .ober small { color: var(--grau); }
.baum .ober .punkt { width: 12px; height: 12px; border-radius: 50%; display: inline-block; flex: none; }
.baum .auf { border: 0; background: none; cursor: pointer; font-size: 14px; padding: 2px 6px; color: var(--grau); min-width: 28px; min-height: 26px; }
.pills-s { display: flex; flex-wrap: wrap; gap: 4px; padding: 2px 0 8px 22px; max-height: 28vh; overflow: auto; }
.pill-s, .pills-s .alle { display: inline-block; margin: 0; padding: 3px 9px; font-size: 12px; border-radius: 12px; border: 1px solid var(--rand); background: #fff; cursor: pointer; }
.pill-s small { color: var(--grau); } .pill-s[aria-pressed="true"] small { color: #fff; opacity: .8; }
.pills-s .alle { color: var(--blau); border-style: dashed; }
#themenkopf .grundlage { display: block; padding: 0 12px 8px; font-size: 11px; color: var(--grau); }
#themenkopf { max-height: 55vh; overflow: auto; }
.themaknopf[aria-pressed="true"] { background: var(--text); color: #fff; border-color: var(--text); }
```

- [ ] **Step 5: Run the full node suite**

Run: `node --test site/tests/*.test.js`
Expected: alle grün. Dann Rauchtest im Browser (Dev-Server `python3 werkzeuge/serve.py 8765`): `http://localhost:8765/site/karte.html?thema=besitz` lädt ohne Konsolenfehler, Baum sichtbar; `?eigentuemer=Fried.+Krupp+AG` migriert auf `vergleich=eig:Fried.+Krupp+AG` (URL nach Laden prüfen).

- [ ] **Step 6: Commit**

```bash
git add site/js/sidebar.js site/js/app.js site/js/daten.js site/css/stil.css site/tests/daten.test.js
git commit -m "feat(karte): Themenbaum in der Sidebar (Kästchen, Klapplisten, Pills starten Vergleich); Legende nur Zeichen; Vergleich nach Schlüsseln in App und Sidebar; aktives Thema markiert

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Popup und Hausansicht: Vergleichsknöpfe, Stellung

**Files:**
- Modify: `site/js/popup.js` (`eigKnopf` → `vergleichKnopf`, `popupZeile`, `popupZusatz`, `eintragHtml`)
- Test: `site/tests/popup.test.js`

**Interfaces:**
- Produces: `<button class="eiglink" data-schluessel="eig:<Name>">` für Eigentümer und `data-schluessel="norm:<ohdab>"` für Berufe mit Norm; Hausansicht-Feld „Stellung“.

- [ ] **Step 1: Write the failing tests** (bestehende Erwartungen `data-eigentuemer=` in `popup.test.js` auf `data-schluessel="eig:…"` umstellen; neu:)

```js
test("popupZeile und eintragHtml: Beruf mit Norm ist ein Vergleichsknopf norm:<ohdab>; ohne Norm kursiver Rohtext ohne Knopf", () => {
  const e = { id: "1", teil: "I", seite: "I-1", name: "Sepeur", vorname: "W.", beruf: "Bergm.", beruf_norm: "Bergmann", ohdab: "B 21112-100", niveau: "fachlich", stellung: "arbeiter", stellung_quelle: "vorschlag", etage: "", stand: "", flags: [], merkmale: [] };
  assert.match(popupZeile(e), /<span class="n">· <button class="eiglink" data-schluessel="norm:B 21112-100">Bergmann<\/button><\/span>/);
  assert.doesNotMatch(popupZeile(E[0]), /data-schluessel/);
  const h = hausHtml(EIG, [e]);
  assert.match(h, /<span class="k">Beruf<\/span> Bergm\. → <button class="eiglink" data-schluessel="norm:B 21112-100">Bergmann<\/button> · Fachliche Tätigkeit/);
  assert.match(h, /<span class="k">Stellung<\/span> Arbeiter \(Vorschlag der Automatik, nicht handgeprüft\)/);
  assert.match(hausHtml(EIG, [{ ...e, stellung_quelle: "hand" }]), /<span class="k">Stellung<\/span> Arbeiter<\/div>/);
  assert.doesNotMatch(hausHtml(EIG, [{ ...e, stellung: "", stellung_quelle: "" }]), /Stellung<\/span>/);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test site/tests/popup.test.js`
Expected: FAIL — kein `data-schluessel`.

- [ ] **Step 3: Write minimal implementation**

```js
import { KATEGORIEN, NIVEAUS, STELLUNGEN } from "./kategorien.js";
// Vergleichsknopf (Spec Themenbaum §3): app.js hängt den Klick an (alle Häuser / zum Vergleich).
function vergleichKnopf(schluessel, name) { return `<button class="eiglink" data-schluessel="${esc(schluessel)}">${esc(name)}</button>`; }
const eigKnopf = (name) => vergleichKnopf(`eig:${name}`, name);
const normKnopf = (e) => e.beruf_norm && e.ohdab ? vergleichKnopf(`norm:${e.ohdab}`, e.beruf_norm) : esc(e.beruf_norm || "");
```

In `popupZusatz` (Teil I): `const beruf = e.beruf_norm ? normKnopf(e) : e.beruf ? `<i …>` : "";`. In `eintragHtml`: Feld Beruf als `roh`-Feld: `["Beruf", e.beruf_norm ? `${esc(e.beruf)} → ${normKnopf(e)} · ${esc(NIVEAUS[e.niveau] || e.niveau)}${e.status ? " · " + esc(statusText(e.status)) : ""}` : esc(e.beruf), true]`; neues Feld nach Beruf: `["Stellung", e.stellung ? `${esc(STELLUNGEN[e.stellung] || e.stellung)}${e.stellung_quelle === "vorschlag" ? " (Vorschlag der Automatik, nicht handgeprüft)" : ""}` : "", true]`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test site/tests/popup.test.js`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add site/js/popup.js site/tests/popup.test.js
git commit -m "feat(popup): Vergleichsknöpfe für Eigentümer (eig:) und Berufsnormen (norm:); Hausansicht nennt die Stellung und kennzeichnet Vorschläge

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: CSV-Spalte `gruppe`

**Files:**
- Modify: `site/js/exportcsv.js` (Z. 21–25)
- Test: `site/tests/exportcsv.test.js` (Test „Eigentümer-Vergleich: Spalte eigentuemer …“)

- [ ] **Step 1: Test anpassen** — Erwartung `",adress_id,gruppe"` bzw. `…,eintraege,gruppe`; Testname „Vergleich: Spalte gruppe, Adresse in zwei Gruppen erscheint je Gruppe“.
- [ ] **Step 2: Run** `node --test site/tests/exportcsv.test.js` — Expected: FAIL (`eigentuemer` statt `gruppe`).
- [ ] **Step 3: Implement** — `const kopfZusatz = ergebnis.gruppen ? ["gruppe"] : [];`, Kommentar auf „Vergleich (Spec Themenbaum §3)“.
- [ ] **Step 4: Run** — Expected: PASS.
- [ ] **Step 5: Commit**

```bash
git add site/js/exportcsv.js site/tests/exportcsv.test.js
git commit -m "feat(csv): Spalte gruppe statt eigentuemer beim Vergleich

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: Doku, Sichtprüfung, Journal

**Files:**
- Modify: `README.md` (Abschnitte Eigentümer-Vergleich → Vergleich; Themenformat: `baum`, `_liste.json`; Legende), `docs/superpowers/specs/2026-09-29-themenbaum-design.md` (nur Zahlen korrigieren, falls Task 3 abweicht)
- Modify: `~/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Journal.md` (Eintrag)

- [ ] **Step 1: README** — im Abschnitt zur Karte: „Vergleich: bis zu fünf Schlüssel `eig:<Name>` / `norm:<ohdab_id>` (`?vergleich=a|b`); alte Links mit `eigentuemer=`/`ohdab=` werden gelesen. Themen mit `baum: true` zeigen in der Sidebar Oberkategorien (Kästchen = Schalter, Pfeil = Klappliste aus `themen/<id>_liste.json`) und Pills, die den Vergleich starten. Thema Berufe färbt nach Stellung (Hausfeld `stellung`). Legende rechts unten: nur Zeichen.“

- [ ] **Step 2: Sichtprüfung (Playwright, `page.route` no-cache, ≥ 8 s Ladezeit, `?debug=1`)** — Prüfpunkte und erwartetes Ergebnis:

1. `karte.html?thema=besitz&ebene=II`: Sidebar zeigt Kopf, neun Klassenzeilen mit Zahl, `gemischt`/`ungeprüft` ohne Pfeil; Legende rechts unten enthält kein `input`. Konsole: 0 Fehler.
2. Kästchen „Privatperson“ abwählen: URL trägt `klassen=` ohne `privatperson`; `window.__karte.farbe.klassen` ohne `privatperson`; Punkte in Orange verschwinden (Screenshot).
3. Pfeil „Bergbau“: Pills mit Zahlen, „alle n anzeigen“ vorhanden, wenn > 15; Klick auf „Gelsenkirchener Bergwerks-AG (GBAG)“: Pill gefüllt Rot, URL `vergleich=eig:Gelsenkirchener+Bergwerks-AG+(GBAG)`, Vergleichsleiste mit Sammelzeilen-Satz, Trefferebene sichtbar (`__karte.map.getSource("treffer")`).
4. `karte.html?thema=bergbau`: Pfeil „Belegschaft“, Pill „Bergmann“, dann Thema Berufe wählen (Themenliste, Knopf mit `aria-pressed="true"` für berufe), Pfeil „Freie Berufe und Akademiker“, Pill „Arzt“: Leiste mit zwei Gruppen, Ungleich-Satz sichtbar (Bergmann ≫ Arzt), Grundgesamtheits-Satz „Berufe: …“.
5. Popup auf einem Punkt mit Teil-I-Eintrag: Norm ist ein Knopf; Klick hängt `norm:` an (URL prüfen); Hausansicht zeigt „Stellung“.
6. Alter Link `?eigentuemer=Fried.+Krupp+AG|Stadt+Essen`: nach Laden URL mit `vergleich=eig:…|eig:…`, zwei Gruppen in der Leiste.
7. Viewport 390×844 mit `?thema=berufe`: Blatt öffnet „halb“, Kästchen im Blatt klickbar (Klick auf `[data-klasse="arbeiter"]` ändert URL), Legende ohne Kästchen.
8. `?thema=akademiker` (Thema ohne Baum): Legende zeigt weiterhin die einfache Farbzeile; Sidebar-Kopf ohne Baum, kein Fehler.

Screenshots in den Scratchpad-Ordner; Befunde, die vom Erwarteten abweichen, werden als Bug mit Test behandelt (systematic-debugging), nicht still korrigiert.

- [ ] **Step 3: Journal-Eintrag** (Vault): Datum, Anlass (Frage nach getrennten Filtern/Pills; Brainstorming-Verlauf: Pills = Normen, Oberkategorie Stellung, Thema Berufe umgestellt, Werkstatt bleibt für Aggregation), Umsetzung (Listen-Export, `vergleich`-Schlüssel, Themenbaum, Legende), Zahlen aus dem Export (Normen je Bergbau-Gruppe, Anteil handgeprüft), offene Punkte (Gewerbe-Baum, Hauptgruppen, Bündelung).

- [ ] **Step 4: Full suites**

Run: `node --test site/tests/*.test.js` — Expected: alle grün (≈ 190 + neue).
Run: `python3 -m pytest -q` — Expected: alle grün.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/superpowers/specs/2026-09-29-themenbaum-design.md
git commit -m "docs: Themenbaum, Vergleich nach Schlüsseln und Thema Berufe nach Stellung im README; Sichtprüfung dokumentiert

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Self-Review

- **Spec-Abdeckung:** §2 Baum (Task 7/8), Akkordeon und „alle n“ (7), Themenwechsel-Markierung (8), Grundlage unten (7/8); §3 Zustand/Migration (4), Suche (5), Leiste mit Grundgesamtheit und Ungleich-Satz (6), Popup-Knöpfe (9), CSV `gruppe` (10); §4 Stellung: Hausfeld (1), Thema (3), Namen/Farben (7), Popup (9), Anteil handgeprüft (2, 7); §5 Legende (8); §6 Listen (2), `baum: true` (3); §7 Tests je Task; §8 Reihenfolge eingehalten. Spec §2 sagt, der Themenkopf werde bei Treffern ausgeblendet — im Code ist er es nicht (eigenes Element `#themenkopf`), es ist nichts zu tun; Ledger-Notiz genügt.
- **Platzhalter:** keine „TBD“/„später“; jeder Codeschritt hat Code.
- **Typkonsistenz:** `schluessel(s) → {typ, wert}` (Task 4) wird in 5, 6 genutzt; Gruppen tragen `schluessel` (5) und werden in 6, 8, 10 gelesen; `baumHtml(thema, liste, opt)` (7) in 8; `themaListe(id)` (8) in 8; `onVergleich(s, umschalten)`/`onKlassen(klassen)` (8) in 8/9-Handlern; `OBERKATEGORIEN` (2) passt zu `schalter.klassen` (3) bis auf `gemischt`/`ungeprueft`, die die Liste separat trägt.
- **Review Focus:** 1 → Task 4, 2 → Task 5, 3 → Task 1, 4 → Task 7, 5 → Task 2. Abgedeckt.
