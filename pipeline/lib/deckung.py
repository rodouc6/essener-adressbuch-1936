"""Deckung Handwerksberufe: Wie viele Betriebe in Teil III erklären die als Inhaber gekennzeichneten Einträge
in Teil I nicht — und wie groß ist damit die Unschärfe der Schreibweise ohne Zusatz („Friseur“, „Schneider“)?

Grundlage der Handprüfung nach Weg 3 (docs/stellung.md, Grenzfälle): je Berufsfamilie
  offen    = Nennungen ohne Meister-/Gewerbezusatz mit Stellung arbeiter|unbestimmt
  inhaber  = Nennungen mit Stellung selbstaendige (Meister- und Gewerbeformen)
  betriebe = Betriebe der passenden Rubriken in Teil III (erstes Wort der Rubrik; Bedarf/Maschinen/… ausgeschlossen)
  luecke   = max(0, betriebe - inhaber)   → Betriebe, die kein gekennzeichneter Eintrag erklärt
  quote    = luecke / offen               → Anteil der offenen Nennungen, der mindestens Inhaber sein muss
Empfehlung: quote < SCHWELLE → „arbeiter“ bestätigen, sonst „unbestimmt“ bis zum Adressabgleich Teil I ↔ Teil III.
Aufgenommen werden nur Familien mit Betrieben in Teil III und (Inhaberform in Teil I oder offen ≥ MIN_OFFEN).
Die Zuordnung Rubrik ↔ Beruf ist eine Heuristik; die Tabelle nennt die getroffenen Rubriken, damit sie prüfbar bleibt.
"""
import re
from collections import defaultdict

from pipeline.lib.berufe import falte_form

SCHWELLE = 0.10      # Quote, ab der die Schreibweise ohne Zusatz offen bleibt
MIN_OFFEN = 50       # Familien ohne Inhaberform in Teil I nur ab so vielen offenen Nennungen

# Synonyme Teil I ↔ Teil III; Schlüssel = Familienname (gefaltet).
_SYNONYME = {
    "schreiner": ("tischler",), "maler": ("anstreicher",), "metzger": ("fleischer", "schlachter"),
    "klempner": ("installateur",), "fotograf": ("photograph",), "zimmerer": ("zimmermann", "zimmer"),
    "stellmacher": ("wagner",), "kuefer": ("boettcher",), "friseur": ("frisoer",), "schmied": ("schmiede",),
}
_SYNONYM_ZU = {s: f for f, ss in _SYNONYME.items() for s in ss}
_ZUSATZ = re.compile(r"(meisterin|meister|mstrin|mstr|ei)$")
_NICHT_BETRIEB = re.compile(r"bedarf|maschine|material|werkzeug|artikel|schule|einricht|apparat|zubeh|ger[äa]t|waren$", re.I)
_OFFEN = ("arbeiter", "unbestimmt")


def familie_von(beruf: str) -> str:
    """Gefalteter Stamm ohne Meister-/Gewerbezusatz, Synonyme zusammengeführt („Tischler“ → „schreiner“)."""
    stamm = _ZUSATZ.sub("", falte_form(beruf).replace(" ", ""))
    return _SYNONYM_ZU.get(stamm, stamm)


def rubrik_familie(rubrik: str) -> str | None:
    """Familie einer Teil-III-Rubrik nach ihrem ersten Wort; Bedarfs-, Maschinen-, Schul-Rubriken sind keine Betriebe."""
    if _NICHT_BETRIEB.search(rubrik):
        return None
    erstes = re.split(r"[\s(,/]", rubrik.strip(), 1)[0]
    return familie_von(erstes) if erstes else None


def _falte_weiblich(familien: dict[str, list]) -> dict[str, list]:
    """„schneiderin“ zu „schneider“, wenn die männliche Familie vorkommt."""
    out = defaultdict(list)
    for f, zeilen in familien.items():
        ziel = f[:-2] if f.endswith("in") and f[:-2] in familien else f
        out[ziel].extend(zeilen)
    return out


def deckung(berufe: list[dict], gewerbe: list[dict]) -> list[dict]:
    """Eine Zeile je Familie mit Inhaberform oder Rubrik, sortiert nach Quote absteigend (None zuletzt)."""
    fam = defaultdict(list)
    for z in berufe:
        if z.get("beruf"):
            fam[familie_von(z["beruf"])].append(z)
    fam = _falte_weiblich(fam)
    rub = defaultdict(list)
    for g in gewerbe:
        f = rubrik_familie(g.get("rubrik", ""))
        if f:
            rub[f].append(g)
    rub = _falte_weiblich(rub)
    out = []
    for f, zeilen in fam.items():
        offen_z = [z for z in zeilen if z.get("stellung") in _OFFEN]
        offen = sum(int(z["nennungen"]) for z in offen_z)
        inhaber = sum(int(z["nennungen"]) for z in zeilen if z.get("stellung") == "selbstaendige")
        betriebe = sum(int(g["betriebe"]) for g in rub.get(f, []))
        # Nur Familien, in denen Teil I eine Inhaberform kennt oder die offene Menge ins Gewicht fällt — sonst
        # erzeugen Einzelnennungen wie „Steuerberatung“ (5) gegen 80 Betriebe Scheinquoten.
        if not betriebe or (not inhaber and offen < MIN_OFFEN):
            continue
        luecke = max(0, betriebe - inhaber)
        quote = round(luecke / offen, 3) if offen else None
        empfehlung = "" if quote is None else ("arbeiter" if quote < SCHWELLE else "unbestimmt")
        out.append({"familie": f, "offen": offen, "inhaber": inhaber, "betriebe": betriebe, "luecke": luecke, "quote": quote,
                    "empfehlung": empfehlung, "rubriken": [g["rubrik"] for g in rub.get(f, [])],
                    "schreibweisen_offen": [z["schreibweise"] for z in offen_z]})
    out.sort(key=lambda r: (r["quote"] is None, -(r["quote"] or 0), -r["offen"]))
    return out
