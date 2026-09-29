import test from "node:test";
import assert from "node:assert/strict";
import { baumHtml, kopfHtml, grundlageHtml, PILLS_KURZ } from "../js/themenbaum.js";

const T = { id: "besitz", titel: "Besitz", text: "Häuser nach Art des Eigentümers.", grundlage: "eigentuemer.csv",
  farbe: { art: "kategorien", feld: "besitz", werte: { bergbau: "#111827", privatperson: "#d97706", gemischt: "#9a3412" }, sonst: "#c8c8c8" },
  schalter: { feld: "besitz", klassen: ["bergbau", "privatperson", "gemischt", "ungeprueft"] } };
const eintraege = (n, p) => Array.from({ length: n }, (_, i) => ({ schluessel: `eig:${p}${i}`, name: `${p}${i}`, adressen: 100 - i }));
const L = { oberkategorien: [
    { id: "bergbau", name: "Bergbau", adressen: 2, eintraege: eintraege(2, "Zeche ") },
    { id: "privatperson", name: "Privatperson", adressen: 300, eintraege: eintraege(20, "P") }],
  gemischt: 4, ungeprueft: 9, handgeprueft_anteil: null };
const opt = { klassen: "", vergleich: [], farben: ["#dc2626", "#2563eb"], offen: null, alle: null };

test("baumHtml: eine Zeile je Schalterklasse mit Kästchen, Farbpunkt, Name, Zahl; Pfeil nur mit Einträgen (Review Focus 4)", () => {
  const h = baumHtml(T, L, opt);
  assert.match(h, /<input type="checkbox" data-klasse="bergbau" checked><span class="punkt" style="background:#111827"><\/span> Bergbau <small>2<\/small>/);
  assert.match(h, /data-auf="bergbau"/); assert.match(h, /data-auf="privatperson"/);
  assert.doesNotMatch(h, /data-auf="gemischt"/); assert.doesNotMatch(h, /data-auf="ungeprueft"/);
  assert.match(h, /data-klasse="gemischt" checked>.*mehrere Kategorien <small>4<\/small>/);
  assert.match(h, /data-klasse="ungeprueft" checked>.*ungeprüft <small>9<\/small>/);
  assert.doesNotMatch(h, /pill-s/);                                  // nichts offen → keine Pills
});

test("baumHtml: Kästchen folgen klassen=; offene Kategorie zeigt 15 Pills mit Zahl und „alle n anzeigen“; alle=id zeigt alle", () => {
  const h = baumHtml(T, L, { ...opt, klassen: "privatperson", offen: "privatperson" });
  assert.match(h, /data-klasse="bergbau">/); assert.match(h, /data-klasse="privatperson" checked>/);
  assert.equal((h.match(/class="pill-s"/g) || []).length, PILLS_KURZ);
  assert.match(h, /<button class="pill-s" data-schluessel="eig:P0" aria-pressed="false" title="alle Häuser: P0">P0 <small>100<\/small><\/button>/);
  assert.match(h, /<button class="alle" data-alle="privatperson">alle 20 anzeigen<\/button>/);
  assert.match(h, /<button class="auf" data-auf="privatperson" aria-expanded="true"/);
  const v = baumHtml(T, L, { ...opt, offen: "privatperson", alle: "privatperson" });
  assert.equal((v.match(/class="pill-s"/g) || []).length, 20); assert.doesNotMatch(v, /data-alle=/);
  assert.equal((baumHtml(T, L, { ...opt, offen: "bergbau" }).match(/class="pill-s"/g) || []).length, 2);
});

test("baumHtml: gewählte Schlüssel sind gefüllt in ihrer Platzfarbe, Tooltip je Zustand", () => {
  const h = baumHtml(T, L, { ...opt, offen: "bergbau", vergleich: ["eig:X", "eig:Zeche 1"] });
  assert.match(h, /data-schluessel="eig:Zeche 1" aria-pressed="true" style="background:#2563eb;border-color:#2563eb;color:#fff" title="aus dem Vergleich entfernen"/);
  assert.match(h, /data-schluessel="eig:Zeche 0" aria-pressed="false" title="zum Vergleich hinzufügen"/);
  assert.match(baumHtml(T, L, { ...opt, offen: "bergbau" }), /data-schluessel="eig:Zeche 0" aria-pressed="false" title="alle Häuser: Zeche 0"/);
});

test("baumHtml ohne Liste (altes Datenpaket): Zeilen ohne Zahl und ohne Pfeil; Bergbau nimmt schalter.namen", () => {
  const h = baumHtml(T, null, opt);
  assert.match(h, /data-klasse="bergbau" checked>.*Bergbau<\/label>/); assert.doesNotMatch(h, /data-auf=/);
  const BB = { id: "bergbau", farbe: { art: "kategorien", feld: "bergbau", werte: { leitung: "#7c3aed" } }, schalter: { praefix: "n_bb_", klassen: ["leitung"], namen: { leitung: "Leitung und Beamte" } } };
  assert.match(baumHtml(BB, null, opt), /Leitung und Beamte/);
});

test("kopfHtml und grundlageHtml", () => {
  assert.equal(kopfHtml(T), `<div class="thema"><b>Besitz</b><p>Häuser nach Art des Eigentümers.</p><button data-thema-aus="1">Thema verlassen</button></div>`);
  assert.equal(grundlageHtml(T), `<small class="grundlage">eigentuemer.csv</small>`);
  assert.equal(grundlageHtml({ ...T, grundlage: "" }), "");
});

test("baumHtml Berufe: Anteil handgeprüft als Zeile unter dem Baum", () => {
  const B = { id: "berufe", farbe: { art: "kategorien", feld: "stellung", werte: { arbeiter: "#e69f00" } }, schalter: { feld: "stellung", klassen: ["arbeiter", "ungeprueft"] } };
  const h = baumHtml(B, { oberkategorien: [{ id: "arbeiter", name: "Arbeiter", adressen: 10, eintraege: [] }], gemischt: 0, ungeprueft: 1, handgeprueft_anteil: 0.437 }, opt);
  assert.match(h, /<div class="zeile klein">Stellung handgeprüft bei 44 % der Nennungen, sonst Vorschlag der Automatik.<\/div>/);
});
