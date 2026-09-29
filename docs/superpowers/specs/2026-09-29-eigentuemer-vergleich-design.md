# Eigentümer-Vergleich: schnelle Treffer, Mehrfachauswahl mit Farben

Stand 2026-09-29. Ergebnis des Gesprächs mit Christos nach der Bestandsaufnahme der Kartenfeatures.
Gilt für die Hauptkarte `site/karte.html`.

## 1. Anlass und Entscheidungen

Nach dem Klick auf einen Eigentümer unter „Größte Eigentümer“ wartet man mehrere Sekunden, bis Karte und
Liste stehen; der gewählte Knopf bleibt unmarkiert; mehrere Körperschaften lassen sich nicht gegenüberstellen.

Ursache der Wartezeit (`app.js eigMap`/`eigVon`): Die Trefferliste braucht je Haus Adresse und Stadtteil. Dafür
läuft je Haus eine gefilterte `querySourceFeatures`-Abfrage über alle geladenen Punkte, und was dort fehlt,
kommt aus den Adressscherben `adressen/<xx>.json`, die alle Zählfelder tragen (im Mittel 143 KB, 256 Dateien,
37 MB). Bei aktivem Thema ist die Hauptquelle ausgedünnt, also fehlt fast alles. Die Liste wird nach dem
nächsten `idle` ein zweites Mal gebaut. Dasselbe trifft Beruf, OhdAB und Straße.

Entscheidungen (Christos):

- Allgemeine Reparatur der Ladezeit für alle Trefferarten, kein Sonderweg für Eigentümer.
- Bis zu **fünf** Eigentümer gleichzeitig, feste Farbpalette in Reihenfolge der Auswahl. Keine Bündelung
  mehrerer Namen zu einer Gruppe (das übernimmt die Werkstatt, 5c).
- Ein Haus mit zwei gewählten Eigentümern bekommt einen **Ring**, keine Mischfarbe.
- Speichern eines Vergleichs = die URL. „Meine Ansichten“ im Browser kommt mit der Werkstatt.
- Präzision vor Vollständigkeit: Eigentümer-Knöpfe nur für geprüfte Eigentümer (Index `suche/eigentuemer.json`).

## 2. Daten: Kurzindex der Adressen

`schreibe_paket` schreibt zusätzlich `site/daten/adressen_kurz/<x>.json` für `x` = erstes Zeichen der
Adress-ID (16 Dateien). Inhalt: `{ "<id>": [lon, lat, stufe, stadtteil, strasse_heute, hausnr, historisch] }`
für alle Adressen mit Punkt (dieselbe Menge wie `adressen.geojson`). `lon`/`lat` auf 6 Nachkommastellen
gerundet. Funktion `baue_adressen_kurz(adressen) -> dict[str, dict[str, list]]`, Aufruf neben
`baue_adressscherben`. Die Adressscherben `adressen/<xx>.json` bleiben (Popup, Hausansicht, Ansichten).

Erwartete Größe: rund 300 KB je Datei (gzip etwa 100 KB); im Test mit dem echten Paket gemessen und im
Journal notiert.

`daten.js Lader`: neue Methode `adressenKurz(ids) -> Promise<Map<id, {id, lon, lat, stufe, stadtteil,
strasse_heute, hausnr, historisch}>>`. Sie lädt nur die Dateien, deren erstes Zeichen unter den IDs
vorkommt, parallel, und hält jede geladene Datei im vorhandenen JSON-Cache. Unbekannte IDs fehlen in der Map.

## 3. Zustand und URL

`zustand.js`: `eigentuemer` wird eine **Liste** von Namen (Standard `[]`), URL-Form
`eigentuemer=Name1|Name2|Name3` (Trenner `|`, weil kanonische Namen Kommas enthalten können und das Komma
in dieser URL-Form schon Listen wie `ebene=I,II` trennt). Beim Lesen: leere Teile und Dubletten
fallen weg, es bleiben höchstens fünf, Reihenfolge wie in der URL. Beim Schreiben: `join("|")`. Ein
einzelner Name ohne `|` liest sich als Liste mit einem Eintrag, alte Links bleiben gültig.

Die Auswahl in `app.js` (`auswahl = { art: "eigentuemer", name }`) wird `{ art: "eigentuemer", namen: [...] }`.
`beruf`, `ohdab` und `q` schließen Eigentümer weiterhin aus: wer einen Beruf wählt, leert die
Eigentümerliste und umgekehrt (heutige Regel, unverändert).

## 4. Treffer mit Gruppen

`suche.js treffer(auswahl, lader)` liefert zusätzlich `gruppen: [{ name, farbe, adressIds, zaehler }]`
(bei `art: eigentuemer` eine Gruppe je Name in Auswahlreihenfolge; bei allen anderen Arten `null`).
`adressIds` und `zaehler` des Gesamtergebnisses bleiben die Vereinigung, `zaehler` summiert über Gruppen.
Je Name eine Eigentümerscherbe; gleiche Präfixe werden nur einmal geladen.

Palette `FARBEN.gruppen = ["#dc2626", "#2563eb", "#16a34a", "#7c3aed", "#f59e0b"]` in `konfig.js`
(Rot, Blau, Grün, Violett, Orange). Die Farbe hängt am Platz in der Auswahl, nicht am Namen.

## 5. Karte

`karte.js setzeTreffer(adressIds, gruppen = null)`:

- ohne `gruppen` wie heute: Feature-State `{ treffer: true }` auf allen Quellen (`adressen`, `thema`).
- mit `gruppen`: je Adresse `{ treffer: true, gruppe: i, mehrfach: bool }`, `i` = Index der **ersten** Gruppe,
  die die Adresse enthält, `mehrfach` wahr, wenn sie in mehr als einer Gruppe liegt.

`setzeFilter`: Farbe
`["case", ["boolean", ["feature-state", "treffer"], false], ["match", ["feature-state", "gruppe"], 0, F0, 1, F1, 2, F2, 3, F3, 4, F4, FARBEN.treffer], grund]`.
Ohne `gruppe` im State greift `FARBEN.treffer` (Rot) wie heute. Ring: `circle-stroke-color`
`["case", ["boolean", ["feature-state", "mehrfach"], false], FARBEN.auswahl, "#fff"]` und
`circle-stroke-width` `["case", mehrfach, 2, HALO]` auf `adressen-haus` und `thema-haus`; die ungenauen
Symbole bekommen bei `mehrfach` `icon-halo-color` `FARBEN.auswahl`, `icon-halo-width` 1.

`passeEin(adressIds, koordinaten = null)`: mit `koordinaten` (Map id → [lon, lat] aus dem Kurzindex) wird
der Rahmen aus den Koordinaten gebildet, ohne Kachelabfrage; Rückgabe `true`. Ohne `koordinaten` wie heute.
`app.js sucheAusfuehren` ruft `passeEin` mit den Koordinaten aus dem Kurzindex; der `once("idle")`-Zweig
entfällt für alle Trefferarten, `zeigeInhalt` läuft einmal.

## 6. Sidebar

`app.js eigMap(ids)` wird `lader.adressenKurz(ids)`; `eigVon(id)` (Popup, Hausansicht) bleibt für die
volle Punktzeile bestehen, nutzt aber den Kurzindex nicht.

`sidebar.js zeigeTreffer(z, ergebnis, eig, titel)`:

- Bei `ergebnis.gruppen`: über der Kopfzeile eine **Vergleichsleiste** `<div class="vergleich">`, je Gruppe
  eine Zeile: Farbpunkt, Name, „n Häuser · m Einträge“, die drei stärksten Stadtteile („Bochold 396 ·
  Borbeck-Mitte 235 · Gerschede 129“), ein Knopf `×` mit `data-eig-weg="<name>"`. Dahinter, wenn Adressen in
  mehreren Gruppen liegen: „k Häuser mit mehreren gewählten Eigentümern (Ring)“.
- Kopfzeile „n Treffer · m Häuser“ wie heute; die heutige Verteilung „Nach Stadtteil“ (ab 500 Häusern)
  entfällt bei Gruppen, weil die Leiste sie je Gruppe zeigt.
- Trefferzeilen bekommen bei Gruppen einen Farbpunkt (`<span class="punkt" style="background:F">`), bei
  `mehrfach` zusätzlich die Klasse `mehrfach` (Ring per CSS). Sortierung: Gruppen in Auswahlreihenfolge,
  innerhalb wie heute.
- `_verteilung` wird zu `verteilung(adressIds, zaehler, eig, n = 3) -> [[stadtteil, zahl]]` (exportiert,
  testbar) und dient der Leiste.

„Größte Eigentümer“ (`zeigeThema`): Knöpfe tragen `aria-pressed="true"` und `style="background:F;
color:#fff"`, wenn der Name gewählt ist. Klick: gewählt → entfernen; nicht gewählt und weniger als fünf →
anhängen; sonst Hinweis `<div class="hinweis warn">Höchstens fünf Eigentümer gleichzeitig.</div>` unter der
Liste (2 s, dann weg). Die Sidebar kennt dafür `z.eigentuemer` und ruft `onZustand({ eigentuemer: neu, q: "",
beruf: "", ohdab: "", id: "" })`.

Suchfeld: bei genau einem gewählten Eigentümer steht sein Name im Feld (wie heute); bei mehreren bleibt es
leer, die Leiste trägt die Auswahl. „Suche leeren“ leert `eigentuemer` komplett.

Suchvorschlag Gruppe „Eigentümer“ (`setzeVorschlaege`): ist mindestens ein Eigentümer gewählt, zeigt der
Vorschlag rechts ein `+` (`<span class="plus">+</span>`), und `waehleVorschlag` hängt den Namen an statt zu
ersetzen (bei fünf: Hinweis wie oben). Ohne Auswahl ersetzt er wie heute.

## 7. Popup und Hausansicht

`popup.js`: Bei Teil-II-Einträgen mit `eigentuemer_kanon` wird der Name in `popupName` und im Feld
„Zugeordnet“ zu `<button class="eiglink" data-eigentuemer="<name>">…</button>`. `app.js` registriert auf Popup
und Hausansicht einen Klick-Handler: leere Auswahl → `eigentuemer: [name]`; sonst anhängen (höchstens fünf,
sonst Hinweis); bereits enthalten → nichts. Der Knopftext: „alle Häuser dieses Eigentümers“ bei leerer
Auswahl, „zum Vergleich hinzufügen“ sonst (Titel-Attribut, sichtbar bleibt der Name).

## 8. CSV

`exportcsv.js csvAusTreffern`: bei `ergebnis.gruppen` zusätzliche letzte Spalte `eigentuemer` in beiden
Formen (je Eintrag und je Adresse) mit dem Namen der Gruppe; Adressen in mehreren Gruppen erscheinen je
Gruppe einmal. Dateiname `essen1936-eigentuemer-vergleich.csv` bei mehr als einem Namen.

## 9. Legende

`app.js zeichneLegende`: bei Gruppen statt der Zeile „Suchtreffer“ je Gruppe eine Zeile mit Farbpunkt und
Name, danach „Ring = mehrere gewählte Eigentümer“, wenn `mehrfach` vorkommt.

## 10. Dateien

- `pipeline/lib/karte_export.py`: `baue_adressen_kurz`, Aufruf in `schreibe_paket`; README Dateiliste.
- `site/js/konfig.js` (`FARBEN.gruppen`), `daten.js` (`adressenKurz`), `zustand.js` (Liste, `|`),
  `suche.js` (`gruppen`), `karte.js` (`setzeTreffer`, `setzeFilter`, `passeEin`), `sidebar.js`
  (Vergleichsleiste, Knöpfe, Vorschlag-Plus, `verteilung`), `app.js` (Auswahl, Hinweis, Popup-Handler,
  Legende, CSV-Name), `popup.js` (`eiglink`), `exportcsv.js` (Spalte), `site/css/stil.css`.
- `docs/superpowers/specs/2026-09-24-perspektiven-werkstatt-design.md` §10 „Später“: Bündelung mehrerer
  Eigentümer zu einer Gruppe, „Meine Ansichten“.

## 11. Tests

- `tests/test_karte_export.py`: `baue_adressen_kurz` verteilt nach erstem Zeichen, sieben Werte je Adresse,
  gerundete Koordinaten, nur Adressen mit Punkt; Paket enthält `adressen_kurz/`.
- `site/tests/zustand.test.js`: Liste lesen/schreiben, `|`, Dubletten, Kappung auf fünf, alter Einzelname.
- `site/tests/suche.test.js`: `treffer` mit zwei Eigentümern liefert Gruppen in Reihenfolge, Vereinigung der
  IDs, summierte Zähler, Scherbe je Präfix nur einmal geladen.
- `site/tests/karte_ebenen.test.js`: `setzeTreffer` mit Gruppen setzt `gruppe`/`mehrfach`; Farbausdruck mit
  `match` auf `gruppe`; Ring-Ausdruck; `passeIn` mit Koordinaten ohne Kachelabfrage.
- `site/tests/daten.test.js` (neu oder bestehend): `adressenKurz` lädt nur betroffene Dateien, einmal.
- `site/tests/sidebar.test.js` oder `popup.test.js`: `verteilung` Top 3; Trefferzeile mit Farbpunkt und
  `mehrfach`; `eiglink` nur bei `eigentuemer_kanon`.
- `site/tests/exportcsv.test.js`: Spalte `eigentuemer`, Adresse in zwei Gruppen zweimal.
- Sichtprüfung (Playwright, `?debug=1`): Thema Besitz, `eigentuemer=Fried. Krupp AG|Stadt Essen`: Zeit vom
  Klick bis zur gefüllten Liste unter 1,5 s bei warmem Cache; zwei Farben auf der Karte; Ring bei einem Haus
  in beiden Gruppen (falls vorhanden, sonst konstruiert); Knöpfe gefüllt; Legende mit zwei Zeilen.

## 12. Offen

- Der Kurzindex verdoppelt Koordinaten (Kacheln, Adressscherben, Kurzindex). Sollte das Paket zu groß
  werden, könnten die Adressscherben auf die Felder schrumpfen, die Popup und Hausansicht brauchen.
- Farbe je Name stabil (Hash) statt je Platz wurde verworfen; falls Nutzer sich über wechselnde Farben
  wundern, wäre das die Alternative.
- Beruf und OhdAB profitieren vom Kurzindex, bekommen aber keine Gruppen; Berufsgruppen sind Werkstatt (5c).
