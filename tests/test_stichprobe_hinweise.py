from pathlib import Path

import pytest

from pipeline.lib.konkordanz import Strassenindex
from werkzeuge.stichprobe_hinweise import hinweis, namensstadien, nummer_getroffen

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def idx():
    return Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv")


def test_nummer_getroffen_einfache_nummer():
    assert nummer_getroffen("262", "", "Lofus, 262, Rellinghauser Straße, Bergerhausen, Essen") is True


def test_nummer_getroffen_zusatz_fehlt_im_treffer():
    assert nummer_getroffen("89", "d", "89, Prosperstraße, Dellwig, Essen") is False


def test_nummer_getroffen_zusatz_im_treffer():
    assert nummer_getroffen("89", "d", "89d, Prosperstraße, Dellwig, Essen") is True


def test_namensstadien_chronologisch_mit_ende(idx):
    stadien = namensstadien(idx, "00003")
    assert [(s["name"], s["gueltig_ab"], s["gueltig_bis"]) for s in stadien] == [
        ("Bredeneyer Straße", "1900", "1933-07-13"),
        ("Horst-Wessel-Straße", "1933-07-13", "1945-06-01"),
        ("Bredeneyer Straße", "1945-06-01", ""),
    ]


def test_hinweis_bündelt_pipelinefelder_und_stadien(idx):
    zeile = {"stufe": "haus", "strasse_roh": "Horst-Wessel-Str.", "hausnr": "5", "hausnr_zusatz": "",
             "stadtteil": "Bredeney", "strasse_heute": "Bredeneyer Straße",
             "display_name": "5, Bredeneyer Straße, Bredeney, Essen"}
    geo = {"herkunft": "konkordanz", "mehrdeutig": "nein", "teilstrecke_abgetrennt": "nein",
           "zeitlich_abweichend": "nein", "zusatz_ignoriert": "", "osm_type": "way", "osm_id": "42",
           "grund_mehrdeutig": ""}
    h = hinweis(zeile, geo, ["00003"], idx)
    assert h["herkunft"] == "konkordanz"
    assert h["osm_type"] == "way" and h["osm_id"] == "42"
    assert h["nummer_getroffen"] is True
    assert h["strassen"] == [{"schl_nr": "00003", "lemma": "Bredeneyer Straße",
                              "stadtteile": "Bredeney; Werden",
                              "stadien": namensstadien(idx, "00003")}]


def test_hinweis_ohne_schluessel_liefert_leere_strassenliste(idx):
    zeile = {"stufe": "strasse", "strasse_roh": "X", "hausnr": "1", "hausnr_zusatz": "",
             "stadtteil": "", "strasse_heute": "", "display_name": "Xstraße, Essen"}
    h = hinweis(zeile, {}, [], idx)
    assert h["strassen"] == [] and h["nummer_getroffen"] is False
