# Manuelle Stichprobe der Geokodierung

Datei: `docs/stichprobe_2026.csv` (200 × haus, 100 × strasse, Zufall mit Seed 2026).
Erzeugt mit `python3 werkzeuge/stichprobe.py 2026` aus `build/04_geokodiert.csv` — derselbe Lauf
ergibt dieselbe Stichprobe. Nach einem Neulauf der Pipeline muss sie neu gezogen und neu geprüft werden.
Prüfung je Zeile: `display_name` und Koordinate gegen OSM und gegen den Stadtplan 1935.
`urteil` ∈ {richtig, falsche_strasse, falsche_nummer, falscher_stadtteil, unklar}; `bemerkung` frei.

## Prüfwerkzeug

    python3 werkzeuge/stichprobe_hinweise.py 2026   # einmal je Stichprobe → build/stichprobe_hinweise.json
    python3 werkzeuge/serve.py                       # → http://localhost:8765/werkzeuge/pruefung.html

Die Seite blättert durch die Stichprobe, zeigt OSM heute und Stadtplan 1935 nebeneinander an der
Koordinate, dazu Herkunft der Auflösung, Dickhoff-Namensstadien der Straße (1936 gültiges Stadium
hervorgehoben, Name des Stadtplans 1935 markiert, wenn er abweicht) und ob die Hausnummer im Nominatim-Treffer vorkommt. Tasten 1–5 setzen das Urteil,
←/→ blättern, Enter springt zur nächsten offenen Zeile. Jede Änderung wird sofort in die CSV
zurückgeschrieben (POST an den Server; nur `urteil` und `bemerkung` ändern sich, alle anderen
Spalten bleiben erhalten). Andere Stichprobe: `pruefung.html?seed=<seed>`.

Was geprüft wird: Stufe `haus` → Straße, Hausnummer, Stadtteil; Stufe `strasse` → nur Straße und
Stadtteil (die Hausnummer ist dort nicht verortet und zählt nicht). Für Straße und Stadtteil ist der
Stadtplan 1935 die Referenz; für die Hausnummer gibt es keine allgemeine Quelle von 1936 — geprüft
wird die Plausibilität (Nummer existiert heute, passt zur Straßenlänge, keine erkennbare
Umnummerierung). Was nicht entscheidbar ist, bekommt `unklar` mit Begründung.

Abnahmekriterium (Spec §6): haus → 0 falsche Straßen, ≤ 2 falsche Nummern; strasse → 0 falscher Stadtteil.
Jede Abweichung wird als Test (tests/), Regel (pipeline/lib/) oder Zeile in kuratierung/ nachgetragen.

## Ergebnis Seed 2026 (Prüfung 2026-09-15)

| Stufe | richtig | unklar | falsch |
|---|---:|---:|---:|
| haus (200) | 193 | 7 | 0 |
| strasse (100) | 89 | 11 | 0 |

Abnahmekriterium formal erfüllt (0 falsche Straßen, 0 falsche Nummern, 0 falscher Stadtteil).
Hausnummern: bei zwei Zeilen über Eckzahlen des Stadtplans 1935 belegt, sonst Plausibilität.

Befunde aus den `unklar`-Fällen:

- **Umbenennungen 1935-11-14 / 1936-01-15.** Sieben Straßen-Fälle (Waterloostr., Krayer Str.,
  Huttropstr., Sulterkamp, Am Parkfriedhof, Alfredstr. Leithe, Löhstr. Kupferdreh) zeigen im
  Stadtplan 1935 den Altnamen; das Adreßbuch führt bereits den Neunamen (bzw. bei Alfredstr. noch
  den Altnamen). Die Auflösung ist jeweils korrekt; das Werkzeug markiert seit b047407+1 den
  Namen des Plans 1935.
- **Ritterstr. [Ostviertel] → Rauterstraße (101 Zeilen, `zeitlich_abweichend`).** Laut Dickhoff hieß
  die Rauterstraße nur 1868–1904 Ritterstraße; ein 1936 hundertfach belegter Name kann das nicht
  sein. Wahrscheinlich eine heute verschwundene Straße, die Dickhoff nicht führt → Kuratierung.
  Gleiches Muster bei weiteren Auflösungen mit `zeitlich_abweichend=ja` (2.162 Zeilen, 115
  Kombinationen, u. a. Provinzialstr., Altenhofstr., Mauerstr.). Vorschlag: solche Auflösungen
  nicht mehr automatisch akzeptieren, sondern in die Vorschlagsliste geben (Spec-Änderung).
- **Verlängerte Straßen** (Stubertal Verl. 1972, Förderstr. Verl. 1930, Königsberger Str.,
  Schmiedestraße): Hausnummer kann auf dem späteren Abschnitt liegen; ohne Eckzahlen nicht
  entscheidbar. Bleibt `unklar`.
