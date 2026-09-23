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
FELDER_KURATIERUNG = ["schreibweise", "art", "eigentuemer", "kategorie", "geprueft", "bearbeiter", "datum", "hinweis", "identitaet"]
# identitaet: leer = Identität des Eigentümers nicht belegbar (Personen mit Allerweltsnamen, nur Initialen);
# "sicher" = vom Bearbeiter bestätigt. Nur sichere Eigentümer erscheinen in Suche und Liste (Nachtrag 2026-09-23).
IDENTITAETEN = {"", "sicher"}
# Schreibweisen aus kuratierung/eigentuemer_stadtteil.csv (Körperschaften ohne Zusatz, z. B. „Kath. Kirchengem.“)
# werden je Stadtteil der Adresse als eigene Schreibweise „Kath. Kirchengem. ‹Katernberg›“ geführt, damit sie sich
# von Hand trennen und zuordnen lassen (Nachtrag 2026-09-23).
STADTTEIL_AUF, STADTTEIL_ZU = " ‹", "›"


def mit_stadtteil(schreibweise: str, e: dict) -> str:
    """Schreibweise um den Stadtteil der Adresse ergänzt: „Kath. Kirchengem. ‹Katernberg›“."""
    ort = (e.get("stadtteil") or e.get("Vorort") or "").strip() or "Stadtteil unbekannt"
    return f"{schreibweise}{STADTTEIL_AUF}{ort}{STADTTEIL_ZU}"


def schreibweise_von(e: dict, nach_stadtteil: set[str] | frozenset[str] = frozenset()) -> tuple[str, str]:
    """(Schreibweise, Art) eines Teil-II-Eintrags; Personen als „Nachname, Vorname“; Schreibweisen aus
    `nach_stadtteil` bekommen den Stadtteil angehängt."""
    firma = (e.get("Firmenname") or "").strip()
    if firma:
        return (mit_stadtteil(firma, e) if firma in nach_stadtteil else firma), "koerperschaft"
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


def lade_stadtteil_liste(zeilen: list[dict]) -> frozenset[str]:
    return frozenset((z.get("schreibweise") or "").strip() for z in zeilen if (z.get("schreibweise") or "").strip())


def identitaet_sicher(z: dict) -> bool:
    """Körperschaften gelten als identifiziert; Personen nur mit identitaet=sicher."""
    return z.get("art") != "person" or (z.get("identitaet") or "").strip() == "sicher"
