import { Karte } from "./karte.js";
import { Lader } from "./daten.js";
import { Sidebar } from "./sidebar.js";
import { vorschlaege, treffer } from "./suche.js";
import { liesZustand, schreibeZustand } from "./zustand.js";
import { popupHtml } from "./popup.js";
import { FARBEN, PLAN_FREIGEGEBEN, STILE } from "./konfig.js";
import { ladeThema, themenListe } from "./themen.js";
import { csvAusTreffern, herunterladen } from "./exportcsv.js";

const lader = new Lader();
let zustand = liesZustand(location.search);
let ergebnis = null;              // aktuelle Treffermenge
let auswahl = null;               // { art, ... } der Suche
const eigCache = new Map();       // adressId → Punkteigenschaften aus Kacheln
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
  onZurueck: () => history.back(),
  onExport: () => exportiere(),
});
const karte = new Karte("karte", zustand, {
  onKlick: (id, lngLat) => klickPunkt(id, lngLat),
  onBewegt: (z, c) => setzeZustand({ z, c }, false, true),
  onHover: () => {},
});

function eigVon(id) {
  if (!eigCache.has(id)) {
    const f = karte.map.querySourceFeatures("adressen", { sourceLayer: "adressen", filter: ["==", ["get", "id"], id] });
    if (f.length) eigCache.set(id, f[0].properties);
  }
  return eigCache.get(id) || null;
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
  if (alt.karte !== zustand.karte) karte.setzeStil(zustand.karte);
  if (alt.thema !== zustand.thema) await wendeThemaAn();
  karte.setzeFilter(zustand);
  karte.setzePlan(zustand.plan); karte.setzeZechen(zustand.zechen);
  if (alt.beruf !== zustand.beruf) { auswahl = zustand.beruf ? { art: "beruf", beruf: zustand.beruf } : null; await sucheAusfuehren(); }
  else zeigeInhalt();
  zeichneSteuerung(); zeichneLegende();
}

async function wendeThemaAn() {
  const t = zustand.thema ? await ladeThema(lader, zustand.thema) : null;
  sidebar.zeigeThema(t);
  karte.setzeFarbe(t ? t.farbregel : null);
  if (t && t.zusatz && t.zusatz.zechen && !zustand.zechen) zustand = { ...zustand, zechen: 1 };
  if (t && t.ebenen) zustand = { ...zustand, ebene: t.ebenen };
}

function zeigeInhalt() {
  if (ergebnis) sidebar.zeigeTreffer(zustand, ergebnis, eigMap(ergebnis.adressIds), zustand.q);
  else { sidebar.zeigeSuche(zustand); themenListe(lader).then((l) => sidebar.zeigeThemenliste(l)); }
}

function eigMap(ids) { const m = new Map(); for (const id of ids) { const e = eigVon(id); if (e) m.set(id, e); } return m; }

async function sucheAusfuehren() {
  try {
    if (!auswahl) { ergebnis = null; karte.setzeTreffer(null); zeigeInhalt(); return; }
    ergebnis = await treffer(auswahl, lader);
    karte.setzeTreffer(ergebnis.adressIds);
    if (!karte.passeEin(ergebnis.adressIds) && ergebnis.adressIds.length) {
      // Kacheln der Treffer noch nicht geladen: einmal warten und erneut versuchen
      karte.map.once("idle", () => { karte.passeEin(ergebnis.adressIds); zeigeInhalt(); });
    }
    zeigeInhalt();
    sidebar.setzeStufe("halb");
  } catch (fehler) {
    fehlerHinweis(fehler, "Suche fehlgeschlagen");
  }
}

async function waehleVorschlag(v) {
  sidebar.setzeVorschlaege(null);
  sidebar.suche.value = v.text;
  if (v.art === "person" || v.art === "firma") { setzeZustand({ q: v.text, id: v.adressId }, true, true); return oeffneHaus(v.adressId, v.eintragId); }
  if (v.art === "beruf") return setzeZustand({ q: "", beruf: v.beruf }, true);
  // v.art === "strasse": v trägt bereits name/artName/ort/schluessel, treffer() lädt die IDs selbst.
  auswahl = v;
  setzeZustand({ q: v.text, id: "" }, true, true);
  await sucheAusfuehren();
}

async function sucheAusText(q) {
  // Enter ohne Vorschlagsauswahl: Personensuche über den Text, Straßen über exakten Namen.
  auswahl = { art: "person", q };
  setzeZustand({ q, id: "" }, true, true);
  await sucheAusfuehren();
}

async function oeffneHaus(id, eintragId) {
  try {
    const [eig, eintraege] = [eigVon(id), await lader.scherbe(id)];
    if (!eintraege) return;
    const e = eig || { id, stufe: "haus", historisch: "", strasse_heute: "", hausnr: "", stadtteil: "", n_I: 0, n_II: 0, n_III: 0 };
    // id in der URL: Adress-ID, bei hervorgehobenem Eintrag "adressId.eintragId"
    setzeZustand({ id: eintragId ? `${id}.${eintragId}` : id }, true, true);
    karte.setzeAuswahl(id);
    const pos = karte.position(id);
    if (pos) karte.fliegeZu(pos);
    sidebar.zeigeHaus(e, eintraege, eintragId);
  } catch (fehler) {
    fehlerHinweis(fehler, "Hausansicht fehlgeschlagen");
  }
}

async function klickPunkt(id, lngLat) {
  try {
    const eig = eigVon(id); const eintraege = await lader.scherbe(id);
    if (!eig || !eintraege) return;
    karte.setzeAuswahl(id);
    karte.zeigePopup(lngLat, popupHtml(eig, eintraege, mobil()));
    const el = karte.popup.getElement();
    el.querySelectorAll("[data-eintrag]").forEach((n) => n.addEventListener("click", () => oeffneHaus(id, n.dataset.eintrag)));
    el.querySelectorAll("[data-mehr]").forEach((n) => n.addEventListener("click", () => oeffneHaus(id, null)));
  } catch (fehler) {
    fehlerHinweis(fehler, "Popup fehlgeschlagen");
  }
}

function zeichneSteuerung() {
  const s = document.getElementById("steuerung");
  s.innerHTML = `<button data-karte="1">Grundkarte: ${zustand.karte === "positron" ? "dezent" : "detailliert"}</button>` +
    `<button data-zechen="1" aria-pressed="${!!zustand.zechen}">Zechen ${zustand.zechen ? "aus" : "an"}</button>` +
    (PLAN_FREIGEGEBEN ? `<label>Stadtplan 1935 <input type="range" min="0" max="1" step="0.1" value="${zustand.plan}" data-plan="1"></label>` : "") +
    (mobil() ? `<button data-legende="1">Legende</button>` : "");
  s.querySelector("[data-karte]").onclick = () => setzeZustand({ karte: zustand.karte === "positron" ? "liberty" : "positron" }, false);
  s.querySelector("[data-zechen]").onclick = () => setzeZustand({ zechen: zustand.zechen ? 0 : 1 }, false);
  const p = s.querySelector("[data-plan]"); if (p) p.oninput = () => setzeZustand({ plan: +p.value }, false);
  const l = s.querySelector("[data-legende]"); if (l) l.onclick = () => document.getElementById("legende").classList.toggle("offen");
}

function zeichneLegende() {
  const f = zustand.ebene.length === 1 ? FARBEN[zustand.ebene[0]] : FARBEN.neutral;
  document.getElementById("legende").innerHTML =
    `<div class="zeile"><span class="punkt" style="background:${f}"></span> hausgenau</div>` +
    `<div class="zeile"><span class="punkt ungenau" style="color:${f}"></span> nur straßengenau / Stadtplan 1935</div>` +
    `<div class="zeile"><span class="punkt" style="background:${FARBEN.treffer}"></span> Suchtreffer</div>` +
    `<div class="zeile">Größe = Zahl der Einträge</div>`;
}

async function exportiere() {
  if (!ergebnis) return;
  const csv = await csvAusTreffern(ergebnis, lader, eigMap(ergebnis.adressIds));
  herunterladen(csv, `essen1936-${(zustand.q || zustand.beruf || "treffer").replace(/[^\w]+/g, "_")}.csv`);
}

// Suchfeld
let timer = null;
sidebar.suche.value = zustand.q;
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
document.getElementById("suche-leeren").addEventListener("click", () => { sidebar.suche.value = ""; auswahl = null; setzeZustand({ q: "", id: "" }, true, true); sucheAusfuehren(); });
document.addEventListener("click", (ev) => { if (!ev.target.closest(".suchfeld")) sidebar.setzeVorschlaege(null); });
window.addEventListener("popstate", async () => { zustand = liesZustand(location.search); sidebar.suche.value = zustand.q; await start(); });

async function start() {
  await karte.bereit();
  const [st, be, kz] = await Promise.all([lader.stadtteile(), lader.berufe(), lader.kennzahlen()]);
  sidebar.setzeFilteroptionen(st, be);
  if (kz) document.getElementById("vermerk").textContent = `Work in progress · Datenstand ${kz.stand} · ${kz.stufen.haus} % hausgenau`;
  await wendeThemaAn();
  karte.setzeFilter(zustand); karte.setzePlan(zustand.plan); karte.setzeZechen(zustand.zechen);
  zeichneSteuerung(); zeichneLegende();
  if (zustand.beruf) auswahl = { art: "beruf", beruf: zustand.beruf };
  else if (zustand.q) auswahl = { art: "person", q: zustand.q };
  else auswahl = null;
  await sucheAusfuehren();
  if (zustand.id) {
    const [aid, eid] = zustand.id.split(".");   // "adressId" oder "adressId.eintragId"
    oeffneHaus(aid, eid || null);
  }
  sidebar.setzeStufe(mobil() ? (zustand.q ? "halb" : "griff") : "halb");
}
karte.map.on("sourcedata", (e) => { if (e.sourceId === "adressen" && e.isSourceLoaded) eigCache.clear(); });
await start();
window.karte = karte;
window.app = { zustand: () => zustand };
