# Datenquelle und Lizenz der Transkription (Beleg, Stand 2026-09-29)

**Ergebnis:** `data/essen1936.csv` ist byteidentisch mit `essen1936.csv` aus dem Datensatz
„Historische Adressbücher aus dem Rheinland und Ruhrgebiet“ des Vereins für Computergenealogie e. V.,
bereitgestellt für Coding da Vinci Nieder.Rhein.Land 2021. Der Datensatz steht laut Datensatzseite unter
**CC BY-SA 4.0**. Hinweis von Christos (2026-09-29): die Datei stammt von genau dort.

## Belege

| Was | Wert |
|---|---|
| Datensatzseite (archiviert 2021-09-06) | https://web.archive.org/web/20210906074729/https://codingdavinci.de/daten/historische-adressbuecher-aus-dem-rheinland-und-ruhrgebiet |
| Lizenzangabe dort (wörtlich) | „CC BY-SA 4.0 Verein für Computergenealogie“ (mehrfach: Datenset, Mediendateien, Metadaten) |
| Beschreibung dort | „Transkriptionen von insgesamt 25 historischen Adressbüchern aus dem 19. und 20. Jahrhundert (1856-1957) … erfasst wurden Vor- und Nachnamen, Berufe und Straßenadressen für Haushaltsvorstände und Hauseigentümer sowie Firmennamen“; 25 Mediendateien, 73,10 MB, 833 692 Objekte, CSV |
| Datenzugang (Nextcloud-Freigabe, 2026-09-29 noch erreichbar) | https://download.codingdavinci.de/s/c8zc6Bn4dZMzyFS |
| Datei in der Freigabe | `essen1936.csv`, 22 348 363 Bytes, Last-Modified 2021-08-06 15:44:01 GMT |
| MD5 Freigabe = MD5 `data/essen1936.csv` | `c43e17a2300ba4939dda7c0bf1f94299` |
| Metadatenzeile (aus `_metadaten_adressbuecher.csv`, Kopie in `docs/cdv_metadaten_adressbuecher.csv`) | `essen1936.csv;242604;https://adressbuecher.genealogy.net/addressbook/54747f7a1e6272f5d1ec771c;http://wiki-de.genealogy.net/Essen/Adressbuch_1936;http://wiki-de.genealogy.net/w/index.php?title=Datei:Essen-AB-1936.djvu;;Essen;Essener Adreßbuch 1936: unter Benutzung amtl. Quellen ;Essen;August Scherl Deutsche Adressbuch-Gesellschaft m.b.H.;1936` |
| Event-Seite (archiviert 2022-02-19) | https://web.archive.org/web/20220219011312/https://codingdavinci.de/de/events/niederrheinland-2021 — „Kulturinstitutionen … stellen … Daten und Inhalte unter einer offenen Lizenz zur Verfügung“ |

Die 25 Dateien der Freigabe: remscheidABNRW1935, landkreis_dortmund_1900, kreisDuerenKöln1954, grevenbroichKreis1912,
lünen_1907, mettmannKreisNrw1922, westerholtHerten1939, grevenbroichKreis1906, unna1911_12, **essen1936**, mettmannNRW1939,
kempenKrefeldAB1953, dueren1932, dinslaken1935, bonn1856-57, aachen1929, aachen1887, bonn1907, hamm1895,
Wattenscheid-AB-1925, Schalke_1898, Viersen-AB-1950, Hattingen_Kreis_1908, Camen_1895, Camen_1902 (+ `_metadaten_adressbuecher.csv`).

## Was daraus folgt

- **Namensnennung** (BY): „Transkription: Verein für Computergenealogie e. V., Datensatz ‚Historische Adressbücher aus dem
  Rheinland und Ruhrgebiet‘ (Coding da Vinci Nieder.Rhein.Land 2021), CC BY-SA 4.0“ — auf der Startseite, im Impressum,
  im Kapitel Datenbasis und in der README; Link auf die Lizenz https://creativecommons.org/licenses/by-sa/4.0/.
- **Weitergabe unter gleichen Bedingungen** (SA): alle Ableitungen, die die Transkription enthalten (unsere
  `build/eintraege.csv`, das Datenpaket `site/daten/`, CSV-Exporte der Karte, ein späterer Zenodo-Datensatz), sind
  unter **CC BY-SA 4.0** zu veröffentlichen. Eigener Code (Pipeline, Site) ist davon nicht betroffen und kann eine
  eigene Lizenz tragen; die Kuratierungstabellen (`kuratierung/*.csv`) sind eigene Werke, die Transkriptionsfelder
  darin (Schreibweisen) sind aber aus dem Datensatz übernommen — im Zweifel ebenfalls BY-SA.
- **Nicht abgedeckt:** die offline erfassten Namen H–J in adressbuecher.genealogy.net (nicht Teil des
  CdV-Datensatzes; Export und Lizenz separat bei CompGen erbitten) und das Digitalisat (Scans; Feld
  „Digitalisat-Lizenz extern“ ist für Essen leer, anders als „cc:pd“ bei den älteren Bänden). Für Faksimile-Links
  spielt das keine Rolle, für eine Übernahme von Scans schon.
- **Offen bleibt** die Mail an CompGen — jetzt nicht mehr wegen der Lizenz, sondern (a) als Hinweis auf das Projekt
  und Nachfrage, ob die Namensnennung so gewünscht ist, (b) wegen des H–J-Exports.
