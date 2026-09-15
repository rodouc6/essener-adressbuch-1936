"""Zeilenweise Anwendung der Bibliotheksfunktionen (Stufen 02 und 03)."""
from __future__ import annotations

from dataclasses import asdict

from pipeline.lib.konkordanz import Strassenindex
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


AUFLOESUNGSFELDER = ["strasse_heute", "schl_nr", "stadtteil", "herkunft", "zeitlich_abweichend", "mehrdeutig", "kandidaten"]
PAARFELDER = ["strasse_norm", "vorort", "zeilen", "beispiel"] + AUFLOESUNGSFELDER
VORSCHLAGSFELDER = ["strasse_norm", "vorort", "zeilen", "beispiel"] + [
    f"{k}_{i}" for i in (1, 2, 3) for k in ("kandidat", "lemma", "aehnlichkeit")]


def loese_strassen(zeilen: list[dict], idx: Strassenindex) -> tuple[list[dict], list[dict], list[dict]]:
    """Löst je Zeile die Straße auf, baut die Paartabelle (strasse_norm, vorort) und eine Vorschlagsliste.

    Rückgabe: (Zeilen mit Auflösungsfeldern, Paartabelle nach Zeilenzahl absteigend,
    Vorschlagsliste für offene/mehrdeutige Paare nach Zeilenzahl absteigend).
    """
    paare: dict[tuple[str, str], dict] = {}
    for z in zeilen:
        k = (z["strasse_norm"], z["Vorort"])
        if k not in paare:
            a = idx.aufloesen(*k) if k[0] else None
            paare[k] = {"strasse_norm": k[0], "vorort": k[1], "zeilen": 0, "beispiel": z["Adresse"],
                        **({f: "" for f in AUFLOESUNGSFELDER} | ({"herkunft": "offen"} if a is None else asdict(a)))}
        paare[k]["zeilen"] += 1
    out = []
    for z in zeilen:
        p = paare[(z["strasse_norm"], z["Vorort"])]
        d = dict(z)
        d.update({f: p[f] for f in AUFLOESUNGSFELDER})
        out.append(d)
    vorschlaege = []
    for p in paare.values():
        if p["herkunft"] == "offen" or p["mehrdeutig"] == "ja":
            v = {f: p[f] for f in ("strasse_norm", "vorort", "zeilen", "beispiel")}
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
