from pipeline.lib.stufen import parse_zeilen


def test_parse_zeilen_ergaenzt_felder():
    z = [{"id": "1", "Adresse": "Kahrstr. 39D II", "Vorort": ""}]
    out = parse_zeilen(z)
    assert out[0]["strasse_roh"] == "Kahrstr." and out[0]["strasse_norm"] == "kahrstraße"
    assert out[0]["hausnr"] == "39" and out[0]["hausnr_zusatz"] == "d" and out[0]["lage"] == "II"
    assert out[0]["parse_status"] == "ok"
