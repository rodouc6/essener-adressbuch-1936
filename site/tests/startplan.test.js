import test from "node:test";
import assert from "node:assert/strict";
import { nach3857, punktLage } from "../js/startplan.js";

const PLAN = { bbox3857: [778322.27, 6701033.35, 782822.27, 6704033.35], seitenverhaeltnis: 3 / 2, ankerX: 0.3 };

test("nach3857 entspricht Web-Mercator", () => {
  const [x, y] = nach3857(7.012, 51.457);
  assert.ok(Math.abs(x - 780572.27) < 1 && Math.abs(y - 6702533.35) < 1);
});

test("punktLage: Bildmitte liegt bei quadratischem Behälter mittig-versetzt nach ankerX", () => {
  // Behälter 600×600, Bild 3:2 → skaliert 900×600, Überstand 300 px, Anker 0,3 → Bild beginnt bei -90 px
  const p = punktLage(7.012, 51.457, PLAN, 600, 600);
  // Bildmitte (u = 0,5) → -90 + 450 = 360 px → 60 %
  assert.ok(Math.abs(p.x - 60) < 0.5 && Math.abs(p.y - 50) < 0.5);
});

test("punktLage: außerhalb der Box oder im abgeschnittenen Rand → null", () => {
  assert.equal(punktLage(7.2, 51.457, PLAN, 600, 600), null);
  // linker Bildrand (u = 0) liegt bei -90 px → abgeschnitten
  assert.equal(punktLage(6.9917, 51.457, PLAN, 600, 600), null);
});

test("punktLage: breiter Behälter zeigt das ganze Bild ohne Versatz in x", () => {
  const p = punktLage(7.012, 51.457, PLAN, 900, 600);
  assert.ok(Math.abs(p.x - 50) < 0.5 && Math.abs(p.y - 50) < 0.5);
});
