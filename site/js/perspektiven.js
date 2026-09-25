// site/js/perspektiven.js — Perspektiven-Seite (Spec §6.2): lädt die Kapitel, baut je Kapitel die
// Schritte und die klebende Grafik, schaltet beim Scrollen (Scrollama) oder per Tastaturfokus
// zwischen den Schritten um und öffnet den Detailkasten zu einer angeklickten Einheit.
// Browsercode; alles Prüfbare steht in perspektiven_modell.js.
import { Lader } from "./daten.js";
import { normalisiere } from "./ansicht.js";
import { ladeEbenen, werteJeEinheit } from "./daten_ebenen.js";
import { esc } from "./formen/skalen.js";
import * as balken from "./formen/balken.js";
import * as rangliste from "./formen/rangliste.js";
import * as stadtteilkarte from "./formen/stadtteilkarte.js";
import * as bubbles from "./formen/bubbles.js";
import { detailText, formFuer, fuellePlatzhalter, linkKarte, linkWerkstatt, sichtbareKapitel } from "./perspektiven_modell.js";

const FORMEN = { balken, rangliste, stadtteilkarte, bubbles };
const lader = new Lader();
const vorschau = new URLSearchParams(location.search).get("vorschau") === "1";
const reduziert = matchMedia("(prefers-reduced-motion: reduce)").matches;

const daten = await ladeEbenen(lader);
const index = sichtbareKapitel((await lader.perspektivenIndex()) || [], vorschau);
document.getElementById("einleitung").textContent = fuellePlatzhalter("Drei Blicke auf das Adressbuch von 1936: {adressen} verortete Adressen, Stand {stand}. Jede Grafik nennt, wie viel geprüft ist und was ausgeschlossen bleibt.", daten.kennzahlen);
document.getElementById("inhalt").innerHTML = index.map((k) => `<li><a href="#k-${esc(k.id)}">${esc(k.titel)}</a>${k.freigegeben ? "" : " <small>(Vorschau)</small>"}</li>`).join("");

if (index.length === 0) {
  document.getElementById("kapitel").innerHTML = '<p class="leer">Noch kein Kapitel freigegeben.</p>';
} else {
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
    + `<div class="grafik"><div class="svg" aria-hidden="true"></div><div class="legende" aria-hidden="true"></div><div class="zahlen"></div></div>`
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
  const grafik = sec.querySelector(".grafik");
  const breite = grafik.clientWidth || 600, hoehe = Math.max(320, Math.min(grafik.clientHeight || 500, 700));
  const r = form.zeige(ansicht, daten, { breite, hoehe, hervorheben: schritt.hervorheben || [], titel: schritt.beschreibung });
  // Schrittwechsel als Überblendung des bleibenden Behälters: Übergänge auf den SVG-Knoten selbst
  // liefen nie, weil innerHTML sie alle ersetzt. Bei reduzierter Bewegung wird hart getauscht.
  const svg = grafik.querySelector(".svg");
  svg.innerHTML = r.svg;
  if (!reduziert) {
    svg.classList.add("blass");
    requestAnimationFrame(() => requestAnimationFrame(() => svg.classList.remove("blass")));
  }
  grafik.querySelector(".legende").innerHTML = r.legende.map((l) => `<span><i style="background:${esc(l.farbe)}"></i>${esc(l.name)}${l.text && l.text !== l.name ? ` <small>${esc(l.text)}</small>` : ""}</span>`).join("");
  // Präzision: jeder Schritt nennt den Hinweis der Form und die Zahl der Einheiten unter min_n.
  grafik.querySelector(".zahlen").textContent = r.zahlen.hinweis + (r.zahlen.unter_min ? ` · ${r.zahlen.unter_min} Einheiten unter ${ansicht.min_n} Nennungen (grau, nicht eingefärbt)` : "");
  svg.setAttribute("aria-label", schritt.beschreibung || "");
  const werte = werteJeEinheit(ansicht, daten);
  svg.querySelectorAll(".einheit").forEach((el) => el.addEventListener("click", () => zeigeDetail(el.dataset.id, werte, ansicht, el.querySelector("title")?.textContent)));
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
    addEventListener("resize", () => sc.resize());
  }
  zeigeSchritt(sec.querySelector(".schritt"));
}
