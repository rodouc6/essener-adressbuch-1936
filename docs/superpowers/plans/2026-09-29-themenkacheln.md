# Themenkacheln Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bei aktivem Thema zeigt die Karte aus der Vogelperspektive alle betroffenen Adressen als feine Punkte, aus einer schlanken Kacheldatei je Thema ohne Ausdünnung.

**Architecture:** Der Export schreibt je freigegebenem Thema `site/daten/themen/<id>.pmtiles` (nur Treffer-Adressen, nur die Felder aus Filter, Schaltern und Farbregel, Zoom 9–15, `-r1`). Die Karte bekommt eine zweite Vektorquelle `thema` mit dem Ebenenpaar `thema-haus`/`thema-ungenau`; bei aktivem Thema mit Kacheln sind die Hauptpunkte unsichtbar, die Themenpunkte tragen Filter und Farbe des Themas ohne Zoomgrenze und mit zoomabhängigem Radius.

**Tech Stack:** Python 3 (Pipeline, pytest), tippecanoe, MapLibre GL + PMTiles (ES-Module ohne Bundler), node:test.

**Spec:** `docs/superpowers/specs/2026-09-29-themenkacheln-design.md`

## Global Constraints

- Präzision vor Vollständigkeit: jeder Punkt ist eine Adresse; keine Heatmap, kein Clustering (Spec §1).
- Feine Ansicht nur bei aktivem Thema, dort immer; Grundansicht und `adressen.pmtiles` unverändert (Spec §1, §2).
- Kacheldatei je Thema: `site/daten/themen/<id>.pmtiles`, Ebene `adressen`, Zoom 9–15, `-r1 --no-feature-limit --no-tile-size-limit`, nur für `freigegeben: true` (Spec §2).
- Felder je Punkt: immer `id, stufe, stadtteil, n_I, n_II, n_III`; dazu `farbe.feld` (kategorien), `m_<merkmal>` (einfach/stufen mit Merkmal), alle `<praefix><klasse>` (Spec §2).
- Thema ohne einzige Treffer-Adresse → `ValueError` im Export (Spec §2).
- Themenebenen ohne die Regel „Zoom < 12 nur n ≥ 5“; Radius `["interpolate", ["linear"], ["zoom"], 10, 1, 12, 2, 14, RADIUS]` (Spec §3).
- `PLAN_FREIGEGEBEN` bleibt `false`; kein Push ohne Nachfrage; Dev-Server `python3 werkzeuge/serve.py 8765`; Commits enden mit `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- `site/daten/` ist git-ignoriert; Datenpaket per `python3 pipeline/06_karte_export.py` (tippecanoe vorhanden).

## Review Focus

1. Thema aktiv, Datenpaket ohne `themen/<id>.pmtiles` (älterer Export): Karte muss wie heute funktionieren, kein Fehler, keine leere Karte → Test in Task 3 (`ladeThema` ohne `kacheln`) und Task 2 (`setzeThemaQuelle(null)` bei fehlendem Kachelflag).
2. Themenwechsel Bergbau → Besitz → kein Thema: Quelle wird ersetzt bzw. entfernt, Hauptpunkte wieder sichtbar, keine verwaiste Ebene → Test in Task 2 (Attrappe zählt add/remove).
3. Suche (Treffer) bei aktivem Thema: Treffer-State auf beiden Quellen, Nicht-Treffer gedimmt auch auf Themenpunkten → Test in Task 2.
4. Stilwechsel (hell/dunkel) bei aktivem Thema: Themenquelle und -ebenen werden in `ebenenAufsetzen` neu angelegt → Test in Task 2 (`ebenenAufsetzen` ruft `setzeThemaQuelle` mit dem gemerkten Thema).
5. Ebenenwechsel bei aktivem Thema (Nutzer schaltet II zu): Themenkacheln tragen `n_I/n_II/n_III`, der Filter bleibt gültig → Test in Task 1 (`thema_felder` enthält die drei Zahlen immer).

---

### Task 1: Export — schlanke Kacheldatei je freigegebenem Thema

**Files:**
- Modify: `pipeline/lib/karte_export.py` (bei `tippecanoe_befehl`, `schreibe_themen`, `schreibe_paket`)
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Consumes: `punkt_feature(a) -> Feature` (Properties mit `id, stufe, stadtteil, n_I, n_II, n_III, m_*, n_bb_*, bergbau, besitz, niveau, …`).
- Produces: `thema_felder(thema: dict) -> list[str]`, `thema_adressen(thema: dict, features: list[dict]) -> list[dict]`, `thema_geojson(thema, features) -> dict`, `tippecanoe_thema_befehl(geojson: Path, pmtiles: Path) -> list[str]`, `schreibe_themen(quelle, ausgabe, features=None, kacheln=False) -> list[dict]` (Index-Einträge mit `kacheln: bool`).

- [ ] **Step 1: Failing tests schreiben**

An `tests/test_karte_export.py` anhängen:

```python
def _pf(**p):
    basis = dict(id="a", stufe="haus", stadtteil="Kray", n_I=0, n_II=0, n_III=0)
    basis.update(p)
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [7.0, 51.4]}, "properties": basis}


BB = dict(id="bergbau", titel="Bergbau", freigegeben=True, filter=dict(ebenen=["I"]), farbe=dict(art="kategorien", feld="bergbau", werte={}),
          schalter=dict(praefix="n_bb_", klassen=["leitung", "belegschaft"], namen={}))
BESITZ = dict(id="besitz", freigegeben=True, filter=dict(ebenen=["II"]), farbe=dict(art="kategorien", feld="besitz", werte={}))
AKAD = dict(id="akademiker", freigegeben=True, filter=dict(merkmal="akademiker", ebenen=["I"]), farbe=dict(art="einfach", wert="#000"))


def test_thema_felder_aus_filter_schaltern_und_farbe():
    from pipeline.lib.karte_export import thema_felder
    assert thema_felder(BB) == ["id", "stufe", "stadtteil", "n_I", "n_II", "n_III", "bergbau", "n_bb_leitung", "n_bb_belegschaft"]
    assert thema_felder(BESITZ) == ["id", "stufe", "stadtteil", "n_I", "n_II", "n_III", "besitz"]
    assert thema_felder(AKAD) == ["id", "stufe", "stadtteil", "n_I", "n_II", "n_III", "m_akademiker"]


def test_thema_adressen_filtert_nach_ebenen_merkmal_und_schaltern():
    from pipeline.lib.karte_export import thema_adressen
    f = [_pf(id="1", n_I=3, n_bb_belegschaft=2, bergbau="belegschaft"), _pf(id="2", n_I=3), _pf(id="3", n_II=1, n_bb_leitung=1),
         _pf(id="4", n_II=2, besitz="bergbau"), _pf(id="5", n_I=1, m_akademiker=1)]
    assert [x["properties"]["id"] for x in thema_adressen(BB, f)] == ["1"]          # Ebene I und ein Schalterfeld > 0
    assert [x["properties"]["id"] for x in thema_adressen(BESITZ, f)] == ["3", "4"]  # Ebene II
    assert [x["properties"]["id"] for x in thema_adressen(AKAD, f)] == ["5"]         # Ebene I und Merkmal


def test_thema_geojson_traegt_nur_die_themenfelder_und_meldet_leere_themen():
    from pipeline.lib.karte_export import thema_geojson
    f = [_pf(id="1", n_I=3, n_bb_belegschaft=2, bergbau="belegschaft", strasse_heute="Grenzstraße", besitz="privatperson")]
    g = thema_geojson(BB, f)
    assert g["type"] == "FeatureCollection" and len(g["features"]) == 1
    assert g["features"][0]["properties"] == dict(id="1", stufe="haus", stadtteil="Kray", n_I=3, n_II=0, n_III=0, bergbau="belegschaft", n_bb_belegschaft=2)
    assert g["features"][0]["geometry"] == f[0]["geometry"]
    with pytest.raises(ValueError, match="bergbau"):
        thema_geojson(BB, [_pf(id="2", n_I=3)])


def test_tippecanoe_thema_befehl_ohne_ausduennung():
    from pipeline.lib.karte_export import tippecanoe_thema_befehl
    b = tippecanoe_thema_befehl(pathlib.Path("t.geojson"), pathlib.Path("t.pmtiles"))
    assert b[0] == "tippecanoe" and "-r1" in b and "--minimum-zoom=9" in b and "--maximum-zoom=15" in b
    assert "--no-feature-limit" in b and "--no-tile-size-limit" in b and "--drop-densest-as-needed" not in b
    assert "-L" in b and "adressen:t.geojson" in b and "t.pmtiles" in b


def test_schreibe_themen_mit_kacheln_schreibt_geojson_und_index(tmp_path, monkeypatch):
    from pipeline.lib import karte_export
    q = tmp_path / "q"; q.mkdir()
    (q / "bergbau.json").write_text(json.dumps(BB), encoding="utf-8")
    (q / "a.json").write_text('{"id": "a", "titel": "A"}', encoding="utf-8")
    aufrufe = []
    monkeypatch.setattr(karte_export.subprocess, "run", lambda cmd, check: aufrufe.append(cmd))
    f = [_pf(id="1", n_I=3, n_bb_belegschaft=2, bergbau="belegschaft")]
    idx = karte_export.schreibe_themen(q, tmp_path / "out", features=f, kacheln=True)
    assert idx == [dict(id="a", titel="A", freigegeben=False, kacheln=False), dict(id="bergbau", titel="Bergbau", freigegeben=True, kacheln=True)]
    assert (tmp_path / "out" / "themen" / "bergbau.geojson").exists()
    assert json.loads((tmp_path / "out" / "themen" / "index.json").read_text(encoding="utf-8")) == idx
    assert len(aufrufe) == 1 and str(tmp_path / "out" / "themen" / "bergbau.pmtiles") in aufrufe[0]
    # ohne kacheln: kein tippecanoe, Index ohne Kachelflag true
    aufrufe.clear()
    idx2 = karte_export.schreibe_themen(q, tmp_path / "out2", features=f, kacheln=False)
    assert aufrufe == [] and all(e["kacheln"] is False for e in idx2)
```

Den bestehenden `test_schreibe_themen` anpassen: beide erwarteten Index-Einträge bekommen zusätzlich `kacheln=False`.

- [ ] **Step 2: Tests laufen lassen, Fehlschlag sehen**

Run: `python3 -m pytest -q tests/test_karte_export.py -k "thema or schreibe_themen"`
Expected: FAIL mit `ImportError: cannot import name 'thema_felder'` (und der alte `test_schreibe_themen` schlägt wegen des fehlenden `kacheln`-Feldes fehl, sobald er angepasst ist).

- [ ] **Step 3: Implementierung in `pipeline/lib/karte_export.py`**

Nach `tippecanoe_befehl` einfügen:

```python
FELDER_IMMER = ["id", "stufe", "stadtteil", "n_I", "n_II", "n_III"]


def thema_felder(thema: dict) -> list[str]:
    """Felder je Punkt in der Kacheldatei eines Themas (Spec Themenkacheln §2): Filterfelder der Karte,
    Farbfeld bzw. Merkmalsfeld, Schalterfelder — sonst nichts."""
    felder = list(FELDER_IMMER)
    f = thema.get("farbe") or {}
    fi = thema.get("filter") or {}
    if f.get("art") == "kategorien" and f.get("feld"):
        felder.append(f["feld"])
    merkmal = f.get("merkmal") or fi.get("merkmal")
    if merkmal:
        felder.append(f"m_{merkmal}")
    s = thema.get("schalter") or {}
    felder += [f"{s.get('praefix', '')}{k}" for k in s.get("klassen", [])]
    return felder


def thema_adressen(thema: dict, features: list[dict]) -> list[dict]:
    """Adresspunkte, die ein Thema betrifft: Summe der Themen-Ebenen > 0, bei Merkmal m_<merkmal> > 0,
    bei Schaltern mindestens ein Schalterfeld > 0."""
    fi = thema.get("filter") or {}
    ebenen = fi.get("ebenen") or ["I", "II", "III"]
    merkmal = (thema.get("farbe") or {}).get("merkmal") or fi.get("merkmal")
    s = thema.get("schalter") or {}
    schalter = [f"{s.get('praefix', '')}{k}" for k in s.get("klassen", [])]
    aus = []
    for ft in features:
        p = ft["properties"]
        if sum(p.get(f"n_{e}", 0) or 0 for e in ebenen) <= 0:
            continue
        if merkmal and not (p.get(f"m_{merkmal}", 0) or 0) > 0:
            continue
        if schalter and not any((p.get(k, 0) or 0) > 0 for k in schalter):
            continue
        aus.append(ft)
    return aus


def thema_geojson(thema: dict, features: list[dict]) -> dict:
    """FeatureCollection der Themenkacheln: nur Treffer-Adressen, nur die Themenfelder. Ein Thema ohne
    Treffer ist ein Fehler — sonst zeigte die Karte still nichts."""
    felder = thema_felder(thema)
    treffer = thema_adressen(thema, features)
    if not treffer:
        raise ValueError(f"Thema '{thema.get('id')}': keine Adresse trägt seine Felder {felder[len(FELDER_IMMER):]}")
    aus = [{"type": "Feature", "geometry": ft["geometry"],
            "properties": {k: ft["properties"][k] for k in felder if k in ft["properties"]}} for ft in treffer]
    return {"type": "FeatureCollection", "features": aus}


def tippecanoe_thema_befehl(geojson: Path, pmtiles: Path) -> list[str]:
    return ["tippecanoe", "-o", str(pmtiles), "--force", "--minimum-zoom=9", "--maximum-zoom=15", "-r1",
            "--no-feature-limit", "--no-tile-size-limit", "--quiet", "-L", f"adressen:{geojson}"]
```

`schreibe_themen` ersetzen:

```python
def schreibe_themen(quelle: Path, ausgabe: Path, features: list[dict] | None = None, kacheln: bool = False) -> list[dict]:
    """Kopiert die Thema-Definitionen aus kuratierung/themen/*.json nach ausgabe/themen/ und schreibt dort
    index.json (id, titel, freigegeben, kacheln). Mit `features` (Adresspunkte aus punkt_feature) und
    `kacheln=True` entsteht je freigegebenem Thema ausgabe/themen/<id>.geojson und <id>.pmtiles
    (Spec Themenkacheln §2); das GeoJSON bleibt als Zwischenstand liegen (site/daten/ ist nicht versioniert)."""
    index = []
    for pfad in sorted(Path(quelle).glob("*.json")):
        t = json.loads(pfad.read_text(encoding="utf-8"))
        _json(ausgabe / "themen" / pfad.name, t)
        frei = bool(t.get("freigegeben"))
        mit_kacheln = False
        if frei and features is not None and kacheln:
            geo = ausgabe / "themen" / f"{t['id']}.geojson"
            _json(geo, thema_geojson(t, features))
            subprocess.run(tippecanoe_thema_befehl(geo, ausgabe / "themen" / f"{t['id']}.pmtiles"), check=True)
            mit_kacheln = True
        index.append(dict(id=t["id"], titel=t.get("titel", ""), freigegeben=frei, kacheln=mit_kacheln))
    _json(ausgabe / "themen" / "index.json", index)
    return index
```

In `schreibe_paket`: den Aufruf `if themen is not None: schreibe_themen(themen, ausgabe)` **entfernen** und nach der Zeile `_json(ausgabe / "adressen.geojson", geo)` einfügen:

```python
    if themen is not None:
        schreibe_themen(themen, ausgabe, features=geo["features"], kacheln=kacheln)
```


- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest -q tests/test_karte_export.py`
Expected: PASS, alle Tests der Datei.

- [ ] **Step 5: Gesamtsuite und Commit**

Run: `python3 -m pytest -q`
Expected: 446 + 5 passed (7 deselected).

```bash
git add pipeline/lib/karte_export.py tests/test_karte_export.py
git commit -m "feat(export): Kacheldatei je freigegebenem Thema — nur Treffer-Adressen und Themenfelder, ohne Ausdünnung (themen/<id>.pmtiles, Index mit kacheln)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Karte — Themenquelle, Ebenenpaar, Filter ohne Zoomgrenze, Radius, Treffer

**Files:**
- Modify: `site/js/karte.js` (Konstanten oben; `_eigeneQuellen`; neue Methoden `_themaQuelle`, `_themaEbenen`, `setzeThemaQuelle`; `ebenenAufsetzen`; `setzeFilter`; `_deckkraftSetzen`; `setzeTreffer`)
- Test: `site/tests/karte_ebenen.test.js`

**Interfaces:**
- Consumes: nichts aus Task 1 zur Laufzeit (die Datei `themen/<id>.pmtiles` liegt im Datenpaket).
- Produces: `Karte.prototype.setzeThemaQuelle(id: string | null)`; `Karte.prototype._themaEbenen() -> layer[]` (rein, für Tests); Eigenschaft `this.themaId`.

- [ ] **Step 1: Failing tests schreiben**

An `site/tests/karte_ebenen.test.js` anhängen:

```js
const RADIUS = ["interpolate", ["linear"], ["ln", ["max", ["var", "n"], 1]], 0, 4, Math.log(100), 10];

test("Themenebenen: gleiches Paar wie die Hauptpunkte, Quelle thema, Radius wächst mit dem Zoom", () => {
  const e = Karte.prototype._themaEbenen.call(null);
  assert.deepEqual(e.map((l) => l.id), ["thema-haus", "thema-ungenau"]);
  assert.ok(e.every((l) => l.source === "thema" && l["source-layer"] === "adressen"));
  assert.deepEqual(e[0].paint["circle-stroke-width"], HALO);
  assert.equal(e[1].layout["icon-image"], "kreis-gestrichelt");
});

// Attrappe mit Quellen und Ebenen: zählt add/remove und merkt sich Filter, Paint, Layout, Sichtbarkeit.
function kartenAttrappe(ebenenVorhanden) {
  const q = new Set(["adressen"]); const layer = new Set(ebenenVorhanden); const filter = {}; const paint = {}; const layout = {}; const state = [];
  const map = {
    getSource: (s) => q.has(s) ? {} : undefined, addSource: (s) => q.add(s), removeSource: (s) => q.delete(s),
    getLayer: (l) => layer.has(l) ? {} : undefined, addLayer: (l) => layer.add(l.id), removeLayer: (l) => layer.delete(l),
    setFilter: (l, f) => { filter[l] = f; }, setPaintProperty: (l, k, v) => { paint[`${l}.${k}`] = v; },
    setLayoutProperty: (l, k, v) => { layout[`${l}.${k}`] = v; },
    setFeatureState: (f, s) => state.push([f.source, f.id, s]), removeFeatureState: (f) => state.push([f.source, "alle", null]),
    on() {}, getCanvas: () => ({ style: {} }),
  };
  return { map, q, layer, filter, paint, layout, state };
}

test("setzeThemaQuelle legt Quelle und Ebenen an, tauscht sie beim Wechsel, entfernt sie bei null", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau"]);
  const self = { map: a.map, zustand: { ebene: ["I"], praez: ["haus"], stadtteil: "" }, farbe: null, ansicht: null, treffer: new Set(), themaId: null, _handlerAngehaengt: true, _deckkraftSetzen() {} };
  Karte.prototype.setzeThemaQuelle.call(self, "bergbau");
  assert.ok(a.q.has("thema") && a.layer.has("thema-haus") && a.layer.has("thema-ungenau"));
  assert.equal(a.layout["adressen-haus.visibility"], "none"); assert.equal(a.layout["thema-haus.visibility"], "visible");
  Karte.prototype.setzeThemaQuelle.call(self, "besitz");
  assert.equal(self.themaId, "besitz"); assert.ok(a.q.has("thema"));
  Karte.prototype.setzeThemaQuelle.call(self, null);
  assert.ok(!a.q.has("thema") && !a.layer.has("thema-haus"));
  assert.equal(a.layout["adressen-haus.visibility"], "visible");
});

test("setzeFilter: Themenebenen ohne Zoomgrenze, Hauptebenen mit; Radius der Themenebene ist ein Zoom-Interpolate", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "thema-haus", "thema-ungenau"]);
  const self = { map: a.map, farbe: { ausdruck: "#111", filter: null }, ansicht: null, treffer: new Set(), _deckkraftSetzen() {} };
  Karte.prototype.setzeFilter.call(self, { ebene: ["I"], praez: ["haus"], stadtteil: "" });
  assert.ok(JSON.stringify(a.filter["adressen-haus"]).includes('["zoom"]'));
  assert.ok(!JSON.stringify(a.filter["thema-haus"]).includes('["zoom"]'));
  assert.ok(JSON.stringify(a.filter["thema-haus"]).includes('"stufe"'));           // Stufe, Ebenen, Stadtteil bleiben
  assert.deepEqual(a.paint["thema-haus.circle-radius"], ["let", "n", ["+", ["coalesce", ["get", "n_I"], 0]], ["interpolate", ["linear"], ["zoom"], 10, 1, 12, 2, 14, RADIUS]]);
  assert.equal(a.paint["thema-haus.circle-color"], a.paint["adressen-haus.circle-color"]);
});

test("setzeTreffer und Deckkraft wirken auf Haupt- und Themenquelle", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "thema-haus", "thema-ungenau"]); a.q.add("thema");
  const self = { map: a.map, ansicht: null, treffer: new Set() };
  Karte.prototype.setzeTreffer.call(self, ["x"]);
  assert.deepEqual(a.state.filter((s) => s[1] === "x").map((s) => s[0]).sort(), ["adressen", "thema"]);
  assert.deepEqual(a.paint["thema-haus.circle-opacity"], a.paint["adressen-haus.circle-opacity"]);
});

test("ebenenAufsetzen legt die Themenquelle nach einem Stilwechsel neu an", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "stadtteile-flaeche"]);
  const self = { map: a.map, zustand: { ebene: ["I"], praez: ["haus"], stadtteil: "", plan: 0, zechen: 0 }, farbe: null, ansicht: null, ansichtWerte: new Map(), treffer: new Set(), auswahl: null, themaId: "bergbau", _handlerAngehaengt: true,
    setzePlan() {}, setzeZechen() {}, setzeAnsicht() {}, setzeAuswahl() {}, _deckkraftSetzen() {} };
  Karte.prototype.ebenenAufsetzen.call(self);
  assert.ok(a.q.has("thema") && a.layer.has("thema-haus"));
});
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag sehen**

Run: `node --test site/tests/karte_ebenen.test.js`
Expected: FAIL, `TypeError: Karte.prototype._themaEbenen is not a function` (und die weiteren neuen Tests entsprechend).

- [ ] **Step 3: Implementierung in `site/js/karte.js`**

Oben nach `RADIUS`:

```js
// Themenebenen: aus der Vogelperspektive feine Punkte, ab Zoom 14 die Größe nach Zahl der Einträge (Spec Themenkacheln §3).
const RADIUS_THEMA = ["interpolate", ["linear"], ["zoom"], 10, 1, 12, 2, 14, RADIUS];
const THEMA_EBENEN = ["thema-haus", "thema-ungenau"];
```

Im Konstruktor nach `this.auswahl = null;`: `this.themaId = null;   // aktives Thema mit eigener Kacheldatei (setzeThemaQuelle)`.

Neue Methoden (nach `_eigeneEbenen`):

```js
  _themaQuelle(id) {
    return { type: "vector", url: `pmtiles://${new URL(DATEN + `themen/${id}.pmtiles`, location.href)}`, promoteId: "id" };
  }

  // Ebenenpaar der Themenquelle, gleich gebaut wie adressen-haus/adressen-ungenau (Spec Themenkacheln §3).
  _themaEbenen() {
    return [
      { id: "thema-haus", type: "circle", source: "thema", "source-layer": "adressen", filter: ["==", ["get", "stufe"], "haus"],
        paint: { "circle-stroke-color": "#fff", "circle-stroke-width": HALO } },
      { id: "thema-ungenau", type: "symbol", source: "thema", "source-layer": "adressen", filter: ["!=", ["get", "stufe"], "haus"],
        layout: { "icon-image": "kreis-gestrichelt", "icon-allow-overlap": true, "icon-ignore-placement": true },
        paint: { "icon-halo-color": "#fff", "icon-halo-width": HALO } },
    ];
  }

  // Kacheldatei eines Themas als zweite Punktquelle: bei id anlegen (vorhandene ersetzen) und die Hauptpunkte
  // ausblenden, bei null entfernen und die Hauptpunkte wieder zeigen. Vor dem ersten Stil nur merken.
  setzeThemaQuelle(id) {
    this.themaId = id || null;
    const m = this.map;
    if (!m.getLayer("adressen-haus")) return;
    for (const l of THEMA_EBENEN) if (m.getLayer(l)) m.removeLayer(l);
    if (m.getSource("thema")) m.removeSource("thema");
    if (this.themaId) {
      m.addSource("thema", this._themaQuelle(this.themaId));
      // Vor adressen-auswahl einfügen, damit der Auswahlring über den Themenpunkten liegt.
      for (const l of this._themaEbenen()) m.addLayer(l, m.getLayer("adressen-auswahl") ? "adressen-auswahl" : undefined);
      if (!this._themaHandler) {
        this._themaHandler = true;
        for (const l of THEMA_EBENEN) {
          m.on("click", l, (e) => this.ereignisse.onKlick(e.features[0].properties.id, e.lngLat));
          m.on("mouseenter", l, (e) => { m.getCanvas().style.cursor = "pointer"; this.ereignisse.onHover(e.features[0].properties.id, e.lngLat); });
          m.on("mouseleave", l, () => { m.getCanvas().style.cursor = ""; this.ereignisse.onHover(null, null); });
        }
      }
    }
    for (const l of ["adressen-haus", "adressen-ungenau"]) m.setLayoutProperty(l, "visibility", this.themaId ? "none" : "visible");
    for (const l of THEMA_EBENEN) if (m.getLayer(l)) m.setLayoutProperty(l, "visibility", "visible");
    this.setzeFilter(this.zustand);
    for (const id of this.treffer) if (this.themaId) m.setFeatureState({ source: "thema", sourceLayer: "adressen", id }, { treffer: true });
  }
```

Hinweis zu den Handlern: `map.on("click", layerId, …)` auf eine noch nicht vorhandene Ebene ist in MapLibre erlaubt; die Registrierung bleibt über remove/add der Ebene erhalten, darum einmalig (`this._themaHandler`). Der Test übergibt `on() {}` und `getCanvas`.

In `ebenenAufsetzen` nach `this.setzeAuswahl(this.auswahl);` einfügen: `this.setzeThemaQuelle(this.themaId);` (vor `setzeAnsicht`). Da `setzeThemaQuelle` selbst `setzeFilter` ruft, ist die doppelte Anwendung unschädlich.

`setzeFilter` umbauen: die Bedingungen bis einschließlich Schalterfilter wie heute sammeln, dann

```js
    const grund = this.farbe ? this.farbe.ausdruck : (z.ebene.length === 1 ? FARBEN[z.ebene[0]] : FARBEN.neutral);
    const farbe = ["case", ["boolean", ["feature-state", "treffer"], false], FARBEN.treffer, grund];
    // Hauptebenen: Stadtansicht nicht zulaufen lassen. Themenebenen: keine Zoomgrenze — sie sollen von oben alles zeigen.
    const haupt = [...bedingungen, ["any", [">=", ["zoom"], 12], [">=", n, 5]]];
    const paare = [["adressen-haus", "adressen-ungenau", haupt, RADIUS], ["thema-haus", "thema-ungenau", bedingungen, RADIUS_THEMA]];
    for (const [hausId, ungenauId, bed, radiusRegel] of paare) {
      if (!m.getLayer(hausId)) continue;
      m.setFilter(hausId, ["all", ["==", ["get", "stufe"], "haus"], ...bed]);
      m.setFilter(ungenauId, ["all", ["!=", ["get", "stufe"], "haus"], ...bed]);
      m.setPaintProperty(hausId, "circle-color", farbe);
      m.setPaintProperty(hausId, "circle-radius", ["let", "n", n, radiusRegel]);
      m.setPaintProperty(ungenauId, "icon-color", farbe);
      m.setLayoutProperty(ungenauId, "icon-size", ["/", ["let", "n", n, radiusRegel], 16]);
    }
    this._deckkraftSetzen();
```

Die Zeile `bedingungen.push(["any", [">=", ["zoom"], 12], [">=", n, 5]]);` entfällt (sie steckt jetzt in `haupt`).

`_deckkraftSetzen`: nach den drei `setPaintProperty` für die Hauptebenen ergänzen:

```js
    if (this.map.getLayer("thema-haus")) {
      this.map.setPaintProperty("thema-haus", "circle-opacity", d);
      this.map.setPaintProperty("thema-haus", "circle-stroke-opacity", d);
      this.map.setPaintProperty("thema-ungenau", "icon-opacity", d);
    }
```

`setzeTreffer`: nach `m.removeFeatureState({ source: "adressen", sourceLayer: "adressen" });` und in der Schleife jeweils die Themenquelle mitnehmen:

```js
    const quellen = [["adressen", "adressen"], ...(m.getSource("thema") ? [["thema", "adressen"]] : [])];
    for (const [source, sourceLayer] of quellen) m.removeFeatureState({ source, sourceLayer });
    this.treffer = new Set(adressIds || []);
    for (const [source, sourceLayer] of quellen) for (const id of this.treffer) m.setFeatureState({ source, sourceLayer, id }, { treffer: true });
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/karte_ebenen.test.js`
Expected: PASS. Der bestehende Test „setzeFilter: Schalterfilter …“ braucht in seiner Attrappe kein `getLayer`-Update; er übergibt `getLayer: () => true`, damit laufen beide Paare — prüfen, dass er weiter besteht.

- [ ] **Step 5: Gesamtsuite und Commit**

Run: `node --test site/tests/*.test.js`
Expected: 154 + 5 pass.

```bash
git add site/js/karte.js site/tests/karte_ebenen.test.js
git commit -m "feat(karte): Themenquelle mit eigenem Ebenenpaar — Filter ohne Zoomgrenze, zoomabhängiger Radius, Treffer und Deckkraft auf beiden Quellen, Neuaufbau nach Stilwechsel

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Thema laden und anwenden — `kacheln` aus dem Index, Quelle umschalten

**Files:**
- Modify: `site/js/themen.js:46-49` (`ladeThema`), `site/js/app.js:132-142` (`wendeThemaAn`)
- Test: `site/tests/themen.test.js`

**Interfaces:**
- Consumes: `Karte.prototype.setzeThemaQuelle(id | null)` (Task 2); `themen/index.json` mit `kacheln` (Task 1).
- Produces: `ladeThema(lader, id, klassen)` liefert zusätzlich `kacheln: boolean`.

- [ ] **Step 1: Failing test schreiben**

An `site/tests/themen.test.js` anhängen (dort gibt es bereits einen Lader-Fake; falls der Fake anders heißt, das Muster des ersten `ladeThema`-Tests übernehmen):

```js
test("ladeThema liefert kacheln aus dem Index; ohne Index-Eintrag false (altes Datenpaket)", async () => {
  const thema = { id: "bergbau", titel: "Bergbau", freigegeben: true, farbe: { art: "einfach", wert: "#000" } };
  const laderMit = { thema: async () => thema, json: async (p) => p === "themen/index.json" ? [{ id: "bergbau", titel: "Bergbau", freigegeben: true, kacheln: true }] : null };
  assert.equal((await ladeThema(laderMit, "bergbau")).kacheln, true);
  const laderOhne = { thema: async () => thema, json: async () => [{ id: "bergbau", titel: "Bergbau", freigegeben: true }] };
  assert.equal((await ladeThema(laderOhne, "bergbau")).kacheln, false);
  const laderLeer = { thema: async () => thema, json: async () => null };
  assert.equal((await ladeThema(laderLeer, "bergbau")).kacheln, false);
});
```

- [ ] **Step 2: Test laufen lassen, Fehlschlag sehen**

Run: `node --test site/tests/themen.test.js`
Expected: FAIL, `kacheln` ist `undefined` statt `true`.

- [ ] **Step 3: Implementierung**

`site/js/themen.js`:

```js
export async function ladeThema(lader, id, klassen = "") {
  const t = await lader.thema(id);
  if (!t) return null;
  // kacheln: eigene Kacheldatei themen/<id>.pmtiles (Spec Themenkacheln §2); fehlt sie im Index (älteres
  // Datenpaket), verhält sich die Karte wie ohne Themenquelle.
  const index = (await lader.json("themen/index.json")) || [];
  const eintrag = index.find((e) => e.id === id);
  return { ...t, farbregel: farbregel(t, klassen), ebenen: t.filter?.ebenen || null, kacheln: !!(eintrag && eintrag.kacheln) };
}
```

`site/js/app.js` in `wendeThemaAn` nach `karte.setzeFarbe(t ? t.farbregel : null);`:

```js
  karte.setzeThemaQuelle(t && t.kacheln ? t.id : null);   // feine Punkte aus der Kacheldatei des Themas (Spec Themenkacheln §3)
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/*.test.js`
Expected: PASS, alle.

- [ ] **Step 5: Commit**

```bash
git add site/js/themen.js site/js/app.js site/tests/themen.test.js
git commit -m "feat(karte): Thema mit Kacheldatei schaltet die Themenquelle ein; kacheln aus themen/index.json, Rückfall ohne

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Datenpaket, Sichtprüfung, Texte und Doku

**Files:**
- Modify: `kuratierung/themen/bergbau.json` (`grundlage`), `docs/bergbau.md` („Offen“), `README.md` (Themenformat, Dateiliste)
- Sichtprüfung: Playwright-Skript im Scratchpad

**Interfaces:**
- Consumes: Export (Task 1), Karte (Task 2), App (Task 3).

- [ ] **Step 1: Datenpaket bauen**

Run: `python3 pipeline/06_karte_export.py`
Expected: läuft durch; `ls -la site/daten/themen/` zeigt `bergbau.pmtiles`, `berufe.pmtiles`, `besitz.pmtiles` (und keine `akademiker.pmtiles`); `python3 -c "import json;print(json.load(open('site/daten/themen/index.json')))"` zeigt `kacheln: true` für die drei freigegebenen Themen.

- [ ] **Step 2: Sichtprüfung mit Playwright**

Skript `<scratchpad>/sicht_themenkacheln.py` (Dev-Server `python3 werkzeuge/serve.py 8765` muss laufen):

```python
import asyncio
from playwright.async_api import async_playwright
ZAEHL = "(l) => map.queryRenderedFeatures({ layers: [l] }).length"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1400, "height": 900})
        fehler = []; pg.on("pageerror", lambda e: fehler.append(str(e))); pg.on("console", lambda m: fehler.append(m.text) if m.type == "error" else None)
        for url in ("karte.html?z=11.5", "karte.html?z=11.5&thema=bergbau", "karte.html?z=11.5&thema=besitz", "karte.html?z=11.5&thema=berufe"):
            await pg.goto(f"http://localhost:8765/site/{url}"); await pg.wait_for_timeout(4000)
            haupt = await pg.evaluate("() => window.__karte ? window.__karte.map.queryRenderedFeatures({layers:['adressen-haus']}).length : -1")
            thema = await pg.evaluate("() => window.__karte && window.__karte.map.getLayer('thema-haus') ? window.__karte.map.queryRenderedFeatures({layers:['thema-haus']}).length : 0")
            print(url, "Hauptpunkte:", haupt, "Themenpunkte:", thema)
            await pg.screenshot(path=f"build/mockups/themenkacheln_{url.split('thema=')[-1].replace('karte.html?z=11.5','ohne')}.png")
        print("Fehler:", fehler); await b.close()
asyncio.run(main())
```

Falls `window.__karte` nicht existiert: in `app.js` beim Anlegen der Karte `if (new URLSearchParams(location.search).has("debug")) window.__karte = karte;` ergänzen und die URLs um `&debug=1` erweitern (bleibt als Debughilfe, wird nicht dokumentiert).

Run: `python3 <scratchpad>/sicht_themenkacheln.py`
Expected: ohne Thema Hauptpunkte > 0, Themenpunkte 0; mit Thema Hauptpunkte 0 (unsichtbar), Themenpunkte in der Größenordnung Tausende (Bergbau: mehrere Tausend bei Zoom 11,5, kein Ausdünnungsrest); `Fehler: []`. Screenshots anschauen: feine Punkte, Ballungen erkennbar, Farben des Themas, Legende unverändert. Zusätzlich einen Klick auf einen Themenpunkt prüfen (Popup erscheint) und die Suche „Krupp“ bei aktivem Thema (Treffer rot, Rest gedimmt).

- [ ] **Step 3: Kachelgrößen prüfen**

Run: `ls -la site/daten/themen/*.pmtiles`
Expected: Bergbau deutlich unter Besitz unter Berufe; Gesamtgrößen im einstelligen MB-Bereich. Werte in den Commit-Text übernehmen.

- [ ] **Step 4: Texte**

`kuratierung/themen/bergbau.json`, Feld `grundlage`: `"… (Norm → Gruppe, noch ungeprüft) …"` → `"… (Norm → Gruppe, geprüft am 2026-09-29 bis auf vier Grenzfälle) …"`.

`docs/bergbau.md`, Abschnitt „Offen“: „Prüfung der Tabelle durch den Projektleiter (`geprueft`)“ ersetzen durch „vier Grenzfälle der Tabelle (Kokereiarbeiter, Koksarbeiter, Schlepper, Oberschaffner; Rest geprüft 2026-09-29)“; „Bildrate des Übergangs am Handy (Rückfall auf Canvas, falls unter 30 fps)“ ersetzen durch „Übergang läuft seit 2026-09-29 auf Canvas (59 fps Rechner, 33 fps bei vierfach gedrosselter CPU)“.

`README.md`: in der Dateiliste (bei `themen/<id>.json`) eine Zeile `| themen/<id>.pmtiles | Kacheldatei je freigegebenem Thema: nur Treffer-Adressen, nur Filter-, Schalter- und Farbfelder, Zoom 9–15 ohne Ausdünnung (Spec 2026-09-29-themenkacheln) |` ergänzen; im Abschnitt „Themenformat“ einen Absatz:

```
Je freigegebenem Thema entsteht `themen/<id>.pmtiles` (Ebene `adressen`, ohne Ausdünnung). Die Karte zeigt bei
aktivem Thema diese Quelle statt der Hauptpunkte: keine Zoomgrenze, Radius 1 px (Zoom 10) bis zur normalen
Größe (Zoom 14), damit Ballungen aus der Vogelperspektive sichtbar sind. Felder je Punkt: `id, stufe, stadtteil,
n_I, n_II, n_III`, das Farbfeld (`kategorien`), `m_<merkmal>` (Merkmalsthemen) und die Schalterfelder.
`themen/index.json` trägt `kacheln: true`, wenn die Datei geschrieben wurde; fehlt das Flag, verhält sich die
Karte wie ohne Themenquelle.
```

- [ ] **Step 5: Tests und Commit**

Run: `python3 -m pytest -q && node --test site/tests/*.test.js`
Expected: alles grün.

```bash
git add kuratierung/themen/bergbau.json docs/bergbau.md README.md site/js/app.js
git commit -m "docs: Themenkacheln im README, Bergbau-Grundlage geprüft, Offen-Liste aktualisiert; Sichtprüfung der feinen Themenansicht

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

(`site/js/app.js` nur, falls der Debug-Haken aus Step 2 nötig war.)
