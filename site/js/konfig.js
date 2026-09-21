// Konstanten der Karte. PLAN_FREIGEGEBEN erst auf true setzen, wenn die Rechte am Stadtplan 1935 geklärt sind.
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
};
export const PLAN_FREIGEGEBEN = false;
export const STADTPLAN_EXPORT = "https://geo.essen.de/arcgis/rest/services/historischerverein/Stadtplan_1935/MapServer/export";
export const ESSEN_MITTE = [7.0131, 51.4556];
export const DES_PROJEKT = "https://des.genealogy.net/essen1936/";
export const DATEN = "daten/";
