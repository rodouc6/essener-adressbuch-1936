"""Betriebsstatus 1936 der Zechen aus drei Quellen ableiten (Precision first).

    python3 werkzeuge/zechen_abgleich.py [--neu]

Quellen: (1) die Betriebsjahre der Wikipedia-Liste (betrieb_von/betrieb_bis in kuratierung/zechen.csv),
(2) die Infobox des jeweiligen Wikipedia-Artikels (BETRIEBSJAHRE_VON/BIS, zwischengespeichert in
kuratierung/zechen_artikel.csv; --neu lädt neu), (3) die Beschriftungen des Stadtplans Essen 1935
(kuratierung/stadtplan_1935_zechen.csv). Die Liste allein ist unzuverlässig (Beispiel Fridolin:
Liste „1836–1960“, Artikel „stillgelegt 1899“, 1960 ist das Jahr der Straßenbenennung).

Ergebnis: kuratierung/zechen.csv erhält die Spalten artikel_von, artikel_bis, plan_1935, status_1936
(aktiv | stillgelegt | unklar), status_geprueft (ja | nein) und hinweis; kuratierung/zechen_pruefung.csv
listet alle „unklar“ mit den drei Quellenangaben nebeneinander für die Handprüfung (Zechen mit
Koordinaten zuerst). Zeilen mit status_geprueft=ja werden nicht mehr überschrieben: Dort trägt die
Handprüfung status_1936 und hinweis (Beleg) ein.
"""
from __future__ import annotations

import math
import pathlib
import re
import sys
import time
import urllib.parse

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv

API = "https://de.wikipedia.org/w/api.php"
FELDER = ["name", "stadtteil", "lat", "lon", "betrieb_von", "betrieb_bis", "quelle", "bearbeiter", "datum",
          "artikel_von", "artikel_bis", "plan_1935", "status_1936", "status_geprueft", "hinweis"]
PRUEF_FELDER = ["name", "stadtteil", "lat", "lon", "liste", "artikel", "plan_1935", "hinweis", "quelle"]
ARTIKEL_FELDER = ["quelle", "artikel_von", "artikel_bis"]
PLAN_RADIUS_M = 1500
_JAHR = re.compile(r"\d{4}")


def infobox_jahre(wikitext: str) -> tuple[str, str]:
    """(von, bis) als vierstellige Jahre aus BETRIEBSJAHRE_VON/BIS der Infobox Bergwerk, sonst ''."""
    m = re.search(r"\{\{Infobox Bergwerk(.*?)\n\}\}", wikitext, re.S)
    if not m:
        return "", ""
    def feld(name: str) -> str:
        f = re.search(r"\|\s*" + name + r"\s*=\s*([^\n|]*)", m.group(1))
        j = _JAHR.search(f.group(1)) if f else None
        return j.group(0) if j else ""
    return feld("BETRIEBSJAHRE_VON"), feld("BETRIEBSJAHRE_BIS")


def _norm(name: str) -> str:
    """Namensform für den Vergleich Tabelle ↔ Planbeschriftung (Abkürzungen, C/K, Umlaute)."""
    s = name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"\b(zeche|z\.|ehem\.|vereinigte|ver\.|schacht|sch\.)\s*", "", s)
    s = s.replace("karl", "carl").replace("catharin", "katharin").replace("herkules", "hercules")
    s = s.replace("viktoria", "victoria").replace(" u. ", " & ").replace(" und ", " & ")
    return re.sub(r"[^a-z0-9& ]", "", s).strip()


def _passt(zeche: str, plan: str) -> bool:
    a, b = _norm(zeche), _norm(plan)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    # abgekürzte Beschriftung („Math. Stinnes“, „Christ. Levin“): jedes Planwort ist Präfix eines Namensworts
    wa, wb = a.split(), b.split()
    return len(wb) == len(wa) and all(x.startswith(y.rstrip(".")) for x, y in zip(wa, wb))


def _abstand_m(lat1: str, lon1: str, lat2: str, lon2: str) -> float:
    dy = (float(lat1) - float(lat2)) * 111_000
    dx = (float(lon1) - float(lon2)) * 111_000 * math.cos(math.radians(51.45))
    return math.hypot(dx, dy)


def plan_treffer(zeche: dict, plan: list[dict]) -> dict | None:
    """Nächste Planbeschriftung (zeche/schacht) mit passendem Namen im Umkreis, sonst None."""
    if not zeche.get("lat") or not zeche.get("lon"):
        return None
    kand = [(_abstand_m(zeche["lat"], zeche["lon"], p["lat"], p["lon"]), p) for p in plan
            if p.get("art") in ("zeche", "schacht") and _passt(zeche["name"], p["text"])]
    kand = [(d, p) for d, p in kand if d <= PLAN_RADIUS_M]
    return min(kand, key=lambda x: x[0])[1] if kand else None


def _aktiv(von: str, bis: str) -> bool | None:
    """Betrieb 1936? Ein Ende vor 1936 oder ein Beginn nach 1936 genügt für „nein“; für „ja“ braucht es
    beide Jahre; sonst None (nicht entscheidbar)."""
    if bis and int(bis) < 1936 or von and int(von) > 1936:
        return False
    if not von or not bis:
        return None
    return True


def status_ableiten(liste_von: str, liste_bis: str, art_von: str, art_bis: str, plan_text: str) -> tuple[str, str]:
    """(status_1936, hinweis). „aktiv“/„stillgelegt“ nur, wenn Liste und Artikel dasselbe sagen und der Plan
    nicht widerspricht; alles andere „unklar“ (Handprüfung)."""
    la, aa = _aktiv(liste_von, liste_bis), _aktiv(art_von, art_bis)
    ehem = "ehem" in plan_text.lower()
    if la is None or aa is None:
        fehlt = "Liste" if la is None else "Artikel"
        return "unklar", f"Betriebsjahre in Wikipedia-{fehlt} unvollständig"
    if la != aa:
        return "unklar", (f"Widerspruch: Liste {liste_von}–{liste_bis}, Artikel {art_von}–{art_bis}"
                          + (f", Plan 1935: {plan_text}" if plan_text else ", im Plan 1935 nicht beschriftet"))
    if la:
        if ehem:
            return "unklar", f"Wikipedia: aktiv, aber Plan 1935: {plan_text}"
        return "aktiv", "" if plan_text else "im Plan 1935 nicht beschriftet"
    if plan_text and not ehem:
        return "stillgelegt", "im Plan 1935 noch beschriftet"
    return "stillgelegt", ""


def zechen_abgleichen(zechen: list[dict], plan: list[dict], artikel: dict[str, tuple[str, str]]) -> tuple[list[dict], list[dict]]:
    """Ergänzt jede Zeile um artikel_von/bis, plan_1935, status_1936, hinweis; gibt (Zeilen, Prüfliste) zurück.
    Handgeprüfte Zeilen (status_geprueft=ja) behalten status_1936 und hinweis."""
    neu, pruefung = [], []
    for z in zechen:
        z = dict(z)
        art_von, art_bis = artikel.get(z.get("quelle", ""), ("", ""))
        treffer = plan_treffer(z, plan)
        plan_text = treffer["text"] if treffer else ""
        z["artikel_von"], z["artikel_bis"], z["plan_1935"] = art_von, art_bis, plan_text
        if z.get("status_geprueft") == "ja" and z.get("status_1936"):
            neu.append(z)
            continue
        z["status_geprueft"] = "nein"
        z["status_1936"], z["hinweis"] = status_ableiten(z.get("betrieb_von", ""), z.get("betrieb_bis", ""),
                                                          art_von, art_bis, plan_text)
        neu.append(z)
        if z["status_1936"] == "unklar":
            pruefung.append(dict(name=z["name"], stadtteil=z.get("stadtteil", ""), lat=z.get("lat", ""), lon=z.get("lon", ""),
                                 liste=f'{z.get("betrieb_von", "")}–{z.get("betrieb_bis", "")}',
                                 artikel=f"{art_von}–{art_bis}", plan_1935=plan_text, hinweis=z["hinweis"],
                                 quelle=z.get("quelle", "")))
    pruefung.sort(key=lambda p: (not p["lat"], p["name"]))
    return neu, pruefung


def _artikeltitel(quelle: str) -> str:
    return urllib.parse.unquote(quelle.split("/wiki/", 1)[1].split("#", 1)[0]).replace("_", " ")


def hole_infobox_jahre(quelle: str, pause: float = 0.5) -> tuple[str, str]:
    """Betriebsjahre aus der Infobox des Artikels; wartet bei 429 und versucht es erneut."""
    for versuch in range(8):
        r = requests.get(API, params=dict(action="parse", page=_artikeltitel(quelle), prop="wikitext",
                                          format="json", redirects=1),
                         headers={"User-Agent": "essener-adressbuch-1936 (Zechen-Abgleich)"}, timeout=60)
        time.sleep(pause)
        if r.status_code == 429:
            time.sleep(5 * (versuch + 1))
            continue
        try:
            j = r.json()
        except ValueError:
            time.sleep(5 * (versuch + 1))
            continue
        if "parse" not in j:
            return "", ""
        return infobox_jahre(j["parse"]["wikitext"]["*"])
    raise RuntimeError(f"Wikipedia-API nicht erreichbar für {quelle}")


def main() -> None:
    k = projektwurzel() / "kuratierung"
    zechen = lies_csv(k / "zechen.csv")
    plan = lies_csv(k / "stadtplan_1935_zechen.csv")
    cache_pfad = k / "zechen_artikel.csv"
    cache = {} if "--neu" in sys.argv or not cache_pfad.exists() else \
        {z["quelle"]: (z["artikel_von"], z["artikel_bis"]) for z in lies_csv(cache_pfad)}
    for z in zechen:
        q = z.get("quelle", "")
        if q and "/wiki/" in q and q not in cache:
            cache[q] = hole_infobox_jahre(q)
            print(f"{z['name']}: Artikel {cache[q][0]}–{cache[q][1]}")
    schreib_csv(cache_pfad, [dict(quelle=q, artikel_von=v, artikel_bis=b) for q, (v, b) in sorted(cache.items())],
                ARTIKEL_FELDER)
    neu, pruefung = zechen_abgleichen(zechen, plan, cache)
    schreib_csv(k / "zechen.csv", neu, FELDER)
    schreib_csv(k / "zechen_pruefung.csv", pruefung, PRUEF_FELDER)
    zaehl = {s: sum(1 for z in neu if z["status_1936"] == s) for s in ("aktiv", "stillgelegt", "unklar")}
    print(f"{len(neu)} Zechen: {zaehl}; Prüfliste {len(pruefung)} → {k / 'zechen_pruefung.csv'}")


if __name__ == "__main__":
    main()
