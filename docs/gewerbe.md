# Gewerberubriken Teil III: Zuordnungsprinzipien

Stand 2026-09-25 (Teilprojekt 5a, Spec §5.3). Quellcode: `pipeline/lib/gewerbe.py` (Vokabular, Wortregeln,
Export), `werkzeuge/gewerbe_vorschlag.py` (Aufbau der Tabelle), `werkzeuge/zuordnung.html?tabelle=gewerbe`
(Handprüfung). Tabelle: `kuratierung/gewerbe.csv` (848 Rubriken, 18.863 Betriebe).

## Warum hier Branchen (und bei den Berufen nicht)

Die Rubrik des Branchenverzeichnisses nennt das Geschäft („Bäcker“, „Kohlen“, „Schankwirt“), nicht die Person.
Anders als die Berufsbezeichnung in Teil I (Tätigkeit, kein Betrieb — deshalb dort OhdAB-Hauptgruppen, Spec §5.2)
trägt sie die Branche tatsächlich. Zwei Achsen je Rubrik:

- **`gruppe` = Branche, der das Geschäft dient.** Bei Waren die Warenbranche („Eier“ → `lebensmittel`, „Kurzwaren“
  → `textil_bekleidung`), bei Zulieferern die belieferte Branche („Bergwerks- und Hüttenbedarf“ → `bergbau`,
  „Bäckereibedarf“ → `lebensmittel`). `handel` nur für Waren ohne erkennbare Branche (Eisenwaren, Papier, Farben,
  Porzellan). `sonstige` heißt: aus der Rubrik nicht erkennbar — kein Verlegenheitsfach, sondern Aussage.
- **`art` = Betriebsform:**
  - `handwerk` — stellt her, verarbeitet oder repariert vor Ort, typischerweise Meisterbetrieb. Einschließlich
    **Bauhauptgewerbe** (Baugeschäft, Tiefbau-, Bauunternehmer, Straßenbau: Bauinnung, Handwerksrolle),
    **Gärtnerei** (produziert Pflanzen), **Wäscherei/Plättanstalt** (Wäscher und Plätter), **Fotograf**
    (Photographenhandwerk), **Druckerei, Buchbinderei, Instrumentenbau**.
  - `handel` — die Rubrik nennt eine Ware oder „-handlung“, „-waren“, „-bedarf“, „Großhandlung“.
  - `industrie` — Fabrik, Werk, Gießerei, Walzwerk, Bergwerk, Brauerei, Brennerei, Ziegelei, Sägewerk.
  - `gastgewerbe` — Schankwirt, Gaststätte, Hotel, Café, Pension, Trinkhalle, Speiseanstalt.
  - `dienstleistung` — Verkehr, Geld und Vermittlung, Pflege, Unterhaltung, Bestattung, Reinigung, Friseur.
  - `freier_beruf` — persönliche Qualifikation: Ärzte, Hebammen, Anwälte, Revisoren, Treuhänder, Architekten,
    Ingenieure, Landmesser, Lehrer und private Lehranstalten, Künstler, Kapellmeister.
  - `sonstige` — Genossenschaften, Organisationen, Unlesbares („künstl.“).

## Vokabular `gruppe` (15, seit 2026-09-25)

`bergbau`, `metall_maschinen` (Metall, Maschinen, Elektro — einschließlich Elektroinstallation), `bau`,
`holz_moebel` (auch Raumausstatter, Polsterer), `textil_bekleidung` (auch Leder, Schuhe), `lebensmittel`
(**und Genussmittel**: Tabak, Zigarren — Nahrungs- und Genußmittelgewerbe der Berufszählung), `handel`
(übrige Waren), `gastgewerbe`, `verkehr_bahn_post`, **`finanzen_recht`** (neu: Banken, Versicherungen,
Immobilien, Hypotheken, Treuhänder, Revisoren, Steuer- und Rechtsberatung, Auskunfteien), `verwaltung`
(Behörden, Genossenschaften, Organisationen), `bildung_kultur_kirche` (auch Medien: Verlage, Zeitungen,
Kinos, Foto), `gesundheit` (auch Apotheken, Drogerien, Optiker, Bandagisten), `haus_reinigung` (**Haushalt,
Reinigung, Körperpflege**: Friseure, Bäder, Wäschereien, Gärtnereien, Haushaltswaren), `sonstige`.

## Entschiedene Grenzfälle (Christos' Fragen, Entscheidung Claude 2026-09-25)

| Rubrik | Entscheidung | Warum |
|---|---|---|
| Baugeschäft (205), Tiefbauunternehmer (65), Bauunternehmer, Straßenbau | `bau` / `handwerk` | Bauhauptgewerbe ist Handwerk (Bauinnung, Handwerksrolle), kein Dienstleister; „Mitglied der Bauinnung“ steht als eigene Rubrik in der Vorlage |
| Gartenbaubetrieb (81), Gartengestalter, Baumschule | `haus_reinigung` / `handwerk` | Produktionsgärtnerei stellt her; Landschaftsgärtner sind Meisterbetriebe |
| Photogr. Atelier (48), Vergrößerungen | `bildung_kultur_kirche` / `handwerk` | Photographenhandwerk, kein freier Beruf; Kultur/Medien als Branche |
| Ingenieur (278), Ingenieurbüro (43) | `sonstige` / `freier_beruf` | Branche aus 278 Personennamen nicht erkennbar; Prüfingenieur f. Statik und Landmesser dagegen `bau` |
| Bücherrevisor, Treuhänder, Immobilien, Bank, Hausverwaltung, Auskunftei | `finanzen_recht` | eigene Branche statt „Verwaltung“ |
| Elektrische Licht- u. Kraftanlagen (91) | `metall_maschinen` / `handwerk` | Elektroinstallateure, keine Werke |
| Heizungs-/Lüftungsanlagen, Zentralheizungen, Bauklempnerei | `bau` / `handwerk` | Installationshandwerk (Baunebengewerbe) |
| Automobilkutscherei (43), Garagen, Tankstelle | `verkehr_bahn_post` / `dienstleistung` | Mietwagen, kein Handel |
| Viehhandlung, Viehagentur | `lebensmittel` | Vieh beliefert Metzger |
| Bergwerksbetrieb, -unternehmer, Steinbruchbesitzer | `bergbau` / `industrie` | keine Händler |
| Brot, Molkereierzeugnisse, Speiseeis | `lebensmittel` / `handel` | Verkaufsstellen |
| Mineralwasser (30) | `lebensmittel` / `industrie` | Sprudelfabriken angenommen (unsicher) |
| Kaffee (12) | `lebensmittel` / `handel` | Kaffeehandel angenommen — ein Café schriebe die Vorlage „Café“ (unsicher) |
| Seifen | `haus_reinigung` / `handel` | kein Lebensmittel |
| Beerdigungsanstalt, Leichenbestatter | `sonstige` / `dienstleistung` | Bestattung passt in keine Branche |
| Lichtspielhaus, Zeitungsbetrieb, Leihbibliothek | `bildung_kultur_kirche` / `dienstleistung` | Unterhaltung/Medien sind Betriebe, keine freien Berufe |
| Dekorateur (143), Wagen und Wagenbau | `holz_moebel` / `handwerk` | Raumausstatter bzw. Stellmacher |
| Uhrmacher und Uhrenhandlung (130) | `metall_maschinen` / `handwerk` | Feinmechanik, Handel im Nebenbetrieb |
| Silberwaren u. Juwelen, Uhren, Schmuck | `handel` / `handel` | Juweliergeschäfte |
| Apotheken (44 Rubriken mit Eigennamen) | `gesundheit` / `handel` | Einzelhandel mit Approbation; Berufszählung zählt Apotheken zum Handel |
| Chem. Produkte, Benzol, Karbid, Kohlensäure | `handel` / `handel` | Chemikalienhandel angenommen; „Chem. Fabrik“ dagegen `industrie` |

## Export und Kennzeichnung

Wie bei der sozialen Stellung (docs/stellung.md, Exportregel): 68 Rubriken hat Christos von Hand geprüft
(12.782 Betriebe, 68 %), 242 hat Claude nach den Prinzipien oben entschieden (`bearbeiter=claude`, 3.826
Betriebe, 20 %), 538 kleine Rubriken tragen den Vorschlag der Wortregeln (2.255 Betriebe, 12 %). Alle drei
werden exportiert; je Eintrag sagt `gewerbe_quelle` = `hand` | `claude` | `vorschlag`, woher die Zuordnung
stammt. Kennzahlen: `gewerbe_geprueft` (hand), `gewerbe_entschieden` (claude), `gewerbe_vorschlag`.
`werkzeuge/gewerbe_vorschlag.py` lässt entschiedene Zeilen (geprüft oder benannter Bearbeiter) unangetastet.

Handgeprüfte Zeilen, die vor der Vokabularänderung entschieden wurden und heute anders lägen (nicht
überschrieben): Friseur, Friseur für Damen, Zigaretten- und Tabakgeschäft, Kunstmaler → `sonstige`;
Steuerberatung, Versicherungsgeschäft, Sachverständiger → `verwaltung` (heute `finanzen_recht`).
