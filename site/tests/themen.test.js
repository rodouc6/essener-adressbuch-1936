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

test("themenListe nur freigegebene", async () => {
  assert.deepEqual(await themenListe(new Lader("daten/", fetchFake)), [{ id: "akademiker", titel: "Akademiker" }]);
});

test("farbregel kategorien → match-Ausdruck", () => {
  const r = farbregel({ filter: {}, farbe: { art: "kategorien", feld: "besitz", werte: { industrie: "#b91c1c", stadt_staat: "#1d4ed8" }, sonst: "#ccc" } });
  assert.equal(r.merkmal, null);
  assert.deepEqual(r.ausdruck, ["match", ["get", "besitz"], "industrie", "#b91c1c", "stadt_staat", "#1d4ed8", "#ccc"]);
  assert.deepEqual(r.kategorien, { industrie: "#b91c1c", stadt_staat: "#1d4ed8" });
});
