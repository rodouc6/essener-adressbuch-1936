import test from "node:test";
import assert from "node:assert/strict";
import { STANDARD, liesZustand, schreibeZustand, zustandGleich } from "../js/zustand.js";

test("leerer Query ergibt Standard", () => {
  assert.deepEqual(liesZustand(""), STANDARD);
  assert.deepEqual(liesZustand("?"), STANDARD);
});

test("Parameter werden gelesen und getippt", () => {
  const z = liesZustand("?q=Sepeur&ebene=I,II&praez=haus&plan=0.5&zechen=1&z=15.2&c=7.06,51.49&id=abc&karte=liberty");
  assert.equal(z.q, "Sepeur");
  assert.deepEqual(z.ebene, ["I", "II"]);
  assert.deepEqual(z.praez, ["haus"]);
  assert.equal(z.plan, 0.5);
  assert.equal(z.zechen, 1);
  assert.equal(z.z, 15.2);
  assert.deepEqual(z.c, [7.06, 51.49]);
  assert.equal(z.id, "abc");
  assert.equal(z.karte, "liberty");
});

test("ungültige Werte fallen auf Standard zurück", () => {
  const z = liesZustand("?ebene=X,I&karte=bunt&plan=7&c=a,b&z=abc");
  assert.deepEqual(z.ebene, ["I"]);
  assert.equal(z.karte, "positron");
  assert.equal(z.plan, 1);
  assert.equal(z.c, null);
  assert.equal(z.z, null);
});

test("leeres z ergibt null statt 0", () => {
  assert.equal(liesZustand("?z=").z, null);
});

test("schreibeZustand lässt Standardwerte weg und sortiert", () => {
  assert.equal(schreibeZustand(STANDARD), "");
  const s = schreibeZustand({ ...STANDARD, q: "Grenzstr. Katernberg", ebene: ["I"], c: [7.06, 51.49], z: 15 });
  assert.equal(s, "c=7.06,51.49&ebene=I&q=Grenzstr.+Katernberg&z=15");
  assert.deepEqual(liesZustand("?" + s), { ...STANDARD, q: "Grenzstr. Katernberg", ebene: ["I"], c: [7.06, 51.49], z: 15 });
});

test("zustandGleich vergleicht tief", () => {
  assert.ok(zustandGleich(liesZustand("?ebene=I,II"), { ...STANDARD, ebene: ["I", "II"] }));
  assert.ok(!zustandGleich(STANDARD, { ...STANDARD, q: "x" }));
});

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

test("ansicht wird roh durchgereicht", () => {
  const z = liesZustand("?ansicht=eyJkYXRlbiI6ImJlc2l0eiJ9");
  assert.equal(z.ansicht, "eyJkYXRlbiI6ImJlc2l0eiJ9");
  assert.equal(schreibeZustand(z), "ansicht=eyJkYXRlbiI6ImJlc2l0eiJ9");
  assert.equal(liesZustand("").ansicht, "");
});

test("ohdab im Zustand", () => {
  assert.equal(liesZustand("?ohdab=B+21112-100").ohdab, "B 21112-100");
  assert.equal(schreibeZustand({ ...STANDARD, ohdab: "B 21112-100" }), "ohdab=B+21112-100");
});

test("plan mit zwei Nachkommastellen wird gelesen und unverändert geschrieben", () => {
  const z = liesZustand("?plan=0.35");
  assert.equal(z.plan, 0.35);
  assert.equal(schreibeZustand(z), "plan=0.35");
});

test("klassen: Komma-Liste oder 'keine', Standard leer, Rundreise", () => {
  assert.equal(STANDARD.klassen, "");
  assert.equal(liesZustand("?thema=bergbau&klassen=leitung,aufsicht").klassen, "leitung,aufsicht");
  assert.equal(liesZustand("?klassen=keine").klassen, "keine");
  assert.equal(liesZustand("").klassen, "");
  assert.equal(schreibeZustand({ ...STANDARD, thema: "bergbau", klassen: "leitung" }), "klassen=leitung&thema=bergbau");
});
