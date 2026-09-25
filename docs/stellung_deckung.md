# Deckung Handwerksberufe: Teil III gegen Teil I

Erzeugt von `werkzeuge/handwerk_deckung.py` am 2026-09-25 — nicht von Hand bearbeiten. Grundlage der Handprüfung
der sozialen Stellung nach Weg 3 (`docs/stellung.md`, Grenzfälle).

Je Berufsfamilie: **offen** = Nennungen ohne Meister-/Gewerbezusatz mit Stellung `arbeiter`/`unbestimmt`;
**Inhaber** = Nennungen mit Stellung `selbstaendige`; **Betriebe** = Betriebe der genannten Rubriken in Teil III;
**Lücke** = Betriebe − Inhaber (mindestens 0) = Betriebe, die kein gekennzeichneter Eintrag erklärt;
**Quote** = Lücke / offen = Anteil der offenen Nennungen, der mindestens Inhaber sein muss.
Empfehlung: Quote < 10% → `arbeiter` bestätigen; sonst `unbestimmt` bis zum Adressabgleich Teil I ↔ Teil III.
Aufgenommen sind Familien mit Betrieben in Teil III und Inhaberform in Teil I oder ≥ 50 offenen Nennungen.
Die Zuordnung Rubrik ↔ Beruf ist eine Heuristik (erstes Wort der Rubrik, Synonyme wie Tischler/Schreiner);
Quoten über 100 % heißen: mehr unerklärte Betriebe als offene Nennungen — die Familie ist zu eng gefasst.

| Familie | offen | Inhaber | Betriebe | Lücke | Quote | Empfehlung | Rubriken (Teil III) | offene Schreibweisen |
|---|---:|---:|---:|---:|---:|---|---|---|
| schornsteinfeger | 8 | 22 | 35 | 13 | 162% | unbestimmt | Schornsteinfegermeister | Schornsteinfeger |
| dekorateur | 105 | 0 | 143 | 143 | 136% | unbestimmt | Dekorateur u. Dekorationsgeschäft | Dekorateur |
| uhrmacher | 141 | 9 | 130 | 121 | 86% | unbestimmt | Uhrmacher und Uhrenhandlung | Uhrm., Uhrmach., Uhrmacher |
| friseur | 809 | 300 | 657 | 357 | 44% | unbestimmt | Friseur, Friseur für Damen | Friseur, Friseuse |
| schuhmacher | 494 | 582 | 693 | 111 | 22% | unbestimmt | Schuhmacher | Schuhm., Schuhmach., Schuhmacher |
| drechsler | 26 | 5 | 10 | 5 | 19% | unbestimmt | Drechsler (Holz- u. Horn-) | Drechsler |
| kuerschner | 17 | 15 | 18 | 3 | 18% | unbestimmt | Kürschner | Kürschner |
| maler | 2048 | 439 | 728 | 289 | 14% | unbestimmt | Maler | Anstreich., Anstreicher, Maler |
| stukkateur | 351 | 0 | 44 | 44 | 12% | unbestimmt | Stukkateur | Stukkateur |
| schneider | 1218 | 1082 | 1209 | 127 | 10% | unbestimmt | Schneider für Herren, Schneider für Damen, Schneiderin | Schneid., Schneider, Schneiderin |
| schmied | 1337 | 0 | 122 | 122 | 9% | arbeiter | Schmied | Schmied |
| buchdrucker | 303 | 83 | 110 | 27 | 9% | arbeiter | Buchdruckerei | Buchdruck., Buchdrucker |
| glasblaeser | 50 | 0 | 3 | 3 | 6% | arbeiter | Glasbläserei | Glasbläs., Glasbläser |
| konditor | 173 | 158 | 162 | 4 | 2% | arbeiter | Konditorei | Konditor |
| schleifer | 382 | 0 | 8 | 8 | 2% | arbeiter | Schleiferei | Schleifer |
| sattler | 202 | 66 | 70 | 4 | 2% | arbeiter | Sattler | Sattler |
| mechaniker | 344 | 23 | 28 | 5 | 2% | arbeiter | Mechaniker und mech. Werkstätte | Mechanik., Mechaniker |
| dreher | 2418 | 0 | 4 | 4 | 0% | arbeiter | Dreherei | Dreh., Dreher |
| schlosser | 7425 | 222 | 111 | 0 | 0% | arbeiter | Schlosser | Schloss., Schlosser |
| maurer | 2416 | 60 | 19 | 0 | 0% | arbeiter | Maurermeister | Maur., Maurer |
| schreiner | 1751 | 699 | 376 | 0 | 0% | arbeiter | Tischler | Schrein., Schreiner, Tischler |
| klempner | 847 | 290 | 260 | 0 | 0% | arbeiter | Klempner, Installateur | Install., Installat., Installateur, Klempn., Klempner |
| gaertner | 582 | 132 | 63 | 0 | 0% | arbeiter | Gärtner | Gärtn., Gärtner |
| baecker | 565 | 840 | 536 | 0 | 0% | arbeiter | Bäcker | Bäcker |
| metzger | 541 | 741 | 496 | 0 | 0% | arbeiter | Metzger, Metzger (Groß-) | Fleischer, Metzg., Metzger |
| zimmerer | 478 | 67 | 44 | 0 | 0% | arbeiter | Zimmermeister | Zimmerer, Zimmerm., Zimmermann |
| dachdecker | 306 | 163 | 85 | 0 | 0% | arbeiter | Dachdeckermeister | Dachdeck., Dachdecker |
| stellmacher | 162 | 31 | 25 | 0 | 0% | arbeiter | Stellmacher | Stellm., Stellmach., Stellmacher |
| weber | 146 | 5 | 5 | 0 | 0% | arbeiter | Weberei | Weber |
| buchbinder | 121 | 28 | 26 | 0 | 0% | arbeiter | Buchbinderei | Buchbind., Buchbinder |
| kuefer | 39 | 19 | 9 | 0 | 0% | arbeiter | Küfer | Küfer |
| marmorschleifer | 23 | 5 | 4 | 0 | 0% | arbeiter | Marmorschleiferei | Marmorschleif., Marmorschleifer |
| glaser | 16 | 6 | 1 | 0 | 0% | arbeiter | Glaser und Glashandlung | Glaser |
| faerber | 11 | 8 | 7 | 0 | 0% | arbeiter | Färberei | Färber |
| leichenbestatter | 9 | 19 | 16 | 0 | 0% | arbeiter | Leichenbestatter u. -bestatterinnen | Leichenbestatter |
| autosattler | 0 | 7 | 6 | 0 | – | – | Auto-Sattlerei |  |
| bauunternehmer | 0 | 274 | 134 | 0 | – | – | Bauunternehmer |  |
| bauklempner | 0 | 14 | 12 | 0 | – | – | Bauklempnerei |  |
| bildhauer | 0 | 10 | 53 | 43 | – | – | Bildhauer |  |
| gastwirt | 0 | 415 | 273 | 0 | – | – | Gastwirt |  |
| handelsvertreter | 0 | 75 | 9 | 0 | – | – | Handelsvertreter |  |
| hebamme | 0 | 151 | 167 | 16 | – | – | Hebamme |  |
| heilpraktiker | 0 | 16 | 54 | 38 | – | – | Heilpraktiker |  |
| klavierbauer | 0 | 15 | 13 | 0 | – | – | Klavierbauer |  |
| kunststopfer | 0 | 14 | 15 | 1 | – | – | Kunststopferei |  |
| masseur | 0 | 38 | 24 | 0 | – | – | Masseur und Masseuse |  |
| schankwirt | 0 | 1413 | 904 | 0 | – | – | Schankwirt |  |
| strassenbau | 0 | 5 | 14 | 9 | – | – | Straßenbau |  |
| tiefbauunternehmer | 0 | 14 | 65 | 51 | – | – | Tiefbauunternehmer |  |
