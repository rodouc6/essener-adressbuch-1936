# Manuelle Stichprobe der Geokodierung

Datei: `docs/stichprobe_2026.csv` (200 × haus, 100 × strasse, Zufall mit Seed 2026).
Erzeugt mit `python3 werkzeuge/stichprobe.py 2026` aus `build/04_geokodiert.csv` — derselbe Lauf
ergibt dieselbe Stichprobe. Nach einem Neulauf der Pipeline muss sie neu gezogen und neu geprüft werden.
Prüfung je Zeile: `display_name` und Koordinate gegen OSM und, bei Zweifel, gegen den Stadtplan 1935
(Kontrollkarte: `python3 werkzeuge/serve.py`, dann Stadtplan-Overlay einschalten).
`urteil` ∈ {richtig, falsche_strasse, falsche_nummer, falscher_stadtteil, unklar}; `bemerkung` frei.

Abnahmekriterium (Spec §6): haus → 0 falsche Straßen, ≤ 2 falsche Nummern; strasse → 0 falscher Stadtteil.
Jede Abweichung wird als Test (tests/), Regel (pipeline/lib/) oder Zeile in kuratierung/ nachgetragen.
