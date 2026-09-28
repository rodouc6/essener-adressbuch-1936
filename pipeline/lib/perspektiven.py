"""Kapitel der Perspektiven-Seite (Spec §6.2): Schema prüfen, laden, Index bauen. Inhalte: kuratierung/perspektiven/*.json."""
from __future__ import annotations

import json
from pathlib import Path

DATEN = ("stellung", "gruppe", "niveau", "besitz", "gewerbe", "bergbau")
EBENEN = ("adresse", "strasse", "stadtteil", "hex")
FORMEN = ("karte", "stadtteilkarte", "bubbles", "balken", "multiples", "rangliste", "punktkarte")
PUNKTE_ZUSTAENDE = ("gesammelt", "karten", "haeuser")
MASSE = ("anteil", "dominant", "mischung", "dichte")
KAUFLEUTE = ("unbestimmt", "angestellte", "selbstaendige")
MUSTER = ("schraffur",)
PFLICHT = ("id", "reihenfolge", "titel", "untertitel", "freigegeben", "einleitung", "schritte", "grenzen", "quellen",
           "datenbasis", "datenbasis_schritt", "ausschluss")
PFLICHT_SCHRITT = ("id", "text", "ansicht", "hervorheben", "beschreibung")
PFLICHT_ANSICHT = ("daten", "ebene", "form", "gruppen", "kaufleute", "unsicher", "mass", "bezug", "min_n", "filter", "karte")


def ist_trichter(a: dict) -> bool:
    return a.get("daten") == "kennzahlen" or a.get("form") == "trichter"


def pruefe_trichter(a: dict, wo: str) -> list[str]:
    """Trichter (Spec 2026-09-27 §3.1): `daten: kennzahlen` nur mit `form: trichter` und umgekehrt; `stufen` nicht
    leer; jede Stufe und jedes Segment mit name, aus (Kennzahl-Schlüssel), farbe; Namen eindeutig; muster nur schraffur."""
    if a.get("daten") != "kennzahlen" or a.get("form") != "trichter":
        return [f"{wo}: daten kennzahlen nur mit form trichter und umgekehrt"]
    stufen = a.get("stufen")
    if not isinstance(stufen, list) or not stufen:
        return [f"{wo}: trichter ohne stufen"]
    f: list[str] = []
    namen: list = []
    schluessel: list = []
    for s in stufen:
        segmente = s.get("segmente", []) if isinstance(s, dict) else []
        if not isinstance(segmente, list):
            f.append(f"{wo}: segmente muss eine Liste sein"); segmente = []
        for x in [s, *segmente]:
            if not isinstance(x, dict) or not x.get("name") or not isinstance(x.get("aus"), str) or not x.get("aus") or not x.get("farbe"):
                f.append(f"{wo}: Stufe unvollständig {x!r}")
                continue
            if x.get("muster") is not None and x["muster"] not in MUSTER: f.append(f"{wo}: muster {x['muster']!r} unbekannt")
            if "ohne_anteil" in x and not isinstance(x["ohne_anteil"], bool): f.append(f"{wo}: ohne_anteil muss true/false sein")
            namen.append(x["name"]); schluessel.append(x["aus"])
    if len(set(namen)) != len(namen): f.append(f"{wo}: Stufenname doppelt")
    # Jede Stufe und jedes Segment ist eine Einheit mit data-id = aus; doppelte aus fänden im Detailkasten nur die erste.
    if len(set(schluessel)) != len(schluessel): f.append(f"{wo}: aus doppelt")
    if not isinstance(a.get("erklaerungen", {}), dict): f.append(f"{wo}: erklaerungen muss ein Objekt sein")
    return f


def pruefe_ansicht(a: dict, wo: str) -> list[str]:
    if ist_trichter(a):
        return pruefe_trichter(a, wo)
    f = [f"{wo}: Ansicht ohne Feld {p!r}" for p in PFLICHT_ANSICHT if p not in a]
    if f:
        return f
    if a["daten"] not in DATEN: f.append(f"{wo}: daten {a['daten']!r} unbekannt")
    if a["ebene"] not in EBENEN: f.append(f"{wo}: ebene {a['ebene']!r} unbekannt")
    if a["form"] not in FORMEN: f.append(f"{wo}: form {a['form']!r} unbekannt")
    if a["mass"] not in MASSE: f.append(f"{wo}: mass {a['mass']!r} unbekannt")
    if a["kaufleute"] not in KAUFLEUTE: f.append(f"{wo}: kaufleute {a['kaufleute']!r} unbekannt")
    if a["mass"] == "dichte" and a["daten"] != "gewerbe": f.append(f"{wo}: mass dichte nur mit daten gewerbe")
    namen = [g.get("name") for g in a["gruppen"]]
    if len(set(namen)) != len(namen): f.append(f"{wo}: Gruppenname doppelt")
    for g in a["gruppen"]:
        if not g.get("name") or not isinstance(g.get("aus"), list) or not g.get("farbe"): f.append(f"{wo}: Gruppe unvollständig {g!r}")
    if a["mass"] in ("anteil", "dichte") and a["bezug"] not in namen: f.append(f"{wo}: bezug {a['bezug']!r} ist keine Gruppe")
    if not isinstance(a["min_n"], int) or a["min_n"] < 0: f.append(f"{wo}: min_n muss ganze Zahl ≥ 0 sein")
    p = a.get("punkte")
    if a["form"] == "punktkarte" or p is not None:
        if not isinstance(p, dict): f.append(f"{wo}: punktkarte braucht punkte {{zustand, hervor}}")
        else:
            if p.get("zustand") not in PUNKTE_ZUSTAENDE: f.append(f"{wo}: punkte.zustand {p.get('zustand')!r} unbekannt")
            if not isinstance(p.get("hervor"), list): f.append(f"{wo}: punkte.hervor muss Liste sein")
            elif any(h not in namen for h in p["hervor"]): f.append(f"{wo}: punkte.hervor nennt keine Gruppe")
    return f


def pruefe_punkte_bezug(k: dict, punkte: dict) -> list[str]:
    """Schritte im Zustand `haeuser` gruppieren nach Gesellschafts-IDs; jede muss in bergbau_punkte.json stehen —
    sonst bliebe eine Gesellschaft stumm grau, und der Text spräche von Häusern, die niemand sieht."""
    ids = {g["id"] for g in punkte.get("gesellschaften", [])}
    f = []
    for s in k.get("schritte", []):
        a = s.get("ansicht", {})
        if a.get("form") != "punktkarte" or (a.get("punkte") or {}).get("zustand") != "haeuser": continue
        for g in a.get("gruppen", []):
            for aus in g.get("aus", []):
                if aus not in ids:
                    f.append(f"Kapitel {k.get('id')!r}, Schritt {s.get('id')!r}: Gesellschaft {aus!r} fehlt in bergbau_punkte.json")
    return f


def pruefe_kapitel(k: dict) -> list[str]:
    f = [f"Kapitel ohne Feld {p!r}" for p in PFLICHT if p not in k]
    if "schritte" not in k:
        return f
    ids = [s.get("id") for s in k["schritte"]]
    if len(set(ids)) != len(ids): f.append("Schritt-id doppelt")
    for s in k["schritte"]:
        wo = f"Schritt {s.get('id')!r}"
        f += [f"{wo}: ohne Feld {p!r}" for p in PFLICHT_SCHRITT if p not in s]
        if "ansicht" in s: f += pruefe_ansicht(s["ansicht"], wo)
    # Fachkapitel (mindestens eine Ansicht auf Ebenen-Daten) müssen Datenbasis und Ausschluss benennen;
    # Kapitel 0 (nur Trichter) darf die Felder leer lassen.
    fach = any("ansicht" in s and not ist_trichter(s["ansicht"]) for s in k["schritte"])
    if fach:
        for p in ("datenbasis", "datenbasis_schritt", "ausschluss"):
            if not k.get(p): f.append(f"Fachkapitel ohne {p}")
    return f


def stufen_schluessel(k: dict) -> list[str]:
    """Alle Kennzahl-Schlüssel (`aus`) der Trichter-Ansichten eines Kapitels, in Reihenfolge, mit Dubletten."""
    out: list[str] = []
    for s in k.get("schritte", []):
        a = s.get("ansicht", {})
        if not ist_trichter(a): continue
        for st in a.get("stufen", []):
            out.append(st.get("aus", ""))
            out += [x.get("aus", "") for x in st.get("segmente", []) or []]
    return out


def pruefe_datenbasis_bezug(kapitel: list[dict]) -> list[str]:
    """`datenbasis_schritt` eines Fachkapitels muss eine Schritt-id von Kapitel `datenbasis` sein — sonst zeigte
    der Link „Datenbasis ›“ ins Leere (gleiche Fehlerklasse wie ein unsichtbares Kapitel 0)."""
    k0 = next((k for k in kapitel if k.get("id") == "datenbasis"), None)
    fach = [k for k in kapitel if k.get("datenbasis_schritt")]
    if not fach:
        return []
    if k0 is None:
        return []      # ohne Kapitel 0 rendert die Seite den Link gar nicht (datenbasisLink)
    ids = {s.get("id") for s in k0.get("schritte", [])}
    return [f"Kapitel {k['id']!r}: datenbasis_schritt {k['datenbasis_schritt']!r} ist kein Schritt von Kapitel 'datenbasis'"
            for k in fach if k["datenbasis_schritt"] not in ids]


def pruefe_kennzahlen_bezug(k: dict, kennzahlen: dict) -> list[str]:
    """Jeder `aus`-Schlüssel eines Trichters muss in kennzahlen.json stehen — sonst zeichnete die Seite einen leeren Balken."""
    return [f"Kapitel {k.get('id')!r}: Kennzahl {aus!r} fehlt" for aus in stufen_schluessel(k) if aus not in kennzahlen]


def _loese_gruppen_auf(k: dict) -> dict:
    """Löst die Kurzform `"gruppen": "wie:<schritt-id>"` auf: kopiert die Gruppenliste des Schritts mit
    dieser id (tiefe Kopie, damit spätere Änderungen sich nicht gegenseitig beeinflussen). Unbekannte
    Schritt-id → KeyError (bewusst laut, statt eine leere Liste zu erfinden)."""
    nach_id = {s["id"]: s for s in k.get("schritte", []) if "id" in s}
    for s in k.get("schritte", []):
        g = s.get("ansicht", {}).get("gruppen")
        if isinstance(g, str) and g.startswith("wie:"):
            s["ansicht"]["gruppen"] = json.loads(json.dumps(nach_id[g[4:]]["ansicht"]["gruppen"]))
    return k


def lade_kapitel(ordner: Path | str) -> list[dict]:
    ks = [_loese_gruppen_auf(json.loads(p.read_text(encoding="utf-8"))) for p in sorted(Path(ordner).glob("*.json"))]
    return sorted(ks, key=lambda k: (k.get("reihenfolge", 999), k.get("id", "")))


def kapitel_index(kapitel: list[dict]) -> list[dict]:
    return [{"id": k["id"], "titel": k["titel"], "untertitel": k["untertitel"], "freigegeben": bool(k["freigegeben"]), "reihenfolge": k["reihenfolge"]} for k in kapitel]
