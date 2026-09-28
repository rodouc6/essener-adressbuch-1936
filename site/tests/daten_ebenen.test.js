import test from "node:test";
import assert from "node:assert/strict";
import { Lader } from "../js/daten.js";
import { normalisiere } from "../js/ansicht.js";
import { einheiten, filterEinheiten, ladeEbenen, werteJeEinheit, zusammenfassung } from "../js/daten_ebenen.js";

const D = {
  "daten/ebenen/stadtteile.json": [{ id: "Katernberg", lat: 51.5, lon: 7.05, adressen: 40, n_I: 100, n_st_arbeiter: 70, n_st_beamte: 5, n_st_unbestimmt: 25, rang_nord: 1 },
                                   { id: "Südviertel", lat: 51.44, lon: 7.01, adressen: 30, n_I: 60, n_st_arbeiter: 10, n_st_beamte: 20, n_st_unbestimmt: 30, rang_nord: 2 }],
  "daten/ebenen/strassen.json": [{ id: "00001", name: "Aachener Straße", stadtteil: "Frohnhausen", adressen: 5, n_I: 20, n_st_arbeiter: 12, n_st_beamte: 2 }],
  "daten/hauptgruppen.json": { B21: { kurz: "Bergbau" } }, "daten/kennzahlen.json": { adressen: 70316 },
};
const fetchFake = async (u) => ({ ok: u in D, status: u in D ? 200 : 404, json: async () => D[u] });
const G = [{ name: "Arbeiter", aus: ["arbeiter"], farbe: "#e69f00" }, { name: "Beamte", aus: ["beamte"], farbe: "#009e73" }];

test("ladeEbenen lädt einmal und toleriert fehlende Dateien", async () => {
  const l = new Lader("daten/", fetchFake);
  const e = await ladeEbenen(l);
  assert.equal(e.stadtteile.length, 2); assert.equal(e.strassen.length, 1); assert.deepEqual(e.hex, []); assert.equal(e.polygone, null);
  assert.deepEqual(e.layout.berufe, null); assert.equal(e.kennzahlen.adressen, 70316);
});

test("werteJeEinheit rechnet je Einheit und markiert unter min_n", async () => {
  const e = await ladeEbenen(new Lader("daten/", fetchFake));
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", gruppen: G, bezug: "Arbeiter", min_n: 50 });
  const w = werteJeEinheit(a, e);
  assert.deepEqual(w.map((x) => [x.id, x.N, x.n_aus, x.unter_min, Math.round(x.wert * 100)]), [["Katernberg", 75, 25, false, 93], ["Südviertel", 30, 30, true, 33]]);
  assert.equal(w[0].name, "Katernberg"); assert.equal(w[0].rang_nord, 1);
  const s = werteJeEinheit(normalisiere({ ...a, ebene: "strasse", min_n: 10 }), e);
  assert.equal(s[0].name, "Aachener Straße"); assert.equal(s[0].N, 14);
  assert.deepEqual(einheiten(e, normalisiere({ ebene: "adresse" })), []);
  assert.deepEqual(zusammenfassung(w), { N: 105, n_aus: 55, unter_min: 1, einheiten: 2 });
});

test("filterEinheiten nach Stadtteil und top", async () => {
  const e = await ladeEbenen(new Lader("daten/", fetchFake));
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", gruppen: G, bezug: "Beamte", min_n: 0 });
  const w = werteJeEinheit(a, e);
  assert.deepEqual(filterEinheiten(w, { stadtteil: ["Südviertel"] }).map((x) => x.id), ["Südviertel"]);
  assert.deepEqual(filterEinheiten(w, { top: 1 }).map((x) => x.id), ["Südviertel"]);
  const s = werteJeEinheit(normalisiere({ ...a, ebene: "strasse" }), e);
  assert.deepEqual(filterEinheiten(s, { stadtteil: ["Frohnhausen"] }).length, 1);
  assert.deepEqual(filterEinheiten(s, { stadtteil: ["Steele"] }).length, 0);
});

test("ladeEbenen liefert Kapitelpunkte und Zechen, fehlend → null", async () => {
  const D2 = { ...D, "daten/perspektiven/bergbau_punkte.json": { gruppen: [], hex: {}, haeuser: [], gesellschaften: [], maxn: 0 } };
  const f = async (u) => ({ ok: u in D2, status: u in D2 ? 200 : 404, json: async () => D2[u] });
  const d = await ladeEbenen(new Lader("daten/", f));
  assert.deepEqual(d.punkte.gruppen, []); assert.equal(d.zechen, null);
});
