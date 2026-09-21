import { Lader } from "./daten.js";
import { vorschlaege, hinweisHJ } from "./suche.js";
import { themenListe } from "./themen.js";
import { esc } from "./popup.js";
import { schreibeZustand, STANDARD } from "./zustand.js";

const lader = new Lader();
const suche = document.getElementById("suche");
const box = document.getElementById("vorschlaege");
let liste = [];

function zielUrl(v) {
  let z;
  if (v.art === "person" || v.art === "firma") z = { ...STANDARD, q: v.text, id: v.adressId + (v.eintragId ? "." + v.eintragId : "") };
  else if (v.art === "beruf") z = { ...STANDARD, beruf: v.beruf };
  // v.art === "strasse": v.text trägt den Ort in Klammern ("Name (Ort)") — für den q-Parameter
  // den reinen Namen verwenden, sonst findet ihn app.js' Straßenindex-Abgleich nicht exakt
  // (Task 14 Amendment 1).
  else z = { ...STANDARD, q: v.name };
  return "karte.html?" + schreibeZustand(z);
}

function zeige(g) {
  liste = [];
  if (!g || g.gesamt === 0) { box.hidden = true; return; }
  let html = "";
  for (const [k, titel] of [["personen", "Personen"], ["strassen", "Straßen"], ["firmen", "Firmen"], ["berufe", "Berufe"]]) {
    if (!g[k].length) continue;
    html += `<div class="gruppe">${titel}</div>`;
    for (const v of g[k]) { html += `<a class="eintrag" href="${zielUrl(v)}">${esc(v.text)}<small>${esc(v.untertitel)}</small></a>`; liste.push(v); }
  }
  box.innerHTML = html; box.hidden = false;
}

let timer = null;
suche.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const g = await vorschlaege(suche.value, lader);
    zeige(g);
    document.getElementById("hinweis-hj").hidden = !(g.personen.length === 0 && hinweisHJ(suche.value) && suche.value.length >= 2);
  }, 120);
});
suche.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && suche.value.trim()) location.href = "karte.html?" + schreibeZustand({ ...STANDARD, q: suche.value.trim() });
});
document.addEventListener("click", (ev) => { if (!ev.target.closest(".suchfeld")) box.hidden = true; });

const kz = await lader.kennzahlen();
if (kz) {
  const t = kz.eintraege_je_teil;
  const verortet = (kz.stufen.haus + kz.stufen.strasse + kz.stufen.stadtplan).toFixed(0);
  document.getElementById("zahlen").innerHTML = [[t.I, "Einwohner"], [t.II, "Häuser"], [t.III, "Firmen"], [verortet + " %", "verortet"]]
    .map(([n, l]) => `<div><b>${typeof n === "number" ? n.toLocaleString("de-DE") : n}</b><small>${l}</small></div>`).join("");
}
const st = await lader.stadtteile();
if (st) {
  const k = document.getElementById("kachel-stadtteil");
  k.href = "#"; k.addEventListener("click", (ev) => {
    ev.preventDefault();
    k.outerHTML = `<div class="kachel"><b>Stadtteil</b><select id="st-wahl"><option value="">wählen …</option>${st.map((s) => `<option value="${esc(s.name)}">${esc(s.name)} (${s.zeilen})</option>`).join("")}</select></div>`;
    document.getElementById("st-wahl").addEventListener("change", (e) => {
      if (!e.target.value) return;
      const s = st.find((x) => x.name === e.target.value);
      location.href = "karte.html?" + schreibeZustand({ ...STANDARD, stadtteil: e.target.value, z: 14, c: [s.lon, s.lat] });
    });
  });
}
const themen = await themenListe(lader);
if (themen.length) {
  const k = document.getElementById("kachel-thema");
  k.href = "karte.html?thema=" + encodeURIComponent(themen[0].id);
  k.querySelector("b").textContent = themen[0].titel; k.querySelector("small").textContent = "Thema";
  k.hidden = false;
}
