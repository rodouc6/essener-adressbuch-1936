import test from "node:test";
import assert from "node:assert/strict";
import { Lader } from "../js/daten.js";
import { vorschlaege, treffer, hinweisHJ } from "../js/suche.js";

const DATEIEN = {
  "daten/suche/namen/se.json": [
    ["sepeur anna", "Sepeur", "Anna", "Bergm.", "Lattenkamp 27, Katernberg", "2", "b2", "I"],
    ["sepeur wilh", "Sepeur", "Wilh.", "Bergm.", "Lattenkamp 25, Katernberg", "1", "a1", "I"],
    ["seppelt karl", "Seppelt", "Karl", "Kfm.", "Viehofer Str. 3", "3", "c3", "I"],
  ],
  "daten/suche/firmen/se.json": [["sepp soehne kohlen", "Sepp & Söhne, Kohlen", "Viehofer Str. 3", "9", "c3"]],
  "daten/suche/strassen.json": [
    { schluessel: "grenzstr", name: "Grenzstr.", art: "1936", ort: "Katernberg", zeilen: 3, adressen_n: 2 },
    { schluessel: "lattenkamp", name: "Lattenkamp", art: "heute", ort: "Katernberg", zeilen: 3, adressen_n: 2 },
  ],
  "daten/suche/strassen/gr.json": { "Grenzstr.|1936|Katernberg": ["a1", "b2"] },
  "daten/suche/strassen/la.json": { "Lattenkamp|heute|Katernberg": ["a1", "b2"] },
  "daten/suche/berufe.json": [["bergm", "Bergm.", 2], ["kfm", "Kfm.", 1]],
  "daten/suche/berufe/be.json": { "Bergm.": [["a1", 1], ["b2", 1]] },
  "daten/suche/eigentuemer.json": [["fried krupp ag", "Fried. Krupp AG", 2, "industrie"], ["stadt essen", "Stadt Essen", 1, "stadt_staat"]],
  "daten/suche/eigentuemer/fr.json": { "Fried. Krupp AG": [["a1", 1], ["b2", 2]] },
  "daten/suche/eigentuemer/st.json": { "Stadt Essen": [["b2", 1], ["c3", 3]] },
  "daten/suche/berufe_norm.json": [["bergmann", "Bergmann", "B 21112-100", 3, 2, "fachlich"]],
  "daten/suche/berufe_norm/be.json": { "B 21112-100": [["a1", 2], ["b2", 1]] },
};
const fetchFake = async (url) => ({
  ok: url in DATEIEN, status: url in DATEIEN ? 200 : 404, json: async () => DATEIEN[url],
});
const lader = () => new Lader("daten/", fetchFake);

test("Lader cached und liefert null bei 404", async () => {
  const l = lader();
  assert.equal(await l.namen("xx"), null);
  const a = await l.namen("se"); const b = await l.namen("se");
  assert.equal(a, b);
});

test("vorschlaege gruppiert und begrenzt", async () => {
  const v = await vorschlaege("Sep", lader());
  assert.deepEqual(v.personen.map((p) => p.text), ["Sepeur, Anna", "Sepeur, Wilh.", "Seppelt, Karl"]);
  assert.equal(v.personen[1].adressId, "a1");
  assert.equal(v.firmen[0].text, "Sepp & Söhne, Kohlen");
  assert.deepEqual(v.strassen, []);
  assert.equal(v.gesamt, 4);
  assert.equal(v.gesamt_personen, 3);
  assert.equal(v.gesamt_firmen, 1);
  assert.equal(v.gesamt_strassen, 0);
  assert.equal(v.gesamt_berufe, 0);
});

test("vorschlaege alle liefert die ungekürzte Gruppe (I6)", async () => {
  const kurz = await vorschlaege("Grenz", lader());
  assert.equal(kurz.strassen.length, kurz.gesamt_strassen);   // hier bereits unter dem Limit
  const voll = await vorschlaege("Grenz", lader(), { strassen: true });
  assert.equal(voll.strassen.length, voll.gesamt_strassen);
  assert.deepEqual(voll.strassen.map((s) => s.text), kurz.strassen.map((s) => s.text));
});

test("vorschlaege Nachname Vorname und Straße 1936", async () => {
  const v = await vorschlaege("sepeur w", lader());
  assert.deepEqual(v.personen.map((p) => p.text), ["Sepeur, Wilh."]);
  const s = await vorschlaege("Grenz", lader());
  assert.equal(s.strassen[0].text, "Grenzstr. (Katernberg)");
  assert.equal(s.strassen[0].untertitel, "Name 1936 · 3 Einträge");
  assert.equal(s.strassen[0].artName, "1936");
  assert.equal(s.strassen[0].ort, "Katernberg");
  const b = await vorschlaege("berg", lader());
  // Normbezeichnungen (Vorschlagsart "ohdab") stehen vor den Rohtexten — Task 11.
  assert.equal(b.berufe[1].text, "Bergm.");
});

test("treffer für Straße, Beruf und Person", async () => {
  const s = await treffer({ art: "strasse", name: "Lattenkamp", artName: "heute", ort: "Katernberg" }, lader());
  assert.deepEqual(s.adressIds, ["a1", "b2"]);
  const b = await treffer({ art: "beruf", beruf: "Bergm." }, lader());
  assert.deepEqual([...b.zaehler.entries()], [["a1", 1], ["b2", 1]]);
  const p = await treffer({ art: "person", q: "Sepeur" }, lader());
  assert.deepEqual(p.adressIds, ["b2", "a1"]);
  assert.equal(p.personen.length, 2);
});

test("Vorschlagsart Eigentümer und Treffermenge", async () => {
  const l = lader();
  const v = await vorschlaege("fried", l);
  assert.deepEqual(v.eigentuemer, [{ art: "eigentuemer", text: "Fried. Krupp AG", untertitel: "2 Häuser · Industrie", name: "Fried. Krupp AG" }]);
  assert.equal(v.gesamt_eigentuemer, 1);
  const t = await treffer({ art: "eigentuemer", name: "Fried. Krupp AG" }, l);
  assert.deepEqual(t.adressIds, ["a1", "b2"]);
  assert.equal(t.zaehler.get("b2"), 2);
});

test("Vorschläge: Normbezeichnung vor Rohtext, Untertitel mit Niveau", async () => {
  const v = await vorschlaege("Berg", lader());
  assert.deepEqual(v.berufe.map((b) => [b.art, b.text]), [["ohdab", "Bergmann"], ["beruf", "Bergm."]]);
  assert.equal(v.berufe[0].untertitel, "3 Einträge · 2 Schreibweisen · Fachliche Tätigkeit");
});

test("Treffer für ohdab über die Normscherbe", async () => {
  const t = await treffer({ art: "ohdab", ohdab: "B 21112-100", name: "Bergmann" }, lader());
  assert.deepEqual(t.adressIds, ["a1", "b2"]); assert.equal(t.zaehler.get("a1"), 2);
});

test("Hinweis auf Lücke H–J", async () => {
  assert.ok(hinweisHJ("Hoffmann"));
  assert.ok(hinweisHJ("jäger"));
  assert.ok(!hinweisHJ("Sepeur"));
  const t = await treffer({ art: "person", q: "Hoffmann" }, lader());
  assert.equal(t.hinweisHJ, true);
  assert.deepEqual(t.adressIds, []);
});

test("treffer mit mehreren Eigentümern: Gruppen in Reihenfolge mit Farbe, Vereinigung der Häuser, summierte Zähler", async () => {
  const geladen = []; const l = new Lader("daten/", async (u) => { geladen.push(u); return fetchFake(u); });
  const t = await treffer({ art: "eigentuemer", namen: ["Fried. Krupp AG", "Stadt Essen", "Gibtsnicht GmbH"] }, l);
  assert.deepEqual(t.gruppen.map((g) => [g.name, g.farbe, g.adressIds]), [
    ["Fried. Krupp AG", "#dc2626", ["a1", "b2"]], ["Stadt Essen", "#2563eb", ["b2", "c3"]], ["Gibtsnicht GmbH", "#16a34a", []]]);
  assert.deepEqual(t.adressIds, ["a1", "b2", "c3"]);
  assert.equal(t.zaehler.get("b2"), 3);                   // 2 (Krupp) + 1 (Stadt)
  assert.equal(t.gruppen[1].zaehler.get("c3"), 3);
  assert.equal(geladen.filter((u) => u.includes("eigentuemer/")).length, 3);   // fr, st, gi — je Präfix einmal
});

test("treffer: alte Auswahlform {name} und andere Arten liefern gruppen null bzw. eine Gruppe", async () => {
  const alt = await treffer({ art: "eigentuemer", name: "Fried. Krupp AG" }, lader());
  assert.deepEqual(alt.gruppen.map((g) => g.name), ["Fried. Krupp AG"]);
  assert.deepEqual(alt.adressIds, ["a1", "b2"]);
  assert.equal((await treffer({ art: "beruf", beruf: "Bergm." }, lader())).gruppen, null);
});
