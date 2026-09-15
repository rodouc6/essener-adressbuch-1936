"""Zeilenweise Anwendung der Bibliotheksfunktionen (Stufen 02 und 03)."""
from __future__ import annotations

from dataclasses import asdict

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
