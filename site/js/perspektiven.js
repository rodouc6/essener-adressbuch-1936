// site/js/perspektiven.js — Perspektiven-Seite (Spec §6.2): lädt die Kapitel, baut je Kapitel die
// Schritte und die klebende Grafik, schaltet beim Scrollen (Scrollama) oder per Tastaturfokus
// zwischen den Schritten um und öffnet den Detailkasten zu einer angeklickten Einheit.
// Browsercode; alles Prüfbare steht in perspektiven_modell.js.
import { Lader } from "./daten.js";
import { normalisiere } from "./ansicht.js";
import { ladeEbenen, werteJeEinheit } from "./daten_ebenen.js";
import { esc, nennerText } from "./formen/skalen.js";
import * as balken from "./formen/balken.js";
import * as rangliste from "./formen/rangliste.js";
import * as stadtteilkarte from "./formen/stadtteilkarte.js";
import * as bubbles from "./formen/bubbles.js";
import { detailText, formFuer, fuellePlatzhalter, linkKarte, linkWerkstatt, sichtbareKapitel, zeichenflaeche } from "./perspektiven_modell.js";

const FORMEN = { balken, rangliste, stadtteilkarte, bubbles };
const lader = new Lader();
const vorschau = new URLSearchParams(location.search).get("vorschau") === "1";
const reduziert = matchMedia("(prefers-reduced-motion: reduce)").matches;

// Zahlwörter für die Einleitung: „Ein Blick“, „Zwei Blicke“, „Drei Blicke“, ab vier Ziffern.
const ZAHLWORT = { 1: "Ein", 2: "Zwei", 3: "Drei" };

let daten = null;
// Ein Ladefehler (Netz, kaputtes JSON) darf die Seite nicht als leere Fläche zurücklassen.
try {
  await seiteAufbauen();
} catch (fehler) {
  console.error("Perspektiven konnten nicht geladen werden", fehler);
  document.getElementById("kapitel").innerHTML =
    `<p class="leer">Die Perspektiven konnten nicht geladen werden (${esc((fehler && fehler.message) || fehler)}). Bitte später erneut versuchen.</p>`;
}

async function seiteAufbauen() {
  daten = await ladeEbenen(lader);
  const index = sichtbareKapitel((await lader.perspektivenIndex()) || [], vorschau);
  // Die Einleitung zählt, was wirklich sichtbar ist — „Drei Blicke“ wäre falsch, sobald ein
  // Kapitel nicht freigegeben ist.
  const n = index.length;
  // Ohne freigegebenes Kapitel bleibt die Einleitung leer; der Leerzustand steht einmal in #kapitel.
  const einleitung = n === 0 ? ""
    : `${n === 1 ? "Ein Blick" : `${ZAHLWORT[n] || n} Blicke`} auf das Adressbuch von 1936: {adressen} verortete Adressen, Stand {stand}. `
      + "Jede Grafik nennt, wie viel geprüft ist und was ausgeschlossen bleibt.";
  document.getElementById("einleitung").textContent = fuellePlatzhalter(einleitung, daten.kennzahlen);
  document.getElementById("inhalt").innerHTML = index.map((k) => `<li><a href="#k-${esc(k.id)}">${esc(k.titel)}</a>${k.freigegeben ? "" : " <small>(Vorschau)</small>"}</li>`).join("");

  if (index.length === 0) {
    document.getElementById("kapitel").innerHTML = '<p class="leer">Noch kein Kapitel freigegeben.</p>';
    return;
  }
  for (const eintrag of index) {
    const k = await lader.kapitel(eintrag.id);
    if (!k) continue;
    const sec = document.createElement("section");
    sec.className = "kapitel";
    sec.id = `k-${k.id}`;
    sec.innerHTML = kapitelHtml(k);
    document.getElementById("kapitel").appendChild(sec);
    bindeKapitel(sec, k);
  }
}

// Markup eines Kapitels: Kopf, Scrolly aus Grafik und Schritten, danach der Grenzen-Abschnitt.
// Jeder Schritt bekommt tabindex, damit er auch ohne Maus und ohne Scrollen erreichbar ist.
function kapitelHtml(k) {
  const schritte = (Array.isArray(k.schritte) ? k.schritte : []).map((s) => {
    const a = normalisiere(s.ansicht);
    return `<article class="schritt" data-schritt="${esc(s.id)}" tabindex="0"><p>${esc(s.text)}</p><p class="sr-only">${esc(s.beschreibung || "")}</p>`
      + `<p class="links"><a href="${esc(linkKarte(a))}">Auf der Karte öffnen</a> · <a href="${esc(linkWerkstatt(a))}">In der Werkstatt öffnen</a></p></article>`;
  }).join("");
  const quellen = (Array.isArray(k.quellen) ? k.quellen : []).map((q) => esc(q)).join(" · ");
  return `<header><h2>${esc(k.titel)}</h2><p class="untertitel">${esc(k.untertitel || "")}</p><p>${esc(k.einleitung || "")}</p></header>`
    + `<div class="scrolly">`
    // Nur Bild und Legende sind für Hilfsmittel verborgen (die Beschreibung steht je Schritt in
    // .sr-only); die Zahlenzeile bleibt lesbar, weil jeder Schritt seine Grundlage nennen muss.
    + `<div class="grafik"><div class="buehne"><div class="svg" aria-hidden="true"></div><div class="legende" aria-hidden="true"></div><div class="zahlen"></div></div></div>`
    + `<div class="schritte">${schritte}</div>`
    + `</div>`
    + `<section class="grenzen"><h3>Was die Zahlen zeigen – und was nicht</h3>`
    + `<p>${esc(fuellePlatzhalter(k.grenzen || "", daten.kennzahlen))}</p>`
    + (quellen ? `<p class="quellen">Quellen: ${quellen}</p>` : "")
    + `</section>`;
}

// Zeichnet die Ansicht eines Schritts in die Grafik des Kapitels. Die Form „multiples“ ist die
// Balkenform mit einem Balken je Einheit; fehlt das Flag in der kuratierten Ansicht, wird es hier
// gesetzt, damit nicht versehentlich ein Gesamtbalken erscheint.
function zeichne(sec, schritt) {
  if (!schritt) return;
  // Der Detailkasten gehört zur vorigen Ansicht; stehen bliebe er mit Zahlen, die zur neuen
  // Grafik nicht mehr passen.
  document.getElementById("detail").hidden = true;
  const ansicht = normalisiere(schritt.ansicht);
  if (schritt.ansicht && schritt.ansicht.form === "multiples") ansicht.filter = { ...ansicht.filter, je_einheit: true };
  const form = FORMEN[formFuer(ansicht)];
  const buehne = sec.querySelector(".buehne");
  const svg = buehne.querySelector(".svg");
  const legende = buehne.querySelector(".legende");
  const zahlen = buehne.querySelector(".zahlen");
  const optionen = { hervorheben: schritt.hervorheben || [], titel: schritt.beschreibung };
  // Zwei Durchgänge: Das Bild bekommt, was die Bühne nach Legende und Zahlenzeile übrig lässt —
  // und deren Höhe kennt man erst, wenn die Legende dieses Schritts steht. Der erste Durchgang
  // liefert nur Legende und Zahlen; danach ist .svg (flex: 1) genau der Rest der Bühne.
  const vorab = form.zeige(ansicht, daten, { ...zeichenflaeche(svg.clientWidth, svg.clientHeight), ...optionen });
  legende.innerHTML = legendeHtml(vorab.legende);
  zahlen.textContent = zahlenText(vorab, ansicht);
  const r = form.zeige(ansicht, daten, { ...zeichenflaeche(svg.clientWidth, svg.clientHeight), ...optionen });
  // Schrittwechsel als Überblendung des bleibenden Behälters: Übergänge auf den SVG-Knoten selbst
  // liefen nie, weil innerHTML sie alle ersetzt. Bei reduzierter Bewegung wird hart getauscht.
  svg.innerHTML = r.svg;
  if (!reduziert) {
    svg.classList.add("blass");
    requestAnimationFrame(() => requestAnimationFrame(() => svg.classList.remove("blass")));
  }
  svg.setAttribute("aria-label", schritt.beschreibung || "");
  const werte = werteJeEinheit(ansicht, daten);
  svg.querySelectorAll(".einheit").forEach((el) => el.addEventListener("click", () => zeigeDetail(el.dataset.id, werte, ansicht, el.querySelector("title")?.textContent)));
}

const legendeHtml = (legende) => legende.map((l) => `<span><i style="background:${esc(l.farbe)}"></i>${esc(l.name)}${l.text && l.text !== l.name ? ` <small>${esc(l.text)}</small>` : ""}</span>`).join("");

// Präzision: jeder Schritt nennt den Hinweis der Form, wie viele Einheiten der Ebene überhaupt
// gezeichnet sind (eine Rangliste zeigt nie alle) und wie viele unter min_n grau bleiben.
// Ohne bekannte Gesamtzahl (Formen, die nicht über eine Ebene gehen) wird keine erfunden.
function zahlenText(r, ansicht) {
  const gezeichnet = Number.isInteger(r.zahlen.einheiten_gesamt)
    ? `${r.zahlen.einheiten} von ${r.zahlen.einheiten_gesamt} Einheiten gezeichnet`
    : `${r.zahlen.einheiten} Einheiten gezeichnet`;
  return `${r.zahlen.hinweis} · ${gezeichnet} · ${r.zahlen.unter_min} unter ${ansicht.min_n} ${nennerText(ansicht)} (grau, nicht eingefärbt)`;
}

// Detailkasten zu einer angeklickten Einheit: Name, Nennungen, Anteile je Gruppe, Hinweis unter min_n.
function zeigeDetail(id, werte, ansicht, titelFallback) {
  const w = werte.find((x) => x.id === id);
  const d = w ? detailText(w, ansicht) : { titel: titelFallback || id, zeilen: [] };
  const box = document.getElementById("detail");
  box.innerHTML = `<button class="schliessen" type="button" aria-label="Schließen">✕</button><h4>${esc(d.titel)}</h4>${d.zeilen.map((z) => `<p>${esc(z)}</p>`).join("")}`
    + (ansicht.ebene === "stadtteil" && w ? `<p><a href="karte.html?stadtteil=${encodeURIComponent(id)}">Auf der Karte zeigen</a></p>` : "");
  box.hidden = false;
  box.querySelector(".schliessen").onclick = () => { box.hidden = true; };
}

// Verbindet die Schritte eines Kapitels mit der Grafik: Scrollama beim Scrollen, Fokus für die
// Tastatur. Der erste Schritt wird sofort gezeichnet, damit die Grafik nie leer bleibt.
function bindeKapitel(sec, k) {
  const schritte = Object.fromEntries((k.schritte || []).map((s) => [s.id, s]));
  const zeigeSchritt = (el) => {
    if (!el) return;
    sec.querySelectorAll(".schritt").forEach((e) => e.classList.remove("aktiv"));
    el.classList.add("aktiv");
    zeichne(sec, schritte[el.dataset.schritt]);
  };
  sec.querySelectorAll(".schritt").forEach((el) => el.addEventListener("focus", () => zeigeSchritt(el)));
  if (window.scrollama) {
    const sc = window.scrollama();
    sc.setup({ step: `#${sec.id} .schritt`, offset: 0.6 }).onStepEnter((r) => zeigeSchritt(r.element));
    // Nach einer Größenänderung (Drehen des Handys) muss die Bühne neu vermessen werden.
    addEventListener("resize", () => { sc.resize(); zeigeSchritt(sec.querySelector(".schritt.aktiv")); });
  }
  zeigeSchritt(sec.querySelector(".schritt"));
}
