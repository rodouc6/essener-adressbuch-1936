import test from "node:test";
import assert from "node:assert/strict";
import { zechePopupHtml } from "../js/karte.js";

test("zechePopupHtml: Artikeljahre, abweichende Liste, Planbeschriftung, nur Wikipedia-Link", () => {
  const h = zechePopupHtml({ name: "Zollverein", stadtteil: "Katernberg", betrieb_von: "1851", betrieb_bis: "1986",
    liste_von: "1847", liste_bis: "1986", jahre_widerspruch: true, jahre_unbekannt: false,
    plan_1935: "Zeche Zollverein", quelle: "https://de.wikipedia.org/wiki/Zeche_Zollverein" });
  assert.match(h, /in Betrieb 1851–1986/);
  assert.match(h, /Wikipedia-Liste abweichend: 1847–1986/);
  assert.match(h, /Stadtplan 1935: „Zeche Zollverein“/);
  assert.match(h, /href="https:\/\/de\.wikipedia\.org\/wiki\/Zeche_Zollverein"/);
});

test("zechePopupHtml: unbekannte Jahre, fremde Quelle nicht verlinkt", () => {
  const h = zechePopupHtml({ name: "X", jahre_unbekannt: true, quelle: "https://example.org/x" });
  assert.match(h, /Betriebsjahre unbekannt/);
  assert.doesNotMatch(h, /href=/);
  assert.doesNotMatch(h, /abweichend|Stadtplan/);
});
