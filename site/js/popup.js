import { EBENEN, PRAEZISION, DIGIBIB_WERK } from "./konfig.js";
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

export function popupHtml(eig, eintraege, kompakt) {
  const max = kompakt ? 3 : 12;
  const zeilen = eintraege.slice(0, max).map((e) => `<div class="pname" data-eintrag="${esc(e.id)}">${nameZeile(e)}</div>`);
  // Kompakt (Popup) verweist immer auf die Hausansicht — auch bei genau drei Namen, damit „alle
  // im Detail“ dort landet, wo die vollen Angaben (Beruf, Etage, Quelle) stehen.
  if (kompakt || eintraege.length > max) zeilen.push(`<div class="pmehr" data-mehr="1">alle ${eintraege.length} im Detail ›</div>`);
  return `<div class="popup-kopf"><b>${esc(heutigeAdresse(eig))}</b>` +
    (eig.strasse_heute ? `<div class="hist">historische Adresse: ${esc(eig.historisch)}</div>` : "") +
    `<div class="praez praez-${esc(eig.stufe)}">${esc(praezisionText(eig.stufe))}</div>` +
    `<div class="zaehler">${esc(zaehlerText(eig))}</div></div>` +
    `<div class="popup-namen">${zeilen.join("")}</div>`;
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
