import { Karte } from "./karte.js";
import { Lader } from "./daten.js";
import { Sidebar } from "./sidebar.js";
import { vorschlaege, treffer } from "./suche.js";
import { liesZustand, schreibeZustand } from "./zustand.js";
import { popupHtml, esc } from "./popup.js";
import { steuerungHtml, abweichend } from "./steuerung.js";
import { dekodiereOderNull } from "./ansicht.js";
import { ladeEbenen, werteJeEinheit } from "./daten_ebenen.js";
import { ansichtTitel, werteFarben, legendeFuer } from "./ansicht_farben.js";
import { FARBEN, PLAN_FREIGEGEBEN, STILE } from "./konfig.js";
import { ladeThema, themenListe } from "./themen.js";
import { csvAusTreffern, herunterladen } from "./exportcsv.js";
import { strasseAusText } from "./strassenwahl.js";
import { ANZEIGE } from "./kategorien.js";

const lader = new Lader();
// PLAN_FREIGEGEBEN sperrt die Stadtplan-1935-Ebene hart: ein manipulierter ?plan=1-Link darf die
// Ebene nicht aktivieren, solange die Nutzungsrechte am Dienst geo.essen.de nicht geklärt sind (C1).
function gateZustand(z) { return PLAN_FREIGEGEBEN ? z : { ...z, plan: 0 }; }

// Grundkartenwahl in localStorage merken (Spec §4); localStorage kann in Privatmodus/mit
// blockiertem Speicher werfen — nie die Seite deswegen scheitern lassen (I5).
const KARTE_SPEICHER = "essen1936.karte";
function liesKarteSpeicher() {
  try {
    const v = localStorage.getItem(KARTE_SPEICHER);
    return v === "positron" || v === "liberty" ? v : null;
  } catch { return null; }
}
function schreibeKarteSpeicher(v) {
  try { localStorage.setItem(KARTE_SPEICHER, v); } catch { /* ignorieren */ }
}

let zustand = gateZustand(liesZustand(location.search));
// Nur ohne karte= in der URL auf den gespeicherten Wert zurückgreifen — ein expliziter Link/Reload
// mit karte= soll immer Vorrang vor localStorage haben.
if (!new URLSearchParams(location.search).has("karte")) {
  const gespeichert = liesKarteSpeicher();
  if (gespeichert) zustand = { ...zustand, karte: gespeichert };
}
let ergebnis = null;              // aktuelle Treffermenge
let auswahl = null;               // { art, ... } der Suche
let themaAktiv = null;            // aktives Thema mit farbregel und ebenen
let ansichtAktiv = null;          // normalisierte Ansicht (Spec §8) oder null
let ansichtWerte = [];            // Werte je Einheit der aktiven Ansicht
let ebenenVersprechen = null;     // ladeEbenen() nur einmal je Seite
let ebenenDaten = null;           // aufgelöste Ebenendaten (für Kennzahlen der Legende)
let ansichtFehler = false;        // ?ansicht= war nicht lesbar
const eigCache = new Map();       // adressId → Punkteigenschaften (aus Kacheln oder Adressscherbe)
const mobil = () => matchMedia("(max-width: 899px)").matches;

// Zeigt einen kurzen Hinweis statt einer hängenden UI, wenn ein Ladepfad scheitert (Task 9-Review).
function fehlerHinweis(fehler, kontext) {
  console.error(kontext, fehler);
  document.getElementById("inhalt").innerHTML = `<div class="hinweis warn">Daten konnten nicht geladen werden.</div>`;
}

const sidebar = new Sidebar(document.getElementById("sidebar"), lader, {
  onZustand: (patch) => setzeZustand(patch, false),
  onHausWaehlen: (id) => oeffneHaus(id, null),
  onEintragWaehlen: (eid, id) => oeffneHaus(id, eid),
  onVorschlag: (v) => waehleVorschlag(v),
  onAlleVorschlaege: (art) => alleVorschlaege(art),
  onZurueck: () => history.back(),
  onExport: () => exportiere(),
});
const karte = new Karte("karte", zustand, {
  onKlick: (id, lngLat) => klickPunkt(id, lngLat),
  onBewegt: (z, c) => setzeZustand({ z, c }, false, true),
  onHover: () => {},
});

// Punkteigenschaften einer Adresse: zuerst der Speicher, dann die geladenen Kartenkacheln (schnell,
// aber nur im aktuellen Viewport vorhanden), sonst die Adressscherbe (immer vollständig, aber ein
// Ladevorgang). Die Eigenschaften sind pro Build unveränderlich — der Speicher wird nie geleert.
async function eigVon(id) {
  if (eigCache.has(id)) return eigCache.get(id);
  const f = karte.map.querySourceFeatures("adressen", { sourceLayer: "adressen", filter: ["==", ["get", "id"], id] });
  if (f.length) { eigCache.set(id, f[0].properties); return f[0].properties; }
  const e = await lader.adresse(id);
  eigCache.set(id, e);
  return e;
}

function schreibeUrl(push) {
  const q = schreibeZustand(zustand);
  const url = location.pathname + (q ? "?" + q : "");
  if (push) history.pushState(zustand, "", url); else history.replaceState(zustand, "", url);
}

async function setzeZustand(patch, push, nurKarte = false) {
  const alt = zustand;
  zustand = { ...zustand, ...patch };
  schreibeUrl(push);
  if (nurKarte) return;
  // setzeStil() kann bei schnell aufeinanderfolgenden Wechseln nie auflösen (Karte meldet den
  // veralteten Warter ab, ohne ihn aufzulösen) — daher nicht awaiten, sonst hängt setzeZustand.
  // Die Karte wendet Filter/Plan/Zechen/Treffer/Auswahl in ebenenAufsetzen() selbst wieder an.
  if (alt.karte !== zustand.karte) { karte.setzeStil(zustand.karte); schreibeKarteSpeicher(zustand.karte); }
  if (alt.thema !== zustand.thema) await wendeThemaAn();
  if (alt.ansicht !== zustand.ansicht) await wendeAnsichtAn();
  // Bei einem Stilwechsel legt ebenenAufsetzen() die Ebenen erst neu an (asynchron, nicht
  // awaitet); ein sofortiger setzeFilter/setzePlan/setzeZechen hier würde noch auf die alten,
  // gerade abgebauten Layer zielen ("Cannot filter non-existing layer"). Nur anwenden, wenn sich
  // der Kartenstil in diesem Aufruf nicht geändert hat.
  if (alt.karte === zustand.karte) {
    karte.setzeFilter(zustand);
    karte.setzePlan(zustand.plan); karte.setzeZechen(zustand.zechen);
  }
  if (alt.beruf !== zustand.beruf || alt.eigentuemer !== zustand.eigentuemer || alt.ohdab !== zustand.ohdab) {
    if (zustand.beruf) auswahl = { art: "beruf", beruf: zustand.beruf };
    else if (zustand.eigentuemer) auswahl = { art: "eigentuemer", name: zustand.eigentuemer };
    else if (zustand.ohdab) auswahl = { art: "ohdab", ohdab: zustand.ohdab, name: await ohdabName(zustand.ohdab) };
    else auswahl = null;
    // Aus „Größte Eigentümer“ gewählt (sidebar.js) setzt nur den Zustand, nicht das Suchfeld — ohne das
    // hier nachzuholen bliebe der aktive Filter unsichtbar und „Suche leeren“ hätte nichts zum Leeren.
    if (zustand.eigentuemer) sidebar.suche.value = zustand.eigentuemer;
    if (zustand.ohdab) sidebar.suche.value = auswahl.name;
    await sucheAusfuehren();
  }
  else await zeigeInhalt();
  zeichneSteuerung(); zeichneLegende();
}

// Normbezeichnung zu einer OhdAB-Nummer nachschlagen (Suchfeld/CSV bei aktivem ?ohdab=…, Task 11).
async function ohdabName(id) {
  const liste = (await lader.berufeNorm()) || [];
  return (liste.find((z) => z[2] === id) || [])[1] || id;
}

async function wendeThemaAn() {
  const t = zustand.thema ? await ladeThema(lader, zustand.thema) : null;
  themaAktiv = t;
  sidebar.zeigeThema(t, t && t.zusatz && t.zusatz.eigentuemerliste ? await lader.eigentuemer() : null);
  karte.setzeFarbe(t ? t.farbregel : null);
  if (t && t.zusatz && t.zusatz.zechen && !zustand.zechen) zustand = { ...zustand, zechen: 1 };
  if (t && t.ebenen) zustand = { ...zustand, ebene: t.ebenen };
  schreibeUrl(false);   // vom Thema erzwungene Ebenen/Zechen auch in der URL abbilden
}

// Eine Ansicht aus der URL auf Karte, Sidebar und Legende legen (Spec §8). Die Ebenendaten
// (Kennzahlen je Straße/Stadtteil/Hexfeld) werden nur geladen, wenn wirklich eine Ansicht aktiv ist.
async function wendeAnsichtAn() {
  ansichtFehler = false;
  if (!zustand.ansicht) {
    ansichtAktiv = null; ansichtWerte = [];
    karte.setzeAnsicht(null, null); sidebar.zeigeAnsicht(null);
    return;
  }
  // Ein unlesbarer Parameter wird nicht stillschweigend zur Standardansicht: das wäre eine Karte,
  // die etwas anderes zeigt als der Link verspricht.
  const a = dekodiereOderNull(zustand.ansicht);
  if (!a) {
    ansichtFehler = true; ansichtAktiv = null; ansichtWerte = [];
    karte.setzeAnsicht(null, null); sidebar.zeigeAnsicht(null, "", true);
    return;
  }
  try {
    if (!ebenenVersprechen) ebenenVersprechen = ladeEbenen(lader);
    const ebenen = await ebenenVersprechen;
    ebenenDaten = ebenen;
    ansichtAktiv = a;
    ansichtWerte = werteJeEinheit(a, ebenen);
    karte.setzeAnsicht(a, werteFarben(ansichtWerte, a));
    sidebar.zeigeAnsicht(a, zustand.ansicht);
  } catch (fehler) {
    // Eine kaputte Ansicht darf die Kartenseite nicht lahmlegen — Karte bleibt ohne Einfärbung.
    console.error("Ansicht konnte nicht angewendet werden", fehler);
    ansichtAktiv = null; ansichtWerte = [];
    karte.setzeAnsicht(null, null); sidebar.zeigeAnsicht(null);
  }
}

async function zeigeInhalt() {
  if (ergebnis) sidebar.zeigeTreffer(zustand, ergebnis, await eigMap(ergebnis.adressIds), zustand.q);
  else { sidebar.zeigeSuche(zustand); themenListe(lader).then((l) => sidebar.zeigeThemenliste(l)); }
}

async function eigMap(ids) {
  const m = new Map();
  const paare = await Promise.all(ids.map(async (id) => [id, await eigVon(id)]));
  for (const [id, e] of paare) if (e) m.set(id, e);
  return m;
}

async function sucheAusfuehren() {
  try {
    if (!auswahl) { ergebnis = null; karte.setzeTreffer(null); await zeigeInhalt(); return; }
    ergebnis = await treffer(auswahl, lader);
    karte.setzeTreffer(ergebnis.adressIds);
    if (!karte.passeEin(ergebnis.adressIds) && ergebnis.adressIds.length) {
      // Kacheln der Treffer noch nicht geladen: einmal warten und erneut versuchen
      karte.map.once("idle", () => { karte.passeEin(ergebnis.adressIds); zeigeInhalt(); });
    }
    await zeigeInhalt();
    sidebar.setzeStufe("halb");
  } catch (fehler) {
    fehlerHinweis(fehler, "Suche fehlgeschlagen");
  }
}

async function waehleVorschlag(v) {
  sidebar.setzeVorschlaege(null);
  sidebar.suche.value = v.text;
  if (v.art === "person" || v.art === "firma") { setzeZustand({ q: v.text, id: v.adressId }, true, true); return oeffneHaus(v.adressId, v.eintragId); }
  if (v.art === "beruf") return setzeZustand({ q: "", eigentuemer: "", ohdab: "", beruf: v.beruf }, true);
  if (v.art === "eigentuemer") return setzeZustand({ q: "", beruf: "", ohdab: "", eigentuemer: v.name }, true);
  if (v.art === "ohdab") return setzeZustand({ q: "", beruf: "", eigentuemer: "", ohdab: v.ohdab }, true);
  // v.art === "strasse": v trägt bereits name/artName/ort/schluessel, treffer() lädt die IDs selbst.
  // q wird als reiner Name geschrieben (nicht v.text mit "(Ort)") — sonst kann strasseAusZustand()
  // die URL bei Reload/Zurück/Vor nicht mehr auflösen (Fix-Runde 1).
  auswahl = v;
  setzeZustand({ q: v.name, id: "" }, true, true);
  await sucheAusfuehren();
}

// "alle n anzeigen" unter einer Vorschlagsgruppe (Spec §6): bei Personen die volle Personensuche
// starten, bei Straßen/Firmen/Berufen stattdessen die Gruppe selbst ungekürzt nachladen.
async function alleVorschlaege(art) {
  const q = sidebar.suche.value;
  if (art === "personen") { sidebar.setzeVorschlaege(null); return sucheAusText(q); }
  try {
    sidebar.setzeVorschlaege(await vorschlaege(q, lader, { [art]: true }));
  } catch (fehler) {
    fehlerHinweis(fehler, "Vorschläge fehlgeschlagen");
  }
}

// q ohne Vorschlagsauswahl (Enter im Suchfeld, oder q= aus der URL — z. B. ein Straßenlink von
// der Startseite, Task 14 Amendment 1, oder ein Reload/Zurück/Vor auf einer Straßen-URL, Fix-
// Runde 1): zuerst im Straßenindex nachsehen (strasseAusText(), toleriert auch "Name (Ort)"),
// sonst Personensuche über den Text.
async function strasseAusZustand(q) {
  return strasseAusText(q, await lader.strassen());
}

async function sucheAusText(q) {
  const s = await strasseAusZustand(q);
  auswahl = s || { art: "person", q };
  setzeZustand({ q, id: "", beruf: "", eigentuemer: "", ohdab: "" }, true, true);
  await sucheAusfuehren();
}

async function oeffneHaus(id, eintragId) {
  try {
    const [eig, eintraege] = await Promise.all([eigVon(id), lader.scherbe(id)]);
    if (!eintraege) return;
    const e = eig || { id, stufe: "unbekannt", historisch: "", strasse_heute: "", hausnr: "", stadtteil: "", n_I: 0, n_II: 0, n_III: 0 };
    // id in der URL: Adress-ID, bei hervorgehobenem Eintrag "adressId.eintragId"
    setzeZustand({ id: eintragId ? `${id}.${eintragId}` : id }, true, true);
    karte.setzeAuswahl(id);
    // Kachel-Position bevorzugt (Kachel bereits geladen); außerhalb des Viewports (Kachel nicht
    // geladen) liefert die Adressscherbe lat/lon als Fallback (Task 13-Review).
    const pos = karte.position(id) || (eig && eig.lon != null && eig.lat != null ? [eig.lon, eig.lat] : null);
    if (pos) karte.fliegeZu(pos);
    sidebar.zeigeHaus(e, eintraege, eintragId, await lader.faksimile());
  } catch (fehler) {
    fehlerHinweis(fehler, "Hausansicht fehlgeschlagen");
  }
}

async function klickPunkt(id, lngLat) {
  try {
    const [eig, eintraege] = await Promise.all([eigVon(id), lader.scherbe(id)]);
    if (!eig || !eintraege) return;
    karte.setzeAuswahl(id);
    karte.zeigePopup(lngLat, popupHtml(eig, eintraege, mobil(), zustand.ebene));
    const el = karte.popup.getElement();
    el.querySelectorAll("[data-eintrag]").forEach((n) => n.addEventListener("click", () => oeffneHaus(id, n.dataset.eintrag)));
    el.querySelectorAll("[data-mehr]").forEach((n) => n.addEventListener("click", () => oeffneHaus(id, null)));
  } catch (fehler) {
    fehlerHinweis(fehler, "Popup fehlgeschlagen");
  }
}

let feldOffen = false;   // Ebenenfeld auf/zu — nicht in der URL

// Einmal bauen, danach nur Werte setzen: ein Neubau des DOM bei jedem `input` des Reglers würde die
// Zieh-Geste abbrechen (Spec §5). Der Regler wird nicht überschrieben, solange er fokussiert ist.
function zeichneSteuerung() {
  const s = document.getElementById("steuerung");
  if (!s.querySelector(".ebenenfeld")) {
    s.innerHTML = steuerungHtml(zustand, { offen: feldOffen, plan: PLAN_FREIGEGEBEN });
    s.querySelector("[data-feld]").onclick = () => { feldOffen = !feldOffen; zeichneSteuerung(); };
    s.querySelectorAll("[data-karte]").forEach((b) => { b.onclick = () => { if (zustand.karte !== b.dataset.karte) setzeZustand({ karte: b.dataset.karte }, false); }; });
    s.querySelector("[data-zechen]").onclick = () => setzeZustand({ zechen: zustand.zechen ? 0 : 1 }, false);
    // Beim Ziehen nur die Kartenebene und die Prozentzahl (Dutzende input-Ereignisse je Geste); die
    // volle Zustandskaskade (URL, Trefferliste, Legende) erst bei change, also beim Loslassen.
    const p = s.querySelector("[data-plan]");
    if (p) {
      p.oninput = () => { karte.setzePlan(+p.value); s.querySelector(".prozent").textContent = `${Math.round(p.value * 100)} %`; };
      p.onchange = () => setzeZustand({ plan: Math.round(p.value * 100) / 100 }, false);
    }
    const l = s.querySelector("[data-legende]"); if (l) l.onclick = () => document.getElementById("legende").classList.toggle("offen");
  }
  const knopf = s.querySelector("[data-feld]");
  knopf.classList.toggle("aktiv", abweichend(zustand));
  knopf.setAttribute("aria-expanded", String(feldOffen));
  s.querySelector(".ebenenfeld").hidden = !feldOffen;
  s.querySelectorAll("[data-karte]").forEach((b) => b.setAttribute("aria-pressed", String(zustand.karte === b.dataset.karte)));
  s.querySelector("[data-zechen]").setAttribute("aria-pressed", String(!!zustand.zechen));
  const p = s.querySelector("[data-plan]");
  if (p) { if (document.activeElement !== p) p.value = zustand.plan; s.querySelector(".prozent").textContent = `${Math.round(zustand.plan * 100)} %`; }
}

function schliesseFeld() { if (feldOffen) { feldOffen = false; zeichneSteuerung(); } }

// Straßen-Einheiten ohne OSM-Linie: sie tragen Zahlen bei, lassen sich aber nicht zeichnen.
// `strassen_mit_linie` aus kennzahlen.json gegen die Zahl der Straßen-Einheiten gerechnet.
function strassenOhneLinie() {
  const kz = ebenenDaten && ebenenDaten.kennzahlen;
  if (!kz || !Number.isFinite(kz.strassen_mit_linie)) return null;
  return Math.max(0, (ebenenDaten.strassen || []).length - kz.strassen_mit_linie);
}

function zeichneLegende() {
  let html = "";

  // Legende der aktiven Ansicht (Spec §8): Stufen bzw. Gruppen, min_n, Grundlage, Herkunft.
  if (ansichtFehler) html += `<div class="zeile"><b>Ansicht nicht lesbar – Karte ungefärbt.</b></div>`;
  if (ansichtAktiv) {
    html += `<div class="zeile"><b>${esc(ansichtTitel(ansichtAktiv))}</b></div>`;
    for (const e of legendeFuer(ansichtAktiv, ansichtWerte, { ohne_linie: strassenOhneLinie() })) {
      html += e.farbe
        ? `<div class="zeile"><span class="flaeche" style="background:${esc(e.farbe)}"></span> ${esc(e.text)}</div>`
        : `<div class="zeile klein">${esc(e.text)}</div>`;
    }
    html += `<div class="zeile klein">Adresspunkte treten zurück, solange eine Fläche eingefärbt ist.</div>`;
  }

  // Themenlegende, falls ein Thema aktiv ist (und eine Farbregel trägt — ohne Farbe keine Legende)
  if (themaAktiv && themaAktiv.farbe) {
    const farbe = themaAktiv.farbe;
    if (farbe.art === "einfach") {
      html += `<div class="zeile"><span class="punkt" style="background:${farbe.wert}"></span> ${themaAktiv.legende}</div>`;
    } else if (farbe.art === "skala") {
      // Kleine Farbgradiente aus den Stufen
      const farbeStufen = farbe.stufen.map(([_, c]) => c);
      const gradient = farbeStufen.map((c, i) => `${c} ${(i / (farbeStufen.length - 1)) * 100}%`).join(", ");
      html += `<div class="zeile"><span class="punkt" style="background:linear-gradient(90deg, ${gradient})"></span> ${themaAktiv.legende}</div>`;
    } else if (farbe.art === "kategorien") {
      html += `<div class="zeile"><b>${themaAktiv.legende}</b></div>`;
      for (const [k, c] of Object.entries(farbe.werte)) html += `<div class="zeile"><span class="punkt" style="background:${c}"></span> ${ANZEIGE[k] || k}</div>`;
      html += `<div class="zeile"><span class="punkt" style="background:${farbe.sonst || "#c8c8c8"}"></span> ${ANZEIGE.ungeprueft}</div>`;
    }
  }

  const f = zustand.ebene.length === 1 ? FARBEN[zustand.ebene[0]] : FARBEN.neutral;
  html +=
    `<div class="zeile"><span class="punkt" style="background:${f}"></span> hausgenau</div>` +
    `<div class="zeile"><span class="punkt ungenau" style="color:${f}"></span> nur straßengenau / Stadtplan 1935</div>` +
    `<div class="zeile"><span class="punkt" style="background:${FARBEN.treffer}"></span> Suchtreffer</div>` +
    `<div class="zeile">Größe = Zahl der Einträge</div>`;

  document.getElementById("legende").innerHTML = html;
}

async function exportiere() {
  if (!ergebnis) return;
  const csv = await csvAusTreffern(ergebnis, lader, await eigMap(ergebnis.adressIds));
  herunterladen(csv, `essen1936-${(zustand.q || zustand.beruf || zustand.eigentuemer || zustand.ohdab || "treffer").replace(/[^\w]+/g, "_")}.csv`);
}

// Suchfeld
let timer = null;
// ohdab zeigt vorerst die rohe OhdAB-Nummer; start() ersetzt sie durch die Normbezeichnung, sobald
// der Normindex geladen ist (Task 11).
sidebar.suche.value = zustand.q || zustand.eigentuemer || zustand.ohdab || "";
sidebar.suche.addEventListener("input", () => {
  clearTimeout(timer);
  document.getElementById("suche-leeren").hidden = !sidebar.suche.value;
  timer = setTimeout(async () => {
    try {
      sidebar.setzeVorschlaege(await vorschlaege(sidebar.suche.value, lader));
    } catch (fehler) {
      fehlerHinweis(fehler, "Vorschläge fehlgeschlagen");
    }
  }, 120);
});
sidebar.suche.addEventListener("keydown", (ev) => { if (ev.key === "Enter") { sidebar.setzeVorschlaege(null); sucheAusText(sidebar.suche.value.trim()); } });
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") schliesseFeld(); });
document.getElementById("karte").addEventListener("click", schliesseFeld, true);   // #steuerung liegt neben #karte, nicht darin
document.getElementById("suche-leeren").addEventListener("click", () => { sidebar.suche.value = ""; auswahl = null; setzeZustand({ q: "", id: "", beruf: "", eigentuemer: "", ohdab: "" }, true, true); sucheAusfuehren(); });
document.addEventListener("click", (ev) => { if (!ev.target.closest(".suchfeld")) sidebar.setzeVorschlaege(null); });
window.addEventListener("popstate", async () => {
  zustand = gateZustand(liesZustand(location.search));
  if (!new URLSearchParams(location.search).has("karte")) {
    const gespeichert = liesKarteSpeicher();
    if (gespeichert) zustand = { ...zustand, karte: gespeichert };
  }
  sidebar.suche.value = zustand.q || zustand.eigentuemer || zustand.ohdab || "";
  await start();
});

async function start() {
  await karte.bereit();
  const [st, be, kz] = await Promise.all([lader.stadtteile(), lader.berufe(), lader.kennzahlen()]);
  sidebar.setzeFilteroptionen(st, be);
  if (kz) document.getElementById("vermerk").textContent = `Work in progress · Datenstand ${kz.stand} · ${kz.stufen.haus} % hausgenau`;
  await wendeThemaAn();
  await wendeAnsichtAn();
  karte.setzeFilter(zustand); karte.setzePlan(zustand.plan); karte.setzeZechen(zustand.zechen);
  zeichneSteuerung(); zeichneLegende();
  if (zustand.beruf) auswahl = { art: "beruf", beruf: zustand.beruf };
  else if (zustand.eigentuemer) auswahl = { art: "eigentuemer", name: zustand.eigentuemer };
  else if (zustand.ohdab) {
    const name = await ohdabName(zustand.ohdab);
    auswahl = { art: "ohdab", ohdab: zustand.ohdab, name };
    sidebar.suche.value = name;
  }
  else if (zustand.q) {
    const s = await strasseAusZustand(zustand.q);
    auswahl = s || { art: "person", q: zustand.q };
  }
  else auswahl = null;
  await sucheAusfuehren();
  if (zustand.id) {
    const [aid, eid] = zustand.id.split(".");   // "adressId" oder "adressId.eintragId"
    oeffneHaus(aid, eid || null);
  }
  sidebar.setzeStufe(mobil() ? (zustand.q ? "halb" : "griff") : "halb");
}
// Kein Zurücksetzen des eigCache bei "sourcedata" mehr: Punkteigenschaften sind pro Build
// unveränderlich, egal ob sie aus der Kachel oder der Adressscherbe stammen (Task 13-Review).
await start();
window.karte = karte;
window.app = { zustand: () => zustand };
