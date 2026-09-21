"""Betriebsstatus 1936 je Zeche aus dem Historischen Portal Essen (Huske-Auszüge) ableiten.

    python3 werkzeuge/zechen_portal.py [--neu]

Das Portal (Stadt Essen / Historischer Verein) veröffentlicht je Anlage wörtliche Auszüge aus Joachim Huske,
„Die Steinkohlenzechen im Ruhrrevier“ (2006): eine Jahreschronologie mit Förderzahlen und Belegschaft.
Das Werkzeug liest den A–Z-Index, sucht zu jeder Zeile von kuratierung/zechen.csv die passende Seite (Name,
ersatzweise Stadtteil), zieht die Chronologie und leitet daraus `huske_status` ab (aktiv | stillgelegt |
unklar). Ergebnis: kuratierung/zechen_huske.csv mit Belegzitat (Chronik 1930–1940) und URL; der Abgleich
(werkzeuge/zechen_abgleich.py) nimmt diesen Status als entscheidend.

Grenzen: Bei langen Einträgen ist der Portaltext abgeschnitten (endet z. B. 1898) → „unklar“, kein Ratewert.
Seiten werden in build/zechen_portal/ zwischengespeichert; --neu lädt neu. Rechte: Zitierquelle, keine
Massenübernahme (Texte © Deutsches Bergbau-Museum); siehe docs/zechen_quellen.md.
"""
from __future__ import annotations

import html
import pathlib
import re
import sys
import time

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv

BASIS = "https://historischesportal.essen.de/historischesportal_orte/bergbau_1/"
INDEX_URL = BASIS + "bergbau_abisz.de.html"
UA = {"User-Agent": "essener-adressbuch-1936 (Zechen-Abgleich, Einzelabruf mit Pause)"}
FELDER = ["name", "stadtteil", "fs_id", "url", "portal_name", "portal_stadtteil", "huske_status", "grund",
          "letztes_jahr", "chronik_1930_1940", "atlas_auszug"]
ABGESCHNITTEN_AB = 3500  # Zeichen; das Portal kappt lange Huske-Texte (Graf Beust endet nach 3.758 Zeichen im Jahr 1898)

_ENDE = re.compile(r"Stilllegung|Fördereinstellung|Betriebseinstellung|Erlöschen|in Fristen|außer Betrieb|liegt .*still"
                   r"|\bzu [A-ZÄÖÜ]|Übernahme durch|Übergang (auf|an)|Verkauf an|Konsolidation (zu|mit)"
                   r"|Einstellung|aufgegeben", re.I)
_WIEDER = re.compile(r"Wiederinbetriebnahme|erneut in Betrieb|Neugründung|wieder in Betrieb", re.I)
_SCHACHT = re.compile(r"\bSch\.|\bSchacht\b|Wetterschacht|Luftschacht|Brikettfabr|Kokerei|Ziegelei|Wäsche|Kraftwerk|Seilbahn"
                      r"|Fördereinstellung (auf|in|im)\b", re.I)
_BETRIEB = re.compile(r"\d+ t\b|\bBetrieb\b|Förderbeginn|Abbaubeginn|Abbau\b|Inbetriebnahme|Wiederinbetriebnahme|Betriebsaufnahme"
                      r"|Neugründung|wieder in Betrieb|erneut in Betrieb|Förderung|Teufbeginn|Teufen|Ansetzen|Durchschlag"
                      r"|Anpachtung|Aufschluss|Weiterteufen|Tieferteufen|Sümpfen", re.I)
_UNTER_ANDEREM_NAMEN = re.compile(r"unter dem Namen\s*|als Teil (von|der)\s*", re.I)


def index_parsen(html_text: str) -> list[dict]:
    """Einträge des A–Z-Index: fs_id, name, art (Schacht/Kleinzeche/Stollen/…), stadtteil."""
    eintraege = []
    for m in re.finditer(r'bergbau_detailseite_(\d+)\.de\.html".*?<h4>(.*?)</h4>\s*<div class="tileDescription">(.*?)</div>',
                         html_text, re.S):
        besch = html.unescape(m.group(3))
        art = re.sub(r"<.*", "", besch).strip()
        st = re.search(r"Stadtteil:\s*(.*)$", re.sub(r"<[^>]+>", "", besch).strip())
        eintraege.append(dict(fs_id=m.group(1), name=html.unescape(m.group(2)).strip(), art=art,
                              stadtteil=st.group(1).strip() if st else ""))
    return eintraege


def _norm(name: str) -> str:
    """Vergleichsform: Umlaute, Bindestriche, „Vereinigte/Ver.“ (im Portal auch nachgestellt, teils „Vereingte“),
    „&“/„und“, Klammerzusätze und angehängte Schachtnummern („Zollverein 1/2/3“) fallen weg."""
    s = name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"\([^)]*\)", " ", s).replace("-", " ").replace("’", "'")
    s = re.sub(r"\b(vereinigte|vereingte|ver\.|und|&|u\.)(\s|$)", " ", s)
    s = re.sub(r"[^a-z0-9' ]", " ", s)
    s = re.sub(r"(\s+(schacht\s+)?\d+(/\d+)*)+$", "", s.strip())  # „Heinrich Schacht 3“, „Zollverein 1/2“
    return re.sub(r"\s+", " ", s).strip()


def _norm_stadtteil(s: str) -> str:
    return _norm(s.replace("Essen-", ""))


def kandidaten(name: str, stadtteil: str, index: list[dict]) -> list[dict]:
    """Indexeinträge mit diesem Zechennamen (vor einem Komma, z. B. „Carolus-Magnus, Schacht 1“), passender
    Stadtteil und kurze Namen zuerst. Welche Seite gilt, entscheidet danach der Seitenkopf (waehle_seite)."""
    ziel = _norm(name)
    treffer = [e for e in index if _norm(e["name"].split(",")[0]) == ziel]
    st = _norm_stadtteil(stadtteil)
    def passt(e: dict) -> bool:
        es = _norm_stadtteil(e["stadtteil"])
        return bool(st and es and (st in es or es in st))
    return sorted(treffer, key=lambda e: (e["art"] == "Schacht", not passt(e), len(e["name"])))


def _absaetze(teil: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.findall(r"<p>(.*?)</p>", teil, re.S)]


def seite_parsen(html_text: str) -> dict:
    """Kopf (Zechenname, Stadtteil) sowie Huske-Absätze und Atlas-Text einer Detailseite."""
    body = html_text[html_text.find('<div class="jquery_tabs">'):html_text.find("<h4>Literaturquellen")]
    teile = re.split(r"<h2>(.*?)</h2>", body)
    huske, atlas = [], ""
    for i in range(1, len(teile), 2):
        titel, inhalt = html.unescape(teile[i]), teile[i + 1]
        if "Steinkohlenzechen" in titel:
            huske = _absaetze(inhalt)
        elif "Atlas" in titel:
            atlas = " ".join(a for a in _absaetze(inhalt)[1:])
    kopf = re.match(r'^"?(.*?)\s*\(Essen-(.*?)\)', huske[0]) if huske else None
    rest = [a for a in huske[1:] if not a.startswith("(")]  # Klammerzeile mit Namensvarianten überspringen
    return dict(portal_name=kopf.group(1).strip() if kopf else (huske[0] if huske else ""),
                portal_stadtteil=kopf.group(2).strip() if kopf else "", huske=rest, atlas=atlas)


def chronik_parsen(absaetze: list[str]) -> list[tuple[int, str]]:
    """(Jahr, Text) je Eintrag; Absätze ohne Jahresanfang werden dem vorigen Eintrag angehängt."""
    chronik: list[tuple[int, str]] = []
    for a in absaetze:
        m = re.match(r"^(\d{4})(?:/\d{2})?\s+(.*)$", a, re.S)
        if m:
            chronik.append((int(m.group(1)), m.group(2).strip()))
        elif chronik:
            j, t = chronik[-1]
            chronik[-1] = (j, f"{t} {a}")
    return chronik


def _eintrag_art(text: str, eigenname: str = "") -> str | None:
    """betrieb | ende | fremd | None für einen Chronologie-Eintrag. Klammerbemerkungen („(1951 Wiederinbetriebnahme,
    s. dort)“) zählen nicht; Ende-Ereignisse einzelner Schächte oder Nebenanlagen („Sch. 1: Fördereinstellung“,
    „Stilllegung Brikettfabrik“) sind kein Zechenende; innerhalb eines Eintrags gilt das zuletzt genannte Ereignis
    („Stilllegung, … Wiederinbetriebnahme“), erfolglose Versuche zählen nicht. „unter dem Namen X“ ist fremd,
    wenn X nicht der eigene Name ist."""
    text = re.sub(r"\([^)]*\)", "", text)
    m = _UNTER_ANDEREM_NAMEN.search(text)
    if m:
        genannt = re.split(r"[,;]", text[m.end():])[0]
        if not (eigenname and _norm(genannt).startswith(_norm(eigenname))):
            return "fremd"
    art = None
    for k in re.split(r"[,;]\s*", text):
        if "erfolglos" in k:
            continue
        if _WIEDER.search(k):
            art = "betrieb"
        elif _ENDE.search(k) and not _SCHACHT.search(k):
            art = "ende"
        elif _BETRIEB.search(k) and art != "ende":
            art = "betrieb"
    return art


def huske_status(chronik: list[tuple[int, str]], laenge: int, eigenname: str = "") -> tuple[str, str]:
    """Zustand Ende 1936 aus der Chronologie: letzter Eintrag ≤ 1936 mit Betriebs- bzw. Endemerkmal
    entscheidet; abgeschnittene Texte (lang, enden vor 1937 ohne Ende) und Abbau „unter dem Namen“ einer
    anderen Zeche bleiben unklar."""
    if not chronik:
        return "unklar", "keine Chronologie im Portal"
    if chronik[0][0] > 1936:
        return "stillgelegt", f"erst {chronik[0][0]}: {chronik[0][1][:60]}"
    letztes = chronik[-1][0]
    if letztes < 1937 and laenge >= ABGESCHNITTEN_AB:
        return "unklar", f"Portaltext abgeschnitten (endet {letztes})"
    bis_1936 = [(j, t) for j, t in chronik if j <= 1936]
    zustand, beleg = None, ""
    for j, t in bis_1936:
        art = _eintrag_art(t, eigenname)
        if art:
            zustand, beleg = art, f"{j} {t[:80]}"
    if zustand == "ende":
        jahr_ende = int(beleg[:4])
        danach = [f"{j} {t[:40]}" for j, t in chronik if jahr_ende < j <= 1940 and re.search(r"\d[\d.]* t\b", t)]
        if danach:
            return "unklar", f"Ende laut {beleg[:60]}, aber Förderzahlen danach: {danach[0]}"
        return "stillgelegt", beleg
    if zustand == "fremd":
        return "unklar", f"Abbau unter anderem Namen: {beleg}"
    if zustand == "betrieb":
        if letztes < 1937:
            return "unklar", f"kein Eintrag nach {letztes}, Ende unbekannt"
        return "aktiv", beleg
    return "unklar", "kein Betriebsbeleg bis 1936"


def waehle_seite(name: str, seiten: list[tuple[dict, dict]], stadtteil: str = "") -> list[tuple[dict, dict]]:
    """Aus (Indexeintrag, geparste Seite)-Paaren die, deren Seitenkopf den gesuchten Zechennamen trägt; gleiche
    Köpfe (mehrere Schächte derselben Zeche) zählen einmal. Bleiben mehrere Zechen gleichen Namens, entscheidet
    ein gemeinsames Stadtteil-Wort (Überruhr-Burgaltendorf ~ Burgaltendorf). Ohne Kopftreffer bleiben alle Paare."""
    ziel = _norm(name)
    passend = [(k, s) for k, s in seiten if _norm(s["portal_name"]) == ziel] or seiten
    gesehen, eindeutig = set(), []
    for k, s in passend:
        kopf = (_norm(s["portal_name"]), _norm_stadtteil(s["portal_stadtteil"]))
        if kopf not in gesehen:
            gesehen.add(kopf)
            eindeutig.append((k, s))
    if len(eindeutig) > 1 and stadtteil:
        woerter = set(_norm_stadtteil(stadtteil).split())
        nah = [(k, s) for k, s in eindeutig if woerter & set(_norm_stadtteil(s["portal_stadtteil"]).split())]
        if len(nah) == 1:
            return nah
    return eindeutig


def _hole(url: str, cache: pathlib.Path, neu: bool) -> str:
    if cache.exists() and not neu:
        return cache.read_text(encoding="utf-8")
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    time.sleep(0.7)
    text = r.content.decode("utf-8")  # das Portal liefert UTF-8 ohne passende Kopfzeile; r.text riete falsch
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return text


def _atlas_auszug(atlas: str) -> str:
    saetze = [s.strip() for s in re.split(r"(?<=\.)\s+", atlas) if re.search(r"\b19[2-4]\d\b", s)]
    return " ".join(saetze)[:400]


def main() -> None:
    neu = "--neu" in sys.argv
    wurzel = projektwurzel()
    cache_dir = wurzel / "build" / "zechen_portal"
    index = index_parsen(_hole(INDEX_URL, cache_dir / "abisz.html", neu))
    zeilen = []
    for z in lies_csv(wurzel / "kuratierung" / "zechen.csv"):
        kand = kandidaten(z["name"], z.get("stadtteil", ""), index)
        zeile = dict(name=z["name"], stadtteil=z.get("stadtteil", ""), fs_id="", url="", portal_name="",
                     portal_stadtteil="", huske_status="unklar", grund="", letztes_jahr="", chronik_1930_1940="", atlas_auszug="")
        seiten = [(k, seite_parsen(_hole(f"{BASIS}bergbau_detailseite_{k['fs_id']}.de.html", cache_dir / f"{k['fs_id']}.html", neu)))
                  for k in kand[:10]]
        wahl = waehle_seite(z["name"], [(k, s) for k, s in seiten if s["huske"]], z.get("stadtteil", ""))
        if not kand:
            zeile["grund"] = "im Portal-Index nicht gefunden"
        elif not wahl:
            zeile["grund"] = "keine Chronologie im Portal (" + "; ".join(k["fs_id"] for k in kand[:8]) + ")"
        elif len(wahl) > 1:
            zeile["grund"] = "mehrdeutig: " + "; ".join(f'{s["portal_name"]} ({s["portal_stadtteil"]}, {k["fs_id"]})' for k, s in wahl)
        else:
            k, s = wahl[0]
            url = f"{BASIS}bergbau_detailseite_{k['fs_id']}.de.html"
            chronik = chronik_parsen(s["huske"])
            status, grund = huske_status(chronik, sum(len(a) for a in s["huske"]), s["portal_name"])
            zeile.update(fs_id=k["fs_id"], url=url, portal_name=s["portal_name"], portal_stadtteil=s["portal_stadtteil"],
                         huske_status=status, grund=grund, letztes_jahr=chronik[-1][0] if chronik else "",
                         chronik_1930_1940=" | ".join(f"{j} {t}" for j, t in chronik if 1930 <= j <= 1940),
                         atlas_auszug=_atlas_auszug(s["atlas"]))
            print(f'{z["name"]:35} {status:12} {grund[:70]}')
        zeilen.append(zeile)
    schreib_csv(wurzel / "kuratierung" / "zechen_huske.csv", zeilen, FELDER)
    zaehl = {s: sum(1 for z in zeilen if z["huske_status"] == s) for s in ("aktiv", "stillgelegt", "unklar")}
    print(f"{len(zeilen)} Zechen: {zaehl}")


if __name__ == "__main__":
    main()
