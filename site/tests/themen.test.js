import test from "node:test";
import assert from "node:assert/strict";
import { farbregel, ladeThema, themenListe } from "../js/themen.js";
import { Lader } from "../js/daten.js";

const AK = { id: "akademiker", titel: "Akademiker", text: "…", grundlage: "Titelliste", freigegeben: true,
  filter: { merkmal: "akademiker", ebenen: ["I"] }, farbe: { art: "einfach", wert: "#7c3aed" }, zusatz: { zechen: false }, legende: "lila = Akademiker", darstellung: "punkte" };
const DATEIEN = { "daten/themen/akademiker.json": AK, "daten/themen/index.json": [{ id: "akademiker", titel: "Akademiker", freigegeben: true }, { id: "bergbau", titel: "Bergbau", freigegeben: false }] };
const fetchFake = async (u) => ({ ok: u in DATEIEN, status: u in DATEIEN ? 200 : 404, json: async () => DATEIEN[u] });

test("farbregel einfach und skala", () => {
  assert.deepEqual(farbregel(AK), { merkmal: "akademiker", ausdruck: "#7c3aed" });
  const s = farbregel({ filter: {}, farbe: { art: "skala", merkmal: "schicht", stufen: [[0, "#000"], [2, "#fff"]] } });
  assert.equal(s.merkmal, "schicht");
  assert.equal(s.ausdruck[0], "interpolate");
  assert.equal(farbregel({ filter: {} }), null);
});

test("ladeThema hängt farbregel und ebenen an, unbekannt → null", async () => {
  const l = new Lader("daten/", fetchFake);
  const t = await ladeThema(l, "akademiker");
  assert.equal(t.farbregel.merkmal, "akademiker");
  assert.deepEqual(t.ebenen, ["I"]);
  assert.equal(await ladeThema(l, "gibtsnicht"), null);
});

test("ladeThema liefert kacheln aus dem Index; ohne Index-Eintrag false (altes Datenpaket)", async () => {
  const thema = { id: "bergbau", titel: "Bergbau", freigegeben: true, farbe: { art: "einfach", wert: "#000" } };
  const laderMit = { thema: async () => thema, json: async (p) => p === "themen/index.json" ? [{ id: "bergbau", titel: "Bergbau", freigegeben: true, kacheln: true }] : null };
  assert.equal((await ladeThema(laderMit, "bergbau")).kacheln, true);
  const laderOhne = { thema: async () => thema, json: async () => [{ id: "bergbau", titel: "Bergbau", freigegeben: true }] };
  assert.equal((await ladeThema(laderOhne, "bergbau")).kacheln, false);
  const laderLeer = { thema: async () => thema, json: async () => null };
  assert.equal((await ladeThema(laderLeer, "bergbau")).kacheln, false);
  // Lader-Klasse: Index-Eintrag ohne Flag → false
  assert.equal((await ladeThema(new Lader("daten/", fetchFake), "akademiker")).kacheln, false);
});

test("themenListe nur freigegebene", async () => {
  assert.deepEqual(await themenListe(new Lader("daten/", fetchFake)), [{ id: "akademiker", titel: "Akademiker" }]);
});

test("farbregel kategorien → match-Ausdruck", () => {
  const r = farbregel({ filter: {}, farbe: { art: "kategorien", feld: "besitz", werte: { industrie: "#b91c1c", stadt_staat: "#1d4ed8" }, sonst: "#ccc" } });
  assert.equal(r.merkmal, null);
  assert.deepEqual(r.ausdruck, ["match", ["get", "besitz"], "industrie", "#b91c1c", "stadt_staat", "#1d4ed8", "#ccc"]);
  assert.deepEqual(r.kategorien, { industrie: "#b91c1c", stadt_staat: "#1d4ed8" });
});

import { schalterFarbe, schalterFilter, schalterKlassen } from "../js/themen.js";
const BB = { id: "bergbau", titel: "Bergbau", freigegeben: true, filter: { ebenen: ["I"] },
  farbe: { art: "kategorien", feld: "bergbau", werte: { leitung: "#7c3aed", aufsicht: "#1d4ed8", belegschaft: "#c2410c", invaliden: "#15803d" } },
  schalter: { praefix: "n_bb_", klassen: ["leitung", "aufsicht", "belegschaft", "invaliden"], namen: { leitung: "Leitung und Beamte", aufsicht: "Aufsicht", belegschaft: "Belegschaft", invaliden: "Berginvaliden" } },
  zusatz: { zechen: true }, legende: "Farbe: höchste Bergbau-Gruppe im Haus" };

test("schalterKlassen: leer = alle, keine = [], unbekannte Werte fallen weg, Reihenfolge des Themas", () => {
  assert.deepEqual(schalterKlassen(BB, ""), ["leitung", "aufsicht", "belegschaft", "invaliden"]);
  assert.deepEqual(schalterKlassen(BB, "keine"), []);
  assert.deepEqual(schalterKlassen(BB, "belegschaft,quatsch,leitung"), ["leitung", "belegschaft"]);
  assert.deepEqual(schalterKlassen({ id: "besitz" }, "leitung"), []);
});

test("schalterFilter: any über eingeschaltete Klassen; alle aus → null; Thema ohne Schalter → null", () => {
  assert.deepEqual(schalterFilter(BB, "leitung,belegschaft"),
    ["any", [">", ["coalesce", ["get", "n_bb_leitung"], 0], 0], [">", ["coalesce", ["get", "n_bb_belegschaft"], 0], 0]]);
  assert.equal(schalterFilter(BB, "keine"), null);
  assert.equal(schalterFilter({ id: "besitz", farbe: { art: "kategorien", feld: "besitz", werte: {} } }, "leitung"), null);
});

test("schalterFarbe: case nach Rang über eingeschaltete Klassen, sonst Grau", () => {
  const f = schalterFarbe(BB, "aufsicht,belegschaft");
  assert.deepEqual(f, ["case", [">", ["coalesce", ["get", "n_bb_aufsicht"], 0], 0], "#1d4ed8", [">", ["coalesce", ["get", "n_bb_belegschaft"], 0], 0], "#c2410c", "#c8c8c8"]);
  // Haus mit Bergmann und Zechenbeamtem bei klassen=leitung: lila; Haus nur mit Bergmann: Grau (und per Filter weg)
  const nur = schalterFarbe(BB, "leitung");
  assert.deepEqual(nur, ["case", [">", ["coalesce", ["get", "n_bb_leitung"], 0], 0], "#7c3aed", "#c8c8c8"]);
});

test("farbregel mit Schalter trägt filter und klassen; ohne Schalter ignoriert sie klassen", () => {
  const r = farbregel(BB, "leitung");
  assert.deepEqual(r.filter, ["any", [">", ["coalesce", ["get", "n_bb_leitung"], 0], 0]]);
  assert.deepEqual(r.klassen, ["leitung"]); assert.equal(r.ausdruck[0], "case");
  const b = farbregel({ filter: {}, farbe: { art: "kategorien", feld: "besitz", werte: { bergbau: "#111" } } }, "leitung");
  assert.equal(b.filter, null); assert.equal(b.ausdruck[0], "match");
});

test("schalterFarbe ohne eingeschaltete Klasse: schlichte Grundfarbe, kein leeres case (MapLibre lehnt case mit einem Argument ab)", () => {
  assert.equal(schalterFarbe(BB, "keine"), "#c8c8c8");
  assert.equal(farbregel(BB, "keine").ausdruck, "#c8c8c8");
});
