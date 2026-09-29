import test from "node:test";
import assert from "node:assert/strict";
import { Lader } from "../js/daten.js";

const DATEIEN = { "daten/adressen/a1.json": { a1b2c3d4e5f6: { id: "a1b2c3d4e5f6", stufe: "haus", lat: 51.49, lon: 7.06 } } };
const fakeFetch = async (u) => ({ ok: u in DATEIEN, status: u in DATEIEN ? 200 : 404, json: async () => DATEIEN[u] });

test("Lader.adresse liest die Adressscherbe und liefert die passende Adresse", async () => {
  const l = new Lader("daten/", fakeFetch);
  const a = await l.adresse("a1b2c3d4e5f6");
  assert.deepEqual(a, { id: "a1b2c3d4e5f6", stufe: "haus", lat: 51.49, lon: 7.06 });
});

test("Lader.adresse liefert null, wenn die ID in der (vorhandenen) Scherbe fehlt", async () => {
  const l = new Lader("daten/", fakeFetch);
  const a = await l.adresse("a1ffffffffff");
  assert.equal(a, null);
});

test("Lader.adresse liefert null bei 404 (Scherbe existiert nicht)", async () => {
  const l = new Lader("daten/", fakeFetch);
  const a = await l.adresse("zzffffffffff");
  assert.equal(a, null);
});

test("Lader.ebene lädt ebenen/<name>.json", async () => {
  const DATEIEN2 = { "daten/ebenen/strassen.json": [{ id: "00001", name: "Aachener Straße" }] };
  const fetchFake2 = async (u) => ({ ok: u in DATEIEN2, status: u in DATEIEN2 ? 200 : 404, json: async () => DATEIEN2[u] });
  const l = new Lader("daten/", fetchFake2);
  const s = await l.ebene("strassen");
  assert.deepEqual(s, [{ id: "00001", name: "Aachener Straße" }]);
});

test("Lader.adressenKurz lädt nur die betroffenen Dateien, einmal, und baut Objekte aus den sieben Werten", async () => {
  const DATEIEN3 = {
    "daten/adressen_kurz/a.json": { a1: [7.06, 51.49, "haus", "Katernberg", "Lattenkamp", "25", "Grenzstr. 25, Katernberg"], a2: [7.07, 51.5, "strasse", "Kray", "", "", "Kampstr. 3"] },
    "daten/adressen_kurz/b.json": { b1: [7.0, 51.4, "stadtplan", "", "", "3", "Alte Str. 3"] },
  };
  const geladen = [];
  const l = new Lader("daten/", async (u) => { geladen.push(u); return { ok: u in DATEIEN3, status: u in DATEIEN3 ? 200 : 404, json: async () => DATEIEN3[u] }; });
  const m = await l.adressenKurz(["a1", "b1", "a2", "zz"]);
  assert.deepEqual(m.get("a1"), { id: "a1", lon: 7.06, lat: 51.49, stufe: "haus", stadtteil: "Katernberg", strasse_heute: "Lattenkamp", hausnr: "25", historisch: "Grenzstr. 25, Katernberg" });
  assert.equal(m.get("b1").stufe, "stadtplan");
  assert.equal(m.has("zz"), false);                       // Datei fehlt (404) → keine Ausnahme, kein Eintrag
  assert.deepEqual(geladen.sort(), ["daten/adressen_kurz/a.json", "daten/adressen_kurz/b.json", "daten/adressen_kurz/z.json"]);
  await l.adressenKurz(["a2"]);
  assert.equal(geladen.length, 3);                        // zweiter Aufruf lädt nichts nach
});

test("Lader.adressenKurz mit leerer Liste liefert eine leere Map ohne Ladevorgang", async () => {
  let n = 0;
  const l = new Lader("daten/", async () => { n++; return { ok: false, status: 404 }; });
  assert.equal((await l.adressenKurz([])).size, 0);
  assert.equal(n, 0);
});

test("themaListe lädt themen/<id>_liste.json, null wenn es sie nicht gibt", async () => {
  const l = new Lader("daten/", async (u) => ({ ok: u === "daten/themen/besitz_liste.json", status: u === "daten/themen/besitz_liste.json" ? 200 : 404, json: async () => ({ oberkategorien: [] }) }));
  assert.deepEqual(await l.themaListe("besitz"), { oberkategorien: [] });
  assert.equal(await l.themaListe("bergbau"), null);
});

test("Lader hängt die Versionsmarke an jede Daten-URL, im Entwicklungsmodus nicht", async () => {
  const { Lader } = await import("../js/daten.js");
  const urls = [];
  const fetchFn = (u) => { urls.push(u); return Promise.resolve({ ok: true, json: () => Promise.resolve({}) }); };
  await new Lader("daten/", fetchFn, "abc1234").json("kennzahlen.json");
  await new Lader("daten/", fetchFn, "dev").json("kennzahlen.json");
  assert.deepEqual(urls, ["daten/kennzahlen.json?v=abc1234", "daten/kennzahlen.json"]);
});
