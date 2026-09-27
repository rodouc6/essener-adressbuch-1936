import test from "node:test";
import assert from "node:assert/strict";
import { steuerungHtml, abweichend } from "../js/steuerung.js";

const STANDARD = { karte: "positron", zechen: 0, plan: 0 };

test("abweichend: nur bei Liberty, Zechen oder sichtbarem Plan", () => {
  assert.equal(abweichend(STANDARD), false);
  assert.equal(abweichend({ ...STANDARD, karte: "liberty" }), true);
  assert.equal(abweichend({ ...STANDARD, zechen: 1 }), true);
  assert.equal(abweichend({ ...STANDARD, plan: 0.3 }), true);
});

test("steuerungHtml: Knopf, Feld verborgen, Umschalter und Schalter mit Zustand, ohne Planregler", () => {
  const h = steuerungHtml({ ...STANDARD, zechen: 1 }, { offen: false, mobil: false, plan: false });
  assert.match(h, /<button class="ebenenknopf aktiv" data-feld="1" aria-expanded="false" aria-label="Kartenebenen"/);
  assert.match(h, /<div class="ebenenfeld" hidden>/);
  assert.match(h, /data-karte="positron" aria-pressed="true"/); assert.match(h, /data-karte="liberty" aria-pressed="false"/);
  assert.match(h, /data-zechen="1" aria-pressed="true"[^>]*><svg/);
  assert.doesNotMatch(h, /data-plan|data-legende/);
});

test("steuerungHtml: offen, Handy mit Legendenknopf, Planregler stufenlos mit Prozent", () => {
  const h = steuerungHtml({ ...STANDARD, plan: 0.35 }, { offen: true, mobil: true, plan: true });
  assert.match(h, /aria-expanded="true"/);
  assert.match(h, /<div class="ebenenfeld">/);
  assert.match(h, /data-legende="1"/);
  assert.match(h, /<input type="range" min="0" max="1" step="0.01" value="0.35" data-plan="1"/);
  assert.match(h, /<span class="prozent">35 %<\/span>/);
});
