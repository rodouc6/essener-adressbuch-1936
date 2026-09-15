"""Stufe 05: Kennzahlen als Markdown und eine Kontrollstichprobe als GeoJSON."""
from __future__ import annotations

import random
from collections import Counter


def _pz(n: int, g: int) -> str:
    return f"{(n / g * 100 if g else 0):.1f}".replace(".", ",")


def _tabelle(titel: str, zaehler: Counter, gesamt: int) -> list[str]:
    z = [f"### {titel}", "", "| Wert | Zeilen | Anteil |", "|---|---:|---:|"]
    for k, v in zaehler.most_common():
        z.append(f"| {k} | {v} | {_pz(v, gesamt)} % |")
    return z + [""]


def erzeuge(eintraege, adressen, strassen, dubletten, ausgeschlossen, vorschlaege) -> tuple[str, dict]:
    g = len(eintraege)
    md = ["# Bericht Datenpipeline", "", f"Einträge (Teile I–III, ohne Dubletten): {g}",
          f"Ausgeschlossen: {len(ausgeschlossen)} — " + ", ".join(f"{k}: {v}" for k, v in Counter(x['grund'] for x in ausgeschlossen).items()),
          f"Dubletten: {len(dubletten)}", f"Eindeutige Adressen: {len(adressen)}",
          f"Offene/mehrdeutige Straßen in Vorschlagsliste: {len(vorschlaege)}", ""]
    md += _tabelle("Präzisionsstufe", Counter(e["stufe"] for e in eintraege), g)
    md += _tabelle("Gründe (nur offen)", Counter(e["grund"] for e in eintraege if e["stufe"] == "offen"), g)
    md += _tabelle("Herkunft der Straßenauflösung", Counter(e["herkunft"] for e in eintraege), g)
    md += _tabelle("Parse-Status", Counter(e["parse_status"] for e in eintraege), g)
    for teil in ("I", "II", "III"):
        sub = [e for e in eintraege if e["teil"] == teil]
        md += _tabelle(f"Präzisionsstufe Teil {teil} ({len(sub)} Zeilen)", Counter(e["stufe"] for e in sub), len(sub))
    offen = sorted((a for a in adressen if a["stufe"] == "offen"), key=lambda a: -int(a["zeilen"]))[:50]
    md += ["### Top 50 offene Adressen", "", "| Zeilen | Adresse | Stadtteil | Grund |", "|---:|---|---|---|"]
    md += [f"| {a['zeilen']} | {a['strasse_roh']} {a['hausnr']}{a['hausnr_zusatz']} | {a['stadtteil']} | {a['grund']} |" for a in offen]
    md.append("")
    verortet = [a for a in adressen if a["lat"]]
    random.seed(1936)
    probe = random.sample(verortet, min(2000, len(verortet)))
    geo = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(a["lon"]), float(a["lat"])]},
         "properties": {"stufe": a["stufe"], "herkunft": a.get("herkunft", ""),
                        "adresse": f"{a['strasse_roh']} {a['hausnr']}{a['hausnr_zusatz']}".strip(),
                        "stadtteil": a["stadtteil"], "display_name": a["display_name"], "zeilen": a["zeilen"]}}
        for a in probe]}
    return "\n".join(md), geo
