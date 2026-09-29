# Eigentümer-Vergleich Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eigentümer-Treffer erscheinen sofort, bis zu fünf Eigentümer lassen sich mit festen Farben gegenüberstellen, Häuser in mehreren Gruppen tragen einen Ring, und der Vergleich steckt in der URL.

**Architecture:** Ein schlanker Adress-Kurzindex (16 Dateien) ersetzt die teuren Kachelabfragen und Adressscherben beim Aufbau der Trefferliste. `treffer()` liefert für Eigentümer Gruppen mit Farbe; die Karte färbt über den Feature-State (`gruppe`, `mehrfach`), die Sidebar zeigt eine Vergleichsleiste, Knöpfe und Suchvorschläge fügen hinzu oder entfernen. Reine Hilfsfunktionen liegen in einem neuen Modul `site/js/vergleich.js`, damit sie ohne DOM testbar sind.

**Tech Stack:** Python 3 / pytest (Pipeline), ES-Module ohne Bundler, MapLibre GL 4.7.1, node:test.

**Spec:** `docs/superpowers/specs/2026-09-29-eigentuemer-vergleich-design.md`

## Global Constraints

- Höchstens **fünf** Eigentümer gleichzeitig (`MAX_EIGENTUEMER = 5` in `zustand.js`).
- Palette `FARBEN.gruppen = ["#dc2626", "#2563eb", "#16a34a", "#7c3aed", "#f59e0b"]`, Farbe hängt am Platz in der Auswahl.
- URL-Form `eigentuemer=Name1|Name2` (Trenner `|`), ein Einzelname ohne `|` bleibt gültig.
- Kurzindex `adressen_kurz/<x>.json`, `x` = erstes Zeichen der Adress-ID, Wert `[lon, lat, stufe, stadtteil, strasse_heute, hausnr, historisch]`, Koordinaten auf 6 Nachkommastellen.
- Eigentümer-Knöpfe nur für geprüfte Eigentümer (`eigentuemer_kanon` bzw. Index `suche/eigentuemer.json`).
- Mehrfachtreffer = Ring in `FARBEN.auswahl`, keine Mischfarbe.
- Commit-Nachrichten auf Deutsch, Abschluss `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
- `PLAN_FREIGEGEBEN` in `site/js/konfig.js` bleibt `false`; kein Push.
- Testbefehle: `node --test site/tests/*.test.js` und `python3 -m pytest -q`.

## Review Focus

1. Ein Link `eigentuemer=A|A|B|C|D|E|F` (Dubletten, mehr als fünf): erwartet Liste `[A, B, C, D, E]`, keine Fehlermeldung — Test in Task 3.
2. Ein Eigentümer, dessen Scherbe fehlt (404, z. B. alter Link auf einen umbenannten Namen) neben einem gültigen: erwartet Gruppe mit null Häusern, die andere Gruppe zeigt normal — Test in Task 4.
3. Ein Haus, das in drei gewählten Gruppen liegt: erwartet Farbe der ersten Gruppe, `mehrfach: true`, in der CSV dreimal — Tests in Task 5 und 8.
4. Kurzindex-Datei fehlt (Datenpaket älter als dieser Stand): erwartet leere Map, Liste zeigt IDs statt Adressen, keine Ausnahme — Test in Task 2.
5. MapLibre lehnt einen Ausdruck ab (Feature-State in `circle-stroke-width` unter einem Zoom-Interpolate, Halo der Symbolebene): erwartet keine Konsolenfehler beim Laden — Sichtprüfung in Task 9 liest die Konsole.

---

### Task 1: Kurzindex im Datenpaket

**Files:**
- Modify: `pipeline/lib/karte_export.py` (nach `baue_adressscherben`, Z. 319–327; `schreibe_paket` Z. ~995)
- Modify: `README.md` Dateiliste (Z. 268, nach `adressen/<xx>.json`)
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Produces: `baue_adressen_kurz(adressen: dict[str, dict]) -> dict[str, dict[str, list]]`; Dateien `adressen_kurz/<x>.json`.

- [ ] **Step 1: Failing test schreiben** (an `tests/test_karte_export.py` anhängen)

```python
def test_baue_adressen_kurz_verteilt_nach_erstem_zeichen_und_traegt_sieben_werte():
    from pipeline.lib.karte_export import baue_adressen_kurz
    adressen = {
        "a1b2": dict(id="a1b2", lat=51.4912345678, lon=7.0612345678, stufe="haus", stadtteil="Katernberg", strasse_heute="Lattenkamp", hausnr="25", hausnr_zusatz="a", historisch="Grenzstr. 25, Katernberg"),
        "a9ff": dict(id="a9ff", lat=51.5, lon=7.1, stufe="stadtplan", stadtteil="", strasse_heute="", hausnr="3", hausnr_zusatz="", historisch="Alte Str. 3"),
        "b000": dict(id="b000", lat=51.6, lon=7.2, stufe="strasse", stadtteil="Kray", strasse_heute="Kampstr.", hausnr="", hausnr_zusatz=None, historisch="Kampstr."),
    }
    k = baue_adressen_kurz(adressen)
    assert sorted(k) == ["a", "b"]
    assert k["a"]["a1b2"] == [7.061235, 51.491235, "haus", "Katernberg", "Lattenkamp", "25a", "Grenzstr. 25, Katernberg"]
    assert k["a"]["a9ff"] == [7.1, 51.5, "stadtplan", "", "", "3", "Alte Str. 3"]
    assert k["b"]["b000"] == [7.2, 51.6, "strasse", "Kray", "Kampstr.", "", "Kampstr."]


def test_schreibe_paket_schreibt_kurzindex(tmp_path):
    e = [_v(id="1", lastname="Sepeur", firstname="Wilh.", teil="I")]
    schreibe_paket(tmp_path, e, [], lies_csv(FIX / "zechen.csv"), "2026-09-21", kacheln=False)
    aid = adress_id(e[0])
    kurz = json.loads((tmp_path / "adressen_kurz" / f"{aid[0]}.json").read_text())
    assert kurz[aid][:3] == [7.06, 51.49, "haus"] and kurz[aid][4] == "Lattenkamp"
```

- [ ] **Step 2: Test laufen lassen**

Run: `python3 -m pytest -q tests/test_karte_export.py -k "adressen_kurz or kurzindex"`
Expected: FAIL, `ImportError: cannot import name 'baue_adressen_kurz'` bzw. `FileNotFoundError`.

- [ ] **Step 3: Implementieren** (nach `baue_adressscherben` einfügen)

```python
def baue_adressen_kurz(adressen: dict[str, dict]) -> dict[str, dict[str, list]]:
    """Kurzindex für Trefferlisten (Spec Eigentümer-Vergleich §2): Datei = erstes Zeichen der Adress-ID,
    je Adresse [lon, lat, stufe, stadtteil, strasse_heute, hausnr, historisch] — sieben Werte, keine Zählfelder.
    Ersetzt die Kachelabfrage und die fetten Adressscherben beim Aufbau der Liste."""
    kurz: dict[str, dict[str, list]] = defaultdict(dict)
    for aid, a in adressen.items():
        kurz[aid[0]][aid] = [round(a["lon"], 6), round(a["lat"], 6), a["stufe"], a.get("stadtteil") or "",
                             a.get("strasse_heute") or "", (a.get("hausnr") or "") + (a.get("hausnr_zusatz") or ""),
                             a.get("historisch") or ""]
    return dict(kurz)
```

In `schreibe_paket` direkt nach der Schleife über `baue_adressscherben(adressen)`:

```python
    for name, inhalt in baue_adressen_kurz(adressen).items():
        _json(ausgabe / "adressen_kurz" / f"{name}.json", inhalt)
```

README-Dateiliste, neue Zeile nach `adressen/<xx>.json`:

```
| `adressen_kurz/<x>.json` | Kurzindex je erstem Zeichen der Adress-ID: `[lon, lat, stufe, stadtteil, strasse_heute, hausnr, historisch]` — für Trefferlisten und Einpassen ohne Kachelabfrage (Spec 2026-09-29-eigentuemer-vergleich) |
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle bestehenden plus 2 neue Tests PASS (454 passed, 7 deselected).

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/karte_export.py tests/test_karte_export.py README.md
git commit -m "feat(export): Kurzindex adressen_kurz/<x>.json — sieben Werte je Adresse für Trefferlisten ohne Kachelabfrage

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: `Lader.adressenKurz`

**Files:**
- Modify: `site/js/daten.js` (nach `adresse()`, Z. 33–36)
- Test: `site/tests/daten.test.js`

**Interfaces:**
- Consumes: Dateien `adressen_kurz/<x>.json` aus Task 1.
- Produces: `Lader.adressenKurz(ids: string[]) -> Promise<Map<string, {id, lon, lat, stufe, stadtteil, strasse_heute, hausnr, historisch}>>`.

- [ ] **Step 1: Failing test schreiben** (an `site/tests/daten.test.js` anhängen)

```js
test("Lader.adressenKurz lädt nur die betroffenen Dateien, einmal, und baut Objekte aus den sieben Werten", async () => {
  const DATEIEN3 = {
    "daten/adressen_kurz/a.json": { a1: [7.06, 51.49, "haus", "Katernberg", "Lattenkamp", "25", "Grenzstr. 25, Katernberg"], a2: [7.07, 51.5, "strasse", "Kray", "", "", "Kampstr. 3"] },
    "daten/adressen_kurz/b.json": { b1: [7.0, 51.4, "stadtplan", "", "", "3", "Alte Str. 3"] },
  };
  const geladen = [];
  const l = new Lader("daten/", async (u) => { geladen.push(u); return { ok: u in DATEIEN3, status: u in DATEIEN3 ? 200 : 404, json: async () => DATEIEN3[u] }; });
  const m = await l.adressenKurz(["a1", "b1", "a2", "zz"]);
  assert.deepEqual(m.get("a1"), { id: "a1", lon: 7.06, lat: 51.49, stufe: "haus", stadtteil: "Katernberg", strasse_heute: "Lattenkamp", hausnr: "25", historisch: "Grenzstr. 25, Katernberg" });
  assert.equal(m.get("b1").stufe, "stadtplan");
  assert.equal(m.has("zz"), false);                       // Datei fehlt (404) → keine Ausnahme, kein Eintrag
  assert.deepEqual(geladen.sort(), ["daten/adressen_kurz/a.json", "daten/adressen_kurz/b.json", "daten/adressen_kurz/z.json"]);
  await l.adressenKurz(["a2"]);
  assert.equal(geladen.length, 3);                        // zweiter Aufruf lädt nichts nach
});

test("Lader.adressenKurz mit leerer Liste liefert eine leere Map ohne Ladevorgang", async () => {
  let n = 0;
  const l = new Lader("daten/", async () => { n++; return { ok: false, status: 404 }; });
  assert.equal((await l.adressenKurz([])).size, 0);
  assert.equal(n, 0);
});
```

- [ ] **Step 2: Test laufen lassen**

Run: `node --test site/tests/daten.test.js`
Expected: FAIL, `TypeError: l.adressenKurz is not a function`.

- [ ] **Step 3: Implementieren** (in `Lader`, nach `adresse()`)

```js
  // Kurzindex (Spec Eigentümer-Vergleich §2): je Datei das erste Zeichen der ID, sieben Werte je Adresse.
  // Lädt nur die Dateien, die unter den IDs vorkommen; json() hält sie im Cache. Fehlende Datei → keine Einträge.
  async adressenKurz(ids) {
    const dateien = [...new Set(ids.map((id) => id[0]))];
    const geladen = await Promise.all(dateien.map((x) => this.json(`adressen_kurz/${x}.json`)));
    const je = new Map(dateien.map((x, i) => [x, geladen[i] || {}]));
    const m = new Map();
    for (const id of ids) {
      const w = je.get(id[0])[id];
      if (w) m.set(id, { id, lon: w[0], lat: w[1], stufe: w[2], stadtteil: w[3], strasse_heute: w[4], hausnr: w[5], historisch: w[6] });
    }
    return m;
  }
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/daten.test.js`
Expected: PASS (6 Tests).

- [ ] **Step 5: Commit**

```bash
git add site/js/daten.js site/tests/daten.test.js
git commit -m "feat(daten): Lader.adressenKurz — Kurzindex je erstem ID-Zeichen, nur betroffene Dateien

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Zustand `eigentuemer` als Liste, Palette

**Files:**
- Modify: `site/js/zustand.js` (STANDARD Z. 2–7, `liesZustand` Z. 34, `schreibeZustand` Z. 52–61)
- Modify: `site/js/konfig.js` Z. 9 (`FARBEN`)
- Test: `site/tests/zustand.test.js` (bestehenden Test „eigentuemer im Zustand“ ersetzen)

**Interfaces:**
- Produces: `STANDARD.eigentuemer = []`, `MAX_EIGENTUEMER = 5` (export), `namensliste(wert: string|null) -> string[]` (export); `FARBEN.gruppen: string[5]`.

- [ ] **Step 1: Failing test schreiben** (Test „eigentuemer im Zustand“ in `site/tests/zustand.test.js` durch diesen Block ersetzen)

```js
import { MAX_EIGENTUEMER, namensliste } from "../js/zustand.js";

test("eigentuemer ist eine Liste: Einzelname, |-Liste, Dubletten und Kappung auf fünf", () => {
  assert.deepEqual(liesZustand("?eigentuemer=Fried.+Krupp+AG").eigentuemer, ["Fried. Krupp AG"]);
  assert.deepEqual(liesZustand("?eigentuemer=Fried.+Krupp+AG|Stadt+Essen").eigentuemer, ["Fried. Krupp AG", "Stadt Essen"]);
  assert.deepEqual(liesZustand("?eigentuemer=A|A|B|C|D|E|F").eigentuemer, ["A", "B", "C", "D", "E"]);
  assert.deepEqual(liesZustand("?eigentuemer=|+|").eigentuemer, []);
  assert.equal(MAX_EIGENTUEMER, 5);
  assert.deepEqual(namensliste("x| y |x"), ["x", "y"]);
  assert.deepEqual(namensliste(null), []);
});

test("eigentuemer wird mit | geschrieben und rund gelesen; leer bleibt weg", () => {
  assert.equal(schreibeZustand({ ...STANDARD, eigentuemer: ["Stadt Essen"] }), "eigentuemer=Stadt+Essen");
  const s = schreibeZustand({ ...STANDARD, eigentuemer: ["Fried. Krupp AG", "Stadt Essen"] });
  assert.equal(s, "eigentuemer=Fried.+Krupp+AG|Stadt+Essen");
  assert.deepEqual(liesZustand("?" + s).eigentuemer, ["Fried. Krupp AG", "Stadt Essen"]);
  assert.equal(schreibeZustand({ ...STANDARD, eigentuemer: [] }), "");
});
```

- [ ] **Step 2: Test laufen lassen**

Run: `node --test site/tests/zustand.test.js`
Expected: FAIL, `SyntaxError: The requested module '../js/zustand.js' does not provide an export named 'MAX_EIGENTUEMER'`.

- [ ] **Step 3: Implementieren**

`site/js/zustand.js`: in `STANDARD` `eigentuemer: ""` → `eigentuemer: []`. Vor `liesZustand` einfügen:

```js
// Eigentümer-Vergleich (Spec 2026-09-29 §3): höchstens fünf Namen, Trenner | (Namen können Kommas enthalten).
export const MAX_EIGENTUEMER = 5;
export function namensliste(wert) {
  if (!wert) return [];
  const aus = [];
  for (const t of wert.split("|")) { const n = t.trim(); if (n && !aus.includes(n)) aus.push(n); }
  return aus.slice(0, MAX_EIGENTUEMER);
}
```

In `liesZustand`: `eigentuemer: p.get("eigentuemer") || "",` → `eigentuemer: namensliste(p.get("eigentuemer")),`.

In `schreibeZustand` die Zeile `p.set(k, Array.isArray(w) ? w.join(",") : String(w));` → `p.set(k, Array.isArray(w) ? w.join(k === "eigentuemer" ? "|" : ",") : String(w));` und die Rückgabe `return p.toString().replace(/%2C/g, ",");` → `return p.toString().replace(/%2C/g, ",").replace(/%7C/g, "|");`.

`site/js/konfig.js` Z. 9:

```js
export const FARBEN = { I: "#1d4ed8", II: "#ca8a04", III: "#c2410c", neutral: "#1f2937", treffer: "#dc2626", auswahl: "#111827",
  // Eigentümer-Vergleich: Farbe je Platz in der Auswahl (Rot, Blau, Grün, Violett, Orange)
  gruppen: ["#dc2626", "#2563eb", "#16a34a", "#7c3aed", "#f59e0b"] };
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/zustand.test.js`
Expected: PASS. Danach `node --test site/tests/*.test.js`: alles PASS (app.js wird von keinem Test importiert; die Anpassung dort folgt in Task 9).

- [ ] **Step 5: Commit**

```bash
git add site/js/zustand.js site/js/konfig.js site/tests/zustand.test.js
git commit -m "feat(zustand): eigentuemer als Liste bis fünf Namen (Trenner |), Gruppenpalette

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: `treffer()` mit Gruppen

**Files:**
- Modify: `site/js/suche.js` Z. 59–87 (`treffer`), Import `FARBEN`
- Test: `site/tests/suche.test.js`

**Interfaces:**
- Consumes: `FARBEN.gruppen` (Task 3).
- Produces: `treffer(auswahl, lader)` mit `auswahl = { art: "eigentuemer", namen: string[] }` liefert `{ adressIds, zaehler, personen, hinweisHJ, gruppen }`; `gruppen = [{ name, farbe, adressIds: string[], zaehler: Map }]` bei Eigentümern, sonst `null`. `{ art: "eigentuemer", name }` (alt) wird wie `namen: [name]` behandelt.

- [ ] **Step 1: Failing test schreiben** (an `site/tests/suche.test.js` anhängen; `DATEIEN` oben um die Zeile `"daten/suche/eigentuemer/st.json": { "Stadt Essen": [["b2", 1], ["c3", 3]] },` ergänzen)

```js
test("treffer mit mehreren Eigentümern: Gruppen in Reihenfolge mit Farbe, Vereinigung der Häuser, summierte Zähler", async () => {
  const geladen = []; const l = new Lader("daten/", async (u) => { geladen.push(u); return fetchFake(u); });
  const t = await treffer({ art: "eigentuemer", namen: ["Fried. Krupp AG", "Stadt Essen", "Gibtsnicht GmbH"] }, l);
  assert.deepEqual(t.gruppen.map((g) => [g.name, g.farbe, g.adressIds]), [
    ["Fried. Krupp AG", "#dc2626", ["a1", "b2"]], ["Stadt Essen", "#2563eb", ["b2", "c3"]], ["Gibtsnicht GmbH", "#16a34a", []]]);
  assert.deepEqual(t.adressIds, ["a1", "b2", "c3"]);
  assert.equal(t.zaehler.get("b2"), 3);                   // 2 (Krupp) + 1 (Stadt)
  assert.equal(t.gruppen[1].zaehler.get("c3"), 3);
  assert.equal(geladen.filter((u) => u.includes("eigentuemer/")).length, 3);   // fr, st, gi — je Präfix einmal
});

test("treffer: alte Auswahlform {name} und andere Arten liefern gruppen null bzw. eine Gruppe", async () => {
  const alt = await treffer({ art: "eigentuemer", name: "Fried. Krupp AG" }, lader());
  assert.deepEqual(alt.gruppen.map((g) => g.name), ["Fried. Krupp AG"]);
  assert.deepEqual(alt.adressIds, ["a1", "b2"]);
  assert.equal((await treffer({ art: "beruf", beruf: "Bergm." }, lader())).gruppen, null);
});
```

- [ ] **Step 2: Test laufen lassen**

Run: `node --test site/tests/suche.test.js`
Expected: FAIL, `TypeError: Cannot read properties of undefined (reading 'map')` (kein `gruppen`).

- [ ] **Step 3: Implementieren**

Import oben in `site/js/suche.js` ergänzen (nach Z. 2): `import { FARBEN } from "./konfig.js";` — `konfig.js` wird dort bisher nicht importiert.

`treffer` Eigentümer-Zweig und Rückgabe:

```js
  let gruppen = null;
  …
  } else if (auswahl.art === "eigentuemer") {
    // Eigentümer-Vergleich (Spec 2026-09-29 §4): je Name eine Gruppe mit Farbe nach Platz; die Gesamtmenge ist die Vereinigung.
    const namen = auswahl.namen || (auswahl.name ? [auswahl.name] : []);
    gruppen = [];
    for (const [i, name] of namen.entries()) {
      const s = await lader.eigentuemerScherbe(praefix2(name));
      const z = new Map((s && s[name]) || []);
      for (const [a, n] of z) zaehler.set(a, (zaehler.get(a) || 0) + n);
      gruppen.push({ name, farbe: FARBEN.gruppen[i % FARBEN.gruppen.length], adressIds: [...z.keys()], zaehler: z });
    }
  } else if (auswahl.art === "ohdab") {
  …
  return { adressIds: [...zaehler.keys()], zaehler, personen, hinweisHJ: hinweis, gruppen };
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/suche.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add site/js/suche.js site/tests/suche.test.js
git commit -m "feat(suche): treffer liefert Eigentümer-Gruppen mit Farbe, Vereinigung und summierten Zählern

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Modul `vergleich.js` und Trefferzeile/Eigentümer-Knopf in `popup.js`

**Files:**
- Create: `site/js/vergleich.js`
- Modify: `site/js/popup.js` (`popupZeile` Z. 78–81, `eintragHtml` Z. 107–117, `trefferzeileHtml` Z. 146–152)
- Test: `site/tests/vergleich.test.js` (neu), `site/tests/popup.test.js`

**Interfaces:**
- Consumes: `gruppen` aus Task 4; `eig`-Map aus Task 2.
- Produces: `gruppenZuordnung(gruppen) -> Map<id, {gruppe: number, mehrfach: boolean}>`; `mehrfachZahl(gruppen) -> number`; `verteilung(adressIds, zaehler, eig, n = 3) -> [string, number][]`; `vergleichsleisteHtml(gruppen, eig) -> string`; `trefferzeileHtml(t)` versteht `t.farbe` und `t.mehrfach`; Popup und Hausansicht tragen `<button class="eiglink" data-eigentuemer="…">`.

- [ ] **Step 1: Failing tests schreiben**

`site/tests/vergleich.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { gruppenZuordnung, mehrfachZahl, verteilung, vergleichsleisteHtml } from "../js/vergleich.js";

const G = [
  { name: "Krupp", farbe: "#dc2626", adressIds: ["a", "b", "c"], zaehler: new Map([["a", 1], ["b", 2], ["c", 1]]) },
  { name: "Stadt", farbe: "#2563eb", adressIds: ["b", "d"], zaehler: new Map([["b", 1], ["d", 1]]) },
  { name: "Stinnes", farbe: "#16a34a", adressIds: ["b"], zaehler: new Map([["b", 1]]) },
];
const EIG = new Map([["a", { stadtteil: "Kray" }], ["b", { stadtteil: "Kray" }], ["c", { stadtteil: "Bochold" }], ["d", { stadtteil: "Kray" }]]);

test("gruppenZuordnung: erste Gruppe gewinnt, mehrfach bei mehr als einer", () => {
  const z = gruppenZuordnung(G);
  assert.deepEqual(z.get("a"), { gruppe: 0, mehrfach: false });
  assert.deepEqual(z.get("b"), { gruppe: 0, mehrfach: true });    // in drei Gruppen
  assert.deepEqual(z.get("d"), { gruppe: 1, mehrfach: false });
  assert.equal(mehrfachZahl(G), 1);
  assert.equal(mehrfachZahl([G[0]]), 0);
});

test("verteilung: Top n Stadtteile nach Einträgen, unbekannt ohne Eintrag im Kurzindex", () => {
  assert.deepEqual(verteilung(G[0].adressIds, G[0].zaehler, EIG), [["Kray", 3], ["Bochold", 1]]);
  assert.deepEqual(verteilung(["x"], new Map([["x", 2]]), EIG), [["unbekannt", 2]]);
  assert.deepEqual(verteilung(G[0].adressIds, G[0].zaehler, EIG, 1), [["Kray", 3]]);
});

test("vergleichsleisteHtml: eine Zeile je Gruppe mit Farbe, Zahlen, Stadtteilen und Entfernen-Knopf; Ring-Hinweis", () => {
  const h = vergleichsleisteHtml(G, EIG);
  assert.match(h, /<div class="vergleich">/);
  assert.match(h, /<span class="punkt" style="background:#dc2626"><\/span> <b>Krupp<\/b> <small>3 Häuser · 4 Einträge<\/small>/);
  assert.match(h, /Kray 3 · Bochold 1/);
  assert.match(h, /<button class="weg" data-eig-weg="Krupp" title="Krupp entfernen">×<\/button>/);
  assert.match(h, /1 Haus mit mehreren gewählten Eigentümern \(Ring\)/);
  assert.doesNotMatch(vergleichsleisteHtml([G[0]], EIG), /Ring/);
  assert.match(vergleichsleisteHtml([{ ...G[1], adressIds: [], zaehler: new Map() }], EIG), /0 Häuser · 0 Einträge/);
});
```

An `site/tests/popup.test.js` anhängen und die zwei bestehenden Erwartungen anpassen:

```js
test("trefferzeileHtml: Farbpunkt und Ring-Klasse bei Gruppen", () => {
  const h = trefferzeileHtml({ adressId: "a1", titel: "x", untertitel: "y", stufe: "haus", farbe: "#dc2626", mehrfach: true });
  assert.match(h, /^<div class="treffer mehrfach" data-adresse="a1"><span class="punkt" style="background:#dc2626"><\/span><b>x<\/b>/);
  assert.doesNotMatch(trefferzeileHtml({ adressId: "a1", titel: "x", untertitel: "y", stufe: "haus" }), /punkt|mehrfach/);
});

test("Eigentümer-Knopf: nur bei geprüftem Eigentümer (eigentuemer_kanon), im Popup und in der Hausansicht", () => {
  const knopf = `<button class="eiglink" data-eigentuemer="Fried. Krupp AG">Fried. Krupp AG</button>`;
  assert.equal(popupZeile(VIELE[5]), `<div class="z" data-eintrag="e1"><b>${knopf}</b> <span class="n">· Industrie</span></div>`);
  const eig = { id: "a1", stufe: "haus", strasse_heute: "Lattenkamp", hausnr: "25", stadtteil: "Katernberg", historisch: "Grenzstr. 25", n_I: 0, n_II: 2, n_III: 0 };
  const e = [{ id: "1", teil: "II", seite: "II-1", name: "", vorname: "", firma: "Fried. Krupp A.G.", eigentuemer: "Eigentümer", eigentuemer_kanon: "Fried. Krupp AG", kategorie: "industrie", flags: [], merkmale: [] },
             { id: "2", teil: "II", seite: "II-1", name: "", vorname: "", firma: "Bauverein GmbH", eigentuemer: "Eigentümer", eigentuemer_kanon: "", kategorie: "", flags: [], merkmale: [] }];
  const h = hausHtml(eig, e);
  assert.ok(h.includes(`Zugeordnet</span> ${knopf} · Industrie`), h);
  assert.equal((h.match(/eiglink/g) || []).length, 1);
});
```

Bestehende Tests anpassen: in „Hausansicht zeigt geprüften Eigentümer mit Kategorie…“ (Z. 59) die Zeile `assert.match(h, /Zugeordnet<\/span> Fried\. Krupp AG · Industrie/);` → `assert.match(h, /Zugeordnet<\/span> <button class="eiglink" data-eigentuemer="Fried\. Krupp AG">Fried\. Krupp AG<\/button> · Industrie/);`. In „popupZeile: Eigentümer mit Kanon und Klasse…“ (Z. 127) die erste Erwartung → `` `<div class="z" data-eintrag="e1"><b><button class="eiglink" data-eigentuemer="Fried. Krupp AG">Fried. Krupp AG</button></b> <span class="n">· Industrie</span></div>` ``.

- [ ] **Step 2: Tests laufen lassen**

Run: `node --test site/tests/vergleich.test.js site/tests/popup.test.js`
Expected: FAIL, `Cannot find module '…/site/js/vergleich.js'` und die Popup-Erwartungen.

- [ ] **Step 3: Implementieren**

`site/js/vergleich.js`:

```js
// Eigentümer-Vergleich (Spec 2026-09-29 §5/§6): reine Hilfsfunktionen ohne DOM und Karte.
import { esc } from "./popup.js";

// Adresse → { gruppe: Index der ersten Gruppe, mehrfach: in mehr als einer Gruppe }
export function gruppenZuordnung(gruppen) {
  const z = new Map();
  gruppen.forEach((g, i) => {
    for (const id of g.adressIds) {
      const alt = z.get(id);
      if (alt) alt.mehrfach = true; else z.set(id, { gruppe: i, mehrfach: false });
    }
  });
  return z;
}

export function mehrfachZahl(gruppen) {
  let n = 0;
  for (const z of gruppenZuordnung(gruppen).values()) if (z.mehrfach) n++;
  return n;
}

// Top n Stadtteile nach Einträgen; Adressen ohne Kurzindex-Eintrag zählen als „unbekannt“.
export function verteilung(adressIds, zaehler, eig, n = 3) {
  const je = new Map();
  for (const id of adressIds) { const s = (eig.get(id) || {}).stadtteil || "unbekannt"; je.set(s, (je.get(s) || 0) + (zaehler.get(id) || 0)); }
  return [...je.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);
}

export function vergleichsleisteHtml(gruppen, eig) {
  const zeilen = gruppen.map((g) => {
    const eintraege = [...g.zaehler.values()].reduce((a, b) => a + b, 0);
    const top = verteilung(g.adressIds, g.zaehler, eig).map(([s, n]) => `${esc(s)} ${n}`).join(" · ");
    return `<div class="zeile"><span class="punkt" style="background:${esc(g.farbe)}"></span> <b>${esc(g.name)}</b> <small>${g.adressIds.length} Häuser · ${eintraege} Einträge</small>` +
      (top ? `<small class="orte">${top}</small>` : "") +
      `<button class="weg" data-eig-weg="${esc(g.name)}" title="${esc(g.name)} entfernen">×</button></div>`;
  });
  const m = mehrfachZahl(gruppen);
  const ring = m ? `<div class="zeile klein">${m} ${m === 1 ? "Haus" : "Häuser"} mit mehreren gewählten Eigentümern (Ring)</div>` : "";
  return `<div class="vergleich">${zeilen.join("")}${ring}</div>`;
}
```

`site/js/popup.js`:

```js
// Geprüfter Eigentümer als Knopf (Spec Eigentümer-Vergleich §7): app.js hängt den Klick an (alle Häuser / zum Vergleich).
function eigKnopf(name) { return `<button class="eiglink" data-eigentuemer="${esc(name)}">${esc(name)}</button>`; }

export function popupZeile(e) {
  const z = popupZusatz(e);
  const name = e.teil === "II" && e.eigentuemer_kanon ? eigKnopf(e.eigentuemer_kanon) : esc(popupName(e));
  return `<div class="z" data-eintrag="${esc(e.id)}"><b>${name}</b>${z ? ` <span class="n">· ${z}</span>` : ""}</div>`;
}
```

In `eintragHtml` das Feld „Zugeordnet“ wird HTML statt Text. Die Felderliste bekommt ein drittes Element `roh` (true = schon HTML):

```js
    ["Zugeordnet", e.eigentuemer_kanon ? `${eigKnopf(e.eigentuemer_kanon)} · ${esc(KATEGORIEN[e.kategorie] || e.kategorie)}`
      : e.pruefung === "regel" ? esc(`${KATEGORIEN[e.kategorie] || e.kategorie} (Regel: Person ohne Firmenname → Privatperson, keine Handprüfung)`) : "", true],
    …
    .filter(([, w]) => w).map(([k, w, roh]) => `<div><span class="k">${k}</span> ${roh ? w : esc(w)}</div>`).join("");
```

`trefferzeileHtml`:

```js
export function trefferzeileHtml(t) {
  // t = { adressId, titel, untertitel, stufe, n, eintragId?, farbe?, mehrfach? } — farbe/mehrfach beim Eigentümer-Vergleich
  const kennText = t.stufe === "stadtplan" ? "Stadtplan 1935" : t.stufe === "unbekannt" ? "Präzision unbekannt" : "nur Straße";
  const kenn = t.stufe === "haus" ? "" : `<span class="kenn">${kennText}</span>`;
  const punkt = t.farbe ? `<span class="punkt" style="background:${esc(t.farbe)}"></span>` : "";
  return `<div class="treffer${t.mehrfach ? " mehrfach" : ""}" data-adresse="${esc(t.adressId)}"${t.eintragId ? ` data-eintrag="${esc(t.eintragId)}"` : ""}>` +
    `${punkt}<b>${esc(t.titel)}</b>${kenn}<small>${esc(t.untertitel)}</small></div>`;
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/*.test.js`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add site/js/vergleich.js site/js/popup.js site/tests/vergleich.test.js site/tests/popup.test.js
git commit -m "feat(vergleich): Gruppenzuordnung, Verteilung, Vergleichsleiste; Trefferzeile mit Farbpunkt/Ring; Eigentümer-Knopf in Popup und Hausansicht

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Karte — Gruppenfarben, Ring, Einpassen über Koordinaten

**Files:**
- Modify: `site/js/karte.js` (Konstanten nach `HALO` Z. 46; `setzeFilter` Z. 282–306; `setzeTreffer` Z. 328–335; `passeEin` Z. 355–363)
- Test: `site/tests/karte_ebenen.test.js`

**Interfaces:**
- Consumes: `gruppenZuordnung` (Task 5), `FARBEN.gruppen`, `FARBEN.auswahl`.
- Produces: `setzeTreffer(adressIds, gruppen = null)`; `passeEin(adressIds, koordinaten = null)` mit `koordinaten: Map<id, [lon, lat]>`; `_rahmen()` liefert `new maplibregl.LngLatBounds()` (in Tests ersetzbar).

- [ ] **Step 1: Failing tests schreiben** (an `site/tests/karte_ebenen.test.js` anhängen; `kartenAttrappe` existiert dort bereits und merkt sich `state`, `paint`, `filter`)

```js
test("setzeTreffer mit Gruppen: Feature-State trägt gruppe (erste) und mehrfach", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "thema-haus", "thema-ungenau"]);
  const self = Object.assign(Object.create(Karte.prototype), { map: a.map, ansicht: null, treffer: new Set() });
  const gruppen = [{ name: "K", farbe: "#dc2626", adressIds: ["x", "y"], zaehler: new Map() }, { name: "S", farbe: "#2563eb", adressIds: ["y", "z"], zaehler: new Map() }];
  Karte.prototype.setzeTreffer.call(self, ["x", "y", "z"], gruppen);
  const st = Object.fromEntries(a.state.map((s) => [s[1], s[2]]));
  assert.deepEqual(st.x, { treffer: true, gruppe: 0, mehrfach: false });
  assert.deepEqual(st.y, { treffer: true, gruppe: 0, mehrfach: true });
  assert.deepEqual(st.z, { treffer: true, gruppe: 1, mehrfach: false });
  Karte.prototype.setzeTreffer.call(self, ["x"]);
  assert.deepEqual(a.state.at(-1)[2], { treffer: true });     // ohne Gruppen wie bisher
});

test("setzeFilter: Trefferfarbe nach Gruppe, Rot ohne Gruppe; Ring über mehrfach auf Kreis und Symbol", () => {
  const filter = {}; const paint = {}; const layout = {};
  const map = { getLayer: () => true, setFilter: (l, f) => { filter[l] = f; }, setPaintProperty: (l, k, v) => { paint[`${l}.${k}`] = v; }, setLayoutProperty: (l, k, v) => { layout[`${l}.${k}`] = v; } };
  const self = { map, farbe: null, ansicht: null, treffer: new Set(), _deckkraftSetzen() {} };
  Karte.prototype.setzeFilter.call(self, { ebene: ["I"], praez: ["haus"], stadtteil: "" });
  const farbe = paint["adressen-haus.circle-color"];
  assert.equal(farbe[0], "case");
  assert.deepEqual(farbe[2], ["match", ["coalesce", ["feature-state", "gruppe"], -1], 0, "#dc2626", 1, "#2563eb", 2, "#16a34a", 3, "#7c3aed", 4, "#f59e0b", "#dc2626"]);
  const mehrfach = ["boolean", ["feature-state", "mehrfach"], false];
  assert.deepEqual(paint["adressen-haus.circle-stroke-color"], ["case", mehrfach, "#111827", "#fff"]);
  assert.deepEqual(paint["adressen-haus.circle-stroke-width"], ["interpolate", ["linear"], ["zoom"], 12, ["case", mehrfach, 2, 0], 14, ["case", mehrfach, 2, 1], 16, ["case", mehrfach, 2.4, 1.6]]);
  assert.deepEqual(paint["adressen-ungenau.icon-halo-color"], ["case", mehrfach, "#111827", "#fff"]);
  assert.deepEqual(paint["thema-haus.circle-stroke-color"], paint["adressen-haus.circle-stroke-color"]);
});

test("passeEin mit Koordinaten aus dem Kurzindex braucht keine Kachelabfrage", () => {
  const punkte = []; let fit = null;
  const rahmen = { extend: (p) => punkte.push(p) };
  const self = { map: { querySourceFeatures: () => { throw new Error("nicht erwartet"); }, fitBounds: (b, o) => { fit = [b, o]; } }, _rahmen: () => rahmen };
  const ok = Karte.prototype.passeEin.call(self, ["a", "b", "c"], new Map([["a", [7.0, 51.4]], ["b", [7.1, 51.5]]]));
  assert.equal(ok, true);
  assert.deepEqual(punkte, [[7.0, 51.4], [7.1, 51.5]]);     // c fehlt im Kurzindex → übersprungen
  assert.equal(fit[0], rahmen); assert.equal(fit[1].maxZoom, 16);
  assert.equal(Karte.prototype.passeEin.call(self, ["c"], new Map()), false);
});
```

- [ ] **Step 2: Tests laufen lassen**

Run: `node --test site/tests/karte_ebenen.test.js`
Expected: FAIL — `st.x` ist `{ treffer: true }`; `farbe[2]` ist `"#dc2626"`; `passeEin` wirft „nicht erwartet“.

- [ ] **Step 3: Implementieren**

Import oben in `karte.js`: `import { gruppenZuordnung } from "./vergleich.js";`

Konstanten nach `HALO`:

```js
// Eigentümer-Vergleich (Spec 2026-09-29 §5): Trefferfarbe nach Gruppe (Feature-State), Rot ohne Gruppe.
const TREFFER_FARBE = ["match", ["coalesce", ["feature-state", "gruppe"], -1], ...FARBEN.gruppen.flatMap((f, i) => [i, f]), FARBEN.treffer];
// Ring um Häuser in mehreren gewählten Gruppen. Der Zoom-Ausdruck muss außen bleiben (MapLibre), die
// Fallunterscheidung sitzt deshalb in den Stützwerten.
const MEHRFACH = ["boolean", ["feature-state", "mehrfach"], false];
const RING_FARBE = ["case", MEHRFACH, FARBEN.auswahl, "#fff"];
const RING_BREITE = ["interpolate", ["linear"], ["zoom"], 12, ["case", MEHRFACH, 2, 0], 14, ["case", MEHRFACH, 2, 1], 16, ["case", MEHRFACH, 2.4, 1.6]];
```

In `setzeFilter`: `const farbe = ["case", ["boolean", ["feature-state", "treffer"], false], FARBEN.treffer, grund];` → `… false], TREFFER_FARBE, grund];` und in der Schleife nach `circle-radius`:

```js
      m.setPaintProperty(hausId, "circle-stroke-color", RING_FARBE);
      m.setPaintProperty(hausId, "circle-stroke-width", RING_BREITE);
      m.setPaintProperty(ungenauId, "icon-halo-color", RING_FARBE);
      m.setPaintProperty(ungenauId, "icon-halo-width", RING_BREITE);
```

`setzeTreffer`:

```js
  // Treffer per Feature-State: alle bisherigen zurücksetzen, neue setzen, Rest dimmen. Mit Gruppen
  // (Eigentümer-Vergleich) trägt jede Adresse ihre erste Gruppe und ob sie in mehreren liegt.
  setzeTreffer(adressIds, gruppen = null) {
    const m = this.map;
    if (!m.getSource("adressen")) return;
    const quellen = [["adressen", "adressen"], ...(m.getSource("thema") ? [["thema", "adressen"]] : [])];
    for (const [source, sourceLayer] of quellen) m.removeFeatureState({ source, sourceLayer });
    this.treffer = new Set(adressIds || []);
    const zuordnung = gruppen ? gruppenZuordnung(gruppen) : null;
    for (const [source, sourceLayer] of quellen) for (const id of this.treffer) {
      const z = zuordnung && zuordnung.get(id);
      m.setFeatureState({ source, sourceLayer, id }, z ? { treffer: true, gruppe: z.gruppe, mehrfach: z.mehrfach } : { treffer: true });
    }
    this._deckkraftSetzen();
  }
```

`passeEin`:

```js
  _rahmen() { return new maplibregl.LngLatBounds(); }

  // Auf die Treffer einpassen. Mit Koordinaten (Kurzindex) ohne Kachelabfrage; sonst nur auf die
  // geladenen Treffer — nicht geladene Kacheln kennen wir nicht → dann kein Zoom.
  passeEin(adressIds, koordinaten = null) {
    const b = this._rahmen();
    let n = 0;
    if (koordinaten) {
      for (const id of adressIds) { const k = koordinaten.get(id); if (k) { b.extend(k); n++; } }
    } else {
      const ids = new Set(adressIds);
      for (const x of this.map.querySourceFeatures("adressen", { sourceLayer: "adressen" })) if (ids.has(x.properties.id)) { b.extend(x.geometry.coordinates); n++; }
    }
    if (!n) return false;
    this.map.fitBounds(b, { padding: 60, maxZoom: 16, duration: 600 });
    return true;
  }
```

`kartenAttrappe` (Z. 73–84 der Testdatei) schreibt `paint[…]`, `layout[…]` und `state` generisch; `getLayer` liefert für alle übergebenen Ebenen ein Objekt — deshalb im Gruppen-Test alle vier Ebenen angeben.

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/*.test.js`
Expected: PASS. Der Test „Adresspunkte tragen einen weißen Halo“ bleibt grün, weil die Ebenendefinition unverändert ist; `setzeFilter` überschreibt die Werte erst zur Laufzeit.

- [ ] **Step 5: Commit**

```bash
git add site/js/karte.js site/tests/karte_ebenen.test.js
git commit -m "feat(karte): Trefferfarbe je Gruppe über Feature-State, Ring bei Mehrfachtreffern, Einpassen über Kurzindex-Koordinaten

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Sidebar — Vergleichsleiste, farbige Knöpfe, Plus am Vorschlag, Hinweis

**Files:**
- Modify: `site/js/sidebar.js` (`setzeVorschlaege` Z. 32–46, `zeigeTreffer` Z. 75–91, `_verteilung` Z. 100–105, `zeigeThema` Z. 127–138, `_klick` Z. 186–195)
- Modify: `site/css/stil.css` (nach Z. 66 und Z. 104)

Die Sidebar hat keine Unit-Tests (DOM); reine Logik liegt in `vergleich.js` (Task 5). Die Sichtprüfung in Task 9 deckt diese Task ab.

**Interfaces:**
- Consumes: `vergleichsleisteHtml`, `gruppenZuordnung` (Task 5); `ergebnis.gruppen` (Task 4); `z.eigentuemer` als Liste (Task 3).
- Produces: Aktion `this.a.onEigentuemer(name, umschalten)` (app.js liefert sie in Task 9); `setzeVorschlaege(g, plus = false)`; `zeigeThema(thema, groesste, gewaehlt = [])`; `markiereEigentuemer(namen, farben)`; `zeigeHinweis(text)`.

- [ ] **Step 1: Import und Vorschläge**

Import: `import { vergleichsleisteHtml, gruppenZuordnung } from "./vergleich.js";`

`setzeVorschlaege(g, plus = false)`: in der Schleife die Eintragszeile ersetzen durch

```js
        const zusatz = plus && k === "eigentuemer" ? `<span class="plus" title="zum Vergleich hinzufügen">+</span>` : "";
        html += `<div class="eintrag" data-index="${liste.length}">${esc(v.text)}${zusatz}<small>${esc(v.untertitel)}</small></div>`;
```

- [ ] **Step 2: `zeigeTreffer` mit Gruppen**

```js
  zeigeTreffer(z, ergebnis, eig, titel) {
    this.pills.innerHTML = this._pillsHtml(z);
    const n = ergebnis.personen ? ergebnis.personen.length : [...ergebnis.zaehler.values()].reduce((a, b) => a + b, 0);
    let html = this._filterHtml(z);
    // Eigentümer-Vergleich (Spec 2026-09-29 §6): Leiste je Gruppe vor der Kopfzeile, Farbpunkt je Zeile, Gruppenreihenfolge.
    const zuordnung = ergebnis.gruppen ? gruppenZuordnung(ergebnis.gruppen) : null;
    if (ergebnis.gruppen) html += vergleichsleisteHtml(ergebnis.gruppen, eig);
    html += `<div class="kopf"><b>${n} Treffer</b> · ${ergebnis.adressIds.length} Häuser` +
      `<button class="export" data-export="1">CSV</button></div>`;
    if (ergebnis.hinweisHJ) html += `<div class="hinweis warn">Keine Treffer. Die Namen H bis J fehlen in der Vorlage (Seiten 186–258 des Teils I). Straßen und Firmen sind nicht betroffen.</div>`;
    const ids = zuordnung ? [...ergebnis.adressIds].sort((a, b) => zuordnung.get(a).gruppe - zuordnung.get(b).gruppe) : ergebnis.adressIds;
    const zeilen = ergebnis.personen
      ? ergebnis.personen.map((p) => ({ adressId: p.adressId, eintragId: p.eintragId, titel: p.text, untertitel: p.untertitel, stufe: (eig.get(p.adressId) || {}).stufe || "unbekannt" }))
      : ids.map((id) => { const e = eig.get(id) || {}; const g = zuordnung && zuordnung.get(id);
          return { adressId: id, titel: e.historisch ? heutigeAdresse(e) : id, untertitel: `${ergebnis.zaehler.get(id)} Einträge${e.historisch ? " · " + e.historisch : ""}`, stufe: e.stufe || "unbekannt",
                   farbe: g ? ergebnis.gruppen[g.gruppe].farbe : undefined, mehrfach: !!(g && g.mehrfach) }; });
    this._alleZeilen = zeilen; this._gezeigt = 0;
    html += `<div class="liste" id="liste"></div><button class="mehr" data-mehr="1" hidden>weitere 50</button>`;
    this.inhalt.innerHTML = html;
    this._filterEreignisse(z);
    this._mehrZeilen();
    if (!ergebnis.gruppen && ergebnis.adressIds.length >= 500) this._verteilung(ergebnis, eig);
  }
```

- [ ] **Step 3: „Größte Eigentümer“ mit Auswahlzustand, Hinweis**

```js
  zeigeThema(thema, groesste = null, gewaehlt = [], farben = []) {
    if (!thema) { this.themenkopf.hidden = true; this.themenkopf.innerHTML = ""; return; }
    this.themenkopf.innerHTML = `<div class="thema"><b>${esc(thema.titel)}</b><p>${esc(thema.text)}</p><small>${esc(thema.grundlage)}</small>` +
      `<button data-thema-aus="1">Thema verlassen</button></div>`;
    this.themenkopf.hidden = false;
    this.themenkopf.querySelector("[data-thema-aus]").addEventListener("click", () => this.a.onZustand({ thema: "" }));
    if (groesste && groesste.length) {
      this.themenkopf.insertAdjacentHTML("beforeend", `<div class="gruppe">Größte Eigentümer</div><div class="eigentuemerliste">` +
        groesste.slice(0, 30).map((z) => `<button class="themaknopf" data-eigentuemer="${esc(z[1])}" aria-pressed="false">${esc(z[1])} <small>${z[2]}</small></button>`).join("") + `</div>`);
      // Klick schaltet um: gewählt → entfernen, sonst anhängen (app.js prüft die Höchstzahl)
      this.themenkopf.querySelectorAll("[data-eigentuemer]").forEach((b) => b.addEventListener("click", () => this.a.onEigentuemer(b.dataset.eigentuemer, true)));
      this.markiereEigentuemer(gewaehlt, farben);
    }
  }

  // Gewählte Eigentümer-Knöpfe in ihrer Gruppenfarbe füllen (Spec 2026-09-29 §6).
  markiereEigentuemer(namen, farben) {
    this.themenkopf.querySelectorAll("[data-eigentuemer]").forEach((b) => {
      const i = namen.indexOf(b.dataset.eigentuemer);
      b.setAttribute("aria-pressed", String(i >= 0));
      b.style.background = i >= 0 ? farben[i] : ""; b.style.color = i >= 0 ? "#fff" : ""; b.style.borderColor = i >= 0 ? farben[i] : "";
    });
  }

  // Kurzer Hinweis oben im Inhalt (z. B. „Höchstens fünf Eigentümer“), verschwindet nach 2 s.
  zeigeHinweis(text) {
    const el = document.createElement("div"); el.className = "hinweis warn fluechtig"; el.textContent = text;
    this.inhalt.prepend(el);
    setTimeout(() => el.remove(), 2000);
  }
```

In `_klick` vor der `.treffer`-Zeile:

```js
    const weg = t.closest("[data-eig-weg]"); if (weg) return this.a.onEigentuemer(weg.dataset.eigWeg, true);
    const eig = t.closest("[data-eigentuemer]"); if (eig) return this.a.onEigentuemer(eig.dataset.eigentuemer, false);
```

- [ ] **Step 4: CSS** (`site/css/stil.css`)

Nach Z. 66 (`.treffer b …`):

```css
.treffer .punkt { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; vertical-align: middle; }
.treffer.mehrfach .punkt { box-shadow: 0 0 0 2px #fff, 0 0 0 4px #111827; }
.vergleich { padding: 6px 0 2px; border-bottom: 1px solid var(--rand); }
.vergleich .zeile { display: flex; align-items: center; gap: 6px; padding: 3px 0; font-size: 13px; flex-wrap: wrap; }
.vergleich .zeile .punkt { width: 12px; height: 12px; border-radius: 50%; display: inline-block; flex: none; }
.vergleich .zeile small { color: var(--grau); }
.vergleich .zeile .orte { flex-basis: 100%; padding-left: 18px; }
.vergleich .weg { margin-left: auto; border: 0; background: none; font-size: 16px; cursor: pointer; color: var(--grau); }
.vergleich .zeile.klein { font-size: 12px; color: var(--grau); }
.eiglink { border: 0; background: none; padding: 0; font: inherit; color: var(--blau); cursor: pointer; text-decoration: underline dotted; }
.vorschlaege .plus { margin-left: 6px; color: var(--blau); font-weight: bold; }
.hinweis.fluechtig { margin: 4px 0; }
```

Nach Z. 104 (`.eigentuemerliste .themaknopf small`):

```css
.eigentuemerliste .themaknopf[aria-pressed="true"] small { color: #fff; opacity: .8; }
```

Die Vorschlagsliste heißt im CSS `.vorschlaege` (Z. 13), der `.plus`-Selektor oben passt.

- [ ] **Step 5: Syntaxprüfung und Commit**

Run: `node --check site/js/sidebar.js && node --test site/tests/*.test.js`
Expected: kein Syntaxfehler, Tests PASS.

```bash
git add site/js/sidebar.js site/css/stil.css
git commit -m "feat(sidebar): Vergleichsleiste je Eigentümer, farbige Auswahlknöpfe, Plus am Suchvorschlag, flüchtiger Hinweis

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: CSV mit Spalte `eigentuemer`

**Files:**
- Modify: `site/js/exportcsv.js` Z. 7–8, 17–36
- Test: `site/tests/exportcsv.test.js`

**Interfaces:**
- Consumes: `ergebnis.gruppen` (Task 4).
- Produces: `csvAusTreffern(ergebnis, lader, eig, maxEintraege)` mit letzter Spalte `eigentuemer`, wenn `ergebnis.gruppen` gesetzt ist.

- [ ] **Step 1: Failing test schreiben** (anhängen)

```js
test("Eigentümer-Vergleich: Spalte eigentuemer, Adresse in zwei Gruppen erscheint je Gruppe", async () => {
  const gruppen = [{ name: "Krupp", farbe: "#dc2626", adressIds: ["a1"], zaehler: new Map([["a1", 2]]) }, { name: "Stadt", farbe: "#2563eb", adressIds: ["a1"], zaehler: new Map([["a1", 1]]) }];
  const erg = { adressIds: ["a1"], zaehler: new Map([["a1", 3]]), personen: null, gruppen };
  const voll = (await csvAusTreffern(erg, l, EIG)).split("\r\n");
  assert.ok(voll[0].endsWith(",adress_id,eigentuemer"));
  assert.equal(voll.filter((z) => z.endsWith(",Krupp")).length, 2);
  assert.equal(voll.filter((z) => z.endsWith(",Stadt")).length, 2);
  const kurz = (await csvAusTreffern(erg, l, EIG, 1)).split("\r\n");
  assert.equal(kurz[0].replace("﻿", ""), "adress_id,adresse_heute,adresse_1936,stadtteil,praezision,eintraege,eigentuemer");
  assert.equal(kurz[1], "a1,\"Lattenkamp 25, Katernberg\",\"Grenzstr. 25, Katernberg\",Katernberg,haus,2,Krupp");
  assert.equal(kurz[2], "a1,\"Lattenkamp 25, Katernberg\",\"Grenzstr. 25, Katernberg\",Katernberg,haus,1,Stadt");
});
```

- [ ] **Step 2: Test laufen lassen**

Run: `node --test site/tests/exportcsv.test.js`
Expected: FAIL, Kopfzeile endet auf `adress_id`.

- [ ] **Step 3: Implementieren**

```js
export async function csvAusTreffern(ergebnis, lader, eig, maxEintraege = 5000) {
  const gesamt = [...ergebnis.zaehler.values()].reduce((a, b) => a + b, 0);
  const zeilen = [];
  const adr = (id) => { const e = eig.get(id) || {}; return [e.historisch ? heutigeAdresse(e) : "", e.historisch || "", e.stadtteil || "", e.stufe || ""]; };
  // Eigentümer-Vergleich (Spec 2026-09-29 §8): eine Spalte mit dem Gruppennamen; ohne Gruppen ein Block ohne Zusatzspalte.
  const bloecke = ergebnis.gruppen
    ? ergebnis.gruppen.map((g) => ({ ids: g.adressIds, zaehler: g.zaehler, zusatz: [g.name] }))
    : [{ ids: ergebnis.adressIds, zaehler: ergebnis.zaehler, zusatz: [] }];
  const kopfZusatz = ergebnis.gruppen ? ["eigentuemer"] : [];
  if (gesamt <= maxEintraege) {
    zeilen.push(csvZeile([...KOPF_E, ...kopfZusatz]));
    const nurIds = ergebnis.personen ? new Set(ergebnis.personen.map((p) => p.eintragId)) : null;
    for (const b of bloecke) for (const id of b.ids) {
      const eintraege = (await lader.scherbe(id)) || [];
      for (const e of eintraege) {
        if (nurIds && !nurIds.has(e.id)) continue;
        zeilen.push(csvZeile([e.id, e.teil, e.seite, e.name, e.vorname, e.beruf, e.etage, e.stand, ...adr(id), (e.flags || []).join(";"), id, ...b.zusatz]));
      }
    }
  } else {
    zeilen.push(csvZeile([...KOPF_A, ...kopfZusatz]));
    for (const b of bloecke) for (const id of b.ids) zeilen.push(csvZeile([id, ...adr(id), b.zaehler.get(id), ...b.zusatz]));
  }
  return "﻿" + zeilen.join("\r\n") + "\r\n";
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test site/tests/exportcsv.test.js`
Expected: PASS (bestehende zwei Exporttests unverändert grün).

- [ ] **Step 5: Commit**

```bash
git add site/js/exportcsv.js site/tests/exportcsv.test.js
git commit -m "feat(csv): Spalte eigentuemer beim Vergleich, Adresse je Gruppe einmal

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: `app.js` verdrahten, Datenpaket, Sichtprüfung

**Files:**
- Modify: `site/js/app.js` (Import Z. 5; `eigVon`/`eigMap` Z. 79–86, 188–192; `setzeZustand` Z. 115–125; `wendeThemaAn` Z. 141; `sucheAusfuehren` Z. 195–208; `waehleVorschlag` Z. 210–217; `klickPunkt` Z. 271–283; `zeichneLegende` Z. 365–370; `exportiere` Z. 382–385; Suchfeld Z. 392, 407, 415; `start` Z. 429; Sidebar-Aktionen Z. 59–66; Vorschläge Z. 396)
- Datenpaket: `python3 pipeline/06_karte_export.py`

**Interfaces:**
- Consumes: alles aus Task 2–8.
- Produces: Aktion `onEigentuemer(name, umschalten)`; laufende Karte.

- [ ] **Step 1: Import und Aktion**

`import { liesZustand, schreibeZustand, MAX_EIGENTUEMER } from "./zustand.js";` und `import { mehrfachZahl } from "./vergleich.js";`

Sidebar-Aktionen ergänzen: `onEigentuemer: (name, umschalten) => eigentuemerWaehlen(name, umschalten),`

Nach `eigVon` einfügen:

```js
// Eigentümer-Vergleich (Spec 2026-09-29 §6/§7): Name anhängen, bei umschalten=true einen gewählten entfernen;
// höchstens MAX_EIGENTUEMER, sonst Hinweis. Beruf/OhdAB/q schließen Eigentümer aus (wie bisher).
function eigentuemerWaehlen(name, umschalten) {
  const alt = zustand.eigentuemer;
  let neu;
  if (alt.includes(name)) { if (!umschalten) return; neu = alt.filter((n) => n !== name); }
  else if (alt.length >= MAX_EIGENTUEMER) { sidebar.zeigeHinweis(`Höchstens ${MAX_EIGENTUEMER} Eigentümer gleichzeitig.`); return; }
  else neu = [...alt, name];
  sidebar.setzeVorschlaege(null);
  setzeZustand({ eigentuemer: neu, q: "", beruf: "", ohdab: "", id: "" }, true);
}
```

- [ ] **Step 2: Kurzindex statt Kachelabfrage**

`eigMap` ersetzen:

```js
// Kurzindex (Spec 2026-09-29 §2): Adresse, Stadtteil, Koordinaten für Liste, Leiste und Einpassen — kein
// Nachladen fetter Adressscherben, keine Kachelabfrage je Haus.
async function eigMap(ids) { return lader.adressenKurz(ids); }
```

`setzeZustand` (Z. 115–125): Bedingung `alt.eigentuemer !== zustand.eigentuemer` → `alt.eigentuemer.join("|") !== zustand.eigentuemer.join("|")`; `else if (zustand.eigentuemer)` → `else if (zustand.eigentuemer.length) auswahl = { art: "eigentuemer", namen: zustand.eigentuemer };`; die Zeile `if (zustand.eigentuemer) sidebar.suche.value = zustand.eigentuemer;` → `if (zustand.eigentuemer.length) sidebar.suche.value = zustand.eigentuemer.length === 1 ? zustand.eigentuemer[0] : "";` und danach `sidebar.markiereEigentuemer(zustand.eigentuemer, FARBEN.gruppen);`.

`wendeThemaAn`: `sidebar.zeigeThema(t, …, zustand.eigentuemer, FARBEN.gruppen);` (dritter und vierter Parameter).

`sucheAusfuehren`:

```js
    ergebnis = await treffer(auswahl, lader);
    karte.setzeTreffer(ergebnis.adressIds, ergebnis.gruppen);
    const eig = await eigMap(ergebnis.adressIds);
    const koordinaten = new Map([...eig.values()].map((e) => [e.id, [e.lon, e.lat]]));
    if (ergebnis.adressIds.length) karte.passeEin(ergebnis.adressIds, koordinaten);
    sidebar.zeigeTreffer(zustand, ergebnis, eig, zustand.q);
    zeichneLegende();
    sidebar.setzeStufe("halb");
```

(`zeigeInhalt` bleibt für den Fall ohne Auswahl; der `once("idle")`-Zweig entfällt.)

`waehleVorschlag`: `if (v.art === "eigentuemer") return eigentuemerWaehlen(v.name, false);` (statt `setzeZustand({… eigentuemer: v.name})`); die Zeile `sidebar.suche.value = v.text;` bleibt, `eigentuemerWaehlen` setzt das Feld über `setzeZustand` passend.

Vorschläge (Z. 396): `sidebar.setzeVorschlaege(await vorschlaege(sidebar.suche.value, lader), zustand.eigentuemer.length > 0);`

Suchfeld-Initialisierung (Z. 392, 415): `sidebar.suche.value = zustand.q || (zustand.eigentuemer.length === 1 ? zustand.eigentuemer[0] : "") || zustand.ohdab || "";`

„Suche leeren“ (Z. 407): `eigentuemer: []` statt `""`. Ebenso Z. 249 (`sucheAusText`) und `waehleVorschlag` Beruf/OhdAB: `eigentuemer: []`.

`start` (Z. 429): `else if (zustand.eigentuemer.length) auswahl = { art: "eigentuemer", namen: zustand.eigentuemer };`

`exportiere`: `herunterladen(csv, zustand.eigentuemer.length > 1 ? "essen1936-eigentuemer-vergleich.csv" : \`essen1936-${(zustand.q || zustand.beruf || zustand.eigentuemer[0] || zustand.ohdab || "treffer").replace(/[^\w]+/g, "_")}.csv\`);`

`klickPunkt` nach den `[data-mehr]`-Handlern: `el.querySelectorAll("[data-eigentuemer]").forEach((n) => n.addEventListener("click", () => eigentuemerWaehlen(n.dataset.eigentuemer, false)));` — der Knopf in der Hausansicht läuft über `sidebar._klick` (Task 7).

`zeichneLegende` (Z. 367): die Zeile `Suchtreffer` ersetzen durch

```js
  if (ergebnis && ergebnis.gruppen) {
    for (const g of ergebnis.gruppen) html += `<div class="zeile"><span class="punkt" style="background:${esc(g.farbe)}"></span> ${esc(g.name)}</div>`;
    if (mehrfachZahl(ergebnis.gruppen)) html += `<div class="zeile"><span class="punkt ring"></span> mehrere gewählte Eigentümer</div>`;
  } else html += `<div class="zeile"><span class="punkt" style="background:${FARBEN.treffer}"></span> Suchtreffer</div>`;
```

CSS für `.legende .punkt.ring { background: none !important; border: 2px solid #111827; }` in `stil.css` nach Z. 40.

- [ ] **Step 3: Syntax und Suiten**

Run: `node --check site/js/app.js && node --test site/tests/*.test.js && python3 -m pytest -q`
Expected: kein Syntaxfehler, beide Suiten grün.

- [ ] **Step 4: Datenpaket bauen**

Run: `python3 pipeline/06_karte_export.py > /tmp/export.log 2>&1; ls -la site/daten/adressen_kurz | head -5; du -sh site/daten/adressen_kurz`
Expected: 16 Dateien, zusammen etwa 4–5 MB; Größe der größten Datei ins Journal.

- [ ] **Step 5: Sichtprüfung (Playwright, Dev-Server `python3 werkzeuge/serve.py 8765`)**

Skript im Scratchpad, Kernpunkte:

1. `karte.html?thema=besitz&eigentuemer=Fried.+Krupp+AG|Stadt+Essen&debug=1` laden, 9 s warten, Konsole auf `error` prüfen (Review Focus 5): erwartet keine Fehler.
2. `document.querySelectorAll(".vergleich .zeile b").length === 2`, Leiste nennt „Fried. Krupp AG“ und „Stadt Essen“ mit Häuserzahlen 3351 und 2069.
3. Zwei gefüllte Knöpfe: `[data-eigentuemer][aria-pressed="true"]` = 2, Hintergrundfarben `#dc2626`, `#2563eb`.
4. `__karte.map.queryRenderedFeatures({layers:["thema-haus"]})`, gefiltert nach `state.gruppe === 1`, Länge > 0.
5. Zeitmessung: `performance.now()` vor Klick auf den Knopf „Essener Bergwerks-Verein König Wilhelm“, bis `.vergleich` drei Zeilen zeigt: erwartet unter 1.500 ms bei warmem Cache.
6. Klick auf `×` bei „Stadt Essen“: URL enthält `eigentuemer=Fried.+Krupp+AG|Essener+Bergwerks-Verein+K%C3%B6nig+Wilhelm` (oder Umlaut roh), Leiste zwei Zeilen.
7. Legende: Zeilen je Gruppe vorhanden, „Suchtreffer“ fehlt.
8. Popup auf einen Krupp-Punkt nahe der Bildmitte: `.eiglink` vorhanden; Klick fügt nichts Neues hinzu (schon gewählt); Popup auf ein Stadt-Essen-Haus nach Entfernen: Klick fügt „Stadt Essen“ wieder hinzu.
9. Sechs Knöpfe nacheinander klicken: nach dem sechsten erscheint `.hinweis.fluechtig` mit „Höchstens 5“.
10. Alter Link `karte.html?eigentuemer=Stadt+Essen` (ohne Thema): eine Gruppe, rote Punkte, Suchfeld zeigt „Stadt Essen“.

Screenshots `.playwright-mcp/vergleich_*.png` ansehen.

- [ ] **Step 6: Commit**

```bash
git add site/js/app.js site/css/stil.css
git commit -m "feat(karte): Eigentümer-Vergleich verdrahtet — Kurzindex statt Kachelabfrage, Mehrfachauswahl mit Farben, Legende, CSV-Name, Knöpfe aus Popup und Hausansicht

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Doku und Journal

**Files:**
- Modify: `docs/superpowers/specs/2026-09-24-perspektiven-werkstatt-design.md` §10 „Später“
- Modify: `README.md` Abschnitt Karte/URL-Parameter (Zeile mit `eigentuemer=` suchen: `grep -n "eigentuemer=" README.md`)
- Journal `~/Projekte/obsidian-chris/10-Projekte/adressbuch-essen-1936-v2/Journal.md`

- [ ] **Step 1: Werkstatt-Spec §10 ergänzen**

```
- Eigentümer-Vergleich (2026-09-29): Bündelung mehrerer kanonischer Namen zu einer Gruppe mit einer Farbe
  („Krupp gesamt“), und „Meine Ansichten“ im Browser — beides bewusst nicht im Kartenpaket, sondern hier.
```

- [ ] **Step 2: README**

Bei der Beschreibung des URL-Parameters `eigentuemer=` ergänzen: „bis zu fünf Namen, Trenner `|`; Farbe nach Platz (Rot, Blau, Grün, Violett, Orange), Ring bei Häusern in mehreren Gruppen; Vergleichsleiste mit Häusern, Einträgen und Top-3-Stadtteilen; CSV mit Spalte `eigentuemer` (Spec 2026-09-29-eigentuemer-vergleich).“

- [ ] **Step 3: Journal-Eintrag** „2026-09-29 — Eigentümer-Vergleich“: Ursache der Wartezeit (Adressscherben 143 KB × 256, Kachelabfrage je Haus), Kurzindex mit gemessenen Größen, Mehrfachauswahl, Ring, gemessene Zeit aus Task 9 Schritt 5, Stolperer.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/superpowers/specs/2026-09-24-perspektiven-werkstatt-design.md
git commit -m "docs: Eigentümer-Vergleich im README, Bündelung und Meine Ansichten in der Werkstatt-Spec vermerkt

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```
