# Themenkacheln: feine Punktkarte aus der Vogelperspektive

Stand 2026-09-29. Ergebnis des Brainstormings mit Christos nach dem Bergbau-Kapitel.

## 1. Anlass und Entscheidungen

Bei aktivem Thema (Screenshot Bergbau, Zoom 12) zeigt die Karte nur einen Bruchteil der Adressen. Zwei Ursachen,
beide Darstellungsentscheidungen, keine Datenlücken:

1. `adressen.pmtiles` wird mit `--drop-densest-as-needed` und Basiszoom 15 gebaut. Je Zoomstufe darunter bleibt
   etwa jeder 2,5te Punkt; bei Zoom 12 sind das rund 6 % der Adressen.
2. `karte.js setzeFilter` blendet unterhalb von Zoom 12 alle Adressen mit weniger als 5 Einträgen aus
   („Stadtansicht nicht zulaufen lassen“), und der Kreisradius (4–10 px nach Zahl der Einträge) schrumpft nicht
   mit dem Zoom.

Entscheidungen (Christos):

- Die feine Ansicht gilt für **Themen** (Bergbau, Besitz, Berufe, künftige), nicht für die Grundansicht mit allen
  Einwohnern, Eigentümern und Gewerben. Begründung: Ballungen vergleicht man in Themen und Schlaglichtern; die
  Grundansicht braucht sie nicht, und 70.000 Punkte ohne Ausdünnung wiegen je Kachel 0,7–2 MB.
- Bei aktivem Thema gilt die feine Ansicht **immer**, ohne eigenen Schalter.
- Präzision vor Vollständigkeit: jeder Punkt bleibt eine Adresse. Keine Heatmap, kein Clustering.

Messung (tippecanoe ohne Ausdünnung, größte Kachel, gzip):

| Kachelinhalt | Adressen | Zoom 9 | Zoom 12 |
|---|---|---|---|
| alle Adressen, alle Felder | 70.316 | ≈ 2 MB | 0,9 MB |
| alle Adressen, nur n_I/n_II/n_III | 70.316 | 750 KB | 341 KB |
| Thema Berufe (Teil I, Feld niveau) | 62.794 | 669 KB | 304 KB |
| Thema Besitz (Teil II, Feld besitz) | 31.453 | 335 KB | 163 KB |
| Thema Bergbau (Treffer, vier Zählfelder) | 18.350 | 158 KB | 81 KB |

## 2. Daten: eine Kacheldatei je Thema

`schreibe_paket` schreibt für jedes Thema mit `freigegeben: true` eine Datei `site/daten/themen/<id>.pmtiles`,
Ebene `adressen`, Zoom 9–15, **ohne Ausdünnung** (`-r1`, `--no-feature-limit`, `--no-tile-size-limit`).

**Auswahl der Adressen** (`thema_adressen(thema, adressen)`): eine Adresse gehört zum Thema, wenn die Summe der
Zählfelder der Themen-Ebenen (`filter.ebenen`, Vorgabe alle drei) größer 0 ist und, bei `filter.merkmal`,
`m_<merkmal>` größer 0 ist und, bei `schalter`, mindestens ein Schalterfeld größer 0 ist.

**Felder je Punkt** (`thema_felder(thema)`), sonst nichts:

- immer: `id`, `stufe`, `stadtteil`, `n_I`, `n_II`, `n_III` (die Karte filtert nach Stufe, Stadtteil und
  aktiven Ebenen; die drei Zahlen sind billig und halten den Ebenenwechsel bei aktivem Thema funktionsfähig);
- `farbe.feld` bei `art: kategorien`; `m_<merkmal>` bei `art: einfach`/`stufen` mit Merkmal;
- alle Schalterfelder `<praefix><klasse>`.

Umsetzung: `thema_geojson(thema, adressen) -> FeatureCollection` (Geometrie wie `punkt_feature`, nur die
Felder oben), Datei `build/themen/<id>.geojson` (nicht versioniert), dann
`tippecanoe_thema_befehl(geojson, pmtiles)`. `schreibe_themen` gibt weiterhin den Index zurück; dessen Einträge
bekommen `kacheln: true`, wenn die Datei geschrieben wurde. Themen ohne Freigabe (heute `akademiker`) bekommen
keine Datei. Ein Thema, dessen Farbfeld oder Schalterfeld in keiner Adresse vorkommt, ist ein Fehler im Export
(`ValueError`), keine leere Datei — sonst zeigte die Karte still nichts.

`adressen.pmtiles` bleibt unverändert (Ausdünnung, alle Felder). Die Grundansicht ändert sich nicht.

## 3. Karte: Themenquelle statt Hauptquelle

`karte.js` bekommt eine zweite Vektorquelle `thema` und zwei Ebenen `thema-haus` (circle) und `thema-ungenau`
(symbol), gleich gebaut wie `adressen-haus`/`adressen-ungenau`, Quelle `thema`, `source-layer: adressen`,
`promoteId: id`.

- `setzeThemaQuelle(id | null)`: bei `id` Quelle auf `themen/<id>.pmtiles` setzen (bestehende Quelle entfernen,
  neu anlegen, Ebenen neu anlegen; Klick-/Hover-Handler wie für die Hauptebenen, nur einmal registriert). Bei
  `null` Quelle und Ebenen entfernen.
- Sichtbarkeit: Themenquelle aktiv → `adressen-haus`/`adressen-ungenau` `visibility: none`, Themenebenen
  sichtbar; sonst umgekehrt. `adressen-auswahl` (Ring) bleibt auf der Hauptquelle.
- `setzeFilter` legt Filter und Farbe auf **beide** Ebenenpaare (dieselben Bedingungen: Stufe, Stadtteil, Ebenen,
  Merkmal, Schalter), aber: die Regel `[">=", zoom, 12] oder n ≥ 5` gilt nur für die Hauptebenen. Auf den
  Themenebenen gibt es keine Zoomgrenze.
- Radius auf den Themenebenen: `["interpolate", ["linear"], ["zoom"], 10, 1, 12, 2, 14, RADIUS]` mit `RADIUS`
  wie heute (nach Zahl der Einträge); Halo (`circle-stroke-width`) wie heute per `HALO` (0 unter Zoom 12).
  Das gestrichelte Symbol der ungenauen Adressen skaliert mit demselben Faktor.
- Treffer (`setzeTreffer`) setzen den Feature-State zusätzlich auf der Themenquelle, wenn sie existiert;
  `_deckkraftSetzen` deckt beide Paare ab.
- Nach einem Stilwechsel (`ebenenAufsetzen`) wird die Themenquelle mit angelegt.

`app.js wendeThemaAn`: nach `ladeThema` `karte.setzeThemaQuelle(t && t.kacheln ? t.id : null)`. `t.kacheln`
kommt aus `themen/index.json`. Ein freigegebenes Thema ohne Kacheldatei (Datenpaket älter als dieser Stand)
verhält sich wie heute.

Klick und Hover reichen `properties.id` weiter; Popup und Hausansicht laden die Adresse über die ID aus den
Scherben, brauchen also keine weiteren Felder in der Kachel.

## 4. Themen-Texte

`kuratierung/themen/bergbau.json` `grundlage`: „noch ungeprüft“ → „geprüft bis auf vier Grenzfälle“ (Stand
2026-09-29, 56 von 60 Normen). `docs/bergbau.md` „Offen“ entsprechend.

## 5. Dateien

- `pipeline/lib/karte_export.py`: `thema_felder`, `thema_adressen`, `thema_geojson`, `tippecanoe_thema_befehl`,
  `schreibe_themen(quelle, ausgabe, adressen=None, kacheln=False)`; Aufruf in `schreibe_paket` nach `gruppiere`.
- `site/js/karte.js`: Quelle `thema`, Ebenen `thema-haus`/`thema-ungenau`, `setzeThemaQuelle`, `setzeFilter`
  und `_deckkraftSetzen` und `setzeTreffer` für beide Paare, Radius mit Zoomfaktor.
- `site/js/app.js`: `wendeThemaAn` ruft `setzeThemaQuelle`.
- `site/js/themen.js`: `ladeThema` reicht `kacheln` aus dem Index durch.
- `kuratierung/themen/bergbau.json`, `docs/bergbau.md`, README (Themenformat: Kacheldatei je Thema, Felder).

## 6. Tests

- `tests/test_karte_export.py`: `thema_felder` für Bergbau (Schalter + Farbfeld), Besitz (Farbfeld), Merkmal-Thema;
  `thema_adressen` filtert nach Ebenen/Schaltern; `thema_geojson` trägt nur die genannten Felder;
  `tippecanoe_thema_befehl` ohne `--drop-densest-as-needed`, mit `-r1`, Zoom 9–15; Index mit `kacheln`;
  Fehler bei Thema ohne Treffer.
- `site/tests/karte_ebenen.test.js` (bestehendes Muster mit Karten-Attrappe): Filter ohne Zoomgrenze auf
  `thema-haus`, mit Zoomgrenze auf `adressen-haus`; Sichtbarkeit wechselt mit `setzeThemaQuelle`; Radius der
  Themenebene ist ein Zoom-Interpolate; Treffer-State auf beiden Quellen.
- `site/tests/themen.test.js`: `ladeThema` liefert `kacheln`.
- Sichtprüfung (Playwright): Thema Bergbau bei Zoom 11 und 12 zeigt alle 18.350 Treffer-Adressen (Zahl der
  gerenderten Features per `queryRenderedFeatures` gegen Erwartung), Grundansicht unverändert; Kachelgrößen
  laut Tabelle in §1.

## 7. Offen

- **Werkstatt (5c):** Nutzergruppen aus Berufsnormen haben keine vorgerechneten Kacheln. Vorschlag für die
  Werkstatt-Spec: kompakte Adressliste (id, lon, lat, Berufs-IDs) im Browser zu einer GeoJSON-Quelle bauen,
  dieselben Ebenen `thema-haus`/`thema-ungenau` mit dieser Quelle. Hier nicht umgesetzt.
- Thema `akademiker` ist nicht freigegeben und bekommt deshalb keine Kacheldatei; sobald es freigegeben wird,
  greift die Mechanik (Merkmalsfeld `m_akademiker`, 2.393 Adressen) ohne weitere Änderung.
- Ladezeit am Handy für das Thema Berufe (≈ 1,2 MB bei Zoom 12) nach der Umsetzung messen.
