import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from werkzeuge.zechen_portal import (chronik_parsen, huske_status, index_parsen, kandidaten, seite_parsen, waehle_seite)

INDEX = """
<li><a href="bergbau_detailseite_1213126.de.html" ><div class="entryAlphaList divbergbau"><h4>Fridolin</h4>
<div class="tileDescription">Stollen<br /><br/>Stadtteil:  Horst</div></div></a></li>
<li><a href="bergbau_detailseite_1214553.de.html" ><div class="entryAlphaList divbergbau"><h4>Carolus-Magnus, Schacht 1</h4>
<div class="tileDescription">Schacht<br /><br/>Stadtteil:  Bergeborbeck</div></div></a></li>
<li><a href="bergbau_detailseite_1214507.de.html" ><div class="entryAlphaList divbergbau"><h4>Wolfsbank</h4>
<div class="tileDescription"><br /><br/>Stadtteil:  Überruhr-Holthausen</div></div></a></li>
<li><a href="bergbau_detailseite_1214509.de.html" ><div class="entryAlphaList divbergbau"><h4>Wolfsbank-Neuwesel</h4>
<div class="tileDescription"><br /><br/>Stadtteil:  Bergeborbeck</div></div></a></li>
<li><a href="bergbau_detailseite_1213951.de.html" ><div class="entryAlphaList divbergbau"><h4>Ver. Pörtingssiepen</h4>
<div class="tileDescription"><br /><br/>Stadtteil:  Fischlaken</div></div></a></li>
"""

SEITE = """<div id="col3"> <h1>Zeche "Fridolin"</h1>
<div class="jquery_tabs"><h4>Literaturauszüge aus...</h4><div class="tabbody">
<h2>"Die Steinkohlenzechen im Ruhrrevier"</h2>
<p>Fridolin (Essen-Steele-Horst)</p><p>1836 6.4. Verleihung Geviertfeld (0,64 km&sup2;), Stollenbau</p><p>1842 Betrieb</p>
<p>1855 in Fristen</p><p>1882 zu Eiberg</p></div>
<h2>"Bergbauhistorischer Atlas f&uuml;r die Stadt Essen"</h2><div class="tabbody"><p>Fridolin</p>
<p>Die Zeche wird 1882 mit Eiberg konsolidiert. Im Jahre 1960 wird die Fridolinstra&szlig;e nach ihr benannt.</p></div>
<h4>Literaturquellen</h4><div class="tabbody"><p>Die Steinkohlenzechen im Ruhrrevier, Joachim Huske</p></div>"""


def test_index_parsen():
    e = index_parsen(INDEX)
    assert e[0] == dict(fs_id="1213126", name="Fridolin", art="Stollen", stadtteil="Horst")
    assert e[1]["name"] == "Carolus-Magnus, Schacht 1" and e[1]["art"] == "Schacht"
    assert e[2]["art"] == "" and e[2]["stadtteil"] == "Überruhr-Holthausen"


def test_kandidaten_namensformen_und_stadtteil():
    e = index_parsen(INDEX)
    assert [k["fs_id"] for k in kandidaten("Fridolin", "Steele", e)] == ["1213126"]
    # Schacht-Einträge tragen den Zechentext: „Carolus-Magnus, Schacht 1“ passt zu „Carolus Magnus“
    assert [k["fs_id"] for k in kandidaten("Carolus Magnus", "Bergeborbeck", e)] == ["1214553"]
    # Vereinigte ↔ Ver.
    assert [k["fs_id"] for k in kandidaten("Vereinigte Pörtingssiepen", "Heidhausen", e)] == ["1213951"]
    # gleicher Name zweimal: Stadtteil entscheidet, sonst beide
    assert [k["fs_id"] for k in kandidaten("Wolfsbank", "Überruhr", e)][0] == "1214507"
    assert len(kandidaten("Wolfsbank", "", e)) == 1  # „Wolfsbank-Neuwesel“ ist kein exakter Namenstreffer
    assert kandidaten("Gibt es nicht", "", e) == []


def test_norm_namensformen():
    from werkzeuge.zechen_portal import _norm
    assert _norm("Klosterbusch Vereinigte") == _norm("Vereinigte Klosterbusch") == "klosterbusch"
    assert _norm("Alte Sackberg & Geitling Vereinigte") == _norm("Vereinigte Alte Sackberg & Geitling")
    assert _norm("Zollverein 1/2/3/4/5/6/7/8/9/10/11/12") == _norm("Zollverein 1/2") == "zollverein"
    assert _norm("Gabe Gottes (Essen)") == "gabe gottes"
    assert _norm("Sälzer und Neuack") == _norm("Sälzer & Neuack")
    assert _norm("Centrum 4/6") == "centrum"
    assert _norm("Heinrich Schacht 3") == "heinrich"  # Nummern fallen weg — Kopfvergleich unterscheidet dann nicht mehr


def test_eintrag_art_teilanlagen():
    from werkzeuge.zechen_portal import _eintrag_art
    assert _eintrag_art("Jahresanfang: Stilllegung Brikettfabrik") is None
    assert _eintrag_art("Durchschlag 6. S. mit Heinrich, Sch. 2: Förderbeginn, Sch. 1: Fördereinstellung") == "betrieb"
    assert _eintrag_art("1.10. Fördereinstellung auf Heinrich, Baufeld zu Fritz") == "ende"  # „Baufeld zu“ ist mehrdeutig
    assert _eintrag_art("15.9. Stilllegung") == "ende"
    assert _eintrag_art("Stilllegung (1951 Wiederinbetriebnahme, s. dort)") == "ende"
    # letztes Ereignis im Eintrag gilt; erfolglose Versuche nicht
    assert _eintrag_art("Mitte August: Fördereinstellung, 1.10. Stilllegung angeblich 1925 noch einmal kurze, jedoch erfolglose Wiederinbetriebnahme") == "ende"
    assert _eintrag_art("30.4. Stilllegung, Dezember: Wiederinbetriebnahme") == "betrieb"
    # „unter dem Namen“ des eigenen Namens ist kein Fremdabbau
    assert _eintrag_art("nach Stilllegung von Eiberg Wiederinbetriebnahme unter dem Namen Wohlverwahrt, Abbau", "Ver. Wohlverwahrt") == "betrieb"
    assert _eintrag_art("Abbau des Flözes unter dem Namen Wohlverwahrt", "Geitling") == "fremd"


def test_seite_parsen_und_chronik():
    s = seite_parsen(SEITE)
    assert s["portal_name"] == "Fridolin" and s["portal_stadtteil"] == "Steele-Horst"
    assert s["huske"][0].startswith("1836 6.4. Verleihung Geviertfeld (0,64 km²)")
    assert s["atlas"].startswith("Die Zeche wird 1882")
    c = chronik_parsen(s["huske"])
    assert [(j, t[:10]) for j, t in c] == [(1836, "6.4. Verle"), (1842, "Betrieb"), (1855, "in Fristen"), (1882, "zu Eiberg")]


def test_huske_status_faelle():
    # Fridolin: Betrieb, in Fristen, 1882 zu Eiberg → stillgelegt
    st, grund = huske_status([(1836, "6.4. Verleihung"), (1842, "Betrieb"), (1855, "in Fristen"), (1882, "zu Eiberg")], laenge=200)
    assert st == "stillgelegt" and "1882 zu Eiberg" in grund
    # Carolus Magnus: Förderzahlen 1935, Anpachtung 1936 → aktiv
    st, grund = huske_status([(1848, "Förderbeginn"), (1935, "273275 t, 716 B"), (1936, "Anpachtung Teilfeld"), (1951, "20.10. Stilllegung")], laenge=3000)
    assert st == "aktiv" and "1936 Anpachtung" in grund
    # Plaetzgesbank: Stilllegung 1927, Neugründung 1933, Betrieb 1936 → aktiv (kampagnenweise)
    st, _ = huske_status([(1927, "30.4. Stilllegung"), (1933, "Neugründung"), (1936, "20.1. – 20.3. Betrieb"), (1959, "31.5. Stilllegung")], laenge=1800)
    assert st == "aktiv"
    # Voßhege: um 1871 zu Flor Flörchen, 1947 Wiederinbetriebnahme → 1936 stillgelegt
    st, _ = huske_status([(1800, "Stollenbau"), (1871, "zu Flor Flörchen"), (1947, "Wiederinbetriebnahme"), (1952, "Stilllegung")], laenge=500)
    assert st == "stillgelegt"
    # Geitling: 1844 Abbau unter dem Namen Wohlverwahrt, 1940 Konsolidation → nichts Positives nach 1844 … stillgelegt? Nein:
    # „liegt schon lange still“ 1837 ist ein Stillstand, 1844 „Abbau des Flözes unter dem Namen Wohlverwahrt“ → kein eigener Betrieb → unklar
    st, _ = huske_status([(1813, "ab März außer Betrieb"), (1837, "„die Zeche liegt schon lange still“"), (1844, "Abbau des Flözes unter dem Namen Wohlverwahrt"), (1940, "Konsolidation zu Wohlverwahrt")], laenge=600)
    assert st == "unklar"
    # Graf Beust: langer Text, endet 1898 ohne Ende → abgeschnitten → unklar
    st, grund = huske_status([(1838, "Beantragung"), (1841, "Förderbeginn"), (1898, "Tieferteufen Sch. 1")], laenge=3758)
    assert st == "unklar" and "abgeschnitten" in grund
    # Emil-Fritz: erster Eintrag nach 1936 → stillgelegt (existierte noch nicht)
    st, grund = huske_status([(1965, "entstanden aus"), (1970, "Stilllegung")], laenge=300)
    assert st == "stillgelegt" and "erst 1965" in grund
    # Langenbrahm: langer Text, bricht 1828 mitten in „Stille…“ ab → abgeschnitten, auch wenn die letzte Zeile wie ein Ende aussieht
    st, grund = huske_status([(1800, "Betrieb"), (1828, "Inbetriebnahme des Schienenweges, Stille")], laenge=3705)
    assert st == "unklar" and "abgeschnitten" in grund
    # Fritz-Heinrich: „Ende“ 1935 (Baufeld zu Fritz), aber Förderzahlen 1940 → Widerspruch → unklar
    st, grund = huske_status([(1934, "1.129830 t, 2813 B"), (1935, "1.10. Fördereinstellung auf Heinrich, Baufeld zu Fritz"), (1940, "1.280280 t, 2938 B")], laenge=2000)
    assert st == "unklar" and "Förderzahlen" in grund
    # kurzer Text ohne Betriebsbeleg bis 1936 und ohne Ende → unklar
    assert huske_status([(1850, "Verleihung Geviertfeld")], laenge=100)[0] == "unklar"


def test_waehle_seite_nach_seitenkopf():
    k1, k2, k3 = dict(fs_id="1"), dict(fs_id="2"), dict(fs_id="3")
    s_kat = dict(portal_name="Katharina", portal_stadtteil="Kray")
    s_cen = dict(portal_name="Centrum 4/6", portal_stadtteil="Kray-Leithe")
    # zwei Schachtseiten derselben Zeche + eine fremde → eindeutig Katharina
    w = waehle_seite("Katharina", [(k1, s_kat), (k2, s_cen), (k3, dict(s_kat))])
    assert [k["fs_id"] for k, _ in w] == ["1"]
    # Kopf abweichend geschrieben („Ver. Helene Amalie“) → kein Kopftreffer, Kandidat bleibt
    w = waehle_seite("Vereinigte Helene & Amalie", [(k1, dict(portal_name="Ver. Helene Amalie", portal_stadtteil="Altenessen"))])
    assert len(w) == 1
    # zwei verschiedene Zechen gleichen Namens → beide bleiben (mehrdeutig), außer der Stadtteil entscheidet
    paare = [(k1, dict(portal_name="Geitling", portal_stadtteil="Steele-Horst")), (k2, dict(portal_name="Geitling", portal_stadtteil="Überruhr-Burgaltendorf"))]
    assert len(waehle_seite("Geitling", paare)) == 2
    assert [k["fs_id"] for k, _ in waehle_seite("Geitling", paare, "Burgaltendorf")] == ["2"]
