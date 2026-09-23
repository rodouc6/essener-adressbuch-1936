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
    assert FELDER_KURATIERUNG == ["schreibweise", "art", "eigentuemer", "kategorie", "geprueft", "bearbeiter", "datum", "hinweis", "identitaet"]


def test_stadtteil_aufteilung_und_identitaet():
    from pipeline.lib.eigentuemer import identitaet_sicher, lade_stadtteil_liste, mit_stadtteil
    e = {"Firmenname": "Kath. Kirchengem.", "lastname": "", "firstname": "", "stadtteil": "Katernberg"}
    assert schreibweise_von(e) == ("Kath. Kirchengem.", "koerperschaft")
    assert schreibweise_von(e, {"Kath. Kirchengem."}) == ("Kath. Kirchengem. ‹Katernberg›", "koerperschaft")
    assert mit_stadtteil("X", {"stadtteil": "", "Vorort": "Kray"}) == "X ‹Kray›"
    assert mit_stadtteil("X", {}) == "X ‹Stadtteil unbekannt›"
    assert lade_stadtteil_liste([{"schreibweise": " Kath. Kirchengem. "}, {"schreibweise": ""}]) == frozenset({"Kath. Kirchengem."})
    assert identitaet_sicher({"art": "koerperschaft"}) is True
    assert identitaet_sicher({"art": "person", "identitaet": ""}) is False
    assert identitaet_sicher({"art": "person", "identitaet": "sicher"}) is True
