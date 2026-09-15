# Entscheidungen zur Straßenauflösung

Kurzprotokoll der Regel- und Kuratierungsentscheidungen, chronologisch. Belege je Straße
stehen in `kuratierung/strassen_zuordnung.csv` (Spalte `beleg`); hier nur das Warum.
Grundsatz: Präzision vor Vollständigkeit. Unsicheres wird nicht geraten, sondern markiert
(`mehrdeutig`, `vorort_angenommen`, `nummer_unsicher`) und kann nach dem Launch
schrittweise kuratiert werden.

## 2026-09-15 — Runde 3 nach der Stichprobe (Spec §6)

**Anlass.** Stichprobe Seed 2026 bestanden (haus 194/6/0, strasse 95/5/0, s. `stichprobe.md`).
Danach Analyse der 12.600 Zeilen mit „Doppelnamen“ (`homonym_1936`, `konkordanz_nicht_eindeutig`).
Ergebnis: vier verschiedene Ursachen, nur eine braucht Handentscheidungen.

**R3.1 Burgaltendorf ist keine Kernstadt.** Der Kernstadt-Filter (Teil I ohne Vorort) ließ
Straßen durch, deren Stadtteil weder Vorort noch Kernstadt ist (Burgaltendorf, 1936 nicht
Essen). Behoben in `_kernstadt()`; Beispiel Charlottenstraße → Dohmanns Kamp.

**R3.2 Kernstadt-Entscheid in Teil II/III.** Ein leerer Vorort bedeutet in Teil II/III zu 95 %
Kernstadt (eindeutig aufgelöste Zeilen: 31.886 Kernstadt gegen 1.434 Vorort). Als Vorfilter zu
riskant, als Entscheider unter sonst gleichwertigen Kandidaten vertretbar. Flag
`vorort_angenommen=ja`, alle Kandidaten bleiben notiert. Betrifft u. a. Steeler Straße,
Holsterhauser Straße, Alfredstraße, Schützenbahn, Moltkestraße (Teil II/III).

**R3.3 Teilstrecken-Zusatz tolerant.** Dickhoffs „(tlw.)“ steht auch als „(tlw. Umb.)“, „(Umb. tlw.)“;
das Muster prüft jetzt „tlw“ in der Klammer. Drei OCR-Varianten („tlIw“, „tiIw“, „tim“) wurden
im Datensatz essener-strassen korrigiert (Overlay, Commit d91e0c7 dort). Beuststraße/Immestraße,
Walpurgisstraße/Im Walpurgistal und II. Hagen/Schwarze Horn sind damit Teilstrecken, keine Homonyme.

**R3.4 Hausnummernbereiche in der Kuratierung.** Nach 1936 geteilte oder zusammengelegte Straßen
lassen sich nur über die Hausnummer zuordnen. Methode: Nummernkreis 1936 aus Teil II (Häuser/
Eigentümer; Doppelnummern zeigen zwei Kreise, a-Varianten nicht) gegen heutige Nummernbereiche
aus OSM (Overpass, 2026-09-15). Bleibt die heutige Zählung erhalten, gilt die Hausebene; wurde
neu gezählt, nur die Straßenebene (`nummer_unsicher=ja`). Neue Spalten `hausnr_von`,
`hausnr_bis`, `nummer_unsicher`; `vorort=Kernstadt` gilt nur für Einträge ohne Vorort.
Kuratiert: Hermann-Göring-Straße (≤323 Rüttenscheider, ≥324 Bredeneyer Straße),
Adolf-Hitler-Straße (≤75 Kettwiger, ≥76 Viehofer Straße; Anker Baedeker Nr. 35), Eickenscheidter
Fuhr (>144 Gerhard-Stötzel-Straße), Helmholtzstraße (→ Heinrich-Strunk-Straße, ≤22 unsicher),
Walpurgisstraße (>77 Im Walpurgistal), Wittekindstraße (>94 unsicher), Karlstraße (Kernstadt →
Altenessen-Nord), Vogelheimer Straße (→ heutige; das Buch nutzt schon den Neunamen Hafenstraße).

**R3.5 Nachlauf nach gezielter Stichprobe (100 Zeilen, s. `stichprobe.md`).** Kernstadt-Annahme
bestätigt (0 Vorortfälle unter 40). Bereichsgrenzen bestätigt bis auf Eickenscheidter Fuhr 144 →
Grenzstreifen 140–144 `nummer_unsicher`. Fund Beuststraße: heutige Nr. 49–63 liegen auf der
Herkulesstraße von 1935 (Umwidmung fehlt bei Dickhoff) → Beuststraße ab 47 und Herkulesstraße ganz
nur Straßenebene. Kosten: 154 Hausnummern-Treffer, Quote unverändert 62,5 %.

**Bewusst offen gelassen.** Bredeneyer Straße ohne Vorort (Name galt 1936 offiziell nicht),
Im Hesselbruch (141 Nummern gegen 28 heute), Kapellenstraße; Vorortfälle mit nicht eindeutiger
Konkordanz (Kirchstraße Katernberg, Wallstraße, Bruchweiher …); 2.635 offene Namen ohne Dickhoff-
Treffer (verschwundene Straßen, brauchen Landmarken vom Stadtplan 1935).

**Lehre aus der Ritterstraße.** `zeitlich_abweichend=ja` ist kein Fehlerindikator: Dickhoffs
Namensketten fassen bei zusammengelegten Straßen mehrere Stränge zusammen, das abgeleitete
Gültigkeitsende kann Artefakt sein. Prüfung am Stadtplan 1935, nicht per Automatik.
