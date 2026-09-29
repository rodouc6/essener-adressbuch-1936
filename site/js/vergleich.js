// Eigentümer-Vergleich (Spec 2026-09-29 §5/§6): reine Hilfsfunktionen ohne DOM und Karte.
import { esc } from "./popup.js";
import { schluessel } from "./zustand.js";

// Grundgesamtheit je Schlüsseltyp (Spec Themenbaum §3): steht unter der Vergleichsleiste, nicht im Popup.
const GRUNDGESAMTHEIT = {
  norm: "Berufe: Einträge des Einwohnerverzeichnisses mit geprüftem Beruf; die Namen H bis J fehlen in der Vorlage.",
  eig: "Eigentümer: auch Häuser aus Sammelzeilen des Adressbuchs („2–84 E. …“).",
  rub: "Gewerbe: Betriebe des Branchenverzeichnisses (Teil III), ein Punkt je Haus mit Betrieb.",
};
export function grundgesamtheitSaetze(gruppen) {
  const typen = [...new Set(gruppen.map((g) => schluessel(g.schluessel || "").typ))];
  return ["norm", "eig", "rub"].filter((t) => typen.includes(t)).map((t) => GRUNDGESAMTHEIT[t]);
}
const zahl = (n) => n.toLocaleString("de-DE");
// Punkte zeigen Vorkommen, keine Anteile: bei Gruppen über Faktor 10 sagt die Leiste das (Spec §3).
export function ungleichSatz(gruppen) {
  const n = gruppen.map((g) => g.adressIds.length).filter((x) => x > 0);
  if (n.length < 2) return null;
  const max = Math.max(...n), min = Math.min(...n);
  if (max <= 10 * min) return null;
  return `Die Gruppen sind sehr ungleich groß (${zahl(max)} gegen ${zahl(min)} Häuser); Punkte zeigen Vorkommen, keine Anteile.`;
}

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
    const titel = schluessel(g.schluessel || "").typ === "norm" ? ` title="${esc(g.schluessel)}"` : "";
    return `<div class="zeile"><span class="punkt" style="background:${esc(g.farbe)}"></span> <b${titel}>${esc(g.name)}</b> <small>${g.adressIds.length} Häuser · ${eintraege} Einträge</small>` +
      (top ? `<small class="orte">${top}</small>` : "") +
      `<button class="weg" data-weg="${esc(g.schluessel)}" title="${esc(g.name)} entfernen">×</button></div>`;
  });
  const m = mehrfachZahl(gruppen);
  const ring = m ? `<div class="zeile klein">${m} ${m === 1 ? "Haus" : "Häuser"} mit mehreren gewählten Gruppen (Ring)</div>` : "";
  const saetze = grundgesamtheitSaetze(gruppen).map((s) => `<div class="zeile klein">${esc(s)}</div>`).join("");
  const u = ungleichSatz(gruppen);
  return `<div class="vergleich">${zeilen.join("")}${ring}${saetze}${u ? `<div class="zeile klein">${esc(u)}</div>` : ""}</div>`;
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
