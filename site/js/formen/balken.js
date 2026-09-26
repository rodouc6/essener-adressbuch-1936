// site/js/formen/balken.js — Gesamtbalken (ein Balken für alle Einheiten) oder ein Balken je Einheit.
// Die Segmente sind proportional zu N + n_aus; das letzte Segment ist immer grau „ausgeschlossen“.
import { werteJeEinheit, filterEinheiten } from "../daten_ebenen.js";
import { esc, formatProzent, formatZahl, GRAU, einheitKlasse, nennerText, r2, svgKopf, zahlenZeile } from "./skalen.js";

const RAND = 8;
const ZEILE = 26;
const WERTSPALTE = 54;

// Beschriftung rechts neben dem Balken einer Einheit: der Wert des Maßes, das die Ansicht trägt.
// Ohne ihn behauptete der Kapiteltext eine Zahl, die im Bild gar nicht steht.
function wertText(w, ansicht) {
  if (ansicht.mass === "mischung") return (Number(w.mischung) || 0).toFixed(2).replace(".", ",");
  if (ansicht.mass === "dominant") return String(w.dominant ?? "");
  if (ansicht.mass === "dichte") return typeof w.wert === "number" ? `${formatZahl(w.wert)} je 1.000` : "—";
  return formatProzent(typeof w.wert === "number" ? w.wert : 0);
}

// Segmente eines Balkens: je Gruppe eines, danach das graue für die ausgeschlossenen Nennungen. `regel`
// (Besitz: Adressen, die nur per Regel Person → Privatperson klassifiziert sind) hängt an der Gruppe, die
// die Privatpersonen enthält, und steht im Hover-Text des Segments.
function segmente(ansicht, zaehler, n_aus, regel = 0) {
  const s = ansicht.gruppen.map((g) => ({ id: g.name, wert: zaehler[g.name] || 0, farbe: g.farbe, regel: g.aus.includes("privatperson") ? regel : 0 }));
  s.push({ id: "ausgeschlossen", wert: n_aus || 0, farbe: GRAU, regel: 0 });
  return s;
}

export const regelText = (n) => `davon ${formatZahl(n)} per Regel klassifiziert (Person ohne Firmenname → Privatperson, keine Handprüfung)`;

// Ein Balken mit Segmenten. `id` ist gesetzt, wenn der ganze Balken eine Einheit ist (je_einheit);
// dann tragen die Segmente selbst kein data-id, damit jede Einheit genau einmal anklickbar ist.
function balkenZeile(segs, x, y, breite, hoehe, summe, jeEinheit) {
  let px = x;
  const teile = [];
  for (const [i, seg] of segs.entries()) {
    const b = summe > 0 ? (seg.wert / summe) * breite : i === segs.length - 1 ? breite : 0;
    if (b <= 0) continue;
    const kopf = jeEinheit ? `<rect class="segment"` : `<rect class="einheit" data-id="${esc(seg.id)}"`;
    const titel = `${seg.id}: ${formatZahl(seg.wert)}${seg.regel > 0 ? `, ${regelText(seg.regel)}` : ""}`;
    teile.push(`${kopf} x="${r2(px)}" y="${r2(y)}" width="${r2(b)}" height="${r2(hoehe)}" fill="${esc(seg.farbe)}"><title>${esc(titel)}</title></rect>`);
    px += b;
  }
  return teile.join("");
}

export function zeige(ansicht, daten, optionen = {}) {
  const breite = optionen.breite || 600;
  const hoehe = optionen.hoehe || 200;
  const hervor = new Set(optionen.hervorheben || []);
  const alle = werteJeEinheit(ansicht, daten);
  const werte = filterEinheiten(alle, ansicht.filter);
  const zahlen = zahlenZeile(werte, alle);
  const legende = [...ansicht.gruppen.map((g) => ({ name: g.name, farbe: g.farbe, text: g.name })),
    { name: "ausgeschlossen", farbe: GRAU, text: "unbestimmt/ungeprüft" }];
  const teile = [svgKopf(breite, hoehe)];
  if (optionen.titel) teile.push(`<text x="${RAND}" y="18" class="titel">${esc(optionen.titel)}</text>`);
  const oben = optionen.titel ? 30 : RAND;

  if (ansicht.filter && ansicht.filter.je_einheit) {
    const nachRang = werte.every((w) => Number.isFinite(w.rang_nord));
    const sortiert = [...werte].sort((a, b) => (nachRang ? a.rang_nord - b.rang_nord
      : (typeof b.wert === "number" ? b.wert : 0) - (typeof a.wert === "number" ? a.wert : 0)));
    const zeile = Math.min(ZEILE, Math.max(10, (hoehe - oben - RAND) / Math.max(1, sortiert.length)));
    const beschriftung = Math.min(160, breite * 0.3);
    const balkenBreite = Math.max(10, breite - beschriftung - WERTSPALTE - RAND);
    for (const [i, w] of sortiert.entries()) {
      const y = oben + i * zeile;
      const h = Math.max(4, zeile - 4);
      const klasse = einheitKlasse(hervor.has(w.id), w.unter_min);
      const inhalt = w.unter_min
        ? `<rect class="segment" x="${r2(beschriftung)}" y="${r2(y)}" width="${r2(balkenBreite)}" height="${r2(h)}" fill="${GRAU}"></rect>`
          + `<text x="${r2(beschriftung + 6)}" y="${r2(y + h - 4)}" class="hinweis">unter ${formatZahl(ansicht.min_n)} ${nennerText(ansicht)}</text>`
        : balkenZeile(segmente(ansicht, w.zaehler, w.n_aus, w.regel), beschriftung, y, balkenBreite, h, w.N + w.n_aus, true)
          + `<text x="${r2(beschriftung + balkenBreite + 6)}" y="${r2(y + h - 4)}" class="wert">${esc(wertText(w, ansicht))}</text>`;
      teile.push(`<g class="${klasse}" data-id="${esc(w.id)}">`
        + `<text x="${RAND}" y="${r2(y + h - 4)}" class="name">${esc(w.name)}</text>${inhalt}</g>`);
    }
    teile.push("</svg>");
    return { svg: teile.join(""), legende, zahlen };
  }

  // Gesamtbalken: Summen je Gruppe über die gezeichneten Einheiten.
  const zaehler = {};
  for (const g of ansicht.gruppen) zaehler[g.name] = werte.reduce((s, w) => s + (w.zaehler[g.name] || 0), 0);
  const summe = zahlen.N + zahlen.n_aus;
  const regel = werte.reduce((s, w) => s + (w.regel || 0), 0);
  const h = Math.max(16, Math.min(48, hoehe - oben - 40));
  teile.push(balkenZeile(segmente(ansicht, zaehler, zahlen.n_aus, regel), RAND, oben, breite - 2 * RAND, h, summe, false));
  let x = RAND;
  for (const seg of segmente(ansicht, zaehler, zahlen.n_aus)) {
    const b = summe > 0 ? (seg.wert / summe) * (breite - 2 * RAND) : 0;
    if (b > 30) teile.push(`<text x="${r2(x + 4)}" y="${r2(oben + h + 14)}" class="wert">${formatProzent(summe ? seg.wert / summe : 0)}</text>`);
    x += b;
  }
  teile.push("</svg>");
  return { svg: teile.join(""), legende, zahlen };
}
