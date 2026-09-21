import { Karte } from "./karte.js";
import { Lader } from "./daten.js";
import { Sidebar } from "./sidebar.js";
import { vorschlaege, treffer } from "./suche.js";
import { liesZustand, schreibeZustand } from "./zustand.js";
import { popupHtml } from "./popup.js";
import { FARBEN, PLAN_FREIGEGEBEN, STILE } from "./konfig.js";
import { ladeThema, themenListe } from "./themen.js";
import { csvAusTreffern, herunterladen } from "./exportcsv.js";
import { strasseAusText } from "./strassenwahl.js";

const lader = new Lader();
let zustand = liesZustand(location.search);
let ergebnis = null;              // aktuelle Treffermenge
let auswahl = null;               // { art, ... } der Suche
let themaAktiv = null;            // aktives Thema mit farbregel und ebenen
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
  if (alt.karte !== zustand.karte) karte.setzeStil(zustand.karte);
  if (alt.thema !== zustand.thema) await wendeThemaAn();
  // Bei einem Stilwechsel legt ebenenAufsetzen() die Ebenen erst neu an (asynchron, nicht
  // awaitet); ein sofortiger setzeFilter/setzePlan/setzeZechen hier würde noch auf die alten,
  // gerade abgebauten Layer zielen ("Cannot filter non-existing layer"). Nur anwenden, wenn sich
  // der Kartenstil in diesem Aufruf nicht geändert hat.
  if (alt.karte === zustand.karte) {
    karte.setzeFilter(zustand);
    karte.setzePlan(zustand.plan); karte.setzeZechen(zustand.zechen);
  }
  if (alt.beruf !== zustand.beruf) { auswahl = zustand.beruf ? { art: "beruf", beruf: zustand.beruf } : null; await sucheAusfuehren(); }
  else await zeigeInhalt();
  zeichneSteuerung(); zeichneLegende();
}

async function wendeThemaAn() {
  const t = zustand.thema ? await ladeThema(lader, zustand.thema) : null;
  themaAktiv = t;
  sidebar.zeigeThema(t);
  karte.setzeFarbe(t ? t.farbregel : null);
  if (t && t.zusatz && t.zusatz.zechen && !zustand.zechen) zustand = { ...zustand, zechen: 1 };
  if (t && t.ebenen) zustand = { ...zustand, ebene: t.ebenen };
  schreibeUrl(false);   // vom Thema erzwungene Ebenen/Zechen auch in der URL abbilden
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
  if (v.art === "beruf") return setzeZustand({ q: "", beruf: v.beruf }, true);
  // v.art === "strasse": v trägt bereits name/artName/ort/schluessel, treffer() lädt die IDs selbst.
  // q wird als reiner Name geschrieben (nicht v.text mit "(Ort)") — sonst kann strasseAusZustand()
  // die URL bei Reload/Zurück/Vor nicht mehr auflösen (Fix-Runde 1).
  auswahl = v;
  setzeZustand({ q: v.name, id: "" }, true, true);
  await sucheAusfuehren();
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
  setzeZustand({ q, id: "" }, true, true);
  await sucheAusfuehren();
}

async function oeffneHaus(id, eintragId) {
  try {
    const [eig, eintraege] = await Promise.all([eigVon(id), lader.scherbe(id)]);
    if (!eintraege) return;
    const e = eig || { id, stufe: "haus", historisch: "", strasse_heute: "", hausnr: "", stadtteil: "", n_I: 0, n_II: 0, n_III: 0 };
    // id in der URL: Adress-ID, bei hervorgehobenem Eintrag "adressId.eintragId"
    setzeZustand({ id: eintragId ? `${id}.${eintragId}` : id }, true, true);
    karte.setzeAuswahl(id);
    // Kachel-Position bevorzugt (Kachel bereits geladen); außerhalb des Viewports (Kachel nicht
    // geladen) liefert die Adressscherbe lat/lon als Fallback (Task 13-Review).
    const pos = karte.position(id) || (eig && eig.lon != null && eig.lat != null ? [eig.lon, eig.lat] : null);
    if (pos) karte.fliegeZu(pos);
    sidebar.zeigeHaus(e, eintraege, eintragId);
  } catch (fehler) {
    fehlerHinweis(fehler, "Hausansicht fehlgeschlagen");
  }
}

async function klickPunkt(id, lngLat) {
  try {
    const [eig, eintraege] = await Promise.all([eigVon(id), lader.scherbe(id)]);
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
  let html = "";

  // Themenlegende, falls ein Thema aktiv ist
  if (themaAktiv) {
    const farbe = themaAktiv.farbe;
    if (farbe.art === "einfach") {
      html += `<div class="zeile"><span class="punkt" style="background:${farbe.wert}"></span> ${themaAktiv.legende}</div>`;
    } else if (farbe.art === "skala") {
      // Kleine Farbgradiente aus den Stufen
      const farbeStufen = farbe.stufen.map(([_, c]) => c);
      const gradient = farbeStufen.map((c, i) => `${c} ${(i / (farbeStufen.length - 1)) * 100}%`).join(", ");
      html += `<div class="zeile"><span class="punkt" style="background:linear-gradient(90deg, ${gradient})"></span> ${themaAktiv.legende}</div>`;
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
