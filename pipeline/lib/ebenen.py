"""Aggregationsebenen für Perspektiven und Werkstatt (Teilprojekt 5a, Spec §4.1, §5.4): Zählfelder je Adresse,
Summen je Straße, Stadtteil und Hexzelle. Der Browser addiert nur noch Zählfelder — hier wird gezählt.

Hexraster: „pointy-top“, Kantenlänge 120 m, lokale äquirektangulare Projektion um ZENTRUM (Essen); Zellen-ID „q_r“
in Axialkoordinaten. Genau genug für ein Stadtgebiet von ±15 km.
"""
from __future__ import annotations

import math
from collections import defaultdict

HEX_KANTE = 120.0
ZENTRUM = (51.45, 7.01)
_M_JE_GRAD = 111_320.0
_COS = math.cos(math.radians(ZENTRUM[0]))
EBENEN = ("strasse", "stadtteil", "hex")


def _xy(lat: float, lon: float) -> tuple[float, float]:
    return (lon - ZENTRUM[1]) * _M_JE_GRAD * _COS, (lat - ZENTRUM[0]) * _M_JE_GRAD


def _lonlat(x: float, y: float) -> list[float]:
    return [round(x / (_M_JE_GRAD * _COS) + ZENTRUM[1], 6), round(y / _M_JE_GRAD + ZENTRUM[0], 6)]


def hex_zelle(lat: float, lon: float) -> tuple[int, int]:
    """Axialkoordinaten (q, r) der Zelle, die den Punkt enthält (Cube-Rundung)."""
    x, y = _xy(lat, lon)
    qf = (math.sqrt(3) / 3 * x - 1 / 3 * y) / HEX_KANTE
    rf = (2 / 3 * y) / HEX_KANTE
    sf = -qf - rf
    q, r, s = round(qf), round(rf), round(sf)
    dq, dr, ds = abs(q - qf), abs(r - rf), abs(s - sf)
    if dq > dr and dq > ds:
        q = -r - s
    elif dr > ds:
        r = -q - s
    return int(q), int(r)


def hex_mitte(q: int, r: int) -> tuple[float, float]:
    return HEX_KANTE * math.sqrt(3) * (q + r / 2), HEX_KANTE * 1.5 * r


def hex_polygon(q: int, r: int) -> list[list[float]]:
    """Sechs Ecken (lon, lat) plus Schlusspunkt, gegen den Uhrzeigersinn ab der Ecke rechts oben."""
    cx, cy = hex_mitte(q, r)
    ecken = [_lonlat(cx + HEX_KANTE * math.cos(math.radians(60 * i + 30)), cy + HEX_KANTE * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    return ecken + [ecken[0]]


def hex_id(q: int, r: int) -> str:
    return f"{q}_{r}"


def zaehlfelder(a: dict) -> dict[str, int]:
    """Zählfelder einer Adresse: Teile, Niveau (wie bisher), Stellung, Berufsgruppe (Teil I), Gewerbegruppe und -art
    (Teil III, je Betrieb einmal), Besitzklasse (je Adresse). Teil-I-Einträge ohne geprüften Beruf zählen bei Stellung
    und Gruppe als unbestimmt/ungeprüft — der Nenner bleibt sichtbar."""
    n: dict[str, int] = defaultdict(int)
    gesehen: set[tuple[str, str]] = set()   # (Betrieb, Gruppe/Art): derselbe Betrieb zählt je Gruppe nur einmal (Spec §5.3)
    for e in a["eintraege"]:
        n["n_" + e["teil"]] += 1
        if e["teil"] == "I":
            b = e.get("_beruf") or {}
            if b:
                n["n_" + b["niveau"]] += 1
            n["n_st_" + b.get("stellung", "unbestimmt")] += 1
            if b.get("stellung_quelle") == "hand":
                n["n_stellung_hand"] += 1      # Nenner für „davon handgeprüft“ (kein n_st_-Präfix: keine Klasse)
            n["n_gr_" + b.get("gruppe", "ungeprueft")] += 1
        elif e["teil"] == "III" and e.get("_gewerbe"):
            g = e["_gewerbe"]
            if (g["schluessel"], "g:" + g["gruppe"]) not in gesehen:
                gesehen.add((g["schluessel"], "g:" + g["gruppe"]))
                n["n_gw_" + g["gruppe"]] += 1
            if (g["schluessel"], "a:" + g["art"]) not in gesehen:
                gesehen.add((g["schluessel"], "a:" + g["art"]))
                n["n_gwa_" + g["art"]] += 1
    n["n_bs_" + a.get("besitz", "ungeprueft")] += 1
    if a.get("besitz_pruefung") == "regel":      # nur per Regel Person → Privatperson klassifiziert (kein n_bs_-Präfix: keine Klasse)
        n["n_besitz_regel"] += 1
    return {k: v for k, v in n.items() if v}


def strassenschluessel(a: dict) -> tuple[str, str]:
    """Heutige Straße über die fünfstellige schl_nr (Dickhoff); sonst die 1936er Schreibung mit Vorort. Liest dazu nur
    den ersten Eintrag: schl_nr/strasse_roh/Vorort sind je Adresse gleich, weil die Adress-ID daraus gebildet wird."""
    e0 = a["eintraege"][0] if a["eintraege"] else {}
    schl = (e0.get("schl_nr") or "").strip()
    if a.get("strasse_heute") and schl:
        return schl, a["strasse_heute"]
    roh, vorort = (e0.get("strasse_roh") or "").strip(), (e0.get("Vorort") or a.get("stadtteil") or "").strip()
    return f"1936:{roh}|{vorort}", f"{roh} (1936)"


def aggregiere(adressen: dict[str, dict], ebene: str) -> list[dict]:
    """Summen der Zählfelder je Einheit; Straße: id = Schlüssel, name, stadtteil (häufigster); Stadtteil: id = Name,
    lat/lon (Mittel), rang_nord (1 = nördlichster); Hex: id, lat/lon der Zellmitte. Sortiert nach id.

    Stadtteil-Ebene: `a["stadtteil"]` ist seit dem Polygonabgleich (Task 2, `karte_export.gruppiere`) je Adresse
    genau ein Name — keine `;`-Kombination mehrerer Straßen-Stadtteile mehr. Adressen ohne Stadtteil werden nicht
    verworfen, sondern unter der Einheit id="ohne_stadtteil" mitgezählt (lat/lon-Mittel wie sonst), damit die
    Summe der Einheiten stets der Summe der Adressen entspricht. Diese Einheit bekommt kein rang_nord, sodass
    Nord-Süd-Reihungen sie ignorieren können."""
    if ebene not in EBENEN:
        raise ValueError(f"unbekannte Ebene {ebene!r}")
    einheiten: dict[str, dict] = {}
    for a in adressen.values():
        if ebene == "strasse":
            k, name = strassenschluessel(a)
            u = einheiten.setdefault(k, dict(id=k, name=name, _st=defaultdict(int), adressen=0, _lat=0.0, _lon=0.0))
            u["_st"][a.get("stadtteil", "")] += 1
        elif ebene == "stadtteil":
            k = a.get("stadtteil") or "ohne_stadtteil"
            u = einheiten.setdefault(k, dict(id=k, adressen=0, _lat=0.0, _lon=0.0))
        else:
            q, r = hex_zelle(a["lat"], a["lon"])
            k = hex_id(q, r)
            u = einheiten.setdefault(k, dict(id=k, adressen=0, _lat=0.0, _lon=0.0, _qr=(q, r)))
        u["adressen"] += 1
        u["_lat"] += a["lat"]; u["_lon"] += a["lon"]
        for f, v in zaehlfelder(a).items():
            u[f] = u.get(f, 0) + v
    out = []
    for u in einheiten.values():
        n = u["adressen"]
        if ebene == "strasse":
            u["stadtteil"] = max(u.pop("_st").items(), key=lambda x: (x[1], x[0]))[0]
            u.pop("_lat"); u.pop("_lon")
        elif ebene == "stadtteil":
            u["lat"], u["lon"] = round(u.pop("_lat") / n, 5), round(u.pop("_lon") / n, 5)
        else:
            u.pop("_lat"); u.pop("_lon")
            u["lon"], u["lat"] = _lonlat(*hex_mitte(*u.pop("_qr")))
        out.append(u)
    out.sort(key=lambda u: u["id"])
    if ebene == "stadtteil":
        einreihbar = [u for u in out if u["id"] != "ohne_stadtteil"]
        for i, u in enumerate(sorted(einreihbar, key=lambda u: -u["lat"]), 1):
            u["rang_nord"] = i
    return out
