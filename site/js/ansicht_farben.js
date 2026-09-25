// site/js/ansicht_farben.js — Farbe und Legende einer Ansicht auf der Karte (Spec §8).
// Rein und ohne DOM: karte.js bekommt nur fertige Farben, app.js nur fertige Legendeneinträge,
// damit beides in node:test prüfbar bleibt.
import { GRAU, SEQUENZ, STUFEN_TEXT, farbeAnteil, formatZahl, hinweisText } from "./formen/skalen.js";

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

// Farbe einer einzelnen Einheit. Unter min_n ist immer grau — eine zu dünne Grundlage wird nie
// eingefärbt, auch wenn ein Wert ausgerechnet werden könnte (Präzision vor Bild).
export function farbeFuer(w, ansicht, max) {
  if (!w || w.unter_min) return GRAU;
  if (ansicht.mass === "dominant") {
    const g = ansicht.gruppen.find((x) => x.name === w.dominant);
    return g ? g.farbe : GRAU;
  }
  if (typeof w.wert !== "number" || !Number.isFinite(w.wert)) return GRAU;
  if (ansicht.mass === "dichte") return max > 0 ? farbeAnteil(w.wert / max) : GRAU;
  return farbeAnteil(w.wert);
}

export function werteFarben(werte, ansicht) {
  const max = ansicht.mass === "dichte" ? hoechstwert(werte) : 0;
  const m = new Map();
  for (const w of werte || []) m.set(w.id, { farbe: farbeFuer(w, ansicht, max), wert: w.wert, unter_min: !!w.unter_min, dominant: w.dominant });
  return m;
}

// Legendeneinträge: { art, name, farbe, text }. farbe === null heißt: reine Textzeile.
export function legendeFuer(ansicht, werte = []) {
  const l = [];
  if (ansicht.mass === "dominant") {
    for (const g of ansicht.gruppen) l.push({ art: "gruppe", name: g.name, farbe: g.farbe, text: g.name });
    l.push({ art: "gemischt", name: "gemischt", farbe: GRAU, text: "gemischt (keine Gruppe ≥ 40 %)" });
  } else if (ansicht.mass === "dichte") {
    const max = hoechstwert(werte);
    for (let i = 0; i < SEQUENZ.length; i++) {
      const lo = (max * i) / SEQUENZ.length; const hi = (max * (i + 1)) / SEQUENZ.length;
      l.push({ art: "stufe", name: STUFEN_TEXT[i], farbe: SEQUENZ[i], text: `${formatZahl(lo)}–${formatZahl(hi)} je 1.000 Einträge` });
    }
  } else {
    for (let i = 0; i < SEQUENZ.length; i++) l.push({ art: "stufe", name: STUFEN_TEXT[i], farbe: SEQUENZ[i], text: STUFEN_TEXT[i] });
  }
  const unterMin = werte.filter((w) => w.unter_min).length;
  l.push({ art: "min_n", name: "zu dünne Grundlage", farbe: GRAU,
           text: `unter ${formatZahl(ansicht.min_n)} Nennungen: ${formatZahl(unterMin)} ${unterMin === 1 ? "Einheit" : "Einheiten"} ohne Farbe` });
  const N = werte.reduce((s, w) => s + (w.N || 0), 0);
  const n_aus = werte.reduce((s, w) => s + (w.n_aus || 0), 0);
  l.push({ art: "grundlage", name: "Grundlage", farbe: null, text: hinweisText({ N, n_aus }) });
  if (HERKUNFT[ansicht.ebene]) l.push({ art: "herkunft", name: "Herkunft", farbe: null, text: HERKUNFT[ansicht.ebene] });
  return l;
}

// Kopfzeile der Sidebar unter einer Ansicht.
export const ansichtTitel = (a) => `Ansicht: ${a.daten} · ${a.ebene} · ${a.mass}`;
