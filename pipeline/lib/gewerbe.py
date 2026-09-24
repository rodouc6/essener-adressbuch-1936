"""Gewerberubriken aus Teil III (Teilprojekt 5a, Spec §5.3). Die Rubrik steht nicht in einer eigenen Spalte, sondern
als Suffix hinter dem letzten Komma des Firmennamens („M. Jäger, Althandlung“)."""
from __future__ import annotations

import re

from pipeline.lib.gruppen import GRUPPEN  # noqa: F401 — gleiche Gruppen wie Teil I, damit beide vergleichbar sind
from pipeline.lib.berufe import falte_form

ARTEN = {"handwerk": "Handwerk", "handel": "Handel", "gastgewerbe": "Gastgewerbe", "dienstleistung": "Dienstleistung",
         "industrie": "Industrie", "freier_beruf": "Freier Beruf", "sonstige": "Sonstige"}
UNGEPRUEFT = "ungeprueft"
FELDER_GEWERBE = ["rubrik", "betriebe", "gruppe", "art", "geprueft", "bearbeiter", "datum", "hinweis"]
AUTOMATIK = "gewerbe_vorschlag"


def rubrik_von(firmenname: str) -> tuple[str, str]:
    """(Firma ohne Suffix, Rubrik). Ohne Komma keine Rubrik."""
    f = (firmenname or "").strip()
    if "," not in f:
        return f, ""
    firma, rubrik = f.rsplit(",", 1)
    return firma.strip(), rubrik.strip()


# (Gruppe, Art, Muster) — erste Regel gewinnt; Art-Regeln nach Wortform am Ende.
_REGELN = [
    ("bergbau", "handel", r"bergwerks|hütten|grubenholz|steinbruch|schachtabteuf|schachtförder|sprengarbeit|tiefbohrunternehm|^erze$"),
    ("gesundheit", "freier_beruf", r"arzt|ärzt|zahn|dentist|hebamme|heilpraktik|masseur|tierarzt|bestrahlungstherapie"),
    ("gesundheit", "handel", r"apotheke|drogen|sanitäts|optik|pharmazeu|kosmet|bandagist"),
    ("bau", "freier_beruf", r"architekt|vermessung|landmesser|ingenieurbüro|ingenieur"),
    ("bau", "handwerk", r"baugeschäft|bauunternehm|dachdeck|maler|anstreich|maurer|zimmer|glaser|klempner|installat|stukkat|fliesen|ofensetz|schornstein|bauklempner|abbruchunternehm|bauaustrocknung|betonbau|brunnenbau|deckenbau|kaminbau|kachelöfen|öfen \(kachel\)|parkettfußböden|rohrleitungsbau|straßenbau|rollladen|rolladen|rollgitter|jalousien|gerüstbau|sanitäre anlagen|sanitäre einrichtung"),
    ("bau", "handel", r"baustoff|baumaterial|zement|kalk|kunststeine|marmor|ziegelei|sand und kies|grabdenkmäler|markisen"),
    ("gastgewerbe", "gastgewerbe", r"schankwirt|gastwirt|gaststätte|restaurant|hotel|café|kaffee|pension|wirtschaft|trinkhalle|ausflugslokal|speiseanstalt"),
    ("lebensmittel", "handwerk", r"bäcker|konditor|metzger|fleischer|schlachter|brot$|brauerei|molkerei|mühle|marinieranstalt"),
    ("lebensmittel", "handel", r"lebensmittel|kolonialwaren|feinkost|gemüse|obst|südfrüchte|kartoffel|eier|butter|milch|fisch|geflügel|bier|wein|spirituosen|tabak|zigar|delikatess|süßwaren|landesprodukte|futtermittel|furage|mehl|waffeln|honigkuchen|konserven|margarine|käse|senf|sauerkraut|^salz$|liköre|essigsprit|reformhaus|gewürze|mineralwasser|getreide|seifen|speiseeis|alkoholfreie getränke"),
    ("textil_bekleidung", "handwerk", r"schneider|schuhmacher|putz|kürschner|hut|sattler|polster|dekorateur|näh|wäscherei|heißmangel|plätt|kunststopferei|stickerei|strickerei|weberei|gardinenspannerei|gardinen.*waschanstalt|plissier|dekatieranstalt|besohlanstalt|aufbügelanstalt|gerber"),
    ("textil_bekleidung", "handel", r"kleidung|ausstattung|textil|manufaktur|schuhwaren|strumpf|wäsche|stoffe|tuch|handarbeit|wolle|filze|teppiche|matratzen|betten|uniformen|militäreffekten|handschuhe|hausschuhe|schirme|posamenten|korsetts|schnittmuster|pelze|häute|felle"),
    ("holz_moebel", "handwerk", r"tischler|schreiner|drechsler|böttcher|stellmacher|korb|einrahm|küfer"),
    ("holz_moebel", "handel", r"möbel|holz|furniere|sperrhölzer|stühle|rahmen und leisten|galerieleisten|kisten|fässer"),
    ("verkehr_bahn_post", "dienstleistung", r"fuhr|transport|spedition|automobilverm|kraftwagen|taxi|schiff|umzug|lagerhaus|tankstelle|autobusbetrieb|reisebüro|telephonzellen|telephonvermietung|rundfunkvermittlung|feldbahn|fahrtreppen"),
    ("metall_maschinen", "industrie", r"fabrik|werk$|werke|gießerei|walzwerk|hütte$|apparatebau|maschinenbau|stahlbau|karosseriebau|wagenbau|motorräder|transformator|werkzeugmaschin|eisenkonstrukt|kühl- und gefrieranlage|feuerungsanlage|feuerungstechnische anlage|industrieofenbau|koksofenbau|kesseleinbau|kesseleinmauerung|akkumulatoren|ankerwickelei"),
    ("metall_maschinen", "handwerk", r"schlosser|schmied|dreher|mechanik|elektr|installation|reparatur|lackier|klempner|uhrmacher|gold|silber|graveur|feinmechanik|büchsenmacher|uhrgehäusemacher|autogene schweiß|schweiß- und schneid|autogengeräte|autozylinder|schalttafeln|verchromung|vernickelung|schleiferei|polierwerkstätt|zylinderschleiferei"),
    ("metall_maschinen", "handel", r"kugellager|schrauben und muttern|messingbleche|metallbuchstaben|metallwerkstätte|^röhren$|kupferrohre|dahtseile|drahtseile|^armaturen$|waagen und gewichte|^schläuche$|treibriemen|krane und hebezeuge|sandstrahlgebläse|luftfilter|^automaten$|kontrollkassen|registrierkassen|isoliermaterialien|isolierungen|dichtungs- und packungsmaterial|stopfbuchsenpackungen|chem\.|chemisches labor|calcium-karbid|benzol|feuerfeste produkte|technische oele|büroeinrichtung"),
    ("bildung_kultur_kirche", "freier_beruf", r"musiklehr|lehrer|unterricht|schule|künstler|maler$|bildhauer|fotograf|photogr|schriftsteller|verlag|zeitung|buchdruck|druckerei|buchbind|lichtspiel|musik|kapellmeist|klavier|orgelbau|pianoforte|geigenbauer|leihbibliothek|bibliothek|lehranstalt|lehrmittel|kunstgewerbe|kunstanstalt|graph|gemälde|filmaufnahmen|theater|konzert|vergnügungsstätte|reklame|schulwandtafel"),
    ("verwaltung", "freier_beruf", r"rechtsanwalt|anwalt|notar|steuerberat|bücherrevisor|wirtschaftsprüf|auskunft|patent|sachverständig|treuhänd|rechtsberat|rechtsbeistand"),
    ("verwaltung", "dienstleistung", r"immobilien|hypothek|versicherung|bank|sparkasse|makler|agentur|vertretung|hausverwaltung|grundstücksverwaltung|inkassobüro|finanzierung|ehevermittlung|pfandvermittler|pfandleihanstalt"),
    ("haus_reinigung", "dienstleistung", r"reinigung|friseur|bad|wäscherei|bestattung|beerdigung|gärtner|gartenbau|blumen|leichenbestatt|kammerjäger|chemische waschanstalt"),
    ("bau", "handel", r"türen|türschließer|leitern|zentralheizungen|öfen \(industrielle\)|öfen u\. kamine|waschkesselöfen|backöfen"),
    # Generisches Handel-Fallback zuletzt: sonst überdeckt es speziellere Kategorien, die selbst
    # Waren-/Geräte-/Apparate-Wörter enthalten (z. B. „Friseureinrichtungen u. -apparate“ → haus_reinigung,
    # nicht handel, weil „friseur“ hier eine speziellere Regel weiter oben trifft).
    ("handel", "handel", r"eisenwaren|handlung|waren|handel|geschäft|bedarf|artikel|großhandel|vertrieb|verkauf|kohlen|farben|papier|schreib|bücher|buchhandlung|fahrräder|automobil|reifen|antiquitäten|briefmarken|ansichtspostkarten|schmuck|^uhren$|porzellan|keramik|^glas \(|glasdächer|glasschleiferei|glasätzerei|glasbläserei|kerzen|leder|koffer|kinderwagen|schallplatten|landkarten|apparat|maschin|anlage|meßinstrument|manometer|tachometer|^eisen|^stahl$|^erze?$|draht|ketten|pumpen|ventilatoren|geldschränke|waffen$|technische öle|kaufhaus|einrichtung|registratur|versteig|korken|^leim$|bohnerwachs|lack und firnis|düngemittel|^öle$|teer"),
]
_HANDWERK_ENDUNG = re.compile(r"(meister|ei)$", re.I)


def gewerbe_vorschlag(rubrik: str) -> tuple[str, str]:
    t = (rubrik or "").lower()
    for gruppe, art, muster in _REGELN:
        if re.search(muster, t):
            return gruppe, art
    if _HANDWERK_ENDUNG.search(t):
        return "sonstige", "handwerk"
    return "sonstige", "sonstige"


def lade_gewerbe(zeilen: list[dict]) -> dict[str, dict]:
    return {z["rubrik"].strip(): {k: (v or "").strip() for k, v in z.items()} for z in zeilen if (z.get("rubrik") or "").strip()}


def gewerbe_export(zeile: dict | None) -> tuple[str, str]:
    if zeile and zeile.get("geprueft") == "ja" and zeile.get("gruppe") in GRUPPEN and zeile.get("art") in ARTEN:
        return zeile["gruppe"], zeile["art"]
    return UNGEPRUEFT, UNGEPRUEFT


def betriebsschluessel(eintrag: dict) -> str:
    """Derselbe Betrieb unter mehreren Rubriken: gleiche Firma (ohne Suffix, gefaltet) an gleicher Adresse."""
    firma, _ = rubrik_von(eintrag.get("Firmenname", ""))
    return "|".join([falte_form(firma), eintrag.get("strasse_norm", ""), eintrag.get("hausnr", ""), eintrag.get("Vorort", "")])
