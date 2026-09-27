// site/js/perspektiven_modell.js — reine Hilfen der Perspektiven-Seite (Spec §6.2): Auswahl der
// Kapitel, Platzhalter in den Grenzen-Texten, Links in Karte und Werkstatt, Wahl der Form und der
// Text des Detailkastens. Ohne DOM, damit node:test alles prüfen kann.
import { kodiere } from "./ansicht.js";
import { formatProzent, formatZahl } from "./formen/skalen.js";
import { regelText } from "./formen/balken.js";

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

// Kennzahlen, für die `{…_prozent}` ausgerechnet werden darf: reine Zählfelder, deren Nenner die
// verorteten Adressen sind. Die übrigen Felder in kennzahlen.json sind entweder selbst schon
// Prozentwerte (stellung_geprueft, gewerbe_geprueft …) oder haben einen anderen Nenner
// (eigentuemer_geprueft) — für sie bliebe die Rechnung falsch, also wird sie nicht gemacht.
export const PROZENT_BASIS = ["besitz_geprueft"];

// Ersetzt {schluessel} aus kennzahlen.json. Der Zusatz `_prozent` rechnet den Anteil an den
// verorteten Adressen aus ({besitz_geprueft_prozent}), aber nur für PROZENT_BASIS. Unbekannte
// Platzhalter bleiben sichtbar stehen — lieber eine erkennbare Lücke im Text als eine
// stillschweigend erfundene Zahl.
export function fuellePlatzhalter(text, kennzahlen = {}) {
  const kz = kennzahlen && typeof kennzahlen === "object" ? kennzahlen : {};
  return String(text ?? "").replace(/\{(\w+)\}/g, (treffer, k) => {
    if (k.endsWith("_prozent")) {
      const feld = k.slice(0, -"_prozent".length);
      if (!PROZENT_BASIS.includes(feld)) return treffer;
      const basis = kz[feld];
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

// Größe der Zeichenfläche einer Form aus dem gemessenen Platz der Bühne: was Legende und
// Zahlenzeile brauchen, geht ab; unter den Mindestmaßen wird nicht mehr geschrumpft, damit die
// Formen lesbar bleiben (die Seite skaliert das SVG dann herunter). Ohne Messwerte (0) gelten
// Standardmaße.
export const FLAECHE_MIN = { breite: 280, hoehe: 240 };
export function zeichenflaeche(buehneBreite, buehneHoehe, unterbau = 0) {
  const b = Math.floor(Number(buehneBreite) || 0) || 600;
  const h = Math.floor((Number(buehneHoehe) || 0) - (Number(unterbau) || 0)) || 500;
  return { breite: Math.max(FLAECHE_MIN.breite, b), hoehe: Math.max(FLAECHE_MIN.hoehe, h) };
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
  // Besitz: Privatpersonen sind zum Teil nur per Regel klassifiziert — das gehört sichtbar dazu.
  if (ansicht?.daten === "besitz" && e.regel > 0) zeilen.push(regelText(e.regel));
  if (e.unter_min) zeilen.push(`unter ${formatZahl(ansicht?.min_n)} Nennungen — Anteil nicht belastbar`);
  return { titel: String(e.name || e.id || ""), zeilen };
}

// Detailkasten zu einem angeklickten Segment des Gesamtbalkens: die Gruppe über alle gezeichneten
// Einheiten (Summe, Anteil an den einbezogenen Nennungen), bei Besitz mit dem Regel-Anteil der
// Privatpersonen. `null`, wenn der Name weder Gruppe noch „ausgeschlossen“ ist.
export function detailTextGruppe(name, werte, ansicht) {
  const g = (ansicht?.gruppen || []).find((x) => x.name === name);
  if (!g && name !== "ausgeschlossen") return null;
  const N = werte.reduce((s, w) => s + (w.N || 0), 0);
  const n_aus = werte.reduce((s, w) => s + (w.n_aus || 0), 0);
  if (!g) return { titel: "ausgeschlossen", zeilen: [`${formatZahl(n_aus)} Nennungen ausgeschlossen (unbestimmt, ungeprüft), ${formatZahl(N)} einbezogen`] };
  const z = werte.reduce((s, w) => s + (w.zaehler?.[name] || 0), 0);
  const zeilen = [`${formatZahl(z)} von ${formatZahl(N)} einbezogenen Nennungen (${formatProzent(N ? z / N : 0)})`];
  const regel = werte.reduce((s, w) => s + (w.regel || 0), 0);
  if (ansicht?.daten === "besitz" && g.aus.includes("privatperson") && regel > 0) zeilen.push(regelText(regel));
  return { titel: name, zeilen };
}

// Zustand des Detailkastens. Schweben zeigt ihn flüchtig, ein Klick stellt ihn fest (er bleibt
// stehen, wenn der Zeiger die Einheit verlässt); erst Schließen oder ein Schrittwechsel räumt ihn
// weg. Schwebt der Zeiger über eine andere Einheit, gewinnt immer die Einheit unter dem Zeiger —
// die Feststellung einer anderen Einheit fällt damit, sonst zeigte der Kasten beim Verlassen
// wieder etwas, das gerade niemand ansieht.
export const DETAIL_ZU = { id: null, sichtbar: false, fest: false };
export function detailZustand(zustand, ereignis, id = null) {
  const z = zustand || DETAIL_ZU;
  switch (ereignis) {
    case "schweben": return { id, sichtbar: true, fest: z.fest && z.id === id };
    case "verlassen": return z.fest ? z : DETAIL_ZU;
    case "klick": return { id, sichtbar: true, fest: true };
    case "schliessen": case "schrittwechsel": return DETAIL_ZU;
    default: return z;
  }
}

// Lage des Detailkastens (fixed, in Fensterkoordinaten): mittig über dem Rechteck der Einheit mit
// etwas Abstand; reicht der Platz oben nicht, darunter; seitlich so verschoben, dass er im Fenster
// bleibt (mindestens `rand` zum Fensterrand). Alle Maße in px.
export function detailLage(einheit, kasten, fenster, abstand = 10, rand = 8) {
  const e = einheit || {}, k = kasten || {}, f = fenster || {};
  const links = (e.left || 0) + (e.width || 0) / 2 - (k.width || 0) / 2;
  const left = Math.max(rand, Math.min(links, (f.width || 0) - (k.width || 0) - rand));
  let top = (e.top || 0) - (k.height || 0) - abstand;
  if (top < rand) top = (e.top || 0) + (e.height || 0) + abstand;
  if (top + (k.height || 0) > (f.height || 0) - rand) top = Math.max(rand, (f.height || 0) - (k.height || 0) - rand);
  return { left: Math.round(left), top: Math.round(top) };
}
