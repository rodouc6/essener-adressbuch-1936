"""Zieht Kontrollstichproben aus build/04_geokodiert.csv (Spec §6).

Aufruf:  python3 werkzeuge/stichprobe.py [seed]            → docs/stichprobe_<seed>.csv
         python3 werkzeuge/stichprobe.py gezielt <name>    → docs/stichprobe_<name>.csv

Zufallsstichprobe: 200 Adressen der Stufe `haus` und 100 der Stufe `strasse`, mit festem
Seed aus einer sortierten Grundmenge — derselbe Lauf ergibt dieselbe Stichprobe.

Gezielte Stichprobe (Runde 3, docs/entscheidungen_strassen.md): prüft nur die von den neuen
Regeln berührten Adressen — 40 mit angenommener Kernstadt (Teil II/III ohne Vorort), 40 aus
kuratierten Hausnummernbereichen, bevorzugt nahe den Bereichsgrenzen (±15 Nummern), 20 neu
erkannte Teilstrecken. Spalte `gruppe` nennt den Grund der Ziehung.

`urteil` und `bemerkung` bleiben leer und werden von Hand gefüllt (Vokabular: docs/stichprobe.md).
"""
from __future__ import annotations

import random
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv

FELDER = ["stufe", "strasse_roh", "hausnr", "hausnr_zusatz", "stadtteil", "strasse_heute",
          "display_name", "lat", "lon", "urteil", "bemerkung", "gruppe"]
UMFANG = {"haus": 200, "strasse": 100}
UMFANG_GEZIELT = {"kernstadt_angenommen": 40, "bereichsgrenze": 40, "teilstrecke_neu": 20}
GRENZSTREIFEN = 15
# Teilstrecken, die erst durch die OCR-Korrekturen vom 2026-09-15 erkannt werden (essener-strassen v1.0.1).
TEILSTRECKEN_NEU = ["Beuststraße", "Walpurgisstraße", "II. Hagen"]

_SORT = lambda a: (a["strasse_heute"], a["hausnr"], a["hausnr_zusatz"], a["strasse_roh"])


def _zeile(a: dict, gruppe: str = "") -> dict:
    return {**{f: a.get(f, "") for f in FELDER}, "urteil": "", "bemerkung": "", "gruppe": gruppe}


def _wahl(menge: list[dict], n: int, rnd: random.Random) -> list[dict]:
    menge = sorted(menge, key=_SORT)
    return rnd.sample(menge, min(n, len(menge)))


def ziehe(adressen: list[dict], seed: int) -> list[dict]:
    probe = []
    for stufe, n in UMFANG.items():
        grundmenge = [a for a in adressen if a["stufe"] == stufe]
        rnd = random.Random(seed)
        gezogen = _wahl(grundmenge, n, rnd)
        probe += [_zeile(a) for a in gezogen]
        print(f"{stufe}: {len(gezogen)} von {len(grundmenge)} gezogen")
    return probe


def grenzen_aus_zuordnung(zuordnung: list[dict]) -> dict[str, set[int]]:
    """Bereichsgrenzen je heutiger Straße: jede gesetzte Unter- oder Obergrenze der Kuratierung
    (außer der Untergrenze 1, die nur den Beginn der Zählung markiert)."""
    grenzen: dict[str, set[int]] = {}
    for z in zuordnung:
        for f in ("hausnr_von", "hausnr_bis"):
            if z.get(f, "").strip().isdigit() and int(z[f]) > 1:
                grenzen.setdefault(z["strasse_heute"], set()).add(int(z[f]))
    return grenzen


def _grenznah(a: dict, grenzen: dict[str, set[int]]) -> bool:
    if not a["hausnr"].isdigit():
        return False
    return any(abs(int(a["hausnr"]) - g) <= GRENZSTREIFEN for g in grenzen.get(a["strasse_heute"], ()))


def ziehe_gezielt(adressen: list[dict], grenzen: dict[str, set[int]], teilstrecken_neu: list[str],
                  seed: int) -> list[dict]:
    haus = [a for a in adressen if a["stufe"] == "haus"]
    rnd = random.Random(seed)
    probe: list[dict] = []

    kern = [a for a in haus if a.get("vorort_angenommen") == "ja"]
    probe += [_zeile(a, "kernstadt_angenommen") for a in _wahl(kern, UMFANG_GEZIELT["kernstadt_angenommen"], rnd)]

    kuratiert = [a for a in haus if a.get("herkunft") == "kuratiert"]
    nahe = [a for a in kuratiert if _grenznah(a, grenzen)]
    fern = [a for a in kuratiert if not _grenznah(a, grenzen)]
    n = UMFANG_GEZIELT["bereichsgrenze"]
    gezogen = _wahl(nahe, n, rnd)
    gezogen += _wahl(fern, n - len(gezogen), rnd)
    probe += [_zeile(a, "bereichsgrenze") for a in gezogen]

    teil = [a for a in haus if a.get("teilstrecke_abgetrennt") == "ja" and a["strasse_heute"] in teilstrecken_neu]
    probe += [_zeile(a, "teilstrecke_neu") for a in _wahl(teil, UMFANG_GEZIELT["teilstrecke_neu"], rnd)]
    for g in UMFANG_GEZIELT:
        print(f"{g}: {sum(1 for p in probe if p['gruppe'] == g)} gezogen")
    return probe


def main(argv: list[str]) -> None:
    W = projektwurzel()
    adressen = lies_csv(W / "build" / "04_geokodiert.csv")
    if argv[:1] == ["gezielt"]:
        name = argv[1] if len(argv) > 1 else "r3"
        grenzen = grenzen_aus_zuordnung(lies_csv(W / "kuratierung" / "strassen_zuordnung.csv"))
        probe = ziehe_gezielt(adressen, grenzen, TEILSTRECKEN_NEU, seed=2026)
    else:
        name = argv[0] if argv else "2026"
        probe = ziehe(adressen, int(name))
    ziel = W / "docs" / f"stichprobe_{name}.csv"
    schreib_csv(ziel, probe, FELDER)
    print(f"geschrieben: {ziel.relative_to(W)} ({len(probe)} Zeilen)")


if __name__ == "__main__":
    main(sys.argv[1:])
