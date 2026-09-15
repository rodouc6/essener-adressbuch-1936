from pipeline.lib.bericht import erzeuge


def test_bericht_enthaelt_kernzahlen():
    e = [dict(teil="I", stufe="haus", grund="", herkunft="heutig", parse_status="ok", mehrdeutig="nein"),
         dict(teil="I", stufe="offen", grund="kein_treffer", herkunft="heutig", parse_status="ok", mehrdeutig="nein"),
         dict(teil="II", stufe="strasse", grund="", herkunft="konkordanz", parse_status="ok", mehrdeutig="nein")]
    a = [dict(strasse_heute="A", hausnr="1", hausnr_zusatz="", stadtteil="", stufe="haus", lat="51.4", lon="7.0",
              display_name="x", zeilen="2", herkunft="", strasse_roh="A", grund="", parse_status="ok"),
         dict(strasse_heute="B", hausnr="2", hausnr_zusatz="", stadtteil="", stufe="offen", lat="", lon="",
              display_name="", zeilen="1", herkunft="", strasse_roh="B", grund="kein_treffer", parse_status="ok")]
    md, geo = erzeuge(e, a, strassen=[], dubletten=[{"id": "1", "dublette_von": "2"}], ausgeschlossen=[], vorschlaege=[])
    assert "| haus |" in md and "33,3" in md and "Dubletten: 1" in md
    assert geo["type"] == "FeatureCollection" and len(geo["features"]) == 1
    assert geo["features"][0]["geometry"]["coordinates"] == [7.0, 51.4]
