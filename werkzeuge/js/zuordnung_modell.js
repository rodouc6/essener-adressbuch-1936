// werkzeuge/js/zuordnung_modell.js — Zustand des generischen Zuordnungswerkzeugs (Gruppen je OhdAB-Item, Gewerbe je
// Rubrik): eine Zeile je Schlüssel, ein oder zwei Felder mit festem Vokabular, geprüft-Schalter. Ohne DOM (node:test).
const GRUPPEN = ["bergbau", "metall_maschinen", "bau", "holz_moebel", "textil_bekleidung", "lebensmittel", "handel", "gastgewerbe",
  "verkehr_bahn_post", "verwaltung", "bildung_kultur_kirche", "gesundheit", "haus_reinigung", "sonstige"];
const ARTEN = ["handwerk", "handel", "gastgewerbe", "dienstleistung", "industrie", "freier_beruf", "sonstige"];
export const KONFIG = {
  gruppen: { datei: "gruppen.csv", schluessel: "ohdab_id", anzeige: "norm", menge: "nennungen", titel: "Berufsgruppen je OhdAB-Item",
    felder: [{ name: "gruppe", vokabular: GRUPPEN }] },
  gewerbe: { datei: "gewerbe.csv", schluessel: "rubrik", anzeige: "rubrik", menge: "betriebe", titel: "Gewerberubriken (Teil III)",
    felder: [{ name: "gruppe", vokabular: GRUPPEN }, { name: "art", vokabular: ARTEN }] },
};
const VERLAUF_MAX = 30;

export function baueModell(zeilen, konfig) {
  const m = { konfig, zeilen: new Map(), verlauf: [] };
  for (const k of zeilen) {
    const s = (k[konfig.schluessel] || "").trim();
    if (!s) continue;
    const z = { schluessel: s, anzeige: (k[konfig.anzeige] || "").trim(), menge: Number(k[konfig.menge]) || 0, geprueft: k.geprueft || "",
      hinweis: k.hinweis || "", bearbeiter: (k.bearbeiter || "").trim() };
    for (const f of konfig.felder) z[f.name] = (k[f.name] || "").trim();
    m.zeilen.set(s, z);
  }
  return m;
}

export function liste(m) {
  return [...m.zeilen.values()].sort((a, b) => b.menge - a.menge || a.schluessel.localeCompare(b.schluessel, "de"));
}

function merke(m) {
  m.verlauf.push(new Map([...m.zeilen].map(([k, z]) => [k, { ...z }])));
  if (m.verlauf.length > VERLAUF_MAX) m.verlauf.shift();
}

function aendere(m, s, werte) {
  const z = m.zeilen.get(s);
  if (!z || Object.entries(werte).every(([k, v]) => z[k] === v)) return [];
  merke(m); Object.assign(z, werte); return [z];
}

export function setzeFeld(m, s, feld, wert) {
  const f = m.konfig.felder.find((x) => x.name === feld);
  if (!f || !f.vokabular.includes(wert)) return [];
  return aendere(m, s, { [feld]: wert });
}

export function setzeGeprueft(m, s, ja) {
  const z = m.zeilen.get(s);
  if (!z || (ja && m.konfig.felder.some((f) => !z[f.name]))) return [];
  return aendere(m, s, { geprueft: ja ? "ja" : "" });
}

export function setzeHinweis(m, s, text) { return aendere(m, s, { hinweis: text }); }

export function rueckgaengig(m) {
  const alt = m.verlauf.pop();
  if (!alt) return null;
  const geaendert = [];
  for (const [k, z] of alt) {
    const jetzt = m.zeilen.get(k);
    if (!jetzt || Object.keys(z).some((f) => jetzt[f] !== z[f])) { m.zeilen.set(k, z); geaendert.push(z); }
  }
  return geaendert;
}

export function fortschritt(m) {
  const l = [...m.zeilen.values()], g = l.filter((z) => z.geprueft === "ja");
  return { geprueft: g.length, gesamt: l.length, mengeGeprueft: g.reduce((s, z) => s + z.menge, 0), mengeGesamt: l.reduce((s, z) => s + z.menge, 0) };
}

export function zumSpeichern(z, konfig) {
  const out = { [konfig.schluessel]: z.schluessel };
  for (const f of konfig.felder) out[f.name] = z[f.name];
  out.geprueft = z.geprueft; out.hinweis = z.hinweis;
  return out;
}
