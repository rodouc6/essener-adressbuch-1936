import test from "node:test";
import assert from "node:assert/strict";
import { csvZeile, csvAusTreffern } from "../js/exportcsv.js";
import { Lader } from "../js/daten.js";

const DATEIEN = { "daten/haus/a1.json": { a1: [
  { id: "1", teil: "I", seite: "I-551", name: "Sepeur", vorname: "Wilh.", beruf: "Bergm.", etage: "", stand: "", flags: [], merkmale: [] },
  { id: "2", teil: "II", seite: "II-1", name: "Zeche \"Z\"", vorname: "", beruf: "", etage: "", stand: "", flags: ["nummer_unsicher"], merkmale: [] } ] } };
const l = new Lader("daten/", async (u) => ({ ok: u in DATEIEN, status: u in DATEIEN ? 200 : 404, json: async () => DATEIEN[u] }));
const EIG = new Map([["a1", { id: "a1", stufe: "haus", strasse_heute: "Lattenkamp", hausnr: "25", stadtteil: "Katernberg", historisch: "Grenzstr. 25, Katernberg" }]]);

test("csvZeile quotet Komma, Anführungszeichen und Zeilenumbruch", () => {
  assert.equal(csvZeile(["a", "b,c", 'd"e', "f\ng"]), 'a,"b,c","d""e","f\ng"');
});

test("csvZeile entschärft Formelinjektion (=, +, -, @)", () => {
  assert.equal(csvZeile(["=SUMME(A1)", "+1", "-1", "@HYPERLINK", "normal"]),
    "'=SUMME(A1),'+1,'-1,'@HYPERLINK,normal");
});

test("vollständiger Export bis zur Grenze", async () => {
  const csv = await csvAusTreffern({ adressIds: ["a1"], zaehler: new Map([["a1", 2]]), personen: null }, l, EIG);
  const zeilen = csv.split("\r\n");
  assert.ok(zeilen[0].startsWith("﻿"));
  assert.equal(zeilen[0].replace("﻿", ""), "eintrag_id,teil,seite,name,vorname,beruf,etage,stand,adresse_heute,adresse_1936,stadtteil,praezision,flags,adress_id");
  assert.equal(zeilen[1], "1,I,I-551,Sepeur,Wilh.,Bergm.,,,\"Lattenkamp 25, Katernberg\",\"Grenzstr. 25, Katernberg\",Katernberg,haus,,a1");
  assert.match(zeilen[2], /"Zeche ""Z"""/);
});

test("über der Grenze nur Adressebene", async () => {
  const csv = await csvAusTreffern({ adressIds: ["a1"], zaehler: new Map([["a1", 2]]), personen: null }, l, EIG, 1);
  assert.equal(csv.split("\r\n")[0].replace("﻿", ""), "adress_id,adresse_heute,adresse_1936,stadtteil,praezision,eintraege");
  assert.equal(csv.split("\r\n")[1], "a1,\"Lattenkamp 25, Katernberg\",\"Grenzstr. 25, Katernberg\",Katernberg,haus,2");
});

test("Vergleich: Spalte gruppe, Adresse in zwei Gruppen erscheint je Gruppe", async () => {
  const gruppen = [{ name: "Krupp", farbe: "#dc2626", adressIds: ["a1"], zaehler: new Map([["a1", 2]]) }, { name: "Stadt", farbe: "#2563eb", adressIds: ["a1"], zaehler: new Map([["a1", 1]]) }];
  const erg = { adressIds: ["a1"], zaehler: new Map([["a1", 3]]), personen: null, gruppen };
  const voll = (await csvAusTreffern(erg, l, EIG)).split("\r\n");
  assert.ok(voll[0].endsWith(",adress_id,gruppe"));
  assert.equal(voll.filter((z) => z.endsWith(",Krupp")).length, 2);
  assert.equal(voll.filter((z) => z.endsWith(",Stadt")).length, 2);
  const kurz = (await csvAusTreffern(erg, l, EIG, 1)).split("\r\n");
  assert.equal(kurz[0].replace("﻿", ""), "adress_id,adresse_heute,adresse_1936,stadtteil,praezision,eintraege,gruppe");
  assert.equal(kurz[1], "a1,\"Lattenkamp 25, Katernberg\",\"Grenzstr. 25, Katernberg\",Katernberg,haus,2,Krupp");
  assert.equal(kurz[2], "a1,\"Lattenkamp 25, Katernberg\",\"Grenzstr. 25, Katernberg\",Katernberg,haus,1,Stadt");
});
