from pipeline.lib.karte_export import (adress_id, etagen_rang, falte, praefix2, scherbe,
                                       sortiere_eintraege)
from pipeline.lib.stufen import ADRESSSCHLUESSEL


def _e(**k):
    z = {f: "" for f in ADRESSSCHLUESSEL}
    z.update(lastname="", firstname="", lage="", teil="I", id="1")
    z.update(k)
    return z


def test_adress_id_haengt_nur_am_schluessel():
    a = _e(strasse_heute="Lattenkamp", hausnr="25", stadtteil="Katernberg", lastname="Sepeur")
    b = _e(strasse_heute="Lattenkamp", hausnr="25", stadtteil="Katernberg", lastname="Kowalski")
    c = _e(strasse_heute="Lattenkamp", hausnr="27", stadtteil="Katernberg")
    assert adress_id(a) == adress_id(b) != adress_id(c)
    assert len(adress_id(a)) == 12 and scherbe(adress_id(a)) == adress_id(a)[:2]


def test_falte_und_praefix():
    assert falte("Grenzstraße") == "grenzstrasse"
    assert falte("Müller-Lüdenscheidt, Ä.") == "mueller luedenscheidt ae"
    assert falte("  St.  Ännchen ") == "st aennchen"
    assert praefix2("Sepeur") == "se" and praefix2("Ö") == "oe" and praefix2("") == "_"


def test_etagen_rang_und_sortierung():
    assert etagen_rang("Erdg.") < etagen_rang("I") < etagen_rang("II") < etagen_rang("III") < etagen_rang("")
    assert etagen_rang("parterre.") == etagen_rang("Erdg.")
    e = [_e(lastname="Zander", lage=""), _e(lastname="Meier", lage="II"), _e(lastname="Adam", lage=""),
         _e(lastname="Kunz", lage="Erdg."), _e(lastname="Berg", lage="II")]
    assert [x["lastname"] for x in sortiere_eintraege(e)] == ["Kunz", "Berg", "Meier", "Adam", "Zander"]
