import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readdirSync } from "node:fs";
import { join } from "node:path";

// Module ohne eigenen Test (sidebar.js, app.js, karte.js …) laufen sonst nur im Browser — ein Tippfehler
// dort bleibt in der Suite unsichtbar und legt die ganze Karte still.
const ordner = new URL("../js/", import.meta.url).pathname;
const dateien = (d) => readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? dateien(join(d, e.name)) : e.name.endsWith(".js") ? [join(d, e.name)] : []));

test("alle Module in site/js sind syntaktisch gültig", () => {
  const module = dateien(ordner);
  assert.ok(module.length > 20);
  for (const m of module) assert.doesNotThrow(() => execFileSync(process.execPath, ["--check", m], { stdio: "pipe" }), m);
});
