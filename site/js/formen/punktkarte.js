// site/js/formen/punktkarte.js — Punktkarte des Bergbau-Kapitels (Spec 2026-09-28 §4): ein Kreis je Hexfeld und
// Gruppe, Kreisfläche = eingetragene Personen (absolut, kein min_n). Drei Zustände derselben Kreise:
// gesammelt (Packungen nebeneinander, nach Größe), karten (eine kleine Karte je Gruppe), haeuser (ein Punkt je
// Haus im Zechenbesitz, Farbe nach Gesellschaft). `zeige` baut das SVG, `aktualisiere` verschiebt die vorhandenen
// Kreise — die CSS-Transition macht daraus den fließenden Übergang. Rein, ohne DOM (node:test).
import { esc, formatZahl, GRAU, leer, svgKopf } from "./skalen.js";

const COS = Math.cos((51.45 * Math.PI) / 180);
const K_MAP = 0.62;            // Radius auf der Karte relativ zur Packung
const R_MIN_KARTE = 1.6;
const R_HAUS = 2.4;
const ABSTAND = 40;            // zwischen zwei Packungen
// Schlägel und Eisen (site/bilder/zeche.svg, Wikimedia Commons, gemeinfrei) als Symbol im SVG.
const ZECHE_PFAD = "M 90.99997,385.61425 C 76.28281,380.5685 74.6516,379.13624 71.50838,368.49999 C 68.56032,358.52412 68.56171,357.13217 71.52034,356.5208 C 73.21478,356.17066 90.71541,338.46781 124.92406,302.49999 C 152.90991,273.07499 179.38947,245.33909 183.76755,240.86465 C 189.73363,234.76725 191.51128,232.34851 190.86383,231.20917 C 189.03292,227.98729 112.69583,147.78913 110.7488,147.04198 C 109.99268,146.75183 107.99981,147.97368 106.32019,149.75721 C 102.45213,153.86459 83.49183,179.15596 72.02799,195.49999 C 67.20581,202.37499 62.71192,207.94959 62.04156,207.888 C 61.37121,207.8264 51.29305,200.1764 39.64565,190.888 L 18.46857,173.99999 L 21.30869,171.49999 C 22.87076,170.12499 28.60027,162.47499 34.04094,154.49999 C 49.87877,131.28472 67.28445,108.63548 75.95969,99.95299 C 87.69483,88.20805 153.57535,39.49999 157.72593,39.49999 C 158.79371,39.49999 164.74554,46.38406 173.22951,57.43189 C 182.63996,69.68619 187.89923,75.69546 189.84016,76.41131 C 191.40227,76.98745 192.52727,77.88552 192.34016,78.40703 C 192.15306,78.92854 181.87497,86.97932 169.49997,96.29765 C 157.12497,105.61597 143.76138,116.24354 139.8031,119.91447 C 129.41402,129.54935 128.93314,128.3951 153.70152,153.27489 C 178.56659,178.2518 240.5476,238.33592 301.99997,297.03474 C 327.29997,321.20111 351.18404,344.01703 355.07568,347.73679 C 359.62155,352.08188 362.97485,354.49999 364.45451,354.49999 C 366.65347,354.49999 366.72626,354.73647 366.06399,359.72893 C 364.95732,368.07141 361.50493,375.58925 357.5628,378.24093 C 353.85538,380.73472 346.71808,383.01724 339.45908,384.03051 L 334.91819,384.66436 L 275.54278,321.05428 C 242.88631,286.06873 215.85831,257.56924 215.48056,257.72209 C 215.10281,257.87493 190.37558,285.67499 160.53115,319.49999 C 130.68673,353.32499 104.63313,382.65533 102.63427,384.67851 L 98.99997,388.35704 L 90.99997,385.61425 z M 226.062,220.20497 L 214.12403,208.91143 L 250.14533,171.12282 C 280.54977,139.22665 286.16664,132.88172 286.16664,130.43241 C 286.16664,127.92877 282.76007,124.35824 261.3393,104.4101 C 247.68427,91.69382 236.76083,80.88693 237.06499,80.39479 C 237.36915,79.90265 238.53459,79.49999 239.65487,79.49999 C 240.92465,79.49999 248.40919,73.09778 259.52883,62.49999 C 269.33924,53.14999 277.84725,45.49999 278.43552,45.49999 C 279.02379,45.49999 289.66833,55.39999 302.09004,67.49999 C 325.64913,90.44892 327.29856,91.59 330.99997,87.49999 C 331.99546,86.39999 333.5277,85.50591 334.40496,85.51314 C 335.28221,85.52037 339.14474,88.19986 342.98834,91.46756 C 347.44836,95.25931 351.04777,97.51577 352.93711,97.70441 L 355.89752,97.99999 L 352.56336,101.7862 C 350.72957,103.86862 349.0756,106.89157 348.88788,108.50387 C 348.58682,111.08954 349.50487,112.26478 356.67119,118.46765 C 361.13973,122.33544 365.29175,125.50435 365.89789,125.50968 C 366.89652,125.51847 411.50902,211.55144 410.91976,212.3321 C 410.78188,212.51477 393.64353,203.58156 372.83452,192.48054 L 334.99997,172.29686 L 323.48495,160.89843 C 317.15169,154.62929 311.68592,149.49999 311.33879,149.49999 C 310.99166,149.49999 294.41419,167.94999 274.49997,190.49999 C 254.58575,213.04999 238.22653,231.49966 238.14614,231.49925 C 238.06574,231.49885 232.62788,226.41642 226.062,220.20497 z";

export const raster = (breite) => ({ spalten: breite >= 600 ? 2 : 1 });
const ringe = (g) => (!g ? [] : g.type === "MultiPolygon" ? g.coordinates.flat() : g.type === "Polygon" ? g.coordinates : []);

// Bounding-Box der Stadtteile in der Plattkarte (x = lon·cos φ, y = −lat).
function box(polygone) {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const f of polygone.features) for (const r of ringe(f.geometry)) for (const [lon, lat] of r) {
    const x = lon * COS, y = -lat;
    if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
  }
  return { minX, maxX, minY, maxY };
}

// Projektion in ein Rechteck; gibt xy(lon, lat) → [x, y] zurück.
function projektion(b, x0, y0, w, h) {
  const s = Math.min(w / (b.maxX - b.minX || 1), h / (b.maxY - b.minY || 1));
  const ox = x0 + (w - (b.maxX - b.minX) * s) / 2, oy = y0 + (h - (b.maxY - b.minY) * s) / 2;
  return { s, xy: (lon, lat) => [ox + (lon * COS - b.minX) * s, oy + (-lat - b.minY) * s] };
}

const pfad = (polygone, p) => polygone.features.map((f) => ringe(f.geometry).map((r) => "M" + r.map(([lon, lat]) => p.xy(lon, lat).map((v) => v.toFixed(1)).join(",")).join("L") + "Z").join("")).join("");

const zechenAktiv = (zechen) => (zechen && Array.isArray(zechen.features) ? zechen.features : []).filter((f) => f.properties && f.properties.aktiv_1936 && f.geometry && f.geometry.type === "Point");
const zechenIn = (p, zechen) => (p ? zechen.map((z) => { const [x, y] = p.xy(z.geometry.coordinates[0], z.geometry.coordinates[1]); return { x, y, name: z.properties.name }; }) : []);

// Alles, was Zeichnen und Aktualisieren gemeinsam brauchen: Kreise mit Ziel-Lage, Kartenfelder, Titel, Legende, Zahlen.
export function berechne(ansicht, daten, optionen = {}) {
  const P = daten.punkte;
  const breite = optionen.breite || 600, hoehe = optionen.hoehe || 500;
  const zustand = (ansicht.punkte && ansicht.punkte.zustand) || "gesammelt";
  const hervor = new Set((ansicht.punkte && ansicht.punkte.hervor) || []);
  const farbeJe = new Map(); const nameJe = new Map();
  for (const g of ansicht.gruppen) for (const k of g.aus) { if (!farbeJe.has(k)) { farbeJe.set(k, g.farbe); nameJe.set(k, g.name); } }
  const b = daten.polygone && daten.polygone.features && daten.polygone.features.length ? box(daten.polygone) : null;
  const zechen = zechenAktiv(daten.zechen);

  if (zustand === "haeuser") {
    const rand = 16;
    const p = b ? projektion(b, rand, rand, breite - 2 * rand, hoehe - 2 * rand - 20) : null;
    const kreise = []; let ringeN = 0; const jeGes = new Map();
    for (const h of P.haeuser || []) {
      const [x, y] = p ? p.xy(h.lon, h.lat) : [0, 0];
      const inGruppe = farbeJe.has(h.eig);
      const ring = h.stufe !== "haus"; if (ring) ringeN += 1;
      jeGes.set(h.eig, (jeGes.get(h.eig) || 0) + 1);
      kreise.push({ id: h.id, gruppe: h.eig, x, y, r: R_HAUS, farbe: inGruppe ? farbeJe.get(h.eig) : GRAU, ring, gedimmt: false,
        zeile: `${inGruppe ? nameJe.get(h.eig) : "übrige Bergbau-Eigentümer"} · ${ring ? "nur straßengenau" : "hausgenau"}` });
    }
    const karten = [{ gruppe: "haeuser", x: rand, y: rand, w: breite - 2 * rand, h: hoehe - 2 * rand - 20, titel: "", pfad: b && p ? pfad(daten.polygone, p) : "",
      zechen: zechenIn(p, zechen), sichtbar: true }];
    const legende = [...ansicht.gruppen.map((g) => ({ name: g.name, farbe: g.farbe, text: `${g.name} · ${formatZahl(g.aus.reduce((s, k) => s + (jeGes.get(k) || 0), 0))}` })),
      { name: "übrige", farbe: GRAU, text: "übrige Bergbau-Eigentümer" },
      { name: "ring", farbe: null, text: `Ring: nur straßengenau oder Stadtplan 1935 (${formatZahl(ringeN)})` },
      { name: "zechen", farbe: null, text: "Schlägel und Eisen: Zechen in Förderung 1936, Betreiber nicht zugeordnet" }];
    const N = kreise.length;
    const zahlen = { N, n_aus: 0, unter_min: 0, einheiten: N, einheiten_gesamt: N, hinweis: `${formatZahl(N)} geprüfte Häuser der Klasse Bergbau, ein Punkt je Haus` };
    return { breite, hoehe, kreise, karten, titel: [], legende, zahlen, zustand };
  }

  // gesammelt / karten: Gruppen in Kapitelreihenfolge, Packung je Gruppe nach Größe sortiert nebeneinander.
  const gruppen = ansicht.gruppen.map((g) => ({ name: g.name, farbe: g.farbe, schluessel: g.aus[0], n: (P.gruppen.find((x) => x.id === g.aus[0]) || { n: 0 }).n }));
  const reihe = [...gruppen].sort((a, c) => c.n - a.n);
  const ext = {}; for (const g of gruppen) { const ps = P.hex[g.schluessel] || []; ext[g.schluessel] = ps.length ? Math.max(...ps.map((k) => Math.hypot(k.x, k.y) + k.r)) : 4; }
  const kPack = Math.min(1.3, (breite - 2 * ABSTAND) / (reihe.reduce((s, g) => s + 2 * ext[g.schluessel], 0) + ABSTAND * (reihe.length - 1)));
  const mitte = {}; { let x = ABSTAND; for (const g of reihe) { x += ext[g.schluessel] * kPack; mitte[g.schluessel] = [x, hoehe / 2 - 24]; x += ext[g.schluessel] * kPack + ABSTAND; } }
  const { spalten } = raster(breite);
  const zeilen = Math.ceil(gruppen.length / spalten);
  const fw = breite / spalten, fh = (hoehe - 20) / zeilen;
  const karten = gruppen.map((g, i) => {
    const x = (i % spalten) * fw, y = Math.floor(i / spalten) * fh;
    const p = b ? projektion(b, x + 10, y + 20, fw - 20, fh - 26) : null;
    return { gruppe: g.schluessel, x, y, w: fw, h: fh, titel: `${g.name} · ${formatZahl(g.n)}`, pfad: b && p ? pfad(daten.polygone, p) : "", p,
      zechen: zechenIn(p, zechen), sichtbar: zustand === "karten" };
  });
  const kreise = [];
  for (const g of gruppen) {
    const k = karten.find((c) => c.gruppe === g.schluessel);
    const gedimmt = hervor.size > 0 && !hervor.has(g.name);
    for (const pkt of P.hex[g.schluessel] || []) {
      let x, y, r;
      if (zustand === "karten" && k.p) { [x, y] = k.p.xy(pkt.lon, pkt.lat); r = Math.max(R_MIN_KARTE, pkt.r * kPack * K_MAP); }
      else { x = mitte[g.schluessel][0] + pkt.x * kPack; y = mitte[g.schluessel][1] + pkt.y * kPack; r = pkt.r * kPack; }
      kreise.push({ id: `${pkt.id}|${g.schluessel}`, gruppe: g.schluessel, x, y, r, farbe: g.farbe, ring: false, gedimmt,
        zeile: `${g.name} · ${formatZahl(pkt.n)} eingetragene Personen · Feld ${pkt.id}` });
    }
  }
  const titel = reihe.map((g) => ({ gruppe: g.schluessel, x: mitte[g.schluessel][0], y: mitte[g.schluessel][1] + ext[g.schluessel] * kPack + 18,
    name: g.name, wert: `${formatZahl(g.n)} eingetragene Personen`, sichtbar: zustand === "gesammelt" }));
  const N = gruppen.reduce((s, g) => s + g.n, 0);
  const kz = daten.kennzahlen || {};
  const n_aus = Math.max(0, (kz.teil_i_n || 0) - (kz.beruf_geprueft_n || 0));
  const zahlen = { N, n_aus, unter_min: 0, einheiten: kreise.length, einheiten_gesamt: kreise.length, hinweis: `${formatZahl(N)} eingetragene Personen mit Bergbau-Beruf, ${formatZahl(n_aus)} Einträge ohne geprüften Beruf ausgeschlossen` };
  const legende = [...gruppen.map((g) => ({ name: g.name, farbe: g.farbe, text: `${g.name} · ${formatZahl(g.n)}` })),
    { name: "mass", farbe: null, text: `Kreisfläche = eingetragene Personen je Hexfeld (120 m Kante), größter Wert ${formatZahl(P.maxn)}` },
    { name: "zechen", farbe: null, text: "Schlägel und Eisen: Zechen in Förderung 1936" }];
  return { breite, hoehe, kreise, karten, titel, legende, zahlen, zustand };
}

const kreisHtml = (k) => `<circle class="einheit p${k.gedimmt ? " gedimmt" : ""}" data-id="${esc(k.id)}" data-gruppe="${esc(k.gruppe)}" data-zeile="${esc(k.zeile)}" style="transform: translate(${k.x.toFixed(1)}px, ${k.y.toFixed(1)}px)" r="${k.r.toFixed(2)}" fill="${k.ring ? "none" : esc(k.farbe)}"${k.ring ? ` stroke="${esc(k.farbe)}" stroke-width="1.2"` : ""}><title>${esc(k.zeile)}</title></circle>`;

export function zeige(ansicht, daten, optionen = {}) {
  if (!daten || !daten.punkte || !Array.isArray(daten.punkte.gruppen)) return leer("Kapiteldaten des Bergbau-Kapitels fehlen");
  const b = berechne(ansicht, daten, optionen);
  const t = [svgKopf(b.breite, b.hoehe), `<defs><symbol id="pk-zeche" viewBox="0 0 430 430"><path d="${ZECHE_PFAD}"/></symbol></defs>`];
  for (const k of b.karten) {
    t.push(`<g class="karte" data-g="${esc(k.gruppe)}" style="opacity:${k.sichtbar ? 1 : 0}"><path class="umriss" d="${k.pfad}"/>`);
    if (k.titel) t.push(`<text class="karte-titel" x="${(k.x + 12).toFixed(1)}" y="${(k.y + 14).toFixed(1)}">${esc(k.titel)}</text>`);
    for (const z of k.zechen) t.push(`<use class="zeche" href="#pk-zeche" x="${(z.x - 6).toFixed(1)}" y="${(z.y - 6).toFixed(1)}" width="12" height="12"><title>${esc(z.name)}</title></use>`);
    t.push(`</g>`);
  }
  for (const k of b.kreise) t.push(kreisHtml(k));
  for (const ti of b.titel) t.push(`<text class="gruppe-titel" data-g="${esc(ti.gruppe)}" text-anchor="middle" x="${ti.x.toFixed(1)}" y="${ti.y.toFixed(1)}" style="opacity:${ti.sichtbar ? 1 : 0}">${esc(ti.name)}<tspan class="wert" x="${ti.x.toFixed(1)}" dy="15">${esc(ti.wert)}</tspan></text>`);
  t.push("</svg>");
  return { svg: t.join(""), legende: b.legende, zahlen: b.zahlen };
}

// Verschiebt die vorhandenen Kreise auf die Lage des neuen Zustands (Übergang per CSS-Transition auf transform/r).
// Voraussetzung: das SVG stammt aus `zeige` mit denselben Gruppen und einem Zustand ≠ haeuser (perspektiven.js prüft das).
export function aktualisiere(svgEl, ansicht, daten, optionen = {}) {
  const b = berechne(ansicht, daten, optionen);
  const je = new Map(b.kreise.map((k) => [k.id, k]));
  for (const el of svgEl.querySelectorAll("circle.p")) {
    const k = je.get(el.dataset.id); if (!k) continue;
    el.style.transform = `translate(${k.x.toFixed(1)}px, ${k.y.toFixed(1)}px)`;
    el.setAttribute("r", k.r.toFixed(2));
    el.classList.toggle("gedimmt", k.gedimmt);
  }
  for (const g of svgEl.querySelectorAll("g.karte")) { const k = b.karten.find((c) => c.gruppe === g.dataset.g); g.style.opacity = k && k.sichtbar ? 1 : 0; }
  for (const t of svgEl.querySelectorAll("text.gruppe-titel")) { const ti = b.titel.find((x) => x.gruppe === t.dataset.g); t.style.opacity = ti && ti.sichtbar ? 1 : 0; }
  return { legende: b.legende, zahlen: b.zahlen };
}
