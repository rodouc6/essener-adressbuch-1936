// Ein Thema ist eine Voreinstellung: Merkmalsfilter, Farbregel, Zusatzebenen, Text (Spec §8).

// Schalter eines Themas (Spec Bergbau §5): welche Klassen an sind, welcher Kartenfilter und welche Farbe daraus folgt.
// `klassen` ist der URL-String: "" = alle, "keine" = keine, sonst Komma-Liste; Unbekanntes fällt weg.
export function schalterKlassen(thema, klassen = "") {
  const s = thema && thema.schalter;
  if (!s || !Array.isArray(s.klassen)) return [];
  if (klassen === "keine") return [];
  if (!klassen) return [...s.klassen];
  const gew = new Set(String(klassen).split(",").map((k) => k.trim()));
  return s.klassen.filter((k) => gew.has(k));
}
const feld = (thema, k) => [">", ["coalesce", ["get", `${thema.schalter.praefix}${k}`], 0], 0];
export function schalterFilter(thema, klassen = "") {
  const an = schalterKlassen(thema, klassen);
  return an.length ? ["any", ...an.map((k) => feld(thema, k))] : null;
}
// Farbe nach Rang: die Reihenfolge in schalter.klassen ist der Rang; abgeschaltete Klassen färben nicht.
export function schalterFarbe(thema, klassen = "") {
  const an = schalterKlassen(thema, klassen);
  const werte = (thema.farbe && thema.farbe.werte) || {};
  const sonst = (thema.farbe && thema.farbe.sonst) || "#c8c8c8";
  if (!an.length) return sonst;     // ein `case` ohne Bedingung ist für MapLibre ungültig
  return ["case", ...an.flatMap((k) => [feld(thema, k), werte[k] || "#c8c8c8"]), sonst];
}

export function farbregel(thema, klassen = "") {
  const f = thema.farbe;
  if (!f) return null;
  if (f.art === "einfach") return { merkmal: thema.filter?.merkmal || null, ausdruck: f.wert };
  if (f.art === "skala") {
    const stufen = f.stufen.flatMap(([w, farbe]) => [w, farbe]);
    return { merkmal: f.merkmal, ausdruck: ["interpolate", ["linear"], ["coalesce", ["get", `m_${f.merkmal}`], 0], ...stufen] };
  }
  if (f.art === "kategorien") {
    if (thema.schalter) {
      return { merkmal: null, ausdruck: schalterFarbe(thema, klassen), kategorien: f.werte || {}, sonst: f.sonst || "#c8c8c8",
               filter: schalterFilter(thema, klassen), klassen: schalterKlassen(thema, klassen) };
    }
    const paare = Object.entries(f.werte || {}).flatMap(([k, farbe]) => [k, farbe]);
    return { merkmal: null, ausdruck: ["match", ["get", f.feld], ...paare, f.sonst || "#c8c8c8"], kategorien: f.werte || {}, sonst: f.sonst || "#c8c8c8", filter: null };
  }
  return null;
}

export async function ladeThema(lader, id, klassen = "") {
  const t = await lader.thema(id);
  if (!t) return null;
  // kacheln: eigene Kacheldatei themen/<id>.pmtiles (Spec Themenkacheln §2); fehlt sie im Index (älteres
  // Datenpaket), verhält sich die Karte wie ohne Themenquelle.
  const index = (await lader.json("themen/index.json")) || [];
  const eintrag = index.find((e) => e.id === id);
  return { ...t, farbregel: farbregel(t, klassen), ebenen: t.filter?.ebenen || null, kacheln: !!(eintrag && eintrag.kacheln) };
}

export async function themenListe(lader) {
  const l = (await lader.json("themen/index.json")) || [];
  return l.filter((t) => t.freigegeben).map((t) => ({ id: t.id, titel: t.titel }));
}
