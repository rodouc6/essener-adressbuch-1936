// site/js/formen/rangliste.js — Einheiten als sortierte Zeilen mit Balken; Einheiten unter min_n
// stehen grau am Ende und werden nie eingefärbt. Reicht die Höhe nicht für lesbare Zeilen, wird
// die Liste auf zwei Spalten verteilt (48 Stadtteile auf einem Handy).
import { werteJeEinheit, filterEinheiten } from "../daten_ebenen.js";
import { esc, farbeNachMass, formatProzent, formatZahl, legendeNachMass, nennerText, einheitKlasse, r2, svgKopf, zahlenZeile } from "./skalen.js";

const RAND = 8;
const ZEILE_MIN = 13;   // darunter überlappen 11-px-Beschriftungen
const ZEILE_MAX = 28;
const SPALTE_MIN = 300; // schmaler lassen sich Name, Balken und Wert nicht nebeneinander lesen

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

// Spaltenzahl und Zeilenhöhe für n Zeilen in einer Fläche: erst eine Spalte; passen die Zeilen
// dann nicht mehr lesbar übereinander (unter ZEILE_MIN) und ist die Fläche breit genug für zwei
// Spalten, werden es zwei. Rein, damit node:test die Entscheidung prüfen kann.
export function spaltenWahl(n, breite, hoehe) {
  const zeilen = Math.max(1, n);
  const proSpalte = (spalten) => Math.min(ZEILE_MAX, hoehe / Math.ceil(zeilen / spalten));
  if (proSpalte(1) >= ZEILE_MIN || breite < 2 * SPALTE_MIN) return { spalten: 1, zeile: Math.max(ZEILE_MIN, proSpalte(1)) };
  return { spalten: 2, zeile: Math.max(ZEILE_MIN, proSpalte(2)) };
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
  const { spalten, zeile } = spaltenWahl(sortiert.length, breite, hoehe - oben - RAND);
  const proSpalte = Math.ceil(sortiert.length / spalten);
  const spaltenBreite = (breite - RAND) / spalten;
  const beschriftung = Math.min(180, spaltenBreite * 0.36);
  const wertSpalte = Math.min(90, spaltenBreite * 0.24);
  const balkenBreite = Math.max(10, spaltenBreite - beschriftung - wertSpalte - RAND);
  // Die Fläche wächst mit, wenn die Zeilen nicht hineinpassen; die Seite skaliert das SVG dann.
  const hoeheGesamt = Math.max(hoehe, oben + proSpalte * zeile + RAND);

  const teile = [svgKopf(breite, hoeheGesamt)];
  if (optionen.titel) teile.push(`<text x="${RAND}" y="18" class="titel">${esc(optionen.titel)}</text>`);
  for (const [i, w] of sortiert.entries()) {
    const x0 = RAND + Math.floor(i / proSpalte) * spaltenBreite;
    const y = oben + (i % proSpalte) * zeile;
    const h = Math.max(4, zeile - 6);
    const anteil = max > 0 ? Math.min(1, laengenWert(w, ansicht) / max) : 0;
    const istHervor = hervor.has(w.id);
    teile.push(`<g data-id="${esc(w.id)}" class="${einheitKlasse(istHervor, w.unter_min)}">`
      + `<text x="${r2(x0)}" y="${r2(y + h - 2)}" class="name"${istHervor ? ' font-weight="bold"' : ""}>${esc(w.name)}</text>`
      + `<rect class="balken" x="${r2(x0 + beschriftung)}" y="${r2(y)}" width="${r2(anteil * balkenBreite)}" height="${r2(h)}" fill="${esc(farbeNachMass(w, ansicht, maxDichte))}"></rect>`
      + `<text x="${r2(x0 + beschriftung + balkenBreite + 6)}" y="${r2(y + h - 2)}" class="wert">${esc(w.unter_min ? `unter ${formatZahl(ansicht.min_n)} ${nennerText(ansicht)}` : wertText(w, ansicht))}</text>`
      + "</g>");
  }
  teile.push("</svg>");
  return { svg: teile.join(""), legende: legendeNachMass(ansicht, { max: maxDichte }), zahlen };
}
