# Teilprojekt 4: Berufsangaben — Auflösung, OhdAB-Anbindung, Thema — Entwurf

Stand: 2026-09-23. Ergebnis des Brainstormings mit dem Projektleiter. Anforderung: Vault
`Anforderungen.md` E3 (Berufe/Sozialstruktur). Grundsatz: Precision first — die Automatik
schlägt nur Nachvollziehbares vor, jede Zuordnung entscheidet der Mensch, Ungeprüftes erscheint
auf der Karte nie als gesichert. Vorbild in Aufbau und Werkzeug: Teilprojekt 3
(`2026-09-22-eigentuemer-design.md`).

## 1. Ziel und Abgrenzung

Die Berufsangaben (`Beruf o. ä.`) aus Teil I (Einwohner) und Teil II (Eigentümer) werden je
Schreibweise zu einer aufgelösten Bezeichnung und einem Eintrag der **OhdAB** (Ontologie
historischer, deutschsprachiger Amts- und Berufsbezeichnungen, Uni Halle/Katrin Moeller,
publiziert auf FactGrid) zugeordnet. Aus der OhdAB folgen Anforderungsniveau und
Berufsgattung. Auf der Karte entstehen ein Thema „Berufe (Anforderungsniveau)“ und eine
Berufssuche über Normbezeichnungen.

Datenlage (`build/eintraege.csv`): Teil I 163.505 Nennungen in 9.196 Schreibweisen, Teil II
20.738 in 3.249, Teil III 153 (meist „Inh.“, bleibt außen vor). Gesamt 11.641 verschiedene
Werte; 55 % der Nennungen sind abgekürzt („Bergm.“ 27.794, „Kaufm.“/„Kfm.“, „Inval.“).
Schreibweisen mit ≥ 5 Nennungen (Teil I+II): 1.981 Werte = 93 % der Nennungen.

OhdAB (Probe 2026-09-23 per SPARQL, `database.factgrid.de/sparql`): 46.220 Schlüssel-Items
(`P904` OhdAB-ID wie `B 21112-100`, `P914` Normbezeichnung, `P889`/`P888` männliche/weibliche
Form, `P911` Anforderungsniveau, `P1007` Berufsgattung). Abkürzungen kennt OhdAB nicht (156
Aliasse insgesamt). Direkttreffer der 1.209 Werte ≥ 10 ohne Auflösung: eindeutig 24,5 %,
mehrdeutig 16,4 %, kein Treffer 59,1 %. Mehrdeutige Treffer liegen meist in derselben
Berufsgattung (Lehrer → 9 Items in B 84124); echte Niveau-Entscheidungen bei „Arbeiter“
(Helfer vs. Fachlich) und „Ingenieur“ (Spezialist vs. Hochkomplex).

Nicht Teil dieses Teilprojekts (→ TP5 Sozialscore): Nutzergruppierung der Berufe, Regler und
Schwellen, Einfärbung von Straßen/Gebäudepolygonen, Kartenexport; außerdem Teil III, die
≈ 9.600 seltenen Schreibweisen (< 5), `Beruf Bezugsperson`.

## 2. Entscheidungen aus dem Brainstorming

| Frage | Entscheidung |
|---|---|
| Zuschnitt | TP4 liefert die Grundlage (Auflösung, OhdAB-ID, Niveau, Gattung, einfaches Thema, Suche); Sozialscore und Werkzeugkasten werden TP5 |
| Untergrenze | Schreibweisen mit ≥ 5 Nennungen in Teil I+II (1.981); Rest „ungeprüft“, später nachkuratierbar |
| Zuordnungsebene | Immer ein OhdAB-Schlüssel-Item; zusätzlich Spalte `niveau_unsicher`, die der Mensch setzt, wenn die Quelle das Niveau nicht trägt (Variante C) |
| Vorschläge | Deterministisch (Abkürzungskatalog + exakter/unscharfer Abgleich), LLM nur als gekennzeichnete Reserve für Reste ohne Treffer |
| Teile | I und II in einer Schreibweisen-Tabelle; Teil III nicht |
| Werkzeug | Browser-Seite über `werkzeuge/serve.py` wie bei den Eigentümern |

## 3. Datenmodell

### 3.1 `kuratierung/ohdab.csv` (versioniert, Schnappschuss)

Von `werkzeuge/ohdab_laden.py` per SPARQL erzeugt, ≈ 46.000 Zeilen. Spalten:
`ohdab_id, qid, norm, maennlich, weiblich, niveau, gattung_id, gattung`.
`niveau` ist einer von sechs Schlüsseln (Abbildung der FactGrid-Labels):
`helfer` (Tätigkeitsprofil Helfer- und Anlerntätigkeiten), `fachlich` (Fachliche Tätigkeiten),
`spezialist` (Komplexe Spezialistentätigkeit), `hochkomplex` (Hoch komplexe Tätigkeiten),
`aufsicht` (Tätigkeitsprofil Aufsichtskräfte), `fuehrung` (Tätigkeitsprofil Führungskräfte);
Items ohne oder mit unbekanntem Niveau erhalten `keins`. `gattung_id` ist der Teil der
OhdAB-ID vor dem Bindestrich (`B 21112`), `gattung` das Label des Kategorie-Items ohne den
ID-Präfix. Nur deutsche Normbezeichnungen (Sprache `de` oder ohne Sprachkennung).
Die CSV bleibt kommentarfrei; Abrufdatum und Item-Zahl stehen im README-Abschnitt und in der
Commit-Nachricht.
Lizenz: CC BY 4.0 (Moeller, Uni Halle; KldB-Anteile unter KldB-Lizenz) → Impressum, Über-Seite.

`pipeline/lib/berufe.py` lädt den Schnappschuss (`lade_ohdab(pfad) -> dict[ohdab_id, dict]`)
und bricht mit klarer Meldung ab, wenn die Datei fehlt.

### 3.2 `kuratierung/berufe_abkuerzungen.csv` (versioniert)

Spalten `kurz, lang, beleg, bearbeiter, datum`. `kurz` ist ein abgekürztes Wort mit Punkt
(„Bergm.“, „Kfm.“, „Führ.“), `lang` das Vollwort („Bergmann“, „Kaufmann“, „Führer“). Von mir
aus den 1.981 Werten vorbefüllt; Beleg ist das Abkürzungsverzeichnis des Adressbuchs (Seite
angeben, falls vorhanden — im Digitalisat prüfen) oder „üblich“. Ganze Kürzel mit mehreren
Wörtern („Kraftw. Führ.“) werden wortweise aufgelöst und dann zusammengesetzt, wenn im Katalog
eine Komposita-Zeile steht (`kurz` = ganze Folge, `lang` = Kompositum: „Kraftw. Führ.“ →
„Kraftwagenführer“); ganze Folgen haben Vorrang vor Einzelwörtern.

### 3.3 Status-Zusätze

Vor dem Abgleich trennt die Automatik Zusätze ab, die keinen Beruf bezeichnen, und
schreibt sie in `status` (Vokabular, mehrere durch `;`):

| `status` | Muster (Regex, am Ende oder als eigenes Wort) | Beispiele |
|---|---|---|
| `ruhestand` | `i\. ?R\.`, `a\. ?D\.`, `Pens\.`, `Pensionär(in)?`, `Rentner(in)?`, `Ruhest\.` | „Bergm. i. R.“, „Lehrer a. D.“ |
| `invalide` | `Inval\.`, `Invalide`, Suffix `-?inval(ide)?\.?$` | „Berginval.“ → Bergmann + invalide |
| `witwe` | `Ww\.`, `Wwe\.`, `Witwe` | „Bergm. Ww.“ |
| `gewerbe` | kein Muster; von Hand bzw. per Vorschlagsskript für Gewerbebezeichnungen („Bäckerei“, „Lebensmittel“, „Fuhrgesch.“) — Nachtrag 2026-09-24, s. `docs/berufe_gewerbeformen.md` | „Bäckerei“ → Bäcker/in + gewerbe + niveau_unsicher |

Besteht die Schreibweise nur aus dem Status („Invalide“, „Pensionär“, „Rentner“, „Ww.“),
wird das OhdAB-Item für den Status vorgeschlagen (z. B. `A 10200-502 Invalide/Invalidin`;
die konkreten IDs für Pensionär/Rentner/Witwe ermittelt die Umsetzung aus dem Schnappschuss
und hält sie in `pipeline/lib/berufe.py` als `STATUS_ITEMS` fest) und `status` bleibt gefüllt.

### 3.4 `kuratierung/berufe.csv` (versioniert, Entscheidungen)

Eine Zeile je Schreibweise (exakter Rohwert aus `Beruf o. ä.`, getrimmt). Spalten:

| Spalte | Inhalt |
|---|---|
| `schreibweise` | Schlüssel |
| `nennungen` | Zahl in Teil I+II beim letzten Automatiklauf |
| `beruf` | aufgelöste Bezeichnung (Vollwörter, ohne Status), z. B. „Bergmann“ |
| `status` | leer oder `ruhestand`/`invalide`/`witwe`, mehrere mit `;` |
| `ohdab_id` | z. B. `B 21112-100`; leer = keine Zuordnung |
| `niveau_unsicher` | `ja` oder leer (nur vom Menschen) |
| `geprueft` | `ja` oder leer; `ja` verlangt `ohdab_id` |
| `vorschlag_grund` | `katalog`, `exakt`, `aehnlich 0.93`, `llm`, leer (Kombination erlaubt: „katalog; exakt“) |
| `bearbeiter` | `berufe_vorschlag` oder Name des Menschen (`christos`) |
| `datum` | ISO-Datum |
| `hinweis` | frei |

Sperrregel (`gesperrt(z)`): `geprueft=ja` **oder** `bearbeiter≠berufe_vorschlag` → die
Automatik ändert die Zeile nicht mehr (nur `nennungen` wird nachgeführt). Aufnahme neuer Zeilen
nur für Schreibweisen ≥ `--min-nennungen` (Standard 5); vom Menschen von Hand angelegte
seltene Schreibweisen bleiben erhalten. Niveau und Gattung stehen nicht in der Tabelle; sie
kommen beim Export aus dem Schnappschuss (eine Wahrheit).

### 3.5 `build/berufe_belege.json` (erzeugt, nicht versioniert)

`{schreibweise: [{name, adresse, teil, seite}, …]}` mit bis zu 5 Beispiel-Einträgen je
Schreibweise (Teil I bevorzugt, verschiedene Adressen) für die Belegtafel im Werkzeug;
`seite` für den DigiBib-Link wie im Eigentümerwerkzeug (`faksimile.json`).

## 4. Automatik: `werkzeuge/berufe_vorschlag.py`

Aufruf: `python3 werkzeuge/berufe_vorschlag.py [--min-nennungen 5] [--llm]`. Liest
`build/eintraege.csv`, `kuratierung/ohdab.csv`, `kuratierung/berufe_abkuerzungen.csv`,
`kuratierung/berufe.csv`; schreibt `kuratierung/berufe.csv` (Upsert) und
`build/berufe_belege.json`; gibt auf der Konsole die Trefferquote je Grund aus (Werte und
Nennungen).

Je Schreibweise, der erste Treffer gewinnt; `vorschlag_grund` nennt die beteiligten Schritte:

1. **Zerlegen** (§3.3): Status abtrennen, Kern trimmen, doppelte Leerzeichen, „u.“ bleibt.
2. **Katalog**: ganze Folgen, dann Einzelwörter mit Punkt über `berufe_abkuerzungen.csv`;
   Wörter ohne Punkt bleiben. Ergebnis ist `beruf`. Bleibt ein Wort mit Punkt unaufgelöst,
   ist der Kern „unvollständig“ (kein Exakt-Abgleich, nur Ähnlich mit Warnung).
3. **Exakt**: gefalteter Kern (Kleinschreibung, ä→ae usw., Bindestrich = Leerzeichen) gleich
   gefaltete `maennlich`, `weiblich` oder `norm` ohne Geschlechtszusatz (`/in`, `/-frau`,
   `/innen`). Mehrere Treffer → Vorschlag = Item mit der **kürzesten Normbezeichnung**, bei
   Gleichstand die kleinste OhdAB-ID; alle Kandidaten gehen ins Werkzeug (§5).
4. **Ähnlich**: RapidFuzz `ratio` auf denselben gefalteten Formen, Schwelle **≥ 0,90**,
   Vorschlag = bester Wert; unter der Schwelle kein Vorschlag. Kandidatenliste = die 20 besten.
5. **LLM-Reserve** (nur mit `--llm`, nur Zeilen ohne Vorschlag nach 1–4, ungesperrt): Anfrage
   mit Schreibweise, drei Belegen und den 20 nächsten OhdAB-Formen; Antwort ist genau eine
   OhdAB-ID aus dieser Liste oder „unklar“. Ergebnis nur als Vorschlag (`vorschlag_grund=llm`),
   nie `geprueft`. Modell und Aufruf über die Anthropic-API (`claude-sonnet-5`), Schlüssel aus
   der Umgebung; ohne Schlüssel bricht `--llm` mit Meldung ab.

Regeln: Die Automatik vergibt nie ein Niveau und setzt nie `niveau_unsicher`. Sie ist
idempotent: zweiter Lauf ohne Datenänderung ändert keine Zeile. Fehlt `kuratierung/ohdab.csv`,
bricht sie ab. Kandidaten mit **verschiedenen Niveaus** werden im Werkzeug als „Niveau
entscheiden“ markiert (Berechnung im Werkzeug aus der Kandidatenliste, nicht in der CSV).

Die Kandidatenlisten (bis 20 je Schreibweise: `ohdab_id`, Grund, Wert) schreibt die Automatik
nach `build/berufe_kandidaten.json` (nicht versioniert), damit das Werkzeug sie ohne eigene
Berechnung zeigen kann.

## 5. Werkzeug: `werkzeuge/berufe.html` + `werkzeuge/js/berufe_modell.js`

Architektur wie das Eigentümerwerkzeug: Modell ohne DOM (Node-Tests), Oberfläche lädt
`kuratierung/berufe.csv`, `kuratierung/ohdab.csv`, `build/berufe_belege.json`,
`build/berufe_kandidaten.json`, `site/daten/faksimile.json`; speichert jede Änderung sofort
per `POST /kuratierung/berufe.csv` `{"zeilen": [...]}` (sequenzielle Kette, Sperre `gestoert`
bei Fehler, Undo-Stapel).

### 5.1 Aufbau

- **Liste links:** Schreibweisen nach `nennungen` absteigend; Filter „nur ungeprüft“, „nur
  ohne Vorschlag“, „Niveau entscheiden“, Textsuche; Fortschritt „x von n geprüft · y % der
  Nennungen“.
- **Detail rechts:** Kopf (Schreibweise, Nennungen I/II, erkannter Status); Feld `beruf`
  (vorbelegt); **OhdAB-Suche**: Eingabe durchsucht die Formen des Schnappschusses lokal
  (Index nach gefaltetem Präfix; Treffer zeigen Normbezeichnung, Niveau, Gattung); darüber
  der Automatik-Vorschlag mit Grund und die Kandidaten, Kandidaten mit abweichendem Niveau
  farblich abgesetzt; Belegtafel (bis 5 Einträge mit DigiBib-Link); Hinweisfeld.
- **Tasten:** `Enter` Vorschlag/gewählten Kandidaten übernehmen, `G` geprüft (nur mit
  `ohdab_id`, sonst deaktiviert), `N` `niveau_unsicher` umschalten, `S` Status durchschalten
  (– / ruhestand / invalide / witwe; Mehrfachstatus nur über die Kästchen), `Z` Undo,
  `↓`/`↑` nächste/vorige Schreibweise in der gefilterten Liste.
- **Katalog-Rückkopplung:** Wird `beruf` gegenüber dem Katalogergebnis geändert und enthält
  die Schreibweise ein Wort mit Punkt, bietet ein Knopf „In Katalog“ an, die Zerlegung
  (`kurz` = Kern der Schreibweise ohne Status, `lang` = eingegebener `beruf`, Beleg „Werkzeug“)
  per `POST /kuratierung/berufe_abkuerzungen.csv` anzulegen; bestehende `kurz`-Zeilen werden
  nicht überschrieben (Server antwortet 409).

### 5.2 Server (`werkzeuge/serve.py`)

`pruefe_berufe(z, bekannt, ohdab)`: `schreibweise` bekannt; `ohdab_id` leer oder im
Schnappschuss; `status` leer oder nur Vokabular; `niveau_unsicher` ∈ {"", "ja"}; `geprueft`
∈ {"", "ja"}; `geprueft=ja` nur mit `ohdab_id`. Setzt `bearbeiter=christos`, `datum` heute.
`upsert_viele` in place wie bei den Eigentümern. Endpunkt für den Katalog: Upsert nach `kurz`,
409 bei vorhandener Zeile.

## 6. Export und Karte (Stufe 06)

### 6.1 Zuordnung je Eintrag

`pipeline/lib/berufe.py`: `lade_kuratierung(zeilen) -> dict[schreibweise, zeile]`,
`zuordnung(eintrag, kuratierung, ohdab) -> dict | None` — nur für `geprueft=ja` mit gültiger
`ohdab_id`: `{beruf, ohdab, niveau, gattung, status}`; `niveau` = `unsicher`, wenn
`niveau_unsicher=ja`, sonst der Schlüssel aus dem Schnappschuss. `karte_export.gruppiere`
hängt `_beruf` (dieses Dict) an den Eintrag; `eintrag_kurz` gibt `beruf`, `ohdab`, `niveau`,
`status` weiter (ungeprüft: nicht vorhanden). Eine geprüfte `ohdab_id`, die im Schnappschuss
fehlt, ist ein Exportfehler (Abbruch mit Schreibweise), kein stiller Ausfall.

### 6.2 Punktattribut `niveau` je Adresse

Nur Teil-I-Einträge zählen. Regel: unter den geprüften Einträgen der Adresse hat eine Stufe
**mehr als die Hälfte** → diese Stufe; sonst `gemischt`; nur `unsicher`-Einträge → `unsicher`
(`unsicher` zählt bei der Mehrheit nicht mit, aber zur Gesamtzahl); kein geprüfter Eintrag →
`ungeprueft`. Dazu Zählungen `n_helfer`, `n_fachlich`, `n_spezialist`, `n_hochkomplex`,
`n_aufsicht`, `n_fuehrung`, `n_unsicher` (nur wenn > 0) für TP5.

### 6.3 Thema `kuratierung/themen/berufe.json`

`{"id":"berufe","titel":"Berufe","text":"Häuser nach dem Anforderungsniveau der Berufe ihrer
Bewohner (Teil I) laut OhdAB …","grundlage":"… OhdAB (Moeller, Uni Halle, CC BY 4.0) …",
"freigegeben":false,"filter":{"ebenen":["I"]},"farbe":{"art":"kategorien","feld":"niveau",
"werte":{…},"sonst":"#c8c8c8"},"legende":"Farbe = Mehrheitsniveau der geprüften Bewohner",
"darstellung":"punkte"}`. Farben: `helfer` hell → `fuehrung` dunkel (eine Sequenz, sechs
Stufen), `gemischt` braun, `unsicher` grau-gelb, `ungeprueft` grau (`sonst`). Freigabe nach
der Kuratierung.

### 6.4 Hausansicht, Popup, Suche

Eintrag mit Zuordnung: „Bergm. i. R. → Bergmann · Fachliche Tätigkeit · Ruhestand“ (Rohtext
bleibt sichtbar); ungeprüft nur Rohtext. Popup wie Hausansicht in Kurzform.

Suche, Gruppe „Berufe“: Treffer sind **Normbezeichnungen** geprüfter Zuordnungen
(`suche/berufe_norm.json`: `[schluessel, norm, ohdab_id, nennungen, schreibweisen, niveau]`,
Scherben `suche/berufe_norm/<praefix>.json` → `ohdab_id → [[adressId, n], …]`); Untertitel
„29.400 Einträge · 6 Schreibweisen · Fachliche Tätigkeit“. Der bisherige Rohtext-Index
bleibt für ungeprüfte Schreibweisen; geprüfte Schreibweisen erscheinen dort nicht mehr (kein
doppelter Treffer). URL-Zustand: `ohdab=<id>` neben `beruf=`; `ohdab`, `beruf` und
`eigentuemer` schließen einander aus.

### 6.5 Kennzahlen, Über-Seite, Impressum

`berufe_geprueft` = Anteil der Teil-I-Nennungen (verortete Adressen) mit geprüfter Zuordnung,
`berufe_schreibweisen_geprueft` = Zahl geprüfter Schreibweisen. Über-Seite: Abschnitt
„Berufe“ (Auflösung, OhdAB, Untergrenze, Grenze beim Niveau, Status-Zusätze). Impressum:
OhdAB-Zitat mit Lizenz CC BY 4.0 und FactGrid-Verweis.

## 7. Tests

- `tests/test_berufe.py`: Zerlegung (Status-Muster, Kern), Katalog (Folgen vor Einzelwörtern,
  unvollständiger Kern), Faltung, Exakt (eindeutig, mehrdeutig → kürzeste Normbezeichnung),
  Ähnlich (Schwelle 0,90, kein Vorschlag darunter), Sperrregel/Idempotenz, `STATUS_ITEMS`
  vorhanden im Schnappschuss (mit kleiner Fixture-OhdAB).
- `tests/test_karte_export.py`: Zuordnung nur bei geprüft, Mehrheitsregel je Adresse
  (Mehrheit, gemischt, unsicher, ungeprüft), Zählfelder, Suchindex nach Normbezeichnung,
  fehlende `ohdab_id` im Schnappschuss → Fehler.
- `tests/test_serve.py`: `pruefe_berufe` (alle Ablehnungen), Katalog-409.
- `werkzeuge/tests/berufe_modell.test.js`: übernehmen, geprüft nur mit ID, Status
  durchschalten, `niveau_unsicher`, Undo, Katalog-Vorschlag, Filter „Niveau entscheiden“.
- `site/tests`: zustand `ohdab`, Ausschließlichkeit, Suche-Untertitel.
- e2e: `test_thema_berufe_legende_und_hausansicht` (Legende, Hausansicht mit „→“),
  `pytest.skip`, solange keine Zeile geprüft ist.

## 8. Abnahme

1. Ich: `ohdab_laden.py`, Katalog vorbefüllt, Automatik gelaufen, Werkzeug; Bericht mit
   Trefferquote je Grund (Werte und Nennungen) und Liste der Zeilen ohne Vorschlag.
2. Projektleiter: Kuratierung im Werkzeug (`http://localhost:8765/werkzeuge/berufe.html`).
3. `python3 pipeline/06_karte_export.py`, `freigegeben: true`, Über-Seite/Impressum,
   Journal.
