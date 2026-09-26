// site/js/formen/stadtteilkarte.js — Choroplethenkarte der heutigen Stadtteilgrenzen (OSM).
// Einfache Plattkarte mit Breitengrad-Korrektur; für das Stadtgebiet genau genug.
import { werteJeEinheit, filterEinheiten } from "../daten_ebenen.js";
import { esc, farbeNachMass, einheitKlasse, leer, legendeNachMass, r2, skaliere, svgKopf, zahlenZeile } from "./skalen.js";

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
    // Dunkler Rand: die hellste Stufe (#f7fbff) und Grau heben sich vom Papierhintergrund sonst
    // kaum ab — die äußeren Stadtteile wären ohne Kontur unsichtbar.
    const rand = istHervor ? ' stroke="#111" stroke-width="2"' : ' stroke="#555" stroke-width="0.6"';
    // Nichts unter min_n und nichts ohne Werte wird eingefärbt (farbeNachMass, gemeinsame Regel).
    teile.push(`<path class="${einheitKlasse(istHervor, !w || w.unter_min)}" data-id="${esc(id)}" d="${d}" fill="${esc(farbeNachMass(w, ansicht, maxDichte))}"${rand}><title>${esc(id)}</title></path>`);
  }
  teile.push("</svg>");
  return { svg: teile.join(""), legende: legendeNachMass(ansicht, { max: maxDichte }), zahlen };
}
