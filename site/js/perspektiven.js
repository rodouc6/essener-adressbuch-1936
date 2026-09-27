// site/js/perspektiven.js — Perspektiven-Seite (Spec §6.2): lädt die Kapitel, baut je Kapitel die
// Schritte und die klebende Grafik, schaltet beim Scrollen (Scrollama) oder per Tastaturfokus
// zwischen den Schritten um und öffnet den Detailkasten zu einer angeklickten Einheit.
// Browsercode; alles Prüfbare steht in perspektiven_modell.js.
import { Lader } from "./daten.js";
import { normalisiere } from "./ansicht.js";
import { filterEinheiten, ladeEbenen, werteJeEinheit } from "./daten_ebenen.js";
import { esc, nennerText } from "./formen/skalen.js";
import * as balken from "./formen/balken.js";
import * as rangliste from "./formen/rangliste.js";
import * as stadtteilkarte from "./formen/stadtteilkarte.js";
import * as bubbles from "./formen/bubbles.js";
import { detailLage, detailText, detailTextGruppe, detailZustand, DETAIL_ZU, formFuer, fuellePlatzhalter, linkKarte, linkWerkstatt, sichtbareKapitel, zeichenflaeche } from "./perspektiven_modell.js";

const FORMEN = { balken, rangliste, stadtteilkarte, bubbles };
const lader = new Lader();
const vorschau = new URLSearchParams(location.search).get("vorschau") === "1";
const reduziert = matchMedia("(prefers-reduced-motion: reduce)").matches;
// Nur Geräte mit echtem Zeiger bekommen die Schwebe-Anzeige; auf dem Touchscreen bliebe der Kasten
// sonst nach jeder Berührung offen, ohne dass ein „Verlassen“ je käme.
const schweben = matchMedia("(hover: hover) and (pointer: fine)").matches;
// Auf schmalen Schirmen liegt der Kasten als Leiste am unteren Rand (CSS), nicht an der Einheit.
const schmal = matchMedia("(max-width: 899px)");
let detail = DETAIL_ZU;
// Rechteck der Einheit, an der der Kasten zuletzt aufgegangen ist; festgestellt bleibt er dort.
let anker = null;
// Die gerade gezeichnete Ansicht: ihre Werte füllen den Detailkasten, ihr SVG trägt die Hervorhebung.
let gezeigt = { werte: [], ansicht: null, svg: null };

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
    // Die Überschrift des Bildes steht als HTML über dem SVG, damit sie umbrechen kann.
    + `<div class="grafik"><div class="buehne"><div class="titel" aria-hidden="true"></div><div class="svg" aria-hidden="true"></div><div class="legende" aria-hidden="true"></div><div class="zahlen"></div></div></div>`
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
  // Grafik nicht mehr passen — auch dann, wenn er festgestellt war.
  melde("schrittwechsel");
  const ansicht = normalisiere(schritt.ansicht);
  if (schritt.ansicht && schritt.ansicht.form === "multiples") ansicht.filter = { ...ansicht.filter, je_einheit: true };
  const form = FORMEN[formFuer(ansicht)];
  const buehne = sec.querySelector(".buehne");
  const svg = buehne.querySelector(".svg");
  const legende = buehne.querySelector(".legende");
  const zahlen = buehne.querySelector(".zahlen");
  const optionen = { hervorheben: schritt.hervorheben || [] };
  buehne.querySelector(".titel").textContent = schritt.beschreibung || "";
  // Zwei Durchgänge: Das Bild bekommt, was die Bühne nach Überschrift, Legende und Zahlenzeile
  // übrig lässt — und deren Höhe kennt man erst, wenn die Legende dieses Schritts steht. Der
  // erste Durchgang liefert nur Legende und Zahlen; danach ist .svg (flex: 1) genau der Rest.
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
  gezeigt = { werte: werteJeEinheit(ansicht, daten), ansicht, svg };
  svg.querySelectorAll(".einheit").forEach((el) => {
    const titel = el.querySelector("title")?.textContent;
    el.addEventListener("click", () => melde("klick", el.dataset.id, titel, el.getBoundingClientRect()));
    if (!schweben) return;
    el.addEventListener("mouseenter", () => melde("schweben", el.dataset.id, titel, el.getBoundingClientRect()));
    el.addEventListener("mouseleave", () => melde("verlassen", el.dataset.id, titel));
  });
}

// Funktionsdeklaration, kein const: seiteAufbauen läuft schon beim Top-Level-await, also bevor
// spätere const-Zuweisungen des Moduls initialisiert wären.
function legendeHtml(legende) {
  return legende.map((l) => `<span><i style="background:${esc(l.farbe)}"></i>${esc(l.name)}${l.text && l.text !== l.name ? ` <small>${esc(l.text)}</small>` : ""}</span>`).join("");
}

// Präzision: jeder Schritt nennt den Hinweis der Form, wie viele Einheiten der Ebene überhaupt
// gezeichnet sind (eine Rangliste zeigt nie alle) und wie viele unter min_n grau bleiben.
// Ohne bekannte Gesamtzahl (Formen, die nicht über eine Ebene gehen) wird keine erfunden.
function zahlenText(r, ansicht) {
  const gezeichnet = Number.isInteger(r.zahlen.einheiten_gesamt)
    ? `${r.zahlen.einheiten} von ${r.zahlen.einheiten_gesamt} Einheiten gezeichnet`
    : `${r.zahlen.einheiten} Einheiten gezeichnet`;
  return `${r.zahlen.hinweis} · ${gezeichnet} · ${r.zahlen.unter_min} unter ${ansicht.min_n} ${nennerText(ansicht)} (grau, nicht eingefärbt)`;
}

// Ein Ereignis an einer Einheit (Schweben, Verlassen, Klick) oder an der Seite (Schließen,
// Schrittwechsel) fortschreiben und den Detailkasten neu zeichnen.
function melde(ereignis, id = null, titelFallback = "", rechteck = null) {
  detail = detailZustand(detail, ereignis, id);
  if (rechteck && detail.sichtbar && detail.id === id) anker = rechteck;
  // Die Einheit, über der der Zeiger steht (oder die festgestellt ist), hebt sich im Bild ab.
  gezeigt.svg?.querySelectorAll(".einheit").forEach((el) =>
    el.classList.toggle("angesehen", detail.sichtbar && el.dataset.id === detail.id));
  zeichneDetail(titelFallback);
}

// Detailkasten zur Einheit unter dem Zeiger: Name, Nennungen, Anteile je Gruppe, Hinweis unter
// min_n. Festgestellt (angeklickt) trägt er den Schließknopf und den Kartenlink; flüchtig
// (schwebend) bleibt er knapp — dort führt kein Klick hin, ohne den Zeiger wegzunehmen.
function zeichneDetail(titelFallback = "") {
  const box = document.getElementById("detail");
  const { werte, ansicht } = gezeigt;
  box.classList.toggle("fest", detail.fest);
  if (!detail.sichtbar || !ansicht) { box.hidden = true; box.innerHTML = ""; return; }
  // Einheit (Stadtteil, Straße …) oder — beim Gesamtbalken — ein Gruppensegment über alle Einheiten.
  const w = werte.find((x) => x.id === detail.id);
  const d = w ? detailText(w, ansicht)
    : (detailTextGruppe(detail.id, filterEinheiten(werte, ansicht.filter), ansicht) || { titel: titelFallback || detail.id, zeilen: [] });
  box.innerHTML = (detail.fest ? `<button class="schliessen" type="button" aria-label="Schließen">✕</button>` : "")
    + `<h4>${esc(d.titel)}</h4>${d.zeilen.map((z) => `<p>${esc(z)}</p>`).join("")}`
    + (detail.fest && ansicht.ebene === "stadtteil" && w ? `<p><a href="karte.html?stadtteil=${encodeURIComponent(detail.id)}">Auf der Karte zeigen</a></p>` : "")
    + (detail.fest ? "" : `<p class="wink">Klicken hält die Angaben fest.</p>`);
  box.hidden = false;
  if (detail.fest) box.querySelector(".schliessen").onclick = () => melde("schliessen");
  // An der Einheit ausrichten — erst nach dem Füllen, denn die Maße des Kastens hängen am Text.
  // Schmal: Leiste am unteren Rand aus dem CSS, keine Inline-Lage.
  if (schmal.matches || !anker) { box.style.left = box.style.top = ""; return; }
  const lage = detailLage(anker, { width: box.offsetWidth, height: box.offsetHeight }, { width: innerWidth, height: innerHeight });
  box.style.left = `${lage.left}px`;
  box.style.top = `${lage.top}px`;
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
