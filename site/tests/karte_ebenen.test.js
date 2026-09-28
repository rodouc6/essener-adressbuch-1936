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
