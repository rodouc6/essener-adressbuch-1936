// site/js/perspektiven.js — Perspektiven-Seite (Spec §6.2): lädt die Kapitel, baut je Kapitel die
// Schritte und die klebende Grafik, schaltet beim Scrollen (Scrollama) oder per Tastaturfokus
// zwischen den Schritten um und öffnet den Detailkasten zu einer angeklickten Einheit.
// Browsercode; alles Prüfbare steht in perspektiven_modell.js.
import { Lader } from "./daten.js";
import { normalisiere } from "./ansicht.js";
import { filterEinheiten, ladeEbenen, werteJeEinheit } from "./daten_ebenen.js";
import { esc, formatZahl, nennerText } from "./formen/skalen.js";
import { faksimileUrl } from "./popup.js";
import * as balken from "./formen/balken.js";
import * as rangliste from "./formen/rangliste.js";
import * as stadtteilkarte from "./formen/stadtteilkarte.js";
import * as bubbles from "./formen/bubbles.js";
import * as trichter from "./formen/trichter.js";
import { datenbasisLink, detailLage, detailText, detailTextGruppe, detailTextStufe, detailZustand, DETAIL_ZU, formFuer, fuellePlatzhalter, herkunftAktuell, herkunftDatei, herkunftLink, herkunftPfad, herkunftTabelle, linkKarte, linkWerkstatt, sichtbareKapitel, zeichenflaeche } from "./perspektiven_modell.js";

const FORMEN = { balken, rangliste, stadtteilkarte, bubbles, trichter };
const istTrichter = (a) => !!a && (a.form === "trichter" || a.daten === "kennzahlen");
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
let gezeigt = { werte: [], ansicht: null, svg: null, trichter: false, ausschluss: "" };
// Sichtbarer Kapitelindex — die Datenbasis-Zeile verlinkt nur, wenn Kapitel 0 darin steht.
let sichtbar = [];
// Herkunftsdateien (site/daten/herkunft/*.json), nachgeladen beim ersten Bedarf; undefined = wird
// geladen, null = Laden fehlgeschlagen (alter Export) — dann bleibt der Kasten ohne Pfad.
const herkunft = new Map();
let faksimile = null;
// Zeile der zuletzt gemeldeten Einheit (Bubbles geben ihre Zahlenzeile per data-zeile mit); für das
// Neuzeichnen nach dem Nachladen, wenn der Kasten inzwischen eine andere Einheit derselben Datei zeigt.
let detailZeile = "";

// Zahlwörter für die Einleitung: „Ein Blick“, „Zwei Blicke“, „Drei Blicke“, „Vier Blicke“, ab fünf Ziffern.
const ZAHLWORT = { 1: "Ein", 2: "Zwei", 3: "Drei", 4: "Vier" };

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
  faksimile = (await lader.faksimile()) || {};
  const index = sichtbareKapitel((await lader.perspektivenIndex()) || [], vorschau);
  sichtbar = index;
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
    const kopf = `<article class="schritt" id="s-${esc(k.id)}-${esc(s.id)}" data-schritt="${esc(s.id)}" tabindex="0"><p>${esc(s.text)}</p><p class="sr-only">${esc(s.beschreibung || "")}</p>`;
    // Trichter zeigen Kennzahlen, keine Einheiten der Karte — Karten- und Werkstattlink ergäben nichts.
    if (istTrichter(s.ansicht)) return `${kopf}</article>`;
    const a = normalisiere(s.ansicht);
    return `${kopf}<p class="links"><a href="${esc(linkKarte(a))}">Auf der Karte öffnen</a> · <a href="${esc(linkWerkstatt(a))}">In der Werkstatt öffnen</a></p></article>`;
  }).join("");
  const quellen = (Array.isArray(k.quellen) ? k.quellen : []).map((q) => esc(q)).join(" · ");
  const link = datenbasisLink(k, sichtbar);
  const datenbasis = k.datenbasis
    ? `<p class="datenbasis">${esc(fuellePlatzhalter(k.datenbasis, daten.kennzahlen))}${link ? ` <a href="${esc(link)}">Datenbasis ›</a>` : ""}</p>` : "";
  return `<header><h2>${esc(k.titel)}</h2><p class="untertitel">${esc(k.untertitel || "")}</p>${datenbasis}<p>${esc(k.einleitung || "")}</p></header>`
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
function zeichne(sec, schritt, k) {
  if (!schritt) return;
  // Der Detailkasten gehört zur vorigen Ansicht; stehen bliebe er mit Zahlen, die zur neuen
  // Grafik nicht mehr passen — auch dann, wenn er festgestellt war.
  melde("schrittwechsel");
  // Trichter (Kapitel 0) zeichnen Kennzahlen, keine Ebenen-Ansicht: kein normalisiere, keine Einheiten.
  const trichterSchritt = istTrichter(schritt.ansicht);
  const ansicht = trichterSchritt ? schritt.ansicht : normalisiere(schritt.ansicht);
  if (!trichterSchritt && schritt.ansicht && schritt.ansicht.form === "multiples") ansicht.filter = { ...ansicht.filter, je_einheit: true };
  const form = FORMEN[formFuer(ansicht)];
  const buehne = sec.querySelector(".buehne");
  const svg = buehne.querySelector(".svg");
  const legende = buehne.querySelector(".legende");
  const zahlen = buehne.querySelector(".zahlen");
  const optionen = { hervorheben: schritt.hervorheben || [], ausschlussText: (k && k.ausschluss) || "" };
  buehne.querySelector(".titel").textContent = schritt.beschreibung || "";
  // Vor dem Messen wieder die ganze Bühne freigeben — der vorige Schritt kann sie verkleinert haben.
  svg.style.flex = "";
  // Zwei Durchgänge: Das Bild bekommt, was die Bühne nach Überschrift, Legende und Zahlenzeile
  // übrig lässt — und deren Höhe kennt man erst, wenn die Legende dieses Schritts steht. Der
  // erste Durchgang liefert nur Legende und Zahlen; danach ist .svg (flex: 1) genau der Rest.
  const vorab = form.zeige(ansicht, daten, { ...zeichenflaeche(svg.clientWidth, svg.clientHeight), ...optionen });
  legende.innerHTML = legendeHtml(vorab.legende);
  zahlen.textContent = trichterSchritt ? vorab.zahlen.hinweis : zahlenText(vorab, ansicht);
  const r = form.zeige(ansicht, daten, { ...zeichenflaeche(svg.clientWidth, svg.clientHeight), ...optionen });
  // Schrittwechsel als Überblendung des bleibenden Behälters: Übergänge auf den SVG-Knoten selbst
  // liefen nie, weil innerHTML sie alle ersetzt. Bei reduzierter Bewegung wird hart getauscht.
  svg.innerHTML = r.svg;
  // Formen, die nur so hoch sind wie ihr Inhalt (Trichter, Balken), geben den Rest der Bühne frei:
  // Legende und Zahlenzeile rücken direkt unter das Bild, statt am unteren Rand zu hängen.
  if (Number.isFinite(r.hoehe)) svg.style.flex = "0 0 auto";
  if (!reduziert) {
    svg.classList.add("blass");
    requestAnimationFrame(() => requestAnimationFrame(() => svg.classList.remove("blass")));
  }
  svg.setAttribute("aria-label", schritt.beschreibung || "");
  gezeigt = { werte: trichterSchritt ? r.werte : werteJeEinheit(ansicht, daten), ansicht, svg, trichter: trichterSchritt, ausschluss: optionen.ausschlussText };
  svg.querySelectorAll(".einheit").forEach((el) => {
    const zeile = el.dataset.zeile || "";
    el.addEventListener("click", () => melde("klick", el.dataset.id, zeile, el.getBoundingClientRect()));
    if (!schweben) return;
    el.addEventListener("mouseenter", () => melde("schweben", el.dataset.id, zeile, el.getBoundingClientRect()));
    el.addEventListener("mouseleave", () => melde("verlassen", el.dataset.id, zeile));
  });
}

// Funktionsdeklaration, kein const: seiteAufbauen läuft schon beim Top-Level-await, also bevor
// spätere const-Zuweisungen des Moduls initialisiert wären.
function legendeHtml(legende) {
  return legende.map((l) => {
    const stil = l.muster === "schraffur" ? `background: repeating-linear-gradient(45deg, ${esc(l.farbe)} 0 3px, #fff 3px 6px)` : `background:${esc(l.farbe)}`;
    return `<span><i style="${stil}"></i>${esc(l.name)}${l.text && l.text !== l.name ? ` <small>${esc(l.text)}</small>` : ""}</span>`;
  }).join("");
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
function melde(ereignis, id = null, zeile = "", rechteck = null) {
  detail = detailZustand(detail, ereignis, id);
  if (detail.sichtbar && detail.id === id) detailZeile = zeile;
  if (rechteck && detail.sichtbar && detail.id === id) anker = rechteck;
  // Die Einheit, über der der Zeiger steht (oder die festgestellt ist), hebt sich im Bild ab.
  gezeigt.svg?.querySelectorAll(".einheit").forEach((el) =>
    el.classList.toggle("angesehen", detail.sichtbar && el.dataset.id === detail.id));
  zeichneDetail(zeile);
}

// Detailkasten zur Einheit unter dem Zeiger: Name, Nennungen, Anteile je Gruppe, Hinweis unter
// min_n. Festgestellt (angeklickt) trägt er den Schließknopf und den Kartenlink; flüchtig
// (schwebend) bleibt er knapp — dort führt kein Klick hin, ohne den Zeiger wegzunehmen.
// Welche Art Einheit der Kasten zeigt: Segment eines Gesamtbalkens (Gruppenname), dessen Regel-Teil,
// Kreis einer Bubbles-Ansicht (Norm, Eigentümer, Rubrik), sonst eine Einheit der Ebene.
function kontextVon(id, ansicht) {
  if (!ansicht || gezeigt.trichter) return null;
  if (id === "ausgeschlossen") return { art: "ausgeschlossen", daten: ansicht.daten, id, gruppe: null };
  if (typeof id === "string" && id.endsWith("#regel")) {
    const g = (ansicht.gruppen || []).find((x) => x.name === id.slice(0, -"#regel".length));
    return g ? { art: "regel", daten: ansicht.daten, id, gruppe: g } : null;
  }
  const g = (ansicht.gruppen || []).find((x) => x.name === id);
  if (g) return { art: "segment", daten: ansicht.daten, id, gruppe: g };
  if (ansicht.form === "bubbles") return { art: "kreis", daten: ansicht.daten, id, gruppe: null };
  return { art: "einheit", daten: ansicht.daten, id, gruppe: null };
}

// Herkunftsdatei holen; nach dem Laden den Kasten neu zeichnen, falls er noch etwas zeigt, das diese Datei
// braucht (dieselbe Einheit oder ein Nachbar derselben Datei — sonst bliebe „wird geladen“ stehen).
function ladeHerkunft(name) {
  if (herkunft.has(name)) return;
  herkunft.set(name, undefined);            // „wird geladen“
  lader.herkunft(name).then((h) => {
    herkunft.set(name, h || null);
    if (!h) console.warn(`Herkunft ${name}: nicht geladen (alter Export?)`);
    if (herkunftAktuell(detail, name, herkunftDatei(kontextVon(detail.id, gezeigt.ansicht)))) zeichneDetail(detailZeile);
  }).catch((e) => { herkunft.set(name, null); console.warn(`Herkunft ${name}:`, e); });
}

const MARKE = { hand: "Hand", vorschlag: "Vorschlag", claude: "Prinzipien", regel: "Regel", ohne: "ohne Quelle" };
const markeHtml = (m) => `<span class="q ${esc(m.art)}">${m.anteil < 1 ? `${Math.round(m.anteil * 100)} % ` : ""}${MARKE[m.art] || m.art}</span>`;

function pfadHtml(pfad) {
  if (!pfad || !pfad.length) return "";
  const stufen = pfad.map((s) => `<span class="stufe"><small>${esc(s.label)}</small>${esc(s.wert)}${(s.marken || []).map(markeHtml).join("")}</span>`).join(`<span class="pfeil">›</span>`);
  const beispiele = pfad.beispiele && pfad.beispiele.length ? `<p class="wink">Häufigste Schreibweisen: ${pfad.beispiele.map((b) => `${esc(b[0])} (${formatZahl(b[1])})`).join(", ")}</p>` : "";
  const zusatz = pfad.zusatz ? `<p class="wink">${esc(pfad.zusatz)}</p>` : "";
  const hinweis = pfad.hinweis ? `<p class="wink">${esc(pfad.hinweis)}</p>` : "";
  return `<div class="pfad">${stufen}</div>${zusatz}${beispiele}${hinweis}`;
}

function tabelleHtml(t, kontext) {
  if (!t) return "";
  const zelle = (v, i) => t.kopf[i] === "Quelle" ? `<td>${v ? markeHtml({ art: v, anteil: 1 }) : "—"}</td>` : typeof v === "number" ? `<td class="z">${formatZahl(v)}</td>` : `<td>${esc(v)}</td>`;
  const zeilen = t.zeilen.map((z) => `<tr>${z.map(zelle).join("")}</tr>`).join("");
  const link = herkunftLink(kontext);
  // Einzelobjekte (Norm, Eigentümer, Rubrik) führen in die Suche — auch, wenn die Tabelle schon alles zeigt.
  const linkText = t.gesamt > t.zeilen.length ? `alle ${formatZahl(t.gesamt)} in der Suche ›` : "in der Suche zeigen ›";
  const alle = link ? `<tr><td colspan="${t.kopf.length}"><a href="${esc(link)}">${linkText}</a></td></tr>` : "";
  const bild = t.seite && faksimile && faksimile[t.seite] ? ` · <a href="${esc(faksimileUrl(faksimile[t.seite]))}" target="_blank" rel="noopener">Faksimile Seite ${esc(t.seite)}</a>` : "";
  return `<details open><summary>Woher kommt diese Zahl?</summary><table><tr>${t.kopf.map((k) => `<th>${esc(k)}</th>`).join("")}</tr>${zeilen}${alle}</table>`
    + `<p class="beleg">${esc(t.hinweis)}${bild}</p></details>`;
}

function zeichneDetail(zeile = "") {
  const box = document.getElementById("detail");
  const { werte, ansicht } = gezeigt;
  box.classList.toggle("fest", detail.fest);
  if (!detail.sichtbar || !ansicht) { box.hidden = true; box.innerHTML = ""; return; }
  // Einheit (Stadtteil, Straße …), beim Gesamtbalken ein Gruppensegment über alle Einheiten, bei
  // Bubbles ein Kreis (Eigentümer, Beruf), dessen Zeile die Form selbst mitgibt (data-zeile).
  const w = werte.find((x) => x.id === detail.id);
  const d = gezeigt.trichter ? (w ? detailTextStufe(w) : { titel: detail.id, zeilen: [] })
    : w ? detailText(w, ansicht)
    : (detailTextGruppe(detail.id, filterEinheiten(werte, ansicht.filter), ansicht, gezeigt.ausschluss) || { titel: detail.id, zeilen: zeile ? [zeile] : [] });
  box.innerHTML = (detail.fest ? `<button class="schliessen" type="button" aria-label="Schließen">✕</button>` : "")
    + `<h4>${esc(d.titel)}</h4>${d.zeilen.map((z) => `<p>${esc(z)}</p>`).join("")}`
    + (detail.fest && ansicht.ebene === "stadtteil" && w ? `<p><a href="karte.html?stadtteil=${encodeURIComponent(detail.id)}">Auf der Karte zeigen</a></p>` : "");
  // Herkunftspfad (Spec Herkunftspfad §4): Kette direkt unter der Zahlenzeile beim Schweben, Belegtabelle
  // beim Klick; die Datei kommt beim ersten Bedarf, bis dahin steht „wird geladen“.
  const kontext = kontextVon(detail.id, ansicht);
  const datei = herkunftDatei(kontext);
  if (datei) {
    if (!herkunft.has(datei)) ladeHerkunft(datei);
    const h = herkunft.get(datei);
    if (h === undefined) box.insertAdjacentHTML("beforeend", `<p class="wink">Herkunft wird geladen …</p>`);
    else if (h) {
      box.insertAdjacentHTML("beforeend", pfadHtml(herkunftPfad(kontext, h, ansicht)));
      if (detail.fest) box.insertAdjacentHTML("beforeend", tabelleHtml(herkunftTabelle(kontext, h, ansicht), kontext));
    }
  }
  if (!detail.fest) box.insertAdjacentHTML("beforeend", `<p class="wink">Klicken hält die Angaben fest.</p>`);
  box.hidden = false;
  if (detail.fest) box.querySelector(".schliessen").onclick = () => melde("schliessen");
  // An der Einheit ausrichten — erst nach dem Füllen, denn die Maße des Kastens hängen am Text.
  // Schmal: Leiste am unteren Rand aus dem CSS, keine Inline-Lage.
  if (schmal.matches || !anker) { box.style.cssText = ""; return; }
  const lage = detailLage(anker, { width: box.offsetWidth, height: box.offsetHeight }, { width: innerWidth, height: innerHeight });
  // right/bottom ausdrücklich lösen: stünde eines davon aus einer Stilregel, zöge es den Kasten auf.
  box.style.cssText = `left:${lage.left}px; top:${lage.top}px; right:auto; bottom:auto`;
}

// Verbindet die Schritte eines Kapitels mit der Grafik: Scrollama beim Scrollen, Fokus für die
// Tastatur. Der erste Schritt wird sofort gezeichnet, damit die Grafik nie leer bleibt.
function bindeKapitel(sec, k) {
  const schritte = Object.fromEntries((k.schritte || []).map((s) => [s.id, s]));
  const zeigeSchritt = (el) => {
    if (!el) return;
    sec.querySelectorAll(".schritt").forEach((e) => e.classList.remove("aktiv"));
    el.classList.add("aktiv");
    zeichne(sec, schritte[el.dataset.schritt], k);
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
