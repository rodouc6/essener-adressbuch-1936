"""Straßenindex: löst normierte Straßennamen von 1936 als Kandidatenmengen auf heutige Straßen auf."""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path

from pipeline.lib.io import lies_csv
from pipeline.lib.normalisierung import norm_stadtteil, norm_strasse

# Zeitfenster, in dem ein Namensstadium für das Adreßbuch 1936 gelten muss.
FENSTER = ("1930-01-01", "1937-12-31")

# Kettwig und Burgaltendorf gehörten 1936 nicht zu Essen (Eingemeindung 1975).
# Kandidaten, deren Stadtteile vollständig hier liegen, können keine Adresse
# des Adreßbuchs 1936 sein und entfallen ausnahmslos.
NICHT_ESSEN_1936 = frozenset({"Kettwig", "Burgaltendorf"})

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

# Alle Stadtteile, die 1936 zu einem der zwölf Vororte gehörten. Ein Eintrag aus
# Teil I (Kernstadt) ohne Vorortangabe kann keiner dieser Stadtteile sein.
VORORT_STADTTEILE_ALLE: frozenset[str] = frozenset().union(*VORORT_STADTTEILE.values())

# Herkunftsquellen in absteigender Priorität: liefern mehrere Quellen denselben
# Straßenschlüssel, gewinnt die vorderste.
QUELLEN = ("heutig", "konkordanz", "stadium")

# Zeitstatus eines Kandidaten:
#   "fenster"    — ein datiertes Namensstadium deckt 1930–1937 ab
#   "undatiert"  — kein datiertes Stadium mit diesem Namen (Gültigkeit unbekannt)
#   "ausserhalb" — nur datierte Stadien außerhalb des Fensters (nur Rückfallkandidat)
ZEIT_FENSTER, ZEIT_UNDATIERT, ZEIT_AUSSERHALB = "fenster", "undatiert", "ausserhalb"


@dataclass(frozen=True)
class Kandidat:
    """Eine mögliche heutige Straße für einen Namen von 1936."""

    schl_nr: str
    quelle: str
    zeitlich: str
    konkordanz_eindeutig: str = ""

    @property
    def rang(self) -> int:
        return QUELLEN.index(self.quelle)


@dataclass(frozen=True)
class Aufloesung:
    """Ergebnis einer Straßenauflösung samt Herkunft und Mehrdeutigkeitsgrund."""

    strasse_heute: str
    schl_nr: str
    stadtteil: str
    herkunft: str
    zeitlich_abweichend: str = "nein"
    mehrdeutig: str = "nein"
    kandidaten: str = ""
    grund_mehrdeutig: str = ""


OFFEN = Aufloesung(strasse_heute="", schl_nr="", stadtteil="", herkunft="offen")


def _ohne_klammer(name: str) -> str:
    """Entfernt Klammerzusätze aus einem Namen, z. B. '(Umb.)'."""
    return re.sub(r"\s*\(.*?\)\s*", " ", name).strip()


def _schneidet_fenster(gueltig_ab: str, gueltig_bis: str) -> bool:
    """Prüft, ob [gueltig_ab, gueltig_bis) das Fenster 1930–1937 schneidet.

    Die Daten liegen in gemischter Präzision vor ("1900" neben "1933-07-13");
    der Vergleich als Zeichenkette ist dafür ausreichend, weil kürzere Angaben
    lexikographisch an der Jahresgrenze einsortieren.
    """
    return gueltig_ab[:10] <= FENSTER[1] and gueltig_bis[:10] >= FENSTER[0]


class Strassenindex:
    """Löst normierte Straßennamen aus dem Adreßbuch 1936 auf heutige Straßen auf.

    Modell (Spec §5.03): die kuratierte Zuordnung schlägt alles; sonst werden alle
    Kandidaten aus heutigem Lemma, Konkordanz 1936 und Namensstadien gesammelt,
    um Nicht-Essener Orte und um Vorort-Widersprüche gekürzt und nur dann
    aufgelöst, wenn genau ein Straßenschlüssel übrig bleibt. Unter mehreren
    passenden Kandidaten wird nie gewählt.
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
        self.stadien_je_strasse: dict[str, list[dict]] = {}
        for i, z in enumerate(namen):
            folge = namen[i + 1] if i + 1 < len(namen) and namen[i + 1]["schl_nr"] == z["schl_nr"] else None
            # Das letzte Stadium einer Straße ist offen; "9999" ist die obere Schranke.
            eintrag = dict(z, gueltig_bis=folge["gueltig_ab"] if folge else "9999",
                           name_norm=norm_strasse(_ohne_klammer(z["name"])))
            self.stadien.setdefault(eintrag["name_norm"], []).append(eintrag)
            self.stadien_je_strasse.setdefault(z["schl_nr"], []).append(eintrag)
        self.zuordnung: dict[tuple[str, str], dict] = {}
        if zuordnung_pfad.exists():
            for z in lies_csv(zuordnung_pfad):
                self.zuordnung[(norm_strasse(z["strasse_roh_norm"]), z["vorort"])] = z
        self._pool = sorted(set(self.stadien) | set(self.heutig))

    # --- Kandidaten -----------------------------------------------------------
    def _nicht_essen_1936(self, schl_nr: str) -> bool:
        """Liegt die Straße vollständig in einem 1936 nicht Essener Ort?"""
        stadtteile = self.stadtteile.get(schl_nr, [])
        return bool(stadtteile) and set(stadtteile) <= NICHT_ESSEN_1936

    def _zeitstatus(self, schl_nr: str, name_norm: str) -> str:
        """Bestimmt, ob der Name für diese Straße 1936 galt (siehe ZEIT_*-Konstanten)."""
        stufen = [s for s in self.stadien_je_strasse.get(schl_nr, []) if s["name_norm"] == name_norm]
        datiert = [s for s in stufen if s["gueltig_ab"].strip()]
        if not datiert:
            # Keine datierte Gültigkeit bekannt: Kandidat bleibt gültig, aber gekennzeichnet.
            return ZEIT_UNDATIERT
        if any(_schneidet_fenster(s["gueltig_ab"], s["gueltig_bis"]) for s in datiert):
            return ZEIT_FENSTER
        return ZEIT_AUSSERHALB

    def _sammle(self, strasse_norm: str) -> list[Kandidat]:
        """Sammelt alle Kandidaten zu einem Namen von 1936 (ohne Nicht-Essener Orte)."""
        roh: list[Kandidat] = []
        for schl_nr in self.heutig.get(strasse_norm, []):
            roh.append(Kandidat(schl_nr, "heutig", self._zeitstatus(schl_nr, strasse_norm)))
        for z in self.konk.get(strasse_norm, []):
            # konkordanz_1936.csv ist bereits auf den Stichtag 1936-06-30 abgeleitet.
            roh.append(Kandidat(z["schl_nr"], "konkordanz", ZEIT_FENSTER, z["eindeutig"]))
        for s in self.stadien.get(strasse_norm, []):
            roh.append(Kandidat(s["schl_nr"], "stadium", self._zeitstatus(s["schl_nr"], strasse_norm)))
        return [k for k in roh if not self._nicht_essen_1936(k.schl_nr)]

    def _beste_je_schluessel(self, kandidaten: list[Kandidat]) -> dict[str, Kandidat]:
        """Fasst Kandidaten je Straßenschlüssel zusammen; die höchste Quelle gewinnt."""
        beste: dict[str, Kandidat] = {}
        for k in sorted(kandidaten, key=lambda k: k.rang):
            beste.setdefault(k.schl_nr, k)
        return beste

    # --- Filter ---------------------------------------------------------------
    def _passt(self, schl_nr: str, vorort: str, teil: str) -> bool:
        """Prüft, ob Vorort bzw. Teil mit den heutigen Stadtteilen des Kandidaten vereinbar sind.

        Ein 1936 nicht Essener Kandidat passt nie. Ein bekannter Vorort verlangt einen
        Stadtteil aus seiner Menge. Teil I ohne Vorort ist Kernstadt und verlangt einen
        Stadtteil außerhalb aller Vorort-Mengen. Teil II/III ohne Vorort und ein
        unbekannter Vorort sind keine Information und filtern nicht — ein fehlender
        Eintrag ist nie ein Widerspruch. Eine Straße ohne Stadtteilangabe passt immer.
        """
        if self._nicht_essen_1936(schl_nr):
            return False
        stadtteile = self.stadtteile.get(schl_nr, [])
        if not stadtteile:
            return True
        if vorort in VORORT_STADTTEILE:
            return any(t in VORORT_STADTTEILE[vorort] for t in stadtteile)
        if not vorort and teil == "I":
            return any(t not in VORORT_STADTTEILE_ALLE for t in stadtteile)
        return True

    # --- Ergebnisbau ----------------------------------------------------------
    def _fertig(self, kandidat: Kandidat) -> Aufloesung:
        """Baut die eindeutige Auflösung zu einem Kandidaten."""
        s = self.strassen[kandidat.schl_nr]
        return Aufloesung(
            strasse_heute=s["lemma"],
            schl_nr=kandidat.schl_nr,
            stadtteil="; ".join(self.stadtteile[kandidat.schl_nr]),
            herkunft=kandidat.quelle,
            zeitlich_abweichend="nein" if kandidat.zeitlich == ZEIT_FENSTER else "ja",
            mehrdeutig="nein",
        )

    def _mehrdeutig(self, kandidaten: dict[str, Kandidat], grund: str) -> Aufloesung:
        """Baut ein mehrdeutiges Ergebnis mit allen beteiligten Straßenschlüsseln."""
        beste = min(kandidaten.values(), key=lambda k: k.rang)
        return Aufloesung(
            strasse_heute="",
            schl_nr="",
            stadtteil="",
            herkunft=beste.quelle,
            zeitlich_abweichend="nein",
            mehrdeutig="ja",
            kandidaten=";".join(kandidaten),
            grund_mehrdeutig=grund,
        )

    # --- Auflösung ------------------------------------------------------------
    def aufloesen(self, strasse_norm: str, vorort: str, teil: str = "") -> Aufloesung:
        """Löst einen normierten Straßennamen von 1936 auf die heutige Straße auf.

        strasse_norm wird zusätzlich durch norm_strasse geschickt (die Funktion ist
        idempotent), da die kuratierte Tabelle mit norm_strasse(...)-Schlüsseln geführt wird.
        `teil` ist der Buchteil I/II/III; er unterscheidet die Kernstadt (I) von den
        Vorortbänden (II/III), in denen ein leerer Vorort keine Information ist.
        """
        strasse_norm = norm_strasse(strasse_norm)

        # 1. Kuratierung schlägt alles, weil vom Menschen belegt.
        z = self.zuordnung.get((strasse_norm, vorort)) or self.zuordnung.get((strasse_norm, ""))
        if z:
            return Aufloesung(strasse_heute=z["strasse_heute"], schl_nr=z["schl_nr"],
                              stadtteil="; ".join(self.stadtteile.get(z["schl_nr"], [])),
                              herkunft="kuratiert")

        # 2. Kandidaten sammeln.
        kandidaten = self._sammle(strasse_norm)
        if not kandidaten:
            return OFFEN

        # 3. Zeitlich belegte Kandidaten zuerst; nur wenn keiner übrig bleibt,
        #    kommen die außerhalb des Fensters datierten als Rückfall zum Zug.
        im_fenster = [k for k in kandidaten if k.zeitlich != ZEIT_AUSSERHALB]
        aktiv = im_fenster or kandidaten

        # 4. Vorort-Filter.
        passend = [k for k in aktiv if self._passt(k.schl_nr, vorort, teil)]
        if not passend:
            return self._mehrdeutig(self._beste_je_schluessel(aktiv), "vorort_widerspruch")

        # 5. Entscheidung: nur ein einziger Straßenschlüssel wird aufgelöst.
        beste = self._beste_je_schluessel(passend)
        if len(beste) == 1:
            return self._fertig(next(iter(beste.values())))
        nur_unklare_konkordanz = all(k.quelle == "konkordanz" and k.konkordanz_eindeutig == "nein"
                                     for k in beste.values())
        return self._mehrdeutig(beste, "konkordanz_nicht_eindeutig" if nur_unklare_konkordanz else "homonym_1936")

    def vorschlaege(self, strasse_norm: str, n: int = 3) -> list[tuple[str, str, float]]:
        """Schlägt ähnliche Straßennamen vor (Name im Datensatz, heutiges Lemma, Ähnlichkeit)."""
        strasse_norm = norm_strasse(strasse_norm)
        out = []
        for kand in difflib.get_close_matches(strasse_norm, self._pool, n=n, cutoff=0.8):
            schl = (self.heutig.get(kand) or [z["schl_nr"] for z in self.stadien.get(kand, [])])[0]
            lemma = self.strassen.get(schl, {}).get("lemma", "")
            out.append((kand, lemma, round(difflib.SequenceMatcher(None, strasse_norm, kand).ratio(), 3)))
        return out
