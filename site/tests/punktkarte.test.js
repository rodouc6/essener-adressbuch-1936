import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { normalisiere, standardGruppen } from "../js/ansicht.js";
import { aktualisiere, berechne, raster, uebergang, zeige, zwischen } from "../js/formen/punktkarte.js";

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
  assert.equal(r.legende.find((l) => l.name === "Belegschaft").text, "5");        // Name steht schon im Eintrag, kein Doppel
  assert.equal(r.legende.find((l) => l.name === "Kreisfläche").text, "eingetragene Personen je Hexfeld (120 m Kante), größter Wert 4");
  assert.ok(r.legende.every((l) => !["mass", "zechen", "ring"].includes(l.name)));     // keine technischen Namen in der Legende
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
  assert.equal(r.zahlen.N, 2); assert.equal(r.legende.find((l) => l.name === "Ring").text, "nur straßengenau oder Stadtplan 1935 (1)");
  assert.equal(r.legende.find((l) => l.name === "übrige Bergbau-Eigentümer").farbe, "#c8c8c8");
  assert.equal(r.legende.find((l) => l.name === "Stinnes").text, "1");
});

test("gesammelt: Packungstitel überlappen nicht (Mindestabstand der Mitten ≥ 150 px bei 1000 px Breite)", () => {
  const b = berechne(A({ zustand: "gesammelt" }), DATEN, O);
  const xs = b.titel.map((t) => t.x).sort((p, q) => p - q);
  for (let i = 1; i < xs.length; i++) assert.ok(xs[i] - xs[i - 1] >= 150 - 0.01, `Abstand ${xs[i] - xs[i - 1]}`);
});

test("gesammelt: auf schmaler Bühne passen alle Packungen samt Titel in die Breite", () => {
  const groß = { ...PUNKTE, hex: { ...PUNKTE.hex, belegschaft: Array.from({ length: 60 }, (_, i) => ({ id: `${i}_0`, lon: 7.01, lat: 51.45, n: 4, r: 9, x: (i % 8) * 19, y: Math.floor(i / 8) * 19 })) } };
  for (const breite of [420, 600]) {
    const b = berechne(A({ zustand: "gesammelt" }), { ...DATEN, punkte: groß }, { breite, hoehe: 500 });
    assert.ok(b.kreise.every((k) => k.x - k.r >= 0 && k.x + k.r <= breite), `Kreis außerhalb bei ${breite}`);
    assert.ok(b.titel.every((t) => t.x >= 80 && t.x <= breite - 80), `Titel außerhalb bei ${breite}`);
  }
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

test("Legende nennt den Mindestradius: bis zu welcher Personenzahl Felder gleich groß erscheinen", () => {
  const gross = { ...PUNKTE, maxn: 210, hex: { ...PUNKTE.hex, belegschaft: [{ id: "0_0", lon: 7.01, lat: 51.45, n: 210, r: 9, x: 0, y: 0 }, { id: "1_0", lon: 7.02, lat: 51.46, n: 3, r: 1.2, x: 14, y: 0 }, { id: "2_0", lon: 7.03, lat: 51.46, n: 1, r: 1.2, x: 28, y: 0 }, { id: "3_0", lon: 7.04, lat: 51.46, n: 20, r: 2.777, x: 42, y: 0 }] } };
  const k = berechne(A({ zustand: "karten" }), { ...DATEN, punkte: gross }, O);
  const boden = k.legende.find((l) => l.name === "Mindestgröße");
  assert.ok(boden, "Legendenzeile fehlt");
  assert.equal(boden.text, "Felder bis 3 Personen erscheinen gleich groß");   // r für n=3 und n=1 liegt am Boden, n=20 darüber
  const g = berechne(A({ zustand: "gesammelt" }), { ...DATEN, punkte: gross }, O);
  assert.equal(g.legende.find((l) => l.name === "Mindestgröße").text, "Felder bis 3 Personen erscheinen gleich groß");
  const ohne = berechne(A({ zustand: "karten" }), DATEN, { breite: 3000, hoehe: 2000 });   // alle Radien über dem Boden
  assert.equal(ohne.legende.find((l) => l.name === "Mindestgröße"), undefined);
});

test("gesammelt unter 760 px: Packungen 2×2, Titel überlappen nicht, alles im Bild", () => {
  assert.equal(new Set(berechne(A({ zustand: "gesammelt" }), DATEN, { breite: 700, hoehe: 600 }).titel.map((t) => Math.round(t.y))).size, 2, "bei 700 px zwei Zeilen");
  const reihe = berechne(A({ zustand: "gesammelt" }), DATEN, { breite: 800, hoehe: 600 }).titel.map((t) => t.y);
  assert.ok(Math.max(...reihe) - Math.min(...reihe) < 40, "ab 760 px eine Reihe (Titel hängen je unter ihrer Packung)");
  const b = berechne(A({ zustand: "gesammelt" }), DATEN, { breite: 360, hoehe: 520 });
  const ys = new Set(b.titel.map((t) => Math.round(t.y)));
  assert.equal(ys.size, 2, "zwei Zeilen erwartet");
  for (const t of b.titel) { const nachbarn = b.titel.filter((u) => u !== t && Math.round(u.y) === Math.round(t.y)); for (const u of nachbarn) assert.ok(Math.abs(u.x - t.x) >= 150, `Titelabstand ${Math.abs(u.x - t.x)}`); }
  assert.ok(b.kreise.every((k) => k.x - k.r >= 0 && k.x + k.r <= 360 && k.y - k.r >= 0 && k.y + k.r <= 520));
  assert.ok(b.titel.every((t) => t.y + 16 <= 520));
});

// Übergang auf Canvas: die CSS-Transition auf 3.000 SVG-Kreisen lief mit 2–4 fps (Messung 2026-09-29).
test("zwischen interpoliert Lage, Radius und Deckkraft je Kreis-ID, unabhängig von der Reihenfolge", () => {
  const von = [{ id: "a", x: 0, y: 0, r: 2, farbe: "#111", gedimmt: false }, { id: "b", x: 10, y: 10, r: 4, farbe: "#222", gedimmt: false }];
  const nach = [{ id: "b", x: 20, y: 30, r: 8, farbe: "#222", gedimmt: true }, { id: "a", x: 100, y: 0, r: 2, farbe: "#111", gedimmt: false }];
  const z = zwischen(von, nach, 0.5);
  assert.deepEqual(z.map((k) => k.id), ["b", "a"]);                          // Reihenfolge des Ziels
  assert.deepEqual(z[1], { id: "a", x: 50, y: 0, r: 2, farbe: "#111", alpha: 1 });
  assert.equal(z[0].x, 15); assert.equal(z[0].y, 20); assert.equal(z[0].r, 6);
  assert.ok(Math.abs(z[0].alpha - (1 + 0.12) / 2) < 1e-9);                  // gedimmt = Deckkraft .12 (CSS .gedimmt)
  assert.deepEqual(zwischen(von, nach, 1)[0], { id: "b", x: 20, y: 30, r: 8, farbe: "#222", alpha: 0.12 });
  assert.equal(zwischen([], nach, 0)[0].x, 20);                              // ohne Vorgänger: Ziel steht fest
});

test("uebergang zeichnet je Bild alle Kreise mit Easing, meldet das Ende einmal und lässt sich abbrechen", () => {
  const aufrufe = []; const ctx = { clearRect: (...a) => aufrufe.push(["clear", ...a]), beginPath() {}, moveTo() {}, arc: (x, y, r) => aufrufe.push(["arc", x, y, r]), fill() {}, save() {}, restore() {}, setTransform() {}, set fillStyle(v) { aufrufe.push(["farbe", v]); }, set globalAlpha(v) { aufrufe.push(["alpha", v]); } };
  const canvas = { width: 200, height: 100, getContext: () => ctx };
  const von = [{ id: "a", x: 0, y: 0, r: 2, farbe: "#111", gedimmt: false }];
  const nach = [{ id: "a", x: 100, y: 0, r: 2, farbe: "#111", gedimmt: false }];
  let t = 0; const warteschlange = []; const raf = (f) => warteschlange.push(f); let fertig = 0;
  const u = uebergang({ canvas, von, nach, breite: 100, hoehe: 50, dauer: 1000, jetzt: () => t, raf, fertig: () => fertig++ });
  assert.equal(warteschlange.length, 1);
  t = 500; warteschlange.shift()();                                           // Bild bei t = 0,5 → Easing (ein-aus) liegt bei 0,5
  const arcs = aufrufe.filter((a) => a[0] === "arc");
  assert.equal(arcs.length, 1); assert.ok(Math.abs(arcs[0][1] - 50) < 1e-9);
  assert.equal(u.aktuell()[0].x, arcs[0][1]);                                 // aktuell liefert den gezeichneten Stand
  assert.equal(fertig, 0);
  t = 1000; warteschlange.shift()();
  assert.equal(fertig, 1); assert.equal(warteschlange.length, 0);            // Ende: kein weiteres Bild
  assert.equal(aufrufe.filter((a) => a[0] === "arc").pop()[1], 100);
  const u2 = uebergang({ canvas, von, nach, breite: 100, hoehe: 50, dauer: 1000, jetzt: () => t, raf, fertig: () => fertig++ });
  u2.abbrechen(); t = 1500; warteschlange.shift()();
  assert.equal(fertig, 1);                                                    // nach Abbruch kein fertig und kein Bild
  assert.equal(aufrufe.filter((a) => a[0] === "arc").length, 2);
});

test("uebergang skaliert Zeichenflächen-Einheiten auf die Pixel des Canvas", () => {
  const aufrufe = []; const ctx = { clearRect() {}, beginPath() {}, moveTo() {}, arc() {}, fill() {}, save() {}, restore() {}, setTransform: (...a) => aufrufe.push(a), set fillStyle(v) {}, set globalAlpha(v) {} };
  const canvas = { width: 400, height: 200, getContext: () => ctx };
  const k = [{ id: "a", x: 0, y: 0, r: 2, farbe: "#111", gedimmt: false }];
  const q = []; uebergang({ canvas, von: k, nach: k, breite: 100, hoehe: 50, dauer: 1, jetzt: () => 0, raf: (f) => q.push(f), fertig() {} });
  q[0]();
  assert.deepEqual(aufrufe[0], [4, 0, 0, 4, 0, 0]);                          // 400 px / 100 Einheiten
});

test("zeige und aktualisiere liefern die Kreise und die Zeichenfläche für den Übergang", () => {
  const r = zeige(A({ zustand: "gesammelt" }), DATEN, O);
  assert.equal(r.kreise.length, 3); assert.equal(r.breite, 1000); assert.equal(r.hoehe, 700);
  const svgEl = { querySelectorAll: () => [] };
  const a = aktualisiere(svgEl, A({ zustand: "karten" }), DATEN, O);
  assert.equal(a.kreise.length, 3); assert.ok(a.kreise.every((k) => "gedimmt" in k)); assert.equal(a.breite, 1000);
});

test("zwischen nimmt einen Zwischenstand (mit alpha) als Ausgangspunkt, damit ein unterbrochener Übergang weiterläuft", () => {
  const nach = [{ id: "a", x: 100, y: 0, r: 2, farbe: "#111", gedimmt: false }];
  const stand = [{ id: "a", x: 30, y: 0, r: 2, farbe: "#111", alpha: 0.5 }];
  const z = zwischen(stand, nach, 0);
  assert.equal(z[0].x, 30); assert.equal(z[0].alpha, 0.5);
});
