"""Zerlegt das Feld `Adresse` in Straße, Hausnummer, Zusatz, Lage."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_ROEMISCH = {"i": "I", "ii": "II", "iii": "III", "iv": "IV", "v": "V"}
_LAGE_WORT = re.compile(r"^(erdg|untg|erdgesch|erdgeschoss|untergeschoss|hochpt|parterre)\.?$", re.I)

# Ordinal- bzw. römisches Präfix ("1. Weberstr.", "II. Schichtstr."), das Teil
# des Straßennamens bleibt statt als Hausnummer-vor-Straße zu gelten.
_PRAEFIX = r"(?:I{1,3}|IV|\d+)\.\s"


@dataclass(frozen=True)
class Adresse:
    strasse_roh: str
    hausnr: str
    hausnr_zusatz: str
    hausnr_bis: str
    lage: str
    zusatz_frei: str
    status: str


def _leer(status: str, strasse: str = "", zusatz: str = "") -> Adresse:
    return Adresse(strasse, "", "", "", "", zusatz, status)


def parse_adresse(text: str) -> Adresse:
    """Zerlegt einen rohen Adresstext in Straße, Hausnummer, Zusatz und Lage.

    `text` wird NICHT normalisiert (keine Kleinschreibung o. Ä.) – nur
    Whitespace wird vereinheitlicht, damit die Regeln stabil greifen.
    """
    t = unicodedata.normalize("NFC", text or "")
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return _leer("leer")

    # Führt ein Ordnungswort ("II. Schichtstr.", "1. Weberstr.") die Straße
    # an, zählt die führende Ziffer nicht als Hausnummer-vor-Straße. Eine
    # führende Zahl ist nur dann unklar, wenn ihr kein ". " folgt.
    fuehrt_praefix = re.match(r"^(?:I{1,3}|IV|\d+)\.\s", t) is not None
    if re.match(r"^\d", t) and not fuehrt_praefix:
        return _leer("unklar", t)

    # Straße = alles vor der ersten "echten" Ziffer (Hausnummer), getrennt
    # durch Komma, Leerzeichen oder direkt angeklebt (ggf. mit einem
    # zusätzlichen OCR-Punkt); ein optionales "Nr." vor der Zahl wird
    # übersprungen. Der Straßenteil endet lazy, darf aber mit einem Punkt
    # enden (z. B. "Ludwigstr.9"). Liegt ein Ordinal-/römisches Präfix vor,
    # muss die Hauptregex es verpflichtend konsumieren – sonst würde die
    # führende Ziffer des Präfixes fälschlich als Hausnummer gelesen
    # ("1. Postneubau a. Hbf." darf nicht zu Hausnr. "1" werden).
    praefix = _PRAEFIX if fuehrt_praefix else ""
    m = re.match(
        rf"^(?P<strasse>{praefix}[^\d]*?\.?)(?:,\s*|\s*\.?\s*)(?:Nr\.\s*)?(?P<rest>\d.*)$",
        t,
    )
    if not m:
        # Keine Hausnummer vorhanden → Straße ohne Nummer; ein Zusatz nach
        # dem Komma wird als freier Zusatz übernommen.
        strasse, _, zusatz = t.partition(",")
        return _leer("ohne_nummer", strasse.strip(" ,"), zusatz.strip())

    strasse = m.group("strasse").strip(" ,")
    rest = m.group("rest")

    # Hausnummer + optionaler einzelner Buchstaben-Zusatz (z. B. "39D").
    hm = re.match(r"^(?P<nr>\d+)(?P<zus>[A-Za-z](?![a-zäöü]))?(?P<rest>.*)$", rest)
    hausnr = hm.group("nr")
    zusatz = (hm.group("zus") or "").lower()
    rest = hm.group("rest").strip()

    hausnr_bis = ""
    zusatz_frei_teile: list[str] = []
    lage = ""

    # Bereich, z. B. "-13" oder "-137A".
    bm = re.match(r"^-\s*(?P<bis>\d+\s?[A-Za-z]?)(?P<rest>.*)$", rest)
    if bm:
        hausnr_bis = bm.group("bis").replace(" ", "").lower()
        rest = bm.group("rest").strip()

    # Liste weiterer Hausnummern, z. B. ".15B.15C" oder ".3".
    lm = re.match(r"^\.(?P<liste>\S+)(?P<rest>.*)$", rest)
    if lm:
        zusatz_frei_teile.append(lm.group("liste"))
        rest = lm.group("rest").strip()

    for tok in rest.split():
        tl = tok.rstrip(".").lower()
        if tl in _ROEMISCH and not lage:
            lage = _ROEMISCH[tl]
        elif _LAGE_WORT.match(tok) and not lage:
            lage = tok if tok.endswith(".") else tok + "."
        else:
            zusatz_frei_teile.append(tok)

    zusatz_frei = " ".join(zusatz_frei_teile).strip(" ,")
    return Adresse(strasse, hausnr, zusatz, hausnr_bis, lage, zusatz_frei, "ok")
