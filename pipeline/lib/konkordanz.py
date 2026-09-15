"""Straßenindex: löst normierte Straßennamen von 1936 auf heutige Straßen auf (Auflösungsleiter a–f)."""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path

from pipeline.lib.io import lies_csv
from pipeline.lib.normalisierung import norm_stadtteil, norm_strasse

FENSTER = ("1930-01-01", "1937-12-31")

# Vorort (Buch 1936, Stadtkreise vor 1929) → heutige Stadtteile (Dickhoff-Schreibweise).
# Grundlage: Eingemeindungen 1929; Zuordnung ist ein Prüfkriterium, kein Beleg. Bei Widerspruch
# wird nicht still aufgelöst, sondern mehrdeutig=ja gesetzt.
VORORT_STADTTEILE: dict[str, frozenset[str]] = {
    "Frillendorf": frozenset({"Frillendorf"}),
    "Heidhausen": frozenset({"Heidhausen", "Fischlaken"}),
    "Heisingen": frozenset({"Heisingen"}),
    "Karnap": frozenset({"Karnap"}),
    "Katernberg": frozenset({"Katernberg"}),
    "Kray": frozenset({"Kray", "Leithe"}),
    "Kupferdreh": frozenset({"Kupferdreh", "Byfang"}),
    "Schonnebeck": frozenset({"Schonnebeck"}),
    "Steele": frozenset({"Steele", "Freisenbruch", "Horst"}),
    "Stoppenberg": frozenset({"Stoppenberg"}),
    "Ueberruhr": frozenset({"Überruhr-Hinsel", "Überruhr-Holthausen"}),
    "Werden": frozenset({"Werden"}),
}


@dataclass(frozen=True)
class Aufloesung:
    """Ergebnis einer Straßenauflösung samt Herkunft auf der Auflösungsleiter."""

    strasse_heute: str
    schl_nr: str
    stadtteil: str
    herkunft: str
    zeitlich_abweichend: str = "nein"
    mehrdeutig: str = "nein"
    kandidaten: str = ""


OFFEN = Aufloesung("", "", "", "offen")


def _ohne_klammer(name: str) -> str:
    """Entfernt Klammerzusätze aus einem Namen, z. B. '(Umb.)'."""
    return re.sub(r"\s*\(.*?\)\s*", " ", name).strip()


class Strassenindex:
    """Löst normierte Straßennamen aus dem Adressbuch 1936 auf heutige Straßen auf.

    Auflösungsleiter (Priorität absteigend): kuratierte Zuordnung, heutiger Name,
    Konkordanz 1936, historisches Namensstadium, sonst offen.
    """

    def __init__(self, strassen_dir: Path, zuordnung_pfad: Path):
        self.strassen = {z["schl_nr"]: z for z in lies_csv(strassen_dir / "strassen.csv")}
        self.stadtteile = {s: [norm_stadtteil(t) for t in z["stadtteile"].split(";") if t.strip()]
                           for s, z in self.strassen.items()}
        self.heutig: dict[str, list[str]] = {}
        for s, z in self.strassen.items():
            self.heutig.setdefault(norm_strasse(z["lemma"]), []).append(s)
        self.konk: dict[str, list[dict]] = {}
        for z in lies_csv(strassen_dir / "konkordanz_1936.csv"):
            self.konk.setdefault(norm_strasse(z["ehemalig"]), []).append(z)
        namen = lies_csv(strassen_dir / "namen.csv")
        namen.sort(key=lambda z: (z["schl_nr"], int(z["stadium"])))
        self.stadien: dict[str, list[dict]] = {}
        for i, z in enumerate(namen):
            folge = namen[i + 1] if i + 1 < len(namen) and namen[i + 1]["schl_nr"] == z["schl_nr"] else None
            eintrag = dict(z, gueltig_bis=folge["gueltig_ab"] if folge else "9999")
            self.stadien.setdefault(norm_strasse(_ohne_klammer(z["name"])), []).append(eintrag)
        self.zuordnung: dict[tuple[str, str], dict] = {}
        if zuordnung_pfad.exists():
            for z in lies_csv(zuordnung_pfad):
                self.zuordnung[(norm_strasse(z["strasse_roh_norm"]), z["vorort"])] = z
        self._pool = sorted(set(self.stadien) | set(self.heutig))

    # --- Hilfen ---------------------------------------------------------------
    def _passt(self, schl_nr: str, vorort: str) -> bool:
        """Prüft, ob der Vorort mit den heutigen Stadtteilen des Kandidaten vereinbar ist."""
        if not vorort:
            return True
        erlaubt = VORORT_STADTTEILE.get(vorort, frozenset())
        return any(t in erlaubt for t in self.stadtteile.get(schl_nr, []))

    def _fertig(self, schl_nr: str, herkunft: str, zeitlich: str = "nein") -> Aufloesung:
        """Baut eine eindeutig aufgelöste Auflösung für einen bekannten Straßenschlüssel."""
        s = self.strassen[schl_nr]
        return Aufloesung(s["lemma"], schl_nr, "; ".join(self.stadtteile[schl_nr]), herkunft, zeitlich, "nein")

    def _entscheide(self, kandidaten: list[str], vorort: str, herkunft: str, zeitlich: str = "nein") -> Aufloesung:
        """Wählt unter mehreren Kandidaten anhand des Vororts aus; bei Widerspruch/Mehrdeutigkeit bleibt offen."""
        kandidaten = list(dict.fromkeys(kandidaten))
        passend = [s for s in kandidaten if self._passt(s, vorort)]
        if len(passend) == 1:
            return self._fertig(passend[0], herkunft, zeitlich)
        return Aufloesung("", "", "", herkunft, zeitlich, "ja", ";".join(kandidaten))

    # --- Leiter ---------------------------------------------------------------
    def aufloesen(self, strasse_norm: str, vorort: str) -> Aufloesung:
        """Löst einen normierten Straßennamen von 1936 samt Vorort auf die heutige Straße auf.

        strasse_norm wird zusätzlich durch norm_strasse geschickt (die Funktion ist
        idempotent), da die kuratierte Tabelle mit norm_strasse(...)-Schlüsseln geführt wird.
        """
        strasse_norm = norm_strasse(strasse_norm)
        # e) Kuratierung schlägt alles, weil vom Menschen belegt
        z = self.zuordnung.get((strasse_norm, vorort)) or self.zuordnung.get((strasse_norm, ""))
        if z:
            return Aufloesung(z["strasse_heute"], z["schl_nr"], "; ".join(self.stadtteile.get(z["schl_nr"], [])), "kuratiert")
        # a) heutiger Name
        if strasse_norm in self.heutig:
            return self._entscheide(self.heutig[strasse_norm], vorort, "heutig")
        # b/c) Konkordanz 1936
        if strasse_norm in self.konk:
            zeilen = self.konk[strasse_norm]
            eindeutig = [z for z in zeilen if z["eindeutig"] == "ja"]
            if eindeutig:
                return self._entscheide([z["schl_nr"] for z in eindeutig], vorort, "konkordanz")
            if vorort:
                return self._entscheide([z["schl_nr"] for z in zeilen], vorort, "konkordanz")
            return Aufloesung("", "", "", "konkordanz", "nein", "ja", ";".join(z["schl_nr"] for z in zeilen))
        # d) anderes Namensstadium
        if strasse_norm in self.stadien:
            st = self.stadien[strasse_norm]
            im_fenster = [z for z in st if z["gueltig_ab"][:10] <= FENSTER[1] and z["gueltig_bis"][:10] >= FENSTER[0]]
            if im_fenster:
                return self._entscheide([z["schl_nr"] for z in im_fenster], vorort, "stadium", "nein")
            return self._entscheide([z["schl_nr"] for z in st], vorort, "stadium", "ja")
        return OFFEN

    def vorschlaege(self, strasse_norm: str, n: int = 3) -> list[tuple[str, str, float]]:
        """Schlägt ähnliche Straßennamen vor (Name im Datensatz, heutiges Lemma, Ähnlichkeit)."""
        strasse_norm = norm_strasse(strasse_norm)
        out = []
        for kand in difflib.get_close_matches(strasse_norm, self._pool, n=n, cutoff=0.8):
            schl = (self.heutig.get(kand) or [z["schl_nr"] for z in self.stadien.get(kand, [])])[0]
            lemma = self.strassen.get(schl, {}).get("lemma", "")
            out.append((kand, lemma, round(difflib.SequenceMatcher(None, strasse_norm, kand).ratio(), 3)))
        return out
