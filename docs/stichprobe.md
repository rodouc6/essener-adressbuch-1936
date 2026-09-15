# Manuelle Stichprobe der Geokodierung

**Aktuell zu prüfen:** `docs/stichprobe_2027.csv` (Volllauf nach Runde 3, s. `entscheidungen_strassen.md`);
Prüfseite mit `pruefung.html?seed=2027`. Seed 2026 ist abgeschlossen und bleibt als Beleg liegen.

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

## Ergebnis Seed 2026 (Prüfung 2026-09-15, Nachprüfung der unklar-Fälle)

| Stufe | richtig | unklar | falsch |
|---|---:|---:|---:|
| haus (200) | 194 | 6 | 0 |
| strasse (100) | 95 | 5 | 0 |

Abnahmekriterium erfüllt (0 falsche Straßen, 0 falsche Nummern, 0 falscher Stadtteil).
Hausnummern: bei zwei Zeilen über Eckzahlen des Stadtplans 1935 belegt, sonst Plausibilität
(Block, Straßenseite, Bebauung 1935 vorhanden). Erstdurchgang: 193/7 und 89/11; sieben Straßen-
und ein weiterer Fall wurden nach Recherche auf richtig gesetzt (Begründung in `bemerkung`).

Befunde:

- **Umbenennungen 1935-11-14 / 1936-01-15.** Der Stadtplan 1935 zeigt Altnamen (Bruchstraße,
  Gelsenkirchener Straße, Herwarthstraße, Schulstraße, Luegstraße, Talstraße), das Adreßbuch führt
  meist schon die neuen Namen. Das Prüfwerkzeug markiert seit eb80c94 den Namen des Plans 1935.
- **Ritterstr. [Ostviertel] → Rauterstraße (105 Zeilen, `zeitlich_abweichend`) ist richtig.**
  Dickhoff (S. 269) kettet für die Rauterstraße: 1868 Ritterstraße, 1904 Phönixstraße, 1915
  Steingröverstraße, 1935 Vorrathstraße (tlw.), 1937 Rauterstraße. Der Stadtplan 1935 beschriftet
  aber neben der Steingröverstraße eine kurze Diagonale als „Ritterstr.“, und das Adreßbuch 1936
  kennt dort 19 Häuser (Nr. 2–31). Die Kette fasst zwei Stränge zusammen: Phönix-/Steingröver-
  straße gehören zum Zug entlang der Bahn (so auch Dickhoffs Vorrathstraße-Eintrag), die Diagonale
  hieß bis 1937 Ritterstraße. Das aus der Kette abgeleitete `gueltig_bis` 1904 ist ein Artefakt.
  Lehre: `zeitlich_abweichend=ja` ist kein Fehlerindikator; Dickhoffs Namensketten sind bei
  zusammengelegten Straßen nicht linear, und Dickhoff führt nur heutige Straßen. Statt eines
  Automatismus: die 115 Kombinationen (2.162 Zeilen) nach Zeilenzahl sortiert am Stadtplan 1935
  prüfen und Ergebnis in `kuratierung/strassen_zuordnung.csv` festhalten.
- **Verlängerte Straßen** (Stubertal Verl. 1972, Förderstr. Verl. 1930, Königsberger Str.,
  Schmiedestraße): Hausnummer kann auf dem späteren Abschnitt liegen; ohne Eckzahlen nicht
  entscheidbar. Bleibt `unklar`.
