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
])
def test_parse_adresse(text, erwartet):
    assert parse_adresse(text) == erwartet


def test_unklar_wenn_zahl_vor_strasse():
    r = parse_adresse("12 Karlstr.")
    assert r.status == "unklar"
