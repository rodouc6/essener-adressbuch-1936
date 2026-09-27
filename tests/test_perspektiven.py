import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.perspektiven import kapitel_index, lade_kapitel, pruefe_kapitel

GUT = {"id": "wohneigentum", "reihenfolge": 1, "titel": "Wohneigentum 1936", "untertitel": "privat, industriell, genossenschaftlich, städtisch, kirchlich",
       "freigegeben": False, "einleitung": "Lorem ipsum.", "quellen": ["Teil II"], "grenzen": "Geprüft sind {besitz_geprueft} Adressen.",
       "datenbasis": "{besitz_geprueft} von {adressen} Adressen mit Besitzklasse.", "datenbasis_schritt": "besitz",
       "ausschluss": "ohne Eigentümerangabe oder Eigentümer nicht zugeordnet",
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


TRICHTER = {"daten": "kennzahlen", "form": "trichter",
            "stufen": [{"name": "Zeilen", "aus": "eintraege", "farbe": "#94a3b8"},
                       {"name": "verortet", "aus": "verortet", "farbe": "#1d4ed8",
                        "segmente": [{"name": "hausgenau", "aus": "stufe_haus", "farbe": "#1d4ed8"},
                                     {"name": "per Regel", "aus": "stufe_strasse", "farbe": "#60a5fa", "muster": "schraffur"}]}],
            "erklaerungen": {"verortet": "Zeilen mit Punkt auf der Karte."}}
KAP0 = {"id": "datenbasis", "reihenfolge": 0, "titel": "Die Datenbasis", "untertitel": "Vom Buch zur Karte", "freigegeben": False,
        "einleitung": "x", "quellen": [], "grenzen": "y", "datenbasis": "", "datenbasis_schritt": "", "ausschluss": "",
        "schritte": [{"id": "weg", "text": "t", "beschreibung": "b", "hervorheben": [], "ansicht": TRICHTER}]}


def test_trichter_ansicht_gueltig():
    from pipeline.lib.perspektiven import pruefe_ansicht
    assert pruefe_ansicht(TRICHTER, "S") == []
    assert pruefe_kapitel(KAP0) == []          # Kapitel 0 braucht keine datenbasis/ausschluss-Texte


def test_trichter_fehler():
    from pipeline.lib.perspektiven import pruefe_ansicht
    assert any("nur mit form trichter" in x for x in pruefe_ansicht(dict(TRICHTER, form="balken"), "S"))
    assert any("nur mit form trichter" in x for x in pruefe_ansicht(dict(GUT["schritte"][0]["ansicht"], form="trichter"), "S"))
    assert any("ohne stufen" in x for x in pruefe_ansicht(dict(TRICHTER, stufen=[]), "S"))
    doppelt = json.loads(json.dumps(TRICHTER)); doppelt["stufen"][1]["segmente"][0]["name"] = "Zeilen"
    assert any("doppelt" in x for x in pruefe_ansicht(doppelt, "S"))
    muster = json.loads(json.dumps(TRICHTER)); muster["stufen"][1]["segmente"][1]["muster"] = "punkte"
    assert any("muster" in x for x in pruefe_ansicht(muster, "S"))
    unvoll = json.loads(json.dumps(TRICHTER)); del unvoll["stufen"][0]["aus"]
    assert any("unvollständig" in x for x in pruefe_ansicht(unvoll, "S"))


def test_fachkapitel_braucht_datenbasis_und_ausschluss():
    k = json.loads(json.dumps(GUT)); del k["datenbasis"]; del k["ausschluss"]; del k["datenbasis_schritt"]
    f = pruefe_kapitel(k)
    assert any("datenbasis" in x for x in f) and any("ausschluss" in x for x in f)
    k = json.loads(json.dumps(GUT)); k["datenbasis"] = ""
    assert any("datenbasis" in x for x in pruefe_kapitel(k))         # leer ist bei Fachkapiteln ein Fehler


def test_kennzahlen_bezug():
    from pipeline.lib.perspektiven import pruefe_kennzahlen_bezug, stufen_schluessel
    assert stufen_schluessel(KAP0) == ["eintraege", "verortet", "stufe_haus", "stufe_strasse"]
    assert pruefe_kennzahlen_bezug(KAP0, {"eintraege": 1, "verortet": 1, "stufe_haus": 1, "stufe_strasse": 1}) == []
    f = pruefe_kennzahlen_bezug(KAP0, {"eintraege": 1})
    assert any("verortet" in x for x in f) and any("stufe_haus" in x for x in f)
    assert pruefe_kennzahlen_bezug(GUT, {}) == []                   # keine Trichter → nichts zu prüfen
