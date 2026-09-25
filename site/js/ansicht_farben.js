// site/js/ansicht_farben.js — Farbe und Legende einer Ansicht auf der Karte (Spec §8).
// Rein und ohne DOM: karte.js bekommt nur fertige Farben, app.js nur fertige Legendeneinträge,
// damit beides in node:test prüfbar bleibt.
import { farbeNachMass, formatZahl, hinweisText, legendeNachMass } from "./formen/skalen.js";

const HERKUNFT = {
  stadtteil: "heutige Stadtteilgrenzen (OSM)",
  strasse: "Straßenlinien: heutige Führung (OSM)",
  hex: "Raster über den verorteten Adressen",
};

// Höchstwert der auswertbaren (nicht unter min_n liegenden) Einheiten — Bezug der Dichteskala.
export function hoechstwert(werte) {
  let max = 0;
  for (const w of werte) if (!w.unter_min && typeof w.wert === "number" && Number.isFinite(w.wert) && w.wert > max) max = w.wert;
  return max;
}

// Farbe einer einzelnen Einheit — dieselbe Regel wie in allen Formen (skalen.js).
export const farbeFuer = (w, ansicht, max) => farbeNachMass(w, ansicht, max);

export function werteFarben(werte, ansicht) {
  const max = ansicht.mass === "dichte" ? hoechstwert(werte) : 0;
  const m = new Map();
  for (const w of werte || []) m.set(w.id, { farbe: farbeFuer(w, ansicht, max), wert: w.wert, unter_min: !!w.unter_min, dominant: w.dominant });
  return m;
}

// Legendeneinträge: { art, name, farbe, text }. farbe === null heißt: reine Textzeile.
// `zusatz.ohne_linie` ist die Zahl der Straßen-Einheiten ohne OSM-Linie: sie zählen zu N mit,
// können aber gar nicht gezeichnet werden — das muss die Legende sagen, sonst summiert sie
// stillschweigend Einheiten mit, die niemand auf der Karte sieht.
export function legendeFuer(ansicht, werte = [], zusatz = {}) {
  const max = ansicht.mass === "dichte" ? hoechstwert(werte) : 0;
  const l = legendeNachMass(ansicht, { max });
  const unterMin = werte.filter((w) => w.unter_min).length;
  l.push({ art: "unter_min", name: "zu dünne Grundlage", farbe: null,
           text: `davon ${formatZahl(unterMin)} ${unterMin === 1 ? "Einheit" : "Einheiten"} unter ${formatZahl(ansicht.min_n)} (grau)` });
  if (ansicht.ebene === "strasse" && Number.isFinite(zusatz.ohne_linie) && zusatz.ohne_linie > 0) {
    l.push({ art: "ohne_linie", name: "ohne Linie", farbe: null,
             text: `${formatZahl(zusatz.ohne_linie)} Straßen ohne OSM-Linie (nicht darstellbar)` });
  }
  const N = werte.reduce((s, w) => s + (w.N || 0), 0);
  const n_aus = werte.reduce((s, w) => s + (w.n_aus || 0), 0);
  l.push({ art: "grundlage", name: "Grundlage", farbe: null, text: hinweisText({ N, n_aus }) });
  if (HERKUNFT[ansicht.ebene]) l.push({ art: "herkunft", name: "Herkunft", farbe: null, text: HERKUNFT[ansicht.ebene] });
  return l;
}

// Kopfzeile der Sidebar unter einer Ansicht.
export const ansichtTitel = (a) => `Ansicht: ${a.daten} · ${a.ebene} · ${a.mass}`;
