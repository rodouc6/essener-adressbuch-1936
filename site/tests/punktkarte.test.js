import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { normalisiere, standardGruppen } from "../js/ansicht.js";
import { aktualisiere, berechne, raster, zeige } from "../js/formen/punktkarte.js";

const G = standardGruppen("bergbau");
const Q = (id, x, y) => ({ type: "Feature", properties: { id }, geometry: { type: "Polygon", coordinates: [[[x, y], [x + 0.1, y], [x + 0.1, y + 0.1], [x, y + 0.1], [x, y]]] } });
const PUNKTE = {
  gruppen: [{ id: "belegschaft", name: "Belegschaft", n: 5, felder: 2 }, { id: "aufsicht", name: "Aufsicht", n: 1, felder: 1 }, { id: "leitung", name: "Leitung und Beamte", n: 0, felder: 0 }, { id: "invaliden", name: "Berginvaliden", n: 0, felder: 0 }],
  hex: { belegschaft: [{ id: "0_0", lon: 7.01, lat: 51.45, n: 4, r: 9, x: 0, y: 0 }, { id: "1_0", lon: 7.02, lat: 51.46, n: 1, r: 4.5, x: 14, y: 0 }],
         aufsicht: [{ id: "0_0", lon: 7.01, lat: 51.45, n: 1, r: 4.5, x: 0, y: 0 }], leitung: [], invaliden: [] },
  haeuser: [{ id: "a1", lon: 7.01, lat: 51.45, eig: "gewerkschaft_mathias_stinnes", stufe: "haus" }, { id: "a2", lon: 7.02, lat: 51.46, eig: "zeche_x", stufe: "strasse" }],
  gesellschaften: [{ id: "gewerkschaft_mathias_stinnes", name: "Gewerkschaft Mathias Stinnes", haeuser: 1 }, { id: "zeche_x", name: "Zeche X", haeuser: 1 }],
  maxn: 4,
};
const DATEN = { punkte: PUNKTE, polygone: { type: "FeatureCollection", features: [Q("Katernberg", 7.0, 51.4)] },
  zechen: { type: "FeatureCollection", features: [{ type: "Feature", geometry: { type: "Point", coordinates: [7.05, 51.45] }, properties: { name: "Zollverein", aktiv_1936: true } }, { type: "Feature", geometry: { type: "Point", coordinates: [7.0, 51.4] }, properties: { name: "Alt", aktiv_1936: false } }] },
  kennzahlen: { teil_i_n: 100, beruf_geprueft_n: 80 } };
const A = (punkte) => normalisiere({ daten: "bergbau", ebene: "hex", form: "punktkarte", gruppen: G, bezug: "Belegschaft", min_n: 0, punkte });
const O = { breite: 1000, hoehe: 700 };

test("gesammelt: ein Kreis je Feld und Gruppe, Packung nebeneinander, Karten unsichtbar", () => {
  const r = zeige(A({ zustand: "gesammelt" }), DATEN, O);
  assert.equal((r.svg.match(/<circle class="einheit p"/g) || []).length, 3);
  assert.match(r.svg, /data-id="0_0\|belegschaft"[^>]*data-gruppe="belegschaft"/);
  assert.match(r.svg, /<g class="karte" data-g="belegschaft" style="opacity:0"/);
  assert.match(r.svg, /Belegschaft/); assert.match(r.svg, /5 eingetragene Personen/);
  const b = berechne(A({ zustand: "gesammelt" }), DATEN, O);
  const xs = b.titel.map((t) => t.x);
  assert.deepEqual([...xs].sort((p, q) => p - q), xs);                    // nach Größe sortiert von links nach rechts
  assert.ok(b.kreise.every((k) => k.x >= 0 && k.x <= 1000 && k.y >= 0 && k.y <= 700));
  assert.equal(r.zahlen.N, 6); assert.equal(r.zahlen.n_aus, 20);           // ungeprüfte Berufe als Ausschluss
  assert.equal(r.legende.find((l) => l.name === "Belegschaft").text, "Belegschaft · 5");
  assert.match(r.legende.map((l) => l.text).join(" "), /größter Wert 4/);
});

test("karten: jeder Kreis liegt im Feld seiner Gruppe, Mindestradius, nur Zechen in Förderung", () => {
  const b = berechne(A({ zustand: "karten" }), DATEN, O);
  for (const k of b.kreise) {
    const f = b.karten.find((c) => c.gruppe === k.gruppe);
    assert.ok(k.x >= f.x && k.x <= f.x + f.w && k.y >= f.y && k.y <= f.y + f.h, `${k.id} außerhalb`);
  }
  assert.ok(b.kreise.every((k) => k.r >= 1.6));
  assert.equal(b.karten[0].zechen.length, 1); assert.equal(b.karten[0].zechen[0].name, "Zollverein");
  const r = zeige(A({ zustand: "karten" }), DATEN, O);
  assert.match(r.svg, /<g class="karte" data-g="belegschaft" style="opacity:1"/);
  assert.match(r.svg, /<use class="zeche" href="#pk-zeche"/);
});

test("hervor dimmt die anderen Gruppen", () => {
  const b = berechne(A({ zustand: "karten", hervor: ["Belegschaft"] }), DATEN, O);
  assert.ok(b.kreise.filter((k) => k.gruppe === "aufsicht").every((k) => k.gedimmt));
  assert.ok(b.kreise.filter((k) => k.gruppe === "belegschaft").every((k) => !k.gedimmt));
  assert.match(zeige(A({ zustand: "karten", hervor: ["Belegschaft"] }), DATEN, O).svg, /class="einheit p gedimmt"/);
});

test("haeuser: ein Punkt je Haus, Farbe nach Gesellschaft, Ring bei nur straßengenau, Rest grau", () => {
  const a = normalisiere({ daten: "besitz", ebene: "adresse", form: "punktkarte", min_n: 0, bezug: "Stinnes",
    gruppen: [{ name: "Stinnes", aus: ["gewerkschaft_mathias_stinnes"], farbe: "#e69f00" }], punkte: { zustand: "haeuser" } });
  const r = zeige(a, DATEN, O);
  assert.equal((r.svg.match(/<circle class="einheit p/g) || []).length, 2);
  assert.match(r.svg, /data-id="a1"[^>]*fill="#e69f00"/);
  assert.match(r.svg, /data-id="a2"[^>]*fill="none"[^>]*stroke="#c8c8c8"/);
  assert.equal(r.zahlen.N, 2); assert.match(r.legende.map((l) => l.text).join(" "), /Ring: nur straßengenau oder Stadtplan 1935 \(1\)/);
  assert.match(r.legende.map((l) => l.text).join(" "), /übrige Bergbau-Eigentümer/);
});

test("raster: zwei Spalten ab 600 px, sonst eine", () => {
  assert.deepEqual(raster(1000), { spalten: 2 }); assert.deepEqual(raster(500), { spalten: 1 });
});

test("aktualisiere setzt Lage, Radius und Dimmung auf vorhandene Knoten, ohne sie zu ersetzen", () => {
  const knoten = (id, gruppe) => ({ dataset: { id, gruppe }, style: {}, attrs: {}, klassen: new Set(["einheit", "p"]),
    setAttribute(k, v) { this.attrs[k] = v; }, classList: { toggle(c, an) { an ? this.owner.klassen.add(c) : this.owner.klassen.delete(c); } } });
  const ks = [knoten("0_0|belegschaft", "belegschaft"), knoten("1_0|belegschaft", "belegschaft"), knoten("0_0|aufsicht", "aufsicht")];
  ks.forEach((k) => { k.classList.owner = k; });
  const karten = [{ dataset: { g: "belegschaft" }, style: {} }, { dataset: { g: "aufsicht" }, style: {} }];
  const titel = [{ dataset: { g: "belegschaft" }, style: {}, setAttribute(k, v) { this[k] = v; } }];
  const svgEl = { querySelectorAll: (sel) => sel === "circle.p" ? ks : sel === "g.karte" ? karten : titel };
  const r = aktualisiere(svgEl, A({ zustand: "karten", hervor: ["Belegschaft"] }), DATEN, O);
  assert.match(ks[0].style.transform, /^translate\([\d.]+px, ?[\d.]+px\)$/);
  assert.ok(Number(ks[0].attrs.r) >= 1.6); assert.ok(ks[2].klassen.has("gedimmt")); assert.ok(!ks[0].klassen.has("gedimmt"));
  assert.equal(karten[0].style.opacity, 1);
  assert.equal(r.zahlen.N, 6); assert.ok(Array.isArray(r.legende));
});

test("Zechensymbol der Punktkarte ist der Pfad aus bilder/zeche.svg", () => {
  const d = readFileSync(new URL("../bilder/zeche.svg", import.meta.url), "utf8").match(/ d="([^"]+)"/)[1];
  const js = readFileSync(new URL("../js/formen/punktkarte.js", import.meta.url), "utf8");
  assert.ok(js.includes(`const ZECHE_PFAD = "${d}"`));
});
