// site/js/formen/bubbles.js — Kreispackung aus den vorberechneten Layouts (5a): ein Kreis je
// Beruf, Eigentümer oder Gewerbe. Die Lage kommt aus der Datei, eingefärbt wird nach Gruppe.
import { esc, formatZahl, GRAU, hinweisText, einheitKlasse, leer, r2, skaliere, svgKopf } from "./skalen.js";

// Datenkern → Layoutdatei und Feld, über das die Zugehörigkeit zu einer Gruppe entschieden wird.
const LAYOUT = { besitz: ["eigentuemer", "gruppe"], stellung: ["berufe", "stellung"], gruppe: ["berufe", "gruppe"], gewerbe: ["gewerbe", "gruppe"] };

export function zeige(ansicht, daten, optionen = {}) {
  const wahl = LAYOUT[ansicht.daten];
  const layout = wahl && daten && daten.layout ? daten.layout[wahl[0]] : null;
  if (!layout || !Array.isArray(layout.kreise) || !layout.kreise.length) return leer("kein Layout für diesen Datenkern");
  const feld = wahl[1];
  const breite = optionen.breite || 400;
  const hoehe = optionen.hoehe || 400;
  const hervor = new Set(optionen.hervorheben || []);

  // Farbe je Schlüssel des Layoutfelds; was in keiner Gruppe liegt, bleibt grau.
  const farbeJeSchluessel = new Map();
  for (const g of ansicht.gruppen) for (const k of g.aus) if (!farbeJeSchluessel.has(k)) farbeJeSchluessel.set(k, g.farbe);

  const kreise = layout.kreise;
  const minX = Math.min(...kreise.map((k) => k.x - k.r));
  const maxX = Math.max(...kreise.map((k) => k.x + k.r));
  const minY = Math.min(...kreise.map((k) => k.y - k.r));
  const maxY = Math.max(...kreise.map((k) => k.y + k.r));
  const p = skaliere({ minX, maxX, minY, maxY }, breite, hoehe);

  let N = 0; let n_aus = 0; let unter_min = 0;
  const teile = [svgKopf(breite, hoehe)];
  if (optionen.titel) teile.push(`<text x="8" y="18" class="titel">${esc(optionen.titel)}</text>`);
  for (const k of kreise) {
    const n = Number(k.n) || 0;
    const inGruppe = farbeJeSchluessel.has(k[feld]);
    const unterMin = n < ansicht.min_n;
    // Gleiche Grau-Regel wie überall: zu wenige Nennungen werden nie eingefärbt.
    const farbe = unterMin || !inGruppe ? GRAU : farbeJeSchluessel.get(k[feld]);
    if (inGruppe) N += n; else n_aus += n;
    if (unterMin) unter_min += 1;
    const istHervor = hervor.has(k.id);
    const rand = istHervor ? ' stroke="#111" stroke-width="2"' : "";
    teile.push(`<circle class="${einheitKlasse(istHervor, unterMin)}" data-id="${esc(k.id)}" cx="${r2(p.x(k.x))}" cy="${r2(p.y(k.y))}" r="${r2(Math.max(1, k.r * p.s))}" fill="${esc(farbe)}"${rand}>`
      + `<title>${esc(k.id)}: ${formatZahl(n)}</title></circle>`);
  }
  teile.push("</svg>");
  const zahlen = { N, n_aus, unter_min, einheiten: kreise.length, hinweis: "" };
  zahlen.hinweis = hinweisText(zahlen);
  const legende = [...ansicht.gruppen.map((g) => ({ name: g.name, farbe: g.farbe, text: g.name })),
    { name: "ausgeschlossen", farbe: GRAU, text: "in keiner Gruppe" }];
  return { svg: teile.join(""), legende, zahlen };
}
