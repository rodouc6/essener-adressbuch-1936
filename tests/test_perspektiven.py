import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.perspektiven import kapitel_index, lade_kapitel, pruefe_kapitel

GUT = {"id": "wohneigentum", "reihenfolge": 1, "titel": "Wohneigentum 1936", "untertitel": "privat, industriell, genossenschaftlich, städtisch, kirchlich",
       "freigegeben": False, "einleitung": "Lorem ipsum.", "quellen": ["Teil II"], "grenzen": "Geprüft sind {besitz_geprueft} Adressen.",
       "schritte": [{"id": "anteile", "text": "Lorem.", "beschreibung": "Balken der acht Klassen.", "hervorheben": [],
                     "ansicht": {"daten": "besitz", "ebene": "stadtteil", "form": "balken", "gruppen": [{"name": "Privat", "aus": ["privatperson"], "farbe": "#e69f00"}],
                                 "kaufleute": "unbestimmt", "unsicher": False, "mass": "anteil", "bezug": "Privat", "min_n": 200, "filter": {}, "karte": None}}]}


def test_gueltiges_kapitel():
    assert pruefe_kapitel(GUT) == []


def test_fehler_werden_benannt():
    k = json.loads(json.dumps(GUT))
    k["schritte"][0]["ansicht"]["daten"] = "geld"; k["schritte"][0]["ansicht"]["bezug"] = "Fremd"; del k["titel"]
    k["schritte"].append({"id": "anteile", "text": "", "beschreibung": "", "hervorheben": [], "ansicht": dict(GUT["schritte"][0]["ansicht"], mass="dichte")})
    f = pruefe_kapitel(k)
    assert any("titel" in x for x in f) and any("daten" in x for x in f) and any("bezug" in x for x in f)
    assert any("doppelt" in x for x in f) and any("dichte" in x for x in f)


def test_lade_und_index(tmp_path):
    (tmp_path / "b.json").write_text(json.dumps(dict(GUT, id="b", reihenfolge=2)), encoding="utf-8")
    (tmp_path / "a.json").write_text(json.dumps(GUT), encoding="utf-8")
    ks = lade_kapitel(tmp_path)
    assert [k["id"] for k in ks] == ["wohneigentum", "b"]
    assert kapitel_index(ks)[0] == {"id": "wohneigentum", "titel": "Wohneigentum 1936", "untertitel": GUT["untertitel"], "freigegeben": False, "reihenfolge": 1}


def test_echte_kapitel_sind_gueltig():
    W = pathlib.Path(__file__).resolve().parents[1]
    for k in lade_kapitel(W / "kuratierung" / "perspektiven"):
        assert pruefe_kapitel(k) == [], k["id"]


def test_gruppen_wie_wird_aufgeloest(tmp_path):
    k = json.loads(json.dumps(GUT))
    k["schritte"].append({"id": "anteile2", "text": "Lorem.", "beschreibung": "", "hervorheben": [],
                           "ansicht": dict(GUT["schritte"][0]["ansicht"], gruppen="wie:anteile")})
    (tmp_path / "k.json").write_text(json.dumps(k), encoding="utf-8")
    geladen = lade_kapitel(tmp_path)[0]
    aufgeloest = geladen["schritte"][1]["ansicht"]["gruppen"]
    assert aufgeloest == GUT["schritte"][0]["ansicht"]["gruppen"]
    assert pruefe_kapitel(geladen) == []


def test_gruppen_wie_unbekannte_id_wirft():
    k = json.loads(json.dumps(GUT))
    k["schritte"][0]["ansicht"]["gruppen"] = "wie:nichtvorhanden"
    import pytest
    with pytest.raises(KeyError):
        from pipeline.lib.perspektiven import _loese_gruppen_auf
        _loese_gruppen_auf(k)
