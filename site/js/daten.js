import { DATEN } from "./konfig.js";

// Lädt Dateien des Datenpakets und hält sie im Speicher. Ein 404 (Scherbe existiert nicht) ist
// kein Fehler, sondern "keine Daten" → null.
export class Lader {
  constructor(basis = DATEN, fetchFn = (u) => fetch(u)) {
    this.basis = basis;
    this.fetchFn = fetchFn;
    this.cache = new Map();
  }

  async json(pfad) {
    const url = this.basis + pfad;
    if (!this.cache.has(url)) {
      this.cache.set(url, (async () => {
        const r = await this.fetchFn(url);
        if (!r.ok) {
          if (r.status === 404) return null;
          throw new Error(`Laden fehlgeschlagen: ${url} (${r.status})`);
        }
        return r.json();
      })());
    }
    return this.cache.get(url);
  }

  async scherbe(adressId) {
    const s = await this.json(`haus/${adressId.slice(0, 2)}.json`);
    return s && s[adressId] ? s[adressId] : null;
  }
  // Punkteigenschaften einer Adresse — Fallback, wenn die Adresse (noch) nicht in den geladenen
  // Kartenkacheln liegt (z. B. außerhalb des Viewports); unabhängig vom Kachelstand des Browsers.
  async adresse(adressId) {
    const s = await this.json(`adressen/${adressId.slice(0, 2)}.json`);
    return s && s[adressId] ? s[adressId] : null;
  }
  // Kurzindex (Spec Eigentümer-Vergleich §2): je Datei das erste Zeichen der ID, sieben Werte je Adresse.
  // Lädt nur die Dateien, die unter den IDs vorkommen; json() hält sie im Cache. Fehlende Datei → keine Einträge.
  async adressenKurz(ids) {
    const dateien = [...new Set(ids.map((id) => id[0]))];
    const geladen = await Promise.all(dateien.map((x) => this.json(`adressen_kurz/${x}.json`)));
    const je = new Map(dateien.map((x, i) => [x, geladen[i] || {}]));
    const m = new Map();
    for (const id of ids) {
      const w = je.get(id[0])[id];
      if (w) m.set(id, { id, lon: w[0], lat: w[1], stufe: w[2], stadtteil: w[3], strasse_heute: w[4], hausnr: w[5], historisch: w[6] });
    }
    return m;
  }
  namen(praefix) { return this.json(`suche/namen/${praefix}.json`); }
  firmen(praefix) { return this.json(`suche/firmen/${praefix}.json`); }
  berufeScherbe(praefix) { return this.json(`suche/berufe/${praefix}.json`); }
  strassen() { return this.json("suche/strassen.json"); }
  strassenScherbe(praefix) { return this.json(`suche/strassen/${praefix}.json`); }
  berufe() { return this.json("suche/berufe.json"); }
  berufeNorm() { return this.json("suche/berufe_norm.json"); }
  berufeNormScherbe(praefix) { return this.json(`suche/berufe_norm/${praefix}.json`); }
  eigentuemer() { return this.json("suche/eigentuemer.json"); }
  eigentuemerScherbe(praefix) { return this.json(`suche/eigentuemer/${praefix}.json`); }
  stadtteile() { return this.json("suche/stadtteile.json"); }
  kennzahlen() { return this.json("kennzahlen.json"); }
  startseite() { return this.json("startseite.json"); }
  faksimile() { return this.json("faksimile.json"); }
  thema(id) { return this.json(`themen/${id}.json`); }
  ebene(name) { return this.json(`ebenen/${name}.json`); }
  layout(name) { return this.json(`layout/${name}.json`); }
  hauptgruppen() { return this.json("hauptgruppen.json"); }
  stadtteilePolygone() { return this.json("stadtteile.geojson"); }
  perspektivenIndex() { return this.json("perspektiven/index.json"); }
  kapitel(id) { return this.json(`perspektiven/${id}.json`); }
  herkunft(name) { return this.json(`herkunft/${name}.json`); }
  punkte() { return this.json("perspektiven/bergbau_punkte.json"); }
  zechen() { return this.json("zechen.geojson"); }
}
