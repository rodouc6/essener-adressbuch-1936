// werkzeuge/js/berufe_modell.js — Zustand des Berufs-Werkzeugs (Spec §5): eine Zeile je Schreibweise; Aktionen liefern
// die geänderten Zeilen zum Speichern. Ohne DOM, damit node:test es prüfen kann.
const CSV_FELDER = ["schreibweise", "beruf", "status", "ohdab_id", "niveau_unsicher", "geprueft", "hinweis"];
export const STATUS = ["", "ruhestand", "invalide", "witwe", "gewerbe"];
const VERLAUF_MAX = 30;
const UMLAUTE = { "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss" };

export function falte(t) {
  return String(t ?? "").toLowerCase().replace(/-/g, " ").replace(/[äöüß]/g, (c) => UMLAUTE[c]).replace(/[^a-z0-9 ]+/g, " ").trim().replace(/\s+/g, " ");
}

// Geschlechtszusatz wie pipeline/lib/berufe._GESCHLECHT: „/in“, „/-r“ usw. am Wortende entfernen.
// JS kennt kein Unicode-\b, darum expliziter Lookahead statt \b — sonst reißt z. B. „Marineintendanturrat/-rätin“
// vor dem „ä“ eine (aus ASCII-Sicht) Wortgrenze auf und „/-r“ verschwindet fälschlich mit.
const WORTZEICHEN = "A-Za-z0-9_äöüÄÖÜß";
const GESCHLECHT = new RegExp(`/-?(innen|in|frau|r|e)(?![${WORTZEICHEN}])`, "g");

// Klammerzusätze ab drei Zeichen und Alternativen einer Mehrfachnorm („, “ oder „ / “), wie in Python.
const KLAMMER = /\s*\((?=[^)]{3,})[^)]*\)/g;
const KLAMMER_GESCHLECHT = /\((er|e)\/in\)/g;   // „Beamt(er/in)“ → „Beamter“
const ALTERNATIVE = /,\s+|\s+\/\s+/;

// Formen wie pipeline/lib/berufe.formen_von: männlich, weiblich, Norm ohne Geschlechts- und „ - “-Zusatz,
// dazu die Norm ohne Klammerzusatz und jede Alternative einer Mehrfachnorm.
function formenVon(o) {
  const basis = (o.norm || "").replace(KLAMMER_GESCHLECHT, "$1").replace(GESCHLECHT, "");
  const norm = basis.replace(/\s+-\s+/g, " ");
  const extra = [norm, o.maennlich || "", o.weiblich || ""].map((f) => f.replace(KLAMMER, ""));
  // Alternativen nur ohne „ - “-Zusatz und wenn jeder Teil großgeschrieben beginnt (wie Python).
  const teile = extra[0].split(ALTERNATIVE);
  if (teile.length > 1 && !/\s-\s/.test(basis) && teile.every((t) => /^[A-ZÄÖÜ]/.test(t))) extra.push(...teile);
  const out = [];
  for (const f of [o.maennlich, o.weiblich, norm, ...extra]) {
    const k = falte(f); if (k && !out.includes(k)) out.push(k);
  }
  return out;
}

export function baueModell(kuratierungZeilen, ohdabZeilen, kandidaten = {}) {
  const ohdab = new Map(ohdabZeilen.map((o) => [o.ohdab_id.trim(), o]));
  const formen = [];
  for (const o of ohdab.values()) for (const f of formenVon(o)) formen.push([f, o.ohdab_id.trim()]);
  const zeilen = new Map();
  for (const k of kuratierungZeilen) {
    const s = k.schreibweise.trim();
    const kand = (kandidaten[s] || []).map(([id, grund, wert]) => ({ ohdab_id: id, grund, wert: Number(wert), niveau: ohdab.get(id)?.niveau || "keins" }));
    zeilen.set(s, { schreibweise: s, nennungen: Number(k.nennungen) || 0, beruf: (k.beruf || "").trim(), status: (k.status || "").trim(),
      ohdab_id: (k.ohdab_id || "").trim(), niveau_unsicher: k.niveau_unsicher || "", geprueft: k.geprueft || "", hinweis: k.hinweis || "",
      vorschlag_grund: k.vorschlag_grund || "", automatikBeruf: (k.beruf || "").trim(), kandidaten: kand,
      niveauEntscheiden: new Set(kand.map((x) => x.niveau)).size > 1 });
  }
  return { zeilen, ohdab, formen, verlauf: [] };
}

export function liste(m) {
  return [...m.zeilen.values()].sort((a, b) => b.nennungen - a.nennungen || a.schreibweise.localeCompare(b.schreibweise, "de"));
}

export function sucheOhdab(m, text, n = 15) {
  const q = falte(text);
  if (!q) return [];
  const treffer = new Map();   // id → Rang (0 exakt, 1 Präfix, 2 Teilstring)
  for (const [f, id] of m.formen) {
    const r = f === q ? 0 : f.startsWith(q) ? 1 : f.includes(q) ? 2 : -1;
    if (r >= 0 && (!treffer.has(id) || treffer.get(id) > r)) treffer.set(id, r);
  }
  return [...treffer].sort((a, b) => a[1] - b[1] || m.ohdab.get(a[0]).norm.length - m.ohdab.get(b[0]).norm.length || a[0].localeCompare(b[0]))
    .slice(0, n).map(([id]) => m.ohdab.get(id));
}

function merke(m) {
  m.verlauf.push(new Map([...m.zeilen].map(([k, z]) => [k, { ...z }])));
  if (m.verlauf.length > VERLAUF_MAX) m.verlauf.shift();
}

function aendere(m, s, werte) {
  const z = m.zeilen.get(s);
  if (!z || Object.entries(werte).every(([k, v]) => z[k] === v)) return [];
  merke(m);
  Object.assign(z, werte);
  return [z];
}

// Zuordnung ändern → nicht mehr geprüft; Beruf aus der männlichen Form (oder Norm), wenn keiner übergeben wird.
export function setzeZuordnung(m, s, ohdabId, beruf = null) {
  const o = m.ohdab.get(ohdabId);
  if (!o) return [];
  const z = m.zeilen.get(s);
  const b = beruf ?? (z && z.ohdab_id === ohdabId ? z.beruf : (o.maennlich || o.norm));
  // automatikBeruf mitführen: eine OhdAB-Zuordnung ist selbst „automatisch“ (nicht manuell abweichend) —
  // nur ein späterer setzeBeruf() kann den Text noch vom aktuellen Zuordnungsergebnis abweichen lassen.
  return aendere(m, s, { ohdab_id: ohdabId, beruf: b, automatikBeruf: b, geprueft: "" });
}
export const uebernehmeKandidat = (m, s, ohdabId) => setzeZuordnung(m, s, ohdabId);
export function setzeBeruf(m, s, text) { return aendere(m, s, { beruf: text.trim() }); }
export function setzeStatus(m, s, status) { return aendere(m, s, { status }); }
export function schalteStatus(m, s) {
  const z = m.zeilen.get(s); if (!z) return [];
  const i = STATUS.indexOf(z.status.split(";")[0]);
  return setzeStatus(m, s, STATUS[(i + 1) % STATUS.length]);
}
export function setzeNiveauUnsicher(m, s, ja) { return aendere(m, s, { niveau_unsicher: ja ? "ja" : "" }); }
export function setzeGeprueft(m, s, ja) {
  const z = m.zeilen.get(s);
  if (!z || (ja && !z.ohdab_id)) return [];
  return aendere(m, s, { geprueft: ja ? "ja" : "" });
}
export function setzeHinweis(m, s, text) { return aendere(m, s, { hinweis: text }); }

export function rueckgaengig(m) {
  const alt = m.verlauf.pop();
  if (!alt) return null;
  const geaendert = [];
  for (const [k, z] of alt) {
    const jetzt = m.zeilen.get(k);
    if (!jetzt || CSV_FELDER.some((f) => jetzt[f] !== z[f])) { m.zeilen.set(k, z); geaendert.push(z); }
  }
  return geaendert;
}

export function fortschritt(m) {
  const l = [...m.zeilen.values()];
  const g = l.filter((z) => z.geprueft === "ja");
  return { geprueft: g.length, gesamt: l.length, nennungenGeprueft: g.reduce((s, z) => s + z.nennungen, 0), nennungenGesamt: l.reduce((s, z) => s + z.nennungen, 0) };
}

// Status-Wörter wie werkzeuge/berufe_vorschlag.py STATUS_MUSTER (ruhestand, invalide, witwe) — als eigenes
// Wort entfernen, damit „kurz“ wie in zerlege() nur den Berufskern behält.
const STATUS_MUSTER = [
  new RegExp(`(?<![${WORTZEICHEN}])(i\\.\\s?R\\.|a\\.\\s?D\\.|Pensionär(?:in)?|Pension\\.|Pens\\.|Rentner(?:in)?|Rentenempf\\.|Rentn\\.|Rent\\.|Ruhest\\.)(?![${WORTZEICHEN}])`, "g"),
  new RegExp(`(?<![${WORTZEICHEN}])(Invalide|Invalidin|Invalid\\.|Inval\\.|Inv\\.|Inval)(?![${WORTZEICHEN}])`, "g"),
  new RegExp(`(?<![${WORTZEICHEN}])(Ww\\.|Wwe\\.|Witwe)(?![${WORTZEICHEN}])`, "g"),
];

function ohneStatusWoerter(text) {
  let kern = text;
  for (const muster of STATUS_MUSTER) kern = kern.replace(muster, " ");
  return kern.split(/\s+/).filter(Boolean).join(" ").replace(/^[\s,;]+|[\s,;]+$/g, "");
}

// Katalog-Rückkopplung (Spec §5.1): Schreibweise enthält ein Punktwort und der Beruf weicht vom Automatik-Wert ab.
export function katalogVorschlag(m, s) {
  const z = m.zeilen.get(s);
  if (!z || !/\.\s*(\s|$)/.test(s) || !z.beruf || z.beruf === z.automatikBeruf) return null;
  return { kurz: ohneStatusWoerter(s), lang: z.beruf, status: "" };
}

export function zumSpeichern(z) { return Object.fromEntries(CSV_FELDER.map((f) => [f, z[f]])); }
