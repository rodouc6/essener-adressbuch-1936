# Gewerbebezeichnungen in der Berufsspalte (Befund 2026-09-24)

## Befund

Rund 220 Schreibweisen der Berufsspalte (≈ 6.900 Nennungen, 4 % aller Berufsangaben) bezeichnen
keinen Beruf, sondern einen Betrieb: „Lebensmittel“ (556), „Schneiderei“ (369), „Bäckerei“ (257),
„Schuhmacherei“ (251), „Friseurgesch.“ (246), „Baugesch.“ (233), „Fuhrgesch.“ (204), „Heißmangel“
(199), „Metzgerei“ (199), „Milchhdlg.“ (170) …

Die Zeilen sind **Personeneinträge des Teils I** (Einwohnerverzeichnis), nicht Firmen: Nachname,
Vorname (oder Familienstand mit Bezugsperson), Berufsspalte, Wohnadresse; von 1.506 geprüften
Zeilen hat keine einen Firmennamen. Beispiele (`build/eintraege.csv`):

```
Eumann   | Fritz | Lebensmittel | Wüstenhöferstraße 180 | Teil I, S. 127
Dellmann | –     | Bäckerei     | Klosterstr. 2a        | Witwe von Friedr.
Kanstein | –     | Heißmangel   | Krausstr. 13          | Frau von Albert
```

Scherl setzt bei selbständigen Gewerbetreibenden das Gewerbe in die Berufsspalte. Bei Frauen
(Witwen, „Frau Albert Kanstein“) steht praktisch immer die Gewerbeform: Die Witwe führt den
Betrieb weiter, hat aber keine Berufsbezeichnung.

## Dieselbe Gruppe wie die Meister

Anteil der Teil-I-Personen, die zusätzlich in Teil III (Gewerbe) mit gleichem Namen und gleicher
Adresse als Firma stehen:

| Berufsspalte Teil I | Zeilen | mit Teil-III-Eintrag |
|---|---|---|
| Bäckerei | 176 | 84 % |
| Bäckermstr. | 288 | 74 % |
| Bäcker | 534 | 7 % |
| Schneiderei | 366 | 37 % |
| Schneidermstr. | 531 | 83 % |
| Schneider | 573 | 16 % |
| Metzgerei | 136 | 69 % |
| Metzgermstr. | 307 | 77 % |
| Metzger | 476 | 9 % |
| Lebensmittel | 523 | 64 % |
| Bergm. | 26.847 | 0 % |

„Bäckerei“ und „Bäckermstr.“ sind also dieselbe soziale Gruppe (Inhaber), „Bäcker“ der Geselle.

## Keine Doppelzählung

Die Berufszuordnung betrifft nur Teil I und II; Teil III ist ausgeschlossen. Jede Person wird genau
einmal über ihre Teil-I-Zeile gezählt; Teil III bleibt eine eigene Ebene (Firmen, ohne Beruf).

## Entscheidung

- Gewerbeform → Item des **Berufsträgers** (Bäckerei → Bäcker/in B 29222-101, Lebensmittel →
  Lebensmittelhändler/in B 62302-107, Fuhrgesch. → Fuhrunternehmer/in B 51694-113, Heißmangel →
  Heißmangler/in B 54132-129).
- Status **`gewerbe`** hält fest, dass die Vorlage den Betrieb nennt, nicht die Qualifikation
  (Anzeige „Bäckerei → Bäcker · Fachliche Tätigkeit (unsicher) · Gewerbebetrieb“).
- **`niveau_unsicher=ja`**, weil das OhdAB-Niveau die Inhaberstellung nicht abbildet (Bäcker =
  fachlich, Bäckermeister = Aufsicht); die Teil-III-Quote spricht für die Meister-Nähe, belegt ist
  sie nicht. Der Sozialscore (TP5) kann `status=gewerbe` gesondert behandeln.
- Verworfen: alle → „Gewerbetreibende/r“ A 61094-500 (Berufsinhalt weg, Niveau Führung
  überzeichnet); offen lassen (systematische Lücke beim selbständigen Kleinmittelstand).

Die Vorschläge entstanden regelhaft (`-hdlg.` → `-händler`, `-gesch.` → Stamm, `-erei` → `-er`,
`-wr.` → `-warenhändler`) mit Ausnahmeliste und werden wie alle anderen von Hand geprüft
(`bearbeiter=claude`, `geprueft` leer).
