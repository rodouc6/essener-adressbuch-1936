"""Nominatim-Client mit JSONL-Cache und die Verortungsregeln (haus / strasse / landmarke / offen)."""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path

import requests

from pipeline.lib.io import lies_csv
from pipeline.lib.normalisierung import norm_stadtteil, norm_strasse

SCHEMA_VERSION = "1"
BASIS = {"format": "json", "addressdetails": "1", "countrycodes": "de", "limit": "5"}


@dataclass(frozen=True)
class Verortung:
    lat: str = ""
    lon: str = ""
    stufe: str = "offen"
    grund: str = ""
    osm_type: str = ""
    osm_id: str = ""
    display_name: str = ""
    zusatz_ignoriert: str = "nein"


class Client:
    """Nominatim-HTTP-Client mit persistentem JSONL-Cache (Schlüssel = sortiertes JSON der Anfrageparameter).

    `suche` ist thread-sicher: Cache-Zugriff und Anhängen an die Cache-Datei sind
    durch eine Lock geschützt, die eigentliche HTTP-Anfrage läuft außerhalb der Lock
    (für Task 8: parallele Aufrufe aus mehreren Threads).
    """

    def __init__(self, basis_url: str, cache_pfad: Path):
        self.url = basis_url.rstrip("/") + "/search"
        self.cache_pfad = Path(cache_pfad)
        self.cache: dict[str, list] = {}
        self._lock = threading.Lock()
        if self.cache_pfad.exists():
            with open(self.cache_pfad, encoding="utf-8") as f:
                for zeile in f:
                    d = json.loads(zeile)
                    self.cache[d["k"]] = d["v"]
        self.cache_pfad.parent.mkdir(parents=True, exist_ok=True)
        self._out = open(self.cache_pfad, "a", encoding="utf-8")

    def suche(self, params: dict) -> list[dict]:
        """Sucht bei Nominatim, gecacht über den sortierten JSON-Schlüssel der Parameter."""
        k = json.dumps({"v": SCHEMA_VERSION, **params}, sort_keys=True, ensure_ascii=False)
        with self._lock:
            if k in self.cache:
                return self.cache[k]
        r = requests.get(self.url, params={**BASIS, **params}, timeout=15)
        r.raise_for_status()
        v = r.json()
        with self._lock:
            self.cache[k] = v
            self._out.write(json.dumps({"k": k, "v": v}, ensure_ascii=False) + "\n")
        return v

    def schliessen(self) -> None:
        self._out.close()


def lade_landmarken(pfad: Path) -> list[dict]:
    """Lädt bekannte Landmarken (Substring-Muster → Koordinaten) aus einer CSV-Datei."""
    return lies_csv(pfad) if Path(pfad).exists() else []


def _road_passt(t: dict, strasse_heute: str) -> bool:
    return norm_strasse(t.get("address", {}).get("road", "")) == norm_strasse(strasse_heute)


_ORTS_FELDER = ("neighbourhood", "suburb", "quarter")


def _orte(t: dict) -> set[str]:
    """Alle in der OSM-Antwort genannten Stadtteil-artigen Felder, normalisiert (leere ausgefiltert)."""
    adr = t.get("address", {})
    return {norm_stadtteil(adr.get(feld, "")) for feld in _ORTS_FELDER} - {""}


def _feinster_ort(t: dict) -> str:
    """Feinste bekannte Ortsangabe (neighbourhood > suburb > quarter), normalisiert."""
    adr = t.get("address", {})
    for feld in _ORTS_FELDER:
        wert = adr.get(feld, "")
        if wert:
            return norm_stadtteil(wert)
    return ""


def _erlaubte_stadtteile(stadtteil: str) -> set[str]:
    return {norm_stadtteil(s) for s in stadtteil.split(";") if s.strip()} if stadtteil else set()


def _stadtteil_status(t: dict, stadtteil: str) -> str:
    """'ok' wenn Prüfung nicht möglich oder bestanden, sonst 'widerspruch'.

    Geprüft wird gegen die Vereinigung aus `neighbourhood`, `suburb` und `quarter`
    (mind. eines muss in der erlaubten Dickhoff-Liste liegen). Kettwig gehörte 1936
    nicht zu Essen (vgl. konkordanz.py) und wird deshalb verworfen, außer die
    übergebene Stadtteil-Liste nennt Kettwig ausdrücklich.
    """
    orte = _orte(t)
    erlaubt = _erlaubte_stadtteile(stadtteil)
    if "Kettwig" in orte and "Kettwig" not in erlaubt:
        return "widerspruch"
    if not stadtteil:
        return "ok"
    if not orte:
        return "ok"
    return "ok" if orte & erlaubt else "widerspruch"


def _treffer(t: dict, stufe: str, grund: str = "", zusatz_ignoriert: str = "nein") -> Verortung:
    return Verortung(t["lat"], t["lon"], stufe, grund, t.get("osm_type", ""), str(t.get("osm_id", "")),
                      t.get("display_name", ""), zusatz_ignoriert)


def _hausebene(client, strasse_heute, hausnr, zusatz, stadtteil) -> Verortung | None:
    """Sucht auf Hausebene: erst mit Zusatz, dann (falls vorhanden) ohne Zusatz."""
    zusatz = zusatz.lower()
    for z, ignoriert in ((zusatz, "nein"), ("", "ja")) if zusatz else (("", "nein"),):
        for t in client.suche({"street": f"{hausnr}{z} {strasse_heute}", "city": "Essen"}):
            adr = t.get("address", {})
            if adr.get("house_number", "").lower().replace(" ", "") not in {hausnr + z, hausnr}:
                continue
            if not _road_passt(t, strasse_heute):
                continue
            if _stadtteil_status(t, stadtteil) != "ok":
                continue
            return _treffer(t, "haus", "", ignoriert)
    return None


def _strassenebene(client, strasse_heute, stadtteil, grund="") -> Verortung:
    """Sucht auf Straßenebene; bei mehreren Stadtteilen ohne bekannten Stadtteil bleibt es offen."""
    treffer = [t for t in client.suche({"street": strasse_heute, "city": "Essen"})
               if t.get("class") == "highway" and _road_passt(t, strasse_heute)]
    if not treffer:
        return Verortung(stufe="offen", grund="kein_treffer")
    passend = [t for t in treffer if _stadtteil_status(t, stadtteil) == "ok"]
    if stadtteil and not passend:
        return Verortung(stufe="offen", grund="stadtteil_widerspruch")
    if not passend:
        return Verortung(stufe="offen", grund="kein_treffer")
    gruppen = {_feinster_ort(t) for t in passend}
    if len(gruppen) > 1 and not stadtteil:
        return Verortung(stufe="offen", grund="mehrdeutig_strasse")
    return _treffer(passend[0], "strasse", grund)


def geokodiere(client, strasse_heute: str, hausnr: str, hausnr_zusatz: str, stadtteil: str,
               parse_status: str, strasse_roh: str, landmarken: list[dict]) -> Verortung:
    """Verortet eine Adresse: Hausebene, sonst Straßenebene, sonst Landmarke, sonst offen.

    `stadtteil` ist eine mit „; “ getrennte Dickhoff-Liste möglicher Stadtteile;
    ein leerer Stadtteil bedeutet, dass keine Stadtteil-Prüfung stattfindet.
    """
    if parse_status in ("ohne_nummer", "leer", "unklar") and not hausnr:
        roh = strasse_roh.lower()
        for lm in landmarken:
            if lm["muster"].lower() in roh:
                return Verortung(lm["lat"], lm["lon"], "landmarke", "", "", "", lm["name"])
        if not strasse_heute:
            return Verortung(stufe="offen", grund="ohne_nummer" if parse_status == "ohne_nummer" else "strasse_offen")
        return _strassenebene(client, strasse_heute, stadtteil, grund="ohne_nummer")
    if not strasse_heute:
        return Verortung(stufe="offen", grund="strasse_offen")
    haus = _hausebene(client, strasse_heute, hausnr, hausnr_zusatz, stadtteil)
    if haus:
        return haus
    return _strassenebene(client, strasse_heute, stadtteil)
