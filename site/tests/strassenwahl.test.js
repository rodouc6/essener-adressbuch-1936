import test from "node:test";
import assert from "node:assert/strict";
import { strasseAusText } from "../js/strassenwahl.js";

const STRASSEN = [
  { schluessel: "aachener strasse", name: "Aachener Straße", art: "1936", ort: "Frohnhausen", zeilen: 40, adressen_n: 26 },
  { schluessel: "aachener strasse", name: "Aachener Straße", art: "heute", ort: "Frohnhausen", zeilen: 225, adressen_n: 55 },
  { schluessel: "muehlenstr", name: "Mühlenstr.", art: "1936", ort: "Werden", zeilen: 10, adressen_n: 6 },
  { schluessel: "muehlenstr", name: "Mühlenstr.", art: "1936", ort: "Steele", zeilen: 50, adressen_n: 22 },
  { schluessel: "grenzstrasse", name: "Grenzstraße", art: "1936", ort: "Katernberg", zeilen: 5, adressen_n: 3 },
  { schluessel: "grenzstrasse", name: "Grenzstraße", art: "1936", ort: "Stoppenberg", zeilen: 9, adressen_n: 4 },
];

test("exakter Treffer bevorzugt den heutigen Namen", () => {
  const s = strasseAusText("Aachener Straße", STRASSEN);
  assert.deepEqual(s, { art: "strasse", name: "Aachener Straße", artName: "heute", ort: "Frohnhausen" });
});

test("nur 1936er Zeilen: die mit den meisten Einträgen gewinnt", () => {
  const s = strasseAusText("Mühlenstr.", STRASSEN);
  assert.deepEqual(s, { art: "strasse", name: "Mühlenstr.", artName: "1936", ort: "Steele" });
});

test("'Name (Ort)' mit bekanntem Ort wählt genau diesen Ort", () => {
  const s = strasseAusText("Grenzstraße (Katernberg)", STRASSEN);
  assert.deepEqual(s, { art: "strasse", name: "Grenzstraße", artName: "1936", ort: "Katernberg" });
});

test("unbekannter Name ergibt null", () => {
  assert.equal(strasseAusText("Nichtvorhandenweg", STRASSEN), null);
  assert.equal(strasseAusText("", STRASSEN), null);
});

test("gefalteter Umlaut-Treffer ohne Klammerzusatz", () => {
  const s = strasseAusText("Grenzstrasse", STRASSEN);
  assert.equal(s.name, "Grenzstraße");
  assert.equal(s.ort, "Stoppenberg");   // ohne Ort-Hinweis gewinnt die Zeile mit mehr Einträgen
});
