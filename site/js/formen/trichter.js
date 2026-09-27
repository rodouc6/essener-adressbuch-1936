// site/js/formen/trichter.js — Trichter aus Kennzahlen (Kapitel 0 „Die Datenbasis“, Spec 2026-09-27 §3):
// Stufen als Balken untereinander, Breite proportional zur ersten Stufe; eine Stufe darf Segmente tragen
// (Hand / Regel / Vorschlag), schraffiert, wo nichts von Hand geprüft ist. Rein, ohne DOM.
import { esc, formatProzent, formatZahl, r2, schraffurDefs, schraffurId, svgKopf } from "./skalen.js";

const RAND = 8;
const BESCHRIFTUNG = 0.32;      // Anteil der Breite für den Stufennamen
const WERTSPALTE = 150;         // Platz für „x von y (z %)“
const ZEILE_MAX = 56;

// Wert einer Kennzahl oder null, wenn sie fehlt (alter Export) — null wird nie gerechnet, nur angezeigt.
const wertVon = (kz, aus) => (typeof kz[aus] === "number" && Number.isFinite(kz[aus]) ? kz[aus] : null);
const anteil = (wert, basis) => (wert === null || !basis ? 0 : wert / basis);
const wertText = (wert, basis, erste) => wert === null ? "—" : erste ? formatZahl(wert) : `${formatZahl(wert)} von ${formatZahl(basis)} (${formatProzent(anteil(wert, basis))})`;

export function zeige(ansicht, daten, optionen = {}) {
  const breite = optionen.breite || 600;
  const hoehe = optionen.hoehe || 300;
  const kz = (daten && daten.kennzahlen) || {};
  const stufen = Array.isArray(ansicht.stufen) ? ansicht.stufen : [];
  const erklaerungen = ansicht.erklaerungen || {};
  const basis = stufen.length ? wertVon(kz, stufen[0].aus) : null;
  const basisName = stufen.length ? stufen[0].name : "";
  const oben = optionen.titel ? 30 : RAND;
  const zeile = Math.min(ZEILE_MAX, Math.max(18, (hoehe - oben - RAND) / Math.max(1, stufen.length)));
  const beschriftung = Math.min(200, breite * BESCHRIFTUNG);
  const maxBreite = Math.max(10, breite - beschriftung - WERTSPALTE - RAND);
  const werte = [];
  const legende = [];
  const muster = [];
  const teile = [];
  if (optionen.titel) teile.push(`<text x="${RAND}" y="18" class="titel">${esc(optionen.titel)}</text>`);

  stufen.forEach((s, i) => {
    const wert = wertVon(kz, s.aus);
    const y = oben + i * zeile;
    const h = Math.max(6, zeile - 8);
    const b = basis ? Math.min(maxBreite, maxBreite * anteil(wert, basis)) : 0;
    const segmente = Array.isArray(s.segmente) ? s.segmente : [];
    teile.push(`<text x="${RAND}" y="${r2(y + h / 2 + 4)}" class="name">${esc(s.name)}</text>`);
    teile.push(`<text x="${r2(beschriftung + b + 6)}" y="${r2(y + h / 2 + 4)}" class="wert">${esc(wertText(wert, basis, i === 0))}</text>`);
    if (!segmente.length) {
      werte.push({ id: s.aus, name: s.name, wert, basis, basisName, anteil: anteil(wert, basis), erklaerung: erklaerungen[s.aus] || "", muster: s.muster || "" });
      teile.push(`<rect class="einheit" data-id="${esc(s.aus)}" x="${r2(beschriftung)}" y="${r2(y)}" width="${r2(b)}" height="${r2(h)}" fill="${esc(s.farbe)}"><title>${esc(`${s.name}: ${wertText(wert, basis, i === 0)}`)}</title></rect>`);
      return;
    }
    // Stufe mit Segmenten: ein blasser Grund in Stufenbreite, darauf die Segmente als Einheiten. Die
    // Segmentbreiten sind auf die Stufenbreite begrenzt — ein Kuratierungsfehler darf nicht überlaufen.
    teile.push(`<rect class="grund" x="${r2(beschriftung)}" y="${r2(y)}" width="${r2(b)}" height="${r2(h)}" fill="${esc(s.farbe)}" opacity=".25"></rect>`);
    let x = beschriftung;
    for (const seg of segmente) {
      const sw = wertVon(kz, seg.aus);
      const sb = Math.max(0, Math.min(beschriftung + b - x, maxBreite * anteil(sw, basis)));
      let fill = seg.farbe;
      if (seg.muster === "schraffur") { const id = schraffurId(seg.aus); muster.push({ id, farbe: seg.farbe }); fill = `url(#${id})`; }
      werte.push({ id: seg.aus, name: seg.name, wert: sw, basis, basisName, anteil: anteil(sw, basis), erklaerung: erklaerungen[seg.aus] || "", muster: seg.muster || "" });
      legende.push({ name: seg.name, farbe: seg.farbe, text: seg.muster === "schraffur" ? "nicht von Hand geprüft" : seg.name, muster: seg.muster || "" });
      teile.push(`<rect class="einheit" data-id="${esc(seg.aus)}" x="${r2(x)}" y="${r2(y)}" width="${r2(sb)}" height="${r2(h)}" fill="${esc(fill)}"><title>${esc(`${seg.name}: ${wertText(sw, basis, false)}`)}</title></rect>`);
      x += sb;
    }
  });
  const svg = svgKopf(breite, hoehe) + schraffurDefs(muster) + teile.join("") + "</svg>";
  const zahlen = { N: basis || 0, n_aus: 0, unter_min: 0, einheiten: werte.length, hinweis: `Stand ${kz.stand || "unbekannt"}` };
  return { svg, legende, zahlen, werte };
}
