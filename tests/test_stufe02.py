from pipeline.lib.stufen import parse_zeilen


def test_parse_zeilen_ergaenzt_felder():
    z = [{"id": "1", "Adresse": "Kahrstr. 39D II", "Vorort": ""}]
    out = parse_zeilen(z)
    assert out[0]["strasse_roh"] == "Kahrstr." and out[0]["strasse_norm"] == "kahrstraße"
    assert out[0]["hausnr"] == "39" and out[0]["hausnr_zusatz"] == "d" and out[0]["lage"] == "II"
    assert out[0]["parse_status"] == "ok"


def test_parse_zeilen_leere_adresse():
    z = [{"id": "2", "Adresse": "", "Vorort": "Steele"}]
    out = parse_zeilen(z)
    row = out[0]
    assert row["parse_status"] == "leer"
    assert row["strasse_roh"] == "" and row["strasse_norm"] == ""
    assert row["hausnr"] == "" and row["hausnr_zusatz"] == "" and row["hausnr_bis"] == ""
    assert row["lage"] == "" and row["zusatz_frei"] == ""


def test_parse_zeilen_ohne_adresse_feld():
    z = [{"id": "3", "Vorort": "Kray"}]
    out = parse_zeilen(z)
    row = out[0]
    assert row["parse_status"] == "leer"
    assert row["strasse_roh"] == "" and row["strasse_norm"] == ""


def test_parse_zeilen_ohne_nummer():
    z = [{"id": "4", "Adresse": "Börsenhaus", "Vorort": ""}]
    out = parse_zeilen(z)
    row = out[0]
    assert row["parse_status"] == "ohne_nummer"
    assert row["strasse_roh"] == "Börsenhaus"
    assert row["strasse_norm"] == "börsenhaus"
    assert row["hausnr"] == ""


def test_parse_zeilen_behaelt_urspruengliche_felder():
    z = [{"id": "5", "Adresse": "Kahrstr. 39D II", "Vorort": "Steele"}]
    out = parse_zeilen(z)
    row = out[0]
    assert row["id"] == "5"
    assert row["Vorort"] == "Steele"
