// Lädt Ebenen, Layouts, Polygone und Kennzahlen einmal je Seite und rechnet Werte je Einheit aus einer Ansicht (Spec §6.3).
import { kennzahlen } from "./ansicht.js";

export async function ladeEbenen(lader) {
  const [strassen, stadtteile, hex, berufe, eigentuemer, gewerbe, hauptgruppen, polygone, kz, punkte, zechen] = await Promise.all([
    lader.ebene("strassen"), lader.ebene("stadtteile"), lader.ebene("hex"), lader.layout("berufe"), lader.layout("eigentuemer"), lader.layout("gewerbe"),
    lader.hauptgruppen(), lader.stadtteilePolygone(), lader.kennzahlen(), lader.punkte(), lader.zechen()]);
  return { strassen: strassen || [], stadtteile: stadtteile || [], hex: hex || [], layout: { berufe, eigentuemer, gewerbe }, hauptgruppen: hauptgruppen || {}, polygone, kennzahlen: kz || {}, punkte: punkte || null, zechen: zechen || null };
}

export function einheiten(ebenen, ansicht) {
  return ansicht.ebene === "strasse" ? ebenen.strassen : ansicht.ebene === "stadtteil" ? ebenen.stadtteile : ansicht.ebene === "hex" ? ebenen.hex : [];
}

export function werteJeEinheit(ansicht, ebenen) {
  return einheiten(ebenen, ansicht).map((u) => ({ id: u.id, name: u.name || u.id, lat: u.lat, lon: u.lon, stadtteil: u.stadtteil, rang_nord: u.rang_nord,
    n_I: u.n_I || 0, n_III: u.n_III || 0, adressen: u.adressen || 0, ...kennzahlen(u, ansicht) }));
}

export function zusammenfassung(werte) {
  return { N: werte.reduce((s, w) => s + w.N, 0), n_aus: werte.reduce((s, w) => s + w.n_aus, 0), unter_min: werte.filter((w) => w.unter_min).length, einheiten: werte.length };
}

export function filterEinheiten(werte, filter = {}) {
  let w = werte;
  if (Array.isArray(filter.stadtteil) && filter.stadtteil.length) w = w.filter((x) => filter.stadtteil.includes(x.stadtteil ?? x.id));
  if (Number.isInteger(filter.top) && filter.top > 0) w = [...w].filter((x) => !x.unter_min).sort((a, b) => (typeof b.wert === "number" ? b.wert : 0) - (typeof a.wert === "number" ? a.wert : 0)).slice(0, filter.top);
  return w;
}
