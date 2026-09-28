# Bergbau-Gruppen je Berufsnorm (Kapitel 4 der Schlaglichter, Thema „Bergbau“)

Stand: 2026-09-28. Tabelle `kuratierung/merkmale/bergbau.csv` (Norm → Gruppe), Modul `pipeline/lib/bergbau.py`,
Spec `docs/superpowers/specs/2026-09-28-bergbau-kapitel-design.md`.

## Warum nicht die OhdAB-Hauptgruppe B21?

B21 („Rohstoffgewinnung und -aufbereitung, Glas- und Keramikherstellung“) enthält neben Bergleuten Techniker,
Diplomingenieure, Schleifer, Gießer, Glasmacher, Steinmetze und Ziegler — Berufe, die ebenso in der
Metallverarbeitung standen. Für ein Bergbau-Kapitel zählen nur Berufe, die eindeutig zum Bergbau gehören.

## Vier Gruppen

| Gruppe | Schlüssel | Beispiele |
|---|---|---|
| Belegschaft | `belegschaft` | Bergmann, Hauer, Bergarbeiter, Anschläger, Fördermaschinist, Grubenschlosser |
| Aufsicht | `aufsicht` | Steiger (alle Arten), Schießmeister, Förderaufseher, Koksmeister |
| Leitung und Beamte | `leitung` | Zechenbeamter, Grubenbeamter, Bergassessor, Bergrat, Markscheider, Bergwerksdirektor |
| Berginvaliden | `invaliden` | Berginvalide |

Rang bei mehreren Gruppen im Haus (Adressfeld `bergbau`): Leitung > Aufsicht > Belegschaft > Berginvaliden.

Stand des Exports 2026-09-28 (verortete Teil-I-Einträge): Belegschaft 26.179, Aufsicht 1.121, Leitung und Beamte 342,
Berginvaliden 602; zusammen 28.244 von 173.168 Einträgen. Häuser der Klasse Bergbau: 5.428 (davon 1.651 nur
straßengenau oder Stadtplan 1935); 26 Gesellschaften, elf davon mit mehr als 90 Häusern.

## Grenzfälle (aufgenommen, mit Hinweis in der Tabelle)

- Kokereiarbeiter, Koksarbeiter: die Kokerei war meist Betriebsteil der Zeche, aber ein eigener Betriebsteil.
- Schlepper: im Ruhrbergbau ein Bergbau-Beruf; die OhdAB führt ihn unter Verkehr (B 5131).
- Oberschaffner: OhdAB B 2111, Bedeutung im Bergbau unklar.

## Nicht aufgenommen (mit Grund)

Techniker, Diplomingenieur (Tätigkeit ohne Branche), Schleifer, Gießer (Metall), Glasmacher, Steinmetz, Ziegler,
Zementeur (Steine, Glas, Keramik), Schachtmeister (Tiefbau-Polier, B 3229), Zimmerhauer (Bau), Kohlenhändler
(Handel), Bremser (Bahn).

## Zählfelder und Dateien

`n_bb_<gruppe>` je Adresse (Kacheln), Straße, Stadtteil, Hexfeld; Adressfeld `bergbau` (Rang); Kennzahlen
`bergbau_n`, `bergbau_<gruppe>_n`, `bergbau_haeuser_n`; Kapiteldaten `site/daten/perspektiven/bergbau_punkte.json`
(gepackte Kreise je Hexfeld und Gruppe, Häuser der Zechen mit Gesellschaft, Gesellschafts-ID =
`falte(name)` mit Unterstrichen). Thema `kuratierung/themen/bergbau.json` mit `schalter` (Kästchen in der Legende,
URL-Parameter `klassen=`: leer = alle, `keine`, sonst Komma-Liste). Form `site/js/formen/punktkarte.js`
(Zustände `gesammelt`, `karten`, `haeuser`; `aktualisiere` verschiebt vorhandene Kreise für den Übergang).

## Bezugsgröße

Teil I führt jede erwachsene Person mit eigenem Beruf oder Stand, nicht einen Eintrag je Haushalt (Befund 2026-09-28:
in 11.046 Fällen derselbe Nachname mehrfach an einer Adresse, 23.360 Einträge). Alle Texte sagen „eingetragene
Personen“; „Haushaltsvorstand“ wurde in Kapitel 0 und im Stellungs-Kapitel ersetzt.

## Eigentümer-Zusammenführung (2026-09-28)

Vor dem Kapitel wurden in `kuratierung/eigentuemer.csv` vier kanonische Schreibungen des Essener Bergwerks-Vereins
König Wilhelm und zwei des Mülheimer Bergwerks-Vereins auf je einen Namen geführt und der Tippfehler
„Gewerkschft Zeche Carolus Magnus“ behoben (37 Zeilen); Test `test_kuratierung_bergbau_kanonische_namen_ohne_dubletten`.

## Offen

Betreiber je Zeche (Historisches Portal), Adressabgleich Bergleute in Zechenhäusern, Betriebe des Bergbaus aus
Teil III nach Handprüfung, Prüfung der Tabelle durch den Projektleiter (`geprueft`), Bildrate des Übergangs am
Handy (Rückfall auf Canvas, falls unter 30 fps).
