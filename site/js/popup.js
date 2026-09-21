import { EBENEN, PRAEZISION, DES_PROJEKT } from "./konfig.js";

export function esc(t) {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export function praezisionText(stufe) { return PRAEZISION[stufe] || stufe; }

// Bis der DES-Spike eine seitengenaue URL liefert, führt der Link zur Projektseite; die Seite
// steht daneben, damit man sie dort aufschlagen kann.
export function faksimileUrl(seite) { return DES_PROJEKT + "#" + encodeURIComponent(seite || ""); }

const FLAGTEXT = { nummer_unsicher: "Hausnummer unsicher (Straße neu gezählt)", zeitlich_abweichend: "Straßenname zeitlich abweichend belegt", mehrdeutig: "Zuordnung mehrdeutig" };

export function heutigeAdresse(eig) {
  if (!eig.strasse_heute) return `${eig.historisch} (Stadtplan 1935)`;
  return `${eig.strasse_heute} ${eig.hausnr || ""}`.trim() + (eig.stadtteil ? `, ${eig.stadtteil}` : "");
}

function zaehlerText(eig) {
  return ["I", "II", "III"].filter((t) => eig[`n_${t}`] > 0).map((t) => `${eig[`n_${t}`]} ${EBENEN[t]}`).join(" · ");
}

function nameZeile(e) {
  const name = e.firma && e.teil === "III" ? e.firma : [e.name, e.vorname].filter(Boolean).join(", ");
  const rest = [e.beruf, e.stand].filter(Boolean).join(", ");
  return `<b>${esc(name)}</b>${rest ? ` · ${esc(rest)}` : ""}${e.etage ? ` <span class="etage">${esc(e.etage)}</span>` : ""}`;
}

export function popupHtml(eig, eintraege, kompakt) {
  // Kompakt (Popup) zeigt höchstens drei Zeilen insgesamt: bei mehr als zwei Namen ersetzt der
  // "alle N im Detail"-Verweis die dritte Zeile, damit die Aufzählung "höchstens drei Namen" hält.
  const max = kompakt ? 2 : 12;
  const zeilen = eintraege.slice(0, max).map((e) => `<div class="pname" data-eintrag="${esc(e.id)}">${nameZeile(e)}</div>`);
  if (eintraege.length > max) zeilen.push(`<div class="pmehr" data-mehr="1">alle ${eintraege.length} im Detail ›</div>`);
  return `<div class="popup-kopf"><b>${esc(heutigeAdresse(eig))}</b>` +
    (eig.strasse_heute ? `<div class="hist">historische Adresse: ${esc(eig.historisch)}</div>` : "") +
    `<div class="praez praez-${esc(eig.stufe)}">${esc(praezisionText(eig.stufe))}</div>` +
    `<div class="zaehler">${esc(zaehlerText(eig))}</div></div>` +
    `<div class="popup-namen">${zeilen.join("")}</div>`;
}

function eintragHtml(e) {
  const felder = [["Beruf", e.beruf], ["Etage laut Buch", e.etage], ["Stand", e.stand],
    ["Bezugsperson", [e.bezug_vorname, e.bezug_beruf].filter(Boolean).join(", ")], ["Firma", e.firma],
    ["Eigentümer", e.eigentuemer], ["Verwalter", e.verwalter], ["Wohnort", e.wohnort]]
    .filter(([, w]) => w).map(([k, w]) => `<div><span class="k">${k}</span> ${esc(w)}</div>`).join("");
  const flags = (e.flags || []).map((f) => `<div class="flag">${esc(FLAGTEXT[f] || f)}</div>`).join("");
  return `<div class="eintrag" id="e-${esc(e.id)}"><div class="ename">${nameZeile(e)}</div>${felder}${flags}` +
    `<div class="quelle">Seite ${esc(e.seite)} · <a href="${faksimileUrl(e.seite)}" target="_blank" rel="noopener">Faksimile beim CompGen</a></div></div>`;
}

export function hausHtml(eig, eintraege) {
  const gruppen = ["I", "II", "III"].map((t) => {
    const l = eintraege.filter((e) => e.teil === t);
    return l.length ? `<h3>${EBENEN[t]} (${l.length})</h3>${l.map(eintragHtml).join("")}` : "";
  }).join("");
  return `<div class="haus-kopf"><h2>${esc(heutigeAdresse(eig))}</h2>` +
    (eig.strasse_heute ? `<div class="hist">historische Adresse: ${esc(eig.historisch)}</div>` : "") +
    `<div class="praez praez-${esc(eig.stufe)}">${esc(praezisionText(eig.stufe))}</div>` +
    (eig.nummer_unsicher === "ja" ? `<div class="flag">${FLAGTEXT.nummer_unsicher}</div>` : "") +
    `</div>${gruppen}`;
}

export function trefferzeileHtml(t) {
  // t = { adressId, titel, untertitel, stufe, n, eintragId? }
  const kenn = t.stufe === "haus" ? "" : `<span class="kenn">${t.stufe === "stadtplan" ? "Stadtplan 1935" : "nur Straße"}</span>`;
  return `<div class="treffer" data-adresse="${esc(t.adressId)}"${t.eintragId ? ` data-eintrag="${esc(t.eintragId)}"` : ""}>` +
    `<b>${esc(t.titel)}</b>${kenn}<small>${esc(t.untertitel)}</small></div>`;
}
