import test from "node:test";
import assert from "node:assert/strict";
import { popupHtml, popupZeile, hausHtml, faksimileUrl, praezisionText, esc, trefferzeileHtml } from "../js/popup.js";

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

test("hausHtml nennt die Herkunft einer Besitzklasse aus einer Hausnummernspanne", () => {
  const h = hausHtml({ ...EIG, besitz: "kirche_stiftung", besitz_quelle: "spanne", besitz_spanne: "Sommerburgstr. 2–84 · Frau-Margarete-Krupp-Stiftung" }, E);
  assert.match(h, /Hausnummernspanne\): Sommerburgstr\. 2–84 · Frau-Margarete-Krupp-Stiftung · /);
  assert.match(hausHtml({ ...EIG, besitz: "industrie", besitz_quelle: "nummer", besitz_spanne: "Grenzstraße 20 · Fried. Krupp A.G." }, E), /gleiche Hausnummer, andere Schreibung\): Grenzstraße 20 · Fried\. Krupp A\.G\. · /);
  assert.doesNotMatch(hausHtml({ ...EIG, besitz: "industrie", besitz_quelle: "eintrag", besitz_spanne: "" }, E), /laut Häuserbuch/);
});

test("hausHtml nennt bei Regel-Klassifikation die Regel statt eines Namens", () => {
  const e = [{ id: "9", teil: "II", seite: "II-1", name: "Schmidt", vorname: "W.", firma: "", eigentuemer: "Eigentümer", eigentuemer_kanon: "", kategorie: "privatperson", pruefung: "regel", flags: [], merkmale: [] }];
  const h = hausHtml(EIG, e);
  assert.match(h, /Zugeordnet<\/span> Privatperson.* \(Regel: Person ohne Firmenname → Privatperson, keine Handprüfung\)/);
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

test("popupHtml zeigt bei geprüfter Zuordnung nur die Norm, ohne Rohtext, Niveau und Status", () => {
  const eintraege = [{ id: "9", teil: "I", seite: "I-1", name: "Sepeur", vorname: "Wilh.", beruf: "Bergm.",
    beruf_norm: "Bergmann", ohdab: "B 21112-100", niveau: "fachlich", status: "ruhestand", etage: "", stand: "", flags: [], merkmale: [] }];
  const h = popupHtml(EIG, eintraege, true);
  assert.match(h, /· Bergmann</);
  assert.doesNotMatch(h, /Bergm\.|→|Fachliche Tätigkeit|Ruhestand/);
});

const VIELE = [
  ...[1, 2, 3, 4, 5].map((i) => ({ id: `i${i}`, teil: "I", seite: "I-1", name: `Person${i}`, vorname: "A.", beruf: "Bergm.", beruf_norm: "Bergmann", etage: "", stand: "", flags: [], merkmale: [] })),
  { id: "e1", teil: "II", seite: "II-1", name: "", vorname: "", firma: "Fried. Krupp A.-G.", eigentuemer: "Eigentümer", eigentuemer_kanon: "Fried. Krupp AG", kategorie: "industrie", pruefung: "hand", flags: [], merkmale: [] },
  ...[1, 2, 3, 4, 5].map((i) => ({ id: `g${i}`, teil: "III", seite: "III-1", name: "Vößing", vorname: "W.", firma: `Firma ${i}`, rubrik: "Schneiderin", flags: [], merkmale: [] })),
];

test("popupHtml: Kopf mit Adresse, Buchadresse, Kennzeile; Teile in fester Reihenfolge", () => {
  const h = popupHtml({ ...EIG, stufe: "haus" }, VIELE, false);
  assert.match(h, /<div class="popup-kopf"><b>Lattenkamp 25, Katernberg<\/b><div class="hist">Grenzstr\. 25, Katernberg im Buch<\/div>/);
  assert.match(h, /<div class="kennzeile">2 Einwohner · 1 Eigentümer<\/div>/);   // hausgenau: kein Präzisionstext
  assert.doesNotMatch(h, /hausgenau verortet/);
  const iE = h.indexOf("<h4>Einwohner · 5</h4>"), iG = h.indexOf("<h4>Eigentümer</h4>"), iW = h.indexOf("<h4>Gewerbe · 5</h4>");
  assert.ok(iE > 0 && iG > iE && iW > iG, "Reihenfolge I, II, III; Zahl nur bei > 1");
  assert.match(h, /<div class="pmehr" data-mehr="1">Haus im Detail ›<\/div>$/);
});

test("popupHtml: Kennzeile nennt die Präzision, wenn nicht hausgenau", () => {
  assert.match(popupHtml(EIG, E, false), /<div class="kennzeile"><span class="praez-strasse">nur straßengenau<\/span> · 2 Einwohner · 1 Eigentümer<\/div>/);
  assert.match(popupHtml({ ...EIG, stufe: "stadtplan" }, E, false), /praez-stadtplan">Punkt vom Stadtplan 1935</);
});

test("popupHtml: Kennzeile bei unbekannter Präzision", () => {
  assert.match(popupHtml({ ...EIG, stufe: "unbekannt" }, E, false), /praez-unbekannt">Präzision unbekannt</);
});

test("popupHtml: Kappung je Teil, Laptop 4 und Handy 2", () => {
  const h = popupHtml(EIG, VIELE, false);
  assert.equal((h.match(/data-eintrag="i/g) || []).length, 4);
  assert.equal((h.match(/data-eintrag="g/g) || []).length, 4);
  assert.equal((h.match(/und 1 weitere Zeile</g) || []).length, 2);
  const k = popupHtml(EIG, VIELE, true);
  assert.equal((k.match(/data-eintrag="i/g) || []).length, 2);
  assert.match(k, /und 3 weitere Zeilen</);
  assert.doesNotMatch(popupHtml(EIG, E, false), /weitere/);   // nichts gekappt
});

test("popupZeile: Einwohner nur mit Norm, sonst Buchschreibung kursiv mit Tooltip; Stand bleibt", () => {
  assert.equal(popupZeile(VIELE[0]), `<div class="z" data-eintrag="i1"><b>Person1, A.</b> <span class="n">· Bergmann</span></div>`);
  assert.match(popupZeile(E[0]), /<b>Sepeur, Wilh\.<\/b> <span class="n">· <i title="Schreibung im Buch, Beruf noch nicht zugeordnet">Bergm\.<\/i><\/span>/);
  assert.match(popupZeile(E[1]), /<i title="[^"]+">Hauer<\/i>, Wwe\.<\/span>/);
  assert.doesNotMatch(popupZeile(VIELE[0]), /→|Erdg\./);
});

test("popupZeile: Eigentümer mit Kanon und Klasse, per Regel mit Vermerk; Gewerbe mit Firma und Rubrik", () => {
  assert.equal(popupZeile(VIELE[5]), `<div class="z" data-eintrag="e1"><b>Fried. Krupp AG</b> <span class="n">· Industrie</span></div>`);
  const regel = { id: "r", teil: "II", name: "Schmidt", vorname: "W.", firma: "", eigentuemer_kanon: "", kategorie: "privatperson", pruefung: "regel" };
  assert.match(popupZeile(regel), /<b>Schmidt, W\.<\/b> <span class="n">· Privatperson \(Regel\)<\/span>/);
  assert.equal(popupZeile(VIELE[6]), `<div class="z" data-eintrag="g1"><b>Firma 1</b> <span class="n">· Schneiderin</span></div>`);
  assert.equal(popupZeile({ id: "g0", teil: "III", name: "Meier", vorname: "K.", firma: "", rubrik: "" }), `<div class="z" data-eintrag="g0"><b>Meier, K.</b></div>`);
  // Das Firmenfeld in Teil III endet im Datenpaket auf „, Rubrik“ — der Zusatz darf sie nicht doppeln.
  assert.equal(popupZeile({ id: "g9", teil: "III", name: "", vorname: "", firma: "Karl Autenrieth, Kunstgewerbe", rubrik: "Kunstgewerbe" }), `<div class="z" data-eintrag="g9"><b>Karl Autenrieth</b> <span class="n">· Kunstgewerbe</span></div>`);
});

test("popupZeile: Teil-I-Eintrag ohne Namen nimmt die Firma", () => {
  assert.match(popupZeile({ id: "v", teil: "I", name: "", vorname: "", firma: "Turnverein 1877", beruf: "", beruf_norm: "" }), /<b>Turnverein 1877<\/b><\/div>/);
});

test("popupHtml: eine oder zwei Ebenen heben ihre Teile hervor, drei nicht", () => {
  const eine = popupHtml(EIG, VIELE, false, ["III"]);
  assert.match(eine, /<div class="teil hervor" style="--f:#c2410c"><h4>Gewerbe · 5<\/h4>/);
  assert.match(eine, /<div class="teil"><h4>Einwohner · 5<\/h4>/);
  assert.equal((eine.match(/class="teil hervor"/g) || []).length, 1);
  const zwei = popupHtml(EIG, VIELE, false, ["I", "II"]);
  assert.equal((zwei.match(/class="teil hervor"/g) || []).length, 2);
  assert.match(zwei, /--f:#1d4ed8"><h4>Einwohner/); assert.match(zwei, /--f:#ca8a04"><h4>Eigentümer/);
  assert.doesNotMatch(popupHtml(EIG, VIELE, false, ["I", "II", "III"]), /hervor/);
  assert.doesNotMatch(popupHtml(EIG, VIELE, false), /hervor/);
});

test("popupHtml: leere Ebenenliste hebt nichts hervor", () => {
  assert.doesNotMatch(popupHtml(EIG, VIELE, false, []), /hervor/);
});
