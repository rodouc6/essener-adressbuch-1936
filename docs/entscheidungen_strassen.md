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

**Bewusst offen gelassen.** Im Hesselbruch (141 Nummern gegen 28 heute), Kapellenstraße; Vorortfälle mit nicht eindeutiger
Konkordanz (Kirchstraße Katernberg, Wallstraße, Bruchweiher …); 2.635 offene Namen ohne Dickhoff-
Treffer (verschwundene Straßen, brauchen Landmarken vom Stadtplan 1935).

**Lehre aus der Ritterstraße.** `zeitlich_abweichend=ja` ist kein Fehlerindikator: Dickhoffs
Namensketten fassen bei zusammengelegten Straßen mehrere Stränge zusammen, das abgeleitete
Gültigkeitsende kann Artefakt sein. Prüfung am Stadtplan 1935, nicht per Automatik.

## Runde 4 (2026-09-15, Nacht): Vorort-Widerspruch zerlegt

**Befund.** 7.828 Zeilen `vorort_widerspruch` (994 Paare). Zwei Drittel sind Teil-I-Zeilen ohne
Vorort, deren einziger 1936 gültiger Kandidat im Vorort liegt. Ursache bei den großen Fällen: Die
Zeitstufung lief vor dem Vorort-Filter und warf „weit“ datierte Kandidaten weg. Altendorfer Straße
(941 Zeilen): Dickhoff beendet den Namen 1933 mit „Thomaestraße (tlw. Umb.)“ für die ganze
Kernstadtstraße; übrig blieb die Horster Altendorfer Straße (bis 1937), die als Vorortstraße
scheiterte. Gleiches Muster Viktoriastraße Katernberg (Verl. 1937), Stoppenberger Straße Katernberg.

**R4.1 Vorort-Filter vor Zeitstufung.** Erst räumlich filtern, dann zeitlich stufen: 1936/undatiert,
sonst weit (1930–1937), sonst außerhalb — die Stufen verschmelzen nicht zu Homonymen (Schölerpad,
„Altendorfer Straße“ bis 1896, verdrängt nicht die bis 1933 so benannte Straße). Rückfälle tragen
`zeitlich_abweichend=ja`. Kein zuvor aufgelöstes Paar wechselt still den Schlüssel; drei Umsprünge
innerhalb der Rückfallstufe: Rotthausener Straße Katernberg → Ückendorfer Straße (Name bis 1935,
statt Auf der Reihe bis 1896), Bredeneyer Straße ohne Vorort → 00433 (weit, statt Homonym mit
Heisinger/Westfalenstraße), Phönixberg Kupferdreh → Oslenderstraße (Phönixberg bis 1934, statt der
erst 2000 benannten heutigen Straße; Prüfstelle). Tests: Fixture 00050/01371/02805.

**Wirkung.** 179 Paare, 3.578 Zeilen neu aufgelöst, alle mit `zeitlich_abweichend=ja`; Widerspruch
7.828 → 4.064 Zeilen (Rest: kein Kandidat in Essen passt, Ø 5 Zeilen je Paar → Schreibvarianten,
Dickhoff-Lücken). haus 62,5 → 63,0 %, offen 11,3 → 9,8 %, mehrdeutig 10.519 → 7.034,
zeitlich abweichend 9.019 → 12.504 Zeilen.

**Prüfstellen daraus (Stadtplan 1935).** Neu aufgelöste Paare mit Namen, die Dickhoff außerhalb
1930–1937 datiert, obwohl das Buch sie 1936 vielfach führt: Josephstraße → Westerdorfstraße
Altenessen (316 Zeilen), Luisenstraße → Lydiastraße Rüttenscheid (221), Königstraße → Porscheplatz
(100), Heinrichstraße Katernberg → Middeldorper Weg (85), Wilhelmstraße Werden → Tuchmachersteig
(72), Berliner Straße Steele → Bochumer Straße (40). Dickhoffs Datum oder Strang-Vermischung; als
Veränderungsmenge für die nächste gezielte Stichprobe vorgesehen.

**Nebenfund.** OCR-Fehler im Straßendatensatz: 02333 Stadium 3 „Ostenderstraße“ → Oslenderstraße
(Overlay in essener-strassen, für v1.0.2).

**R4.2 Erloschene Namen nicht automatisch (nach Stichprobe r4, 60 Zeilen, s. `stichprobe.md`).**
Grundsatzfrage des Projektleiters: Dickhoff ist kein Lexikon aller Straßen, die es je gab. Messung:
Dickhoff deckt 3.337 von 3.388 heutigen Straßen (98,5 %), führt aber keine verschwundenen Straßen.
Daraus folgt: Ein Name, den Dickhoff nur für eine Straße kennt, die ihn vor 1930 verlor, gehört 1936
meist einer verschwundenen Namensschwester. Die Stichprobe bestätigt das: Stufe „außerhalb“ mit
erloschenem Namen 11 falsch (Josephstraße → Westerdorfstraße: Plan zeigt dort Westerdorfstr.;
Luisenstraße, Königstraße, Kalkstraße, Voßstraße …), 6 richtig, 2 dritter Name, 3 unklar. Stufe „weit“
dagegen 29 richtig oder plausibel, 0 klar falsch, 6 unklar. Regel: „außerhalb“ greift nur noch, wenn der
Name heute gilt (Oberdorfstraße, Berzeliusstraße: Dickhoff datiert den heutigen Namen erst nach 1937,
die Kette ist lückenhaft); sonst `mehrdeutig=ja`, `grund_mehrdeutig=name_erloschen`, Kandidat als
Vorschlag. Die sechs am Plan bestätigten Fälle plus die Ritterstraße stehen jetzt kuratiert mit Beleg
(Wilhelmstraße Werden → Tuchmachersteig, Berliner Straße Steele → Bochumer Straße, Deipenbeckstalweg →
Deipenbecktal, Querstraße Karnap → Boshamerweg, Maxstraße Kray → Kiwittstraße, Hermannstraße Heisingen →
Butenbergs Kamp, Ritterstraße → Rauterstraße). Kosten: 149 Paare, 2.906 Zeilen zurück auf offen
(1,2 %), kein Schlüsselwechsel. Größte offene Prüfstellen daraus: Provinzialstraße Katernberg/
Schonnebeck → Gelsenkirchener Straße (492 Zeilen), Josephstraße (316, Lage 1936 unbekannt),
Luisenstraße (221), Altenhofstraße Katernberg → Schonnebeckhöfe (194), Viehauser Straße Werden (133).
Volllauf nach R4.2: haus 62,4 %, strasse 26,6 %, offen 11,0 %; mehrdeutig 9.940, zeitlich abweichend 9.194 Zeilen.

**Lehre zur Stichprobe r4.** Das Urteil wurde am geflaggten Dickhoff-Stadium gemessen („richtig“ = Plan
zeigt Dickhoffs Namen), nicht an der Pipeline; die Bemerkung nennt den am Plan gelesenen Namen. Beides ist
umrechenbar, aber die Anleitung muss künftig die Prüffrage eindeutig festlegen. Der am Plan gelesene Name
ist die wertvollere Information — er belegt Straßen unabhängig von Dickhoff.

**Offen aus r4.** Altendorfer Straße: der Plan zeigt um die heutige Nr. 262 „Thomaestraße“ (Teil-Umbenennung
1933); Nummernkreis 1936 gegen Ausdehnung der Thomaestraße prüfen (Muster Hermann-Göring-Straße). Heutige
Namen mit Dickhoff-Datierung nach 1937 (103 Paare, 3.091 Zeilen) sind automatisch, aber nur mit einer
Stichprobenzeile geprüft → Kandidat für eine gezielte Stichprobe.

## Runde 5 (2026-09-16): Schreibvarianten regelbasiert

**Vorgabe des Projektleiters.** Schreibvarianten nicht händisch durchsehen, sondern normalisieren und
kenntlich machen; auf der Karte historische und heutige Schreibweise untereinander.

**Befund.** 3.050 Namen ohne Kandidaten (14.909 Zeilen). Gemessen gegen alle Dickhoff-Namen in gestuften
Schlüsselformen: 466 Paare, 2.729 Zeilen fallen mit genau einem Dickhoff-Namen zusammen, dazu ≈1.000
Zeilen über Endungsvarianten; kein Fall mehrdeutig. Abkürzungen spielen keine Rolle (Herm.-Göring-Straße
141 Zeilen, Rest Einzelfälle). Der Rest (≈10.000 Zeilen: Matthiasstraße 359, Stadtwiese 353,
Friedrichshof 343, Maschinenstraße 223) sind verschwundene Straßen für den Stadtplan.

**R5.1 Schlüsselformen als Rückfall.** Fünf Stufen (`SCHLUESSELSTUFEN` in normalisierung.py), jede
strenger: ß/ss · Leerzeichen/Bindestrich/Punkt · ck/th/dt/ph/c/y/ie · Umlaut-Umschrift, ei/ey · Endung
-ener/-er, Genitiv-s, Doppelbuchstaben. Greift nur, wenn der Buchname keinen Kandidaten hat; die erste
Stufe mit genau einem Dickhoff-Namen entscheidet, mehrere Namen auf einer Stufe beenden die Suche
(Maierstraße/Mairstraße). Der angeglichene Name durchläuft die ganze Kette (Vorort-Filter, Zeitstufung,
R4.2). Flag `schreibvariante=ja`, `strasse_angeglichen` bis in Adresstabelle, Bericht, Prüfwerkzeug.
Ergebnis Stufe 03: 785 Paare/4.754 Zeilen angeglichen, davon 690/3.883 aufgelöst (Klementinen- →
Clementinenstraße → Brassertstraße 269; Eickenscheidter Straße Kray → Am Zehnthof 166; Einigkeit- →
Einigkeitsstraße 215; Heidhausener → Heidhauser Straße 219; Ueberruhr- → Überruhrstraße 137; De-Wolf- →
De-Wolff-Straße 120), 95 Paare bleiben Widerspruch/erloschen/homonym (Matthiasstraße → Mathiasstraße
homonym). Offen ohne Kandidaten 14.909 → 10.155 Zeilen; kein Schlüsselwechsel bei zuvor aufgelösten.
Volllauf: haus 62,4 → 63,5 %, strasse 26,6 → 27,0 %, offen 11,0 → 9,5 %; schreibvariante=ja 4.935 Zeilen.
Prüfung: gezielte Stichprobe r5 (60 Zeilen aus den 690 Paaren), geprüft 2026-09-16: 59 richtig, 1 unklar,
0 falsche Straße; keine Stufe zurückgenommen (Details in stichprobe.md).

## Runde 6 (2026-09-16): Prüfstellen und Sichtung am Stadtplan 1935

**Befund.** Die offenen Prüfstellen aus R4.2 (Provinzialstraße 523 Zeilen, Josephstraße 346, Luisenstraße 212,
Altenhofstraße 221, Viehauser Straße 190, Heinrichstraße 233, Königstraße 97) sind fast alle Buchnamen ohne
Vorort, zu denen Dickhoff nur einen vor 1930 erloschenen Namen kennt (`name_erloschen`). Sie zerfallen in zwei
Sorten: (1) die Straße existiert heute unter anderem Namen und Dickhoffs Kette ist lückenhaft — der Stadtplan
1935 zeigt den Buchnamen an der Kandidatenstraße; (2) die Straße ist verschwunden (Kernstadt: Josephstraße,
Luisenstraße, Königstraße; dahinter Stadtwiese 362, Friedrichshof 347, Maschinenstraße 267) — Dickhoff führt
sie nicht, OSM kennt sie nicht, die Lage kommt allein vom Plan. Insgesamt 2.963 offene Gruppen (Buchname,
Vorort) mit 20.785 Zeilen, davon 196 Gruppen mit ≥ 20 Zeilen.

**R6.1 Punkte vom Stadtplan 1935.** Neue Tabelle `kuratierung/strassen_1935.csv` (Schlüssel: normierter
Buchname + Buchvorort, `Kernstadt` für Einträge ohne Vorort). Eine Zeile mit `befund=punkt` löst in Stufe 03
mit `herkunft=stadtplan_1935` ohne heutige Straße auf (nach der Zuordnungstabelle, vor jeder Automatik) und
bekommt in Stufe 04 den Punkt auf Straßenebene mit `grund=stadtplan_1935`, ohne Nominatim. `befund=nicht_gefunden`
dokumentiert eine erfolglose Sichtung und verortet nichts. `Vorort` gehört dafür zum Adressschlüssel von Stufe 04.
Sorte (1) wird weiter über `strassen_zuordnung.csv` kuratiert, Beleg „Stadtplan 1935: … liegt an der heutigen …“.

**Werkzeug.** `werkzeuge/sichtung_liste.py` fasst alle offenen/mehrdeutigen Paare je (Buchname, Vorort) zusammen
(Zeilen, Teile, Gründe, Dickhoff-Kandidaten mit Namensstadien und Sprungkoordinate aus Nominatim, ähnliche Namen)
→ `build/sichtung_1935.json`; `werkzeuge/sichtung.html` zeigt OSM und Stadtplan 1935 nebeneinander, ein Klick
setzt den Punkt, ein Knopf je Kandidat schreibt die Zuordnung; der Server (`serve.py`) schreibt beide Tabellen
und liefert den Stadtteil-Vorschlag per Reverse-Geocoding. Anleitung: `docs/sichtung.md`.

**R6.2 Altendorfer Straße nur Straßenebene (Prüfstelle aus r4).** Dickhoff: 1933-05-08 innerer Teil →
Thomaestraße (tlw. Umb.), 1945 zurück. Das Buch 1936 zählt beide Straßen getrennt: Thomaestr. 1–293 mit
Lücke 50–199 (Krupp-Werk), Altendorfer Str. dicht 1–350 ohne Lücke (Teil I 941, II 176, III 165 Zeilen);
Eigentümer „Thomaestr. N“ aus dem Häuserteil wohnen laut Teil I in 20 von 51 Nummern unter Thomaestr. N,
in 0 von 46 unter Altendorfer Str. N. „Altendorfer Str. N“ von 1936 ist also nicht die heutige Nr. N (der
Plan zeigt an der heutigen 262 „Thomaestraße“); der äußere Teil zählte 1936 neu. → Zuordnungszeile
`altendorfer straße, Kernstadt, nummer_unsicher=ja` (Muster Beuststraße R3.5), ≈1.280 Zeilen von Haus- auf
Straßenebene. Thomaestraße → Altendorfer Straße mit Nummer bleibt (Annahme: alte Zählung behalten; Thomaestr. 1
trifft heute Altendorfer Str. 1, Krupp-Lücke passt, Plan zeigt Thomaestraße bei heutiger 262). Offen: der
Versatz der 1936er Zählung des äußeren Teils (Anker im Buch: Stadt Essen 278–282 und 23–27, Mülheimer
Bergwerksverein 81–179, Hansa-Apotheke 18/20, Hermann-Apotheke 152 — keine davon heute an der Straße).

**Gezielte Stichprobe r6.** Die 103 Paare (3.091 Zeilen), deren heutiger Name laut Dickhoff erst nach 1937
beginnt und die die Stufe „außerhalb + heutig“ automatisch auflöst (Oberdorfstraße 360, Berzeliusstraße 331,
Ruhrtalstraße Werden 233, Pieperstraße 197): Liste `docs/stichprobe_r6_paare.csv` mit `heutiger_name_ab` und
`name_davor`, Ziehung `stichprobe.py paare r6` (46 Zeilen), Prüffrage in stichprobe.md.

**R6.3 Wiederverwendete Namen (nach Stichprobe r6).** Ergebnis r6: 14 richtig, 10 falsche Straße, 22 unklar;
Regel ausgelöst. Alle zehn Fehler haben dasselbe Muster: der Buchname gilt heute für einen Abschnitt, den
Dickhoff 1936 unter anderem Namen führt („Frohnhauser Straße (tlw.)“ → Berzeliusstraße 1961, „Kruppstraße
(tlw.)“ → Jenckestraße 1969, Gartenstraße → Pausstraße 1977); der Plan 1935 zeigt dort den alten Namen, die
Straße des Buches lag woanders und existiert nicht mehr — der Name wurde wiederverwendet. Ohne solchen
Gegenbeleg (Kette beginnt nur später, oft Siedlungsstraßen mit Benennung 1938-10-21) gab es keinen Fehler.
Regel: in Schritt 4b/4c der Auflösung bleibt „außerhalb + heutig“ automatisch nur, wenn Dickhoff für 1936
kein datiertes Stadium mit anderem Namen belegt; Schreibvarianten (gleiche Schlüsselform oder Ähnlichkeit
≥ 0,94: Brahmkamp/Bramkamp, Rafael/Raffael, 1./I. Schniering) zählen nicht als anderer Name. Sonst
`mehrdeutig=ja`, `grund_mehrdeutig=name_spaeter`, Kandidat als Vorschlag in der Sichtungsliste. Kosten im
Lauf: 55 Paare, 1.666 Zeilen `name_spaeter`; haus 63,4 → 62,9 %, offen 8,6 → 9,2 % (dazu R6.2 Altendorfer Straße). Am Plan bestätigt und zu kuratieren:
Oberdorfstraße (461 Zeilen), Ruhrtalstraße Werden (319), Am Bocklerbaum (69), Mechtenbergstraße (42).

**Prüfstelle Straßendatensatz.** Dickhoff 01004 Gelsenkirchener Straße: Stadium 1 „1984-08-07 Provinzialstraße“
neben „1892-03-29 Gelsenkirchener Straße“ (Länge 0) und „1892-03-29 Mittelstraße“ — die Datierung ist
wahrscheinlich 1894, für essener-strassen v1.0.2 prüfen.

