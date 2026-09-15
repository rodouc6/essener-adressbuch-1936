from pathlib import Path
import pytest
from pipeline.lib.konkordanz import NICHT_ESSEN_1936, VORORT_STADTTEILE, VORORT_STADTTEILE_ALLE, Strassenindex

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
    # Kettwig gehörte 1936 nicht zu Essen: die Kettwiger Hauptstraße (00002) darf auch
    # ohne Vorort nie Kandidat sein. Im Kandidatenmengen-Modell bleibt dann der einzige
    # verbleibende Kandidat aus der Konkordanz übrig (00011), statt die Auflösung abzubrechen.
    a = idx.aufloesen("hauptstraße", "")
    assert a.schl_nr != "00002" and "00002" not in a.kandidaten


def test_nur_in_kettwig_gelegene_strasse_bleibt_offen(idx):
    # Am Bilstein liegt ausschließlich in Kettwig → kein Kandidat → offen
    a = idx.aufloesen("am bilstein", "")
    assert (a.herkunft, a.strasse_heute, a.kandidaten) == ("offen", "", "")


def test_kettwig_mit_weiterem_stadtteil_bleibt_zulaessig(idx):
    a = idx.aufloesen("ruhrtalstraße", "Werden")
    assert (a.strasse_heute, a.mehrdeutig) == ("Ruhrtalstraße", "nein")


def test_vorort_widerspruch_ohne_alternative_bleibt_mehrdeutig_mit_grund(idx):
    a = idx.aufloesen("bochumer straße", "Kray")
    assert a.mehrdeutig == "ja" and a.grund_mehrdeutig == "vorort_widerspruch" and "00007" in a.kandidaten


def test_mehrere_passende_kandidaten_haben_grund(idx):
    # Kandidatenmengen-Modell: mehrere passende Kandidaten heißen jetzt homonym_1936 (Spec §5.03)
    a = idx.aufloesen("schulstraße", "")
    assert a.mehrdeutig == "ja" and a.grund_mehrdeutig == "homonym_1936"


def test_konkordanz_nicht_eindeutig_hat_grund(idx):
    a = idx.aufloesen("hochstraße", "")
    assert a.mehrdeutig == "ja" and a.grund_mehrdeutig == "konkordanz_nicht_eindeutig"


# --- Kandidatenmengen-Modell (Gesamt-Review 2026-09-15, Spec §5.03) ----------


def test_taubenstrasse_heutiger_name_erst_1966(idx):
    """Heutige Taubenstraße liegt in Burgaltendorf und heißt erst seit 1966 so;
    1936 war die Taubenstraße im Ostviertel (heute Natorpstraße)."""
    a = idx.aufloesen("taubenstraße", "", "I")
    assert (a.strasse_heute, a.schl_nr, a.herkunft) == ("Natorpstraße", "02287", "konkordanz")
    assert (a.mehrdeutig, a.zeitlich_abweichend) == ("nein", "nein")


def test_burgaltendorf_ist_nie_kandidat(idx):
    """Burgaltendorf gehörte 1936 nicht zu Essen — 03046 darf nicht auftauchen."""
    a = idx.aufloesen("taubenstraße", "", "I")
    assert "03046" not in a.kandidaten and a.schl_nr != "03046"


def test_gerswidastrasse_stadium_im_fenster_schlaegt_heutiges_lemma(idx):
    """Die heutige Gerswidastraße im Stadtkern trägt den Namen erst seit 1966;
    1936 hieß die heutige Girardetstraße in Rüttenscheid so."""
    a = idx.aufloesen("gerswidastraße", "", "I")
    assert (a.strasse_heute, a.schl_nr, a.herkunft) == ("Girardetstraße", "01119", "stadium")
    assert (a.mehrdeutig, a.zeitlich_abweichend) == ("nein", "nein")


def test_hermannstrasse_kernstadt_bleibt_mehrdeutig(idx):
    """Teil I ohne Vorort = Kernstadt: Katernberg und Fischlaken fallen weg,
    es bleiben aber mehrere Kernstadt-Hermannstraßen → homonym_1936."""
    a = idx.aufloesen("hermannstraße", "", "I")
    assert (a.mehrdeutig, a.grund_mehrdeutig) == ("ja", "homonym_1936")
    assert set(a.kandidaten.split(";")) == {"00770", "01569"}


def test_hermannstrasse_teil_ii_ohne_vorort_bleibt_mehrdeutig(idx):
    """Teil II ohne Vorort = keine Information: kein Filter, also mehrdeutig."""
    a = idx.aufloesen("hermannstraße", "", "II")
    assert (a.mehrdeutig, a.grund_mehrdeutig) == ("ja", "homonym_1936")
    assert "01282" in a.kandidaten


def test_hermannstrasse_mit_vorort_wird_eindeutig(idx):
    a = idx.aufloesen("hermannstraße", "Heidhausen", "II")
    assert (a.strasse_heute, a.schl_nr, a.herkunft, a.mehrdeutig) == ("Alinenhöhe", "00037", "konkordanz", "nein")


def test_kernstadt_schliesst_reine_vorort_kandidaten_aus(idx):
    """Schulstraße gibt es nur in Steele und Kray — in Teil I passt keiner."""
    a = idx.aufloesen("schulstraße", "", "I")
    assert (a.mehrdeutig, a.grund_mehrdeutig) == ("ja", "vorort_widerspruch")
    assert set(a.kandidaten.split(";")) == {"00008", "00009"}


def test_teil_ii_ohne_vorort_filtert_nicht(idx):
    a = idx.aufloesen("schulstraße", "", "II")
    assert (a.mehrdeutig, a.grund_mehrdeutig) == ("ja", "homonym_1936")


def test_unbekannter_vorort_ist_keine_information(idx):
    """"Frillenburg" steht nicht in der Tabelle → kein Filter, kein Widerspruch."""
    a = idx.aufloesen("bochumer straße", "Frillenburg", "II")
    assert (a.schl_nr, a.mehrdeutig) == ("00007", "nein")


def test_quellenprioritaet_konkordanz_vor_stadium(idx):
    """Derselbe Schlüssel aus Konkordanz und Stadium → Herkunft konkordanz."""
    a = idx.aufloesen("hermann-göring-straße", "", "I")
    assert (a.schl_nr, a.herkunft) == ("00003", "konkordanz")


def test_kuratiert_greift_auch_ohne_vorort_in_der_tabelle(idx):
    """Zuordnungszeile mit leerem Vorort gilt für jeden Vorort (Fallback (strasse, ""))."""
    a = idx.aufloesen("am lichtbogen", "Kray", "II")
    assert (a.strasse_heute, a.schl_nr, a.herkunft) == ("Bochumer Straße", "00007", "kuratiert")


def test_nicht_essen_1936_konstante():
    assert NICHT_ESSEN_1936 == frozenset({"Kettwig", "Burgaltendorf"})


def test_vorort_stadtteile_alle_ist_vereinigung():
    assert VORORT_STADTTEILE_ALLE == frozenset().union(*VORORT_STADTTEILE.values())
    assert "Katernberg" in VORORT_STADTTEILE_ALLE and "Nordviertel" not in VORORT_STADTTEILE_ALLE
