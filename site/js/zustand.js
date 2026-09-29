// Der gesamte Zustand der Kartenseite liegt in der URL (Spec §4): reproduzierbare Links.
export const STANDARD = Object.freeze({
  q: "", ebene: ["I", "II", "III"], stadtteil: "", praez: ["haus", "strasse", "stadtplan"], beruf: "", eigentuemer: [], ohdab: "",
  thema: "", klassen: "", id: "", karte: "positron", plan: 0, zechen: 0, z: null, c: null,
  // Roh-String der Ansicht (Spec §8); dekodiert wird erst in app.js über ansicht.js.
  ansicht: "",
});
const EBENEN = ["I", "II", "III"];
const PRAEZ = ["haus", "strasse", "stadtplan"];
const KARTEN = ["positron", "liberty"];

function liste(wert, erlaubt, standard) {
  if (wert === null) return [...standard];
  const l = wert.split(",").filter((x) => erlaubt.includes(x));
  return l.length ? l : [...standard];
}

function zahl(wert, min, max, standard) {
  if (wert === null) return standard;
  const n = Number(wert);
  if (Number.isNaN(n)) return standard;
  return Math.min(Math.max(n, min), max);
}

// Eigentümer-Vergleich (Spec 2026-09-29 §3): höchstens fünf Namen, Trenner | (Namen können Kommas enthalten).
export const MAX_EIGENTUEMER = 5;
export function namensliste(wert) {
  if (!wert) return [];
  const aus = [];
  for (const t of Array.isArray(wert) ? wert : String(wert).split("|")) { const n = t.trim(); if (n && !aus.includes(n)) aus.push(n); }
  return aus.slice(0, MAX_EIGENTUEMER);
}

export function liesZustand(search) {
  const p = new URLSearchParams((search || "").replace(/^\?/, ""));
  const c = p.get("c") ? p.get("c").split(",").map(Number) : null;
  return {
    q: p.get("q") || "",
    ebene: liste(p.get("ebene"), EBENEN, STANDARD.ebene),
    stadtteil: p.get("stadtteil") || "",
    praez: liste(p.get("praez"), PRAEZ, STANDARD.praez),
    beruf: p.get("beruf") || "",
    eigentuemer: namensliste(p.get("eigentuemer")),
    ohdab: p.get("ohdab") || "",
    thema: p.get("thema") || "",
    klassen: p.get("klassen") || "",
    ansicht: p.get("ansicht") || "",
    id: p.get("id") || "",
    karte: KARTEN.includes(p.get("karte")) ? p.get("karte") : STANDARD.karte,
    plan: zahl(p.get("plan"), 0, 1, 0),
    zechen: p.get("zechen") === "1" ? 1 : 0,
    z: p.get("z") ? (!Number.isNaN(Number(p.get("z"))) ? Number(p.get("z")) : null) : null,
    c: c && c.length === 2 && c.every((x) => !Number.isNaN(x)) ? c : null,
  };
}

function gleich(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function schreibeZustand(z) {
  const p = new URLSearchParams();
  for (const k of Object.keys(STANDARD).sort()) {
    const w = z[k];
    if (gleich(w, STANDARD[k]) || w === null || w === "") continue;
    p.set(k, Array.isArray(w) ? w.join(k === "eigentuemer" ? "|" : ",") : String(w));
  }
  // URLSearchParams kodiert Kommas als %2C; für lesbare Links (c=7.06,51.49) zurücknehmen.
  return p.toString().replace(/%2C/g, ",").replace(/%7C/g, "|");
}

export function zustandGleich(a, b) {
  return schreibeZustand(a) === schreibeZustand(b);
}
