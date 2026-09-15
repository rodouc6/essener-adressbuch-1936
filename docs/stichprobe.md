# Manuelle Stichprobe der Geokodierung

Datei: `docs/stichprobe_2026.csv` (200 × haus, 100 × strasse, Zufall mit Seed 2026).
Prüfung je Zeile: `display_name` und Koordinate gegen OSM und, bei Zweifel, gegen den Stadtplan 1935
(Kontrollkarte: `python3 werkzeuge/serve.py`, dann Stadtplan-Overlay einschalten).
`urteil` ∈ {richtig, falsche_strasse, falsche_nummer, falscher_stadtteil, unklar}; `bemerkung` frei.

Abnahmekriterium (Spec §6): haus → 0 falsche Straßen, ≤ 2 falsche Nummern; strasse → 0 falscher Stadtteil.
Jede Abweichung wird als Test (tests/), Regel (pipeline/lib/) oder Zeile in kuratierung/ nachgetragen.
