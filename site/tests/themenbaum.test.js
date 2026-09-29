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
  assert.match(h, /<input type="checkbox" id="klasse-bergbau" data-klasse="bergbau" checked><\/label><button class="punkt" data-nur="bergbau" style="background:#111827"[^>]*><\/button><label class="schalter name" for="klasse-bergbau"> Bergbau <small title="[^"]*">2<\/small><\/label>/);
  assert.match(h, /data-auf="bergbau"/); assert.match(h, /data-auf="privatperson"/);
  assert.doesNotMatch(h, /data-auf="gemischt"/); assert.doesNotMatch(h, /data-auf="ungeprueft"/);
  assert.match(h, /data-klasse="gemischt" checked>.*mehrere Kategorien <small title="[^"]*">4<\/small>/);
  assert.match(h, /data-klasse="ungeprueft" checked>.*ungeprüft <small title="[^"]*">9<\/small>/);
  assert.doesNotMatch(h, /pill-s/);                                  // nichts offen → keine Pills
});

test("baumHtml: Kästchen folgen klassen=; offene Kategorie zeigt 15 Pills mit Zahl und „alle n anzeigen“; alle=id zeigt alle", () => {
  const h = baumHtml(T, L, { ...opt, klassen: "privatperson", offen: "privatperson" });
  assert.match(h, /data-klasse="bergbau">/); assert.match(h, /data-klasse="privatperson" checked>/);
  assert.equal((h.match(/class="pill-s"/g) || []).length, PILLS_KURZ);
  assert.match(h, /<button class="pill-s" data-schluessel="eig:P0" aria-pressed="false" title="alle Häuser: P0">P0 <small title="[^"]*">100<\/small><\/button>/);
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
  assert.match(h, /<div class="zeile klein">Stellung handgeprüft bei 44 % der Nennungen mit geprüftem Beruf, sonst Vorschlag der Automatik.<\/div>/);
});

test("baumHtml: Zeile „alle an / alle aus“ über dem Baum, der wirkungslose Knopf ist deaktiviert; Farbpunkt = „nur diese“", () => {
  const alle = baumHtml(T, L, opt);
  assert.match(alle, /<div class="zeile alle-klassen"><button data-alle-an="1" disabled>alle an<\/button><button data-alle-aus="1">alle aus<\/button><small>Punkt anklicken = nur diese Klasse<\/small><\/div>/);
  const keine = baumHtml(T, L, { ...opt, klassen: "keine" });
  assert.match(keine, /<button data-alle-an="1">alle an<\/button><button data-alle-aus="1" disabled>alle aus<\/button>/);
  const teil = baumHtml(T, L, { ...opt, klassen: "bergbau" });
  assert.match(teil, /<button data-alle-an="1">alle an<\/button><button data-alle-aus="1">alle aus<\/button>/);
  assert.match(alle, /<button class="punkt" data-nur="bergbau" style="background:#111827" title="nur Bergbau zeigen" aria-label="nur Bergbau zeigen"><\/button>/);
  assert.match(baumHtml(T, null, opt), /data-nur="privatperson"/);
});

test("Minors nach Review: Legendensatz als erste Zeile, Tooltips an den Zahlen, Hinweis bei klassen=keine, Nenner des Handgeprüft-Satzes", () => {
  const TL = { ...T, legende: "Farbe = Kategorie des geprüften Eigentümers" };
  const h = baumHtml(TL, L, { ...opt, offen: "bergbau" });
  assert.match(h, /<div class="baum"><div class="zeile klein legende-satz">Farbe = Kategorie des geprüften Eigentümers<\/div>/);
  assert.match(h, /Bergbau <small title="Häuser mit mindestens einem Eintrag dieser Gruppe">2<\/small>/);
  assert.match(h, /Zeche 0 <small title="Häuser mit mindestens einer Nennung dieser Bezeichnung">100<\/small>/);
  assert.match(baumHtml(TL, L, { ...opt, klassen: "keine" }), /<div class="zeile klein">Keine Klasse gewählt – alle Adressen in Grundfarbe\.<\/div>/);
  assert.doesNotMatch(h, /Keine Klasse gewählt/);
  const B = { id: "berufe", farbe: { art: "kategorien", feld: "stellung", werte: { arbeiter: "#e69f00" } }, schalter: { feld: "stellung", klassen: ["arbeiter", "ungeprueft"] } };
  assert.match(baumHtml(B, { oberkategorien: [], gemischt: 0, ungeprueft: 0, handgeprueft_anteil: 0.916 }, opt), /Stellung handgeprüft bei 92 % der Nennungen mit geprüftem Beruf, sonst Vorschlag der Automatik\./);
});

test("baumHtml für ein Kategorien-Thema ohne Schalter: Zeilen mit Farbpunkt und Name, ohne Kästchen, ohne Knopfzeile", () => {
  const K = { id: "x", legende: "Farbe = Klasse", farbe: { art: "kategorien", feld: "besitz", werte: { bergbau: "#111827", privatperson: "#d97706" }, sonst: "#c8c8c8" } };
  const h = baumHtml(K, null, opt);
  assert.match(h, /legende-satz/);
  assert.doesNotMatch(h, /data-klasse|data-alle-an|data-nur/);
  assert.match(h, /<div class="zeile ober"><span class="punkt" style="background:#111827"><\/span> Bergbau<\/div>/);
  assert.match(h, /<span class="punkt" style="background:#c8c8c8"><\/span> ungeprüft<\/div>/);
});
