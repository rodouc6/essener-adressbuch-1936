from pipeline.lib.karte_export import (adress_id, anzeige_adresse, baue_adressscherben, baue_berufsindex,
                                       baue_firmenindex, baue_namensindex, baue_stadtteile, baue_strassenindex,
                                       baue_strassenscherben, etagen_rang, falte, praefix2, scherbe,
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


def test_adressscherben_entsprechen_punkt_feature_plus_koordinaten():
    adressen = _adressen()
    scherben = baue_adressscherben(adressen)
    for aid, a in adressen.items():
        eintrag = scherben[scherbe(aid)][aid]
        erwartet = dict(punkt_feature(a)["properties"], lat=a["lat"], lon=a["lon"])
        assert eintrag == erwartet
    # zwei Adressen in unterschiedlichen Scherben (Lattenkamp/Katernberg vs. Bochumer Straße/Steele)
    aid_katernberg = adress_id(_v(id="1"))
    aid_steele = adress_id(_v(id="4", strasse_heute="Bochumer Straße", hausnr="5", stadtteil="Steele",
                                strasse_roh="Bochumer Str.", Vorort="Steele"))
    assert scherbe(aid_katernberg) != scherbe(aid_steele)
    assert scherben[scherbe(aid_steele)][aid_steele]["lat"] == 51.45


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
    assert namen[("Lattenkamp", "heute", "Katernberg")]["adressen_n"] == 2
    assert namen[("Grenzstr.", "1936", "Katernberg")]["zeilen"] == 3
    assert namen[("Bochumer Str.", "1936", "Steele")]["schluessel"] == "bochumer str"
    assert all("adressen" not in x for x in s)


def test_strassenscherben():
    sch = baue_strassenscherben(_adressen())
    lattenkamp = sorted([adress_id(_v(id="1")), adress_id(_v(id="2", hausnr="27"))])
    grenzstr = sorted([adress_id(_v(id="1")), adress_id(_v(id="2", hausnr="27"))])
    assert sch["la"]["Lattenkamp|heute|Katernberg"] == lattenkamp
    assert sch["gr"]["Grenzstr.|1936|Katernberg"] == grenzstr


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


import json, pathlib, shutil

import pytest

from pipeline.lib.karte_export import baue_kennzahlen, schreibe_paket, tippecanoe_befehl, zechen_geojson
from pipeline.lib.io import lies_csv

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_kennzahlen():
    e = [_v(id="1", teil="I"), _v(id="2", teil="II"), _v(id="3", teil="I", stufe="strasse", hausnr="27"),
         _v(id="4", teil="III", stufe="offen", lat="", lon="")]
    k = baue_kennzahlen(e, gruppiere(e, []), "2026-09-21")
    assert k["eintraege_je_teil"] == {"I": 2, "II": 1, "III": 1}
    assert k["stufen"] == {"haus": 50.0, "strasse": 25.0, "stadtplan": 0.0, "offen": 25.0}
    assert k["verortet"] == 3 and k["offen"] == 1 and k["adressen"] == 2 and k["stand"] == "2026-09-21"


def test_zechen_geojson_laesst_zeilen_ohne_koordinaten_weg():
    g = zechen_geojson(lies_csv(FIX / "zechen.csv"))
    assert [f["properties"]["name"] for f in g["features"]] == ["Zeche Zollverein", "Zeche Alt", "Zeche Jahre Unbekannt"]
    p = g["features"][0]["properties"]
    assert p["aktiv_1936"] is True and p["status_1936"] == "aktiv" and p["jahre_unbekannt"] is False
    # Betriebsjahre aus dem Artikel; die abweichende Liste bleibt als Widerspruch sichtbar
    assert (p["betrieb_von"], p["betrieb_bis"]) == ("1851", "1986") and p["jahre_widerspruch"] is True
    assert p["liste_von"] == "1847" and p["plan_1935"] == "Zeche Zollverein"
    assert g["features"][1]["properties"]["aktiv_1936"] is False and g["features"][1]["properties"]["jahre_widerspruch"] is False
    assert g["features"][0]["geometry"]["coordinates"] == [7.0447, 51.4861]


def test_zechen_geojson_status_unklar_zaehlt_nicht_als_aktiv():
    g = zechen_geojson(lies_csv(FIX / "zechen.csv"))
    p = next(f["properties"] for f in g["features"] if f["properties"]["name"] == "Zeche Jahre Unbekannt")
    assert p["aktiv_1936"] is False and p["status_1936"] == "unklar" and p["jahre_unbekannt"] is True
    # ohne status_1936-Spalte (alte Tabelle) ist nichts aktiv — kein Rückfall auf die Listenjahre
    g2 = zechen_geojson([dict(name="X", lat="51.4", lon="7.0", betrieb_von="1900", betrieb_bis="1950")])
    assert g2["features"][0]["properties"]["aktiv_1936"] is False


def test_tippecanoe_befehl():
    b = tippecanoe_befehl(pathlib.Path("a.geojson"), pathlib.Path("a.pmtiles"))
    assert b[0] == "tippecanoe" and "-o" in b and "a.pmtiles" in b and "--maximum-zoom=15" in b


def test_schreibe_paket(tmp_path):
    e = [_v(id="1", lastname="Sepeur", firstname="Wilh.", teil="I"), _v(id="2", lastname="Jäger", teil="III",
         Firmenname="M. Jäger, Althandlung")]
    k = schreibe_paket(tmp_path, e, [], lies_csv(FIX / "zechen.csv"), "2026-09-21", kacheln=False)
    aid = adress_id(e[0])
    assert json.loads((tmp_path / "haus" / f"{aid[:2]}.json").read_text())[aid][0]["name"] == "Jäger"
    assert (tmp_path / "suche" / "namen" / "se.json").exists()
    assert (tmp_path / "suche" / "firmen" / "mj.json").exists()
    assert json.loads((tmp_path / "suche" / "strassen.json").read_text())[0]["name"] in ("Grenzstr.", "Lattenkamp")
    assert (tmp_path / "suche" / "strassen" / "gr.json").exists()
    assert json.loads((tmp_path / "kennzahlen.json").read_text()) == k
    assert len(json.loads((tmp_path / "zechen.geojson").read_text())["features"]) == 3
    geo = json.loads((tmp_path / "adressen.geojson").read_text())
    assert geo["features"][0]["properties"]["n_I"] == 1
    scherbe_inhalt = json.loads((tmp_path / "adressen" / f"{aid[:2]}.json").read_text())
    assert scherbe_inhalt[aid]["lat"] == 51.49 and scherbe_inhalt[aid]["strasse_heute"] == "Lattenkamp"


@pytest.mark.skipif(shutil.which("tippecanoe") is None, reason="tippecanoe nicht installiert")
def test_schreibe_paket_mit_kacheln(tmp_path):
    e = [_v(id="1", lastname="Sepeur", teil="I")]
    schreibe_paket(tmp_path, e, [], [], "2026-09-21", kacheln=True)
    assert (tmp_path / "adressen.pmtiles").stat().st_size > 100


def test_faksimile_tabelle_und_export(tmp_path):
    from pipeline.lib.karte_export import faksimile_tabelle
    fak = [dict(seite="I-333", bild="355", etikett="I. Teil:  333"), dict(seite="", bild="", etikett="")]
    assert faksimile_tabelle(fak) == {"I-333": 355}
    schreibe_paket(tmp_path, [_v(id="1", lastname="Sepeur", teil="I")], [], [], "2026-09-21", kacheln=False, faksimile=fak)
    assert json.loads((tmp_path / "faksimile.json").read_text()) == {"I-333": 355}
