"""Eigentümer aus Teil II clustern (Teilprojekt 3, Spec §4).

Aufruf: python3 werkzeuge/eigentuemer_cluster.py [--min-haeuser 5]
Liest build/eintraege.csv, schreibt build/eigentuemer_vorschlag.csv und build/eigentuemer_belege.json
und legt fehlende Zeilen in kuratierung/eigentuemer.csv an (gesperrte Zeilen bleiben unberührt).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.lib.eigentuemer import (AUTOMATIK, FELDER_KURATIERUNG, STADTTEIL_AUF, gesperrt, lade_kuratierung,
                                      lade_stadtteil_liste, schreibweise_von)
from pipeline.lib.io import lies_csv, projektwurzel, schreib_csv

# Rechtsformen: Buchschreibungen wie „A.G.“, „A. G.“, „A.-G.“, „AG.“, „A. -G.“ → ein Token.
# Case-insensitiv nur in den eigenen Buchstaben (Scoped-Group `(?i:...)`), damit die nachfolgende
# Lookahead-Prüfung auf ein großgeschriebenes Wort case-sensitiv bleibt: Initialen vor einem Namen
# („A. G. Müller“) werden dadurch NICHT als Rechtsform erkannt, ein Namensanhang („Fried. Krupp A.G.“,
# „…A.G., Abt. II“) schon (Spec §4.2, Review-Fund Task 2 Runde 1).
def _rechtsform_muster(kern: str) -> re.Pattern:
    # Atomic Group `(?>...)`: verhindert, dass die Regex-Engine den optionalen End-Punkt
    # zurücknimmt, nur um die nachfolgende Lookahead-Prüfung zu umgehen (sonst würde
    # „A. G. Müller“ trotz Lookahead noch als „A. G“ + isoliertem Punkt erkannt).
    return re.compile(rf"(?>(?i:{kern}))(?!\s*[A-ZÄÖÜ][a-zäöüß])")


RECHTSFORMEN: list[tuple[re.Pattern, str]] = [
    (_rechtsform_muster(r"\be\.?\s?g\.?\s?m\.?\s?b\.?\s?h\b\.?"), "egmbh"),
    (_rechtsform_muster(r"\bg\.?\s?m\.?\s?b\.?\s?h\b\.?"), "gmbh"),
    (_rechtsform_muster(r"\ba\.?\s?-?\s?g\b\.?"), "ag"),
    (_rechtsform_muster(r"\be\.\s?v\b\.?"), "ev"),
    (_rechtsform_muster(r"\bk\.\s?-?\s?g\b\.?"), "kg"),
]
RECHTSFORM_TOKENS = {"egmbh", "gmbh", "ag", "ev", "kg", "ohg"}
ANZEIGE = {"egmbh": "eGmbH", "gmbh": "GmbH", "ag": "AG", "ev": "e. V.", "kg": "KG"}
STOPP = {"der", "die", "das", "und", "u", "von", "zu", "in", "für", "des"}

Katalog = dict


def lade_katalog(pfad: Path | str) -> Katalog:
    abk: dict[str, tuple[str, str]] = {}
    firmenwoerter: set[str] = set()
    for z in lies_csv(pfad):
        kurz, lang, kontext = (z.get("kurz") or "").strip().lower(), (z.get("lang") or "").strip().lower(), (z.get("kontext") or "").strip()
        if kurz:
            abk[kurz] = (lang, kontext)
        elif kontext == "firmenwort" and lang:
            firmenwoerter.add(lang)
    return dict(abk=abk, firmenwoerter=firmenwoerter)


def _rechtsformen(text: str) -> str:
    for muster, ersatz in RECHTSFORMEN:
        text = muster.sub(" " + ersatz + " ", text)
    return text


def normalisiere(name: str, katalog: Katalog) -> str:
    """Vergleichsschlüssel: klein, Rechtsformen vereinheitlicht, Abkürzungen (nur mit Punkt) aufgelöst,
    Komposita aus Firmenwörtern zusammengezogen, Interpunktion entfernt (Spec §4.2)."""
    t = unicodedata.normalize("NFKC", name)
    t = _rechtsformen(t)
    t = t.lower()
    t = t.replace(",", " ").replace("/", " ")
    roh = [x for x in re.split(r"\s+", t.strip()) if x]
    tokens: list[str] = []
    for i, tok in enumerate(roh):
        abgekuerzt = tok.endswith(".")
        kern = tok.strip(".-").lower()
        if not kern:
            continue
        eintrag = katalog["abk"].get(kern) if abgekuerzt else None
        if eintrag:
            lang, kontext = eintrag
            naechster = roh[i + 1].strip(".-") if i + 1 < len(roh) else ""
            if kontext == "firmenwort":
                folgt = katalog["abk"].get(naechster, (naechster, ""))[0] if roh[i + 1:] and roh[i + 1].endswith(".") else naechster
                if folgt in katalog["firmenwoerter"]:
                    kern = lang
            else:
                kern = lang
        tokens.append(kern)
    # Komposita: „bergwerks verein“ → „bergwerksverein“, wenn beide Teile Firmenwörter sind und das
    # zusammengesetzte Wort ebenfalls als Firmenwort geführt wird.
    out: list[str] = []
    for tok in tokens:
        if out and out[-1] in katalog["firmenwoerter"] and tok in katalog["firmenwoerter"] and (out[-1] + tok) in katalog["firmenwoerter"]:
            out[-1] = out[-1] + tok
        else:
            out.append(tok)
    return re.sub(r"[^\w\s]", "", " ".join(out)).strip()


def rechtsform_anzeige(name: str) -> str:
    """Auto-Name-Hilfe: Rechtsform im Anzeigenamen vereinheitlichen, Rest unverändert (Spec §4.4)."""
    t = name
    for muster, ersatz in RECHTSFORMEN:
        t = muster.sub(" " + ANZEIGE[ersatz] + " ", t)
    t = re.sub(r"\s*,\s*(AG|GmbH|eGmbH|KG|e\. V\.)\b", r" \1", t)
    return re.sub(r"\s+", " ", t).strip()


from rapidfuzz import fuzz


def cluster_id(schluessel: str) -> str:
    return hashlib.sha1(schluessel.encode("utf-8")).hexdigest()[:10]


def auto_name(mitglieder: list[tuple[str, int]]) -> str:
    """Häufigste Schreibweise mit vereinheitlichter Rechtsform (Spec §4.4)."""
    return rechtsform_anzeige(max(mitglieder, key=lambda m: (m[1], -len(m[0])))[0])


def _block(schluessel: str) -> str:
    for tok in schluessel.split():
        if tok not in RECHTSFORM_TOKENS and tok not in STOPP:
            return tok
    return schluessel


def _sim(a: str, b: str) -> float:
    # token_sort_ratio statt token_set_ratio: bei Teilmengen („… Schacht 3“) liefert token_set_ratio 1,0
    # und würde Teilanlagen in die Zeche mergen; precision first (Ruling Vorprüfung).
    return fuzz.token_sort_ratio(a, b) / 100.0


# Zahlen-Wächter (Spec §4.3/Fund F3): reine Zahl-Token und römische Ziffern ii–iv, wie sie
# Hausnummern („Adolf-Hitler-Straße 19“ vs. „… 81“, Ähnlichkeit 0,95) oder Zählungen
# („Ev. Schule“ vs. „Ev. Schule II“) unterscheiden. token_sort_ratio allein hält solche Paare
# nicht auseinander; ein Merge mit unterschiedlichen Zahl-Token bliebe unbelegt (precision first).
_ZAHL_TOKEN = re.compile(r"^(\d+|ii|iii|iv)$")


def _zahlentoken(schluessel: str) -> frozenset[str]:
    return frozenset(t for t in schluessel.split() if _ZAHL_TOKEN.fullmatch(t))


def _numerisch_vertraeglich(a: str, b: str) -> bool:
    return _zahlentoken(a) == _zahlentoken(b)


def clustere(zaehler: dict[str, int], katalog: Katalog, schwelle: float = 0.92, vorschlag_ab: float = 0.75) -> list[dict]:
    """Schreibweise → Anzahl zu Clustern (Spec §4.3): exakt gleicher Schlüssel, dann Complete-Linkage
    innerhalb eines Blocks (erstes signifikantes Token); Grenzfälle als vorschlag_fuer."""
    # 1. exakte Gruppen
    gruppen: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for s, n in zaehler.items():
        gruppen[normalisiere(s, katalog)].append((s, n))
    cluster: list[dict] = [dict(schluessel=[k], mitglieder=sorted(m, key=lambda x: (-x[1], x[0])), aehnlichkeit=1.0)
                           for k, m in gruppen.items()]
    # 2. Complete-Linkage je Block
    bloecke: dict[str, list[dict]] = defaultdict(list)
    for c in cluster:
        bloecke[_block(c["schluessel"][0])].append(c)
    fertig: list[dict] = []
    for block in bloecke.values():
        aktiv = list(block)
        while True:
            bestes = None
            for i in range(len(aktiv)):
                for j in range(i + 1, len(aktiv)):
                    mn = min(_sim(a, b) for a in aktiv[i]["schluessel"] for b in aktiv[j]["schluessel"])
                    vertraeglich = all(_numerisch_vertraeglich(a, b) for a in aktiv[i]["schluessel"] for b in aktiv[j]["schluessel"])
                    if mn >= schwelle and vertraeglich and (bestes is None or mn > bestes[0]):
                        bestes = (mn, i, j)
            if bestes is None:
                break
            mn, i, j = bestes
            a, b = aktiv[i], aktiv[j]
            neu = dict(schluessel=a["schluessel"] + b["schluessel"],
                       mitglieder=sorted(a["mitglieder"] + b["mitglieder"], key=lambda x: (-x[1], x[0])),
                       aehnlichkeit=min(a["aehnlichkeit"], b["aehnlichkeit"], mn))
            aktiv = [c for k, c in enumerate(aktiv) if k not in (i, j)] + [neu]
        for c in aktiv:
            c["haeuser"] = sum(n for _, n in c["mitglieder"])
            c["name"] = auto_name(c["mitglieder"])
            c["id"] = cluster_id(normalisiere(c["mitglieder"][0][0], katalog))
            c["vorschlag_fuer"] = ""
        # 3. Grenzfälle: kleinerer Cluster → Vorschlag auf den größeren mit der höchsten Ähnlichkeit
        for i in range(len(aktiv)):
            for j in range(len(aktiv)):
                if i == j:
                    continue
                klein, gross = aktiv[i], aktiv[j]
                if (gross["haeuser"], gross["name"]) <= (klein["haeuser"], klein["name"]):
                    continue
                mx = max(_sim(a, b) for a in klein["schluessel"] for b in gross["schluessel"])
                # Zahlen-Wächter: unterscheiden sich alle Paare in ihren Zahl-Token, war die Fusion oben
                # blockiert, egal wie hoch die Ähnlichkeit — der Deckel `schwelle` entfällt dann.
                vertraeglich = all(_numerisch_vertraeglich(a, b) for a in klein["schluessel"] for b in gross["schluessel"])
                obergrenze = schwelle if vertraeglich else 1.0 + 1e-9
                if vorschlag_ab <= mx < obergrenze and mx > klein.get("_vorschlag_sim", 0.0):
                    klein["vorschlag_fuer"], klein["_vorschlag_sim"] = gross["id"], mx
        fertig.extend(aktiv)
    for c in fertig:
        c.pop("_vorschlag_sim", None)
        c["schluessel"] = c["schluessel"][0]
        c["aehnlichkeit"] = round(c["aehnlichkeit"], 3)
    return sorted(fertig, key=lambda c: (-c["haeuser"], c["name"]))


VORSCHLAG_FELDER = ["schreibweise", "art", "anzahl", "cluster_id", "cluster_name", "aehnlichkeit", "vorschlag_fuer", "pruefpflichtig"]


def _zahl(v: str):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def sammle(eintraege: list[dict], nach_stadtteil: frozenset[str] = frozenset()) -> tuple[dict[str, int], dict[str, int], dict[str, list[dict]]]:
    """Teil-II-Zeilen → (Zähler Körperschaften, Zähler Personen, Belege je Schreibweise, Spec §3.2)."""
    koerper: dict[str, int] = defaultdict(int)
    personen: dict[str, int] = defaultdict(int)
    belege: dict[str, list[dict]] = defaultdict(list)
    for e in eintraege:
        if e.get("teil") != "II":
            continue
        s, art = schreibweise_von(e, nach_stadtteil)
        if not s:
            continue
        (koerper if art == "koerperschaft" else personen)[s] += 1
        nr = ((e.get("hausnr") or "") + (e.get("hausnr_zusatz") or "")).strip()
        belege[s].append(dict(id=e.get("id", ""), adresse=" ".join(x for x in (e.get("strasse_roh", ""), nr) if x),
                              stadtteil=e.get("stadtteil", "") or e.get("Vorort", ""), verwalter=e.get("Verwalter", ""),
                              seite=e.get("page", ""), lat=_zahl(e.get("lat")), lon=_zahl(e.get("lon")), stufe=e.get("stufe", "")))
    return dict(koerper), dict(personen), dict(belege)


def vorschlagszeilen(cluster: list[dict], personen: dict[str, int], min_haeuser: int) -> list[dict]:
    zeilen: list[dict] = []
    for c in cluster:
        for s, n in c["mitglieder"]:
            # Stadtteil-Schreibweisen sind immer prüfpflichtig — sie entstehen nur, um von Hand zugeordnet zu werden.
            pflicht = c["haeuser"] >= min_haeuser or STADTTEIL_AUF in s
            zeilen.append(dict(schreibweise=s, art="koerperschaft", anzahl=str(n), cluster_id=c["id"], cluster_name=c["name"],
                               aehnlichkeit=str(c["aehnlichkeit"]), vorschlag_fuer=c["vorschlag_fuer"],
                               pruefpflichtig="ja" if pflicht else "nein", _haeuser=c["haeuser"]))
    for s, n in personen.items():
        zeilen.append(dict(schreibweise=s, art="person", anzahl=str(n), cluster_id=cluster_id(s), cluster_name=s,
                           aehnlichkeit="1.0", vorschlag_fuer="", pruefpflichtig="ja" if n >= min_haeuser else "nein", _haeuser=n))
    zeilen.sort(key=lambda z: (-z["_haeuser"], z["art"], z["cluster_name"], -int(z["anzahl"]), z["schreibweise"]))
    for z in zeilen:
        z.pop("_haeuser")
    return zeilen


def aktualisiere_kuratierung(alt: list[dict], vorschlag: list[dict], datum: str) -> list[dict]:
    """Gesperrte Zeilen (geprüft oder vom Menschen angefasst) bleiben; Automatik-Zeilen bekommen den neuen
    Vorschlag (Kategorie und Hinweis bleiben); Fehlendes wird angehängt; Verwaistes bleibt stehen."""
    bekannt = lade_kuratierung(alt)
    out: list[dict] = [dict(z) for z in alt]
    index = {z["schreibweise"].strip(): i for i, z in enumerate(out)}
    for v in vorschlag:
        s = v["schreibweise"]
        if s in bekannt:
            if gesperrt(bekannt[s]):
                continue
            z = out[index[s]]
            if z.get("eigentuemer", "").strip() != v["cluster_name"]:
                z.update(eigentuemer=v["cluster_name"], datum=datum)
        else:
            # Spec §3.3: neue Personen-Zeilen nur ab der Prüfpflicht-Untergrenze; Körperschaften immer.
            if v["art"] == "person" and v.get("pruefpflichtig", "ja") != "ja":
                continue
            # Stadtteil-Aufteilung („Kath. Kirchengem. ‹Katernberg›“): Kategorie der einfachen Schreibweise erben,
            # den Namen aber nicht — der ist ja gerade je Stadtteil zu entscheiden.
            basis = bekannt.get(s.split(STADTTEIL_AUF)[0]) if STADTTEIL_AUF in s else None
            kategorie = "privatperson" if v["art"] == "person" else (basis or {}).get("kategorie", "")
            out.append(dict(schreibweise=s, art=v["art"], eigentuemer=v["cluster_name"], kategorie=kategorie, geprueft="",
                            bearbeiter=AUTOMATIK, datum=datum, hinweis="", identitaet=""))
    return out


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-haeuser", type=int, default=5)
    ap.add_argument("--wurzel", default=None, help="Projektwurzel (Tests)")
    a = ap.parse_args(argv)
    W = Path(a.wurzel) if a.wurzel else projektwurzel()
    katalog = lade_katalog(W / "kuratierung" / "eigentuemer_abkuerzungen.csv")
    st_pfad = W / "kuratierung" / "eigentuemer_stadtteil.csv"
    nach_stadtteil = lade_stadtteil_liste(lies_csv(st_pfad)) if st_pfad.exists() else frozenset()
    koerper, personen, belege = sammle(lies_csv(W / "build" / "eintraege.csv"), nach_stadtteil)
    cluster = clustere(koerper, katalog)
    vorschlag = vorschlagszeilen(cluster, personen, a.min_haeuser)
    schreib_csv(W / "build" / "eigentuemer_vorschlag.csv", vorschlag, VORSCHLAG_FELDER)
    (W / "build" / "eigentuemer_belege.json").write_text(json.dumps(belege, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    pfad = W / "kuratierung" / "eigentuemer.csv"
    alt = lies_csv(pfad) if pfad.exists() else []
    neu = aktualisiere_kuratierung(alt, vorschlag, datetime.date.today().isoformat())
    schreib_csv(pfad, neu, FELDER_KURATIERUNG)
    k = dict(koerperschaften=len(cluster), schreibweisen=len(koerper), personen=len(personen),
             pruefpflichtig=sum(1 for c in cluster if c["haeuser"] >= a.min_haeuser) + sum(1 for n in personen.values() if n >= a.min_haeuser),
             pruefpflichtig_koerperschaften=sum(1 for c in cluster if c["haeuser"] >= a.min_haeuser),
             haeuser_pruefpflichtig=sum(c["haeuser"] for c in cluster if c["haeuser"] >= a.min_haeuser),
             haeuser_koerperschaften=sum(koerper.values()), vorschlaege=sum(1 for c in cluster if c["vorschlag_fuer"]),
             kuratierung_zeilen=len(neu))
    print(json.dumps(k, ensure_ascii=False, indent=1))
    return k


if __name__ == "__main__":
    main()
