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

// Klassen einer Einheit. Reihenfolge fest: erst "einheit", dann der Zustand. Hervorhebung geht
// vor "unter-min", damit angeklickte Einheiten eindeutig erkennbar bleiben; die graue Darstellung
// unter min_n markieren die Formen zusätzlich am inneren Element.
export const einheitKlasse = (hervor, unterMin) => (hervor ? "einheit hervorgehoben" : unterMin ? "einheit unter-min" : "einheit");

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

// Legende der Gruppen einer Ansicht; jede Form hängt eigene Zusatzeinträge an.
export const gruppenLegende = (ansicht) => ansicht.gruppen.map((g) => ({ name: g.name, farbe: g.farbe, text: g.name }));

// Leeres Ergebnis mit erklärendem Hinweis — jede Form liefert dieselbe Struktur.
export const leer = (hinweis) => ({ svg: "", legende: [], zahlen: { N: 0, n_aus: 0, unter_min: 0, einheiten: 0, hinweis } });
