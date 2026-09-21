// Konstanten der Karte. PLAN_FREIGEGEBEN: Stadtplan 1935 (geo.essen.de) als Overlay anbieten.
// Die Rechte sind noch nicht geklärt (Stand 2026-09-21); für die interne Arbeit am nicht
// veröffentlichten Stand ist der Regler aktiv. VOR DER VERÖFFENTLICHUNG auf false setzen, falls
// die Freigabe der Stadt Essen / des Historischen Vereins bis dahin nicht vorliegt.
export const STILE = {
  positron: "https://tiles.openfreemap.org/styles/positron",
  liberty: "https://tiles.openfreemap.org/styles/liberty",
};
export const FARBEN = { I: "#1d4ed8", II: "#ca8a04", III: "#c2410c", neutral: "#1f2937", treffer: "#dc2626", auswahl: "#111827" };
export const EBENEN = { I: "Einwohner", II: "Eigentümer", III: "Gewerbe" };
export const PRAEZISION = {
  haus: "hausgenau verortet",
  strasse: "Straße bekannt, Hausnummer nicht verortbar",
  stadtplan: "Punkt vom Stadtplan 1935, Straße heute verschwunden",
  unbekannt: "Präzision unbekannt (Daten nicht geladen)",
};
export const PLAN_FREIGEGEBEN = true;
export const STADTPLAN_EXPORT = "https://geo.essen.de/arcgis/rest/services/historischerverein/Stadtplan_1935/MapServer/export";
export const ESSEN_MITTE = [7.0131, 51.4556];
export const DES_PROJEKT = "https://des.genealogy.net/essen1936/";
// Faksimile in der DigiBib des CompGen: Bildnummer je Seite kommt aus daten/faksimile.json.
export const DIGIBIB_WERK = "https://www.digibib.genealogy.net/viewer/image/857439804_1936/";
export const DATEN = "daten/";
// Startseite: Ausschnitt des Stadtplans 1935 (einmalig exportiert, EPSG:3857-Box des Bildes) und die
// Bildgrößen in bilder/startplan-1935-<breite>.{webp,jpg}; die Beispielpunkte kommen aus daten/startseite.json.
export const STARTPLAN = { bbox3857: [778322.27, 6701033.35, 782822.27, 6704033.35], seitenverhaeltnis: 3 / 2, ankerX: 0.3 };
