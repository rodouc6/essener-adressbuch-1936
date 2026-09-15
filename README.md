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
`werkzeuge/pruefung.html` (Anleitung in `docs/stichprobe.md`).

## Vokabulare der Ausgabespalten

`stufe` — Präzision der Verortung einer Adresse:

| Wert | Bedeutung |
|---|---|
| `haus` | Punkt auf der Hausnummer |
| `strasse` | Punkt auf der Straße (Hausnummer nicht gefunden oder nicht vorhanden) |
| `landmarke` | kuratierter Punkt aus `kuratierung/landmarken.csv` |
| `offen` | keine Verortung; `grund` sagt, warum |

`grund` — nur bei `stufe=offen` gefüllt: `strasse_offen` (Straße nicht aufgelöst),
`ohne_nummer`, `kein_treffer`, `mehrdeutig_strasse` (mehrere gleichnamige Straßen ohne
unterscheidenden Stadtteil), `stadtteil_widerspruch`, `fehler` (Nominatim-Anfrage
fehlgeschlagen; ein erneuter Lauf holt sie nach).

`herkunft` — woher die heutige Straße kommt:

| Wert | Bedeutung |
|---|---|
| `kuratiert` | vom Menschen belegt (`kuratierung/strassen_zuordnung.csv`) |
| `heutig` | Name gilt heute und galt 1936 für genau diese Straße |
| `konkordanz` | Umbenennung nach `konkordanz_1936.csv` |
| `stadium` | anderes Namensstadium aus `namen.csv` |
| `offen` | keine Kandidaten |

`zeitlich_abweichend=ja` — der gewählte Namensstand ist für 1936 nicht datiert belegt
(undatiertes Stadium oder nur Stadien außerhalb des Fensters 1930–1937).

`mehrdeutig=ja` mit `grund_mehrdeutig` — es blieb mehr als ein Kandidat übrig oder keiner passte:

| Wert | Bedeutung |
|---|---|
| `homonym_1936` | mehrere verschiedene Straßen trugen 1936 diesen Namen |
| `konkordanz_nicht_eindeutig` | alle Kandidaten stammen aus Konkordanzzeilen mit `eindeutig=nein` |
| `vorort_widerspruch` | Kandidaten vorhanden, aber keiner passt zum Vorort bzw. zur Kernstadt |

`build/strassen_vorschlaege.csv` ist die Arbeitsliste für die Kuratierung: alle offenen und
mehrdeutigen Paare mit unscharfen Kandidaten, nach Zeilenzahl sortiert.

## Dokumentation

Spezifikation: Obsidian-Vault `~/Projekte/obsidian-chris`, Ordner
`10-Projekte/adressbuch-essen-1936-v2/` (`Spec-1-Datenpipeline.md`) — verbindlich.
Plan und Protokolle: `docs/superpowers/`.
