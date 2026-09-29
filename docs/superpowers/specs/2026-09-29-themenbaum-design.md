# Themenbaum in der Sidebar, Vergleich nach Schlüsseln, Thema Berufe nach Stellung — Entwurf

Stand 2026-09-29. Ergebnis eines Brainstormings; ersetzt für die Karte die Legendenkästchen
(Schalter-Paket vom 2026-09-29) und verallgemeinert den Eigentümer-Vergleich
(`2026-09-29-eigentuemer-vergleich-design.md`). Nimmt Punkt 2 des Werkstatt-Panels
(`2026-09-24-perspektiven-werkstatt-design.md` §7.1, Gruppen bilden) in vereinfachter Form vorweg.

## 1. Ziel und Abgrenzung

**Problem.** Ein Thema wird links oben gewählt und erklärt, seine Schalter stehen rechts unten in
einem Kasten, der Legende heißt; am Handy liegt der Kasten über der Karte und ist praktisch
unerreichbar. Nur das Thema Besitz hat Pills (größte Eigentümer), Bergbau und Berufe nicht. Das
Thema Berufe färbt nach Anforderungsniveau, einer unscharfen Achse.

**Ziel.** Jedes Thema hat in der Sidebar dieselbe Form: Oberkategorien als Zeilen, die die
Themenfarbe schalten und darunter die Einzelbezeichnungen aufklappen; jede Einzelbezeichnung
ist als Pill anklickbar und startet einen Vergleich (bis zu fünf, mit Farben) wie heute bei
Eigentümern. Die Legende rechts unten erklärt nur noch Zeichen.

| Thema | Oberkategorie (schaltet Farbe, klappt auf) | Einzelbezeichnung (Pill, Vergleich) |
| --- | --- | --- |
| Besitz | Besitzklasse (9 + ungeprüft) | Eigentümer (284 kanonische Namen) |
| Bergbau | Bergbau-Gruppe (4) | OhdAB-Norm (46 Schlüssel, 38 mit verorteten Nennungen) |
| Berufe | Stellung (9 + gemischt + ungeprüft) | OhdAB-Norm (856) |

**Nicht in diesem Schritt** (§9): Gewerbe als Thema mit Branche → Rubrik; OhdAB-Hauptgruppen als
zweiter Einstieg für Berufe; Bündelung mehrerer Schlüssel zu einer Gruppe; alles Aggregierende
(Anteile, Rangliste, Balken, Exporte von Grafiken) bleibt Werkstatt (5c). Die Werkstatt verliert
damit die Gruppenbildung aus einzelnen Schlüsseln an die Karte und behält Aggregation, Maße,
Formen und Export; die Ansicht wandert per URL in beide Richtungen.

**Leitprinzip** (Memory `feedback_precision_first`): Nichts Falsches als richtig. Vorschläge der
Automatik werden gefärbt, aber gekennzeichnet; Grundgesamtheit und Lücke H–J stehen an der
Vergleichsleiste; Größenunterschiede zwischen Gruppen werden genannt.

## 2. Sidebar im Thema-Zustand

Reihenfolge von oben (ersetzt den heutigen `#themenkopf` mit Text + Pills):

1. **Kopf**: Titel, ein Satz (`text`, ohne den Satz über die Legendenkästchen), Knopf
   „Thema verlassen“.
2. **Baum**: je Oberkategorie eine Zeile
   `[Kästchen] [Farbpunkt] Name [Zahl Adressen] [Pfeil]`.
   - Kästchen = heutiger Schalter (`klassen` im Zustand, `schalterFilter`/`schalterFarbe` in
     `themen.js`, unverändert). Adressen ohne eingeschaltete Oberkategorie verschwinden.
   - Zahl = Adressen dieser Oberkategorie im Thema (aus der Liste, §6), unabhängig von Zoom und
     Ausschnitt; bei Bergbau die Häuser mit mindestens einem Eintrag der Gruppe (nicht nur die,
     deren höchste Gruppe sie ist), mit Tooltip „Häuser mit mindestens einem Eintrag“.
   - Pfeil klappt die Einzelbezeichnungen auf; genau eine Oberkategorie ist offen (Akkordeon),
     beim Öffnen des Themas keine. Der Klappzustand ist nicht in der URL.
   - Zeile „gemischt“/„mehrere“ und „ungeprüft“ haben Kästchen und Zahl, aber keinen Pfeil.
3. **Einzelbezeichnungen** (unter der offenen Oberkategorie): Pills `Name <Zahl>` nach Zahl
   absteigend, die 15 häufigsten, dann „alle n anzeigen“ (klappt den Rest auf). Zahl = Adressen
   (Eigentümer: Häuser inkl. Spannen; Normen: Häuser mit mindestens einem Eintrag dieser Norm).
   Eine Pill ist gefüllt in ihrer Gruppenfarbe, wenn ihr Schlüssel im Vergleich ist (wie heute
   `markiereEigentuemer`); Tooltip „alle Häuser …“ bzw. „zum Vergleich hinzufügen“; bei vollem
   Vergleich (5) der flüchtige Hinweis wie heute.
4. **Grundlage**: `grundlage` in Kleinschrift, ganz unten.

Der Rest der Sidebar (Suchfeld, Ebenen-Pills, Filter, Themenliste) bleibt darunter wie heute.
Läuft ein Vergleich, zeigt die Sidebar wie heute Vergleichsleiste und Trefferliste; der Baum
bleibt oberhalb sichtbar (heute wird der Themenkopf bei Treffern ausgeblendet; künftig bleibt er
stehen, damit Pills abwählbar bleiben; die Trefferliste beginnt unter der Grundlage). Am Handy
liegt alles im Blatt; das Blatt öffnet beim Themenwechsel auf „halb“.

Themenwechsel: Klick auf ein anderes Thema in der Themenliste wechselt direkt (heute nötig:
„Thema verlassen“ zuerst). „Thema verlassen“ bleibt für die normale Karte. Ein laufender
Vergleich bleibt beim Themenwechsel erhalten (Trefferebene ist themenunabhängig).

## 3. Vergleich nach Schlüsseln

Der Eigentümer-Vergleich wird zum Vergleich typisierter Schlüssel.

- **Zustand**: `vergleich: string[]` (max. 5, `MAX_VERGLEICH = 5`), Einträge `eig:<Name>` oder
  `norm:<ohdab_id>`; URL-Parameter `vergleich`, Trenner `|`. **Abwärtskompatibel**: der alte
  Parameter `eigentuemer=a|b` wird beim Lesen zu `vergleich=eig:a|eig:b`; `schreibeZustand`
  schreibt nur noch `vergleich`. `namensliste` → `schluesselliste` (trimmt, dedupliziert, kappt
  auf 5, verwirft Einträge ohne bekannten Typ).
- **Suche** (`suche.js`): `treffer({art: "vergleich", schluessel})` liefert `gruppen`
  `[{schluessel, name, farbe, adressIds, zaehler}]`; Farbe nach Platz aus `FARBEN.gruppen`.
  `eig:` läuft über `eigentuemerScherbe` (wie heute), `norm:` über `berufeNormScherbe` (heute
  Suchart „ohdab“; die Scherbe wird nach `praefix2(name)` gewählt, darum trägt die Liste je
  Schlüssel den Normnamen). Die Sucharten „eigentuemer“ und „ohdab“ aus dem Vorschlagsmenü
  erzeugen künftig einen `vergleich`-Eintrag statt eines eigenen Zustands (ein Weg für alles).
- **Anzeige**: Vergleichsleiste, Verteilung nach Stadtteil, Ring bei mehrfach, Trefferebene,
  Legende der Gruppen (jetzt in der Leiste, nicht rechts unten), CSV-Spalte `gruppe` — alles wie
  heute, nur mit Namen statt Eigentümernamen. Der Name einer `norm:`-Gruppe ist der Normname
  („Bergmann“), Tooltip zeigt den Schlüssel.
- **Grundgesamtheit** (Satz unter der Leiste, je nach vorhandenen Typen, beide möglich):
  - `norm:` „Berufe: Einträge des Einwohnerverzeichnisses mit geprüftem Beruf; die Namen H bis J
    fehlen in der Vorlage.“
  - `eig:` „Eigentümer: auch Häuser aus Sammelzeilen des Adressbuchs („2–84 E. …“).“
  - Liegen die Häuserzahlen der größten und der kleinsten Gruppe um mehr als das Zehnfache
    auseinander: „Die Gruppen sind sehr ungleich groß (26.299 gegen 39 Häuser); Punkte zeigen
    Vorkommen, keine Anteile. Anteile je Stadtteil: Werkstatt.“ (Link erst, wenn 5c existiert;
    bis dahin ohne Link.)
- Mischen von Typen ist erlaubt (Krupp-Häuser gegen Bergleute).
- Popup: `eigKnopf` wird `vergleichKnopf(schluessel, name)`; im Popup erhalten Eigentümer wie
  bisher und zusätzlich Berufe mit Norm (`beruf_norm`, `ohdab`) den Knopf.

## 4. Thema Berufe färbt nach Stellung

- Hausfeld `stellung` (Pipeline, analog `niveau`): Mehrheitsstellung der Bewohner mit geprüftem
  Beruf; Vorschläge der Automatik (`stellung_quelle = vorschlag`) zählen mit; bei Gleichstand
  „gemischt“; ohne geprüften Beruf „ungeprueft“. Feld `n_stellung` (Verteilung) wie `n_niveau`.
- Klassen laut `berufe.csv` Spalte `stellung` sind **neun**, nicht acht: arbeiter (86.599
  Nennungen), ohne_erwerb (20.795), selbstaendige (17.688), angestellte (15.350), beamte
  (12.843), kaufleute (7.117, nur 3 Normen, vor allem „Kaufmann“ — Stellung bewusst offen,
  Experiment `kaufleute` in `ansicht.js`), unbestimmt (6.130), freie_berufe (3.280),
  unternehmer (2.334). „Kaufleute“ bleibt auf der Karte eine eigene Klasse mit eigener Farbe
  (kein Umschalten wie in der Werkstatt; Tooltip „Kaufmann ohne Zusatz: Angestellter oder
  Selbständiger, aus der Bezeichnung nicht zu entscheiden“).
- `kuratierung/themen/berufe.json`: `farbe.feld = "stellung"`, `werte` = 9 Klassen mit den
  Farben aus `STELLUNG` in `site/js/ansicht.js` (Okabe-Ito, dieselbe Farbe je Klasse auf Karte
  und Kapitel; `kaufleute` dort Schwarz — auf der Karte stattdessen ein dunkles Grau `#4b5563`,
  weil Schwarz die Bergbau-Farbe des Themas Besitz ist; `unbestimmt` fehlt in `STELLUNG` und
  bekommt `#9ca3af`), `gemischt` `#a16207`, `ungeprueft` Grau `#c8c8c8` (`sonst`).
  `schalter.feld = "stellung"`, Klassen in fester Reihenfolge: arbeiter, angestellte, beamte,
  selbstaendige, freie_berufe, unternehmer, kaufleute, ohne_erwerb, unbestimmt, gemischt,
  ungeprueft.
  `legende`: „Farbe = Mehrheitsstellung der geprüften Bewohner“; darunter aus den Daten:
  „Stellung handgeprüft bei n % der Nennungen, sonst Vorschlag“ (Zähler `n_stellung_hand`
  gegen Summe `n_st_*`, im Listen-Export §6 als `handgeprueft_anteil`). Handgeprüft sind heute
  641 von 1.977 Schreibweisen; der Anteil nach Nennungen ist zu berechnen, nicht zu schätzen.
  Kacheln `berufe.pmtiles` tragen `stellung` statt `niveau`.
- `kategorien.js`: `STELLUNGEN` (Namen) neben `KATEGORIEN`/`NIVEAUS`; `anzeigeFuer("stellung")`.
- Popup/Hausansicht: je Eintrag „Stellung: Arbeiter (nach Vorschlag)“ wenn `stellung_quelle`
  nicht `hand`. Niveau bleibt als Feld im Popup („Niveau: fachlich“).
- „unbestimmt“ ist eine echte Klasse (Bezeichnung lässt die Stellung offen) mit eigener Farbe
  und Kästchen; nicht mit „ungeprüft“ (kein geprüfter Beruf) verwechseln — beide Zeilen tragen
  einen Tooltip mit dieser Erklärung.
- Niveau bleibt Datenkern der Werkstatt und Feld im Export; verschwindet nur als Themenfarbe.

## 5. Legende rechts unten

Nur Zeichen: hausgenau, nur straßengenau / Stadtplan 1935, Suchtreffer (ohne Vergleich), Ring
„in mehreren Gruppen“ (nur bei Vergleich), „Größe = Zahl der Einträge“ (nur wo zutreffend).
Keine Kästchen, keine Gruppenfarben, keine Themensätze. `zeichneLegende` in `app.js`
schrumpft entsprechend; der Schalter-Teil zieht in `sidebar.js` (Baum) um.

## 6. Daten (Pipeline `06_karte_export.py`, `pipeline/lib/karte_export.py`)

Je Thema mit Baum eine Liste `themen/<id>_liste.json`:

```json
{ "oberkategorien": [
    { "id": "belegschaft", "name": "Belegschaft", "adressen": 0,
      "eintraege": [ { "schluessel": "norm:B 21112-100", "name": "Bergmann", "adressen": 0 }, … ] },
    … ],
  "gemischt": 0, "ungeprueft": 0, "handgeprueft_anteil": null }
```

(Zahlen im Beispiel sind Platzhalter der Form, keine Werte; `handgeprueft_anteil` nur bei
Berufen, sonst `null`.)

- **Besitz**: Oberkategorie = Besitzklasse; Einträge = kanonische Eigentümer der Klasse aus
  `kuratierung/eigentuemer.csv` mit Häuserzahl inkl. Spannen (wie `suche/eigentuemer.json`);
  `adressen` der Klasse = Häuser mit `besitz = klasse` (inkl. Spannen, `n_besitz`).
- **Bergbau**: Oberkategorie = Gruppe; Einträge = OhdAB-Schlüssel, die die Bergbau-Tabelle
  (`kuratierung/merkmale/bergbau.csv`, Spalte `beruf` = Bezeichnung aus `berufe.csv`) trifft;
  Zuordnung Bezeichnung → `ohdab_id` über `berufe.csv`. Ein Schlüssel steht in genau einer
  Gruppe: der, in der die meisten seiner Nennungen liegen (Fall „Berginvalide“ → B 21112-100
  Bergmann: Nennungen mit Bezeichnung „Berginvalide“ sind Invaliden, die Norm selbst bleibt
  Belegschaft; die Pill „Bergmann“ findet alle Nennungen der Norm, was die Pill-Zahl ggü. der
  Gruppenzahl erklärt — Tooltip nennt das). Schlüssel ohne verortete Nennung (8) fehlen.
  Zahl je Gruppe = Häuser mit `n_bb_<gruppe> > 0`.
- **Berufe**: Oberkategorie = Stellung (9); Einträge = OhdAB-Schlüssel mit dieser Stellung
  (`berufe.csv`, Spalte `stellung` je Schreibweise; eine Norm mit mehreren Stellungen steht bei
  der mit den meisten Nennungen); Zahl je Klasse = Häuser mit `n_st_<klasse> > 0`.
- `kuratierung/themen/<id>.json` bekommt `baum: true` (Themen ohne Baum, etwa Akademiker,
  zeigen weiter Text + Legende, nur ohne Kästchen); `zusatz.eigentuemerliste` entfällt.
- Bestehende Suchindizes bleiben (Vorschlagsmenü). `adressen_kurz` unverändert.

## 7. Module und Tests

| Datei | Änderung | Tests (node, `site/tests/`) |
| --- | --- | --- |
| `zustand.js` | `vergleich`, `schluesselliste`, Migration `eigentuemer` → `vergleich` | Rundreise, alte URL, Kappung, unbekannter Typ verworfen |
| `suche.js` | Art `vergleich` mit `eig:`/`norm:`, Gruppen | Gruppen je Typ, gemischt, Farbe nach Platz |
| `vergleich.js` | `vergleichsleisteHtml` mit Grundgesamtheit und Ungleich-Satz | Sätze je Typmenge; Schwelle 10× |
| `sidebar.js` | `zeigeThema(thema, liste, vergleich, farben)` → Baum, Akkordeon, „alle n“; Klick-Handler `[data-schluessel]`, `[data-klasse]` | HTML des Baums; 15/alle; offene Kategorie; Pill-Markierung |
| `app.js` | Themenwechsel direkt; `zeichneLegende` nur Zeichen; Klassen-Schalter aus Sidebar | Legende ohne Schalter (Snapshot-Text) |
| `popup.js` | `vergleichKnopf` für Eigentümer und Normen | Knopf bei Beruf mit Norm, keiner ohne |
| `kategorien.js` | `STELLUNGEN`, `anzeigeFuer("stellung")` | Namen, unbekannt → Rohwert |
| `karte.js` | unverändert bis auf Feldname `stellung` in Themenkacheln | bestehende Tests |
| `pipeline/lib/karte_export.py` | `baue_themen_listen`, Hausfeld `stellung`, Kacheln | pytest: Listen je Thema (Zahlen, Sortierung, ein Schlüssel je Gruppe), Mehrheitsstellung mit Gleichstand, Vorschläge zählen |

Sichtprüfung (Playwright, `?debug=1`): drei Themen am Desktop (Baum, Kästchen färben um,
Pill startet Vergleich, zwei Pills aus zwei Themen gemischt), Handy-Viewport 390×844 (Blatt
öffnet, Kästchen erreichbar, keine Legende mit Schaltern), alte URL mit `eigentuemer=` lädt.

## 8. Reihenfolge

1. Pipeline: Hausfeld `stellung`, Listen-Export, Thema Berufe umgestellt (Datenpaket neu).
2. Zustand + Suche + Vergleich (Schlüssel, Migration) — Karte funktioniert weiter mit alter UI.
3. Sidebar-Baum + Legende gekürzt + Themenwechsel direkt.
4. Popup-Knöpfe, Texte (Thementexte ohne Legendensatz), README, Journal.
5. Review, Sichtprüfung, Merge.

## 9. Später

- Gewerbe als Thema: Branche (15) → Rubrik (848); braucht Themenexport (Farbe je Branche,
  Hausfeld Mehrheitsbranche) und Suchindex je Rubrik; dann `rub:<rubrik>` als dritter Typ.
- OhdAB-Hauptgruppen als zweiter Einstieg im Thema Berufe (70, Bereiche darüber).
- Bündelung mehrerer Schlüssel zu einer Gruppe mit einem Namen („Krupp gesamt“, „Steiger aller
  Art“); „Meine Ansichten“ — Werkstatt.
- Werkstatt (5c) übernimmt `vergleich` aus der URL als Startgruppen.
