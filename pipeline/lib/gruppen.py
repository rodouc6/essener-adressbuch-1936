"""Berufsgruppen (Branche) je OhdAB-Item (Teilprojekt 5a, Spec §5.2): Vokabular, Vorschlag aus Gattung/Norm, Export."""
from __future__ import annotations

import re

GRUPPEN = {
    "bergbau": "Bergbau und Kokerei",
    "metall_maschinen": "Metall, Maschinen, Elektro",
    "bau": "Bau",
    "holz_moebel": "Holz und Möbel",
    "textil_bekleidung": "Textil und Bekleidung",
    "lebensmittel": "Lebensmittel",
    "handel": "Handel",
    "gastgewerbe": "Gastgewerbe",
    "verkehr_bahn_post": "Verkehr, Bahn, Post",
    "verwaltung": "Verwaltung, Polizei, Recht",
    "bildung_kultur_kirche": "Bildung, Kultur, Kirche",
    "gesundheit": "Gesundheit",
    "haus_reinigung": "Haushalt und Reinigung",
    "sonstige": "Sonstige",
}
UNGEPRUEFT = "ungeprueft"
FELDER_GRUPPEN = ["ohdab_id", "norm", "nennungen", "gruppe", "geprueft", "bearbeiter", "datum", "hinweis"]
AUTOMATIK = "gruppen_vorschlag"

# Reihenfolge = Priorität; geprüft wird Gattung + Norm.
_REGELN = [
    # „hauer“ ohne Wortgrenze zog Bildhauer, Feilenhauer, Steinhauer, Trichinenschauer (über „schauer“) und
    # Zimmerhauer fälschlich nach bergbau — echte Bergbauberufe tragen ohnehin die Berg-/Tagebau-Gattung
    # (Review TP5a Task 2). Ausgenommen bleibt „Lehrhauer/in“, der dadurch in eine andere Gruppe fällt.
    ("bergbau", r"berg- und tagebau|bergbau|kokerei|sprengtechnik|grube|zeche|steiger"),
    ("verkehr_bahn_post", r"eisenbahn|bahn|post|zustell|triebfahrzeug|fahrzeugführ|kraftfahr|straßenbahn|schiff|verkehr|lager|fuhr|kutsch|schaffner|autovermiet"),
    ("verwaltung", r"öffentliche verwaltung|polizei|justiz|recht|steuer|zoll|verwaltungs|sekretär|beamt|\bgericht|feuerwehr|militär|soldat|bürovorsteher|büroangestellt|bürogehilf|bürodiener|büroassistent|kontorist|amtmann|revisor"),
    ("bildung_kultur_kirche", r"lehrkr|lehrer|erzieh|hochschul|wissenschaft|theolog|seelsorg|pfarrer|kirche|kunst|musik|schauspiel|bibliothek|schriftsteller|journalist|redakt|schriftsetz|fotograf|buchbind|schulrektor|klavier"),
    ("gesundheit", r"ärzt|arzt|apothek|geburtshilf|hebamme|pflege|krankenpfleg|heilpraktik|zahn|masseur|gesundheit|dentist|tierarzt"),
    ("gastgewerbe", r"gastronomie|gastwirt|schankwirt|hotel|kellner|koch|köchin|pension"),
    ("lebensmittel", r"backwaren|bäcker|konditor|fleisch|metzger|schlachter|lebensmittel|getränke|brau|molkerei|müller|mühle|nahrungsmittel"),
    ("handel", r"kaufleute|handel|verkauf|händler|kaufmann|verkäufer|drogist|kommission|makler|agent"),
    ("textil_bekleidung", r"bekleidung|textil|schneider|näh|weber|spinn|schuh|hut|kürschner|wäsche|sattler|polster"),
    ("holz_moebel", r"holz|möbel|tischler|schreiner|zimmer|drechsler|böttcher|stellmacher|korb"),
    ("metall_maschinen", r"metall|maschinen|schlosser|dreher|schweiß|gießer|hütten|walz|schmied|elektr|mechanik|monteur|heizer|kessel|anlagen|produktion|fabrik|technik|ingenieur|chem|uhrmacher|kranführ|konstrukt"),
    # „bau“ nur mit Wortgrenze am ANFANG (wie beim „gericht“-Fix: \bgericht statt gericht) — trifft
    # damit „Bauzeichner“, „Baustoffherstellung“, „Bausachverständige“ (Wort beginnt mit „bau“),
    # aber NICHT „Gartenbau“ (Gärtner → bewusst haus_reinigung, wie in gewerbe.py), „Gerätebau“
    # (Konstrukteur → metall_maschinen, siehe oben) oder „Ackerbauer“ (Landwirtschaft → keine eigene
    # Gruppe, bleibt bewusst sonstige) — dort steht „bau“ nicht am Wortanfang. Ruling Fix-Runde 2.
    ("bau", r"\bbau|hochbau|tiefbau|rohrleitungsbau|luftheizungsbau|ofen.*bau|beton|maurer|dachdeck|maler|anstreich|glaser|stukkat|stuckat|installat|klempner|schornstein|fliesen|ofensetz|architekt|pflaster"),
    ("haus_reinigung", r"hauswirtschaft|hausangestellt|dienstmädchen|reinigung|wäscher|plätt|hausmeister|portier|wächter|friseur|gärtner|gartenbau"),
]


def gruppe_vorschlag(item: dict) -> str:
    text = f"{item.get('gattung', '')} | {item.get('norm', '')}".lower()
    for gruppe, muster in _REGELN:
        if re.search(muster, text):
            return gruppe
    return "sonstige"


def lade_gruppen(zeilen: list[dict]) -> dict[str, dict]:
    return {z["ohdab_id"].strip(): {k: (v or "").strip() for k, v in z.items()} for z in zeilen if (z.get("ohdab_id") or "").strip()}


def gruppe_export(zeile: dict | None) -> str:
    if zeile and zeile.get("geprueft") == "ja" and zeile.get("gruppe") in GRUPPEN:
        return zeile["gruppe"]
    return UNGEPRUEFT
