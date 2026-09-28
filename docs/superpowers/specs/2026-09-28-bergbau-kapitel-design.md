# Bergbau 1936 — Kapitel 4 der Schlaglichter, Punktkarte, Thema auf der Karte — Entwurf

Stand: 2026-09-28. Ergebnis des Brainstormings mit dem Projektleiter nach Abschluss des
Karten-UI (adfc003). Leitprinzip unverändert: Precision first — nichts Ungeprüftes erscheint
als gesichert, jede Zahl trägt ihre Grundlage und ihren Ausschluss, Grenzfälle sind benannt.
Vorbild für Aufbau und Datenmodell: `2026-09-24-perspektiven-werkstatt-design.md` (§4, §6).

## 1. Ziel und Abgrenzung

Ein viertes Kapitel der Schlaglichter zeigt, wie stark der Bergbau die Stadt prägte: wo die
Bergleute wohnten, wo ihre Aufsicht und Leitung, wo die ausgeschiedenen Bergleute, und
welche Gesellschaften welche Häuser besaßen. Dazu eine neue Darstellungsform „Punktkarte“
für die Kapitel und ein Thema „Bergbau“ auf der Hauptkarte, mit dem sich die vier Gruppen
straßengenau ein- und ausschalten lassen.

Entscheidungen des Projektleiters (2026-09-28):

| Frage | Entscheidung |
|---|---|
| Abgrenzung | nur Bergbau-Berufsnormen aus einer kuratierten Tabelle, nicht die OhdAB-Hauptgruppe B21 (die enthält Techniker, Ingenieure, Glas, Keramik, Steine) |
| Gruppen | vier: Belegschaft, Aufsicht, Leitung und Beamte, Berginvaliden |
| Grenzfälle Kokerei, Schlepper, Oberschaffner | in der Tabelle mit Hinweis geführt; im Kapitel dabei und in den Grenzen benannt |
| Bezugsgröße | „eingetragene Personen“ (Teil I), nicht Haushalte, nicht Einwohner (§2.1) |
| Einheit der Punktkarte | Hexfeld (120 m Kante), Kreisfläche = absolute Zahl, keine Anteile, kein `min_n` |
| Karten je Gruppe | vier kleine Karten nebeneinander, nicht eine gemeinsame |
| Farbwelt | hell wie die übrigen Kapitel |
| Hauptkarte | Thema „Bergbau“ mit vier schaltbaren Klassen, Farbe nach Rang bei mehreren Klassen im Haus |
| Zechenbesitz | hausgenaue Punktkarte nach Gesellschaft; Zechen neutral markiert, kein Betreiber ohne Beleg |
| Eigentümer-Kuratierung | Dubletten „König Wilhelm“ (4 Schreibungen) und „Mülheimer Bergwerks-Verein“ (2) vorher zusammenführen |

Nicht Teil dieses Schritts (→ §9): Betreiber je Zeche mit Beleg, Adressabgleich „Bergleute in
Zechenhäusern“, Betriebe des Bergbaus aus Teil III (109, fast alle ungeprüft), Punktkarte für
die bestehenden Kapitel (die Form ist dafür vorbereitet).

## 2. Datengrundlage

### 2.1 Bezugsgröße „eingetragene Personen“

Teil I führt nicht einen Eintrag je Haushalt, sondern jede erwachsene Person mit eigenem Beruf
oder Stand: Erwerbstätige, Witwen, Rentner, Invaliden, auch erwachsene Söhne und Eltern im
selben Haus. Befund (2026-09-28): 188.241 Einträge auf 56.518 Adressen; 23.028 als Witwe,
4.357 als „Frau“, 1.048 als „Fräulein“; in 11.046 Fällen derselbe Nachname mehrfach an einer
Adresse (23.360 Einträge, 12 %). Nicht enthalten: Ehefrauen ohne eigenen Eintrag, Kinder.

Wortwahl in allen Texten: „eingetragene Personen“ oder „Einträge des Einwohnerverzeichnisses“.
Bestehende Texte werden korrigiert: `kuratierung/perspektiven/stellung.json` (Einleitung
„zu jedem Haushaltsvorstand“, Schritt `anteile` „jeder zweite Haushaltsvorstand“) und
`kuratierung/perspektiven/datenbasis.json` (Platzhalter `eintraege_I`
„Haushaltsvorstände mit Beruf und Adresse“).

### 2.2 Tabelle `kuratierung/merkmale/bergbau.csv`

Spalten: `beruf, gruppe, geprueft, bearbeiter, datum, hinweis`. `beruf` ist die Norm aus
`kuratierung/berufe.csv` (Spalte `beruf`), nicht die Schreibweise; alle Schreibweisen einer
Norm folgen ihr. `gruppe` ∈ `belegschaft | aufsicht | leitung | invaliden`. Erstbefüllung aus
dem Brainstorming (Nennungen aus `berufe.csv`, Stand 2026-09-28):

- **belegschaft** (≈ 30.000): Bergmann, Hauer, Bergarbeiter, Zechenarbeiter, Fördermaschinist,
  Anschläger, Kettenanschläger, Schachthauer, Fahrhauer, Lehrhauer, Grubenschlosser,
  Zechenschmied, Zechenschreiner, Zechenschlosser, Bergtagelöhner, Schießhauer, Gesteinshauer,
  Zechenbote; Grenzfälle mit Hinweis: Kokereiarbeiter, Koksarbeiter (Kokerei meist Betriebsteil
  der Zeche), Schlepper (im Ruhrbergbau Bergbau-Beruf, OhdAB führt ihn unter Verkehr).
- **aufsicht** (≈ 1.400): Steiger, Fahrsteiger, Maschinensteiger, Obersteiger, Reviersteiger,
  Grubensteiger, Elektrosteiger, Wettersteiger, Schießmeister, Förderaufseher, Koksmeister,
  Lampenmeister, Schachtaufseher, Bohrmeister, Obermaschinenmeister (jeweils mit den
  abgekürzten Normvarianten wie „Fahrsteig.“, solange `berufe.csv` sie getrennt führt).
- **leitung** (≈ 450): Zechenbeamter, Grubenbeamter, Bergbeamter, Bergwerksbeamter,
  kaufmännischer Grubenbeamter, Bergassessor, Bergrat, Bergwerksdirektor,
  Bergwerksunternehmer, Grubeninspektor, Bergrevierinspektor, Markscheider,
  Markscheiderassistent, Bergbauingenieur, Kokereiassistent, Zechenangestellter,
  Bergbauangestellter; Grenzfall mit Hinweis: Oberschaffner (OhdAB B 2111, Bedeutung unklar).
- **invaliden** (≈ 1.200): Berginvalide.

Nicht aufgenommen (Begründung im Hinweis der Doku, nicht in der Tabelle): Techniker,
Diplomingenieur, Schleifer, Gießer, Glasmacher, Steinmetz, Ziegler, Zementeur,
Schachtmeister (Tiefbau), Zimmerhauer (Bau), Kohlenhändler (Handel), Bremser (Bahn).
`geprueft` ist bei der Erstbefüllung leer; der Projektleiter prüft die Tabelle, bevor das
Kapitel freigegeben wird. Ein Test stellt sicher, dass jede Norm der Tabelle in `berufe.csv`
vorkommt und keine Norm zwei Gruppen hat.

### 2.3 Zählfelder (Export, `pipeline/lib/ebenen.py`)

Je Teil-I-Eintrag mit geprüfter Norm in der Tabelle: `n_bb_<gruppe>` je Adresse (Kacheln),
Straße, Stadtteil und Hexfeld — dieselbe Mechanik wie `n_gr_`/`n_st_`. Einträge ohne
Bergbau-Norm bekommen kein Feld; der Nenner ist `n_I`. Ungeprüfte Berufe (ohne Norm) zählen
wie bei den Berufsgruppen als `n_gr_ungeprueft` und erscheinen im Ausschluss.

Adressfeld `bergbau` (Kacheln, Teil-I-Adressen): höchste vorhandene Gruppe nach Rang
`leitung > aufsicht > belegschaft > invaliden`, sonst fehlt das Feld. Das Feld färbt das Thema
auf der Hauptkarte (§5); die Zählfelder tragen die Schalter.

Kennzahlen (`kennzahlen.json`): `bergbau_n` (verortete Teil-I-Einträge mit Bergbau-Norm),
`bergbau_<gruppe>_n`, `bergbau_haeuser_n` (geprüfte Häuser der Klasse Bergbau),
`bergbau_gesellschaften_n`.

### 2.4 Kapiteldaten `site/daten/perspektiven/bergbau_punkte.json`

Vorberechnet (Spec 5, §2: Layouts werden nicht im Browser simuliert):

```json
{
  "gruppen": [{"id": "belegschaft", "name": "Belegschaft", "n": 26199, "felder": 1928}, …],
  "hex": {"belegschaft": [{"id": "-10_-1", "lon": 6.978, "lat": 51.448, "n": 12, "r": 2.1, "x": 14.2, "y": -3.0}, …], …},
  "haeuser": [{"id": "c439…", "lon": 7.02, "lat": 51.47, "eig": "gewerkschaft_mathias_stinnes", "stufe": "haus"}, …],
  "gesellschaften": [{"id": "gewerkschaft_mathias_stinnes", "name": "Gewerkschaft Mathias Stinnes", "haeuser": 725}, …],
  "maxn": 210
}
```

`x, y` sind die Packungskoordinaten je Gruppe (`packe_kreise`, größte zuerst um den Ursprung);
`r` ist der Radius im Packungsmaßstab, `r ∝ sqrt(n / maxn)` mit einem Maßstab über alle
Gruppen. `haeuser` enthält alle geprüften Adressen der Klasse Bergbau mit dem kanonischen
Eigentümer-Schlüssel (`falte(name)` wie im Suchindex); `gesellschaften` ist nach Häusern
sortiert. Adressen der Stufe `strasse` und `stadtplan` sind enthalten und tragen ihre Stufe;
die Form zeichnet sie als Ring statt Scheibe, die Legende zählt sie getrennt.

### 2.5 Eigentümer-Kuratierung

Vor dem Export: in `kuratierung/eigentuemer.csv` die Schreibungen „Ss. Bergw. Verein König
Wilhelm“, „Essen. Bergwerksverein König Wilhelm“, „Essener Bergw. Verein“ auf den kanonischen
Namen „Essener Bergwerks-Verein König Wilhelm“ führen; „Mühlheimer Bergwerksverein“ und
„Mühlheimer Bergwerks-Verein“ auf den kanonischen Namen „Mülheimer Bergwerks-Verein“ (die
Buchschreibung „Mühlheimer“ bleibt als Schreibweise erhalten) (Merge-Ziel per kanonischem Namen, Quellzeilen zur
Verifikation, wie in der Kuratierungs-Doku). Layout, Suchindex und Wohneigentum-Kapitel
folgen automatisch; die Zahlen des Wohneigentum-Kapitels (Rangliste, Bubbles) ändern sich
und werden nach dem Export im Text nachgezogen.

## 3. Ansicht-Modell (Erweiterung `site/js/ansicht.js`)

- `DATEN` um `bergbau` (Präfix `n_bb_`, Nenner `n_I`); Standardgruppen: die vier Gruppen mit
  den Kapitelfarben Belegschaft `#c2410c`, Aufsicht `#1d4ed8`, Leitung `#7c3aed`,
  Berginvaliden `#15803d`.
- `FORMEN` um `punktkarte`.
- Neues Feld `punkte` (nur für `punktkarte`), normalisiert:
  `{ zustand: "gesammelt" | "karten" | "haeuser", hervor: [Gruppenname…] }`.
  `gesammelt` = Packungen nebeneinander, `karten` = eine Karte je Gruppe, `haeuser` =
  hausgenaue Punkte aus `haeuser` (Gruppen sind dann Gesellschaften: `aus: [eig-Schlüssel]`,
  Rest „übrige Bergbau-Eigentümer“ grau). `hervor` blendet alle anderen Gruppen ab.
- Der Werkstatt-Kern bleibt unberührt; `bergbau` als Datenkern in der Werkstatt kommt mit 5c.

## 4. Form `site/js/formen/punktkarte.js`

Schnittstelle wie die übrigen Formen: `zeige(ansicht, daten, optionen) → { svg, legende,
zahlen, hoehe }`. `daten.punkte` ist die Kapiteldatei (§2.4), `daten.polygone` die
Stadtteilgrenzen, `daten.zechen` die Zechen in Förderung 1936 (Symbol Schlägel und Eisen aus
`bilder/zeche.svg` als `<symbol>`).

Zusätzlich `aktualisiere(svg, ansicht, daten, optionen)`: setzt für die vorhandenen Kreise
neue Positionen und Radien und die Abblendung, ohne das SVG zu ersetzen. Das ist die
Voraussetzung für den fließenden Übergang, denn `perspektiven.js` ersetzt heute je Schritt
`svg.innerHTML`. Neue Regel in `zeichne()`: Ist die Form des vorigen und des neuen Schritts
`punktkarte` mit demselben `daten` und `punkte.zustand ≠ haeuser` in beiden, wird
`aktualisiere` gerufen statt `zeige`; sonst wie bisher. Übergang per CSS-Transition auf
`transform` und `r` (0,9 s), bei `prefers-reduced-motion` ohne Übergang.

Geometrie: Plattkarte mit Breitengradkorrektur wie `stadtteilkarte.js`; vier Felder 2×2 am
Laptop, bei Bühnenbreite unter 600 px 1×4 untereinander; jede Karte in ihr Feld eingepasst.
Radius auf der Karte: `r_karte = max(1,6 px, 0,62 · r_packung)`; im gesammelten Zustand
`r_packung`. Hausgenaue Punkte: fester Radius 2,4 px, Ring bei `stufe ≠ haus`.

Elementbudget und Rückfall: rund 3.100 Kreise (gesammelt/karten) bzw. 5.400 (Häuser). Erster
Task der Umsetzung ist eine Bildratenprüfung des Übergangs im Browser des Projektleiters
(Laptop und Handy) über die Mockup-Seite `build/mockups/bergbau.html`; unter 30 fps am
Handy wird die Form auf `<canvas>` mit `requestAnimationFrame` umgestellt und die Kreise
verlieren den Detailkasten (dann Schwebetext über Trefferprüfung im Canvas). Die Spec legt
SVG als Erstweg fest.

Legende: Gruppen mit Farbe und Zahl; Zeile „Kreisfläche = eingetragene Personen je Hexfeld
(120 m Kante), größter Wert {maxn}“; Zeile „Schlägel und Eisen: Zechen in Förderung 1936“;
im Zustand `haeuser` zusätzlich „Ring: nur straßengenau oder Stadtplan 1935 ({n})“.
Zahlenzeile: `N` eingetragene Personen mit Bergbau-Norm von `n_I` verorteten, Ausschluss
ungeprüfte Berufe wie bei `gruppe`.

Detailkasten: Kreis ist `.einheit` mit `data-id` (Hex-ID bzw. Adress-ID); der Kasten zeigt
Gruppe, Zahl, Stadtteil des Feldes (aus `hex.json`) und den Link „auf der Karte ansehen“.

## 5. Thema „Bergbau“ auf der Hauptkarte

`kuratierung/themen/bergbau.json` → `site/daten/themen/bergbau.json`:

```json
{ "id": "bergbau", "titel": "Bergbau", "freigegeben": true,
  "text": "Adressen mit Bergbau-Berufen laut Teil I, nach Gruppe. Bei mehreren Gruppen im Haus zählt die höchste.",
  "grundlage": "Bergbau-Tabelle kuratierung/merkmale/bergbau.csv, Berufe kuratierung/berufe.csv; Stand …",
  "filter": { "ebenen": ["I"] },
  "farbe": { "art": "kategorien", "feld": "bergbau",
             "werte": { "leitung": "#7c3aed", "aufsicht": "#1d4ed8", "belegschaft": "#c2410c", "invaliden": "#15803d" } },
  "schalter": { "praefix": "n_bb_", "klassen": ["leitung", "aufsicht", "belegschaft", "invaliden"] },
  "zusatz": { "zechen": true },
  "legende": "Farbe: höchste Bergbau-Gruppe im Haus" }
```

Neu gegenüber den bestehenden Themen:

- **Schalter.** Trägt ein Thema `schalter`, zeigt die Legende je Klasse ein Kästchen
  (`<label><input type=checkbox data-klasse>`). Der Kartenfilter (`karte.setzeFilter`)
  bekommt zusätzlich `["any", …[">", ["coalesce", ["get", "n_bb_<k>"], 0], 0] je eingeschalteter Klasse]`;
  Adressen ohne eingeschaltete Klasse fallen weg. Alle Klassen aus = nur die Grundfarbe, kein
  Filter (der Nutzer sieht dann die Karte wie ohne Thema, die Legende sagt „keine Klasse
  gewählt“). Die Farbregel bleibt Rang über `bergbau`; ist die Rangklasse eines Hauses
  abgeschaltet, färbt die höchste eingeschaltete Klasse: Ausdruck
  `["case", [">", n_bb_leitung, 0] ∧ leitung an, farbe_leitung, …, sonst]` — gebaut in
  `themen.js` aus `schalter` und dem Zustand, rein und testbar.
- **Zustand.** Neuer URL-Parameter `klassen` (Komma-Liste, Standard: alle Klassen des Themas;
  nur gültig, wenn `thema` Schalter hat; unbekannte Werte werden verworfen). `zustand.js`
  liest und schreibt ihn wie `ebene`.
- **Legende.** Unter den Kästchen die Zeile „Farbe: höchste Bergbau-Gruppe im Haus“. Keine
  Zählung sichtbarer Adressen (die Karte zählt nicht clientseitig); der Themen-Text in der
  Sidebar nennt Grundlage und Stand.

Alle bestehenden Themen ohne `schalter` verhalten sich unverändert.

## 6. Kapitel `kuratierung/perspektiven/bergbau.json`

`id: bergbau, reihenfolge: 4, freigegeben: false, titel: "Bergbau 1936", untertitel:
"Zechen, Belegschaft, Aufsicht, Leitung: Wo die Bergleute wohnten"`. `datenbasis` mit
Platzhaltern `{bergbau_n}`, `{teil_i_n}`, `{beruf_geprueft_n}`; `datenbasis_schritt: gruppe`;
`ausschluss: "Beruf ungeprüft oder keine Bergbau-Norm"`. Texte sind Platzhalter mit echten
Zahlen, bis der Projektleiter sie schreibt.

Schritte (jeder mit `beschreibung` für `aria-label` und `ansicht`):

1. `gruppen` — `punktkarte`, `punkte.zustand: gesammelt`. Text: Abgrenzung, Bezugsgröße.
2. `karten` — `punktkarte`, `punkte.zustand: karten`. Zechen eingeblendet. Text: Nordband,
   Südosten um Kupferdreh und Überruhr, „Nähe heißt nicht Beschäftigung“.
   Link: `karte.html?thema=bergbau`.
3. `belegschaft-leitung` — wie 2 mit `punkte.hervor: ["Belegschaft", "Leitung und Beamte"]`.
   Link: `karte.html?thema=bergbau&klassen=belegschaft,leitung`.
4. `invaliden` — wie 2 mit `punkte.hervor: ["Berginvaliden"]`.
   Link: `karte.html?thema=bergbau&klassen=invaliden`.
5. `hausherr` — `punktkarte`, `daten: besitz`, `ebene: adresse`, `punkte.zustand: haeuser`,
   Gruppen = die elf Gesellschaften mit mehr als 90 Häusern, Rest grau. Farben in der
   Reihenfolge der Häuserzahl: `#e69f00 #56b4e9 #009e73 #f0e442 #0072b2 #d55e00 #cc79a7
   #7c3aed #15803d #c2410c #0e7490` (Okabe-Ito ohne Schwarz, ergänzt um vier Farben der
   Besitzklassen).
   Zechen neutral. Text: Kolonien, Graf Beust (1929 stillgelegt, 166 Häuser).
   Links je Gesellschaft: `karte.html?eigentuemer=<kanonischer Name>` (Eigentümersuche).
6. Grenzen (Abschnitt wie in den anderen Kapiteln, Platzhalter aus `kennzahlen.json`):
   nur verortete Einträge; ungeprüfte Berufe ausgeschlossen; H–J-Lücke; Kokerei, Schlepper,
   Oberschaffner als Grenzfälle; keine Zuordnung Person → Zeche; Betriebe aus Teil III nicht
   gezeigt; Zechen ohne Betreiber; Eigentümer nur geprüfte Adressen (Ausschluss `n_bs_ungeprueft`).

Der Link „auf der Karte ansehen“ wird wie in den anderen Kapiteln über `linkKarte` gebaut;
für `punktkarte` liefert das Modell die Thema-Form statt eines `?ansicht=`-Links.

## 7. Dateien

- Neu: `kuratierung/merkmale/bergbau.csv`, `kuratierung/themen/bergbau.json`,
  `kuratierung/perspektiven/bergbau.json`, `site/js/formen/punktkarte.js`,
  `site/tests/punktkarte.test.js`, `site/tests/themen_schalter.test.js`,
  `pipeline/tests/test_bergbau.py`, `docs/bergbau.md` (Abgrenzung, Gruppen, Grenzfälle,
  Nicht-Aufgenommenes mit Begründung).
- Geändert: `pipeline/lib/ebenen.py` (Zählfelder, Rangfeld), `pipeline/lib/karte_export.py`
  (Kapiteldaten, Kennzahlen, Thema, Index), `kuratierung/eigentuemer.csv` (Zusammenführung),
  `kuratierung/perspektiven/stellung.json` und `datenbasis.json` (Wortwahl),
  `site/js/ansicht.js`, `site/js/perspektiven.js` (Aktualisieren statt Ersetzen),
  `site/js/perspektiven_modell.js` (`formFuer`, `linkKarte`), `site/js/daten.js` und
  `site/js/daten_ebenen.js` (Kapiteldaten, Zechen laden), `site/js/themen.js` (Schalter,
  Farbausdruck), `site/js/zustand.js` (`klassen`), `site/js/app.js` (Legende mit Kästchen),
  `site/js/karte.js` (Filter), `site/css/perspektiven.css` (Übergänge), `README.md`,
  `site/ueber.html` (Absatz Bergbau).

## 8. Tests

- Pipeline: jede Norm der Tabelle existiert in `berufe.csv`, keine Norm doppelt; Zählfelder
  je Ebene summieren auf dieselbe Zahl (Straße = Stadtteil = Hex = Kennzahl `bergbau_n`);
  Rangfeld bei Adresse mit Bergmann und Steiger = `aufsicht`; Kapiteldatei: Packung ohne
  Überlappung (`ueberlappen` leer), `haeuser` = Anzahl geprüfter Bergbau-Adressen; nach der
  Zusammenführung genau ein Eigentümer „König Wilhelm“ im Layout.
- Site (`node --test site/tests/*.test.js`): `normalisiere` mit `punkte`; `punktkarte.zeige`
  liefert je Gruppe so viele Kreise wie Felder, Zustand `karten` legt jeden Kreis in sein
  Feld, `hervor` setzt die Abblendklasse, `haeuser` zeichnet Ringe bei `stufe ≠ haus`;
  `aktualisiere` ersetzt keine Knoten (gleiche Knotenidentität); `themen.js` baut aus
  `schalter` und `klassen` den Filter- und Farbausdruck, alle Klassen aus → kein Filter;
  `zustand.js` liest und schreibt `klassen` nur mit gültigen Werten; `linkKarte` liefert
  für `punktkarte` den Thema-Link.
- Sichtprüfung (Playwright im Scratchpad, wie beim Karten-UI): Übergang Schritt 1 → 2 ersetzt
  das SVG nicht; Legende mit Kästchen auf der Karte; Abschalten einer Klasse ändert den Filter.

## 9. Offen

- Betreiber je Zeche (Historisches Portal, Huske) als Spalte der Zechenliste; danach Zechen im
  Schritt „hausherr“ in Gesellschaftsfarbe.
- Adressabgleich Teil I ↔ Teil II: Anteil Bergleute in Zechenhäusern (neues Zählfeld).
- Punktkarte für Stellung und Besitz in den bestehenden Kapiteln.
- Betriebe des Bergbaus (Teil III) nach Handprüfung der 109 Vorschläge.
- Ob die gepackten Klumpen (Zielscheiben-Optik durch strenge Größensortierung) eine andere
  Packung bekommen — nach der Sichtprüfung.
