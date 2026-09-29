import { Karte } from "./karte.js";
import { Lader } from "./daten.js";
import { Sidebar } from "./sidebar.js";
import { vorschlaege, treffer } from "./suche.js";
import { liesZustand, schreibeZustand, MAX_VERGLEICH, schluesselliste } from "./zustand.js";
import { mehrfachZahl, trefferGeoJson } from "./vergleich.js";
import { popupHtml, esc } from "./popup.js";
import { steuerungHtml, abweichend } from "./steuerung.js";
import { dekodiereOderNull } from "./ansicht.js";
import { ladeEbenen, werteJeEinheit } from "./daten_ebenen.js";
import { ansichtTitel, werteFarben, legendeFuer } from "./ansicht_farben.js";
import { FARBEN, PLAN_FREIGEGEBEN, STILE } from "./konfig.js";
import { ladeThema, themenListe, themaQuelleFuer } from "./themen.js";
import { csvAusTreffern, herunterladen } from "./exportcsv.js";
import { strasseAusText } from "./strassenwahl.js";

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
  onVergleich: (s, umschalten) => vergleichWaehlen(s, umschalten),
  onKlassen: (klassen) => setzeZustand({ klassen }, false),
});
// Debughilfe für Sichtprüfungen (Playwright): ?debug=1 legt die Karte auf window.
const karte = new Karte("karte", zustand, {
  onKlick: (id, lngLat) => klickPunkt(id, lngLat),
  onBewegt: (z, c) => setzeZustand({ z, c }, false, true),
  onHover: () => {},
});
if (new URLSearchParams(location.search).has("debug")) window.__karte = karte;

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

// Vergleich (Spec Themenbaum §3): Schlüssel anhängen, bei umschalten=true einen gewählten entfernen; höchstens MAX_VERGLEICH.
function vergleichWaehlen(s, umschalten) {
  const alt = zustand.vergleich;
  let neu;
  if (alt.includes(s)) { if (!umschalten) return; neu = alt.filter((x) => x !== s); }
  else if (alt.length >= MAX_VERGLEICH) { sidebar.zeigeHinweis(`Höchstens ${MAX_VERGLEICH} Gruppen gleichzeitig.`); return; }
  else neu = [...alt, s];
  sidebar.setzeVorschlaege(null);
  setzeZustand({ vergleich: neu, q: "", beruf: "", id: "" }, true);
}

// Titel des Vergleichsknopfs in Popup und Hausansicht.
function knopfTitel(s) {
  if (zustand.vergleich.includes(s)) return "bereits im Vergleich";
  return zustand.vergleich.length ? "zum Vergleich hinzufügen" : "alle Häuser dieser Gruppe";
}

function schreibeUrl(push) {
  const q = schreibeZustand(zustand);
  const url = location.pathname + (q ? "?" + q : "");
  if (push) history.pushState(zustand, "", url); else history.replaceState(zustand, "", url);
}

async function setzeZustand(patch, push, nurKarte = false) {
  const alt = zustand;
  zustand = { ...zustand, ...patch, vergleich: schluesselliste(patch.vergleich === undefined ? zustand.vergleich : patch.vergleich) };   // kein Aufrufer kann einen String einschleusen
  // Themenwechsel nimmt klassen= nicht mit (Review 2026-09-29): die Klassen des alten Themas passen nicht zum neuen.
  if (patch.thema !== undefined && patch.thema !== alt.thema && patch.klassen === undefined) zustand = { ...zustand, klassen: "" };
  schreibeUrl(push);
  if (nurKarte) return;
  // setzeStil() kann bei schnell aufeinanderfolgenden Wechseln nie auflösen (Karte meldet den
  // veralteten Warter ab, ohne ihn aufzulösen) — daher nicht awaiten, sonst hängt setzeZustand.
  // Die Karte wendet Filter/Plan/Zechen/Treffer/Auswahl in ebenenAufsetzen() selbst wieder an.
  if (alt.karte !== zustand.karte) { karte.setzeStil(zustand.karte); schreibeKarteSpeicher(zustand.karte); }
  if (alt.thema !== zustand.thema) await wendeThemaAn();
  else if (alt.klassen !== zustand.klassen && zustand.thema) {
    // Nur die Schalter: Farbregel neu, Kästchen im Baum nachziehen — kein Neuaufbau von Liste und Themenquelle.
    themaAktiv = await ladeThema(lader, zustand.thema, zustand.klassen);
    karte.setzeFarbe(themaAktiv ? themaAktiv.farbregel : null);
    sidebar.setzeKlassen(zustand.klassen);
  }
  if (alt.ansicht !== zustand.ansicht) await wendeAnsichtAn();
  // Bei einem Stilwechsel legt ebenenAufsetzen() die Ebenen erst neu an (asynchron, nicht
  // awaitet); ein sofortiger setzeFilter/setzePlan/setzeZechen hier würde noch auf die alten,
  // gerade abgebauten Layer zielen ("Cannot filter non-existing layer"). Nur anwenden, wenn sich
  // der Kartenstil in diesem Aufruf nicht geändert hat.
  if (alt.karte === zustand.karte) {
    // Ebenenwechsel bei aktivem Thema: Themenquelle nur, solange die Ebenen zu den Kacheln passen (Review 2026-09-29).
    if (alt.ebene !== zustand.ebene && themaAktiv) karte.setzeThemaQuelle(themaQuelleFuer(themaAktiv, zustand.ebene));
    karte.setzeFilter(zustand);
    karte.setzePlan(zustand.plan); karte.setzeZechen(zustand.zechen);
  }
  if (alt.beruf !== zustand.beruf || alt.vergleich.join("|") !== zustand.vergleich.join("|")) {
    auswahl = zustand.beruf ? { art: "beruf", beruf: zustand.beruf } : zustand.vergleich.length ? { art: "vergleich", schluessel: zustand.vergleich } : null;
    // Aus dem Themenbaum gewählt setzt nur den Zustand, nicht das Suchfeld — sucheAusfuehren() trägt bei genau
    // einer Gruppe deren Namen ein; sonst bleibt das Feld leer, „Suche leeren“ folgt dem Feld.
    if (!zustand.beruf && !zustand.q) sidebar.suche.value = "";
    document.getElementById("suche-leeren").hidden = !sidebar.suche.value;
    await sucheAusfuehren();
  }
  else await zeigeInhalt();
  zeichneSteuerung(); zeichneLegende();
}

async function wendeThemaAn() {
  const t = zustand.thema ? await ladeThema(lader, zustand.thema, zustand.klassen) : null;
  themaAktiv = t;
  // klassen gehört nur zu einem Thema mit Schaltern; sonst klebte der Parameter an der URL.
  if (!(t && t.schalter) && zustand.klassen) zustand = { ...zustand, klassen: "" };
  sidebar.zeigeThema(t, t && t.baum ? await lader.themaListe(t.id) : null, zustand.vergleich, FARBEN.gruppen, zustand.klassen);
  karte.setzeFarbe(t ? t.farbregel : null);
  if (t && t.ebenen) zustand = { ...zustand, ebene: t.ebenen };
  karte.setzeThemaQuelle(themaQuelleFuer(t, zustand.ebene));   // feine Punkte aus der Kacheldatei des Themas (Spec Themenkacheln §3)
  if (t && t.zusatz && t.zusatz.zechen && !zustand.zechen) zustand = { ...zustand, zechen: 1 };
  if (t && t.ebenen) zustand = { ...zustand, ebene: t.ebenen };
  schreibeUrl(false);   // vom Thema erzwungene Ebenen/Zechen auch in der URL abbilden
  if (t && mobil() && sidebar.el.dataset.stufe === "griff") sidebar.setzeStufe("halb");
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
  else sidebar.zeigeSuche(zustand);
}

// Kurzindex (Spec 2026-09-29 §2): Adresse, Stadtteil, Koordinaten für Liste, Leiste und Einpassen — kein
// Nachladen fetter Adressscherben, keine Kachelabfrage je Haus.
async function eigMap(ids) { return lader.adressenKurz(ids); }

async function sucheAusfuehren() {
  try {
    sidebar.markiereVergleich(zustand.vergleich, FARBEN.gruppen);
    if (!auswahl) { ergebnis = null; karte.setzeTreffer(null); await zeigeInhalt(); zeichneLegende(); return; }
    ergebnis = await treffer(auswahl, lader);
    if (ergebnis.gruppen && ergebnis.gruppen.length === 1 && !zustand.q) { sidebar.suche.value = ergebnis.gruppen[0].name; document.getElementById("suche-leeren").hidden = false; }
    const eig = await eigMap(ergebnis.adressIds);
    karte.setzeTreffer(ergebnis.adressIds, ergebnis.gruppen, trefferGeoJson(ergebnis.adressIds, ergebnis.zaehler, ergebnis.gruppen, eig));
    const koordinaten = new Map([...eig.values()].map((e) => [e.id, [e.lon, e.lat]]));
    if (ergebnis.adressIds.length) karte.passeEin(ergebnis.adressIds, koordinaten);
    sidebar.zeigeTreffer(zustand, ergebnis, eig, zustand.q);
    zeichneLegende();
    sidebar.setzeStufe("halb");
  } catch (fehler) {
    fehlerHinweis(fehler, "Suche fehlgeschlagen");
  }
}

async function waehleVorschlag(v) {
  sidebar.setzeVorschlaege(null);
  sidebar.suche.value = v.text;
  if (v.art === "person" || v.art === "firma") { setzeZustand({ q: v.text, id: v.adressId, vergleich: [], beruf: "" }, true, true); return oeffneHaus(v.adressId, v.eintragId); }
  if (v.art === "beruf") return setzeZustand({ q: "", vergleich: [], beruf: v.beruf }, true);
  if (v.art === "eigentuemer") return vergleichWaehlen(`eig:${v.name}`, false);
  if (v.art === "ohdab") return vergleichWaehlen(`norm:${v.ohdab}`, false);
  if (v.art === "rubrik") return vergleichWaehlen(`rub:${v.name}`, false);
  // v.art === "strasse": v trägt bereits name/artName/ort/schluessel, treffer() lädt die IDs selbst.
  // q wird als reiner Name geschrieben (nicht v.text mit "(Ort)") — sonst kann strasseAusZustand()
  // die URL bei Reload/Zurück/Vor nicht mehr auflösen (Fix-Runde 1).
  auswahl = v;
  setzeZustand({ q: v.name, id: "", vergleich: [], beruf: "" }, true, true);
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
  setzeZustand({ q, id: "", beruf: "", vergleich: [] }, true, true);
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
    sidebar.zeigeHaus(e, eintraege, eintragId, await lader.faksimile(), zustand.ebene, ergebnis && ergebnis.gruppen);
    sidebar.inhalt.querySelectorAll("[data-schluessel]").forEach((n) => { n.title = knopfTitel(n.dataset.schluessel); });
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
    // stopPropagation: der Knopf liegt in der Eintragszeile, deren Klick die Hausansicht öffnet (Sichtprüfung 2026-09-29).
    el.querySelectorAll("[data-schluessel]").forEach((n) => { n.title = knopfTitel(n.dataset.schluessel); n.addEventListener("click", (ev) => { ev.stopPropagation(); vergleichWaehlen(n.dataset.schluessel, false); }); });
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

  // Themen ohne Baum (einfach/skala): eine Farbzeile. Schalter und Kategorien stehen im Themenbaum der Sidebar (Spec Themenbaum §5).
  if (themaAktiv && themaAktiv.farbe) {
    const farbe = themaAktiv.farbe;
    if (farbe.art === "einfach") {
      html += `<div class="zeile"><span class="punkt" style="background:${farbe.wert}"></span> ${esc(themaAktiv.legende)}</div>`;
    } else if (farbe.art === "skala") {
      const farbeStufen = farbe.stufen.map(([_, c]) => c);
      const gradient = farbeStufen.map((c, i) => `${c} ${(i / (farbeStufen.length - 1)) * 100}%`).join(", ");
      html += `<div class="zeile"><span class="punkt" style="background:linear-gradient(90deg, ${gradient})"></span> ${esc(themaAktiv.legende)}</div>`;
    }
  }

  const f = zustand.ebene.length === 1 ? FARBEN[zustand.ebene[0]] : FARBEN.neutral;
  html += `<div class="zeile"><span class="punkt" style="background:${f}"></span> hausgenau</div>` +
    `<div class="zeile"><span class="punkt ungenau" style="color:${f}"></span> nur straßengenau / Stadtplan 1935</div>`;
  if (ergebnis && ergebnis.gruppen) { if (mehrfachZahl(ergebnis.gruppen)) html += `<div class="zeile"><span class="punkt ring"></span> in mehreren Gruppen</div>`; }
  else if (ergebnis) html += `<div class="zeile"><span class="punkt" style="background:${FARBEN.treffer}"></span> Suchtreffer</div>`;
  // Themenkacheln zeichnen unter Zoom 14 gleich große Punkte (RADIUS_THEMA), darüber nach Einträgen wie die Grundkarte.
  html += `<div class="zeile">${themaAktiv ? "Größe = Zahl der Einträge ab Zoom 14, darunter gleich groß" : "Größe = Zahl der Einträge"}</div>`;
  document.getElementById("legende").innerHTML = html;
}

async function exportiere() {
  if (!ergebnis) return;
  const csv = await csvAusTreffern(ergebnis, lader, await eigMap(ergebnis.adressIds));
  const name = zustand.q || zustand.beruf || (ergebnis.gruppen && ergebnis.gruppen[0] && ergebnis.gruppen[0].name) || "treffer";
  herunterladen(csv, zustand.vergleich.length > 1 ? "essen1936-vergleich.csv" : `essen1936-${name.replace(/[^\w]+/g, "_")}.csv`);
}

// Suchfeld
let timer = null;
sidebar.suche.value = zustand.q || "";   // bei genau einer Vergleichsgruppe trägt sucheAusfuehren() deren Namen ein
sidebar.suche.addEventListener("input", () => {
  clearTimeout(timer);
  document.getElementById("suche-leeren").hidden = !sidebar.suche.value;
  timer = setTimeout(async () => {
    try {
      sidebar.setzeVorschlaege(await vorschlaege(sidebar.suche.value, lader), zustand.vergleich.length > 0);
    } catch (fehler) {
      fehlerHinweis(fehler, "Vorschläge fehlgeschlagen");
    }
  }, 120);
});
sidebar.suche.addEventListener("keydown", (ev) => { if (ev.key === "Enter") { sidebar.setzeVorschlaege(null); sucheAusText(sidebar.suche.value.trim()); } });
document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") schliesseFeld(); });
document.getElementById("karte").addEventListener("click", schliesseFeld, true);   // #steuerung liegt neben #karte, nicht darin
document.getElementById("suche-leeren").addEventListener("click", () => { sidebar.suche.value = ""; auswahl = null; setzeZustand({ q: "", id: "", beruf: "", vergleich: [] }, true, true); sucheAusfuehren(); });
document.addEventListener("click", (ev) => { if (!ev.target.closest(".suchfeld")) sidebar.setzeVorschlaege(null); });
window.addEventListener("popstate", async () => {
  zustand = gateZustand(liesZustand(location.search));
  if (!new URLSearchParams(location.search).has("karte")) {
    const gespeichert = liesKarteSpeicher();
    if (gespeichert) zustand = { ...zustand, karte: gespeichert };
  }
  sidebar.suche.value = zustand.q || "";
  document.getElementById("suche-leeren").hidden = !sidebar.suche.value;   // Knopf folgt dem Feld (Review-Minor)
  await start();
});

async function start() {
  await karte.bereit();
  const [st, be, kz] = await Promise.all([lader.stadtteile(), lader.berufe(), lader.kennzahlen()]);
  sidebar.setzeFilteroptionen(st, be);
  sidebar.zeigeThemenliste(await themenListe(lader), zustand.thema);
  if (kz) document.getElementById("vermerk").textContent = `Work in progress · Datenstand ${kz.stand} · ${kz.stufen.haus} % hausgenau`;
  await wendeThemaAn();
  await wendeAnsichtAn();
  karte.setzeFilter(zustand); karte.setzePlan(zustand.plan); karte.setzeZechen(zustand.zechen);
  zeichneSteuerung(); zeichneLegende();
  if (zustand.beruf) auswahl = { art: "beruf", beruf: zustand.beruf };
  else if (zustand.vergleich.length) auswahl = { art: "vergleich", schluessel: zustand.vergleich };
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
  // Am Handy öffnet das Blatt bei Suche oder aktivem Thema auf „halb“, damit der Themenbaum erreichbar ist (Spec Themenbaum §2).
  sidebar.setzeStufe(mobil() ? (zustand.q || zustand.thema ? "halb" : "griff") : "halb");
}
// Kein Zurücksetzen des eigCache bei "sourcedata" mehr: Punkteigenschaften sind pro Build
// unveränderlich, egal ob sie aus der Kachel oder der Adressscherbe stammen (Task 13-Review).
await start();
window.karte = karte;
window.app = { zustand: () => zustand };
