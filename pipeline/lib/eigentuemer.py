"""Gemeinsames für Eigentümer-Kuratierung (Teilprojekt 3): Kategorien, Schlüssel, Sperre.

Der Eigentümername steht in Teil II bei Körperschaften in `Firmenname`, bei Personen in
`lastname`/`firstname`; die Spalte `Eigentümer` trägt nur die Rolle (Spec §1).
"""
from __future__ import annotations

KATEGORIEN = {
    "stadt_staat": "Stadt/Staat/Reich",
    "bergbau": "Bergbau",
    "industrie": "Industrie",
    "genossenschaft_siedlung": "Genossenschaft/Siedlung",
    "kirche_stiftung": "Kirche/Stiftung",
    "bank_versicherung": "Bank/Versicherung",
    "privatperson": "Privatperson",
    "sonstige": "Sonstige",
}
AUTOMATIK = "eigentuemer_cluster"
FELDER_KURATIERUNG = ["schreibweise", "art", "eigentuemer", "kategorie", "geprueft", "bearbeiter", "datum", "hinweis"]


def schreibweise_von(e: dict) -> tuple[str, str]:
    """(Schreibweise, Art) eines Teil-II-Eintrags; Personen als „Nachname, Vorname"."""
    firma = (e.get("Firmenname") or "").strip()
    if firma:
        return firma, "koerperschaft"
    nach, vor = (e.get("lastname") or "").strip(), (e.get("firstname") or "").strip()
    if not nach:
        return "", ""
    return (f"{nach}, {vor}" if vor else nach), "person"


def lade_kuratierung(zeilen: list[dict]) -> dict[str, dict]:
    """kuratierung/eigentuemer.csv als Schreibweise → Zeile (Werte getrimmt)."""
    out: dict[str, dict] = {}
    for z in zeilen:
        z = {k: (v or "").strip() for k, v in z.items()}
        if z.get("schreibweise"):
            out[z["schreibweise"]] = z
    return out


def gesperrt(z: dict) -> bool:
    """Die Automatik darf eine Zeile nur überschreiben, wenn sie ungeprüft ist und zuletzt von ihr selbst stammt."""
    return z.get("geprueft") == "ja" or (z.get("bearbeiter") or AUTOMATIK) != AUTOMATIK
