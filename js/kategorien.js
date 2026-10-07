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

// Anzeigenamen der Stellung (Spec Themenbaum §4); Schlüssel wie pipeline/lib/stellung.py.
export const STELLUNGEN = {
  arbeiter: "Arbeiter", angestellte: "Angestellte", beamte: "Beamte", selbstaendige: "Selbständige (Handwerk, Handel, Gastgewerbe)",
  freie_berufe: "Freie Berufe und Akademiker", unternehmer: "Unternehmer und Leitende", kaufleute: "Kaufleute (Stellung unbestimmt)",
  ohne_erwerb: "Ohne Erwerbsberuf", unbestimmt: "unbestimmt", gemischt: "mehrere Stellungen", ungeprueft: "ungeprüft",
};

// Beschriftung je Farbfeld für Themenbaum und Legende. Nicht vereinen: `gemischt` heißt je Feld verschieden.
const ANZEIGE_JE_FELD = { besitz: KATEGORIEN, niveau: NIVEAUS, stellung: STELLUNGEN };
export function anzeigeFuer(feld) { return ANZEIGE_JE_FELD[feld] || {}; }
