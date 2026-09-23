// Zustand des Eigentümer-Werkzeugs (Spec §5): eine Zeile je Schreibweise; ein „Eigentümer“ ist die Menge
// der Zeilen mit gleichem eigentuemer-Wert. Aktionen liefern die geänderten Zeilen zum Speichern.
const CSV_FELDER = ["schreibweise", "art", "eigentuemer", "kategorie", "geprueft", "hinweis", "identitaet"];
const VERLAUF_MAX = 20;

export function baueModell(vorschlagZeilen, kuratierungZeilen) {
  const vorschlag = new Map(vorschlagZeilen.map((v) => [v.schreibweise.trim(), v]));
  const zeilen = new Map();
  for (const k of kuratierungZeilen) {
    const s = k.schreibweise.trim();
    const v = vorschlag.get(s);
    zeilen.set(s, { schreibweise: s, art: k.art || (v && v.art) || "", eigentuemer: (k.eigentuemer || "").trim() || s,
      kategorie: k.kategorie || "", geprueft: k.geprueft || "", hinweis: k.hinweis || "", identitaet: k.identitaet || "",
      anzahl: v ? Number(v.anzahl) : 0, cluster_id: v ? v.cluster_id : "", pruefpflichtig: !!v && v.pruefpflichtig === "ja", verwaist: !v });
  }
  return { zeilen, vorschlag, verlauf: [] };
}

function gruppen(m) {
  const g = new Map();
  for (const z of m.zeilen.values()) {
    if (!g.has(z.eigentuemer)) g.set(z.eigentuemer, []);
    g.get(z.eigentuemer).push(z);
  }
  return g;
}

// War O(Zeilen × Eigentümer): je Eigentümer wurde noch einmal über alle Zeilen gescannt, um dessen
// Vorschläge zu finden (411 ms auf den echten Daten, 2.714 Zeilen × ~2.100 Eigentümer). Jetzt ein
// einziger Durchlauf über m.zeilen, der die Vorschläge nach dem cluster_id ihres Ziels bündelt
// (cluster_id → wartende Zeilen); jeder Eigentümer holt sich anschließend nur die Einträge seiner
// eigenen cluster_ids (O(Zeilen + Eigentümer)).
export function eigentuemerListe(m) {
  const g = gruppen(m);
  const wartendJeZiel = new Map();
  for (const z of m.zeilen.values()) {
    const v = m.vorschlag.get(z.schreibweise);
    if (v && v.vorschlag_fuer) {
      if (!wartendJeZiel.has(v.vorschlag_fuer)) wartendJeZiel.set(v.vorschlag_fuer, []);
      wartendJeZiel.get(v.vorschlag_fuer).push({ zeile: z, aehnlichkeit: Number(v.aehnlichkeit) });
    }
  }
  const liste = [...g].map(([name, zs]) => {
    zs.sort((a, b) => b.anzahl - a.anzahl || a.schreibweise.localeCompare(b.schreibweise, "de"));
    // Mehrere Schreibweisen derselben Gruppe teilen sich oft dieselbe cluster_id (ungetrennter
    // Automatik-Cluster) — je Ziel-ID nur einmal nachsehen, sonst tauchen Vorschläge doppelt auf.
    const idsInGruppe = new Set(zs.map((z) => z.cluster_id));
    const vorschlaege = [];
    for (const id of idsInGruppe) {
      for (const w of wartendJeZiel.get(id) || []) if (w.zeile.eigentuemer !== name) vorschlaege.push(w);
    }
    vorschlaege.sort((a, b) => b.aehnlichkeit - a.aehnlichkeit || b.zeile.anzahl - a.zeile.anzahl);
    return { name, art: zs[0].art, kategorie: zs[0].kategorie, identitaet: zs[0].identitaet || "", haeuser: zs.reduce((s, z) => s + z.anzahl, 0), schreibweisen: zs,
      geprueft: zs.every((z) => z.geprueft === "ja"), pruefpflichtig: zs.some((z) => z.pruefpflichtig), vorschlaege };
  });
  return liste.sort((a, b) => b.haeuser - a.haeuser || a.name.localeCompare(b.name, "de"));
}

function merke(m) {
  m.verlauf.push(new Map([...m.zeilen].map(([k, z]) => [k, { ...z }])));
  if (m.verlauf.length > VERLAUF_MAX) m.verlauf.shift();
}

function zeilenVon(m, name) { return [...m.zeilen.values()].filter((z) => z.eigentuemer === name); }

// Bestand eines Eigentümers hat sich geändert → nicht mehr „geprüft“ (der Mensch sieht ihn noch einmal an).
// Liefert nur die tatsächlich geänderten Zeilen (war vorher "ja"), damit die Rückgabe der Aktionen nur
// wirklich veränderte Zeilen enthält.
function entpruefe(zs) {
  const geaendert = [];
  for (const z of zs) { if (z.geprueft !== "") { z.geprueft = ""; geaendert.push(z); } }
  return geaendert;
}

export function setzeKategorie(m, name, kategorie) {
  const zs = zeilenVon(m, name);
  if (zs.every((z) => z.kategorie === kategorie)) return [];
  merke(m);
  for (const z of zs) z.kategorie = kategorie;
  return zs;
}

// Zielt der neue Name schon auf einen bestehenden Eigentümer, ist das inhaltlich ein Zusammenführen
// (mit dessen Kategorie, beide Gruppen entprüft) — nicht ein stilles Umbenennen, das den Bestand des
// Ziels unverändert „geprüft“ lässt, obwohl er gerade neue Schreibweisen bekommen hat.
export function benenne(m, alt, neu) {
  neu = neu.trim();
  if (!neu || neu === alt) return [];
  if (zeilenVon(m, neu).length) return zusammenfuehren(m, alt, neu);
  merke(m);
  const zs = zeilenVon(m, alt);
  for (const z of zs) z.eigentuemer = neu;
  return zs;
}

// Identität (Personen): "sicher" = vom Bearbeiter bestätigt, leer = nicht belegbar; gilt für alle Zeilen des Eigentümers.
export function setzeIdentitaet(m, name, sicher) {
  const zs = zeilenVon(m, name);
  const wert = sicher ? "sicher" : "";
  if (!zs.length || zs.every((z) => z.identitaet === wert)) return [];
  merke(m);
  for (const z of zs) z.identitaet = wert;
  return zs;
}

export function setzeGeprueft(m, name, ja) {
  const wert = ja ? "ja" : "";
  const zs = zeilenVon(m, name);
  if (zs.every((z) => z.geprueft === wert)) return [];
  merke(m);
  for (const z of zs) z.geprueft = wert;
  return zs;
}

export function setzeHinweis(m, name, text) {
  const zs = zeilenVon(m, name);
  if (zs.every((z) => z.hinweis === text)) return [];
  merke(m);
  for (const z of zs) z.hinweis = text;
  return zs;
}

export function abspalten(m, schreibweise) {
  const z = m.zeilen.get(schreibweise);
  if (!z) return [];
  merke(m);
  const rest = zeilenVon(m, z.eigentuemer).filter((x) => x !== z);
  z.eigentuemer = schreibweise; z.geprueft = ""; z.kategorie = z.art === "person" ? "privatperson" : "";
  return [z, ...entpruefe(rest)];
}

export function zusammenfuehren(m, quelle, ziel) {
  if (quelle === ziel) return [];
  const zielZeilen = zeilenVon(m, ziel);
  if (!zielZeilen.length) return [];
  merke(m);
  const kat = zielZeilen[0].kategorie;
  const zs = zeilenVon(m, quelle);
  for (const z of zs) { z.eigentuemer = ziel; z.kategorie = kat; z.geprueft = ""; }
  return [...zs, ...entpruefe(zielZeilen)];
}

// Vorschläge gelten je Schreibweise (nicht je Gruppe) — nur diese eine Zeile wandert zum Ziel,
// der Rest ihrer bisherigen Gruppe bleibt unverändert dort stehen.
export function uebernehmeVorschlag(m, schreibweise, ziel) {
  const z = m.zeilen.get(schreibweise);
  if (!z) return [];
  const zielZeilen = zeilenVon(m, ziel);
  if (!zielZeilen.length || z.eigentuemer === ziel) return [];
  merke(m);
  const alteGruppe = zeilenVon(m, z.eigentuemer).filter((x) => x !== z);
  z.eigentuemer = ziel; z.kategorie = zielZeilen[0].kategorie; z.geprueft = "";
  return [z, ...entpruefe(alteGruppe), ...entpruefe(zielZeilen)];
}

export function rueckgaengig(m) {
  const alt = m.verlauf.pop();
  if (!alt) return null;
  const geaendert = [];
  for (const [k, z] of alt) {
    const jetzt = m.zeilen.get(k);
    if (!jetzt || CSV_FELDER.some((f) => jetzt[f] !== z[f])) { m.zeilen.set(k, z); geaendert.push(z); }
  }
  return geaendert;
}

// liste: von eigentuemerListe(m) wiederverwendbar, damit ein Neuzeichnen sie nicht ein zweites Mal berechnet.
export function fortschritt(m, liste = null) {
  const l = (liste || eigentuemerListe(m)).filter((e) => e.pruefpflichtig);
  return { geprueft: l.filter((e) => e.geprueft).length, gesamt: l.length,
    haeuserGeprueft: l.filter((e) => e.geprueft).reduce((s, e) => s + e.haeuser, 0), haeuserGesamt: l.reduce((s, e) => s + e.haeuser, 0) };
}

export function zumSpeichern(z) { return Object.fromEntries(CSV_FELDER.map((f) => [f, z[f]])); }
