"""Soziale Stellung je Berufsschreibweise (Teilprojekt 5, Spec §5.1) — Vokabular, Vorschlagsregeln, Exportregel.

Vorbild ist die „Stellung im Beruf“ der Berufszählungen 1933/1939. Die Regeln liefern nur Vorschläge; entschieden
wird im Werkzeug (`stellung_geprueft=ja`). Reihenfolge der Regeln = Reihenfolge in `stellung_vorschlag`; die
Doku in docs/stellung.md beschreibt jede Regel mit Beispielen.
"""
from __future__ import annotations

import re

from pipeline.lib.berufe import falte_form
from pipeline.lib.merkmale import Regel, merkmale_fuer

STELLUNGEN = {
    "arbeiter": "Arbeiter",
    "angestellte": "Angestellte",
    "beamte": "Beamte",
    "selbstaendige": "Selbständige (Handwerk, Handel, Gastgewerbe)",
    "freie_berufe": "Freie Berufe und Akademiker",
    "unternehmer": "Unternehmer und Leitende",
    "ohne_erwerb": "Ohne Erwerbsberuf",
    "kaufleute": "Kaufleute (Stellung unbestimmt)",
    "unbestimmt": "unbestimmt",
}
UNBESTIMMT = "unbestimmt"

# Meister im Handwerk (selbständig) — Stamm vor „meister“/„mstr.“; alle anderen Meister (Werk-, Betriebs-,
# Fahr-, Zug-, Bahnmeister …) sind betriebliche Vorgesetzte, also Angestellte.
_HANDWERK = ("bäcker", "metzger", "schlachter", "fleischer", "konditor", "schneider", "schuhmacher", "friseur", "maler",
             "anstreicher", "tischler", "schreiner", "klempner", "installateur", "dachdecker",
             "maurer", "zimmer", "stukkateur", "glaser", "sattler", "polsterer", "tapezier", "uhrmacher", "gold",
             "buchbinder", "drucker", "gärtner", "fuhr", "elektro", "schornsteinfeger", "kürschner", "hut", "korb",
             "stellmacher", "wagner", "böttcher", "küfer", "müller", "mühlen", "brauer", "gerber", "seiler", "töpfer",
             "ofensetzer", "steinmetz", "bildhauer", "graveur", "optiker", "fotograf")
# Meister in Industrieberufen: in Essen (Krupp, Zechen) überwiegend Betriebsmeister, teils Inhaber — die Deckungstabelle
# (docs/stellung_deckung.md) zeigt mehr Meister als Betriebe in Teil III. Entscheidung 2026-09-25: offen lassen.
_INDUSTRIE = ("schmied", "schlosser", "dreher", "mechaniker")
_HANDWERK_GEFALTET = tuple(falte_form(h) for h in _HANDWERK)
_INDUSTRIE_GEFALTET = tuple(falte_form(h) for h in _INDUSTRIE)
# Erwerbsquelle statt Beruf: die Berufszählung 1933 zählt Hausbesitzer, Rentiers, Privatiers ohne anderen Beruf als
# „berufslose Selbständige“ zu den Berufslosen — hier ohne_erwerb, das damit bewusst heterogen ist (docs/stellung.md).
_OHNE_ERWERB = re.compile(r"hausbesitzer|rentier|privatier", re.I)
# Straßenbahn Essen 1936 = private Süddeutsche Eisenbahn-Gesellschaft; Fahrpersonal versicherungsrechtlich Arbeiter.
_STRASSENBAHN = re.compile(r"stra(ß|ss)enbahn", re.I)
# Dienstposten der Reichsbahn, die Beamte des einfachen Dienstes wie Arbeiter besetzten, und Schaffner ohne Zusatz
# (Straßenbahn oder Bahn?) — nicht entscheidbar (Entscheidung 2026-09-25, docs/stellung.md Grenzfälle).
_DIENSTPOSTEN = re.compile(r"weichenwärter|weichensteller|bahnwärter|schrankenwärter|streckenwärter|^eisenbahner|^schaffner", re.I)
_MEISTER = re.compile(r"(meister(in)?|mstr(in)?\.?)$", re.I)   # auch „…mstrin.“ (weibliche Kurzform)
_FREIE = re.compile(r"arzt|ärzt|zahnarzt|dentist|tierarzt|apotheker|rechtsanwalt|anwalt|notar|architekt|patentanwalt|"
                    r"wirtschaftsprüfer|steuerberater|bücherrevisor|schriftsteller|künstler|kunstmaler|bildhauer/in$", re.I)
# Bewusste Abweichung von der Berufszählung (die Direktoren als leitende Angestellte führt): Inhaber und Leitende
# bilden eine eigene Klasse, weil die Leitfragen sonst Fabrikanten und Bäckermeister nicht unterscheiden könnten.
# Prokuristen bleiben Angestellte (Handlungsbevollmächtigte, AVG 1911 § 1).
_UNTERNEHMER = re.compile(r"fabrikant|fabrikbesitzer|(?<!studien)(?<!kataster)direktor|generaldirektor|vorstand|geschäftsführer|"
                          r"inhaber|unternehmer|bergwerksbesitzer|gutsbesitzer", re.I)
# „oberst“ nur als eigenes Wort (nicht als Präfix in „Obersteiger“) — sonst Fehltreffer aus dem OhdAB-Gattungstext.
_BEAMTE = re.compile(r"beamt|sekretär|inspektor|assistent|amtmann|\brat\b|rätin|schaffner|zugführer|lokomotivführer|"
                     r"briefträger|postbote|polizei|schutzmann|wachtmeister|zoll|richter|pfarrer|pastor|geistlich|kaplan|vikar|"
                     r"feuerwehr|rangiermeister|rangieraufseher|"
                     r"\boberst\b|major|hauptmann|förster|gerichtsvollzieher|studiendirektor|katasterdirektor|"
                     r"\(.*dienst\)", re.I)
# „lehrer“/„offizier“ nur im eigenen Titel (Norm/Beruf), nicht in der OhdAB-Gattung — sonst Fehltreffer wie
# „Trainer“ über die Gattung „Sportlehrer/innen“ oder „Rottenführer“ über „Unteroffiziere ohne Portepee“.
_BEAMTE_TITEL = re.compile(r"lehrer|offizier", re.I)
_ANGESTELLTE = re.compile(r"angestellt|buchhalter|kontorist|techniker|ingenieur|steiger|zeichner|verkäufer|handlungsgehilf|"
                          r"kassierer|vertreter|reisender|bürogehilf|stenotypist|laborant|chemiker|betriebsführer|prokurist|"
                          r"abteilungsleiter|filialleiter|disponent|expedient|magazinverwalter|werkführer|obersteiger", re.I)
_SELBSTAENDIGE = re.compile(r"händler|handel|wirt(in)?$|gastwirt|schankwirt|krämer|fuhrmann|kaufmann/-frau -|kaufmann/-frau \(|"
                            r"hausierer|agent|makler|kommissionär|verleger|drogist|hebamme|masseur|heilpraktiker|"
                            r"landwirt(?!schaftlich)|bauer|kötter|pächter|fischer|schiffer", re.I)


def _norm(item: dict | None) -> str:
    return (item or {}).get("norm", "")


def _text(zeile: dict, item: dict | None) -> str:
    """Prüftext = Normbezeichnung + Gattung + aufgelöster Beruf (Schreibweise selbst nur für Meister/Titel)."""
    return " | ".join(x for x in (_norm(item), (item or {}).get("gattung", ""), zeile.get("beruf", "")) if x)


def _titel(zeile: dict, item: dict | None) -> str:
    """Prüftext ohne Gattung: nur Normbezeichnung und aufgelöster Beruf — für Merkmale, die in der OhdAB-Gattung
    nur zufällig als Wortbestandteil vorkommen können (Spec-Review TP5a: „Trainer“ über „Sportlehrer“-Gattung)."""
    return " | ".join(x for x in (_norm(item), zeile.get("beruf", "")) if x)


def stellung_vorschlag(zeile: dict, item: dict | None, regeln: list[Regel]) -> tuple[str, str]:
    """(Klasse, Grund) nach der ersten treffenden Regel; ohne Treffer („unbestimmt“, „“)."""
    status = [s.strip() for s in (zeile.get("status") or "").split(";") if s.strip()]
    text = _text(zeile, item)
    schreibweise = zeile.get("schreibweise", "")
    if any(s in ("ruhestand", "invalide", "witwe") for s in status):
        return "ohne_erwerb", "status"
    if (item or {}).get("gattung_id", "").startswith("A 1"):
        return "ohne_erwerb", "item A 1"
    if "gewerbe" in status:
        return "selbstaendige", "gewerbe"
    if _MEISTER.search(schreibweise) or _MEISTER.search(_norm(item)):
        if _BEAMTE.search(text) or _BEAMTE_TITEL.search(_titel(zeile, item)):
            return "beamte", "beamte"
        # Stamm in Schreibweise UND Normbezeichnung suchen — „Schuhmmstr.“ trägt den Stamm nur im Item „Schuhmachermeister/in“.
        stamm = falte_form(schreibweise) + " " + falte_form(_norm(item))
        if any(h in stamm for h in _INDUSTRIE_GEFALTET):
            return UNBESTIMMT, "industriemeister"
        return ("selbstaendige", "handwerksmeister") if any(h in stamm for h in _HANDWERK_GEFALTET) else ("angestellte", "betriebsmeister")
    if "akademiker" in merkmale_fuer({"Beruf o. ä.": schreibweise}, regeln):
        return "freie_berufe", "akademiker"
    if _FREIE.search(_norm(item)):
        return "freie_berufe", "freier beruf"
    if _OHNE_ERWERB.search(_norm(item)):
        return "ohne_erwerb", "erwerbsquelle"
    if _STRASSENBAHN.search(_titel(zeile, item)):
        return "arbeiter", "strassenbahn"
    if _DIENSTPOSTEN.search(_norm(item)):
        return UNBESTIMMT, "dienstposten"
    if _UNTERNEHMER.search(text):
        return "unternehmer", "unternehmer"
    if falte_form(_norm(item)) == "kaufmann frau" and not re.search(r"angest|beamt", text, re.I):
        return "kaufleute", "kaufmann"
    if _ANGESTELLTE.search(text) and not (_BEAMTE.search(_norm(item)) or _BEAMTE_TITEL.search(_titel(zeile, item))):
        return "angestellte", "angestellte"
    if _BEAMTE.search(text) or _BEAMTE_TITEL.search(_titel(zeile, item)):
        return "beamte", "beamte"
    if _SELBSTAENDIGE.search(_norm(item)):
        return "selbstaendige", "selbstaendig"
    niveau = (item or {}).get("niveau", "")
    if niveau in ("spezialist", "aufsicht") or (item or {}).get("gattung", "").startswith("Aufsichtskräfte"):
        return "angestellte", "angestellte"
    if niveau in ("helfer", "fachlich"):
        return "arbeiter", f"niveau {niveau}"
    return UNBESTIMMT, ""


def stellung_export(zeile: dict) -> str:
    """Export nur, wenn Beruf und Stellung geprüft sind (Spec §5.1); sonst „unbestimmt“."""
    if zeile.get("geprueft") == "ja" and zeile.get("stellung_geprueft") == "ja" and zeile.get("stellung") in STELLUNGEN:
        return zeile["stellung"]
    return UNBESTIMMT
