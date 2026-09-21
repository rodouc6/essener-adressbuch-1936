"""Zechen Essens aus der Wikipedia-Liste → kuratierung/zechen.csv (einmalig, danach Handprüfung).

    python3 werkzeuge/zechen_wikipedia.py [--neu]

Die Tabelle wird nicht überschrieben, wenn sie existiert (Handprüfungen bleiben erhalten); --neu erzwingt.
Zeilen ohne Koordinaten bleiben in der CSV, damit sie von Hand ergänzt werden können; Stufe 06 lässt sie weg.
"""
from __future__ import annotations

import datetime
import pathlib
import re
import sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.io import projektwurzel, schreib_csv

SEITE = "Liste_von_Bergwerken_in_Essen"
API = "https://de.wikipedia.org/w/api.php"
FELDER = ["name", "stadtteil", "lat", "lon", "betrieb_von", "betrieb_bis", "quelle", "bearbeiter", "datum"]
_LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_JAHRE = re.compile(r"(\d{4})\s*[–\-]\s*(\d{4})?")  # ein Jahr oder Jahresspanne in einer Zelle ("Betrieb"-Format)
_JAHR = re.compile(r"\d{4}")  # einzelnes Jahr in einer eigenen Beginn-/Ende-Spalte
_KOORD = re.compile(r"NS=([\d.]+)\|EW=([\d.]+)")
# Wikitabellen-Zellattribute vor dem eigentlichen Inhalt, z. B. "width=200px | Name" oder
# 'data-sort-value="1875"|nach 1875'; Wikilinks ("[[...]]") beginnen nie so und bleiben unberührt.
_ATTRIBUT = re.compile(r'^\s*(?:[\w\-]+=(?:"[^"]*"|\S+)\s*\|\s*)+')


def _ohne_attribut(zelle: str) -> str:
    """Entfernt eine führende Zellattribut-Angabe (vor dem letzten "|"), lässt Wikilinks unberührt."""
    return _ATTRIBUT.sub("", zelle).strip()


def _text(zelle: str) -> str:
    """Wikilink-Anzeigetext, sonst der bereinigte Zelleninhalt."""
    zelle = _ohne_attribut(zelle)
    m = _LINK.search(zelle)
    if m:
        return (m.group(2) or m.group(1)).strip()
    return re.sub(r"'{2,}|<[^>]+>", "", zelle).strip()


def _ziel(zelle: str) -> str:
    """Wikipedia-Artikelname (erstes Linkziel) für den quelle-Link; leer ohne Wikilink."""
    m = _LINK.search(_ohne_attribut(zelle))
    return m.group(1).strip().replace(" ", "_") if m else ""


def _zellen(zeile: str) -> list[str]:
    """Zellinhalte einer Tabellenzeile (Text zwischen zwei "|-"-Markern).

    Zeilenformat kann pro Zelle eine eigene Zeile sein (die echte Wikipedia-Seite) oder
    mit "||" auf einer Zeile getrennt (Kurzform, z. B. in Tests). Leere Zellen bleiben als
    leerer String erhalten, damit die Spaltenposition (und damit die Zuordnung zu
    Name/Stadtteil/Jahren) nicht verrutscht.
    """
    zellen: list[str] = []
    for teil in zeile.split("\n"):
        teil = teil.strip()
        if not teil or teil.startswith(("{|", "!", "|}")):
            continue
        if not teil.startswith("|"):
            continue
        rest = teil[1:]
        for stueck in re.split(r"\s\|\|\s|\|\|", rest):
            zellen.append(stueck.strip())
    return zellen


def _kopfspalten(kopf_teil: str) -> list[str]:
    """Spaltenüberschriften aus einem Tabellenabschnitt, z. B. ['Name', 'Stadt- oder Ortsteil', 'Beginn', 'Ende', ...].

    Deckt sowohl eine Kopfzeile mit "!!"-getrennten Spalten als auch mehrere einzelne
    "!"-Zeilen (eine Spalte pro Zeile, wie auf der echten Seite) ab.
    """
    spalten = []
    for zeile in kopf_teil.split("\n"):
        zeile = zeile.strip()
        if not zeile.startswith("!"):
            continue
        for stueck in zeile[1:].split("!!"):
            stueck = _ohne_attribut(stueck)
            if stueck:
                spalten.append(stueck)
    return spalten


def _kopf_und_datenzeilen(tabelle: str) -> tuple[list[str], list[str]]:
    """Trennt einen Tabellenabschnitt (zwischen zwei "{|") in Kopfspalten und Datenzeilen.

    Die Kopfzeile steht je nach Vorlage entweder vor dem ersten "|-" (Testausschnitt) oder
    in einem eigenen Abschnitt zwischen zwei "|-" (die echte Wikipedia-Seite). Der erste
    "|-"-getrennte Abschnitt, der "!"-Zeilen enthält, gilt als Kopfzeile; alle danach
    folgenden Abschnitte sind Datenzeilen.
    """
    teile = tabelle.split("|-")
    kopf_index = next(
        (i for i, teil in enumerate(teile) if any(z.strip().startswith("!") for z in teil.split("\n"))),
        None,
    )
    if kopf_index is None:
        return [], teile[1:]
    return _kopfspalten(teile[kopf_index]), teile[kopf_index + 1:]


def _spaltenindex(kopf: list[str], stichworte: list[str]) -> int | None:
    """Index der ersten Kopfspalte, deren (klein geschriebener) Text eines der Stichworte enthält."""
    for i, spalte in enumerate(kopf):
        if any(stichwort in spalte.lower() for stichwort in stichworte):
            return i
    return None


def _zelle(zellen: list[str], index: int | None) -> str:
    return zellen[index] if index is not None and index < len(zellen) else ""


def parse_zechen(wikitext: str) -> list[dict]:
    """Liest die Zechen-Tabelle(n) aus dem Wikitext der Seite „Liste von Bergwerken in Essen“.

    Die Spaltenreihenfolge wird aus der Kopfzeile jeder Tabelle erkannt, da sie zwischen
    Testausschnitt (eine kombinierte "Betrieb"-Spalte mit Jahresspanne wie "1851–1986") und
    der echten Seite (getrennte "Beginn"/"Ende"-Spalten, keine Koordinaten-Spalte) abweicht.
    Fehlt eine Kopfzeile, wird die Reihenfolge Name, Stadtteil, Betrieb, Koordinaten angenommen.
    """
    zechen = []
    for tabelle in re.split(r"\n\{\|", wikitext):
        if "|-" not in tabelle:
            continue
        # Ohne erkennbare Kopfzeile gilt die Reihenfolge des Testausschnitts: Name, Stadtteil,
        # Betrieb (kombinierte Jahresspanne), Koordinaten.
        kopf, datenzeilen = _kopf_und_datenzeilen(tabelle)
        i_name = _spaltenindex(kopf, ["name", "zeche"]) if kopf else 0
        i_ort = _spaltenindex(kopf, ["stadtteil", "ortsteil", "ort"]) if kopf else 1
        i_von = _spaltenindex(kopf, ["beginn", "von", "start"]) if kopf else None
        i_bis = _spaltenindex(kopf, ["ende", "bis"]) if kopf else None
        if i_von is None and i_bis is None:
            i_betrieb = _spaltenindex(kopf, ["betrieb", "jahr", "zeit"]) if kopf else 2
        else:
            i_betrieb = None
        if i_name is None:
            i_name = 0

        for zeile in datenzeilen:
            zellen = _zellen(zeile)
            name = _text(_zelle(zellen, i_name))
            if not name:
                continue

            if i_von is not None or i_bis is not None:
                jahr_von = _JAHR.search(_zelle(zellen, i_von))
                jahr_bis = _JAHR.search(_zelle(zellen, i_bis))
                betrieb_von = jahr_von.group(0) if jahr_von else ""
                betrieb_bis = jahr_bis.group(0) if jahr_bis else ""
            else:
                jahre = _JAHRE.search(_zelle(zellen, i_betrieb))
                betrieb_von = jahre.group(1) if jahre else ""
                betrieb_bis = (jahre.group(2) or "") if jahre else ""

            # Koordinaten stehen meist in einer eigenen {{Coordinate|...}}-Vorlage irgendwo in der
            # Zeile statt in einer eigenen Spalte; die Suche im ganzen Zeilentext deckt beides ab.
            koord = _KOORD.search(zeile)
            ziel = _ziel(_zelle(zellen, i_name))
            zechen.append(dict(
                name=name,
                stadtteil=_text(_zelle(zellen, i_ort)),
                lat=koord.group(1) if koord else "",
                lon=koord.group(2) if koord else "",
                betrieb_von=betrieb_von,
                betrieb_bis=betrieb_bis,
                quelle=f"https://de.wikipedia.org/wiki/{ziel}" if ziel else "",
                bearbeiter="wikipedia",
                datum=datetime.date.today().isoformat(),
            ))
    return zechen


def main() -> None:
    ziel = projektwurzel() / "kuratierung" / "zechen.csv"
    if ziel.exists() and "--neu" not in sys.argv:
        sys.exit(f"{ziel} existiert, --neu zum Überschreiben")
    r = requests.get(API, params=dict(action="parse", page=SEITE, prop="wikitext", format="json"),
                     headers={"User-Agent": "essener-adressbuch-1936 (Zechenliste)"}, timeout=30)
    r.raise_for_status()
    zechen = parse_zechen(r.json()["parse"]["wikitext"]["*"])
    schreib_csv(ziel, zechen, FELDER)
    print(f"{len(zechen)} Zechen, {sum(1 for z in zechen if z['lat'])} mit Koordinaten → {ziel}")


if __name__ == "__main__":
    main()
