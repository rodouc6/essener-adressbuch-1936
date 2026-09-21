"""Stufe 06: Datenpaket der Karte aus build/eintraege.csv (Spec docs/superpowers/specs/2026-09-21-basiskarte-design.md §5)."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict

from pipeline.lib.merkmale import Regel, merkmale_fuer
from pipeline.lib.stufen import ADRESSSCHLUESSEL

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"})
_NICHT_ZEICHEN = re.compile(r"[^a-z0-9 ]+")
_ETAGEN = {"erdg.": 0, "erdg": 0, "parterre.": 0, "parterre": 0, "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5}
ETAGE_OHNE = 99


def adress_id(eintrag: dict) -> str:
    """Stabile Adress-ID: SHA-1 über den ADRESSSCHLUESSEL, 12 Hex-Zeichen."""
    roh = "\x1f".join(eintrag.get(f, "") for f in ADRESSSCHLUESSEL)
    return hashlib.sha1(roh.encode("utf-8")).hexdigest()[:12]


def scherbe(aid: str) -> str:
    return aid[:2]


def falte(text: str) -> str:
    """Suchschlüssel: klein, Umlaute aufgelöst, Akzente entfernt, nur a–z, 0–9 und Leerzeichen."""
    t = (text or "").translate(_UMLAUTE).lower()
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = _NICHT_ZEICHEN.sub(" ", t)
    return " ".join(t.split())


def praefix2(text: str) -> str:
    """Scherbenname des Suchindex: die ersten zwei Zeichen des gefalteten Schlüssels, `_` wenn leer."""
    k = falte(text).replace(" ", "")
    return k[:2] if k else "_"


def etagen_rang(lage: str) -> int:
    return _ETAGEN.get((lage or "").strip().lower(), ETAGE_OHNE)


def sortiere_eintraege(eintraege: list[dict]) -> list[dict]:
    """Etage laut Buch zuerst (Erdg., I, II …), Einträge ohne Etage danach; innerhalb alphabetisch."""
    return sorted(eintraege, key=lambda e: (etagen_rang(e.get("lage", "")), falte(e.get("lastname", "")),
                                            falte(e.get("firstname", "")), e.get("id", "")))


VERORTET = {"haus", "strasse"}
FLAGS = ["nummer_unsicher", "zeitlich_abweichend", "mehrdeutig"]


def _historisch(e: dict) -> str:
    """Buchschreibung der Adresse: Straße, Hausnummer (mit Zusatz), Vorort."""
    nr = (e.get("hausnr", "") + (e.get("hausnr_zusatz", "") or "")).strip()
    kopf = " ".join(x for x in (e.get("strasse_roh", ""), nr) if x)
    return f"{kopf}, {e['Vorort']}" if e.get("Vorort") else kopf


def _stufe(e: dict) -> str:
    return "stadtplan" if e.get("herkunft") == "stadtplan_1935" else e["stufe"]


def gruppiere(eintraege: list[dict], regeln: list[Regel]) -> dict[str, dict]:
    """Verortete Einträge je Adresse bündeln; Einträge sortiert, Merkmale angehängt."""
    gruppen: dict[str, dict] = {}
    for e in eintraege:
        if e.get("stufe") not in VERORTET or not e.get("lat") or not e.get("lon"):
            continue
        aid = adress_id(e)
        a = gruppen.get(aid)
        if a is None:
            a = gruppen[aid] = dict(id=aid, lat=float(e["lat"]), lon=float(e["lon"]), stufe=_stufe(e),
                                    stadtteil=e.get("stadtteil", "") or e.get("Vorort", ""),
                                    strasse_heute=e.get("strasse_heute", ""), hausnr=e.get("hausnr", ""),
                                    hausnr_zusatz=e.get("hausnr_zusatz", ""), historisch=_historisch(e),
                                    nummer_unsicher=e.get("nummer_unsicher", "nein"), eintraege=[])
        e = dict(e, _merkmale=merkmale_fuer(e, regeln))
        a["eintraege"].append(e)
    for a in gruppen.values():
        a["eintraege"] = sortiere_eintraege(a["eintraege"])
    return gruppen


def punkt_feature(a: dict) -> dict:
    p = dict(id=a["id"], stufe=a["stufe"], stadtteil=a["stadtteil"], strasse_heute=a["strasse_heute"],
             hausnr=a["hausnr"] + (a["hausnr_zusatz"] or ""), historisch=a["historisch"],
             nummer_unsicher=a["nummer_unsicher"], n_I=0, n_II=0, n_III=0)
    merkmale: dict[str, int] = defaultdict(int)
    for e in a["eintraege"]:
        p["n_" + e["teil"]] += 1
        for m in e["_merkmale"]:
            merkmale[m] += 1
    p.update({f"m_{m}": n for m, n in sorted(merkmale.items())})
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [a["lon"], a["lat"]]},
            "properties": p}


def eintrag_kurz(e: dict, merkmale: list[str]) -> dict:
    return dict(id=e["id"], teil=e["teil"], seite=e.get("page", ""), name=e.get("lastname", ""),
                vorname=e.get("firstname", ""), beruf=e.get("Beruf o. ä.", ""), etage=e.get("lage", ""),
                stand=e.get("Familienstand", ""), bezug_vorname=e.get("Vorname Bezugsperson", ""),
                bezug_beruf=e.get("Beruf Bezugsperson", ""), firma=e.get("Firmenname", ""),
                eigentuemer=e.get("Eigentümer", ""), verwalter=e.get("Verwalter", ""),
                wohnort=e.get("abweichender Wohnort", ""),
                flags=[f for f in FLAGS if e.get(f) == "ja"], merkmale=list(merkmale))


def baue_scherben(adressen: dict[str, dict]) -> dict[str, dict[str, list[dict]]]:
    scherben: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    for aid, a in adressen.items():
        scherben[scherbe(aid)][aid] = [eintrag_kurz(e, e["_merkmale"]) for e in a["eintraege"]]
    return dict(scherben)
