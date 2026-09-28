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


def test_hausnummernspanne_und_haeuser_der_zeile():
    from pipeline.lib.eigentuemer import haeuser_der_zeile, hausnummernspanne
    assert hausnummernspanne(dict(hausnr="2", hausnr_bis="84")) == (2, 84, 0)          # gerade Seite
    assert hausnummernspanne(dict(hausnr="1", hausnr_bis="9")) == (1, 9, 1)            # ungerade Seite
    assert hausnummernspanne(dict(hausnr="2", hausnr_bis="9")) == (2, 9, None)         # beide Seiten
    assert hausnummernspanne(dict(hausnr="1", hausnr_bis="31a")) == (1, 31, 1)         # Buchstabe zählt als Zahl
    assert hausnummernspanne(dict(hausnr="37", hausnr_bis="37A")) == (37, 37, 1)       # Haus und Anbau
    assert hausnummernspanne(dict(hausnr="40", hausnr_bis="4")) is None                # verdreht
    assert hausnummernspanne(dict(hausnr="12", hausnr_bis="")) is None and hausnummernspanne({}) is None
    assert [haeuser_der_zeile(dict(hausnr=a, hausnr_bis=b)) for a, b in (("2", "84"), ("2", "9"), ("37", "37A"), ("5", ""), ("40", "4"))] == [42, 8, 1, 1, 1]


def test_kuratierung_bergbau_kanonische_namen_ohne_dubletten():
    """Spec Bergbau §2.5: ein kanonischer Name je Gesellschaft — sonst zählt das Kapitel eine Gesellschaft mehrfach."""
    from pipeline.lib.io import lies_csv, projektwurzel
    zeilen = lies_csv(projektwurzel() / "kuratierung" / "eigentuemer.csv")
    kanon = {z["eigentuemer"].strip() for z in zeilen if z.get("kategorie") == "bergbau" and z.get("geprueft") == "ja"}
    assert [k for k in kanon if "König Wilhelm" in k] == ["Essener Bergwerks-Verein König Wilhelm"]
    assert [k for k in kanon if "lheimer Bergwerks" in k] == ["Mülheimer Bergwerks-Verein"]
    assert "Gewerkschft Zeche Carolus Magnus" not in kanon and "Gewerkschaft Zeche Carolus Magnus" in kanon
