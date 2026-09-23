"""Stufe 06: Datenpaket der Karte aus build/eintraege.csv (Spec docs/superpowers/specs/2026-09-21-basiskarte-design.md §5)."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path

from pipeline.lib.berufe import NIVEAUS, lade_kuratierung as lade_berufe, zuordnung as berufszuordnung
from pipeline.lib.eigentuemer import identitaet_sicher, lade_kuratierung, mit_stadtteil, schreibweise_von
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


def _besitz(eintraege: list[dict]) -> str:
    kats = {e["_kategorie"] for e in eintraege if e.get("teil") == "II" and e.get("_kategorie")}
    if not kats:
        return "ungeprueft"
    return kats.pop() if len(kats) == 1 else "gemischt"


def gruppiere(eintraege: list[dict], regeln: list[Regel], eigentuemer: dict[str, dict] | None = None,
             berufe: dict[str, dict] | None = None, ohdab: dict[str, dict] | None = None) -> dict[str, dict]:
    """Verortete Einträge je Adresse bündeln; Einträge sortiert, Merkmale, (Teil II) geprüfter Eigentümer
    und Berufszuordnung angehängt; `besitz` je Adresse = Kategorie | gemischt | ungeprueft (Spec §6.1),
    `niveau`/`n_niveau` je Adresse aus den Berufszuordnungen (Spec §6.2)."""
    gruppen: dict[str, dict] = {}
    eigentuemer = eigentuemer or {}
    berufe = berufe or {}
    ohdab = ohdab or {}
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
        kanon, kat, sicher = "", "", False
        if e.get("teil") == "II":
            s, _ = schreibweise_von(e)
            # zuerst die stadtteilgenaue Schreibweise („… ‹Katernberg›“), sonst die einfache
            z = eigentuemer.get(mit_stadtteil(s, e)) or eigentuemer.get(s)
            if z and z.get("geprueft") == "ja" and z.get("kategorie"):
                kanon, kat = z["eigentuemer"], z["kategorie"]
                sicher = identitaet_sicher(z)
        # _identitaet: nur identifizierte Eigentümer kommen in Suchindex und Liste; die Kategorie gilt immer.
        e = dict(e, _merkmale=merkmale_fuer(e, regeln), _eigentuemer=kanon, _kategorie=kat, _identitaet=sicher,
                _beruf=berufszuordnung(e, berufe, ohdab) if berufe else None)
        a["eintraege"].append(e)
    for a in gruppen.values():
        a["eintraege"] = sortiere_eintraege(a["eintraege"])
        a["besitz"] = _besitz(a["eintraege"])
        a["niveau"], a["n_niveau"] = _niveau(a["eintraege"])
    return gruppen


def _niveau(eintraege: list[dict]) -> tuple[str, dict[str, int]]:
    """Punktattribut je Adresse (Spec §6.2): nur Teil I; eine Stufe mit mehr als der Hälfte der geprüften
    Einträge → Stufe; sonst gemischt; nur unsicher → unsicher; nichts geprüft → ungeprueft. Zählung je
    Stufe für TP5."""
    n: dict[str, int] = defaultdict(int)
    for e in eintraege:
        if e.get("teil") == "I" and e.get("_beruf"):
            n[e["_beruf"]["niveau"]] += 1
    gesamt = sum(n.values())
    if not gesamt:
        return "ungeprueft", {}
    stufen = {k: v for k, v in n.items() if k != "unsicher"}
    if not stufen:
        return "unsicher", dict(n)
    beste, anzahl = max(stufen.items(), key=lambda x: x[1])
    return (beste if anzahl * 2 > gesamt else "gemischt"), dict(n)


def punkt_feature(a: dict) -> dict:
    p = dict(id=a["id"], stufe=a["stufe"], stadtteil=a["stadtteil"], strasse_heute=a["strasse_heute"],
             hausnr=a["hausnr"] + (a["hausnr_zusatz"] or ""), historisch=a["historisch"],
             nummer_unsicher=a["nummer_unsicher"], besitz=a.get("besitz", "ungeprueft"),
             niveau=a.get("niveau", "ungeprueft"), n_I=0, n_II=0, n_III=0)
    merkmale: dict[str, int] = defaultdict(int)
    for e in a["eintraege"]:
        p["n_" + e["teil"]] += 1
        for m in e["_merkmale"]:
            merkmale[m] += 1
    p.update({f"m_{m}": n for m, n in sorted(merkmale.items())})
    p.update({f"n_{k}": v for k, v in sorted(a.get("n_niveau", {}).items())})
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [a["lon"], a["lat"]]},
            "properties": p}


def eintrag_kurz(e: dict, merkmale: list[str]) -> dict:
    b = e.get("_beruf") or {}
    return dict(id=e["id"], teil=e["teil"], seite=e.get("page", ""), name=e.get("lastname", ""),
                vorname=e.get("firstname", ""), beruf=e.get("Beruf o. ä.", ""), etage=e.get("lage", ""),
                stand=e.get("Familienstand", ""), bezug_vorname=e.get("Vorname Bezugsperson", ""),
                bezug_beruf=e.get("Beruf Bezugsperson", ""), firma=e.get("Firmenname", ""),
                eigentuemer=e.get("Eigentümer", ""), verwalter=e.get("Verwalter", ""),
                wohnort=e.get("abweichender Wohnort", ""), eigentuemer_kanon=e.get("_eigentuemer", ""),
                kategorie=e.get("_kategorie", ""), beruf_norm=b.get("beruf", ""), ohdab=b.get("ohdab", ""),
                niveau=b.get("niveau", ""), status=b.get("status", ""),
                flags=[f for f in FLAGS if e.get(f) == "ja"], merkmale=list(merkmale))


def baue_scherben(adressen: dict[str, dict]) -> dict[str, dict[str, list[dict]]]:
    scherben: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    for aid, a in adressen.items():
        scherben[scherbe(aid)][aid] = [eintrag_kurz(e, e["_merkmale"]) for e in a["eintraege"]]
    return dict(scherben)


def baue_adressscherben(adressen: dict[str, dict]) -> dict[str, dict[str, dict]]:
    """Adressscherben: Scherbe (die ersten zwei Zeichen der Adress-ID) → Adress-ID → Punkteigenschaften
    (wie punkt_feature(), aber ohne Umweg über GeoJSON) plus lat/lon — als Fallback, wenn eine Adresse
    nicht in den gerade geladenen Kartenkacheln liegt (Task 13-Review)."""
    scherben: dict[str, dict[str, dict]] = defaultdict(dict)
    for aid, a in adressen.items():
        p = dict(punkt_feature(a)["properties"], lat=a["lat"], lon=a["lon"])
        scherben[scherbe(aid)][aid] = p
    return dict(scherben)


def anzeige_adresse(a: dict) -> str:
    """Adresse zur Anzeige: heutige Straße, Nummer, Stadtteil; bei Stadtplan die historische Schreibung."""
    if a["stufe"] == "stadtplan" or not a["strasse_heute"]:
        return f"{a['historisch']} (Stadtplan 1935)"
    nr = a["hausnr"] + (a["hausnr_zusatz"] or "")
    kopf = f"{a['strasse_heute']} {nr}".strip()
    return f"{kopf}, {a['stadtteil']}" if a["stadtteil"] else kopf


def baue_namensindex(adressen: dict[str, dict]) -> dict[str, list[list]]:
    """Namenindex: Scherbe (praefix2(Nachname)) → Zeilen mit Schlüssel, Name, Vorname, Beruf, Adresse, IDs."""
    idx: dict[str, list[list]] = defaultdict(list)
    for a in adressen.values():
        anz = anzeige_adresse(a)
        for e in a["eintraege"]:
            nach = e.get("lastname", "")
            if not nach:
                continue
            k = falte(f"{nach} {e.get('firstname', '')}")
            idx[praefix2(nach)].append([k, nach, e.get("firstname", ""), e.get("Beruf o. ä.", ""), anz,
                                        e["id"], a["id"], e["teil"]])
    return {s: sorted(z) for s, z in idx.items()}


def baue_firmenindex(adressen: dict[str, dict]) -> dict[str, list[list]]:
    """Firmenindex: Scherbe (praefix2(Firmenname)) → Zeilen mit Schlüssel, Name, Adresse, IDs."""
    idx: dict[str, list[list]] = defaultdict(list)
    for a in adressen.values():
        anz = anzeige_adresse(a)
        for e in a["eintraege"]:
            firma = e.get("Firmenname", "")
            if firma:
                idx[praefix2(firma)].append([falte(firma), firma, anz, e["id"], a["id"]])
    return {s: sorted(z) for s, z in idx.items()}


def _strassengruppen(adressen: dict[str, dict]) -> dict[tuple, dict]:
    """Adressen je (Name, Art, Ort) bündeln (heute + 1936); gemeinsame Grundlage für Index und Scherben."""
    gruppen: dict[tuple, dict] = {}
    for a in adressen.values():
        n = len(a["eintraege"])
        ort = a["stadtteil"]
        paare = [(a["strasse_heute"], "heute", ort)] if a["strasse_heute"] else []
        roh = a["eintraege"][0].get("strasse_roh", "")
        vorort = a["eintraege"][0].get("Vorort", "") or ort
        if roh:
            paare.append((roh, "1936", vorort))
        for name, art, o in paare:
            g = gruppen.setdefault((name, art, o), dict(schluessel=falte(name), name=name, art=art, ort=o,
                                                        zeilen=0, adressen=[]))
            g["zeilen"] += n
            g["adressen"].append(a["id"])
    return gruppen


def baue_strassenindex(adressen: dict[str, dict]) -> list[dict]:
    """Straßenindex: je (Name, Art, Ort) ein dict mit Schlüssel, Name, Art, Ort, Zeilenanzahl, Adressanzahl."""
    gruppen = _strassengruppen(adressen)
    return sorted(({"schluessel": g["schluessel"], "name": g["name"], "art": g["art"], "ort": g["ort"],
                   "zeilen": g["zeilen"], "adressen_n": len(g["adressen"])} for g in gruppen.values()),
                 key=lambda g: (g["schluessel"], g["art"], g["ort"]))


def baue_strassenscherben(adressen: dict[str, dict]) -> dict[str, dict[str, list[str]]]:
    """Straßenscherben: Scherbe (praefix2(Name)) → "Name|Art|Ort" → sortierte Liste der Adress-IDs."""
    gruppen = _strassengruppen(adressen)
    scherben: dict[str, dict[str, list[str]]] = defaultdict(dict)
    for g in gruppen.values():
        scherben[praefix2(g["name"])][f"{g['name']}|{g['art']}|{g['ort']}"] = sorted(g["adressen"])
    return dict(scherben)


def baue_berufsindex(adressen: dict[str, dict]) -> tuple[list[list], dict[str, dict[str, list[list]]]]:
    """Berufsindex (Rohtext, nur ungeprüfte Schreibweisen — geprüfte erscheinen im Normindex, Spec §6.4):
    (Liste [Schlüssel, Schreibung, Zeilen], Scherbe → Schreibung → [[Adress-ID, Zähler]])."""
    zaehler: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for a in adressen.values():
        for e in a["eintraege"]:
            b = e.get("Beruf o. ä.", "")
            if b and not e.get("_beruf"):
                zaehler[b][a["id"]] += 1
    liste = sorted([[falte(b), b, sum(z.values())] for b, z in zaehler.items()])
    scherben: dict[str, dict[str, list[list]]] = defaultdict(dict)
    for b, z in zaehler.items():
        scherben[praefix2(b)][b] = sorted([[aid, n] for aid, n in z.items()])
    return liste, dict(scherben)


def baue_berufsnormindex(adressen: dict[str, dict]) -> tuple[list[list], dict[str, dict[str, list[list]]]]:
    """Suchindex nach Normbezeichnung geprüfter Zuordnungen (Spec §6.4): Liste [Schlüssel, Beruf, ohdab_id,
    Nennungen, Schreibweisen, Niveau] nach Nennungen absteigend; Scherbe praefix2(Beruf) → ohdab_id →
    [[Adress-ID, Zähler]]."""
    zaehler: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    info: dict[str, dict] = {}
    schreibweisen: dict[str, set[str]] = defaultdict(set)
    for a in adressen.values():
        for e in a["eintraege"]:
            b = e.get("_beruf")
            if b:
                zaehler[b["ohdab"]][a["id"]] += 1
                info[b["ohdab"]] = b
                schreibweisen[b["ohdab"]].add(e.get("Beruf o. ä.", ""))
    liste = sorted([[falte(info[o]["beruf"]), info[o]["beruf"], o, sum(z.values()), len(schreibweisen[o]), info[o]["niveau"]] for o, z in zaehler.items()],
                   key=lambda x: (-x[3], x[0]))
    scherben: dict[str, dict[str, list[list]]] = defaultdict(dict)
    for o, z in zaehler.items():
        scherben[praefix2(info[o]["beruf"])][o] = sorted([[aid, n] for aid, n in z.items()])
    return liste, dict(scherben)


def baue_eigentuemerindex(adressen: dict[str, dict]) -> tuple[list[list], dict[str, dict[str, list[list]]]]:
    """Eigentümerindex (nur geprüfte, Spec §6.4): (Liste [Schlüssel, Name, Häuser, Kategorie] nach Häusern
    absteigend, Scherbe praefix2(Name) → Name → [[Adress-ID, Zähler]]). Trägt derselbe kanonische Name in
    verschiedenen Teil-II-Zeilen verschiedene Kategorien (Kuratierungsstand uneinheitlich), zeigt der
    Index „gemischt“ statt der zuletzt gesehenen Kategorie (F5 — „last wins“ hätte das verschluckt)."""
    zaehler: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    kategorien: dict[str, set[str]] = defaultdict(set)
    for a in adressen.values():
        for e in a["eintraege"]:
            if e.get("_eigentuemer") and e.get("_identitaet"):
                zaehler[e["_eigentuemer"]][a["id"]] += 1
                kategorien[e["_eigentuemer"]].add(e["_kategorie"])
    kategorie = {n: (k.pop() if len(k) == 1 else "gemischt") for n, k in kategorien.items()}
    liste = sorted([[falte(n), n, len(z), kategorie[n]] for n, z in zaehler.items()], key=lambda x: (-x[2], x[0]))
    scherben: dict[str, dict[str, list[list]]] = defaultdict(dict)
    for n, z in zaehler.items():
        scherben[praefix2(n)][n] = sorted([[aid, k] for aid, k in z.items()])
    return liste, dict(scherben)


def baue_stadtteile(adressen: dict[str, dict]) -> list[dict]:
    """Stadtteilindex: je Stadtteil ein dict mit Name, Breitengrad (Mittel), Längengrad (Mittel), Zeilenanzahl."""
    summen: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0, 0])  # lat, lon, adressen, zeilen
    for a in adressen.values():
        if not a["stadtteil"]:
            continue
        s = summen[a["stadtteil"]]
        s[0] += a["lat"]; s[1] += a["lon"]; s[2] += 1; s[3] += len(a["eintraege"])
    return [dict(name=n, lat=round(s[0] / s[2], 5), lon=round(s[1] / s[2], 5), zeilen=s[3])
            for n, s in sorted(summen.items())]


STUFEN = ["haus", "strasse", "stadtplan", "offen"]


def baue_kennzahlen(eintraege: list[dict], adressen: dict[str, dict], datum: str) -> dict:
    je_teil: dict[str, int] = defaultdict(int)
    je_stufe: dict[str, int] = defaultdict(int)
    for e in eintraege:
        je_teil[e["teil"]] += 1
        s = _stufe(e) if e.get("stufe") in VERORTET else "offen"
        je_stufe[s] += 1
    n = len(eintraege) or 1
    teil_i = [e for a in adressen.values() for e in a["eintraege"] if e["teil"] == "I"]
    return dict(eintraege_je_teil=dict(sorted(je_teil.items())),
                stufen={s: round(100 * je_stufe[s] / n, 1) for s in STUFEN},
                verortet=sum(je_stufe[s] for s in STUFEN[:3]), offen=je_stufe["offen"],
                adressen=len(adressen), stand=datum,
                besitz_geprueft=sum(1 for a in adressen.values() if a.get("besitz", "ungeprueft") != "ungeprueft"),
                eigentuemer_geprueft=len({e["_eigentuemer"] for a in adressen.values() for e in a["eintraege"] if e.get("_eigentuemer")}),
                berufe_geprueft=round(100 * sum(1 for e in teil_i if e.get("_beruf")) / (len(teil_i) or 1), 1),
                berufe_schreibweisen_geprueft=len({e["Beruf o. ä."] for e in teil_i if e.get("_beruf")}))


def zechen_geojson(zeilen: list[dict]) -> dict:
    """`aktiv_1936` kommt aus dem kuratierten `status_1936` (werkzeuge/zechen_abgleich.py: Wikipedia-Liste,
    Artikel-Infobox und Stadtplan 1935 müssen übereinstimmen); „unklar“ und „stillgelegt“ sind nicht aktiv.
    Betriebsjahre: die des Artikels, ersatzweise die der Liste; `jahre_widerspruch`, wenn beide bekannt
    sind und abweichen; `jahre_unbekannt`, wenn keine Quelle beide Jahre nennt (Precision first)."""
    features = []
    for z in zeilen:
        if not z.get("lat") or not z.get("lon"):
            continue
        liste = (z.get("betrieb_von") or "", z.get("betrieb_bis") or "")
        artikel = (z.get("artikel_von") or "", z.get("artikel_bis") or "")
        von, bis = artikel if all(artikel) else liste
        jahre_unbekannt = not von or not bis
        jahre_widerspruch = all(artikel) and all(liste) and artikel != liste
        features.append({"type": "Feature",
                         "geometry": {"type": "Point", "coordinates": [float(z["lon"]), float(z["lat"])]},
                         "properties": dict(name=z["name"], stadtteil=z.get("stadtteil", ""),
                                            betrieb_von=von, betrieb_bis=bis,
                                            liste_von=liste[0], liste_bis=liste[1],
                                            plan_1935=z.get("plan_1935", ""),
                                            quelle=z.get("quelle", ""), status_1936=z.get("status_1936", "unklar"),
                                            aktiv_1936=z.get("status_1936") == "aktiv",
                                            jahre_unbekannt=jahre_unbekannt, jahre_widerspruch=jahre_widerspruch)})
    return {"type": "FeatureCollection", "features": features}


def tippecanoe_befehl(geojson: Path, pmtiles: Path) -> list[str]:
    return ["tippecanoe", "-o", str(pmtiles), "--force", "--layer=adressen", "--minimum-zoom=9",
            "--maximum-zoom=15", "--drop-densest-as-needed", "--extend-zooms-if-still-dropping",
            "--no-feature-limit", "--no-tile-size-limit", "--quiet", str(geojson)]


def _json(pfad: Path, daten) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def faksimile_tabelle(zeilen: list[dict]) -> dict[str, int]:
    """Seite (I-333) → Bildnummer im DigiBib-Viewer, aus kuratierung/faksimile_seiten.csv."""
    return {z["seite"]: int(z["bild"]) for z in zeilen if z.get("seite") and z.get("bild")}


def startseite_beispiele(zeilen: list[dict], adressen: dict[str, dict]) -> list[dict]:
    """Beispielpunkte der Startseite aus kuratierung/startseite_beispiele.csv (adress_id, eintrag_id):
    nur hausgenau verortete Adressen, Reihenfolge wie in der Tabelle; unbekannte IDs fallen weg
    (Precision first — kein Beispiel ohne belastbaren Punkt)."""
    beispiele = []
    for z in zeilen:
        a = adressen.get(z.get("adress_id", ""))
        if not a or a["stufe"] != "haus":
            continue
        e = next((x for x in a["eintraege"] if x["id"] == z.get("eintrag_id")), None)
        if e is None:
            continue
        k = eintrag_kurz(e, e["_merkmale"])
        # Teil II: Firmenname trägt den Eigentümer (Körperschaft), eigentuemer die Rolle („Eigentümer“/„Verwalter“)
        person = ", ".join(x for x in (k["name"], k["vorname"]) if x)
        titel = (k["firma"] or person) if k["teil"] in ("II", "III") else person
        rolle = (k["eigentuemer"] or "Eigentümer") if k["teil"] == "II" else ", ".join(x for x in (k["beruf"], k["stand"]) if x)
        beispiele.append(dict(id=a["id"], e=k["id"], lat=a["lat"], lon=a["lon"], titel=titel,
                              untertitel=" · ".join(x for x in (rolle, a["historisch"]) if x)))
    return beispiele


def schreibe_themen(quelle: Path, ausgabe: Path) -> list[dict]:
    """Kopiert die Thema-Definitionen aus kuratierung/themen/*.json nach ausgabe/themen/ und schreibt
    dort index.json (id, titel, freigegeben); gibt den Index zurück."""
    index = []
    for pfad in sorted(Path(quelle).glob("*.json")):
        t = json.loads(pfad.read_text(encoding="utf-8"))
        _json(ausgabe / "themen" / pfad.name, t)
        index.append(dict(id=t["id"], titel=t["titel"], freigegeben=bool(t.get("freigegeben"))))
    _json(ausgabe / "themen" / "index.json", index)
    return index


def schreibe_paket(ausgabe: Path, eintraege: list[dict], regeln: list[Regel], zechen: list[dict],
                   datum: str, kacheln: bool = True, faksimile: list[dict] | None = None,
                   beispiele: list[dict] | None = None, themen: Path | None = None,
                   eigentuemer: list[dict] | None = None, berufe: list[dict] | None = None,
                   ohdab: dict[str, dict] | None = None) -> dict:
    """Schreibt das komplette Datenpaket nach `ausgabe` (site/daten) und gibt die Kennzahlen zurück."""
    ausgabe = Path(ausgabe)
    if themen is not None:
        schreibe_themen(themen, ausgabe)
    _json(ausgabe / "faksimile.json", faksimile_tabelle(faksimile or []))
    adressen = gruppiere(eintraege, regeln, lade_kuratierung(eigentuemer or []),
                         berufe=lade_berufe(berufe or []), ohdab=ohdab or {})
    _json(ausgabe / "startseite.json", startseite_beispiele(beispiele or [], adressen))
    geo = {"type": "FeatureCollection", "features": [punkt_feature(a) for a in adressen.values()]}
    _json(ausgabe / "adressen.geojson", geo)
    if kacheln:
        subprocess.run(tippecanoe_befehl(ausgabe / "adressen.geojson", ausgabe / "adressen.pmtiles"), check=True)
    for name, inhalt in baue_scherben(adressen).items():
        _json(ausgabe / "haus" / f"{name}.json", inhalt)
    for name, inhalt in baue_adressscherben(adressen).items():
        _json(ausgabe / "adressen" / f"{name}.json", inhalt)
    for name, zeilen in baue_namensindex(adressen).items():
        _json(ausgabe / "suche" / "namen" / f"{name}.json", zeilen)
    for name, zeilen in baue_firmenindex(adressen).items():
        _json(ausgabe / "suche" / "firmen" / f"{name}.json", zeilen)
    _json(ausgabe / "suche" / "strassen.json", baue_strassenindex(adressen))
    for name, inhalt in baue_strassenscherben(adressen).items():
        _json(ausgabe / "suche" / "strassen" / f"{name}.json", inhalt)
    liste, scherben = baue_berufsindex(adressen)
    _json(ausgabe / "suche" / "berufe.json", liste)
    for name, inhalt in scherben.items():
        _json(ausgabe / "suche" / "berufe" / f"{name}.json", inhalt)
    liste, scherben = baue_berufsnormindex(adressen)
    _json(ausgabe / "suche" / "berufe_norm.json", liste)
    for name, inhalt in scherben.items():
        _json(ausgabe / "suche" / "berufe_norm" / f"{name}.json", inhalt)
    liste, scherben = baue_eigentuemerindex(adressen)
    _json(ausgabe / "suche" / "eigentuemer.json", liste)
    for name, inhalt in scherben.items():
        _json(ausgabe / "suche" / "eigentuemer" / f"{name}.json", inhalt)
    _json(ausgabe / "suche" / "stadtteile.json", baue_stadtteile(adressen))
    _json(ausgabe / "zechen.geojson", zechen_geojson(zechen))
    kennzahlen = baue_kennzahlen(eintraege, adressen, datum)
    _json(ausgabe / "kennzahlen.json", kennzahlen)
    return kennzahlen
