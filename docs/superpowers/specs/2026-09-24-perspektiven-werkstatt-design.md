# Teilprojekt 5: Perspektiven und Werkstatt — soziale Stellung, Gruppen, Gewerbe — Entwurf

Stand: 2026-09-24. Ergebnis des Brainstormings mit dem Projektleiter nach Abschluss von TP4.
Grundsatz unverändert: Precision first — nichts Ungeprüftes erscheint als gesichert, jede
Kennzahl trägt ihre Fallzahl und ihren Ausschlussanteil, Nutzerentscheidungen sind als solche
sichtbar. Vorbilder: `2026-09-22-eigentuemer-design.md`, `2026-09-23-berufe-design.md`.

## 1. Ziel und Abgrenzung

Die geprüften Daten der Teilprojekte 3 und 4 (Eigentümerklassen, Berufe mit OhdAB-Item) sowie
das Branchenverzeichnis (Teil III) werden für Besucher **explorierbar** gemacht:

- **Perspektiven** (`site/perspektiven.html`): eine erzählende Seite mit scrollgesteuerten
  Grafiken (Bubbles, Anteilsbalken, Stadtteil-Kacheln, Ranglisten, eingebettete Karte), die
  Daten kurz kontextualisiert, Abdeckung und Grenzen benennt und aus jedem Schritt auf die
  Karte und in die Werkstatt verlinkt.
- **Werkstatt** (`site/werkstatt.html`): Nutzer wählen Datenkern, Ebene und Darstellung,
  bilden eigene Gruppen mit Farben, sehen die Wirkung sofort und exportieren (CSV, SVG, PNG,
  Permalink).
- **Soziale Stellung** als neue, vordefinierte Klassifikation der Berufe (statt eines
  „Sozialscores“), plus Berufsgruppen (Branche) und Gewerberubriken.

Leitfragen des Projektleiters, an denen die Seite gemessen wird: War Essen schon 1936 in
einen ärmeren Norden und einen wohlhabenderen Süden geteilt? Gibt es Befunde, die man nicht
erwartet? War die Stadtmitte sozial durchmischter als heute?

Nicht Teil dieses Teilprojekts (→ §10 „Später“): Gebäudepolygone, Abgleich Eigentümer ↔
Bewohner (Teil I/II), Vergleich mit der Berufszählung 1933, Entfernungsmaße, H–J-Lücke,
Launch auf GitHub Pages.

## 2. Recherche-Ergebnis (Kurzfassung)

Belegt (Quellen im Journal 2026-09-24):

- Scrollytelling-Standard ist Scrollama (IntersectionObserver, ohne Abhängigkeiten, ~6 KB)
  mit `position: sticky`-Grafik und Textkarten; Layouts werden in der Praxis (Pudding,
  Observable) **vorberechnet**, nicht im Browser simuliert. SVG bleibt bis ≈ 1.000 Elemente
  flüssig und klickbar; Bubble-Darstellungen werden ab einigen Tausend Punkten unlesbar.
- DH: Whitelaw „Generous Interfaces“ (Sammlung zeigen statt leeres Suchfeld), Drucker
  (Unsicherheit sichtbar halten, nicht glätten), Shneiderman (Overview → Filter → Details).
  Sozialstatus aus Berufen: HISCO/HISCLASS/HISCAM; die Literatur warnt vor ungeeichten
  Gewichten. Die Berufszählungen 1933/1939 klassifizierten nach „Stellung im Beruf“
  (Selbständige, Mithelfende, Beamte, Angestellte, Arbeiter, Hausangestellte).
- Werkzeugmuster (RAWGraphs, Datawrapper): Daten → Darstellung → Zuordnung → Export mit
  Live-Vorschau; Konfiguration im Panel, Direktmanipulation in der Grafik nur für Auswahl.
  Zustand teilbar über die URL. Qualitative Palette Okabe-Ito (8 Farben), sequenzielle Skalen
  für Anteile.
- Vergleichbare Adressbuchprojekte (Lehmann Wien, Sachsendigital, ZLB) bieten Scans und
  Volltextsuche, keine kategoriale Exploration.

Folgen für den Entwurf: Bubbles nur für wenige hundert benannte Einheiten (Berufsnormen,
Eigentümer, Rubriken); Anteile als Balken mit sichtbarem Ausschluss-Segment; kein Score mit
erfundenen Gewichten; keine neuen Bibliotheken außer Scrollama (lokal in `site/vendor/`).

## 3. Entscheidungen aus dem Brainstorming

| Frage | Entscheidung |
|---|---|
| Aufteilung | 5a Datengrundlage → 5b Perspektiven → 5c Werkstatt; eine Spec, drei Pläne |
| Seitenstruktur | zwei neue Unterseiten (Perspektiven, Werkstatt); Karte bleibt, versteht aber das Ansicht-Format |
| Erstes Kapitel | Wohneigentum (Klassen klar, Abdeckung 11 % der Adressen — wird ausgewiesen); dann soziale Stellung, dann Gewerbe/Versorgung |
| Texte | Kapitel 1 mit echten Ansichten und Zahlen, Text als Platzhalter; `freigegeben: false`, bis der Text steht |
| Ton | sachliche Perspektiven statt plakativer Titel; jedes Kapitel mit Abschnitt „Was die Zahlen zeigen – und was nicht“ |
| Score | kein vordefinierter Sozialscore; stattdessen Klassifikation „Soziale Stellung“ (7 Klassen + Kaufleute + unbestimmt); „arm/reich“ ist Nutzergruppierung in der Werkstatt |
| Kaufleute | eigene sichtbare Gruppe; Nutzer können sie probeweise Angestellten oder Selbständigen zuschlagen |
| Teil III | wird vierter Datenkern; Rubrik aus dem Firmenname-Suffix, 849 Rubriken zu Gruppe/Art kuratiert |
| Flächen | Straßenlinien (OSM, heutige Führung, gekennzeichnet) und Hexraster; Gebäudepolygone später als gekennzeichnetes Experiment |
| Rechnen | Pipeline zählt je Ebene, Browser addiert; keine Datenbank im Browser |
| Bibliotheken | Scrollama lokal; sonst Vanilla JS, MapLibre, PMTiles |

## 4. Datenmodell „Ansicht“

Eine Ansicht beschreibt eine Darstellung vollständig; Karte, Perspektiven und Werkstatt lesen
und schreiben dasselbe Objekt. Modul `site/js/ansicht.js` (rein, ohne DOM).

```json
{
  "daten": "stellung",
  "ebene": "strasse",
  "form": "karte",
  "gruppen": [
    {"name": "Arbeiter", "aus": ["arbeiter"], "farbe": "#d55e00"},
    {"name": "Bürgertum", "aus": ["beamte", "freie_berufe", "unternehmer"], "farbe": "#0072b2"}
  ],
  "kaufleute": "unbestimmt",
  "unsicher": false,
  "mass": "anteil",
  "bezug": "Bürgertum",
  "min_n": 20,
  "filter": {"stadtteil": ["Altenessen-Nord"], "stufe": ["haus", "strasse"]},
  "karte": {"zentrum": [7.01, 51.46], "zoom": 13}
}
```

| Feld | Werte | Bedeutung |
|---|---|---|
| `daten` | `stellung`, `gruppe`, `niveau`, `besitz`, `gewerbe` | Datenkern (Zählfelder, aus denen gerechnet wird) |
| `ebene` | `adresse`, `strasse`, `stadtteil`, `hex` | Aggregationsebene; `adresse` = Punkte wie bisher |
| `form` | `karte`, `bubbles`, `balken`, `multiples`, `rangliste` | Darstellung; nicht jede Form gilt für jede Ebene (Matrix in §7.2) |
| `gruppen` | Liste | Nutzer- oder Standardgruppen: Name, Menge von Klassen-/Item-Schlüsseln, Farbe |
| `kaufleute` | `unbestimmt`, `angestellte`, `selbstaendige` | Experiment: wohin die Klasse `kaufleute` zählt (nur `daten=stellung`) |
| `unsicher` | bool | Einträge mit unsicherem Niveau einbeziehen (`daten=niveau`) bzw. Automatik-Vorschläge der Stellung einbeziehen (`daten=stellung`, `stellung_quelle=vorschlag`; Standard: einbeziehen, Anteil handgeprüft wird genannt) |
| `mass` | `anteil`, `dominant`, `mischung`, `dichte` | Kennzahl je Einheit (§4.1) |
| `bezug` | Gruppenname | Gruppe, deren Anteil/Dichte gezeigt wird |
| `min_n` | Zahl | Einheiten mit kleinerer Fallzahl bleiben grau |
| `filter` | Stadtteile, Verortungsstufen, Straße | Teilmenge |
| `karte` | Zentrum, Zoom | nur für `form=karte` |

### 4.1 Kennzahlen (alle im Browser aus Zählfeldern)

Je Einheit (Adresse, Straße, Stadtteil, Hexzelle) liegen Zählfelder `n_<klasse>` vor. Mit
`N` = Summe der Zählfelder der einbezogenen Klassen und `n_aus` = Summe der ausgeschlossenen:

- `anteil` = `n_bezug / N`; `dichte` = Betriebe der Bezugsgruppe je 1.000 Teil-I-Einträge;
- `dominant` = Gruppe mit größtem Anteil, nur wenn ihr Anteil ≥ 40 % (sonst „gemischt“);
- `mischung` = normierte Shannon-Entropie über die Gruppen (0 = eine Gruppe, 1 = alle gleich).
- Jede Ansicht meldet `N`, `n_aus` und die Zahl der Einheiten unter `min_n`. Diese drei Zahlen
  erscheinen in Legende, Zahlenzeile und Export.

### 4.2 URL und Themen

- `karte.html?ansicht=<base64url(JSON)>`, dito Perspektiven-Schritt-Links und Werkstatt.
  `zustand.js` erhält das Feld `ansicht`; `?thema=<id>` bleibt als Kurzform: ein Thema ist eine
  gespeicherte Ansicht.
- Die drei Themen in `kuratierung/themen/` werden auf das Ansicht-Format gehoben
  (`daten`, `ebene: "adresse"`, `form: "karte"`, `gruppen` aus `farbe.werte`); Felder `titel`,
  `text`, `grundlage`, `freigegeben`, `legende`, `zusatz` bleiben. `themen.js` liest beides,
  bis die Migration durch ist; danach nur noch das neue Format.
- Validierung: unbekannte Felder werden ignoriert, ungültige Werte auf Standard gesetzt,
  Gruppen ohne gültige Schlüssel verworfen; die Funktion liefert die bereinigte Ansicht und
  eine Liste der Korrekturen (für einen Hinweis in der Werkstatt).

## 5. TP5a — Datengrundlage

### 5.1 Soziale Stellung (`kuratierung/berufe.csv`, Spalte `stellung`)

Klassen (Schlüssel, Anzeigetext):

| Schlüssel | Anzeige | Regelvorschlag (Automatik, `bearbeiter=stellung_vorschlag`) |
|---|---|---|
| `arbeiter` | Arbeiter | OhdAB-Niveau helfer/fachlich in Gattungen der Produktion, des Bergbaus, Baus, Verkehrs, Reinigung; Schreibweisen mit „Arbeiter“, „Bergm.“, „Hauer“ |
| `angestellte` | Angestellte | Item/Gattung mit „Angestellte“, kaufmännische/technische Büroberufe, Meister- und Aufsichtsitems in Betrieben (Steiger, Werkmeister), Handlungsgehilfe |
| `beamte` | Beamte | Item mit Dienststufe („mittl. Dienst“ …), Bahn-/Post-/Polizei-/Verwaltungsbeamte, Lehrer an öffentlichen Schulen |
| `selbstaendige` | Selbständige (Handwerk, Handel, Gastgewerbe) | `status=gewerbe`; Meistertitel („Bäckermstr.“); Items Gastwirt, Händler, Inhaber |
| `freie_berufe` | Freie Berufe und Akademiker | Merkmal Akademiker; Ärzte, Anwälte, Architekten, Apotheker, Ingenieure mit Titel |
| `unternehmer` | Unternehmer und Leitende | Fabrikant, Fabrikbesitzer, Direktor, Bergwerksdirektor, Generaldirektor, Items Führung in Unternehmen |
| `ohne_erwerb` | Ohne Erwerbsberuf | `status` ruhestand/invalide/witwe; Items A 10xxx (Berufslose, Rentner, Pensionäre) |
| `kaufleute` | Kaufleute (Stellung unbestimmt) | Kaufmann und Varianten ohne Zusatz („Kfm.“, „Kaufm.“); mit Zusatz „Angest.“ → angestellte |
| `unbestimmt` | unbestimmt | alles, was keine Regel trifft |

Regeln: Vorschlag deterministisch aus Item, Gattung, Niveau, Status, Titel; jede Regel steht
mit Beispielen in `docs/stellung.md`. Zwei neue Spalten in `berufe.csv`: `stellung` (Vorschlag
oder Entscheidung) und `stellung_geprueft` (`ja` | leer). Die Automatik
(`werkzeuge/stellung_vorschlag.py`) füllt `stellung` überall dort, wo `stellung_geprueft` leer
ist — auch bei Zeilen, die für die Berufszuordnung gesperrt sind, denn die Stellung ist eine
neue, noch nicht entschiedene Frage; `stellung_geprueft=ja` setzt nur der Mensch. Handprüfung
im Berufe-Werkzeug (Auswahl je Klasse mit Zifferntasten, Filter „Stellung offen“). Export
(geändert 2026-09-25, nach Handprüfung von 91 % der Nennungen): Eine Stellung geht in den Export,
sobald der Beruf geprüft ist (`geprueft=ja`); das Feld `stellung_quelle` = `hand` |
`vorschlag` kennzeichnet je Eintrag, ob der Mensch entschieden hat (`stellung_geprueft=ja`)
oder die Automatik. Ohne geprüften Beruf `unbestimmt`. Zählfelder: `n_st_<klasse>` und
`n_stellung_hand` (Nenner für „davon handgeprüft“); die Ansicht-Option `unsicher` kann
Vorschläge ausblenden, Kapiteltexte nennen den Anteil.

Grenzfälle, die die Doku benennt: Steiger (Angestellte, obwohl OhdAB Aufsicht), Meister im
Betrieb vs. selbständiger Meister (Schreibweise entscheidet: „Bäckermstr.“ → selbständig,
„Werkmstr.“ → Angestellte), Lehrer (Beamte, Privatlehrer → freie Berufe), Ingenieur ohne
Titel (Angestellte), Kaufleute (eigene Klasse), Gewerbeformen (Selbständige, Niveau bleibt
unsicher).

### 5.2 Berufsgruppen / Branche (`kuratierung/gruppen.csv`)

Spalten `ohdab_id, norm, nennungen, gruppe, geprueft, bearbeiter, datum, hinweis`. Gruppen
(erste Liste, im Werkzeug erweiterbar): `bergbau`, `metall_maschinen`, `bau`, `holz_moebel`,
`textil_bekleidung`, `lebensmittel`, `handel`, `gastgewerbe`, `verkehr_bahn_post`,
`verwaltung`, `bildung_kultur_kirche`, `gesundheit`, `haus_reinigung`, `sonstige`.
Vorschlag aus Gattungstext (OhdAB-Gattungen sind bereits branchennah), Handprüfung in einem
kleinen Werkzeug `werkzeuge/gruppen.html` nach dem Muster von `berufe.html`. Nur 1.004 Items
(die in `berufe.csv` vorkommen). Zählfeld `n_gr_<gruppe>`.

Grenze (in Doku und Über-Seite): der Arbeitgeber steht nicht im Beruf; „Schlosser“ kann bei
Krupp oder auf der Zeche arbeiten. Gruppen sind Tätigkeitsbranchen, keine Betriebszugehörigkeit.

### 5.3 Gewerberubriken Teil III (`kuratierung/gewerbe.csv`)

- Pipeline (`pipeline/lib/gewerbe.py`): Rubrik = Text nach dem letzten Komma im `Firmenname`
  (18.864 von 18.892 Namen); Name ohne Suffix als `firma`. 849 Rubriken. Betriebe, die unter
  mehreren Rubriken an derselben Adresse mit gleichem Namen stehen, erhalten
  `dublette_gewerbe=<id des ersten>` und zählen nur einmal je Gruppe.
- Kuratierung: `rubrik, betriebe, gruppe, art, geprueft, bearbeiter, datum, hinweis`.
  `gruppe` wie §5.2 (gleiche Schlüssel, damit Teil I und III vergleichbar sind); `art` ∈
  `handwerk, handel, gastgewerbe, dienstleistung, industrie, freier_beruf, sonstige`.
  Vorschlag über Wortregeln („-handlung“, „-waren“ → handel; „-meister“, „-ei“ → handwerk;
  Schankwirt/Gastwirt → gastgewerbe …). Werkzeug `werkzeuge/gewerbe.html`.
- Gewerbeformen in Teil I (`status=gewerbe`, 218 Schreibweisen) erhalten dieselbe `gruppe`
  über `gruppen.csv` (ihr Item ist der Berufsträger).
- Zählfelder `n_gw_<gruppe>` und `n_gw_art_<art>` je Ebene; Nenner für `dichte` ist
  `n_I` (Teil-I-Einträge) je Einheit.

### 5.4 Export (`pipeline/06_karte_export.py`)

Neu in `site/daten/`:

| Datei | Inhalt |
|---|---|
| `ebenen/strassen.json` | je Straße (`schl_nr` bzw. Suchschlüssel): Name, Stadtteil, `n_I`, `n_II`, `n_III`, alle Zählfelder |
| `ebenen/stadtteile.json` | je Stadtteil dito, plus Zentrum und Breitengrad-Rang (für Nord–Süd-Reihen) |
| `ebenen/hex.json` | Hexraster ≈ 120 m Kantenlänge (H3 nicht nötig: eigenes Axialraster in `karte_export.py`), je Zelle Mittelpunkt und Zählfelder; nur Zellen mit `n_I ≥ 1` |
| `adressen.pmtiles` | Layer `adressen` wie bisher plus Zählfelder `n_st_*`, `n_gr_*`, `n_gw_*`; neuer Layer `strassen` (Linien) und `hex` (Polygone) mit `id` — die Werte kommen aus den JSON-Dateien per `feature-state`, damit Nutzergruppen ohne Tile-Neubau färben |
| `layout/berufe.json` | Bubble-Koordinaten der Berufsnormen (Kreis je Norm: Fläche ∝ Nennungen; Varianten: nach Stellung, nach Gruppe, nach Niveau als Achse) |
| `layout/eigentuemer.json` | Bubbles der 101 Eigentümer (Fläche ∝ Häuser) und Packung je Klasse |
| `layout/gewerbe.json` | Bubbles der Rubriken (Fläche ∝ Betriebe), Packung je Gruppe |
| `kennzahlen.json` | zusätzlich Abdeckung je Datenkern: Einträge/Adressen mit geprüfter Stellung, Gruppe, Gewerbe; Anteil unbestimmt/unsicher |

Straßenlinien: OSM-Ways der heutigen Straßen (`osm_id` der Verortung, sonst Namensabfrage
über `strasse_heute` im Essener Extrakt; Quelle und Abrufdatum in `site/vendor/README.md`
bzw. `kuratierung/strassen_geometrie.md`). Straßen ohne heutige Linie (verschwunden, Stufe
`stadtplan`) haben keine Linie und werden in der Legende gezählt. Die Linie ist die heutige
Führung — Legende sagt das.

Bubble-Layouts entstehen deterministisch (Kreispackung nach Größe absteigend, feste
Reihenfolge, keine Zufallszahl), Test prüft Überlappungsfreiheit und Reproduzierbarkeit. Der
`gattung`-Text je Eintrag wird in `haus/*.json` ergänzt.

### 5.5 Doku

`docs/stellung.md` (Klassen, Regeln, Grenzfälle, Kaufleute-Experiment), README-Abschnitte
„Datenkerne“ und „Ansicht-Format“, Über-Seite (neue Zahlen), Journal.

## 6. TP5b — Perspektiven (`site/perspektiven.html`)

### 6.1 Aufbau

- Einleitung (Zweck, Quelle, Stand aus `kennzahlen.json`), Inhaltsverzeichnis mit
  Sprungmarken, Kapitel untereinander.
- Je Kapitel: sticky Grafikfläche (Desktop rechts ≈ 60 %; mobil Vollbild im Hintergrund,
  Textkarten mit halbtransparentem Grund darüber) und Textkarten = Schritte. Beim Eintritt
  eines Schritts (Scrollama `onStepEnter`) wird dessen Ansicht gezeigt.
- Übergänge: gleiche Einheiten (Bubbles → Balken, Bubbles → Kartenpunkte) werden animiert
  (CSS-Transition der Kreisposition/-größe, ≤ 800 ms); sonst harter Wechsel. Bei
  `prefers-reduced-motion` keine Animation.
- Jeder Schritt: Text, Ansicht, optional Hervorhebung (Schlüssel, die betont werden), Links
  „Auf der Karte öffnen“ und „In der Werkstatt öffnen“ (beide mit `?ansicht=`).
- Detailkasten bei Klick auf Bubble/Balken/Kachel: Name, Zahlen, Beispiel-Schreibweisen bzw.
  Adressen-Link, „Auf der Karte zeigen“.
- Abschnitt „Was die Zahlen zeigen – und was nicht“ je Kapitel: Abdeckung (Zahlen aus
  `kennzahlen.json` eingesetzt), Erhebungsstand 1936, H–J-Lücke, Mehrheitsregel, Verortung.
- Tastatur: Schritte per Tab erreichbar, Fokus zeigt die Ansicht; Screenreader: Text ist
  vollständig ohne Grafik, Grafik `aria-hidden` mit Kurzbeschreibung je Schritt (`alt`-Text im
  Kapitel-JSON).

### 6.2 Inhalt (`kuratierung/perspektiven/<kapitel>.json`)

Felder: `id, titel, untertitel, freigegeben, einleitung, schritte[] {text, ansicht,
hervorheben[], beschreibung}, grenzen (Text mit Platzhaltern wie `{besitz_geprueft}`),
quellen[]`. Nur freigegebene Kapitel werden gerendert; die Startseiten-Kachel erscheint,
sobald ein Kapitel freigegeben ist.

Kapitel (Reihenfolge):

1. **Wohneigentum 1936: privat, industriell, genossenschaftlich, städtisch, kirchlich** —
   Schritte: Anteilsbalken der 8 Klassen mit Segment „ungeprüft“ (62.770 Adressen) →
   Bubbles der 101 Eigentümer nach Klasse → Rangliste der 15 größten → Karte Stadtteil-Anteil
   Bergbau/Industrie → Karte Genossenschaften/Siedlungen → Grenzen. Text: Platzhalter, bis
   der Projektleiter ihn schreibt (`freigegeben: false`).
2. **Soziale Stellung: Wer wohnte wo?** — Gliederung mit Leitfragen (Nord–Süd-Reihe der
   Stadtteile, Mischung Stadtmitte vs. Siedlungen, Kaufleute-Experiment); Ansichten werden
   angelegt, sobald 5a die Stellung liefert.
3. **Gewerbe und Versorgung** — Gliederung (Rubriken als Bubbles, Dichte Bäcker/Lebensmittel/
   Schankwirte je Stadtteil, Geschäftsstraßen); Ansichten nach 5a.

### 6.3 Technik

`site/js/perspektiven.js` (Seite, Scrollama-Anbindung), `site/js/formen/{bubbles,balken,
multiples,rangliste,karte}.js` mit gemeinsamer Schnittstelle
`zeige(container, ansicht, daten, optionen) → {svg|canvas, legende, zahlen}`;
`site/js/daten_ebenen.js` lädt `ebenen/*.json` und `layout/*.json` einmal je Seite.
Scrollama 3.x als `site/vendor/scrollama.js` (MIT, Version in `vendor/README.md`).
Startseite: Kachel „Perspektiven“; Über-Seite: Absatz.

## 7. TP5c — Werkstatt (`site/werkstatt.html`)

### 7.1 Panel (links; mobil als Lade)

1. **Daten**: Datenkern, Ebene, Filter (Stadtteile, Verortungsstufe, Straße per Suche).
2. **Gruppen**: Klassenliste mit Zählung; Gruppen bilden (Klasse anklicken → aktuelle Gruppe),
   benennen, Farbe (Okabe-Ito-Palette, freie Farbe); Suche nach Berufsnormen, Gattungen,
   Rubriken zum Hinzufügen; Schalter „Kaufleute zählen als …“, „Unsichere einbeziehen“;
   Standardgruppen je Datenkern als Startpunkt (aus den Themen).
3. **Darstellung**: Form, Maß, Bezugsgruppe, `min_n`-Regler, Farbskala für Anteile
   (sequenziell) und Mischung.
4. **Export**: CSV der aggregierten Tabelle (Kopf: Quelle, Stand, Ansicht-JSON als Kommentar-
   zeile), SVG und PNG der Grafik, PNG der Karte (`preserveDrawingBuffer: true` nur auf der
   Werkstatt-Karte), Permalink (kopieren), „Auf der Karte öffnen“. Personendaten werden hier
   nicht exportiert (dafür bleibt der Karten-CSV).

### 7.2 Formen × Ebenen

| | adresse | strasse | stadtteil | hex |
|---|---|---|---|---|
| karte | Punkte | Linien | Fläche (Zentrum-Kreis, da keine Stadtteilpolygone; §10) | Sechsecke |
| bubbles | — (Einheiten sind Normen/Eigentümer/Rubriken, nicht Adressen) | — | — | — |
| balken | gesamt | je Straße (Top-N) | je Stadtteil | — |
| multiples | — | — | Kacheln je Stadtteil | — |
| rangliste | — | Straßen | Stadtteile | — |

`bubbles` ist ebenenunabhängig: Einheiten sind die Layout-Objekte des Datenkerns (Normen für
stellung/gruppe/niveau, Eigentümer für besitz, Rubriken für gewerbe), gefärbt nach den
Nutzergruppen.

### 7.3 Interaktion und Zustand

Hover = Details; Klick in Grafik = Gruppe hervorheben bzw. Element der aktiven Gruppe
hinzufügen; Klick auf Stadtteil im Balken → Karte zoomt (Brushing). Zustand ausschließlich in
der Ansicht (`history.replaceState` bei jeder Änderung); „Meine Ansichten“ in `localStorage`
(Name + JSON), optional. Zahlenzeile unter der Vorschau: `N`, ausgeschlossen, Einheiten unter
`min_n`, Abdeckung des Datenkerns.

## 8. Karte (`site/karte.html`)

- `zustand.js`: Feld `ansicht` (base64url-JSON); bei gesetzter Ansicht steuert sie Ebene,
  Färbung und Legende; die bisherigen Filter (`ebene`, `praez`, `stadtteil`) bleiben wirksam.
- Neue Ebenen: `strassen` (Linien, Breite nach Zoom) und `hex` (Polygone, Deckkraft 0,6);
  Farbe per `feature-state` aus der clientseitigen Aggregation. Punkte bleiben bei
  `ebene=adresse`.
- Legende: Gruppen mit Farben, Maß, `min_n`, `N`/ausgeschlossen, Hinweis „Straßenlinien:
  heutige Führung“.
- Sidebar: Ansicht anzeigen, „In der Werkstatt öffnen“.

## 9. Tests

- pytest: Rubrik-Ablösung und Dubletten (§5.3); Stellungs-/Gruppen-/Rubrikvorschläge an
  Beispielen; Aggregation (Summe der Straßen = Summe der Adressen je Zählfeld; jede Adresse in
  genau einer Hexzelle); Layout deterministisch und überlappungsfrei; Kennzahlen; Ansicht-
  Migration der Themen.
- node: `ansicht.js` (Validierung, URL-Rundreise, Gruppenbildung, Kaufleute-Umschalten,
  Kennzahlen mit bekannten Werten inkl. Mischung 0 und 1, `min_n`); Formen-Module ohne DOM-
  Teile (Skalen, Legende, Zahlen).
- Playwright: Perspektiven (Schrittwechsel ändert Grafik; Bubble-Klick öffnet Detail;
  Kartenlink übergibt Ansicht; reduced-motion ohne Transition), Werkstatt (Gruppe bilden →
  Vorschau/Karte färben um; CSV/SVG/PNG-Download; Permalink reproduziert Ansicht), Karte
  (`?ansicht=` färbt Straßen/Hex).

## 10. Später (nicht in diesem Teilprojekt)

- **Gebäudepolygone**: (a) heutige OSM-Umrisse für Stufe „Haus“, gekennzeichnet „Gebäude
  heute, Daten 1936“; (b) Umrisse aus dem Stadtplan 1935 (ArcGIS-Dienst geo.essen.de, Rechte
  offen) vektorisieren — Segmentierung des Rasters oder händisches Nachzeichnen je Quartier —
  und füllen; historisch die richtige Geometrie, eigenes Projekt.
- Stadtteilpolygone (heutige Grenzen von der Stadt Essen / OSM) statt Zentrum-Kreisen.
- Abgleich Eigentümer ↔ Bewohner (wohnt der Eigentümer im Haus?), Anteil je Straße.
- **Abgleich Teil I ↔ Teil III über Name + Adresse (vorziehen, Kandidat für 5b):** Wer in
  Teil III als Betrieb an derselben Adresse steht, ist Inhaber → Stellung `selbstaendige`.
  Anlass (2026-09-25): „Friseur“ (724) ist als `arbeiter` vorgeschlagen, Teil III zählt aber
  657 Friseurbetriebe (Rubriken „Friseur“ 560 + „Friseur für Damen“ 97), während Teil I nur
  ~300 Einträge als Geschäft/Meister kennzeichnet („Friseurgesch.“ 246, „Friseurmstr.“ 30,
  Salons 24). Mehrere hundert „Friseur“ müssen also Inhaber sein. Gleiches gilt für andere
  Handwerksberufe ohne Meister-/Gehilfen-Zusatz (Schneider, Schuhmacher, Bäcker, Metzger,
  Uhrmacher …); der Meisterzwang für Neugründungen galt erst ab 1935, Altinhaber ohne Titel
  blieben. Bis zum Abgleich: solche Schreibweisen bei der Handprüfung `unbestimmt`, nicht
  pauschal `arbeiter`.
- Vergleich mit der Berufszählung 1933 (Stellung im Beruf) für Essen.
- Entfernung zum nächsten Betrieb einer Rubrik je Adresse.
- H–J-Lücke (Export adressbuecher.net), Pages-Launch, OhdAB-Rückmeldung.
