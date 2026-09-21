import { falte, praefix2 } from "./schluessel.js";

const MAX = { personen: 5, strassen: 3, firmen: 3, berufe: 3 };

export function hinweisHJ(q) {
  const k = falte(q);
  return /^[hij]/.test(k);
}

function person(z) {
  return { art: "person", text: `${z[1]}, ${z[2]}`.replace(/, $/, ""), untertitel: [z[3], z[4]].filter(Boolean).join(" · "),
           eintragId: z[5], adressId: z[6], teil: z[7], q: z[1] };
}

function strasse(s) {
  const art = s.art === "1936" ? "Name 1936" : "heutiger Name";
  return { art: "strasse", text: `${s.name} (${s.ort})`, untertitel: `${art} · ${s.zeilen} Einträge`,
           name: s.name, artName: s.art, ort: s.ort, schluessel: s.schluessel };
}

export async function vorschlaege(q, lader) {
  const k = falte(q);
  const leer = { personen: [], strassen: [], firmen: [], berufe: [], gesamt: 0 };
  if (k.length < 2) return leer;
  const [namen, firmen, strassen, berufe] = await Promise.all([
    lader.namen(praefix2(k)), lader.firmen(praefix2(k)), lader.strassen(), lader.berufe()]);
  const alleP = (namen || []).filter((z) => z[0].startsWith(k)).map(person);
  const alleS = (strassen || []).filter((s) => s.schluessel.startsWith(k)).map(strasse);
  const alleF = (firmen || []).filter((z) => z[0].startsWith(k))
    .map((z) => ({ art: "firma", text: z[1], untertitel: z[2], eintragId: z[3], adressId: z[4] }));
  const alleB = (berufe || []).filter((z) => z[0].startsWith(k))
    .map((z) => ({ art: "beruf", text: z[1], untertitel: `${z[2]} Einträge`, beruf: z[1] }));
  return {
    personen: alleP.slice(0, MAX.personen), strassen: alleS.slice(0, MAX.strassen),
    firmen: alleF.slice(0, MAX.firmen), berufe: alleB.slice(0, MAX.berufe),
    gesamt: alleP.length + alleS.length + alleF.length + alleB.length,
  };
}

// Auswahl → Treffermenge. adressIds sind die Häuser, die die Karte hervorhebt; zaehler zählt
// Einträge je Haus; personen ist nur bei Namenssuche gefüllt (Liste zeigt dann Personen).
export async function treffer(auswahl, lader) {
  const zaehler = new Map();
  let personen = null;
  let hinweis = false;
  if (auswahl.art === "strasse") {
    const scherbe = await lader.strassenScherbe(praefix2(auswahl.name));
    const key = `${auswahl.name}|${auswahl.artName}|${auswahl.ort}`;
    const ids = (scherbe && scherbe[key]) || [];
    for (const a of ids) zaehler.set(a, (zaehler.get(a) || 0) + 1);
  } else if (auswahl.art === "beruf") {
    const s = await lader.berufeScherbe(praefix2(auswahl.beruf));
    for (const [a, n] of (s && s[auswahl.beruf]) || []) zaehler.set(a, n);
  } else if (auswahl.art === "person") {
    const k = falte(auswahl.q);
    const namen = (await lader.namen(praefix2(k))) || [];
    personen = namen.filter((z) => z[0].startsWith(k)).map(person);
    for (const p of personen) zaehler.set(p.adressId, (zaehler.get(p.adressId) || 0) + 1);
    hinweis = personen.length === 0 && hinweisHJ(auswahl.q);
  } else if (auswahl.art === "firma") {
    zaehler.set(auswahl.adressId, 1);
  }
  return { adressIds: [...zaehler.keys()], zaehler, personen, hinweisHJ: hinweis };
}
