import test from "node:test";
import assert from "node:assert/strict";
import { normalisiere } from "../js/ansicht.js";
import { datenbasisLink, detailLage, detailText, detailTextGruppe, detailTextStufe, detailZustand, DETAIL_ZU, formFuer, fuellePlatzhalter, linkKarte, sichtbareKapitel, zeichenflaeche } from "../js/perspektiven_modell.js";

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
