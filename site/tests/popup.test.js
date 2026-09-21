import test from "node:test";
import assert from "node:assert/strict";
import { popupHtml, hausHtml, faksimileUrl, praezisionText, esc } from "../js/popup.js";

const EIG = { id: "a1", stufe: "strasse", strasse_heute: "Lattenkamp", hausnr: "25", stadtteil: "Katernberg",
              historisch: "Grenzstr. 25, Katernberg", n_I: 2, n_II: 1, n_III: 0, nummer_unsicher: "nein" };
const E = [
  { id: "1", teil: "I", seite: "I-551", name: "Sepeur", vorname: "Wilh.", beruf: "Bergm.", etage: "Erdg.", stand: "", flags: [], merkmale: [] },
  { id: "2", teil: "I", seite: "I-402", name: "Kowalski", vorname: "Jos.", beruf: "Hauer", etage: "", stand: "Wwe.", flags: ["nummer_unsicher"], merkmale: [] },
  { id: "3", teil: "II", seite: "II-088", name: "Zeche Zollverein", vorname: "", beruf: "", etage: "", stand: "", eigentuemer: "Eigentümer", flags: [], merkmale: [] },
];

test("esc entschärft HTML", () => {
  assert.equal(esc("<b>&\"'"), "&lt;b&gt;&amp;&quot;&#39;");
});

test("popupHtml: heutige und historische Adresse, Präzision, Namen ohne Seiten", () => {
  const h = popupHtml(EIG, E, false);
  assert.match(h, /Lattenkamp 25, Katernberg/);
  assert.match(h, /historische Adresse: Grenzstr\. 25, Katernberg/);
  assert.match(h, /Straße bekannt, Hausnummer nicht verortbar/);
  assert.match(h, /2 Einwohner · 1 Eigentümer/);
  assert.ok(h.indexOf("Sepeur") < h.indexOf("Kowalski"), "Etage Erdg. vor ohne Etage");
  assert.match(h, /data-eintrag="2"/);
  assert.doesNotMatch(h, /I-551/);
});

test("popupHtml kompakt zeigt höchstens drei Namen", () => {
  const h = popupHtml(EIG, E, true);
  assert.match(h, /alle 3 im Detail/);
  assert.equal((h.match(/data-eintrag=/g) || []).length, 3);
});

test("hausHtml gruppiert nach Teil und verlinkt das Faksimile", () => {
  const h = hausHtml(EIG, E);
  assert.match(h, /Einwohner \(2\)/);
  assert.match(h, /Eigentümer \(1\)/);
  assert.match(h, /id="e-1"/);
  assert.match(h, /Seite I-551/);
  assert.match(h, new RegExp(faksimileUrl("I-551").replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  assert.match(h, /Hausnummer unsicher/);
});

test("praezisionText und faksimileUrl", () => {
  assert.equal(praezisionText("haus"), "hausgenau verortet");
  assert.match(faksimileUrl("I-551"), /^https:\/\//);
});
