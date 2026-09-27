import { STILE, FARBEN, STADTPLAN_EXPORT, ESSEN_MITTE, DATEN, PLAN_FREIGEGEBEN } from "./konfig.js";
import { esc } from "./popup.js";

const WIKIPEDIA_QUELLE = /^https:\/\/de\.wikipedia\.org\//;

const RADIUS = ["interpolate", ["linear"], ["ln", ["max", ["var", "n"], 1]], 0, 4, Math.log(100), 10];

function summeAktiv(ebenen) {
  // Summe der Einträge über die aktiven Ebenen als Ausdruck
  return ["+", ...ebenen.map((e) => ["coalesce", ["get", `n_${e}`], 0])];
}

async function ladeIcon(map, name, url, sdf) {
  const img = new Image(64, 64);
  await new Promise((ok, nein) => { img.onload = ok; img.onerror = nein; img.src = url; });
  if (!map.hasImage(name)) map.addImage(name, img, { sdf, pixelRatio: 2 });
}

// Popup einer Zeche. Betriebsjahre stammen aus dem Wikipedia-Artikel (ersatzweise der Liste); weicht die
// Liste ab, wird das gesagt statt eine Angabe als sicher zu zeigen. Nur auf de.wikipedia.org verlinken —
// quelle ist Rohdaten aus der Kuratierung, kein beliebiges Ziel soll unbeaufsichtigt verlinkt werden (I1).
export function zechePopupHtml(p) {
  const jahre = p.jahre_unbekannt ? "Betriebsjahre unbekannt" : `in Betrieb ${esc(p.betrieb_von)}–${esc(p.betrieb_bis)}`;
  const widerspruch = p.jahre_widerspruch
    ? `<br><small>Wikipedia-Liste abweichend: ${esc(p.liste_von)}–${esc(p.liste_bis)}</small>` : "";
  const plan = p.plan_1935 ? `<br><small>Stadtplan 1935: „${esc(p.plan_1935)}“</small>` : "";
  const link = p.quelle && WIKIPEDIA_QUELLE.test(p.quelle)
    ? `<br><a href="${esc(p.quelle)}" target="_blank" rel="noopener">Wikipedia</a>` : "";
  return `<b>${esc(p.name)}</b><br>${esc(p.stadtteil || "")}<br>${jahre}${widerspruch}${plan}${link}`;
}

// Grau der Einheiten ohne Farbe (unter min_n oder gar nicht in den Ebenendaten) — wie GRAU in formen/skalen.js.
const GRAU_KARTE = "#c8c8c8";

// Weißer Rand um jeden Adresspunkt (Spec 2026-09-28 §4): in der Stadtansicht keiner (sonst weiße
// Flecken), ab Straßenzoom sichtbar — trennt überlappende Punkte und hält den Kontrast auf Liberty.
const HALO = ["interpolate", ["linear"], ["zoom"], 12, 0, 14, 1, 16, 1.6];

const ICONS = { "kreis-gestrichelt": ["bilder/kreis-gestrichelt.svg", true], zeche: ["bilder/zeche.svg", false] };
const LEERER_STIL = { version: 8, sources: {}, layers: [] };

export class Karte {
  constructor(container, zustand, ereignisse) {
    this.ereignisse = ereignisse;
    this.zustand = zustand;
    this.farbe = null;          // Themenfarbregel (Task 13) oder null
    this.ansicht = null;        // normalisierte Ansicht (Spec §8) oder null
    this.ansichtWerte = new Map();
    this._ansichtGen = 0;
    this.treffer = new Set();
    this.auswahl = null;
    this._stilCache = new Map();
    this._stilGen = 0;
    this.protokoll = new pmtiles.Protocol();
    maplibregl.addProtocol("pmtiles", this.protokoll.tile);
    // Die Karte startet mit einem leeren Stil; der eigentliche Stil kommt über setzeStil(), das die
    // Grundkarte als JSON lädt und unsere Quellen und Ebenen hineinmischt. So sind unsere Ebenen von
    // Anfang an Teil des Stils, und ein Stilwechsel kann sie nicht mehr wegräumen.
    this.map = new maplibregl.Map({
      container, style: LEERER_STIL, center: zustand.c || ESSEN_MITTE, zoom: zustand.z ?? 11,
      minZoom: 9, maxZoom: 18,
      // Impressum/Datenschutz müssen von jeder Seite erreichbar sein — auf der Kartenseite über die Attribution.
      attributionControl: { compact: true, customAttribution: '<a href="impressum.html">Impressum</a> · <a href="impressum.html#datenschutz">Datenschutz</a>' },
    });
    this.map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    this.map.addControl(new maplibregl.GeolocateControl({ trackUserLocation: false }), "top-right");
    this.map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");
    this.popup = new maplibregl.Popup({ closeButton: true, maxWidth: "320px", offset: 10 });
    // Icons gehen bei jedem Stilwechsel verloren; MapLibre meldet fehlende Bilder, wir laden sie nach.
    this.map.on("styleimagemissing", (e) => { const d = ICONS[e.id]; if (d) ladeIcon(this.map, e.id, d[0], d[1]); });
    this.map.on("moveend", () => {
      const c = this.map.getCenter();
      ereignisse.onBewegt(Math.round(this.map.getZoom() * 100) / 100, [+c.lng.toFixed(5), +c.lat.toFixed(5)]);
    });
    this._bereit = new Promise((ok) => this.map.once("load", ok)).then(() => this.setzeStil(zustand.karte));
  }

  bereit() { return this._bereit; }

  _eigeneQuellen() {
    const q = {
      adressen: { type: "vector", url: `pmtiles://${new URL(DATEN + "adressen.pmtiles", location.href)}`, promoteId: "id" },
      zechen: { type: "geojson", data: new URL(DATEN + "zechen.geojson", location.href).href },
      // Flächen der Ansichten (Spec §8); promoteId hebt die Eigenschaft `id` zur Feature-ID,
      // damit Farben per feature-state gesetzt werden können.
      stadtteile: { type: "geojson", data: new URL(DATEN + "stadtteile.geojson", location.href).href, promoteId: "id" },
    };
    // Solange PLAN_FREIGEGEBEN false ist (Rechte am Dienst geo.essen.de ungeklärt), weder Quelle
    // noch Ebene anlegen — kein einziger Request an den Dienst, auch nicht über ?plan=1 (C1).
    if (PLAN_FREIGEGEBEN) {
      q["stadtplan-1935"] = {
        type: "raster", tileSize: 256, minzoom: 10, maxzoom: 17,
        tiles: [`${STADTPLAN_EXPORT}?bbox={bbox-epsg-3857}&bboxSR=3857&imageSR=3857&size=256,256&format=png32&transparent=true&f=image`],
        attribution: "Stadtplan 1935: Stadt Essen / Historischer Verein",
      };
    }
    return q;
  }

  _eigeneEbenen() {
    const sl = "adressen";
    const e = [];
    if (PLAN_FREIGEGEBEN) e.push({ id: "stadtplan-1935", type: "raster", source: "stadtplan-1935",
                                  layout: { visibility: "none" }, paint: { "raster-opacity": 0 } });
    // Ansichtsebenen liegen unter den Adresspunkten, damit die Punkte sichtbar bleiben; ohne
    // Ansicht sind alle drei unsichtbar. Ohne feature-state bleibt eine Einheit grau.
    e.push({ id: "stadtteile-flaeche", type: "fill", source: "stadtteile", layout: { visibility: "none" },
             paint: { "fill-color": ["coalesce", ["feature-state", "farbe"], GRAU_KARTE], "fill-opacity": 0.55, "fill-outline-color": "#fff" } });
    e.push({ id: "strassen-linie", type: "line", source: "adressen", "source-layer": "strassen", layout: { visibility: "none" },
             paint: { "line-color": ["coalesce", ["feature-state", "farbe"], GRAU_KARTE],
                      "line-width": ["interpolate", ["linear"], ["zoom"], 11, 1.5, 15, 5] } });
    e.push({ id: "hex-flaeche", type: "fill", source: "adressen", "source-layer": "hex", layout: { visibility: "none" },
             paint: { "fill-color": ["coalesce", ["feature-state", "farbe"], GRAU_KARTE], "fill-opacity": 0.6 } });
    e.push({ id: "adressen-haus", type: "circle", source: "adressen", "source-layer": sl,
             filter: ["==", ["get", "stufe"], "haus"],
             paint: { "circle-stroke-color": "#fff", "circle-stroke-width": HALO } });
    e.push({ id: "adressen-ungenau", type: "symbol", source: "adressen", "source-layer": sl,
             filter: ["!=", ["get", "stufe"], "haus"],
             layout: { "icon-image": "kreis-gestrichelt", "icon-allow-overlap": true, "icon-ignore-placement": true },
             paint: { "icon-halo-color": "#fff", "icon-halo-width": HALO } });
    e.push({ id: "adressen-auswahl", type: "circle", source: "adressen", "source-layer": sl,
             filter: ["==", ["get", "id"], ""],
             paint: { "circle-radius": 14, "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": FARBEN.auswahl, "circle-stroke-width": 3 } });
    e.push({ id: "zechen", type: "symbol", source: "zechen", filter: ["==", ["get", "aktiv_1936"], true],
             layout: { visibility: "none", "icon-image": "zeche", "icon-size": 0.6, "text-field": ["get", "name"], "text-font": ["Noto Sans Regular"],
                       "text-size": 11, "text-offset": [0, 1.4], "text-anchor": "top", "icon-allow-overlap": true },
             paint: { "text-halo-color": "#fff", "text-halo-width": 1.5 } });
    return e;
  }

  // Grundkarte als JSON laden (einmal je Stil) und unsere Quellen und Ebenen hineinmischen.
  async _stilMitEbenen(name) {
    if (!this._stilCache.has(name)) {
      this._stilCache.set(name, fetch(STILE[name]).then((r) => { if (!r.ok) throw new Error(`Stil ${name}: ${r.status}`); return r.json(); }));
    }
    const basis = await this._stilCache.get(name);
    return { ...basis, sources: { ...basis.sources, ...this._eigeneQuellen() }, layers: [...basis.layers, ...this._eigeneEbenen()] };
  }

  // Stil setzen; ein späterer Aufruf überholt einen noch laufenden (Generationszähler), und der
  // überholte Aufruf löst trotzdem auf, damit niemand auf ihn hängen bleibt.
  async setzeStil(name) {
    const gen = ++this._stilGen;
    let stil;
    try { stil = await this._stilMitEbenen(name); }
    catch (e) { console.error(e); return; }
    if (gen !== this._stilGen) return;
    // Nach setStyle(objekt) liegen Quellen und Ebenen sofort im neuen Stil; "styledata" bestätigt,
    // dass MapLibre ihn übernommen hat, danach Filter/Zustand anlegen.
    const uebernommen = new Promise((ok) => this.map.once("styledata", ok));
    this.map.setStyle(stil, { diff: false });
    await uebernommen;
    if (gen !== this._stilGen) return;
    this.ebenenAufsetzen();
  }

  // Zustand (Filter, Plan, Zechen, Treffer, Auswahl) auf die im Stil vorhandenen Ebenen legen.
  ebenenAufsetzen() {
    const m = this.map;
    // Klick-/Hover-Handler sind an die Karte gebunden, nicht an den Stil — nur einmal registrieren.
    if (!this._handlerAngehaengt) {
      this._handlerAngehaengt = true;
      for (const id of ["adressen-haus", "adressen-ungenau"]) {
        m.on("click", id, (e) => this.ereignisse.onKlick(e.features[0].properties.id, e.lngLat));
        m.on("mouseenter", id, (e) => { m.getCanvas().style.cursor = "pointer"; this.ereignisse.onHover(e.features[0].properties.id, e.lngLat); });
        m.on("mouseleave", id, () => { m.getCanvas().style.cursor = ""; this.ereignisse.onHover(null, null); });
      }
      m.on("click", "zechen", (e) => {
        const p = e.features[0].properties;
        this.zeigePopup(e.lngLat, zechePopupHtml(p));
      });
    }
    this.setzeFilter(this.zustand);
    this.setzePlan(this.zustand.plan);
    this.setzeZechen(this.zustand.zechen);
    this.setzeTreffer(this.treffer.size ? [...this.treffer] : null);
    this.setzeAuswahl(this.auswahl);
    // Nach einem Stilwechsel sind Quellen und feature-state neu — Ansicht erneut auflegen.
    this.setzeAnsicht(this.ansicht, this.ansichtWerte);
  }

  // Eine Ansicht (Spec §8) auf der Karte zeigen: passende Ebene sichtbar, Farben per feature-state,
  // Adresspunkte gedimmt. `werte` ist eine Map id → { farbe, … } aus ansicht_farben.js.
  setzeAnsicht(ansicht, werte) {
    this.ansicht = ansicht || null;
    this.ansichtWerte = werte || new Map();
    const m = this.map;
    this._ansichtGen = (this._ansichtGen || 0) + 1;   // hebt noch wartende Farbanwendungen auf
    if (!m.getLayer("stadtteile-flaeche")) return;    // vor dem ersten Stil: kommt über ebenenAufsetzen()
    const ebene = this.ansicht ? this.ansicht.ebene : null;
    m.setLayoutProperty("stadtteile-flaeche", "visibility", ebene === "stadtteil" ? "visible" : "none");
    m.setLayoutProperty("strassen-linie", "visibility", ebene === "strasse" ? "visible" : "none");
    m.setLayoutProperty("hex-flaeche", "visibility", ebene === "hex" ? "visible" : "none");
    if (ebene && ebene !== "adresse") {
      const quelle = ebene === "stadtteil" ? { source: "stadtteile" }
        : { source: "adressen", sourceLayer: ebene === "strasse" ? "strassen" : "hex" };
      this._farbenAnwenden(quelle, this._ansichtGen);
    }
    this._deckkraftSetzen();
  }

  // feature-state lässt sich erst setzen, wenn die Quelle geladen ist; sonst bliebe alles grau.
  // Deshalb bei Bedarf einmal auf "sourcedata" warten und dann anwenden.
  _farbenAnwenden(quelle, gen) {
    const m = this.map;
    const anwenden = () => {
      if (gen !== this._ansichtGen) return true;      // von einer neueren Ansicht überholt
      try {
        m.removeFeatureState(quelle);
        for (const [id, w] of this.ansichtWerte) m.setFeatureState({ ...quelle, id }, { farbe: w.farbe });
      } catch { return false; }
      return true;
    };
    if (m.isSourceLoaded(quelle.source) && anwenden()) return;
    const horch = (e) => {
      if (gen !== this._ansichtGen) { m.off("sourcedata", horch); return; }
      if (e.sourceId !== quelle.source || !e.isSourceLoaded) return;
      if (anwenden()) m.off("sourcedata", horch);
    };
    m.on("sourcedata", horch);
  }

  // Farbe und Größe aus Zustand + Themenregel ableiten und auf beide Adressebenen legen.
  setzeFilter(z) {
    this.zustand = z;
    const m = this.map;
    if (!m.getLayer("adressen-haus")) return;   // vor dem ersten Stil: Zustand wird beim Aufsetzen angewendet
    const n = summeAktiv(z.ebene);
    const bedingungen = [[">", n, 0], ["in", ["get", "stufe"], ["literal", z.praez]]];
    if (z.stadtteil) bedingungen.push(["==", ["get", "stadtteil"], z.stadtteil]);
    if (this.farbe && this.farbe.merkmal) bedingungen.push([">", ["coalesce", ["get", `m_${this.farbe.merkmal}`], 0], 0]);
    bedingungen.push(["any", [">=", ["zoom"], 12], [">=", n, 5]]);   // Stadtansicht nicht zulaufen lassen
    const grund = this.farbe ? this.farbe.ausdruck : (z.ebene.length === 1 ? FARBEN[z.ebene[0]] : FARBEN.neutral);
    const farbe = ["case", ["boolean", ["feature-state", "treffer"], false], FARBEN.treffer, grund];
    const radius = ["let", "n", n, RADIUS];
    m.setFilter("adressen-haus", ["all", ["==", ["get", "stufe"], "haus"], ...bedingungen]);
    m.setFilter("adressen-ungenau", ["all", ["!=", ["get", "stufe"], "haus"], ...bedingungen]);
    m.setPaintProperty("adressen-haus", "circle-color", farbe);
    m.setPaintProperty("adressen-haus", "circle-radius", radius);
    m.setPaintProperty("adressen-ungenau", "icon-color", farbe);
    m.setLayoutProperty("adressen-ungenau", "icon-size", ["/", ["let", "n", n, RADIUS], 16]);
    this._deckkraftSetzen();
  }

  // Ohne Treffermenge sind alle Punkte voll sichtbar; mit Treffermenge nur die Treffer, der Rest
  // gedimmt. Unter einer Flächenansicht treten die Punkte insgesamt zurück, damit die Fläche lesbar bleibt.
  _deckkraftSetzen() {
    if (!this.map.getLayer("adressen-haus")) return;
    const basis = this.ansicht && this.ansicht.ebene !== "adresse" ? 0.15 : 0.9;
    const d = this.treffer.size ? ["case", ["boolean", ["feature-state", "treffer"], false], basis, Math.min(basis, 0.25)] : basis;
    this.map.setPaintProperty("adressen-haus", "circle-opacity", d);
    this.map.setPaintProperty("adressen-haus", "circle-stroke-opacity", d);
    this.map.setPaintProperty("adressen-ungenau", "icon-opacity", d);
  }

  setzeFarbe(regel) { this.farbe = regel; this.setzeFilter(this.zustand); }

  // Treffer per Feature-State: alle bisherigen zurücksetzen, neue setzen, Rest dimmen.
  setzeTreffer(adressIds) {
    const m = this.map;
    if (!m.getSource("adressen")) return;
    m.removeFeatureState({ source: "adressen", sourceLayer: "adressen" });
    this.treffer = new Set(adressIds || []);
    for (const id of this.treffer) m.setFeatureState({ source: "adressen", sourceLayer: "adressen", id }, { treffer: true });
    this._deckkraftSetzen();
  }

  setzeAuswahl(adressId) {
    this.auswahl = adressId;
    if (this.map.getLayer("adressen-auswahl")) this.map.setFilter("adressen-auswahl", ["==", ["get", "id"], adressId || ""]);
  }

  setzePlan(deckkraft) {
    if (!PLAN_FREIGEGEBEN || !this.map.getLayer("stadtplan-1935")) return;
    this.map.setLayoutProperty("stadtplan-1935", "visibility", deckkraft > 0 ? "visible" : "none");
    this.map.setPaintProperty("stadtplan-1935", "raster-opacity", deckkraft);
  }

  setzeZechen(an) {
    if (this.map.getLayer("zechen")) this.map.setLayoutProperty("zechen", "visibility", an ? "visible" : "none");
  }

  fliegeZu(lngLat, zoom = 16) { this.map.flyTo({ center: lngLat, zoom: Math.max(this.map.getZoom(), zoom), duration: 600 }); }

  // Auf die geladenen Treffer einpassen; nicht geladene Kacheln kennen wir nicht → dann kein Zoom.
  passeEin(adressIds) {
    const ids = new Set(adressIds);
    const f = this.map.querySourceFeatures("adressen", { sourceLayer: "adressen" }).filter((x) => ids.has(x.properties.id));
    if (!f.length) return false;
    const b = new maplibregl.LngLatBounds();
    for (const x of f) b.extend(x.geometry.coordinates);
    this.map.fitBounds(b, { padding: 60, maxZoom: 16, duration: 600 });
    return true;
  }

  // Koordinate eines Punktes aus den geladenen Kacheln (für die Liste → Karte-Kopplung).
  position(adressId) {
    const f = this.map.querySourceFeatures("adressen", { sourceLayer: "adressen", filter: ["==", ["get", "id"], adressId] });
    return f.length ? f[0].geometry.coordinates : null;
  }

  zeigePopup(lngLat, html) { this.popup.setLngLat(lngLat).setHTML(html).addTo(this.map); }
  schliessePopup() { this.popup.remove(); }
}
