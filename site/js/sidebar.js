import { EBENEN } from "./konfig.js";
import { esc, hausHtml, trefferzeileHtml, heutigeAdresse } from "./popup.js";
import { ansichtTitel } from "./ansicht_farben.js";
import { nennerText } from "./formen/skalen.js";
import { vergleichsleisteHtml, gruppenZuordnung } from "./vergleich.js";

const STUFEN = ["griff", "halb", "voll"];

export class Sidebar {
  constructor(el, lader, aktionen) {
    this.el = el; this.lader = lader; this.a = aktionen;
    this.inhalt = el.querySelector("#inhalt");
    this.pills = el.querySelector("#pills");
    this.vorschlaegeEl = el.querySelector("#vorschlaege");
    this.themenkopf = el.querySelector("#themenkopf");
    this.ansichtkopf = el.querySelector("#ansichtkopf");
    this.suche = el.querySelector("#suche");
    this.stadtteile = []; this.berufe = [];
    el.querySelector("#griff").addEventListener("click", () => this.naechsteStufe());
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
    for (const [k, titel] of [["personen", "Personen"], ["strassen", "Straßen"], ["firmen", "Firmen"], ["berufe", "Berufe"], ["eigentuemer", "Eigentümer"]]) {
      if (!g[k].length) continue;
      html += `<div class="gruppe">${titel}</div>`;
      for (const v of g[k]) {
        const zusatz = plus && k === "eigentuemer" ? `<span class="plus" title="zum Vergleich hinzufügen">+</span>` : "";
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
      `<div class="hinweis">Tippe einen Namen, eine Straße, eine Firma oder einen Beruf. Die Namen H bis J fehlen in der Vorlage.</div>` +
      `<div class="themenliste" id="themenliste"></div>`;
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
    if (ergebnis.hinweisHJ) html += `<div class="hinweis warn">Keine Treffer. Die Namen H bis J fehlen in der Vorlage (Seiten 186–258 des Teils I). Straßen und Firmen sind nicht betroffen.</div>`;
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
  zeigeHaus(eig, eintraege, hervorgehoben, faksimile = null, ebenen = []) {
    const hv = hervorgehoben ? eintraege.find((e) => e.id === hervorgehoben) : null;
    const reiter = hv ? hv.teil : ebenen.length === 1 ? ebenen[0] : "alle";
    this._haus = { eig, eintraege, faksimile };
    this._hausZeichnen(reiter, hervorgehoben);
    this.setzeStufe("voll");
  }

  _hausZeichnen(reiter, hervorgehoben = null) {
    const { eig, eintraege, faksimile } = this._haus;
    this.inhalt.innerHTML = `<button class="zurueck" data-zurueck="1">‹ zurück</button>` + hausHtml(eig, eintraege, faksimile, reiter);
    this.inhalt.querySelectorAll("[data-teil]").forEach((b) => b.addEventListener("click", () => { this._hausZeichnen(b.dataset.teil); this.inhalt.scrollTop = 0; }));
    if (hervorgehoben) {
      const e = this.inhalt.querySelector(`#e-${CSS.escape(hervorgehoben)}`);
      if (e) { e.classList.add("hervor"); e.scrollIntoView({ block: "center" }); }
    }
  }

  zeigeThema(thema, groesste = null, gewaehlt = [], farben = []) {
    if (!thema) { this.themenkopf.hidden = true; this.themenkopf.innerHTML = ""; return; }
    this.themenkopf.innerHTML = `<div class="thema"><b>${esc(thema.titel)}</b><p>${esc(thema.text)}</p><small>${esc(thema.grundlage)}</small>` +
      `<button data-thema-aus="1">Thema verlassen</button></div>`;
    this.themenkopf.hidden = false;
    this.themenkopf.querySelector("[data-thema-aus]").addEventListener("click", () => this.a.onZustand({ thema: "" }));
    if (groesste && groesste.length) {
      this.themenkopf.insertAdjacentHTML("beforeend", `<div class="gruppe">Größte Eigentümer</div><div class="eigentuemerliste">` +
        groesste.slice(0, 30).map((z) => `<button class="themaknopf" data-eigentuemer="${esc(z[1])}" aria-pressed="false">${esc(z[1])} <small>${z[2]}</small></button>`).join("") + `</div>`);
      // Klick schaltet um: gewählt → entfernen, sonst anhängen (app.js prüft die Höchstzahl)
      this.themenkopf.querySelectorAll("[data-eigentuemer]").forEach((b) => b.addEventListener("click", () => this.a.onEigentuemer(b.dataset.eigentuemer, true)));
      this.markiereEigentuemer(gewaehlt, farben);
    }
  }

  // Gewählte Eigentümer-Knöpfe in ihrer Gruppenfarbe füllen (Spec 2026-09-29 §6).
  markiereEigentuemer(namen, farben) {
    this.themenkopf.querySelectorAll("[data-eigentuemer]").forEach((b) => {
      const i = namen.indexOf(b.dataset.eigentuemer);
      b.setAttribute("aria-pressed", String(i >= 0));
      b.style.background = i >= 0 ? farben[i] : ""; b.style.color = i >= 0 ? "#fff" : ""; b.style.borderColor = i >= 0 ? farben[i] : "";
    });
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
      `<p>${ansicht.bezug ? `Bezug: ${esc(ansicht.bezug)}. ` : ""}Gruppen: ${esc(gruppen) || "keine"}.<br>` +
      `Einheiten unter ${ansicht.min_n} ${esc(nennerText(ansicht))} bleiben grau.</p>` +
      `<a href="werkstatt.html?ansicht=${encodeURIComponent(roh)}">In der Werkstatt öffnen (ab 5c)</a>` +
      `<button data-ansicht-aus="1">Ansicht verlassen</button></div>`;
    el.hidden = false;
    el.querySelector("[data-ansicht-aus]").addEventListener("click", () => this.a.onZustand({ ansicht: "" }));
  }

  zeigeThemenliste(themen) {
    const el = this.inhalt.querySelector("#themenliste");
    if (!el || !themen.length) return;
    el.innerHTML = `<div class="gruppe">Themen</div>` + themen.map((t) => `<button class="themaknopf" data-thema="${esc(t.id)}">${esc(t.titel)}</button>`).join("");
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
    if (beruf) beruf.addEventListener("change", () => this.a.onZustand({ beruf: beruf.value.trim(), eigentuemer: "", ohdab: "" }));
  }

  _klick(ev) {
    const t = ev.target;
    if (t.closest("[data-zurueck]")) return this.a.onZurueck();
    if (t.closest("[data-mehr]")) return this._mehrZeilen();
    if (t.closest("[data-export]")) return this.a.onExport();
    const th = t.closest("[data-thema]"); if (th) return this.a.onZustand({ thema: th.dataset.thema });
    const weg = t.closest("[data-eig-weg]"); if (weg) return this.a.onEigentuemer(weg.dataset.eigWeg, true);
    const eig = t.closest("[data-eigentuemer]"); if (eig) return this.a.onEigentuemer(eig.dataset.eigentuemer, false);
    const z = t.closest(".treffer");
    if (z) return z.dataset.eintrag ? this.a.onEintragWaehlen(z.dataset.eintrag, z.dataset.adresse) : this.a.onHausWaehlen(z.dataset.adresse);
  }
}
