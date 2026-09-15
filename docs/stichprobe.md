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
hervorgehoben) und ob die Hausnummer im Nominatim-Treffer vorkommt. Tasten 1–5 setzen das Urteil,
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
