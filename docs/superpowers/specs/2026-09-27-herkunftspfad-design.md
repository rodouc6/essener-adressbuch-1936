# Schlaglichter, Schritt 2: Herkunftspfad im Detailkasten — Entwurf

Stand 2026-09-27. Entschieden am Mockup `build/mockups/herkunftspfad.html` (nicht versioniert): Variante A
(Brotkrumen) beim Schweben, Variante C (aufklappbarer Beleg) beim Klick; Quellmarken in eigenen Farben
(Hand grün, Vorschlag grau, nach Prinzipien violett, Regel orange), nicht an die Schraffur angelehnt.
Baut auf `2026-09-27-datenbasis-kapitel0-design.md` auf.

## 1. Ziel

Wer in den Schlaglichtern ein Segment, einen Kreis oder eine Einheit anschaut, soll sehen, wie die Zahl
zustande kam: welche Schreibweisen des Buches dahinterstehen, zu welcher Norm bzw. welchem kanonischen
Namen sie zusammengeführt wurden, welche Klasse daraus abgeleitet ist und welcher Anteil davon von Hand
geprüft, vorgeschlagen oder per Regel klassifiziert ist. Der Leser soll die Zahl bis zur Kuratierungstabelle
zurückverfolgen können, ohne die Erzählung der Kapitel zu unterbrechen.

Nicht Ziel: Änderungen an der Karte oder der Hausansicht; Werkstatt; ein neues Kuratierungswerkzeug.

## 2. Datenkerne und ihre Pfade

| Datenkern | Stufen des Pfads | Quellmarke |
|---|---|---|
| stellung / gruppe / niveau (Teil I) | Schreibweise im Buch → Beruf nach OhdAB → Stellung (bzw. Hauptgruppe, Niveau) → Gruppe im Kapitel | Hand / Vorschlag (`stellung_quelle`) |
| besitz (Teil II) | Schreibweise im Häuserbuch → kanonischer Eigentümer → Klasse → Gruppe; dazu Zeilen → Häuser (Spannen, Nummerntreffer) | Hand / Regel (`besitz_pruefung`) |
| gewerbe (Teil III) | Rubrik im Branchenverzeichnis → Branche und Betriebsform → Gruppe | Hand / nach Prinzipien / Wortregel (`gewerbe_quelle`) |
| kennzahlen (Trichter) | unverändert (Erklärtext je Stufe, Schritt 1) | — |

## 3. Exportpaket `site/daten/herkunft/`

Neu in `pipeline/lib/karte_export.py` (`baue_herkunft(adressen) -> dict[str, dict]`, Dateiname → Inhalt; die
Einträge tragen `_beruf`, `_eigentuemer`, `_identitaet`, `_pruefung`, `_gewerbe` schon aus `gruppiere`), geschrieben
von `schreibe_paket`, Ordner vorher geleert wie `perspektiven`. Alle Zählungen beziehen sich auf die
**verorteten** Einträge (dieselbe Grundmenge wie Ebenen und Layouts), nicht auf die Kuratierungstabellen.

- `herkunft/stellung.json` — je Klasse (`arbeiter`, …, `unbestimmt`):
  `{ schreibweisen: int, normen: int, nennungen: int, quelle: { hand: int, vorschlag: int },
     top: [[schreibweise, nennungen, norm, quelle], … max 10] }`
- `herkunft/gruppe.json`, `herkunft/niveau.json` — gleiche Form je Hauptgruppe bzw. Niveau, Quelle
  `{ hand: int }` (Beruf ist immer von Hand zugeordnet; Niveau `unsicher` als eigene Zahl).
- `herkunft/berufe.json` — je OhdAB-Norm (Schlüssel wie `layout/berufe.json`):
  `{ norm, nennungen, schreibweisen: [[schreibweise, nennungen], … max 10], stellung, stellung_quelle }`
- `herkunft/besitz.json` — je Klasse: `{ eigentuemer: int, zeilen: int, haeuser: int, quelle: { hand: int, regel: int },
     spanne: int, nummer: int, top: [[kanonischer Name, haeuser], … max 10] }`; für `privatperson` zusätzlich
  `regel_beispiele: [[schreibweise, haeuser], … 5]`.
- `herkunft/eigentuemer.json` — je kanonischem Namen (Schlüssel wie `layout/eigentuemer.json`):
  `{ schreibweisen: [[schreibweise, zeilen], … max 10], schreibweisen_gesamt: int, zeilen: int, haeuser: int,
     spanne: int, nummer: int, kategorie, identitaet }`
- `herkunft/gewerbe.json` — je Branche: `{ rubriken: int, betriebe: int, quelle: { hand, claude, vorschlag },
     top: [[rubrik, betriebe, art, quelle], … max 10] }`
- `herkunft/rubriken.json` — je Rubrik: `{ betriebe, gruppe, art, quelle }`

Größe: alle Dateien zusammen unter 1 MB (Schätzung: 854 Normen × 10 Schreibweisen, 287 Eigentümer × 10,
823 Rubriken × 1). `daten_ebenen.ladeEbenen` lädt sie **nicht** vorab; `Lader.herkunft(name)` holt eine
Datei beim ersten Bedarf und hält sie im Speicher.

## 4. Anzeige im Detailkasten (`site/js/perspektiven_modell.js`, `perspektiven.js`)

### 4.1 Schwebend (Variante A)

Unter der bisherigen Zahlenzeile eine Brotkrumen-Zeile `herkunftPfad(kontext, herkunft) → [{ label, wert, marke? }]`:

- Segment (Gruppe im Balken), Datenkern stellung: `Buch: 534 Schreibweisen › OhdAB: 419 Berufe › Stellung: Arbeiter [94 % Hand] [6 % Vorschlag] › Gruppe: <Gruppenname>`.
  Bei Gruppen aus mehreren Klassen (z. B. Bürgertum = beamte + angestellte + …) werden die Klassen
  summiert; die Stufe „Stellung“ nennt dann die Klassen mit Komma.
- Segment, Datenkern besitz: `Buch: <n> Schreibweisen › Eigentümer: <n> zusammengeführt › Klasse: <Name> [Hand n %][Regel n %] › Gruppe`.
- Segment, Datenkern gewerbe: `Buch: <n> Rubriken › Branche: <Name> [Hand][Prinzipien][Wortregel] › Gruppe`.
- Kreis (Bubbles) Beruf: `Buch: <n> Schreibweisen › OhdAB: <Norm> › Stellung: <Klasse> [Hand|Vorschlag] › Gruppe`.
- Kreis Eigentümer: `Buch: <n> Schreibweisen › Eigentümer: <Name> › Klasse [Hand] › Gruppe`, darunter Zeile
  „<zeilen> Zeilen im Häuserbuch, <haeuser − zeilen> Häuser dazu über Hausnummernspannen“, wenn > 0.
- Kreis Rubrik: `Buch: <Rubrik> › Branche: <Name> [Quelle] › Gruppe`.
- Einheit (Stadtteil, Straße, Hexfeld): kein Pfad, nur eine Quellzeile aus den Zählfeldern der Einheit:
  stellung „<n_stellung_hand> von <N> von Hand“, besitz „<regel> per Regel“ (gibt es schon), gewerbe keine.
- Segment „ausgeschlossen“: kein Pfad (der Ausschluss-Text aus Schritt 1 bleibt).
- Schraffierter Regel-Teil der Privatpersonen: `Buch: Person ohne Firmenname › Regel: → Privatperson [Regel] › Gruppe`,
  Hinweis „keine Handprüfung, keine Identität“ (Fall 3 des Mockups). Dafür bekommt der schraffierte
  Teil im Balken eine eigene `data-id` `<Gruppe>#regel`; `detailTextGruppe` erkennt das Suffix.

Quellmarken als `<span class="q hand|vorschlag|claude|regel">` mit Prozent, wenn die Zahl > 0. Marken mit
0 % entfallen. Farben: hand `#15803d`, vorschlag `#6b7280`, claude `#6d28d9`, regel `#b45309` (Mockup).

Darunter, kursiv grau: „Häufigste Schreibweisen: A (n), B (n), C (n)“ (drei), bei Rubriken entfällt sie.

### 4.2 Festgestellt (Variante C)

Zusätzlich ein `<details>` „Woher kommt diese Zahl?“ (standardmäßig **geöffnet**, damit der Klick den
Beleg sofort zeigt) mit:

- Tabelle: Schreibweise | Nennungen bzw. Zeilen | Norm bzw. Klasse | Quelle (Marke), zehn Zeilen aus `top`
  bzw. `schreibweisen`; darunter „alle <n> Schreibweisen in der Suche ›“ als Link auf
  `karte.html?ohdab=<id>` (Norm), `karte.html?eigentuemer=<kanon>` (Eigentümer) oder
  `karte.html?q=<rubrik>` (Rubrik); für Klassen ohne Einzelziel entfällt der Link.
- Belegzeile (Klasse `beleg`): Regel und Tabelle in Worten, z. B. „Stellung nach Berufszählung 1933 / AVG 1911
  (docs/stellung.md). Tabelle: kuratierung/berufe.csv, Spalte stellung.“ Texte je Datenkern als Konstante
  `BELEG` im Modell.
- Bei Eigentümern: „<zeilen> Zeilen ergeben <haeuser> Häuser, weil Spannen einmal je Straßenseite stehen“ und
  Link „Faksimile“ auf die DigiBib-Seite der ersten Zeile (Seite aus dem Eintrag; `faksimileUrl` in popup.js).

Der bisherige Kartenlink („Auf der Karte zeigen“ bei Stadtteilen) bleibt.

### 4.3 Laden und Fehler

Beim ersten Schweben über eine Einheit eines Datenkerns lädt die Seite die passende Herkunftsdatei
(`Lader.herkunft`). Solange sie fehlt, zeigt der Kasten die Zahlen wie heute und darunter „Herkunft wird
geladen …“; nach dem Laden wird der Kasten neu gezeichnet, falls er noch dieselbe Einheit zeigt. Schlägt das
Laden fehl (404, alter Export), bleibt der Kasten ohne Pfad und ohne Fehlermeldung, die Konsole meldet es
einmal. Der Detailkasten wächst durch den Pfad; `detailLage` positioniert wie bisher nach dem Füllen.

## 5. Modell und Tests

- `perspektiven_modell.js`: `herkunftPfad(kontext, herkunft)` (rein, gibt Stufenliste zurück),
  `herkunftTabelle(kontext, herkunft)` (Zeilen der Belegtabelle), `herkunftLink(kontext)` (Karten-URL
  oder null), `BELEG`; `detailText`/`detailTextGruppe` bleiben, `perspektiven.js` setzt Pfad und Tabelle
  darunter. `kontext` = `{ art: "segment"|"kreis"|"einheit"|"regel", daten, id, gruppe }`.
- node: Pfade für alle sechs Fälle aus §4.1 an Fixtures; Marken nur bei > 0; Klassenmischung summiert;
  Tabelle max zehn Zeilen; Link je Art; fehlende Herkunftsdatei → leerer Pfad ohne Fehler.
- pytest: `baue_herkunft` an einer kleinen Adressmenge (Summen je Klasse = Ebenen-Summen; `top` sortiert
  und begrenzt; Krupp-Fixture: Zeilen < Häuser mit Spannen); `schreibe_paket` schreibt die sieben Dateien.
- Sichtprüfung im Browser (Schweben, Klick, Touch-Weg ohne Schweben).

## 6. Doku

`docs/perspektiven.md`: Abschnitt „Herkunftspfad“ (Dateien, Kontextarten, Beleg-Texte). README:
Ausgabetabelle um `herkunft/*.json`. Journal-Eintrag.
