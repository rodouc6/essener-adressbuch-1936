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

export class Karte {
  constructor(container, zustand, ereignisse) {
    this.ereignisse = ereignisse;
    this.zustand = zustand;
    this.farbe = null;          // Themenfarbregel (Task 13) oder null
    this.treffer = new Set();
    this.auswahl = null;
    this.protokoll = new pmtiles.Protocol();
    maplibregl.addProtocol("pmtiles", this.protokoll.tile);
    this.map = new maplibregl.Map({
      container, style: STILE[zustand.karte], center: zustand.c || ESSEN_MITTE, zoom: zustand.z ?? 11,
      minZoom: 9, maxZoom: 18, attributionControl: { compact: true },
    });
    this.map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    this.map.addControl(new maplibregl.GeolocateControl({ trackUserLocation: false }), "top-right");
    this.map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");
    this.popup = new maplibregl.Popup({ closeButton: true, maxWidth: "320px", offset: 10 });
    this._bereit = new Promise((ok) => this.map.once("load", ok)).then(() => this.ebenenAufsetzen());
    this.map.on("moveend", () => {
      const c = this.map.getCenter();
      ereignisse.onBewegt(Math.round(this.map.getZoom() * 100) / 100, [+c.lng.toFixed(5), +c.lat.toFixed(5)]);
    });
  }

  bereit() { return this._bereit; }

  // Layer nur anlegen, wenn er (etwa durch einen zweiten, gleichzeitig gestarteten Stilwechsel) noch nicht existiert.
  _ebeneHinzufuegen(def) {
    if (!this.map.getLayer(def.id)) this.map.addLayer(def);
  }

  async ebenenAufsetzen() {
    const m = this.map;
    await ladeIcon(m, "kreis-gestrichelt", "bilder/kreis-gestrichelt.svg", true);
    await ladeIcon(m, "zeche", "bilder/zeche.svg", false);
    if (!m.getSource("adressen")) {
      m.addSource("adressen", { type: "vector", url: `pmtiles://${new URL(DATEN + "adressen.pmtiles", location.href)}`, promoteId: "id" });
    }
    if (!m.getSource("zechen")) m.addSource("zechen", { type: "geojson", data: DATEN + "zechen.geojson" });
    // Solange PLAN_FREIGEGEBEN false ist (Rechte am Dienst geo.essen.de ungeklärt), weder Quelle
    // noch Ebene anlegen — kein einziger Request an den Dienst, auch nicht über ?plan=1 (C1).
    if (PLAN_FREIGEGEBEN) {
      if (!m.getSource("stadtplan-1935")) {
        m.addSource("stadtplan-1935", {
          type: "raster", tileSize: 256, minzoom: 10, maxzoom: 17,
          tiles: [`${STADTPLAN_EXPORT}?bbox={bbox-epsg-3857}&bboxSR=3857&imageSR=3857&size=256,256&format=png32&transparent=true&f=image`],
          attribution: "Stadtplan 1935: Stadt Essen / Historischer Verein",
        });
      }
      this._ebeneHinzufuegen({ id: "stadtplan-1935", type: "raster", source: "stadtplan-1935",
                   layout: { visibility: "none" }, paint: { "raster-opacity": 0 } });
    }
    const sl = "adressen";
    this._ebeneHinzufuegen({ id: "adressen-haus", type: "circle", source: "adressen", "source-layer": sl,
                 filter: ["==", ["get", "stufe"], "haus"], paint: { "circle-stroke-width": 0 } });
    this._ebeneHinzufuegen({ id: "adressen-ungenau", type: "symbol", source: "adressen", "source-layer": sl,
                 filter: ["!=", ["get", "stufe"], "haus"],
                 layout: { "icon-image": "kreis-gestrichelt", "icon-allow-overlap": true, "icon-ignore-placement": true } });
    this._ebeneHinzufuegen({ id: "adressen-auswahl", type: "circle", source: "adressen", "source-layer": sl,
                 filter: ["==", ["get", "id"], ""],
                 paint: { "circle-radius": 14, "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": FARBEN.auswahl, "circle-stroke-width": 3 } });
    this._ebeneHinzufuegen({ id: "zechen", type: "symbol", source: "zechen", filter: ["==", ["get", "aktiv_1936"], true],
                 layout: { visibility: "none", "icon-image": "zeche", "icon-size": 0.6, "text-field": ["get", "name"],
                           "text-size": 11, "text-offset": [0, 1.4], "text-anchor": "top", "icon-allow-overlap": true },
                 paint: { "text-halo-color": "#fff", "text-halo-width": 1.5 } });
    // Klick-/Hover-Handler sind an die Karte gebunden, nicht an den Stil — bei jedem Stilwechsel
    // neu anzuhängen würde sie stapeln (mehrfache Popups/Klicks). Daher nur einmal registrieren.
    if (!this._handlerAngehaengt) {
      this._handlerAngehaengt = true;
      for (const id of ["adressen-haus", "adressen-ungenau"]) {
        m.on("click", id, (e) => this.ereignisse.onKlick(e.features[0].properties.id, e.lngLat));
        m.on("mouseenter", id, (e) => { m.getCanvas().style.cursor = "pointer"; this.ereignisse.onHover(e.features[0].properties.id, e.lngLat); });
        m.on("mouseleave", id, () => { m.getCanvas().style.cursor = ""; this.ereignisse.onHover(null, null); });
      }
      m.on("click", "zechen", (e) => {
        const p = e.features[0].properties;
        const jahre = p.jahre_unbekannt ? "Betriebsjahre unbekannt" : `in Betrieb ${esc(p.betrieb_von)}–${esc(p.betrieb_bis)}`;
        // Nur auf de.wikipedia.org verlinken — quelle ist Rohdaten aus der Kuratierung, kein
        // beliebiges Ziel soll unbeaufsichtigt verlinkt werden (I1).
        const link = p.quelle && WIKIPEDIA_QUELLE.test(p.quelle)
          ? `<br><a href="${esc(p.quelle)}" target="_blank" rel="noopener">Wikipedia</a>` : "";
        this.zeigePopup(e.lngLat, `<b>${esc(p.name)}</b><br>${esc(p.stadtteil || "")}<br>${jahre}${link}`);
      });
    }
    this.setzeFilter(this.zustand);
    this.setzePlan(this.zustand.plan);
    this.setzeZechen(this.zustand.zechen);
    this.setzeTreffer(this.treffer.size ? [...this.treffer] : null);
    this.setzeAuswahl(this.auswahl);
  }

  setzeStil(name) {
    // Einen noch laufenden Warter eines vorigen Stilwechsels abbrechen, sonst setzen zwei sich
    // überlappende Wechsel beide ebenenAufsetzen() auf demselben Stil auf ("Layer already exists"),
    // und eine veraltete, noch laufende ebenenAufsetzen()-Ausführung darf ihre (inzwischen wieder
    // ersetzten) Ebenen nicht mehr anlegen (_stilGen-Generationszähler, vor dem Aufruf von
    // ebenenAufsetzen() geprüft).
    if (this._stilRaf) { cancelAnimationFrame(this._stilRaf); this._stilRaf = null; }
    const gen = (this._stilGen = (this._stilGen || 0) + 1);
    this.map.setStyle(STILE[name]);
    // MapLibre 4.7.1 feuert nach setStyle() kein "style.load" auf der Map (nur auf dem internen
    // Style-Objekt, ohne Weiterleitung) — daher auf isStyleLoaded() warten statt auf das Ereignis.
    // isStyleLoaded() wird beim Laden eines entfernten Stils (URL) kurz true, bevor MapLibre seine
    // interne Rekonziliation (Sprite/Glyphen/Quellen des neuen Stils) abgeschlossen hat; währenddessen
    // von ebenenAufsetzen() hinzugefügte Ebenen verschwinden binnen ~100 ms spurlos wieder (beobachtet
    // beim Grundkartenwechsel, Task 15).
    // Erst mit dem "styledata"-Ereignis auf isStyleLoaded() zu prüfen (die ursprüngliche Fassung) oder
    // auf das nächste "idle"-Ereignis zu warten, erwies sich unter schnell aufeinanderfolgenden
    // Stilwechseln als unzuverlässig: ruft man setzeStil() innerhalb weniger Millisekunden mehrfach auf
    // (z. B. drei rasche Klicks), bleibt für einen der dazwischenliegenden Aufrufe manchmal jedes
    // weitere "styledata"/"idle"-Ereignis aus — vermutlich, weil MapLibres interner Ladezyklus für den
    // inzwischen überholten Zwischenstand keine weitere Arbeit mehr anstößt und daher auch keine
    // weiteren Ereignisse mehr feuert; die Wartepromise hing dann dauerhaft. Ein reines
    // rAF-Polling auf isStyleLoaded() hängt nicht von einem bestimmten Ereignis ab und läuft daher
    // auch dann weiter, wenn "styledata"/"idle" ausbleiben; nach dem ersten true wird zusätzlich ein
    // zweiter Animationsframe abgewartet (Puffer für den Rekonziliationsabschluss). Geprüft mit drei
    // raschen Wechseln plus einem vierten nach dem Beruhigen: keine Fehler, alle Ebenen vorhanden,
    // `adressen-haus` bleibt auch 2 s nach dem letzten Wechsel bestehen.
    this._bereit = new Promise((ok) => {
      const pruefen = () => {
        // Überholt von einem späteren setzeStil(): trotzdem ok() rufen, sonst löst dieser Warter nie
        // auf und alles, was auf ihn wartet (z. B. ein awaiteter Aufrufer), hängt dauerhaft (I4).
        if (gen !== this._stilGen) return ok();
        if (!this.map.isStyleLoaded()) { this._stilRaf = requestAnimationFrame(pruefen); return; }
        this._stilRaf = requestAnimationFrame(() => {
          if (gen !== this._stilGen) return ok();
          this._stilRaf = null;
          ok();
        });
      };
      // Erst Loading überhaupt beobachten, nicht sofort synchron prüfen: unmittelbar nach setStyle()
      // liest isStyleLoaded() noch den Wert des alten Stils (kurzzeitig „true“), bevor der Browser die
      // anstehende Stiländerung überhaupt verarbeitet hat — ein rAF Abstand genügt, um das zu vermeiden.
      this._stilRaf = requestAnimationFrame(pruefen);
    }).then(() => {
      if (gen !== this._stilGen) return;     // überholt: die aktuelle Generation setzt die Ebenen selbst auf
      return this.ebenenAufsetzen();
    });
    return this._bereit;
  }

  // Farbe und Größe aus Zustand + Themenregel ableiten und auf beide Adressebenen legen.
  setzeFilter(z) {
    this.zustand = z;
    const m = this.map;
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

  // Ohne Treffermenge sind alle Punkte voll sichtbar; mit Treffermenge nur die Treffer, der Rest gedimmt.
  _deckkraftSetzen() {
    const d = this.treffer.size ? ["case", ["boolean", ["feature-state", "treffer"], false], 0.9, 0.25] : 0.9;
    this.map.setPaintProperty("adressen-haus", "circle-opacity", d);
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
