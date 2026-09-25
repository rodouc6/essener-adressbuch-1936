// site/js/perspektiven_modell.js — reine Hilfen der Perspektiven-Seite (Spec §6.2): Auswahl der
// Kapitel, Platzhalter in den Grenzen-Texten, Links in Karte und Werkstatt, Wahl der Form und der
// Text des Detailkastens. Ohne DOM, damit node:test alles prüfen kann.
import { kodiere } from "./ansicht.js";
import { formatProzent, formatZahl } from "./formen/skalen.js";

// Ohne ?vorschau=1 zeigt die Seite nur freigegebene Kapitel; in der Vorschau alle, damit
// unfertige Kapitel gelesen werden können, ohne sie zu veröffentlichen.
export function sichtbareKapitel(index, vorschau = false) {
  const alle = Array.isArray(index) ? index : [];
  return vorschau ? [...alle] : alle.filter((k) => k && k.freigegeben === true);
}

const round1 = (v) => Math.round(v * 10) / 10;
const komma = (v) => v.toLocaleString("de-DE", { maximumFractionDigits: 1 });

// Eine Kennzahl als Text: Zeichenketten (Stand) unverändert, ganze Zahlen mit Tausenderpunkt,
// gebrochene Zahlen (Prozentwerte der Pipeline) mit einer Nachkommastelle — 73.0 wird zu „73“.
function alsText(v) {
  if (typeof v === "string") return v;
  if (typeof v !== "number" || !Number.isFinite(v)) return null;
  return Number.isInteger(v) ? formatZahl(v) : komma(round1(v));
}

// Ersetzt {schluessel} aus kennzahlen.json. Der Zusatz `_prozent` rechnet den Anteil an den
// verorteten Adressen aus ({besitz_geprueft_prozent}). Unbekannte Platzhalter bleiben sichtbar
// stehen — lieber eine erkennbare Lücke im Text als eine stillschweigend erfundene Zahl.
export function fuellePlatzhalter(text, kennzahlen = {}) {
  const kz = kennzahlen && typeof kennzahlen === "object" ? kennzahlen : {};
  return String(text ?? "").replace(/\{(\w+)\}/g, (treffer, k) => {
    if (k.endsWith("_prozent")) {
      const basis = kz[k.slice(0, -"_prozent".length)];
      const nenner = kz.adressen;
      if (typeof basis !== "number" || typeof nenner !== "number" || !nenner) return treffer;
      return komma(round1((100 * basis) / nenner));
    }
    return alsText(kz[k]) ?? treffer;
  });
}

export const linkKarte = (ansicht) => `karte.html?ansicht=${kodiere(ansicht)}`;
export const linkWerkstatt = (ansicht) => `werkstatt.html?ansicht=${kodiere(ansicht)}`;

// Welche Form zeichnet diese Ansicht auf der Perspektiven-Seite? Die Seite hat keine MapLibre-
// Karte: `karte` auf Stadtteilebene wird zur Choroplethenkarte, auf jeder anderen Ebene zur
// Rangliste (ehrlicher als eine Punktkarte, die es hier nicht gibt). `multiples` zeichnet die
// Balkenform, die mit filter.je_einheit einen Balken je Einheit liefert.
export function formFuer(ansicht) {
  const form = ansicht && ansicht.form;
  if (form === "karte") return ansicht.ebene === "stadtteil" ? "stadtteilkarte" : "rangliste";
  if (form === "multiples") return "balken";
  if (form === "stadtteilkarte" || form === "bubbles" || form === "rangliste") return form;
  return "balken";
}

// Text des Detailkastens zu einer angeklickten Einheit. Genannt werden immer die einbezogenen
// und die ausgeschlossenen Nennungen; Gruppen ohne Nennung bleiben weg. Liegt die Einheit unter
// min_n, steht das als letzte Zeile da — der Anteil ist dann nicht belastbar.
export function detailText(einheit, ansicht) {
  const e = einheit || {};
  const gruppen = (ansicht && Array.isArray(ansicht.gruppen) ? ansicht.gruppen : [])
    .filter((g) => (e.zaehler?.[g.name] || 0) > 0)
    .sort((a, b) => (e.anteile?.[b.name] || 0) - (e.anteile?.[a.name] || 0));
  const zeilen = [`${formatZahl(e.N)} Nennungen einbezogen, ${formatZahl(e.n_aus)} ausgeschlossen`];
  for (const g of gruppen) zeilen.push(`${g.name} ${formatProzent(e.anteile?.[g.name] || 0)} (${formatZahl(e.zaehler[g.name])})`);
  if (e.unter_min) zeilen.push(`unter ${formatZahl(ansicht?.min_n)} Nennungen — Anteil nicht belastbar`);
  return { titel: String(e.name || e.id || ""), zeilen };
}
