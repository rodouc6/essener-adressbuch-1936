"""Test für Stufe 03: Straßenauflösung mit Paartabelle und Vorschlagsliste."""
from pathlib import Path

from pipeline.lib.konkordanz import Strassenindex
from pipeline.lib.stufen import loese_strassen

FIX = Path(__file__).parent / "fixtures"


def test_loese_strassen():
    idx = Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv")
    zeilen = [
        {"id": "1", "strasse_norm": "bochumer straße", "Vorort": "Steele", "teil": "II", "Adresse": "Bochumer Str. 5"},
        {"id": "2", "strasse_norm": "bochumer straße", "Vorort": "Steele", "teil": "II", "Adresse": "Bochumer Str. 7"},
        {"id": "3", "strasse_norm": "stadtwiese", "Vorort": "", "teil": "I", "Adresse": "Stadtwiese 3"},
        {"id": "4", "strasse_norm": "archternbergstraße", "Vorort": "Kray", "teil": "II", "Adresse": "Archternbergstr. 1"},
    ]
    out, paare, vorschlaege = loese_strassen(zeilen, idx)
    assert out[0]["strasse_heute"] == "Bochumer Straße" and out[1]["herkunft"] == "heutig"
    assert out[2]["herkunft"] == "offen"
    p = {(x["strasse_norm"], x["vorort"], x["teil"]): x for x in paare}
    assert p[("bochumer straße", "Steele", "II")]["zeilen"] == "2"
    assert {v["strasse_norm"] for v in vorschlaege} == {"stadtwiese", "archternbergstraße"}
    v = [x for x in vorschlaege if x["strasse_norm"] == "archternbergstraße"][0]
    assert v["lemma_1"] == "Achternbergstraße" and v["zeilen"] == "1"
    assert vorschlaege[0]["zeilen"] >= vorschlaege[-1]["zeilen"]  # nach Zeilenzahl absteigend


def test_loese_strassen_leerer_strasse_norm():
    """Zeilen ohne Straßenname (strasse_norm=='') bleiben offen mit Enum-Neutralwerten statt leerem String."""
    idx = Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv")
    zeilen = [{"id": "1", "strasse_norm": "", "Vorort": "", "teil": "I", "Adresse": ""}]
    out, paare, _ = loese_strassen(zeilen, idx)
    assert out[0]["herkunft"] == "offen"
    assert out[0]["mehrdeutig"] == "nein"
    assert out[0]["zeitlich_abweichend"] == "nein"
    assert out[0]["strasse_heute"] == ""
    assert out[0]["grund_mehrdeutig"] == ""
    p = {(x["strasse_norm"], x["vorort"], x["teil"]): x for x in paare}
    assert p[("", "", "I")]["herkunft"] == "offen"


def test_paare_trennen_nach_teil():
    """Derselbe Name in Teil I (Kernstadt) und Teil II ist ein anderes Paar und geht
    anders aus: die Hermannstraße ohne Vorort wird in Teil I eindeutig (Kernstadt,
    Eltingstraße), in Teil II bleibt sie mehrdeutig (Katernberg kommt hinzu)."""
    idx = Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv")
    zeilen = [
        {"id": "1", "strasse_norm": "hermannstraße", "Vorort": "", "teil": "I", "Adresse": "Hermannstr. 1"},
        {"id": "2", "strasse_norm": "hermannstraße", "Vorort": "", "teil": "II", "Adresse": "Hermannstr. 2"},
    ]
    out, paare, _ = loese_strassen(zeilen, idx)
    assert len(paare) == 2
    assert (out[0]["mehrdeutig"], out[0]["strasse_heute"]) == ("nein", "Eltingstraße")
    assert out[1]["mehrdeutig"] == "ja" and "01282" in out[1]["kandidaten"]
