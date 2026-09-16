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
    a = idx.aufloesen("horst-wessel-straße", "")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend) == ("Bredeneyer Straße", "konkordanz", "nein")


def test_konkordanz_nicht_eindeutig_bleibt_offen(idx):
    a = idx.aufloesen("hochstraße", "")
    assert a.herkunft == "konkordanz" and a.mehrdeutig == "ja" and a.strasse_heute == ""


def test_stadium_im_fenster(idx):
    # Gusestraße galt bis 1938-10-21 → Stadium gültig 1936 → stadium, nicht abweichend
    a = idx.aufloesen("gusestraße", "")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend) == ("Goosestraße", "stadium", "nein")


def test_stadium_ausserhalb_fenster_erloschener_name_wird_nicht_automatisch_vergeben(idx):
    # Carlstraße endete 1910. Dickhoff führt keine verschwundenen Straßen; ein 20 Jahre vor 1936
    # erloschener Name gehört eher einer verschwundenen Namensschwester (R4.2, Stichprobe r4:
    # 11 von 17 solcher Zuordnungen am Stadtplan 1935 widerlegt). → offen mit Kandidat als Vorschlag.
    a = idx.aufloesen("carlstraße", "")
    assert (a.strasse_heute, a.mehrdeutig, a.grund_mehrdeutig) == ("", "ja", "name_erloschen")
    assert "00001" in a.kandidaten


def test_heutiger_name_mit_spaeter_datierung_bleibt_automatisch(idx):
    # Oberdorfstraße gilt heute; Dickhoff datiert den Namen erst ab 1950. Das Buch führt ihn 1936
    # → die Kette ist unvollständig, nicht die Straße falsch: aufgelöst, aber zeitlich abweichend.
    a = idx.aufloesen("oberdorfstraße", "", "I")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend, a.mehrdeutig) == \
        ("Oberdorfstraße", "heutig", "ja", "nein")


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


def test_hermannstrasse_kernstadt_wird_eindeutig(idx):
    """Teil I ohne Vorort = Kernstadt: Katernberg und Fischlaken fallen über den
    Vorort-Filter weg, die Holsterhauser Hermannstraße (01569) endete schon 1902.
    Es bleibt die Kernstadt-Hermannstraße, die 1937 zur Eltingstraße wurde."""
    a = idx.aufloesen("hermannstraße", "", "I")
    assert (a.strasse_heute, a.schl_nr, a.herkunft, a.mehrdeutig) == ("Eltingstraße", "00770", "konkordanz", "nein")


def test_hermannstrasse_teil_ii_ohne_vorort_nimmt_kernstadt_an(idx):
    """Teil II ohne Vorort: kein Vorfilter, aber unter gleichwertigen Kandidaten entscheidet
    die Kernstadt (Runde 3) — sichtbar über vorort_angenommen=ja, alle Kandidaten bleiben notiert."""
    a = idx.aufloesen("hermannstraße", "", "II")
    assert (a.strasse_heute, a.schl_nr, a.mehrdeutig, a.vorort_angenommen) == ("Eltingstraße", "00770", "nein", "ja")
    assert {"01282", "00037", "00770"} <= set(a.kandidaten.split(";"))


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
    a = idx.aufloesen("horst-wessel-straße", "", "I")
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


# --- Fix-Runde 2: Fenster 1936, Teilstrecken, gueltig_bis ---------------------


def test_fenster_1936_altenessener_strasse(idx):
    """Nur Stadien, die irgendwann 1936 gelten, sind Homonyme: Tuttmannstraße und
    Viehofer Straße hießen bis 1933 so, Krablerstraße bis 1915 — bleibt 00053."""
    a = idx.aufloesen("altenessener straße", "", "I")
    assert (a.strasse_heute, a.schl_nr, a.herkunft) == ("Altenessener Straße", "00053", "heutig")
    assert (a.mehrdeutig, a.zeitlich_abweichend) == ("nein", "nein")


def test_fenster_1936_beide_haelften_des_jahres(idx):
    """01157 hieß bis 1936-01-15 Vogelheimer Straße, 03230 ab 1936-01-15 — beide
    gelten 1936, also echtes Homonym."""
    a = idx.aufloesen("vogelheimer straße", "", "I")
    assert (a.mehrdeutig, a.grund_mehrdeutig) == ("ja", "homonym_1936")
    assert set(a.kandidaten.split(";")) == {"03230", "01157"}


def test_homonym_ohne_teilstrecke_bleibt_mehrdeutig(idx):
    """Zwei Straßen hießen 1936 Hermann-Göring-Straße, keine davon Teilstrecke."""
    a = idx.aufloesen("hermann-göring-straße", "", "I")
    assert (a.mehrdeutig, a.grund_mehrdeutig) == ("ja", "homonym_1936")
    assert set(a.kandidaten.split(";")) == {"02656", "00433"}
    assert a.teilstrecke_abgetrennt == "nein"


def test_teilstrecke_schlaegt_nicht_als_homonym_durch(idx):
    """Am Richtenberg und Berzeliusstraße sind 1961/63 abgetrennte Teilstrecken
    der Frohnhauser Straße ("(tlw.)") — kein Homonym, 00930 wird aufgelöst."""
    a = idx.aufloesen("frohnhauser straße", "", "I")
    assert (a.strasse_heute, a.schl_nr, a.herkunft, a.mehrdeutig) == ("Frohnhauser Straße", "00930", "heutig", "nein")
    assert a.teilstrecke_abgetrennt == "ja"
    assert {"00238", "00348"} <= set(a.kandidaten.split(";"))


def test_ohne_teilstrecke_ist_das_feld_nein(idx):
    assert idx.aufloesen("bochumer straße", "Steele", "II").teilstrecke_abgetrennt == "nein"


def test_gueltig_bis_ueberspringt_rueckdatierte_stadien(idx):
    """03215 (Viehofer Straße) hat nicht chronologische Stadiumsnummern
    (Stadium 5 = 1945, Stadium 6 = 1915). Das Stadium "Altenessener Straße"
    (1826) endet trotzdem 1933-04-20 und gilt damit nicht 1936."""
    st = {s["stadium"]: s for s in idx.stadien_je_strasse["03215"]}
    assert st["3"]["gueltig_bis"] == "1933-04-20"
    assert st["5"]["gueltig_bis"] == "9999"
    assert st["4"]["gueltig_bis"] == "1945-05-15"


def test_halb_datiertes_stadium_gilt_als_datiert(idx):
    """02266 trägt "Frohnhauser Straße" ohne Anfangsdatum, aber mit bekanntem Ende
    (1911-04-21) — der Name galt 1936 nachweislich nicht."""
    a = idx.aufloesen("frohnhauser straße", "", "I")
    assert "02266" not in a.kandidaten and a.schl_nr != "02266"


# --- Runde 3 (2026-09-15, nach Stichprobe): Teilstrecken-Varianten, Kernstadt, Nummernbereiche ---

def test_teilstrecke_auch_mit_zusatz_umb(idx):
    """„II. Hagen (tlw. Umb.)“ ist eine Teilstrecke, kein Doppelname."""
    a = idx.aufloesen("ii. hagen", "", "I")
    assert (a.schl_nr, a.mehrdeutig, a.teilstrecke_abgetrennt) == ("00014", "nein", "ja")


def test_burgaltendorf_zaehlt_nicht_als_kernstadt(idx):
    """Ein Kandidat in Burgaltendorf/Überruhr kann keine Kernstadt-Adresse aus Teil I sein."""
    a = idx.aufloesen("charlottenstraße", "", "I")
    assert (a.strasse_heute, a.schl_nr, a.mehrdeutig) == ("Dohmanns Kamp", "00017", "nein")


def test_kernstadt_entscheidet_in_teil_ii_mit_flag(idx):
    a = idx.aufloesen("steeler straße", "", "II")
    assert (a.schl_nr, a.mehrdeutig, a.vorort_angenommen) == ("00018", "nein", "ja")


def test_kernstadt_in_teil_i_ohne_flag(idx):
    a = idx.aufloesen("steeler straße", "", "I")
    assert (a.schl_nr, a.vorort_angenommen) == ("00018", "nein")


def test_vorort_kray_schlaegt_kernstadtannahme(idx):
    a = idx.aufloesen("steeler straße", "Kray", "II")
    assert (a.schl_nr, a.vorort_angenommen) == ("00019", "nein")


def test_kuratierter_hausnummernbereich(idx):
    a = idx.aufloesen("hermann-göring-straße", "", "I", hausnr="100")
    assert (a.schl_nr, a.herkunft, a.nummer_unsicher) == ("02656", "kuratiert", "nein")
    b = idx.aufloesen("hermann-göring-straße", "", "I", hausnr="400")
    assert (b.schl_nr, b.herkunft, b.nummer_unsicher) == ("00433", "kuratiert", "ja")


def test_hausnummernbereich_ohne_nummer_faellt_auf_automatik_zurueck(idx):
    a = idx.aufloesen("hermann-göring-straße", "", "I", hausnr="")
    assert a.herkunft != "kuratiert"


def test_bereichsschluessel(idx):
    assert idx.bereich("hermann-göring-straße", "", "100") == "1-323"
    assert idx.bereich("hermann-göring-straße", "", "400") == "324-"
    assert idx.bereich("hermann-göring-straße", "", "") == ""
    assert idx.bereich("bochumer straße", "Steele", "5") == ""


def test_kernstadt_zeile_greift_nur_ohne_vorort(idx):
    """vorort="Kernstadt" in der Zuordnungstabelle: gilt für Zeilen ohne Vorort, nicht als Platzhalter."""
    a = idx.aufloesen("karlstraße", "", "I")
    assert (a.schl_nr, a.herkunft) == ("00001", "kuratiert")
    b = idx.aufloesen("karlstraße", "Kray", "I")
    assert b.herkunft != "kuratiert"


def test_vorort_filter_greift_vor_dem_zeitfenster_rueckfall(idx):
    # Altendorfer Straße (Kernstadt, 00050) gilt bei Dickhoff nur bis zur Teil-Umbenennung 1933
    # → "weit". Die Horster Altendorfer Straße (01371) gilt 1936, liegt aber im Vorort Steele.
    # Teil I ohne Vorort darf nicht am Vorort-Kandidaten scheitern, sondern muss auf den
    # weit datierten Kernstadt-Kandidaten zurückfallen — gekennzeichnet als zeitlich abweichend.
    a = idx.aufloesen("altendorfer straße", "", "I")
    assert (a.strasse_heute, a.schl_nr, a.mehrdeutig, a.zeitlich_abweichend) == \
        ("Altendorfer Straße", "00050", "nein", "ja")


def test_vorort_filter_vor_zeitfenster_mit_vorort(idx):
    a = idx.aufloesen("altendorfer straße", "Steele", "I")
    assert (a.schl_nr, a.zeitlich_abweichend) == ("01371", "nein")


def test_widerspruch_bleibt_wenn_auch_weite_kandidaten_nicht_passen(idx):
    a = idx.aufloesen("altendorfer straße", "Kray", "I")
    assert a.mehrdeutig == "ja" and a.grund_mehrdeutig == "vorort_widerspruch"


def test_rueckfall_ist_gestuft_weit_vor_ausserhalb(idx):
    # Schölerpad (02805) hieß bis 1896 ebenfalls Altendorfer Straße ("außerhalb"). Der weit
    # datierte Kandidat 00050 (bis 1933) ist der nähere Rückfall und darf nicht mit dem
    # außerhalb datierten zum Homonym verschmelzen.
    a = idx.aufloesen("altendorfer straße", "", "I")
    assert (a.schl_nr, a.mehrdeutig, a.zeitlich_abweichend) == ("00050", "nein", "ja")


# --- Runde 5: Schreibvarianten ----------------------------------------------------
def test_schreibvariante_wird_angeglichen_und_gekennzeichnet(idx):
    a = idx.aufloesen("klementinenstraße", "", "I")
    assert (a.strasse_heute, a.schl_nr, a.herkunft) == ("Clementinenstraße", "00021", "heutig")
    assert (a.schreibvariante, a.strasse_angeglichen) == ("ja", "clementinenstraße")


def test_exakter_name_ist_keine_schreibvariante(idx):
    a = idx.aufloesen("clementinenstraße", "", "I")
    assert (a.schreibvariante, a.strasse_angeglichen) == ("nein", "")


def test_schreibvariante_durchlaeuft_vorort_filter(idx):
    # Clementinenstraße liegt im Südviertel; Vorort Kray widerspricht → bleibt Widerspruch, kein Treffer
    a = idx.aufloesen("klementinenstraße", "Kray", "I")
    assert a.mehrdeutig == "ja" and a.grund_mehrdeutig == "vorort_widerspruch" and a.schreibvariante == "ja"


def test_schreibvariante_nur_bei_eindeutigem_schluessel(idx):
    # "mayerstraße" träfe auf Stufe 2 Maierstraße und Mairstraße zugleich → nicht raten, bleibt offen
    a = idx.aufloesen("mayerstraße", "", "I")
    assert a.herkunft == "offen" and a.schreibvariante == "nein"


def test_schreibvariante_greift_nicht_vor_exaktem_treffer(idx):
    # Karlstraße existiert exakt → keine Angleichung an etwas anderes
    a = idx.aufloesen("karlstraße", "", "I")
    assert a.schreibvariante == "nein"


# --- Stadtplan 1935 (kuratierung/strassen_1935.csv) --------------------------
@pytest.fixture
def idx_plan():
    return Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv", FIX / "strassen_1935.csv")


def test_stadtplan_1935_verortet_verschwundene_strasse(idx_plan):
    a = idx_plan.aufloesen("stadtwiese", "", "I")
    assert (a.strasse_heute, a.schl_nr, a.stadtteil, a.herkunft, a.mehrdeutig) == \
        ("", "", "Stadtkern", "stadtplan_1935", "nein")


def test_stadtplan_1935_nicht_gefunden_bleibt_offen(idx_plan):
    a = idx_plan.aufloesen("carlstraße", "", "I")
    assert a.herkunft != "stadtplan_1935" and a.strasse_heute == ""


def test_stadtplan_1935_kernstadt_gilt_nur_ohne_vorort(idx_plan):
    a = idx_plan.aufloesen("stadtwiese", "Kray", "II")
    assert a.herkunft == "offen"


def test_stadtplan_1935_schlaegt_automatik(idx_plan):
    # Bochumer Straße Steele wäre automatisch "heutig"; der vom Menschen gesetzte Punkt gewinnt.
    a = idx_plan.aufloesen("bochumer straße", "Steele")
    assert a.herkunft == "stadtplan_1935" and a.stadtteil == "Steele"


def test_zuordnungstabelle_geht_dem_stadtplan_vor(idx_plan):
    a = idx_plan.aufloesen("hstr.", "Kray")
    assert a.herkunft == "kuratiert" and a.schl_nr == "00009"


def test_ohne_plan_tabelle_wie_bisher(idx):
    assert idx.aufloesen("stadtwiese", "", "I").herkunft == "offen"


def test_lade_stadtplan_1935_nur_punkte(tmp_path):
    from pipeline.lib.konkordanz import lade_stadtplan_1935
    punkte = lade_stadtplan_1935(FIX / "strassen_1935.csv")
    assert ("stadtwiese", "Kernstadt") in punkte and ("carlstraße", "Kernstadt") not in punkte
    assert lade_stadtplan_1935(tmp_path / "fehlt.csv") == {}


# --- R6.3: heutiger Name, den Dickhoff erst nach 1937 datiert -----------------------------
def test_heutiger_name_spaeter_mit_anderem_namen_1936_bleibt_offen(idx):
    # Berzeliusstraße gilt heute, laut Dickhoff erst seit 1961; 1936 hieß die Straße Frohnhauser
    # Straße (tlw.). Die Berzeliusstraße des Buches lag also woanders (Stichprobe r6: 10 von 10
    # solcher Fälle am Plan 1935 widerlegt) → nicht automatisch, Kandidat als Vorschlag.
    a = idx.aufloesen("berzeliusstraße", "", "I")
    assert (a.strasse_heute, a.mehrdeutig, a.grund_mehrdeutig, a.herkunft) == ("", "ja", "name_spaeter", "heutig")
    assert "00024" in a.kandidaten


def test_heutiger_name_spaeter_schreibvariante_zaehlt_nicht_als_anderer_name(idx):
    # Brahmkampstraße → Bramkampstraße 1938: derselbe Name in anderer Schreibung, kein Widerspruch.
    a = idx.aufloesen("bramkampstraße", "", "I")
    assert (a.strasse_heute, a.herkunft, a.zeitlich_abweichend, a.mehrdeutig) == \
        ("Bramkampstraße", "heutig", "ja", "nein")


def test_anderer_name_1936_aehnliche_aber_verschiedene_namen():
    import difflib
    from pipeline.lib.konkordanz import SCHREIBVARIANTE_AEHNLICHKEIT
    r = lambda a, b: difflib.SequenceMatcher(None, a, b).ratio()
    assert r("brahmkampstraße", "bramkampstraße") >= SCHREIBVARIANTE_AEHNLICHKEIT
    assert r("raffaelstraße", "rafaelstraße") >= SCHREIBVARIANTE_AEHNLICHKEIT
    assert r("marienstraße", "martinstraße") < SCHREIBVARIANTE_AEHNLICHKEIT
    assert r("gartenstraße", "pausstraße") < SCHREIBVARIANTE_AEHNLICHKEIT
