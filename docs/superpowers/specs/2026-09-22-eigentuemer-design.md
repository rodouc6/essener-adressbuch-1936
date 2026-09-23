# Teilprojekt 3: Eigentümer-Kuratierung und Besitz-Ebene — Entwurf

Stand: 2026-09-22. Ergebnis des Brainstormings mit dem Projektleiter. Anforderung: Vault
`Anforderungen.md` E4 (Besitzverhältnisse). Grundsatz: Precision first — die Automatik führt
nur eindeutig Belegbares zusammen, Unsicheres entscheidet der Mensch, Ungeprüftes erscheint
auf der Karte nie als gesichert.

## 1. Ziel und Abgrenzung

Die Eigentümerangaben aus Teil II (Häuser und Eigentümer) werden zu kanonischen Eigentümern
mit Kategorie zusammengeführt und als Besitz-Ebene auf der Karte gezeigt. Dafür entstehen ein
Clustering-Skript (Vorschläge), ein Browser-Werkzeug im Dev-Server (Entscheidungen) und der
Export in Stufe 06 (Thema, Hausansicht, Suche).

Datenlage (`build/eintraege.csv`, Teil II, 33.467 Zeilen): Der Eigentümername steht bei
Körperschaften in `Firmenname` (6.655 Zeilen, 2.261 Schreibweisen), bei Personen in
`lastname`/`firstname` (26.805 Zeilen, 18.781 Namen); die Spalte `Eigentümer` trägt nur die
Rolle. Krupp allein hat 72 Schreibweisen mit 790 Häusern, davon 63 Schreibweisen mit weniger
als zehn Vorkommen.

Nicht Teil dieses Teilprojekts: Konzernzuordnung (Gewerkschaft → Mutterkonzern), Trennung
gleichnamiger Personen, Clustering der Firmennamen aus Teil I/III (v1-Versuch unter
`AdressbuchEssen1936/v2/analyse/koerperschaften`, dessen Abkürzungskatalog übernommen wird),
Straßendarstellung (bleibt Teilprojekt 4), GND-Anreicherung.

## 2. Entscheidungen aus dem Brainstorming

| Frage | Entscheidung |
|---|---|
| Umfang | Nur Eigentümer aus Teil II; Firmennamen aller Abschnitte später mit demselben Werkzeug |
| Untergrenze | Auf dem **Cluster** nach Automatik, nicht auf der Schreibweise: geprüft werden Cluster und Personen mit ≥ 5 Häusern (Parameter `--min-haeuser`); Rest bleibt „ungeprüft“ |
| Ergebnis | Kanonischer Name **und** Kategorie aus fester Liste; keine Konzernzuordnung |
| Werkzeug | Browser-Seite über `werkzeuge/serve.py` (kein marimo, kein Excel); Entscheidungen als CSV im Repo |
| Personen | Nicht geclustert; ab 5 Häusern in der Prüfliste mit Kategorie `privatperson` vorbelegt |

## 3. Datenmodell

### 3.1 `build/eigentuemer_vorschlag.csv` (erzeugt, nicht versioniert)

Eine Zeile je Schreibweise. Spalten: `schreibweise, art, anzahl, cluster_id, cluster_name,
aehnlichkeit, vorschlag_fuer, pruefpflichtig`.

- `art` ∈ `koerperschaft | person`; Personen-Schreibweise ist „Nachname, Vorname“.
- `cluster_id` = stabiler Hash des Vergleichsschlüssels des größten Mitglieds;
  `cluster_name` = Auto-Name (§4.4); `aehnlichkeit` = niedrigste paarweise Ähnlichkeit im
  Cluster (1,0 bei exakt gleichem Schlüssel).
- `vorschlag_fuer` = `cluster_id` eines anderen Clusters, zu dem die Schreibweise mit
  Ähnlichkeit 0,75–0,92 passt (leer, wenn kein Grenzfall); das Werkzeug zeigt sie dort als
  Vorschlag „gehört vielleicht dazu“.
- `pruefpflichtig` = `ja`, wenn der Cluster (bzw. die Person) ≥ `--min-haeuser` Häuser hat.

### 3.2 `build/eigentuemer_belege.json` (erzeugt, nicht versioniert)

Je Schreibweise die Liste ihrer Häuser: `{schreibweise: [{id, adresse, stadtteil, verwalter,
seite, lat, lon, stufe}]}`. `verwalter` = Spalte `Verwalter`, `seite` = Teil-II-Seite für den
DigiBib-Link. Das Werkzeug lädt diese Datei statt der 88-MB-Pipeline-Ausgabe.

### 3.3 `kuratierung/eigentuemer.csv` (versioniert, Entscheidungen)

Eine Zeile je **Schreibweise** (Abspalten und Zusammenführen sind dieselbe Operation: die
Schreibweise zeigt auf einen anderen Eigentümer). Spalten:

`schreibweise, art, eigentuemer, kategorie, geprueft, bearbeiter, datum, hinweis`

- Schlüssel: `schreibweise` (getrimmt, sonst die rohe Buchschreibung; bei Personen
  „Nachname, Vorname“). Korrekturen aus `zeilenkorrekturen.csv` greifen vorher.
- `eigentuemer`: kanonischer, lesbarer Name; gilt für alle Schreibweisen mit demselben Wert.
- `kategorie` ∈ `stadt_staat | bergbau | industrie | genossenschaft_siedlung |
  kirche_stiftung | bank_versicherung | privatperson | sonstige`; hängt am Eigentümer, das
  Werkzeug schreibt sie auf alle seine Schreibweisen. Anzeigenamen: Stadt/Staat/Reich ·
  Bergbau · Industrie · Genossenschaft/Siedlung · Kirche/Stiftung · Bank/Versicherung ·
  Privatperson · Sonstige.
- `geprueft` = `ja` sperrt die Zeile: die Automatik überschreibt sie nie (wie
  `status_geprueft` bei `zechen.csv`). Alle anderen Zeilen dürfen bei jedem Lauf neu
  vorgeschlagen werden.
- `bearbeiter`/`datum` setzt der Server beim Speichern (`christos`, ISO-Datum); die Automatik
  schreibt `eigentuemer_cluster`. **Nachtrag 2026-09-22:** Körperschaften bekommen bei jedem
  Lauf eine Zeile, auch unterhalb von `--min-haeuser` — nur Personen legt die Automatik erst
  ab der Prüfpflicht-Untergrenze an; kleinere Personen-Schreibweisen erscheinen also gar nicht
  in der Datei, statt als „nicht prüfpflichtig“ mitgeführt zu werden.

### 3.4 `kuratierung/eigentuemer_abkuerzungen.csv` (versioniert)

Abkürzungskatalog der Normalisierung: `kurz, lang, kontext, beleg`. `kontext` leer = immer;
`firmenwort` = nur, wenn ein Firmenwort folgt (für `Ver.`/`Verein.` → „vereinigte“). Startbestand
aus dem v1-Katalog, von Hand übernommen.

## 4. Automatik: `werkzeuge/eigentuemer_cluster.py`

Aufruf: `python3 werkzeuge/eigentuemer_cluster.py [--min-haeuser 5]`. Liest
`build/eintraege.csv` (Teil II), schreibt §3.1 und §3.2 und legt in §3.3 fehlende
Schreibweisen an (Vorschlagswerte, `geprueft` leer); vorhandene Zeilen mit `geprueft=ja`
bleiben unverändert, ungeprüfte werden auf den neuen Vorschlag gesetzt, wenn sich dieser
geändert hat. **Nachtrag 2026-09-22:** die Sperre gilt ebenso für Zeilen mit
`bearbeiter ≠ eigentuemer_cluster` (vom Menschen angefasst, aber noch nicht `geprueft=ja`) —
nur Zeilen, die zuletzt von der Automatik selbst stammen, dürfen erneut automatisch
vorgeschlagen werden (`pipeline/lib/eigentuemer.gesperrt()`). Schreibweisen, die in der Quelle
nicht mehr vorkommen, bleiben stehen und werden im Werkzeug als „verwaist“ markiert.

### 4.1 Trennung Körperschaft/Person

`Firmenname` gefüllt → Körperschaft, sonst `lastname`/`firstname` → Person. Kein
Klassifikator (die Teil-II-Spalte ist sauber). Personen werden nicht geclustert, nur gezählt.

### 4.2 Normalisierung zum Vergleichsschlüssel

1. Kleinschreibung, Unicode-NFKC, mehrfache Leerzeichen.
2. Rechtsformen vereinheitlichen: `A.G.`, `A. G.`, `A.-G.`, `AG.`, `A. -G.` → `ag`; ebenso
   `gmbh`, `egmbh` (`e.G.m.b.H.`, `e. G. m. b. H.`), `ev`, `kg`, `ohg`; Kommas und Punkte
   davor entfallen.
3. Abkürzungskatalog (§3.4) tokenweise; `kontext=firmenwort` nur vor einem Wort aus der
   Firmenwortliste (stahlwerke, bergwerke, bergwerks, hütten, glanzstoff, kesselwerke …, im
   Katalog als eigene Zeilen `art=firmenwort`).
4. Kompositum-Angleich: Leerzeichen zwischen zwei Firmenwörtern entfernen
   („bergwerks verein“ → „bergwerksverein“).
5. Restliche Interpunktion entfernen.

### 4.3 Clustering

- Exakt gleicher Schlüssel → ein Cluster (Ähnlichkeit 1,0).
- Blocking nach erstem signifikantem Token (nicht Rechtsform, nicht Stoppwort); innerhalb
  eines Blocks paarweise Token-Set-Ratio (rapidfuzz `token_set_ratio`, 0–1; rapidfuzz wird Abhängigkeit in `pyproject.toml`).
  **Nachtrag 2026-09-22:** tatsächlich `token_sort_ratio`, nicht `token_set_ratio` — bei Teilmengen
  („… Schacht 3“ vs. der Zeche selbst) liefert `token_set_ratio` 1,0 und würde Teilanlagen in die
  Zeche mergen.
- Complete-Linkage: zwei Cluster verschmelzen nur, wenn **alle** Paare ≥ 0,92 **und** dieselben
  Zahl-Token tragen (Nachtrag 2026-09-22, Fund F3: Zahl-Token = Ziffernfolgen und römisch
  ii/iii/iv; unterscheiden sie sich, z. B. „Adolf-Hitler-Straße 19“ vs. „… 81“ mit Ähnlichkeit
  0,95, oder „Ev. Schule“ vs. „Ev. Schule II“, blockiert das den Merge und das Paar wird
  stattdessen zum Vorschlag, auch oberhalb von 0,92).
- Paare mit 0,75 ≤ Ähnlichkeit < 0,92, deren Cluster nicht verschmelzen: das kleinere
  Mitglied erhält `vorschlag_fuer` = größerer Cluster (höchster Wert, falls mehrere).
- Kein transitives Zusammenziehen (v1-Befund: Single-Linkage zog Pfarreien zusammen).

### 4.4 Auto-Name

Häufigste Schreibweise des Clusters mit vereinheitlichter Rechtsform (`Fried. Krupp AG`,
`Hoesch-Köln Neuessen AG`). Abkürzungen im Namen werden **nicht** aufgelöst (Deutung);
der Name ist im Werkzeug editierbar.

### 4.5 Ausgabe

Cluster nach Häuserzahl absteigend, Personen ebenso; `pruefpflichtig=ja` ab
`--min-haeuser`. Erwartung: ≈ 120–150 Körperschafts-Cluster und ≈ 450 Personen in der
Prüfliste, zusammen ≈ 60 % der Körperschaftshäuser.

## 5. Werkzeug: `werkzeuge/eigentuemer.html`

Aufruf `http://localhost:8765/werkzeuge/eigentuemer.html` (Dev-Server `werkzeuge/serve.py`,
auch im VS-Code-Browser). Lädt §3.1, §3.2, §3.3. Logik in `werkzeuge/js/eigentuemer_modell.js`
(reines Modul, node-testbar); Leaflet wie in `pruefung.html`.

### 5.1 Aufbau

**Links – Eigentümerliste.** Cluster nach Häuserzahl; Filter offen/geprüft/alle,
Körperschaften/Personen, Textsuche; Farbpunkt der Kategorie; Fortschritt
„37 von 148 geprüft · 2.130 von 3.913 Häusern“. Standardansicht: nur prüfpflichtige.

**Rechts – aktiver Eigentümer.**
1. Kopf: Name (editierbar), Kategorie als Knopfreihe mit Tasten `1`–`8`, Häuserzahl, Status.
2. Schreibweisen mit Anzahl; `×` spaltet die Schreibweise als eigenen Eigentümer (offen) ab.
   Darunter Vorschläge „gehört vielleicht dazu“ (aus `vorschlag_fuer`, mit Ähnlichkeit);
   `+` übernimmt. **Nachtrag 2026-09-22:** ein Vorschlag gilt je Schreibweise, nicht je
   Gruppe — `+` bewegt nur diese eine Schreibweise zum aktiven Eigentümer, der Rest ihrer
   bisherigen Gruppe bleibt unverändert stehen.
3. „Zusammenführen mit …“: Suchfeld über alle Eigentümer, Vorschläge nach Ähnlichkeit;
   Auswahl hängt den aktiven Cluster an das Ziel (Ziel behält Name und Kategorie).
4. Belege: Tabelle der Häuser (Adresse, Stadtteil, Verwalter, Seite mit DigiBib-Link) und
   Leaflet-Karte der Punkte.
5. `Geprüft` (Taste `G`): setzt `geprueft=ja` auf alle Schreibweisen, springt zum nächsten
   offenen; `Hinweis` frei; „Rückgängig“ (letzte 20 Aktionen, nur in der Sitzung).

Personen-Eigentümer: gleiche Ansicht ohne Schreibweisen-Abschnitt; Zusammenführen erlaubt
(Schreibvariante derselben Person), Trennen nicht (§1).

### 5.2 Speichern

Jede Aktion sendet die betroffenen Zeilen (alle Schreibweisen der beteiligten Eigentümer)
als `POST /kuratierung/eigentuemer.csv` `{"zeilen": [...]}`; `serve.py` ersetzt nach
Schlüssel `schreibweise`, setzt `bearbeiter` und `datum`, schreibt die Datei mit
`schreib_csv`. Validierung (400 bei Verstoß): Kategorie aus dem Vokabular, `eigentuemer`
nicht leer, `geprueft` ∈ {`ja`, leer}, `schreibweise` bekannt (in §3.3 vorhanden),
`geprueft=ja` verlangt eine gesetzte Kategorie (Nachtrag 2026-09-22, Fund F2). Kein
Speichern-Knopf; ein Fehler erscheint als Banner. **Nachtrag 2026-09-22:** anders als
ursprünglich vorgesehen macht das Werkzeug die Aktion dabei *nicht* lokal rückgängig — die
POSTs laufen sequenziell über eine Promise-Kette, und ein rückwirkendes `rueckgaengig()`
könnte bei zwei schon wartenden Aktionen den Schnappschuss einer zweiten, noch gar nicht
gescheiterten Aktion zurücknehmen. Stattdessen sperrt ein Fehler das Werkzeug bis zum Neuladen
der Seite; der zuletzt gespeicherte Serverstand bleibt so die einzige Quelle der Wahrheit.

## 6. Export und Karte (Stufe 06)

### 6.1 Zuordnung

`pipeline/lib/karte_export.py` liest `kuratierung/eigentuemer.csv` und hängt an jede
Teil-II-Zeile `eigentuemer`, `kategorie`, `besitz_geprueft`. Je Adresse ins
PMTiles-Attribut `besitz`: die Kategorie des geprüften Eigentümers; mehrere geprüfte
Teil-II-Zeilen mit verschiedenen Kategorien → `gemischt`; keine geprüfte → `ungeprueft`.
`kennzahlen.json` erhält `besitz_geprueft` (Häuser) und `eigentuemer_geprueft` (Cluster).

### 6.2 Thema `besitz`

`site/daten/themen/besitz.json` mit neuer Farbart `kategorien`
(`{"art": "kategorien", "feld": "besitz", "werte": {kategorie: farbe}, "sonst": "#bbb"}`);
`themen.js` erzeugt einen MapLibre-`match`-Ausdruck, `app.js` zeichnet eine Legendenzeile
je Kategorie (Anzeigenamen aus §3.3), `ungeprueft` grau. Ebene II vorausgewählt;
`freigegeben` erst nach Abnahme. Sidebar-Block „Größte Eigentümer“ (Top 30 aus
`suche/eigentuemer.json`, Klick = Suche) nur bei aktivem Thema. **Nachtrag 2026-09-22:** das
Thema setzt in `zusatz` außerdem `zechen: true` — ohne die aktiven Zechen 1936 mitzuzeichnen
fehlte bei den Bergbau-Kategorien der Bezug zur zugehörigen Zeche auf der Karte.

### 6.3 Hausansicht und Popup

Unter dem Teil-II-Eintrag zusätzlich „Eigentümer: Fried. Krupp AG · Industrie“, nur bei
`besitz_geprueft=ja`; die rohe Buchschreibung bleibt immer sichtbar.

### 6.4 Suche

Neue Vorschlagsart `eigentuemer` nach dem Muster der Berufe: `suche/eigentuemer.json` als
Liste `[schluessel, anzeige, haeuser, kategorie]` (nur geprüfte Eigentümer) und Scherben
`suche/eigentuemer/<praefix>.json` = `{eigentuemer: [[adresse_id, n], …]}`. URL-Zustand
`eigentuemer=<name>`, Gruppe „Eigentümer (3)“ in den Vorschlägen, Untertitel
„n Häuser · Kategorie“. Auswahl → Treffermenge der Häuser.

## 7. Tests

- `tests/test_eigentuemer_cluster.py`: Normalisierung (Rechtsformen, `Ver.`-Regel,
  Kompositum), Clustering an Beispielen (Krupp-Varianten zusammen; „St. Andreas“ und
  „St. Josef“ getrennt; Grenzfall wird Vorschlag, nicht Merge), Sperre geprüfter Zeilen,
  verwaiste Schreibweisen.
- `tests/test_serve.py` (erweitert): Endpunkt Validierung, Ersetzen nach Schlüssel,
  `bearbeiter`/`datum`.
- `tests/test_karte_export.py` (erweitert): `besitz` geprüft/ungeprüft/gemischt, Suchindex
  Eigentümer, Kennzahlen.
- `site/tests/`: `farbregel` mit `kategorien`; Vorschlagsart `eigentuemer`.
- `werkzeuge/js/eigentuemer_modell.js` (node): abspalten, zusammenführen, Vorschlag
  übernehmen, Rückgängig, Fortschrittszählung.
- e2e: Thema `besitz` öffnen → Legende zeigt Kategorien; Klick auf ein Krupp-Haus zeigt den
  kanonischen Namen (Fixture mit einer geprüften Zeile).

## 8. Abnahme

Werkzeug in Betrieb, Körperschaften ≥ 5 Häuser geprüft (≈ 150 Cluster), Personen ≥ 5
Häuser durchgesehen; Thema `besitz` mit Legende auf der Karte; Hausansicht und Suche zeigen
kanonische Eigentümer; Über-Seite nennt Methode und Stand der Prüfung; Journal-Eintrag.

## Nachtrag 2026-09-23 — Identität und Stadtteil-Aufteilung

- Befund aus der ersten Durchsicht: Von 453 prüfpflichtigen Personen tragen 425 nur Initialen, 3 einen Titel — die
  Identität („dieselbe Person?“) ist aus dem Namen nicht belegbar, die Kategorie `privatperson` dagegen immer sicher.
  Neue Spalte `identitaet` (leer | `sicher`); alle Personen wurden pauschal auf `geprueft=ja`, `privatperson`,
  `identitaet` leer gesetzt (Hinweis in der Zeile). Export: Kategorie färbt die Karte, aber nur `identitaet=sicher`
  kommt in Suchindex und „Größte Eigentümer“. Werkzeug: Taste `U`.
- Kirchengemeinden ohne Zusatz („Kath. Kirchengem.“) lassen sich nur über den Stadtteil der Adresse trennen.
  `kuratierung/eigentuemer_stadtteil.csv` listet solche Schreibweisen; die Automatik führt sie je Stadtteil als
  eigene Schreibweise „… ‹Stadtteil›“ (immer prüfpflichtig, Kategorie von der einfachen Schreibweise geerbt), die
  von Hand benannt und zusammengeführt werden. Export: stadtteilgenaue Schreibweise vor einfacher.
