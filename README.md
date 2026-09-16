# Adressbuch Essen 1936 — Datenpipeline (v2)

Erzeugt aus dem DES-Export des Essener Adreßbuchs 1936 (`data/essen1936.csv`, Tab-getrennt)
eine geokodierte Tabelle mit ausgewiesener Präzisionsstufe je Eintrag.
Leitprinzip: Präzision vor Vollständigkeit — nichts Falsches als richtig, Unsicheres wird gekennzeichnet.

## Voraussetzungen
- Python ≥ 3.12, `pip install -e .[test]`
- Lokale Nominatim-Instanz (Docker `mediagis/nominatim:4.4`, NRW-Extrakt).
  Adresse über die Umgebungsvariable `NOMINATIM_URL`, Standard `http://localhost:8080`.
- Straßendatensatz `essener-strassen` (Umgebungsvariable `ESSENER_STRASSEN_DIR`,
  Standard `../essener-strassen/daten`; erwartet `strassen.csv`, `konkordanz_1936.csv`, `namen.csv`)

## Aufruf
```
python3 pipeline/01_einlesen.py
python3 pipeline/02_adresse_parsen.py
python3 pipeline/03_strasse_aufloesen.py
python3 pipeline/04_geokodieren.py     # ≈ 7 Minuten mit leerem Cache
python3 pipeline/05_bericht.py
```
Ausgaben liegen in `build/` (löschbar, nicht im Git). Vom Menschen gepflegte Tabellen in `kuratierung/`.

Tests: `python3 -m pytest -q` (keine Netzverbindung nötig).
Lokale Vorschau der Ergebnisse: `python3 werkzeuge/serve.py` (statt `python3 -m http.server`,
weil PMTiles Range-Requests braucht und der Server die geprüfte Stichprobe zurückschreibt).
Kontrollkarte: `werkzeuge/kontrollkarte.html`; Prüfwerkzeug für die manuelle Stichprobe:
`werkzeuge/pruefung.html` (Anleitung in `docs/stichprobe.md`); Sichtung offener Straßen am
Stadtplan 1935: `werkzeuge/sichtung.html` nach `python3 werkzeuge/sichtung_liste.py` (Anleitung in `docs/sichtung.md`).

## Vokabulare der Ausgabespalten

`stufe` — Präzision der Verortung einer Adresse:

| Wert | Bedeutung |
|---|---|
| `haus` | Punkt auf der Hausnummer |
| `strasse` | Punkt auf der Straße (Hausnummer nicht gefunden, nicht vorhanden oder nicht verlässlich; `grund` sagt, warum) |
| `landmarke` | kuratierter Punkt aus `kuratierung/landmarken.csv` |
| `offen` | keine Verortung; `grund` sagt, warum |

`grund` — bei `stufe=offen`: `strasse_offen` (Straße nicht aufgelöst),
`ohne_nummer`, `kein_treffer`, `mehrdeutig_strasse` (mehrere gleichnamige Straßen ohne
unterscheidenden Stadtteil), `stadtteil_widerspruch`, `fehler` (Nominatim-Anfrage
fehlgeschlagen; ein erneuter Lauf holt sie nach). Bei `stufe=strasse` zusätzlich
`nummer_unsicher` (kuratierter Hausnummernbereich, dessen Nummern heute nicht mehr gelten —
die Hausebene wird bewusst nicht gesucht) und `stadtplan_1935` (Punkt vom Menschen am Stadtplan 1935
gesetzt, `kuratierung/strassen_1935.csv`; keine heutige Straße, kein Nominatim).

`herkunft` — woher die heutige Straße kommt:

| Wert | Bedeutung |
|---|---|
| `kuratiert` | vom Menschen belegt (`kuratierung/strassen_zuordnung.csv`) |
| `stadtplan_1935` | vom Menschen am Stadtplan 1935 verortet, keine heutige Straße (`kuratierung/strassen_1935.csv`) |
| `heutig` | Name gilt heute und galt 1936 für genau diese Straße |
| `konkordanz` | Umbenennung nach `konkordanz_1936.csv` |
| `stadium` | anderes Namensstadium aus `namen.csv` |
| `offen` | keine Kandidaten |

`zeitlich_abweichend=ja` — der gewählte Namensstand ist für 1936 nicht datiert belegt
(undatiertes Stadium oder nur Stadien außerhalb des Fensters 1930–1937).

Reihenfolge der Automatik: Kuratierung (Zuordnung, dann Stadtplan-Punkt), dann Vorort-Filter (Vorort bzw. Kernstadt), dann die
Zeitstufung nur unter den räumlich passenden Kandidaten — 1936 belegt oder undatiert, sonst
weites Fenster 1930–1937, sonst außerhalb datiert. Die Stufen verschmelzen nicht zu Homonymen.
Die Stufe „außerhalb“ greift automatisch nur, wenn der Name heute gilt und Dickhoff für 1936 keinen
anderen Namen derselben Straße belegt (Dickhoffs Kette ist dann lückenhaft, nicht die Straße falsch);
erloschene Namen bleiben `name_erloschen`, wiederverwendete `name_spaeter` — beide werden kuratiert.
Der Vorort-Filter steht vor der Zeitstufung, weil Dickhoffs Ketten einen Namen bei Teil-
Umbenennungen für die ganze Straße beenden (Altendorfer Straße „bis 1933“); sonst verdrängt
eine 1936 gültige Namensschwester im falschen Ort den richtigen Kandidaten.

`mehrdeutig=ja` mit `grund_mehrdeutig` — es blieb mehr als ein Kandidat übrig oder keiner passte:

| Wert | Bedeutung |
|---|---|
| `homonym_1936` | mehrere verschiedene Straßen trugen 1936 diesen Namen |
| `konkordanz_nicht_eindeutig` | alle Kandidaten stammen aus Konkordanzzeilen mit `eindeutig=nein` |
| `vorort_widerspruch` | Kandidaten vorhanden, aber keiner passt zum Vorort bzw. zur Kernstadt |
| `name_erloschen` | der Name gehört bei Dickhoff nur Straßen, die ihn schon vor 1930 verloren haben und heute anders heißen — nicht automatisch vergeben, weil Dickhoff keine verschwundenen Straßen führt (Kandidat steht in `kandidaten` als Vorschlag) |
| `name_spaeter` | der Name gilt heute, Dickhoff datiert ihn aber erst nach 1937 und belegt für 1936 einen *anderen* Namen derselben Straße (meist ein später umbenannter Abschnitt) — die Straße des Buches lag woanders, der Name wurde wiederverwendet; nicht automatisch vergeben (Stichprobe r6). Beginnt Dickhoffs Kette nur später, bleibt die Automatik mit `zeitlich_abweichend=ja` |

`vorort_angenommen=ja` — Teil II/III ohne Vorortangabe: unter sonst gleichwertigen Kandidaten
hat die Kernstadt entschieden. Ein leerer Vorort bedeutet dort zu 95 % Kernstadt (Kreuztabelle
2026-09-15), ist aber kein Beleg; alle Kandidaten bleiben in `kandidaten` notiert.

`nummer_unsicher=ja` — die Zeile fiel in einen kuratierten Hausnummernbereich, dessen Nummern
heute nicht mehr gelten (Straße nach 1936 geteilt, zusammengelegt oder neu gezählt); verortet
wird nur die Straße.

`schreibvariante=ja` mit `strasse_angeglichen` — der Buchname fand keinen Kandidaten und wurde über
gestufte Schlüsselformen (ß/ss; Leerzeichen, Bindestrich, Punkt; ck/k, th/t, dt/t, ph/f, c/k, y/i, ie/i;
Umlaut-Umschrift, ei/ey; Endung -ener/-er, Genitiv-s, Doppelbuchstaben) an genau einen Dickhoff-Namen
angeglichen (`strasse_angeglichen`, normiert), der dann die normale Kette durchläuft. Mehrere Namen mit
gleichem Schlüssel → keine Angleichung. Der Buchname bleibt in `strasse_roh` erhalten; Karte und
Prüfwerkzeug zeigen beide Schreibweisen (Regelliste: `pipeline/lib/normalisierung.py`, SCHLUESSELSTUFEN).

`kuratierung/strassen_zuordnung.csv` — vom Menschen belegte Straßenzuordnung, schlägt alles:

| Spalte | Bedeutung |
|---|---|
| `strasse_roh_norm` | normierter Name von 1936 (`norm_strasse`) |
| `vorort` | Vorort des Eintrags; `Kernstadt` = nur Einträge ohne Vorort; leer = Platzhalter für alle |
| `strasse_heute`, `schl_nr` | Ziel (Dickhoff-Schlüssel) |
| `hausnr_von`, `hausnr_bis` | optionaler Hausnummernbereich (je offen, wenn leer); ohne passende Nummer greift die Automatik |
| `nummer_unsicher` | `ja` → nur Straßenebene (s. o.) |
| `beleg`, `bearbeiter`, `datum` | Quelle der Entscheidung, kurz und nachprüfbar |

`kuratierung/strassen_1935.csv` — Straßen, die kein Dickhoff-Name trifft (verschwunden oder Kette lückenhaft),
vom Menschen am georeferenzierten Stadtplan 1935 verortet (Werkzeug `werkzeuge/sichtung.html`):

| Spalte | Bedeutung |
|---|---|
| `strasse_roh_norm`, `vorort` | normierter Buchname und Buchvorort; `Kernstadt` = Einträge ohne Vorort |
| `befund` | `punkt` (verortet) oder `nicht_gefunden` (gesichtet, im Plan nicht auffindbar — verortet nichts) |
| `lat`, `lon` | Straßenmitte am Stadtplan 1935 (Stufe `strasse`, Grund `stadtplan_1935`) |
| `name_im_plan`, `stadtteil` | Schreibweise im Plan; heutiger Stadtteil (Vorschlag aus OSM, geprüft) |
| `bemerkung`, `bearbeiter`, `datum` | Beleg und Nachvollziehbarkeit |

Entscheidungen zu einzelnen Straßen: [`docs/entscheidungen_strassen.md`](docs/entscheidungen_strassen.md).

`build/strassen_vorschlaege.csv` ist die Arbeitsliste für die Kuratierung: alle offenen und
mehrdeutigen Paare mit unscharfen Kandidaten, nach Zeilenzahl sortiert.

## Dokumentation

Spezifikation: Obsidian-Vault `~/Projekte/obsidian-chris`, Ordner
`10-Projekte/adressbuch-essen-1936-v2/` (`Spec-1-Datenpipeline.md`) — verbindlich.
Plan und Protokolle: `docs/superpowers/`.
