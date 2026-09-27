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
