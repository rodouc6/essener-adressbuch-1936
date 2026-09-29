// Eigentümer-Vergleich (Spec 2026-09-29 §5/§6): reine Hilfsfunktionen ohne DOM und Karte.
import { esc } from "./popup.js";

// Adresse → { gruppe: Index der ersten Gruppe, mehrfach: in mehr als einer Gruppe }
export function gruppenZuordnung(gruppen) {
  const z = new Map();
  gruppen.forEach((g, i) => {
    for (const id of g.adressIds) {
      const alt = z.get(id);
      if (alt) alt.mehrfach = true; else z.set(id, { gruppe: i, mehrfach: false });
    }
  });
  return z;
}

export function mehrfachZahl(gruppen) {
  let n = 0;
  for (const z of gruppenZuordnung(gruppen).values()) if (z.mehrfach) n++;
  return n;
}

// Top n Stadtteile nach Einträgen; Adressen ohne Kurzindex-Eintrag zählen als „unbekannt“.
export function verteilung(adressIds, zaehler, eig, n = 3) {
  const je = new Map();
  for (const id of adressIds) { const s = (eig.get(id) || {}).stadtteil || "unbekannt"; je.set(s, (je.get(s) || 0) + (zaehler.get(id) || 0)); }
  return [...je.entries()].sort((a, b) => b[1] - a[1]).slice(0, n);
}

export function vergleichsleisteHtml(gruppen, eig) {
  const zeilen = gruppen.map((g) => {
    const eintraege = [...g.zaehler.values()].reduce((a, b) => a + b, 0);
    const top = verteilung(g.adressIds, g.zaehler, eig).map(([s, n]) => `${esc(s)} ${n}`).join(" · ");
    return `<div class="zeile"><span class="punkt" style="background:${esc(g.farbe)}"></span> <b>${esc(g.name)}</b> <small>${g.adressIds.length} Häuser · ${eintraege} Einträge</small>` +
      (top ? `<small class="orte">${top}</small>` : "") +
      `<button class="weg" data-eig-weg="${esc(g.name)}" title="${esc(g.name)} entfernen">×</button></div>`;
  });
  const m = mehrfachZahl(gruppen);
  const ring = m ? `<div class="zeile klein">${m} ${m === 1 ? "Haus" : "Häuser"} mit mehreren gewählten Eigentümern (Ring)</div>` : "";
  return `<div class="vergleich">${zeilen.join("")}${ring}</div>`;
}

// Trefferebene (2026-09-29, Befund Christos): alle Treffer als eigene Punktquelle aus dem Kurzindex — unabhängig
// von Kachel-Ausdünnung, Thema und Ebenenfilter. gruppe -1 = ohne Gruppen (schlichte Trefferfarbe).
export function trefferGeoJson(adressIds, zaehler, gruppen, punkte) {
  const zuordnung = gruppen ? gruppenZuordnung(gruppen) : null;
  const features = [];
  for (const id of adressIds) {
    const p = punkte.get(id);
    if (!p || p.lon == null || p.lat == null) continue;
    const z = zuordnung && zuordnung.get(id);
    features.push({ type: "Feature", geometry: { type: "Point", coordinates: [p.lon, p.lat] },
      properties: { id, stufe: p.stufe, stadtteil: p.stadtteil, n: zaehler.get(id) || 0, gruppe: z ? z.gruppe : -1, mehrfach: !!(z && z.mehrfach) } });
  }
  return { type: "FeatureCollection", features };
}
