import test from "node:test";
import assert from "node:assert/strict";
import { Lader } from "../js/daten.js";
import { normalisiere } from "../js/ansicht.js";
import { ladeEbenen } from "../js/daten_ebenen.js";
import { farbeAnteil, formatProzent, formatZahl } from "../js/formen/skalen.js";
import * as balken from "../js/formen/balken.js";
import * as rangliste from "../js/formen/rangliste.js";
import * as stadtteilkarte from "../js/formen/stadtteilkarte.js";
import * as bubbles from "../js/formen/bubbles.js";
import * as trichter from "../js/formen/trichter.js";

const Q = (x, y) => ({ type: "Feature", properties: { id: "", quelle: "OSM", stand: "d" }, geometry: { type: "MultiPolygon", coordinates: [[[[x, y], [x + 0.1, y], [x + 0.1, y + 0.1], [x, y + 0.1], [x, y]]]] } });
const D = {
  "daten/ebenen/stadtteile.json": [{ id: "Katernberg", lat: 51.5, lon: 7.05, adressen: 40, n_I: 100, n_st_arbeiter: 70, n_st_beamte: 5, n_st_unbestimmt: 25, rang_nord: 1, n_bs_bergbau: 20, n_bs_privatperson: 10, n_bs_ungeprueft: 10, n_besitz_regel: 7 },
                                   { id: "Südviertel", lat: 51.44, lon: 7.01, adressen: 30, n_I: 60, n_st_arbeiter: 10, n_st_beamte: 20, n_st_unbestimmt: 30, rang_nord: 2, n_bs_privatperson: 5, n_bs_ungeprueft: 25 }],
  "daten/stadtteile.geojson": { type: "FeatureCollection", features: [{ ...Q(7.0, 51.45), properties: { id: "Katernberg" } }, { ...Q(7.0, 51.4), properties: { id: "Südviertel" } }] },
  "daten/layout/eigentuemer.json": { kreise: [{ id: "Stadt Essen", n: 969, gruppe: "stadt_staat", r: 60, x: 0, y: 0 }, { id: "Fried. Krupp AG", n: 559, gruppe: "industrie", r: 45, x: 120, y: 0 }, { id: "X", n: 5, gruppe: "sonstige", r: 4, x: 0, y: 80 }], gruppen: [{ gruppe: "stadt_staat", x: 0, y: 0, r: 70 }] },
};
const fetchFake = async (u) => ({ ok: u in D, status: u in D ? 200 : 404, json: async () => D[u] });
const G = [{ name: "Arbeiter", aus: ["arbeiter"], farbe: "#e69f00" }, { name: "Beamte", aus: ["beamte"], farbe: "#009e73" }];
const daten = await ladeEbenen(new Lader("daten/", fetchFake));

test("Skalen", () => {
  assert.equal(farbeAnteil(0.1), "#f7fbff"); assert.equal(farbeAnteil(0.95), "#08306b"); assert.equal(farbeAnteil(0.4), "#6baed6");
  assert.equal(formatProzent(0.6333), "63 %"); assert.equal(formatZahl(70316), "70.316");
});

test("balken: Gesamtbalken mit Segmenten, unbestimmt grau, Zahlenzeile", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "balken", gruppen: G, bezug: "Arbeiter", min_n: 0 });
  const r = balken.zeige(a, daten, { breite: 600, hoehe: 200 });
  assert.match(r.svg, /^<svg/); assert.match(r.svg, /data-id="Arbeiter"/); assert.match(r.svg, /#c8c8c8/);
  assert.deepEqual(r.zahlen, { N: 105, n_aus: 55, unter_min: 0, einheiten: 2, einheiten_gesamt: 2, hinweis: "105 Nennungen einbezogen, 55 ausgeschlossen (unbestimmt, ungeprüft)" });
  assert.equal(r.legende.length, 3); assert.equal(r.legende[2].name, "ausgeschlossen");
  const je = balken.zeige({ ...a, filter: { je_einheit: true } }, daten, { breite: 600, hoehe: 200 });
  assert.match(je.svg, /data-id="Katernberg"/); assert.match(je.svg, /data-id="Südviertel"/);
});

test("balken: ausschlussText ersetzt „unbestimmt/ungeprüft“ in Legende und Segmenttitel", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "balken", gruppen: G, bezug: "Arbeiter", min_n: 0 });
  const r = balken.zeige(a, daten, { breite: 600, hoehe: 200, ausschlussText: "Beruf ungeprüft oder Stellung unbestimmt" });
  assert.equal(r.legende[2].text, "Beruf ungeprüft oder Stellung unbestimmt");
  assert.match(r.svg, /<title>Beruf ungeprüft oder Stellung unbestimmt: 55<\/title>/);
  const ohne = balken.zeige(a, daten, { breite: 600, hoehe: 200 });
  assert.equal(ohne.legende[2].text, "unbestimmt/ungeprüft");
});

test("rangliste: sortiert nach Wert, unter min_n ans Ende und grau, hervorheben", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "rangliste", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const r = rangliste.zeige(a, daten, { breite: 600, hoehe: 300, hervorheben: ["Südviertel"] });
  const ids = [...r.svg.matchAll(/data-id="([^"]+)"/g)].map((m) => m[1]);
  assert.deepEqual(ids, ["Katernberg", "Südviertel"]);
  assert.match(r.svg, /class="einheit hervorgehoben"[^>]*data-id="Südviertel"|data-id="Südviertel"[^>]*class="einheit[^"]*hervorgehoben/);
  assert.ok(!/font-weight/.test(r.svg), "Hervorhebung nur per Klasse, kein Inline-Gewicht");
  assert.match(r.svg, /unter-min/);
  assert.equal(r.zahlen.unter_min, 1);
  // Gefiltert: N/n_aus/einheiten zur gezeichneten Menge, unter_min weiterhin zur ganzen Ebene.
  const t = rangliste.zeige({ ...a, filter: { top: 1 } }, daten, { breite: 600, hoehe: 300 });
  assert.equal(t.zahlen.einheiten, 1); assert.equal(t.zahlen.unter_min, 1); assert.equal(t.zahlen.einheiten_gesamt, 2);
});

test("rangliste: zwei Spalten, wenn 48 Zeilen nicht lesbar untereinander passen", () => {
  assert.deepEqual(rangliste.spaltenWahl(48, 390, 450).spalten, 1);      // Handy: zu schmal für zwei Spalten → eine, Fläche wächst
  assert.deepEqual(rangliste.spaltenWahl(48, 700, 450).spalten, 2);      // Tablet quer: zwei Spalten
  assert.ok(rangliste.spaltenWahl(48, 700, 450).zeile >= 13);
  assert.deepEqual(rangliste.spaltenWahl(15, 700, 450), { spalten: 1, zeile: 28 });
  const st = Array.from({ length: 48 }, (_, i) => ({ id: `S${i}`, lat: 51.4, lon: 7, adressen: 10, n_I: 200, n_st_arbeiter: 100 + i, n_st_beamte: 50, rang_nord: i }));
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "rangliste", gruppen: G, bezug: "Arbeiter", min_n: 0 });
  const zwei = rangliste.zeige(a, { ...daten, stadtteile: st }, { breite: 700, hoehe: 450 });
  assert.equal((zwei.svg.match(/<g data-id=/g) || []).length, 48);
  assert.match(zwei.svg, /<text x="35[0-9.]*" /);                          // zweite Spalte beginnt rechts der Mitte
  const eins = rangliste.zeige(a, { ...daten, stadtteile: st }, { breite: 390, hoehe: 450 });
  assert.match(eins.svg, /viewBox="0 0 390 (6[0-9]{2}|7[0-9]{2})"/);       // eine Spalte: 48 × 13 px → die Fläche wächst
});

test("Legende nach Maß: dichte in absoluten Stufen, mischung als Mischungsgrad", () => {
  // Bei dichte darf keine Prozentstufe in der Legende stehen — gezeigt wird „je 1.000“.
  const d = normalisiere({ daten: "gewerbe", ebene: "stadtteil", form: "rangliste", mass: "dichte",
    gruppen: [{ name: "Lebensmittel", aus: ["lebensmittel"], farbe: "#d55e00" }], bezug: "Lebensmittel", min_n: 0 });
  for (const form of [rangliste, stadtteilkarte]) {
    const l = form.zeige(d, daten, { breite: 500, hoehe: 400 }).legende;
    assert.ok(l.filter((e) => e.art === "stufe").every((e) => /je 1\.000/.test(e.text)), "dichte-Stufen nennen je 1.000");
    assert.ok(!l.some((e) => /%/.test(e.text)), "keine Prozentangabe bei dichte");
    assert.equal(l.at(-1).name, "unter 0 Teil-I-Einträgen");
  }
  const m = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "rangliste", mass: "mischung", gruppen: G, min_n: 50 });
  for (const form of [rangliste, stadtteilkarte]) {
    const l = form.zeige(m, daten, { breite: 500, hoehe: 400 }).legende;
    assert.ok(l.filter((e) => e.art === "stufe").every((e) => /^Mischung /.test(e.text)), "Mischungsstufen");
    assert.equal(l[0].text, "Mischung 0,0–0,2");
    assert.equal(l.at(-1).name, "unter 50 Nennungen");
  }
});

test("balken bei Besitz: Hover-Text der Privatpersonen nennt den Regel-Anteil", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", form: "balken", gruppen: [{ name: "Privatpersonen", aus: ["privatperson"], farbe: "#d97706" }, { name: "Bergbau", aus: ["bergbau"], farbe: "#111827" }], min_n: 0 });
  const r = balken.zeige(a, daten, { breite: 600, hoehe: 200 });
  assert.match(r.svg, /<title>Privatpersonen: 15, davon 7 per Regel klassifiziert \(Person ohne Firmenname → Privatperson, keine Handprüfung\)<\/title>/);
  assert.match(r.svg, /<title>Bergbau: 20<\/title>/);
  const je = balken.zeige({ ...a, filter: { je_einheit: true } }, daten, { breite: 600, hoehe: 200 });
  assert.match(je.svg, /Privatpersonen: 10, davon 7 per Regel/);
  assert.match(je.svg, /<title>Privatpersonen: 5<\/title>/);           // Südviertel ohne Regel-Anteil
});

test("balken je_einheit: der Wert des Maßes steht neben dem Balken", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "balken", gruppen: G, bezug: "Arbeiter", min_n: 0,
    filter: { je_einheit: true } });
  assert.match(balken.zeige(a, daten, { breite: 600, hoehe: 200 }).svg, /class="wert">93 %</);
  const m = balken.zeige({ ...a, mass: "mischung" }, daten, { breite: 600, hoehe: 200 });
  assert.match(m.svg, /class="wert">0,\d\d</);
});

test("stadtteilkarte: Pfade je Polygon, Farbe nach Anteil, grau unter min_n", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "stadtteilkarte", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const r = stadtteilkarte.zeige(a, daten, { breite: 500, hoehe: 500 });
  assert.equal((r.svg.match(/<path/g) || []).length, 2);
  assert.match(r.svg, /data-id="Katernberg"[^>]*fill="#08306b"|fill="#08306b"[^>]*data-id="Katernberg"/);
  assert.match(r.svg, /data-id="Südviertel"[^>]*fill="#c8c8c8"|fill="#c8c8c8"[^>]*data-id="Südviertel"/);
  assert.equal(r.legende[0].text, "0–20 %"); assert.equal(r.legende.at(-1).name, "unter 50 Nennungen");
  assert.match(r.zahlen.hinweis, /heutige Stadtteilgrenzen/);
  assert.equal(stadtteilkarte.zeige(a, { ...daten, polygone: null }, { breite: 500, hoehe: 500 }).svg, "");
});

test("bubbles: Kreise aus dem Layout, Farbe nach Gruppe, hervorheben, Skalierung in die Fläche", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", form: "bubbles", gruppen: [{ name: "Stadt", aus: ["stadt_staat"], farbe: "#1d4ed8" }, { name: "Industrie", aus: ["industrie"], farbe: "#b91c1c" }], min_n: 0 });
  const r = bubbles.zeige(a, daten, { breite: 400, hoehe: 400, hervorheben: ["Fried. Krupp AG"] });
  // Jeder Kreis trägt die Zeile des Detailkastens: Zahl, Nenner, Gruppe (oder „in keiner Gruppe“).
  assert.match(r.svg, /data-id="Fried. Krupp AG" data-zeile="[\d.]+ Adressen mit Besitzklasse · Industrie"/);
  assert.equal((r.svg.match(/<circle class="einheit/g) || []).length, 3);
  assert.match(r.svg, /data-id="Stadt Essen"[^>]*fill="#1d4ed8"|fill="#1d4ed8"[^>]*data-id="Stadt Essen"/);
  assert.match(r.svg, /data-id="X"[^>]*fill="#c8c8c8"|fill="#c8c8c8"[^>]*data-id="X"/);   // in keiner Gruppe → grau
  assert.match(r.svg, /hervorgehoben/);
  assert.equal(r.zahlen.einheiten, 3); assert.equal(r.zahlen.einheiten_gesamt, 3);
  assert.equal(bubbles.zeige({ ...a, daten: "niveau" }, daten, { breite: 400, hoehe: 400 }).svg, "");   // kein Layout für niveau → leer
});

const KZ = { eintraege: 1000, verortet: 800, adressen: 300, stufe_haus: 500, stufe_strasse: 300, stand: "2026-09-27" };
const T = { daten: "kennzahlen", form: "trichter",
  stufen: [{ name: "Zeilen", aus: "eintraege", farbe: "#94a3b8" },
           { name: "verortet", aus: "verortet", farbe: "#1d4ed8", segmente: [
             { name: "hausgenau", aus: "stufe_haus", farbe: "#1d4ed8" },
             { name: "straßengenau", aus: "stufe_strasse", farbe: "#60a5fa", muster: "schraffur" }] },
           { name: "Adressen", aus: "adressen", farbe: "#1d4ed8" }],
  erklaerungen: { verortet: "Zeilen mit Punkt auf der Karte." } };

test("trichter: Breiten proportional zur ersten Stufe, Segmente, Schraffur, Einheiten", () => {
  const r = trichter.zeige(T, { kennzahlen: KZ }, { breite: 600, hoehe: 300 });
  assert.match(r.svg, /^<svg/);
  // Stufe ohne Segmente ist selbst die Einheit; Stufe mit Segmenten trägt die Segmente als Einheiten
  assert.match(r.svg, /class="einheit" data-id="eintraege"/);
  assert.match(r.svg, /class="einheit" data-id="stufe_haus"/);
  assert.match(r.svg, /class="einheit" data-id="stufe_strasse"/);
  assert.ok(!/data-id="verortet"/.test(r.svg), "Stufe mit Segmenten ist keine eigene Einheit");
  // Breiten: verortet = 80 % der Zeilen, hausgenau 5/8 davon
  const b = (id) => Number(r.svg.match(new RegExp(`data-id="${id}"[^>]*width="([\\d.]+)"`))[1]);
  assert.ok(Math.abs(b("stufe_haus") / b("eintraege") - 0.5) < 0.01);
  assert.ok(Math.abs(b("stufe_strasse") / b("eintraege") - 0.3) < 0.01);
  assert.match(r.svg, /<pattern id="schraffur-stufe_strasse"/); assert.match(r.svg, /fill="url\(#schraffur-stufe_strasse\)"/);
  assert.match(r.svg, /800 von 1\.000 \(80 %\)/); assert.match(r.svg, /300 von 1\.000 \(30 %\)/);
  assert.deepEqual(r.zahlen, { N: 1000, n_aus: 0, unter_min: 0, einheiten: 4, hinweis: "Stand 2026-09-27" });
  assert.deepEqual(r.legende.map((l) => [l.name, l.muster || ""]), [["hausgenau", ""], ["straßengenau", "schraffur"]]);
  const v = r.werte.find((w) => w.id === "stufe_strasse");
  assert.deepEqual([v.name, v.wert, v.basis, v.basisName, v.muster], ["straßengenau", 300, 1000, "Zeilen", "schraffur"]);
  assert.equal(r.werte.find((w) => w.id === "eintraege").erklaerung, "");
});

test("trichter: fehlende Kennzahl, erste Stufe 0 und übergroße Segmente brechen nichts", () => {
  // Review Focus 1: alter Export ohne Schlüssel → „—“, Breite 0, kein NaN
  const alt = trichter.zeige(T, { kennzahlen: { eintraege: 1000 } }, { breite: 600, hoehe: 300 });
  assert.ok(!/NaN/.test(alt.svg)); assert.match(alt.svg, /—/);
  assert.equal(alt.werte.find((w) => w.id === "adressen").wert, null);
  // Review Focus 2: erste Stufe 0
  const leer = trichter.zeige(T, { kennzahlen: { eintraege: 0, verortet: 0, adressen: 0, stufe_haus: 0, stufe_strasse: 0 } }, { breite: 600, hoehe: 300 });
  assert.ok(!/NaN/.test(leer.svg)); assert.match(leer.svg, /0 von 0 \(0 %\)/);
  // Review Focus 3: Segmente größer als die Stufe → auf die Stufenbreite begrenzt
  const gross = trichter.zeige(T, { kennzahlen: { ...KZ, stufe_haus: 900, stufe_strasse: 900 } }, { breite: 600, hoehe: 300 });
  const b = (svg, id) => Number(svg.match(new RegExp(`data-id="${id}"[^>]*width="([\\d.]+)"`))[1]);
  assert.ok(b(gross.svg, "stufe_haus") + b(gross.svg, "stufe_strasse") <= b(gross.svg, "eintraege") * 0.8 + 0.01);
});
