# Schlaglichter, Schritt 1: Kapitel 0 „Die Datenbasis“, Trichter-Form, Ausschluss-Benennung, Kapiteltexte — Entwurf

Stand 2026-09-27. Beschlossen im Brainstorming (Zuschnitt 3, Zielgruppe „beides in Schichten“).
Baut auf `2026-09-24-perspektiven-werkstatt-design.md` §6 (Perspektiven) auf; Seite heißt nach außen
„Schlaglichter“ (`site/schlaglichter.html`), Codenamen bleiben `perspektiven`.

## 1. Ziel

Besucher sollen bei jedem Schlaglicht sehen, welchen Anteil des Gesamtbestands die gezeigten Zahlen
abdecken, wie die Daten vom gedruckten Buch bis zur Karte gekommen sind und was das graue Segment
„ausgeschlossen“ in jedem Kapitel konkret bedeutet. Außerdem bekommen alle Kapitel Texte (Entwurf
durch Claude, Handprüfung durch den Projektleiter), damit 5b inhaltlich abgeschlossen werden kann.

Zielgruppe und Ton (Entscheidung 2026-09-27): erzählerischer Haupttext für interessierte Laien,
Heimat- und Familienforscher (60 bis 100 Wörter je Schritt, Fachbegriffe erklärt); Methode und Belege
(Berufszählung 1933, AVG 1911, Dickhoff 2015, Huske) nur im Grenzen-Abschnitt und in Kapitel 0.

Nicht Ziel: Werkstatt (5c), Herkunftspfad im Detailkasten (Schritt 2 der Liste vom 27.9.), Karten-UI,
Bergbau-Kapitel, Seitenbilder der Vorlage (Bildrechte der DigiBib ungeklärt, nur Link).

## 2. Kapitel 0 „Die Datenbasis“

Datei `kuratierung/perspektiven/datenbasis.json`, `id: "datenbasis"`, `reihenfolge: 0`, Titel
„Die Datenbasis“, Untertitel „Vom Adreßbuch 1936 zur Karte“. Fünf Schritte, alle mit `form: trichter`:

| Schritt-id | Inhalt des Textes | Trichter |
|---|---|---|
| `vorlage` | Essener Adreßbuch 1936, Scherl, 1.198 Seiten, Beilage Stadtplan; Standorte Stadtarchiv Essen, DNB Leipzig; Teile I Einwohner, II Häuser/Eigentümer, III Gewerbe kartiert; IV Behörden und W Innungen ohne Adressen, nicht kartiert; Erfassung durch das DES-Projekt des Vereins für Computergenealogie (abgeschlossen 2020) | Zeilen je Teil: I, II, III (Stufen `eintraege_I`, `eintraege_II`, `eintraege_III`, erste Stufe = Summe `eintraege`) |
| `weg` | Digitalisat in der DigiBib → Transkription im DES → Tabelle → Pipeline: Adresse zerlegen, Straße über Dickhoff 2015 und Stadtplan 1935 auflösen, Hausnummer über Nominatim, Präzisionsstufe je Zeile; Regel „lieber nicht verortet als falsch“ | `eintraege` → `verortet` → `adressen`; Segmente der Stufe `verortet`: `stufe_haus`, `stufe_strasse`, `stufe_stadtplan` |
| `besitz` | Teil II nennt je Haus den Eigentümer; Schreibweisen zusammengeführt, Klassen von Hand (Körperschaften ab fünf Häusern, größte Privatpersonen), Rest per Regel „Person ohne Firmenname → Privatperson“; Hausnummernspannen | `adressen` → `besitz_geprueft`; Segmente: `besitz_hand`, `besitz_regel` (schraffiert) |
| `stellung` | Berufsangaben in Teil I, Abkürzungskatalog, OhdAB-Zuordnung von Hand, daraus Stellung nach zeitgenössischer Rechtslage; Vorschläge der Automatik gekennzeichnet | `teil_i_n` → `beruf_geprueft_n`; Segmente: `stellung_hand_n`, `stellung_vorschlag_n` (schraffiert), `stellung_unbestimmt_n` (grau) |
| `gewerbe` | Teil III Branchenverzeichnis, Rubriken → Branche und Betriebsform; von Hand, nach dokumentierten Prinzipien, per Regel | `betriebe_n` → Segmente: `gewerbe_hand_n`, `gewerbe_claude_n` (schraffiert), `gewerbe_regel_n` (schraffiert, hellere Stufe) |

`grenzen`: H–J-Lücke (Seiten 186–258, ≈23.000 Personen), Erhebungsstand im Lauf des Jahres 1936,
Lizenz der Transkription noch offen (Anfrage an CompGen), Stadtteilgrenzen heutig (OSM, ODbL),
Straßenlinien heutige Führung. `quellen`: Adreßbuch (Bibliografie), DES-Projekt essen1936, DigiBib,
Dickhoff 2015 / Zenodo-DOI, OhdAB, Stadtplan 1935 der Stadt Essen.

`freigegeben: false` bis zur Handprüfung; Kapitel 0 erscheint im Inhaltsverzeichnis an erster Stelle.

## 3. Form `trichter`

### 3.1 Ansicht im Kapitel-JSON

```json
{"daten": "kennzahlen", "form": "trichter",
 "stufen": [
   {"name": "Zeilen der Vorlage (Teile I–III)", "aus": "eintraege", "farbe": "#94a3b8"},
   {"name": "verortet", "aus": "verortet", "farbe": "#1d4ed8",
    "segmente": [{"name": "hausgenau", "aus": "stufe_haus", "farbe": "#1d4ed8"},
                 {"name": "straßengenau", "aus": "stufe_strasse", "farbe": "#60a5fa"},
                 {"name": "Stadtplan 1935", "aus": "stufe_stadtplan", "farbe": "#93c5fd"}]},
   {"name": "Adressen auf der Karte", "aus": "adressen", "farbe": "#1d4ed8"}
 ],
 "erklaerungen": {"verortet": "Zeilen, deren Straße und Hausnummer …", "adressen": "…"}}
```

- `daten: "kennzahlen"` ist nur mit `form: "trichter"` zulässig und umgekehrt (`pruefe_ansicht`).
- Für diese Form gelten eigene Pflichtfelder: `daten`, `form`, `stufen`; `ebene`, `gruppen`,
  `kaufleute`, `unsicher`, `mass`, `bezug`, `min_n`, `filter`, `karte` entfallen.
- Jede Stufe: `name`, `aus` (Schlüssel in `kennzahlen.json`), `farbe`; optional `segmente` (gleiche
  Felder, ohne weitere Verschachtelung) und `muster: "schraffur"` je Segment für nicht handgeprüfte
  Anteile. `erklaerungen` (optional) ordnet Stufen- und Segmentschlüsseln einen Erklärtext für den
  Detailkasten zu.
- `pruefe_ansicht` prüft: Stufen nicht leer, Namen eindeutig (Stufen und Segmente zusammen), `aus`
  nicht leer, Farbe vorhanden, `muster` nur `schraffur` oder fehlend. Ob ein `aus`-Schlüssel in
  `kennzahlen.json` existiert, prüft der Export (`schreibe_paket` kennt die Kennzahlen): fehlender
  Schlüssel → `ValueError`, damit kein leerer Balken durchrutscht.

### 3.2 Rendering (`site/js/formen/trichter.js`)

Schnittstelle wie die anderen Formen: `zeige(ansicht, daten, optionen) → { svg, legende, zahlen }`,
wobei `daten` hier `{ kennzahlen }` ist. Stufen als horizontale Balken untereinander, Breite
proportional zum Wert der ersten Stufe (Trichter von oben nach unten), linksbündig. Beschriftung
links der Stufenname, rechts „x von y (z %)“ mit y = erste Stufe; bei der ersten Stufe nur „x“.
Segmente teilen den Balken ihrer Stufe, Schraffur als SVG-`pattern` (diagonal, Farbe des Segments
auf Weiß) für `muster: "schraffur"`. Jede Stufe und jedes Segment ist eine Einheit (`class="einheit"`,
`data-id` = `aus`-Schlüssel), damit `detailZustand` und die Hervorhebungs-CSS unverändert greifen.
Legende: Segmentnamen mit Farbe, Schraffur als „nicht von Hand geprüft“. `zahlen`: `N` = erste
Stufe, `n_aus` = 0, `hinweis` = leer (die Zahlenzeile zeigt nur die Nennerangabe „Stand {stand}“).
Detailkasten: Name, Wert, Anteil an der ersten Stufe, Erklärtext aus `erklaerungen`; **kein**
Kartenlink und kein Werkstattlink, weil Kennzahlen keine Einheiten der Karte sind
(`detailText` bekommt dafür ein Flag `ohneKarte`).

### 3.3 Anbindung in der Seite

`perspektiven.js` prüft vor `normalisiere(ansicht)` auf `form === "trichter"` und geht dann direkt an
`trichter.zeige` mit den geladenen Kennzahlen (die Seite lädt `kennzahlen.json` bereits für die
Platzhalter). `formFuer` liefert `"trichter"` für diese Form. Links „Auf der Karte öffnen“ und „In der
Werkstatt öffnen“ werden für Trichter-Schritte nicht gerendert. Übergang zwischen zwei
Trichter-Schritten: harter Wechsel (Cross-Fade wie bisher), keine Kreisanimation.

### 3.4 Kennzahlen (`baue_kennzahlen`, `pipeline/lib/karte_export.py`)

Neue absolute Felder in `site/daten/kennzahlen.json` (bestehende bleiben unverändert):

| Feld | Definition |
|---|---|
| `eintraege` | Summe der Zeilen der Teile I–III |
| `eintraege_I`, `eintraege_II`, `eintraege_III` | wie `eintraege_je_teil`, flach für `aus` |
| `stufe_haus`, `stufe_strasse`, `stufe_stadtplan`, `stufe_offen` | Zeilen je Präzisionsstufe (absolut; `stufen` bleibt in Prozent) |
| `besitz_hand` | `besitz_geprueft − besitz_regel` |
| `teil_i_n` | verortete Teil-I-Einträge (bisheriger Nenner von `berufe_geprueft`) |
| `beruf_geprueft_n` | davon mit geprüftem Beruf |
| `stellung_hand_n`, `stellung_vorschlag_n`, `stellung_unbestimmt_n` | absolute Zähler der drei disjunkten Anteile (Summe = `teil_i_n`) |
| `betriebe_n` | verortete Teil-III-Einträge mit Gewerbedaten |
| `gewerbe_hand_n`, `gewerbe_claude_n`, `gewerbe_regel_n` | absolute Zähler (Summe = `betriebe_n`) |

Test: die Summen stimmen (`stellung_*_n` = `teil_i_n`, `gewerbe_*_n` = `betriebe_n`,
`stufe_*` = `eintraege`, `besitz_hand + besitz_regel = besitz_geprueft`).

## 4. Datenbasis-Zeile je Fachkapitel

Neues Kapitelfeld `datenbasis` (str, Pflicht für Kapitel mit `daten ≠ kennzahlen`, für Kapitel 0 leer
erlaubt): Text mit Platzhaltern wie in `grenzen`, z. B. „{besitz_geprueft} von {adressen} Adressen
tragen eine Besitzklasse ({besitz_geprueft_prozent} %), davon {besitz_regel} nur per Regel.“ Die
Seite rendert ihn als Unterzeile unter Titel und Untertitel, gefolgt vom Link „Datenbasis ›“ auf
`#datenbasis-<schritt>` (Feld `datenbasis_schritt`, str, Schritt-id in Kapitel 0). `PROZENT_BASIS`
wird um `besitz_hand` erweitert; für Stellung und Gewerbe sind die Prozentwerte schon Kennzahlen.

## 5. Ausschluss-Segment benennen

Neues Kapitelfeld `ausschluss` (str, Pflicht für Fachkapitel): kurzer Text, der Legende, Balken-Hover
und Detailkasten statt des generischen „unbestimmt/ungeprüft“ zeigen. Vorgabe:

| Kapitel | `ausschluss` |
|---|---|
| wohneigentum | ohne Eigentümerangabe oder Eigentümer nicht zugeordnet |
| stellung | Beruf ungeprüft oder Stellung unbestimmt |
| gewerbe | Rubrik ohne Branche |

`balken.zeige` bekommt `optionen.ausschlussText`; `detailTextGruppe` und `hinweisText` nutzen ihn,
wenn gesetzt, sonst den bisherigen Text (Karte und Werkstatt bleiben unverändert).

## 6. Wortlaut „geprüft“ vs. „klassifiziert“

- Beim Besitz heißt der Anteil mit Klasse künftig „mit Besitzklasse“ oder „klassifiziert“; „von Hand
  geprüft“ nur für `besitz_hand`. Betroffen: Grenzen-Texte, Balken-Hover („x per Regel“ bleibt),
  Über-Seite, README-Absatz zu den Kennzahlen. Der Schlüssel `besitz_geprueft` bleibt (Kompatibilität),
  die Beschriftung ändert sich.
- Über-Seite: Satz „Geplant: ein Sozialscore je Straße aus den Berufen“ entfällt (Entscheidung
  2026-09-24: Stellung statt Score); Berufszahlen (1.537 / 97,8 %) werden gegen `kennzahlen.json`
  geprüft und mit Nenner benannt oder aus der Kennzahl gefüllt.

## 7. Texte der Kapitel 0 bis 3

Claude entwirft alle Texte (`einleitung`, `text` je Schritt, `beschreibung`, `grenzen`, `datenbasis`)
direkt in den JSON-Dateien, nach dem Ton aus §1. Jeder Zahlenwert im Text kommt aus einem Platzhalter
oder wird gegen `site/daten/ebenen/stadtteile.json` bzw. `kennzahlen.json` nachgerechnet und im
Commit-Text belegt (Lehre vom 26.9.: Zahlen gegen die Quelle prüfen). `hervorheben` bleibt auf den
geprüften Spitzenreitern. Der Projektleiter prüft und setzt `freigegeben: true` selbst.

## 8. Tests

- pytest `tests/test_perspektiven.py`: Trichter-Ansicht gültig; `daten: kennzahlen` ohne `trichter`
  und `trichter` ohne `kennzahlen` sind Fehler; Stufenname doppelt, `muster` unbekannt; Fachkapitel
  ohne `ausschluss`/`datenbasis` ist Fehler; Export bricht bei unbekanntem `aus`-Schlüssel ab.
- pytest `tests/test_karte_export.py`: neue Kennzahlen und ihre Summen.
- node `site/tests/formen.test.js`: Trichter — Breiten proportional, Segmente summieren zur Stufe,
  Schraffur-Pattern vorhanden, `data-id` je Einheit, Legende, `zahlen.N`.
- node `site/tests/perspektiven.test.js`: `formFuer` für Trichter; `detailText` ohne Kartenlink;
  `fuellePlatzhalter` mit `besitz_hand_prozent`; `ausschlussText` in `detailTextGruppe`.
- Sichtprüfung im Browser durch den Projektleiter (`?vorschau=1`).

## 9. Doku

`docs/perspektiven.md`: Schema-Erweiterung (Trichter, `datenbasis`, `ausschluss`), neue Kennzahlen,
Kapitel 0. README: Kennzahlen-Tabelle ergänzen. Journal-Eintrag.
