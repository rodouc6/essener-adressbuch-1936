// Der gesamte Zustand der Kartenseite liegt in der URL (Spec §4): reproduzierbare Links.
export const STANDARD = Object.freeze({
  q: "", ebene: ["I", "II", "III"], stadtteil: "", praez: ["haus", "strasse", "stadtplan"], beruf: "", vergleich: [],
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

// Vergleich (Spec Themenbaum §3): höchstens fünf typisierte Schlüssel eig:<Name> | norm:<ohdab_id> | rub:<Rubrik>, Trenner |.
export const MAX_VERGLEICH = 5;
const TYPEN = ["eig", "norm", "rub"];
export function schluessel(s) {
  const i = String(s).indexOf(":");
  return i < 0 ? { typ: "", wert: String(s) } : { typ: s.slice(0, i), wert: s.slice(i + 1) };
}
export function schluesselliste(wert) {
  if (!wert) return [];
  const aus = [];
  for (const t of Array.isArray(wert) ? wert : String(wert).split("|")) {
    const s = String(t).trim();
    const { typ, wert: w } = schluessel(s);
    if (TYPEN.includes(typ) && w.trim() && !aus.includes(s)) aus.push(s);
  }
  return aus.slice(0, MAX_VERGLEICH);
}
// Alte Links (eigentuemer=a|b, ohdab=id) werden gelesen, aber nicht mehr geschrieben.
function vergleichAus(p) {
  const neu = schluesselliste(p.get("vergleich"));
  if (neu.length) return neu;
  const alt = (p.get("eigentuemer") || "").split("|").filter((n) => n.trim()).map((n) => `eig:${n.trim()}`);
  if (p.get("ohdab")) alt.push(`norm:${p.get("ohdab")}`);
  return schluesselliste(alt);
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
    vergleich: vergleichAus(p),
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
    p.set(k, Array.isArray(w) ? w.join(k === "vergleich" ? "|" : ",") : String(w));
  }
  // URLSearchParams kodiert Komma, Pipe und Doppelpunkt; für lesbare Links (c=7.06,51.49; vergleich=eig:A|norm:B) zurücknehmen.
  return p.toString().replace(/%2C/g, ",").replace(/%7C/g, "|").replace(/%3A/g, ":");
}

export function zustandGleich(a, b) {
  return schreibeZustand(a) === schreibeZustand(b);
}
