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
