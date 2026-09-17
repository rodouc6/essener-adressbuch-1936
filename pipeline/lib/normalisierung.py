"""Normalisierung von Straßennamen, Vororten (Buch 1936) und Stadtteilen (Dickhoff/OSM)."""
from __future__ import annotations

import re
import unicodedata

VORORTE: tuple[str, ...] = (
    "Frillendorf", "Heidhausen", "Heisingen", "Karnap", "Katernberg", "Kray",
    "Kupferdreh", "Schonnebeck", "Steele", "Stoppenberg", "Ueberruhr", "Werden",
)
_VORORT_ALIAS = {v.lower(): v for v in VORORTE}
_VORORT_ALIAS.update({"überruhr": "Ueberruhr", "ueberruhr": "Ueberruhr"})

# Geschützte Leerzeichen (NBSP, schmales NBSP, Ziffern-Leerzeichen) auf das normale
# Leerzeichen, typografische Apostrophe und Gedankenstriche auf ASCII.
_TYPO = str.maketrans({"´": "'", "’": "'", "`": "'", "\u00a0": " ", "\u202f": " ",
                       "\u2007": " ", "–": "-", "—": "-"})

_ERSETZUNGEN = [
    (re.compile(r"\bstr\.(?=\s|$)"), "straße"),          # "Bochumer str." → "bochumer straße"
    (re.compile(r"(?<=[a-zäöüß\-])str\.(?=\s|$)"), "straße"),  # "karlstr." → "karlstraße"
    (re.compile(r"(?<=[a-zäöüß])str$"), "straße"),       # "Luisenstr" → "luisenstraße" (ohne Punkt)
    (re.compile(r"\bstr$"), "straße"),                   # "Bochumer Str" → "bochumer straße" (ohne Punkt)
    (re.compile(r"strasse\b"), "straße"),
    (re.compile(r"\bpl\.(?=\s|$)"), "platz"),
    (re.compile(r"(?<=[a-zäöüß\-])pl\.(?=\s|$)"), "platz"),
    (re.compile(r"^kl\.\s+"), "kleine "),
    (re.compile(r"^gr\.\s+"), "große "),
]


def norm_strasse(text: str) -> str:
    """Normalisiert einen Straßennamen: klein geschrieben, Abkürzungen ausgeschrieben, Einzelleerzeichen."""
    s = unicodedata.normalize("NFC", text).translate(_TYPO).strip().lower()
    s = re.sub(r"\s+", " ", s)
    for muster, ersatz in _ERSETZUNGEN:
        s = muster.sub(ersatz, s)
    return s.strip()


def norm_vorort(text: str) -> tuple[str, bool]:
    """Normalisiert einen Vorort-Namen auf den kanonischen Namen aus VORORTE.

    Gibt (kanonischer Name, True) zurück, wenn der Name erkannt wird,
    sonst (Originaltext, False).
    """
    t = unicodedata.normalize("NFC", text).strip()
    if not t:
        return "", True
    kanon = _VORORT_ALIAS.get(t.lower())
    if kanon is None:
        return t, False
    return kanon, True


_STADTTEIL_ALIAS = {
    "alten-essen-süd": "Altenessen-Süd",
    "ost-viertel": "Ostviertel",
    "brenedey": "Bredeney",
    "deltwig": "Dellwig",
    "geschede": "Gerschede",
    # „Schönebeck“ ist ein eigener Stadtteil im Westen (bei Borbeck, 1936 Kernstadt) und darf NICHT auf den
    # Vorort Schonnebeck im Nordosten abgebildet werden (Fehler bis 2026-09-17). Dickhoffs „Schönnebeck“ (ö + nn)
    # kommt genau einmal vor (01370 Hopfenstraße) und liegt laut OSM in Schönebeck.
    "schönnebeck": "Schönebeck",
    "margarethenhöhe": "Margaretenhöhe",
    "stoppen- berg": "Stoppenberg",
    "stoppen-berg": "Stoppenberg",
    "kettwig vor der brücke": "Kettwig",
}


def norm_stadtteil(text: str) -> str:
    """Normalisiert einen Stadtteil-Namen: bekannte Schreibvarianten/Tippfehler korrigiert, Trennstriche bereinigt."""
    t = unicodedata.normalize("NFC", text).translate(_TYPO).strip()
    t = re.sub(r"\s+", " ", t)
    alias = _STADTTEIL_ALIAS.get(t.lower())
    if alias:
        return alias
    return t.replace("- ", "")


# --- Schlüsselformen für Schreibvarianten (Runde 5) ---------------------------------
# Jede Stufe ist strenger als die vorige und wirft mehr Unterschiede weg. Zwei Namen gelten
# als Schreibvarianten, wenn sie auf irgendeiner Stufe denselben Schlüssel haben — der
# Straßenindex nutzt das nur, wenn der Name sonst keinen Kandidaten hat, und nur bei
# genau einem Dickhoff-Namen mit gleichem Schlüssel. Stufen: 0 ß/ss · 1 Leerzeichen,
# Bindestrich, Punkt, Apostroph · 2 ck/k, th/t, dt/t, ph/f, c/k, y/i, ie/i · 3 Umlaut-
# Umschrift, ei/ey/ai · 4 Endung -ener/-er, Genitiv-s, Doppelbuchstaben.
def _k0(s: str) -> str:
    return s.replace("ß", "ss")


def _k1(s: str) -> str:
    return re.sub(r"[\s\-\.']", "", _k0(s))


def _k2(s: str) -> str:
    s = _k1(s)
    for a, b in (("ck", "k"), ("th", "t"), ("dt", "t"), ("ph", "f"), ("c", "k"), ("y", "i"), ("ie", "i")):
        s = s.replace(a, b)
    return s


def _k3(s: str) -> str:
    s = _k2(s)
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ae", "e"), ("oe", "o"), ("ue", "u"),
                 ("ey", "ai"), ("ei", "ai")):
        s = s.replace(a, b)
    return s


def _k4(s: str) -> str:
    s = _k3(s)
    s = re.sub(r"enerstrasse$", "erstrasse", s)      # heidhausener → heidhauser
    s = re.sub(r"s(strasse|weg|platz|berg|kamp|hof)$", r"\1", s)  # einigkeitsstraße → einigkeitstraße
    return re.sub(r"([a-z])\1", r"\1", s)            # schederhoff → schederhof


SCHLUESSELSTUFEN = (_k0, _k1, _k2, _k3, _k4)


def schluesselformen(name_norm: str) -> list[str]:
    """Schlüsselformen eines normalisierten Namens, je Stufe eine (siehe SCHLUESSELSTUFEN)."""
    return [f(name_norm) for f in SCHLUESSELSTUFEN]
