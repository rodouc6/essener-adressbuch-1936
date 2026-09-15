"""Stufe 05: Kennzahlen als Markdown und eine Kontrollstichprobe als GeoJSON."""
from __future__ import annotations

import random
from collections import Counter

from pipeline.lib.konkordanz import VORORT_STADTTEILE


def _pz(n: int, g: int) -> str:
    return f"{(n / g * 100 if g else 0):.1f}".replace(".", ",")


def _tabelle(titel: str, zaehler: Counter, gesamt: int) -> list[str]:
    z = [f"### {titel}", "", "| Wert | Zeilen | Anteil |", "|---|---:|---:|"]
    for k, v in zaehler.most_common():
        z.append(f"| {k} | {v} | {_pz(v, gesamt)} % |")
    return z + [""]


def _vorort_tabelle() -> list[str]:
    """Gibt die Prüftabelle Vorort (Buch 1936) → heutige Stadtteile aus (Spec §5.03)."""
    z = ["### Vorort → heutige Stadtteile (Prüfkriterium, kein Beleg)", "",
         "| Vorort | heutige Stadtteile |", "|---|---|"]
    for vorort, stadtteile in sorted(VORORT_STADTTEILE.items()):
        z.append(f"| {vorort} | {'; '.join(sorted(stadtteile))} |")
    return z + [""]


def erzeuge(eintraege, adressen, strassen, dubletten, ausgeschlossen, vorschlaege,
            zuordnung=(), statistik=None) -> tuple[str, dict]:
    """Baut den Markdown-Bericht und die Kontrollstichprobe als GeoJSON.

    `zuordnung` sind die Zeilen der kuratierten Straßenzuordnung (nur für die Größe),
    `statistik` die optionalen Laufzahlen aus Stufe 04 (build/04_statistik.json).
    """
    g = len(eintraege)
    md = ["# Bericht Datenpipeline", "", f"Einträge (Teile I–III, ohne Dubletten): {g}",
          f"Ausgeschlossen: {len(ausgeschlossen)} — " + ", ".join(f"{k}: {v}" for k, v in Counter(x['grund'] for x in ausgeschlossen).items()),
          f"Dubletten: {len(dubletten)}", f"Eindeutige Adressen: {len(adressen)}",
          f"Offene/mehrdeutige Straßen in Vorschlagsliste: {len(vorschlaege)}",
          f"Zuordnungstabelle: {len(zuordnung)} kuratierte Zeilen",
          f"Straße-Vorort-Teil-Paare: {len(strassen)}"]
    if statistik:
        anfragen = statistik.get("cache_anfragen", 0)
        md.append(f"Cache-Treffer: {statistik.get('cache_treffer', 0)} von {anfragen} Anfragen "
                  f"({_pz(statistik.get('cache_treffer', 0), anfragen)} %)")
    md.append("")
    md += _tabelle("Präzisionsstufe", Counter(e["stufe"] for e in eintraege), g)
    md += _tabelle("Gründe (nur offen)", Counter(e["grund"] for e in eintraege if e["stufe"] == "offen"), g)
    md += _tabelle("Herkunft der Straßenauflösung", Counter(e["herkunft"] for e in eintraege), g)
    md += _tabelle("Mehrdeutig", Counter(e["mehrdeutig"] for e in eintraege), g)
    md += _tabelle("Grund der Mehrdeutigkeit (nur mehrdeutig=ja)",
                   Counter(e["grund_mehrdeutig"] for e in eintraege if e["mehrdeutig"] == "ja"), g)
    md += _tabelle("Zeitlich abweichend", Counter(e["zeitlich_abweichend"] for e in eintraege), g)
    md += _tabelle("Teilstrecke abgetrennt", Counter(e["teilstrecke_abgetrennt"] for e in eintraege), g)
    md += _tabelle("Vorort angenommen (Teil II/III ohne Vorort, Kernstadt-Entscheid)",
                   Counter(e.get("vorort_angenommen", "nein") for e in eintraege), g)
    md += _tabelle("Nummer unsicher (kuratierter Bereich, nur Straßenebene)",
                   Counter(e.get("nummer_unsicher", "nein") for e in eintraege), g)
    md += _tabelle("Parse-Status", Counter(e["parse_status"] for e in eintraege), g)
    md += _vorort_tabelle()
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
