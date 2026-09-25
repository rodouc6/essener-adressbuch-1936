// site/js/formen/stadtteilkarte.js — Choroplethenkarte der heutigen Stadtteilgrenzen (OSM).
// Einfache Plattkarte mit Breitengrad-Korrektur; für das Stadtgebiet genau genug.
import { werteJeEinheit, filterEinheiten } from "../daten_ebenen.js";
import { esc, farbeAnteil, formatZahl, GRAU, einheitKlasse, leer, r2, SEQUENZ, skaliere, STUFEN_TEXT, svgKopf, zahlenZeile } from "./skalen.js";

const COS = Math.cos((51.45 * Math.PI) / 180);
const ringe = (geom) => (!geom ? [] : geom.type === "MultiPolygon" ? geom.coordinates.flat() : geom.type === "Polygon" ? geom.coordinates : []);

export function zeige(ansicht, daten, optionen = {}) {
  const fc = daten && daten.polygone;
  if (!fc || !Array.isArray(fc.features) || !fc.features.length) return leer("Stadtteilgrenzen fehlen");
  const breite = optionen.breite || 500;
  const hoehe = optionen.hoehe || 500;
  const hervor = new Set(optionen.hervorheben || []);

  const alle = werteJeEinheit(ansicht, daten);
  const werte = filterEinheiten(alle, ansicht.filter);
  const zahlen = zahlenZeile(werte, alle, " · heutige Stadtteilgrenzen (OSM)");
  const jeId = new Map(werte.map((w) => [w.id, w]));
  const maxDichte = Math.max(0, ...werte.filter((w) => !w.unter_min && typeof w.wert === "number").map((w) => w.wert));

  // Bounding-Box aller Ringe, danach lineare Abbildung in die Fläche.
  let minX = Infinity; let maxX = -Infinity; let minY = Infinity; let maxY = -Infinity;
  for (const f of fc.features) for (const ring of ringe(f.geometry)) for (const [lon, lat] of ring) {
    const x = lon * COS;
    minX = Math.min(minX, x); maxX = Math.max(maxX, x); minY = Math.min(minY, lat); maxY = Math.max(maxY, lat);
  }
  const p = skaliere({ minX, maxX, minY, maxY }, breite, hoehe, true);

  const teile = [svgKopf(breite, hoehe)];
  if (optionen.titel) teile.push(`<text x="8" y="18" class="titel">${esc(optionen.titel)}</text>`);
  for (const f of fc.features) {
    const id = f.properties && f.properties.id ? f.properties.id : "";
    const w = jeId.get(id);
    const d = ringe(f.geometry).map((ring) => ring.map(([lon, lat], i) => `${i ? "L" : "M"}${r2(p.x(lon * COS))} ${r2(p.y(lat))}`).join("") + "Z").join("");
    if (!d) continue;
    const istHervor = hervor.has(id);
    const rand = istHervor ? ' stroke="#111" stroke-width="2"' : ' stroke="#fff" stroke-width="0.5"';
    teile.push(`<path class="${einheitKlasse(istHervor, !w || w.unter_min)}" data-id="${esc(id)}" d="${d}" fill="${esc(fuellung(w, ansicht, maxDichte))}"${rand}><title>${esc(id)}</title></path>`);
  }
  teile.push("</svg>");
  return { svg: teile.join(""), legende: legendeBauen(ansicht), zahlen };
}

// Nichts unter min_n und nichts ohne Werte wird eingefärbt.
function fuellung(w, ansicht, maxDichte) {
  if (!w || w.unter_min) return GRAU;
  if (ansicht.mass === "dominant") return w.dominant === "gemischt" ? GRAU : (ansicht.gruppen.find((g) => g.name === w.dominant)?.farbe || GRAU);
  if (ansicht.mass === "mischung") return farbeAnteil(w.mischung);
  if (ansicht.mass === "dichte") return w.wert == null || maxDichte <= 0 ? GRAU : farbeAnteil(w.wert / maxDichte);
  return farbeAnteil(typeof w.wert === "number" ? w.wert : 0);
}

function legendeBauen(ansicht) {
  const grau = { name: `unter ${formatZahl(ansicht.min_n)} Nennungen`, farbe: GRAU, text: "zu wenige Nennungen" };
  if (ansicht.mass === "dominant") {
    return [...ansicht.gruppen.map((g) => ({ name: g.name, farbe: g.farbe, text: `überwiegend ${g.name}` })),
      { name: "gemischt", farbe: GRAU, text: "keine Gruppe über 40 %" }, grau];
  }
  const stufen = STUFEN_TEXT.map((t, i) => ({ name: t, farbe: SEQUENZ[i], text: t }));
  return [...stufen, grau];
}
