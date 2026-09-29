import test from "node:test";
import assert from "node:assert/strict";
import { anzeigeFuer, KATEGORIEN, NIVEAUS } from "../js/kategorien.js";

test("anzeigeFuer: Beschriftung je Farbfeld — gemischt heißt bei Besitz und Niveau verschieden", () => {
  assert.equal(anzeigeFuer("besitz"), KATEGORIEN);
  assert.equal(anzeigeFuer("niveau"), NIVEAUS);
  assert.equal(anzeigeFuer("besitz").gemischt, "mehrere Kategorien");
  assert.equal(anzeigeFuer("niveau").gemischt, "mehrere Niveaus");
  assert.deepEqual(anzeigeFuer("bergbau"), {});
});

import { STELLUNGEN } from "../js/kategorien.js";
test("STELLUNGEN: neun Klassen plus gemischt/ungeprüft, anzeigeFuer('stellung')", () => {
  assert.equal(STELLUNGEN.kaufleute, "Kaufleute (Stellung unbestimmt)");
  assert.equal(STELLUNGEN.gemischt, "mehrere Stellungen"); assert.equal(STELLUNGEN.ungeprueft, "ungeprüft");
  assert.equal(anzeigeFuer("stellung"), STELLUNGEN);
});
