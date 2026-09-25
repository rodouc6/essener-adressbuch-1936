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
}
