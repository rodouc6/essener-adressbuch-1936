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
Schreibt nach `site/daten/` (Adresspunkte, Sucheindex, Kennzahlen, Themen). Ergebnis wird
committet, nicht neu gebaut beim Deploy (Pages baut nicht). Der Workflow für GitHub Pages liegt als
`docs/pages.yml.beispiel` bereit und wird erst bei der Veröffentlichung nach `.github/workflows/` kopiert
(Push von Workflow-Dateien braucht ein `gh`-Token mit `workflow`-Scope).

`site/daten/` wiegt insgesamt ≈110 MB (`adressen.pmtiles` 3,5 MB, `haus/` 55 MB, `suche/` 37 MB,
`adressen/` 18 MB) und wird bei jeder Regenerierung komplett neu committet, damit Pages ohne
Build-Schritt auskommt — jede Regenerierung legt dieses Volumen erneut in der Git-Historie ab.
Bekannter Trade-off; Alternativen für später: Build in CI statt Commit, Auslieferung über
Release-Assets, oder kompaktere Array- statt Objekt-Scherben.

Lokale Ansicht:
```
python3 werkzeuge/serve.py 8765   # → http://localhost:8765/site/
```
`serve.py` statt `python3 -m http.server`, weil PMTiles Range-Requests braucht (siehe oben).

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
| `zechen.geojson` | Zechen aus `kuratierung/zechen.csv` mit `status_1936`, `aktiv_1936`, Artikel-/Listenjahren, `jahre_widerspruch`, `plan_1935` |
| `faksimile.json` | Seite (`I-333`) → Bildnummer im DigiBib-Viewer, aus `kuratierung/faksimile_seiten.csv` (erzeugt von `werkzeuge/faksimile_mets.py` aus der METS-Datei des Digitalisats; II-170/171 fehlen im Digitalisat) |
| `kennzahlen.json` | Einträge je Teil, Anteile je Präzisionsstufe, Zahl offener Zeilen, Build-Datum |
| `themen/<id>.json` | Thema-Definitionen (siehe Themenformat unten) |

### URL-Parameter (`karte.html?…`)

| Parameter | Bedeutung | Standard |
|---|---|---|
| `q` | Suchtext | leer |
| `ebene` | Aktive Teile, kommagetrennt: `I,II,III` | alle |
| `stadtteil` | Filter auf einen heutigen Stadtteil | keiner |
| `praez` | Aktive Präzisionsstufen, kommagetrennt: `haus,strasse,stadtplan` | alle |
| `beruf` | Berufsfilter | keiner |
| `thema` | Aktives Thema (`site/daten/themen/<id>.json`) | keins |
| `id` | Adress-ID (öffnet die Hausansicht) oder Eintrags-ID (öffnet die Hausansicht und hebt den Eintrag hervor) | keine |
| `karte` | Grundkartenstil: `positron` oder `liberty` | `positron` |
| `plan` | Stadtplan-1935-Ebene ein-/ausblenden: `0` oder `1` — nur nach Freigabe wirksam (siehe unten) | `0` |
| `zechen` | Zechen-Ebene ein-/ausblenden: `0` oder `1` | `0` |
| `z` | Zoomstufe | 11 |
| `c` | Kartenmitte `lon,lat` | Essen gesamt |

Fehlende Parameter fallen auf den Standardwert zurück. Änderungen an Filtern/Ansicht schreiben
`history.replaceState`; Navigationsschritte (Suche, Haus öffnen) `pushState`. Die Grundkartenwahl
steht zusätzlich in `localStorage`. `PLAN_FREIGEGEBEN` (`site/js/konfig.js`) sperrt die
Stadtplan-1935-Ebene, bis die Stadt Essen bzw. der Historische Verein die Nutzung freigibt.

### Themenformat (`site/daten/themen/<id>.json`)

Felder: `titel`, `text`, `grundlage` (Quelle, Prüfdatum), `filter` (Merkmale, Ebenen), `farbe`
(eine Farbe | Kategorien | Skala auf Merkmalswert), `zusatz` (z. B. `zechen: true`), `legende`,
`darstellung` (`punkte`; `strassen` ist für Teilprojekt 4 reserviert), `freigegeben` (nur dann
erscheint die Kachel auf der Startseite). Merkmale stammen aus `kuratierung/merkmale/<name>.csv`
(Spalten `feld`, `art`, `muster`, `merkmal`, `beleg`, `bearbeiter`, `datum`) und werden in Stufe 06 an
jeden Eintrag angehängt und je Adresse gezählt (`m_<merkmal>` in `adressen.pmtiles`). Aktiv über
`thema=<id>` in der URL, kombinierbar mit Suche und Filtern.

## Dokumentation

Spezifikation: Obsidian-Vault `~/Projekte/obsidian-chris`, Ordner
`10-Projekte/adressbuch-essen-1936-v2/` (`Spec-1-Datenpipeline.md`) — verbindlich.
Plan und Protokolle: `docs/superpowers/`.
