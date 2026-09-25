import test from "node:test";
import assert from "node:assert/strict";
import { normalisiere } from "../js/ansicht.js";
import { werteFarben, legendeFuer } from "../js/ansicht_farben.js";
import { GRAU, SEQUENZ } from "../js/formen/skalen.js";

const ANSICHT = (o) => normalisiere({
  daten: "stellung", ebene: "stadtteil", form: "karte", min_n: 200,
  gruppen: [{ name: "Arbeiter", aus: ["arbeiter"], farbe: "#e69f00" }, { name: "übrige", aus: ["angestellte"], farbe: "#999999" }],
  bezug: "Arbeiter", ...o,
});

test("Einheiten unter min_n bleiben grau", () => {
  const a = ANSICHT({ mass: "anteil" });
  const m = werteFarben([{ id: "A", wert: 0.9, unter_min: true, N: 10, n_aus: 0 }], a);
  assert.equal(m.get("A").farbe, GRAU);
  assert.equal(m.get("A").unter_min, true);
});

test("dominant nutzt Gruppenfarbe, gemischt wird grau", () => {
  const a = ANSICHT({ mass: "dominant" });
  const m = werteFarben([
    { id: "A", wert: "Arbeiter", dominant: "Arbeiter", unter_min: false, N: 500, n_aus: 0 },
    { id: "B", wert: "gemischt", dominant: "gemischt", unter_min: false, N: 500, n_aus: 0 },
  ], a);
  assert.equal(m.get("A").farbe, "#e69f00");
  assert.equal(m.get("B").farbe, GRAU);
});

test("anteil färbt nach Stufe", () => {
  const a = ANSICHT({ mass: "anteil" });
  const m = werteFarben([{ id: "A", wert: 0.1, unter_min: false, N: 500, n_aus: 0 },
                         { id: "B", wert: 0.95, unter_min: false, N: 500, n_aus: 0 }], a);
  assert.equal(m.get("A").farbe, SEQUENZ[0]);
  assert.equal(m.get("B").farbe, SEQUENZ[4]);
});

test("dichte wird am Höchstwert der auswertbaren Einheiten skaliert", () => {
  const a = ANSICHT({ daten: "gewerbe", mass: "dichte" });
  const m = werteFarben([
    { id: "A", wert: 100, unter_min: false, N: 500, n_aus: 0 },
    { id: "B", wert: 20, unter_min: false, N: 500, n_aus: 0 },
    { id: "C", wert: 999, unter_min: true, N: 5, n_aus: 0 },
  ], a);
  assert.equal(m.get("A").farbe, SEQUENZ[4]);   // 100/100 → oberste Stufe
  assert.equal(m.get("B").farbe, SEQUENZ[1]);   // 20/100 → zweite Stufe
  assert.equal(m.get("C").farbe, GRAU);         // unter min_n zählt nicht zum Höchstwert
});

test("Legende nennt min_n, Grundlage und Herkunft", () => {
  const a = ANSICHT({ mass: "anteil" });
  const werte = [{ id: "A", wert: 0.5, unter_min: false, N: 400, n_aus: 30 },
                 { id: "B", wert: 0.1, unter_min: true, N: 10, n_aus: 2 }];
  const l = legendeFuer(a, werte);
  assert.equal(l.filter((e) => e.farbe === SEQUENZ[0]).length, 1);
  const min = l.find((e) => e.art === "min_n");
  assert.ok(min && min.farbe === GRAU && /200/.test(min.text) && /1 /.test(min.text));
  const grundlage = l.find((e) => e.art === "grundlage");
  assert.ok(grundlage && /410/.test(grundlage.text) && /32/.test(grundlage.text));
  assert.ok(l.some((e) => e.art === "herkunft" && /Stadtteilgrenzen/.test(e.text)));
  assert.ok(legendeFuer(ANSICHT({ ebene: "strasse" }), werte).some((e) => e.art === "herkunft" && /Straßenlinien/.test(e.text)));
});

test("Legende bei dominant listet Gruppen und gemischt", () => {
  const l = legendeFuer(ANSICHT({ mass: "dominant" }), []);
  assert.deepEqual(l.filter((e) => e.art === "gruppe").map((e) => e.name), ["Arbeiter", "übrige"]);
  assert.ok(l.some((e) => e.name === "gemischt" && e.farbe === GRAU));
});
