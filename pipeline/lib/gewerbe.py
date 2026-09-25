"""Gewerberubriken aus Teil III (Teilprojekt 5a, Spec §5.3). Die Rubrik steht nicht in einer eigenen Spalte, sondern
als Suffix hinter dem letzten Komma des Firmennamens („M. Jäger, Althandlung“).

Zuordnungsprinzipien (Entscheidung 2026-09-25, Begründung in docs/gewerbe.md):
  gruppe = Branche, der das Geschäft dient — bei Waren die Warenbranche („Eier“ → lebensmittel, „Kurzwaren“ →
          textil_bekleidung), bei Zulieferern die belieferte Branche („Bergwerksbedarf“ → bergbau); `handel` nur für
          Waren ohne erkennbare Branche (Eisenwaren, Papier, Farben); `sonstige` = aus der Rubrik nicht erkennbar.
  art    = handwerk (stellt her, verarbeitet, repariert; Meisterbetrieb; einschließlich Bauhauptgewerbe, Gärtnerei,
          Wäscherei, Fotograf, Druckerei), handel (Rubrik nennt Ware, -handlung, -waren, -bedarf), industrie (Fabrik,
          Werk, Gießerei, Bergwerk, Brauerei, Ziegelei), gastgewerbe, dienstleistung (Verkehr, Geld, Vermittlung,
          Pflege, Unterhaltung), freier_beruf (persönliche Qualifikation: Ärzte, Anwälte, Revisoren, Architekten,
          Ingenieure, Lehrer, Künstler), sonstige (Genossenschaften, Organisationen, Unklares).
"""
from __future__ import annotations

import re

from pipeline.lib.berufe import falte_form

# Branchen der Teil-III-Rubriken. Bis 2026-09-25 mit Teil I geteilt; die Berufsgruppen sind seither OhdAB-Hauptgruppen
# (pipeline/lib/gruppen.py), Teil III behält die Branchen, weil die Rubrik hier tatsächlich eine Branche ist (Spec §5.2/5.3).
# 2026-09-25 ergänzt: finanzen_recht (Banken, Versicherungen, Immobilien, Beratung); Beschriftungen präzisiert.
GRUPPEN = {
    "bergbau": "Bergbau und Kokerei", "metall_maschinen": "Metall, Maschinen, Elektro", "bau": "Bau",
    "holz_moebel": "Holz und Möbel", "textil_bekleidung": "Textil und Bekleidung", "lebensmittel": "Lebensmittel und Genussmittel",
    "handel": "Handel (übrige Waren)", "gastgewerbe": "Gastgewerbe", "verkehr_bahn_post": "Verkehr, Bahn, Post",
    "finanzen_recht": "Banken, Versicherungen, Immobilien, Beratung", "verwaltung": "Verwaltung, Polizei, Recht",
    "bildung_kultur_kirche": "Bildung, Kultur, Medien, Kirche", "gesundheit": "Gesundheit",
    "haus_reinigung": "Haushalt, Reinigung, Körperpflege", "sonstige": "Sonstige",
}

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


# (Gruppe, Art, Muster) — erste Regel gewinnt: Speziellere Muster stehen vor allgemeinen, Waren-Fallback zuletzt.
_REGELN = [
    # Freie Berufe und Beratung
    ("gesundheit", "freier_beruf", r"arzt|ärzt|zahn(?!fabrik|räder|technisch|ärztliche bedarf)|dentist|hebamme|heilpraktik|masseur|tierarzt|bestrahlungstherapie|graphologie|wünschelrute"),
    ("gesundheit", "handel", r"apoth|spotheke|drogen|zahntechn|zahnärztliche|sanitäts|optik|pharmazeu|kosmet|bandagist|verbandstoffe|krankenpflegeartikel|instrumente \(ärztl|medizin"),
    ("finanzen_recht", "freier_beruf", r"rechtsanwalt|anwalt|notar|steuerberat|bücherrevisor|wirtschaftsprüf|patent(?!\))|sachverständig|treuhänd|rechtsberat|rechtsbeistand|auskunft"),
    ("finanzen_recht", "dienstleistung", r"immobilien|hypothek|versicherung|bank|sparkasse|makler|hausverwaltung|grundstücksverwaltung|inkasso|finanzierung|pfandleih|pfandvermittl|abzahlungsgeschäft|zweck-spar|wohnungsnachweis|büro- u\. ladenvermietung"),
    ("bau", "freier_beruf", r"architekt|vermessung|landmesser|prüfingenieur"),
    ("sonstige", "freier_beruf", r"^ingenieur"),
    # Bau: Hauptgewerbe und Ausbau = Handwerk, Baustoffe = Handel, Ziegelei/Steinwerke = Industrie
    ("bau", "industrie", r"ziegelei|basaltwerk|steinholzwerk|zementwaren|gips u\. gipsfabrikate|dampf-straßenwalzen"),
    ("bau", "handwerk", r"baugeschäft|bauunternehm|tiefbau|straßenbau|dachdeck|maler(?!bedarf)|anstreich|maurer|zimmer|glaser|klempner|installat|stukkat|fliesen|ofensetz|schornstein|abbruch|bauaustrocknung|betonbau|brunnenbau|deckenbau|kaminbau|kachelöfen|öfen \(kachel\)|parkettfußböden|rohrleitungsbau|rollladen|rolladen|rollgitter|jalousien|gerüstbau|sanitäre|heizung|lüftung|zentralheizung|steinmetz|grabdenkmäler|marmorschleif|pflaster|asphalt|steinputz|holzbauten|bühnenbau|kegelbahnbau|schiebefenster|blitzableiter|baumeister|bauinnung|schornsteinbau|teerstraßenbau|eisenschutzanstrich"),
    ("bau", "handel", r"baustoff|baumaterial|zement|kalk|kunststeine|marmor|sand und kies|markisen|türen|türschließer|leitern|leiter-|öfen u\. kamine|badeöfen|waschkesselöfen|backöfen|kanalisationsartikel|prismenoberlichte|glasdächer|dachdeckermaterial|baugeräte|fenster \(schmiede"),
    # Bergbau
    ("bergbau", "industrie", r"bergwerksbetrieb|bergwerksunternehm|steinbruch|schachtabteuf|schachtförder|sprengarbeit|tiefbohrunternehm|kies- und sandbaggerei|schlackenbrecherei"),
    ("bergbau", "handel", r"bergwerks|hütten|grubenholz|^erze$|bergtechnische|sprengstoffe"),
    # Gastgewerbe
    ("gastgewerbe", "gastgewerbe", r"schankwirt|gastwirt|gaststätte|restaurant|hotel|café|pension|^wirtschaft|trinkhalle|ausflugslokal|speiseanstalt|weinstube|hospiz"),
    # Lebens- und Genussmittel
    ("lebensmittel", "industrie", r"brauerei(?!-)|brennerei(?!bedarf)|mineralwasser|keksfabrik|mayonnaisefabrik|essigsprit|^eis$|häckselwerk|metzger \(groß"),
    ("lebensmittel", "handwerk", r"bäcker(?!ei- u|eimaschinen)|konditor(?!eibedarf)|metzger(?!eibedarf)|fleischer(?!ei-)|schlachter|molkerei(?!erzeugnisse)|mühle|marinieranstalt|kaffeerösterei|fischbackstube|pferdemetzger"),
    ("lebensmittel", "handel", r"lebensmittel|kolonialwaren|feinkost|gemüse|obst|südfrüchte|kartoffel|eier|butter|milch|fisch|geflügel|bier|wein|spirituosen|tabak|zigar|delikatess|süßwaren|scholokade|schokolade|landesprodukte|futtermittel|furage|mehl|brot|waffeln|honigkuchen|konserven|margarine|käse|senf|sauerkraut|^salz$|liköre|reformhaus|gewürze|getreide|speiseeis|^eis$|alkoholfreie getränke|vieh|kaffee|tee$|fettwaren|därme|kellereibedarf|bäckerei- u|metzgereibedarf|brauerei- und brennereibedarf|fleischerei-maschinen|bäckereimaschinen"),
    # Textil, Bekleidung, Leder
    ("textil_bekleidung", "industrie", r"kleiderfabrik|hutfabrik|mützenfabrik|fahnenfabrik|seidenstoffweberei|weberei"),
    ("textil_bekleidung", "handwerk", r"schneider(?!bedarf)|schuhmacher(?!bedarf)|putz(?!-großhandlung|lappen|wolle)|kürschner|hutpresserei|sattler|polster|näh(?!maschinen|garne|- u)|kunststopferei|stickerei|strickerei|gardinenspannerei|plissier|dekatieranstalt|besohlanstalt|aufbügelanstalt|gerber|färberei|hüte$|orthopäd"),
    ("textil_bekleidung", "handel", r"kleidung|kleider|ausstattung|textil|manufaktur|schuhwaren|strumpf|wäsche(?!rei)|(?<!treib)(?<!kleb)stoffe|tuch|handarbeit|wolle|woll|filze|teppiche|matratzen|betten|uniformen|militäreffekten|handschuhe|hausschuhe|(?<!lampen)schirme|posamenten|korsetts|schnittmuster|pelze|häute|felle|kurzwaren|weißwaren|seiden|garne|kapok|lederwaren|bijouterie|koffer|sattlerwaren|schneiderbedarf|schuhmacherbedarf|berufskleidung|planen|säcke|matten"),
    # Holz und Möbel
    ("holz_moebel", "industrie", r"holzbearbeitungswerke|sargfabrik|tischfabrik|sägewerk"),
    ("holz_moebel", "handwerk", r"tischler|schreiner|drechsler|böttcher|stellmacher|korb|einrahm|küfer|dekorateur|dekorationsgeschäft|polstergestelle|wagen und wagenbau"),
    ("holz_moebel", "handel", r"möbel|holz(?!kohle)|furniere|sperrhölzer|stühle|rahmen und leisten|galerieleisten|kisten|fässer|leisten|stiele|wohnungs-einrichtungen|ladeneinrichtungen|schaufenster|dekorationsartikel|dekorationsstoffe|sargmagazin|sargbeschläge|beschläge"),
    # Verkehr
    ("verkehr_bahn_post", "dienstleistung", r"fuhr|transport|spedition|automobilverm|automobilkutscherei|kraftwagen|lastkraftwagen|taxi|schiff|umzug|lagerhaus|tankstelle|autobus|reisebüro|telephon|rundfunkvermittlung|feldbahn|fahrtreppen|garagen|fahrschule|verkehrsunternehm|leichenfuhrwesen|möbelaufbewahrung|verleih|eisenbahnbedarf|auto-treibstoffe|autoöle"),
    # Metall, Maschinen, Elektro
    ("metall_maschinen", "industrie", r"fabrik|werk$|werke|gießerei|walzwerk|hütte$|apparatebau|maschinenbau|stahlbau|karosseriebau|motorräder|transformator|werkzeugmaschin|eisenkonstrukt|kühl- und gefrieranlage|feuerungsanlage|feuerungstechnische anlage|industrieofenbau|koksofenbau|kesseleinbau|kesseleinmauerung|akkumulatoren|ankerwickelei|hammerwerk|metallschmelz|elektrizitätsgesellschaft|chem\. anlagen|gasreinigungsanlagen|abwärmeverwertung|wärmewirtschaft|preßluftanlagen|mühlenbau|bootswerft|elektrotechn\. institute|kohlensäure|benzol|calcium|chem\. produkte|chemische pharma|chemisches labor|pharmazeutisches labor"),
    ("metall_maschinen", "handwerk", r"schlosser|schmied|dreher|mechanik|elektr(?!o-technik$|otechn\. bedarf|ische beleuchtungsgegenstände|ische uhren)|installation|reparatur|lackier|uhrmacher|gold|silberschmied|graveur|feinmechanik|büchsenmacher|uhrgehäusemacher|schweiß|autogengeräte|autozylinder|schalttafeln|verchromung|vernickelung|schleiferei|polier|beiz|glasmaler|glasschleif|glasätz|glasbläs|vulkanisier|kupferschmied|zylinderschleiferei|elektro-schweiß|dampfkesselreinigung|prägeanstalt|klischeeanstalt|spiegelbeleg|umpreßanstalt|licht- u\. kraftanlagen|lichtpaus"),
    ("metall_maschinen", "handel", r"kugellager|schrauben|messingbleche|metallbuchstaben|metallwerkstätte|^röhren$|kupferrohre|dahtseile|drahtseile|^armaturen$|waagen und gewichte|^schläuche$|treibriemen|krane und hebezeuge|sandstrahlgebläse|luftfilter|^automaten$|kontrollkassen|registrierkassen|isoliermaterial|isolierungen|dichtungs- und packungsmaterial|stopfbuchsenpackungen|chem\.|feuerfeste produkte|technische oele|technische öle|büroeinrichtung|büromaschinen|schreibmaschinen|rechenmaschinen|addiermaschinen|buchungsmaschinen|metall|stahl|eisen(?!waren|bahn)|draht|ketten|pumpen|ventilatoren|geldschränke|maschin|apparat|anlage|meßinstrument|manometer|tachometer|elektrotechn|elektro-technik|elektromotoren|elektrische|beleuchtung|lampen|leuchtspiegel|radio|sprechapparate|fernmelde|fernsprech|nähmaschinen|werkzeuge|technische gegenstände|technische gummi|technische großhandlung|gummiwaren|asbest|aluminium|bestecke|stahlwaren|blech|zahnräder|gußstahl|autobeleuchtung|automobilkühler|automobilbereifung|automobil-bestand|reifen|bootsmotoren|gas und gasapparate|feuerlösch|sauerstoff|gas- und luftschutz|laboratorium|carbid|schleifscheiben|elektrofahrzeug|batterien|akkumulatorenvertrieb|uhren|schmuck|juwelen|silberwaren|industriebedarf|gießereibedarf|kesselreinigung"),
    # Bildung, Kultur, Medien, Kirche
    ("bildung_kultur_kirche", "freier_beruf", r"musiklehr|lehrer|unterricht|(?<!baum)schule|lehranstalt|künstler|kunstmaler|bildhauer|schriftsteller|kapellmeist|musikdirektor|graphiker|theatermaler|reklamemaler|schaufenstergestalter|gesanglehrer|lautenlehrer"),
    ("bildung_kultur_kirche", "handwerk", r"fotograf|photogr\. atelier|photographische vergrößerungen|buchdruck|druckerei|buchbind|klavierbauer|orgelbau|pianoforte|geigenbauer|kupferdruck|steindruck|offsetdruck|klavierstimmer|stempel|kunstanstalt|kunstgewerbe|reklameatelier"),
    ("bildung_kultur_kirche", "dienstleistung", r"lichtspiel|theater|konzert|vergnügungsstätte|leihbibliothek|bibliothek|verlag|zeitung|zeitschriften|filmaufnahmen|reklame|plakatanschlag|anzeigenvermittl|ausstellung|adressenverlag"),
    ("bildung_kultur_kirche", "handel", r"musik|schallplatten|lehrmittel|schulwandtafel|gemälde|kunsthandlung|buchhandlung|bücher|antiquariat|photogr|graph|kirchenbedarf|paramenten|landkarten|briefmarken|ansichtspostkarten|postkarten|sportartikel|turn- und sportgeräte|spielwaren|puppen|vereinsartikel|karnevalsartikel|feuerwerkskörper|illuminationsartikel|billardartikel|nationalsozialistische"),
    # Haushalt, Reinigung, Körperpflege
    ("haus_reinigung", "handwerk", r"wäscherei|waschanstalt|heißmangel|plätt|gärtnerei|gartenbau|baumschule|gartengestalt|obst u\. gemüseerzeuger|entmottung|teppichreinigung|fußbodenreinigung|bürsten"),
    ("haus_reinigung", "dienstleistung", r"reinigung|friseur|bad|kammerjäger|wach- u\. schließ|detektiv|kosmetisches institut|puppen-klinik"),
    ("haus_reinigung", "handel", r"blumen|seifen|parfümerie|reinigungsmittel|bohnerwachs|haus- u|haus- und|küchengeräte|herde|staubsauger|wasch- u\. wring|kerzen|wachswaren|wachsfackeln|fußpflege|friseurbedarf|friseureinricht|wäscherei-einricht|sämerei|gärtnerei-|düngemittel|zoologische|pferdehandlung"),
    # Bestattung, Verwaltung, Sonstiges
    ("sonstige", "dienstleistung", r"bestattung|beerdigung|leichenbestatt|feuerbestattung|wettannahme|lotterie|schreibbüro|versteiger|ehevermittlung|büro$|durchschreibe|unfallschäden|heimarbeiten"),
    ("verwaltung", "sonstige", r"genossenschaft|organisationen|innung|mitglied"),
    # Waren-Fallback (Handel übrige Waren) zuletzt
    ("handel", "handel", r"handlung|waren|handel|geschäft|bedarf|artikel|großhandel|vertrieb|verkauf|kohlen|farben|lack|papier|schreib|kaufhaus|warenhaus|einrichtung|registratur|korken|^leim$|klebstoffe|^öle$|teer|rohprodukte|alt|linoleum|porzellan|keramik|tonwaren|glas|flaschen|kartonagen|verpackung|füllhalter|geschäftsbücher|briefumschläge|modelle|bindfaden|seilerwaren|holzkohle|brennholz|automobile|fahrräder|kinderwagen|faltboote|pfeifen|waffen|antiquitäten|export|import|versand|handelsvertreter|vertretung|agentur|leichenfuhr"),
]
# Grobe Heuristik: Handwerksbetriebe enden oft auf „-ei“ oder „-meister“ (Bäckerei, Schreinermeister) — unscharfer
# Fallback vor „sonstige“.
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


def entschieden(zeile: dict | None) -> bool:
    """Handgeprüft oder von einem benannten Bearbeiter entschieden (nicht die Automatik) — bleibt beim Neuaufbau erhalten."""
    return bool(zeile) and (zeile.get("geprueft") == "ja" or (zeile.get("bearbeiter") or AUTOMATIK) != AUTOMATIK)


def gewerbe_export(zeile: dict | None) -> tuple[str, str]:
    """Seit 2026-09-25 wie bei der Stellung: Jeder Vorschlag im Vokabular wird exportiert, `gewerbe_quelle` sagt, woher."""
    if zeile and zeile.get("gruppe") in GRUPPEN and zeile.get("art") in ARTEN:
        return zeile["gruppe"], zeile["art"]
    return UNGEPRUEFT, UNGEPRUEFT


def gewerbe_quelle(zeile: dict | None) -> str:
    """„hand“ (geprueft=ja), „claude“ (Entscheidung 2026-09-25 nach Prinzipien), „vorschlag“ (Wortregeln), „“ (nichts)."""
    if gewerbe_export(zeile) == (UNGEPRUEFT, UNGEPRUEFT):
        return ""
    if zeile.get("geprueft") == "ja":
        return "hand"
    return "claude" if zeile.get("bearbeiter") == "claude" else "vorschlag"


def betriebsschluessel(eintrag: dict) -> str:
    """Derselbe Betrieb unter mehreren Rubriken: gleiche Firma (ohne Suffix, gefaltet) an gleicher Adresse."""
    firma, _ = rubrik_von(eintrag.get("Firmenname", ""))
    return "|".join([falte_form(firma), eintrag.get("strasse_norm", ""), eintrag.get("hausnr", ""), eintrag.get("Vorort", "")])
