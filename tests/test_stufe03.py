"""Test für Stufe 03: Straßenauflösung mit Paartabelle und Vorschlagsliste."""
from pathlib import Path

from pipeline.lib.konkordanz import Strassenindex
from pipeline.lib.stufen import loese_strassen

FIX = Path(__file__).parent / "fixtures"


def test_loese_strassen():
    idx = Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv")
    zeilen = [
        {"id": "1", "strasse_norm": "bochumer straße", "Vorort": "Steele", "Adresse": "Bochumer Str. 5"},
        {"id": "2", "strasse_norm": "bochumer straße", "Vorort": "Steele", "Adresse": "Bochumer Str. 7"},
        {"id": "3", "strasse_norm": "stadtwiese", "Vorort": "", "Adresse": "Stadtwiese 3"},
        {"id": "4", "strasse_norm": "archternbergstraße", "Vorort": "Kray", "Adresse": "Archternbergstr. 1"},
    ]
    out, paare, vorschlaege = loese_strassen(zeilen, idx)
    assert out[0]["strasse_heute"] == "Bochumer Straße" and out[1]["herkunft"] == "heutig"
    assert out[2]["herkunft"] == "offen"
    p = {(x["strasse_norm"], x["vorort"]): x for x in paare}
    assert p[("bochumer straße", "Steele")]["zeilen"] == "2"
    assert {v["strasse_norm"] for v in vorschlaege} == {"stadtwiese", "archternbergstraße"}
    v = [x for x in vorschlaege if x["strasse_norm"] == "archternbergstraße"][0]
    assert v["lemma_1"] == "Achternbergstraße" and v["zeilen"] == "1"
    assert vorschlaege[0]["zeilen"] >= vorschlaege[-1]["zeilen"]  # nach Zeilenzahl absteigend
