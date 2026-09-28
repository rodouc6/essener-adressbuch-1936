// site/js/perspektiven_modell.js — reine Hilfen der Perspektiven-Seite (Spec §6.2): Auswahl der
// Kapitel, Platzhalter in den Grenzen-Texten, Links in Karte und Werkstatt, Wahl der Form und der
// Text des Detailkastens. Ohne DOM, damit node:test alles prüfen kann.
import { BESITZ, GEWERBE_TEXT, kodiere, STELLUNG } from "./ansicht.js";
import { KATEGORIEN } from "./kategorien.js";
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
export const PROZENT_BASIS = ["besitz_geprueft", "besitz_hand"];

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

// Punktkarten (Bergbau) führen nicht in eine ?ansicht=, sondern auf das Thema der Karte mit den
// hervorgehobenen Klassen (Spec Bergbau §6); die hausgenaue Karte verlinkt je Gesellschaft im Detailkasten.
export function linkKarte(ansicht) {
  if (ansicht && ansicht.form === "punktkarte") {
    if (!ansicht.punkte || ansicht.punkte.zustand === "haeuser") return null;
    const klassen = ansicht.punkte.hervor.map((h) => (ansicht.gruppen.find((g) => g.name === h) || { aus: [] }).aus[0]).filter(Boolean);
    return `karte.html?thema=bergbau${klassen.length ? `&klassen=${klassen.join(",")}` : ""}`;
  }
  return `karte.html?ansicht=${kodiere(ansicht)}`;
}
export const linkWerkstatt = (ansicht) => `werkstatt.html?ansicht=${kodiere(ansicht)}`;

// Welche Form zeichnet diese Ansicht auf der Perspektiven-Seite? Die Seite hat keine MapLibre-
// Karte: `karte` auf Stadtteilebene wird zur Choroplethenkarte, auf jeder anderen Ebene zur
// Rangliste (ehrlicher als eine Punktkarte, die es hier nicht gibt). `multiples` zeichnet die
// Balkenform, die mit filter.je_einheit einen Balken je Einheit liefert.
export function formFuer(ansicht) {
  const form = ansicht && ansicht.form;
  if (form === "trichter") return "trichter";
  if (form === "punktkarte") return "punktkarte";
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
  // Stellung: wie viel der Einheit von Hand bestimmt ist (Rest: Vorschlag der Automatik).
  // Nenner sind alle Teil-I-Einträge der Einheit: n_stellung_hand zählt auch geprüfte Einträge mit offener
  // Stellung, und die gezeichneten Gruppen können eine Teilmenge der Klassen sein.
  if (ansicht?.daten === "stellung" && e.stellung_hand > 0) zeilen.push(`${formatZahl(e.stellung_hand)} von ${formatZahl(e.n_I)} Einträgen in Teil I mit von Hand bestimmter Stellung (${formatProzent(e.n_I ? e.stellung_hand / e.n_I : 0)})`);
  if (e.unter_min) zeilen.push(`unter ${formatZahl(ansicht?.min_n)} Nennungen — Anteil nicht belastbar`);
  return { titel: String(e.name || e.id || ""), zeilen };
}

// Detailkasten zu einem angeklickten Segment des Gesamtbalkens: die Gruppe über alle gezeichneten
// Einheiten (Summe, Anteil an den einbezogenen Nennungen), bei Besitz mit dem Regel-Anteil der
// Privatpersonen. `null`, wenn der Name weder Gruppe noch „ausgeschlossen“ ist.
export function detailTextGruppe(name, werte, ansicht, ausschlussText = "") {
  // Schraffierter Regel-Teil eines Segments („<Gruppe>#regel“): nur der Regel-Anteil der Gruppe.
  if (typeof name === "string" && name.endsWith("#regel")) {
    const basis = name.slice(0, -"#regel".length);
    const gr = (ansicht?.gruppen || []).find((x) => x.name === basis);
    if (!gr) return null;
    const z = werte.reduce((s, w) => s + (w.zaehler?.[basis] || 0), 0);
    const regel = werte.reduce((s, w) => s + (w.regel || 0), 0);
    return { titel: `${basis} · per Regel`, zeilen: [`${formatZahl(regel)} von ${formatZahl(z)} ${basis} nur per Regel klassifiziert (${formatProzent(z ? regel / z : 0)})`] };
  }
  const g = (ansicht?.gruppen || []).find((x) => x.name === name);
  if (!g && name !== "ausgeschlossen") return null;
  const N = werte.reduce((s, w) => s + (w.N || 0), 0);
  const n_aus = werte.reduce((s, w) => s + (w.n_aus || 0), 0);
  if (!g) return { titel: "ausgeschlossen", zeilen: [`${formatZahl(n_aus)} Nennungen ausgeschlossen (${ausschlussText || "unbestimmt, ungeprüft"}), ${formatZahl(N)} einbezogen`] };
  const z = werte.reduce((s, w) => s + (w.zaehler?.[name] || 0), 0);
  const zeilen = [`${formatZahl(z)} von ${formatZahl(N)} einbezogenen Nennungen (${formatProzent(N ? z / N : 0)})`];
  const regel = werte.reduce((s, w) => s + (w.regel || 0), 0);
  if (ansicht?.daten === "besitz" && g.aus.includes("privatperson") && regel > 0) zeilen.push(regelText(regel));
  return { titel: name, zeilen };
}

// Detailkasten zu einer Trichter-Stufe (Kapitel 0): Wert und Anteil an der ersten Stufe, Erklärtext,
// Hinweis bei Schraffur. Fehlt die Kennzahl im Export, steht das da — keine erfundene Null.
export function detailTextStufe(w) {
  const e = w || {};
  if (e.wert === null || e.wert === undefined) return { titel: String(e.name || e.id || ""), zeilen: ["Kennzahl im Export nicht vorhanden"] };
  // Ohne Basis (erste Stufe) oder ohne Anteil (keine Teilmenge der ersten Stufe) steht nur die Zahl.
  const zeilen = [e.basis === null || e.basis === undefined || e.ohne_anteil
    ? formatZahl(e.wert)
    : [formatZahl(e.wert), "von", formatZahl(e.basis), e.basisName, `(${formatProzent(e.anteil || 0)})`].filter(Boolean).join(" ")];
  if (e.erklaerung) zeilen.push(e.erklaerung);
  if (e.muster === "schraffur") zeilen.push("nicht von Hand geprüft (schraffiert)");
  return { titel: String(e.name || e.id || ""), zeilen };
}

// Anker der Datenbasis-Zeile eines Fachkapitels auf den passenden Schritt in Kapitel 0 — nur, wenn
// Kapitel 0 überhaupt sichtbar ist (sonst zeigte der Link ins Leere).
export function datenbasisLink(kapitel, index) {
  const k = kapitel || {};
  if (!k.datenbasis || !k.datenbasis_schritt) return null;
  if (!(index || []).some((e) => e.id === "datenbasis")) return null;
  return `#s-datenbasis-${k.datenbasis_schritt}`;
}

// Zustand des Detailkastens. Schweben zeigt ihn flüchtig, ein Klick stellt ihn fest; festgestellt
// gewinnt: Schweben und Verlassen ändern dann nichts mehr, denn der Weg des Zeigers zum Kasten führt
// (bei der Stadtteilkarte zwangsläufig) über Nachbar-Einheiten. Erst ein Klick auf eine andere Einheit,
// Schließen oder ein Schrittwechsel lösen die Feststellung.
export const DETAIL_ZU = { id: null, sichtbar: false, fest: false };
export function detailZustand(zustand, ereignis, id = null) {
  const z = zustand || DETAIL_ZU;
  switch (ereignis) {
    case "schweben": return z.fest ? z : { id, sichtbar: true, fest: false };
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

// ---- Herkunftspfad (Spec 2026-09-27 Herkunftspfad §4) ----------------------------------------------

// Welche Datei aus site/daten/herkunft/ ein Kontext braucht. Einheiten (Stadtteil, Straße, Hex) und das
// Ausschluss-Segment haben keinen Pfad.
export const HERKUNFT_DATEI = {
  segment: { stellung: "stellung", gruppe: "gruppe", niveau: "niveau", besitz: "besitz", gewerbe: "gewerbe" },
  regel: { besitz: "besitz" },
  kreis: { stellung: "berufe", gruppe: "berufe", niveau: "berufe", besitz: "eigentuemer", gewerbe: "rubriken" },
};
export function herkunftDatei(kontext) {
  const k = kontext || {};
  return (HERKUNFT_DATEI[k.art] || {})[k.daten] || null;
}

// Beschriftungen der Klassen — dieselben Tabellen, die die Kapitel über `wie:` nutzen (ansicht.js), keine
// eigene Kopie; nur die Betriebsform (art) hat auf der Site sonst keine Tabelle (Schlüssel wie pipeline/lib/gewerbe.py).
const namen = (tabelle) => Object.fromEntries(Object.entries(tabelle).map(([k, v]) => [k, v[0]]));
export const KLASSEN = {
  stellung: { ...namen(STELLUNG), unbestimmt: "unbestimmt" },
  besitz: { ...namen(BESITZ), gemischt: KATEGORIEN.gemischt },
  gewerbe: GEWERBE_TEXT,
  art: { handwerk: "Handwerk", handel: "Handel", industrie: "Industrie", dienstleistung: "Dienstleistung", gastgewerbe: "Gastgewerbe", freier_beruf: "Freier Beruf", sonstige: "Sonstige" },
};
const klasseText = (daten, roh) => (KLASSEN[daten === "gruppe" || daten === "niveau" ? "stellung" : daten] || {})[roh] || roh;

// Belegtexte je Datenkern: Regel und Kuratierungstabelle in Worten.
export const BELEG = {
  stellung: "Stellung nach Berufszählung 1933 / AVG 1911 (docs/stellung.md). Tabelle: kuratierung/berufe.csv, Spalte stellung.",
  gruppe: "Hauptgruppe = OhdAB-Gattung (KldB 2010, 2-stellig), kuratierung/hauptgruppen.csv. Tabelle: kuratierung/berufe.csv, Spalte ohdab_id.",
  niveau: "Anforderungsniveau der OhdAB je Norm; „unsicher“ bei Betriebsangaben statt Beruf. Tabelle: kuratierung/berufe.csv.",
  besitz: "Klasse je Eigentümer von Hand (kuratierung/eigentuemer.csv); Personen ohne Firmenname per Regel Privatperson. Spannen des Häuserbuchs gelten je Straßenseite.",
  gewerbe: "Branche und Betriebsform je Rubrik nach docs/gewerbe.md. Tabelle: kuratierung/gewerbe.csv, Spalten gruppe, art, geprueft.",
};

// Quellmarken in fester Reihenfolge; nur mit Zahl > 0. Der Nenner ist die Zahl, die die Stufe nennt
// (Nennungen, Häuser, Betriebe) — nicht die Summe der Quellen: Nennungen ohne Quelle (Beruf ungeprüft)
// erscheinen als eigene Marke „ohne“, statt die übrigen Anteile aufzublähen.
const QUELLEN = ["hand", "vorschlag", "claude", "regel"];
function marken(quelle, basis) {
  const q = quelle || {};
  const summe = QUELLEN.reduce((s, a) => s + (q[a] || 0), 0);
  const nenner = basis > 0 ? basis : summe;
  const anteil = (z) => (nenner ? Math.round((z / nenner) * 10000) / 10000 : 0);
  const m = QUELLEN.filter((a) => (q[a] || 0) > 0).map((a) => ({ art: a, anteil: anteil(q[a]), zahl: q[a] }));
  if (nenner > summe) m.push({ art: "ohne", anteil: anteil(nenner - summe), zahl: nenner - summe });
  return m;
}

// Summe mehrerer Klassen (Gruppe aus mehreren Rohwerten): Zähler addieren, Quellen addieren, Top-Listen
// zusammenlegen und neu sortieren. Fehlende Klassen zählen 0.
function summeKlassen(herkunft, aus) {
  const k = { schreibweisen: 0, normen: 0, nennungen: 0, eigentuemer: 0, zeilen: 0, haeuser: 0, rubriken: 0, betriebe: 0, quelle: {}, top: [] };
  for (const roh of aus || []) {
    const h = (herkunft || {})[roh];
    if (!h) continue;
    for (const f of ["schreibweisen", "normen", "nennungen", "eigentuemer", "zeilen", "haeuser", "rubriken", "betriebe"]) k[f] += h[f] || 0;
    for (const [a, z] of Object.entries(h.quelle || {})) k.quelle[a] = (k.quelle[a] || 0) + z;
    k.top.push(...(h.top || []));
  }
  k.top.sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])));
  return k;
}

const gruppeVon = (ansicht, roh) => (ansicht?.gruppen || []).find((g) => Array.isArray(g.aus) && g.aus.includes(roh));

// Die Brotkrumen-Kette für einen Kontext; zusätzlich `beispiele` (Top-3-Schreibweisen), `zusatz`
// (Eigentümer: Zeilen → Häuser) und `hinweis` (Regel). Leer, wenn die Datei den Schlüssel nicht kennt.
export function herkunftPfad(kontext, herkunft, ansicht) {
  const k = kontext || {};
  const pfad = [];
  if (!herkunft) return pfad;
  if (k.art === "segment" && k.gruppe) {
    const s = summeKlassen(herkunft, k.gruppe.aus);
    const klassen = k.gruppe.aus.map((r) => klasseText(k.daten, r)).join(", ");
    if (k.daten === "besitz") {
      // `eigentuemer` zählt nur identifizierte Eigentümer; Häuser per Regel (Person ohne Firmenname) haben keinen.
      pfad.push({ label: "Buch", wert: `${formatZahl(s.zeilen)} Zeilen im Häuserbuch` }, { label: "Eigentümer", wert: `${formatZahl(s.eigentuemer)} identifiziert` },
        { label: "Klasse", wert: klassen, marken: marken(s.quelle, s.haeuser) }, { label: "Gruppe", wert: k.gruppe.name });
      if (s.quelle.regel > 0) pfad.hinweis = `${formatZahl(s.quelle.regel)} der ${formatZahl(s.haeuser)} Häuser per Regel, ohne belegbare Identität des Eigentümers`;
    } else if (k.daten === "gewerbe") {
      pfad.push({ label: "Buch", wert: `${formatZahl(s.rubriken)} Rubriken` }, { label: "Branche", wert: klassen, marken: marken(s.quelle, s.betriebe) }, { label: "Gruppe", wert: k.gruppe.name });
    } else {
      const stufe = k.daten === "gruppe" ? "Hauptgruppe" : k.daten === "niveau" ? "Niveau" : "Stellung";
      pfad.push({ label: "Buch", wert: `${formatZahl(s.schreibweisen)} Schreibweisen` }, { label: "OhdAB", wert: `${formatZahl(s.normen)} Berufe` },
        { label: stufe, wert: klassen, marken: marken(s.quelle, s.nennungen) }, { label: "Gruppe", wert: k.gruppe.name });
    }
    pfad.beispiele = s.top.slice(0, 3).map((t) => [t[0], t[1]]);
    return pfad;
  }
  if (k.art === "regel" && k.gruppe) {
    const s = summeKlassen(herkunft, ["privatperson"]);
    pfad.push({ label: "Buch", wert: "Person ohne Firmenname" }, { label: "Regel", wert: "→ Privatperson", marken: marken({ regel: s.quelle.regel || 0 }, s.quelle.regel || 0) }, { label: "Gruppe", wert: k.gruppe.name });
    pfad.hinweis = "keine Handprüfung, keine Identität";
    pfad.beispiele = (herkunft.privatperson?.regel_beispiele || []).slice(0, 3);
    return pfad;
  }
  if (k.art === "kreis") {
    const h = herkunft[k.id];
    if (!h) return pfad;
    if (k.daten === "besitz") {
      const g = gruppeVon(ansicht, h.kategorie);
      pfad.push({ label: "Buch", wert: `${formatZahl(h.schreibweisen_gesamt)} Schreibweisen` }, { label: "Eigentümer", wert: k.id },
        { label: "Klasse", wert: klasseText("besitz", h.kategorie), marken: marken({ hand: h.haeuser }, h.haeuser) }, { label: "Gruppe", wert: g ? g.name : klasseText("besitz", h.kategorie) });
      const dazu = h.haeuser - h.zeilen;
      if (dazu > 0) pfad.zusatz = `${formatZahl(h.zeilen)} Zeilen im Häuserbuch, ${formatZahl(dazu)} Häuser dazu über Hausnummernspannen und gleiche Nummern`;
      pfad.beispiele = (h.schreibweisen || []).slice(0, 3);
      return pfad;
    }
    if (k.daten === "gewerbe") {
      const g = gruppeVon(ansicht, h.gruppe);
      pfad.push({ label: "Buch", wert: k.id }, { label: "Branche", wert: `${klasseText("gewerbe", h.gruppe)} · ${klasseText("art", h.art)}`, marken: marken({ [h.quelle]: h.betriebe }, h.betriebe) },
        { label: "Gruppe", wert: g ? g.name : klasseText("gewerbe", h.gruppe) });
      return pfad;
    }
    const g = gruppeVon(ansicht, h.stellung);
    pfad.push({ label: "Buch", wert: `${formatZahl(h.schreibweisen_gesamt ?? (h.schreibweisen || []).length)} Schreibweisen` }, { label: "OhdAB", wert: h.norm },
      { label: "Stellung", wert: klasseText("stellung", h.stellung), marken: marken(h.quelle, h.nennungen) },
      { label: "Gruppe", wert: g ? g.name : klasseText("stellung", h.stellung) });
    pfad.beispiele = (h.schreibweisen || []).slice(0, 3);
    return pfad;
  }
  return pfad;
}

// Belegtabelle für den festgestellten Kasten: Kopf, höchstens zehn Zeilen, Gesamtzahl, Hinweis.
export function herkunftTabelle(kontext, herkunft, ansicht) {
  const k = kontext || {};
  if (!herkunft || !["segment", "kreis", "regel"].includes(k.art)) return null;
  if (k.art === "segment" && k.gruppe) {
    const s = summeKlassen(herkunft, k.gruppe.aus);
    if (k.daten === "besitz") {
      const regel = s.quelle.regel > 0 ? `${formatZahl(s.quelle.regel)} der ${formatZahl(s.haeuser)} Häuser: Person ohne Firmenname, per Regel Privatperson, keine Identität. ` : "";
      return { kopf: ["Eigentümer (identifiziert)", "Häuser"], zeilen: s.top.slice(0, 10).map((t) => [t[0], t[1]]), gesamt: s.eigentuemer, hinweis: regel + BELEG.besitz };
    }
    if (k.daten === "gewerbe") return { kopf: ["Rubrik", "Betriebe", "Betriebsform", "Quelle"], zeilen: s.top.slice(0, 10).map((t) => [t[0], t[1], klasseText("art", t[2]), t[3]]), gesamt: s.rubriken, hinweis: BELEG.gewerbe };
    return { kopf: ["Schreibweise", "Nennungen", "OhdAB", "Quelle"], zeilen: s.top.slice(0, 10), gesamt: s.schreibweisen, hinweis: BELEG[k.daten] || BELEG.stellung };
  }
  if (k.art === "regel") {
    const h = herkunft.privatperson || {};
    return { kopf: ["Schreibweise im Buch", "Zeilen"], zeilen: (h.regel_beispiele || []).slice(0, 10), gesamt: h.quelle?.regel || 0,
      hinweis: "Der Eigentümer steht als Person ohne Firmennamen im Häuserbuch; die Klasse folgt aus der Regel, nicht aus einer Prüfung des Einzelfalls. Ausnahmen: Firmenmuster wie „Gebr.“; „gen.“-Hofnamen zählen als Personen. Export: besitz_pruefung = regel." };
  }
  const h = herkunft[k.id];
  if (!h) return null;
  if (k.daten === "besitz") {
    return { kopf: ["Schreibweise im Buch", "Zeilen", "Quelle"], zeilen: (h.schreibweisen || []).slice(0, 10).map((t) => [t[0], t[1], "hand"]), gesamt: h.schreibweisen_gesamt,
      hinweis: h.haeuser > h.zeilen ? `${formatZahl(h.zeilen)} Zeilen ergeben ${formatZahl(h.haeuser)} Häuser, weil Spannen („2–84“) einmal je Straßenseite stehen. ${BELEG.besitz}` : BELEG.besitz,
      seite: h.seite || "" };
  }
  if (k.daten === "gewerbe") return { kopf: ["Rubrik", "Betriebe", "Betriebsform", "Quelle"], zeilen: [[k.id, h.betriebe, klasseText("art", h.art), h.quelle]], gesamt: 1, hinweis: BELEG.gewerbe };
  return { kopf: ["Schreibweise", "Nennungen", "OhdAB", "Quelle"], zeilen: (h.schreibweisen || []).slice(0, 10).map((t) => [t[0], t[1], h.norm, t[2] || ""]),
    gesamt: h.schreibweisen_gesamt ?? (h.schreibweisen || []).length, hinweis: BELEG[k.daten] || BELEG.stellung };
}

// Kartenziel des Kastens (Kartensymbol hinter der Zahlenzeile): Einzelobjekte (Norm, Eigentümer, Rubrik)
// führen in die Suche, Stadtteile auf die Karte; Segmente, Straßen, Hexfelder haben keins.
// Kontext eines Kreises der Punktkarte (Spec Bergbau §4): Hexfeld → Gruppe, Feld, Stadtteil, Themenlink mit
// dieser Klasse; Haus → Gesellschaft und Eigentümersuche; unbekannte Gesellschaft ohne Link.
export function punktKontext(id, ansicht, punkte, hexe) {
  const k = { art: "punkt", id, daten: ansicht.daten, ebene: ansicht.ebene, gruppe: null, klasse: null, eigentuemer: null, titel: String(id) };
  const p = punkte || {};
  if (ansicht.punkte && ansicht.punkte.zustand === "haeuser") {
    const haus = (p.haeuser || []).find((h) => h.id === id);
    const ges = haus && (p.gesellschaften || []).find((g) => g.id === haus.eig);
    if (ges) { k.titel = ges.name; if (ges.id !== "unbekannt") k.eigentuemer = ges.name; }
    return k;
  }
  const [feld, klasse] = String(id).split("|");
  const g = (ansicht.gruppen || []).find((x) => x.aus[0] === klasse);
  if (!g) return k;
  const st = (hexe || []).find((h) => h.id === feld);
  k.klasse = klasse;
  k.titel = `${g.name} · Feld ${feld}${st && st.stadtteil ? ` (${st.stadtteil})` : ""}`;
  return k;
}

export function herkunftLink(kontext) {
  const k = kontext || {};
  if (!k.id) return null;
  if (k.art === "punkt") {
    if (k.klasse) return `karte.html?thema=bergbau&klassen=${encodeURIComponent(k.klasse)}`;
    return k.eigentuemer ? `karte.html?eigentuemer=${encodeURIComponent(k.eigentuemer)}` : null;
  }
  if (k.art === "einheit") return k.ebene === "stadtteil" ? `karte.html?stadtteil=${encodeURIComponent(k.id)}` : null;
  if (k.art !== "kreis") return null;
  if (k.daten === "besitz") return `karte.html?eigentuemer=${encodeURIComponent(k.id)}`;
  if (k.daten === "gewerbe") return `karte.html?q=${encodeURIComponent(k.id)}`;
  return `karte.html?ohdab=${encodeURIComponent(k.id)}`;
}

// Nach dem Nachladen wird der Kasten neu gezeichnet, wenn er sichtbar ist und das, was er gerade zeigt,
// genau diese Datei braucht — dieselbe Einheit oder eine Nachbar-Einheit derselben Datei (Kreis A → Kreis B
// während des Ladens). Braucht er eine andere oder keine, bleibt er, wie er ist: kein Pfad aus der falschen Datei.
export const herkunftAktuell = (detail, name, dateiAktuell) => !!detail && detail.sichtbar === true && !!name && dateiAktuell === name;
