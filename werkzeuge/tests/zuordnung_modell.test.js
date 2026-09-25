import test from "node:test";
import assert from "node:assert/strict";
import { KONFIG, baueModell, fortschritt, liste, rueckgaengig, setzeFeld, setzeGeprueft, zumSpeichern } from "../js/zuordnung_modell.js";

const Z = [
  { rubrik: "Bäcker", betriebe: "536", gruppe: "lebensmittel", art: "handwerk", geprueft: "", bearbeiter: "gewerbe_vorschlag", datum: "", hinweis: "" },
  { rubrik: "Schankwirt", betriebe: "904", gruppe: "gastgewerbe", art: "gastgewerbe", geprueft: "ja", bearbeiter: "christos", datum: "", hinweis: "" },
];

test("Konfiguration, Liste nach Menge, Felder mit Vokabular", () => {
  const m = baueModell(Z, KONFIG.gewerbe);
  assert.deepEqual(liste(m).map((z) => z.schluessel), ["Schankwirt", "Bäcker"]);
  assert.deepEqual(KONFIG.gewerbe.felder.map((f) => f.name), ["gruppe", "art"]);
  assert.equal(KONFIG.gruppen, undefined);                                   // Berufsgruppen sind seit 2026-09-25 OhdAB-Hauptgruppen
  assert.deepEqual(setzeFeld(m, "Bäcker", "art", "adel"), []);              // unbekanntes Vokabular
  assert.deepEqual(setzeFeld(m, "Bäcker", "art", "handel").map((z) => z.art), ["handel"]);
  assert.deepEqual(fortschritt(m), { geprueft: 1, gesamt: 2, mengeGeprueft: 904, mengeGesamt: 1440 });
});

test("geprüft nur mit gefüllten Feldern; Rückgängig; Speichern nur CSV-Felder", () => {
  const m = baueModell([{ ...Z[0], gruppe: "" }], KONFIG.gewerbe);
  assert.deepEqual(setzeGeprueft(m, "Bäcker", true), []);
  setzeFeld(m, "Bäcker", "gruppe", "lebensmittel");
  assert.deepEqual(setzeGeprueft(m, "Bäcker", true).map((z) => z.geprueft), ["ja"]);
  assert.deepEqual(rueckgaengig(m).map((z) => z.geprueft), [""]);
  const s = zumSpeichern(m.zeilen.get("Bäcker"), KONFIG.gewerbe);
  assert.deepEqual(Object.keys(s), ["rubrik", "gruppe", "art", "geprueft", "hinweis"]);
});
