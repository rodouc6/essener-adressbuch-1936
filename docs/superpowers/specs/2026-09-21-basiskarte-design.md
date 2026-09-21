# Teilprojekt 2: Basiskarte — Entwurf

Stand: 2026-09-21. Ergebnis des Brainstormings mit dem Projektleiter (Mockups unter
`.superpowers/brainstorm/`, nicht versioniert). Anforderungen: Vault `Anforderungen.md`
(E1, E2, E5). Grundsatz: Precision first, nichts Unsicheres als sicher zeigen.

## 1. Ziel und Abgrenzung

Eine statische Webkarte des Adressbuchs Essen 1936 (Teile I–III), suchzentriert, vom
ersten Tag an für Laptop und Mobilgerät. Sie zeigt die Ergebnisse der Datenpipeline
(Stufen 01–05) mit ihrer Präzisionsstufe und ist so gebaut, dass Teilprojekt 3
(Eigentümer) und 4 (Berufe) nur noch Inhalte liefern, keine neuen Kartenmechaniken.

Nicht Teil dieses Teilprojekts: Berufsgruppen, Schicht-Score, Eigentümer-Cluster,
Straßenaggregation der Schichtung (nur als Darstellungsart im Themenformat
vorgesehen), Rechteanfrage Stadtplan 1935, Lizenz der Quelle, Veröffentlichung des
Repos.

## 2. Entscheidungen aus dem Brainstorming

| Frage | Entscheidung |
|---|---|
| Straßengenaue Einträge auf der Karte | Eigenes Symbol am Straßenpunkt (gestrichelter Rand), nie entlang der Straße verteilt |
| Suchtreffer | Liste und Karte gekoppelt; Laptop Sidebar links, Handy Bottom-Sheet in drei Stufen; dieselbe Komponente |
| Startseite | Banner Stadtplan 1935, Suchleiste mit Sofortvorschlägen, Zahlenzeile, vier Kacheln, Hinweiszeile Lücke H–J; kein eigener Listenmodus |
| Angeklicktes Haus | Popup mit Basisinformationen, ausführliche Hausansicht in der Sidebar; Klick auf Namen im Popup hebt den Eintrag in der Sidebar hervor |
| Quellenangaben (Seite, Faksimile) | nur in der Sidebar |
| Punktfarbe bei mehreren Ebenen | ein Punkt je Adresse; Ebenenfarbe nur bei genau einer aktiven Ebene, sonst neutral |
| Filter zum Start | Ebenen-Pills, Stadtteil, Präzision, Beruf/Firmenzweig als Freitext; keine v1-Gewerbekategorien |
| Themen | Merkmale je Eintrag aus kuratierten Tabellen plus Themen-Voreinstellungen als JSON; erstes Thema „Akademiker“ nach Abnahme der Titelliste |
| Grundkarte | Positron (Standard), Liberty („detailliert“) umschaltbar; Stadtplan 1935 als Overlay mit Deckkraft, Schalter erst nach Rechteklärung sichtbar |
| Zustand | vollständig in der URL (reproduzierbare Links) |
| Export | Treffer als CSV aus der Sidebar |

## 3. Seitenaufbau

Ordner `site/`, ausgeliefert über GitHub Pages, lokal über `werkzeuge/serve.py`. Kein
Framework, kein Frontend-Build: ES-Module, CSS mit Media-Queries. MapLibre GL JS und
pmtiles.js liegen unter `site/vendor/` (keine CDN-Abhängigkeit).

Seiten:

- `index.html` Startseite: Banner (Ausschnitt Stadtplan 1935, zunächst vom
  ArcGIS-Dienst, später Digitalisat des Projektleiters), Suchleiste mit Vorschlägen,
  Zahlenzeile aus `kennzahlen.json` (Einwohner, Häuser, Firmen, Anteil verortet),
  Kacheln „Karte öffnen“, „Stadtteil wählen“, „Zechen und Krupp“, vierte Kachel
  reserviert für ein freigegebenes Thema; Hinweiszeile zur Lücke H–J; Fußzeile.
- `karte.html` Anwendung, siehe Abschnitte 5–7.
- `ueber.html` Projekt, Quelle, Methode, Präzisionsstufen, Lücken (E5), Kennzahlen.
- `impressum.html` nach dem Muster des Wuppertal-Projekts (Kacheln OpenFreeMap,
  Stadtplan geo.essen.de, sonst nichts Externes).

Layout `karte.html`: ab 900 px Breite Sidebar links (360 px), Karte rechts; darunter
Karte im Vollbild und die Sidebar als Bottom-Sheet mit drei Stufen (Griff: Suchfeld
und Pills; halb: Liste; voll: Detail). Bedienelemente mindestens 44 px, kein
horizontales Scrollen.

Sidebar-Zustände: (1) Suche und Filter, (2) Trefferliste, (3) Hausansicht oder
Eintrag, (4) Thema aktiv (Kopfblock über 1–3). Zurück über den Browser-Verlauf, weil
jeder Zustand eine URL ist.

## 4. URL-Zustand

`karte.html?q=&ebene=I,II,III&stadtteil=&praez=haus,strasse,stadtplan&beruf=&thema=&id=&karte=positron|liberty&plan=0..1&zechen=0|1&z=&c=lon,lat`

- Fehlende Parameter haben Standardwerte (alle Ebenen, alle Präzisionen, Positron,
  Plan aus, Zechen aus, Essen gesamt).
- `id` ist eine Adress-ID (öffnet die Hausansicht) oder eine Eintrags-ID (öffnet die
  Hausansicht und hebt den Eintrag hervor).
- Änderungen schreiben `history.replaceState`; Navigationsschritte (Suche, Haus
  öffnen) `pushState`.
- Grundkartenwahl zusätzlich in `localStorage`.

## 5. Datenpaket: Stufe 06

`pipeline/06_karte_export.py` liest `build/04_geokodiert.csv` und
`build/eintraege.csv`, schreibt nach `site/daten/`. Deterministisch, mit Tests wie
die Stufen 01–05. Ergebnis wird committet (Pages baut nicht).

### 5.1 Adresspunkte `adressen.pmtiles`

Ein Punkt je verorteter Adresse (Stufe `haus` oder `strasse`; offene Zeilen bleiben
draußen und werden in `kennzahlen.json` beziffert). Adress-ID: stabiler Hash aus dem
`ADRESSSCHLUESSEL` der Pipeline. Eigenschaften:

| Feld | Inhalt |
|---|---|
| `id` | Adress-ID |
| `n_I`, `n_II`, `n_III` | Zahl der Einträge je Teil |
| `stufe` | `haus`, `strasse`, `stadtplan` (herkunft `stadtplan_1935`) |
| `stadtteil` | heutiger Stadtteil (Pipeline) |
| `strasse_heute`, `hausnr` | heutige Adresse |
| `historisch` | Buchschreibung (Straße, Hausnummer, Vorort) |
| `nummer_unsicher` | ja/nein |
| `m_<merkmal>` | Zähler je Merkmal (Abschnitt 8) |

Erzeugung mit tippecanoe: bis Zoom 10 mit `--drop-densest-as-needed`, ab Zoom 13
vollständig, maximaler Zoom 15 (darüber Overzoom). Verpackt als PMTiles. Zielgröße
unter 10 MB.

### 5.2 Einträge in Scherben `haus/<xx>.json`

Alle Einträge nach Adress-ID in 256 Dateien gehasht (erste zwei Hex-Zeichen). Je Datei
ein Objekt Adress-ID → Liste der Einträge, sortiert nach Etage (Erdg., I, II, III, IV,
V; Einträge ohne Etage danach, innerhalb alphabetisch nach Name). Felder je Eintrag:
Eintrags-ID, Teil, Seite, Nachname, Vorname, Beruf, Etage, Familienstand, Bezugsperson
(Vorname, Beruf), Firmenname, Eigentümer, Verwalter, abweichender Wohnort,
Präzisionsflags (nummer_unsicher, zeitlich_abweichend, mehrdeutig mit Grund),
Merkmale.

Hinweis: Nur etwa 3,6 % der Einträge tragen eine Etage; die Sortierung greift dort,
wo sie belegt ist, und ist im Detail als „Etage laut Buch“ ausgewiesen.

### 5.3 Suchindex `suche/`

Schlüsselfaltung: Kleinschreibung, ä→ae, ö→oe, ü→ue, ß→ss, Satzzeichen entfernt.

- `namen/<ab>.json`: Personen (Teil I und Namen aus Teil II/III) nach den ersten zwei
  Schlüsselzeichen des Nachnamens; je Zeile Nachname, Vorname, Beruf, Adresse
  (Anzeige), Eintrags-ID, Adress-ID.
- `firmen/<ab>.json`: Firmen (Teil III) nach Firmenname, gleiche Struktur.
- `strassen.json`: heutige und 1936er Straßennamen mit Vorort, Zeilenzahl, Liste der
  Adress-IDs.
- `berufe.json`: Schreibungen mit Häufigkeit (für Vorschläge);
  `berufe/<ab>.json`: Schreibung → Adress-IDs mit Zähler.
- `stadtteile.json`: Name, Mittelpunkt, Zeilenzahl.

### 5.4 Weitere Dateien

`zechen.geojson` (aus `kuratierung/zechen.csv`), `kennzahlen.json` (aus
`build/04_statistik.json` und dem Bericht: Einträge je Teil, Anteile je
Präzisionsstufe, Zahl offener Zeilen, Build-Datum), `themen/<id>.json`.

## 6. Suche

Ein Feld, gleiches Verhalten auf beiden Seiten. Ab zwei Zeichen wird die passende
Scherbe geladen; Vorschläge in Gruppen: Personen (5), Straßen (3), Firmen (3), Berufe
(3), jede mit „alle n anzeigen“. Präfixtreffer auf dem gefalteten Schlüssel; Personen
auch als „Nachname Vorname“; Straßen über heutigen und 1936er Namen. Keine
Fuzzy-Suche; Schreibvarianten des Buchs bleiben getrennt sichtbar.

Enter oder Auswahl öffnet `karte.html` mit `q=` und offener Sidebar. Personen- und
Firmenvorschlag → Haus (`id=`), Straßen- und Berufsvorschlag → Treffermenge.

Trefferliste: Kopf mit Trefferzahl und Häuserzahl; Zeilen als Häuser (Adresse, Zähler)
oder Personen (Namenssuche); 50 Zeilen, Nachladen beim Scrollen; ab 500 Treffern eine
Textverteilung nach Stadtteil. Kennzeichen „nur Straße“ und „Stadtplan 1935“ je Zeile.
Karte hebt alle Treffer hervor und zoomt auf ihre Ausdehnung; Liste und Karte sind in
beide Richtungen gekoppelt.

Lücke H–J: Nachname mit H, I oder J ohne Personentreffer → ausdrücklicher Hinweis, dass
die Seiten 186–258 in der Vorlage fehlen; Straßen und Firmen sind nicht betroffen.

Export: „Treffer als CSV“ in der Sidebar; bis 5.000 Einträge vollständig (Scherben
werden nachgeladen), darüber auf Adressebene. UTF-8 mit BOM.

## 7. Karte und Darstellung

Punkte: ein Punkt je Adresse. Radius logarithmisch nach Summe der aktiven Ebenen (4 px
bei 1 bis 10 px ab 100). Farbe: Einwohner Blau, Eigentümer Gold, Gewerbe Rot bei genau
einer aktiven Ebene, sonst neutral Dunkelgrau. Präzision: `haus` gefüllt; `strasse`
und `stadtplan` als gestricheltes SDF-Icon (Symbol-Ebene, `icon-allow-overlap`,
Farbe und Größe per Ausdruck). Unter 6 px Radius ist die Strichelung nicht erkennbar;
Präzision steht deshalb auch in Popup, Liste, Detail und Legende.

Treffermengen: Adress-IDs aus dem Index werden per Feature-State gesetzt
(`promoteId: id`); Treffer in Signalfarbe, übrige auf 25 % Deckkraft. Auswahl mit
Ring. Filter auf Punkteigenschaften (Ebene, Stadtteil, Präzision, Merkmal) als
MapLibre-Filterausdruck.

Zoom: unter 12 nur Punkte ab 5 Einträgen, ohne Strichelung; ab 13 vollständig.

Popup: heutige Adresse, „historische Adresse: …“, Präzisionskennzeichen, Zähler je
Ebene, Namen mit Beruf nach Etage geordnet (mobil drei Namen und „alle im Detail“);
Klick auf einen Namen öffnet bzw. scrollt die Sidebar zum Eintrag und hebt ihn hervor.
Keine Seiten, keine Links im Popup.

Hausansicht (Sidebar): Adresse 1936 und heute, Stadtteil, Präzisionsstufe mit Erklärung
(„Straße bekannt, Hausnummer nicht verortbar“ / „Punkt vom Stadtplan 1935, Straße
verschwunden“), Einträge nach Ebene gruppiert, je Eintrag alle Felder, Seite und
Faksimile-Link.

Legende unten rechts, klappbar. Steuerung rechts oben: Zoom, Standort (mobil),
Grundkarte dezent|detailliert, Stadtplan 1935 mit Deckkraft-Regler (nur sichtbar bei
`plan_freigegeben: true` in `site/konfig.js`), Zechen an/aus. Ebenen-Pills in der
Sidebar bzw. am Kopf des Sheets.

Grundkarte: OpenFreeMap Positron (Standard) und Liberty; Stilwechsel über
`map.setStyle`, danach `ebenenAufsetzen()` für alle eigenen Quellen und Ebenen.
Stadtplan 1935: Raster vom ArcGIS-Export in EPSG:3857 (Regel R6.5).

Zechen: Symbol Schlägel und Eisen mit Name; Popup mit Betriebsjahren und
Wikipedia-Link. `werkzeuge/zechen_wikipedia.py` liest die Wikipedia-Listen einmalig,
Ergebnis wird als geprüfte Tabelle `kuratierung/zechen.csv` (Name, Stadtteil, lat,
lon, betrieb_von, betrieb_bis, quelle, bearbeiter, datum) versioniert; standardmäßig
nur Zechen, die 1936 in Betrieb waren.

## 8. Themen und Merkmale

Merkmale: `pipeline/lib/merkmale.py`, aufgerufen in Stufe 06. Quelle sind Tabellen
`kuratierung/merkmale/<name>.csv` (feld, muster, merkmal, beleg, bearbeiter, datum);
`muster` ist ein exakter Wert oder ein als solches gekennzeichnetes Präfix/Regex.
Stufe 06 hängt jedem Eintrag seine Merkmale an und zählt sie je Adresse
(`m_<merkmal>`). Ohne Tabelle kein Merkmal.

Erstes Thema „Akademiker“: Titelliste (Dr., Prof., Dipl.-Ing., Dr. med., Studienrat …)
auf Namens- und Berufsfeld; die Liste liegt als Tabelle im Repo und geht erst nach
Prüfung durch den Projektleiter live. Bergbau, Schichtung, Genossenschaften folgen mit
TP3/TP4.

Thema: `site/daten/themen/<id>.json` mit `titel`, `text`, `grundlage` (Quelle,
Prüfdatum), `filter` (Merkmale, Ebenen), `farbe` (eine Farbe | Kategorien |
Skala auf Merkmalswert), `zusatz` (z. B. `zechen: true`), `legende`,
`darstellung` (`punkte`; `strassen` reserviert für TP4). Aktiv über `thema=<id>`,
kombinierbar mit Suche und Filtern. Sichtbar: Kopfblock in der Sidebar mit Text,
Legende und „Thema verlassen“; Liste der Themen im Filterbereich; Kachel auf der
Startseite nur für freigegebene Themen (`freigegeben: true`).

## 9. Tests und Qualität

- Stufe 06 mit pytest: Fixtures mit wenigen Zeilen; Scherbenzuordnung, Schlüsselfaltung,
  Etagensortierung, Merkmalsregeln, Zähler je Adresse; Golden-Test, dass ein bekannter
  Eintrag in Kachel-Eigenschaften, Scherbe und Index konsistent liegt. tippecanoe-Lauf
  als Integrationstest (übersprungen, wenn nicht installiert).
- Frontend: reine Funktionen (URL-Zustand, Schlüsselfaltung, Etagensortierung,
  Themenauswertung, CSV-Export) als ES-Module ohne DOM, Tests mit `node --test`.
- Playwright-Rauchtests gegen `serve.py`: Startseite lädt; „Sepeur“ liefert Vorschlag;
  Kartenseite zeigt Punkt; Klick öffnet Hausansicht; Sheet bei 390 px Breite;
  Grundkartenwechsel erhält Ebenen und Auswahl; URL-Zustand wird wiederhergestellt.
- Precision first in der Oberfläche: Präzisionsstufe an jeder Stelle; Über-Seite mit
  Kennzahlen und Lücken; Vermerk „Work in progress, Stand vom <Build-Datum>“.

## 10. Betrieb

GitHub Pages aus `site/` auf `main`. Build lokal: Stufen 01–06, tippecanoe; `site/daten/`
wird committet. Externe Dienste zur Laufzeit: OpenFreeMap (Kacheln, Stile),
geo.essen.de (Stadtplan, nur wenn freigegeben). Keine Analytik, keine Cookies.

## 11. Offene Punkte außerhalb des Teilprojekts

- Rechteanfrage Stadtplan 1935 an Stadt Essen / Historischer Verein.
- Faksimile: erledigt am 2026-09-21 — die METS-Datei der DigiBib liefert je Bild das Etikett der
  gedruckten Seite (`werkzeuge/faksimile_mets.py` → `kuratierung/faksimile_seiten.csv`); Link
  `https://www.digibib.genealogy.net/viewer/image/857439804_1936/<Bild>/`.
- Lizenz der Quelldaten, Kontakt CompGen wegen der Lücke H–J.
- Digitalisat des Stadtplans für das Banner.
