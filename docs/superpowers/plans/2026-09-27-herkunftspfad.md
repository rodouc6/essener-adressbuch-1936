# Schlaglichter Schritt 2: Herkunftspfad im Detailkasten — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Der Detailkasten der Schlaglichter zeigt beim Schweben die Herkunftskette einer Zahl (Buch → Norm/Eigentümer/Rubrik → Klasse → Gruppe, mit Quellmarken) und beim Klick eine Belegtabelle mit Schreibweisen, Nennungen, Quelle und Verweis auf die Kuratierungsdatei.

**Architecture:** Ein neues Exportpaket `site/daten/herkunft/*.json` (`baue_herkunft(adressen)` in `pipeline/lib/karte_export.py`) liefert je Klasse und je Einzelobjekt (Norm, Eigentümer, Rubrik) Schreibweisen und Quellanteile aus den verorteten Einträgen. Im Browser bleiben alle Textregeln in `site/js/perspektiven_modell.js` (rein, getestet); `perspektiven.js` lädt die Datei beim ersten Bedarf nach (`Lader.herkunft`) und hängt Pfad und Belegtabelle unter den bisherigen Kasten.

**Tech Stack:** Python ≥ 3.12 + pytest; ES-Module + `node --test`; kein Build-Schritt.

**Spec:** `docs/superpowers/specs/2026-09-27-herkunftspfad-design.md`

## Global Constraints

- Alle Zählungen im Herkunftspaket beziehen sich auf die **verorteten** Einträge (Grundmenge von `gruppiere`), nicht auf die Kuratierungstabellen.
- Quellmarken: `hand` `#15803d`, `vorschlag` `#6b7280`, `claude` `#6d28d9`, `regel` `#b45309`; Marken mit 0 entfallen.
- Beim Klick ist die Belegtabelle **sofort geöffnet**; höchstens zehn Zeilen, dann Link „alle … in der Suche ›“.
- Fehlt die Herkunftsdatei (alter Export, 404): Kasten wie bisher, keine Fehlermeldung im Kasten, ein `console.warn`.
- Formen bleiben reine Zeichenkettenerzeuger; Textregeln nur im Modell.
- Tests vor Beginn: 429 pytest, 98 node; nach jeder Task grün. Commits mit `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Review Focus

1. **Gruppe aus mehreren Klassen** (Bürgertum = beamte + angestellte + freie_berufe + unternehmer): Quellanteile und Schreibweisen müssen über alle Klassen summiert und die Top-Liste neu sortiert sein, nicht nur die erste Klasse zeigen. Test in Task 2.
2. **Klasse ohne Eintrag in der Herkunftsdatei** (z. B. `gemischt`, `sonstige` mit 0 Einträgen im Fixture-Export): Pfad zeigt 0 Schreibweisen und keine Marke, kein `undefined` im Text. Test in Task 2.
3. **Kreis, dessen id nicht in der Datei steht** (Layout und Herkunft aus verschiedenen Exportläufen): leerer Pfad, Kasten wie bisher. Test in Task 2.
4. **Schwebender Kasten während des Nachladens**: erst nach dem Laden erscheint der Pfad, aber nur, wenn der Kasten noch dieselbe Einheit zeigt; ein schneller Zeigerwechsel darf keinen falschen Pfad hinterlassen. Sichtprüfung in Task 3, Regel `herkunftAktuell(detail, geladenFuer)` mit Test in Task 2.
5. **Eigentümer ohne gesicherte Identität** (Privatperson mit Allerweltsnamen): kein Kreis im Layout, aber in `herkunft/eigentuemer.json` darf er auch nicht auftauchen (keine Identitätsbehauptung). Test in Task 1.

---

### Task 1: Exportpaket `herkunft/`

**Files:**
- Modify: `pipeline/lib/karte_export.py` (neue Funktion `baue_herkunft` vor `baue_layouts`; Aufruf in `schreibe_paket` nach den Layouts)
- Modify: `pipeline/06_karte_export.py:51` (Ordner `herkunft` mit leeren)
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Produces: `baue_herkunft(adressen: dict[str, dict]) -> dict[str, dict]` mit den Schlüsseln `stellung`, `gruppe`, `niveau`, `berufe`, `besitz`, `eigentuemer`, `gewerbe`, `rubriken` (Inhalte wie Spec §3). `schreibe_paket` schreibt `ausgabe/herkunft/<name>.json` je Schlüssel.

- [ ] **Step 1: Failing test schreiben**

An `tests/test_karte_export.py` anhängen:

```python
def _adr(aid, eintraege, **k):
    return dict(id=aid, lat=51.4, lon=7.0, stufe="haus", stadtteil="Kray", eintraege=eintraege,
                besitz="ungeprueft", besitz_pruefung="", besitz_quelle="", besitz_eigentuemer="", **k)


def _bf(schreibweise, norm, ohdab, stellung, quelle="hand", niveau="fachlich", gruppe="B21"):
    return dict(teil="I", **{"Beruf o. ä.": schreibweise},
                _beruf=dict(beruf=norm, ohdab=ohdab, niveau=niveau, gattung="", gattung_id="", status="", norm=norm,
                            stellung=stellung, stellung_quelle=quelle, gruppe=gruppe))


def test_baue_herkunft_stellung_und_berufe():
    from pipeline.lib.karte_export import baue_herkunft
    a = {"1": _adr("1", [_bf("Bergm.", "Bergmann", "B 21112-100", "arbeiter"), _bf("Bergm.", "Bergmann", "B 21112-100", "arbeiter"),
                        _bf("Bergmann", "Bergmann", "B 21112-100", "arbeiter"), _bf("Schlosser", "Schlosser", "B 24412-127", "arbeiter", "vorschlag"),
                        _bf("Lehrer", "Lehrer", "B 84124-120", "beamte", niveau="hochkomplex", gruppe="B84"),
                        dict(teil="I", **{"Beruf o. ä.": "Kfm."}, _beruf=None)])}
    h = baue_herkunft(a)
    st = h["stellung"]["arbeiter"]
    assert (st["schreibweisen"], st["normen"], st["nennungen"]) == (3, 2, 4)
    assert st["quelle"] == {"hand": 3, "vorschlag": 1}
    assert st["top"] == [["Bergm.", 2, "Bergmann", "hand"], ["Bergmann", 1, "Bergmann", "hand"], ["Schlosser", 1, "Schlosser", "vorschlag"]]
    assert h["stellung"]["beamte"]["top"] == [["Lehrer", 1, "Lehrer", "hand"]]
    # ungeprüfter Beruf zählt zu „unbestimmt“, ohne Norm
    assert h["stellung"]["unbestimmt"]["nennungen"] == 1 and h["stellung"]["unbestimmt"]["top"] == [["Kfm.", 1, "", ""]]
    assert h["gruppe"]["B21"]["nennungen"] == 4 and h["gruppe"]["B21"]["quelle"] == {"hand": 4}
    assert h["niveau"]["hochkomplex"]["nennungen"] == 1
    b = h["berufe"]["B 21112-100"]
    assert b == {"norm": "Bergmann", "nennungen": 3, "schreibweisen": [["Bergm.", 2], ["Bergmann", 1]], "stellung": "arbeiter", "stellung_quelle": "hand"}


def test_baue_herkunft_besitz_und_eigentuemer():
    from pipeline.lib.karte_export import baue_herkunft
    krupp = lambda s: dict(teil="II", **{"Firmenname": s}, lastname="", firstname="", page="II-040", _eigentuemer="Fried. Krupp AG",
                           _kategorie="industrie", _identitaet=True, _pruefung="hand")
    person = dict(teil="II", **{"Firmenname": ""}, lastname="Müller", firstname="H.", page="II-041", _eigentuemer="", _kategorie="privatperson",
                  _identitaet=False, _pruefung="regel")
    a = {"1": _adr("1", [krupp("Fried. Krupp A.G.")], besitz="industrie", besitz_pruefung="hand", besitz_quelle="eintrag", besitz_eigentuemer="Fried. Krupp AG"),
         "2": _adr("2", [krupp("Fried. Krupp A.-G.")], besitz="industrie", besitz_pruefung="hand", besitz_quelle="eintrag", besitz_eigentuemer="Fried. Krupp AG"),
         "3": _adr("3", [], besitz="industrie", besitz_pruefung="hand", besitz_quelle="spanne", besitz_eigentuemer="Fried. Krupp AG"),
         "4": _adr("4", [person], besitz="privatperson", besitz_pruefung="regel", besitz_quelle="eintrag"),
         "5": _adr("5", [], besitz="ungeprueft")}
    h = baue_herkunft(a)
    ind = h["besitz"]["industrie"]
    assert (ind["eigentuemer"], ind["zeilen"], ind["haeuser"], ind["spanne"], ind["nummer"]) == (1, 2, 3, 1, 0)
    assert ind["quelle"] == {"hand": 3, "regel": 0} and ind["top"] == [["Fried. Krupp AG", 3]]
    pr = h["besitz"]["privatperson"]
    assert pr["quelle"] == {"hand": 0, "regel": 1} and pr["regel_beispiele"] == [["Müller, H.", 1]]
    k = h["eigentuemer"]["Fried. Krupp AG"]
    assert k == {"schreibweisen": [["Fried. Krupp A.-G.", 1], ["Fried. Krupp A.G.", 1]], "schreibweisen_gesamt": 2, "zeilen": 2, "haeuser": 3,
                 "spanne": 1, "nummer": 0, "kategorie": "industrie", "identitaet": True, "seite": "II-040"}
    # Review Focus 5: ohne gesicherte Identität kein Eintrag je Eigentümer
    assert "Müller, H." not in h["eigentuemer"] and "" not in h["eigentuemer"]


def test_baue_herkunft_gewerbe_und_rubriken():
    from pipeline.lib.karte_export import baue_herkunft
    gw = lambda rubrik, gruppe, art, quelle: dict(teil="III", **{"Firmenname": "X, " + rubrik}, _gewerbe=dict(rubrik=rubrik, firma="X", gruppe=gruppe, art=art, quelle=quelle, schluessel="x"))
    a = {"1": _adr("1", [gw("Bäcker", "lebensmittel", "handwerk", "hand"), gw("Bäcker", "lebensmittel", "handwerk", "hand"),
                        gw("Kolonialwaren", "lebensmittel", "handel", "claude"), gw("Maler", "bau", "handwerk", "vorschlag")])}
    h = baue_herkunft(a)
    lm = h["gewerbe"]["lebensmittel"]
    assert (lm["rubriken"], lm["betriebe"]) == (2, 3) and lm["quelle"] == {"hand": 2, "claude": 1, "vorschlag": 0}
    assert lm["top"] == [["Bäcker", 2, "handwerk", "hand"], ["Kolonialwaren", 1, "handel", "claude"]]
    assert h["rubriken"]["Maler"] == {"betriebe": 1, "gruppe": "bau", "art": "handwerk", "quelle": "vorschlag"}


def test_schreibe_paket_schreibt_herkunft(tmp_path):
    schreibe_paket(tmp_path, [_v(id="1", teil="I")], [], [], "2026-09-27", kacheln=False)
    for name in ("stellung", "gruppe", "niveau", "berufe", "besitz", "eigentuemer", "gewerbe", "rubriken"):
        assert (tmp_path / "herkunft" / f"{name}.json").exists(), name
    assert json.loads((tmp_path / "herkunft" / "stellung.json").read_text(encoding="utf-8"))["unbestimmt"]["nennungen"] == 1
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag sehen**

Run: `python3 -m pytest tests/test_karte_export.py -q -k herkunft`
Expected: FAIL mit `ImportError: cannot import name 'baue_herkunft'`.

- [ ] **Step 3: `baue_herkunft` implementieren**

In `pipeline/lib/karte_export.py` direkt vor `def baue_layouts` einfügen:

```python
TOP_N = 10


def _top(zaehler: dict, n: int = TOP_N) -> list:
    """Die n häufigsten Einträge eines Zählers als Listen [schlüssel…, zahl], absteigend, bei Gleichstand alphabetisch."""
    return [[*k, z] if isinstance(k, tuple) else [k, z] for k, z in sorted(zaehler.items(), key=lambda kv: (-kv[1], kv[0]))[:n]]


def _sammle_berufe(adressen: dict[str, dict], schluessel) -> dict[str, dict]:
    """Je Wert von `schluessel(_beruf)` (Stellung, Hauptgruppe, Niveau): Schreibweisen, Normen, Nennungen, Quelle, Top-Schreibweisen.
    Einträge ohne geprüften Beruf zählen bei der Stellung als `unbestimmt` (Schreibweise ohne Norm und ohne Quelle)."""
    aus: dict[str, dict] = {}
    for a in adressen.values():
        for e in a["eintraege"]:
            if e.get("teil") != "I":
                continue
            b = e.get("_beruf")
            klasse = schluessel(b) if b else None
            if klasse is None:
                continue
            k = aus.setdefault(klasse, dict(_schreib=defaultdict(int), _normen=set(), _quelle=defaultdict(int), _norm_von={}, _quelle_von={}))
            s = e.get("Beruf o. ä.", "")
            k["_schreib"][s] += 1
            if b:
                k["_normen"].add(b["ohdab"]); k["_norm_von"][s] = b["norm"]
                q = b.get("stellung_quelle", "hand") if schluessel is _stellung_klasse else "hand"
                k["_quelle"][q] += 1; k["_quelle_von"][s] = q
            else:
                k["_norm_von"][s] = ""; k["_quelle_von"][s] = ""
    out = {}
    for klasse, k in aus.items():
        out[klasse] = dict(schreibweisen=len(k["_schreib"]), normen=len(k["_normen"]), nennungen=sum(k["_schreib"].values()),
                           quelle=dict(k["_quelle"]),
                           top=[[s, n, k["_norm_von"][s], k["_quelle_von"][s]] for s, n in _top(k["_schreib"])])
    return out


def _stellung_klasse(b):
    return b["stellung"] if b else "unbestimmt"


def baue_herkunft(adressen: dict[str, dict]) -> dict[str, dict]:
    """Herkunftspaket (Spec 2026-09-27 Herkunftspfad §3): je Klasse und je Einzelobjekt, woher die Zahl kommt —
    Schreibweisen des Buches, Normen bzw. kanonische Namen, Quellanteile (Hand/Vorschlag/Regel/Prinzipien)."""
    stellung = _sammle_berufe(adressen, _stellung_klasse)
    # Stellung: auch Einträge ohne geprüften Beruf, als unbestimmt
    unbest = stellung.setdefault("unbestimmt", dict(schreibweisen=0, normen=0, nennungen=0, quelle={}, top=[]))
    ohne = defaultdict(int)
    for a in adressen.values():
        for e in a["eintraege"]:
            if e.get("teil") == "I" and not e.get("_beruf"):
                ohne[e.get("Beruf o. ä.", "")] += 1
    if ohne:
        schreib = defaultdict(int, {t[0]: t[1] for t in unbest["top"]})
        for s, n in ohne.items(): schreib[s] += n
        vorhanden = {t[0]: (t[2], t[3]) for t in unbest["top"]}
        unbest["schreibweisen"] += len(ohne); unbest["nennungen"] += sum(ohne.values())
        unbest["top"] = [[s, n, *vorhanden.get(s, ("", ""))] for s, n in _top(schreib)]
    for k in stellung.values():
        k["quelle"] = {"hand": k["quelle"].get("hand", 0), "vorschlag": k["quelle"].get("vorschlag", 0)}
    gruppe = _sammle_berufe(adressen, lambda b: b["gruppe"] if b else None)
    niveau = _sammle_berufe(adressen, lambda b: b["niveau"] if b else None)
    for d in (gruppe, niveau):
        for k in d.values(): k["quelle"] = {"hand": k["quelle"].get("hand", 0)}

    berufe: dict[str, dict] = {}
    for a in adressen.values():
        for e in a["eintraege"]:
            b = e.get("_beruf")
            if not b or e.get("teil") != "I":
                continue
            n = berufe.setdefault(b["ohdab"], dict(norm=b["norm"], _schreib=defaultdict(int), stellung=b["stellung"], stellung_quelle=b.get("stellung_quelle", "hand")))
            n["_schreib"][e.get("Beruf o. ä.", "")] += 1
    berufe = {k: dict(norm=v["norm"], nennungen=sum(v["_schreib"].values()), schreibweisen=_top(v["_schreib"]), stellung=v["stellung"], stellung_quelle=v["stellung_quelle"])
              for k, v in berufe.items()}

    besitz: dict[str, dict] = {}
    eig: dict[str, dict] = {}
    for a in adressen.values():
        klasse = a.get("besitz", "ungeprueft")
        if klasse == "ungeprueft":
            continue
        k = besitz.setdefault(klasse, dict(_eig=set(), zeilen=0, haeuser=0, quelle={"hand": 0, "regel": 0}, spanne=0, nummer=0, _top=defaultdict(int), _regel=defaultdict(int)))
        k["haeuser"] += 1
        k["quelle"]["regel" if a.get("besitz_pruefung") == "regel" else "hand"] += 1
        if a.get("besitz_quelle") == "spanne": k["spanne"] += 1
        if a.get("besitz_quelle") == "nummer": k["nummer"] += 1
        kanon = a.get("besitz_eigentuemer", "")
        if kanon:
            k["_eig"].add(kanon); k["_top"][kanon] += 1
            x = eig.setdefault(kanon, dict(_schreib=defaultdict(int), zeilen=0, haeuser=0, spanne=0, nummer=0, kategorie=klasse, identitaet=True, seite=""))
            x["haeuser"] += 1
            if a.get("besitz_quelle") == "spanne": x["spanne"] += 1
            if a.get("besitz_quelle") == "nummer": x["nummer"] += 1
        for e in a["eintraege"]:
            if e.get("teil") != "II":
                continue
            k["zeilen"] += 1
            s = e.get("Firmenname") or ", ".join(t for t in (e.get("lastname", ""), e.get("firstname", "")) if t)
            if e.get("_pruefung") == "regel":
                k["_regel"][s] += 1
            if e.get("_eigentuemer") and e.get("_identitaet"):
                x = eig.setdefault(e["_eigentuemer"], dict(_schreib=defaultdict(int), zeilen=0, haeuser=0, spanne=0, nummer=0, kategorie=e.get("_kategorie", klasse), identitaet=True, seite=""))
                x["zeilen"] += 1; x["_schreib"][s] += 1
                if not x["seite"]: x["seite"] = e.get("page", "")
    besitz = {kl: dict(eigentuemer=len(k["_eig"]), zeilen=k["zeilen"], haeuser=k["haeuser"], quelle=k["quelle"], spanne=k["spanne"], nummer=k["nummer"],
                       top=_top(k["_top"]), **({"regel_beispiele": _top(k["_regel"], 5)} if kl == "privatperson" else {}))
              for kl, k in besitz.items()}
    eigentuemer = {kanon: dict(schreibweisen=_top(x["_schreib"]), schreibweisen_gesamt=len(x["_schreib"]), zeilen=x["zeilen"], haeuser=x["haeuser"],
                               spanne=x["spanne"], nummer=x["nummer"], kategorie=x["kategorie"], identitaet=x["identitaet"], seite=x["seite"])
                   for kanon, x in eig.items()}

    gewerbe: dict[str, dict] = {}
    rubriken: dict[str, dict] = {}
    for a in adressen.values():
        for e in a["eintraege"]:
            g = e.get("_gewerbe")
            if not g or e.get("teil") != "III":
                continue
            k = gewerbe.setdefault(g["gruppe"], dict(_rub=defaultdict(int), quelle={"hand": 0, "claude": 0, "vorschlag": 0}, _art={}, _quelle={}))
            k["_rub"][g["rubrik"]] += 1
            k["quelle"][g["quelle"]] = k["quelle"].get(g["quelle"], 0) + 1
            k["_art"][g["rubrik"]] = g["art"]; k["_quelle"][g["rubrik"]] = g["quelle"]
            r = rubriken.setdefault(g["rubrik"], dict(betriebe=0, gruppe=g["gruppe"], art=g["art"], quelle=g["quelle"]))
            r["betriebe"] += 1
    gewerbe = {gr: dict(rubriken=len(k["_rub"]), betriebe=sum(k["_rub"].values()), quelle=k["quelle"],
                        top=[[r, n, k["_art"][r], k["_quelle"][r]] for r, n in _top(k["_rub"])])
               for gr, k in gewerbe.items()}
    return dict(stellung=stellung, gruppe=gruppe, niveau=niveau, berufe=berufe, besitz=besitz, eigentuemer=eigentuemer, gewerbe=gewerbe, rubriken=rubriken)
```

Hinweis zum `unbestimmt`-Block: Einträge mit geprüftem Beruf und `stellung == "unbestimmt"` kommen schon über `_sammle_berufe` (mit Norm und Quelle) hinein; Einträge ohne geprüften Beruf werden dazugezählt (Schreibweise ohne Norm, ohne Quelle). Die Top-Liste ist damit nach Nennungen über beide Herkünfte sortiert.

`defaultdict` ist in der Datei bereits importiert (Zeile 9).

In `schreibe_paket` nach der Layout-Schleife (`_json(ausgabe / "layout" / f"{name}.json", inhalt)`) ergänzen:

```python
    for name, inhalt in baue_herkunft(adressen).items():
        _json(ausgabe / "herkunft" / f"{name}.json", inhalt)
```

In `pipeline/06_karte_export.py:51` die Tupel-Liste um `"herkunft"` erweitern:

```python
for unter in ("haus", "suche", "adressen", "themen", "ebenen", "layout", "perspektiven", "herkunft"):
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS (433). Schlägt `test_baue_herkunft_stellung_und_berufe` an `schreibweisen == 3` für arbeiter fehl, prüfen, ob `_sammle_berufe` die Schreibweise aus `Beruf o. ä.` liest (nicht aus `_beruf["beruf"]`).

- [ ] **Step 5: Export laufen lassen, Größe prüfen**

Run: `python3 pipeline/06_karte_export.py --ohne-kacheln && du -sh site/daten/herkunft && python3 -c "import json;h=json.load(open('site/daten/herkunft/stellung.json'));print(h['arbeiter']['top'][:3], h['arbeiter']['quelle'])"`
Expected: Ordner unter 1 MB; `Bergm.` an erster Stelle, `quelle` mit hand ≫ vorschlag.

- [ ] **Step 6: Commit**

```bash
git add pipeline/lib/karte_export.py pipeline/06_karte_export.py tests/test_karte_export.py
git commit -m "feat(export): Herkunftspaket site/daten/herkunft — Schreibweisen, Normen und Quellanteile je Klasse, Norm, Eigentümer, Rubrik

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Modell — Pfad, Belegtabelle, Link, Regel-Teil im Balken

**Files:**
- Modify: `site/js/perspektiven_modell.js` (neu: `HERKUNFT_DATEI`, `herkunftDatei`, `herkunftPfad`, `herkunftTabelle`, `herkunftLink`, `herkunftAktuell`, `BELEG`, `QUELLEN`)
- Modify: `site/js/formen/balken.js` (schraffierter Teil bekommt `data-id="<Gruppe>#regel"`)
- Modify: `site/js/daten.js` (`herkunft(name)`)
- Test: `site/tests/perspektiven.test.js`, `site/tests/formen.test.js`

**Interfaces:**
- Produces:
  - `herkunftDatei(kontext) → "stellung"|"gruppe"|"niveau"|"besitz"|"gewerbe"|"berufe"|"eigentuemer"|"rubriken"|null`
  - `herkunftPfad(kontext, herkunft, ansicht) → [{ label, wert, marken: [{ art, anteil, zahl }] }]` (leer, wenn nichts bekannt)
  - `herkunftTabelle(kontext, herkunft, ansicht) → { kopf: [..], zeilen: [[..]], gesamt: int, hinweis: string }` oder `null`
  - `herkunftLink(kontext, herkunft) → string|null`
  - `herkunftAktuell(detail, geladenFuer) → boolean`
  - `kontext = { art: "segment"|"kreis"|"einheit"|"regel"|"ausgeschlossen", daten, id, gruppe }` — `gruppe` ist das Gruppenobjekt der Ansicht (`{ name, aus, farbe }`) bei `segment`/`regel`, sonst null.
  - `Lader.herkunft(name)` lädt `herkunft/<name>.json`.
  - Balken: schraffierter Teil `data-id="<Gruppenname>#regel"`; `detailTextGruppe` behandelt `#regel` wie die Gruppe (Titel „<Gruppe> · per Regel“).

- [ ] **Step 1: Failing tests schreiben**

`site/tests/perspektiven.test.js`, Import erweitern um `herkunftAktuell, herkunftDatei, herkunftLink, herkunftPfad, herkunftTabelle` und anhängen:

```js
const H_ST = { arbeiter: { schreibweisen: 534, normen: 419, nennungen: 74635, quelle: { hand: 70000, vorschlag: 4635 }, top: [["Bergm.", 27781, "Bergmann", "hand"], ["Arbeiter", 8432, "Arbeiter", "hand"], ["Schlosser", 7193, "Schlosser", "hand"]] },
               beamte: { schreibweisen: 120, normen: 80, nennungen: 10444, quelle: { hand: 10444, vorschlag: 0 }, top: [["Lehrer", 900, "Lehrer", "hand"]] },
               angestellte: { schreibweisen: 200, normen: 150, nennungen: 12604, quelle: { hand: 12000, vorschlag: 604 }, top: [["Angest.", 5000, "Angestellter", "hand"]] } };
const G_ST = { name: "Arbeiter/Gehilfen", aus: ["arbeiter"], farbe: "#e69f00" };
const A_ST = { daten: "stellung", gruppen: [G_ST, { name: "Bürgertum", aus: ["beamte", "angestellte", "freie_berufe"], farbe: "#1d4ed8" }] };

test("herkunftDatei je Kontext", () => {
  assert.equal(herkunftDatei({ art: "segment", daten: "stellung" }), "stellung");
  assert.equal(herkunftDatei({ art: "kreis", daten: "stellung" }), "berufe");
  assert.equal(herkunftDatei({ art: "kreis", daten: "gruppe" }), "berufe");
  assert.equal(herkunftDatei({ art: "kreis", daten: "besitz" }), "eigentuemer");
  assert.equal(herkunftDatei({ art: "kreis", daten: "gewerbe" }), "rubriken");
  assert.equal(herkunftDatei({ art: "regel", daten: "besitz" }), "besitz");
  assert.equal(herkunftDatei({ art: "einheit", daten: "stellung" }), null);
  assert.equal(herkunftDatei({ art: "ausgeschlossen", daten: "stellung" }), null);
});

test("herkunftPfad: Segment Stellung mit Quellmarken und Top-Schreibweisen", () => {
  const p = herkunftPfad({ art: "segment", daten: "stellung", id: "Arbeiter/Gehilfen", gruppe: G_ST }, H_ST, A_ST);
  assert.deepEqual(p.map((s) => [s.label, s.wert]), [["Buch", "534 Schreibweisen"], ["OhdAB", "419 Berufe"], ["Stellung", "Arbeiter"], ["Gruppe", "Arbeiter/Gehilfen"]]);
  assert.deepEqual(p[2].marken, [{ art: "hand", anteil: 0.9379, zahl: 70000 }, { art: "vorschlag", anteil: 0.0621, zahl: 4635 }]);
  assert.deepEqual(p.beispiele, [["Bergm.", 27781], ["Arbeiter", 8432], ["Schlosser", 7193]]);
});

test("herkunftPfad: Gruppe aus mehreren Klassen summiert (Review Focus 1), fehlende Klasse zählt 0 (Review Focus 2)", () => {
  const g = A_ST.gruppen[1];
  const p = herkunftPfad({ art: "segment", daten: "stellung", id: "Bürgertum", gruppe: g }, H_ST, A_ST);
  assert.equal(p[0].wert, "320 Schreibweisen"); assert.equal(p[1].wert, "230 Berufe");
  assert.equal(p[2].wert, "Beamte, Angestellte, Freie Berufe");          // freie_berufe fehlt in der Datei → 0, aber genannt
  assert.deepEqual(p[2].marken.map((m) => [m.art, m.zahl]), [["hand", 22444], ["vorschlag", 604]]);
  assert.deepEqual(p.beispiele, [["Angest.", 5000], ["Lehrer", 900]]);  // über beide Klassen neu sortiert
  assert.ok(!JSON.stringify(p).includes("undefined"));
});

test("herkunftPfad: Kreis Beruf, Kreis Eigentümer, Kreis Rubrik, Regel-Teil; unbekannte id → leer (Review Focus 3)", () => {
  const berufe = { "B 21112-100": { norm: "Bergmann", nennungen: 24913, schreibweisen: [["Bergm.", 24700], ["Bergmann", 213]], stellung: "arbeiter", stellung_quelle: "hand" } };
  const k = herkunftPfad({ art: "kreis", daten: "stellung", id: "B 21112-100", gruppe: null }, berufe, A_ST);
  assert.deepEqual(k.map((s) => [s.label, s.wert]), [["Buch", "2 Schreibweisen"], ["OhdAB", "Bergmann"], ["Stellung", "Arbeiter"], ["Gruppe", "Arbeiter/Gehilfen"]]);
  assert.deepEqual(k[2].marken, [{ art: "hand", anteil: 1, zahl: 24913 }]);
  assert.deepEqual(herkunftPfad({ art: "kreis", daten: "stellung", id: "B 99999-000", gruppe: null }, berufe, A_ST), []);
  const eig = { "Fried. Krupp AG": { schreibweisen: [["Fried. Krupp A.G.", 257], ["Fried. Krupp A. G.", 181]], schreibweisen_gesamt: 60, zeilen: 733, haeuser: 3351, spanne: 2600, nummer: 18, kategorie: "industrie", identitaet: true, seite: "II-040" } };
  const AB = { daten: "besitz", gruppen: [{ name: "Zechen und Werke", aus: ["bergbau", "industrie"], farbe: "#111" }, { name: "Privatpersonen", aus: ["privatperson"], farbe: "#d97706" }] };
  const e = herkunftPfad({ art: "kreis", daten: "besitz", id: "Fried. Krupp AG", gruppe: null }, eig, AB);
  assert.deepEqual(e.map((s) => [s.label, s.wert]), [["Buch", "60 Schreibweisen"], ["Eigentümer", "Fried. Krupp AG"], ["Klasse", "Industrie"], ["Gruppe", "Zechen und Werke"]]);
  assert.equal(e.zusatz, "733 Zeilen im Häuserbuch, 2.618 Häuser dazu über Hausnummernspannen und gleiche Nummern");
  const rub = { Bäcker: { betriebe: 518, gruppe: "lebensmittel", art: "handwerk", quelle: "hand" } };
  const AG = { daten: "gewerbe", gruppen: [{ name: "Lebensmittel", aus: ["lebensmittel"], farbe: "#d62728" }] };
  const r = herkunftPfad({ art: "kreis", daten: "gewerbe", id: "Bäcker", gruppe: null }, rub, AG);
  assert.deepEqual(r.map((s) => [s.label, s.wert]), [["Buch", "Bäcker"], ["Branche", "Lebensmittel und Genussmittel · Handwerk"], ["Gruppe", "Lebensmittel"]]);
  assert.deepEqual(r[1].marken, [{ art: "hand", anteil: 1, zahl: 518 }]);
  const besitz = { privatperson: { eigentuemer: 300, zeilen: 41000, haeuser: 40800, quelle: { hand: 8275, regel: 32525 }, spanne: 0, nummer: 0, top: [], regel_beispiele: [["Müller, H.", 12]] } };
  const rg = herkunftPfad({ art: "regel", daten: "besitz", id: "Privatpersonen#regel", gruppe: AB.gruppen[1] }, besitz, AB);
  assert.deepEqual(rg.map((s) => [s.label, s.wert]), [["Buch", "Person ohne Firmenname"], ["Regel", "→ Privatperson"], ["Gruppe", "Privatpersonen"]]);
  assert.deepEqual(rg[1].marken, [{ art: "regel", anteil: 1, zahl: 32525 }]);
  assert.equal(rg.hinweis, "keine Handprüfung, keine Identität");
});

test("herkunftTabelle und herkunftLink", () => {
  const t = herkunftTabelle({ art: "segment", daten: "stellung", id: "Arbeiter/Gehilfen", gruppe: G_ST }, H_ST, A_ST);
  assert.deepEqual(t.kopf, ["Schreibweise", "Nennungen", "OhdAB", "Quelle"]);
  assert.deepEqual(t.zeilen[0], ["Bergm.", 27781, "Bergmann", "hand"]); assert.equal(t.gesamt, 534);
  assert.match(t.hinweis, /Berufszählung 1933/); assert.match(t.hinweis, /berufe\.csv/);
  const viele = { x: { ...H_ST.arbeiter, top: Array.from({ length: 12 }, (_, i) => [`S${i}`, 100 - i, "N", "hand"]) } };
  assert.equal(herkunftTabelle({ art: "segment", daten: "stellung", id: "G", gruppe: { name: "G", aus: ["x"] } }, viele, { daten: "stellung", gruppen: [] }).zeilen.length, 10);
  assert.equal(herkunftLink({ art: "kreis", daten: "stellung", id: "B 21112-100" }), "karte.html?ohdab=B%2021112-100");
  assert.equal(herkunftLink({ art: "kreis", daten: "besitz", id: "Fried. Krupp AG" }), "karte.html?eigentuemer=Fried.%20Krupp%20AG");
  assert.equal(herkunftLink({ art: "kreis", daten: "gewerbe", id: "Bäcker" }), "karte.html?q=B%C3%A4cker");
  assert.equal(herkunftLink({ art: "segment", daten: "stellung", id: "Arbeiter/Gehilfen" }), null);
  const eig = { "Fried. Krupp AG": { schreibweisen: [["Fried. Krupp A.G.", 257]], schreibweisen_gesamt: 60, zeilen: 733, haeuser: 3351, spanne: 2600, nummer: 18, kategorie: "industrie", identitaet: true, seite: "II-040" } };
  const te = herkunftTabelle({ art: "kreis", daten: "besitz", id: "Fried. Krupp AG", gruppe: null }, eig, { daten: "besitz", gruppen: [] });
  assert.deepEqual(te.kopf, ["Schreibweise im Buch", "Zeilen", "Quelle"]); assert.deepEqual(te.zeilen[0], ["Fried. Krupp A.G.", 257, "hand"]);
  assert.match(te.hinweis, /733 Zeilen ergeben 3\.351 Häuser/); assert.equal(te.seite, "II-040");
  assert.equal(herkunftTabelle({ art: "einheit", daten: "stellung", id: "Katernberg" }, H_ST, A_ST), null);
});

test("herkunftAktuell: Pfad nur, wenn der Kasten noch dieselbe Einheit zeigt (Review Focus 4)", () => {
  assert.equal(herkunftAktuell({ id: "Arbeiter", sichtbar: true }, "Arbeiter"), true);
  assert.equal(herkunftAktuell({ id: "Beamte", sichtbar: true }, "Arbeiter"), false);
  assert.equal(herkunftAktuell({ id: "Arbeiter", sichtbar: false }, "Arbeiter"), false);
});

test("detailTextGruppe: Regel-Teil (#regel) heißt „per Regel“ und nennt den Regel-Anteil", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", form: "balken", gruppen: [{ name: "Privat", aus: ["privatperson"], farbe: "#000" }], bezug: "Privat" });
  const werte = [{ id: "K", N: 90, n_aus: 10, zaehler: { Privat: 90 }, regel: 70 }];
  const d = detailTextGruppe("Privat#regel", werte, a);
  assert.equal(d.titel, "Privat · per Regel");
  assert.equal(d.zeilen[0], "70 von 90 Privat nur per Regel klassifiziert (78 %)");
});
```

`site/tests/formen.test.js`, im Test „balken: Regel-Anteil der Privatpersonen schraffiert …“ die Zeile mit `data-id="Privat"`-Zählung ersetzen:

```js
  assert.equal((r.svg.match(/data-id="Privat"/g) || []).length, 1);
  assert.equal((r.svg.match(/data-id="Privat#regel"/g) || []).length, 1);
```
und die Breitenprüfung auf beide ids anpassen:
```js
  const bv = Number(r.svg.match(/data-id="Privat"[^>]*width="([\d.]+)"/)[1]);
  const br = Number(r.svg.match(/data-id="Privat#regel"[^>]*width="([\d.]+)"/)[1]);
  assert.ok(Math.abs(br / (bv + br) - 7 / 15) < 0.01, "schraffierter Teil = Regel-Anteil");
```
(die Variable `b` und ihre Zeile entfallen).

- [ ] **Step 2: Tests laufen lassen, Fehlschlag sehen**

Run: `cd site && node --test tests/`
Expected: FAIL (Exporte fehlen; Balken-Test findet `#regel` nicht).

- [ ] **Step 3: Balken und Lader**

`site/js/formen/balken.js`, in `balkenZeile` beim schraffierten Rechteck die id ergänzen (nur, wenn nicht `jeEinheit`):

```js
    if (regelB > 0) {
      const id = schraffurId(seg.id);
      if (!muster.some((m) => m.id === id)) muster.push({ id, farbe: seg.farbe });
      const kopfRegel = jeEinheit ? `<rect class="segment"` : `<rect class="einheit" data-id="${esc(seg.id)}#regel"`;
      teile.push(`${kopfRegel} x="${r2(px + b - regelB)}" y="${r2(y)}" width="${r2(regelB)}" height="${r2(hoehe)}" fill="url(#${id})"><title>${esc(titel)}</title></rect>`);
    }
```

`site/js/daten.js`, in der `Lader`-Klasse nach `kapitel(id)`:

```js
  herkunft(name) { return this.json(`herkunft/${name}.json`); }
```

- [ ] **Step 4: Modell**

`site/js/perspektiven_modell.js` — am Ende anhängen (Import von `formatZahl`, `formatProzent` steht schon oben; prüfen, sonst aus `./formen/skalen.js` ergänzen):

```js
// ---- Herkunftspfad (Spec 2026-09-27 Herkunftspfad §4) ----------------------------------------------

// Welche Datei aus site/daten/herkunft/ ein Kontext braucht. Einheiten (Stadtteil, Straße, Hex) und das
// Ausschluss-Segment haben keinen Pfad.
export const HERKUNFT_DATEI = {
  segment: { stellung: "stellung", gruppe: "gruppe", niveau: "niveau", besitz: "besitz", gewerbe: "gewerbe" },
  regel: { besitz: "besitz" },
  kreis: { stellung: "berufe", gruppe: "berufe", niveau: "berufe", besitz: "eigentuemer", gewerbe: "rubriken" },
};
export function herkunftDatei(kontext) {
  const k = kontext || {};
  return (HERKUNFT_DATEI[k.art] || {})[k.daten] || null;
}

// Beschriftungen der Klassen, wie die Kapitel sie nennen (Rohwert → Anzeige).
export const KLASSEN = {
  stellung: { arbeiter: "Arbeiter", angestellte: "Angestellte", beamte: "Beamte", selbstaendige: "Selbständige", freie_berufe: "Freie Berufe",
    unternehmer: "Unternehmer", ohne_erwerb: "Ohne Erwerbsberuf", kaufleute: "Kaufleute", unbestimmt: "unbestimmt" },
  besitz: { privatperson: "Privatperson", stadt_staat: "Stadt und Staat", bergbau: "Bergbau", industrie: "Industrie", genossenschaft_siedlung: "Genossenschaft und Siedlung",
    kirche_stiftung: "Kirche und Stiftung", bank_versicherung: "Bank und Versicherung", sonstige: "Sonstige", gemischt: "gemischt" },
  gewerbe: { bergbau: "Bergbau und Kokerei", metall_maschinen: "Metall, Maschinen, Elektro", bau: "Bau", holz_moebel: "Holz und Möbel", textil_bekleidung: "Textil und Bekleidung",
    lebensmittel: "Lebensmittel und Genussmittel", handel: "Handel (übrige Waren)", gastgewerbe: "Gastgewerbe", verkehr_bahn_post: "Verkehr, Bahn, Post",
    finanzen_recht: "Banken, Versicherungen, Immobilien, Beratung", verwaltung: "Verwaltung, Polizei, Recht", bildung_kultur_kirche: "Bildung, Kultur, Medien, Kirche",
    gesundheit: "Gesundheit", haus_reinigung: "Haushalt, Reinigung, Körperpflege", sonstige: "Sonstige" },
  art: { handwerk: "Handwerk", handel: "Handel", industrie: "Industrie", dienstleistung: "Dienstleistung", gastgewerbe: "Gastgewerbe", freier_beruf: "Freier Beruf", sonstige: "Sonstige" },
};
const klasseText = (daten, roh) => (KLASSEN[daten === "gruppe" || daten === "niveau" ? "stellung" : daten] || {})[roh] || roh;

// Belegtexte je Datenkern: Regel und Kuratierungstabelle in Worten.
export const BELEG = {
  stellung: "Stellung nach Berufszählung 1933 / AVG 1911 (docs/stellung.md). Tabelle: kuratierung/berufe.csv, Spalte stellung.",
  gruppe: "Hauptgruppe = OhdAB-Gattung (KldB 2010, 2-stellig), kuratierung/hauptgruppen.csv. Tabelle: kuratierung/berufe.csv, Spalte ohdab_id.",
  niveau: "Anforderungsniveau der OhdAB je Norm; „unsicher“ bei Betriebsangaben statt Beruf. Tabelle: kuratierung/berufe.csv.",
  besitz: "Klasse je Eigentümer von Hand (kuratierung/eigentuemer.csv); Personen ohne Firmenname per Regel Privatperson. Spannen des Häuserbuchs gelten je Straßenseite.",
  gewerbe: "Branche und Betriebsform je Rubrik nach docs/gewerbe.md. Tabelle: kuratierung/gewerbe.csv, Spalten gruppe, art, geprueft.",
};

// Quellmarken in fester Reihenfolge; nur mit Zahl > 0.
const QUELLEN = ["hand", "vorschlag", "claude", "regel"];
function marken(quelle) {
  const q = quelle || {};
  const summe = QUELLEN.reduce((s, a) => s + (q[a] || 0), 0);
  return QUELLEN.filter((a) => (q[a] || 0) > 0).map((a) => ({ art: a, anteil: summe ? Math.round((q[a] / summe) * 10000) / 10000 : 0, zahl: q[a] }));
}

// Summe mehrerer Klassen (Gruppe aus mehreren Rohwerten): Zähler addieren, Quellen addieren, Top-Listen
// zusammenlegen und neu sortieren. Fehlende Klassen zählen 0.
function summeKlassen(herkunft, aus) {
  const k = { schreibweisen: 0, normen: 0, nennungen: 0, eigentuemer: 0, zeilen: 0, haeuser: 0, rubriken: 0, betriebe: 0, quelle: {}, top: [] };
  for (const roh of aus || []) {
    const h = (herkunft || {})[roh];
    if (!h) continue;
    for (const f of ["schreibweisen", "normen", "nennungen", "eigentuemer", "zeilen", "haeuser", "rubriken", "betriebe"]) k[f] += h[f] || 0;
    for (const [a, z] of Object.entries(h.quelle || {})) k.quelle[a] = (k.quelle[a] || 0) + z;
    k.top.push(...(h.top || []));
  }
  k.top.sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])));
  return k;
}

const gruppeVon = (ansicht, roh) => (ansicht?.gruppen || []).find((g) => Array.isArray(g.aus) && g.aus.includes(roh));

// Die Brotkrumen-Kette für einen Kontext; zusätzlich `beispiele` (Top-3-Schreibweisen), `zusatz`
// (Eigentümer: Zeilen → Häuser) und `hinweis` (Regel). Leer, wenn die Datei den Schlüssel nicht kennt.
export function herkunftPfad(kontext, herkunft, ansicht) {
  const k = kontext || {};
  const pfad = [];
  if (!herkunft) return pfad;
  if (k.art === "segment" && k.gruppe) {
    const s = summeKlassen(herkunft, k.gruppe.aus);
    const klassen = k.gruppe.aus.map((r) => klasseText(k.daten, r)).join(", ");
    if (k.daten === "besitz") {
      pfad.push({ label: "Buch", wert: `${formatZahl(s.zeilen)} Zeilen im Häuserbuch` }, { label: "Eigentümer", wert: `${formatZahl(s.eigentuemer)} zusammengeführt` },
        { label: "Klasse", wert: klassen, marken: marken(s.quelle) }, { label: "Gruppe", wert: k.gruppe.name });
    } else if (k.daten === "gewerbe") {
      pfad.push({ label: "Buch", wert: `${formatZahl(s.rubriken)} Rubriken` }, { label: "Branche", wert: klassen, marken: marken(s.quelle) }, { label: "Gruppe", wert: k.gruppe.name });
    } else {
      const stufe = k.daten === "gruppe" ? "Hauptgruppe" : k.daten === "niveau" ? "Niveau" : "Stellung";
      pfad.push({ label: "Buch", wert: `${formatZahl(s.schreibweisen)} Schreibweisen` }, { label: "OhdAB", wert: `${formatZahl(s.normen)} Berufe` },
        { label: stufe, wert: klassen, marken: marken(s.quelle) }, { label: "Gruppe", wert: k.gruppe.name });
    }
    pfad.beispiele = s.top.slice(0, 3).map((t) => [t[0], t[1]]);
    return pfad;
  }
  if (k.art === "regel" && k.gruppe) {
    const s = summeKlassen(herkunft, ["privatperson"]);
    pfad.push({ label: "Buch", wert: "Person ohne Firmenname" }, { label: "Regel", wert: "→ Privatperson", marken: marken({ regel: s.quelle.regel || 0 }) }, { label: "Gruppe", wert: k.gruppe.name });
    pfad.hinweis = "keine Handprüfung, keine Identität";
    pfad.beispiele = (herkunft.privatperson?.regel_beispiele || []).slice(0, 3);
    return pfad;
  }
  if (k.art === "kreis") {
    const h = herkunft[k.id];
    if (!h) return pfad;
    if (k.daten === "besitz") {
      const g = gruppeVon(ansicht, h.kategorie);
      pfad.push({ label: "Buch", wert: `${formatZahl(h.schreibweisen_gesamt)} Schreibweisen` }, { label: "Eigentümer", wert: k.id },
        { label: "Klasse", wert: klasseText("besitz", h.kategorie), marken: marken({ hand: h.haeuser }) }, { label: "Gruppe", wert: g ? g.name : klasseText("besitz", h.kategorie) });
      const dazu = h.haeuser - h.zeilen;
      if (dazu > 0) pfad.zusatz = `${formatZahl(h.zeilen)} Zeilen im Häuserbuch, ${formatZahl(dazu)} Häuser dazu über Hausnummernspannen und gleiche Nummern`;
      pfad.beispiele = (h.schreibweisen || []).slice(0, 3);
      return pfad;
    }
    if (k.daten === "gewerbe") {
      const g = gruppeVon(ansicht, h.gruppe);
      pfad.push({ label: "Buch", wert: k.id }, { label: "Branche", wert: `${klasseText("gewerbe", h.gruppe)} · ${klasseText("art", h.art)}`, marken: marken({ [h.quelle]: h.betriebe }) },
        { label: "Gruppe", wert: g ? g.name : klasseText("gewerbe", h.gruppe) });
      return pfad;
    }
    const g = gruppeVon(ansicht, h.stellung);
    pfad.push({ label: "Buch", wert: `${formatZahl((h.schreibweisen || []).length)} Schreibweisen` }, { label: "OhdAB", wert: h.norm },
      { label: "Stellung", wert: klasseText("stellung", h.stellung), marken: marken({ [h.stellung_quelle || "hand"]: h.nennungen }) },
      { label: "Gruppe", wert: g ? g.name : klasseText("stellung", h.stellung) });
    pfad.beispiele = (h.schreibweisen || []).slice(0, 3);
    return pfad;
  }
  return pfad;
}

// Belegtabelle für den festgestellten Kasten: Kopf, höchstens zehn Zeilen, Gesamtzahl, Hinweis.
export function herkunftTabelle(kontext, herkunft, ansicht) {
  const k = kontext || {};
  if (!herkunft || !["segment", "kreis", "regel"].includes(k.art)) return null;
  if (k.art === "segment" && k.gruppe) {
    const s = summeKlassen(herkunft, k.gruppe.aus);
    if (k.daten === "besitz") return { kopf: ["Eigentümer", "Häuser"], zeilen: s.top.slice(0, 10).map((t) => [t[0], t[1]]), gesamt: s.eigentuemer, hinweis: BELEG.besitz };
    if (k.daten === "gewerbe") return { kopf: ["Rubrik", "Betriebe", "Betriebsform", "Quelle"], zeilen: s.top.slice(0, 10).map((t) => [t[0], t[1], klasseText("art", t[2]), t[3]]), gesamt: s.rubriken, hinweis: BELEG.gewerbe };
    return { kopf: ["Schreibweise", "Nennungen", "OhdAB", "Quelle"], zeilen: s.top.slice(0, 10), gesamt: s.schreibweisen, hinweis: BELEG[k.daten] || BELEG.stellung };
  }
  if (k.art === "regel") {
    const h = herkunft.privatperson || {};
    return { kopf: ["Schreibweise im Buch", "Häuser"], zeilen: (h.regel_beispiele || []).slice(0, 10), gesamt: h.quelle?.regel || 0,
      hinweis: "Der Eigentümer steht als Person ohne Firmennamen im Häuserbuch; die Klasse folgt aus der Regel, nicht aus einer Prüfung des Einzelfalls. Ausnahmen: Firmenmuster wie „Gebr.“; „gen.“-Hofnamen zählen als Personen. Export: besitz_pruefung = regel." };
  }
  const h = herkunft[k.id];
  if (!h) return null;
  if (k.daten === "besitz") {
    return { kopf: ["Schreibweise im Buch", "Zeilen", "Quelle"], zeilen: (h.schreibweisen || []).slice(0, 10).map((t) => [t[0], t[1], "hand"]), gesamt: h.schreibweisen_gesamt,
      hinweis: h.haeuser > h.zeilen ? `${formatZahl(h.zeilen)} Zeilen ergeben ${formatZahl(h.haeuser)} Häuser, weil Spannen („2–84“) einmal je Straßenseite stehen. ${BELEG.besitz}` : BELEG.besitz,
      seite: h.seite || "" };
  }
  if (k.daten === "gewerbe") return { kopf: ["Rubrik", "Betriebe", "Betriebsform", "Quelle"], zeilen: [[k.id, h.betriebe, klasseText("art", h.art), h.quelle]], gesamt: 1, hinweis: BELEG.gewerbe };
  return { kopf: ["Schreibweise", "Nennungen", "OhdAB", "Quelle"], zeilen: (h.schreibweisen || []).slice(0, 10).map((t) => [t[0], t[1], h.norm, h.stellung_quelle || "hand"]),
    gesamt: (h.schreibweisen || []).length, hinweis: BELEG[k.daten] || BELEG.stellung };
}

// Link „alle … in der Suche“: nur für Einzelobjekte (Norm, Eigentümer, Rubrik).
export function herkunftLink(kontext) {
  const k = kontext || {};
  if (k.art !== "kreis" || !k.id) return null;
  if (k.daten === "besitz") return `karte.html?eigentuemer=${encodeURIComponent(k.id)}`;
  if (k.daten === "gewerbe") return `karte.html?q=${encodeURIComponent(k.id)}`;
  return `karte.html?ohdab=${encodeURIComponent(k.id)}`;
}

// Nach dem Nachladen darf der Pfad nur erscheinen, wenn der Kasten noch dieselbe Einheit zeigt.
export const herkunftAktuell = (detail, geladenFuer) => !!detail && detail.sichtbar === true && detail.id === geladenFuer;
```

`detailTextGruppe` erweitern — am Anfang der Funktion:

```js
export function detailTextGruppe(name, werte, ansicht, ausschlussText = "") {
  if (typeof name === "string" && name.endsWith("#regel")) {
    const basis = name.slice(0, -"#regel".length);
    const g = (ansicht?.gruppen || []).find((x) => x.name === basis);
    if (!g) return null;
    const z = werte.reduce((s, w) => s + (w.zaehler?.[basis] || 0), 0);
    const regel = werte.reduce((s, w) => s + (w.regel || 0), 0);
    return { titel: `${basis} · per Regel`, zeilen: [`${formatZahl(regel)} von ${formatZahl(z)} ${basis} nur per Regel klassifiziert (${formatProzent(z ? regel / z : 0)})`] };
  }
```
(Rest unverändert.)

- [ ] **Step 4b: Quellzeile je Einheit (Spec §4.1, Einheit)**

Test in `site/tests/perspektiven.test.js` anhängen:

```js
test("detailText: Stadtteil bei Stellung nennt den handbestimmten Anteil", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "rangliste", gruppen: [{ name: "Arbeiter", aus: ["arbeiter"], farbe: "#000" }], bezug: "Arbeiter" });
  const d = detailText({ id: "Katernberg", name: "Katernberg", N: 100, n_aus: 20, zaehler: { Arbeiter: 70 }, anteile: { Arbeiter: 0.7 }, stellung_hand: 90 }, a);
  assert.ok(d.zeilen.includes("90 von 100 Nennungen mit von Hand bestimmter Stellung (90 %)"));
  const ohne = detailText({ id: "K", name: "K", N: 100, n_aus: 0, zaehler: {}, anteile: {} }, a);
  assert.ok(!ohne.zeilen.some((z) => /von Hand bestimmter/.test(z)));
});
```

`site/js/ansicht.js:107-108` — `kennzahlen(einheit, ansicht)` gibt zusätzlich `stellung_hand` zurück:

```js
  const regel = ansicht.daten === "besitz" ? (einheit?.n_besitz_regel || 0) : 0;
  const stellung_hand = ansicht.daten === "stellung" ? (einheit?.n_stellung_hand || 0) : 0;
  return { N, n_aus, unter_min, anteile, zaehler, wert, dominant, mischung, dichte, regel, stellung_hand };
```

`detailText` in `perspektiven_modell.js`, nach der Regel-Zeile (`if (ansicht?.daten === "besitz" && e.regel > 0) …`):

```js
  // Stellung: wie viel der Einheit von Hand bestimmt ist (Rest: Vorschlag der Automatik).
  if (ansicht?.daten === "stellung" && e.stellung_hand > 0) zeilen.push(`${formatZahl(e.stellung_hand)} von ${formatZahl(e.N)} Nennungen mit von Hand bestimmter Stellung (${formatProzent(e.N ? e.stellung_hand / e.N : 0)})`);
```

Prüfen, ob `site/tests/ansicht.test.js` die Rückgabe von `kennzahlen` per `deepEqual` vergleicht; wenn ja, dort `stellung_hand: 0` ergänzen.

- [ ] **Step 5: Tests laufen lassen**

Run: `cd site && node --test tests/`
Expected: alle PASS. Stimmt `p[2].marken[0].anteil` nicht auf vier Stellen (0.9379), Rundung in `marken` prüfen: `Math.round(x * 10000) / 10000`.

- [ ] **Step 6: Commit**

```bash
git add site/js/perspektiven_modell.js site/js/formen/balken.js site/js/daten.js site/js/ansicht.js site/tests/
git commit -m "feat(schlaglichter): Modell des Herkunftspfads — Kette je Kontext, Quellmarken, Belegtabelle, Suchlink; Regel-Teil im Balken als eigene Einheit

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Seite — Nachladen, Pfad beim Schweben, Beleg beim Klick, CSS

**Files:**
- Modify: `site/js/perspektiven.js` (`zeichneDetail`, neu `kontextVon`, `ladeHerkunft`, `pfadHtml`, `tabelleHtml`)
- Modify: `site/css/perspektiven.css`

Browsercode; die Regeln sind in Task 2 getestet. Sichtprüfung ist Teil der Task.

- [ ] **Step 1: Imports und Zustand**

In `site/js/perspektiven.js` den Modell-Import um `herkunftAktuell, herkunftDatei, herkunftLink, herkunftPfad, herkunftTabelle` erweitern, `faksimileUrl` aus `./popup.js` importieren, und nach `let sichtbar = [];` ergänzen:

```js
// Herkunftsdateien (site/daten/herkunft/*.json), nachgeladen beim ersten Bedarf; null = Laden fehlgeschlagen.
const herkunft = new Map();
let faksimile = null;
```

In `seiteAufbauen` nach `daten = await ladeEbenen(lader);`:
```js
  faksimile = (await lader.faksimile()) || {};
```

- [ ] **Step 2: Kontext bestimmen und Datei laden**

Vor `zeichneDetail` einfügen:

```js
// Welche Art Einheit der Kasten zeigt: Segment eines Gesamtbalkens (Gruppenname), dessen Regel-Teil,
// Kreis einer Bubbles-Ansicht (Norm, Eigentümer, Rubrik), sonst eine Einheit der Ebene.
function kontextVon(id, ansicht, werte) {
  if (!ansicht || gezeigt.trichter) return null;
  if (id === "ausgeschlossen") return { art: "ausgeschlossen", daten: ansicht.daten, id, gruppe: null };
  if (typeof id === "string" && id.endsWith("#regel")) {
    const g = (ansicht.gruppen || []).find((x) => x.name === id.slice(0, -"#regel".length));
    return g ? { art: "regel", daten: ansicht.daten, id, gruppe: g } : null;
  }
  const g = (ansicht.gruppen || []).find((x) => x.name === id);
  if (g) return { art: "segment", daten: ansicht.daten, id, gruppe: g };
  if (ansicht.form === "bubbles") return { art: "kreis", daten: ansicht.daten, id, gruppe: null };
  return { art: "einheit", daten: ansicht.daten, id, gruppe: null };
}

// Herkunftsdatei holen; nach dem Laden den Kasten neu zeichnen, falls er noch dieselbe Einheit zeigt.
function ladeHerkunft(name, fuerId, zeile) {
  if (herkunft.has(name)) return;
  herkunft.set(name, undefined);            // „wird geladen“
  lader.herkunft(name).then((h) => {
    herkunft.set(name, h || null);
    if (!h) console.warn(`Herkunft ${name}: nicht geladen (alter Export?)`);
    if (herkunftAktuell(detail, fuerId)) zeichneDetail(zeile);
  }).catch((e) => { herkunft.set(name, null); console.warn(`Herkunft ${name}:`, e); });
}

const MARKE = { hand: "Hand", vorschlag: "Vorschlag", claude: "Prinzipien", regel: "Regel" };
const markeHtml = (m) => `<span class="q ${esc(m.art)}">${m.anteil < 1 ? `${Math.round(m.anteil * 100)} % ` : ""}${MARKE[m.art] || m.art}</span>`;

function pfadHtml(pfad) {
  if (!pfad || !pfad.length) return "";
  const stufen = pfad.map((s) => `<span class="stufe"><small>${esc(s.label)}</small>${esc(s.wert)}${(s.marken || []).map(markeHtml).join("")}</span>`).join(`<span class="pfeil">›</span>`);
  const beispiele = pfad.beispiele && pfad.beispiele.length ? `<p class="wink">Häufigste Schreibweisen: ${pfad.beispiele.map((b) => `${esc(b[0])} (${formatZahl(b[1])})`).join(", ")}</p>` : "";
  const zusatz = pfad.zusatz ? `<p class="wink">${esc(pfad.zusatz)}</p>` : "";
  const hinweis = pfad.hinweis ? `<p class="wink">${esc(pfad.hinweis)}</p>` : "";
  return `<div class="pfad">${stufen}</div>${zusatz}${beispiele}${hinweis}`;
}

function tabelleHtml(t, kontext) {
  if (!t) return "";
  const zelle = (v, i) => t.kopf[i] === "Quelle" ? `<td>${markeHtml({ art: v, anteil: 1 })}</td>` : typeof v === "number" ? `<td class="z">${formatZahl(v)}</td>` : `<td>${esc(v)}</td>`;
  const zeilen = t.zeilen.map((z) => `<tr>${z.map(zelle).join("")}</tr>`).join("");
  const link = herkunftLink(kontext);
  const alle = t.gesamt > t.zeilen.length && link ? `<tr><td colspan="${t.kopf.length}"><a href="${esc(link)}">alle ${formatZahl(t.gesamt)} in der Suche ›</a></td></tr>` : "";
  const bild = t.seite && faksimile && faksimile[t.seite] ? ` · <a href="${esc(faksimileUrl(faksimile[t.seite]))}" target="_blank" rel="noopener">Faksimile Seite ${esc(t.seite)}</a>` : "";
  return `<details open><summary>Woher kommt diese Zahl?</summary><table><tr>${t.kopf.map((k) => `<th>${esc(k)}</th>`).join("")}</tr>${zeilen}${alle}</table>`
    + `<p class="beleg">${esc(t.hinweis)}${bild}</p></details>`;
}
```
`formatZahl` aus `./formen/skalen.js` importieren (die Datei importiert von dort schon `esc, nennerText`).

- [ ] **Step 3: `zeichneDetail` erweitern**

Nach der Zeile, die `box.innerHTML = …` setzt, und vor `box.hidden = false;` einfügen (den bestehenden `innerHTML`-Ausdruck unverändert lassen, nur anhängen):

```js
  const kontext = kontextVon(detail.id, ansicht, werte);
  const datei = herkunftDatei(kontext);
  if (datei) {
    if (!herkunft.has(datei)) ladeHerkunft(datei, detail.id, zeile);
    const h = herkunft.get(datei);
    if (h === undefined) box.insertAdjacentHTML("beforeend", `<p class="wink">Herkunft wird geladen …</p>`);
    else if (h) {
      box.insertAdjacentHTML("beforeend", pfadHtml(herkunftPfad(kontext, h, ansicht)));
      if (detail.fest) box.insertAdjacentHTML("beforeend", tabelleHtml(herkunftTabelle(kontext, h, ansicht), kontext));
    }
  }
```

Der Schließknopf wird weiterhin nach dem Füllen gebunden (`box.querySelector(".schliessen")`), das bleibt an seiner Stelle; nur die Lage (`detailLage`) muss **nach** dem Anhängen berechnet werden — prüfen, dass der Lage-Block am Ende der Funktion steht.

- [ ] **Step 4: CSS**

An `site/css/perspektiven.css` anhängen:

```css
/* Herkunftspfad im Detailkasten (Spec Herkunftspfad §4) */
.detail { max-width: 360px; }
.detail .pfad { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 6px; margin: 8px 0 2px; font-size: 12px; }
.detail .pfad .stufe { border: 1px solid var(--rand); border-radius: 6px; padding: 2px 7px; background: #fafafa; white-space: nowrap; }
.detail .pfad .stufe small { display: block; font-size: 9.5px; color: var(--grau); text-transform: uppercase; letter-spacing: .04em; }
.detail .pfad .pfeil { color: var(--grau); }
.detail .q { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 10px; margin-left: 4px; vertical-align: middle; color: #fff; }
.detail .q.hand { background: #15803d; } .detail .q.vorschlag { background: #6b7280; } .detail .q.claude { background: #6d28d9; } .detail .q.regel { background: #b45309; }
.detail details { margin-top: 8px; border-top: 1px solid var(--rand); padding-top: 6px; }
.detail summary { cursor: pointer; color: var(--blau); font-size: 12px; }
.detail table { border-collapse: collapse; width: 100%; font-size: 11.5px; margin-top: 6px; }
.detail th, .detail td { text-align: left; padding: 2px 6px 2px 0; border-bottom: 1px solid #eee; vertical-align: top; }
.detail th { color: var(--grau); font-weight: 500; font-size: 10px; text-transform: uppercase; letter-spacing: .04em; }
.detail td.z { text-align: right; font-variant-numeric: tabular-nums; color: var(--grau); }
.detail .beleg { font-size: 11px; color: var(--grau); margin-top: 6px; }
.detail.fest { max-height: 80vh; overflow: auto; }
```

- [ ] **Step 5: Sichtprüfung**

`node --check site/js/perspektiven.js`; Dev-Server (`python3 werkzeuge/serve.py 8765`), `http://localhost:8765/site/schlaglichter.html?vorschau=1`:
- Kapitel Stellung, Gesamtbalken: Schweben über „Arbeiter/Gehilfen“ → Kette mit Marken, drei Schreibweisen; Klick → Tabelle offen, Belegzeile; kein Link „alle …“ (Segment).
- Kapitel Wohneigentum, Balken: Schweben über den schraffierten Teil → „Privatpersonen · per Regel“, Kette Buch › Regel › Gruppe; Kreis „Fried. Krupp AG“ → Kette, Zusatz „733 Zeilen …“, Klick → Tabelle mit Zeilen je Schreibweise, Link „alle 60 in der Suche“, Faksimile-Link.
- Kapitel Gewerbe, Bubbles: Kreis „Bäcker“ → Kette Buch › Branche · Handwerk [Hand] › Gruppe.
- Stadtteil in einer Rangliste: Kasten wie bisher, kein Pfad.
- Kapitel 0: unverändert.
- Konsole ohne Fehler; mit umbenannter Datei (`mv site/daten/herkunft/stellung.json{,.bak}`) zeigt der Kasten die Zahlen ohne Pfad, Konsole eine Warnung; danach zurückbenennen.
- Headless-Variante: Playwright-Skript, das über `[data-id="Arbeiter/Gehilfen (nach Schreibung)"]` schwebt, 800 ms wartet und `#detail .pfad .stufe` zählt (4) sowie nach Klick `#detail table tr` (≥ 4).

- [ ] **Step 6: Commit**

```bash
git add site/js/perspektiven.js site/css/perspektiven.css
git commit -m "feat(schlaglichter): Herkunftspfad im Detailkasten — Kette beim Schweben, Beleg mit Tabelle, Suchlink und Faksimile beim Klick; Herkunft wird nachgeladen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Dokumentation

**Files:**
- Modify: `docs/perspektiven.md`, `README.md`
- Modify: `~/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Journal.md`

- [ ] **Step 1: `docs/perspektiven.md`** — neuer Abschnitt vor „Freigabe“:

```markdown
## Herkunftspfad im Detailkasten

Seit 2026-09-27 zeigt der Detailkasten, woher eine Zahl kommt (Spec `2026-09-27-herkunftspfad-design.md`).
Daten: `site/daten/herkunft/{stellung,gruppe,niveau,berufe,besitz,eigentuemer,gewerbe,rubriken}.json`
(`baue_herkunft` in `pipeline/lib/karte_export.py`, Grundmenge = verortete Einträge), nachgeladen beim ersten
Schweben (`Lader.herkunft`). Kontextarten (`kontextVon` in perspektiven.js): `segment` (Gruppe im
Gesamtbalken, Klassen werden summiert), `regel` (schraffierter Teil, `data-id` `<Gruppe>#regel`), `kreis`
(Bubbles: Norm, Eigentümer, Rubrik), `einheit` (kein Pfad), `ausgeschlossen` (kein Pfad). Schwebend: Kette
Buch › Norm/Eigentümer/Rubrik › Klasse › Gruppe mit Quellmarken (hand grün, vorschlag grau, claude
violett, regel orange) und drei häufigsten Schreibweisen (`herkunftPfad`). Festgestellt zusätzlich
„Woher kommt diese Zahl?“ mit bis zu zehn Zeilen, Link in die Suche (`herkunftLink`, nur Einzelobjekte),
Belegtext (`BELEG`) und bei Eigentümern Faksimile-Link (`herkunftTabelle`). Fehlt die Datei (alter
Export), bleibt der Kasten wie zuvor; die Konsole warnt einmal.
```

- [ ] **Step 2: README** — Ausgabetabelle um eine Zeile:

```markdown
| `herkunft/*.json` | Herkunftspaket für den Detailkasten der Schlaglichter: je Klasse Schreibweisen, Normen, Quellanteile und Top-10; je Norm/Eigentümer/Rubrik die Einzelherkunft (`docs/perspektiven.md`, Abschnitt Herkunftspfad) |
```

- [ ] **Step 3: Journal**

```markdown
## 2026-09-27 — Schlaglichter Schritt 2: Herkunftspfad

Am Mockup (build/mockups/herkunftspfad.html, drei Varianten × drei Fälle mit echten Zahlen) entschieden:
Brotkrumen beim Schweben, aufklappbarer Beleg beim Klick, Quellmarken in eigenen Farben. Umgesetzt:
Exportpaket site/daten/herkunft (Schreibweisen, Normen, Quellanteile je Klasse; Einzelherkunft je Norm,
Eigentümer, Rubrik; Grundmenge verortete Einträge), Modellfunktionen herkunftPfad/-Tabelle/-Link (getestet),
Nachladen beim ersten Schweben, Regel-Teil im Balken als eigene Einheit. Lehrstück Krupp: 733 Zeilen im
Häuserbuch ergeben 3.351 Häuser, weil Spannen einmal je Straßenseite stehen — der Pfad nennt das.
```

- [ ] **Step 4: Tests und Commit**

Run: `python3 -m pytest -q && (cd site && node --test tests/)`
Expected: alle PASS.

```bash
git add docs/perspektiven.md README.md
git commit -m "docs(perspektiven): Herkunftspfad — Paket herkunft/, Kontextarten, Beleg

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```
