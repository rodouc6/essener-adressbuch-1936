// Der gesamte Zustand der Kartenseite liegt in der URL (Spec §4): reproduzierbare Links.
export const STANDARD = Object.freeze({
  q: "", ebene: ["I", "II", "III"], stadtteil: "", praez: ["haus", "strasse", "stadtplan"], beruf: "", eigentuemer: "",
  thema: "", id: "", karte: "positron", plan: 0, zechen: 0, z: null, c: null,
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

export function liesZustand(search) {
  const p = new URLSearchParams((search || "").replace(/^\?/, ""));
  const c = p.get("c") ? p.get("c").split(",").map(Number) : null;
  return {
    q: p.get("q") || "",
    ebene: liste(p.get("ebene"), EBENEN, STANDARD.ebene),
    stadtteil: p.get("stadtteil") || "",
    praez: liste(p.get("praez"), PRAEZ, STANDARD.praez),
    beruf: p.get("beruf") || "",
    eigentuemer: p.get("eigentuemer") || "",
    thema: p.get("thema") || "",
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
    p.set(k, Array.isArray(w) ? w.join(",") : String(w));
  }
  // URLSearchParams kodiert Kommas als %2C; für lesbare Links (c=7.06,51.49) zurücknehmen.
  return p.toString().replace(/%2C/g, ",");
}

export function zustandGleich(a, b) {
  return schreibeZustand(a) === schreibeZustand(b);
}
