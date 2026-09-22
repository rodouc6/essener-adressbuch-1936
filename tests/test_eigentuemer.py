from pipeline.lib.eigentuemer import (AUTOMATIK, FELDER_KURATIERUNG, KATEGORIEN, gesperrt,
                                      lade_kuratierung, schreibweise_von)


def test_kategorien_vollstaendig():
    assert list(KATEGORIEN) == ["stadt_staat", "bergbau", "industrie", "genossenschaft_siedlung",
                                "kirche_stiftung", "bank_versicherung", "privatperson", "sonstige"]
    assert KATEGORIEN["genossenschaft_siedlung"] == "Genossenschaft/Siedlung"


def test_schreibweise_von():
    assert schreibweise_von({"Firmenname": " Fried. Krupp A.G. ", "lastname": "", "firstname": ""}) == ("Fried. Krupp A.G.", "koerperschaft")
    assert schreibweise_von({"Firmenname": "", "lastname": "Schmidt", "firstname": "Wilh."}) == ("Schmidt, Wilh.", "person")
    assert schreibweise_von({"Firmenname": "", "lastname": "Schmidt", "firstname": ""}) == ("Schmidt", "person")
    assert schreibweise_von({"Firmenname": "", "lastname": "", "firstname": ""}) == ("", "")


def test_lade_kuratierung_und_sperre():
    zeilen = [dict(schreibweise=" Stadt Essen ", eigentuemer="Stadt Essen", geprueft="ja", bearbeiter="christos"),
              dict(schreibweise="Fried. Krupp A.G.", eigentuemer="Fried. Krupp AG", geprueft="", bearbeiter=AUTOMATIK),
              dict(schreibweise="Fried. Krupp AG.", eigentuemer="Krupp", geprueft="", bearbeiter="christos")]
    k = lade_kuratierung(zeilen)
    assert set(k) == {"Stadt Essen", "Fried. Krupp A.G.", "Fried. Krupp AG."}
    assert gesperrt(k["Stadt Essen"]) is True          # geprüft
    assert gesperrt(k["Fried. Krupp A.G."]) is False   # Automatik, ungeprüft
    assert gesperrt(k["Fried. Krupp AG."]) is True     # vom Menschen angefasst
    assert FELDER_KURATIERUNG == ["schreibweise", "art", "eigentuemer", "kategorie", "geprueft", "bearbeiter", "datum", "hinweis"]
