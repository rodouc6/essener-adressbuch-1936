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
