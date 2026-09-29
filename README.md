# Adressbuch Essen 1936 — Datenpipeline (v2)

Erzeugt aus dem DES-Export des Essener Adreßbuchs 1936 (`data/essen1936.csv`, Tab-getrennt)
eine geokodierte Tabelle mit ausgewiesener Präzisionsstufe je Eintrag.
Leitprinzip: Präzision vor Vollständigkeit — nichts Falsches als richtig, Unsicheres wird gekennzeichnet.

## Voraussetzungen
- Python ≥ 3.12, `pip install -e .[test]`
- Lokale Nominatim-Instanz (Docker `mediagis/nominatim:4.4`, NRW-Extrakt).
  Adresse über die Umgebungsvariable `NOMINATIM_URL`, Standard `http://localhost:8080`.
- Straßendatensatz `essener-strassen` (Umgebungsvariable `ESSENER_STRASSEN_DIR`,
  Standard `../essener-strassen/daten`; erwartet `strassen.csv`, `konkordanz_1936.csv`, `namen.csv`)

## Aufruf
```
python3 pipeline/01_einlesen.py
python3 pipeline/02_adresse_parsen.py
python3 pipeline/03_strasse_aufloesen.py
python3 pipeline/04_geokodieren.py     # ≈ 7 Minuten mit leerem Cache
python3 pipeline/05_bericht.py
```
Ausgaben liegen in `build/` (löschbar, nicht im Git). Vom Menschen gepflegte Tabellen in `kuratierung/`.

Tests: `python3 -m pytest -q` (keine Netzverbindung nötig).
Lokale Vorschau der Ergebnisse: `python3 werkzeuge/serve.py` (statt `python3 -m http.server`,
weil PMTiles Range-Requests braucht und der Server die geprüfte Stichprobe zurückschreibt).
Kontrollkarte: `werkzeuge/kontrollkarte.html`; Prüfwerkzeug für die manuelle Stichprobe:
`werkzeuge/pruefung.html` (Anleitung in `docs/stichprobe.md`); Sichtung offener Straßen am
Stadtplan 1935: `werkzeuge/sichtung.html` nach `python3 werkzeuge/sichtung_liste.py` (Anleitung in `docs/sichtung.md`).

## Vokabulare der Ausgabespalten

`stufe` — Präzision der Verortung einer Adresse:

| Wert | Bedeutung |
|---|---|
| `haus` | Punkt auf der Hausnummer |
| `strasse` | Punkt auf der Straße (Hausnummer nicht gefunden, nicht vorhanden oder nicht verlässlich; `grund` sagt, warum) |
| `landmarke` | kuratierter Punkt aus `kuratierung/landmarken.csv` |
| `offen` | keine Verortung; `grund` sagt, warum |

Auf der Karte (`site/daten/adressen.pmtiles`) heißt die Präzisionsstufe ebenfalls `stufe`, mit
`haus`, `strasse` und zusätzlich `stadtplan` für Punkte vom Stadtplan 1935 — auf Pipeline-Ebene
bleibt das weiterhin `stufe=strasse` mit `herkunft=stadtplan_1935` (kein eigener Pipeline-Wert,
nur zur Anzeige in der Karte aufgespalten).

`grund` — bei `stufe=offen`: `strasse_offen` (Straße nicht aufgelöst),
`ohne_nummer`, `kein_treffer`, `mehrdeutig_strasse` (mehrere gleichnamige Straßen ohne
unterscheidenden Stadtteil), `stadtteil_widerspruch`, `fehler` (Nominatim-Anfrage
fehlgeschlagen; ein erneuter Lauf holt sie nach). Bei `stufe=strasse` zusätzlich
`nummer_unsicher` (kuratierter Hausnummernbereich, dessen Nummern heute nicht mehr gelten —
die Hausebene wird bewusst nicht gesucht) und `stadtplan_1935` (Punkt vom Menschen am Stadtplan 1935
gesetzt, `kuratierung/strassen_1935.csv`; keine heutige Straße, kein Nominatim).

`herkunft` — woher die heutige Straße kommt:

| Wert | Bedeutung |
|---|---|
| `kuratiert` | vom Menschen belegt (`kuratierung/strassen_zuordnung.csv`) |
| `stadtplan_1935` | vom Menschen am Stadtplan 1935 verortet, keine heutige Straße (`kuratierung/strassen_1935.csv`) |
| `heutig` | Name gilt heute und galt 1936 für genau diese Straße |
| `konkordanz` | Umbenennung nach `konkordanz_1936.csv` |
| `stadium` | anderes Namensstadium aus `namen.csv` |
| `offen` | keine Kandidaten |

`zeitlich_abweichend=ja` — der gewählte Namensstand ist für 1936 nicht datiert belegt
(undatiertes Stadium oder nur Stadien außerhalb des Fensters 1930–1937).

Reihenfolge der Automatik: Kuratierung (Zuordnung, dann Stadtplan-Punkt), dann Vorort-Filter (Vorort bzw. Kernstadt), dann die
Zeitstufung nur unter den räumlich passenden Kandidaten — 1936 belegt oder undatiert, sonst
weites Fenster 1930–1937, sonst außerhalb datiert. Die Stufen verschmelzen nicht zu Homonymen.
Die Stufe „außerhalb“ greift automatisch nur, wenn der Name heute gilt und Dickhoff für 1936 keinen
anderen Namen derselben Straße belegt (Dickhoffs Kette ist dann lückenhaft, nicht die Straße falsch);
erloschene Namen bleiben `name_erloschen`, wiederverwendete `name_spaeter` — beide werden kuratiert.
Der Vorort-Filter steht vor der Zeitstufung, weil Dickhoffs Ketten einen Namen bei Teil-
Umbenennungen für die ganze Straße beenden (Altendorfer Straße „bis 1933“); sonst verdrängt
eine 1936 gültige Namensschwester im falschen Ort den richtigen Kandidaten.

`mehrdeutig=ja` mit `grund_mehrdeutig` — es blieb mehr als ein Kandidat übrig oder keiner passte:

| Wert | Bedeutung |
|---|---|
| `homonym_1936` | mehrere verschiedene Straßen trugen 1936 diesen Namen |
| `konkordanz_nicht_eindeutig` | alle Kandidaten stammen aus Konkordanzzeilen mit `eindeutig=nein` |
| `vorort_widerspruch` | Kandidaten vorhanden, aber keiner passt zum Vorort bzw. zur Kernstadt |
| `name_erloschen` | der Name gehört bei Dickhoff nur Straßen, die ihn schon vor 1930 verloren haben und heute anders heißen — nicht automatisch vergeben, weil Dickhoff keine verschwundenen Straßen führt (Kandidat steht in `kandidaten` als Vorschlag) |
| `name_spaeter` | der Name gilt heute, Dickhoff datiert ihn aber erst nach 1937 und belegt für 1936 einen *anderen* Namen derselben Straße (meist ein später umbenannter Abschnitt) — die Straße des Buches lag woanders, der Name wurde wiederverwendet; nicht automatisch vergeben (Stichprobe r6). Beginnt Dickhoffs Kette nur später, bleibt die Automatik mit `zeitlich_abweichend=ja` |

`vorort_angenommen=ja` — Teil II/III ohne Vorortangabe: unter sonst gleichwertigen Kandidaten
hat die Kernstadt entschieden. Ein leerer Vorort bedeutet dort zu 95 % Kernstadt (Kreuztabelle
2026-09-15), ist aber kein Beleg; alle Kandidaten bleiben in `kandidaten` notiert.

`nummer_unsicher=ja` — die Zeile fiel in einen kuratierten Hausnummernbereich, dessen Nummern
heute nicht mehr gelten (Straße nach 1936 geteilt, zusammengelegt oder neu gezählt); verortet
wird nur die Straße.

`schreibvariante=ja` mit `strasse_angeglichen` — der Buchname fand keinen Kandidaten und wurde über
gestufte Schlüsselformen (ß/ss; Leerzeichen, Bindestrich, Punkt; ck/k, th/t, dt/t, ph/f, c/k, y/i, ie/i;
Umlaut-Umschrift, ei/ey; Endung -ener/-er, Genitiv-s, Doppelbuchstaben) an genau einen Dickhoff-Namen
angeglichen (`strasse_angeglichen`, normiert), der dann die normale Kette durchläuft. Mehrere Namen mit
gleichem Schlüssel → keine Angleichung. Der Buchname bleibt in `strasse_roh` erhalten; Karte und
Prüfwerkzeug zeigen beide Schreibweisen (Regelliste: `pipeline/lib/normalisierung.py`, SCHLUESSELSTUFEN).

`kuratierung/strassen_zuordnung.csv` — vom Menschen belegte Straßenzuordnung, schlägt alles:

| Spalte | Bedeutung |
|---|---|
| `strasse_roh_norm` | normierter Name von 1936 (`norm_strasse`) |
| `vorort` | Vorort des Eintrags; `Kernstadt` = nur Einträge ohne Vorort; leer = Platzhalter für alle |
| `strasse_heute`, `schl_nr` | Ziel (Dickhoff-Schlüssel) |
| `hausnr_von`, `hausnr_bis` | optionaler Hausnummernbereich (je offen, wenn leer); ohne passende Nummer greift die Automatik |
| `nummer_unsicher` | `ja` → nur Straßenebene (s. o.) |
| `beleg`, `bearbeiter`, `datum` | Quelle der Entscheidung, kurz und nachprüfbar |

`kuratierung/strassen_1935.csv` — Straßen, die kein Dickhoff-Name trifft (verschwunden oder Kette lückenhaft),
vom Menschen am georeferenzierten Stadtplan 1935 verortet (Werkzeug `werkzeuge/sichtung.html`):

| Spalte | Bedeutung |
|---|---|
| `strasse_roh_norm`, `vorort` | normierter Buchname und Buchvorort; `Kernstadt` = Einträge ohne Vorort |
| `befund` | `punkt` (verortet) oder `nicht_gefunden` (gesichtet, im Plan nicht auffindbar — verortet nichts) |
| `lat`, `lon` | Straßenmitte am Stadtplan 1935 (Stufe `strasse`, Grund `stadtplan_1935`) |
| `name_im_plan`, `stadtteil` | Schreibweise im Plan; heutiger Stadtteil (Vorschlag aus OSM, geprüft) |
| `bemerkung`, `bearbeiter`, `datum` | Beleg und Nachvollziehbarkeit |

Entscheidungen zu einzelnen Straßen: [`docs/entscheidungen_strassen.md`](docs/entscheidungen_strassen.md).

`build/strassen_vorschlaege.csv` ist die Arbeitsliste für die Kuratierung: alle offenen und
mehrdeutigen Paare mit unscharfen Kandidaten, nach Zeilenzahl sortiert.

#### Zechen (`kuratierung/zechen.csv`)

Ausgangsbasis ist die Wikipedia-„Liste von Bergwerken in Essen“ (`werkzeuge/zechen_wikipedia.py`, Koordinaten
aus den Artikeln). Die Betriebsjahre der Liste sind **nicht belastbar** (Beispiel Fridolin: Liste 1836–1960,
tatsächlich 1899 zu Eiberg konsolidiert; 1960 ist das Jahr der Straßenbenennung; 105 von 212 Artikeln weichen
von der Liste ab). Deshalb leitet `werkzeuge/zechen_abgleich.py` den Status 1936 aus mehreren Quellen ab; an
erster Stelle steht die Huske-Chronologie aus dem Historischen Portal Essen (`werkzeuge/zechen_portal.py` →
`kuratierung/zechen_huske.csv`: je Zeche Portalseite, abgeleiteter `huske_status`, Grund, Chronik 1930–1940 als
Belegzitat), danach Wikipedia-Liste, Artikel-Infobox und Stadtplan 1935:

| Spalte | Bedeutung |
|---|---|
| `betrieb_von`, `betrieb_bis` | Jahre laut Wikipedia-Liste |
| `artikel_von`, `artikel_bis` | Jahre laut Infobox des Wikipedia-Artikels (Cache `kuratierung/zechen_artikel.csv`, `--neu` lädt neu) |
| `plan_1935` | passende Beschriftung im Stadtplan Essen 1935 im Umkreis von 1,5 km (aus `kuratierung/stadtplan_1935_zechen.csv`), leer = nicht beschriftet |
| `huske_status`, `huske_url` | Ergebnis aus der Portal-Chronologie (`aktiv` = Betriebs-/Förderbeleg und kein Zechenende bis 1936; `stillgelegt` = Ende vor 1936 bzw. erst später entstanden; `unklar` = Text abgeschnitten, Widerspruch, kein Beleg, nicht gefunden) und die Portalseite |
| `status_1936` | = `huske_status`, wenn dieser eindeutig ist; sonst `aktiv` nur, wenn Liste und Artikel beide Betrieb 1936 sagen und der Plan nicht „ehem.“ vermerkt, `stillgelegt`, wenn beide ein Ende vor 1936 nennen, sonst `unklar` |
| `status_geprueft` | `ja` = von Hand entschieden, wird vom Werkzeug nicht mehr überschrieben (Beleg in `hinweis`) |
| `hinweis` | Beleg (Huske-Zitat mit Jahr) bzw. Grund für `unklar` (Widerspruch, fehlende Jahre, Portaltext abgeschnitten) bzw. Beleg der Handprüfung |
| `bearbeiter` | `wikipedia` oder `stadtplan-1935` (Koordinaten aus der Planbeschriftung, ±100 m) |

`kuratierung/zechen_pruefung.csv` ist die Arbeitsliste aller `unklar`-Fälle mit allen Quellenangaben
nebeneinander (Zechen mit Koordinaten zuerst; dort vor allem Zechen, deren Portaltext abgeschnitten ist:
Graf Beust, Pörtingssiepen, Helene Amalie, Wolfsbank, Altendorf Tiefbau — hier hilft nur der gedruckte Huske). Die Karte zeigt nur `status_1936 = aktiv`; das Popup nennt
die Artikeljahre und weist auf eine abweichende Liste hin. Der Plan beschriftet auch stillgelegte
Anlagen (teils mit „ehem.“, teils ohne, z. B. Graf Beust, stillgelegt 1929); eine Planbeschriftung
allein belegt daher keinen Betrieb, eine fehlende Beschriftung spricht aber gegen ihn.

Referenzquelle für die Handprüfung: das Historische Portal Essen (Huske-Auszüge je Zeche) und der
ArcGIS-Dienst `historischerverein/Bergbau`, siehe [`docs/zechen_quellen.md`](docs/zechen_quellen.md).

`kuratierung/stadtplan_1935_zechen.csv` — alle Bergbau-Beschriftungen des Plans (125, davon 92 Zechen;
der Plan reicht bis Gelsenkirchen, Bottrop, Mülheim, Bochum), gelesen von sechs Opus-Agenten auf
218 Kacheln à 1,5 km (`werkzeuge/stadtplan_kacheln.py`, 1 m/px), mit Kachel-Box (UTM32) und Pixelposition,
daraus `lat`/`lon`; `geprueft` = Handprüfung der Lesung (noch `nein`).

## Karte (Teilprojekt 2)

Datenpaket erzeugen (braucht `build/04_geokodiert.csv`, `build/eintraege.csv` und tippecanoe):
```
python3 pipeline/06_karte_export.py
```
Schreibt nach `site/daten/` (Adresspunkte, Sucheindex, Kennzahlen, Themen, Zechen). Das Verzeichnis
ist **nicht versioniert** (`.gitignore`), weil es ≈130 MB in 1.600 Dateien wiegt und bei jeder
Regenerierung komplett neu entsteht; es wird lokal erzeugt und beim Deploy mitgenommen.

Deploy nach GitHub Pages:
```
werkzeuge/deploy.sh              # Schnappschuss von site/ → Branch gh-pages (Force-Push)
werkzeuge/deploy.sh --nur-bauen  # nur den lokalen Branch gh-pages setzen, nicht pushen
```
Das Skript baut aus `site/` (ohne `site/tests`, `package.json` und das Roh-GeoJSON) einen einzelnen
Commit ohne Vorgänger und ersetzt damit `gh-pages`; der Branch trägt also immer genau einen Stand,
und `main` bleibt frei von Datenpaketen. Es verweigert den Deploy bei uncommitteten Änderungen,
fehlendem Datenpaket oder `PLAN_FREIGEGEBEN = true` (Stadtplan-Rechte). GitHub Pages wird in den
Repo-Einstellungen auf „Deploy from a branch: gh-pages / (root)“ gestellt; ein Actions-Build kommt
nicht in Frage, weil die Pipeline die lokalen Quelldaten und die eigene Nominatim-Instanz braucht.

Lokale Ansicht:
```
python3 werkzeuge/serve.py 8765   # → http://localhost:8765/site/
```
`serve.py` statt `python3 -m http.server`, weil PMTiles Range-Requests braucht (siehe oben).

Bedienung (Stand 2026-09-28): Rechts oben ein Ebenenknopf (Stapel-Symbol) mit aufklappbarem Feld für
Grundkarte (dezent | detailliert), Zechen (Schlägel-und-Eisen-Symbol, Wikimedia Commons, gemeinfrei, s.
Impressum) und — nur bei `PLAN_FREIGEGEBEN` — den stufenlosen Stadtplan-Regler; ein blauer Punkt am Knopf
zeigt eine Abweichung vom Standard. Das Popup eines Adresspunkts ist die Visitenkarte des Hauses:
Kennzeile (Präzision nur, wenn nicht hausgenau; Zähler je Teil), dann Einwohner, Eigentümer, Gewerbe mit
höchstens vier Zeilen je Teil (Handy zwei), Beruf nur als Norm (ohne Norm die Buchschreibung kursiv),
Eigentümer mit Besitzklasse, Gewerbe mit Rubrik (das Firmenfeld in Teil III endet auf „, Rubrik“ und wird
darum gekürzt); bei ein oder zwei aktiven Ebenen sind deren Teile farbig markiert. „Haus im Detail ›“ öffnet
die Hausansicht in der Sidebar mit der vollen Belegkette; dort Reiter „Alle · Einwohner · Eigentümer · Gewerbe“
(nur bei mehr als einem Teil), Start im Teil der einzigen aktiven Ebene bzw. des angeklickten Eintrags. Alle Adresspunkte tragen ab Straßenzoom einen
weißen Halo (`HALO` in `karte.js`), damit sich überlappende Punkte trennen und der Kontrast auf Liberty
bleibt. HTML der Leiste: `site/js/steuerung.js`, des Popups: `site/js/popup.js`.

## Eigentümer (Teilprojekt 3)

Eigentümer aus Teil II werden zu kanonischen Eigentümern mit Kategorie zusammengeführt
(Spec `docs/superpowers/specs/2026-09-22-eigentuemer-design.md`).

```
python3 werkzeuge/eigentuemer_cluster.py [--min-haeuser 5]   # Vorschläge → build/, legt kuratierung/eigentuemer.csv an
python3 werkzeuge/serve.py 8765                              # dann http://localhost:8765/werkzeuge/eigentuemer.html
python3 pipeline/06_karte_export.py                          # geprüfte Zuordnungen in die Karte (Thema „Besitz“)
```

`kuratierung/eigentuemer.csv`: eine Zeile je Schreibweise (`schreibweise, art, eigentuemer, kategorie,
geprueft, bearbeiter, datum, hinweis`). Die Automatik überschreibt nur Zeilen, die ungeprüft sind und
`bearbeiter=eigentuemer_cluster` tragen; alles, was das Werkzeug gespeichert hat, bleibt. Kategorien:
`stadt_staat, bergbau, industrie, genossenschaft_siedlung, kirche_stiftung, bank_versicherung,
privatperson, sonstige`. Abkürzungskatalog: `kuratierung/eigentuemer_abkuerzungen.csv`.
Nachtrag 2026-09-23: Spalte `identitaet` (leer = Identität nicht belegbar, `sicher` = bestätigt; Taste `U` im
Werkzeug) — Personen tragen immer die sichere Kategorie `privatperson`, erscheinen in Suche und Liste „Größte
Eigentümer“ aber nur mit `identitaet=sicher`. Schreibweisen aus `kuratierung/eigentuemer_stadtteil.csv`
(Kirchengemeinden ohne Zusatz) führt die Automatik je Stadtteil als eigene, immer prüfpflichtige Schreibweise
„Kath. Kirchengem. ‹Katernberg›“; der Export sucht zuerst diese, dann die einfache Schreibweise. Auf der Karte
zählt nur `geprueft=ja`: Punktattribut `besitz` (Kategorie | `gemischt` | `ungeprueft`), Hausansicht
„Zugeordnet“, Suche nach kanonischem Namen (`eigentuemer=` in der URL).
Hausnummernspannen (2026-09-26): Das Häuserbuch druckt einen Eigentümer vieler aufeinanderfolgender Häuser
einmal am Anfang der Straßenseite („2—84 E. Frau-Margarete-Krupp-Stiftung“, danach die Häuser nur mit
Bewohnern; Faksimile II-335). Der Parser liefert dafür `hausnr`/`hausnr_bis`; `karte_export.gruppiere`
überträgt die geprüfte Klasse auf alle Adressen der Spanne derselben Straße (`schl_nr`), bei gleicher Parität
von Anfang und Ende nur auf diese Straßenseite; ein Buchstabe am Ende („1—31a“, „37—37A“ = Haus und Anbau)
zählt als seine Zahl, verdrehte Spannen („40—4“) gelten nicht. Dieselbe Hausnummer wird zu zwei
Adressobjekten, wenn Teil I und II die Straße verschieden schreiben („Baumstr.“/„Baumstraße“, Vorort): die
Teil-II-Zeile des einen Objekts gilt dann auch für das andere. Rangfolge: eigener Teil-II-Eintrag (auch ein
ungeprüfter) > gleiche Hausnummer > Spanne; sich widersprechende Belege ergeben `gemischt`. Punktattribute
`besitz_quelle` (`eintrag` | `nummer` | `spanne` | leer) und `besitz_spanne` (Wortlaut des Belegs, in der
Hausansicht sichtbar); Kennzahlen `besitz_spanne`, `besitz_nummer`. Häuser aus Spannen und Nummerntreffern
zählen in Eigentümerindex und Bubble-Layout mit.
Regel Person → Privatperson (2026-09-26, `eigentuemer.person_nach_regel`): Ein Teil-II-Eintrag ohne
Firmenname gilt ohne Kuratierungszeile als `privatperson` (Ausnahme: Firmenmuster wie „Gebr.“, „& “,
„Söhne“; Stichprobe von 100 Schreibweisen ohne Fehlklassifikation) — ohne Namen und Identität, also weder im
Suchindex noch in den Bubbles. Kennzeichnung: Eintrag `pruefung` hand|regel, Adresse `besitz_pruefung`
(hand | regel — `regel` nur, wenn alle Belege der Adresse Regel-Personen sind), Zählfeld `n_besitz_regel`,
Kennzahl `besitz_regel`; Hausansicht, Balken-Hover und Detailkasten der Perspektiven nennen den Anteil. Vorher hing die Zeile nur an der ersten Nummer —
≈22.000 Adressen blieben „ungeprüft“, Einzelhäuser (Privatpersonen) waren gegenüber Siedlungen und
Werkswohnungen deutlich überzeichnet. Tests: `node --test werkzeuge/tests/`
(`werkzeuge/package.json` mit `type: module`).

Tests:
```
node --test site/tests/                  # Frontend-Module (Resolver, Zustand, Suche …)
python3 -m pytest tests/e2e -q -m e2e    # Playwright-Rauchtests (Server + Chromium, braucht site/daten)
```
`python3 -m pytest -q` lässt die Rauchtests aus (`addopts = "-m 'not e2e'"` in `pyproject.toml`);
`-m e2e` auf der Kommandozeile überschreibt das und schaltet sie gezielt ein. Playwright-Browser
einmalig installieren: `python3 -m playwright install chromium` (Paket über `pip install -e .[e2e]`).

### `site/daten/` — Struktur

| Pfad | Inhalt |
|---|---|
| `adressen.pmtiles` | Ein Punkt je verorteter Adresse (Stufe `haus`/`strasse`, inkl. `stadtplan`), gekachelt mit tippecanoe |
| `haus/<xx>.json` | Einträge je Adress-ID, nach den ersten zwei Hex-Zeichen der ID gehasht (256 Dateien) |
| `adressen/<xx>.json` | Punkteigenschaften je Adress-ID, gleiches Schema wie `haus/<xx>.json`-Schlüssel; unabhängig vom Kachel-Viewport für Export, Liste und Hausansicht |
| `suche/namen/<ab>.json`, `suche/firmen/<ab>.json` | Personen bzw. Firmen nach den ersten zwei Schlüsselzeichen (Schlüsselfaltung: Kleinschreibung, ä/ö/ü/ß transkribiert, Satzzeichen entfernt) |
| `suche/strassen.json` | Heutige und 1936er Straßennamen mit Vorort und Zeilenzahl (keine Adress-IDs) |
| `suche/strassen/<ab>.json` | Je Straße (Name\|Art\|Ort) die sortierten Adress-IDs, Scherbe nach den ersten zwei Schlüsselzeichen |
| `suche/berufe.json`, `suche/berufe/<ab>.json` | Berufsschreibungen mit Häufigkeit bzw. je Schreibung die Adress-IDs mit Zähler |
| `suche/stadtteile.json` | Name, Mittelpunkt, Zeilenzahl je Stadtteil |
| `suche/eigentuemer.json`, `suche/eigentuemer/<xx>.json` | Kanonische Eigentümer (Schlüssel, Name, Häuserzahl, Kategorie) bzw. je Eigentümer die Adress-IDs, Scherbe nach den ersten zwei Schlüsselzeichen; nur geprüfte Zuordnungen |
| `zechen.geojson` | Zechen aus `kuratierung/zechen.csv` mit `status_1936`, `aktiv_1936`, Artikel-/Listenjahren, `jahre_widerspruch`, `plan_1935` |
| `startseite.json` | Beispielpunkte aus `kuratierung/startseite_beispiele.csv` (adress_id, eintrag_id; nur hausgenau) mit Titel, Zeile und Koordinaten — derzeit von der Startseite nicht genutzt (Entscheidung 2026-09-21: ruhiger, abgedunkelter Planhintergrund `site/bilder/startplan-1935-*.{webp,jpg}` ohne Punkte) |
| `faksimile.json` | Seite (`I-333`) → Bildnummer im DigiBib-Viewer, aus `kuratierung/faksimile_seiten.csv` (erzeugt von `werkzeuge/faksimile_mets.py` aus der METS-Datei des Digitalisats; II-170/171 fehlen im Digitalisat) |
| `kennzahlen.json` | Einträge je Teil, Anteile je Präzisionsstufe, Zahl offener Zeilen, Build-Datum, dazu Abdeckung Stellung/Gruppen/Gewerbe und `strassen_mit_linie` (Teilprojekt 5a) |
| `hauptgruppen.json` | Bezeichnungen der OhdAB-Hauptgruppen (`{B21: {bezeichnung, kurz, bereich}}`) aus `kuratierung/hauptgruppen.csv` — Beschriftung der Gruppenachse in Perspektiven und Werkstatt |
| `themen/<id>.json` | Thema-Definitionen (siehe Themenformat unten) |
| `herkunft/*.json` | Herkunftspaket für den Detailkasten der Schlaglichter: je Klasse Schreibweisen, Normen, Quellanteile und Top-10; je Norm/Eigentümer/Rubrik die Einzelherkunft (`docs/perspektiven.md`, Abschnitt Herkunftspfad) |
| `ebenen/strassen.json`, `ebenen/stadtteile.json`, `ebenen/hex.json` | Zählfelder je Straße, Stadtteil und Hexzelle (Teilprojekt 5a, s. u.) |
| `layout/berufe.json`, `layout/eigentuemer.json`, `layout/gewerbe.json` | Vorberechnete Bubble-Layouts für Perspektiven/Werkstatt (Teilprojekt 5a, s. u.) |
| `strassen.geojson`, `hex.geojson` | Straßenlinien (heutige OSM-Führung) und Hex-Polygone, auch als Layer `strassen`/`hex` in `adressen.pmtiles` |
| `stadtteile.geojson` | Heutige OSM-Stadtteilgrenzen (`Stadtteile.geojson()`), je Feature `id` (Name), `quelle`, `stand` — nicht die Stadtteilgrenzen von 1936, siehe `docs/stadtteile.md` |
| `perspektiven/index.json` | Kapitelübersicht der Schlaglichter-Seite (`id, titel, untertitel, freigegeben, reihenfolge`, Teilprojekt 5b, s. u.); fünf Kapitel, Kapitel 0 „Die Datenbasis“ mit Trichtern aus den Kennzahlen (`docs/perspektiven.md`), Kapitel 4 „Bergbau 1936“ (Vorschau, `docs/bergbau.md`; Kapiteldaten `perspektiven/bergbau_punkte.json`) |
| `perspektiven/<id>.json` | Vollständiges, aufgelöstes Kapitel (Schritte, Ansichten, Gruppen, Grenzen, Quellen) — Schema in `docs/perspektiven.md` |

### URL-Parameter (`karte.html?…`)

| Parameter | Bedeutung | Standard |
|---|---|---|
| `q` | Suchtext | leer |
| `ebene` | Aktive Teile, kommagetrennt: `I,II,III` | alle |
| `stadtteil` | Filter auf einen heutigen Stadtteil | keiner |
| `praez` | Aktive Präzisionsstufen, kommagetrennt: `haus,strasse,stadtplan` | alle |
| `beruf` | Berufsfilter | keiner |
| `thema` | Aktives Thema (`site/daten/themen/<id>.json`) | keins |
| `eigentuemer` | Filter auf einen kanonischen Eigentümer (Suche im Thema Besitz) | keiner |
| `ohdab` | Filter auf eine OhdAB-Normbezeichnung (Suche im Thema Berufe); schließt sich mit `beruf` und `eigentuemer` aus | keiner |
| `id` | Adress-ID (öffnet die Hausansicht) oder Eintrags-ID (öffnet die Hausansicht und hebt den Eintrag hervor) | keine |
| `karte` | Grundkartenstil: `positron` oder `liberty` | `positron` |
| `plan` | Stadtplan-1935-Ebene ein-/ausblenden: `0` oder `1` — nur nach Freigabe wirksam (siehe unten) | `0` |
| `zechen` | Zechen-Ebene ein-/ausblenden: `0` oder `1` | `0` |
| `z` | Zoomstufe | 11 |
| `c` | Kartenmitte `lon,lat` | Essen gesamt |
| `ansicht` | Ansicht-Definition (base64url-JSON, Spec §4/`site/js/ansicht.js`) — färbt Stadtteile, Straßen und Hexfelder statt der Punkte; ersetzt kein Thema | keine |

Fehlende Parameter fallen auf den Standardwert zurück. Änderungen an Filtern/Ansicht schreiben
`history.replaceState`; Navigationsschritte (Suche, Haus öffnen) `pushState`. Die Grundkartenwahl
steht zusätzlich in `localStorage`. `PLAN_FREIGEGEBEN` (`site/js/konfig.js`) sperrt die
Stadtplan-1935-Ebene, bis die Stadt Essen bzw. der Historische Verein die Nutzung freigibt.

### Themenformat (`kuratierung/themen/<id>.json` → `site/daten/themen/`)

Felder: `titel`, `text`, `grundlage` (Quelle, Prüfdatum), `filter` (Merkmale, Ebenen), `farbe`
(eine Farbe | Kategorien (`art: kategorien`, `feld`, `werte`, `sonst`) | Skala auf Merkmalswert), `zusatz` (z. B. `zechen: true`), `legende`,
`darstellung` (`punkte`; `strassen` ist für Teilprojekt 4 reserviert), `freigegeben` (nur dann
erscheint die Kachel auf der Startseite). Die Definitionen liegen versioniert in `kuratierung/themen/`;
Stufe 06 kopiert sie nach `site/daten/themen/` und erzeugt dort `index.json`. Merkmale stammen aus `kuratierung/merkmale/<name>.csv`
(Spalten `feld`, `art`, `muster`, `merkmal`, `beleg`, `bearbeiter`, `datum`) und werden in Stufe 06 an
jeden Eintrag angehängt und je Adresse gezählt (`m_<merkmal>` in `adressen.pmtiles`). Aktiv über
`thema=<id>` in der URL, kombinierbar mit Suche und Filtern. Ausnahme in `kuratierung/merkmale/`:
`bergbau.csv` ist keine Merkmalsregel, sondern die Tabelle Norm → Bergbau-Gruppe (`docs/bergbau.md`).
Optional `schalter: {praefix, klassen, namen}` (seit 2026-09-28, Thema „Bergbau“): die Legende zeigt je
Klasse ein Kästchen; abgeschaltete Klassen fallen aus dem Kartenfilter (`any` über `<praefix><klasse> > 0`),
die Farbe folgt dem Rang der Reihenfolge in `klassen` über die eingeschalteten; Zustand im URL-Parameter
`klassen=` (leer = alle, `keine`, sonst Komma-Liste; nur bei einem Thema mit Schaltern).

## Berufe (Teilprojekt 4)

Berufsangaben (`Beruf o. ä.`, Teil I/II) werden je Schreibweise auf ein Schlüssel-Item der
**OhdAB** (Ontologie historischer, deutschsprachiger Amts- und Berufsbezeichnungen, Katrin
Moeller/Uni Halle, publiziert auf FactGrid, CC BY 4.0) abgebildet
(Spec `docs/superpowers/specs/2026-09-23-berufe-design.md`).

```
python3 werkzeuge/ohdab_laden.py [--ziel kuratierung/ohdab.csv]   # Schnappschuss per SPARQL von database.factgrid.de
```

`kuratierung/ohdab.csv` (versioniert, Schnappschuss vom 2026-09-23, 46.220 Items): Spalten
`ohdab_id, qid, norm, maennlich, weiblich, niveau, gattung_id, gattung`. `niveau` ist einer von
sieben Schlüsseln (FactGrid-Label → Schlüssel):

| Label | Schlüssel |
|---|---|
| Tätigkeitsprofil Helfer- und Anlerntätigkeiten | `helfer` |
| Fachliche Tätigkeiten | `fachlich` |
| Komplexe Spezialistentätigkeit | `spezialist` |
| Hoch komplexe Tätigkeiten | `hochkomplex` |
| Tätigkeitsprofil Aufsichtskräfte | `aufsicht` |
| Tätigkeitsprofil Führungskräfte | `fuehrung` |
| (fehlt/unbekannt) | `keins` |

`gattung_id` ist der Teil der OhdAB-ID vor dem Bindestrich (`B 21112`), `gattung` das Label des
Kategorie-Items ohne den ID-Präfix. `pipeline/lib/berufe.py` lädt den Schnappschuss und bricht
mit klarer Meldung ab, wenn die Datei fehlt.

```
python3 werkzeuge/berufe_vorschlag.py [--min-nennungen 5] [--llm]   # Vorschlag je Schreibweise → kuratierung/berufe.csv
python3 werkzeuge/serve.py 8765                                      # dann http://localhost:8765/werkzeuge/berufe.html
python3 pipeline/06_karte_export.py                                  # geprüfte Zuordnungen in die Karte (Thema „Berufe“)
```

`werkzeuge/berufe_vorschlag.py` liest `build/eintraege.csv`, `kuratierung/ohdab.csv`,
`kuratierung/berufe_abkuerzungen.csv` und `kuratierung/berufe.csv`; schreibt
`kuratierung/berufe.csv` (Upsert je Schreibweise ≥ `--min-nennungen`, Standard 5) sowie
`build/berufe_belege.json` (bis 5 Beispiel-Einträge je Schreibweise) und
`build/berufe_kandidaten.json` (bis 20 Kandidaten je Schreibweise für das Werkzeug). Ablauf je
Schreibweise: Status abtrennen (`ruhestand`/`invalide`/`witwe`, Vokabular s. u.), Kern über
`kuratierung/berufe_abkuerzungen.csv` auflösen (ganze Wortfolgen vor Einzelwörtern), dann
Exakt-Abgleich auf die gefalteten Formen aus `kuratierung/ohdab.csv` (männliche und weibliche Form,
Norm ohne Geschlechtszusatz und ohne „ - “-Zusatz, dazu die Formen ohne Klammerzusatz —
„Bankbeamt(er/in) (mittl. Dienst)“ → „bankbeamter“ — und die Teile einer Mehrfachnorm wie
„Wächter/in, Aufseher/in“; Komma-Zusätze wie „Lehrer/in, akadem.“ bleiben ein Ganzes) und zuletzt
RapidFuzz „ähnlich“ ab Schwelle 0,90; mit `--llm` zusätzlich eine LLM-Reserve für Zeilen ohne Vorschlag
(Anthropic API, nur `vorschlag_grund=llm`, nie `geprueft`). Auf einem Lauf ohne Katalog fanden
77,5 % der Nennungen einen Vorschlag, mit dem vorbefüllten Katalog (`berufe_abkuerzungen.csv`,
486 Zeilen) steigt das auf **89,9 % der Nennungen** (154.772 von 172.136, verteilt auf 1.159 von
1.977 Schreibweisen); mit den Klammer-/Mehrfachnorm-Formen und 212 weiteren Katalogzeilen aus
Endungsregeln (`-mstr.` → `-meister`, `-arb.` → `-arbeiter` usw., nur übernommen, wenn das Vollwort
exakt in der OhdAB steht) sind es 1.729 Schreibweisen mit Vorschlag.

**Gewerbebezeichnungen.** Rund 220 Schreibweisen mit 6.900 Nennungen sind keine Berufe, sondern
Betriebe: „Lebensmittel“, „Bäckerei“, „Fuhrgesch.“, „Heißmangel“. Es sind Personeneinträge des
Teils I (Name, Vorname, Adresse, kein Firmenname), bei denen Scherl statt der Berufsbezeichnung das
Gewerbe des Inhabers setzt — dieselbe soziale Gruppe wie „Bäckermstr.“ (84 % bzw. 74 % dieser
Personen stehen zusätzlich als Firma in Teil III, gegenüber 7 % der „Bäcker“). Sie bekommen das
Item des Berufsträgers (Bäckerei → Bäcker/in, Lebensmittel → Lebensmittelhändler/in), den Status
`gewerbe` und `niveau_unsicher=ja`, weil die Inhaberstellung im OhdAB-Niveau nicht abgebildet ist
(Bäcker = fachlich, Bäckermeister = Aufsicht). Teil III bleibt außen vor, die Person wird also nicht
doppelt gezählt. Details und Zahlen: `docs/berufe_gewerbeformen.md`.

`kuratierung/berufe.csv` (eine Zeile je Schreibweise): Spalten `schreibweise, nennungen, beruf,
status, ohdab_id, niveau_unsicher, geprueft, vorschlag_grund, bearbeiter, datum, hinweis`.
`status` ist leer oder eine `;`-Liste aus `ruhestand`, `invalide`, `witwe`, `gewerbe`; `vorschlag_grund`
nennt die beteiligten Schritte (`katalog`, `exakt`, `aehnlich 0.93`, `llm`, Kombinationen wie
„katalog; exakt“). Sperrregel wie bei den Eigentümern: `geprueft=ja` oder
`bearbeiter≠berufe_vorschlag` → die Automatik ändert die Zeile nicht mehr (nur `nennungen` wird
nachgeführt); `geprueft=ja` verlangt eine gültige `ohdab_id`. Niveau und Gattung stehen nicht in
der Tabelle, sondern kommen beim Export aus dem Schnappschuss (eine Wahrheit); `niveau_unsicher`
setzt nur der Mensch im Werkzeug, für Fälle, in denen die OhdAB-Stufe für die 1936er Schreibweise
zu unsicher ist (häufig bei „Arbeiter“). `kuratierung/berufe_abkuerzungen.csv`: Spalten `kurz,
lang, status, beleg, bearbeiter, datum`; die Vorlage hat kein Abkürzungsverzeichnis für Berufe,
daher steht bei allen vorbefüllten Zeilen `beleg=üblich`.

Export (Stufe 06): Mehrheitsregel je Adresse — unter den geprüften Teil-I-Einträgen hat eine
Niveaustufe mehr als die Hälfte → diese Stufe als Punktattribut `niveau`; sonst `gemischt`; nur
`unsicher`-Einträge → `unsicher`; kein geprüfter Eintrag → `ungeprueft`. Zusätzlich Zählfelder
`n_helfer, n_fachlich, n_spezialist, n_hochkomplex, n_aufsicht, n_fuehrung, n_unsicher` (nur bei
Wert > 0) für Teilprojekt 5. Suchindex nach Normbezeichnung: `suche/berufe_norm.json` und
`suche/berufe_norm/<praefix>.json` (nur geprüfte Zuordnungen; der bisherige Rohtext-Index
`suche/berufe.json` bleibt für ungeprüfte Schreibweisen bestehen). Kennzahlen `berufe_geprueft`
(Anteil der Teil-I-Nennungen verorteter Adressen mit geprüfter Zuordnung) und
`berufe_schreibweisen_geprueft` (Zahl geprüfter Schreibweisen) in `kennzahlen.json`.

**Soziale Stellung (Teilprojekt 5a).** Zwei zusätzliche Spalten in `kuratierung/berufe.csv`:
`stellung` (neun Klassen: `arbeiter, angestellte, beamte, selbstaendige, freie_berufe, unternehmer,
ohne_erwerb, kaufleute, unbestimmt`) und `stellung_geprueft` (`ja` | leer). Vorschlag:
`python3 werkzeuge/stellung_vorschlag.py [--wurzel PFAD]` füllt `stellung`, wo `stellung_geprueft`
leer ist — auch bei für die Berufszuordnung bereits gesperrten Zeilen, weil die Stellung eine
eigene, unabhängig zu prüfende Frage ist. Handprüfung im Berufe-Werkzeug (`werkzeuge/berufe.html`):
Zifferntasten `1`–`9` wählen die Klasse (Reihenfolge wie im Vokabular), Taste `T` bestätigt
(`stellung_geprueft=ja`), Taste `A` überträgt die Stellung zusätzlich auf alle Schreibweisen desselben
OhdAB-Items ohne Status mit geprüftem Beruf („Ing.“, „Ingen.“, „Ingenieur“ in einem Zug; Statuszeilen wie
„a. D.“ bleiben außen vor), Checkbox „Stellung offen“ filtert auf ungeprüfte Zeilen. Export, sobald der
Beruf geprüft ist; `stellung_quelle` (`hand` | `vorschlag`) kennzeichnet je Eintrag, ob Mensch oder
Automatik entschieden hat, `n_stellung_hand` zählt je Ebene (Entscheidung 2026-09-25, nach Handprüfung von
91 % der Nennungen). Regeln, Beispiele und Grenzfälle:
`docs/stellung.md`. Für Handwerksberufe ohne Meister-/Gewerbezusatz („Friseur“, „Schneider“) liefert
`python3 werkzeuge/handwerk_deckung.py` die Entscheidungsgrundlage: Betriebe in Teil III gegen die als
Inhaber gekennzeichneten Einträge in Teil I je Berufsfamilie (`docs/stellung_deckung.md`,
`build/handwerk_deckung.json` → Kennzahl-Zeile im Werkzeug).

## Datenkerne für Perspektiven und Werkstatt (Teilprojekt 5a)

Vierter Datenkern neben Berufen (Teil I), Eigentümern (Teil II) und Merkmalen: Gewerbebetriebe aus
Teil III, dazu Berufsgruppen, Aggregationsebenen und Bubble-Layouts als Vorstufe für die Seiten
Perspektiven und Werkstatt (Teilprojekt 5b/5c, noch nicht gebaut). Spec:
`docs/superpowers/specs/2026-09-24-perspektiven-werkstatt-design.md`.

### Berufsgruppen = OhdAB-Hauptgruppen (`kuratierung/hauptgruppen.csv`)

Seit 2026-09-25 gibt es keine handkuratierten Branchen mehr (die 14 Gruppen in `gruppen.csv` samt
Vorschlag und Handprüfung sind entfallen — die Berufsbezeichnung nennt die Tätigkeit, nicht den
Betrieb, und selbst gezogene Grenzen erzeugten Verlegenheitszuordnungen; Spec §5.2). Die Gruppe eines
Eintrags ist seine OhdAB-Hauptgruppe (KldB-2010-Hierarchie, `gattung_id[:4]`, Schlüssel ohne
Leerzeichen wie `B21`; `pipeline/lib/gruppen.py`: `hauptgruppe()`, `gruppe3()`). Branchenlose
Sammelitems liegen in `B20`, Berufslose in `A10`. `kuratierung/hauptgruppen.csv` liefert nur die
Bezeichnungen (`hauptgruppe, bezeichnung, kurz, bereich, quelle` — amtliche KldB-Bezeichnung, eigene
Kurzform; Quelle `KldB 2010` oder `OhdAB` für deren Zusatzgruppen); der Export bricht ab, wenn eine
Hauptgruppe des OhdAB-Schnappschusses fehlt, und schreibt `site/daten/hauptgruppen.json`. Einträge ohne
geprüften Beruf zählen als `ungeprueft`. Zählfeld je Einheit: `n_gr_<hauptgruppe>`. Gröbere Gruppen
(„Industrie“ = B21 + B24 + B25 + …) bilden Kapitel und Nutzer in Perspektiven/Werkstatt.

### Gewerberubriken Teil III (`kuratierung/gewerbe.csv`)

Die Rubrik steht nicht in einer eigenen Spalte, sondern als Suffix hinter dem letzten Komma des
Firmennamens („M. Jäger, Althandlung“ → Firma „M. Jäger“, Rubrik „Althandlung“); ohne Komma keine
Rubrik. Realer Lauf 2026-09-24: 848 distinkte Rubriken (18.863 Betriebe). Spalten `rubrik,
betriebe, gruppe, art, geprueft, bearbeiter, datum, hinweis`; `gruppe` = Branche (15 Schlüssel,
`pipeline/lib/gewerbe.GRUPPEN`, seit 2026-09-25 mit `finanzen_recht`), `art` (7 Schlüssel,
`pipeline/lib/gewerbe.py`, `ARTEN`): `handwerk, handel, gastgewerbe, dienstleistung, industrie,
freier_beruf, sonstige`. Vorschlag aus Wortregeln auf der Rubrik:
`python3 werkzeuge/gewerbe_vorschlag.py`. Handprüfung: `werkzeuge/zuordnung.html?tabelle=gewerbe`
(Zifferntasten setzen `gruppe`, Umschalt+Ziffer setzt `art`). Realer Lauf: `sonstige` 11,8 % (100
von 848 Rubriken, unter der 20-%-Vorgabe). Dublettenregel: Betriebe, die unter mehreren Rubriken an
derselben Adresse mit gleichem Firmennamen stehen (`betriebsschluessel()`: gefalteter Firmenname +
Straße + Hausnummer + Vorort), zählen je Gruppe nur einmal. Export (seit 2026-09-25 wie bei der Stellung):
jeder Wert im Vokabular wird exportiert, `gewerbe_quelle` = `hand` | `claude` | `vorschlag` kennzeichnet je
Eintrag die Herkunft; Prinzipien und entschiedene Grenzfälle in `docs/gewerbe.md`. Zählfelder je Einheit:
`n_gw_<gruppe>`, `n_gwa_<art>`.

### Zählfelder und Aggregationsebenen (`pipeline/lib/ebenen.py`)

`zaehlfelder(adresse)` zählt je Adresse einmal: Teile (`n_I`, `n_II`, `n_III`), Niveau (`n_helfer` …,
wie bisher), Stellung (`n_st_<klasse>`), Berufsgruppe (`n_gr_<gruppe>`), Gewerbegruppe/-art
(`n_gw_<gruppe>`, `n_gwa_<art>`, je Betrieb einmal über die Dublettenregel) und Besitzklasse
(`n_bs_<klasse>`) sowie Bergbau-Gruppe (`n_bb_<gruppe>`, aus `kuratierung/merkmale/bergbau.csv`, `docs/bergbau.md`;
je Adresse zusätzlich das Rangfeld `bergbau` in den Kacheln). Teil-I-Einträge ohne geprüften Beruf zählen bei Stellung und Gruppe als
`unbestimmt`/`ungeprueft` mit — der Nenner bleibt so sichtbar, statt Zeilen stillschweigend zu
verwerfen. `aggregiere(adressen, ebene)` summiert diese Felder auf drei Ebenen
(`EBENEN = ("strasse", "stadtteil", "hex")`):

- **Straße** (`site/daten/ebenen/strassen.json`): Schlüssel die heutige fünfstellige `schl_nr`
  (Dickhoff-Konkordanz) oder, wenn nicht heute benannt, `1936:<Schreibung>|<Vorort>`; Felder `id,
  name, stadtteil` (häufigster) plus alle Zählfelder. Realer Lauf 2026-09-24: 2.040 Straßen-
  Einheiten, davon 2.016 heutige Straßen und 24 nur-1936er Einheiten (616 KB).
- **Stadtteil** (`site/daten/ebenen/stadtteile.json`): `id, lat, lon` (Mittel), `rang_nord` (1 =
  nördlichster; Einheiten ohne Stadtteil bekommen keinen Rang). Adressen ohne Stadtteil werden nicht
  verworfen, sondern unter `id="ohne_stadtteil"` mitgezählt, damit die Summe der Einheiten stets der
  Summe der Adressen entspricht (79 KB).
- **Hexraster** (`site/daten/ebenen/hex.json`): „pointy-top“-Sechsecke, 120 m Kantenlänge, lokale
  äquirektangulare Projektion um das Essener Zentrum, Zellen-ID `q_r` in Axialkoordinaten
  (`hex_zelle`, `hex_mitte`, `hex_polygon`); nur Zellen mit mindestens einer Adresse (688 KB).

### Layouts (`pipeline/lib/layout.py`, `site/daten/layout/*.json`)

Deterministische Bubble-Packung (Kreispackung per Spiralsuche, keine Zufallszahl, keine Simulation —
gleiche Eingabe liefert immer dieselben Koordinaten). Drei Dateien, je ein `dict(kreise=[...],
gruppen=[...])`:

- `layout/berufe.json` — Kreis je OhdAB-Norm (Fläche ∝ Nennungen), gepackt nach Berufsgruppe
  (`packe_gruppen`), zusätzlich `niveau_xy` je Kreis aus einem Beeswarm-Layout nach Niveau-Spalte
  (Beeswarm-Spalten = `NIVEAUS_REIHE` (7 Werte: `helfer, fachlich, spezialist, hochkomplex,
  aufsicht, fuehrung, keins`) `+ ["unsicher"]`).
  Realer Lauf 2026-09-24: 854 Kreise (154 KB).
- `layout/eigentuemer.json` — Kreis je identifiziertem Eigentümer (Fläche ∝ Häuser), gepackt nach
  Kategorie. Realer Lauf: 101 Kreise (11 KB).
- `layout/gewerbe.json` — Kreis je Gewerberubrik (Fläche ∝ Betriebe), gepackt nach Gruppe. Realer
  Lauf: 823 Kreise (85 KB).

Kreisfelder: `{id, n, r, x, y, ...}` (`r` aus `radius(n, max_n)`, Fläche proportional zur Menge, nicht
der Radius). `gruppen`: `[{gruppe, x, y, r}]`, die Packungshülle je Gruppe. `packe_gruppen` packt
zuerst jede Gruppe für sich, dann die Gruppenkreise, und verschiebt die Mitglieder entsprechend;
`beeswarm(kreise, spalten)` legt Kreise je Spalte vom Ursprung nach außen ab (erste freie Stelle,
abwechselnd ±).

### Kachelschichten `strassen`/`hex` und Straßenlinien (OSM)

`adressen.pmtiles` bekommt zwei neue Layer neben `adressen`: `strassen` (Linien, Feature-`id` =
`int(schl_nr)`) und `hex` (Polygone, `id` = `q_r`) — beide tragen nur `id`/`name`/`stadtteil` in der
Kachel; die Zählfelder kommen zur Laufzeit aus den `ebenen/*.json`-Dateien per MapLibre
`feature-state`, damit Nutzergruppen ohne Tile-Neubau eingefärbt werden können. Gezeichnet werden die
Schichten hier noch nicht (das ist Teilprojekt 5b/5c) — dieser Plan erzeugt nur die Daten.

Straßenlinien kommen aus OpenStreetMap (heutige Führung, nicht die von 1936):
`python3 werkzeuge/osm_strassen_laden.py [--url …] [--halbieren]` fragt die Overpass API ab
(OSM-Relation 62713, Stadt Essen; nur benannte Fahrstraßen ohne Fuß-/Rad-/Nebenwege) und schreibt
`build/osm_strassen.json` (nicht versioniert). Details, Filter, Lizenz und Kennzahlen des letzten
Abrufs: `docs/osm_strassen.md`. `strassen_features()` verknüpft nur heutige Straßen (fünfstellige
`schl_nr`) mit einer gefundenen OSM-Linie; Straßen ohne Linie bleiben ungezeichnet, werden aber
gezählt (`kennzahlen.json` → `strassen_mit_linie`). Realer Lauf 2026-09-24: 1.999 von 2.016 heutigen
Straßen (99,2 %) haben eine Linie.

### Stadtteil je Adresse (`pipeline/lib/stadtteile.py`, `site/daten/stadtteile.geojson`)

Bislang trug jede Adresse den (teils mehrdeutigen, `;`-getrennten) Straßen-Stadtteil aus
`build/eintraege.csv`. Seit dem Polygonabgleich ordnet `karte_export.gruppiere` jede Adresse per
Punkt-in-Polygon-Test (`Stadtteile.zuordnen`) genau einem der **heutigen** OSM-Stadtteile zu (ODbL,
© OpenStreetMap-Mitwirkende — nicht die Stadtteilgrenzen von 1936, siehe `docs/stadtteile.md`); nur
wenn eine Adresse außerhalb aller Polygone liegt, bleibt der bisherige Straßen-Stadtteil als
Fallback. Das Feld `stadtteil_quelle` (`polygon` | `strasse` | ``) unterscheidet die beiden Fälle je
Adresse; die Kennzahl `stadtteil_polygon` nennt den Prozentanteil der verorteten Adressen mit
Polygontreffer. `site/daten/stadtteile.geojson` (aus `Stadtteile.geojson()`) trägt die Polygone
selbst, je Feature mit `id` (Stadtteilname), `quelle` und `stand` (Abrufdatum) — für Kartenanzeige
und Perspektiven. Grundlage: `python3 werkzeuge/osm_stadtteile_laden.py` → `build/osm_stadtteile.json`
(nicht versioniert), Namensabgleich `kuratierung/stadtteile_osm.csv`.

### Kennzahlen (`site/daten/kennzahlen.json`)

Zusätzlich zu den bestehenden Feldern (Teile, Präzisionsstufen, Berufe): `stellung_geprueft` (von Hand bestimmt,
seit 2026-09-27 ohne die handgeprüft-unbestimmten, damit die drei Stellung-Anteile 100 % ergeben — vorher 101,8 %),
`stellung_vorschlag`, `stellung_unbestimmt`, `gewerbe_geprueft`, `gewerbe_entschieden`, `gewerbe_vorschlag`
(Prozentwerte, `_prozent(z, n)`; `gruppen_geprueft` entfiel 2026-09-25),
`strassen_mit_linie` (Zahl) und `stadtteil_polygon` (Prozentanteil der verorteten Adressen mit Polygontreffer,
s. o.). Stand 2026-09-25 (Lauf nach der ersten Handprüfungsrunde): `stellung_geprueft: 73.0` (nach der Korrektur 71,2),
`stellung_vorschlag: 6.2`, `stellung_unbestimmt: 22.6`, `gewerbe_geprueft: 68.1`, `gewerbe_entschieden: 20.2`,
`gewerbe_vorschlag: 11.7`, `besitz_geprueft: 7546` (nach den Hausnummernspannen und der Regel vom 26.9. 64439), `stadtteil_polygon: 100.0`, `adressen: 70316`. Diese Werte
ändern sich mit jeder weiteren Handprüfungsrunde beim nächsten Lauf von `pipeline/06_karte_export.py`.

Seit 2026-09-28 Bergbau (Kapitel 4): `bergbau_n` (verortete Teil-I-Einträge mit Bergbau-Norm), `bergbau_belegschaft_n`,
`bergbau_aufsicht_n`, `bergbau_leitung_n`, `bergbau_invaliden_n`, `bergbau_haeuser_n` (geprüfte Adressen der Klasse Bergbau).

Seit 2026-09-27 zusätzlich absolute Zähler für die Trichter von Kapitel 0 der Schlaglichter: `eintraege`,
`eintraege_I/II/III`, `stufe_haus/strasse/stadtplan/offen`, `besitz_hand` (= `besitz_geprueft − besitz_regel`),
`teil_i_n`, `beruf_geprueft_n`, `stellung_bestimmt_n` (= hand + vorschlag), `stellung_hand_n/vorschlag_n/unbestimmt_n` (Summe = `teil_i_n`), `betriebe_n`,
`gewerbe_hand_n/claude_n/regel_n` (Summe = `betriebe_n`). Wortlaut: `besitz_geprueft` heißt nach außen
„Adressen mit Besitzklasse“; „von Hand geprüft“ ist nur `besitz_hand`. Prüfblatt für die Zahlen in den
Kapiteltexten: `python3 werkzeuge/perspektiven_zahlen.py`.

Ablauf des gesamten Teilprojekts 5a:

```text
python3 werkzeuge/stellung_vorschlag.py        # Stellung je Schreibweise vorschlagen → berufe.html (Ziffern, T)
python3 werkzeuge/handwerk_deckung.py          # Deckung Teil III ↔ Teil I je Handwerksfamilie → docs/stellung_deckung.md, Kennzahl im Werkzeug
python3 werkzeuge/gewerbe_vorschlag.py         # Rubriken Teil III → zuordnung.html?tabelle=gewerbe
python3 werkzeuge/osm_strassen_laden.py        # Straßenlinien (Overpass) → build/osm_strassen.json
python3 werkzeuge/osm_stadtteile_laden.py      # Stadtteilgrenzen (Overpass) → build/osm_stadtteile.json
python3 pipeline/06_karte_export.py            # Ebenen, Layouts, Schichten, Stadtteile, Kennzahlen
```

## Perspektiven (Teilprojekt 5b)

Scrollytelling-Seite `site/schlaglichter.html` (nach außen „Schlaglichter“; Code, Kuratierung und Daten
behalten den Arbeitsnamen `perspektiven` aus der Spec): Einleitung, Inhaltsverzeichnis, Kapitel untereinander,
je Kapitel eine klebende Bühne über die volle Fensterhöhe und -breite, an der die Schritte als
schmale Karten vorbeilaufen — auf breiten Schirmen in der rechten Spalte (das Bild nutzt die linken
60 %), auf schmalen über dem unteren Drittel (das Bild nutzt die oberen 62 %); zwischen zwei Karten
liegt ein Bildschirm Scrollweg (Scrollama 3.2.0, lokal in `site/vendor/scrollama.js`, kein CDN —
Datenschutz und Reproduzierbarkeit, s. `site/vendor/README.md`). Das Bild bekommt, was Legende und
Zahlenzeile auf der Bühne übrig lassen (`zeichenflaeche` in `perspektiven_modell.js`); die Rangliste
teilt sich bei vielen Zeilen in zwei Spalten oder wächst und wird herunterskaliert.
Nur Kapitel mit `freigegeben: true` erscheinen; alle Kapitel (auch unfreigegebene) sind mit
`?vorschau=1` sichtbar, damit der Projektleiter Text und Ansicht im echten Seitenkontext prüfen kann,
ohne sie zu veröffentlichen — dieser Parameter steht deshalb an keiner öffentlichen Stelle (Startseite,
Über-Seite) verlinkt. Die Startseiten-Kachel „Perspektiven“ (`site/index.html`) bleibt `hidden`, bis
`start.js` in `perspektiven/index.json` mindestens ein `freigegeben: true`-Kapitel findet; ein
fehlender oder fehlerhafter Index bricht die Startseite dabei nicht ab.

**Ansicht-Format** (Spec §4, `site/js/ansicht.js`): Karte, Perspektiven und Werkstatt lesen und
schreiben dasselbe Objekt `{daten, ebene, form, gruppen, kaufleute, unsicher, mass, bezug, min_n,
filter, karte}`. Es wird als base64url-JSON im URL-Parameter `?ansicht=` transportiert (`kodiere`/
`dekodiere`); Standardwerte werden weggelassen, damit Links kurz bleiben. `kennzahlen(einheit, ansicht)`
berechnet Anteil, dominante Gruppe, Mischung und Dichte je Einheit rein im Browser aus den Zählfeldern
der `ebenen/*.json`-Dateien.

**Kapitel-JSON** (`kuratierung/perspektiven/<id>.json` → `site/daten/perspektiven/`): Schema, Pflichtfelder,
die Gruppen-Kurzform `wie:`, die Platzhalter in `grenzen` und die Freigabelogik stehen in
`docs/perspektiven.md`. Drei Kapitel sind angelegt (Wohneigentum; Soziale Stellung; Gewerbe und
Versorgung), alle mit `freigegeben: false` — die Ansichten sind fertig, die Texte noch Platzhalter.

**Formen** (`site/js/formen/{balken,bubbles,rangliste,stadtteilkarte,punktkarte,skalen}.js`): reine SVG-Erzeuger
ohne DOM-Abhängigkeit, gemeinsame Schnittstelle `zeige(ansicht, daten, optionen) → {svg, legende,
zahlen}`. Die Punktkarte (Kapitel 4 Bergbau, `docs/bergbau.md`) trägt in der Ansicht das Feld
`punkte: {zustand: gesammelt | karten | haeuser, hervor: [Gruppenname]}` und zusätzlich `aktualisiere(svgEl, …)`:
folgen zwei Punktkarten-Schritte mit denselben Gruppen aufeinander, verschiebt die Seite die vorhandenen Kreise
statt neu zu zeichnen; die Bewegung dazwischen zeichnet `uebergang(…)` auf einem Canvas über dem SVG (eine
CSS-Transition auf ≈ 3.000 Kreisen lief mit 2–4 fps); ihre Kapitellinks führen auf das Thema „Bergbau“ der Karte (`klassen=`). Einheiten unter `min_n` (zu wenige geprüfte Adressen) werden grau statt eingefärbt
dargestellt (Grau-Regel); `zahlen` nennt neben N und den ausgeschlossenen Nennungen, wie viele
Einheiten der Ebene gezeichnet sind und wie viele unter `min_n` grau bleiben — die Perspektiven-Seite
druckt das als „… · 15 von 50 Einheiten gezeichnet · 8 unter 200 Nennungen (grau, nicht eingefärbt)“,
damit eine Rangliste oder ein Ausschnitt nicht als Vollständigkeit missverstanden wird. Farbregel
(`farbeNachMass`) und Legendentexte (`legendeNachMass`) stehen einmal in `skalen.js` und gelten für
alle Formen und für die Kartenlegende.

**Karte `?ansicht=`** (`site/js/app.js`, `karte.js`, `ansicht_farben.js`): Drei neue, standardmäßig
unsichtbare Ebenen `stadtteile-flaeche`, `strassen-linie`, `hex-flaeche` werden per MapLibre
`feature-state` eingefärbt, je nachdem welche `ebene` die aktive Ansicht trägt; Punkte
(`ebene=adresse`) bleiben ungefärbt (das folgt erst in 5c mit den Nutzergruppen der Werkstatt). Die
Sidebar zeigt die aktive Ansicht in `#ansichtkopf`; die Legende der Ansicht (Stufen bzw. Gruppen mit
Farbe, `N`, `min_n`, graue Einheiten, nicht darstellbare Straßen, ausgeschlossene Nennungen `n_aus`,
Herkunft/Grundlage) steht im Legendenkasten der Karte. Ein unlesbarer `?ansicht=`-Parameter wird nicht
zur Standardansicht, sondern als „Ansicht nicht lesbar – Karte ungefärbt.“ gemeldet. Perspektiven-Schritte verlinken „Auf
der Karte öffnen“ (`karte.html?ansicht=…`) und „In der Werkstatt öffnen“; letzterer Link führt erst ab
Teilprojekt 5c auf eine bestehende Seite (`site/werkstatt.html` existiert noch nicht).

**Kennzeichnungen:** Die Stadtteilgrenzen sind durchgehend die **heutigen** (OpenStreetMap,
`admin_level=10`, ODbL — nicht die von 1936, s. `docs/stadtteile.md`); jede Kennzahl je Stadtteil trägt
diesen Vorbehalt in Karte und Perspektiven. Jede vorgeschlagene (nicht handgeprüfte) Stellungs- bzw.
Gewerbezuordnung ist an `stellung_quelle`/`gewerbe_quelle` erkennbar (`hand` vs. Automatik-Vorschlag).
Kapiteltexte sind, solange `freigegeben: false` gilt, ausdrücklich Platzhalter und nicht redaktionell
geprüft.

Der Detailkasten folgt dem Zeiger: Schweben über einer Einheit (Balkensegment, Stadtteil, Kreis,
Ranglistenzeile) zeigt ihn flüchtig direkt über der Einheit (`detailLage`: mittig darüber, sonst
darunter, immer im Fenster; auf schmalen Schirmen als Leiste am unteren Rand) und hebt die Einheit
hervor, ein Klick stellt ihn fest (dann erst mit Schließknopf und Kartenlink). Schweben über einer anderen Einheit, Schließen oder ein
Schrittwechsel löst die Feststellung wieder. Die Logik steht als `detailZustand` in
`perspektiven_modell.js` (geprüft), das Verdrahten in `perspektiven.js`; Geräte ohne echten Zeiger
(`(hover: hover) and (pointer: fine)`) bekommen nur den Klickweg, weil dort kein „Verlassen“ käme.

**Ruling:** Die im Spec (§4.2) skizzierte Migration der Themen (`kuratierung/themen/`) auf das
Ansicht-Format ist **nicht** Teil von 5b — `themen.js` bleibt unverändert. Sie gehört zu Teilprojekt 5c,
sobald die Werkstatt Standardgruppen aus den Themen lesen soll.

Tests: `node --test site/tests/` (Ansicht-Modell, Formen ohne DOM-Teile), `python3 -m pytest -q -m
"not e2e"` (Kapitel-Schema, Export, Stadtteilzuordnung). Playwright-Rauchtests für Scrollama-
Schrittwechsel, Detailkasten und Kartenlinks folgen mit der Werkstatt (5c), s. Spec §9.

## Dokumentation

Spezifikation: Obsidian-Vault `~/Projekte/obsidian-chris`, Ordner
`10-Projekte/adressbuch-essen-1936-v2/` (`Spec-1-Datenpipeline.md`) — verbindlich.
Plan und Protokolle: `docs/superpowers/`.
