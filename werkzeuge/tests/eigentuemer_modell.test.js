import test from "node:test";
import assert from "node:assert/strict";
import { abspalten, baueModell, benenne, eigentuemerListe, fortschritt, rueckgaengig, setzeGeprueft, setzeIdentitaet,
         setzeHinweis, setzeKategorie, uebernehmeVorschlag, zumSpeichern, zusammenfuehren } from "../js/eigentuemer_modell.js";

const V = [
  { schreibweise: "Fried. Krupp A.G.", art: "koerperschaft", anzahl: "6", cluster_id: "k1", cluster_name: "Fried. Krupp AG", aehnlichkeit: "1.0", vorschlag_fuer: "", pruefpflichtig: "ja" },
  { schreibweise: "Fried. Krupp AG.", art: "koerperschaft", anzahl: "1", cluster_id: "k1", cluster_name: "Fried. Krupp AG", aehnlichkeit: "1.0", vorschlag_fuer: "", pruefpflichtig: "ja" },
  { schreibweise: "Krupp Stiftung", art: "koerperschaft", anzahl: "2", cluster_id: "k2", cluster_name: "Krupp Stiftung", aehnlichkeit: "1.0", vorschlag_fuer: "k1", pruefpflichtig: "nein" },
  { schreibweise: "Stadt Essen", art: "koerperschaft", anzahl: "9", cluster_id: "s1", cluster_name: "Stadt Essen", aehnlichkeit: "1.0", vorschlag_fuer: "", pruefpflichtig: "ja" },
];
const K = [
  { schreibweise: "Fried. Krupp A.G.", art: "koerperschaft", eigentuemer: "Fried. Krupp AG", kategorie: "", geprueft: "", bearbeiter: "eigentuemer_cluster", datum: "", hinweis: "" },
  { schreibweise: "Fried. Krupp AG.", art: "koerperschaft", eigentuemer: "Fried. Krupp AG", kategorie: "", geprueft: "", bearbeiter: "eigentuemer_cluster", datum: "", hinweis: "" },
  { schreibweise: "Krupp Stiftung", art: "koerperschaft", eigentuemer: "Krupp Stiftung", kategorie: "", geprueft: "", bearbeiter: "eigentuemer_cluster", datum: "", hinweis: "" },
  { schreibweise: "Stadt Essen", art: "koerperschaft", eigentuemer: "Stadt Essen", kategorie: "stadt_staat", geprueft: "ja", bearbeiter: "christos", datum: "2026-09-22", hinweis: "" },
  { schreibweise: "Alt GmbH", art: "koerperschaft", eigentuemer: "Alt GmbH", kategorie: "", geprueft: "", bearbeiter: "eigentuemer_cluster", datum: "", hinweis: "" },
];
const frisch = () => baueModell(V, K);

test("baueModell und Liste", () => {
  const m = frisch();
  const l = eigentuemerListe(m);
  assert.deepEqual(l.map((e) => [e.name, e.haeuser, e.geprueft, e.pruefpflichtig]),
    [["Stadt Essen", 9, true, true], ["Fried. Krupp AG", 7, false, true], ["Krupp Stiftung", 2, false, false], ["Alt GmbH", 0, false, false]]);
  assert.equal(m.zeilen.get("Alt GmbH").verwaist, true);
  const krupp = l[1];
  assert.deepEqual(krupp.schreibweisen.map((z) => z.schreibweise), ["Fried. Krupp A.G.", "Fried. Krupp AG."]);
  assert.deepEqual(krupp.vorschlaege.map((v) => [v.zeile.schreibweise, v.aehnlichkeit]), [["Krupp Stiftung", 1.0]]);
  assert.deepEqual(fortschritt(m), { geprueft: 1, gesamt: 2, haeuserGeprueft: 9, haeuserGesamt: 16 });
});

test("Kategorie, Name, geprüft gelten für alle Schreibweisen", () => {
  const m = frisch();
  const g = setzeKategorie(m, "Fried. Krupp AG", "industrie");
  assert.deepEqual(g.map((z) => z.schreibweise), ["Fried. Krupp A.G.", "Fried. Krupp AG."]);
  assert.equal(m.zeilen.get("Fried. Krupp AG.").kategorie, "industrie");
  benenne(m, "Fried. Krupp AG", "Friedrich Krupp AG");
  assert.equal(eigentuemerListe(m)[1].name, "Friedrich Krupp AG");
  const p = setzeGeprueft(m, "Friedrich Krupp AG", true);
  assert.equal(p.length, 2);
  assert.deepEqual(fortschritt(m), { geprueft: 2, gesamt: 2, haeuserGeprueft: 16, haeuserGesamt: 16 });
  assert.deepEqual(zumSpeichern(m.zeilen.get("Fried. Krupp A.G.")),
    { schreibweise: "Fried. Krupp A.G.", art: "koerperschaft", eigentuemer: "Friedrich Krupp AG", kategorie: "industrie", geprueft: "ja", hinweis: "", identitaet: "" });
});

test("abspalten, zusammenführen, Vorschlag übernehmen", () => {
  const m = frisch();
  const a = abspalten(m, "Fried. Krupp AG.");
  assert.deepEqual(a.map((z) => [z.schreibweise, z.eigentuemer, z.geprueft]), [["Fried. Krupp AG.", "Fried. Krupp AG.", ""]]);
  assert.equal(eigentuemerListe(m).length, 5);
  const z = zusammenfuehren(m, "Fried. Krupp AG.", "Fried. Krupp AG");
  assert.deepEqual(z.map((x) => x.eigentuemer), ["Fried. Krupp AG"]);
  setzeKategorie(m, "Fried. Krupp AG", "industrie");
  const u = uebernehmeVorschlag(m, "Krupp Stiftung", "Fried. Krupp AG");
  assert.deepEqual(u.map((x) => [x.schreibweise, x.eigentuemer, x.kategorie, x.geprueft]), [["Krupp Stiftung", "Fried. Krupp AG", "industrie", ""]]);
  assert.equal(eigentuemerListe(m)[1].haeuser, 9);
  // Zusammenführen hebt „geprüft“ des Ziels auf, weil sich sein Bestand geändert hat
  setzeGeprueft(m, "Fried. Krupp AG", true);
  abspalten(m, "Krupp Stiftung");
  assert.equal(eigentuemerListe(m).find((e) => e.name === "Fried. Krupp AG").geprueft, false);
});

test("rückgängig stellt den vorigen Stand her und liefert die geänderten Zeilen", () => {
  const m = frisch();
  setzeKategorie(m, "Fried. Krupp AG", "industrie");
  abspalten(m, "Fried. Krupp AG.");
  let r = rueckgaengig(m);
  assert.deepEqual(r.map((z) => [z.schreibweise, z.eigentuemer]), [["Fried. Krupp AG.", "Fried. Krupp AG"]]);
  r = rueckgaengig(m);
  assert.deepEqual(r.map((z) => z.kategorie), ["", ""]);
  assert.equal(rueckgaengig(m), null);
});

test("eigentuemerListe dedupliziert Vorschläge, wenn eine Gruppe mehrere Schreibweisen mit derselben cluster_id hat (F1)", () => {
  const m = frisch();
  // Zweite Schreibweise der Krupp-Gruppe mit derselben cluster_id "k1" wie die vorhandenen —
  // der Vorschlag "Krupp Stiftung" darf trotzdem nur einmal erscheinen, nicht einmal je Schreibweise.
  m.zeilen.set("Krupp AG Essen", { schreibweise: "Krupp AG Essen", art: "koerperschaft", eigentuemer: "Fried. Krupp AG", kategorie: "", geprueft: "", hinweis: "", anzahl: 1, cluster_id: "k1", pruefpflichtig: false, verwaist: false });
  const krupp = eigentuemerListe(m).find((e) => e.name === "Fried. Krupp AG");
  assert.deepEqual(krupp.vorschlaege.map((v) => v.zeile.schreibweise), ["Krupp Stiftung"]);
});

test("setzeKategorie/setzeHinweis/setzeGeprueft liefern [] ohne Verlaufseintrag, wenn sich nichts ändert (F9)", () => {
  const m = frisch();
  assert.deepEqual(setzeKategorie(m, "Stadt Essen", "stadt_staat"), []);
  assert.deepEqual(setzeGeprueft(m, "Stadt Essen", true), []);
  assert.deepEqual(setzeHinweis(m, "Stadt Essen", ""), []);
  assert.equal(m.verlauf.length, 0);
  assert.equal(rueckgaengig(m), null);
});

test("benenne in einen bestehenden Eigentümer führt zusammen statt still umzubenennen (F4)", () => {
  const m = frisch();
  setzeGeprueft(m, "Stadt Essen", false);   // damit ein Bestandswechsel sichtbar entprüft
  setzeKategorie(m, "Stadt Essen", "stadt_staat");
  setzeGeprueft(m, "Stadt Essen", true);
  const g = benenne(m, "Krupp Stiftung", "Stadt Essen");
  assert.deepEqual(g.map((z) => [z.schreibweise, z.eigentuemer, z.kategorie, z.geprueft]).sort(),
    [["Krupp Stiftung", "Stadt Essen", "stadt_staat", ""], ["Stadt Essen", "Stadt Essen", "stadt_staat", ""]]);
  const liste = eigentuemerListe(m);
  assert.equal(liste.find((e) => e.name === "Krupp Stiftung"), undefined);
  const stadt = liste.find((e) => e.name === "Stadt Essen");
  assert.equal(stadt.haeuser, 11);
  assert.equal(stadt.geprueft, false);   // Ziel wurde durch den neuen Bestand entprüft
});

test("Vorschlag übernehmen bewegt nur die eine Schreibweise", () => {
  const m = frisch();
  // Krupp Stiftung bekommt eine zweite Schreibweise in derselben Gruppe
  m.zeilen.set("Krupp-Stiftung Essen", { schreibweise: "Krupp-Stiftung Essen", art: "koerperschaft", eigentuemer: "Krupp Stiftung", kategorie: "", geprueft: "", hinweis: "", anzahl: 3, cluster_id: "k2", pruefpflichtig: false, verwaist: false });
  setzeGeprueft(m, "Fried. Krupp AG", true);
  const u = uebernehmeVorschlag(m, "Krupp Stiftung", "Fried. Krupp AG");
  assert.deepEqual(u.map((x) => [x.schreibweise, x.eigentuemer, x.geprueft]).sort(),
    [["Fried. Krupp A.G.", "Fried. Krupp AG", ""], ["Fried. Krupp AG.", "Fried. Krupp AG", ""], ["Krupp Stiftung", "Fried. Krupp AG", ""]]);
  assert.equal(m.zeilen.get("Krupp-Stiftung Essen").eigentuemer, "Krupp Stiftung");   // bleibt zurück
  assert.equal(uebernehmeVorschlag(m, "Krupp Stiftung", "Fried. Krupp AG").length, 0); // schon dort
});

test("Identität nur als Ganzes und ohne Verlaufseintrag bei Nulländerung", () => {
  const m = frisch();
  m.zeilen.set("Müller, J.", { schreibweise: "Müller, J.", art: "person", eigentuemer: "Müller, J.", kategorie: "privatperson", geprueft: "ja", hinweis: "", identitaet: "", anzahl: 31, cluster_id: "p1", pruefpflichtig: true, verwaist: false });
  assert.deepEqual(setzeIdentitaet(m, "Müller, J.", false), []);
  assert.equal(m.verlauf.length, 0);
  const g = setzeIdentitaet(m, "Müller, J.", true);
  assert.deepEqual(g.map((z) => z.identitaet), ["sicher"]);
  assert.equal(eigentuemerListe(m).find((e) => e.name === "Müller, J.").identitaet, "sicher");
  assert.deepEqual(zumSpeichern(g[0]).identitaet, "sicher");
  assert.deepEqual(rueckgaengig(m).map((z) => z.identitaet), [""]);
});
