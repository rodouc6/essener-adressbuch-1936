# Manuelle Stichprobe der Geokodierung

**Stand:** Seed 2026 (Zufall), r3 bis r6 (gezielt) sind geprüft, Ergebnisse unten. `stichprobe_2027.csv` (Zufall) wartet. Gezielte Stichproben
(`stichprobe.py gezielt <name>`) prüfen nur die von einer Regelrunde berührten Adressen, Spalte `gruppe`.

Datei: `docs/stichprobe_2026.csv` (200 × haus, 100 × strasse, Zufall mit Seed 2026).
Erzeugt mit `python3 werkzeuge/stichprobe.py 2026` (gezielt: `python3 werkzeuge/stichprobe.py gezielt r3`; Paarliste: `python3 werkzeuge/stichprobe.py paare r4`) aus `build/04_geokodiert.csv` — derselbe Lauf
ergibt dieselbe Stichprobe. Nach einem Neulauf der Pipeline muss sie neu gezogen und neu geprüft werden.
Prüfung je Zeile: `display_name` und Koordinate gegen OSM und gegen den Stadtplan 1935.
`urteil` ∈ {richtig, falsche_strasse, falsche_nummer, falscher_stadtteil, unklar}; `bemerkung` frei.

## Prüfwerkzeug

    python3 werkzeuge/stichprobe_hinweise.py r3     # einmal je Stichprobe → build/stichprobe_hinweise_<name>.json
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

## Ergebnis r3 — gezielte Stichprobe zu Runde 3 (Prüfung 2026-09-15)

| Gruppe | richtig | unklar | falsche_strasse | Schluss |
|---|---:|---:|---:|---|
| kernstadt_angenommen (40) | 37 | 3 | 0 | Annahme hält (Regel: >2 Vorortfälle → zurücknehmen). Flag bleibt. |
| bereichsgrenze (40) | 37 | 2 | 1 | Grenzen aus Nummernkreis/Anker halten (Rüttenscheider 12/12, Heinrich-Strunk 9/9). Nr. 144 Eickenscheidter Fuhr liegt am Plan an der Burggrafenstraße → Grenzstreifen 140–144 auf `nummer_unsicher`. |
| teilstrecke_neu (20) | 7 | 10 | 3 | **Fund:** heutige Beuststraße 49–63 verläuft auf der Herkulesstraße von 1935 (Abzweig zur Zeche Hercules); Dickhoff verzeichnet die Umwidmung nicht. Nr. 38–45 richtig. → Beuststraße ab 47 und Herkulesstraße ganz auf `nummer_unsicher`. |

Wirkung des Nachlaufs: 154 Hausnummern-Treffer zu Straßenebene (Beuststraße 58, Herkulesstraße 88,
Eickenscheidter Fuhr 8); Gesamtquote haus 62,5 % unverändert. Einzelfall ohne Folge: Holsterhauser Str. 13
(„eher Beiseweg“, unklar). Lehre wie bei der Ritterstraße: Dickhoff führt heutige Namen mit ihrer
Kette, aber nicht jede Verlegung eines Straßenzugs; wo heutige und 1935er Führung abweichen, hilft nur der Plan.

## Stichprobe r4 — gezielte Prüfung zu Runde 4 (gezogen und geprüft 2026-09-15)

Grundmenge: die 176 Straße-Paare, die der Regelfix R4.1 (Vorort-Filter vor Zeitstufung,
`docs/entscheidungen_strassen.md`) neu aufgelöst hat, 3.485 Zeilen, alle `zeitlich_abweichend=ja`;
Liste in `docs/stichprobe_r4_paare.csv` (Spalte `vorher` = alter Grund, `zeitlich_abweichend`).
Ziehung `stichprobe.py paare r4`: die 40 zeilenstärksten Paare mit je einer Adresse (`neu_gross`,
deckt rund 85 % der Zeilen), 20 zufällige Adressen aus den übrigen 136 Paaren (`neu_rest`).

**Prüffrage ist die Straße, nicht die Hausnummer:** Trägt die Straße am Stadtplan 1935 den Namen aus
dem Adreßbuch (Feld „Name im Plan 1935“ im Werkzeug)? Bei Namen, die Dickhoff vor 1930 enden lässt
(Josephstraße → Westerdorfstraße, Luisenstraße → Lydiastraße, Königstraße → Porscheplatz), entscheidet
allein der Plan: steht der alte Name dort an der heutigen Straße, ist Dickhoffs Datum falsch oder die
Kette vermischt Stränge (Muster Ritterstraße) → `richtig`; steht er woanders → `falsche_strasse` mit
Hinweis, wo. Entscheidungsregel vorab: mehr als vier `falsche_strasse` unter den 40 großen Paaren,
und die Rückfallstufe „außerhalb“ wird nicht mehr automatisch, sondern nur kuratiert vergeben.

**Ergebnis.** Geprüft wurde abweichend von der Anleitung: `richtig` = der Plan zeigt am Punkt das von Dickhoff
für 1935 erwartete (geflaggte) Stadium; `falsche_strasse`/`unklar` = der Plan zeigt einen anderen Namen, der
in `bemerkung` steht. Umgerechnet auf die Pipeline-Frage (liegt der Punkt auf der Straße des Buches?):

| Rückfallstufe | Pipeline richtig | plausibel | falsch | dritter Name | unklar |
|---|---:|---:|---:|---:|---:|
| weit (Umbenennung 1930–1937) | 14 (Plan zeigt Buchnamen) | 15 | 0 | 1 | 7 |
| außerhalb, Name erloschen | 6 | 0 | 11 (Plan zeigt Dickhoffs Namen) | 2 | 3 |
| außerhalb, Name gilt heute | 0 | 1 | 0 | 0 | 0 |

Die Entscheidungsregel (>4 falsche Straßen unter den großen Paaren) hat ausgelöst → R4.2: Stufe „außerhalb“
nur noch für heute gültige Namen, sonst `name_erloschen`. Die sechs am Plan bestätigten erloschenen Namen sind
kuratiert (`strassen_zuordnung.csv`, Beleg „Stadtplan 1935 zeigt … am Punkt“). Offen aus den Bemerkungen:
Sevenarstr. 18 Katernberg liegt am Plan an der Rotthauser Str.; Markt Steele = Hansamarkt?; Stoppenberger
Straße 87: Grenze Gelsenkirchener/Mittelstraße; Werdener Str. 44: Hespertaler Landstraße oder Hammer Straße.

## Stichprobe r5 — Schreibvarianten (gezogen 2026-09-16, geprüft 2026-09-16)

Grundmenge: die 690 Paare, die Runde 5 über Schlüsselformen aufgelöst hat (`docs/stichprobe_r5_paare.csv`,
Spalte `strasse_angeglichen`). Ziehung `stichprobe.py paare r5`: 40 zeilenstärkste Paare je eine Adresse
(`neu_gross`), 20 zufällige aus dem Rest (`neu_rest`).

**Prüffrage, eindeutig:** *Liegt der rote Punkt auf der Straße, die im Adreßbuch steht?* Maßstab ist das
Buch, nicht Dickhoff. Am Stadtplan 1935 den Buchnamen (oder seine Schreibvariante, das Werkzeug zeigt
„Schreibvariante: Buchname an … angeglichen“) an der Stelle des Punktes suchen.
- Steht der Buchname bzw. die Variante dort → `richtig`.
- Steht dort ein anderer Name → `falsche_strasse`, in `bemerkung` den Namen aus dem Plan.
- Ausnahme (nachgetragen nach der Prüfung): Zeigt der Plan ein anderes Namensstadium *derselben* Straße
  laut Dickhoff (Vorgängername, weil die Umbenennung zwischen Planstand 1935 und Buch 1936 liegt, oder
  Nachfolgername, weil das Buch den alten Namen weiterführt) → `richtig`, Bemerkung mit Stadium und Datum.
- Nicht lesbar oder unentscheidbar → `unklar`, Bemerkung.
Entscheidungsregel vorab: mehr als drei `falsche_strasse` unter den 40 großen Paaren → die betroffene
Schlüsselstufe wird zurückgenommen (die Stufe steht je Fall in der Paarliste ableitbar; ich werte sie aus).

**Ergebnis.** 59 × `richtig`, 1 × `unklar` (Isingertor 4, Steele: Plan schwer lesbar), 0 × `falsche_strasse`.
Sieben Zeilen waren zunächst als `falsche_strasse` geurteilt, weil der Plan einen anderen Namen zeigt; alle
sieben sind laut Dickhoff Namensstadien derselben Straße und wurden mit Beleg auf `richtig` gesetzt (die
Prüffrage hatte diesen Fall nicht benannt, Ausnahme oben nachgetragen):

| Buch 1936 | Punkt liegt auf | Plan 1935 zeigt | Dickhoff |
|---|---|---|---|
| Ölberg 10, Katernberg | Oelberg | Niermannstraße | umbenannt 1935-01-14 |
| Kösters-Busch 31, Stoppenberg | Kösters Busch | Zechenstraße | umbenannt 1936-01-15 |
| Ueckendorfer Str. 57, Katernberg | Ückendorfer Straße | Rotthausener Straße | umbenannt 1935-11-14 |
| Merziger Au 9, Leithe | Merziger Aue | Fliederstraße | umbenannt 1935-11-14 |
| Wilhelm Bernsau Weg 19, Werden | Wilhelm-Bernsau-Weg | Steinhäuser Weg | umbenannt 1935-06-03 |
| Eickenscheidter Str. 25, Kray | Am Zehnthof | Am Zehnthof | ursprünglicher Name von 00149, seit 1933-05-08 Am Zehnthof |
| Yorkstr. 16, Nordviertel | Altenbergstraße | Altenbergstraße | Yorckstraße 1898–1931, seit 1931-12-11 Altenbergstraße |

Die fünf Vorgängernamen sind das erwartete Bild (Plan älter als die Umbenennung, Buch jünger); die zwei
Nachfolgernamen bestätigen, dass das Adreßbuch Umbenennungen oft Jahre später nachzieht (vgl.
Erhebungsstand). Nach Schlüsselstufe (erste Stufe, auf der Buch- und Dickhoff-Form zusammenfallen):
Stufe 1 (Leerzeichen/Bindestrich/Punkt) 24 Zeilen, Stufe 2 (ck/th/dt/ph/c/y/ie) 11, Stufe 3 (Umlaut,
ei/ey) 5, Stufe 4 (Endung, Genitiv-s, Doppelbuchstaben) 20; Stufe 0 (ß/ss) nicht in der Stichprobe. Die
Entscheidungsregel hat nicht ausgelöst, keine Schlüsselstufe wird zurückgenommen.

## Stichprobe r6 — heutige Namen, die Dickhoff erst nach 1937 datiert (gezogen und geprüft 2026-09-16)

Grundmenge: die 103 Paare (3.091 Zeilen), bei denen der Buchname heute gilt, Dickhoffs Kette den Namen aber
erst nach 1937 beginnen lässt (`docs/stichprobe_r6_paare.csv`, Spalten `heutiger_name_ab`, `name_davor`). Die
Automatik löst sie seit R4.2 als „außerhalb + heutig“ auf (Annahme: Dickhoffs Kette ist lückenhaft, nicht die
Straße falsch), geprüft war das bisher mit einer einzigen Zeile. Ziehung `stichprobe.py paare r6`: 40
zeilenstärkste Paare je eine Adresse (`neu_gross`), 6 aus dem Rest (`neu_rest`).

**Prüffrage:** *Liegt der rote Punkt auf der Straße, die im Adreßbuch steht?* Am Stadtplan 1935 den Buchnamen
an der Stelle des Punktes suchen.
- Steht der Buchname dort → `richtig` (Dickhoffs Kette ist lückenhaft).
- Steht dort ein anderes Namensstadium *derselben* Straße laut Dickhoff (Werkzeug: „Name im Plan 1935“) →
  `richtig`, Bemerkung mit Stadium.
- Steht dort ein anderer Name → `falsche_strasse`, in `bemerkung` den Namen aus dem Plan.
- Nicht lesbar oder unentscheidbar → `unklar`, Bemerkung.
Entscheidungsregel vorab: mehr als drei `falsche_strasse` unter den 40 großen Paaren → die Stufe „außerhalb +
heutig“ wird nicht mehr automatisch, sondern nur kuratiert vergeben.

**Ergebnis.** 14 × `richtig`, 10 × `falsche_strasse`, 22 × `unklar` (46 Zeilen). Die Entscheidungsregel hat
ausgelöst (9 falsche unter den 40 großen). Der Prüfer hat abweichend von der Anleitung auch dann `falsche_strasse`
vergeben, wenn der Plan Dickhoffs Vorgängernamen zeigt — zu Recht: bei Umbenennungen von 1955–1977 sagt der
Vorgängername im Plan 1935 nichts über den Buchnamen von 1936 aus, der Buchname muss woanders gelegen haben.
Die Anleitung oben (Punkt „anderes Namensstadium derselben Straße → richtig“) gilt nur, wenn die Umbenennung
zwischen Planstand 1935 und Buch 1936 liegt (r5), nicht für Jahrzehnte spätere.

Nach dem Kriterium „Dickhoff belegt für 1936 einen *anderen* Namen derselben Straße“:

| Kriterium | richtig | falsche_strasse | unklar | Paare / Zeilen gesamt |
|---|---:|---:|---:|---|
| anderer Name 1936 belegt (meist „(tlw.)“-Abschnitt, umbenannt 1955–1977) | 7 | 10 | 5 | 49 / 1.994 |
| kein anderer Name (Kette beginnt nur später, oft 1938-10-21) | 7 | 0 | 17 | 54 / 1.097 |

Die zehn falschen Straßen (Berzeliusstraße, Franz-Arens-Straße, Heilermannstraße, Jenckestraße, Bessemerstraße,
Pausstraße, Reulsbergweg, Rahmbruchsweg, Steinbrink, Münstermannstraße) liegen alle in der ersten Gruppe. Die
sieben richtigen dort sind drei Schreibvarianten (Bramkamp-/Brahmkampstraße, Raffael-/Rafaelstraße, I./1.
Schnieringstraße) und vier Fälle, in denen der Plan den Buchnamen zeigt (Oberdorfstraße, Ruhrtalstraße Werden,
Am Bocklerbaum, Mechtenbergstraße) — Dickhoffs Datum ist dort zu spät. Die `unklar` der zweiten Gruppe sind
überwiegend 1935 unbebaute oder unbeschriftete Nebenstraßen (Siedlungen, Benennung 1938-10-21), der Plan
kann sie weder bestätigen noch widerlegen; das Buch belegt die Namen für 1936.

→ R6.3: die Stufe „außerhalb + heutig“ bleibt automatisch nur ohne anderen 1936er Namen (Schreibvarianten
ausgenommen); sonst `mehrdeutig=ja`, `grund_mehrdeutig=name_spaeter`, Kandidat als Vorschlag für die Sichtung.
Die vier am Plan bestätigten Fälle sind kuratiert (2026-09-17, vom Prüfer bestätigt: Plan 1935 zeigt den Buchnamen).
Offen aus den Bemerkungen: Gelsenkirchener/Mittelstraße Katernberg (Grenze unklar), Sarnsbank/Schiefernberg,
Asthöwerstraße (Punkt eher auf Bessemerstraße), Stattropstraße (Punkt auf verschwundener Nebenstraße),
Freistatt-/Jakobstraße (vertauscht?).

