"""Seitenzuordnung des Faksimiles aus der METS-Datei der DigiBib (CompGen).

    python3 werkzeuge/faksimile_mets.py [--neu]

Liest https://www.digibib.genealogy.net/viewer/sourcefile?id=857439804_1936 und schreibt
kuratierung/faksimile_seiten.csv (seite, bild, etikett): je gedruckter Seite (z. B. I-333) die
Bildnummer im Viewer (355). Seiten ohne Bild (im Digitalisat fehlen II-170 und II-171) stehen nicht
in der Tabelle; die Karte zeigt dann „im Digitalisat nicht vorhanden“ statt eines falschen Links.
"""
from __future__ import annotations

import pathlib
import re
import sys
import xml.etree.ElementTree as ET

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.io import projektwurzel, schreib_csv

WERK = "857439804_1936"
QUELLE = f"https://www.digibib.genealogy.net/viewer/sourcefile?id={WERK}"
FELDER = ["seite", "bild", "etikett"]
_NS = {"mets": "http://www.loc.gov/METS/"}
_ETIKETT = re.compile(r"^(I|II|III|IV)\. Teil:\s*(\d+)$")


def parse_seiten(mets_xml: str) -> list[dict]:
    """Bildnummer je gedruckter Seite aus der physischen Struktur (ORDERLABEL „I. Teil: 333“)."""
    wurzel = ET.fromstring(mets_xml)
    phys = wurzel.find('.//mets:structMap[@TYPE="PHYSICAL"]', _NS)
    if phys is None:
        raise ValueError("keine physische structMap in der METS-Datei")
    zeilen = []
    for div in phys.findall('.//mets:div[@TYPE="page"]', _NS):
        etikett = (div.get("ORDERLABEL") or "").strip()
        m = _ETIKETT.match(etikett)
        if not m:
            continue
        zeilen.append(dict(seite=f"{m.group(1)}-{int(m.group(2)):03d}", bild=int(div.get("ORDER")), etikett=etikett))
    doppelt = {z["seite"] for z in zeilen if sum(1 for y in zeilen if y["seite"] == z["seite"]) > 1}
    if doppelt:
        raise ValueError(f"mehrdeutige Seiten in der METS-Datei: {sorted(doppelt)[:5]}")
    return sorted(zeilen, key=lambda z: z["bild"])


def main() -> None:
    ziel = projektwurzel() / "kuratierung" / "faksimile_seiten.csv"
    if ziel.exists() and "--neu" not in sys.argv:
        sys.exit(f"{ziel} existiert, --neu zum Überschreiben")
    r = requests.get(QUELLE, headers={"User-Agent": "essener-adressbuch-1936 (Faksimile-Seiten)"}, timeout=60)
    r.raise_for_status()
    zeilen = parse_seiten(r.text)
    schreib_csv(ziel, zeilen, FELDER)
    print(f"{len(zeilen)} Seiten mit Bild → {ziel}")


if __name__ == "__main__":
    main()
