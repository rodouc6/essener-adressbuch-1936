"""Stadtplan Essen 1935 (geo.essen.de) in 1,5-km-Kacheln (1500 px, 1 m/px) exportieren.

    python3 werkzeuge/stadtplan_kacheln.py ZIELORDNER

Schreibt ZIELORDNER/k_<reihe>_<spalte>.png (Reihe 0 = Süden, Spalte 0 = Westen) und
ZIELORDNER/kacheln_index.csv (Kachel, Bounding-Box in EPSG:4647). Leere Kacheln (Randbereiche ohne
Karteninhalt) werden entfernt. Grundlage für die Lesung der Zechen-Beschriftungen in
kuratierung/stadtplan_1935_zechen.csv: Dort ist je Fund die Kachel-Box (UTM32, ohne Zonen-Präfix)
und die Pixelposition vermerkt; lat/lon = Box-Ecke oben links + Pixel (1 px = 1 m), nach WGS84.

Die Kacheln selbst liegen nicht im Repository (Nutzungsrechte des Plans, s. README).
"""
from __future__ import annotations

import concurrent.futures as cf
import csv
import pathlib
import sys

import requests
from PIL import Image, ImageStat

URL = "https://geo.essen.de/arcgis/rest/services/historischerverein/Stadtplan_1935/MapServer/export"
# fullExtent des Dienstes (EPSG:4647 = ETRS89/UTM32 mit Zonen-Präfix 32)
X0, Y0, X1, Y1 = 32352678, 5688368, 32372038, 5713092
K = 1500  # Kachelkante in Metern und Pixeln (1 m/px)
LEER_STDDEV = 5  # Grauwert-Streuung, unter der eine Kachel als leer gilt


def _hole(ziel: pathlib.Path, xs: list[int], ys: list[int], ix: int, iy: int) -> dict:
    x, y = xs[ix], ys[iy]
    p = ziel / f"k_{iy:02d}_{ix:02d}.png"
    if not p.exists():
        r = requests.get(URL, params=dict(bbox=f"{x},{y},{x+K},{y+K}", bboxSR=4647, imageSR=4647,
                                          size=f"{K},{K}", format="png", f="image"),
                         headers={"User-Agent": "essener-adressbuch-1936 (Stadtplan-Kacheln)"}, timeout=180)
        r.raise_for_status()
        p.write_bytes(r.content)
    stddev = ImageStat.Stat(Image.open(p).convert("L")).stddev[0]
    return dict(kachel=p.name, xmin=x, ymin=y, xmax=x + K, ymax=y + K, stddev=round(stddev, 1))


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ziel = pathlib.Path(sys.argv[1])
    ziel.mkdir(parents=True, exist_ok=True)
    xs, ys = list(range(X0, X1, K)), list(range(Y0, Y1, K))
    paare = [(ix, iy) for iy in range(len(ys)) for ix in range(len(xs))]
    with cf.ThreadPoolExecutor(3) as ex:  # höflich gegenüber dem Dienst
        zeilen = list(ex.map(lambda t: _hole(ziel, xs, ys, *t), paare))
    leer = [z for z in zeilen if z["stddev"] < LEER_STDDEV]
    for z in leer:
        (ziel / z["kachel"]).unlink()
    voll = [z for z in zeilen if z["stddev"] >= LEER_STDDEV]
    with open(ziel / "kacheln_index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(voll[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(voll)
    print(f"{len(zeilen)} Kacheln, {len(leer)} leer entfernt, {len(voll)} behalten → {ziel}")


if __name__ == "__main__":
    main()
