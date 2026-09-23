// Anzeigenamen der Eigentümer-Kategorien (Spec §3.3); Schlüssel wie pipeline/lib/eigentuemer.py.
export const KATEGORIEN = {
  stadt_staat: "Stadt/Staat/Reich", bergbau: "Bergbau", industrie: "Industrie", genossenschaft_siedlung: "Genossenschaft/Siedlung",
  kirche_stiftung: "Kirche/Stiftung", bank_versicherung: "Bank/Versicherung", privatperson: "Privatperson", sonstige: "Sonstige",
  gemischt: "mehrere Kategorien", ungeprueft: "ungeprüft",
};

// Anzeigenamen der Berufsniveaus (Spec §6.3); Schlüssel wie pipeline/lib/berufe.py.
export const NIVEAUS = {
  helfer: "Helfer-/Anlerntätigkeit", fachlich: "Fachliche Tätigkeit", spezialist: "Komplexe Spezialistentätigkeit",
  hochkomplex: "Hoch komplexe Tätigkeit", aufsicht: "Aufsichtskraft", fuehrung: "Führungskraft", keins: "ohne Niveau",
  gemischt: "mehrere Niveaus", unsicher: "Niveau unsicher", ungeprueft: "ungeprüft",
};

// Vereinte Beschriftung für die Themenlegende (Eigentümer- und Berufe-Thema teilen sich zeichneLegende()).
export const ANZEIGE = { ...KATEGORIEN, ...NIVEAUS };
