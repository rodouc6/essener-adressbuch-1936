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
    "schönnebeck": "Schonnebeck",
    "schönebeck": "Schonnebeck",
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
