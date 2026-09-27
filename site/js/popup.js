import { EBENEN, PRAEZISION, DIGIBIB_WERK, FARBEN } from "./konfig.js";
import { KATEGORIEN, NIVEAUS } from "./kategorien.js";

// Statustexte der Berufsangabe (mehrere, durch ";" getrennt, einzeln übersetzt und mit ", " verbunden).
const STATUS_TEXT = { ruhestand: "Ruhestand", invalide: "Invalide", witwe: "Witwe", gewerbe: "Gewerbebetrieb" };
function statusText(status) {
  return status.split(";").map((s) => STATUS_TEXT[s] || s).join(", ");
}

export function esc(t) {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export function praezisionText(stufe) { return PRAEZISION[stufe] || stufe; }

// Link auf das Seitenbild in der DigiBib; `bild` ist die Bildnummer aus daten/faksimile.json.
// Ohne Bildnummer (Seite im Digitalisat nicht vorhanden) gibt es keinen Link.
export function faksimileUrl(bild) { return bild ? `${DIGIBIB_WERK}${bild}/` : null; }

function quelleHtml(seite, bild) {
  const url = faksimileUrl(bild);
  const link = url ? `<a href="${url}" target="_blank" rel="noopener">Faksimile in der DigiBib</a>`
                   : `<span class="kein-bild">im Digitalisat nicht vorhanden</span>`;
  return `<div class="quelle">Seite ${esc(seite)} · ${link}</div>`;
}

const BESITZ_HERKUNFT = { spanne: "Hausnummernspanne", nummer: "gleiche Hausnummer, andere Schreibung" };
const FLAGTEXT = { nummer_unsicher: "Hausnummer unsicher (Straße neu gezählt)", zeitlich_abweichend: "Straßenname zeitlich abweichend belegt", mehrdeutig: "Zuordnung mehrdeutig" };

export function heutigeAdresse(eig) {
  if (!eig.strasse_heute) return `${eig.historisch} (Stadtplan 1935)`;
  return `${eig.strasse_heute} ${eig.hausnr || ""}`.trim() + (eig.stadtteil ? `, ${eig.stadtteil}` : "");
}

function zaehlerText(eig) {
  return ["I", "II", "III"].filter((t) => eig[`n_${t}`] > 0).map((t) => `${eig[`n_${t}`]} ${EBENEN[t]}`).join(" · ");
}

function nameZeile(e, mitBeruf = true) {
  const name = e.firma && e.teil === "III" ? e.firma : [e.name, e.vorname].filter(Boolean).join(", ");
  // Kompakt (Popup): bei geprüfter Zuordnung nur „Rohtext → Norm“, ohne Niveau/Status (steht in der
  // Hausansicht, siehe eintragHtml) — sonst der rohe Beruf wie im Buch.
  const beruf = e.beruf_norm ? `${e.beruf} → ${e.beruf_norm}` : e.beruf;
  const rest = mitBeruf ? [beruf, e.stand].filter(Boolean).join(", ") : "";
  return `<b>${esc(name)}</b>${rest ? ` · ${esc(rest)}` : ""}${e.etage ? ` <span class="etage">${esc(e.etage)}</span>` : ""}`;
}

// ---- Popup: Visitenkarte des Hauses (Spec 2026-09-28 §2/§3). Lesestoff steht in hausHtml. ----
const TEILE = ["I", "II", "III"];
const PRAEZ_KURZ = { strasse: "nur straßengenau", stadtplan: "Punkt vom Stadtplan 1935", unbekannt: "Präzision unbekannt" };
const TOOLTIP_ROH = "Schreibung im Buch, Beruf noch nicht zugeordnet";

function personName(e) { return [e.name, e.vorname].filter(Boolean).join(", "); }

function popupName(e) {
  if (e.teil === "II") return e.eigentuemer_kanon || e.firma || personName(e);
  return (e.teil === "III" ? e.firma : "") || personName(e) || e.firma || "";
}

// Zusatz hinter dem Namen, bereits als HTML: Einwohner Beruf (nur Norm; sonst Buchschreibung kursiv)
// und Stand; Eigentümer Besitzklasse (per Regel mit Vermerk); Gewerbe Buchrubrik.
function popupZusatz(e) {
  if (e.teil === "II") {
    if (e.pruefung === "regel") return `${esc(KATEGORIEN.privatperson)} (Regel)`;
    return e.kategorie ? esc(KATEGORIEN[e.kategorie] || e.kategorie) : "";
  }
  if (e.teil === "III") return esc(e.rubrik || "");
  const beruf = e.beruf_norm ? esc(e.beruf_norm) : e.beruf ? `<i title="${TOOLTIP_ROH}">${esc(e.beruf)}</i>` : "";
  return [beruf, esc(e.stand || "")].filter(Boolean).join(", ");
}

export function popupZeile(e) {
  const z = popupZusatz(e);
  return `<div class="z" data-eintrag="${esc(e.id)}"><b>${esc(popupName(e))}</b>${z ? ` <span class="n">· ${z}</span>` : ""}</div>`;
}

function teilHtml(teil, liste, max, hervor) {
  if (!liste.length) return "";
  const zeilen = liste.slice(0, max).map(popupZeile);
  const rest = liste.length - max;
  if (rest > 0) zeilen.push(`<div class="weitere">und ${rest} weitere ${rest === 1 ? "Zeile" : "Zeilen"}</div>`);
  const kopf = liste.length > 1 ? `${EBENEN[teil]} · ${liste.length}` : EBENEN[teil];
  const attr = hervor ? ` class="teil hervor" style="--f:${FARBEN[teil]}"` : ` class="teil"`;
  return `<div${attr}><h4>${kopf}</h4>${zeilen.join("")}</div>`;
}

// ebenen: aktive Ebenen der Karte; bei genau 1 oder 2 werden deren Teile hervorgehoben (§3).
export function popupHtml(eig, eintraege, kompakt, ebenen = TEILE) {
  const max = kompakt ? 2 : 4;
  const hervor = new Set(ebenen.length >= 1 && ebenen.length <= 2 ? ebenen : []);
  const praez = PRAEZ_KURZ[eig.stufe] ? `<span class="praez-${esc(eig.stufe)}">${PRAEZ_KURZ[eig.stufe]}</span>` : "";
  const kenn = [praez, esc(zaehlerText(eig))].filter(Boolean).join(" · ");
  const teile = TEILE.map((t) => teilHtml(t, eintraege.filter((e) => e.teil === t), max, hervor.has(t))).join("");
  return `<div class="popup-kopf"><b>${esc(heutigeAdresse(eig))}</b>` +
    (eig.strasse_heute ? `<div class="hist">${esc(eig.historisch)} im Buch</div>` : "") +
    `<div class="kenn">${kenn}</div></div>${teile}` +
    `<div class="pmehr" data-mehr="1">Haus im Detail ›</div>`;
}

// Hausansicht: die Namenszeile ohne Beruf/Stand, die stehen als Felder darunter (keine Dopplung).
function eintragHtml(e, faksimile) {
  const felder = [["Beruf", e.beruf_norm ? `${e.beruf} → ${e.beruf_norm} · ${NIVEAUS[e.niveau] || e.niveau}${e.status ? " · " + statusText(e.status) : ""}` : e.beruf], ["Etage laut Buch", e.etage], ["Stand", e.stand],
    ["Bezugsperson", [e.bezug_vorname, e.bezug_beruf].filter(Boolean).join(", ")], ["Firma", e.firma],
    ["Eigentümer", e.eigentuemer],
    // Handgeprüft: kanonischer Name und Klasse. Per Regel (Person ohne Firmenname → Privatperson): nur die
    // Klasse, mit der Regel als Herkunft — ohne Namen, denn die Identität ist nicht belegt.
    ["Zugeordnet", e.eigentuemer_kanon ? `${e.eigentuemer_kanon} · ${KATEGORIEN[e.kategorie] || e.kategorie}`
      : e.pruefung === "regel" ? `${KATEGORIEN[e.kategorie] || e.kategorie} (Regel: Person ohne Firmenname → Privatperson, keine Handprüfung)` : ""],
    ["Verwalter", e.verwalter], ["Wohnort", e.wohnort]]
    .filter(([, w]) => w).map(([k, w]) => `<div><span class="k">${k}</span> ${esc(w)}</div>`).join("");
  const flags = (e.flags || []).map((f) => `<div class="flag">${esc(FLAGTEXT[f] || f)}</div>`).join("");
  return `<div class="eintrag" id="e-${esc(e.id)}"><div class="ename">${nameZeile(e, false)}</div>${felder}${flags}` +
    quelleHtml(e.seite, faksimile ? faksimile[e.seite] : null) + `</div>`;
}

// faksimile: Seite → Bildnummer (daten/faksimile.json); ohne Tabelle keine Links.
export function hausHtml(eig, eintraege, faksimile = null) {
  const gruppen = ["I", "II", "III"].map((t) => {
    const l = eintraege.filter((e) => e.teil === t);
    return l.length ? `<h3>${EBENEN[t]} (${l.length})</h3>${l.map((e) => eintragHtml(e, faksimile)).join("")}` : "";
  }).join("");
  return `<div class="haus-kopf"><h2>${esc(heutigeAdresse(eig))}</h2>` +
    (eig.strasse_heute ? `<div class="hist">historische Adresse: ${esc(eig.historisch)}</div>` : "") +
    `<div class="praez praez-${esc(eig.stufe)}">${esc(praezisionText(eig.stufe))}</div>` +
    (eig.nummer_unsicher === "ja" ? `<div class="flag">${FLAGTEXT.nummer_unsicher}</div>` : "") +
    // Besitzklasse aus einer Hausnummernspanne des Häuserbuchs („2—84 E. …“) oder von der Teil-II-Zeile
    // eines anderen Adressobjekts derselben Nummer: die Adresse hat keine eigene Teil-II-Zeile, die
    // Herkunft muss deshalb hier stehen, sonst wäre die Klasse nicht nachprüfbar.
    (BESITZ_HERKUNFT[eig.besitz_quelle] ? `<div class="hist">Eigentümer laut Häuserbuch (${BESITZ_HERKUNFT[eig.besitz_quelle]}): ${esc(eig.besitz_spanne)} · ${esc(KATEGORIEN[eig.besitz] || eig.besitz)}</div>` : "") +
    `</div>${gruppen}`;
}

export function trefferzeileHtml(t) {
  // t = { adressId, titel, untertitel, stufe, n, eintragId? }
  const kennText = t.stufe === "stadtplan" ? "Stadtplan 1935" : t.stufe === "unbekannt" ? "Präzision unbekannt" : "nur Straße";
  const kenn = t.stufe === "haus" ? "" : `<span class="kenn">${kennText}</span>`;
  return `<div class="treffer" data-adresse="${esc(t.adressId)}"${t.eintragId ? ` data-eintrag="${esc(t.eintragId)}"` : ""}>` +
    `<b>${esc(t.titel)}</b>${kenn}<small>${esc(t.untertitel)}</small></div>`;
}
