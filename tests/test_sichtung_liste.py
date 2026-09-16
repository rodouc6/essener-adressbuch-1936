from pathlib import Path

import pytest

from pipeline.lib.konkordanz import Strassenindex
from werkzeuge.sichtung_liste import gruppen, stand

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def idx():
    return Strassenindex(FIX / "strassen", FIX / "strassen_zuordnung.csv")


def paar(**kw):
    basis = dict(strasse_norm="", vorort="", teil="I", hausnr_bereich="", zeilen="1", beispiel="", strasse_heute="",
                 schl_nr="", stadtteil="", herkunft="offen", zeitlich_abweichend="nein", mehrdeutig="nein",
                 kandidaten="", grund_mehrdeutig="", teilstrecke_abgetrennt="nein", vorort_angenommen="nein",
                 nummer_unsicher="nein", schreibvariante="nein", strasse_angeglichen="")
    basis.update(kw)
    return basis


def test_gruppen_fassen_teile_zusammen_und_sortieren(idx):
    paare = [paar(strasse_norm="carlstraße", teil="I", zeilen="10", beispiel="Carlstr. 3", mehrdeutig="ja",
                  grund_mehrdeutig="name_erloschen", kandidaten="00001", herkunft="stadium"),
             paar(strasse_norm="carlstraße", teil="II", zeilen="5", beispiel="Carlstr. 9", mehrdeutig="ja",
                  grund_mehrdeutig="name_erloschen", kandidaten="00001", herkunft="stadium"),
             paar(strasse_norm="stadtwiese", zeilen="40", beispiel="Stadtwiese 1"),
             paar(strasse_norm="bochumer straße", vorort="Steele", zeilen="99", herkunft="heutig", strasse_heute="Bochumer Straße")]
    g = gruppen(paare, idx, lambda lemma: ["51.4", "7.0"] if lemma == "Karlstraße" else [], {})
    assert [e["strasse_norm"] for e in g] == ["stadtwiese", "carlstraße"]
    c = g[1]
    assert c["zeilen"] == 15 and c["teile"] == ["I", "II"] and c["gruende"] == ["name_erloschen"]
    assert c["kandidaten"][0]["lemma"] == "Karlstraße" and c["kandidaten"][0]["koord"] == ["51.4", "7.0"]
    assert any(s["name"] == "Carlstraße" for s in c["kandidaten"][0]["stadien"])
    assert c["vorort_schluessel"] == "Kernstadt" and "stand" not in c


def test_stand_aus_beiden_tabellen():
    st = stand([{"strasse_roh_norm": "stadtwiese", "vorort": "Kernstadt", "befund": "punkt", "lat": "51.46", "lon": "7.01",
                 "name_im_plan": "Stadtwiese", "stadtteil": "Stadtkern", "bemerkung": ""},
                {"strasse_roh_norm": "Carlstr.", "vorort": "", "befund": "nicht_gefunden", "lat": "", "lon": ""}],
               [{"strasse_roh_norm": "provinzialstraße", "vorort": "Kernstadt", "strasse_heute": "Gelsenkirchener Straße",
                 "schl_nr": "01004", "hausnr_von": "", "hausnr_bis": "", "beleg": "Plan"},
                {"strasse_roh_norm": "hermann-göring-straße", "vorort": "", "strasse_heute": "X", "schl_nr": "00001",
                 "hausnr_von": "1", "hausnr_bis": "9", "beleg": "Bereich"}])
    assert st[("stadtwiese", "Kernstadt")]["stand"] == "punkt"
    assert st[("carlstraße", "Kernstadt")]["stand"] == "nicht_gefunden"
    assert st[("provinzialstraße", "Kernstadt")]["stand"] == "zugeordnet"
    assert ("hermann-göring-straße", "") not in st


def test_gruppen_uebernehmen_stand(idx):
    st = {("stadtwiese", "Kernstadt"): {"stand": "punkt", "lat": "51.46", "lon": "7.01"}}
    g = gruppen([paar(strasse_norm="stadtwiese", zeilen="3")], idx, lambda l: [], st)
    assert g[0]["stand"] == "punkt" and g[0]["lat"] == "51.46"
