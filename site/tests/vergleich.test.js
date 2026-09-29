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

import { trefferGeoJson } from "../js/vergleich.js";

test("trefferGeoJson: ein Punkt je Treffer mit Koordinaten aus dem Kurzindex, Gruppe/mehrfach/n; ohne Gruppen gruppe -1; fehlende Koordinaten fallen weg", () => {
  const punkte = new Map([["a", { id: "a", lon: 7.0, lat: 51.4, stufe: "haus", stadtteil: "Kray" }], ["b", { id: "b", lon: 7.1, lat: 51.5, stufe: "strasse", stadtteil: "Bochold" }]]);
  const geo = trefferGeoJson(["a", "b", "c"], new Map([["a", 2], ["b", 1], ["c", 1]]), G, punkte);
  assert.equal(geo.type, "FeatureCollection");
  assert.deepEqual(geo.features.map((f) => f.properties), [
    { id: "a", stufe: "haus", stadtteil: "Kray", n: 2, gruppe: 0, mehrfach: false },
    { id: "b", stufe: "strasse", stadtteil: "Bochold", n: 1, gruppe: 0, mehrfach: true }]);
  assert.deepEqual(geo.features[0].geometry, { type: "Point", coordinates: [7.0, 51.4] });
  const ohne = trefferGeoJson(["a"], new Map([["a", 3]]), null, punkte);
  assert.deepEqual(ohne.features[0].properties, { id: "a", stufe: "haus", stadtteil: "Kray", n: 3, gruppe: -1, mehrfach: false });
});
