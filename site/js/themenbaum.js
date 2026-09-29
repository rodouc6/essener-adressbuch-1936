// Themenbaum in der Sidebar (Spec Themenbaum §2): Oberkategorien als Zeilen (Kästchen = Farbschalter, Pfeil = Klappliste),
// darunter Einzelbezeichnungen als Pills, die einen Vergleich starten. Reine HTML-Funktionen ohne DOM.
import { esc } from "./popup.js";
import { schalterKlassen } from "./themen.js";
import { anzeigeFuer } from "./kategorien.js";

export const PILLS_KURZ = 15;
const TOOLTIP = { gemischt: "mehrere Klassen im Haus, keine mit Mehrheit", ungeprueft: "kein geprüfter Wert für dieses Haus",
  unbestimmt: "Bezeichnung lässt die Stellung offen (z. B. „Friseur“ ohne Zusatz)",
  kaufleute: "„Kaufmann“ ohne Zusatz: Angestellter oder Selbständiger, aus der Bezeichnung nicht zu entscheiden" };

export function kopfHtml(thema) {
  return `<div class="thema"><b>${esc(thema.titel)}</b><p>${esc(thema.text)}</p><button data-thema-aus="1">Thema verlassen</button></div>`;
}
export function grundlageHtml(thema) { return thema.grundlage ? `<small class="grundlage">${esc(thema.grundlage)}</small>` : ""; }

function pill(e, vergleich, farben) {
  const i = vergleich.indexOf(e.schluessel);
  const stil = i >= 0 ? ` style="background:${esc(farben[i])};border-color:${esc(farben[i])};color:#fff"` : "";
  const titel = i >= 0 ? "aus dem Vergleich entfernen" : vergleich.length ? "zum Vergleich hinzufügen" : `alle Häuser: ${e.name}`;
  return `<button class="pill-s" data-schluessel="${esc(e.schluessel)}" aria-pressed="${i >= 0}"${stil} title="${esc(titel)}">${esc(e.name)} <small>${e.adressen}</small></button>`;
}

// opt: { klassen (URL-String), vergleich (Schlüssel), farben, offen (Oberkategorie-ID | null), alle (ID, deren Liste voll gezeigt wird | null) }
export function baumHtml(thema, liste, opt) {
  const an = new Set(schalterKlassen(thema, opt.klassen || ""));
  const namen = anzeigeFuer(thema.farbe?.feld);
  const werte = thema.farbe?.werte || {}, sonst = thema.farbe?.sonst || "#c8c8c8";
  const ober = new Map((liste?.oberkategorien || []).map((o) => [o.id, o]));
  let html = `<div class="baum">`;
  for (const k of thema.schalter?.klassen || []) {
    const o = ober.get(k);
    const zahl = o ? o.adressen : k === "gemischt" && liste ? liste.gemischt : k === "ungeprueft" && liste ? liste.ungeprueft : null;
    const name = thema.schalter?.namen?.[k] || namen[k] || k;
    const tip = TOOLTIP[k] ? ` title="${esc(TOOLTIP[k])}"` : "";
    const auf = !!(o && o.eintraege.length);
    const offen = auf && opt.offen === k;
    html += `<div class="zeile ober"><label class="schalter"${tip}><input type="checkbox" data-klasse="${esc(k)}"${an.has(k) ? " checked" : ""}><span class="punkt" style="background:${esc(werte[k] || sonst)}"></span> ${esc(name)}${zahl == null ? "" : ` <small>${zahl}</small>`}</label>` +
      (auf ? `<button class="auf" data-auf="${esc(k)}" aria-expanded="${offen}" aria-label="${offen ? "zuklappen" : "aufklappen"}">${offen ? "▾" : "▸"}</button>` : "") + `</div>`;
    if (offen) {
      const voll = opt.alle === k;
      const teil = voll ? o.eintraege : o.eintraege.slice(0, PILLS_KURZ);
      html += `<div class="pills-s">${teil.map((e) => pill(e, opt.vergleich || [], opt.farben || [])).join("")}` +
        (voll || o.eintraege.length <= PILLS_KURZ ? "" : `<button class="alle" data-alle="${esc(k)}">alle ${o.eintraege.length} anzeigen</button>`) + `</div>`;
    }
  }
  if (liste && typeof liste.handgeprueft_anteil === "number") {
    html += `<div class="zeile klein">Stellung handgeprüft bei ${Math.round(liste.handgeprueft_anteil * 100)} % der Nennungen, sonst Vorschlag der Automatik.</div>`;
  }
  return html + `</div>`;
}
