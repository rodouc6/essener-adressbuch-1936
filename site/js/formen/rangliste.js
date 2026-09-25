// site/js/formen/rangliste.js — Einheiten als sortierte Zeilen mit Balken; Einheiten unter min_n
// stehen grau am Ende und werden nie eingefärbt.
import { werteJeEinheit, filterEinheiten } from "../daten_ebenen.js";
import { esc, farbeAnteil, formatProzent, formatZahl, GRAU, einheitKlasse, r2, SEQUENZ, STUFEN_TEXT, svgKopf, zahlenZeile } from "./skalen.js";

const RAND = 8;

// Zahl, an der sich die Balkenlänge bemisst — bei „dominant“ der Anteil der dominanten Gruppe.
function laengenWert(w, ansicht) {
  if (ansicht.mass === "dominant") return w.dominant === "gemischt" ? 0 : w.anteile[w.dominant] || 0;
  return typeof w.wert === "number" ? w.wert : 0;
}

// Beschriftung rechts neben dem Balken.
function wertText(w, ansicht) {
  if (ansicht.mass === "dichte") return w.wert == null ? "—" : `${formatZahl(w.wert)} je 1.000`;
  if (ansicht.mass === "dominant") return String(w.dominant);
  return formatProzent(laengenWert(w, ansicht));
}

// Farbe des Balkens — dieselbe Regel wie auf der Stadtteilkarte, damit beide Formen einer Ansicht
// dieselbe Sprache sprechen. Nichts unter min_n wird eingefärbt.
function balkenFarbe(w, ansicht, max) {
  if (w.unter_min) return GRAU;
  if (ansicht.mass === "dominant") return w.dominant === "gemischt" ? GRAU : (ansicht.gruppen.find((g) => g.name === w.dominant)?.farbe || GRAU);
  if (ansicht.mass === "mischung") return farbeAnteil(w.mischung);
  if (ansicht.mass === "dichte") return w.wert == null || max <= 0 ? GRAU : farbeAnteil(w.wert / max);
  return farbeAnteil(typeof w.wert === "number" ? w.wert : 0);
}

export function zeige(ansicht, daten, optionen = {}) {
  const breite = optionen.breite || 600;
  const hoehe = optionen.hoehe || 300;
  const hervor = new Set(optionen.hervorheben || []);
  const alle = werteJeEinheit(ansicht, daten);
  const werte = filterEinheiten(alle, ansicht.filter);
  const zahlen = zahlenZeile(werte, alle);

  // Erst die auswertbaren Einheiten nach Wert absteigend, danach alle unter min_n.
  const sortiert = [...werte].sort((a, b) => (a.unter_min !== b.unter_min ? (a.unter_min ? 1 : -1)
    : laengenWert(b, ansicht) - laengenWert(a, ansicht)));
  const maxDichte = Math.max(0, ...sortiert.filter((w) => !w.unter_min && typeof w.wert === "number").map((w) => w.wert));
  const max = ansicht.mass === "dichte" ? maxDichte : 1;

  const oben = optionen.titel ? 30 : RAND;
  const zeile = Math.min(28, Math.max(12, (hoehe - oben - RAND) / Math.max(1, sortiert.length)));
  const beschriftung = Math.min(180, breite * 0.32);
  const wertSpalte = 90;
  const balkenBreite = Math.max(10, breite - beschriftung - wertSpalte - RAND);

  const teile = [svgKopf(breite, hoehe)];
  if (optionen.titel) teile.push(`<text x="${RAND}" y="18" class="titel">${esc(optionen.titel)}</text>`);
  for (const [i, w] of sortiert.entries()) {
    const y = oben + i * zeile;
    const h = Math.max(4, zeile - 6);
    const anteil = max > 0 ? Math.min(1, laengenWert(w, ansicht) / max) : 0;
    const istHervor = hervor.has(w.id);
    teile.push(`<g data-id="${esc(w.id)}" class="${einheitKlasse(istHervor, w.unter_min)}">`
      + `<text x="${RAND}" y="${r2(y + h - 2)}" class="name"${istHervor ? ' font-weight="bold"' : ""}>${esc(w.name)}</text>`
      + `<rect class="balken" x="${r2(beschriftung)}" y="${r2(y)}" width="${r2(anteil * balkenBreite)}" height="${r2(h)}" fill="${esc(balkenFarbe(w, ansicht, maxDichte))}"></rect>`
      + `<text x="${r2(beschriftung + balkenBreite + 6)}" y="${r2(y + h - 2)}" class="wert">${esc(w.unter_min ? `unter ${formatZahl(ansicht.min_n)} Nennungen` : wertText(w, ansicht))}</text>`
      + "</g>");
  }
  teile.push("</svg>");
  return { svg: teile.join(""), legende: legendeBauen(ansicht), zahlen };
}

// Legende: bei „dominant“ die Gruppen, sonst die fünf Stufen der Sequenz; zuletzt immer Grau.
function legendeBauen(ansicht) {
  const grau = { name: `unter ${formatZahl(ansicht.min_n)} Nennungen`, farbe: GRAU, text: "zu wenige Nennungen" };
  if (ansicht.mass === "dominant") {
    return [...ansicht.gruppen.map((g) => ({ name: g.name, farbe: g.farbe, text: `überwiegend ${g.name}` })),
      { name: "gemischt", farbe: GRAU, text: "keine Gruppe über 40 %" }, grau];
  }
  return [...STUFEN_TEXT.map((t, i) => ({ name: t, farbe: SEQUENZ[i], text: t })), grau];
}
