import pathlib

from pipeline.lib.merkmale import Regel, lade_regeln, merkmale_fuer

FIX = pathlib.Path(__file__).parent / "fixtures" / "merkmale"


def test_lade_regeln_liest_alle_tabellen():
    regeln = lade_regeln(FIX)
    assert len(regeln) == 4
    assert regeln[0] == Regel(feld="Beruf o. ä.", art="praefix", muster="Dr.", merkmal="akademiker")


def test_merkmale_praefix_exakt_regex():
    regeln = lade_regeln(FIX)
    assert merkmale_fuer({"Beruf o. ä.": "Dr. med.", "firstname": "Karl"}, regeln) == ["akademiker"]
    assert merkmale_fuer({"Beruf o. ä.": "Bergm.", "firstname": ""}, regeln) == ["bergbau"]
    assert merkmale_fuer({"Beruf o. ä.": "Hauer u. Dr.", "firstname": "Dr. Fritz"}, regeln) == ["akademiker", "bergbau"]
    assert merkmale_fuer({"Beruf o. ä.": "Bergmann", "firstname": ""}, regeln) == []


def test_unbekannte_art_wird_abgewiesen(tmp_path):
    (tmp_path / "x.csv").write_text("feld,art,muster,merkmal,beleg,bearbeiter,datum\nBeruf o. ä.,fuzzy,Dr,akademiker,,,\n", encoding="utf-8")
    try:
        lade_regeln(tmp_path)
    except ValueError as e:
        assert "fuzzy" in str(e)
    else:
        raise AssertionError("ValueError erwartet")


def test_ungültiger_regex_wird_abgewiesen(tmp_path):
    (tmp_path / "x.csv").write_text("feld,art,muster,merkmal,beleg,bearbeiter,datum\nBeruf o. ä.,regex,(,akademiker,,,\n", encoding="utf-8")
    try:
        lade_regeln(tmp_path)
    except ValueError as e:
        assert "ungültiger regulärer Ausdruck" in str(e)
    else:
        raise AssertionError("ValueError erwartet")


def test_leeres_muster_wird_abgewiesen(tmp_path):
    (tmp_path / "x.csv").write_text("feld,art,muster,merkmal,beleg,bearbeiter,datum\nBeruf o. ä.,exakt,,akademiker,,,\n", encoding="utf-8")
    try:
        lade_regeln(tmp_path)
    except ValueError as e:
        assert "muster und merkmal müssen gefüllt sein" in str(e)
    else:
        raise AssertionError("ValueError erwartet")
