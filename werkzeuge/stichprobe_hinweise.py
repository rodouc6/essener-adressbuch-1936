"""Erzeugt Prüfhinweise zur manuellen Stichprobe (Spec §6) für werkzeuge/pruefung.html.

Aufruf: python3 werkzeuge/stichprobe_hinweise.py [seed]

Liest docs/stichprobe_<seed>.csv, build/04_geokodiert.csv, build/03_strassen.csv und die
Straßendatenbank (essener-strassen) und schreibt build/stichprobe_hinweise.json: je
Stichprobenzeile (gleiche Reihenfolge) die Herkunft der Straßenauflösung, die OSM-Kennung,
ob die Hausnummer im Treffer vorkommt und die Dickhoff-Namensstadien aller beteiligten Straßen.
Die Stichproben-CSV selbst bleibt unverändert.
"""
from __future__ import annotations

import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.lib.io import lies_csv, projektwurzel, strassen_dir
from pipeline.lib.konkordanz import Strassenindex
from pipeline.lib.normalisierung import norm_strasse

GEO_FELDER = ("herkunft", "mehrdeutig", "grund_mehrdeutig", "teilstrecke_abgetrennt",
              "zeitlich_abweichend", "zusatz_ignoriert", "osm_type", "osm_id")
SCHLUESSEL = ("strasse_heute", "hausnr", "hausnr_zusatz", "stadtteil", "strasse_roh")


def nummer_getroffen(hausnr: str, zusatz: str, display_name: str) -> bool:
    """Kommt die Hausnummer samt Zusatz als eigener Bestandteil im Nominatim-Treffer vor?"""
    gesucht = (hausnr + zusatz).replace(" ", "").lower()
    return bool(gesucht) and any(t.strip().replace(" ", "").lower() == gesucht
                                 for t in display_name.split(","))


def namensstadien(idx: Strassenindex, schl_nr: str) -> list[dict]:
    """Namensstadien einer Straße in Stadiumsreihenfolge; offenes Ende als leere Angabe."""
    return [{"name": s["name"], "gueltig_ab": s["gueltig_ab"].strip(),
             "gueltig_bis": "" if s["gueltig_bis"] == "9999" else s["gueltig_bis"]}
            for s in idx.stadien_je_strasse.get(schl_nr, [])]


def hinweis(zeile: dict, geo: dict, schl_nrs: list[str], idx: Strassenindex) -> dict:
    """Bündelt die Prüfhinweise einer Stichprobenzeile."""
    strassen = []
    for s in schl_nrs:
        st = idx.strassen.get(s)
        if st:
            strassen.append({"schl_nr": s, "lemma": st["lemma"], "stadtteile": st["stadtteile"],
                             "stadien": namensstadien(idx, s)})
    h = {f: geo.get(f, "") for f in GEO_FELDER}
    h["nummer_getroffen"] = nummer_getroffen(zeile["hausnr"], zeile["hausnr_zusatz"], zeile["display_name"])
    h["strassen"] = strassen
    return h


def main(seed: int) -> None:
    W = projektwurzel()
    idx = Strassenindex(strassen_dir(), W / "kuratierung" / "strassen_zuordnung.csv")
    geo = {tuple(z[f] for f in SCHLUESSEL): z for z in lies_csv(W / "build" / "04_geokodiert.csv")}
    schl: dict[tuple[str, str], set[str]] = {}
    for z in lies_csv(W / "build" / "03_strassen.csv"):
        if z["schl_nr"]:
            schl.setdefault((z["strasse_norm"], z["strasse_heute"]), set()).add(z["schl_nr"])
    probe = lies_csv(W / "docs" / f"stichprobe_{seed}.csv")
    hinweise = []
    for zeile in probe:
        g = geo.get(tuple(zeile[f] for f in SCHLUESSEL), {})
        nrs = sorted(schl.get((norm_strasse(zeile["strasse_roh"]), zeile["strasse_heute"]), set()))
        hinweise.append(hinweis(zeile, g, nrs, idx))
    ziel = W / "build" / "stichprobe_hinweise.json"
    ziel.write_text(json.dumps(hinweise, ensure_ascii=False, indent=1), encoding="utf-8")
    ohne = sum(1 for h in hinweise if not h["strassen"])
    print(f"geschrieben: {ziel.relative_to(W)} ({len(hinweise)} Zeilen, {ohne} ohne Straßenschlüssel)")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2026)
