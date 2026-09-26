# Perspektiven — Kapitel-Schema

Stand 2026-09-25: Drei Kapitel angelegt (Wohneigentum; Soziale Stellung; Gewerbe und Versorgung), alle
mit `freigegeben: false` — die Texte sind Platzhalter, keins ist freigegeben.

Die Scrollytelling-Seite „Perspektiven" (Spec §6.2) besteht aus Kapiteln. Jedes Kapitel ist eine JSON-Datei
unter `kuratierung/perspektiven/<id>.json`, die der Projektleiter von Hand pflegt (mit LLM-Vorschlag,
Handprüfung — wie bei den anderen Kuratierungstabellen). `pipeline/lib/perspektiven.py` prüft, lädt und
exportiert diese Kapitel; `pipeline/06_karte_export.py` ruft das bei jedem Lauf auf.

## Schema

Pflichtfelder eines Kapitels (`PFLICHT` in `pipeline/lib/perspektiven.py`):

| Feld | Typ | Bedeutung |
| --- | --- | --- |
| `id` | str | Dateiname ohne `.json`, zugleich URL-Baustein |
| `reihenfolge` | int | Sortierung im Index und auf der Seite |
| `titel` | str | Kapitelüberschrift |
| `untertitel` | str | Kurzzeile unter dem Titel |
| `freigegeben` | bool | siehe „Freigabe" unten |
| `einleitung` | str | einleitender Fließtext vor dem ersten Schritt |
| `schritte` | list[dict] | die Scrollama-Schritte, siehe unten |
| `grenzen` | str | Fließtext zu Reichweite und Lücken der Daten, mit Platzhaltern (siehe unten) |
| `quellen` | list[str] | Quellenangaben, am Kapitelende angezeigt |

Jeder Schritt in `schritte` (`PFLICHT_SCHRITT`):

| Feld | Typ | Bedeutung |
| --- | --- | --- |
| `id` | str | eindeutig innerhalb des Kapitels (Kurzform `wie:<id>` verweist darauf) |
| `text` | str | der Scrollama-Text neben/über der Ansicht |
| `beschreibung` | str | Alt-Text / Beschreibung der Ansicht für Redaktion und Barrierefreiheit |
| `hervorheben` | list[str] | Namen (Stadtteile, Eigentümer, …), die die Ansicht optisch hervorhebt |
| `ansicht` | dict | siehe unten |

Jede `ansicht` (`PFLICHT_ANSICHT`) trägt dieselben Felder wie die Ansicht-Definition der Karte (Global
Constraints der Spec), mit einer Erweiterung in `form`:

| Feld | erlaubte Werte | Bedeutung |
| --- | --- | --- |
| `daten` | `stellung, gruppe, niveau, besitz, gewerbe` | welche Kuratierung die Ansicht einfärbt |
| `ebene` | `adresse, strasse, stadtteil, hex` | Aggregationsebene |
| `form` | `karte, stadtteilkarte, bubbles, balken, multiples, rangliste` | Darstellungsform |
| `gruppen` | list[dict] oder `"wie:<schritt-id>"` | siehe „Gruppen und die Kurzform `wie:`" |
| `kaufleute` | `unbestimmt, angestellte, selbstaendige` | Kaufleute-Filter wie in der Karte |
| `unsicher` | bool | unsichere Zuordnungen mit anzeigen? |
| `mass` | `anteil, dominant, mischung, dichte` | Kennzahl je Einheit |
| `bezug` | str | bei `mass anteil`/`dichte`: Name der Bezugsgruppe (muss in `gruppen` vorkommen) |
| `min_n` | int ≥ 0 | Mindestzahl der Nennungen je Einheit (bei `mass: "dichte"`: der Teil-I-Einträge der Einheit), sonst grau/ausgeblendet |
| `filter` | dict | zusätzliche Einschränkung, z. B. `{"top": 15}` bei Ranglisten |
| `karte` | dict oder `null` | Kartenausschnitt, falls die Ansicht einen eigenen braucht |

`form: "stadtteilkarte"` ist in den Kapiteln der Name für `form: "karte"` mit `ebene: "stadtteil"` als
eigenständiges Perspektiven-SVG (nicht die interaktive MapLibre-Karte der Basiskarte) — deshalb führt das
Schema `stadtteilkarte` zusätzlich zu `karte` als eigenen Wert. `mass: "dichte"` ist nur mit
`daten: "gewerbe"` zulässig (Dichte ergibt nur bei Gewerbebetrieben je Fläche/Adresse einen Sinn); jede
andere Kombination meldet `pruefe_kapitel` als Fehler.

`pruefe_kapitel(k) -> list[str]` gibt eine Liste von Fehlertexten zurück (leer = gültiges Kapitel): fehlende
Pflichtfelder, unbekannte Werte in `daten/ebene/form/mass/kaufleute`, doppelte Schritt- oder Gruppennamen,
unvollständige Gruppen (`name`, `aus`, `farbe` fehlen), `bezug`, der keine der `gruppen` ist, `min_n` das
keine ganze Zahl ≥ 0 ist, und die `mass dichte`/`daten gewerbe`-Kopplung.

## Gruppen und die Kurzform `wie:`

Eine Gruppe ist `{"name": str, "aus": list[str], "farbe": str}` — `aus` sind die Rohwerte der jeweiligen
Kuratierung (z. B. bei `daten: "besitz"` die Kategorien aus `kuratierung/eigentuemer.csv`), `farbe` ein
Hex-Farbwert. Wiederholt ein Schritt dieselben Gruppen wie ein vorheriger (z. B. die Bubbles- und die
Rangliste-Ansicht dieselben Besitzklassen wie die Anteile-Ansicht), spart `"gruppen": "wie:<schritt-id>"`
die Wiederholung. `lade_kapitel` löst das beim Laden auf: Es kopiert die Gruppenliste des Schritts mit
dieser `id` (tiefe Kopie, damit spätere Änderungen der einen Ansicht die andere nicht mitverändern) und
ersetzt damit die Kurzform. Verweist `wie:` auf eine nicht vorhandene Schritt-`id`, bricht das Laden mit
einem `KeyError` ab — das ist bewusst laut, statt eine leere Gruppenliste zu erfinden. `pruefe_kapitel` prüft
erst nach dieser Auflösung, sieht also nur noch echte Gruppenlisten.

## Platzhalter in `grenzen`

Der Text in `grenzen` erklärt am Kapitelende Reichweite und Lücken der zugrunde liegenden Daten. Er darf
folgende Platzhalter enthalten, die die Seite beim Rendern aus `site/daten/kennzahlen.json` einsetzt:

- `{adressen}`, `{besitz_geprueft}`, `{besitz_spanne}`, `{besitz_nummer}`, `{berufe_geprueft}`, `{stellung_geprueft}`, `{stellung_vorschlag}`,
  `{stellung_unbestimmt}`, `{gewerbe_geprueft}`, `{gewerbe_entschieden}`, `{gewerbe_vorschlag}`,
  `{stadtteil_polygon}`, `{stand}` — jeweils der gleichnamige Wert aus `kennzahlen.json`.
- `{besitz_geprueft_prozent}` — `besitz_geprueft / adressen`, auf eine Nachkommastelle gerundet (analog
  wären `{berufe_geprueft_prozent}` usw. denkbar, sind aber für Kapitel 1 nicht nötig und daher nicht
  implementiert — YAGNI, bis ein weiteres Kapitel sie braucht).

`{besitz_geprueft_prozent}` ist damit derzeit der **einzige** `_prozent`-Platzhalter; jeder andere
(`{stellung_geprueft_prozent}`, `{eigentuemer_geprueft_prozent}` …) bleibt ungefüllt im Text stehen, weil
die betreffenden Kennzahlen entweder schon Prozentwerte sind oder einen anderen Nenner als `adressen`
haben. Erweitert wird die Liste in `PROZENT_BASIS` in `site/js/perspektiven_modell.js`.

Diese Platzhalter sind bewusst **nicht** Teil von `pruefe_kapitel` — das Schema prüft nur die Struktur, nicht
den Text. Ein Tippfehler in einem Platzhalternamen fällt erst beim Rendern der Seite auf.

## Freigabe (`freigegeben`, `?vorschau=1`)

`freigegeben: false` ist der Normalzustand während der Bearbeitung: Das Kapitel wird exportiert und geprüft
(`pruefe_kapitel` muss auch für unfertige Kapitel leer sein — nur der Text ist Platzhalter, die Struktur
muss stimmen), erscheint aber auf der veröffentlichten Seite **nicht**. Es ist nur sichtbar, wenn die Seite
mit dem Query-Parameter `?vorschau=1` aufgerufen wird — damit kann der Projektleiter ein Kapitel im
Kontext der echten Seite prüfen, ohne es für Besucher freizuschalten. `kapitel_index` liefert `freigegeben`
für jedes Kapitel mit; die Seite entscheidet anhand dieses Felds (und des Query-Parameters), was sie
anzeigt. Kapitel 1 „Wohneigentum 1936" ist mit `freigegeben: false` angelegt, solange die Platzhaltertexte
nicht durch geprüfte Texte ersetzt sind.

## Export

`schreibe_paket(..., perspektiven=<Ordner>)` (Parameter am Ende der Signatur, Default `None` — ohne
Angabe wird nichts exportiert) lädt alle Kapitel aus dem Ordner mit `lade_kapitel`, prüft jedes mit
`pruefe_kapitel` und bricht bei einem ungültigen Kapitel mit `ValueError` ab (Fehlertexte zusammengefasst,
Präfix `kuratierung/perspektiven:`) — ein fehlerhaftes Kapitel darf den Export nicht schweigend
durchrutschen lassen. Bei Erfolg schreibt es:

- `site/daten/perspektiven/index.json` — `kapitel_index(kapitel)`: `id, titel, untertitel, freigegeben,
  reihenfolge`, sortiert wie geladen (nach `reihenfolge`, bei Gleichstand nach `id`).
- `site/daten/perspektiven/<id>.json` — je Kapitel die vollständige, aufgelöste JSON (inklusive der durch
  `wie:` ersetzten Gruppenlisten).

`pipeline/06_karte_export.py` ruft `schreibe_paket(..., perspektiven=W / "kuratierung" / "perspektiven")`
auf und löscht vor dem Export den alten `site/daten/perspektiven`-Ordner (wie bei `haus`, `suche`,
`adressen`, `themen`, `ebenen`, `layout`), damit keine verwaisten Kapiteldateien liegen bleiben.

## Arbeitsablauf für den Projektleiter

1. Kapitel-JSON unter `kuratierung/perspektiven/<id>.json` anlegen oder bearbeiten (LLM-Vorschlag möglich,
   Handprüfung Pflicht — wie bei den anderen Kuratierungstabellen). Neue Kapitel bekommen eine eigene
   `id` und `reihenfolge`.
2. `python3 pipeline/06_karte_export.py` (oder `--ohne-kacheln` für einen schnellen Lauf ohne PMTiles)
   laufen lassen. Ein ungültiges Kapitel bricht den Export mit `ValueError` und den konkreten Fehlern ab.
3. Seite lokal mit `werkzeuge/serve.py` öffnen (nicht `python3 -m http.server` — das kann keine Range-Requests
   für PMTiles) und mit `?vorschau=1` aufrufen, solange `freigegeben: false` ist.
4. Erst wenn Texte und Ansicht geprüft sind: `freigegeben: true` setzen und erneut exportieren.

## Offene Punkte für 5c

- Rangliste der 15 größten Eigentümer (Spec §6.2) braucht eine Layout-Rangliste; in 5b nicht baubar.
  Die Rangliste-Form ordnet nur Einheiten einer Ebene (Straßen, Stadtteile, Hexfelder), keine Einträge
  eines Layouts — der Schritt `rangliste` in `wohneigentum.json` zeigt deshalb vorerst die Stadtteile
  nach Privatbesitz-Anteil.
- `unsicher` wirkt bisher nur bei `daten=niveau`; für `stellung` (Automatik-Vorschläge ausblenden,
  `n_stellung_hand`) in 5c.
