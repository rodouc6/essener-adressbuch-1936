// site/js/formen/skalen.js — gemeinsame Skalen, Formate und SVG-Helfer der Formen (Spec §7).
// Rein und ohne DOM: alle Formen erzeugen nur Zeichenketten, damit node:test sie prüfen kann.
export const SEQUENZ = ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"];
export const GRAU = "#c8c8c8";
export const farbeAnteil = (p) => SEQUENZ[Math.min(4, Math.max(0, Math.floor((Number(p) || 0) * 5)))];
export const STUFEN_TEXT = ["0–20 %", "20–40 %", "40–60 %", "60–80 %", "80–100 %"];
export const formatProzent = (p) => `${Math.round((Number(p) || 0) * 100)} %`;
export const formatZahl = (n) => new Intl.NumberFormat("de-DE").format(Math.round(Number(n) || 0));
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const hinweisText = (z) => `${formatZahl(z.N)} Nennungen einbezogen, ${formatZahl(z.n_aus)} ausgeschlossen (unbestimmt, ungeprüft)`;
export function svgKopf(b, h) { return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${b} ${h}" width="${b}" height="${h}" role="img">`; }

// Klassen einer Einheit, additiv und in fester Reihenfolge: "einheit", dann "unter-min",
// dann "hervorgehoben". Beide Zustände können zugleich gelten (eine angeklickte Einheit unter
// min_n), deshalb darf keiner den anderen verdrängen.
export const einheitKlasse = (hervor, unterMin) => `einheit${unterMin ? " unter-min" : ""}${hervor ? " hervorgehoben" : ""}`;

// Zahlenzeile einer Form. N, n_aus und einheiten beziehen sich auf die tatsächlich gezeichnete
// (gefilterte) Menge; unter_min dagegen auf die vollständige Ebene, weil `filterEinheiten` mit
// `top` genau die Einheiten unter der Schwelle entfernt — sie sollen trotzdem ausgewiesen werden.
export function zahlenZeile(gezeichnet, alle, zusatz = "") {
  const z = { N: gezeichnet.reduce((s, w) => s + w.N, 0), n_aus: gezeichnet.reduce((s, w) => s + w.n_aus, 0),
    unter_min: alle.filter((w) => w.unter_min).length, einheiten: gezeichnet.length, einheiten_gesamt: alle.length };
  return { ...z, hinweis: hinweisText(z) + zusatz };
}

// Worauf sich min_n einer Ansicht bezieht — das muss in jeder Legende wörtlich richtig stehen.
// Bei `mass: "dichte"` schwellt ansicht.js den Nenner (Teil-I-Einträge der Einheit), sonst die
// Nennungen der Gruppen; bei `daten: "besitz"` sind die Nennungen geprüfte Adressen.
export function nennerText(ansicht) {
  if (!ansicht) return "Nennungen";
  if (ansicht.mass === "dichte") return "Teil-I-Einträgen";
  return ansicht.daten === "besitz" ? "Adressen mit Besitzklasse" : "Nennungen";
}

// Eine Nachkommastelle mit deutschem Komma — für kleine Dichte- und Mischungswerte.
const komma1 = (v) => (Number(v) || 0).toFixed(1).replace(".", ",");
const dichteZahl = (v, max) => (max < 10 ? komma1(v) : formatZahl(v));

// Farbe einer Einheit nach dem Maß der Ansicht — die eine Regel für Karte, Rangliste und
// Stadtteilkarte. Unter min_n ist immer grau: eine zu dünne Grundlage wird nie eingefärbt,
// auch wenn ein Wert ausgerechnet werden könnte (Präzision vor Bild).
export function farbeNachMass(w, ansicht, max = 0) {
  if (!w || w.unter_min) return GRAU;
  if (ansicht.mass === "dominant") {
    return w.dominant === "gemischt" ? GRAU : (ansicht.gruppen.find((g) => g.name === w.dominant)?.farbe || GRAU);
  }
  if (ansicht.mass === "mischung") return farbeAnteil(w.mischung);
  const zahl = typeof w.wert === "number" && Number.isFinite(w.wert);
  if (ansicht.mass === "dichte") return zahl && max > 0 ? farbeAnteil(w.wert / max) : GRAU;
  return zahl ? farbeAnteil(w.wert) : GRAU;
}

// Legende zum Maß einer Ansicht — dieselbe Regel und dieselben Texte für alle Formen und die
// Kartenlegende. `max` ist nur bei `dichte` nötig (Bezug der Skala), `min_n`/`nennerText`
// überschreiben die Werte aus der Ansicht. Rückgabe: [{ art, name, farbe, text }].
export function legendeNachMass(ansicht, optionen = {}) {
  const min_n = Number.isFinite(optionen.min_n) ? optionen.min_n : ansicht.min_n;
  const einheit = optionen.nennerText || nennerText(ansicht);
  const l = [];
  if (ansicht.mass === "dominant") {
    for (const g of ansicht.gruppen) l.push({ art: "gruppe", name: g.name, farbe: g.farbe, text: `überwiegend ${g.name}` });
    l.push({ art: "gemischt", name: "gemischt", farbe: GRAU, text: "keine Gruppe über 40 %" });
  } else if (ansicht.mass === "mischung") {
    for (let i = 0; i < SEQUENZ.length; i++) {
      const t = `Mischung ${komma1(i / SEQUENZ.length)}–${komma1((i + 1) / SEQUENZ.length)}`;
      l.push({ art: "stufe", name: t, farbe: SEQUENZ[i], text: t });
    }
  } else if (ansicht.mass === "dichte") {
    const max = Number(optionen.max) || 0;
    for (let i = 0; i < SEQUENZ.length; i++) {
      const t = `${dichteZahl((max * i) / SEQUENZ.length, max)}–${dichteZahl((max * (i + 1)) / SEQUENZ.length, max)} je 1.000`;
      l.push({ art: "stufe", name: t, farbe: SEQUENZ[i], text: t });
    }
  } else {
    for (let i = 0; i < SEQUENZ.length; i++) l.push({ art: "stufe", name: STUFEN_TEXT[i], farbe: SEQUENZ[i], text: STUFEN_TEXT[i] });
  }
  const grau = `unter ${formatZahl(min_n)} ${einheit}`;
  l.push({ art: "min_n", name: grau, farbe: GRAU, text: grau });
  return l;
}

// Runden auf zwei Nachkommastellen — hält die SVG-Zeichenketten kurz und deterministisch.
export const r2 = (v) => Math.round((Number(v) || 0) * 100) / 100;

// Lineare Abbildung einer Bounding-Box in breite × hoehe mit 4 % Rand, seitenverhältnistreu.
// spiegelY kehrt die y-Achse um (geographische Breite wächst nach oben, SVG-y nach unten).
export function skaliere({ minX, maxX, minY, maxY }, breite, hoehe, spiegelY = false) {
  const rand = 0.04;
  const dx = maxX - minX || 1;
  const dy = maxY - minY || 1;
  const s = Math.min((breite * (1 - 2 * rand)) / dx, (hoehe * (1 - 2 * rand)) / dy);
  const ox = (breite - dx * s) / 2 - minX * s;
  const oy = (hoehe - dy * s) / 2 - minY * s;
  return { s, x: (v) => ox + v * s, y: (v) => (spiegelY ? hoehe - (oy + v * s) : oy + v * s) };
}

// Leeres Ergebnis mit erklärendem Hinweis — jede Form liefert dieselbe Struktur.
export const leer = (hinweis) => ({ svg: "", legende: [], zahlen: { N: 0, n_aus: 0, unter_min: 0, einheiten: 0, einheiten_gesamt: 0, hinweis } });

// Schraffur für Anteile, die nicht von Hand geprüft sind (Regel, Vorschlag): ein diagonales Muster in
// der Farbe des Segments. Die id enthält den Kennzahl-Schlüssel, damit mehrere Bühnen auf einer Seite
// (ein Kapitel je Bühne) sich nicht die Muster überschreiben.
export const schraffurId = (schluessel) => `schraffur-${String(schluessel).replace(/[^\w-]/g, "_")}`;
export function schraffurDefs(muster) {
  if (!muster.length) return "";
  return "<defs>" + muster.map(({ id, farbe }) =>
    `<pattern id="${esc(id)}" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">`
    + `<rect width="6" height="6" fill="#fff"/><rect width="3" height="6" fill="${esc(farbe)}"/></pattern>`).join("") + "</defs>";
}
