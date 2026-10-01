import { falte } from "./schluessel.js";

// Reiner Nachschlag im Straßenindex (kein DOM, kein Netzwerk) — testbar ohne Lader/Browser.
// q kann "Name" oder "Name (Ort)" sein: Letzteres liefern die Vorschlagslinks der Startseite/
// Sidebar sowie ein alter Browserverlaufs-Eintrag (q= aus schreibeZustand vor Fix-Runde 1, wo
// noch v.text statt v.name geschrieben wurde) — der Klammerzusatz wird toleriert, nicht verlangt.
// Rückgabe: { art: "strasse", name, artName, ort } oder null, wenn kein Straßenname passt.
export function strasseAusText(q, strassen) {
  const m = /^(.*?)\s*\(([^)]*)\)\s*$/.exec((q || "").trim());
  const name = m ? m[1] : (q || "");
  const ort = m ? m[2] : null;
  const k = falte(name);
  if (!k) return null;
  const alle = (strassen || []).filter((s) => s.schluessel === k);
  if (!alle.length) return null;
  // Ist der Klammer-Ort unter den Treffern bekannt, geht er den anderen Auswahlregeln vor —
  // sonst bliebe z. B. bei zwei Orten mit gleichem Straßennamen der falsche mit mehr Zeilen übrig.
  const kandidaten = ort && alle.some((s) => s.ort === ort) ? alle.filter((s) => s.ort === ort) : alle;
  const treffer = kandidaten.find((s) => s.art === "heute") || kandidaten.slice().sort((a, b) => b.zeilen - a.zeilen)[0];
  return { art: "strasse", name: treffer.name, artName: treffer.art, ort: treffer.ort };
}
