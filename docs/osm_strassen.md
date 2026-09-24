# Straßenlinien aus OpenStreetMap

Quelle: [Overpass API](https://overpass-api.de/api/interpreter) (Fallback: `https://overpass.kumi.systems/api/interpreter`),
Abfrage über die OSM-Relation **62713** (Stadt Essen). Werkzeug: `werkzeuge/osm_strassen_laden.py`
→ `build/osm_strassen.json` (nicht versioniert, `build/` ist ignoriert).

## Filter

Alle Wege mit `highway`-Tag und Namen innerhalb der Stadtgrenze, außer Fuß-/Rad-/sonstigen
Nebenwegen (`footway`, `path`, `steps`, `cycleway`, `track`, `bridleway`, `corridor`,
`platform`, `construction`, `proposed`). Je Straßenname werden alle Segmente gesammelt
(eine Straße besteht in OSM aus vielen kurzen Ways).

Mit `--halbieren` wird die einteilige Area-Abfrage (nur bei Overpass-Timeout nötig) durch zwei
Bounding-Box-Abfragen (Nord/Süd) ersetzt und das Ergebnis zusammengeführt. Die beiden Bboxen
(51.30–51.58 / 6.85–7.20) reichen dabei über die Essener Stadtgrenze hinaus; damit trotzdem nur
Wege **innerhalb der Stadtgrenze** erfasst werden (und bei Namensgleichheit keine fremden Segmente
aus Nachbarstädten mit derselben Straße verschmolzen werden), filtert jede Bbox-Abfrage zusätzlich
auf `area.essen`: `way["highway"]["name"](area.essen)(bbox)`. Die Aussage „innerhalb der
Stadtgrenze“ gilt damit für beide Abfragewege gleichermaßen.

## Stand des Abrufs

Siehe `stand` in `build/osm_strassen.json` (ISO-Datum des letzten `osm_strassen_laden.py`-Laufs).
Letzter Abruf: **2026-09-24**, 3.381 benannte Straßen mit 16.610 Liniensegmenten
(Overpass-Endpunkt `overpass.kumi.systems`, Fallback nach Timeout bei `overpass-api.de`).

## Grenzen — Precision first

- Die Linien zeigen die **heutige Führung** der Straße, nicht die von 1936. Straßenverlauf,
  Länge und Randbebauung können sich seither verändert haben (Kriegszerstörung, Neubau,
  Umgehungsstraßen). Die Legende der Straßenschicht in der Karte weist deshalb ausdrücklich
  auf „Straßenlinien: heutige Führung (OSM)“ hin.
- Straßen, die zwischen 1936 und heute verschwunden sind (umbenannt in einen anderen als den
  konkordierten heutigen Namen, überbaut, eingemeindet in eine andere Straße), haben keine
  Linie in OSM unter dem heutigen Namen und bleiben in der Straßenschicht ohne Geometrie —
  sie werden gezählt (`kennzahlen.json` → `strassen_mit_linie` vs. Gesamtzahl heutiger
  Straßen aus der Konkordanz), aber nie ersatzweise mit einer erfundenen oder falsch
  zugeordneten Linie dargestellt.
- **Annahme, keine Garantie:** Namensgleichheit heutiger Straßen im Essener Stadtgebiet gilt
  als eindeutig, weil mehrfach vorkommende Straßennamen aus den 1937 eingemeindeten
  Nachbargemeinden bei der Eingemeindung umbenannt wurden — die Zuordnung `strassen_features()`
  geht also davon aus, dass ein heutiger Straßenname in Essen genau eine OSM-Linie (bzw.
  Liniengruppe) ergibt. Diese Verwaltungsregel wird hier nicht gegen die tatsächlichen
  OSM-Daten geprüft: OSM-Datenfehler (z. B. eine versehentlich doppelt vergebene Bezeichnung,
  ein falsch benannter Weg) bleiben möglich. Träfe das zu, würde ein Namensdoppel in
  `linien_aus()` zu einer gemeinsamen Liniengruppe unter demselben Namen zusammengefasst und
  könnte so fälschlich zwei unterschiedlichen Straßen dieselbe Linie zuordnen.
- Lizenz: [Open Database License (ODbL)](https://www.openstreetmap.org/copyright),
  © OpenStreetMap-Mitwirkende. Die Attribution der Grundkarte zeigt das bereits; die
  Legende der Straßenschicht nennt zusätzlich die Quelle.

## Kennzahlen

Stand des Exports 2026-09-24 (`site/daten/kennzahlen.json` → `strassen_mit_linie`,
`site/daten/ebenen/strassen.json`):

- 2.040 Straßen-Einheiten insgesamt (Straßen mit Adressen im Buch), davon 2.016 heutige
  Straßen (fünfstellige `schl_nr`) und 24 nur 1936 belegte Einheiten (Präfix `1936:`,
  keine OSM-Linie möglich).
- **1.999 der 2.016 heutigen Straßen (99,2 %) haben eine OSM-Linie** (`strassen_mit_linie`
  in `kennzahlen.json`); 17 heutige Straßen bleiben ohne Linie (z. B. weil sie in OSM anders
  geschrieben sind als in der Straßenkonkordanz, oder sehr kurze/private Erschließungswege
  ohne `highway`-Namenstag sind) — sie werden in der Karte gezählt, aber nicht gezeichnet.
- PMTiles `site/daten/adressen.pmtiles`: **5,99 MB** (5.987.988 Byte), Zoom 9–15, drei
  Schichten `adressen`, `strassen`, `hex` (per Header/`vector_layers`-Metadaten geprüft).
