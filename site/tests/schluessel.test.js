import test from "node:test";
import assert from "node:assert/strict";
import { falte, praefix2 } from "../js/schluessel.js";

test("falte spiegelt die Python-Funktion", () => {
  assert.equal(falte("Grenzstraße"), "grenzstrasse");
  assert.equal(falte("Müller-Lüdenscheidt, Ä."), "mueller luedenscheidt ae");
  assert.equal(falte("  St.  Ännchen "), "st aennchen");
  assert.equal(falte(""), "");
});

test("praefix2", () => {
  assert.equal(praefix2("Sepeur"), "se");
  assert.equal(praefix2("Ö"), "oe");
  assert.equal(praefix2("M. Jäger"), "mj");
  assert.equal(praefix2(""), "_");
});
