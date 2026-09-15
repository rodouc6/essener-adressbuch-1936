"""Zieht Kontrollstichproben aus build/04_geokodiert.csv (Spec §6).

Aufruf:  python3 werkzeuge/stichprobe.py [seed]            → docs/stichprobe_<seed>.csv
         python3 werkzeuge/stichprobe.py gezielt <name>    → docs/stichprobe_<name>.csv
         python3 werkzeuge/stichprobe.py paare <name>      → docs/stichprobe_<name>.csv
                                                            aus docs/stichprobe_<name>_paare.csv

Zufallsstichprobe: 200 Adressen der Stufe `haus` und 100 der Stufe `strasse`, mit festem
Seed aus einer sortierten Grundmenge — derselbe Lauf ergibt dieselbe Stichprobe.

Gezielte Stichprobe (Runde 3, docs/entscheidungen_strassen.md): prüft nur die von den neuen
Regeln berührten Adressen — 40 mit angenommener Kernstadt (Teil II/III ohne Vorort), 40 aus
kuratierten Hausnummernbereichen, bevorzugt nahe den Bereichsgrenzen (±15 Nummern), 20 neu
erkannte Teilstrecken. Spalte `gruppe` nennt den Grund der Ziehung.

Paar-Stichprobe (Runde 4): prüft eine Liste von Straße-Paaren (Spalten `strasse_norm`,
`strasse_heute`, `zeilen`), etwa die von einer Regeländerung neu aufgelösten. Die 40 zeilenstärksten
Paare erhalten je eine Adresse (Gruppe `neu_gross`, bevorzugt Stufe haus), aus den übrigen kommen
20 zufällige Adressen (`neu_rest`). Geprüft wird damit die Straße, nicht die Hausnummer.

`urteil` und `bemerkung` bleiben leer und werden von Hand gefüllt (Vokabular: docs/stichprobe.md).
"""
from __future__ import annotations

import random
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv
from pipeline.lib.normalisierung import norm_strasse

FELDER = ["stufe", "strasse_roh", "hausnr", "hausnr_zusatz", "stadtteil", "strasse_heute",
          "display_name", "lat", "lon", "urteil", "bemerkung", "gruppe"]
UMFANG = {"haus": 200, "strasse": 100}
UMFANG_GEZIELT = {"kernstadt_angenommen": 40, "bereichsgrenze": 40, "teilstrecke_neu": 20}
UMFANG_PAARE = {"neu_gross": 40, "neu_rest": 20}
_STUFENRANG = {"haus": 0, "strasse": 1}
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


def ziehe_paare(adressen: list[dict], paare: list[dict], seed: int) -> list[dict]:
    """Zieht je eine Adresse für die zeilenstärksten Paare und zufällige Adressen aus dem Rest.

    Ein Paar ist (strasse_norm, strasse_heute); Adressen werden über norm_strasse(strasse_roh)
    und strasse_heute zugeordnet. Nur verortete Adressen, Stufe haus vor strasse.
    """
    rnd = random.Random(seed)
    je_paar: dict[tuple[str, str], list[dict]] = {}
    for a in adressen:
        if a.get("lat") and a.get("stufe") in _STUFENRANG:
            je_paar.setdefault((norm_strasse(a["strasse_roh"]), a["strasse_heute"]), []).append(a)
    zeilen: dict[tuple[str, str], int] = {}
    for z in paare:
        k = (z["strasse_norm"], z["strasse_heute"])
        zeilen[k] = zeilen.get(k, 0) + int(z["zeilen"])
    reihe = sorted((k for k in zeilen if k in je_paar), key=lambda k: (-zeilen[k], k))
    gross, rest = reihe[:UMFANG_PAARE["neu_gross"]], reihe[UMFANG_PAARE["neu_gross"]:]
    probe: list[dict] = []
    for k in gross:
        kandidaten = sorted(je_paar[k], key=lambda a: (_STUFENRANG[a["stufe"]], _SORT(a)))
        bestes = kandidaten[0]["stufe"]
        probe.append(_zeile(rnd.choice([a for a in kandidaten if a["stufe"] == bestes]), "neu_gross"))
    restmenge = [a for k in rest for a in je_paar[k]]
    probe += [_zeile(a, "neu_rest") for a in _wahl(restmenge, UMFANG_PAARE["neu_rest"], rnd)]
    for g in UMFANG_PAARE:
        print(f"{g}: {sum(1 for p in probe if p['gruppe'] == g)} gezogen")
    return probe


def main(argv: list[str]) -> None:
    W = projektwurzel()
    adressen = lies_csv(W / "build" / "04_geokodiert.csv")
    if argv[:1] == ["gezielt"]:
        name = argv[1] if len(argv) > 1 else "r3"
        grenzen = grenzen_aus_zuordnung(lies_csv(W / "kuratierung" / "strassen_zuordnung.csv"))
        probe = ziehe_gezielt(adressen, grenzen, TEILSTRECKEN_NEU, seed=2026)
    elif argv[:1] == ["paare"]:
        name = argv[1] if len(argv) > 1 else "r4"
        paare = lies_csv(W / "docs" / f"stichprobe_{name}_paare.csv")
        probe = ziehe_paare(adressen, paare, seed=2026)
    else:
        name = argv[0] if argv else "2026"
        probe = ziehe(adressen, int(name))
    ziel = W / "docs" / f"stichprobe_{name}.csv"
    schreib_csv(ziel, probe, FELDER)
    print(f"geschrieben: {ziel.relative_to(W)} ({len(probe)} Zeilen)")


if __name__ == "__main__":
    main(sys.argv[1:])
