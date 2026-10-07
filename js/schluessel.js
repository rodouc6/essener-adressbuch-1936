// Suchschlüssel, identisch zu pipeline/lib/karte_export.py falte(): klein, Umlaute aufgelöst,
// Akzente entfernt, nur a–z, 0–9 und einzelne Leerzeichen.
const UMLAUTE = { ä: "ae", ö: "oe", ü: "ue", ß: "ss" };

export function falte(text) {
  let t = (text || "").toLowerCase().replace(/[äöüß]/g, (c) => UMLAUTE[c]);
  t = t.normalize("NFKD").replace(/[^\x00-\x7f]/g, "");
  t = t.replace(/[^a-z0-9 ]+/g, " ");
  return t.split(/\s+/).filter(Boolean).join(" ");
}

export function praefix2(text) {
  const k = falte(text).replace(/ /g, "");
  return k ? k.slice(0, 2) : "_";
}
