"""Stufe 06: Datenpaket der Karte aus build/eintraege.csv (Spec docs/superpowers/specs/2026-09-21-basiskarte-design.md §5)."""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path

from pipeline.lib.bergbau import GRUPPEN as BB_GRUPPEN, lade_bergbau, pruefe_gegen_berufe, rang_gruppe
from pipeline.lib.berufe import lade_kuratierung as lade_berufe, zuordnung as berufszuordnung
from pipeline.lib.ebenen import EBENEN, aggregiere, hex_polygon, hex_zelle, zaehlfelder
from pipeline.lib.eigentuemer import hausnummernspanne, identitaet_sicher, lade_kuratierung, mit_stadtteil, person_nach_regel, schreibweise_von
from pipeline.lib.gewerbe import gewerbe_quelle, betriebsschluessel, gewerbe_export, lade_gewerbe, rubrik_von
from pipeline.lib.gruppen import fehlende_bezeichnungen, hauptgruppe, lade_hauptgruppen
from pipeline.lib.layout import beeswarm, packe_gruppen, packe_kreise, radius
from pipeline.lib.merkmale import Regel, merkmale_fuer
from pipeline.lib.perspektiven import kapitel_index, lade_kapitel, pruefe_datenbasis_bezug, pruefe_kapitel, pruefe_kennzahlen_bezug, pruefe_punkte_bezug
from pipeline.lib.stadtteile import Stadtteile
from pipeline.lib.stellung import STELLUNGEN
from pipeline.lib.stufen import ADRESSSCHLUESSEL

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "ae", "Ö": "oe", "Ü": "ue"})
_NICHT_ZEICHEN = re.compile(r"[^a-z0-9 ]+")
_ETAGEN = {"erdg.": 0, "erdg": 0, "parterre.": 0, "parterre": 0, "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5}
ETAGE_OHNE = 99
NIVEAUS_REIHE = ["helfer", "fachlich", "spezialist", "hochkomplex", "aufsicht", "fuehrung", "keins"]


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


def _besitz(eintraege: list[dict]) -> tuple[str, str]:
    """(Besitzklasse, Prüfung) aus den eigenen Teil-II-Zeilen: Kategorie | gemischt | ungeprueft und
    hand | regel | "" — `regel`, wenn alle beteiligten Zeilen nur über die Regel Person → Privatperson
    klassifiziert sind (person_nach_regel), damit die Seite diesen Anteil ausweisen kann."""
    zeilen = [e for e in eintraege if e.get("teil") == "II" and e.get("_kategorie")]
    kats = {e["_kategorie"] for e in zeilen}
    if not kats:
        return "ungeprueft", ""
    return (kats.pop() if len(kats) == 1 else "gemischt"), ("regel" if all(e.get("_pruefung") == "regel" for e in zeilen) else "hand")


def _kuratiert(e: dict, eigentuemer: dict[str, dict]) -> dict | None:
    """Geprüfte Kuratierungszeile zu einem Teil-II-Eintrag: zuerst die stadtteilgenaue Schreibweise
    („… ‹Katernberg›“), sonst die einfache; nur mit geprueft=ja und Kategorie."""
    s, _ = schreibweise_von(e)
    z = eigentuemer.get(mit_stadtteil(s, e)) or eigentuemer.get(s)
    return z if z and z.get("geprueft") == "ja" and z.get("kategorie") else None


def _zuordnung(e: dict, eigentuemer: dict[str, dict]) -> dict | None:
    """Eigentümerzuordnung eines Teil-II-Eintrags: Handprüfung (Kuratierungszeile) vor Regel
    (Person → Privatperson, ohne Namen und Identität); None, wenn keines greift."""
    z = _kuratiert(e, eigentuemer)
    if z:
        return dict(eigentuemer=z["eigentuemer"], kategorie=z["kategorie"], identitaet=identitaet_sicher(z), pruefung="hand")
    if person_nach_regel(e):
        return dict(eigentuemer="", kategorie="privatperson", identitaet=False, pruefung="regel")
    return None


def _strassenschluessel(e: dict) -> str:
    return (e.get("schl_nr") or e.get("strasse_heute") or "").strip()


def hausnummernspannen(eintraege: list[dict], eigentuemer: dict[str, dict]) -> dict[str, list[dict]]:
    """Teil-II-Zeilen mit Hausnummernspanne je Straße. Das Häuserbuch druckt einen Eigentümer vieler
    aufeinanderfolgender Häuser einmal am Anfang der Straßenseite („2—84 E. Frau-Margarete-Krupp-Stiftung“,
    Faksimile II-335); die Häuser dazwischen folgen nur mit Bewohnern. Gleiche Parität von Anfang und Ende
    heißt eine Straßenseite (2—84: nur gerade), sonst gelten alle Nummern dazwischen (2—9). Nur geprüfte
    Eigentümer; auch nicht verortete Zeilen zählen, der Treffer läuft über Straße und Nummer."""
    spannen: dict[str, list[dict]] = defaultdict(list)
    for e in eintraege:
        spanne = hausnummernspanne(e) if e.get("teil") == "II" else None
        strasse = _strassenschluessel(e)
        z = _zuordnung(e, eigentuemer) if spanne and strasse else None
        if not z:
            continue
        von, bis, seite = spanne
        text = f"{_historisch(dict(e, hausnr=f'{von}–{e['hausnr_bis']}', hausnr_zusatz=''))} · {schreibweise_von(e)[0]}"
        spannen[strasse].append(dict(z, von=von, bis=bis, seite=seite, text=text))
    return dict(spannen)


def _hat_teil_ii(a: dict) -> bool:
    return any(e.get("teil") == "II" for e in a["eintraege"])


def _uebernimm_besitz(a: dict, treffer: list[dict], quelle: str) -> None:
    """Klasse aus fremden Belegen (Spanne oder gleiche Hausnummer): verschiedene Kategorien → gemischt; der
    Eigentümername wird nur übernommen, wenn alle Belege denselben identifizierten Eigentümer nennen."""
    kats = {t["kategorie"] for t in treffer}
    namen = {t["eigentuemer"] for t in treffer}
    a["besitz"] = kats.pop() if len(kats) == 1 else "gemischt"
    a["besitz_quelle"] = quelle
    a["besitz_pruefung"] = "regel" if all(t.get("pruefung") == "regel" for t in treffer) else "hand"
    a["besitz_spanne"] = " | ".join(t["text"] for t in treffer)
    a["besitz_eigentuemer"] = namen.pop() if len(namen) == 1 and a["besitz"] != "gemischt" and all(t["identitaet"] for t in treffer) else ""


def hausnummern_mit_besitz(adressen: dict[str, dict]) -> dict[tuple[str, str, str], list[dict]]:
    """(Straße, Nummer, Zusatz) → Belege der Adressobjekte mit eigener geprüfter Teil-II-Zeile. Dieselbe
    Hausnummer wird zu mehreren Adressobjekten, wenn Teil I und Teil II die Straße verschieden schreiben
    („Baumstr.“/„Baumstraße“, Vorort): die Teil-II-Zeile gilt trotzdem für dasselbe Haus."""
    nummern: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for a in adressen.values():
        if a["besitz"] == "ungeprueft" or not _hat_teil_ii(a) or not a["eintraege"]:
            continue
        zeilen = [e for e in a["eintraege"] if e.get("teil") == "II" and e.get("_kategorie")]
        namen = {e["_eigentuemer"] for e in zeilen}
        nummern[(_strassenschluessel(a["eintraege"][0]), a["hausnr"], a["hausnr_zusatz"])].append(dict(
            kategorie=a["besitz"], eigentuemer=namen.pop() if len(namen) == 1 else "", pruefung=a["besitz_pruefung"],
            identitaet=all(e.get("_identitaet") for e in zeilen),
            text=f"{a['historisch']} · {' | '.join(sorted({schreibweise_von(e)[0] for e in zeilen}))}"))
    return dict(nummern)


def _besitz_aus_nummer(a: dict, nummern: dict[tuple[str, str, str], list[dict]]) -> None:
    """Besitzklasse einer Adresse ohne eigenen Teil-II-Eintrag von einem anderen Adressobjekt derselben
    Straße, Nummer und desselben Zusatzes."""
    if _hat_teil_ii(a) or not a["eintraege"]:
        return
    treffer = nummern.get((_strassenschluessel(a["eintraege"][0]), a["hausnr"], a["hausnr_zusatz"]))
    if treffer:
        _uebernimm_besitz(a, treffer, "nummer")


def _besitz_aus_spanne(a: dict, spannen: dict[str, list[dict]]) -> None:
    """Besitzklasse einer Adresse ohne eigenen Teil-II-Eintrag aus den Spannen ihrer Straße. Ein eigener
    Eintrag gewinnt immer — auch ein ungeprüfter, denn er ist die genauere Angabe; ebenso die Zeile eines
    anderen Adressobjekts derselben Nummer (_besitz_aus_nummer). Verschiedene Kategorien in überlappenden
    Spannen → gemischt."""
    if _hat_teil_ii(a) or a["besitz"] != "ungeprueft" or not (a.get("hausnr") or "").isdigit():
        return
    n = int(a["hausnr"])
    strasse = _strassenschluessel(a["eintraege"][0]) if a["eintraege"] else ""
    treffer = [s for s in spannen.get(strasse, []) if s["von"] <= n <= s["bis"] and s["seite"] in (None, n % 2)]
    if treffer:
        _uebernimm_besitz(a, treffer, "spanne")


def gruppiere(eintraege: list[dict], regeln: list[Regel], eigentuemer: dict[str, dict] | None = None,
             berufe: dict[str, dict] | None = None, ohdab: dict[str, dict] | None = None,
             gewerbe: dict[str, dict] | None = None, stadtteile: "Stadtteile | None" = None,
             bergbau: dict[str, str] | None = None) -> dict[str, dict]:
    """Verortete Einträge je Adresse bündeln; Einträge sortiert, Merkmale, (Teil II) geprüfter Eigentümer,
    Berufszuordnung (mit OhdAB-Hauptgruppe als `gruppe`, Spec §5.2) und Gewerbezuordnung (Teil III) angehängt; `besitz` je Adresse =
    Kategorie | gemischt | ungeprueft (Spec §6.1), `niveau`/`n_niveau` je Adresse aus den Berufszuordnungen
    (Spec §6.2). `stadtteil` ist der Polygontreffer aus `stadtteile.zuordnen` (heutige Grenzen), sonst der
    bisherige Straßen-Stadtteil; `stadtteil_quelle` sagt, welcher Fall zutraf (Spec §5.4a)."""
    adressen: dict[str, dict] = {}
    eigentuemer = eigentuemer or {}
    berufe = berufe or {}
    ohdab = ohdab or {}
    for e in eintraege:
        if e.get("stufe") not in VERORTET or not e.get("lat") or not e.get("lon"):
            continue
        aid = adress_id(e)
        a = adressen.get(aid)
        if a is None:
            strassen_st = e.get("stadtteil", "") or e.get("Vorort", "")
            poly = stadtteile.zuordnen(float(e["lat"]), float(e["lon"])) if stadtteile else None
            a = adressen[aid] = dict(id=aid, lat=float(e["lat"]), lon=float(e["lon"]), stufe=_stufe(e),
                                    stadtteil=poly or strassen_st, stadtteil_quelle="polygon" if poly else ("strasse" if strassen_st else ""),
                                    strasse_heute=e.get("strasse_heute", ""), hausnr=e.get("hausnr", ""),
                                    hausnr_zusatz=e.get("hausnr_zusatz", ""), historisch=_historisch(e),
                                    nummer_unsicher=e.get("nummer_unsicher", "nein"), eintraege=[])
        kanon, kat, sicher, pruefung = "", "", False, ""
        if e.get("teil") == "II":
            z = _zuordnung(e, eigentuemer)
            if z:
                kanon, kat, sicher, pruefung = z["eigentuemer"], z["kategorie"], z["identitaet"], z["pruefung"]
        beruf = berufszuordnung(e, berufe, ohdab) if berufe and e.get("teil") in ("I", "II") else None
        if beruf:
            beruf["gruppe"] = hauptgruppe(beruf["gattung_id"])
        if beruf and bergbau and bergbau.get(beruf["beruf"]):
            beruf["bergbau"] = bergbau[beruf["beruf"]]      # Spec Bergbau §2.3
        gew = None
        if e.get("teil") == "III" and e.get("Firmenname"):
            firma, rubrik = rubrik_von(e["Firmenname"])
            if rubrik:
                gz = (gewerbe or {}).get(rubrik)
                g, art = gewerbe_export(gz)
                gew = dict(rubrik=rubrik, firma=firma, gruppe=g, art=art, quelle=gewerbe_quelle(gz), schluessel=betriebsschluessel(e))
        # _identitaet: nur identifizierte Eigentümer kommen in Suchindex und Liste; die Kategorie gilt immer.
        e = dict(e, _merkmale=merkmale_fuer(e, regeln), _eigentuemer=kanon, _kategorie=kat, _identitaet=sicher, _pruefung=pruefung,
                _beruf=beruf, _gewerbe=gew)
        a["eintraege"].append(e)
    for a in adressen.values():
        a["eintraege"] = sortiere_eintraege(a["eintraege"])
        a["besitz"], a["besitz_pruefung"] = _besitz(a["eintraege"])
        a["besitz_quelle"] = "eintrag" if a["besitz"] != "ungeprueft" else ""
        a["besitz_spanne"] = ""
        a["besitz_eigentuemer"] = ""
        a["niveau"], a["n_niveau"] = _niveau(a["eintraege"])
    # Zweiter Durchgang für Adressen ohne eigene Teil-II-Zeile, in dieser Rangfolge: die Zeile eines anderen
    # Adressobjekts derselben Hausnummer, dann Hausnummernspannen („2—84 E. …“) der Straße. besitz_quelle
    # sagt je Adresse, woher die Klasse kommt: eintrag | nummer | spanne | "" (ungeprüft).
    nummern = hausnummern_mit_besitz(adressen)
    spannen = hausnummernspannen(eintraege, eigentuemer)
    for a in adressen.values():
        _besitz_aus_nummer(a, nummern)
        _besitz_aus_spanne(a, spannen)
    return adressen


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
             besitz_quelle=a.get("besitz_quelle", ""), besitz_spanne=a.get("besitz_spanne", ""), besitz_pruefung=a.get("besitz_pruefung", ""),
             niveau=a.get("niveau", "ungeprueft"), n_I=0, n_II=0, n_III=0)
    merkmale: dict[str, int] = defaultdict(int)
    for e in a["eintraege"]:
        for m in e["_merkmale"]:
            merkmale[m] += 1
    p.update({f"m_{m}": n for m, n in sorted(merkmale.items())})
    z = zaehlfelder(a)
    p.update(z)
    bb = rang_gruppe(z)
    if bb:
        p["bergbau"] = bb        # höchste Bergbau-Gruppe im Haus (Thema auf der Karte, Spec §5)
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [a["lon"], a["lat"]]},
            "properties": p}


def eintrag_kurz(e: dict, merkmale: list[str]) -> dict:
    b = e.get("_beruf") or {}
    g = e.get("_gewerbe") or {}
    return dict(id=e["id"], teil=e["teil"], seite=e.get("page", ""), name=e.get("lastname", ""),
                vorname=e.get("firstname", ""), beruf=e.get("Beruf o. ä.", ""), etage=e.get("lage", ""),
                stand=e.get("Familienstand", ""), bezug_vorname=e.get("Vorname Bezugsperson", ""),
                bezug_beruf=e.get("Beruf Bezugsperson", ""), firma=e.get("Firmenname", ""),
                eigentuemer=e.get("Eigentümer", ""), verwalter=e.get("Verwalter", ""),
                wohnort=e.get("abweichender Wohnort", ""), eigentuemer_kanon=e.get("_eigentuemer", ""),
                kategorie=e.get("_kategorie", ""), pruefung=e.get("_pruefung", ""), beruf_norm=b.get("beruf", ""), ohdab=b.get("ohdab", ""),
                niveau=b.get("niveau", ""), status=b.get("status", ""), gattung=b.get("gattung", ""),
                stellung=b.get("stellung", ""), stellung_quelle=b.get("stellung_quelle", ""), gruppe=b.get("gruppe", ""), rubrik=g.get("rubrik", ""),
                gewerbe_gruppe=g.get("gruppe", ""), gewerbe_art=g.get("art", ""), gewerbe_quelle=g.get("quelle", ""),
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
    [[Adress-ID, Zähler]]. Label/Schlüssel/Scherbe kommen aus der OhdAB-Normbezeichnung (`norm`), nicht aus
    dem kuratierten `beruf` — sonst hätte dieselbe Zuordnung unter verschiedenen Schreibweisen (mit
    unterschiedlich kuratiertem `beruf`) verschiedene Indexeinträge bekommen können."""
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
    liste = sorted([[falte(info[o]["norm"]), info[o]["norm"], o, sum(z.values()), len(schreibweisen[o]), info[o]["niveau"]] for o, z in zaehler.items()],
                   key=lambda x: (-x[3], x[0]))
    scherben: dict[str, dict[str, list[list]]] = defaultdict(dict)
    for o, z in zaehler.items():
        scherben[praefix2(info[o]["norm"])][o] = sorted([[aid, n] for aid, n in z.items()])
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
        if a.get("besitz_eigentuemer"):      # Haus aus einer Hausnummernspanne (ohne eigene Teil-II-Zeile)
            zaehler[a["besitz_eigentuemer"]][a["id"]] += 1
            kategorien[a["besitz_eigentuemer"]].add(a["besitz"])
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


def _prozent(z: int, n: int) -> float:
    return round(100 * z / (n or 1), 1)


def baue_kennzahlen(eintraege: list[dict], adressen: dict[str, dict], datum: str) -> dict:
    je_teil: dict[str, int] = defaultdict(int)
    je_stufe: dict[str, int] = defaultdict(int)
    for e in eintraege:
        je_teil[e["teil"]] += 1
        s = _stufe(e) if e.get("stufe") in VERORTET else "offen"
        je_stufe[s] += 1
    n = len(eintraege) or 1
    teil_i = [e for a in adressen.values() for e in a["eintraege"] if e["teil"] == "I"]
    teil_iii = [e for a in adressen.values() for e in a["eintraege"] if e["teil"] == "III" and e.get("_gewerbe")]
    mit_beruf = [e for e in teil_i if e.get("_beruf")]
    st_hand = sum(1 for e in mit_beruf if e["_beruf"].get("stellung_quelle") == "hand" and e["_beruf"]["stellung"] != "unbestimmt")
    st_vorschlag = sum(1 for e in mit_beruf if e["_beruf"].get("stellung_quelle") == "vorschlag" and e["_beruf"]["stellung"] != "unbestimmt")
    st_unbestimmt = sum(1 for e in teil_i if not e.get("_beruf") or e["_beruf"]["stellung"] == "unbestimmt")
    gw_hand = sum(1 for e in teil_iii if e["_gewerbe"].get("quelle") == "hand")
    gw_claude = sum(1 for e in teil_iii if e["_gewerbe"].get("quelle") == "claude")
    gw_regel = sum(1 for e in teil_iii if e["_gewerbe"].get("quelle") == "vorschlag")
    besitz_geprueft = sum(1 for a in adressen.values() if a.get("besitz", "ungeprueft") != "ungeprueft")
    besitz_regel = sum(1 for a in adressen.values() if a.get("besitz_pruefung") == "regel")
    bb = [e for e in teil_i if (e.get("_beruf") or {}).get("bergbau")]
    bb_je = {g: sum(1 for e in bb if e["_beruf"]["bergbau"] == g) for g in BB_GRUPPEN}
    bb_haeuser = [a for a in adressen.values() if a.get("besitz") == "bergbau"]
    def _gesellschaft(a):
        return next((e["_eigentuemer"] for e in a["eintraege"] if e.get("teil") == "II" and e.get("_kategorie") == "bergbau" and e.get("_eigentuemer")),
                    a.get("besitz_eigentuemer") or "")
    bb_namen = [_gesellschaft(a) for a in bb_haeuser]
    return dict(eintraege_je_teil=dict(sorted(je_teil.items())),
                stufen={s: round(100 * je_stufe[s] / n, 1) for s in STUFEN},
                verortet=sum(je_stufe[s] for s in STUFEN[:3]), offen=je_stufe["offen"],
                adressen=len(adressen), stand=datum,
                # absolute Zähler für die Trichter der Schlaglichter (Kapitel 0): Zeilen je Teil und Stufe
                eintraege=len(eintraege), eintraege_I=je_teil["I"], eintraege_II=je_teil["II"], eintraege_III=je_teil["III"],
                stufe_haus=je_stufe["haus"], stufe_strasse=je_stufe["strasse"], stufe_stadtplan=je_stufe["stadtplan"], stufe_offen=je_stufe["offen"],
                besitz_geprueft=besitz_geprueft,
                besitz_spanne=sum(1 for a in adressen.values() if a.get("besitz_quelle") == "spanne"),
                besitz_nummer=sum(1 for a in adressen.values() if a.get("besitz_quelle") == "nummer"),
                besitz_regel=besitz_regel,
                besitz_hand=besitz_geprueft - besitz_regel,
                eigentuemer_geprueft=len({e["_eigentuemer"] for a in adressen.values() for e in a["eintraege"] if e.get("_eigentuemer")}),
                berufe_geprueft=round(100 * len(mit_beruf) / (len(teil_i) or 1), 1),
                berufe_schreibweisen_geprueft=len({e["Beruf o. ä."] for e in teil_i if e.get("_beruf")}),
                # Drei disjunkte Anteile (Summe 100): von Hand bestimmt, Vorschlag bestimmt, unbestimmt (auch
                # nach Handprüfung) oder ohne geprüften Beruf. Handgeprüft-unbestimmt zählte sonst doppelt.
                stellung_geprueft=_prozent(st_hand, len(teil_i)),
                stellung_vorschlag=_prozent(st_vorschlag, len(teil_i)),
                stellung_unbestimmt=_prozent(st_unbestimmt, len(teil_i)),
                teil_i_n=len(teil_i), beruf_geprueft_n=len(mit_beruf),
                stellung_bestimmt_n=st_hand + st_vorschlag, stellung_hand_n=st_hand, stellung_vorschlag_n=st_vorschlag, stellung_unbestimmt_n=st_unbestimmt,
                gewerbe_geprueft=_prozent(gw_hand, len(teil_iii)),
                gewerbe_entschieden=_prozent(gw_claude, len(teil_iii)),
                gewerbe_vorschlag=_prozent(gw_regel, len(teil_iii)),
                betriebe_n=len(teil_iii), gewerbe_hand_n=gw_hand, gewerbe_claude_n=gw_claude, gewerbe_regel_n=gw_regel,
                stadtteil_polygon=_prozent(sum(1 for a in adressen.values() if a.get("stadtteil_quelle") == "polygon"), len(adressen)),
                bergbau_n=len(bb), bergbau_belegschaft_n=bb_je["belegschaft"], bergbau_aufsicht_n=bb_je["aufsicht"],
                bergbau_leitung_n=bb_je["leitung"], bergbau_invaliden_n=bb_je["invaliden"],
                bergbau_haeuser_n=len(bb_haeuser), bergbau_gesellschaften_n=len({n for n in bb_namen if n}),
                bergbau_haeuser_ohne_name_n=sum(1 for n in bb_namen if not n))


TOP_N = 10


def _top(zaehler: dict, n: int = TOP_N) -> list:
    """Die n häufigsten Einträge eines Zählers als Listen [schlüssel…, zahl], absteigend, bei Gleichstand alphabetisch."""
    return [[*k, z] if isinstance(k, tuple) else [k, z] for k, z in sorted(zaehler.items(), key=lambda kv: (-kv[1], kv[0]))[:n]]


def _stellung_klasse(b):
    return b["stellung"] if b else "unbestimmt"


def _mehrheit(zaehler: dict) -> str:
    """Der häufigste Schlüssel eines Zählers, bei Gleichstand der alphabetisch letzte — dieselbe Regel für Layout
    (Farbe des Kreises) und Herkunft (Stellung im Pfad), damit beide dieselbe Stellung je Norm nennen."""
    return max(zaehler.items(), key=lambda kv: (kv[1], kv[0]))[0]


def _sammle_berufe(adressen: dict[str, dict], schluessel) -> dict[str, dict]:
    """Je Wert von `schluessel(_beruf)` (Stellung, Hauptgruppe, Niveau): Schreibweisen, Normen, Nennungen, Quelle, Top-Schreibweisen.
    Einträge ohne geprüften Beruf zählen bei der Stellung als `unbestimmt` (Schreibweise ohne Norm und ohne Quelle)."""
    aus: dict[str, dict] = {}
    for a in adressen.values():
        for e in a["eintraege"]:
            if e.get("teil") != "I":
                continue
            b = e.get("_beruf")
            klasse = schluessel(b) if b else None
            if klasse is None:
                continue
            k = aus.setdefault(klasse, dict(_schreib=defaultdict(int), _normen=set(), _quelle=defaultdict(int), _norm_von={}, _quelle_von={}))
            s = e.get("Beruf o. ä.", "")
            k["_schreib"][s] += 1
            if b:
                k["_normen"].add(b["ohdab"]); k["_norm_von"][s] = b["norm"]
                q = b.get("stellung_quelle", "hand") if schluessel is _stellung_klasse else "hand"
                k["_quelle"][q] += 1; k["_quelle_von"][s] = q
            else:
                k["_norm_von"][s] = ""; k["_quelle_von"][s] = ""
    out = {}
    for klasse, k in aus.items():
        out[klasse] = dict(schreibweisen=len(k["_schreib"]), normen=len(k["_normen"]), nennungen=sum(k["_schreib"].values()),
                           quelle=dict(k["_quelle"]),
                           top=[[s, n, k["_norm_von"][s], k["_quelle_von"][s]] for s, n in _top(k["_schreib"])])
    return out


def baue_herkunft(adressen: dict[str, dict]) -> dict[str, dict]:
    """Herkunftspaket (Spec 2026-09-27 Herkunftspfad §3): je Klasse und je Einzelobjekt, woher die Zahl kommt —
    Schreibweisen des Buches, Normen bzw. kanonische Namen, Quellanteile (Hand/Vorschlag/Regel/Prinzipien).
    Grundmenge sind die verorteten Einträge (Ergebnis von `gruppiere`), nicht die Kuratierungstabellen."""
    stellung = _sammle_berufe(adressen, _stellung_klasse)
    # Stellung: auch Einträge ohne geprüften Beruf, als unbestimmt (Schreibweise ohne Norm, ohne Quelle)
    unbest = stellung.setdefault("unbestimmt", dict(schreibweisen=0, normen=0, nennungen=0, quelle={}, top=[]))
    ohne: dict[str, int] = defaultdict(int)
    for a in adressen.values():
        for e in a["eintraege"]:
            if e.get("teil") == "I" and not e.get("_beruf"):
                ohne[e.get("Beruf o. ä.", "")] += 1
    if ohne:
        schreib = defaultdict(int, {t[0]: t[1] for t in unbest["top"]})
        for s, n in ohne.items(): schreib[s] += n
        vorhanden = {t[0]: (t[2], t[3]) for t in unbest["top"]}
        unbest["schreibweisen"] += len(ohne); unbest["nennungen"] += sum(ohne.values())
        unbest["top"] = [[s, n, *vorhanden.get(s, ("", ""))] for s, n in _top(schreib)]
    for k in stellung.values():
        k["quelle"] = {"hand": k["quelle"].get("hand", 0), "vorschlag": k["quelle"].get("vorschlag", 0)}
    gruppe = _sammle_berufe(adressen, lambda b: b["gruppe"] if b else None)
    niveau = _sammle_berufe(adressen, lambda b: b["niveau"] if b else None)
    for d in (gruppe, niveau):
        for k in d.values(): k["quelle"] = {"hand": k["quelle"].get("hand", 0)}

    berufe: dict[str, dict] = {}
    for a in adressen.values():
        for e in a["eintraege"]:
            b = e.get("_beruf")
            if not b or e.get("teil") != "I":
                continue
            n = berufe.setdefault(b["ohdab"], dict(norm=b["norm"], _schreib=defaultdict(int), _st=defaultdict(int), _quelle=defaultdict(int), _quelle_von={}))
            s = e.get("Beruf o. ä.", ""); q = b.get("stellung_quelle", "hand")
            n["_schreib"][s] += 1; n["_st"][b["stellung"]] += 1; n["_quelle"][q] += 1; n["_quelle_von"][s] = q
    # Stellung je Norm = Mehrheit der Nennungen (wie baue_layouts); die Quelle steht je Schreibweise, denn
    # kuratierung/berufe.csv ordnet je Schreibweise zu — eine Norm kann Hand- und Vorschlagszeilen mischen.
    berufe = {k: dict(norm=v["norm"], nennungen=sum(v["_schreib"].values()), schreibweisen_gesamt=len(v["_schreib"]),
                      schreibweisen=[[s, n, v["_quelle_von"][s]] for s, n in _top(v["_schreib"])], stellung=_mehrheit(v["_st"]),
                      quelle={"hand": v["_quelle"].get("hand", 0), "vorschlag": v["_quelle"].get("vorschlag", 0)})
              for k, v in berufe.items()}

    besitz: dict[str, dict] = {}
    eig: dict[str, dict] = {}
    for a in adressen.values():
        klasse = a.get("besitz", "ungeprueft")
        if klasse == "ungeprueft":
            continue
        k = besitz.setdefault(klasse, dict(_eig=set(), zeilen=0, haeuser=0, quelle={"hand": 0, "regel": 0}, spanne=0, nummer=0, _top=defaultdict(int), _regel=defaultdict(int)))
        k["haeuser"] += 1
        k["quelle"]["regel" if a.get("besitz_pruefung") == "regel" else "hand"] += 1
        if a.get("besitz_quelle") == "spanne": k["spanne"] += 1
        if a.get("besitz_quelle") == "nummer": k["nummer"] += 1
        # Das Haus zählt für jeden identifizierten Eigentümer einmal — wie baue_eigentuemerindex: aus den eigenen
        # Teil-II-Zeilen (dort steht besitz_eigentuemer nicht) oder aus der Übernahme per Spanne / gleicher Nummer.
        neu = lambda kat: dict(_schreib=defaultdict(int), zeilen=0, haeuser=0, spanne=0, nummer=0, kategorie=kat, identitaet=True, seite="")
        kanone: dict[str, str] = {}
        if a.get("besitz_eigentuemer"):
            kanone[a["besitz_eigentuemer"]] = klasse
        for e in a["eintraege"]:
            if e.get("teil") != "II":
                continue
            k["zeilen"] += 1
            s = e.get("Firmenname") or ", ".join(t for t in (e.get("lastname", ""), e.get("firstname", "")) if t)
            if e.get("_pruefung") == "regel":
                k["_regel"][s] += 1
            if e.get("_eigentuemer") and e.get("_identitaet"):
                kanone.setdefault(e["_eigentuemer"], e.get("_kategorie", klasse))
                x = eig.setdefault(e["_eigentuemer"], neu(e.get("_kategorie", klasse)))
                x["zeilen"] += 1; x["_schreib"][s] += 1
                if not x["seite"]: x["seite"] = e.get("page", "")
        for kanon, kat in kanone.items():
            k["_eig"].add(kanon); k["_top"][kanon] += 1
            x = eig.setdefault(kanon, neu(kat))
            x["haeuser"] += 1
            if a.get("besitz_quelle") == "spanne": x["spanne"] += 1
            if a.get("besitz_quelle") == "nummer": x["nummer"] += 1
    besitz = {kl: dict(eigentuemer=len(k["_eig"]), zeilen=k["zeilen"], haeuser=k["haeuser"], quelle=k["quelle"], spanne=k["spanne"], nummer=k["nummer"],
                       top=_top(k["_top"]), **({"regel_beispiele": _top(k["_regel"], 5)} if kl == "privatperson" else {}))
              for kl, k in besitz.items()}
    eigentuemer = {kanon: dict(schreibweisen=_top(x["_schreib"]), schreibweisen_gesamt=len(x["_schreib"]), zeilen=x["zeilen"], haeuser=x["haeuser"],
                               spanne=x["spanne"], nummer=x["nummer"], kategorie=x["kategorie"], identitaet=x["identitaet"], seite=x["seite"])
                   for kanon, x in eig.items()}

    gewerbe: dict[str, dict] = {}
    rubriken: dict[str, dict] = {}
    betriebe: set[tuple[str, str]] = set()
    for a in adressen.values():
        for e in a["eintraege"]:
            g = e.get("_gewerbe")
            if not g or e.get("teil") != "III":
                continue
            if (g["schluessel"], g["rubrik"]) in betriebe:      # je Rubrik zählt ein Betrieb einmal (wie baue_layouts, Ebenen)
                continue
            betriebe.add((g["schluessel"], g["rubrik"]))
            k = gewerbe.setdefault(g["gruppe"], dict(_rub=defaultdict(int), quelle={"hand": 0, "claude": 0, "vorschlag": 0}, _art={}, _quelle={}))
            k["_rub"][g["rubrik"]] += 1
            k["quelle"][g["quelle"]] = k["quelle"].get(g["quelle"], 0) + 1
            k["_art"][g["rubrik"]] = g["art"]; k["_quelle"][g["rubrik"]] = g["quelle"]
            r = rubriken.setdefault(g["rubrik"], dict(betriebe=0, gruppe=g["gruppe"], art=g["art"], quelle=g["quelle"]))
            r["betriebe"] += 1
    gewerbe = {gr: dict(rubriken=len(k["_rub"]), betriebe=sum(k["_rub"].values()), quelle=k["quelle"],
                        top=[[r, n, k["_art"][r], k["_quelle"][r]] for r, n in _top(k["_rub"])])
               for gr, k in gewerbe.items()}
    return dict(stellung=stellung, gruppe=gruppe, niveau=niveau, berufe=berufe, besitz=besitz, eigentuemer=eigentuemer, gewerbe=gewerbe, rubriken=rubriken)


def baue_layouts(adressen: dict[str, dict]) -> dict[str, dict]:
    """Vorberechnete Bubble-Layouts (Spec §5.4): Berufsnormen (Gruppenpackung nach Berufsgruppe + Beeswarm nach Niveau),
    identifizierte Eigentümer (Packung nach Klasse), Gewerberubriken (Packung nach Gruppe). Stellung und Gruppe je Norm =
    Mehrheit über die Einträge (Nennungen), damit ein Item nur eine Farbe trägt; „unbestimmt“ zählt mit."""
    normen: dict[str, dict] = {}
    st: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    eig: dict[str, dict] = {}
    rub: dict[str, dict] = {}
    betriebe: set[tuple[str, str]] = set()
    for a in adressen.values():
        for e in a["eintraege"]:
            b = e.get("_beruf")
            if b and e["teil"] == "I":
                n = normen.setdefault(b["ohdab"], dict(id=b["ohdab"], norm=b["norm"], n=0, niveau=b["niveau"], gruppe=b["gruppe"]))
                n["n"] += 1
                st[b["ohdab"]][b["stellung"]] += 1
            if e.get("_eigentuemer") and e.get("_identitaet"):
                x = eig.setdefault(e["_eigentuemer"], dict(id=e["_eigentuemer"], n=0, gruppe=e["_kategorie"], haeuser=set()))
                x["haeuser"].add(a["id"])
            g = e.get("_gewerbe")
            if g and (g["schluessel"], g["rubrik"]) not in betriebe:      # je Rubrik zählt ein Betrieb einmal
                betriebe.add((g["schluessel"], g["rubrik"]))
                r = rub.setdefault(g["rubrik"], dict(id=g["rubrik"], n=0, gruppe=g["gruppe"], art=g["art"]))
                r["n"] += 1
        if a.get("besitz_eigentuemer"):      # Haus aus einer Hausnummernspanne zählt zur Fläche des Eigentümers
            x = eig.setdefault(a["besitz_eigentuemer"], dict(id=a["besitz_eigentuemer"], n=0, gruppe=a["besitz"], haeuser=set()))
            x["haeuser"].add(a["id"])
    for x in eig.values():
        x["n"] = len(x.pop("haeuser"))
    for n in normen.values():
        n["stellung"] = _mehrheit(st[n["id"]])

    def layout(kreise: list[dict]) -> dict:
        kreise = sorted(kreise, key=lambda k: (-k["n"], k["id"]))
        mx = max((k["n"] for k in kreise), default=0)
        for k in kreise:
            k["r"] = radius(k["n"], mx)
        gepackt, huellen = packe_gruppen(kreise) if kreise else ([], [])
        return dict(kreise=gepackt, gruppen=huellen)

    berufe = layout(list(normen.values()))
    niveaus = [*NIVEAUS_REIHE, "unsicher"]
    bees = {k["id"]: k for k in beeswarm([dict(id=k["id"], r=k["r"], spalte=k["niveau"] if k["niveau"] in niveaus else "keins")
                                          for k in berufe["kreise"]], niveaus)}
    for k in berufe["kreise"]:
        k["niveau_xy"] = dict(x=bees[k["id"]]["x"], y=bees[k["id"]]["y"])
    berufe["niveaus"] = niveaus
    return dict(berufe=berufe, eigentuemer=layout(list(eig.values())), gewerbe=layout(list(rub.values())))


def baue_bergbau_punkte(adressen: dict[str, dict]) -> dict:
    """Kapiteldaten des Bergbau-Kapitels (Spec 2026-09-28 §2.4): je Gruppe ein Kreis je Hexfeld mit Packung
    (gesammelter Zustand) und Lage (verteilter Zustand); dazu alle geprüften Häuser der Klasse Bergbau mit
    ihrer Gesellschaft. Radius ∝ sqrt(n / maxn), ein Maßstab über alle Gruppen (max 9, min 1.2)."""
    from pipeline.lib.bergbau import GRUPPEN as BB, NAMEN
    from pipeline.lib.ebenen import _lonlat, hex_id, hex_mitte, hex_zelle
    je_feld: dict[str, dict[str, int]] = {g: defaultdict(int) for g in BB}
    haeuser: list[dict] = []
    gesellschaften: dict[str, dict] = {}
    for a in adressen.values():
        hid = hex_id(*hex_zelle(a["lat"], a["lon"]))
        for e in a["eintraege"]:
            g = (e.get("_beruf") or {}).get("bergbau") if e.get("teil") == "I" else None
            if g:
                je_feld[g][hid] += 1
        if a.get("besitz") == "bergbau":
            name = next((e["_eigentuemer"] for e in a["eintraege"] if e.get("teil") == "II" and e.get("_kategorie") == "bergbau" and e.get("_eigentuemer")),
                        a.get("besitz_eigentuemer") or "")
            eid = falte(name).replace(" ", "_") if name else "unbekannt"
            haeuser.append(dict(id=a["id"], lon=a["lon"], lat=a["lat"], eig=eid, stufe=a.get("stufe", "haus")))
            x = gesellschaften.setdefault(eid, dict(id=eid, name=name or "unbekannter Bergbau-Eigentümer", haeuser=0))
            x["haeuser"] += 1
    maxn = max((n for z in je_feld.values() for n in z.values()), default=0)

    def r_von(n: int) -> float:
        return max(1.2, round(9.0 * math.sqrt(n / maxn), 3)) if maxn else 1.2

    hexe: dict[str, list[dict]] = {}
    for g in BB:
        kreise = []
        for hid, n in je_feld[g].items():
            q, r = (int(v) for v in hid.split("_"))
            lon, lat = _lonlat(*hex_mitte(q, r))
            kreise.append(dict(id=hid, lon=lon, lat=lat, n=n, r=r_von(n)))
        kreise.sort(key=lambda k: (-k["n"], k["id"]))
        hexe[g] = packe_kreise(kreise, abstand=0.6) if kreise else []
    gruppen = [dict(id=g, name=NAMEN[g], n=sum(je_feld[g].values()), felder=len(je_feld[g])) for g in BB]
    return dict(gruppen=gruppen, hex=hexe, haeuser=haeuser,
                gesellschaften=sorted(gesellschaften.values(), key=lambda x: (-x["haeuser"], x["id"])), maxn=maxn)


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


def strassen_features(strassen: list[dict], linien: dict[str, list]) -> list[dict]:
    """Nur heutige Straßen (fünfstellige schl_nr) mit OSM-Linie; Feature-id = int(schl_nr) für feature-state."""
    out = []
    for s in strassen:
        if not (len(s["id"]) == 5 and s["id"].isdigit()) or s["name"] not in linien:
            continue
        out.append({"type": "Feature", "id": int(s["id"]), "geometry": {"type": "MultiLineString", "coordinates": linien[s["name"]]},
                    "properties": {"id": s["id"], "name": s["name"], "stadtteil": s.get("stadtteil", "")}})
    return out


def hex_features(hexe: list[dict]) -> list[dict]:
    out = []
    for h in hexe:
        q, r = (int(x) for x in h["id"].split("_"))
        out.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [hex_polygon(q, r)]}, "properties": {"id": h["id"]}})
    return out


def tippecanoe_befehl(ausgabe: Path, pmtiles: Path) -> list[str]:
    return ["tippecanoe", "-o", str(pmtiles), "--force", "--minimum-zoom=9", "--maximum-zoom=15", "--drop-densest-as-needed",
            "--extend-zooms-if-still-dropping", "--no-feature-limit", "--no-tile-size-limit", "--quiet",
            "-L", f"adressen:{ausgabe / 'adressen.geojson'}", "-L", f"strassen:{ausgabe / 'strassen.geojson'}", "-L", f"hex:{ausgabe / 'hex.geojson'}"]


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
                   ohdab: dict[str, dict] | None = None, hauptgruppen: list[dict] | None = None,
                   gewerbe: list[dict] | None = None, osm_linien: dict | None = None,
                   stadtteile: "Stadtteile | None" = None, perspektiven: Path | None = None,
                   bergbau: list[dict] | None = None) -> dict:
    """Schreibt das komplette Datenpaket nach `ausgabe` (site/daten) und gibt die Kennzahlen zurück."""
    ausgabe = Path(ausgabe)
    hg = lade_hauptgruppen(hauptgruppen or [])
    if ohdab:
        fehlt = fehlende_bezeichnungen(ohdab, hg)
        if fehlt:
            raise ValueError(f"kuratierung/hauptgruppen.csv: Bezeichnung fehlt für {sorted(fehlt)}")
    _json(ausgabe / "hauptgruppen.json", {k: dict(bezeichnung=v["bezeichnung"], kurz=v["kurz"], bereich=v["bereich"]) for k, v in hg.items()})
    if themen is not None:
        schreibe_themen(themen, ausgabe)
    _json(ausgabe / "faksimile.json", faksimile_tabelle(faksimile or []))
    bb_tabelle = lade_bergbau(bergbau or [])
    if bb_tabelle and berufe:
        fehlt = pruefe_gegen_berufe(bb_tabelle, berufe)
        if fehlt:
            raise ValueError(f"kuratierung/merkmale/bergbau.csv: Norm nicht in berufe.csv: {fehlt}")
    adressen = gruppiere(eintraege, regeln, lade_kuratierung(eigentuemer or []),
                         berufe=lade_berufe(berufe or []), ohdab=ohdab or {}, gewerbe=lade_gewerbe(gewerbe or []),
                         stadtteile=stadtteile, bergbau=bb_tabelle)
    _json(ausgabe / "startseite.json", startseite_beispiele(beispiele or [], adressen))
    geo = {"type": "FeatureCollection", "features": [punkt_feature(a) for a in adressen.values()]}
    _json(ausgabe / "adressen.geojson", geo)
    strassen_agg = aggregiere(adressen, "strasse")
    sf = strassen_features(strassen_agg, osm_linien or {})
    _json(ausgabe / "strassen.geojson", {"type": "FeatureCollection", "features": sf})
    _json(ausgabe / "hex.geojson", {"type": "FeatureCollection", "features": hex_features(aggregiere(adressen, "hex"))})
    if stadtteile:
        _json(ausgabe / "stadtteile.geojson", stadtteile.geojson())
    if kacheln:
        subprocess.run(tippecanoe_befehl(ausgabe, ausgabe / "adressen.pmtiles"), check=True)
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
    _EBENEN_DATEI = {"strasse": "strassen", "stadtteil": "stadtteile", "hex": "hex"}
    for ebene in EBENEN:
        _json(ausgabe / "ebenen" / f"{_EBENEN_DATEI[ebene]}.json", aggregiere(adressen, ebene))
    for name, inhalt in baue_layouts(adressen).items():
        _json(ausgabe / "layout" / f"{name}.json", inhalt)
    punkte = baue_bergbau_punkte(adressen)
    _json(ausgabe / "perspektiven" / "bergbau_punkte.json", punkte)
    for name, inhalt in baue_herkunft(adressen).items():
        _json(ausgabe / "herkunft" / f"{name}.json", inhalt)
    kennzahlen = baue_kennzahlen(eintraege, adressen, datum)
    kennzahlen["strassen_mit_linie"] = len(sf)
    _json(ausgabe / "kennzahlen.json", kennzahlen)
    if perspektiven is not None:
        ks = lade_kapitel(perspektiven)
        for k in ks:
            fehler = pruefe_kapitel(k) + pruefe_kennzahlen_bezug(k, kennzahlen) + pruefe_punkte_bezug(k, punkte)
            if fehler:
                raise ValueError("kuratierung/perspektiven: " + "; ".join(fehler))
        fehler = pruefe_datenbasis_bezug(ks)
        if fehler:
            raise ValueError("kuratierung/perspektiven: " + "; ".join(fehler))
        _json(ausgabe / "perspektiven" / "index.json", kapitel_index(ks))
        for k in ks:
            _json(ausgabe / "perspektiven" / f"{k['id']}.json", k)
    return kennzahlen
