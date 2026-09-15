import pytest
from pipeline.lib.parser import Adresse, parse_adresse


def a(**kw):
    basis = dict(strasse_roh="", hausnr="", hausnr_zusatz="", hausnr_bis="", lage="", zusatz_frei="", status="ok")
    basis.update(kw)
    return Adresse(**basis)


@pytest.mark.parametrize("text, erwartet", [
    ("Kraspothstr. 44", a(strasse_roh="Kraspothstr.", hausnr="44")),
    ("Kahrstr. 39D", a(strasse_roh="Kahrstr.", hausnr="39", hausnr_zusatz="d")),
    ("Lührmannstr. 24A", a(strasse_roh="Lührmannstr.", hausnr="24", hausnr_zusatz="a")),
    ("Arndtstr. 14 III", a(strasse_roh="Arndtstr.", hausnr="14", lage="III")),
    ("Schubertstr. 43 I.", a(strasse_roh="Schubertstr.", hausnr="43", lage="I")),
    ("Julienstr. 26 Iii", a(strasse_roh="Julienstr.", hausnr="26", lage="III")),
    ("Steeler Str. 12 Erdg.", a(strasse_roh="Steeler Str.", hausnr="12", lage="Erdg.")),
    ("Steeler Str. 12 Untg.", a(strasse_roh="Steeler Str.", hausnr="12", lage="Untg.")),
    ("Frohnhauser Str. 137-137A", a(strasse_roh="Frohnhauser Str.", hausnr="137", hausnr_bis="137a")),
    ("Koloniestr. 7-13", a(strasse_roh="Koloniestr.", hausnr="7", hausnr_bis="13")),
    ("Taborstr. 15A.15B.15C", a(strasse_roh="Taborstr.", hausnr="15", hausnr_zusatz="a", zusatz_frei="15B.15C")),
    ("Vogelheimer Str. Nr. 109", a(strasse_roh="Vogelheimer Str.", hausnr="109")),
    ("Laubenhof 1 Nr. 4", a(strasse_roh="Laubenhof", hausnr="1", zusatz_frei="Nr. 4")),
    ("Klosterstr. 1.3", a(strasse_roh="Klosterstr.", hausnr="1", zusatz_frei="3")),
    ("Hauptstr. 14 1/2", a(strasse_roh="Hauptstr.", hausnr="14", zusatz_frei="1/2")),
    ("Wächtlerstr., Lagerplatz", a(strasse_roh="Wächtlerstr.", zusatz_frei="Lagerplatz", status="ohne_nummer")),
    ("Börsenhaus", a(strasse_roh="Börsenhaus", status="ohne_nummer")),
    ("Alfredistraße ", a(strasse_roh="Alfredistraße", status="ohne_nummer")),
    ("", a(status="leer")),
    ("   ", a(status="leer")),
    ("II. Schichtstr., Zechengelände", a(strasse_roh="II. Schichtstr.", zusatz_frei="Zechengelände", status="ohne_nummer")),
    ("Am krausen Bäumchen 18", a(strasse_roh="Am krausen Bäumchen", hausnr="18")),
    ("Hstr. 12a", a(strasse_roh="Hstr.", hausnr="12", hausnr_zusatz="a")),
    ("Ludwigstr.9", a(strasse_roh="Ludwigstr.", hausnr="9")),
    ("Aktienstr.13 I", a(strasse_roh="Aktienstr.", hausnr="13", lage="I")),
    ("Mittelstr.12a", a(strasse_roh="Mittelstr.", hausnr="12", hausnr_zusatz="a")),
    ("Hohe Kuppe6", a(strasse_roh="Hohe Kuppe", hausnr="6")),
    ("Huyssenallee77", a(strasse_roh="Huyssenallee", hausnr="77")),
    ("Byfanger Str. .145", a(strasse_roh="Byfanger Str.", hausnr="145")),
    ("Luisenstr .26", a(strasse_roh="Luisenstr", hausnr="26")),
    ("Hstr..9", a(strasse_roh="Hstr.", hausnr="9")),
    ("1. Weberstr. 22/24", a(strasse_roh="1. Weberstr.", hausnr="22", zusatz_frei="/24")),
    ("1. Postneubau a. Hbf.", a(strasse_roh="1. Postneubau a. Hbf.", status="ohne_nummer")),
    # Buchstabenzusatz mit Leerzeichen (A-H, damit Lage-Ziffern I/V unberührt bleiben)
    ("Hohenburgweg 3 B", a(strasse_roh="Hohenburgweg", hausnr="3", hausnr_zusatz="b")),
    ("Kahrstr. 39 D", a(strasse_roh="Kahrstr.", hausnr="39", hausnr_zusatz="d")),
    ("Arndtstr. 14 I", a(strasse_roh="Arndtstr.", hausnr="14", lage="I")),
    ("Arndtstr. 14 V", a(strasse_roh="Arndtstr.", hausnr="14", lage="V")),
    ("Steeler Str. 12 Erdg.", a(strasse_roh="Steeler Str.", hausnr="12", lage="Erdg.")),
    # Ordinal im Straßennamen
    ("Platz des 21. März 5", a(strasse_roh="Platz des 21. März", hausnr="5")),
    ("Platz des 21. März", a(strasse_roh="Platz des 21. März", status="ohne_nummer")),
    # Das Ordinal im Namen greift nur vor einem Wort, nie vor einer weiteren Zahl:
    # "Hubertstr. 234. 234A" ist eine Hausnummernliste, kein Ordinal im Straßennamen.
    ("Hubertstr. 234.  234A", a(strasse_roh="Hubertstr.", hausnr="234", zusatz_frei=". 234A")),
    ("Wackenberg 17. 19.", a(strasse_roh="Wackenberg", hausnr="17", zusatz_frei=". 19.")),
    ("Thomaestr. 230. 230A", a(strasse_roh="Thomaestr.", hausnr="230", zusatz_frei=". 230A")),
    ("Bochumer Str. 37. 37a", a(strasse_roh="Bochumer Str.", hausnr="37", zusatz_frei=". 37a")),
    # Ein Punkt hinter dem Buchstaben schließt den Hausnummernzusatz aus.
    ("Vereinstraße 38 a. d. Hindenburgstraße",
     a(strasse_roh="Vereinstraße", hausnr="38", zusatz_frei="a. d. Hindenburgstraße")),
    ("Klemensborn 53 H. ", a(strasse_roh="Klemensborn", hausnr="53", zusatz_frei="H.")),
])
def test_parse_adresse(text, erwartet):
    assert parse_adresse(text) == erwartet


def test_unklar_wenn_zahl_vor_strasse():
    r = parse_adresse("12 Karlstr.")
    assert r.status == "unklar"
