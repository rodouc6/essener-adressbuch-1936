# Sichtung offener Straßen am Stadtplan 1935

Für Buchnamen, die kein Dickhoff-Name trifft (verschwundene Straßen, lückenhafte Namensketten, erloschene
Namen ohne Beleg), entscheidet der georeferenzierte Stadtplan 1935 der Stadt Essen. Das Werkzeug
`werkzeuge/sichtung.html` geht die offenen Straßen nach Zeilenzahl durch und schreibt die Entscheidung
direkt in die Kuratierungstabellen. Regel: `docs/entscheidungen_strassen.md`, Runde 6.

## Vorbereitung

    python3 werkzeuge/sichtung_liste.py        # → build/sichtung_1935.json (braucht Stufe 03, lokales Nominatim)
    python3 werkzeuge/serve.py                 # → http://localhost:8765/werkzeuge/sichtung.html

Die Liste fasst alle offenen oder mehrdeutigen Paare je (Buchname, Vorort) zusammen: Zeilenzahl, Buchteile,
Beispieladressen, Pipeline-Gründe, Dickhoff-Kandidaten mit Namensstadien (1936 gültiges Stadium
hervorgehoben, „im Plan 1935“ markiert) und Sprungkoordinate, dazu ähnliche Dickhoff-Namen als Vorschlag.
Kopfzeile: nur ungesichtete, Mindestzeilen (Vorgabe 20), Namensfilter.

## Prüffrage

*Wo liegt die Straße, die im Adreßbuch steht, auf dem Stadtplan 1935?* Maßstab ist das Buch; Dickhoff
liefert nur Kandidaten. Drei Ausgänge:

1. **Buchname steht am Plan an einer heutigen Straße** (Kandidat oder über die Karte gefunden): beim
   Kandidaten „Buchname steht hier“ → Zeile in `kuratierung/strassen_zuordnung.csv` (Beleg „Stadtplan 1935:
   … liegt an der heutigen …“). Zeigt der Plan ein anderes Namensstadium derselben Straße (Umbenennung
   zwischen Planstand 1935 und Buch 1936, vgl. Stichprobe r5), gilt das ebenfalls — Planname in die Bemerkung.
   Ist die gefundene Straße kein Kandidat, den Namen im Feld „Name filtern“ … nicht nötig: einfach Punkt setzen
   (Ausgang 2) und in der Bemerkung die heutige Straße nennen; die Zuordnung wird dann von Hand nachgetragen.
2. **Straße ist am Plan zu finden, existiert heute aber nicht** (oder ihr heutiger Name ist unbekannt):
   Klick auf die Straßenmitte in einer der Karten, „Name im Plan 1935“ prüfen (vorbelegt mit dem Buchnamen),
   Stadtteil prüfen (Vorschlag aus OSM), „Punkt speichern“ → Zeile `befund=punkt` in
   `kuratierung/strassen_1935.csv`. Die Pipeline verortet alle Zeilen dieses Buchnamens auf Straßenebene
   (`stufe=strasse`, `grund=stadtplan_1935`, `herkunft=stadtplan_1935`).
3. **Nicht auffindbar** (Plan unleserlich, Name nirgends): „Nicht gefunden“ mit Bemerkung → Zeile
   `befund=nicht_gefunden`; die Zeilen bleiben offen, die Gruppe gilt als gesichtet.

Hausnummern werden hier nicht geprüft — es geht um die Straße. Ist eine Straße heute nur zum Teil
vorhanden oder neu gezählt, gehört das als Bemerkung dazu; die Hausebene wird dann in
`strassen_zuordnung.csv` mit `nummer_unsicher=ja` abgeschaltet.

## Danach

    python3 pipeline/03_strasse_aufloesen.py && python3 pipeline/04_geokodieren.py && python3 pipeline/05_bericht.py
    python3 werkzeuge/sichtung_liste.py        # Sichtungsstand neu einlesen

Korrekturen: Zeile in der jeweiligen CSV ändern oder löschen, dann `sichtung_liste.py` neu laufen lassen.
Eine Zuordnung (`strassen_zuordnung.csv`) geht einem Punkt (`strassen_1935.csv`) immer vor; das Werkzeug
entfernt beim Zuordnen die Punktzeile desselben Schlüssels.
