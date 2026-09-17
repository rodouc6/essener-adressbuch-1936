"""Erzeugt die Arbeitsliste für die Sichtung offener Straßen am Stadtplan 1935 (werkzeuge/sichtung.html).

Aufruf: python3 werkzeuge/sichtung_liste.py [--min-zeilen N]

Liest build/03_strassen.csv (Paartabelle aus Stufe 03), die Kuratierungstabellen und die
Straßendatenbank und schreibt build/sichtung_1935.json: je Gruppe (normierter Buchname, Vorort)
alle offenen oder mehrdeutigen Paare zusammengefasst, mit Zeilenzahl, Buchteilen, Beispiel,
Gründen, den Dickhoff-Kandidaten (Lemma, Stadtteile, Namensstadien, Sprungkoordinate aus dem
lokalen Nominatim) und ähnlichen Namen als Vorschlag. Der Sichtungsstand kommt aus
kuratierung/strassen_1935.csv (punkt / nicht_gefunden) und strassen_zuordnung.csv (zugeordnet).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import pathlib

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.lib.io import lies_csv, projektwurzel, strassen_dir
from pipeline.lib.konkordanz import STADTPLAN_KERNSTADT, Strassenindex
from pipeline.lib.nominatim import STADT, Client, _ist_essen, _road_passt
from pipeline.lib.normalisierung import norm_strasse
from werkzeuge.stichprobe_hinweise import namensstadien

MAX_KANDIDATEN = 6
MAX_VORSCHLAEGE = 3


def strassen_koordinate(client, lemma: str) -> list[str]:
    """Sprungkoordinate einer heutigen Straße: erster Straßentreffer in Essen, sonst leer."""
    try:
        for t in client.suche({"street": lemma, "city": STADT}):
            if t.get("class") == "highway" and _ist_essen(t) and _road_passt(t, lemma):
                return [t["lat"], t["lon"]]
    except requests.RequestException:
        pass
    return []


def stand(stadtplan: list[dict], zuordnung: list[dict]) -> dict[tuple[str, str], dict]:
    """Sichtungsstand je (Buchname normiert, Vorort/Kernstadt): zugeordnet geht vor punkt/nicht_gefunden."""
    out: dict[tuple[str, str], dict] = {}
    for z in stadtplan:
        k = (norm_strasse(z["strasse_roh_norm"]), z["vorort"].strip() or STADTPLAN_KERNSTADT)
        out[k] = {"stand": z.get("befund", "").strip(), "lat": z.get("lat", ""), "lon": z.get("lon", ""),
                  "name_im_plan": z.get("name_im_plan", ""), "stadtteil": z.get("stadtteil", ""),
                  "bemerkung": z.get("bemerkung", "")}
    for z in zuordnung:
        if z.get("hausnr_von", "").strip() or z.get("hausnr_bis", "").strip():
            continue  # Bereichszeilen sind keine Sichtung ganzer Straßen
        k = (norm_strasse(z["strasse_roh_norm"]), z["vorort"].strip() or "")
        out[k] = {"stand": "zugeordnet", "strasse_heute": z.get("strasse_heute", ""), "schl_nr": z.get("schl_nr", ""),
                  "beleg": z.get("beleg", "")}
    return out


def _strasse(idx: Strassenindex, schl_nr: str, quelle: str, koord) -> dict | None:
    st = idx.strassen.get(schl_nr)
    if not st:
        return None
    return {"schl_nr": schl_nr, "lemma": st["lemma"], "stadtteile": st["stadtteile"], "quelle": quelle,
            "stadien": namensstadien(idx, schl_nr), "koord": koord(st["lemma"])}


def gruppen(paare: list[dict], idx: Strassenindex, koord, sichtungsstand: dict) -> list[dict]:
    """Fasst offene/mehrdeutige Paare je (strasse_norm, vorort) zusammen, nach Zeilenzahl absteigend."""
    g: dict[tuple[str, str], dict] = {}
    for p in paare:
        # Offene und mehrdeutige Paare; dazu die bereits am Plan verorteten (herkunft stadtplan_1935),
        # damit ein gesetzter Punkt nach dem nächsten Pipeline-Lauf im Werkzeug sichtbar und korrigierbar bleibt.
        if not p["strasse_norm"] or (p["herkunft"] not in ("offen", "stadtplan_1935") and p["mehrdeutig"] != "ja"):
            continue
        k = (p["strasse_norm"], p["vorort"])
        e = g.setdefault(k, {"strasse_norm": k[0], "vorort": k[1], "zeilen": 0, "teile": set(), "beispiele": set(),
                             "gruende": set(), "kandidaten_nr": []})
        e["zeilen"] += int(p["zeilen"])
        e["teile"].add(p["teil"])
        e["beispiele"].add(p["beispiel"])
        e["gruende"].add(p["grund_mehrdeutig"] or p["herkunft"])
        for nr in p["kandidaten"].split(";"):
            if nr and nr not in e["kandidaten_nr"]:
                e["kandidaten_nr"].append(nr)
    out = []
    for k, e in g.items():
        kandidaten = [s for nr in e["kandidaten_nr"][:MAX_KANDIDATEN] if (s := _strasse(idx, nr, "kandidat", koord))]
        gesehen = {s["schl_nr"] for s in kandidaten}
        for name, lemma, sim in idx.vorschlaege(k[0], MAX_VORSCHLAEGE):
            nr = (idx.heutig.get(name) or [z["schl_nr"] for z in idx.stadien.get(name, [])])[0]
            if nr not in gesehen and (s := _strasse(idx, nr, f"ähnlich: {name} ({sim:.2f})", koord)):
                kandidaten.append(s); gesehen.add(nr)
        vorort_schluessel = k[1] or STADTPLAN_KERNSTADT
        st = sichtungsstand.get((k[0], vorort_schluessel)) or sichtungsstand.get((k[0], k[1])) or {}
        out.append({"strasse_norm": k[0], "vorort": k[1], "vorort_schluessel": vorort_schluessel,
                    "zeilen": e["zeilen"], "teile": sorted(e["teile"]), "beispiele": sorted(e["beispiele"])[:3],
                    "gruende": sorted(e["gruende"]), "kandidaten": kandidaten, **st})
    out.sort(key=lambda e: (-e["zeilen"], e["strasse_norm"]))
    return out


def main(min_zeilen: int) -> None:
    W = projektwurzel()
    idx = Strassenindex(strassen_dir(), W / "kuratierung" / "strassen_zuordnung.csv", W / "kuratierung" / "strassen_1935.csv")
    client = Client(os.environ.get("NOMINATIM_URL", "http://localhost:8080"), W / "build" / "cache" / "nominatim.jsonl")
    cache: dict[str, list[str]] = {}

    def koord(lemma: str) -> list[str]:
        if lemma not in cache:
            cache[lemma] = strassen_koordinate(client, lemma)
        return cache[lemma]

    try:
        paare = [p for p in lies_csv(W / "build" / "03_strassen.csv") if int(p["zeilen"]) >= 1]
        st = stand(lies_csv(W / "kuratierung" / "strassen_1935.csv"), lies_csv(W / "kuratierung" / "strassen_zuordnung.csv"))
        liste = [e for e in gruppen(paare, idx, koord, st) if e["zeilen"] >= min_zeilen]
    finally:
        client.schliessen()
    ziel = W / "build" / "sichtung_1935.json"
    ziel.write_text(json.dumps({"erzeugt": dt.date.today().isoformat(), "gruppen": liste}, ensure_ascii=False), encoding="utf-8")
    offen = sum(1 for e in liste if not e.get("stand"))
    print(f"geschrieben: {ziel.relative_to(W)} ({len(liste)} Gruppen, {offen} ohne Sichtung, "
          f"{sum(e['zeilen'] for e in liste)} Zeilen; Nominatim {client.treffer}/{client.anfragen} aus Cache)")


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--min-zeilen") + 1]) if "--min-zeilen" in sys.argv else 1
    main(n)
