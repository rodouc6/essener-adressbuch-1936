// Konstanten der Karte. PLAN_FREIGEGEBEN: Stadtplan 1935 (geo.essen.de) als Overlay anbieten.
// Nutzung vom Amt für Geoinformation, Vermessung und Kataster der Stadt Essen am 2026-10-07
// genehmigt: Einbindung live über die Export-Schnittstelle des Dienstes, Quellenvermerk im Impressum.
export const STILE = {
  positron: "https://tiles.openfreemap.org/styles/positron",
  liberty: "https://tiles.openfreemap.org/styles/liberty",
};
export const FARBEN = { I: "#1d4ed8", II: "#ca8a04", III: "#c2410c", neutral: "#1f2937", treffer: "#dc2626", auswahl: "#111827",
  // Eigentümer-Vergleich: Farbe je Platz in der Auswahl (Rot, Blau, Grün, Violett, Orange)
  gruppen: ["#dc2626", "#2563eb", "#16a34a", "#7c3aed", "#f59e0b"] };
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
// Versionsmarke für Cache-Busting: "dev" lokal; werkzeuge/deploy.sh ersetzt sie im Schnappschuss durch den
// Commit-Hash, Lader hängt sie dann als ?v= an jede Daten-URL, die HTML-Seiten an Skripte und Stile.
export const VERSION = "0ded0a7";
