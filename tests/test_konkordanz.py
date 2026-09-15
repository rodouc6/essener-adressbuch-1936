from pathlib import Path
import pytest
from pipeline.lib.konkordanz import VORORT_STADTTEILE, Strassenindex

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def idx():
    return Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv")


def test_heutig_eindeutig(idx):
    a = idx.aufloesen("bochumer straße", "Steele")
    assert (a.strasse_heute, a.schl_nr, a.herkunft, a.mehrdeutig) == ("Bochumer Straße", "00007", "heutig", "nein")


def test_heutig_mehrdeutig_ohne_vorort(idx):
    a = idx.aufloesen("schulstraße", "")
    assert a.herkunft == "heutig" and a.mehrdeutig == "ja" and a.strasse_heute == "" and "00008" in a.kandidaten and "00009" in a.kandidaten


def test_heutig_mehrdeutig_mit_vorort_aufgeloest(idx):
    a = idx.aufloesen("schulstraße", "Kray")
    assert (a.schl_nr, a.mehrdeutig, a.stadtteil) == ("00009", "nein", "Kray")


def test_konkordanz_eindeutig(idx):
    a = idx.aufloesen("hermann-göring-straße", "")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend) == ("Bredeneyer Straße", "konkordanz", "nein")


def test_konkordanz_nicht_eindeutig_bleibt_offen(idx):
    a = idx.aufloesen("hochstraße", "")
    assert a.herkunft == "konkordanz" and a.mehrdeutig == "ja" and a.strasse_heute == ""


def test_stadium_im_fenster(idx):
    # Gusestraße galt bis 1938-10-21 → Stadium gültig 1936 → stadium, nicht abweichend
    a = idx.aufloesen("gusestraße", "")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend) == ("Goosestraße", "stadium", "nein")


def test_stadium_ausserhalb_fenster(idx):
    # Carlstraße endete 1910 → weit vor 1930 → zeitlich_abweichend
    a = idx.aufloesen("carlstraße", "")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend) == ("Karlstraße", "stadium", "ja")


def test_kuratiert(idx):
    a = idx.aufloesen("hstr.", "Kray")
    assert (a.strasse_heute, a.schl_nr, a.herkunft) == ("Schulstraße", "00009", "kuratiert")


def test_offen(idx):
    a = idx.aufloesen("stadtwiese", "")
    assert a.herkunft == "offen" and a.strasse_heute == ""


def test_vorort_widerspruch_wird_nicht_still_aufgeloest(idx):
    # Bochumer Straße liegt in Steele; Vorort Kray widerspricht → mehrdeutig=ja mit Kandidat
    a = idx.aufloesen("bochumer straße", "Kray")
    assert a.mehrdeutig == "ja" and a.strasse_heute == "" and "00007" in a.kandidaten


def test_vorschlaege(idx):
    v = idx.vorschlaege("archternbergstraße")
    assert v[0][1] == "Achternbergstraße" and v[0][2] >= 0.85


def test_vorort_stadtteile_vollstaendig():
    assert set(VORORT_STADTTEILE) == {"Frillendorf", "Heidhausen", "Heisingen", "Karnap", "Katernberg", "Kray", "Kupferdreh", "Schonnebeck", "Steele", "Stoppenberg", "Ueberruhr", "Werden"}
    assert "Fischlaken" in VORORT_STADTTEILE["Heidhausen"]


def test_vorort_widerspruch_faellt_zur_konkordanz_durch(idx):
    # Hauptstraße existiert heute nur in Kettwig; Vorort Kupferdreh → Konkordanz kennt die Umbenennung
    a = idx.aufloesen("hauptstraße", "Kupferdreh")
    assert (a.strasse_heute, a.schl_nr, a.herkunft, a.mehrdeutig) == ("Kupferdreher Straße", "00011", "konkordanz", "nein")


def test_kettwig_allein_ist_nie_treffer(idx):
    # Kettwig gehörte 1936 nicht zu Essen: ohne Vorort darf die Kettwiger Hauptstraße nicht als heutig gelten
    a = idx.aufloesen("hauptstraße", "")
    assert a.herkunft == "offen"


def test_kettwig_mit_weiterem_stadtteil_bleibt_zulaessig(idx):
    a = idx.aufloesen("ruhrtalstraße", "Werden")
    assert (a.strasse_heute, a.mehrdeutig) == ("Ruhrtalstraße", "nein")


def test_vorort_widerspruch_ohne_alternative_bleibt_mehrdeutig_mit_grund(idx):
    a = idx.aufloesen("bochumer straße", "Kray")
    assert a.mehrdeutig == "ja" and a.grund_mehrdeutig == "vorort_widerspruch" and "00007" in a.kandidaten


def test_mehrere_passende_kandidaten_haben_grund(idx):
    a = idx.aufloesen("schulstraße", "")
    assert a.mehrdeutig == "ja" and a.grund_mehrdeutig == "mehrere_kandidaten"


def test_konkordanz_nicht_eindeutig_hat_grund(idx):
    a = idx.aufloesen("hochstraße", "")
    assert a.mehrdeutig == "ja" and a.grund_mehrdeutig == "konkordanz_nicht_eindeutig"
