from pipeline.lib.karte_export import (adress_id, anzeige_adresse, baue_berufsindex, baue_firmenindex,
                                       baue_namensindex, baue_stadtteile, baue_strassenindex, etagen_rang, falte, praefix2, scherbe,
                                       sortiere_eintraege, baue_scherben, eintrag_kurz, gruppiere, punkt_feature)
from pipeline.lib.merkmale import Regel
from pipeline.lib.stufen import ADRESSSCHLUESSEL


def _e(**k):
    z = {f: "" for f in ADRESSSCHLUESSEL}
    z.update(lastname="", firstname="", lage="", teil="I", id="1")
    z.update(k)
    return z


REGELN = [Regel("Beruf o. ä.", "praefix", "Dr.", "akademiker")]


def _v(**k):
    """Verorteter Eintrag mit sinnvollen Standardwerten."""
    z = _e(strasse_heute="Lattenkamp", hausnr="25", stadtteil="Katernberg", strasse_roh="Grenzstr.",
           Vorort="Katernberg", herkunft="konkordanz", lat="51.49", lon="7.06", stufe="haus", page="I-551",
           seite="551", **{"Beruf o. ä.": "Bergm.", "Familienstand": "", "Vorname Bezugsperson": "",
                            "Beruf Bezugsperson": "", "Firmenname": "", "Eigentümer": "", "Verwalter": "",
                            "abweichender Wohnort": "", "zeitlich_abweichend": "nein", "mehrdeutig": "nein",
                            "grund_mehrdeutig": "", "nummer_unsicher": "nein"})
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


def test_gruppiere_zaehlt_teile_und_merkmale():
    e = [_v(id="1", lastname="Sepeur", teil="I"), _v(id="2", lastname="Zeche", teil="II"),
         _v(id="3", lastname="Meier", teil="III", **{"Beruf o. ä.": "Dr. med."}),
         _v(id="4", lastname="Offen", stufe="offen", lat="", lon=""),
         _v(id="5", lastname="Anders", hausnr="27")]
    adressen = gruppiere(e, REGELN)
    assert len(adressen) == 2
    a = adressen[adress_id(e[0])]
    assert [x["id"] for x in a["eintraege"]] == ["3", "1", "2"]  # Etage fehlt überall → alphabetisch
    f = punkt_feature(a)
    assert f["geometry"]["coordinates"] == [7.06, 51.49]
    p = f["properties"]
    assert (p["n_I"], p["n_II"], p["n_III"], p["m_akademiker"]) == (1, 1, 1, 1)
    assert p["stufe"] == "haus" and p["historisch"] == "Grenzstr. 25, Katernberg"
    assert p["strasse_heute"] == "Lattenkamp" and p["hausnr"] == "25" and p["stadtteil"] == "Katernberg"


def test_stadtplan_punkt_bekommt_stufe_stadtplan():
    e = [_v(id="1", stufe="strasse", herkunft="stadtplan_1935", strasse_heute="", hausnr="12",
            strasse_roh="Matthiasstr.", Vorort="")]
    a = next(iter(gruppiere(e, []).values()))
    p = punkt_feature(a)["properties"]
    assert p["stufe"] == "stadtplan" and p["historisch"] == "Matthiasstr. 12" and p["strasse_heute"] == ""


def test_eintrag_kurz_und_scherben():
    e = _v(id="7", lastname="Sepeur", firstname="Wilh.", teil="I", lage="II", nummer_unsicher="ja",
           **{"Beruf o. ä.": "Dr. Bergm.", "Familienstand": "Wwe."})
    k = eintrag_kurz(e, ["akademiker"])
    assert k == {"id": "7", "teil": "I", "seite": "I-551", "name": "Sepeur", "vorname": "Wilh.",
                 "beruf": "Dr. Bergm.", "etage": "II", "stand": "Wwe.", "bezug_vorname": "", "bezug_beruf": "",
                 "firma": "", "eigentuemer": "", "verwalter": "", "wohnort": "", "flags": ["nummer_unsicher"],
                 "merkmale": ["akademiker"]}
    adressen = gruppiere([e], REGELN)
    sch = baue_scherben(adressen)
    aid = adress_id(e)
    assert list(sch) == [aid[:2]] and sch[aid[:2]][aid][0]["name"] == "Sepeur"


def _adressen():
    e = [_v(id="1", lastname="Sepeur", firstname="Wilh.", teil="I"),
         _v(id="2", lastname="Sepeur", firstname="Anna", teil="I", hausnr="27"),
         _v(id="3", lastname="Jäger", firstname="M.", teil="III", Firmenname="M. Jäger, Althandlung",
            **{"Beruf o. ä.": ""}),
         _v(id="4", lastname="Ost", teil="I", strasse_heute="Bochumer Straße", hausnr="5", stadtteil="Steele",
            strasse_roh="Bochumer Str.", Vorort="Steele", lat="51.45", lon="7.08", **{"Beruf o. ä.": "Hauer"})]
    return gruppiere(e, [])


def test_namens_und_firmenindex():
    n = baue_namensindex(_adressen())
    assert sorted(n) == ["ja", "os", "se"]
    assert n["se"][0][:5] == ["sepeur anna", "Sepeur", "Anna", "Bergm.", "Lattenkamp 27, Katernberg"]
    assert n["se"][1][5:] == ["1", adress_id(_v(id="1")), "I"]
    f = baue_firmenindex(_adressen())
    assert list(f) == ["mj"] and f["mj"][0][:2] == ["m jaeger althandlung", "M. Jäger, Althandlung"]


def test_strassenindex_heute_und_1936():
    s = baue_strassenindex(_adressen())
    namen = {(x["name"], x["art"], x["ort"]): x for x in s}
    assert namen[("Lattenkamp", "heute", "Katernberg")]["zeilen"] == 3
    assert len(namen[("Lattenkamp", "heute", "Katernberg")]["adressen"]) == 2
    assert namen[("Grenzstr.", "1936", "Katernberg")]["zeilen"] == 3
    assert namen[("Bochumer Str.", "1936", "Steele")]["schluessel"] == "bochumer str"


def test_berufsindex_und_stadtteile():
    liste, scherben = baue_berufsindex(_adressen())
    assert liste[0] == ["bergm", "Bergm.", 2] and ["hauer", "Hauer", 1] in liste
    assert sorted(scherben["be"]["Bergm."]) == sorted([[adress_id(_v(id="1")), 1], [adress_id(_v(id="2", hausnr="27")), 1]])
    st = baue_stadtteile(_adressen())
    assert [x["name"] for x in st] == ["Katernberg", "Steele"] and st[0]["zeilen"] == 3
    assert st[0]["lat"] == 51.49 and st[1]["lon"] == 7.08


def test_anzeige_adresse_stadtplan():
    a = next(iter(gruppiere([_v(id="1", herkunft="stadtplan_1935", stufe="strasse", strasse_heute="",
                                strasse_roh="Matthiasstr.", Vorort="")], []).values()))
    assert anzeige_adresse(a) == "Matthiasstr. 25 (Stadtplan 1935)"
