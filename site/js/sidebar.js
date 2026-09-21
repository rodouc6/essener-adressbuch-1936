import { EBENEN } from "./konfig.js";
import { esc, hausHtml, trefferzeileHtml, heutigeAdresse } from "./popup.js";

const STUFEN = ["griff", "halb", "voll"];

export class Sidebar {
  constructor(el, lader, aktionen) {
    this.el = el; this.lader = lader; this.a = aktionen;
    this.inhalt = el.querySelector("#inhalt");
    this.pills = el.querySelector("#pills");
    this.vorschlaegeEl = el.querySelector("#vorschlaege");
    this.themenkopf = el.querySelector("#themenkopf");
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

  setzeVorschlaege(g) {
    if (!g || g.gesamt === 0) { this.vorschlaegeEl.hidden = true; this._vorschlagListe = []; return; }
    const liste = []; let html = "";
    for (const [k, titel] of [["personen", "Personen"], ["strassen", "Straßen"], ["firmen", "Firmen"], ["berufe", "Berufe"]]) {
      if (!g[k].length) continue;
      html += `<div class="gruppe">${titel}</div>`;
      for (const v of g[k]) {
        html += `<div class="eintrag" data-index="${liste.length}">${esc(v.text)}<small>${esc(v.untertitel)}</small></div>`;
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
    let html = this._filterHtml(z) + `<div class="kopf"><b>${n} Treffer</b> · ${ergebnis.adressIds.length} Häuser` +
      `<button class="export" data-export="1">CSV</button></div>`;
    if (ergebnis.hinweisHJ) html += `<div class="hinweis warn">Keine Treffer. Die Namen H bis J fehlen in der Vorlage (Seiten 186–258 des Teils I). Straßen und Firmen sind nicht betroffen.</div>`;
    const zeilen = ergebnis.personen
      ? ergebnis.personen.map((p) => ({ adressId: p.adressId, eintragId: p.eintragId, titel: p.text, untertitel: p.untertitel, stufe: (eig.get(p.adressId) || {}).stufe || "unbekannt" }))
      : ergebnis.adressIds.map((id) => { const e = eig.get(id) || {}; return { adressId: id, titel: e.historisch ? heutigeAdresse(e) : id, untertitel: `${ergebnis.zaehler.get(id)} Einträge${e.historisch ? " · " + e.historisch : ""}`, stufe: e.stufe || "unbekannt" }; });
    this._alleZeilen = zeilen; this._gezeigt = 0;
    html += `<div class="liste" id="liste"></div><button class="mehr" data-mehr="1" hidden>weitere 50</button>`;
    this.inhalt.innerHTML = html;
    this._filterEreignisse(z);
    this._mehrZeilen();
    if (ergebnis.adressIds.length >= 500) this._verteilung(ergebnis, eig);
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

  zeigeHaus(eig, eintraege, hervorgehoben) {
    this.inhalt.innerHTML = `<button class="zurueck" data-zurueck="1">‹ zurück</button>` + hausHtml(eig, eintraege);
    if (hervorgehoben) {
      const e = this.inhalt.querySelector(`#e-${CSS.escape(hervorgehoben)}`);
      if (e) { e.classList.add("hervor"); e.scrollIntoView({ block: "center" }); }
    }
    this.setzeStufe("voll");
  }

  zeigeThema(thema) {
    if (!thema) { this.themenkopf.hidden = true; this.themenkopf.innerHTML = ""; return; }
    this.themenkopf.innerHTML = `<div class="thema"><b>${esc(thema.titel)}</b><p>${esc(thema.text)}</p><small>${esc(thema.grundlage)}</small>` +
      `<button data-thema-aus="1">Thema verlassen</button></div>`;
    this.themenkopf.hidden = false;
    this.themenkopf.querySelector("[data-thema-aus]").addEventListener("click", () => this.a.onZustand({ thema: "" }));
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
    if (beruf) beruf.addEventListener("change", () => this.a.onZustand({ beruf: beruf.value.trim() }));
  }

  _klick(ev) {
    const t = ev.target;
    if (t.closest("[data-zurueck]")) return this.a.onZurueck();
    if (t.closest("[data-mehr]")) return this._mehrZeilen();
    if (t.closest("[data-export]")) return this.a.onExport();
    const th = t.closest("[data-thema]"); if (th) return this.a.onZustand({ thema: th.dataset.thema });
    const z = t.closest(".treffer");
    if (z) return z.dataset.eintrag ? this.a.onEintragWaehlen(z.dataset.eintrag, z.dataset.adresse) : this.a.onHausWaehlen(z.dataset.adresse);
  }
}
