"""Straßenindex: löst normierte Straßennamen von 1936 als Kandidatenmengen auf heutige Straßen auf."""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, replace
from pathlib import Path

from pipeline.lib.io import lies_csv
from pipeline.lib.normalisierung import norm_stadtteil, norm_strasse

# Primäres Zeitfenster: das Namensstadium muss irgendwann im Erhebungsjahr 1936 gelten.
# Nur solche Stadien sind Homonyme (Spec §8.1, entschieden 2026-09-15).
FENSTER_1936 = ("1936-01-01", "1936-12-31")

# Weites Rückfallfenster: greift nur, wenn zu einem Namen kein Kandidat für 1936
# existiert. Solche Auflösungen werden mit zeitlich_abweichend=ja gekennzeichnet.
FENSTER = ("1930-01-01", "1937-12-31")

# Dickhoff kennzeichnet später abgetrennte Teilstrecken derselben Straße mit "(tlw.)"
# (z. B. "Frohnhauser Straße (tlw.)" → Am Richtenberg 1963). Solche Kandidaten sind
# keine Homonyme, sondern Stücke derselben Straße von 1936.
# Der Zusatz steht auch kombiniert („(tlw. Umb.)“, „(Umb. tlw.)“); entscheidend ist „tlw“ in der Klammer.
_TEILSTRECKE = re.compile(r"\([^)]*\btlw\.?[^)]*\)")

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

# Zeitstatus eines Kandidaten, in absteigender Güte:
#   "1936"       — ein Namensstadium gilt irgendwann 1936 (der Normalfall)
#   "undatiert"  — keine Datumsangabe zu diesem Namen, Gültigkeit unbekannt
#   "weit"       — gilt nur im Rückfallfenster 1930–1937, nicht 1936
#   "ausserhalb" — gilt auch dort nicht
# "1936" und "undatiert" bilden die erste Auswahlstufe; die beiden anderen kommen
# nur zum Zug, wenn die erste Stufe leer bleibt.
ZEIT_1936, ZEIT_UNDATIERT, ZEIT_WEIT, ZEIT_AUSSERHALB = "1936", "undatiert", "weit", "ausserhalb"
ZEIT_ERSTE_STUFE = (ZEIT_1936, ZEIT_UNDATIERT)


@dataclass(frozen=True)
class Kandidat:
    """Eine mögliche heutige Straße für einen Namen von 1936."""

    schl_nr: str
    quelle: str
    zeitlich: str
    konkordanz_eindeutig: str = ""
    teilstrecke: bool = False

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
    teilstrecke_abgetrennt: str = "nein"
    # "ja": Teil II/III ohne Vorort, Kernstadt nur angenommen (95 % belegt, Spec §5.03 Runde 3).
    vorort_angenommen: str = "nein"
    # "ja": kuratierter Hausnummernbereich, dessen Nummern heute nicht mehr gelten → nur Straßenebene.
    nummer_unsicher: str = "nein"


OFFEN = Aufloesung(strasse_heute="", schl_nr="", stadtteil="", herkunft="offen")


def _ohne_klammer(name: str) -> str:
    """Entfernt Klammerzusätze aus einem Namen, z. B. '(Umb.)'."""
    return re.sub(r"\s*\(.*?\)\s*", " ", name).strip()


def _schneidet(gueltig_ab: str, gueltig_bis: str, fenster: tuple[str, str]) -> bool:
    """Prüft, ob [gueltig_ab, gueltig_bis) das Fenster schneidet.

    Die Daten liegen in gemischter Präzision vor ("1900" neben "1933-07-13");
    der Vergleich als Zeichenkette ist dafür ausreichend, weil kürzere Angaben
    lexikographisch an der Jahresgrenze einsortieren. Ein unbekanntes Anfangsdatum
    wird als "0000" gelesen: bei bekanntem Ende (Nachfolgestadium) ist die
    Gültigkeit damit nach oben begrenzt und prüfbar.
    """
    return (gueltig_ab[:10] or "0000") <= fenster[1] and gueltig_bis[:10] >= fenster[0]


def _folgedatum(stufen: list[dict], i: int) -> str:
    """Ende der Gültigkeit von Stadium `i`: das Datum des ersten folgenden Stadiums.

    Die Stadiumsnummern in `namen.csv` sind nicht durchweg chronologisch (Viehofer
    Straße 03215: Stadium 5 = 1945, Stadium 6 = 1915). Übersprungen werden deshalb
    alle folgenden Stadien ohne Datum und alle, die vor dem eigenen Datum liegen —
    sonst entstehen leere oder falsch verkürzte Gültigkeiten. Gibt es kein
    Folgestadium, ist das Stadium offen ("9999" als obere Schranke).
    """
    eigen = stufen[i]["gueltig_ab"].strip()
    for spaeter in stufen[i + 1:]:
        datum = spaeter["gueltig_ab"].strip()
        if datum and datum[:10] >= eigen[:10]:
            return datum
    return "9999"


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
        je_strasse: dict[str, list[dict]] = {}
        for z in namen:
            je_strasse.setdefault(z["schl_nr"], []).append(z)
        self.stadien: dict[str, list[dict]] = {}
        self.stadien_je_strasse: dict[str, list[dict]] = {}
        for schl_nr, stufen in je_strasse.items():
            for i, z in enumerate(stufen):
                eintrag = dict(z, gueltig_bis=_folgedatum(stufen, i),
                               name_norm=norm_strasse(_ohne_klammer(z["name"])),
                               teilstrecke=bool(_TEILSTRECKE.search(z["name"])))
                self.stadien.setdefault(eintrag["name_norm"], []).append(eintrag)
                self.stadien_je_strasse.setdefault(schl_nr, []).append(eintrag)
        # Kuratierte Zuordnung: je (Name, Vorort) eine oder — bei Hausnummernbereichen — mehrere Zeilen.
        self.zuordnung: dict[tuple[str, str], list[dict]] = {}
        if zuordnung_pfad.exists():
            for z in lies_csv(zuordnung_pfad):
                self.zuordnung.setdefault((norm_strasse(z["strasse_roh_norm"]), z["vorort"]), []).append(z)
        self._pool = sorted(set(self.stadien) | set(self.heutig))

    # --- Kandidaten -----------------------------------------------------------
    def _nicht_essen_1936(self, schl_nr: str) -> bool:
        """Liegt die Straße vollständig in einem 1936 nicht Essener Ort?"""
        stadtteile = self.stadtteile.get(schl_nr, [])
        return bool(stadtteile) and set(stadtteile) <= NICHT_ESSEN_1936

    def _namensstadien(self, schl_nr: str, name_norm: str) -> list[dict]:
        """Alle Stadien dieser Straße, die den gesuchten Namen tragen."""
        return [s for s in self.stadien_je_strasse.get(schl_nr, []) if s["name_norm"] == name_norm]

    def _zeitstatus(self, schl_nr: str, name_norm: str) -> str:
        """Bestimmt, wie gut der Name für diese Straße 1936 belegt ist (ZEIT_*-Konstanten).

        Ein Stadium gilt als datiert, sobald eine der beiden Grenzen bekannt ist: ein
        Stadium ohne Anfangsdatum, aber mit Nachfolger (z. B. Nöggerathstraße 02266,
        "Frohnhauser Straße" bis 1911-04-21) ist für 1936 nachweislich ungültig.
        Undatiert heißt: keine der beiden Grenzen bekannt.
        """
        stufen = self._namensstadien(schl_nr, name_norm)
        datiert = [s for s in stufen if s["gueltig_ab"].strip() or s["gueltig_bis"] != "9999"]
        if any(_schneidet(s["gueltig_ab"], s["gueltig_bis"], FENSTER_1936) for s in datiert):
            return ZEIT_1936
        if len(datiert) < len(stufen) or not stufen:
            # Mindestens ein Stadium ohne jede Datumsangabe: Gültigkeit unbekannt.
            return ZEIT_UNDATIERT
        if any(_schneidet(s["gueltig_ab"], s["gueltig_bis"], FENSTER) for s in datiert):
            return ZEIT_WEIT
        return ZEIT_AUSSERHALB

    def _ist_teilstrecke(self, schl_nr: str, name_norm: str) -> bool:
        """Trägt der Name für diese Straße ausschließlich den Zusatz "(tlw.)"?"""
        stufen = self._namensstadien(schl_nr, name_norm)
        return bool(stufen) and all(s["teilstrecke"] for s in stufen)

    def _sammle(self, strasse_norm: str) -> list[Kandidat]:
        """Sammelt alle Kandidaten zu einem Namen von 1936 (ohne Nicht-Essener Orte)."""
        roh: list[Kandidat] = []
        for schl_nr in self.heutig.get(strasse_norm, []):
            # Das heutige Lemma trägt nie einen Teilstreckenzusatz.
            roh.append(Kandidat(schl_nr, "heutig", self._zeitstatus(schl_nr, strasse_norm)))
        for z in self.konk.get(strasse_norm, []):
            # konkordanz_1936.csv ist bereits auf den Stichtag 1936-06-30 abgeleitet.
            roh.append(Kandidat(z["schl_nr"], "konkordanz", ZEIT_1936, z["eindeutig"],
                                bool(_TEILSTRECKE.search(z.get("zusatz", "")))))
        for s in self.stadien.get(strasse_norm, []):
            roh.append(Kandidat(s["schl_nr"], "stadium", self._zeitstatus(s["schl_nr"], strasse_norm),
                                teilstrecke=self._ist_teilstrecke(s["schl_nr"], strasse_norm)))
        return [k for k in roh if not self._nicht_essen_1936(k.schl_nr)]

    def _beste_je_schluessel(self, kandidaten: list[Kandidat]) -> dict[str, Kandidat]:
        """Fasst Kandidaten je Straßenschlüssel zusammen; die höchste Quelle gewinnt.

        Teilstrecke ist nur, wer in *jeder* Quelle als Teilstrecke geführt wird —
        eine Quelle mit schlichtem Namen hebt die Kennzeichnung auf.
        """
        beste: dict[str, Kandidat] = {}
        for k in sorted(kandidaten, key=lambda k: k.rang):
            beste.setdefault(k.schl_nr, k)
        for schl_nr, k in beste.items():
            if k.teilstrecke and not all(a.teilstrecke for a in kandidaten if a.schl_nr == schl_nr):
                beste[schl_nr] = replace(k, teilstrecke=False)
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
            return self._kernstadt(stadtteile)
        return True

    @staticmethod
    def _kernstadt(stadtteile: list[str]) -> bool:
        """Liegt die Straße (auch) in der Kernstadt von 1936? Vorort- und Nicht-Essener Orte zählen nicht."""
        return any(t not in VORORT_STADTTEILE_ALLE and t not in NICHT_ESSEN_1936 for t in stadtteile)

    # --- Kuratierung ----------------------------------------------------------
    @staticmethod
    def _im_bereich(z: dict, hausnr: str) -> bool:
        """Passt die Hausnummer in den Bereich der Zuordnungszeile? Ohne Bereich passt alles."""
        von, bis = z.get("hausnr_von", "").strip(), z.get("hausnr_bis", "").strip()
        if not von and not bis:
            return True
        if not hausnr.strip().isdigit():
            return False
        n = int(hausnr)
        return (not von or n >= int(von)) and (not bis or n <= int(bis))

    def _kuratiert(self, strasse_norm: str, vorort: str, hausnr: str) -> dict | None:
        """Die kuratierte Zeile zu Name, Vorort und Hausnummer.

        Reihenfolge: Zeile mit genau diesem Vorort; bei leerem Vorort zusätzlich die Zeile
        mit vorort="Kernstadt" (gilt nur für Einträge ohne Vorort, kein Platzhalter);
        zuletzt die Zeile mit leerem Vorort (Platzhalter für alle Vororte, z. B. Schreibfehler).
        """
        schluessel = [(strasse_norm, vorort)]
        if not vorort:
            schluessel.append((strasse_norm, "Kernstadt"))
        schluessel.append((strasse_norm, ""))
        for schl in schluessel:
            for z in self.zuordnung.get(schl, []):
                if self._im_bereich(z, hausnr):
                    return z
        return None

    def bereich(self, strasse_norm: str, vorort: str, hausnr: str) -> str:
        """Kennung des greifenden Hausnummernbereichs („1-323“, „324-“) oder leer."""
        z = self._kuratiert(norm_strasse(strasse_norm), vorort, hausnr)
        if not z or not (z.get("hausnr_von", "").strip() or z.get("hausnr_bis", "").strip()):
            return ""
        return f"{z.get('hausnr_von', '').strip()}-{z.get('hausnr_bis', '').strip()}"

    # --- Ergebnisbau ----------------------------------------------------------
    def _fertig(self, kandidat: Kandidat, abgetrennt: str = "nein", kandidaten: str = "",
                vorort_angenommen: str = "nein") -> Aufloesung:
        """Baut die eindeutige Auflösung zu einem Kandidaten.

        Wurden Teilstrecken-Kandidaten beiseitegelegt, stehen sie weiter in
        `kandidaten` und `teilstrecke_abgetrennt` ist "ja".
        """
        s = self.strassen[kandidat.schl_nr]
        return Aufloesung(
            strasse_heute=s["lemma"],
            schl_nr=kandidat.schl_nr,
            stadtteil="; ".join(self.stadtteile[kandidat.schl_nr]),
            herkunft=kandidat.quelle,
            zeitlich_abweichend="nein" if kandidat.zeitlich == ZEIT_1936 else "ja",
            mehrdeutig="nein",
            kandidaten=kandidaten,
            teilstrecke_abgetrennt=abgetrennt,
            vorort_angenommen=vorort_angenommen,
        )

    def _mehrdeutig(self, entscheidend: dict[str, Kandidat], grund: str,
                    kandidaten: dict[str, Kandidat] | None = None,
                    abgetrennt: str = "nein") -> Aufloesung:
        """Baut ein mehrdeutiges Ergebnis mit allen beteiligten Straßenschlüsseln."""
        beste = min(entscheidend.values(), key=lambda k: k.rang)
        return Aufloesung(
            strasse_heute="",
            schl_nr="",
            stadtteil="",
            herkunft=beste.quelle,
            zeitlich_abweichend="nein",
            mehrdeutig="ja",
            kandidaten=";".join(kandidaten if kandidaten is not None else entscheidend),
            grund_mehrdeutig=grund,
            teilstrecke_abgetrennt=abgetrennt,
        )

    # --- Auflösung ------------------------------------------------------------
    def aufloesen(self, strasse_norm: str, vorort: str, teil: str = "", hausnr: str = "") -> Aufloesung:
        """Löst einen normierten Straßennamen von 1936 auf die heutige Straße auf.

        strasse_norm wird zusätzlich durch norm_strasse geschickt (die Funktion ist
        idempotent), da die kuratierte Tabelle mit norm_strasse(...)-Schlüsseln geführt wird.
        `teil` ist der Buchteil I/II/III; er unterscheidet die Kernstadt (I) von den
        Vorortbänden (II/III), in denen ein leerer Vorort keine Information ist.
        `hausnr` greift nur für kuratierte Hausnummernbereiche (Straßen, die nach 1936
        geteilt oder zusammengelegt wurden); ohne passende Nummer gilt die Automatik.
        """
        strasse_norm = norm_strasse(strasse_norm)

        # 1. Kuratierung schlägt alles, weil vom Menschen belegt.
        z = self._kuratiert(strasse_norm, vorort, hausnr)
        if z:
            return Aufloesung(strasse_heute=z["strasse_heute"], schl_nr=z["schl_nr"],
                              stadtteil="; ".join(self.stadtteile.get(z["schl_nr"], [])),
                              herkunft="kuratiert",
                              nummer_unsicher="ja" if z.get("nummer_unsicher", "").strip() == "ja" else "nein")

        # 2. Kandidaten sammeln.
        kandidaten = self._sammle(strasse_norm)
        if not kandidaten:
            return OFFEN

        # 3. Vorort-Filter — vor der Zeitstufung, damit ein 1936 gültiger Kandidat im
        #    falschen Ort nicht den räumlich richtigen, aber nur weit datierten verdrängt
        #    (Altendorfer Straße: Dickhoffs Teil-Umbenennung 1933 beendet den Namen für
        #    die ganze Kernstadtstraße, übrig bliebe sonst nur die Horster Namensschwester).
        passend = [k for k in kandidaten if self._passt(k.schl_nr, vorort, teil)]
        if not passend:
            erste_stufe = [k for k in kandidaten if k.zeitlich in ZEIT_ERSTE_STUFE]
            return self._mehrdeutig(self._beste_je_schluessel(erste_stufe or kandidaten),
                                    "vorort_widerspruch")

        # 4. Zeitstufung unter den passenden Kandidaten: erst 1936 gültig oder undatiert,
        #    sonst das weite Fenster 1930–1937, sonst außerhalb datierte (die beiden
        #    Rückfälle mit zeitlich_abweichend=ja). Die Stufen verschmelzen nicht zu
        #    Homonymen: Schölerpad (Altendorfer Straße bis 1896) verdrängt nicht die
        #    bis 1933 so benannte Kernstadtstraße.
        for stufe in (ZEIT_ERSTE_STUFE, (ZEIT_WEIT,), (ZEIT_AUSSERHALB,)):
            treffer = [k for k in passend if k.zeitlich in stufe]
            if treffer:
                passend = treffer
                break
        # 4b. Außerhalb datierte Namen, die heute nicht mehr gelten, werden nicht automatisch
        #     vergeben: Dickhoff führt keine verschwundenen Straßen, ein Jahrzehnte vor 1936
        #     erloschener Name gehört meist einer verschwundenen Namensschwester (R4.2; Stichprobe
        #     r4 am Stadtplan 1935: 11 von 17 widerlegt). Gilt der Name heute, ist nur Dickhoffs
        #     Kette lückenhaft (Oberdorfstraße "ab 1950") — der Kandidat bleibt, zeitlich abweichend.
        if stufe == (ZEIT_AUSSERHALB,) and not any(k.quelle == "heutig" for k in passend):
            return self._mehrdeutig(self._beste_je_schluessel(passend), "name_erloschen")

        # 5. Teilstrecken ("(tlw.)") sind Stücke derselben Straße, keine Homonyme:
        #    gibt es daneben Kandidaten mit dem schlichten Namen, entscheiden nur diese.
        beste = self._beste_je_schluessel(passend)
        schlicht = {s: k for s, k in beste.items() if not k.teilstrecke}
        entscheidend = schlicht or beste
        abgetrennt = "ja" if len(entscheidend) < len(beste) else "nein"

        # 6. Entscheidung: nur ein einziger Straßenschlüssel wird aufgelöst.
        if len(entscheidend) == 1:
            return self._fertig(next(iter(entscheidend.values())), abgetrennt,
                                ";".join(beste) if abgetrennt == "ja" else "")
        # 7. Teil II/III ohne Vorort: ein leerer Vorort bedeutet dort zu 95 % Kernstadt
        #    (Kreuztabelle 2026-09-15). Als Vorfilter zu riskant, als Entscheider unter sonst
        #    gleichwertigen Kandidaten vertretbar — mit Flag, damit es sichtbar bleibt.
        if not vorort and teil in ("II", "III"):
            kern = {s: k for s, k in entscheidend.items() if self._kernstadt(self.stadtteile.get(s, []))}
            if len(kern) == 1:
                return self._fertig(next(iter(kern.values())), abgetrennt, ";".join(beste),
                                    vorort_angenommen="ja")
        nur_unklare_konkordanz = all(k.quelle == "konkordanz" and k.konkordanz_eindeutig == "nein"
                                     for k in entscheidend.values())
        return self._mehrdeutig(entscheidend,
                                "konkordanz_nicht_eindeutig" if nur_unklare_konkordanz else "homonym_1936",
                                beste, abgetrennt)

    def vorschlaege(self, strasse_norm: str, n: int = 3) -> list[tuple[str, str, float]]:
        """Schlägt ähnliche Straßennamen vor (Name im Datensatz, heutiges Lemma, Ähnlichkeit)."""
        strasse_norm = norm_strasse(strasse_norm)
        out = []
        for kand in difflib.get_close_matches(strasse_norm, self._pool, n=n, cutoff=0.8):
            schl = (self.heutig.get(kand) or [z["schl_nr"] for z in self.stadien.get(kand, [])])[0]
            lemma = self.strassen.get(schl, {}).get("lemma", "")
            out.append((kand, lemma, round(difflib.SequenceMatcher(None, strasse_norm, kand).ratio(), 3)))
        return out
