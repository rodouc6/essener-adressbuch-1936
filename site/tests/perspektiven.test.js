import test from "node:test";
import assert from "node:assert/strict";
import { normalisiere } from "../js/ansicht.js";
import { datenbasisLink, detailLage, detailText, detailTextGruppe, detailTextStufe, detailZustand, DETAIL_ZU, formFuer, fuellePlatzhalter, herkunftAktuell, herkunftDatei, herkunftLink, herkunftPfad, herkunftTabelle, linkKarte, sichtbareKapitel, zeichenflaeche } from "../js/perspektiven_modell.js";

test("zeichenflaeche zieht Legende und Zahlenzeile ab und hält Mindestmaße", () => {
  assert.deepEqual(zeichenflaeche(800, 700, 90), { breite: 800, hoehe: 610 });
  assert.deepEqual(zeichenflaeche(390, 480, 300), { breite: 390, hoehe: 240 });   // Mindesthöhe
  assert.deepEqual(zeichenflaeche(0, 0), { breite: 600, hoehe: 500 });            // ohne Messung
});

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
  // Besitz: Regel-Anteil der Privatpersonen wird genannt
  const b = normalisiere({ daten: "besitz", gruppen: [{ name: "Privatpersonen", aus: ["privatperson"] }, { name: "Stadt", aus: ["stadt_staat"] }], min_n: 0 });
  const e = { id: "Kray", name: "Kray", N: 40, n_aus: 60, unter_min: false, anteile: { Privatpersonen: 0.75, Stadt: 0.25 }, zaehler: { Privatpersonen: 30, Stadt: 10 }, regel: 12 };
  assert.deepEqual(detailText(e, b).zeilen, ["40 Nennungen einbezogen, 60 ausgeschlossen", "Privatpersonen 75 % (30)", "Stadt 25 % (10)",
    "davon 12 per Regel klassifiziert (Person ohne Firmenname → Privatperson, keine Handprüfung)"]);
  assert.ok(!detailText({ ...e, regel: 0 }, b).zeilen.some((z) => /Regel/.test(z)));
});

test("detailTextGruppe: Segment des Gesamtbalkens über alle Einheiten, Regel-Anteil bei Privatpersonen", () => {
  const b = normalisiere({ daten: "besitz", gruppen: [{ name: "Privatpersonen", aus: ["privatperson"] }, { name: "Stadt", aus: ["stadt_staat"] }], min_n: 0 });
  const werte = [{ N: 40, n_aus: 60, zaehler: { Privatpersonen: 30, Stadt: 10 }, regel: 12 }, { N: 10, n_aus: 5, zaehler: { Privatpersonen: 0, Stadt: 10 }, regel: 0 }];
  assert.deepEqual(detailTextGruppe("Privatpersonen", werte, b), { titel: "Privatpersonen", zeilen: ["30 von 50 einbezogenen Nennungen (60 %)",
    "davon 12 per Regel klassifiziert (Person ohne Firmenname → Privatperson, keine Handprüfung)"] });
  assert.deepEqual(detailTextGruppe("Stadt", werte, b).zeilen, ["20 von 50 einbezogenen Nennungen (40 %)"]);
  assert.deepEqual(detailTextGruppe("ausgeschlossen", werte, b).zeilen, ["65 Nennungen ausgeschlossen (unbestimmt, ungeprüft), 50 einbezogen"]);
  assert.equal(detailTextGruppe("Katernberg", werte, b), null);
});

test("detailZustand: schweben flüchtig, Klick stellt fest, Schrittwechsel räumt weg", () => {
  // Schweben zeigt flüchtig; das Verlassen räumt wieder weg.
  const a = detailZustand(DETAIL_ZU, "schweben", "Borbeck");
  assert.deepEqual(a, { id: "Borbeck", sichtbar: true, fest: false });
  assert.deepEqual(detailZustand(a, "verlassen", "Borbeck"), DETAIL_ZU);
  // Ein Klick stellt fest: das Verlassen lässt den Kasten stehen, erneutes Schweben derselben
  // Einheit auch — erst eine andere Einheit, Schließen oder ein Schrittwechsel löst ihn.
  const f = detailZustand(a, "klick", "Borbeck");
  assert.deepEqual(f, { id: "Borbeck", sichtbar: true, fest: true });
  assert.deepEqual(detailZustand(f, "verlassen", "Borbeck"), f);
  assert.deepEqual(detailZustand(f, "schweben", "Borbeck"), f);
  assert.deepEqual(detailZustand(f, "schweben", "Karnap"), { id: "Karnap", sichtbar: true, fest: false });
  assert.deepEqual(detailZustand(f, "schliessen"), DETAIL_ZU);
  assert.deepEqual(detailZustand(f, "schrittwechsel"), DETAIL_ZU);
  // Unbekanntes Ereignis lässt den Zustand, wie er ist.
  assert.deepEqual(detailZustand(f, "wackeln", "Karnap"), f);
});

test("detailLage: mittig über der Einheit, sonst darunter, immer im Fenster", () => {
  const fenster = { width: 1000, height: 800 };
  const kasten = { width: 200, height: 100 };
  // Platz oben: mittig darüber, 10 px Abstand.
  assert.deepEqual(detailLage({ left: 400, top: 300, width: 100, height: 40 }, kasten, fenster), { left: 350, top: 190 });
  // Kein Platz oben: darunter.
  assert.deepEqual(detailLage({ left: 400, top: 50, width: 100, height: 40 }, kasten, fenster), { left: 350, top: 100 });
  // Am linken und rechten Rand bleibt der Kasten im Fenster.
  assert.equal(detailLage({ left: 0, top: 300, width: 20, height: 40 }, kasten, fenster).left, 8);
  assert.equal(detailLage({ left: 990, top: 300, width: 10, height: 40 }, kasten, fenster).left, 792);
  // Weder oben noch unten Platz (hohe Einheit am unteren Rand): an den unteren Rand gezogen.
  assert.deepEqual(detailLage({ left: 400, top: 20, width: 100, height: 760 }, kasten, fenster), { left: 350, top: 692 });
});

test("formFuer trichter, besitz_hand_prozent, Detail zu einer Trichter-Stufe", () => {
  assert.equal(formFuer({ daten: "kennzahlen", form: "trichter" }), "trichter");
  const kz = { adressen: 70316, besitz_hand: 31914 };
  assert.equal(fuellePlatzhalter("{besitz_hand_prozent} %", kz), "45,4 %");
  const d = detailTextStufe({ id: "stufe_strasse", name: "straßengenau", wert: 300, basis: 1000, basisName: "Zeilen", anteil: 0.3, erklaerung: "Straße bekannt, Nummer nicht.", muster: "schraffur" });
  assert.equal(d.titel, "straßengenau");
  assert.deepEqual(d.zeilen, ["300 von 1.000 Zeilen (30 %)", "Straße bekannt, Nummer nicht.", "nicht von Hand geprüft (schraffiert)"]);
  const fehlt = detailTextStufe({ id: "x", name: "Adressen", wert: null, basis: 1000, basisName: "Zeilen", anteil: 0, erklaerung: "", muster: "" });
  assert.deepEqual(fehlt.zeilen, ["Kennzahl im Export nicht vorhanden"]);
});

test("detailTextGruppe nennt den Ausschluss des Kapitels", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", form: "balken", gruppen: [{ name: "Privat", aus: ["privatperson"], farbe: "#000" }], bezug: "Privat" });
  const werte = [{ id: "K", N: 90, n_aus: 10, zaehler: { Privat: 90 } }];
  assert.equal(detailTextGruppe("ausgeschlossen", werte, a).zeilen[0], "10 Nennungen ausgeschlossen (unbestimmt, ungeprüft), 90 einbezogen");
  assert.equal(detailTextGruppe("ausgeschlossen", werte, a, "ohne Eigentümerangabe").zeilen[0], "10 Nennungen ausgeschlossen (ohne Eigentümerangabe), 90 einbezogen");
});

test("datenbasisLink nur, wenn Kapitel 0 sichtbar ist", () => {
  const k = { id: "wohneigentum", datenbasis: "x", datenbasis_schritt: "besitz" };
  assert.equal(datenbasisLink(k, [{ id: "datenbasis" }, { id: "wohneigentum" }]), "#s-datenbasis-besitz");
  assert.equal(datenbasisLink(k, [{ id: "wohneigentum" }]), null);          // Review Focus 4
  assert.equal(datenbasisLink({ id: "x", datenbasis: "", datenbasis_schritt: "" }, [{ id: "datenbasis" }]), null);
});

test("detailTextStufe ohne Basis oder ohne Anteil nennt nur den Wert", () => {
  assert.deepEqual(detailTextStufe({ id: "verortet", name: "verortet", wert: 800, basis: null, basisName: "", anteil: 0, erklaerung: "", muster: "" }).zeilen, ["800"]);
  assert.deepEqual(detailTextStufe({ id: "adressen", name: "Adressen", wert: 300, basis: 1000, basisName: "Zeilen", anteil: 0.3, erklaerung: "E.", muster: "", ohne_anteil: true }).zeilen, ["300", "E."]);
});

// ---- Herkunftspfad (Spec 2026-09-27 Herkunftspfad §4) ----------------------------------------------

const H_ST = { arbeiter: { schreibweisen: 534, normen: 419, nennungen: 74635, quelle: { hand: 70000, vorschlag: 4635 }, top: [["Bergm.", 27781, "Bergmann", "hand"], ["Arbeiter", 8432, "Arbeiter", "hand"], ["Schlosser", 7193, "Schlosser", "hand"]] },
               beamte: { schreibweisen: 120, normen: 80, nennungen: 10444, quelle: { hand: 10444, vorschlag: 0 }, top: [["Lehrer", 900, "Lehrer", "hand"]] },
               angestellte: { schreibweisen: 200, normen: 150, nennungen: 12604, quelle: { hand: 12000, vorschlag: 604 }, top: [["Angest.", 5000, "Angestellter", "hand"]] } };
const G_ST = { name: "Arbeiter/Gehilfen", aus: ["arbeiter"], farbe: "#e69f00" };
const A_ST = { daten: "stellung", gruppen: [G_ST, { name: "Bürgertum", aus: ["beamte", "angestellte", "freie_berufe"], farbe: "#1d4ed8" }] };

test("herkunftDatei je Kontext", () => {
  assert.equal(herkunftDatei({ art: "segment", daten: "stellung" }), "stellung");
  assert.equal(herkunftDatei({ art: "kreis", daten: "stellung" }), "berufe");
  assert.equal(herkunftDatei({ art: "kreis", daten: "gruppe" }), "berufe");
  assert.equal(herkunftDatei({ art: "kreis", daten: "besitz" }), "eigentuemer");
  assert.equal(herkunftDatei({ art: "kreis", daten: "gewerbe" }), "rubriken");
  assert.equal(herkunftDatei({ art: "regel", daten: "besitz" }), "besitz");
  assert.equal(herkunftDatei({ art: "einheit", daten: "stellung" }), null);
  assert.equal(herkunftDatei({ art: "ausgeschlossen", daten: "stellung" }), null);
});

test("herkunftPfad: Segment Stellung mit Quellmarken und Top-Schreibweisen", () => {
  const p = herkunftPfad({ art: "segment", daten: "stellung", id: "Arbeiter/Gehilfen", gruppe: G_ST }, H_ST, A_ST);
  assert.deepEqual(p.map((s) => [s.label, s.wert]), [["Buch", "534 Schreibweisen"], ["OhdAB", "419 Berufe"], ["Stellung", "Arbeiter"], ["Gruppe", "Arbeiter/Gehilfen"]]);
  assert.deepEqual(p[2].marken, [{ art: "hand", anteil: 0.9379, zahl: 70000 }, { art: "vorschlag", anteil: 0.0621, zahl: 4635 }]);
  assert.deepEqual(p.beispiele, [["Bergm.", 27781], ["Arbeiter", 8432], ["Schlosser", 7193]]);
});

test("herkunftPfad: Gruppe aus mehreren Klassen summiert (Review Focus 1), fehlende Klasse zählt 0 (Review Focus 2)", () => {
  const g = A_ST.gruppen[1];
  const p = herkunftPfad({ art: "segment", daten: "stellung", id: "Bürgertum", gruppe: g }, H_ST, A_ST);
  assert.equal(p[0].wert, "320 Schreibweisen"); assert.equal(p[1].wert, "230 Berufe");
  assert.equal(p[2].wert, "Beamte, Angestellte, Freie Berufe");          // freie_berufe fehlt in der Datei → 0, aber genannt
  assert.deepEqual(p[2].marken.map((m) => [m.art, m.zahl]), [["hand", 22444], ["vorschlag", 604]]);
  assert.deepEqual(p.beispiele, [["Angest.", 5000], ["Lehrer", 900]]);  // über beide Klassen neu sortiert
  assert.ok(!JSON.stringify(p).includes("undefined"));
});

test("herkunftPfad: Kreis Beruf, Kreis Eigentümer, Kreis Rubrik, Regel-Teil; unbekannte id → leer (Review Focus 3)", () => {
  const berufe = { "B 21112-100": { norm: "Bergmann", nennungen: 24913, schreibweisen: [["Bergm.", 24700], ["Bergmann", 213]], stellung: "arbeiter", stellung_quelle: "hand" } };
  const k = herkunftPfad({ art: "kreis", daten: "stellung", id: "B 21112-100", gruppe: null }, berufe, A_ST);
  assert.deepEqual(k.map((s) => [s.label, s.wert]), [["Buch", "2 Schreibweisen"], ["OhdAB", "Bergmann"], ["Stellung", "Arbeiter"], ["Gruppe", "Arbeiter/Gehilfen"]]);
  assert.deepEqual(k[2].marken, [{ art: "hand", anteil: 1, zahl: 24913 }]);
  assert.deepEqual(herkunftPfad({ art: "kreis", daten: "stellung", id: "B 99999-000", gruppe: null }, berufe, A_ST), []);
  const eig = { "Fried. Krupp AG": { schreibweisen: [["Fried. Krupp A.G.", 257], ["Fried. Krupp A. G.", 181]], schreibweisen_gesamt: 60, zeilen: 733, haeuser: 3351, spanne: 2600, nummer: 18, kategorie: "industrie", identitaet: true, seite: "II-040" } };
  const AB = { daten: "besitz", gruppen: [{ name: "Zechen und Werke", aus: ["bergbau", "industrie"], farbe: "#111" }, { name: "Privatpersonen", aus: ["privatperson"], farbe: "#d97706" }] };
  const e = herkunftPfad({ art: "kreis", daten: "besitz", id: "Fried. Krupp AG", gruppe: null }, eig, AB);
  assert.deepEqual(e.map((s) => [s.label, s.wert]), [["Buch", "60 Schreibweisen"], ["Eigentümer", "Fried. Krupp AG"], ["Klasse", "Industrie"], ["Gruppe", "Zechen und Werke"]]);
  assert.equal(e.zusatz, "733 Zeilen im Häuserbuch, 2.618 Häuser dazu über Hausnummernspannen und gleiche Nummern");
  const rub = { Bäcker: { betriebe: 518, gruppe: "lebensmittel", art: "handwerk", quelle: "hand" } };
  const AG = { daten: "gewerbe", gruppen: [{ name: "Lebensmittel", aus: ["lebensmittel"], farbe: "#d62728" }] };
  const r = herkunftPfad({ art: "kreis", daten: "gewerbe", id: "Bäcker", gruppe: null }, rub, AG);
  assert.deepEqual(r.map((s) => [s.label, s.wert]), [["Buch", "Bäcker"], ["Branche", "Lebensmittel und Genussmittel · Handwerk"], ["Gruppe", "Lebensmittel"]]);
  assert.deepEqual(r[1].marken, [{ art: "hand", anteil: 1, zahl: 518 }]);
  const besitz = { privatperson: { eigentuemer: 300, zeilen: 41000, haeuser: 40800, quelle: { hand: 8275, regel: 32525 }, spanne: 0, nummer: 0, top: [], regel_beispiele: [["Müller, H.", 12]] } };
  const rg = herkunftPfad({ art: "regel", daten: "besitz", id: "Privatpersonen#regel", gruppe: AB.gruppen[1] }, besitz, AB);
  assert.deepEqual(rg.map((s) => [s.label, s.wert]), [["Buch", "Person ohne Firmenname"], ["Regel", "→ Privatperson"], ["Gruppe", "Privatpersonen"]]);
  assert.deepEqual(rg[1].marken, [{ art: "regel", anteil: 1, zahl: 32525 }]);
  assert.equal(rg.hinweis, "keine Handprüfung, keine Identität");
});

test("herkunftTabelle und herkunftLink", () => {
  const t = herkunftTabelle({ art: "segment", daten: "stellung", id: "Arbeiter/Gehilfen", gruppe: G_ST }, H_ST, A_ST);
  assert.deepEqual(t.kopf, ["Schreibweise", "Nennungen", "OhdAB", "Quelle"]);
  assert.deepEqual(t.zeilen[0], ["Bergm.", 27781, "Bergmann", "hand"]); assert.equal(t.gesamt, 534);
  assert.match(t.hinweis, /Berufszählung 1933/); assert.match(t.hinweis, /berufe\.csv/);
  const viele = { x: { ...H_ST.arbeiter, top: Array.from({ length: 12 }, (_, i) => [`S${i}`, 100 - i, "N", "hand"]) } };
  assert.equal(herkunftTabelle({ art: "segment", daten: "stellung", id: "G", gruppe: { name: "G", aus: ["x"] } }, viele, { daten: "stellung", gruppen: [] }).zeilen.length, 10);
  assert.equal(herkunftLink({ art: "kreis", daten: "stellung", id: "B 21112-100" }), "karte.html?ohdab=B%2021112-100");
  assert.equal(herkunftLink({ art: "kreis", daten: "besitz", id: "Fried. Krupp AG" }), "karte.html?eigentuemer=Fried.%20Krupp%20AG");
  assert.equal(herkunftLink({ art: "kreis", daten: "gewerbe", id: "Bäcker" }), "karte.html?q=B%C3%A4cker");
  assert.equal(herkunftLink({ art: "segment", daten: "stellung", id: "Arbeiter/Gehilfen" }), null);
  const eig = { "Fried. Krupp AG": { schreibweisen: [["Fried. Krupp A.G.", 257]], schreibweisen_gesamt: 60, zeilen: 733, haeuser: 3351, spanne: 2600, nummer: 18, kategorie: "industrie", identitaet: true, seite: "II-040" } };
  const te = herkunftTabelle({ art: "kreis", daten: "besitz", id: "Fried. Krupp AG", gruppe: null }, eig, { daten: "besitz", gruppen: [] });
  assert.deepEqual(te.kopf, ["Schreibweise im Buch", "Zeilen", "Quelle"]); assert.deepEqual(te.zeilen[0], ["Fried. Krupp A.G.", 257, "hand"]);
  assert.match(te.hinweis, /733 Zeilen ergeben 3\.351 Häuser/); assert.equal(te.seite, "II-040");
  assert.equal(herkunftTabelle({ art: "einheit", daten: "stellung", id: "Katernberg" }, H_ST, A_ST), null);
});

test("herkunftAktuell: Pfad nur, wenn der Kasten noch dieselbe Einheit zeigt (Review Focus 4)", () => {
  assert.equal(herkunftAktuell({ id: "Arbeiter", sichtbar: true }, "Arbeiter"), true);
  assert.equal(herkunftAktuell({ id: "Beamte", sichtbar: true }, "Arbeiter"), false);
  assert.equal(herkunftAktuell({ id: "Arbeiter", sichtbar: false }, "Arbeiter"), false);
});

test("detailTextGruppe: Regel-Teil (#regel) heißt „per Regel“ und nennt den Regel-Anteil", () => {
  const a = normalisiere({ daten: "besitz", ebene: "stadtteil", form: "balken", gruppen: [{ name: "Privat", aus: ["privatperson"], farbe: "#000" }], bezug: "Privat" });
  const werte = [{ id: "K", N: 90, n_aus: 10, zaehler: { Privat: 90 }, regel: 70 }];
  const d = detailTextGruppe("Privat#regel", werte, a);
  assert.equal(d.titel, "Privat · per Regel");
  assert.equal(d.zeilen[0], "70 von 90 Privat nur per Regel klassifiziert (78 %)");
});

test("detailText: Stadtteil bei Stellung nennt den handbestimmten Anteil", () => {
  const a = normalisiere({ daten: "stellung", ebene: "stadtteil", form: "rangliste", gruppen: [{ name: "Arbeiter", aus: ["arbeiter"], farbe: "#000" }], bezug: "Arbeiter" });
  const d = detailText({ id: "Katernberg", name: "Katernberg", N: 100, n_aus: 20, zaehler: { Arbeiter: 70 }, anteile: { Arbeiter: 0.7 }, stellung_hand: 90 }, a);
  assert.ok(d.zeilen.includes("90 von 100 Nennungen mit von Hand bestimmter Stellung (90 %)"));
  const ohne = detailText({ id: "K", name: "K", N: 100, n_aus: 0, zaehler: {}, anteile: {} }, a);
  assert.ok(!ohne.zeilen.some((z) => /von Hand bestimmter/.test(z)));
});
