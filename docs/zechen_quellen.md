# Quellenrecherche: Essener Steinkohlenzechen und ihr Status 1936

Recherche durch einen Opus-Agenten am 2026-09-21 (Websuche), Stichproben (Fridolin, Carolus Magnus) am selben Tag von Hand nachgeprüft. Bezug: `kuratierung/zechen_pruefung.csv`.

---

## (a) Bewertete Quellenliste

### 1. Historisches Portal Essen – Bergbau/Zechen  ★ Hauptfund

- URL (Einstieg): <https://historischesportal.essen.de/historischesportal_orte/bergbau_1/zechen.de.html>
- A–Z-Liste: <https://historischesportal.essen.de/historischesportal_orte/bergbau_1/bergbau_abisz.de.html>
- Detailseiten: `…/bergbau_detailseite_<ID>.de.html`
- **Art:** redaktionelle Datenbank der Stadt Essen, inhaltlich verantwortet vom
  *Historischen Verein für Stadt und Stift Essen e.V.* (Impressum:
  <https://historischesportal.essen.de/startseite_7/impressum_4.de.html>; Sitz im Haus der
  Essener Geschichte/Stadtarchiv).
- **Grundlage:** Die Detailseiten sind ausdrücklich überschrieben mit
  „**Literaturauszüge aus… „Die Steinkohlenzechen im Ruhrrevier“**“ und nennen als
  Literaturquelle „*Die Steinkohlenzechen im Ruhrrevier, Joachim Huske*“, bei vielen
  Einträgen zusätzlich „*Bergbauhistorischer Atlas für die Stadt Essen, Dr. Karl Albrecht
  Ruhbach [sic, richtig: Rubach], Karlheinz Rabas*“. Es handelt sich also um **wörtliche
  Auszüge aus Huske** (3. Aufl. 2006) – genau das gesuchte Werk, frei im Netz lesbar.
- **Umfang:** 1.591 verlinkte Einträge in der A–Z-Liste (Zechen, Schächte, Stollen,
  Kleinzechen, Sonstiges); die Seite selbst spricht von „ca. 1.700 Anlagen“.
- **Eignung:** sehr hoch. Jahresweise Chronologie (Verleihung, Konsolidation, Sohlen,
  Förderung in t und Belegschaft „B“, Stilllegung, Übernahme) – damit lässt sich der
  Status 1936 pro Zeche direkt und mit Zitat belegen.
- **Einschränkung (wichtig!):** Bei langen Einträgen ist der Huske-Text **abgeschnitten**
  (Zeichenlimit). Beispiele: *Ver. Sälzer Neuack* endet mitten im Jahr 1826
  („Schacht Franziska: Förderein“), *Graf Beust* endet 1898 („nach dortigem Schachte"“),
  *Altendorf Tiefbau* endet 1902 („Sch. 2: Förderbegi“), *Ver. Pörtingssiepen* endet 1913,
  *Ver. Helene Amalie* endet 1910. Für diese Zechen muss der 1936-Status aus dem
  ergänzenden Atlas-Abschnitt oder aus den Nachfolge-/Verbundeinträgen erschlossen werden.
- **Lizenz:** keine offene Lizenz angegeben; klassisches Urheberrecht (Stadt Essen /
  Historischer Verein, Textauszüge aus Huske © DBM Bochum). → als **Nachschlage- und
  Zitierquelle** nutzbar, nicht zur Massenübernahme der Texte.

### 2. geo.essen.de – ArcGIS-Dienst `historischerverein/Bergbau`  ★ maschinenlesbar

- REST: <https://geo.essen.de/arcgis/rest/services/historischerverein/Bergbau/MapServer>
- Ordnerübersicht: <https://geo.essen.de/arcgis/rest/services/historischerverein?f=json>
  (45 Dienste, u. a. `Bergbau`, `Bergbaugeschuetzt`, `Stadtplan_1935`, `Honigmannkarte`)
- **Art:** offener ArcGIS-MapServer (Query-API, `f=json`), 4 Layer:
  `0 Schacht` (285), `1 Kleinzechen` (186), `2 Stollen` (132), `3 Sonstiges` (246) = **849 Punkte**.
- **Felder:** `NAME, ART, STADTTEIL, LAGE, ABGETAEUFT, STILLGELEGT, GKX/GKY, UTM_E/UTM_N,
  FS_ID, LINK`. `LINK` zeigt exakt auf die Detailseite im Historischen Portal
  (`…bergbau_detailseite_<FS_ID>.de.html`) – beide Quellen sind also über `FS_ID` gekoppelt.
- **Eignung:** hoch für Verortung und für einen maschinellen Grobfilter („war der Schacht
  1936 zwischen ABGETAEUFT und STILLGELEGT?“). Achtung: die Jahre sind **schachtbezogen**,
  nicht zechenbezogen, und häufig `null` (z. B. alle Carolus-Magnus-Schächte außer Sch. 1).
- **Lizenz:** nicht ausgewiesen; Dienst ist ohne Authentifizierung abrufbar, CORS laut
  Projektnotiz ok. Vor Veröffentlichung Rechte beim Historischen Verein / Stadt Essen klären.
- Vollabzug für dieses Projekt liegt im Scratchpad: `bergbau_0..3.json`, Index `abisz_index.tsv`.

### 3. ruhrzechenaus.de (Torsten Beimborn u. a.)

- Quellenseite: <https://www.ruhrzechenaus.de/quellen.html> – nennt ausdrücklich
  „**Huske, Joachim: Die Steinkohlenzechen im Ruhrrevier; Bochum 2006**“ sowie Karten,
  Werkszeitschriften, TIM-online.
- Beispielseite Essen: <https://www.ruhrzechenaus.de/essen/e-victoria-mathias.html> –
  tabellarisch Teufbeginn / Inbetriebnahme / Stilllegung / max. Teufe je Schacht.
- **Eignung:** gute Zweitmeinung, tabellarisch. **Aber:** auf den Einzelseiten stehen
  **keine Einzelnachweise**; Schwerpunkt der Site liegt auf Bochum und dem östlichen Revier.
- **Zugang:** Verzeichnis-URLs (`/essen/`) liefern 403; Einzelseiten sind abrufbar.
- **Lizenz:** privat, © der Betreiber, keine Nachnutzungsfreigabe erkennbar.

### 4. ruhrkohlenrevier.de – „Der frühe Bergbau an der Ruhr“

- <http://www.ruhrkohlenrevier.de/ezechen.html> (Zechen in Essen, nach Stadtteilen),
  <http://www.ruhrkohlenrevier.de/zechenchro.html>, <http://www.ruhrkohlenrevier.de/iliteratur.html>
- **Grundlage:** ausgewiesene Literaturliste, darin Huske [10]/[11] und Rabas/Rubach [16].
- **Eignung:** gering für unsere Frage – die Site behandelt bewusst den **frühen** Bergbau
  (Stollen-/Kleinzechenzeit); Zechen wie Emil-Emscher oder Helene fehlen ganz.
- **Technisch:** TLS-Zertifikat passt nicht zum Hostnamen (nur per `http://` bzw. curl lesbar).

### 5. Zeitgenössische Verzeichnisse 1936 – Digitalisate: **nicht gefunden**

- „Jahrbuch für den Oberbergamtsbezirk Dortmund“ heißt **ab 1932 „Jahrbuch für den
  Ruhrkohlenbezirk“** (Hrsg. Verein für die bergbaulichen Interessen, Essen); ZDB-Nachweis:
  <https://zdb-katalog.de/title.xhtml?idn=012719331>. Für 1936/37 wurde **kein Digitalisat**
  gefunden (geprüft: archive.org-Volltextsuche via advancedsearch-API – 0 einschlägige
  Treffer für „Oberbergamtsbezirk Dortmund“, „Steinkohlenzechen“, 4 irrelevante für
  „Ruhrkohlenbezirk“; Google-Books-/DDB-Recherche ohne Digitalisat).
- Ein physisches Exemplar des 35. Jahrgangs (1937) ist nachgewiesen bei museum-digital:
  <https://rheinland.museum-digital.de/object/22375> (Objektnachweis, **kein Volltext**).
- „Die Zechen des Ruhrbezirks“, „Kohlen-Adressbuch“, „Adressbuch des Bergbaus“ o. ä. für
  1936: **kein Digitalisat gefunden**.
- Huske selbst (Buch oder Auszüge) ist **nicht** legal als Digitalisat online; einziger
  faktischer Online-Zugang zu seinen Daten für Essen ist Quelle 1.

### 6. Offene Geodaten

- **Open Data Portal Ruhr – „Historische Zechenstandorte“**
  <https://www.opendata.ruhr/dataset/historische-zechenstandorte> – Lizenz **dl-de/zero-2.0**,
  Formate WFS/Shapefile/GeoJSON, Herausgeber Stadt Herne. **Deckt nur Herne ab**, nicht Essen
  → für uns unbrauchbar, aber lizenzrechtlich das Vorbild.
- **Geologischer Dienst NRW**: „Karte des Rheinisch-Westfälischen Steinkohlengebietes
  1:10.000“, 58 Blätter, kostenfrei über GEOportal.NRW
  (<https://www.gd.nrw.de/pr_kd_rohstoffkarte-rheinisch-westf-steinkohle-10000.php>).
  Zeigt Flöze/Tektonik, dient als Altbergbau-Informationssystem – **keine Betriebsjahre je Zeche**.
- **Bezirksregierung Arnsberg, Abt. Bergbau**: nicht geprüft/**nicht gefunden** als
  online-recherchierbares Betriebsjahres-Verzeichnis.
- geo.essen.de hat neben `Bergbau` auch `Bergbaugeschuetzt` (Schutzbereiche) und
  `Stadtplan_1935` – der Stadtplan 1935 bleibt die beste **kartografische** 1936-Kontrolle.

### 7. Das Adressbuch 1936 selbst (eigener Bestand, `data/essen1936.csv`)

- 646 Zeilen mit „Zeche“, 252 verschiedene Firmennamen mit „Zeche/Steinkohlen/Bergwerk“.
- Häufigste Akteure 1936: Essener Bergwerksverein König Wilhelm (63), Gewerkschaft des
  Steinkohlenbergwerks Langenbrahm (~90 Schreibvarianten zusammen), Gelsenkirchener
  Bergwerks-AG (~75), Mülheimer Bergwerksverein (~55), Zeche Heinrich (34), Zeche
  Carolus Magnus (6), Zeche Langenbrahm (7), **Zeche Graf Beust (2)**.
- **Warnung:** Eine Nennung im Adressbuch belegt nur **Grundbesitz/Gewerkschaft**, nicht den
  Förderbetrieb. „Zeche Graf Beust“ ist 1936 als Hauseigentümerin verzeichnet, obwohl das
  Baufeld laut Huske schon 1929 an Victoria Mathias ging (die Gewerkschaft bestand bis 1952).

---

## (b) Befunde je Zeche

Spalte „Huske-Auszug (Hist. Portal Essen)“ = wörtliche/gekürzte Zitate der Detailseite,
`ID` = `bergbau_detailseite_<ID>.de.html`. „1936?“ ist die daraus abgeleitete Bewertung.

| Zeche | ID | Huske-Auszug (nur Jahresangaben; Wortlaut beim Portal, © DBM Bochum) | 1936? |
|---|---|---|---|
| **Fridolin** (Steele-Horst) | 1213126 | Jahre im Auszug: 1836, 1842, 1855, 1882 (Zitat entfernt, siehe Portal-Seite) | **nein** – Ende 1882 (nicht 1899, nicht 1960) |
| **Graf Beust** (Ostviertel) | 1213251 | Jahre im Auszug: 1838, 1898, 1928, 1929, 1952 (Zitat entfernt, siehe Portal-Seite) | **nein** als selbständige Anlage (ab 1929 Teil Victoria Mathias); Gewerkschaft/Grundbesitz bestand aber 1936 noch |
| **Hercules/Herkules** (Ostviertel) | 1214921 | Jahre im Auszug: 1920, 1924, 1925 (Zitat entfernt, siehe Portal-Seite) | **nein** |
| **Carl** (Altenessen-Süd) | 1212951 | Jahre im Auszug: 1924, 1927, 1929 (Zitat entfernt, siehe Portal-Seite) | **nein** als eigene Zeche; Schacht Carl 1/2 lief als Anlage von Emil bzw. ab 1935 Emil-Emscher weiter |
| **Prinz Friedrich** (Kupferdreh) | 1213981 | Jahre im Auszug: 1928, 1930, 1931 (Zitat entfernt, siehe Portal-Seite) | **nein** als eigene Zeche; Schacht als Carl Funke 3 weiter in Nutzung |
| **Altendorf Tiefbau** (Burgaltendorf) | 1212626 | Jahre im Auszug: 1855, 1902, 1914, 1969 (Zitat entfernt, siehe Portal-Seite) | **unklar → nachprüfen**; Geo-Attribut legt Stilllegung 1914 nahe, Beleg fehlt im Text |
| **Gottfried Wilhelm** (Rellinghausen/Stadtwald) | 1214643 | Jahre im Auszug: 1930, 1935, 1940, 1942, 1958 (Zitat entfernt, siehe Portal-Seite) | **ja – in Förderung** |
| **Carolus Magnus** (Bergeborbeck/Bochold) | 1214553 | Jahre im Auszug: 1935, 1936, 1937, 1951 (Zitat entfernt, siehe Portal-Seite) | **ja – in Förderung** (auch im Adressbuch 1936 als „Zeche Carolus Magnus“ belegt) |
| **Centrum 4/6** (Kray-Leithe) | 1212728 | Jahre im Auszug: 1927, 1928, 1933, 1952 (Zitat entfernt, siehe Portal-Seite) | **nein** – 1936 nur Reservefeld + Wasserhaltung über Schacht 6 |
| **Emil-Emscher** (Vogelheim) | 1213019 | Jahre im Auszug: 1935, 1936, 1937 (Zitat entfernt, siehe Portal-Seite) | **ja – in Förderung**, Name erst ab 1.7.1935 |
| **Friedrich Ernestine** (Stoppenberg) | 1213138 | Jahre im Auszug: 1934, 1935, 1937, 1957 (Zitat entfernt, siehe Portal-Seite) | **ja – in Förderung** |
| **Amalie** bzw. **Ver. Helene Amalie** | 1213345 / 1213339 / 1214073 | Jahre im Auszug: 1815, 1910, 1927, 1935, 1937 (Zitat entfernt, siehe Portal-Seite) | **Helene: ja**. **Amalie: ja**, 1936 noch eigenständige Krupp-Anlage – der Name *Sälzer-Amalie* existiert erst ab 1.1.1937. Eine eigene Detailseite „Amalie (Zeche)“ **nicht gefunden** (nur Schacht-Seiten 1214981/1215115). |
| **Vereinigte Pörtingssiepen** (Fischlaken) | 1213951 / 1215283 | Jahre im Auszug: 1913, 1942, 1943, 1967, 1973 (Zitat entfernt, siehe Portal-Seite) | **ja – in Förderung** |
| **Viktoria/Victoria** (Kupferdreh/Byfang) | 1214399 | Jahre im Auszug: 1920, 1924, 1925, 1950 (Zitat entfernt, siehe Portal-Seite) | **nein** |
| **Wolfsbank** | 1214507 (Überruhr-Holthausen) / 1214509 | Jahre im Auszug: 1800, 1801, 1960 (Zitat entfernt, siehe Portal-Seite) | **ja – wahrscheinlich in Förderung** (Verbund erst 1960), aber **Beleg im Portal unvollständig** → zweite Quelle nötig |
| **Katharina** (Kray; Schacht 3 „Ernst Tengelmann“) | 1213541 | Jahre im Auszug: 1903, 1930, 1931, 1935, 1940, 1950, 1952 (Zitat entfernt, siehe Portal-Seite) | **ja – in Förderung**. Achtung: Huske verortet sie in **Kray**, nicht Frillendorf (Frillendorf = Königin Elisabeth, Schacht Emil, ID 1215037) |
| **Vereinigte Klosterbusch** (Bredeney) | 1213559 | Jahre im Auszug: 1877, 1881, 1883 (Zitat entfernt, siehe Portal-Seite) | **nein** (Essener Anlage; gleichnamige Zeche in Bochum-Querenburg ist ein anderer Betrieb) |
| **Voßhege** (Heisingen) | 1214419 / 1214421 | Jahre im Auszug: 1800, 1871, 1947, 1952 (Zitat entfernt, siehe Portal-Seite) | **nein** – 1936 keine Betriebsphase (Lücke 1871–1947) |
| **Vereinigte Gewalt und Gottvertraut** (Überruhr) | 1213200 / 1213198 | Jahre im Auszug: 1902, 1922, 1923, 1924, 1957 (Zitat entfernt, siehe Portal-Seite) | **nein** |
| **Plaetzgesbank** (Heisingen) | 1213945 | Jahre im Auszug: 1927, 1933, 1936, 1937, 1938, 1939, 1959 (Zitat entfernt, siehe Portal-Seite) | **ja, aber nur kampagnenweise** – 1936 exakt zwei Monate Betrieb (Kleinzeche) |
| **Geitling** (Steele-Horst) | 1213174 | Jahre im Auszug: 1813, 1814, 1837, 1844, 1940 (Zitat entfernt, siehe Portal-Seite) | **nein** – 1936 kein Betrieb; die Jahreszahl 1940 ist eine reine **Berechtsams-Konsolidation**, keine Förderung (klassische Falle für Listen-Auswertungen) |

Zusatzbefunde, die für die Kartierung nützlich sind:

- **Carl Funke** (Heisingen, ID 1212712): Jahre im Auszug: 1935, 1936 (Zitat entfernt, siehe Portal-Seite) — Betrieb 1936 belegt.
- **Victoria Mathias, Graf Beust und Friedrich Ernestine** (ID 1214405) ist ein
  **Verbundname erst ab 1957** – wer ihn auf 1936 anwendet, liegt falsch.
- Die Geo-Felder `ABGETAEUFT`/`STILLGELEGT` sind bei vielen Schächten `null`
  (z. B. Katharina Sch. 4/6, Carolus-Magnus Sch. 2/3, Amalie) – sie taugen nicht als
  alleiniges Kriterium.

---

## (c) Empfehlung

**Referenz 1 (Leitquelle): Historisches Portal Essen, Bergbau-Detailseiten.**
Sie liefert für Essen genau das gesuchte Werk (Huske 2006) im Volltextauszug, mit Jahres-
chronologie inklusive Fördermengen und Belegschaftszahlen für 1935/1936/1937 – damit ist
„in Betrieb 1936“ pro Zeche zitierfähig entscheidbar, und die typischen Wikipedia-Fehler
(Straßenbenennung, Konsolidationsjahr, Verbundname) lassen sich benennen. Verantwortlich
zeichnet der Historische Verein für Stadt und Stift Essen – dieselbe Institution, aus deren
ArcGIS-Ordner das Projekt bereits den Stadtplan 1935 bezieht.

**Referenz 2 (Gegenprobe): ruhrzechenaus.de** für Zechen, deren Portal-Text abgeschnitten
oder leer ist (Wolfsbank/Bergeborbeck, Altendorf Tiefbau, Ver. Sälzer Neuack, Amalie) –
dort steht der Verlauf tabellarisch, allerdings ohne Einzelnachweis, also nur als Indiz,
gekennzeichnet. Ideal wäre stattdessen der gedruckte Huske bzw. der Rabas/Rubach-Atlas
(Präsenzbestand Stadtbibliothek/Haus der Essener Geschichte); beide sind **nicht** digital.

**Maschinelle Nutzbarkeit:** ja, über Weg 2 – der ArcGIS-Dienst
`historischerverein/Bergbau` liefert per `…/MapServer/{0..3}/query?where=1=1&outFields=*&f=json`
849 Objekte mit `NAME, ART, STADTTEIL, ABGETAEUFT, STILLGELEGT, UTM_E/UTM_N` und – das ist
der Hebel – mit `LINK`/`FS_ID` auf die Huske-Detailseite. Empfohlener Ablauf:

1. Dienst einmalig abziehen (liegt bereits als `bergbau_0..3.json` im Scratchpad) und mit
   dem A–Z-Index (`abisz_index.tsv`, 1.591 Einträge) zu einer Zechen-/Schachtliste verbinden.
2. Für die Kandidaten, die im Adressbuch 1936 bzw. auf dem Stadtplan 1935 vorkommen,
   die zugehörige Detailseite einmal abrufen und die Zeilen 1930–1940 als Belegzitat in
   die Kuratierungstabelle übernehmen (Feld `beleg_zitat` + `beleg_url`).
3. Drei Statuswerte vergeben: `in Förderung` / `nicht in Betrieb` / `unklar` – letzteres
   überall dort, wo der Huske-Auszug abgeschnitten ist. Kein Ratewert.
4. Wikipedia-Liste und -Infobox nur noch als *Variantenfeld* mitführen, nicht als Quelle.

**Nicht gefunden** (damit es nicht erneut gesucht wird): Huske als Digitalisat/Datenbank
außerhalb des Essener Portals; „Jahrbuch für den Ruhrkohlenbezirk“ 1936/37 als Volltext
(archive.org, Google Books, DDB, HathiTrust ohne Treffer); „Die Zechen des Ruhrbezirks“;
ein Zechen-/Betriebsjahres-Datensatz für Essen in Open Data Portal Ruhr, open.NRW oder
beim Geologischen Dienst NRW.
