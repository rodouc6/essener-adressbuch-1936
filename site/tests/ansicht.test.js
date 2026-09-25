import test from "node:test";
import assert from "node:assert/strict";
import { MIN_N, STANDARD_ANSICHT, dekodiere, kennzahlen, kodiere, normalisiere, praefix, schluesselDerEinheit, standardGruppen } from "../js/ansicht.js";

const G = [{ name: "Arbeiter", aus: ["arbeiter"], farbe: "#e69f00" }, { name: "Bürgertum", aus: ["beamte", "freie_berufe", "unternehmer", "angestellte"], farbe: "#0072b2" }];
const E = { id: "Katernberg", n_I: 100, n_st_arbeiter: 60, n_st_beamte: 5, n_st_angestellte: 5, n_st_selbstaendige: 10, n_st_kaufleute: 4, n_st_unbestimmt: 16, adressen: 40 };

test("normalisiere füllt Standard, min_n je Ebene, Farben und eindeutige Namen", () => {
  const a = normalisiere({ daten: "stellung", ebene: "strasse", form: "hüpf", gruppen: [{ name: "A", aus: ["arbeiter"] }, { name: "A", aus: ["beamte"] }] });
  assert.equal(a.form, "karte"); assert.equal(a.min_n, MIN_N.strasse);
  assert.deepEqual(a.gruppen.map((g) => g.name), ["A", "A 2"]);
  assert.equal(a.gruppen[0].farbe, "#e69f00"); assert.equal(a.gruppen[1].farbe, "#56b4e9");
  assert.deepEqual(normalisiere({}), STANDARD_ANSICHT);
  // Farben aus der URL dürfen nicht aus dem SVG-Attribut ausbrechen.
  assert.equal(normalisiere({ gruppen: [{ name: "A", aus: ["x"], farbe: '#fff" onclick="x' }] }).gruppen[0].farbe, "#e69f00");
});

test("kodiere/dekodiere Rundreise, Standardwerte fallen weg, Unsinn → Standard", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const s = kodiere(a);
  assert.match(s, /^[A-Za-z0-9_-]+$/);
  assert.deepEqual(dekodiere(s), a);
  assert.ok(!JSON.parse(Buffer.from(s.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString()).kaufleute);
  assert.deepEqual(dekodiere("%%%"), STANDARD_ANSICHT);
});

test("praefix und Schlüssel der Einheit, Kaufleute-Umschalten", () => {
  assert.equal(praefix("stellung"), "n_st_"); assert.equal(praefix("gewerbe"), "n_gw_"); assert.equal(praefix("niveau"), "n_");
  const a = normalisiere({ daten: "stellung", gruppen: G, bezug: "Arbeiter" });
  assert.deepEqual(schluesselDerEinheit(E, a), { arbeiter: 60, beamte: 5, angestellte: 5, selbstaendige: 10, kaufleute: 4, unbestimmt: 16 });
  const b = normalisiere({ daten: "stellung", gruppen: G, bezug: "Arbeiter", kaufleute: "angestellte" });
  assert.deepEqual(schluesselDerEinheit(E, b).angestellte, 9);
  assert.equal(schluesselDerEinheit(E, b).kaufleute, undefined);
});

test("kennzahlen: N, n_aus, Anteile, unter_min, dominant, mischung", () => {
  const a = normalisiere({ daten: "stellung", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const k = kennzahlen(E, a);
  assert.equal(k.N, 70); assert.equal(k.n_aus, 30);            // selbstaendige 10 + kaufleute 4 + unbestimmt 16
  assert.equal(k.anteile["Arbeiter"], 60 / 70); assert.equal(k.wert, 60 / 70); assert.equal(k.unter_min, false);
  assert.equal(k.dominant, "Arbeiter");
  const d = kennzahlen(E, normalisiere({ ...a, mass: "dominant", min_n: 200 }));
  assert.equal(d.unter_min, true); assert.equal(d.wert, "Arbeiter");
  const gleich = kennzahlen({ n_st_arbeiter: 10, n_st_beamte: 10 }, normalisiere({ daten: "stellung", gruppen: G, mass: "mischung", min_n: 0 }));
  assert.equal(gleich.mischung, 1); assert.equal(gleich.wert, 1);
  const eins = kennzahlen({ n_st_arbeiter: 10 }, normalisiere({ daten: "stellung", gruppen: G, mass: "mischung", min_n: 0 }));
  assert.equal(eins.mischung, 0);
  assert.equal(kennzahlen({ n_st_arbeiter: 3, n_st_beamte: 3 }, normalisiere({ daten: "stellung", gruppen: G, mass: "dominant", min_n: 0 })).wert, "gemischt");
  assert.equal(kennzahlen({ n_st_arbeiter: 45, n_st_beamte: 55 }, normalisiere({ daten: "stellung", gruppen: G, mass: "dominant", min_n: 0 })).wert, "Bürgertum");
  assert.equal(kennzahlen({ n_st_arbeiter: 41, n_st_beamte: 59 }, normalisiere({ daten: "stellung", gruppen: G, mass: "dominant", min_n: 0 })).wert, "Bürgertum");
  assert.equal(kennzahlen({ n_st_arbeiter: 59, n_st_beamte: 41 }, normalisiere({ daten: "stellung", gruppen: G, mass: "dominant", min_n: 0 })).wert, "Arbeiter");
  assert.equal(kennzahlen({}, a).N, 0); assert.equal(kennzahlen({}, a).wert, 0);
});

test("dichte nur für gewerbe: Betriebe je 1.000 Teil-I-Einträge", () => {
  const a = normalisiere({ daten: "gewerbe", gruppen: [{ name: "Lebensmittel", aus: ["lebensmittel"], farbe: "#000" }], bezug: "Lebensmittel", mass: "dichte", min_n: 0 });
  assert.equal(kennzahlen({ n_I: 500, n_gw_lebensmittel: 25, n_gw_bau: 5 }, a).wert, 50);
  assert.equal(kennzahlen({ n_I: 0, n_gw_lebensmittel: 25 }, a).wert, null);
});

test("standardGruppen je Datenkern", () => {
  assert.equal(standardGruppen("stellung").length, 8);
  assert.equal(standardGruppen("besitz").length, 8);
  assert.equal(standardGruppen("gewerbe").length, 15);
  const hg = { B21: { kurz: "Bergbau, Glas, Keramik" }, A10: { kurz: "Berufslose" } };
  assert.deepEqual(standardGruppen("gruppe", hg).map((g) => [g.name, g.aus]), [["Berufslose", ["A10"]], ["Bergbau, Glas, Keramik", ["B21"]]]);
});
