// site/js/ansicht.js — Ansicht-Modell (Spec §4): eine Ansicht beschreibt eine Darstellung vollständig; Karte,
// Perspektiven und Werkstatt lesen und schreiben dasselbe Objekt. Rein, ohne DOM (node:test).
export const DATEN = ["stellung", "gruppe", "niveau", "besitz", "gewerbe"];
export const EBENEN = ["adresse", "strasse", "stadtteil", "hex"];
export const FORMEN = ["karte", "stadtteilkarte", "bubbles", "balken", "multiples", "rangliste"];
export const MASSE = ["anteil", "dominant", "mischung", "dichte"];
export const KAUFLEUTE = ["unbestimmt", "angestellte", "selbstaendige"];
export const MIN_N = Object.freeze({ adresse: 0, strasse: 30, hex: 50, stadtteil: 200 });
export const OKABE_ITO = ["#e69f00", "#56b4e9", "#009e73", "#f0e442", "#0072b2", "#d55e00", "#cc79a7", "#000000"];
export const STANDARD_ANSICHT = Object.freeze({ daten: "stellung", ebene: "stadtteil", form: "karte", gruppen: [], kaufleute: "unbestimmt", unsicher: false, mass: "anteil", bezug: "", min_n: 200, filter: {}, karte: null });
const PRAEFIX = { stellung: "n_st_", gruppe: "n_gr_", niveau: "n_", besitz: "n_bs_", gewerbe: "n_gw_" };
const NENNER = { stellung: "n_I", gruppe: "n_I", niveau: "n_I", besitz: "adressen", gewerbe: "n_III" };
const AUSGESCHLOSSEN = { stellung: ["unbestimmt"], gruppe: ["ungeprueft"], niveau: ["keins"], besitz: ["ungeprueft"], gewerbe: ["ungeprueft"] };
const NIVEAUS = ["helfer", "fachlich", "spezialist", "hochkomplex", "aufsicht", "fuehrung", "unsicher"];
const STELLUNG = { arbeiter: ["Arbeiter/Gehilfen (nach Schreibung)", "#e69f00"], angestellte: ["Angestellte", "#56b4e9"], beamte: ["Beamte", "#009e73"], selbstaendige: ["Selbständige", "#f0e442"], freie_berufe: ["Freie Berufe und Akademiker", "#0072b2"], unternehmer: ["Unternehmer und Leitende", "#d55e00"], ohne_erwerb: ["Ohne Erwerbsberuf", "#cc79a7"], kaufleute: ["Kaufleute (Stellung unbestimmt)", "#000000"] };
const BESITZ = { privatperson: ["Privatpersonen", "#d97706"], stadt_staat: ["Stadt und Staat", "#1d4ed8"], bergbau: ["Bergbau", "#111827"], industrie: ["Industrie", "#b91c1c"], genossenschaft_siedlung: ["Genossenschaft und Siedlung", "#15803d"], kirche_stiftung: ["Kirche und Stiftung", "#7c3aed"], bank_versicherung: ["Bank und Versicherung", "#0e7490"], sonstige: ["Sonstige", "#6b7280"] };
const GEWERBE = ["bergbau", "metall_maschinen", "bau", "holz_moebel", "textil_bekleidung", "lebensmittel", "handel", "gastgewerbe", "verkehr_bahn_post", "finanzen_recht", "verwaltung", "bildung_kultur_kirche", "gesundheit", "haus_reinigung", "sonstige"];
const GEWERBE_TEXT = { bergbau: "Bergbau und Kokerei", metall_maschinen: "Metall, Maschinen, Elektro", bau: "Bau", holz_moebel: "Holz und Möbel", textil_bekleidung: "Textil und Bekleidung", lebensmittel: "Lebensmittel und Genussmittel", handel: "Handel (übrige Waren)", gastgewerbe: "Gastgewerbe", verkehr_bahn_post: "Verkehr, Bahn, Post", finanzen_recht: "Banken, Versicherungen, Immobilien, Beratung", verwaltung: "Verwaltung, Polizei, Recht", bildung_kultur_kirche: "Bildung, Kultur, Medien, Kirche", gesundheit: "Gesundheit", haus_reinigung: "Haushalt, Reinigung, Körperpflege", sonstige: "Sonstige" };

const wahl = (w, erlaubt, standard) => (erlaubt.includes(w) ? w : standard);

export function normalisiere(obj) {
  const o = obj && typeof obj === "object" ? obj : {};
  const daten = wahl(o.daten, DATEN, STANDARD_ANSICHT.daten);
  const ebene = wahl(o.ebene, EBENEN, STANDARD_ANSICHT.ebene);
  const namen = new Set(); const gruppen = [];
  for (const [i, g] of (Array.isArray(o.gruppen) ? o.gruppen : []).entries()) {
    if (!g || typeof g !== "object" || !Array.isArray(g.aus)) continue;
    let name = String(g.name || `Gruppe ${i + 1}`); let n = 2;
    while (namen.has(name)) name = `${String(g.name || `Gruppe ${i + 1}`)} ${n++}`;
    namen.add(name);
    gruppen.push({ name, aus: g.aus.map(String), farbe: typeof g.farbe === "string" && g.farbe ? g.farbe : OKABE_ITO[gruppen.length % OKABE_ITO.length] });
  }
  const min_n = Number.isInteger(o.min_n) && o.min_n >= 0 ? o.min_n : MIN_N[ebene];
  return {
    daten, ebene, form: wahl(o.form, FORMEN, STANDARD_ANSICHT.form), gruppen,
    kaufleute: wahl(o.kaufleute, KAUFLEUTE, "unbestimmt"), unsicher: o.unsicher === true,
    mass: wahl(o.mass, MASSE, "anteil"), bezug: typeof o.bezug === "string" && namen.has(o.bezug) ? o.bezug : (gruppen[0]?.name || ""),
    min_n, filter: o.filter && typeof o.filter === "object" ? { ...o.filter } : {},
    karte: o.karte && typeof o.karte === "object" ? { zentrum: o.karte.zentrum, zoom: o.karte.zoom } : null,
  };
}

// base64url ohne Padding; Standardwerte werden weggelassen, damit Links kurz bleiben.
function b64(s) { return (typeof btoa === "function" ? btoa(unescape(encodeURIComponent(s))) : Buffer.from(s, "utf8").toString("base64")).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); }
function unb64(s) { const t = s.replace(/-/g, "+").replace(/_/g, "/"); return typeof atob === "function" ? decodeURIComponent(escape(atob(t))) : Buffer.from(t, "base64").toString("utf8"); }
export function kodiere(ansicht) {
  const a = normalisiere(ansicht); const kurz = {};
  for (const k of Object.keys(a)) if (JSON.stringify(a[k]) !== JSON.stringify(STANDARD_ANSICHT[k]) && !(k === "min_n" && a.min_n === MIN_N[a.ebene])) kurz[k] = a[k];
  return b64(JSON.stringify(kurz));
}
export function dekodiere(s) {
  try { return normalisiere(JSON.parse(unb64(String(s || "")))); } catch { return { ...STANDARD_ANSICHT }; }
}

export const praefix = (daten) => PRAEFIX[daten];
export const nenner = (daten) => NENNER[daten];

export function schluesselDerEinheit(einheit, ansicht) {
  const p = praefix(ansicht.daten); const out = {};
  for (const [k, v] of Object.entries(einheit || {})) {
    if (!k.startsWith(p)) continue;
    const s = k.slice(p.length);
    if (ansicht.daten === "niveau" && !NIVEAUS.includes(s)) continue;       // n_I, n_st_… sind keine Niveaus
    out[s] = (out[s] || 0) + v;
  }
  if (ansicht.daten === "stellung" && ansicht.kaufleute !== "unbestimmt" && out.kaufleute) { out[ansicht.kaufleute] = (out[ansicht.kaufleute] || 0) + out.kaufleute; delete out.kaufleute; }
  return out;
}

export function kennzahlen(einheit, ansicht) {
  const z = schluesselDerEinheit(einheit, ansicht); const inGruppe = new Set();
  const anteile = {}; const zaehler = {}; let N = 0;
  for (const g of ansicht.gruppen) { zaehler[g.name] = g.aus.reduce((s, k) => s + (z[k] || 0), 0); N += zaehler[g.name]; g.aus.forEach((k) => inGruppe.add(k)); }
  let n_aus = 0;
  for (const [k, v] of Object.entries(z)) if (!inGruppe.has(k)) n_aus += v;
  if (ansicht.daten === "niveau" && !ansicht.unsicher && inGruppe.has("unsicher")) { N -= z.unsicher || 0; n_aus += z.unsicher || 0; for (const g of ansicht.gruppen) if (g.aus.includes("unsicher")) zaehler[g.name] -= z.unsicher || 0; }
  for (const g of ansicht.gruppen) anteile[g.name] = N ? zaehler[g.name] / N : 0;
  const groesste = ansicht.gruppen.reduce((b, g) => (anteile[g.name] > (b ? anteile[b] : -1) ? g.name : b), null);
  const dominant = groesste && anteile[groesste] > 0.5 ? groesste : "gemischt";
  const k = ansicht.gruppen.length; let h = 0;
  if (k > 1 && N) for (const g of ansicht.gruppen) { const p = anteile[g.name]; if (p > 0) h -= p * Math.log(p); }
  const mischung = k > 1 && N ? Math.min(1, h / Math.log(k)) : 0;
  const nI = einheit?.n_I || 0;
  const dichte = ansicht.daten === "gewerbe" ? (nI ? (1000 * (zaehler[ansicht.bezug] || 0)) / nI : null) : null;
  const wert = ansicht.mass === "anteil" ? (anteile[ansicht.bezug] ?? 0) : ansicht.mass === "dominant" ? dominant : ansicht.mass === "mischung" ? mischung : dichte;
  return { N, n_aus, unter_min: N < ansicht.min_n, anteile, zaehler, wert, dominant, mischung, dichte };
}

export function standardGruppen(daten, hauptgruppen = {}) {
  if (daten === "stellung") return Object.entries(STELLUNG).map(([k, [name, farbe]]) => ({ name, aus: [k], farbe }));
  if (daten === "besitz") return Object.entries(BESITZ).map(([k, [name, farbe]]) => ({ name, aus: k === "sonstige" ? ["sonstige", "gemischt"] : [k], farbe }));
  if (daten === "gewerbe") return GEWERBE.map((k, i) => ({ name: GEWERBE_TEXT[k], aus: [k], farbe: OKABE_ITO[i % OKABE_ITO.length] }));
  if (daten === "niveau") return NIVEAUS.slice(0, 6).map((k, i) => ({ name: k, aus: [k], farbe: OKABE_ITO[i] }));
  return Object.keys(hauptgruppen).sort().map((k, i) => ({ name: hauptgruppen[k].kurz || k, aus: [k], farbe: OKABE_ITO[i % OKABE_ITO.length] }));
}
