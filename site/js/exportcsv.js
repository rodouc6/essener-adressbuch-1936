import { heutigeAdresse } from "./popup.js";

export function csvZeile(felder) {
  return felder.map((f) => { const s = ohneFormel(String(f ?? "")); return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; }).join(",");
}

const KOPF_E = ["eintrag_id", "teil", "seite", "name", "vorname", "beruf", "etage", "stand", "adresse_heute", "adresse_1936", "stadtteil", "praezision", "flags", "adress_id"];
const KOPF_A = ["adress_id", "adresse_heute", "adresse_1936", "stadtteil", "praezision", "eintraege"];

// CSV-Formel-Injektion: ein Feld, das mit =, +, - oder @ beginnt, würde manche Tabellenprogramme
// (Excel, LibreOffice) beim Öffnen als Formel ausführen. Ein führendes ' entschärft das, ohne den
// sichtbaren Wert zu ändern.
function ohneFormel(s) {
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

export async function csvAusTreffern(ergebnis, lader, eig, maxEintraege = 5000) {
  const gesamt = [...ergebnis.zaehler.values()].reduce((a, b) => a + b, 0);
  const zeilen = [];
  const adr = (id) => { const e = eig.get(id) || {}; return [e.historisch ? heutigeAdresse(e) : "", e.historisch || "", e.stadtteil || "", e.stufe || ""]; };
  if (gesamt <= maxEintraege) {
    zeilen.push(csvZeile(KOPF_E));
    const nurIds = ergebnis.personen ? new Set(ergebnis.personen.map((p) => p.eintragId)) : null;
    for (const id of ergebnis.adressIds) {
      const eintraege = (await lader.scherbe(id)) || [];
      for (const e of eintraege) {
        if (nurIds && !nurIds.has(e.id)) continue;
        zeilen.push(csvZeile([e.id, e.teil, e.seite, e.name, e.vorname, e.beruf, e.etage, e.stand, ...adr(id), (e.flags || []).join(";"), id]));
      }
    }
  } else {
    zeilen.push(csvZeile(KOPF_A));
    for (const id of ergebnis.adressIds) zeilen.push(csvZeile([id, ...adr(id), ergebnis.zaehler.get(id)]));
  }
  return "﻿" + zeilen.join("\r\n") + "\r\n";
}

export function herunterladen(text, dateiname) {
  const blob = new Blob([text], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = dateiname;
  // Manche Browser (u. a. Firefox) lösen click() nur zuverlässig aus, wenn der Anker im DOM hängt.
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
