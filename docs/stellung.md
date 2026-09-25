# Soziale Stellung

Stand 2026-09-24 (Teilprojekt 5a, Spec `docs/superpowers/specs/2026-09-24-perspektiven-werkstatt-design.md`
§5.1). Quellcode: `pipeline/lib/stellung.py` (Regeln), `werkzeuge/stellung_vorschlag.py` (Automatik),
`werkzeuge/berufe.html` (Handprüfung).

## Zweck

Vorbild ist die **„Stellung im Beruf“** der amtlichen Berufszählungen 1933 und 1939 (Arbeiter,
Angestellte, Beamte, Selbständige, mithelfende Familienangehörige …). Das Adressbuch übernimmt diese
Unterscheidung als Klassifikation, **keine Statusskala und keinen Sozialscore**: Die Klassen sind
nominal, nicht geordnet, und die Karte färbt nach Klasse, nicht nach einer Rangfolge von „unten“ nach
„oben“. Eine Bewertung „arm/reich“ ist ausdrücklich Sache der Nutzerin oder des Nutzers in der Werkstatt
(Teilprojekt 5c) — die Datengrundlage liefert nur die neun Klassen.

## Die neun Klassen

| Schlüssel | Anzeigetext |
|---|---|
| `arbeiter` | Arbeiter |
| `angestellte` | Angestellte |
| `beamte` | Beamte |
| `selbstaendige` | Selbständige (Handwerk, Handel, Gastgewerbe) |
| `freie_berufe` | Freie Berufe und Akademiker |
| `unternehmer` | Unternehmer und Leitende |
| `ohne_erwerb` | Ohne Erwerbsberuf |
| `kaufleute` | Kaufleute (Stellung unbestimmt) |
| `unbestimmt` | unbestimmt |

`kaufleute` ist keine Verlegenheitslösung, sondern eine bewusst eigene, sichtbare Klasse: „Kaufmann“ ohne
weiteren Zusatz lässt in der Schreibweise offen, ob eine selbständige Existenz oder eine angestellte
Stellung gemeint ist (siehe Kaufleute-Experiment unten). `unbestimmt` ist die Rückfallklasse, wenn keine
Regel greift oder wenn Beruf bzw. Stellung nicht geprüft sind (Exportregel unten).

## Definitionen (Entscheidung 2026-09-25)

Die Grenze zwischen den Klassen ziehen nicht wir, sondern die zeitgenössische Rechtslage, die auch die
Berufszählung 1933 übernahm:

- **Angestellte** sind, wer der Angestelltenversicherung unterlag (AVG 1911 § 1, Fassung 1924):
  kaufmännische Angestellte und Büroangestellte (Buchhalter, Kassierer, Kontoristen, Verkäufer,
  Handlungsgehilfen, Prokuristen), Techniker und Ingenieure, Werkmeister und ähnlich gehobene Aufsicht,
  Bühnen- und Orchestermitglieder, Lehrer und Erzieher in Privatstellung.
- **Arbeiter** sind Lohnempfänger in manueller oder gewerblicher Tätigkeit (Invalidenversicherung),
  einschließlich Vorarbeiter. Nach außen heißt die Klasse „Arbeiter/Gehilfen (nach Schreibung)“, weil
  die Schreibweise ohne Zusatz bei manchen Handwerksberufen Inhaber einschließt (Grenzfälle,
  `docs/stellung_deckung.md`).
- **Selbständige** umfassen Handwerk, Handel, Gastgewerbe **und Landwirtschaft** — keine eigene Klasse für
  Landwirte; der Wirtschaftszweig ist die zweite Achse (Berufsgruppen, `kuratierung/gruppen.csv`).
- **Unternehmer und Leitende** ist eine **bewusste Abweichung** von der Berufszählung, die Direktoren als
  leitende Angestellte und Fabrikanten als Selbständige führt: Inhaber, Fabrikanten, Bauunternehmer,
  Gutsbesitzer sowie Direktoren, Vorstände und Geschäftsführer bilden eine eigene Klasse, weil die Leitfragen
  (Nord–Süd, Durchmischung) sonst Fabrikanten und Bäckermeister nicht unterscheiden könnten. Prokuristen
  gehören nicht dazu (Handlungsbevollmächtigte → Angestellte).
- **Ohne Erwerbsberuf** ist **bewusst heterogen**: Invalide, Witwen, Rentner am einen Ende, Hausbesitzer,
  Rentiers, Privatiers am anderen — die Berufszählung zählt letztere als „berufslose Selbständige“ ebenfalls
  zu den Berufslosen. Das OhdAB-Item bleibt je Eintrag erhalten, sodass die Werkstatt „Hausbesitzer/Rentier/
  Privatier“ als eigene Gruppe herausziehen kann; Kapiteltexte müssen die Heterogenität benennen.
- **Unbestimmt** ist die ehrliche Auflösungsgrenze der Quelle, kein Makel: Handwerksberufe ohne Zusatz mit
  hoher Deckungslücke, Meister in Industrieberufen, Kaufleute (eigene Klasse). Erwartet nach der Handprüfung:
  8–10 % der Nennungen.

Was die Klassifikation leisten kann: Anteile je Straße, Stadtteil oder Hexfeld, mit ausgewiesenem Anteil
„unbestimmt“. Was sie nicht kann und nirgends behaupten darf: Einkommen, Vermögen, individuelle Richtigkeit.
Die strittigen Fälle liegen zwischen benachbarten mittleren Klassen (Angestellte ↔ Leitende, Selbständige ↔
Angestellte), nicht zwischen Arbeitern und Fabrikanten — auf Straßenebene bleiben die Kontraste davon unberührt.

## Die Regeln, in Prüfreihenfolge

`stellung_vorschlag(zeile, item, regeln)` prüft die folgenden Bedingungen der Reihe nach; die erste, die
zutrifft, liefert Klasse und Grund. Geprüft werden drei Texte:

- `_norm(item)` — die OhdAB-Normbezeichnung des zugeordneten Items (z. B. „Bäckermeister/in“);
- `_titel(zeile, item)` — Normbezeichnung + aufgelöster Beruf, **ohne** die OhdAB-Gattung;
- `_text(zeile, item)` — Normbezeichnung + Gattung + aufgelöster Beruf, also inklusive Gattungstext.

Die Trennung zwischen `_titel` (ohne Gattung) und `_text` (mit Gattung) besteht, weil Stichwörter wie
„lehrer“ oder „offizier“ als bloßer Wortbestandteil in einer OhdAB-Gattungsbezeichnung auftauchen können,
ohne dass der Beruf selbst etwas damit zu tun hat (Beispiel: die Gattung „Sportlehrer/innen“ enthält
„lehrer“, obwohl ein „Trainer“ kein Lehrer ist). Solche Merkmale werden deshalb nur gegen `_titel`
geprüft, nicht gegen den vollen Text mit Gattung.

1. **Status `ruhestand`/`invalide`/`witwe` → `ohne_erwerb`, Grund `status`**
   Beispiele: „Bergm. i. R.“ (Status `ruhestand`) → `ohne_erwerb`; „Invalide“ (Status `invalide`) →
   `ohne_erwerb`.

2. **OhdAB-Gattung beginnt mit `A 1` (Berufslose, Rentner, Pensionäre) → `ohne_erwerb`, Grund `item A 1`**
   Beispiel: „Berufslos“ (Item „Berufslose/r“, Gattung-ID `A 10100`) → `ohne_erwerb`.

3. **Status `gewerbe` → `selbstaendige`, Grund `gewerbe`**
   Gewerbeformen (siehe `docs/berufe_gewerbeformen.md`): Personeneinträge, bei denen Scherl statt der
   Berufsbezeichnung das Gewerbe des Inhabers setzt. Beispiel: „Bäckerei“ (Status `gewerbe`, Item
   „Bäcker/in“) → `selbstaendige`.

4. **Meistertitel (Schreibweise oder Norm endet auf „meister(in)“/„mstr.“)**
   Zuerst die **Beamtenausnahme**: Trifft `_BEAMTE` (gegen Norm + Gattung + Beruf) oder `_BEAMTE_TITEL`
   (gegen Norm + Beruf ohne Gattung) zu, gewinnt Regel 10 vor der Meister-Logik → **`beamte`, Grund
   `beamte`**. Grund dafür: Meistertitel im Polizei- und Justizvollzugsdienst sowie in der
   Steuerverwaltung („Pol. Wachtmstr.“, „Polizeimstr.“, „Just. Wachtmstr.“, „Steuerwachtmstr.“,
   „Hauptwachtmstr.“ …) sind Beamte, keine betrieblichen Vorgesetzten — ohne diese Ausnahme hätte die
   Meister-Regel die Beamten-Regel für alle Schreibweisen verdeckt, deren Norm oder aufgelöster Beruf auf
   „meister“/„mstr.“ endet (Review-Fund TP5a: 19 Schreibweisen, 928 Nennungen, fälschlich
   `angestellte`). Beispiel: „Pol. Wachtmstr.“ (Item „Polizeiwachtmeister/in“, Gattung „Berufe im
   Polizeivollzugsdienst“) → `beamte`.

   Erst danach entscheidet der Wortstamm (in Schreibweise oder Normbezeichnung) vor „meister“ zwischen drei Fällen:
   - Stamm in `_INDUSTRIE` (Schmied, Schlosser, Dreher, Mechaniker) → **`unbestimmt`, Grund `industriemeister`**:
     In Essen (Krupp, Zechen) sind das überwiegend Betriebsmeister, teils Inhaber — die Deckungstabelle zeigt
     mehr Meister als Betriebe in Teil III (Schlosser 222 gegen 111, Schmied 160 gegen 122). Beispiel:
     „Schmiedemstr.“ → `unbestimmt`; die Werkstatt kann sie wie die Kaufleute umschalten.
   - Stamm in `_HANDWERK` (Bäcker, Metzger, Schlachter, Fleischer, Konditor, Schneider, Schuhmacher,
     Friseur, Maler, Anstreicher, Tischler, Schreiner, Klempner, Installateur, Dachdecker, Maurer, Zimmer-, Stukkateur, Glaser, Sattler, Polsterer, Tapezier, Uhrmacher, Gold-,
     Buchbinder, Drucker, Gärtner, Fuhr-, Elektro-, Schornsteinfeger, Kürschner, Hut-, Korb-,
     Stellmacher, Wagner, Böttcher, Küfer, Müller, Mühlen-, Brauer, Gerber, Seiler, Töpfer,
     Ofensetzer, Steinmetz, Bildhauer, Graveur, Optiker, Fotograf) → **`selbstaendige`,
     Grund `handwerksmeister`**. Beispiel: „Bäckermstr.“ (Item „Bäckermeister/in“, Niveau `aufsicht`) →
     `selbstaendige`.
   - Alle anderen Meister (Werk-, Betriebs-, Fahr-, Zug-, Bahnmeister …) → **`angestellte`, Grund
     `betriebsmeister`**. Beispiel: „Werkmstr.“ (Item „Werkmeister/in“, Niveau `aufsicht`) →
     `angestellte`.

5. **Merkmal `akademiker` auf der Schreibweise → `freie_berufe`, Grund `akademiker`**
   Das Merkmal kommt aus `kuratierung/merkmale/akademiker.csv` (Präfix „Dr.“, „Prof.“, „Dipl.“ u. Ä. im
   Feld „Beruf o. ä.“ oder im Nachnamensfeld). Beispiel: „Dr. med.“ (Item „Arzt/Ärztin“) → `freie_berufe`.

6. **Freie Berufe ohne Titelpräfix (Regex `_FREIE` gegen die Norm)** → `freie_berufe`, Grund `freier beruf`.
   Muster: Arzt/Ärztin, Zahnarzt, Dentist, Tierarzt, Apotheker, Rechtsanwalt/Anwalt, Notar, Architekt,
   Patentanwalt, Wirtschaftsprüfer, Steuerberater, Bücherrevisor, Schriftsteller, Künstler, Kunstmaler,
   Bildhauer/in. Beispiel: „Rechtsanwalt“ (Item „Rechtsanwalt/-anwältin“) → `freie_berufe`.

6a. **Erwerbsquelle statt Beruf (Regex `_OHNE_ERWERB` gegen die Norm: Hausbesitzer, Rentier, Privatier)** →
   `ohne_erwerb`, Grund `erwerbsquelle` (siehe Definitionen). Beispiel: „Hausbes.“ (Item „Hausbesitzer/in“)
   → `ohne_erwerb`.

7. **Unternehmer (Regex `_UNTERNEHMER` gegen Norm + Gattung + Beruf)** → `unternehmer`, Grund
   `unternehmer`. Muster: Fabrikant, Fabrikbesitzer, Direktor/Generaldirektor (außer „Studiendirektor“
   und „Katasterdirektor“ — negativer Lookbehind, siehe Grenzfälle), Vorstand, Geschäftsführer, Inhaber,
   Unternehmer, Bergwerksbesitzer, Gutsbesitzer. Prokurist nicht mehr (seit 2026-09-25 → Regel 9). Beispiele: „Fabrikant“
   → `unternehmer`; „Direktor“ (Item „Direktor/in“, Gattung „Geschäftsführer/innen und Vorstände“) →
   `unternehmer`; „Bankdirektor“ → `unternehmer` (echter Unternehmer-Direktor, vom Lookbehind nicht
   ausgenommen).

8. **Norm gefaltet gleich „kaufmann frau“ und Text enthält kein „angest“/„beamt“ → `kaufleute`, Grund
   `kaufmann`**
   Beispiel: „Kfm.“ (Item „Kaufmann/-frau“) → `kaufleute`. Gegenbeispiel: „kfm. Angest.“ (Item
   „Kaufmännische/r Angestellte/r“) trifft diese Regel nicht (die Norm ist nicht „Kaufmann/-frau“) und
   fällt auf Regel 9 → `angestellte`.

9. **Angestellte (Regex `_ANGESTELLTE` gegen den vollen Text), außer die Norm ist zugleich Beamten-Norm
   oder der Titel trifft `_BEAMTE_TITEL`** → `angestellte`, Grund `angestellte`. Muster: angestellt,
   Buchhalter, Kontorist, Techniker, Ingenieur, Steiger, Zeichner, Verkäufer, Handlungsgehilfe, Kassierer,
   Vertreter, Reisender, Bürogehilfe, Stenotypist, Laborant, Chemiker, Betriebsführer, Prokurist, Abteilungsleiter,
   Filialleiter, Disponent, Expedient, Magazinverwalter, Werkführer, Obersteiger. Beispiele: „Steiger“
   (Item „Steiger/in“, Niveau `spezialist`) → `angestellte`; „Techniker“ (Item „Techniker/in“) →
   `angestellte`.

10. **Beamte (Regex `_BEAMTE` gegen Norm+Gattung+Beruf, oder `_BEAMTE_TITEL` gegen Norm+Beruf ohne
    Gattung)** → `beamte`, Grund `beamte`. `_BEAMTE`-Muster: beamt, Sekretär, Inspektor, Assistent,
    Amtmann, Rat/Rätin, Schaffner, Zugführer, Lokomotivführer, Briefträger, Postbote, Polizei, Schutzmann,
    Wachtmeister, Zoll, Richter, Pfarrer, Pastor, Geistlich-, „oberst“ nur als eigenes Wort, Major,
    Hauptmann, Förster, Gerichtsvollzieher, Studiendirektor, Katasterdirektor, „(…dienst)“.
    `_BEAMTE_TITEL`-Muster (nur gegen den eigenen Titel, nicht die Gattung): lehrer, offizier. Beispiele:
    „Reichsbahnbeamt.“ (Item „Bahnbeamt(er/in) (mittl. Dienst)“) → `beamte`; „Lehrer“ (Item „Lehrer/in“,
    Gattung „Lehrkräfte in der Sekundarstufe“) → `beamte`; „Lokomotivführer“ → `beamte`.

11. **Selbständige (Regex `_SELBSTAENDIGE` gegen die Norm)** → `selbstaendige`, Grund `selbstaendig`.
    Muster: Händler, Handel, Wirt(in)/Gastwirt/Schankwirt, Krämer, Fuhrmann, „Kaufmann/-frau -“/„(…“,
    Hausierer, Agent, Makler, Kommissionär, Verleger, Drogist, Hebamme, Masseur, Heilpraktiker, Landwirt,
    Bauer, Kötter, Pächter, Fischer, Schiffer. Beispiele: „Gastwirt“ → `selbstaendige`;
    „Kolonialwarenhändler“ → `selbstaendige`.

12. **Niveau `spezialist`/`aufsicht` oder Gattung beginnt mit „Aufsichtskräfte“ → `angestellte`, Grund
    `angestellte`** — verbleibende Aufsichts- und Spezialistentätigkeiten ohne Treffer in den Regeln
    davor.

13. **Niveau `helfer`/`fachlich` → `arbeiter`, Grund `niveau helfer`/`niveau fachlich`**. Beispiele:
    „Arbeiter“ (Item „Arbeiter/in - allgemein“, Niveau `helfer`) → `arbeiter`; „Bergm.“ (Item
    „Bergmann/-frau“, Niveau `fachlich`) → `arbeiter`.

14. **Ohne Treffer → `unbestimmt`, Grund leer**. Beispiel: „Musiker“ (Item „Musiker/in“, Niveau `keins`,
    Gattung „Musik“) → `unbestimmt` — trifft keine der obigen Regeln (kein Akademiker-Merkmal, keine
    freie-Berufe-, Unternehmer-, Angestellten-, Beamten- oder Selbständigen-Norm, kein verwertbares
    Niveau).

## Grenzfälle

- **Steiger/Werkmeister → Angestellte**, obwohl die OhdAB sie im Niveau `spezialist`/`aufsicht` führt —
  betriebliche Vorgesetzte ohne eigenen Betrieb zählen nach der Berufszählungslogik als Angestellte, nicht
  als Selbständige oder Unternehmer.
- **Bäckermeister (und die übrige Handwerksliste) → Selbständige**, weil ein Meistertitel im Handwerk
  historisch fast immer den selbständigen Betriebsinhaber bezeichnet; alle anderen Meistertitel (Werk-,
  Betriebs-, Fahr-, Zug-, Bahnmeister) sind betriebliche Funktionen → Angestellte.
- **Lehrer → Beamte**, weil Lehrer an öffentlichen Schulen 1936 überwiegend im Beamtenstatus standen;
  private Musik-/Tanz-/Sprachlehrer ohne Beamtenkontext, die stattdessen über das Akademiker-Merkmal oder
  die Freie-Berufe-Regel erfasst werden, laufen als `freie_berufe`.
- **Ingenieur ohne Titel → Angestellte** (Regel 9, Muster „ingenieur“ in `_ANGESTELLTE`); erst ein
  akademischer Titel („Dipl.-Ing.“, Akademiker-Merkmal) hebt die Zuordnung in Regel 5 auf `freie_berufe`.
- **Gewerbeformen → Selbständige**, Niveau bleibt aber `niveau_unsicher=ja` (siehe
  `docs/berufe_gewerbeformen.md`) — die Stellung ist hier sicherer entscheidbar als das OhdAB-Niveau.
- **Handwerksberufe ohne Meister-/Gehilfen-Zusatz („Friseur“, „Schneider“, „Schuhmacher“, „Bäcker“ …)
  laufen nach Niveau als `arbeiter`, sind aber oft Betriebsinhaber.** Beleg: „Friseur“ 724 Einträge in
  Teil I, dazu nur ~300 als Geschäft/Meister gekennzeichnet („Friseurgesch.“ 246, „Friseurmstr.“ 30,
  Salons 24) — Teil III zählt aber 657 Friseurbetriebe. Der Meisterzwang für Neugründungen galt erst ab
  1935, Altinhaber ohne Titel blieben. Die Unschärfe ist je Beruf sehr verschieden: Bei Bäckern,
  Metzgern, Schlossern, Maurern erklären die gekennzeichneten Inhaber alle Betriebe von Teil III (ohne
  Zusatz = Arbeiter tragfähig); bei Uhrmachern, Schuhmachern, Malern, Friseuren fehlt der Zusatz
  systematisch. **Entscheidung (Weg 3, 2026-09-25):** je Berufsfamilie datengestützt — Quote
  „unerklärte Betriebe / offene Nennungen“ unter 10 % → `arbeiter` bestätigen, sonst `unbestimmt`, bis der
  Abgleich Teil I ↔ Teil III über Name + Adresse (Spec §10, für 5b vorgezogen) pro Person entscheidet.
  Tabelle mit allen Zahlen und getroffenen Rubriken: `docs/stellung_deckung.md`
  (`werkzeuge/handwerk_deckung.py`, nach jeder Prüfrunde neu erzeugen); das Werkzeug blendet die Kennzahl
  bei betroffenen Schreibweisen ein. Nach außen heißt die Klasse deshalb „Arbeiter/Gehilfen (nach
  Schreibung)“.
- **Kaufleute bekommen eine eigene Klasse**, statt sie einer Nachbarklasse zuzuschlagen, weil die
  Schreibweise „Kaufmann“ ohne Zusatz nicht erkennen lässt, ob eine selbständige Existenz oder eine
  angestellte Stellung gemeint ist (siehe Kaufleute-Experiment unten).

## Prüfregel

Die Automatik (`werkzeuge/stellung_vorschlag.py`, `bearbeiter=stellung_vorschlag`) füllt die Spalte
`stellung` überall dort, wo `stellung_geprueft` leer ist — auch bei Zeilen, die für die eigentliche
Berufszuordnung bereits gesperrt sind (`geprueft=ja`, anderer Bearbeiter), denn die Stellung ist eine
eigenständige, bislang ungeprüfte Frage. `stellung_geprueft=ja` setzt ausschließlich der Mensch im
Berufe-Werkzeug (`werkzeuge/berufe.html`): Auswahl der Klasse über die Zifferntasten `1`–`9` (Reihenfolge
wie oben), Bestätigung mit Taste `T`, Filter „Stellung offen“ zeigt nur ungeprüfte Zeilen. Taste `A` überträgt
die Stellung auf alle Geschwister-Schreibweisen desselben Items ohne Status mit geprüftem Beruf (die Zeile
„Mit A auch: …“ zeigt sie vorher an); Statuszeilen und Titelformen wie „Dr.-Ing.“ bleiben getrennte
Entscheidungen. Begründung (2026-09-25): Von 856 Items der geprüften Schreibweisen tragen nur 104
unterschiedliche Stellungen, 99 davon allein über den Status — die Granularität der Schreibweise bleibt
erhalten, die Zahl der Handentscheidungen sinkt um rund 40 %.

## Exportregel

`stellung_export(zeile)` liefert die Klasse nur, wenn **beide** Bedingungen erfüllt sind: `geprueft=ja`
(Berufszuordnung selbst geprüft) **und** `stellung_geprueft=ja` (Stellung geprüft). Fehlt eine der beiden
Prüfungen, exportiert die Zeile `unbestimmt` — unabhängig davon, welchen Wert die Automatik in `stellung`
vorgeschlagen hat. Damit erscheint kein automatischer Vorschlag ungeprüft als belastbares Ergebnis.

## Kennzahlen

Der Export schreibt in `site/daten/kennzahlen.json`:

- `stellung_geprueft` — Anteil der Teil-I-Einträge mit exportierter (also doppelt geprüfter) Stellung.
- `stellung_unbestimmt` — Anteil der Teil-I-Einträge ohne Beruf oder mit Stellung `unbestimmt`.

Zählfeld je Adresse/Straße/Stadtteil/Hexzelle: `n_st_<klasse>` (`pipeline/lib/ebenen.py`).

**Stand der Automatik (Lauf vom 2026-09-24, real, `kuratierung/berufe.csv`, 1.977 Schreibweisen, nach der
Beamtenausnahme-Korrektur in Regel 4):** Verteilung der Vorschläge (noch keine Handprüfung — siehe unten):

| Klasse | Schreibweisen |
|---|---|
| `arbeiter` | 551 |
| `selbstaendige` | 350 |
| `beamte` | 324 |
| `angestellte` | 298 |
| `unbestimmt` | 196 (9,9 %) |
| `ohne_erwerb` | 138 |
| `unternehmer` | 63 |
| `freie_berufe` | 54 |
| `kaufleute` | 3 |

Gegenüber dem vorigen Lauf (vor der Korrektur) sind 19 Schreibweisen (928 Nennungen) von `angestellte`
nach `beamte` gewandert — Meistertitel im Polizei-/Justizvollzugsdienst und in der Steuerverwaltung, die
zuvor fälschlich der Meister-Regel statt der Beamten-Regel folgten (siehe Regel 4 oben).

`unbestimmt` liegt bei 9,9 % und damit deutlich unter der im Plan gesetzten Grenze von 20 %. Diese Zahlen
sind Vorschläge der Automatik, keine geprüften Ergebnisse: Zum Stand 2026-09-24 trägt keine Zeile in
`kuratierung/berufe.csv` `stellung_geprueft=ja`, entsprechend zeigt `site/daten/kennzahlen.json` aktuell
`stellung_geprueft: 0.0` und `stellung_unbestimmt: 100.0` — die Handprüfung im Berufe-Werkzeug hat noch
nicht begonnen.

## Kaufleute-Experiment in der Werkstatt

Weil die Schreibweise „Kaufmann“/„Kfm.“ allein nicht erkennen lässt, ob eine selbständige Existenz oder
eine angestellte Stellung gemeint ist, bleibt `kaufleute` eine eigene, sichtbare Klasse statt in eine
Nachbarklasse eingerechnet zu werden. Das Ansicht-Datenmodell (Spec §4, Feld `kaufleute` mit den Werten
`unbestimmt`, `angestellte`, `selbstaendige`) erlaubt es Nutzerinnen und Nutzern der Werkstatt (TP5c),
probeweise umzuschalten, wohin die Klasse `kaufleute` bei einer Auswertung zählt, und den Effekt auf
Verteilungen unmittelbar zu sehen. Die Datengrundlage (dieser Plan) legt die Klasse nur an; das Umschalten
selbst ist Sache der Werkstatt.
