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
                 "firma": "", "eigentuemer": "", "verwalter": "", "wohnort": "", "eigentuemer_kanon": "",
                 "kategorie": "", "pruefung": "", "beruf_norm": "", "ohdab": "", "niveau": "", "status": "", "gattung": "",
                 "stellung": "", "stellung_quelle": "", "gruppe": "", "rubrik": "", "gewerbe_gruppe": "", "gewerbe_art": "", "gewerbe_quelle": "",
                 "flags": ["nummer_unsicher"], "merkmale": ["akademiker"]}
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

from pipeline.lib.karte_export import baue_kennzahlen, gruppiere, schreibe_paket, startseite_beispiele, tippecanoe_befehl, zechen_geojson
from pipeline.lib.io import lies_csv

FIX = pathlib.Path(__file__).parent / "fixtures"


def test_kennzahlen():
    e = [_v(id="1", teil="I"), _v(id="2", teil="II"), _v(id="3", teil="I", stufe="strasse", hausnr="27"),
         _v(id="4", teil="III", stufe="offen", lat="", lon="")]
    k = baue_kennzahlen(e, gruppiere(e, []), "2026-09-21")
    assert k["eintraege_je_teil"] == {"I": 2, "II": 1, "III": 1}
    assert k["stufen"] == {"haus": 50.0, "strasse": 25.0, "stadtplan": 0.0, "offen": 25.0}
    assert k["verortet"] == 3 and k["offen"] == 1 and k["adressen"] == 2 and k["stand"] == "2026-09-21"
    # absolute Zähler für die Trichter der Schlaglichter (Spec 2026-09-27 §3.4)
    assert (k["eintraege"], k["eintraege_I"], k["eintraege_II"], k["eintraege_III"]) == (4, 2, 1, 1)
    assert (k["stufe_haus"], k["stufe_strasse"], k["stufe_stadtplan"], k["stufe_offen"]) == (2, 1, 0, 1)
    assert k["stufe_haus"] + k["stufe_strasse"] + k["stufe_stadtplan"] + k["stufe_offen"] == k["eintraege"]
    assert k["besitz_hand"] == k["besitz_geprueft"] - k["besitz_regel"]
    # ohne _beruf/_gewerbe: alles unbestimmt bzw. keine Betriebe
    assert (k["teil_i_n"], k["beruf_geprueft_n"], k["stellung_hand_n"], k["stellung_vorschlag_n"], k["stellung_unbestimmt_n"]) == (2, 0, 0, 0, 2)
    assert (k["betriebe_n"], k["gewerbe_hand_n"], k["gewerbe_claude_n"], k["gewerbe_regel_n"]) == (0, 0, 0, 0)


def test_kennzahlen_absolut_stellung_und_gewerbe():
    e = [_v(id="1", teil="I"), _v(id="2", teil="I"), _v(id="3", teil="I"), _v(id="4", teil="III"), _v(id="5", teil="III")]
    a = gruppiere(e, [])
    eintraege = [x for adr in a.values() for x in adr["eintraege"]]
    by = {x["id"]: x for x in eintraege}
    by["1"]["_beruf"] = {"stellung": "arbeiter", "stellung_quelle": "hand"}
    by["2"]["_beruf"] = {"stellung": "angestellte", "stellung_quelle": "vorschlag"}
    by["3"]["_beruf"] = {"stellung": "unbestimmt", "stellung_quelle": "hand"}      # handgeprüft, aber unbestimmt
    by["4"]["_gewerbe"] = {"quelle": "hand"}
    by["5"]["_gewerbe"] = {"quelle": "vorschlag"}
    k = baue_kennzahlen(e, a, "2026-09-27")
    assert (k["teil_i_n"], k["beruf_geprueft_n"]) == (3, 3)
    assert (k["stellung_hand_n"], k["stellung_vorschlag_n"], k["stellung_unbestimmt_n"]) == (1, 1, 1)
    assert k["stellung_bestimmt_n"] == 2
    assert (k["betriebe_n"], k["gewerbe_hand_n"], k["gewerbe_claude_n"], k["gewerbe_regel_n"]) == (2, 1, 0, 1)
    # Summen: die drei Stellung-Zähler ergeben alle Teil-I-Einträge, die Gewerbe-Zähler alle Betriebe
    assert k["stellung_hand_n"] + k["stellung_vorschlag_n"] + k["stellung_unbestimmt_n"] == k["teil_i_n"]
    assert k["gewerbe_hand_n"] + k["gewerbe_claude_n"] + k["gewerbe_regel_n"] == k["betriebe_n"]


def test_export_bricht_bei_unbekannter_trichter_kennzahl_ab(tmp_path):
    import pytest
    k = {"id": "datenbasis", "reihenfolge": 0, "titel": "D", "untertitel": "u", "freigegeben": False, "einleitung": "x", "quellen": [],
         "grenzen": "y", "datenbasis": "", "datenbasis_schritt": "", "ausschluss": "",
         "schritte": [{"id": "weg", "text": "t", "beschreibung": "b", "hervorheben": [],
                       "ansicht": {"daten": "kennzahlen", "form": "trichter", "stufen": [{"name": "Z", "aus": "gibt_es_nicht", "farbe": "#000"}]}}]}
    ordner = tmp_path / "perspektiven"; ordner.mkdir()
    (ordner / "datenbasis.json").write_text(json.dumps(k), encoding="utf-8")
    e = [_v(id="1", teil="I")]
    with pytest.raises(ValueError, match="gibt_es_nicht"):
        schreibe_paket(tmp_path / "site", e, [], [], "2026-09-27", kacheln=False, perspektiven=ordner)


def test_export_bricht_bei_totem_datenbasis_schritt_ab(tmp_path):
    import pytest
    k0 = {"id": "datenbasis", "reihenfolge": 0, "titel": "D", "untertitel": "u", "freigegeben": False, "einleitung": "x", "quellen": [],
          "grenzen": "y", "datenbasis": "", "datenbasis_schritt": "", "ausschluss": "",
          "schritte": [{"id": "weg", "text": "t", "beschreibung": "b", "hervorheben": [],
                        "ansicht": {"daten": "kennzahlen", "form": "trichter", "stufen": [{"name": "Z", "aus": "eintraege", "farbe": "#000"}]}}]}
    k1 = {"id": "w", "reihenfolge": 1, "titel": "W", "untertitel": "u", "freigegeben": False, "einleitung": "x", "quellen": [], "grenzen": "y",
          "datenbasis": "d", "datenbasis_schritt": "besitzt", "ausschluss": "a",
          "schritte": [{"id": "s", "text": "t", "beschreibung": "b", "hervorheben": [],
                        "ansicht": {"daten": "besitz", "ebene": "stadtteil", "form": "balken", "gruppen": [{"name": "P", "aus": ["privatperson"], "farbe": "#000"}],
                                    "kaufleute": "unbestimmt", "unsicher": False, "mass": "anteil", "bezug": "P", "min_n": 0, "filter": {}, "karte": None}}]}
    ordner = tmp_path / "perspektiven"; ordner.mkdir()
    (ordner / "datenbasis.json").write_text(json.dumps(k0), encoding="utf-8")
    (ordner / "w.json").write_text(json.dumps(k1), encoding="utf-8")
    with pytest.raises(ValueError, match="besitzt"):
        schreibe_paket(tmp_path / "site", [_v(id="1", teil="I")], [], [], "2026-09-27", kacheln=False, perspektiven=ordner)


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
    b = tippecanoe_befehl(pathlib.Path("."), pathlib.Path("a.pmtiles"))
    assert b[0] == "tippecanoe" and "-o" in b and "a.pmtiles" in b and "--maximum-zoom=15" in b


def test_strassen_und_hex_features_und_kachelbefehl(tmp_path):
    from pipeline.lib.karte_export import hex_features, strassen_features, tippecanoe_befehl
    strassen = [dict(id="00464", name="Grenzstraße", stadtteil="Katernberg", adressen=2, n_I=5),
                dict(id="1936:Alt|Kray", name="Alt (1936)", stadtteil="Kray", adressen=1, n_I=1),
                dict(id="00001", name="Ohne Linie", stadtteil="Kray", adressen=1, n_I=1)]
    linien = {"Grenzstraße": [[[7.06, 51.49], [7.061, 51.491]]]}
    f = strassen_features(strassen, linien)
    assert len(f) == 1 and f[0]["geometry"] == {"type": "MultiLineString", "coordinates": linien["Grenzstraße"]}
    assert f[0]["properties"] == {"id": "00464", "name": "Grenzstraße", "stadtteil": "Katernberg"} and f[0]["id"] == 464
    h = hex_features([dict(id="0_0", lat=51.45, lon=7.01, adressen=3, n_I=4)])
    assert h[0]["geometry"]["type"] == "Polygon" and len(h[0]["geometry"]["coordinates"][0]) == 7 and h[0]["properties"] == {"id": "0_0"}
    cmd = tippecanoe_befehl(tmp_path, tmp_path / "a.pmtiles")
    assert "-L" in cmd and any(x.startswith("adressen:") for x in cmd) and any(x.startswith("strassen:") for x in cmd) and any(x.startswith("hex:") for x in cmd)
    assert "--layer=adressen" not in cmd


def test_strassen_features_nur_fuenfstellige_schl_nr():
    # eine nicht-fünfstellige rein numerische id (z. B. Rest eines nicht abgeschlossenen
    # Konkordanz-Schlüssels) darf keine int()-id ergeben; nur echte fünfstellige schl_nr zählen.
    from pipeline.lib.karte_export import strassen_features
    strassen = [dict(id="464", name="Kurz", stadtteil="Kray"),
                dict(id="123456", name="Lang", stadtteil="Kray"),
                dict(id="00464", name="Kurz", stadtteil="Kray")]
    linien = {"Kurz": [[[7.06, 51.49], [7.061, 51.491]]], "Lang": [[[7.06, 51.49], [7.061, 51.491]]]}
    f = strassen_features(strassen, linien)
    assert [x["properties"]["id"] for x in f] == ["00464"]


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


def test_startseite_beispiele_nur_hausgenau_und_bekannt():
    e = [_v(id="1", lastname="Sepeur", firstname="Wilh.", teil="I"),
         _v(id="2", lastname="Jäger", teil="III", Firmenname="M. Jäger, Althandlung"),
         _v(id="3", lastname="", teil="II", strasse_roh="Grenzstr.", hausnr="9", stufe="strasse")]
    e[2]["Eigentümer"] = "Eigentümer"; e[2]["Firmenname"] = "Gewerkschaft Graf Beust"
    adressen = gruppiere(e, [])
    aid1, aid3 = adress_id(e[0]), adress_id(e[2])
    zeilen = [dict(adress_id=aid1, eintrag_id="1"), dict(adress_id=aid1, eintrag_id="2"),
              dict(adress_id=aid3, eintrag_id="3"), dict(adress_id="gibtesnicht", eintrag_id="9"), dict(adress_id=aid1, eintrag_id="99")]
    b = startseite_beispiele(zeilen, adressen)
    assert [x["e"] for x in b] == ["1", "2"]  # straßengenau (3) und Unbekanntes fallen weg
    assert b[0]["titel"] == "Sepeur, Wilh." and b[0]["id"] == aid1 and b[0]["lat"] == 51.49
    assert b[1]["titel"] == "M. Jäger, Althandlung"
    b2 = startseite_beispiele([dict(adress_id=aid3, eintrag_id="3")], gruppiere([dict(e[2], stufe="haus")], []))
    assert b2[0]["titel"] == "Gewerkschaft Graf Beust" and b2[0]["untertitel"].startswith("Eigentümer · Grenzstr. 9")
    assert b[0]["untertitel"] == "Bergm. · Grenzstr. 25, Katernberg"


def test_schreibe_themen(tmp_path):
    from pipeline.lib.karte_export import schreibe_themen
    q = tmp_path / "q"; q.mkdir()
    (q / "b.json").write_text('{"id": "b", "titel": "B", "freigegeben": true}', encoding="utf-8")
    (q / "a.json").write_text('{"id": "a", "titel": "A"}', encoding="utf-8")
    idx = schreibe_themen(q, tmp_path / "out")
    assert idx == [dict(id="a", titel="A", freigegeben=False, kacheln=False), dict(id="b", titel="B", freigegeben=True, kacheln=False)]
    assert json.loads((tmp_path / "out" / "themen" / "index.json").read_text(encoding="utf-8")) == idx
    assert json.loads((tmp_path / "out" / "themen" / "b.json").read_text(encoding="utf-8"))["titel"] == "B"


from pipeline.lib.karte_export import baue_eigentuemerindex


def _kur(**k):
    z = dict(schreibweise="", art="koerperschaft", eigentuemer="", kategorie="", geprueft="", bearbeiter="christos", datum="", hinweis="")
    z.update(k); return z


EIG = [_kur(schreibweise="Fried. Krupp A.G.", eigentuemer="Fried. Krupp AG", kategorie="industrie", geprueft="ja"),
       _kur(schreibweise="Fried. Krupp AG.", eigentuemer="Fried. Krupp AG", kategorie="industrie", geprueft="ja"),
       _kur(schreibweise="Stadt Essen", eigentuemer="Stadt Essen", kategorie="stadt_staat", geprueft="ja"),
       _kur(schreibweise="Bauverein GmbH", eigentuemer="Bauverein GmbH", kategorie="genossenschaft_siedlung", geprueft="")]  # ungeprüft


def test_gruppiere_besitz():
    from pipeline.lib.eigentuemer import lade_kuratierung
    e = [_v(id="1", teil="II", hausnr="1", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="2", teil="II", hausnr="1", **{"Firmenname": "Fried. Krupp AG."}),            # gleiche Adresse, gleicher Eigentümer
         _v(id="3", teil="II", hausnr="2", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="4", teil="II", hausnr="2", **{"Firmenname": "Stadt Essen"}),                 # zwei Kategorien → gemischt
         _v(id="5", teil="II", hausnr="3", **{"Firmenname": "Bauverein GmbH"}),              # ungeprüft
         _v(id="6", teil="II", hausnr="4", lastname="Schmidt", firstname="Wilh."),            # nicht in der Tabelle
         _v(id="7", teil="I", hausnr="4")]
    a = gruppiere(e, [], lade_kuratierung(EIG))
    by = {x["hausnr"]: x for x in a.values()}
    assert by["1"]["besitz"] == "industrie" and by["2"]["besitz"] == "gemischt"
    assert (by["1"]["besitz_pruefung"], by["2"]["besitz_pruefung"]) == ("hand", "hand")
    assert by["3"]["besitz"] == "ungeprueft" and by["3"]["besitz_pruefung"] == ""
    # Person ohne Kuratierungszeile: Regel Person → Privatperson, als solche gekennzeichnet
    assert (by["4"]["besitz"], by["4"]["besitz_quelle"], by["4"]["besitz_pruefung"]) == ("privatperson", "eintrag", "regel")
    k = eintrag_kurz(by["1"]["eintraege"][0], [])
    assert k["eigentuemer_kanon"] == "Fried. Krupp AG" and k["kategorie"] == "industrie" and k["pruefung"] == "hand"
    assert eintrag_kurz(by["3"]["eintraege"][0], [])["eigentuemer_kanon"] == ""
    k4 = eintrag_kurz(next(x for x in by["4"]["eintraege"] if x["teil"] == "II"), [])
    assert (k4["kategorie"], k4["pruefung"], k4["eigentuemer_kanon"]) == ("privatperson", "regel", "")
    assert eintrag_kurz(next(x for x in by["4"]["eintraege"] if x["teil"] == "I"), [])["kategorie"] == ""   # Teil I: nie
    assert punkt_feature(by["2"])["properties"]["besitz"] == "gemischt"
    assert punkt_feature(by["4"])["properties"]["besitz_pruefung"] == "regel" and punkt_feature(by["4"])["properties"]["n_besitz_regel"] == 1
    assert "n_besitz_regel" not in punkt_feature(by["1"])["properties"]
    # ohne Tabelle: nur die Regel greift
    ohne = {x["hausnr"]: x["besitz"] for x in gruppiere(e, []).values()}
    assert ohne == {"1": "ungeprueft", "2": "ungeprueft", "3": "ungeprueft", "4": "privatperson"}


def test_regel_person_privatperson_firmen_ausgenommen_spanne_und_kennzahl():
    from pipeline.lib.eigentuemer import lade_kuratierung
    e = [_v(id="1", teil="II", hausnr="1", lastname="Korn", firstname="Gebr."),                 # Firma trotz Personenfeld → keine Regel
         _v(id="2", teil="II", hausnr="3", lastname="Schee gen. Halfmann", firstname="M."),    # Hofname → Person
         _v(id="3", teil="II", hausnr="10", hausnr_bis="14", lastname="Meier", firstname="K."),  # Spanne einer Regel-Person
         _v(id="4", teil="I", hausnr="12"),
         _v(id="5", teil="II", hausnr="20", lastname="Müller", firstname="F.", **{"Firmenname": ""}),
         _v(id="6", teil="II", hausnr="20", **{"Firmenname": "Stadt Essen"})]                  # Hand + Regel an einer Adresse → gemischt, hand
    a = gruppiere(e, [], lade_kuratierung(EIG))
    by = {x["hausnr"]: x for x in a.values()}
    assert by["1"]["besitz"] == "ungeprueft"
    assert (by["3"]["besitz"], by["3"]["besitz_pruefung"]) == ("privatperson", "regel")
    assert (by["12"]["besitz"], by["12"]["besitz_quelle"], by["12"]["besitz_pruefung"], by["12"]["besitz_eigentuemer"]) == ("privatperson", "spanne", "regel", "")
    assert (by["20"]["besitz"], by["20"]["besitz_pruefung"]) == ("gemischt", "hand")
    kz = baue_kennzahlen(e, a, "2026-09-26")
    assert (kz["besitz_geprueft"], kz["besitz_regel"], kz["eigentuemer_geprueft"]) == (4, 3, 1)   # Regel-Personen zählen nicht als identifizierte Eigentümer


def test_gruppiere_besitz_aus_hausnummernspanne():
    # Das Häuserbuch druckt „2—8 E. Fried. Krupp A.G.“ einmal am Anfang der Straßenseite; die Häuser 4, 6, 8
    # folgen nur mit Bewohnern. Gleiche Parität von Anfang und Ende = eine Straßenseite (Faksimile II-335).
    from pipeline.lib.eigentuemer import lade_kuratierung
    from pipeline.lib.karte_export import baue_layouts
    e = [_v(id="s", teil="II", hausnr="2", hausnr_bis="8", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="1", teil="I", hausnr="4"),                                       # in der Spanne
         _v(id="2", teil="I", hausnr="4", hausnr_zusatz="a"),                    # 4a zählt zu 4
         _v(id="3", teil="I", hausnr="5"),                                       # andere Straßenseite
         _v(id="4", teil="I", hausnr="10"),                                      # außerhalb
         _v(id="5", teil="II", hausnr="6", **{"Firmenname": "Stadt Essen"}),     # eigener Eintrag gewinnt
         _v(id="6", teil="II", hausnr="8", lastname="Schmidt", firstname="W."),  # eigener, ungeprüfter Eintrag: bleibt ungeprüft
         # gemischte Spanne 1–6 (beide Seiten) und 4–8 (gerade) mit anderer Kategorie → Nr. 6 gemischt
         _v(id="m", teil="II", strasse_heute="Bochumer Straße", hausnr="1", hausnr_bis="6", **{"Firmenname": "Stadt Essen"}),
         _v(id="n", teil="II", strasse_heute="Bochumer Straße", hausnr="4", hausnr_bis="8", **{"Firmenname": "Fried. Krupp AG."}),
         _v(id="7", teil="I", strasse_heute="Bochumer Straße", hausnr="2"),
         _v(id="8", teil="I", strasse_heute="Bochumer Straße", hausnr="3"),
         _v(id="9", teil="I", strasse_heute="Bochumer Straße", hausnr="6"),
         # nicht verortete Spannenzeile wirkt trotzdem: Treffer läuft über Straße und Nummer, nicht über Koordinaten
         _v(id="o", teil="II", strasse_heute="Bochumer Straße", hausnr="9", hausnr_bis="11", stufe="offen", lat="", lon="",
            **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="10", teil="I", strasse_heute="Bochumer Straße", hausnr="11"),
         _v(id="p", teil="II", strasse_heute="Bochumer Straße", hausnr="13", hausnr_bis="15", **{"Firmenname": "Bauverein GmbH"}),  # ungeprüft: keine Spanne
         _v(id="11", teil="I", strasse_heute="Bochumer Straße", hausnr="15"),
         # Buchstaben am Ende: „12–12a“ meint Haus und Anbau, „14–16b“ reicht bis 16b (gerade Seite)
         _v(id="q", teil="II", hausnr="12", hausnr_bis="12a", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="12", teil="I", hausnr="12", hausnr_zusatz="a"),
         _v(id="r", teil="II", hausnr="14", hausnr_bis="16b", **{"Firmenname": "Stadt Essen"}),
         _v(id="13", teil="I", hausnr="16", hausnr_zusatz="b"),
         _v(id="14", teil="I", hausnr="15"),
         _v(id="u", teil="II", hausnr="40", hausnr_bis="4", **{"Firmenname": "Stadt Essen"}),   # verdreht (Erfassungsfehler): keine Spanne
         _v(id="15", teil="I", hausnr="30"),
         # gleiche Straße und Nummer, aber anderes Adressobjekt (Buchschreibung „Grenzstraße“ statt „Grenzstr.“):
         # die Teil-II-Zeile gilt für dasselbe Haus
         _v(id="t", teil="II", hausnr="20", strasse_roh="Grenzstraße", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="16", teil="I", hausnr="20")]
    a = gruppiere(e, [], lade_kuratierung(EIG))
    by = {(x["strasse_heute"], x["hausnr"] + x["hausnr_zusatz"]): x for x in a.values() if x["historisch"].startswith(("Grenzstr.", "Bochumer"))}
    L, B = "Lattenkamp", "Bochumer Straße"
    assert (by[L, "12a"]["besitz"], by[L, "12a"]["besitz_quelle"], by[L, "12a"]["besitz_spanne"]) == ("industrie", "spanne", "Grenzstr. 12–12a, Katernberg · Fried. Krupp A.G.")
    assert (by[L, "16b"]["besitz"], by[L, "16b"]["besitz_quelle"]) == ("stadt_staat", "spanne")
    assert by[L, "15"]["besitz"] == "ungeprueft" and by[L, "30"]["besitz"] == "ungeprueft"
    assert (by[L, "20"]["besitz"], by[L, "20"]["besitz_quelle"], by[L, "20"]["besitz_eigentuemer"]) == ("industrie", "nummer", "Fried. Krupp AG")
    assert by[L, "20"]["besitz_spanne"] == "Grenzstraße 20, Katernberg · Fried. Krupp A.G."
    assert (by[L, "4"]["besitz"], by[L, "4"]["besitz_quelle"]) == ("industrie", "spanne")
    assert by[L, "4"]["besitz_spanne"] == "Grenzstr. 2–8, Katernberg · Fried. Krupp A.G." and by[L, "4"]["besitz_eigentuemer"] == "Fried. Krupp AG"
    assert (by[L, "4a"]["besitz"], by[L, "4a"]["besitz_quelle"]) == ("industrie", "spanne")
    assert (by[L, "5"]["besitz"], by[L, "5"]["besitz_quelle"]) == ("ungeprueft", "")
    assert by[L, "10"]["besitz"] == "ungeprueft"
    assert (by[L, "2"]["besitz"], by[L, "2"]["besitz_quelle"]) == ("industrie", "eintrag")
    assert (by[L, "6"]["besitz"], by[L, "6"]["besitz_quelle"]) == ("stadt_staat", "eintrag")
    assert (by[L, "8"]["besitz"], by[L, "8"]["besitz_quelle"], by[L, "8"]["besitz_pruefung"]) == ("privatperson", "eintrag", "regel")   # eigene Zeile (Regel) schlägt die Spanne
    assert (by[B, "2"]["besitz"], by[B, "2"]["besitz_quelle"]) == ("stadt_staat", "spanne")
    assert (by[B, "3"]["besitz"], by[B, "3"]["besitz_quelle"]) == ("stadt_staat", "spanne")
    assert (by[B, "4"]["besitz"], by[B, "4"]["besitz_quelle"]) == ("industrie", "eintrag")
    assert (by[B, "6"]["besitz"], by[B, "6"]["besitz_quelle"], by[B, "6"]["besitz_eigentuemer"]) == ("gemischt", "spanne", "")
    assert (by[B, "11"]["besitz"], by[B, "11"]["besitz_quelle"]) == ("industrie", "spanne")
    assert (by[B, "15"]["besitz"], by[B, "15"]["besitz_quelle"]) == ("ungeprueft", "")
    assert punkt_feature(by[L, "4"])["properties"]["besitz_quelle"] == "spanne"
    assert punkt_feature(by[L, "4"])["properties"]["besitz_spanne"].startswith("Grenzstr. 2–8")
    # Häuser aus Spannen zählen für Index, Kennzahlen und Bubbles wie eigene Einträge
    liste, scherben = baue_eigentuemerindex(a)
    # Krupp: L2, L4, L4a, L12, L12a, L20 (beide Objekte), B4, B11; Stadt: L6, L14, L16b, L40, B1, B2, B3
    assert [x[1:3] for x in liste] == [["Fried. Krupp AG", 9], ["Stadt Essen", 7]]
    krupp_ids = [x["id"] for x in a.values() if x["besitz"] == "industrie" and x["strasse_heute"] == L]
    assert scherben["fr"]["Fried. Krupp AG"] == sorted([[i, 1] for i in krupp_ids] + [[by[B, n]["id"], 1] for n in ("4", "11")])
    kz = baue_kennzahlen(e, a, "2026-09-26")
    # geprüft: 16 eindeutige + B6 gemischt + L8 (Regel-Person); Spanne: L4, L4a, L12a, L16b, B2, B3, B6, B11; Nummer: L20 (Grenzstr.)
    assert (kz["besitz_geprueft"], kz["besitz_spanne"], kz["besitz_nummer"], kz["besitz_regel"]) == (18, 8, 1, 1)
    krupp = next(k for k in baue_layouts(a)["eigentuemer"]["kreise"] if k["id"] == "Fried. Krupp AG")
    assert krupp["n"] == 9


def test_eigentuemerindex_und_kennzahlen():
    from pipeline.lib.eigentuemer import lade_kuratierung
    e = [_v(id="1", teil="II", hausnr="1", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="2", teil="II", hausnr="2", **{"Firmenname": "Fried. Krupp AG."}),
         _v(id="3", teil="II", hausnr="2", **{"Firmenname": "Fried. Krupp AG."}),
         _v(id="4", teil="II", hausnr="3", **{"Firmenname": "Stadt Essen"}),
         _v(id="5", teil="II", hausnr="4", **{"Firmenname": "Bauverein GmbH"})]
    a = gruppiere(e, [], lade_kuratierung(EIG))
    liste, scherben = baue_eigentuemerindex(a)
    assert liste == [["fried krupp ag", "Fried. Krupp AG", 2, "industrie"], ["stadt essen", "Stadt Essen", 1, "stadt_staat"]]
    ids = {x["hausnr"]: x["id"] for x in a.values()}
    assert scherben["fr"]["Fried. Krupp AG"] == sorted([[ids["1"], 1], [ids["2"], 2]])
    assert "Bauverein GmbH" not in str(scherben)
    kz = baue_kennzahlen(e, a, "2026-09-22")
    assert kz["besitz_geprueft"] == 3 and kz["eigentuemer_geprueft"] == 2


def test_eigentuemerindex_uneinheitliche_kategorie_wird_gemischt():
    # F5: zwei Schreibweisen desselben kanonischen Namens mit unterschiedlicher Kategorie (Kuratierungsstand
    # uneinheitlich, z. B. mitten in einer Zusammenführung) — der Index darf nicht einfach die zuletzt
    # gesehene Kategorie übernehmen ("last wins"), sondern muss das als "gemischt" kennzeichnen.
    from pipeline.lib.eigentuemer import lade_kuratierung
    eig = [_kur(schreibweise="Fried. Krupp A.G.", eigentuemer="Fried. Krupp AG", kategorie="industrie", geprueft="ja"),
           _kur(schreibweise="Fried. Krupp AG.", eigentuemer="Fried. Krupp AG", kategorie="bergbau", geprueft="ja")]
    e = [_v(id="1", teil="II", hausnr="1", **{"Firmenname": "Fried. Krupp A.G."}),
         _v(id="2", teil="II", hausnr="2", **{"Firmenname": "Fried. Krupp AG."})]
    a = gruppiere(e, [], lade_kuratierung(eig))
    liste, _ = baue_eigentuemerindex(a)
    assert liste == [["fried krupp ag", "Fried. Krupp AG", 2, "gemischt"]]


def test_schreibe_paket_mit_eigentuemer(tmp_path):
    e = [_v(id="1", teil="II", hausnr="1", **{"Firmenname": "Stadt Essen"})]
    schreibe_paket(tmp_path, e, [], [], "2026-09-22", kacheln=False, eigentuemer=EIG)
    assert json.loads((tmp_path / "suche" / "eigentuemer.json").read_text(encoding="utf-8")) == [["stadt essen", "Stadt Essen", 1, "stadt_staat"]]
    assert (tmp_path / "suche" / "eigentuemer" / "st.json").exists()


def test_schreibe_paket_mit_perspektiven(tmp_path):
    from tests.test_perspektiven import GUT
    q = tmp_path / "q"; q.mkdir()
    (q / "wohneigentum.json").write_text(json.dumps(GUT), encoding="utf-8")
    aus = tmp_path / "out"
    schreibe_paket(aus, [_v(id="1", teil="I")], [], [], "2026-09-22", kacheln=False, perspektiven=q)
    index = json.loads((aus / "perspektiven" / "index.json").read_text(encoding="utf-8"))
    assert index == [{"id": "wohneigentum", "titel": "Wohneigentum 1936", "untertitel": GUT["untertitel"], "freigegeben": False, "reihenfolge": 1}]
    assert json.loads((aus / "perspektiven" / "wohneigentum.json").read_text(encoding="utf-8"))["id"] == "wohneigentum"


def test_schreibe_paket_mit_ungueltigem_perspektiven_kapitel_wirft(tmp_path):
    from tests.test_perspektiven import GUT
    q = tmp_path / "q"; q.mkdir()
    ungueltig = dict(GUT); del ungueltig["titel"]
    (q / "wohneigentum.json").write_text(json.dumps(ungueltig), encoding="utf-8")
    with pytest.raises(ValueError):
        schreibe_paket(tmp_path / "out", [_v(id="1", teil="I")], [], [], "2026-09-22", kacheln=False, perspektiven=q)


def test_gruppiere_stadtteil_schreibweise_und_identitaet():
    from pipeline.lib.eigentuemer import lade_kuratierung
    kur = lade_kuratierung([
        _kur(schreibweise="Kath. Kirchengem. ‹Katernberg›", eigentuemer="Kath. Kirchengemeinde St. Joseph Katernberg", kategorie="kirche_stiftung", geprueft="ja"),
        _kur(schreibweise="Kath. Kirchengem.", eigentuemer="Kath. Kirchengem.", kategorie="kirche_stiftung", geprueft="ja"),
        dict(_kur(schreibweise="Müller, J.", eigentuemer="Müller, J.", kategorie="privatperson", geprueft="ja"), art="person", identitaet=""),
        dict(_kur(schreibweise="Reismann-Grone, Dr. phil., Th.", eigentuemer="Reismann-Grone, Dr. phil., Th.", kategorie="privatperson", geprueft="ja"), art="person", identitaet="sicher")])
    e = [_v(id="1", teil="II", hausnr="1", stadtteil="Katernberg", **{"Firmenname": "Kath. Kirchengem."}),
         _v(id="2", teil="II", hausnr="2", stadtteil="Horst", **{"Firmenname": "Kath. Kirchengem."}),
         _v(id="3", teil="II", hausnr="3", lastname="Müller", firstname="J."),
         _v(id="4", teil="II", hausnr="4", lastname="Reismann-Grone", firstname="Dr. phil., Th.")]
    a = gruppiere(e, [], kur)
    by = {x["hausnr"]: x for x in a.values()}
    assert eintrag_kurz(by["1"]["eintraege"][0], [])["eigentuemer_kanon"] == "Kath. Kirchengemeinde St. Joseph Katernberg"
    assert eintrag_kurz(by["2"]["eintraege"][0], [])["eigentuemer_kanon"] == "Kath. Kirchengem."   # Rückfall auf einfache Schreibweise
    assert by["3"]["besitz"] == "privatperson" and by["4"]["besitz"] == "privatperson"
    liste, _ = baue_eigentuemerindex(a)
    assert [x[1] for x in liste] == ["Kath. Kirchengem.", "Kath. Kirchengemeinde St. Joseph Katernberg", "Reismann-Grone, Dr. phil., Th."]  # Müller, J. fehlt: Identität nicht belegt


def test_niveau_je_adresse_und_berufsnormindex(tmp_path):
    from pipeline.lib.berufe import lade_ohdab, lade_kuratierung as lade_berufe
    from pipeline.lib.karte_export import baue_berufsindex, baue_berufsnormindex, baue_kennzahlen, eintrag_kurz, gruppiere, punkt_feature
    from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); o = lade_ohdab(p)
    b = lade_berufe([dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja"),
                     dict(schreibweise="Lehrer", beruf="Lehrer", status="", ohdab_id="B 84124-120", niveau_unsicher="", geprueft="ja"),
                     dict(schreibweise="Arbeiter", beruf="Arbeiter", status="", ohdab_id="B 20002-500", niveau_unsicher="ja", geprueft="ja")])
    basis = dict(stufe="haus", lat="51.4", lon="7.0", strasse_norm="x", strasse_roh="X", hausnr="1", Vorort="", stadtteil="Kray", lastname="N", firstname="", page="I-1")
    def e(i, teil, beruf, hausnr="1"):
        return dict(basis, id=str(i), teil=teil, hausnr=hausnr, **{"Beruf o. ä.": beruf})
    eintraege = [e(1, "I", "Bergm."), e(2, "I", "Bergm."), e(3, "I", "Lehrer"), e(4, "II", "Lehrer"), e(5, "I", "Kfm."),   # Haus 1: 2× fachlich, 1× hochkomplex, 1 ungeprüft → Mehrheit? 2 von 3 geprüften → fachlich
                 e(6, "I", "Bergm.", "2"), e(7, "I", "Lehrer", "2"),                                                        # Haus 2: 1:1 → gemischt
                 e(8, "I", "Arbeiter", "3"),                                                                                 # Haus 3: nur unsicher
                 e(9, "I", "Kfm.", "4")]                                                                                     # Haus 4: ungeprüft
    a = gruppiere(eintraege, [], None, berufe=b, ohdab=o)
    nach_nr = {x["hausnr"]: x for x in a.values()}
    assert nach_nr["1"]["niveau"] == "fachlich" and nach_nr["2"]["niveau"] == "gemischt" and nach_nr["3"]["niveau"] == "unsicher" and nach_nr["4"]["niveau"] == "ungeprueft"
    p1 = punkt_feature(nach_nr["1"])["properties"]
    assert p1["niveau"] == "fachlich" and p1["n_fachlich"] == 2 and p1["n_hochkomplex"] == 1 and "n_helfer" not in p1
    k = eintrag_kurz(nach_nr["1"]["eintraege"][0], [])
    assert (k["beruf"], k["beruf_norm"], k["ohdab"], k["niveau"], k["status"]) == ("Bergm.", "Bergmann", "B 21112-100", "fachlich", "")
    liste, scherben = baue_berufsnormindex(a)
    assert liste[0][1:] == ["Bergmann", "B 21112-100", 3, 1, "fachlich"] and liste[0][0] == "bergmann"
    assert scherben["be"]["B 21112-100"] == sorted([[nach_nr["1"]["id"], 2], [nach_nr["2"]["id"], 1]])
    roh, _ = baue_berufsindex(a)
    assert [x[1] for x in roh] == ["Kfm."]                      # geprüfte Schreibweisen nur noch über die Normbezeichnung
    kz = baue_kennzahlen(eintraege, a, "2026-09-23")
    assert kz["berufe_geprueft"] == 75.0 and kz["berufe_schreibweisen_geprueft"] == 3   # 6 von 8 Teil-I-Einträgen


def test_berufsnormindex_nutzt_ohdab_norm_nicht_kuratierten_beruf(tmp_path):
    """Zwei Schreibweisen mit unterschiedlichem kuratierten `beruf`, aber demselben ohdab_id, ergeben EINEN
    Indexeintrag mit der OhdAB-Normbezeichnung als Label — unabhängig davon, welche Zeile zuletzt verarbeitet
    wird (Finding 1: baue_berufsnormindex bildete Label/Schlüssel/Scherbe bisher aus dem kuratierten `beruf`)."""
    from pipeline.lib.berufe import lade_ohdab, lade_kuratierung as lade_berufe
    from pipeline.lib.karte_export import baue_berufsnormindex
    from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); o = lade_ohdab(p)
    b = lade_berufe([dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja"),
                     dict(schreibweise="Bergarb.", beruf="Bergarbeiter", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja")])
    basis = dict(stufe="haus", lat="51.4", lon="7.0", strasse_norm="x", strasse_roh="X", hausnr="1", Vorort="", stadtteil="Kray", lastname="N", firstname="", page="I-1")
    def e(i, beruf, hausnr="1"):
        return dict(basis, id=str(i), teil="I", hausnr=hausnr, **{"Beruf o. ä.": beruf})
    for reihenfolge in ([e(1, "Bergarb."), e(2, "Bergm.")], [e(1, "Bergm."), e(2, "Bergarb.")]):
        a = gruppiere(reihenfolge, [], None, berufe=b, ohdab=o)
        liste, scherben = baue_berufsnormindex(a)
        assert len(liste) == 1
        assert liste[0][1:3] == ["Bergmann", "B 21112-100"]   # Label = OhdAB-Norm, nicht der kuratierte beruf
        assert list(scherben["be"]) == ["B 21112-100"]


def test_gruppen_gewerbe_zaehlfelder_ebenen_layouts(tmp_path):
    from pipeline.lib.berufe import lade_ohdab, lade_kuratierung as lade_berufe
    from pipeline.lib.gewerbe import lade_gewerbe
    from pipeline.lib.karte_export import baue_kennzahlen, baue_layouts, eintrag_kurz, gruppiere, punkt_feature, schreibe_paket
    from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); o = lade_ohdab(p)
    b = lade_berufe([dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja", stellung="arbeiter", stellung_geprueft="ja"),
                     dict(schreibweise="Lehrer", beruf="Lehrer", status="", ohdab_id="B 84124-120", niveau_unsicher="", geprueft="ja", stellung="beamte", stellung_geprueft="")])
    hg = [dict(hauptgruppe="B21", bezeichnung="Rohstoffgewinnung …", kurz="Bergbau, Glas, Keramik", bereich="Produktion", quelle="KldB 2010"),
          dict(hauptgruppe="B84", bezeichnung="Lehrende und ausbildende Berufe", kurz="Lehrer", bereich="Gesundheit, Soziales, Lehre", quelle="KldB 2010"),
          dict(hauptgruppe="B20", bezeichnung="Allgemeine Berufe in der Produktion", kurz="ohne Branche", bereich="Produktion", quelle="OhdAB"),
          dict(hauptgruppe="A10", bezeichnung="Berufslose", kurz="Berufslose", bereich="ohne Erwerbsberuf", quelle="OhdAB")]
    gw = lade_gewerbe([dict(rubrik="Bäcker", betriebe="2", gruppe="lebensmittel", art="handwerk", geprueft="ja"),
                       dict(rubrik="Kohlen", betriebe="1", gruppe="handel", art="handel", geprueft="")])
    basis = dict(stufe="haus", lat="51.45", lon="7.01", strasse_norm="x", strasse_roh="X", hausnr="1", Vorort="", stadtteil="Kray", lastname="N", firstname="", page="I-1",
                 strasse_heute="X-Straße", schl_nr="00001")
    def e(i, teil, beruf="", firma="", hausnr="1"):
        return dict(basis, id=str(i), teil=teil, hausnr=hausnr, Firmenname=firma, **{"Beruf o. ä.": beruf})
    eintraege = [e(1, "I", "Bergm."), e(2, "I", "Lehrer"), e(3, "I", "Kfm."), e(4, "II", "Lehrer"),
                 e(5, "III", firma="A. Meier, Bäcker"), e(6, "III", firma="A. Meier, Kohlen"), e(7, "III", firma="B. Kraus, Bäcker"),
                 e(8, "I", "Bergm.", hausnr="2")]
    a = gruppiere(eintraege, [], None, berufe=b, ohdab=o, gewerbe=gw)
    haus1 = next(x for x in a.values() if x["hausnr"] == "1")
    k = {x["id"]: eintrag_kurz(x, []) for x in haus1["eintraege"]}
    assert (k["1"]["stellung"], k["1"]["gruppe"], k["1"]["gattung"]) == ("arbeiter", "B21", "Berufe im Berg- und Tagebau – fachlich ausgerichtete Tätigkeiten")
    assert (k["1"]["stellung_quelle"], k["2"]["stellung_quelle"], k["3"]["stellung_quelle"]) == ("hand", "vorschlag", "")
    assert (k["2"]["stellung"], k["2"]["gruppe"]) == ("beamte", "B84")                    # Stellung als Vorschlag exportiert, Gruppe = Hauptgruppe
    assert (k["5"]["rubrik"], k["5"]["gewerbe_gruppe"], k["5"]["gewerbe_art"], k["5"]["firma"]) == ("Bäcker", "lebensmittel", "handwerk", "A. Meier, Bäcker")
    assert (k["6"]["gewerbe_gruppe"], k["6"]["gewerbe_art"], k["6"]["gewerbe_quelle"]) == ("handel", "handel", "vorschlag")   # Vorschlag exportiert, Quelle gekennzeichnet
    assert k["5"]["gewerbe_quelle"] == "hand"
    assert k["3"]["stellung"] == "" and k["3"]["gruppe"] == ""                          # ohne geprüften Beruf: leer im Eintrag …
    p1 = punkt_feature(haus1)["properties"]
    assert p1["n_st_arbeiter"] == 1 and p1["n_st_beamte"] == 1 and p1["n_st_unbestimmt"] == 1 and p1["n_stellung_hand"] == 1 and p1["n_gr_B21"] == 1 and p1["n_gr_B84"] == 1 and p1["n_gr_ungeprueft"] == 1   # … aber gezählt als unbestimmt
    # Teil-II-Zeile „N“ ohne Firmenname: Regel Person → Privatperson, als Regel gezählt
    assert p1["n_gw_lebensmittel"] == 2 and p1["n_gwa_handwerk"] == 2 and p1["n_gw_handel"] == 1 and p1["n_bs_privatperson"] == 1 and p1["n_besitz_regel"] == 1
    lay = baue_layouts(a)
    assert [x["id"] for x in lay["berufe"]["kreise"]] == ["B 21112-100", "B 84124-120"]
    bm = lay["berufe"]["kreise"][0]
    assert bm["norm"] == "Bergmann" and bm["n"] == 2 and bm["niveau"] == "fachlich" and bm["stellung"] == "arbeiter" and bm["gruppe"] == "B21"
    assert {"x", "y", "r"} <= set(bm) and {"x", "y"} <= set(bm["niveau_xy"]) and [g["gruppe"] for g in lay["berufe"]["gruppen"]] == ["B21", "B84"]
    assert lay["gewerbe"]["kreise"][0] == dict(lay["gewerbe"]["kreise"][0], id="Bäcker", n=2, gruppe="lebensmittel", art="handwerk")
    assert lay["eigentuemer"]["kreise"] == []
    kz = baue_kennzahlen(eintraege, a, "2026-09-26")
    assert kz["stellung_geprueft"] == 50.0 and kz["stellung_vorschlag"] == 25.0 and kz["stellung_unbestimmt"] == 25.0 and "gruppen_geprueft" not in kz and kz["gewerbe_geprueft"] == 66.7 and kz["gewerbe_vorschlag"] == 33.3
    aus = tmp_path / "daten"
    schreibe_paket(aus, eintraege, [], [], "2026-09-26", kacheln=False, berufe=list(b.values()), ohdab=o, hauptgruppen=hg, gewerbe=list(gw.values()))
    assert json.loads((aus / "hauptgruppen.json").read_text(encoding="utf-8"))["B21"]["kurz"] == "Bergbau, Glas, Keramik"
    with pytest.raises(ValueError, match="hauptgruppen.csv"):
        schreibe_paket(tmp_path / "d2", eintraege, [], [], "2026-09-26", kacheln=False, berufe=list(b.values()), ohdab=o, hauptgruppen=hg[:1], gewerbe=[])
    st = json.loads((aus / "ebenen" / "strassen.json").read_text(encoding="utf-8"))
    assert st[0]["id"] == "00001" and st[0]["n_st_arbeiter"] == 2 and st[0]["adressen"] == 2
    assert (aus / "ebenen" / "stadtteile.json").exists() and (aus / "ebenen" / "hex.json").exists()
    assert json.loads((aus / "layout" / "berufe.json").read_text(encoding="utf-8"))["kreise"][0]["id"] == "B 21112-100"


def test_gruppiere_ordnet_teil_iii_keinen_beruf_zu(tmp_path):
    """Berufszuordnung gilt nur für Teil I (Einwohner) und Teil II (Eigentümer) — Teil III (Gewerbe) hat kein
    eigenes Feld `Beruf o. ä.` im fachlichen Sinn; eine geprüfte Schreibweise darf dort nicht `_beruf` setzen
    (Finding 5). Der Eintrag bleibt daher im Rohtext-Berufsindex."""
    from pipeline.lib.berufe import lade_ohdab, lade_kuratierung as lade_berufe
    from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); o = lade_ohdab(p)
    b = lade_berufe([dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja")])
    e = _v(id="1", teil="III", **{"Beruf o. ä.": "Bergm."})
    a = gruppiere([e], [], None, berufe=b, ohdab=o)
    eintrag = next(iter(a.values()))["eintraege"][0]
    assert eintrag["_beruf"] is None
    assert eintrag_kurz(eintrag, [])["beruf_norm"] == ""
    roh, _ = baue_berufsindex(a)
    assert [x[1] for x in roh] == ["Bergm."]


def test_stadtteil_je_adresse_aus_polygon(tmp_path):
    from pipeline.lib.stadtteile import Stadtteile
    from pipeline.lib.karte_export import baue_kennzahlen, gruppiere, schreibe_paket
    from pipeline.lib.ebenen import aggregiere
    st = Stadtteile({"stand": "d", "quelle": "OSM", "stadtteile": {"Kray": [[[7.0, 51.4], [7.1, 51.4], [7.1, 51.5], [7.0, 51.5], [7.0, 51.4]]]}}, {})
    basis = dict(stufe="haus", strasse_norm="x", strasse_roh="X", Vorort="", lastname="N", firstname="", page="I-1", strasse_heute="X-Straße", schl_nr="00001", teil="I")
    e1 = dict(basis, id="1", lat="51.45", lon="7.05", hausnr="1", stadtteil="Kray; Steele")      # im Polygon → Kray
    e2 = dict(basis, id="2", lat="51.60", lon="7.05", hausnr="2", stadtteil="Kray; Steele")      # außerhalb → Straßen-Stadtteil bleibt
    a = gruppiere([e1, e2], [], None, stadtteile=st)
    by = {x["hausnr"]: x for x in a.values()}
    assert (by["1"]["stadtteil"], by["1"]["stadtteil_quelle"]) == ("Kray", "polygon")
    assert (by["2"]["stadtteil"], by["2"]["stadtteil_quelle"]) == ("Kray; Steele", "strasse")
    assert baue_kennzahlen([e1, e2], a, "2026-09-26")["stadtteil_polygon"] == 50.0
    ids = [u["id"] for u in aggregiere(a, "stadtteil")]
    assert ids == ["Kray", "Kray; Steele"]
    aus = tmp_path / "daten"
    schreibe_paket(aus, [e1, e2], [], [], "2026-09-26", kacheln=False, stadtteile=st, hauptgruppen=[])
    g = json.loads((aus / "stadtteile.geojson").read_text(encoding="utf-8"))
    assert g["features"][0]["properties"]["id"] == "Kray"
    ohne = gruppiere([e1], [], None)
    assert list(ohne.values())[0]["stadtteil_quelle"] == "strasse"


# ---- Herkunftspaket (Spec 2026-09-27 Herkunftspfad §3) ----------------------------------------------------

def _adr(aid, eintraege, **k):
    a = dict(id=aid, lat=51.4, lon=7.0, stufe="haus", stadtteil="Kray", eintraege=eintraege,
             besitz="ungeprueft", besitz_pruefung="", besitz_quelle="", besitz_eigentuemer="")
    a.update(k)
    return a


def _bf(schreibweise, norm, ohdab, stellung, quelle="hand", niveau="fachlich", gruppe="B21"):
    return dict(teil="I", **{"Beruf o. ä.": schreibweise},
                _beruf=dict(beruf=norm, ohdab=ohdab, niveau=niveau, gattung="", gattung_id="", status="", norm=norm,
                            stellung=stellung, stellung_quelle=quelle, gruppe=gruppe))


def test_baue_herkunft_stellung_und_berufe():
    from pipeline.lib.karte_export import baue_herkunft
    a = {"1": _adr("1", [_bf("Bergm.", "Bergmann", "B 21112-100", "arbeiter"), _bf("Bergm.", "Bergmann", "B 21112-100", "arbeiter"),
                        _bf("Bergmann", "Bergmann", "B 21112-100", "arbeiter"), _bf("Schlosser", "Schlosser", "B 24412-127", "arbeiter", "vorschlag"),
                        _bf("Lehrer", "Lehrer", "B 84124-120", "beamte", niveau="hochkomplex", gruppe="B84"),
                        dict(teil="I", **{"Beruf o. ä.": "Kfm."}, _beruf=None),
                        # Stellung je Norm = Mehrheit der Nennungen (wie baue_layouts), nicht die erste Zeile
                        _bf("Kfm. Angest.", "Kaufmännischer Angestellter", "B 71304-101", "kaufleute", gruppe="B71"),
                        _bf("kfm. Angestellter", "Kaufmännischer Angestellter", "B 71304-101", "angestellte", "vorschlag", gruppe="B71"),
                        _bf("kfm. Angestellter", "Kaufmännischer Angestellter", "B 71304-101", "angestellte", "vorschlag", gruppe="B71")])}
    h = baue_herkunft(a)
    st = h["stellung"]["arbeiter"]
    assert (st["schreibweisen"], st["normen"], st["nennungen"]) == (3, 2, 4)
    assert st["quelle"] == {"hand": 3, "vorschlag": 1}
    assert st["top"] == [["Bergm.", 2, "Bergmann", "hand"], ["Bergmann", 1, "Bergmann", "hand"], ["Schlosser", 1, "Schlosser", "vorschlag"]]
    assert h["stellung"]["beamte"]["top"] == [["Lehrer", 1, "Lehrer", "hand"]]
    # ungeprüfter Beruf zählt zu „unbestimmt“, ohne Norm
    assert h["stellung"]["unbestimmt"]["nennungen"] == 1 and h["stellung"]["unbestimmt"]["top"] == [["Kfm.", 1, "", ""]]
    assert h["gruppe"]["B21"]["nennungen"] == 4 and h["gruppe"]["B21"]["quelle"] == {"hand": 4}
    assert h["niveau"]["hochkomplex"]["nennungen"] == 1
    b = h["berufe"]["B 21112-100"]
    assert b == {"norm": "Bergmann", "nennungen": 3, "schreibweisen_gesamt": 2, "schreibweisen": [["Bergm.", 2, "hand"], ["Bergmann", 1, "hand"]],
                 "stellung": "arbeiter", "quelle": {"hand": 3, "vorschlag": 0}}
    ka = h["berufe"]["B 71304-101"]
    assert ka["stellung"] == "angestellte" and ka["quelle"] == {"hand": 1, "vorschlag": 2}
    assert ka["schreibweisen"] == [["kfm. Angestellter", 2, "vorschlag"], ["Kfm. Angest.", 1, "hand"]]


def test_baue_herkunft_besitz_und_eigentuemer():
    from pipeline.lib.karte_export import baue_herkunft
    krupp = lambda s: dict(teil="II", **{"Firmenname": s}, lastname="", firstname="", page="II-040", _eigentuemer="Fried. Krupp AG",
                           _kategorie="industrie", _identitaet=True, _pruefung="hand")
    person = dict(teil="II", **{"Firmenname": ""}, lastname="Müller", firstname="H.", page="II-041", _eigentuemer="", _kategorie="privatperson",
                  _identitaet=False, _pruefung="regel")
    # Wie gruppiere: Adressen mit eigener Teil-II-Zeile tragen kein besitz_eigentuemer (das setzt nur die
    # Übernahme aus Spanne oder gleicher Nummer); der Eigentümer steht in der Zeile (_eigentuemer, _identitaet).
    a = {"1": _adr("1", [krupp("Fried. Krupp A.G.")], besitz="industrie", besitz_pruefung="hand", besitz_quelle="eintrag"),
         "2": _adr("2", [krupp("Fried. Krupp A.-G.")], besitz="industrie", besitz_pruefung="hand", besitz_quelle="eintrag"),
         "3": _adr("3", [], besitz="industrie", besitz_pruefung="hand", besitz_quelle="spanne", besitz_eigentuemer="Fried. Krupp AG"),
         "4": _adr("4", [person], besitz="privatperson", besitz_pruefung="regel", besitz_quelle="eintrag"),
         "5": _adr("5", [], besitz="ungeprueft")}
    h = baue_herkunft(a)
    ind = h["besitz"]["industrie"]
    assert (ind["eigentuemer"], ind["zeilen"], ind["haeuser"], ind["spanne"], ind["nummer"]) == (1, 2, 3, 1, 0)
    assert ind["quelle"] == {"hand": 3, "regel": 0} and ind["top"] == [["Fried. Krupp AG", 3]]
    pr = h["besitz"]["privatperson"]
    assert pr["quelle"] == {"hand": 0, "regel": 1} and pr["regel_beispiele"] == [["Müller, H.", 1]]
    k = h["eigentuemer"]["Fried. Krupp AG"]
    assert k == {"schreibweisen": [["Fried. Krupp A.-G.", 1], ["Fried. Krupp A.G.", 1]], "schreibweisen_gesamt": 2, "zeilen": 2, "haeuser": 3,
                 "spanne": 1, "nummer": 0, "kategorie": "industrie", "identitaet": True, "seite": "II-040"}
    # Review Focus 5: ohne gesicherte Identität kein Eintrag je Eigentümer
    assert "Müller, H." not in h["eigentuemer"] and "" not in h["eigentuemer"]


def test_baue_herkunft_gewerbe_und_rubriken():
    from pipeline.lib.karte_export import baue_herkunft
    gw = lambda rubrik, gruppe, art, quelle, schl: dict(teil="III", **{"Firmenname": "X, " + rubrik}, _gewerbe=dict(rubrik=rubrik, firma="X", gruppe=gruppe, art=art, quelle=quelle, schluessel=schl))
    # Je Rubrik zählt ein Betrieb (schluessel) einmal, wie in baue_layouts und den Ebenen — b1 steht zweimal unter „Bäcker“
    a = {"1": _adr("1", [gw("Bäcker", "lebensmittel", "handwerk", "hand", "b1"), gw("Bäcker", "lebensmittel", "handwerk", "hand", "b2"),
                        gw("Bäcker", "lebensmittel", "handwerk", "hand", "b1"),
                        gw("Kolonialwaren", "lebensmittel", "handel", "claude", "k1"), gw("Maler", "bau", "handwerk", "vorschlag", "m1")])}
    h = baue_herkunft(a)
    lm = h["gewerbe"]["lebensmittel"]
    assert (lm["rubriken"], lm["betriebe"]) == (2, 3) and lm["quelle"] == {"hand": 2, "claude": 1, "vorschlag": 0}
    assert lm["top"] == [["Bäcker", 2, "handwerk", "hand"], ["Kolonialwaren", 1, "handel", "claude"]]
    assert h["rubriken"]["Maler"] == {"betriebe": 1, "gruppe": "bau", "art": "handwerk", "quelle": "vorschlag"}


def test_schreibe_paket_schreibt_herkunft(tmp_path):
    schreibe_paket(tmp_path, [_v(id="1", teil="I")], [], [], "2026-09-27", kacheln=False)
    for name in ("stellung", "gruppe", "niveau", "berufe", "besitz", "eigentuemer", "gewerbe", "rubriken"):
        assert (tmp_path / "herkunft" / f"{name}.json").exists(), name
    assert json.loads((tmp_path / "herkunft" / "stellung.json").read_text(encoding="utf-8"))["unbestimmt"]["nennungen"] == 1


def test_gruppiere_bergbau_gruppe_und_rangfeld(tmp_path):
    from pipeline.lib.berufe import lade_ohdab, lade_kuratierung as lade_berufe
    from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); o = lade_ohdab(p)
    # Beide Schreibweisen auf ein Item aus der Test-OhdAB (B 21112-100); die Bergbau-Gruppe hängt an der Norm, nicht am Item.
    b = lade_berufe([dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja"),
                     dict(schreibweise="Steiger", beruf="Steiger", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja"),
                     dict(schreibweise="Lehrer", beruf="Lehrer", status="", ohdab_id="B 84124-120", niveau_unsicher="", geprueft="ja")])
    basis = dict(stufe="haus", lat="51.4", lon="7.0", strasse_norm="x", strasse_roh="X", hausnr="1", Vorort="", stadtteil="Kray", lastname="N", firstname="", page="I-1")
    def e(i, beruf, hausnr="1"):
        return dict(basis, id=str(i), teil="I", hausnr=hausnr, **{"Beruf o. ä.": beruf})
    eintraege = [e(1, "Bergm."), e(2, "Steiger"), e(3, "Bergm.", "2"), e(4, "Lehrer", "3"), e(5, "Kfm.", "4")]
    a = gruppiere(eintraege, [], None, berufe=b, ohdab=o, bergbau={"Bergmann": "belegschaft", "Steiger": "aufsicht"})
    nach_nr = {x["hausnr"]: x for x in a.values()}
    assert [x["_beruf"].get("bergbau") for x in nach_nr["1"]["eintraege"]] == ["belegschaft", "aufsicht"]
    p1 = punkt_feature(nach_nr["1"])["properties"]
    assert p1["bergbau"] == "aufsicht" and p1["n_bb_belegschaft"] == 1 and p1["n_bb_aufsicht"] == 1   # Rang: Aufsicht vor Belegschaft
    assert punkt_feature(nach_nr["2"])["properties"]["bergbau"] == "belegschaft"
    assert "bergbau" not in punkt_feature(nach_nr["3"])["properties"] and "bergbau" not in nach_nr["3"]["eintraege"][0]["_beruf"]
    assert "bergbau" not in punkt_feature(nach_nr["4"])["properties"]      # ungeprüfter Beruf: kein Feld, kein n_bb_
    kz = baue_kennzahlen(eintraege, a, "2026-09-28")
    assert (kz["bergbau_n"], kz["bergbau_belegschaft_n"], kz["bergbau_aufsicht_n"], kz["bergbau_leitung_n"], kz["bergbau_haeuser_n"]) == (3, 2, 1, 0, 0)


def test_baue_bergbau_punkte():
    from pipeline.lib.karte_export import baue_bergbau_punkte
    from pipeline.lib.ebenen import hex_id, hex_zelle
    from pipeline.lib.layout import ueberlappen
    def adr(i, lat, lon, gruppen=(), besitz="ungeprueft", eig="", stufe="haus"):
        eintraege = [dict(teil="I", _beruf=dict(bergbau=g)) for g in gruppen]
        if eig:
            eintraege.append(dict(teil="II", _eigentuemer=eig, _kategorie="bergbau"))
        return dict(id=str(i), lat=lat, lon=lon, stufe=stufe, besitz=besitz, eintraege=eintraege)
    adressen = {a["id"]: a for a in [
        adr(1, 51.45, 7.01, ["belegschaft", "belegschaft", "aufsicht"]),
        adr(2, 51.4501, 7.0101, ["belegschaft"], besitz="bergbau", eig="Gewerkschaft Mathias Stinnes"),
        adr(3, 51.40, 7.10, ["leitung"], besitz="bergbau", eig="Gewerkschaft Mathias Stinnes", stufe="strasse"),
        adr(4, 51.41, 7.11, [], besitz="bergbau"),
        adr(5, 51.42, 7.12, [], besitz="privatperson")]}
    p = baue_bergbau_punkte(adressen)
    assert [g["id"] for g in p["gruppen"]] == ["belegschaft", "aufsicht", "leitung", "invaliden"]
    assert p["gruppen"][0] == dict(id="belegschaft", name="Belegschaft", n=3, felder=1)     # Adresse 1 und 2 im selben Hexfeld
    assert p["maxn"] == 3
    b = p["hex"]["belegschaft"]
    assert len(b) == 1 and b[0]["n"] == 3 and b[0]["id"] == hex_id(*hex_zelle(51.45, 7.01)) and b[0]["r"] == 9.0
    assert set(b[0]) == {"id", "lon", "lat", "n", "r", "x", "y"}
    assert p["hex"]["invaliden"] == [] and ueberlappen(p["hex"]["belegschaft"] + []) == []
    assert [h["eig"] for h in p["haeuser"]] == ["gewerkschaft_mathias_stinnes", "gewerkschaft_mathias_stinnes", "unbekannt"]
    assert p["haeuser"][1]["stufe"] == "strasse" and set(p["haeuser"][0]) == {"id", "lon", "lat", "eig", "stufe"}
    assert p["gesellschaften"] == [dict(id="gewerkschaft_mathias_stinnes", name="Gewerkschaft Mathias Stinnes", haeuser=2),
                                   dict(id="unbekannt", name="unbekannter Bergbau-Eigentümer", haeuser=1)]


def test_kennzahl_bergbau_gesellschaften():
    """Spec Bergbau §2.3: Zahl der Gesellschaften mit geprüften Häusern der Klasse Bergbau (ohne namenlose)."""
    from pipeline.lib.karte_export import baue_kennzahlen
    def adr(i, besitz, eig="", spanne=""):
        e = [dict(teil="II", _eigentuemer=eig, _kategorie="bergbau")] if eig else []
        return dict(id=str(i), lat=51.4, lon=7.0, stufe="haus", besitz=besitz, besitz_eigentuemer=spanne, eintraege=e)
    adressen = {a["id"]: a for a in [adr(1, "bergbau", "Gewerkschaft Mathias Stinnes"), adr(2, "bergbau", "Gewerkschaft Mathias Stinnes"),
                                      adr(3, "bergbau", spanne="Zeche Langenbrahm"), adr(4, "bergbau"), adr(5, "privatperson", "Müller")]}
    kz = baue_kennzahlen([], adressen, "2026-09-28")
    assert kz["bergbau_gesellschaften_n"] == 2 and kz["bergbau_haeuser_n"] == 4 and kz["bergbau_haeuser_ohne_name_n"] == 1


def _pf(**p):
    basis = dict(id="a", stufe="haus", stadtteil="Kray", n_I=0, n_II=0, n_III=0)
    basis.update(p)
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [7.0, 51.4]}, "properties": basis}


BB = dict(id="bergbau", titel="Bergbau", freigegeben=True, filter=dict(ebenen=["I"]), farbe=dict(art="kategorien", feld="bergbau", werte={}),
          schalter=dict(praefix="n_bb_", klassen=["leitung", "belegschaft"], namen={}))
BESITZ = dict(id="besitz", freigegeben=True, filter=dict(ebenen=["II"]), farbe=dict(art="kategorien", feld="besitz", werte={}))
AKAD = dict(id="akademiker", freigegeben=True, filter=dict(merkmal="akademiker", ebenen=["I"]), farbe=dict(art="einfach", wert="#000"))
BESITZ_FELD = dict(BESITZ, schalter=dict(feld="besitz", klassen=["bergbau", "ungeprueft"]))


def test_thema_felder_und_adressen_im_feld_modus():
    """Feld-Schalter (Besitz, Berufe): keine Zählfelder in der Kachel, Adressauswahl nach dem Wert im Farbfeld."""
    from pipeline.lib.karte_export import thema_adressen, thema_felder
    assert thema_felder(BESITZ_FELD) == ["id", "stufe", "stadtteil", "n_I", "n_II", "n_III", "besitz"]
    f = [_pf(id="1", n_II=1, besitz="bergbau"), _pf(id="2", n_II=1, besitz="privatperson"), _pf(id="3", n_II=1), _pf(id="4", n_I=1, besitz="bergbau")]
    assert [x["properties"]["id"] for x in thema_adressen(BESITZ_FELD, f)] == ["1"]   # nur Werte der Klassen, Ebene II; fehlendes Feld ≠ „ungeprueft“


def test_thema_felder_aus_filter_schaltern_und_farbe():
    from pipeline.lib.karte_export import thema_felder
    assert thema_felder(BB) == ["id", "stufe", "stadtteil", "n_I", "n_II", "n_III", "bergbau", "n_bb_leitung", "n_bb_belegschaft"]
    assert thema_felder(BESITZ) == ["id", "stufe", "stadtteil", "n_I", "n_II", "n_III", "besitz"]
    assert thema_felder(AKAD) == ["id", "stufe", "stadtteil", "n_I", "n_II", "n_III", "m_akademiker"]


def test_thema_adressen_filtert_nach_ebenen_merkmal_und_schaltern():
    from pipeline.lib.karte_export import thema_adressen
    f = [_pf(id="1", n_I=3, n_bb_belegschaft=2, bergbau="belegschaft"), _pf(id="2", n_I=3), _pf(id="3", n_II=1, n_bb_leitung=1),
         _pf(id="4", n_II=2, besitz="bergbau"), _pf(id="5", n_I=1, m_akademiker=1)]
    assert [x["properties"]["id"] for x in thema_adressen(BB, f)] == ["1"]          # Ebene I und ein Schalterfeld > 0
    assert [x["properties"]["id"] for x in thema_adressen(BESITZ, f)] == ["3", "4"]  # Ebene II
    assert [x["properties"]["id"] for x in thema_adressen(AKAD, f)] == ["5"]         # Ebene I und Merkmal


def test_thema_geojson_traegt_nur_die_themenfelder_und_meldet_leere_themen():
    from pipeline.lib.karte_export import thema_geojson
    f = [_pf(id="1", n_I=3, n_bb_belegschaft=2, bergbau="belegschaft", strasse_heute="Grenzstraße", besitz="privatperson")]
    g = thema_geojson(BB, f)
    assert g["type"] == "FeatureCollection" and len(g["features"]) == 1
    assert g["features"][0]["properties"] == dict(id="1", stufe="haus", stadtteil="Kray", n_I=3, n_II=0, n_III=0, bergbau="belegschaft", n_bb_belegschaft=2)
    assert g["features"][0]["geometry"] == f[0]["geometry"]
    with pytest.raises(ValueError, match="bergbau"):
        thema_geojson(BB, [_pf(id="2", n_I=3)])


def test_tippecanoe_thema_befehl_ohne_ausduennung():
    from pipeline.lib.karte_export import tippecanoe_thema_befehl
    b = tippecanoe_thema_befehl(pathlib.Path("t.geojson"), pathlib.Path("t.pmtiles"))
    assert b[0] == "tippecanoe" and "-r1" in b and "--minimum-zoom=9" in b and "--maximum-zoom=15" in b
    assert "--no-feature-limit" in b and "--no-tile-size-limit" in b and "--drop-densest-as-needed" not in b
    assert "-L" in b and "adressen:t.geojson" in b and "t.pmtiles" in b


def test_schreibe_themen_mit_kacheln_schreibt_geojson_und_index(tmp_path, monkeypatch):
    from pipeline.lib import karte_export
    q = tmp_path / "q"; q.mkdir()
    (q / "bergbau.json").write_text(json.dumps(BB), encoding="utf-8")
    (q / "a.json").write_text('{"id": "a", "titel": "A"}', encoding="utf-8")
    aufrufe = []
    monkeypatch.setattr(karte_export.subprocess, "run", lambda cmd, check: aufrufe.append(cmd))
    f = [_pf(id="1", n_I=3, n_bb_belegschaft=2, bergbau="belegschaft")]
    idx = karte_export.schreibe_themen(q, tmp_path / "out", features=f, kacheln=True)
    assert idx == [dict(id="a", titel="A", freigegeben=False, kacheln=False), dict(id="bergbau", titel="Bergbau", freigegeben=True, kacheln=True)]
    assert not list((tmp_path / "out" / "themen").glob("*.geojson"))          # Zwischenstand bleibt nicht im Datenpaket (Deploy!)
    assert json.loads((tmp_path / "out" / "themen" / "index.json").read_text(encoding="utf-8")) == idx
    assert len(aufrufe) == 1 and str(tmp_path / "out" / "themen" / "bergbau.pmtiles") in aufrufe[0]
    geo = [a for a in aufrufe[0] if a.startswith("adressen:")][0][len("adressen:"):]
    assert geo.endswith("bergbau.geojson") and not geo.startswith(str(tmp_path / "out"))
    # ohne kacheln: kein tippecanoe, Index ohne Kachelflag true
    aufrufe.clear()
    idx2 = karte_export.schreibe_themen(q, tmp_path / "out2", features=f, kacheln=False)
    assert aufrufe == [] and all(e["kacheln"] is False for e in idx2)


def test_baue_adressen_kurz_verteilt_nach_erstem_zeichen_und_traegt_sieben_werte():
    from pipeline.lib.karte_export import baue_adressen_kurz
    adressen = {
        "a1b2": dict(id="a1b2", lat=51.4912345678, lon=7.0612345678, stufe="haus", stadtteil="Katernberg", strasse_heute="Lattenkamp", hausnr="25", hausnr_zusatz="a", historisch="Grenzstr. 25, Katernberg"),
        "a9ff": dict(id="a9ff", lat=51.5, lon=7.1, stufe="stadtplan", stadtteil="", strasse_heute="", hausnr="3", hausnr_zusatz="", historisch="Alte Str. 3"),
        "b000": dict(id="b000", lat=51.6, lon=7.2, stufe="strasse", stadtteil="Kray", strasse_heute="Kampstr.", hausnr="", hausnr_zusatz=None, historisch="Kampstr."),
    }
    k = baue_adressen_kurz(adressen)
    assert sorted(k) == ["a", "b"]
    assert k["a"]["a1b2"] == [7.061235, 51.491235, "haus", "Katernberg", "Lattenkamp", "25a", "Grenzstr. 25, Katernberg"]
    assert k["a"]["a9ff"] == [7.1, 51.5, "stadtplan", "", "", "3", "Alte Str. 3"]
    assert k["b"]["b000"] == [7.2, 51.6, "strasse", "Kray", "Kampstr.", "", "Kampstr."]


def test_schreibe_paket_schreibt_kurzindex(tmp_path):
    e = [_v(id="1", lastname="Sepeur", firstname="Wilh.", teil="I")]
    schreibe_paket(tmp_path, e, [], lies_csv(FIX / "zechen.csv"), "2026-09-21", kacheln=False)
    aid = adress_id(e[0])
    kurz = json.loads((tmp_path / "adressen_kurz" / f"{aid[0]}.json").read_text())
    assert kurz[aid][:3] == [7.06, 51.49, "haus"] and kurz[aid][4] == "Lattenkamp"


def test_thema_praesenzfeld_nimmt_adressen_ohne_teil_ii_zeile_auf():
    """Thema Besitz (Spannen-Häuser): filter.praesenz nennt ein Zählfeld, das statt der Ebenen-Summe genügt."""
    from pipeline.lib.karte_export import thema_adressen, thema_felder
    t = dict(BESITZ, filter=dict(ebenen=["II"], praesenz="n_besitz"))
    assert thema_felder(t) == ["id", "stufe", "stadtteil", "n_I", "n_II", "n_III", "n_besitz", "besitz"]
    f = [_pf(id="1", n_II=1, besitz="bergbau"), _pf(id="2", n_I=2, n_besitz=1, besitz="industrie"), _pf(id="3", n_I=1, besitz="ungeprueft")]
    assert [x["properties"]["id"] for x in thema_adressen(t, f)] == ["1", "2"]
    assert [x["properties"]["id"] for x in thema_adressen(BESITZ, f)] == ["1"]   # ohne Präsenzfeld wie bisher


def test_stellung_je_adresse_mehrheit_gemischt_ungeprueft():
    """Spec Themenbaum §4: Mehrheitsstellung der geprüften Bewohner; Vorschlag zählt wie Hand; 1:1 → gemischt; nichts geprüft → ungeprueft."""
    from pipeline.lib.karte_export import _stellung, punkt_feature
    def b(st, q="hand"):
        return dict(teil="I", _beruf=dict(stellung=st, stellung_quelle=q, niveau="fachlich"), _merkmale=[])
    ohne = dict(teil="I", _beruf=None, _merkmale=[])
    assert _stellung([b("arbeiter"), b("arbeiter", "vorschlag"), b("beamte"), ohne]) == ("arbeiter", {"arbeiter": 2, "beamte": 1})
    assert _stellung([b("arbeiter"), b("beamte"), ohne]) == ("gemischt", {"arbeiter": 1, "beamte": 1})
    assert _stellung([ohne, dict(teil="II", _beruf=dict(stellung="arbeiter", stellung_quelle="hand"), _merkmale=[])]) == ("ungeprueft", {})
    a = dict(id="x", lat=51.4, lon=7.0, stufe="haus", stadtteil="Kray", strasse_heute="A", hausnr="1", hausnr_zusatz="", historisch="A 1",
             nummer_unsicher="nein", eintraege=[b("arbeiter"), b("arbeiter", "vorschlag"), b("beamte")], besitz="ungeprueft", niveau="fachlich")
    a["stellung"], a["n_stellung"] = _stellung(a["eintraege"])
    assert punkt_feature(a)["properties"]["stellung"] == "arbeiter"


def test_themen_listen_besitz_bergbau_berufe():
    """Spec Themenbaum §6: je Thema Oberkategorie → Einträge (Schlüssel, Name, Häuser); ein OhdAB-Schlüssel steht in genau einer
    Bergbau-Gruppe (die mit den meisten Nennungen) und bei genau einer Stellung; Anteil handgeprüft nach Nennungen."""
    from pipeline.lib.karte_export import baue_themen_listen
    def haus(i, eintraege, **f):
        a = dict(id=f"h{i}", lat=51.4, lon=7.0, stufe="haus", stadtteil="Kray", strasse_heute="A", hausnr=str(i), hausnr_zusatz="", historisch=f"A {i}",
                 nummer_unsicher="nein", eintraege=eintraege, besitz="ungeprueft", besitz_quelle="", besitz_eigentuemer="", stellung="ungeprueft")
        a.update(f)
        return a
    def p(ohdab, norm, st, q="hand", bb=None):
        b = dict(ohdab=ohdab, norm=norm, stellung=st, stellung_quelle=q, niveau="fachlich")
        if bb:
            b["bergbau"] = bb
        return dict(teil="I", _beruf=b, _merkmale=[], _eigentuemer="", _identitaet=False, _kategorie="")
    def eig(name, kat):
        return dict(teil="II", _beruf=None, _merkmale=[], _eigentuemer=name, _identitaet=True, _kategorie=kat)
    adressen = {a["id"]: a for a in [
        haus(1, [p("B1", "Bergmann", "arbeiter", bb="belegschaft"), p("B1", "Bergmann", "arbeiter", "vorschlag", bb="invaliden"), eig("Krupp", "industrie")], besitz="industrie", besitz_quelle="eintrag", stellung="arbeiter"),
        haus(2, [p("B1", "Bergmann", "arbeiter", bb="belegschaft"), p("S1", "Steiger", "angestellte", bb="aufsicht")], stellung="gemischt"),
        haus(3, [p("S1", "Steiger", "angestellte", bb="aufsicht"), eig("Stadt Essen", "stadt_staat")], besitz="stadt_staat", besitz_quelle="eintrag", stellung="angestellte"),
        haus(4, [dict(teil="I", _beruf=None, _merkmale=[], _eigentuemer="", _identitaet=False, _kategorie="")], besitz="industrie", besitz_quelle="spanne", besitz_eigentuemer="Krupp"),
        haus(5, [dict(teil="III", _beruf=None, _merkmale=[], _eigentuemer="", _identitaet=False, _kategorie="")]),   # nur Gewerbe: in keinem der drei Themen sichtbar
    ]}
    L = baue_themen_listen(adressen)
    bs = {o["id"]: o for o in L["besitz"]["oberkategorien"]}
    assert bs["industrie"]["adressen"] == 2 and bs["industrie"]["eintraege"] == [dict(schluessel="eig:Krupp", name="Krupp", adressen=2)]
    assert bs["stadt_staat"]["eintraege"] == [dict(schluessel="eig:Stadt Essen", name="Stadt Essen", adressen=1)]
    assert bs["privatperson"]["adressen"] == 0 and bs["privatperson"]["eintraege"] == []
    # Review 2026-09-29: „ungeprüft“ zählt nur Häuser, die das Thema zeigt (Besitz: Teil-II-Zeile oder belegter Besitz; Berufe: Teil-I-Eintrag)
    assert L["besitz"]["ungeprueft"] == 0 and L["besitz"]["handgeprueft_anteil"] is None
    bb = {o["id"]: o for o in L["bergbau"]["oberkategorien"]}
    assert [o["id"] for o in L["bergbau"]["oberkategorien"]] == ["leitung", "aufsicht", "belegschaft", "invaliden"]
    assert bb["belegschaft"]["adressen"] == 2 and bb["belegschaft"]["eintraege"] == [dict(schluessel="norm:B1", name="Bergmann", adressen=2)]
    assert bb["invaliden"]["adressen"] == 1 and bb["invaliden"]["eintraege"] == []          # Bergmann steht nur einmal: 2 Nennungen Belegschaft, 1 Invaliden
    assert bb["aufsicht"]["eintraege"] == [dict(schluessel="norm:S1", name="Steiger", adressen=2)]
    st = {o["id"]: o for o in L["berufe"]["oberkategorien"]}
    assert [o["id"] for o in L["berufe"]["oberkategorien"]][:3] == ["arbeiter", "angestellte", "beamte"]
    assert st["arbeiter"]["adressen"] == 2 and st["arbeiter"]["eintraege"][0]["schluessel"] == "norm:B1"
    assert st["angestellte"]["eintraege"] == [dict(schluessel="norm:S1", name="Steiger", adressen=2)]
    assert L["berufe"]["gemischt"] == 1 and L["berufe"]["ungeprueft"] == 1      # Haus 4 (Teil I ohne geprüften Beruf), nicht Haus 5
    assert L["berufe"]["handgeprueft_anteil"] == 0.8      # 4 von 5 Nennungen mit geprüftem Beruf sind handgeprüft


def test_themen_definitionen_tragen_baum_und_berufe_faerben_nach_stellung():
    """Spec Themenbaum §4/§6: Berufe färben nach Stellung (neun Klassen + gemischt + ungeprueft); drei Themen mit Baum."""
    themen = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in pathlib.Path("kuratierung/themen").glob("*.json")}
    b = themen["berufe"]
    assert b["farbe"]["feld"] == "stellung" and b["schalter"]["feld"] == "stellung"
    assert b["schalter"]["klassen"] == ["arbeiter", "angestellte", "beamte", "selbstaendige", "freie_berufe", "unternehmer", "kaufleute", "ohne_erwerb", "unbestimmt", "gemischt", "ungeprueft"]
    assert set(b["farbe"]["werte"]) == set(b["schalter"]["klassen"]) - {"ungeprueft"}
    assert b["farbe"]["werte"]["kaufleute"] == "#4b5563" and b["farbe"]["sonst"] == "#c8c8c8"
    assert all(themen[t].get("baum") is True for t in ("besitz", "bergbau", "berufe"))
    assert "eigentuemerliste" not in themen["besitz"].get("zusatz", {})
    assert all("Kästchen" not in themen[t]["text"] for t in ("besitz", "bergbau", "berufe"))
    assert "Popup" not in b["text"]      # Review 2026-09-29: das Popup kennzeichnet Vorschläge nicht, nur die Hausansicht


def test_berufsnormindex_nur_teil_i_und_pillzahl_gleich_scherbe(tmp_path):
    """Review 2026-09-29 (Important 1): Die Normscherbe (Treffer der Pill) und die Themenliste (Zahl an der Pill) zählen dieselben
    Häuser — nur Teil I mit geprüftem Beruf, wie es die Grundgesamtheit in der Vergleichsleiste sagt."""
    from pipeline.lib.berufe import lade_ohdab, lade_kuratierung as lade_berufe
    from pipeline.lib.karte_export import baue_berufsnormindex, baue_themen_listen, gruppiere
    from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); o = lade_ohdab(p)
    b = lade_berufe([dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja", stellung="arbeiter", stellung_geprueft="ja")])
    basis = dict(stufe="haus", lat="51.4", lon="7.0", strasse_norm="x", strasse_roh="X", Vorort="", stadtteil="Kray", lastname="N", firstname="", page="I-1")
    def e(i, teil, hausnr):
        return dict(basis, id=str(i), teil=teil, hausnr=hausnr, **{"Beruf o. ä.": "Bergm."})
    a = gruppiere([e(1, "I", "1"), e(2, "II", "2"), e(3, "I", "3"), e(4, "II", "3")], [], None, berufe=b, ohdab=o)   # Haus 2: nur Eigentümer mit Beruf
    liste, scherben = baue_berufsnormindex(a)
    assert liste[0][3] == 2 and len(scherben["be"]["B 21112-100"]) == 2                     # Nennungen und Häuser: nur Teil I
    L = baue_themen_listen(a)
    st = {o_["id"]: o_ for o_ in L["berufe"]["oberkategorien"]}
    assert st["arbeiter"]["eintraege"][0]["adressen"] == len(scherben["be"]["B 21112-100"])


def test_rubrikindex_liste_und_scherben():
    """Suche nach Gewerberubrik (Kartenlink aus den Schlaglichtern, 2026-09-29): Liste [Schlüssel, Rubrik, Betriebe, Branche] nach
    Betrieben absteigend; Scherbe praefix2(Rubrik) → Rubrik → [[Adress-ID, Betriebe im Haus]]; derselbe Betrieb zählt einmal."""
    from pipeline.lib.karte_export import baue_rubrikindex
    def haus(i, eintraege):
        return dict(id=f"h{i}", eintraege=eintraege)
    def g(rubrik, gruppe, schluessel):
        return dict(teil="III", _gewerbe=dict(rubrik=rubrik, firma="F", gruppe=gruppe, art="handwerk", quelle="hand", schluessel=schluessel), _merkmale=[])
    adressen = {a["id"]: a for a in [
        haus(1, [g("Schneider für Herren", "textil_bekleidung", "s1"), g("Schneider für Herren", "textil_bekleidung", "s1"), g("Bäcker", "lebensmittel", "b1")]),
        haus(2, [g("Schneider für Herren", "textil_bekleidung", "s2"), dict(teil="I", _merkmale=[])]),
    ]}
    liste, scherben = baue_rubrikindex(adressen)
    assert liste == [["schneider fuer herren", "Schneider für Herren", 2, "textil_bekleidung"], ["baecker", "Bäcker", 1, "lebensmittel"]]
    assert scherben["sc"]["Schneider für Herren"] == [["h1", 1], ["h2", 1]]
    assert scherben["ba"]["Bäcker"] == [["h1", 1]]
