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
  // Hausansicht, siehe eintragHtml) — sonst der rohe Beruf wie im Adressbuch.
  const beruf = e.beruf_norm ? `${e.beruf} → ${e.beruf_norm}` : e.beruf;
  const rest = mitBeruf ? [beruf, e.stand].filter(Boolean).join(", ") : "";
  return `<b>${esc(name)}</b>${rest ? ` · ${esc(rest)}` : ""}${e.etage ? ` <span class="etage">${esc(e.etage)}</span>` : ""}`;
}

// ---- Popup: Visitenkarte des Hauses (Spec 2026-09-28 §2/§3). Lesestoff steht in hausHtml. ----
const TEILE = ["I", "II", "III"];
const PRAEZ_KURZ = { strasse: "nur straßengenau", stadtplan: "Punkt vom Stadtplan 1935", unbekannt: "Präzision unbekannt" };
const TOOLTIP_ROH = "Schreibung im Adressbuch, Beruf noch nicht zugeordnet";

function personName(e) { return [e.name, e.vorname].filter(Boolean).join(", "); }

// Teil III: das Firmenfeld endet im Datenpaket auf „, <Rubrik>“ — die Rubrik steht als Zusatz, also hier abschneiden.
function firmaOhneRubrik(e) {
  const suffix = e.rubrik ? `, ${e.rubrik}` : "";
  return suffix && e.firma && e.firma.endsWith(suffix) ? e.firma.slice(0, -suffix.length) : e.firma || "";
}

function popupName(e) {
  if (e.teil === "II") return e.eigentuemer_kanon || e.firma || personName(e);
  return (e.teil === "III" ? firmaOhneRubrik(e) : "") || personName(e) || e.firma || "";
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

// Geprüfter Eigentümer als Knopf (Spec Eigentümer-Vergleich §7): app.js hängt den Klick an (alle Häuser / zum Vergleich).
function eigKnopf(name) { return `<button class="eiglink" data-eigentuemer="${esc(name)}">${esc(name)}</button>`; }

export function popupZeile(e) {
  const z = popupZusatz(e);
  const name = e.teil === "II" && e.eigentuemer_kanon ? eigKnopf(e.eigentuemer_kanon) : esc(popupName(e));
  return `<div class="z" data-eintrag="${esc(e.id)}"><b>${name}</b>${z ? ` <span class="n">· ${z}</span>` : ""}</div>`;
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
    (eig.strasse_heute ? `<div class="hist">${esc(eig.historisch)} im Adressbuch</div>` : "") +
    `<div class="kennzeile">${kenn}</div></div>${teile}` +
    `<div class="pmehr" data-mehr="1">Haus im Detail ›</div>`;
}

// Hausansicht: die Namenszeile ohne Beruf/Stand, die stehen als Felder darunter (keine Dopplung).
function eintragHtml(e, faksimile) {
  const felder = [["Beruf", e.beruf_norm ? `${e.beruf} → ${e.beruf_norm} · ${NIVEAUS[e.niveau] || e.niveau}${e.status ? " · " + statusText(e.status) : ""}` : e.beruf], ["Etage laut Adressbuch", e.etage], ["Stand", e.stand],
    ["Bezugsperson", [e.bezug_vorname, e.bezug_beruf].filter(Boolean).join(", ")], ["Firma", e.firma],
    ["Eigentümer", e.eigentuemer],
    // Handgeprüft: kanonischer Name und Klasse. Per Regel (Person ohne Firmenname → Privatperson): nur die
    // Klasse, mit der Regel als Herkunft — ohne Namen, denn die Identität ist nicht belegt.
    ["Zugeordnet", e.eigentuemer_kanon ? `${eigKnopf(e.eigentuemer_kanon)} · ${esc(KATEGORIEN[e.kategorie] || e.kategorie)}`
      : e.pruefung === "regel" ? esc(`${KATEGORIEN[e.kategorie] || e.kategorie} (Regel: Person ohne Firmenname → Privatperson, keine Handprüfung)`) : "", true],
    ["Verwalter", e.verwalter], ["Wohnort", e.wohnort]]
    .filter(([, w]) => w).map(([k, w, roh]) => `<div><span class="k">${k}</span> ${roh ? w : esc(w)}</div>`).join("");
  const flags = (e.flags || []).map((f) => `<div class="flag">${esc(FLAGTEXT[f] || f)}</div>`).join("");
  return `<div class="eintrag" id="e-${esc(e.id)}"><div class="ename">${nameZeile(e, false)}</div>${felder}${flags}` +
    quelleHtml(e.seite, faksimile ? faksimile[e.seite] : null) + `</div>`;
}

// faksimile: Seite → Bildnummer (daten/faksimile.json); ohne Tabelle keine Links.
// reiter: "alle" oder ein Teil (I/II/III) — zeigt nur dessen Einträge; ein Teil ohne Einträge fällt auf
// "alle" zurück. Die Reiterzeile erscheint nur, wenn das Haus Einträge in mehr als einem Teil hat.
export function hausHtml(eig, eintraege, faksimile = null, reiter = "alle") {
  const je = new Map(TEILE.map((t) => [t, eintraege.filter((e) => e.teil === t)]));
  const vorhanden = TEILE.filter((t) => je.get(t).length);
  const aktiv = vorhanden.includes(reiter) ? reiter : "alle";
  const reiterHtml = vorhanden.length > 1
    ? `<div class="reiter">` + [["alle", `Alle ${eintraege.length}`], ...vorhanden.map((t) => [t, `${EBENEN[t]} ${je.get(t).length}`])]
        .map(([k, text]) => `<button data-teil="${k}" aria-pressed="${k === aktiv}">${text}</button>`).join("") + `</div>`
    : "";
  const gruppen = vorhanden.filter((t) => aktiv === "alle" || t === aktiv).map((t) =>
    `<h3>${EBENEN[t]} (${je.get(t).length})</h3>${je.get(t).map((e) => eintragHtml(e, faksimile)).join("")}`).join("");
  return `<div class="haus-kopf"><h2>${esc(heutigeAdresse(eig))}</h2>` +
    (eig.strasse_heute ? `<div class="hist">historische Adresse: ${esc(eig.historisch)}</div>` : "") +
    `<div class="praez praez-${esc(eig.stufe)}">${esc(praezisionText(eig.stufe))}</div>` +
    (eig.nummer_unsicher === "ja" ? `<div class="flag">${FLAGTEXT.nummer_unsicher}</div>` : "") +
    // Besitzklasse aus einer Hausnummernspanne des Adressbuchs (Teil II) („2—84 E. …“) oder von der Teil-II-Zeile
    // eines anderen Adressobjekts derselben Nummer: die Adresse hat keine eigene Teil-II-Zeile, die
    // Herkunft muss deshalb hier stehen, sonst wäre die Klasse nicht nachprüfbar.
    (BESITZ_HERKUNFT[eig.besitz_quelle] ? `<div class="hist">Eigentümer laut Adressbuch (${BESITZ_HERKUNFT[eig.besitz_quelle]}): ${esc(eig.besitz_spanne)} · ${esc(KATEGORIEN[eig.besitz] || eig.besitz)}</div>` : "") +
    `</div>${reiterHtml}${gruppen}`;
}

export function trefferzeileHtml(t) {
  // t = { adressId, titel, untertitel, stufe, n, eintragId?, farbe?, mehrfach? } — farbe/mehrfach beim Eigentümer-Vergleich
  const kennText = t.stufe === "stadtplan" ? "Stadtplan 1935" : t.stufe === "unbekannt" ? "Präzision unbekannt" : "nur Straße";
  const kenn = t.stufe === "haus" ? "" : `<span class="kenn">${kennText}</span>`;
  const punkt = t.farbe ? `<span class="punkt" style="background:${esc(t.farbe)}"></span>` : "";
  return `<div class="treffer${t.mehrfach ? " mehrfach" : ""}" data-adresse="${esc(t.adressId)}"${t.eintragId ? ` data-eintrag="${esc(t.eintragId)}"` : ""}>` +
    `${punkt}<b>${esc(t.titel)}</b>${kenn}<small>${esc(t.untertitel)}</small></div>`;
}
