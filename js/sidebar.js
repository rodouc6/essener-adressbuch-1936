import { EBENEN } from "./konfig.js";
import { esc, hausHtml, trefferzeileHtml, heutigeAdresse } from "./popup.js";
import { ansichtTitel } from "./ansicht_farben.js";
import { nennerText } from "./formen/skalen.js";
import { vergleichsleisteHtml, gruppenZuordnung } from "./vergleich.js";
import { baumHtml, kopfHtml, grundlageHtml } from "./themenbaum.js";

const STUFEN = ["griff", "halb", "voll"];

export class Sidebar {
  constructor(el, lader, aktionen) {
    this.el = el; this.lader = lader; this.a = aktionen;
    this.inhalt = el.querySelector("#inhalt");
    this.pills = el.querySelector("#pills");
    this.vorschlaegeEl = el.querySelector("#vorschlaege");
    this.themenkopf = el.querySelector("#themenkopf");
    // Fehlt das Element (altes karte.html aus dem Browser-Cache, Befund 2026-09-29), wird es angelegt statt abzustürzen.
    this.themenliste = el.querySelector("#themenliste") || this.pills.insertAdjacentElement("afterend", Object.assign(document.createElement("div"), { className: "themenliste", id: "themenliste", hidden: true }));
    this.themenliste.addEventListener("click", (ev) => { const th = ev.target.closest("[data-thema]"); if (th) this.a.onZustand({ thema: th.dataset.thema === this._themaAktiv ? "" : th.dataset.thema }); });
    this.ansichtkopf = el.querySelector("#ansichtkopf");
    this.suche = el.querySelector("#suche");
    this.stadtteile = []; this.berufe = [];
    this.baumZustand = { offen: null, alle: null };   // Klappzustand des Themenbaums — nicht in der URL (Spec Themenbaum §2)
    el.querySelector("#griff").addEventListener("click", () => this.naechsteStufe());
    this.themenkopf.addEventListener("click", (ev) => this._themenKlick(ev));
    this.themenkopf.addEventListener("change", (ev) => {
      const cb = ev.target.closest("[data-klasse]"); if (!cb || !this._thema) return;
      const alle = this._thema.schalter.klassen;
      const an = alle.filter((k) => this.themenkopf.querySelector(`[data-klasse="${CSS.escape(k)}"]`).checked);
      this.a.onKlassen(an.length === alle.length ? "" : an.length ? an.join(",") : "keine");
    });
    this.inhalt.addEventListener("click", (ev) => this._klick(ev));
    this.vorschlaegeEl.addEventListener("click", (ev) => {
      const e = ev.target.closest("[data-index]");
      if (e) return this.a.onVorschlag(this._vorschlagListe[+e.dataset.index]);
      const alle = ev.target.closest("[data-alle]");
      if (alle) this.a.onAlleVorschlaege(alle.dataset.alle);
    });
  }

  setzeStufe(s) { this.el.dataset.stufe = s; }
  naechsteStufe() { const i = STUFEN.indexOf(this.el.dataset.stufe); this.setzeStufe(STUFEN[(i + 1) % STUFEN.length]); }
  setzeFilteroptionen(stadtteile, berufe) { this.stadtteile = stadtteile || []; this.berufe = berufe || []; }

  // plus: mindestens ein Eigentümer ist gewählt — Eigentümer-Vorschläge fügen dann hinzu statt zu ersetzen (Spec 2026-09-29 §6).
  setzeVorschlaege(g, plus = false) {
    if (!g || g.gesamt === 0) { this.vorschlaegeEl.hidden = true; this._vorschlagListe = []; return; }
    const liste = []; let html = "";
    for (const [k, titel] of [["personen", "Personen"], ["strassen", "Straßen"], ["firmen", "Firmen"], ["berufe", "Berufe"], ["eigentuemer", "Eigentümer"], ["rubriken", "Rubriken"]]) {
      if (!g[k].length) continue;
      html += `<div class="gruppe">${titel}</div>`;
      for (const v of g[k]) {
        const zusatz = plus && (k === "eigentuemer" || k === "rubriken" || v.art === "ohdab") ? `<span class="plus" title="zum Vergleich hinzufügen">+</span>` : "";
        html += `<div class="eintrag" data-index="${liste.length}">${esc(v.text)}${zusatz}<small>${esc(v.untertitel)}</small></div>`;
        liste.push(v);
      }
      const gesamt = g[`gesamt_${k}`] ?? g[k].length;
      if (gesamt > g[k].length) html += `<div class="eintrag alle" data-alle="${k}">alle ${gesamt} anzeigen</div>`;
    }
    this._vorschlagListe = liste; this.vorschlaegeEl.innerHTML = html; this.vorschlaegeEl.hidden = false;
  }

  _pillsHtml(z) {
    return ["I", "II", "III"].map((t) =>
      `<button class="pill ${t}" data-ebene="${t}" aria-pressed="${z.ebene.includes(t)}">${EBENEN[t]}</button>`).join("");
  }

  _filterHtml(z) {
    const st = ['<option value="">alle Stadtteile</option>', ...this.stadtteile.map((s) =>
      `<option value="${esc(s.name)}"${z.stadtteil === s.name ? " selected" : ""}>${esc(s.name)} (${s.zeilen})</option>`)].join("");
    const pr = [["haus", "hausgenau"], ["strasse", "nur Straße"], ["stadtplan", "Stadtplan 1935"]].map(([k, t]) =>
      `<label><input type="checkbox" data-praez="${k}"${z.praez.includes(k) ? " checked" : ""}> ${t}</label>`).join("");
    return `<details class="filter" ${z.stadtteil || z.beruf || z.praez.length < 3 ? "open" : ""}><summary>Filter</summary>
      <label>Stadtteil <select data-filter="stadtteil">${st}</select></label>
      <div class="praez-filter">Präzision ${pr}</div>
      <label>Beruf / Zweig <input type="text" data-filter="beruf" list="berufsliste" value="${esc(z.beruf)}" placeholder="z. B. Bergm."></label>
      <datalist id="berufsliste">${this.berufe.slice(0, 2000).map((b) => `<option value="${esc(b[1])}">${esc(b[2])}</option>`).join("")}</datalist>
      </details>`;
  }

  zeigeSuche(z) {
    this.pills.innerHTML = this._pillsHtml(z);
    this.inhalt.innerHTML = this._filterHtml(z) +
      `<div class="hinweis">Tippe einen Namen, eine Straße, eine Firma, einen Beruf oder eine Gewerberubrik. Die Namen H bis J fehlen in der Transkription.</div>`;
    this._filterEreignisse(z);
  }

  // ergebnis: aus suche.treffer(); eig: Map adressId → Punkteigenschaften (soweit geladen)
  zeigeTreffer(z, ergebnis, eig, titel) {
    this.pills.innerHTML = this._pillsHtml(z);
    const n = ergebnis.personen ? ergebnis.personen.length : [...ergebnis.zaehler.values()].reduce((a, b) => a + b, 0);
    let html = this._filterHtml(z);
    // Eigentümer-Vergleich (Spec 2026-09-29 §6): Leiste je Gruppe vor der Kopfzeile, Farbpunkt je Zeile, Gruppenreihenfolge.
    const zuordnung = ergebnis.gruppen ? gruppenZuordnung(ergebnis.gruppen) : null;
    if (ergebnis.gruppen) html += vergleichsleisteHtml(ergebnis.gruppen, eig);
    html += `<div class="kopf"><b>${n} Treffer</b> · ${ergebnis.adressIds.length} Häuser` +
      `<button class="export" data-export="1">CSV</button></div>`;
    if (ergebnis.hinweisHJ) html += `<div class="hinweis warn">Keine Treffer. Die Namen H bis J fehlen in der Transkription (Seiten 186–258 des Teils I). Straßen und Firmen sind nicht betroffen.</div>`;
    const ids = zuordnung ? [...ergebnis.adressIds].sort((a, b) => zuordnung.get(a).gruppe - zuordnung.get(b).gruppe) : ergebnis.adressIds;
    const zeilen = ergebnis.personen
      ? ergebnis.personen.map((p) => ({ adressId: p.adressId, eintragId: p.eintragId, titel: p.text, untertitel: p.untertitel, stufe: (eig.get(p.adressId) || {}).stufe || "unbekannt" }))
      : ids.map((id) => { const e = eig.get(id) || {}; const g = zuordnung && zuordnung.get(id);
          return { adressId: id, titel: e.historisch ? heutigeAdresse(e) : id, untertitel: `${ergebnis.zaehler.get(id)} Einträge${e.historisch ? " · " + e.historisch : ""}`, stufe: e.stufe || "unbekannt",
                   farbe: g ? ergebnis.gruppen[g.gruppe].farbe : undefined, mehrfach: !!(g && g.mehrfach) }; });
    this._alleZeilen = zeilen; this._gezeigt = 0;
    html += `<div class="liste" id="liste"></div><button class="mehr" data-mehr="1" hidden>weitere 50</button>`;
    this.inhalt.innerHTML = html;
    this._filterEreignisse(z);
    this._mehrZeilen();
    if (!ergebnis.gruppen && ergebnis.adressIds.length >= 500) this._verteilung(ergebnis, eig);
  }

  _mehrZeilen() {
    const liste = this.inhalt.querySelector("#liste");
    const teil = this._alleZeilen.slice(this._gezeigt, this._gezeigt + 50);
    liste.insertAdjacentHTML("beforeend", teil.map(trefferzeileHtml).join(""));
    this._gezeigt += teil.length;
    this.inhalt.querySelector("[data-mehr]").hidden = this._gezeigt >= this._alleZeilen.length;
  }

  _verteilung(ergebnis, eig) {
    const je = new Map();
    for (const id of ergebnis.adressIds) { const s = (eig.get(id) || {}).stadtteil || "unbekannt"; je.set(s, (je.get(s) || 0) + ergebnis.zaehler.get(id)); }
    const top = [...je.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([s, n]) => `${esc(s)} ${n}`).join(" · ");
    this.inhalt.querySelector(".kopf").insertAdjacentHTML("afterend", `<div class="verteilung">Nach Stadtteil: ${top}</div>`);
  }

  // ebenen: aktive Kartenebenen — bei genau einer startet die Hausansicht im Reiter dieses Teils; ein
  // hervorgehobener Eintrag zieht seinen Teil vor, damit er sichtbar ist.
  // gruppen: Gruppen des laufenden Vergleichs — deren Treffer werden farbig hervorgehoben, der Reiter springt auf
  // den Teil des ersten Treffers, und die Ansicht scrollt dorthin (Sichtprüfung Christos 2026-09-29).
  zeigeHaus(eig, eintraege, hervorgehoben, faksimile = null, ebenen = [], gruppen = null) {
    const hv = hervorgehoben ? eintraege.find((e) => e.id === hervorgehoben) : null;
    const reiter = hv ? hv.teil : ebenen.length === 1 ? ebenen[0] : "auto";
    this._haus = { eig, eintraege, faksimile, gruppen };
    this._hausZeichnen(reiter, hervorgehoben);
    this.setzeStufe("voll");
  }

  _hausZeichnen(reiter, hervorgehoben = null) {
    const { eig, eintraege, faksimile, gruppen } = this._haus;
    this.inhalt.innerHTML = `<button class="zurueck" data-zurueck="1">‹ zurück</button>` + hausHtml(eig, eintraege, faksimile, reiter, gruppen);
    this.inhalt.querySelectorAll("[data-teil]").forEach((b) => b.addEventListener("click", () => { this._hausZeichnen(b.dataset.teil); this.inhalt.scrollTop = 0; }));
    const ziel = hervorgehoben ? this.inhalt.querySelector(`#e-${CSS.escape(hervorgehoben)}`) : this.inhalt.querySelector(".eintrag.hervor");
    if (ziel) { ziel.classList.add("hervor"); ziel.scrollIntoView({ block: "center" }); }
  }

  // Themenkopf (Spec Themenbaum §2): Kopf, Baum (Kästchen = Schalter, Pfeil = Klappliste, Pills = Vergleich), Grundlage.
  zeigeThema(thema, liste = null, vergleich = [], farben = [], klassen = "") {
    if (!thema || !this._thema || thema.id !== this._thema.id) this.baumZustand = { offen: null, alle: null };   // anderes Thema: nichts offen (Spec §2)
    this._thema = thema; this._liste = liste; this._vergleich = vergleich; this._farben = farben; this._klassen = klassen;
    this.markiereThema(thema ? thema.id : "");
    if (!thema) { this.themenkopf.hidden = true; this.themenkopf.innerHTML = ""; this.baumZustand = { offen: null, alle: null }; return; }
    this._baumZeichnen();
    this.themenkopf.hidden = false;
  }
  _baumZeichnen() {
    const t = this._thema;
    const baum = t.schalter ? baumHtml(t, this._liste, { klassen: this._klassen, vergleich: this._vergleich, farben: this._farben, ...this.baumZustand }) : "";
    // Neurendern darf die Scrollposition der offenen Pill-Liste nicht verlieren (Review 2026-09-29).
    const alt = this.themenkopf.querySelector(".pills-s");
    const scroll = alt ? alt.scrollTop : 0;
    this.themenkopf.innerHTML = kopfHtml(t) + baum + grundlageHtml(t);
    const neu = this.themenkopf.querySelector(".pills-s");
    if (neu && scroll) neu.scrollTop = scroll;
  }
  // Gewählte Pills in ihrer Gruppenfarbe füllen (Spec Themenbaum §2).
  markiereVergleich(vergleich, farben) { this._vergleich = vergleich; this._farben = farben; if (this._thema) this._baumZeichnen(); }
  setzeKlassen(klassen) { this._klassen = klassen; if (this._thema) this._baumZeichnen(); }
  _themenKlick(ev) {
    const t = ev.target;
    if (t.closest("[data-thema-aus]")) return this.a.onZustand({ thema: "" });
    if (t.closest("[data-alle-an]")) return this.a.onKlassen("");
    if (t.closest("[data-alle-aus]")) return this.a.onKlassen("keine");
    const nur = t.closest("[data-nur]"); if (nur) return this.a.onKlassen(nur.dataset.nur);   // Farbpunkt = nur diese Klasse
    const auf = t.closest("[data-auf]");
    if (auf) { const k = auf.dataset.auf; this.baumZustand = { offen: this.baumZustand.offen === k ? null : k, alle: null }; return this._baumZeichnen(); }
    const alle = t.closest("[data-alle]"); if (alle) { this.baumZustand.alle = alle.dataset.alle; return this._baumZeichnen(); }
    const s = t.closest("[data-schluessel]"); if (s) return this.a.onVergleich(s.dataset.schluessel, true);
  }

  // Kurzer Hinweis oben im Inhalt (z. B. „Höchstens fünf Eigentümer“), verschwindet nach 2 s.
  zeigeHinweis(text) {
    const el = document.createElement("div"); el.className = "hinweis warn fluechtig"; el.textContent = text;
    this.inhalt.prepend(el);
    setTimeout(() => el.remove(), 2000);
  }

  // Kopf einer aktiven Ansicht (Spec §8). `roh` ist der unveränderte URL-String, damit der Link in
  // die Werkstatt genau dieselbe Ansicht öffnet. Die Werkstatt kommt erst in 5c — darum gekennzeichnet.
  zeigeAnsicht(ansicht, roh = "", fehler = false) {
    const el = this.ansichtkopf;
    if (!el) return;
    if (!ansicht) {
      // Kaputter ?ansicht=-Parameter: sagen, dass nichts gefärbt ist, statt eine andere Ansicht zu zeigen.
      if (!fehler) { el.hidden = true; el.innerHTML = ""; return; }
      el.innerHTML = `<div class="thema ansicht"><b>Ansicht nicht lesbar – Karte ungefärbt.</b>` +
        `<button data-ansicht-aus="1">Ansicht verlassen</button></div>`;
      el.hidden = false;
      el.querySelector("[data-ansicht-aus]").addEventListener("click", () => this.a.onZustand({ ansicht: "" }));
      return;
    }
    const gruppen = ansicht.gruppen.map((g) => g.name).join(", ");
    el.innerHTML = `<div class="thema ansicht"><b>${esc(ansichtTitel(ansicht))}</b>` +
      `<p>${ansicht.bezug ? `Bezug: ${esc(ansicht.bezug)}. ` : ""}Gruppen: ${esc(gruppen) || "keine"}.` +
      (ansicht.min_n > 0 ? `<br>Einheiten mit weniger als ${ansicht.min_n} ${esc(nennerText(ansicht))} bleiben grau.` : "") + `</p>` +
      `<a href="werkstatt.html?ansicht=${encodeURIComponent(roh)}">In der Werkstatt öffnen (folgt)</a>` +
      `<button data-ansicht-aus="1">Ansicht verlassen</button></div>`;
    el.hidden = false;
    el.querySelector("[data-ansicht-aus]").addEventListener("click", () => this.a.onZustand({ ansicht: "" }));
  }

  // Feste Zeile unter den Ebenen-Pills, in jedem Zustand sichtbar (Wunsch Christos 2026-09-29): Klick wechselt das Thema
  // direkt, ein Klick auf das aktive Thema verlässt es.
  zeigeThemenliste(themen, aktiv = "") {
    const el = this.themenliste;
    if (!themen.length) { el.hidden = true; return; }
    el.innerHTML = `<span class="gruppe">Themen</span>` + themen.map((t) => `<button class="themaknopf" data-thema="${esc(t.id)}" aria-pressed="${t.id === aktiv}">${esc(t.titel)}</button>`).join("");
    el.hidden = false; this._themaAktiv = aktiv;
  }
  markiereThema(aktiv) {
    this._themaAktiv = aktiv;
    this.themenliste.querySelectorAll("[data-thema]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.thema === aktiv)));
  }

  _filterEreignisse(z) {
    this.pills.querySelectorAll("[data-ebene]").forEach((b) => b.addEventListener("click", () => {
      const e = b.dataset.ebene; const neu = z.ebene.includes(e) ? z.ebene.filter((x) => x !== e) : [...z.ebene, e];
      if (neu.length) this.a.onZustand({ ebene: ["I", "II", "III"].filter((x) => neu.includes(x)) });
    }));
    const sel = this.inhalt.querySelector('[data-filter="stadtteil"]');
    if (sel) sel.addEventListener("change", () => this.a.onZustand({ stadtteil: sel.value }));
    this.inhalt.querySelectorAll("[data-praez]").forEach((c) => c.addEventListener("change", () => {
      const praez = [...this.inhalt.querySelectorAll("[data-praez]:checked")].map((x) => x.dataset.praez);
      // Mindestens eine Präzisionsstufe muss aktiv bleiben, sonst gäbe es keine Punkte mehr zu
      // zeigen — das Abwählen der letzten wird zurückgenommen, statt den Zustand kaputtzuschreiben.
      if (praez.length) this.a.onZustand({ praez }); else c.checked = true;
    }));
    const beruf = this.inhalt.querySelector('[data-filter="beruf"]');
    if (beruf) beruf.addEventListener("change", () => this.a.onZustand({ beruf: beruf.value.trim(), vergleich: [] }));
  }

  _klick(ev) {
    const t = ev.target;
    if (t.closest("[data-zurueck]")) return this.a.onZurueck();
    if (t.closest("[data-mehr]")) return this._mehrZeilen();
    if (t.closest("[data-export]")) return this.a.onExport();
    const th = t.closest("[data-thema]"); if (th) return this.a.onZustand({ thema: th.dataset.thema });
    const weg = t.closest("[data-weg]"); if (weg) return this.a.onVergleich(weg.dataset.weg, true);
    const s = t.closest("[data-schluessel]"); if (s) return this.a.onVergleich(s.dataset.schluessel, false);
    const z = t.closest(".treffer");
    if (z) return z.dataset.eintrag ? this.a.onEintragWaehlen(z.dataset.eintrag, z.dataset.adresse) : this.a.onHausWaehlen(z.dataset.adresse);
  }
}
