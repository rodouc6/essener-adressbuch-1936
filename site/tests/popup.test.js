import test from "node:test";
import assert from "node:assert/strict";
import { popupHtml, hausHtml, faksimileUrl, praezisionText, esc, trefferzeileHtml } from "../js/popup.js";

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

test("hausHtml nennt die Herkunft einer Besitzklasse aus einer Hausnummernspanne", () => {
  const h = hausHtml({ ...EIG, besitz: "kirche_stiftung", besitz_quelle: "spanne", besitz_spanne: "Sommerburgstr. 2–84 · Frau-Margarete-Krupp-Stiftung" }, E);
  assert.match(h, /Hausnummernspanne\): Sommerburgstr\. 2–84 · Frau-Margarete-Krupp-Stiftung · /);
  assert.match(hausHtml({ ...EIG, besitz: "industrie", besitz_quelle: "nummer", besitz_spanne: "Grenzstraße 20 · Fried. Krupp A.G." }, E), /gleiche Hausnummer, andere Schreibung\): Grenzstraße 20 · Fried\. Krupp A\.G\. · /);
  assert.doesNotMatch(hausHtml({ ...EIG, besitz: "industrie", besitz_quelle: "eintrag", besitz_spanne: "" }, E), /laut Häuserbuch/);
});

test("popupHtml kompakt zeigt höchstens drei Namen", () => {
  const h = popupHtml(EIG, E, true);
  assert.match(h, /alle 3 im Detail/);
  assert.equal((h.match(/data-eintrag=/g) || []).length, 3);
});

test("hausHtml gruppiert nach Teil und verlinkt das Faksimile über die Bildnummer", () => {
  const h = hausHtml(EIG, E, { "I-551": 573 });
  assert.match(h, /Einwohner \(2\)/);
  assert.match(h, /Eigentümer \(1\)/);
  assert.match(h, /id="e-1"/);
  assert.match(h, /Seite I-551/);
  assert.match(h, /digibib\.genealogy\.net\/viewer\/image\/857439804_1936\/573\//);
  assert.match(h, /Seite I-402 · <span class="kein-bild">im Digitalisat nicht vorhanden/);
  assert.match(h, /Hausnummer unsicher/);
  // Namenszeile der Hausansicht ohne Beruf/Stand (stehen als Felder darunter)
  assert.match(h, /<div class="ename"><b>Kowalski, Jos\.<\/b><\/div>/);
  assert.match(h, /<span class="k">Stand<\/span> Wwe\./);
});

test("praezisionText und faksimileUrl", () => {
  assert.equal(praezisionText("haus"), "hausgenau verortet");
  assert.equal(faksimileUrl(355), "https://www.digibib.genealogy.net/viewer/image/857439804_1936/355/");
  assert.equal(faksimileUrl(undefined), null);
});

test("praezisionText unbekannt", () => {
  assert.equal(praezisionText("unbekannt"), "Präzision unbekannt (Daten nicht geladen)");
});

test("trefferzeileHtml zeigt Kennzeichnung für unbekannte Präzision", () => {
  const h = trefferzeileHtml({ adressId: "a1", titel: "x", untertitel: "y", stufe: "unbekannt" });
  assert.match(h, /Präzision unbekannt/);
});

test("Hausansicht zeigt geprüften Eigentümer mit Kategorie, sonst nur Buchschreibung", () => {
  const eig = { id: "a1", stufe: "haus", strasse_heute: "Lattenkamp", hausnr: "25", stadtteil: "Katernberg", historisch: "Grenzstr. 25", n_I: 0, n_II: 2, n_III: 0 };
  const e = [{ id: "1", teil: "II", seite: "II-1", name: "", vorname: "", firma: "Fried. Krupp A.G.", eigentuemer: "Eigentümer", eigentuemer_kanon: "Fried. Krupp AG", kategorie: "industrie", flags: [], merkmale: [] },
             { id: "2", teil: "II", seite: "II-1", name: "", vorname: "", firma: "Bauverein GmbH", eigentuemer: "Eigentümer", eigentuemer_kanon: "", kategorie: "", flags: [], merkmale: [] }];
  const h = hausHtml(eig, e);
  assert.match(h, /Zugeordnet<\/span> Fried\. Krupp AG · Industrie/);
  assert.match(h, /Firma<\/span> Fried\. Krupp A\.G\./);
  assert.equal((h.match(/Zugeordnet/g) || []).length, 1);
});

test("Hausansicht zeigt die Berufszuordnung mit Niveau und Status", () => {
  const h = hausHtml(EIG, [{ id: "9", teil: "I", seite: "I-1", name: "A", vorname: "", beruf: "Bergm. i. R.", beruf_norm: "Bergmann", ohdab: "B 21112-100", niveau: "fachlich", status: "ruhestand", etage: "", stand: "", flags: [], merkmale: [] }]);
  assert.match(h, /Bergm\. i\. R\. → Bergmann · Fachliche Tätigkeit · Ruhestand/);
  const u = hausHtml(EIG, [{ id: "9", teil: "I", seite: "I-1", name: "A", vorname: "", beruf: "Kfm.", etage: "", stand: "", flags: [], merkmale: [] }]);
  assert.match(u, /<span class="k">Beruf<\/span> Kfm\.<\/div>/);
});

test("popupHtml (kompakt) zeigt bei geprüfter Zuordnung nur Rohtext → Norm, ohne Niveau/Status", () => {
  const eintraege = [{ id: "9", teil: "I", seite: "I-1", name: "Sepeur", vorname: "Wilh.", beruf: "Bergm.",
    beruf_norm: "Bergmann", ohdab: "B 21112-100", niveau: "fachlich", status: "ruhestand", etage: "", stand: "", flags: [], merkmale: [] }];
  const h = popupHtml(EIG, eintraege, true);
  assert.match(h, /Bergm\. → Bergmann/);
  assert.doesNotMatch(h, /Fachliche Tätigkeit/);
  assert.doesNotMatch(h, /Ruhestand/);
  // ungeprüfter Beruf (kein beruf_norm) bleibt wie bisher der rohe Text
  const roh = popupHtml(EIG, [{ id: "8", teil: "I", seite: "I-1", name: "B", vorname: "", beruf: "Kfm.", etage: "", stand: "", flags: [], merkmale: [] }], true);
  assert.match(roh, /Kfm\./);
  assert.doesNotMatch(roh, /→/);
});
