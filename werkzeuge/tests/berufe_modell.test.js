import test from "node:test";
import assert from "node:assert/strict";
import { baueModell, fortschritt, katalogVorschlag, liste, rueckgaengig, schalteStatus, setzeBeruf, setzeGeprueft,
         setzeNiveauUnsicher, setzeZuordnung, sucheOhdab, uebernehmeKandidat, zumSpeichern } from "../js/berufe_modell.js";

const O = [
  { ohdab_id: "B 21112-100", norm: "Bergmann/-frau", maennlich: "Bergmann", weiblich: "Bergfrau", niveau: "fachlich", gattung_id: "B 21112", gattung: "Berufe im Berg- und Tagebau" },
  { ohdab_id: "B 20001-503", norm: "Arbeiter/in - ungelernte/r", maennlich: "ungelernter Arbeiter", weiblich: "ungelernte Arbeiterin", niveau: "helfer", gattung_id: "B 20001", gattung: "Produktion – Helfer" },
  { ohdab_id: "B 20002-500", norm: "Arbeiter/in - allgemein", maennlich: "Arbeiter", weiblich: "Arbeiterin", niveau: "fachlich", gattung_id: "B 20002", gattung: "Produktion – fachlich" },
];
const K = [
  { schreibweise: "Bergm.", nennungen: "9", beruf: "Bergmann", status: "", ohdab_id: "B 21112-100", niveau_unsicher: "", geprueft: "", vorschlag_grund: "katalog; exakt", bearbeiter: "berufe_vorschlag", datum: "", hinweis: "" },
  { schreibweise: "Arbeiter", nennungen: "20", beruf: "Arbeiter", status: "", ohdab_id: "B 20002-500", niveau_unsicher: "", geprueft: "", vorschlag_grund: "exakt", bearbeiter: "berufe_vorschlag", datum: "", hinweis: "" },
  { schreibweise: "Fabrkarb.", nennungen: "5", beruf: "Fabrkarb.", status: "", ohdab_id: "", niveau_unsicher: "", geprueft: "", vorschlag_grund: "", bearbeiter: "berufe_vorschlag", datum: "", hinweis: "" },
];
const KAND = { "Arbeiter": [["B 20002-500", "exakt", 1], ["B 20001-503", "exakt", 1]], "Bergm.": [["B 21112-100", "exakt", 1]] };
const frisch = () => baueModell(K, O, KAND);

test("Modell, Liste, Kandidaten mit Niveau-Entscheidung", () => {
  const m = frisch();
  assert.deepEqual(liste(m).map((z) => [z.schreibweise, z.nennungen]), [["Arbeiter", 20], ["Bergm.", 9], ["Fabrkarb.", 5]]);
  const a = m.zeilen.get("Arbeiter");
  assert.equal(a.niveauEntscheiden, true);
  assert.deepEqual(a.kandidaten.map((k) => [k.ohdab_id, k.niveau]), [["B 20002-500", "fachlich"], ["B 20001-503", "helfer"]]);
  assert.equal(m.zeilen.get("Bergm.").niveauEntscheiden, false);
  assert.deepEqual(fortschritt(m), { geprueft: 0, gesamt: 3, nennungenGeprueft: 0, nennungenGesamt: 34 });
});

test("sucheOhdab: Präfix vor Teilstring, Umlaute gefaltet", () => {
  const m = frisch();
  assert.deepEqual(sucheOhdab(m, "bergm").map((i) => i.ohdab_id), ["B 21112-100"]);
  assert.deepEqual(sucheOhdab(m, "arbeiter").map((i) => i.ohdab_id), ["B 20002-500", "B 20001-503"]);   // „Arbeiter“ exakt vor „ungelernter Arbeiter“
  assert.deepEqual(sucheOhdab(m, ""), []);
});

test("geprüft nur mit Zuordnung; Zuordnung setzt Beruf aus der Form", () => {
  const m = frisch();
  assert.deepEqual(setzeGeprueft(m, "Fabrkarb.", true), []);
  const g = setzeZuordnung(m, "Fabrkarb.", "B 21112-100");
  assert.equal(g.length, 1); assert.equal(g[0].ohdab_id, "B 21112-100"); assert.equal(g[0].beruf, "Bergmann");
  assert.equal(setzeGeprueft(m, "Fabrkarb.", true)[0].geprueft, "ja");
  assert.deepEqual(zumSpeichern(g[0]), { schreibweise: "Fabrkarb.", beruf: "Bergmann", status: "", ohdab_id: "B 21112-100", niveau_unsicher: "", geprueft: "ja", hinweis: "" });
});

test("Kandidat übernehmen, Status durchschalten, Niveau unsicher, Undo", () => {
  const m = frisch();
  assert.equal(uebernehmeKandidat(m, "Arbeiter", "B 20001-503")[0].ohdab_id, "B 20001-503");
  assert.equal(schalteStatus(m, "Arbeiter")[0].status, "ruhestand");
  assert.equal(schalteStatus(m, "Arbeiter")[0].status, "invalide");
  assert.equal(schalteStatus(m, "Arbeiter")[0].status, "witwe");
  assert.equal(schalteStatus(m, "Arbeiter")[0].status, "");
  assert.equal(setzeNiveauUnsicher(m, "Arbeiter", true)[0].niveau_unsicher, "ja");
  assert.deepEqual(setzeNiveauUnsicher(m, "Arbeiter", true), []);
  const z = rueckgaengig(m);
  assert.equal(z[0].niveau_unsicher, "");
  assert.equal(m.zeilen.get("Arbeiter").status, "");
});

test("Zuordnung ändern entprüft; Katalogvorschlag nur bei Punktwort und Abweichung", () => {
  const m = frisch();
  setzeZuordnung(m, "Bergm.", "B 21112-100"); setzeGeprueft(m, "Bergm.", true);
  assert.equal(setzeZuordnung(m, "Bergm.", "B 20002-500")[0].geprueft, "");
  assert.equal(katalogVorschlag(m, "Bergm."), null);                       // beruf unverändert gegenüber Automatik
  setzeBeruf(m, "Fabrkarb.", "Fabrikarbeiter");
  assert.deepEqual(katalogVorschlag(m, "Fabrkarb."), { kurz: "Fabrkarb.", lang: "Fabrikarbeiter", status: "" });
  setzeBeruf(m, "Arbeiter", "Hilfsarbeiter");
  assert.equal(katalogVorschlag(m, "Arbeiter"), null);                     // kein Punktwort
});
