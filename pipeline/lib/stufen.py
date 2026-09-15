"""Zeilenweise Anwendung der Bibliotheksfunktionen (Stufen 02, 03 und 04).

Stufe 04 (`geokodiere_zeilen`) kennt zusätzlich zu den in `nominatim.geokodiere`
vergebenen Gründen den Grund `fehler` (`stufe="offen"`): eine fehlgeschlagene
HTTP-Anfrage an Nominatim für diese Adresse, siehe Docstring dort.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

import requests

from pipeline.lib.konkordanz import Strassenindex
from pipeline.lib.nominatim import Verortung, geokodiere
from pipeline.lib.normalisierung import norm_strasse
from pipeline.lib.parser import parse_adresse

PARSEFELDER = ["strasse_roh", "strasse_norm", "hausnr", "hausnr_zusatz", "hausnr_bis", "lage", "zusatz_frei", "parse_status"]


def parse_zeilen(zeilen: list[dict]) -> list[dict]:
    """Wendet parse_adresse und norm_strasse auf jede Zeile an und ergänzt die Parsefelder."""
    out = []
    for z in zeilen:
        a = parse_adresse(z.get("Adresse", ""))
        d = dict(z)
        d.update({k: v for k, v in asdict(a).items() if k != "status"})
        d["parse_status"] = a.status
        d["strasse_norm"] = norm_strasse(a.strasse_roh) if a.strasse_roh else ""
        out.append(d)
    return out


AUFLOESUNGSFELDER = ["strasse_heute", "schl_nr", "stadtteil", "herkunft", "zeitlich_abweichend",
                     "mehrdeutig", "kandidaten", "grund_mehrdeutig", "teilstrecke_abgetrennt"]
PAARFELDER = ["strasse_norm", "vorort", "teil", "zeilen", "beispiel"] + AUFLOESUNGSFELDER
VORSCHLAGSFELDER = ["strasse_norm", "vorort", "teil", "zeilen", "beispiel"] + [
    f"{k}_{i}" for i in (1, 2, 3) for k in ("kandidat", "lemma", "aehnlichkeit")]
PAARSCHLUESSEL = ("strasse_norm", "Vorort", "teil")


def loese_strassen(zeilen: list[dict], idx: Strassenindex) -> tuple[list[dict], list[dict], list[dict]]:
    """Löst je Zeile die Straße auf, baut die Paartabelle und eine Vorschlagsliste.

    Ein Paar ist (strasse_norm, Vorort, teil): der Buchteil gehört dazu, weil ein leerer
    Vorort in Teil I die Kernstadt bedeutet, in Teil II/III dagegen keine Information ist.

    Rückgabe: (Zeilen mit Auflösungsfeldern, Paartabelle nach Zeilenzahl absteigend,
    Vorschlagsliste für offene/mehrdeutige Paare nach Zeilenzahl absteigend).
    """
    paare: dict[tuple[str, str, str], dict] = {}
    for z in zeilen:
        k = (z["strasse_norm"], z["Vorort"], z["teil"])
        if k not in paare:
            if k[0]:
                auf = asdict(idx.aufloesen(*k))
            else:
                # Leerer strasse_norm: idx.aufloesen wird nicht aufgerufen, Paar bleibt offen
                # mit den Enum-Neutralwerten "nein" statt leerem String.
                auf = {f: "" for f in AUFLOESUNGSFELDER}
                auf.update(herkunft="offen", mehrdeutig="nein", zeitlich_abweichend="nein",
                           teilstrecke_abgetrennt="nein")
            paare[k] = {"strasse_norm": k[0], "vorort": k[1], "teil": k[2], "zeilen": 0,
                        "beispiel": z["Adresse"], **auf}
        paare[k]["zeilen"] += 1
    out = []
    for z in zeilen:
        p = paare[(z["strasse_norm"], z["Vorort"], z["teil"])]
        d = dict(z)
        d.update({f: p[f] for f in AUFLOESUNGSFELDER})
        out.append(d)
    vorschlaege = []
    for p in paare.values():
        if p["herkunft"] == "offen" or p["mehrdeutig"] == "ja":
            v = {f: p[f] for f in ("strasse_norm", "vorort", "teil", "zeilen", "beispiel")}
            for i, (kand, lemma, sim) in enumerate(idx.vorschlaege(p["strasse_norm"]) if p["strasse_norm"] else [], start=1):
                v[f"kandidat_{i}"], v[f"lemma_{i}"], v[f"aehnlichkeit_{i}"] = kand, lemma, str(sim)
            vorschlaege.append({f: v.get(f, "") for f in VORSCHLAGSFELDER})
    vorschlaege.sort(key=lambda v: -int(v["zeilen"]))
    paarliste = sorted(paare.values(), key=lambda p: -p["zeilen"])
    for p in paarliste:
        p["zeilen"] = str(p["zeilen"])
    for v in vorschlaege:
        v["zeilen"] = str(v["zeilen"])
    return out, paarliste, vorschlaege


VERORTUNGSFELDER = ["lat", "lon", "stufe", "grund", "osm_type", "osm_id", "display_name", "zusatz_ignoriert"]
# Schlüssel einer eindeutigen Adresse. Die vier Auflösungsfelder gehören dazu, damit
# 04_geokodiert.csv je Adresse eindeutig ist und Stufe 05 die Herkunft nicht von Hand
# nachjoinen muss (Spec §5.04).
ADRESSSCHLUESSEL = ["strasse_heute", "hausnr", "hausnr_zusatz", "stadtteil", "parse_status", "strasse_roh",
                    "herkunft", "zeitlich_abweichend", "mehrdeutig", "grund_mehrdeutig",
                    "teilstrecke_abgetrennt"]
ADRESSFELDER = ADRESSSCHLUESSEL + ["zeilen"] + VERORTUNGSFELDER


def geokodiere_zeilen(zeilen: list[dict], client, landmarken: list[dict], threads: int = 8) -> tuple[list[dict], list[dict]]:
    """Geokodiert je eindeutiger Adresse (nicht je Zeile), parallel über einen Thread-Pool.

    Adressen werden über ADRESSSCHLUESSEL dedupliziert und absteigend nach Zeilenzahl
    verortet. Rückgabe: (Zeilen mit Verortungsfeldern, Adresstabelle mit Zeilenzahl
    und Verortungsfeldern, nach Zeilenzahl absteigend sortiert).

    Schlägt die HTTP-Anfrage für eine Adresse fehl (`requests.RequestException`, z. B.
    Timeout, 5xx, Verbindungsabbruch), wird diese Adresse als `stufe="offen"`,
    `grund="fehler"` mit einer kurzen Fehlermeldung in `display_name` markiert; der
    Lauf wird nicht abgebrochen. Da fehlgeschlagene Anfragen nie in den Cache
    geschrieben werden, holt ein erneuter Lauf sie automatisch nach.
    """
    gruppen: dict[tuple, int] = {}
    for z in zeilen:
        k = tuple(z[f] for f in ADRESSSCHLUESSEL)
        gruppen[k] = gruppen.get(k, 0) + 1
    schluessel = sorted(gruppen, key=lambda k: -gruppen[k])

    def arbeit(k: tuple) -> tuple[tuple, Verortung]:
        d = dict(zip(ADRESSSCHLUESSEL, k))
        try:
            return k, geokodiere(client, d["strasse_heute"], d["hausnr"], d["hausnr_zusatz"], d["stadtteil"],
                                 d["parse_status"], d["strasse_roh"], landmarken)
        except requests.RequestException as e:
            return k, Verortung(stufe="offen", grund="fehler", display_name=str(e)[:120])

    ergebnis: dict[tuple, Verortung] = {}
    with ThreadPoolExecutor(max_workers=threads) as ex:
        for k, v in ex.map(arbeit, schluessel):
            ergebnis[k] = v
    out = []
    for z in zeilen:
        v = ergebnis[tuple(z[f] for f in ADRESSSCHLUESSEL)]
        d = dict(z)
        d.update(asdict(v))
        out.append(d)
    adressen = []
    for k in schluessel:
        a = dict(zip(ADRESSSCHLUESSEL, k))
        a["zeilen"] = str(gruppen[k])
        a.update(asdict(ergebnis[k]))
        adressen.append(a)
    return out, adressen
