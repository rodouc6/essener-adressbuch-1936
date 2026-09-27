# Karten-UI: Popup nach Teilen, Ebenen-Hervorhebung, Punkt-Halo, Bedienleiste, Zechensymbol — Design

Stand 2026-09-28. Schritt 3 der abgestimmten Reihenfolge (Journal 2026-09-27). Quelle der Anforderungen:
Christos' Notizen vom 25.9. (`persNotizen-2026-09-25`, Abschnitt „UI der Karte“) und das Brainstorming
vom 28.9. (Mockups `build/mockups/popup.html`, `popup_mock.png`, `halo_mock.png`).

## 1. Ziel

Die Karte (`site/karte.html`) wird in fünf Punkten aufgeräumt, ohne Datenformat, URL-Zustand oder Sidebar zu
ändern:

1. Das Popup eines Adresspunkts trennt Kopf und Einträge und gruppiert die Einträge nach Teil.
2. Bei ein oder zwei aktiven Ebenen hebt das Popup deren Teile farbig hervor.
3. Die Adresspunkte bekommen einen weißen Halo, der mit dem Zoom wächst.
4. Die drei Knöpfe rechts oben werden zu einem Symbolknopf mit aufklappbarem Feld; der Stadtplan-Regler
   wird stufenlos.
5. Das Zechensymbol wird das Schlägel-und-Eisen-Zeichen nach DIN 21800 von Wikimedia Commons, als
   SDF-Symbol mit Halo, mit Nachweis im Impressum.

Nicht Teil dieses Schritts (bewusst verschoben, mit der Sidebar-Diskussion): Reiter in der Hausansicht,
Öffnen von Popup und Hausansicht mit einem Klick, Zoomstufen-Prüfung der Punktdichte.

## 2. Popup nach Teilen (`site/js/popup.js`, `popupHtml`)

Das Popup ist die Visitenkarte des Hauses; der Lesestoff bleibt in der Hausansicht der Sidebar
(`hausHtml`, unverändert). Zwei-Klick-Weg: Punkt → Popup → „Haus im Detail ›“ → Sidebar.

**Kopf.** Heutige Adresse fett (wie bisher `heutigeAdresse`), darunter grau „<historische Adresse> im Buch“
(nur wenn `strasse_heute` gesetzt ist, wie bisher). Dann eine Kennzeile, grau, Elemente mit „ · “ verbunden:

- Präzision nur, wenn nicht hausgenau: `strasse` → „nur straßengenau“, `stadtplan` → „Punkt vom Stadtplan
  1935“, `unbekannt` → „Präzision unbekannt“; in der Warnfarbe (`.praez-strasse`/`.praez-stadtplan`).
- Die Zähler der vorhandenen Teile: „11 Einwohner · 1 Eigentümer · 1 Gewerbe“ (wie `zaehlerText`).

Die Zeile „hausgenau verortet“ entfällt im Popup (in der Hausansicht bleibt sie).

**Teile.** Feste Reihenfolge Einwohner (I), Eigentümer (II), Gewerbe (III); leere Teile fehlen. Je Teil eine
Überschrift `<h4>` in Kapitälchen-Grau: „Einwohner · 11“ (Zahl nur, wenn > 1). Darunter die Zeilen.

**Zeilen.** Name fett, Zusatz grau nach „ · “:

- Einwohner: `beruf_norm`, sonst die Buchschreibung `beruf` kursiv mit `title="Schreibung im Buch, Beruf noch
  nicht zugeordnet"`; ohne Beruf nichts. `stand` wie bisher nach dem Beruf. Etage entfällt im Popup.
- Eigentümer: Name = `eigentuemer_kanon`, sonst `firma`, sonst „Name, Vorname“; Zusatz = Besitzklasse
  (`KATEGORIEN[kategorie]`) wenn `kategorie` gesetzt ist. Bei `pruefung === "regel"` Zusatz „Privatperson
  (Regel)“, damit die Herkunft sichtbar bleibt.
- Gewerbe: Name = `firma`, sonst „Name, Vorname“; Zusatz = `rubrik` (Buchrubrik), sonst nichts.

**Kappung je Teil.** Am Laptop höchstens 4 Zeilen je Teil, auf dem Handy (`kompakt`) 2. Darüber hinaus
„und 1 weitere Zeile“ bzw. „und n weitere Zeilen“ (einheitlich für alle Teile, kein Genus-Problem). Die Kappung gilt
je Teil, nicht über das Popup hinweg, damit jedes Popup alle vorhandenen Arten von Einträgen zeigt.

**Fuß.** Immer „Haus im Detail ›“ (`data-mehr`), auch wenn nichts gekappt wurde, damit der Weg zur Belegkette
in jedem Popup gleich ist. Klick auf eine Namenszeile (`data-eintrag`) öffnet wie bisher die Hausansicht mit
Sprung zum Eintrag.

**Signatur.** `popupHtml(eig, eintraege, kompakt, ebenen = ["I","II","III"])` — der vierte Parameter trägt die
aktiven Ebenen für §3; Aufruf in `app.js` gibt `zustand.ebene` mit.

**Kein Umbau der Hausansicht**; `nameZeile`/`eintragHtml`/`hausHtml` bleiben.

## 3. Ebenen-Hervorhebung im Popup

Bei genau einer oder genau zwei aktiven Ebenen (`ebenen.length` 1 oder 2) bekommen die Teile dieser
Ebenen die Klasse `hervor` und die CSS-Variable `--f` mit der Ebenenfarbe aus `FARBEN` (I `#1d4ed8`,
II `#ca8a04`, III `#c2410c`): linke Kante 3 px in `--f`, Überschrift in `--f`. Nicht gewählte Teile bleiben
grau stehen (Entscheidung 28.9.: das Popup zeigt das ganze Haus; die Ebene sagt nur, warum der Punkt auf der
Karte ist). Bei drei Ebenen keine Hervorhebung. Reihenfolge und Kappung ändern sich durch die Hervorhebung
nicht.

## 4. Punkt-Halo (`site/js/karte.js`)

Beide Punktarten bekommen einen weißen Rand, der mit dem Zoom wächst:

```
HALO = ["interpolate", ["linear"], ["zoom"], 12, 0, 14, 1, 16, 1.6]
adressen-haus:    circle-stroke-color "#fff", circle-stroke-width HALO
adressen-ungenau: icon-halo-color "#fff",     icon-halo-width HALO
```

Gesetzt in `_eigeneEbenen()` (Ebenendefinition), nicht in `setzeFilter` — der Halo hängt nicht vom Zustand
ab. Die Deckkraft des Halos folgt der des Punktes (`circle-stroke-opacity` = `circle-opacity`-Ausdruck aus
`_deckkraftSetzen`, sonst hätten gedimmte Punkte einen vollen weißen Ring). Farben (`FARBEN.neutral` bei
drei Ebenen, Ebenenfarbe bei einer, Treffer rot, Auswahlring) bleiben. Belegt durch `halo_mock.png`:
Gewinn vor allem bei sich überlappenden Punkten; in der Stadtansicht (Zoom ≤ 12) kein Halo, damit die
Innenstadt nicht zu weißen Flecken verklumpt.

## 5. Bedienleiste (`site/js/app.js`, `zeichneSteuerung`; `site/css/stil.css`)

Form A aus dem Brainstorming: ein Symbolknopf, ein aufklappbares Feld.

**Knopf.** `<button class="ebenenknopf" aria-expanded aria-label="Kartenebenen">` rechts oben an der Stelle
der heutigen `.steuerung`, weißes Rundquadrat 32 × 32 px im Stil der MapLibre-Zoomknöpfe darunter, mit einem
Stapel-Symbol (drei versetzte Rauten, Inline-SVG). Trägt einen kleinen farbigen Punkt oben rechts
(`.ebenenknopf.aktiv::after`), wenn ein Wert vom Standard abweicht: `karte !== "positron"`, `zechen`, oder
`plan > 0`.

**Feld.** `<div class="ebenenfeld" hidden>` links neben dem Knopf (Laptop) bzw. unter dem Knopf (Handy),
weiß, Schatten wie `.legende`, drei Zeilen:

1. Grundkarte: zwei Schaltflächen „dezent“ | „detailliert“ als Umschaltgruppe (`aria-pressed`), wirkt
   auf `karte`.
2. Zechen: Schalter mit dem Schlägel-und-Eisen-Symbol (Inline-SVG aus §6) und Text „Zechen“,
   `aria-pressed`, wirkt auf `zechen`.
3. Stadtplan 1935: `<input type="range" min="0" max="1" step="0.01">` mit Prozentanzeige daneben; nur wenn
   `PLAN_FREIGEGEBEN`. `oninput` setzt `plan`, vom Regler auf zwei Nachkommastellen gerundet (`Math.round(v * 100) / 100`), damit die URL kurz
   bleibt. `zustand.js` liest beliebige Werte 0–1 (`zahl()`) und schreibt sie unverändert; dort ist nichts zu ändern.

**Öffnen/Schließen.** Klick auf den Knopf schaltet um. Escape und Klick in die Karte (`map.on("click")`,
bereits vorhanden für Adresspunkte; zusätzlich ein Klick-Handler auf `#karte` mit Capture, der nur das Feld
schließt) schließen das Feld. Der Zustand „offen“ liegt nicht in der URL.

**Legende-Knopf** (nur Handy) bleibt als zweiter Knopf unter dem Ebenenknopf, unverändert.

`zeichneSteuerung()` wird weiterhin nach jeder Zustandsänderung aufgerufen; sie darf das Feld dabei nicht
zuklappen (offen/zu in einer Modulvariable halten, HTML idempotent neu bauen).

## 6. Zechensymbol

**Datei.** `site/bilder/zeche.svg` wird ersetzt durch die Commons-Datei
`https://commons.wikimedia.org/wiki/File:Schlaegel_und_eisen-sign_of_mining.svg` (ein Pfad, eine Füllung,
430 × 430). Vor der Übernahme: XML-Kopf/Inkscape-Metadaten entfernen, `viewBox` setzen, Füllung auf
`#000` (die Farbe kommt bei SDF aus dem Stil), Datei unter 4 KB.

**Lizenz.** Commons weist die Datei als gemeinfrei aus (Baustein PD-self des Hochladers T. Rystau; Feld
Autor „unbekannt“, Quelle „Vorlage vom Heraldiker erhalten nach DIN 21800“, Datum 1989-06). Die Herkunft
ist damit nicht lückenlos; das Zeichen selbst ist ein genormtes Symbol aus wenigen Linien ohne
Schöpfungshöhe. Christos hat am 28.9. entschieden, die Datei zu nehmen. Impressum (`site/impressum.html`,
Abschnitt „Zechen“) bekommt den Satz:

> Das Zechensymbol (Schlägel und Eisen nach DIN 21800) stammt aus Wikimedia Commons
> (<a href="https://commons.wikimedia.org/wiki/File:Schlaegel_und_eisen-sign_of_mining.svg">Schlaegel und
> eisen-sign of mining.svg</a>, gemeinfrei).

**Karte.** `ICONS.zeche` wird SDF (`[..., true]`); Ebene `zechen` bekommt `icon-color` `#111`,
`icon-halo-color` `#fff`, `icon-halo-width` 1.5 (fest, die Zechen sind nur 24 Punkte), `icon-size` so, dass
das Symbol etwa 22 px breit ist (430-px-Vorlage bei `pixelRatio: 2` → `icon-size` ≈ 0.1; beim Umsetzen
messen). Dasselbe SVG wird inline im Zechen-Schalter des Ebenenfelds (§5) genutzt, dort per `currentColor`.

## 7. Dateien

| Datei | Änderung |
|---|---|
| `site/js/popup.js` | `popupHtml` neu (Kopf, Teile, Kappung, Hervorhebung); Helfer `teilHtml`, `popupZeile` |
| `site/js/app.js` | Popup-Aufruf mit `zustand.ebene`; `zeichneSteuerung` → Knopf + Feld; Schließen per Escape/Kartenklick |
| `site/js/karte.js` | Halo an `adressen-haus`/`adressen-ungenau` (+ stroke-opacity in `_deckkraftSetzen`); `zeche` als SDF mit Farbe/Halo |
| `site/css/stil.css` | `.popup-kopf .kenn`, `.teil`, `.teil h4`, `.teil.hervor`, `.weitere`, `.detail`; `.ebenenknopf`, `.ebenenfeld`, Range; Handy-Regeln |
| `site/bilder/zeche.svg` | Commons-Datei, bereinigt |
| `site/impressum.html` | Lizenzsatz Zechensymbol |
| `site/tests/popup.test.js` | Tests §8 |
| `site/tests/zustand.test.js` | Plan-Wert 0.35 wird gelesen und unverändert geschrieben |
| `README.md` | Absatz zur Karte: Ebenenknopf, Popup nach Teilen, Zechensymbol |

## 8. Tests (`node --test site/tests/`)

`popupHtml`:
- gruppiert nach Teil in fester Reihenfolge, leere Teile fehlen, Überschrift mit Zahl nur bei > 1.
- Einwohnerzeile nur mit Norm („Danhof, Karl · Arbeiter“), keine Buchschreibung, kein Pfeil.
- ohne Norm: Buchschreibung kursiv mit dem Tooltip.
- Eigentümer mit Kanon und Klasse; per Regel „Privatperson (Regel)“.
- Gewerbe mit Firma und Rubrik.
- Kappung je Teil: 5 Einwohner + 5 Gewerbe → 4 + „und 1 weitere Zeile“ je Teil; kompakt 2.
- Kennzeile: hausgenau ohne Präzisionstext; `strasse` → „nur straßengenau“.
- Hervorhebung: `ebenen=["III"]` → nur der Gewerbe-Teil hat `hervor` und `--f:#c2410c`; `["I","II"]` → zwei;
  drei Ebenen → keine Klasse.
- „Haus im Detail ›“ immer vorhanden.

Halo, Bedienleiste und Zechensymbol sind Darstellung in MapLibre bzw. DOM ohne Modell; sie werden headless
per Playwright gesichtet (Screenshot Laptop/Handy, Feld offen/zu, Zechen an, `aria-expanded`) und von
Christos im Browser abgenommen. `zustand.test.js` prüft, dass ein Plan-Wert mit zwei Nachkommastellen gelesen und geschrieben wird.

## 9. Offen / später

- Reiter in der Hausansicht, Ein-Klick-Öffnen von Popup und Sidebar (Sidebar-Diskussion).
- Zoomstufen und Punktdichte in der Stadtansicht.
- Stadtplan-Regler bleibt unsichtbar, bis `PLAN_FREIGEGEBEN` true ist (Rechte offen).
