import test from "node:test";
import assert from "node:assert/strict";
import { normalisiere } from "../js/ansicht.js";
import { detailText, formFuer, fuellePlatzhalter, linkKarte, sichtbareKapitel } from "../js/perspektiven_modell.js";

test("sichtbareKapitel nur freigegebene, mit vorschau alle", () => {
  const i = [{ id: "a", freigegeben: true }, { id: "b", freigegeben: false }];
  assert.deepEqual(sichtbareKapitel(i, false).map((k) => k.id), ["a"]);
  assert.deepEqual(sichtbareKapitel(i, true).map((k) => k.id), ["a", "b"]);
});

test("fuellePlatzhalter aus kennzahlen", () => {
  const kz = { adressen: 70316, besitz_geprueft: 7546, stellung_geprueft: 73.0, stand: "2026-09-25" };
  assert.equal(fuellePlatzhalter("{adressen} Adressen, {besitz_geprueft} geprüft ({besitz_geprueft_prozent} %), Stand {stand}, {nix}", kz), "70.316 Adressen, 7.546 geprüft (10,7 %), Stand 2026-09-25, {nix}");
  assert.equal(fuellePlatzhalter("{stellung_geprueft} %", kz), "73 %");
  // stellung_geprueft ist bereits ein Prozentwert — {…_prozent} darf dafür nichts ausrechnen.
  assert.equal(fuellePlatzhalter("{stellung_geprueft_prozent}", kz), "{stellung_geprueft_prozent}");
});

test("linkKarte kodiert die Ansicht, formFuer bildet ab", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", form: "karte" });
  assert.match(linkKarte(a), /^karte\.html\?ansicht=[A-Za-z0-9_-]+$/);
  assert.equal(formFuer(a), "stadtteilkarte");
  assert.equal(formFuer(normalisiere({ form: "multiples" })), "balken");
  assert.equal(formFuer(normalisiere({ form: "bubbles" })), "bubbles");
});

test("detailText", () => {
  const a = normalisiere({ daten: "stellung", gruppen: [{ name: "Arbeiter", aus: ["arbeiter"] }], bezug: "Arbeiter", min_n: 50 });
  const d = detailText({ id: "Katernberg", name: "Katernberg", N: 30, n_aus: 5, unter_min: true, anteile: { Arbeiter: 1 }, zaehler: { Arbeiter: 30 } }, a);
  assert.equal(d.titel, "Katernberg");
  assert.deepEqual(d.zeilen, ["30 Nennungen einbezogen, 5 ausgeschlossen", "Arbeiter 100 % (30)", "unter 50 Nennungen — Anteil nicht belastbar"]);
});
