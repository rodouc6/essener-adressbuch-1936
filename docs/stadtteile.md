# Stadtteilgrenzen (OSM)

## Quelle und Lizenz

Die Stadtteilgrenzen stammen aus OpenStreetMap (Lizenz ODbL, © OpenStreetMap-Mitwirkende), abgefragt über
die Overpass-API (`werkzeuge/osm_stadtteile_laden.py`). Erfasst werden alle Relationen mit
`boundary=administrative` und `admin_level=10` innerhalb des Regionalschlüssels `051130000000` (Stadt
Essen). Ergebnis: `build/osm_stadtteile.json` mit den Feldern `stand` (Abrufdatum), `quelle` und
`stadtteile` (OSM-Name → Liste von Ringen).

Aktueller Abruf: **50 Stadtteile**, Stand siehe `build/osm_stadtteile.json` → `stand` (Abrufdatum des
letzten Laufs von `osm_stadtteile_laden.py`).

## Verfahren

- **Ringe**: Jede Relation liefert mehrere `way`-Mitglieder mit Rolle `outer`. `ringe_aus_relation`
  (`pipeline/lib/stadtteile.py`) verkettet diese Wege über gemeinsame Endpunkte — unabhängig davon, in
  welcher Richtung ein Weg in OSM gespeichert ist — bis jeder Ring geschlossen ist (erster Punkt = letzter
  Punkt). `inner`-Ringe (Enklaven) werden bewusst **nicht** ausgeschnitten; in Essen hat kein Stadtteil
  eine Enklave, daher ist das ohne Auswirkung.
- **Punkt-in-Polygon**: `punkt_in_ring` verwendet die Strahlmethode (even-odd-Regel) auf den
  Ringkoordinaten. Punkte exakt auf einer Kante werden nicht sicher erkannt — für Adressen (die nie exakt
  auf einer Grenzlinie liegen) unerheblich.
- **Bbox-Vorfilter**: `Stadtteile.zuordnen` prüft vor dem eigentlichen Punkt-in-Polygon-Test zuerst die
  Bounding-Box jedes Stadtteils und überspringt Stadtteile, deren Bbox den Punkt nicht enthält — das
  beschleunigt die Zuordnung, ohne das Ergebnis zu verändern.

## Namensabgleich

`kuratierung/stadtteile_osm.csv` (Spalten `osm_name,name,hinweis`) bildet den heutigen OSM-Namen auf den im
Projekt verwendeten Namen ab. Ein leerer `name` bedeutet: Der Stadtteil gehörte 1936 nicht zu Essen und wird
nicht zugeordnet (`Stadtteile.zuordnen` liefert dann `None`).

| osm_name | name | Hinweis |
|---|---|---|
| Margarethenhöhe | Margaretenhöhe | Schreibung wie essener-strassen/Dickhoff |
| Kettwig | *(leer)* | erst 1975 nach Essen eingemeindet — 1936 keine Essener Adressen |
| Burgaltendorf | *(leer)* | erst 1970 eingemeindet |

Alle übrigen 47 OSM-Namen werden unverändert übernommen.

## Grenze der Verwendung

Die Grenzen sind die **heutigen** OSM-Stadtteilgrenzen — nicht die von 1936. Essens Stadtteile waren 1936
anders geschnitten (z. B. gab es das „Sternviertel" als eigene Bezeichnung, und die Eingemeindungen von 1929
hatten das Stadtgebiet gerade erst auf seine heutige Ausdehnung gebracht). Für Adressen aus Gebieten, die
1936 nicht zu Essen gehörten (Kettwig, Burgaltendorf), liefert die Zuordnung bewusst `None` statt eines
falschen heutigen Stadtteils.

## Kennzeichnung

Jede Stelle, die diese Grenzen anzeigt oder verwendet (Karte, Perspektiven-Seite, Export), muss kenntlich
machen, dass es sich um heutige OSM-Grenzen handelt (ODbL, © OpenStreetMap-Mitwirkende), nicht um die
Stadtteilgrenzen von 1936. `Stadtteile.geojson()` trägt `quelle` und `stand` in die Feature-Properties ein,
damit diese Angabe mit den Daten mitgeführt wird.

## Abruf wiederholen

```bash
python3 werkzeuge/osm_stadtteile_laden.py
```

Optional `--url` für einen anderen Overpass-Endpunkt und `--wurzel` für ein anderes Projektverzeichnis. Bei
HTTP 429 (Rate-Limit) oder 504 (Timeout) des Overpass-Servers hilft ein erneuter Versuch nach ca. 90
Sekunden Wartezeit. Das Skript bricht ohne Schreiben ab, wenn weniger als 40 Stadtteile zurückkommen (Hinweis
auf eine unvollständige Overpass-Antwort). `build/osm_stadtteile.json` ist git-ignoriert und wird bei jedem
Lauf neu erzeugt.
