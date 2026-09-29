import test from "node:test";
import assert from "node:assert/strict";
import { Karte } from "../js/karte.js";

const HALO = ["interpolate", ["linear"], ["zoom"], 12, 0, 14, 1, 16, 1.6];
const ebenen = () => Karte.prototype._eigeneEbenen.call(null);
const ebene = (id) => ebenen().find((e) => e.id === id);

test("Adresspunkte tragen einen weißen Halo, der mit dem Zoom wächst", () => {
  const haus = ebene("adressen-haus");
  assert.equal(haus.paint["circle-stroke-color"], "#fff");
  assert.deepEqual(haus.paint["circle-stroke-width"], HALO);
  const ungenau = ebene("adressen-ungenau");
  assert.equal(ungenau.paint["icon-halo-color"], "#fff");
  assert.deepEqual(ungenau.paint["icon-halo-width"], HALO);
});

// Attrappe der Karte: merkt sich gesetzte Paint-Eigenschaften.
function attrappe(ansicht = null, treffer = new Set()) {
  const paint = {};
  const map = { getLayer: () => true, setPaintProperty: (l, k, v) => { paint[`${l}.${k}`] = v; } };
  return { paint, self: { map, ansicht, treffer } };
}

test("_deckkraftSetzen setzt stroke-opacity gleich circle-opacity", () => {
  const { paint, self } = attrappe(null, new Set(["a"]));
  Karte.prototype._deckkraftSetzen.call(self);
  assert.deepEqual(paint["adressen-haus.circle-stroke-opacity"], paint["adressen-haus.circle-opacity"]);
  assert.deepEqual(paint["adressen-haus.circle-opacity"], ["case", ["boolean", ["feature-state", "treffer"], false], 0.9, 0.25]);
});

import { readFileSync } from "node:fs";

test("Zechen-Ebene: SDF-Symbol mit Farbe und Halo, Größe etwa 22 px", () => {
  const z = ebene("zechen");
  assert.equal(z.paint["icon-color"], "#111");
  assert.equal(z.paint["icon-halo-color"], "#fff");
  assert.equal(z.paint["icon-halo-width"], 1.5);
  assert.equal(z.layout["icon-size"], 0.7);   // ladeIcon lädt 64 px bei pixelRatio 2 → 32 CSS-px × 0,7 ≈ 22 px
});

test("zeche.svg: bereinigte Commons-Datei, ein Pfad, viewBox, unter 4 KB", () => {
  const svg = readFileSync(new URL("../bilder/zeche.svg", import.meta.url), "utf8");
  assert.ok(svg.length < 4096, `Größe ${svg.length}`);
  assert.match(svg, /^<svg xmlns="http:\/\/www\.w3\.org\/2000\/svg" viewBox="0 0 430 430" width="430" height="430">/);
  assert.equal((svg.match(/<path/g) || []).length, 1);
  assert.doesNotMatch(svg, /inkscape|sodipodi|<\?xml|<metadata/);
  assert.match(svg, /Wikimedia Commons/);   // Herkunftskommentar in der Datei
});

test("setzeFilter: Schalterfilter des Themas wird Teil des Adressfilters", () => {
  const filter = {}; const paint = {};
  const map = { getLayer: () => true, setFilter: (l, f) => { filter[l] = f; }, setPaintProperty: (l, k, v) => { paint[`${l}.${k}`] = v; }, setLayoutProperty: () => {} };
  const self = { map, farbe: { ausdruck: "#111", filter: ["any", [">", ["coalesce", ["get", "n_bb_leitung"], 0], 0]] }, ansicht: null, treffer: new Set(), _deckkraftSetzen() {} };
  Karte.prototype.setzeFilter.call(self, { ebene: ["I"], praez: ["haus"], stadtteil: "" });
  assert.ok(JSON.stringify(filter["adressen-haus"]).includes('"n_bb_leitung"'));
  self.farbe = { ausdruck: "#111", filter: null };
  Karte.prototype.setzeFilter.call(self, { ebene: ["I"], praez: ["haus"], stadtteil: "" });
  assert.ok(!JSON.stringify(filter["adressen-haus"]).includes("n_bb_"));
});

const RADIUS = ["interpolate", ["linear"], ["ln", ["max", ["var", "n"], 1]], 0, 4, Math.log(100), 10];

test("Themenebenen: gleiches Paar wie die Hauptpunkte, Quelle thema, Radius wächst mit dem Zoom", () => {
  const e = Karte.prototype._themaEbenen.call(null);
  assert.deepEqual(e.map((l) => l.id).slice(0, 2), ["thema-haus", "thema-ungenau"]);
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
  const self = Object.assign(Object.create(Karte.prototype), { map: a.map, zustand: { ebene: ["I"], praez: ["haus"], stadtteil: "" }, farbe: null, ansicht: null, treffer: new Set(), themaId: null, _handlerAngehaengt: true, _themaQuelle: () => ({ type: "vector" }) });
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
  // MapLibre: ein "zoom"-Ausdruck darf nur Eingabe eines äußeren interpolate/step sein (let außen ist erlaubt, "/" nicht).
  const icon = a.layout["thema-ungenau.icon-size"];
  assert.equal(icon[0], "let"); assert.equal(icon[3][0], "interpolate"); assert.deepEqual(icon[3][2], ["zoom"]);
  assert.deepEqual(icon[3].slice(3), [10, 1 / 16, 12, 2 / 16, 14, ["/", RADIUS, 16]]);
});

test("setzeTreffer und Deckkraft wirken auf Haupt- und Themenquelle", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "thema-haus", "thema-ungenau"]); a.q.add("thema");
  const self = Object.assign(Object.create(Karte.prototype), { map: a.map, ansicht: null, treffer: new Set() });
  Karte.prototype.setzeTreffer.call(self, ["x"]);
  assert.deepEqual(a.state.filter((s) => s[1] === "x").map((s) => s[0]).sort(), ["adressen", "thema"]);
  assert.deepEqual(a.paint["thema-haus.circle-opacity"], a.paint["adressen-haus.circle-opacity"]);
});

test("ebenenAufsetzen legt die Themenquelle nach einem Stilwechsel neu an", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "stadtteile-flaeche"]);
  const self = Object.assign(Object.create(Karte.prototype), { map: a.map, zustand: { ebene: ["I"], praez: ["haus"], stadtteil: "", plan: 0, zechen: 0 }, farbe: null, ansicht: null, ansichtWerte: new Map(), treffer: new Set(), auswahl: null, themaId: "bergbau", _handlerAngehaengt: true,
    setzePlan() {}, setzeZechen() {}, setzeAnsicht() {}, setzeAuswahl() {}, _themaQuelle: () => ({ type: "vector" }) });
  Karte.prototype.ebenenAufsetzen.call(self);
  assert.ok(a.q.has("thema") && a.layer.has("thema-haus"));
});

test("setzeThemaQuelle mit derselben ID baut die Quelle nicht neu auf (Legendenklick soll nicht flackern)", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau"]); let adds = 0; const addSource = a.map.addSource; a.map.addSource = (s, d) => { adds++; addSource(s, d); };
  const self = Object.assign(Object.create(Karte.prototype), { map: a.map, zustand: { ebene: ["I"], praez: ["haus"], stadtteil: "" }, farbe: null, ansicht: null, treffer: new Set(), themaId: null, _handlerAngehaengt: true, _themaQuelle: () => ({ type: "vector" }) });
  Karte.prototype.setzeThemaQuelle.call(self, "bergbau");
  Karte.prototype.setzeThemaQuelle.call(self, "bergbau");
  assert.equal(adds, 1); assert.ok(a.q.has("thema") && a.layer.has("thema-haus"));
  Karte.prototype.setzeThemaQuelle.call(self, "besitz");
  assert.equal(adds, 2);
});

test("Auswahlring liegt auch auf der Themenquelle; setzeAuswahl filtert beide Ringe", () => {
  const e = Karte.prototype._themaEbenen.call(null);
  const ring = e.find((l) => l.id === "thema-auswahl");
  assert.ok(ring && ring.source === "thema" && ring.type === "circle" && ring.paint["circle-radius"] === 14);
  assert.equal(e[e.length - 1].id, "thema-auswahl");                                  // zuoberst der Themenebenen
  const a = kartenAttrappe(["adressen-auswahl", "thema-auswahl"]);
  const self = Object.assign(Object.create(Karte.prototype), { map: a.map });
  Karte.prototype.setzeAuswahl.call(self, "x1");
  assert.deepEqual(a.filter["adressen-auswahl"], ["==", ["get", "id"], "x1"]);
  assert.deepEqual(a.filter["thema-auswahl"], ["==", ["get", "id"], "x1"]);
  const b = kartenAttrappe(["adressen-auswahl"]); const self2 = Object.assign(Object.create(Karte.prototype), { map: b.map });
  Karte.prototype.setzeAuswahl.call(self2, null);                                       // ohne Themenebene kein Fehler
  assert.deepEqual(b.filter["adressen-auswahl"], ["==", ["get", "id"], ""]);
});

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

test("Gruppen überleben das Neuaufsetzen: Stilwechsel (ebenenAufsetzen) und Themenquelle (setzeThemaQuelle) tragen gruppe/mehrfach weiter", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "stadtteile-flaeche"]);
  const self = Object.assign(Object.create(Karte.prototype), { map: a.map, zustand: { ebene: ["II"], praez: ["haus"], stadtteil: "", plan: 0, zechen: 0 }, farbe: null, ansicht: null, ansichtWerte: new Map(), treffer: new Set(), auswahl: null, themaId: null, _handlerAngehaengt: true,
    setzePlan() {}, setzeZechen() {}, setzeAnsicht() {}, setzeAuswahl() {}, _themaQuelle: () => ({ type: "vector" }) });
  const gruppen = [{ name: "K", farbe: "#dc2626", adressIds: ["x"], zaehler: new Map() }, { name: "S", farbe: "#2563eb", adressIds: ["x", "y"], zaehler: new Map() }];
  Karte.prototype.setzeTreffer.call(self, ["x", "y"], gruppen);
  a.state.length = 0;
  Karte.prototype.ebenenAufsetzen.call(self);
  const nachStil = Object.fromEntries(a.state.filter((s) => s[0] === "adressen" && s[1] !== "alle").map((s) => [s[1], s[2]]));
  assert.deepEqual(nachStil.y, { treffer: true, gruppe: 1, mehrfach: false });
  a.state.length = 0;
  self.themaId = null;
  Karte.prototype.setzeThemaQuelle.call(self, "besitz");
  const nachThema = Object.fromEntries(a.state.filter((s) => s[0] === "thema" && s[1] !== "alle").map((s) => [s[1], s[2]]));
  assert.deepEqual(nachThema.x, { treffer: true, gruppe: 0, mehrfach: true });
  assert.deepEqual(nachThema.y, { treffer: true, gruppe: 1, mehrfach: false });
});

const GEO = { type: "FeatureCollection", features: [{ type: "Feature", geometry: { type: "Point", coordinates: [7, 51.4] }, properties: { id: "x", stufe: "haus", stadtteil: "Kray", n: 1, gruppe: 1, mehrfach: false } }] };

test("setzeTreffer mit GeoJSON legt die Trefferquelle und zwei Ebenen an; ohne GeoJSON werden sie entfernt", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "adressen-auswahl"]);
  const self = Object.assign(Object.create(Karte.prototype), { map: a.map, ansicht: null, treffer: new Set(), zustand: { ebene: ["II"], praez: ["haus", "strasse", "stadtplan"], stadtteil: "" }, farbe: null });
  Karte.prototype.setzeTreffer.call(self, ["x"], null, GEO);
  assert.ok(a.q.has("treffer") && a.layer.has("treffer-haus") && a.layer.has("treffer-ungenau"));
  assert.equal(self.trefferGeo, GEO);
  Karte.prototype.setzeTreffer.call(self, null);
  assert.ok(!a.q.has("treffer") && !a.layer.has("treffer-haus"));
});

test("setzeFilter auf der Trefferebene: Präzision und Stadtteil, keine Ebenen-Summe; Farbe nach gruppe-Feld, Ring nach mehrfach-Feld", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "treffer-haus", "treffer-ungenau"]);
  const self = { map: a.map, farbe: null, ansicht: null, treffer: new Set(["x"]), _deckkraftSetzen() {} };
  Karte.prototype.setzeFilter.call(self, { ebene: ["II"], praez: ["haus"], stadtteil: "Kray" });
  const f = JSON.stringify(a.filter["treffer-haus"]);
  assert.ok(f.includes('"Kray"') && f.includes('"praez"') === false && f.includes('["get","stufe"]'));
  assert.ok(!f.includes("n_II"));
  assert.deepEqual(a.paint["treffer-haus.circle-color"], ["match", ["get", "gruppe"], 0, "#dc2626", 1, "#2563eb", 2, "#16a34a", 3, "#7c3aed", 4, "#f59e0b", "#dc2626"]);
  assert.deepEqual(a.paint["treffer-haus.circle-stroke-color"], ["case", ["to-boolean", ["get", "mehrfach"]], "#111827", "#fff"]);
  assert.ok(a.filter["treffer-ungenau"] && a.layout["treffer-ungenau.icon-size"]);
});

test("Trefferquelle überlebt Stilwechsel und Themenwechsel; Themenebenen liegen unter der Trefferebene", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "adressen-auswahl"]);
  const vor = []; const addLayer = a.map.addLayer; a.map.addLayer = (l, b) => { vor.push([l.id, b]); addLayer(l); };
  const self = Object.assign(Object.create(Karte.prototype), { map: a.map, zustand: { ebene: ["II"], praez: ["haus"], stadtteil: "", plan: 0, zechen: 0 }, farbe: null, ansicht: null, ansichtWerte: new Map(), treffer: new Set(), auswahl: null, themaId: null, _handlerAngehaengt: true,
    setzePlan() {}, setzeZechen() {}, setzeAnsicht() {}, setzeAuswahl() {}, _themaQuelle: () => ({ type: "vector" }) });
  Karte.prototype.setzeTreffer.call(self, ["x"], null, GEO);
  a.q.delete("treffer"); a.layer.delete("treffer-haus"); a.layer.delete("treffer-ungenau");   // Stilwechsel wirft alles weg
  Karte.prototype.ebenenAufsetzen.call(self);
  assert.ok(a.q.has("treffer") && a.layer.has("treffer-haus"));
  Karte.prototype.setzeThemaQuelle.call(self, "besitz");
  assert.deepEqual(vor.find(([id]) => id === "thema-haus")[1], "treffer-haus");   // Thema unter den Treffern einfügen
  assert.ok(a.layer.has("treffer-haus"));
});

test("setzeFilter: Präsenzfeld des Themas ersetzt die Ebenen-Summe als Bedingung (Spannen-Häuser mit n_II = 0)", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau", "thema-haus", "thema-ungenau"]);
  const self = { map: a.map, farbe: { ausdruck: "#111", filter: null, praesenz: "n_besitz" }, ansicht: null, treffer: new Set(), _deckkraftSetzen() {} };
  Karte.prototype.setzeFilter.call(self, { ebene: ["II"], praez: ["haus"], stadtteil: "" });
  const erwartet = JSON.stringify(["any", [">", ["+", ["coalesce", ["get", "n_II"], 0]], 0], [">", ["coalesce", ["get", "n_besitz"], 0], 0]]);
  assert.ok(JSON.stringify(a.filter["adressen-haus"]).includes(erwartet));
  assert.ok(JSON.stringify(a.filter["thema-haus"]).includes(erwartet));
  self.farbe = null;
  Karte.prototype.setzeFilter.call(self, { ebene: ["I"], praez: ["haus"], stadtteil: "" });
  assert.ok(!JSON.stringify(a.filter["adressen-haus"]).includes("n_besitz"));
});

test("Pill Eigentümer: Häuser mit belegtem Besitz (n_besitz) erscheinen auch ohne eigene Teil-II-Zeile; ohne Ebene II nicht", () => {
  const a = kartenAttrappe(["adressen-haus", "adressen-ungenau"]);
  const self = { map: a.map, farbe: null, ansicht: null, treffer: new Set(), _deckkraftSetzen() {} };
  Karte.prototype.setzeFilter.call(self, { ebene: ["II"], praez: ["haus"], stadtteil: "" });
  const erwartet = JSON.stringify(["any", [">", ["+", ["coalesce", ["get", "n_II"], 0]], 0], [">", ["coalesce", ["get", "n_besitz"], 0], 0]]);
  assert.ok(JSON.stringify(a.filter["adressen-haus"]).includes(erwartet));
  Karte.prototype.setzeFilter.call(self, { ebene: ["I", "III"], praez: ["haus"], stadtteil: "" });
  assert.ok(!JSON.stringify(a.filter["adressen-haus"]).includes("n_besitz"));
  // Thema mit demselben Präsenzfeld: nur einmal in der Bedingung
  self.farbe = { ausdruck: "#111", filter: null, praesenz: "n_besitz" };
  Karte.prototype.setzeFilter.call(self, { ebene: ["II"], praez: ["haus"], stadtteil: "" });
  assert.equal((JSON.stringify(a.filter["adressen-haus"]).match(/n_besitz/g) || []).length, 1);
});
