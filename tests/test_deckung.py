import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.deckung import deckung, familie_von, rubrik_familie


def b(schreibweise, nennungen, beruf, stellung, status=""):
    return {"schreibweise": schreibweise, "nennungen": str(nennungen), "beruf": beruf, "stellung": stellung, "status": status}


def test_familie_von_faltet_meister_gewerbe_und_weibliche_form():
    assert familie_von("Schneidermeister") == "schneider"
    assert familie_von("Schneidermstrin.") == "schneider"
    assert familie_von("Schneiderei") == "schneider"
    assert familie_von("Schneiderin") == "schneiderin"          # weibliche Form erst in deckung() gefaltet
    assert familie_von("Tischler") == "schreiner"               # Synonym
    assert familie_von("Anstreicher") == "maler"


def test_rubrik_familie_nimmt_erstes_wort_und_schliesst_bedarf_aus():
    assert rubrik_familie("Schneider für Herren") == "schneider"
    assert rubrik_familie("Uhrmacher und Uhrenhandlung") == "uhrmacher"
    assert rubrik_familie("Metzger (Groß-)") == "metzger"
    assert rubrik_familie("Maurermeister") == "maurer"
    assert rubrik_familie("Schneiderbedarf") is None
    assert rubrik_familie("Bäckereimaschinen und -geräte") is None
    assert rubrik_familie("Friseurfachschule") is None


def test_deckung_rechnet_luecke_und_empfehlung():
    berufe = [
        b("Friseur", 700, "Friseur", "arbeiter"), b("Friseuse", 80, "Friseur", "arbeiter"),
        b("Friseurgesch.", 250, "Friseur", "selbstaendige", "gewerbe"), b("Friseurmstr.", 30, "Friseurmeister", "selbstaendige"),
        b("Friseur a. D.", 5, "Friseur", "ohne_erwerb", "ruhestand"),
        b("Schlosser", 7000, "Schlosser", "arbeiter"), b("Schlossermstr.", 200, "Schlossermeister", "selbstaendige"),
        b("Schneiderin", 600, "Schneiderin", "unbestimmt"), b("Schneidermstr.", 650, "Schneidermeister", "selbstaendige"),
        b("Bergmann", 28000, "Bergmann", "arbeiter"),   # keine Inhaberform, keine Rubrik → nicht in der Tabelle
    ]
    gewerbe = [
        {"rubrik": "Friseur", "betriebe": "560"}, {"rubrik": "Friseur für Damen", "betriebe": "97"}, {"rubrik": "Friseurbedarf", "betriebe": "10"},
        {"rubrik": "Schlosser", "betriebe": "111"},
        {"rubrik": "Schneider für Herren", "betriebe": "900"}, {"rubrik": "Schneiderin", "betriebe": "175"},
    ]
    d = {r["familie"]: r for r in deckung(berufe, gewerbe)}
    assert set(d) == {"friseur", "schlosser", "schneider"}
    f = d["friseur"]
    assert (f["offen"], f["inhaber"], f["betriebe"], f["luecke"]) == (780, 280, 657, 377)
    assert f["rubriken"] == ["Friseur", "Friseur für Damen"]
    assert f["quote"] == round(377 / 780, 3) and f["empfehlung"] == "unbestimmt"
    assert sorted(f["schreibweisen_offen"]) == ["Friseur", "Friseuse"]
    s = d["schlosser"]
    assert (s["offen"], s["inhaber"], s["betriebe"], s["luecke"], s["empfehlung"]) == (7000, 200, 111, 0, "arbeiter")
    sch = d["schneider"]                                       # „Schneiderin“ zur Familie „schneider“ gefaltet
    assert (sch["offen"], sch["inhaber"], sch["betriebe"], sch["luecke"]) == (600, 650, 1075, 425)
    assert sch["empfehlung"] == "unbestimmt"


def test_deckung_ohne_offene_nennungen():
    berufe = [b("Bäckermstr.", 800, "Bäckermeister", "selbstaendige")]
    gewerbe = [{"rubrik": "Bäcker", "betriebe": "560"}]
    (r,) = deckung(berufe, gewerbe)
    assert (r["offen"], r["quote"], r["empfehlung"]) == (0, None, "")


def test_deckung_laesst_kleinstfamilien_ohne_inhaberform_weg():
    berufe = [b("Steuerberatung", 5, "Steuerberatung", "unbestimmt"), b("Dekorateur", 105, "Dekorateur", "arbeiter"),
              b("Maurer", 2400, "Maurer", "arbeiter"), b("Maurermstr.", 60, "Maurermeister", "selbstaendige")]
    gewerbe = [{"rubrik": "Steuerberatung", "betriebe": "80"}, {"rubrik": "Dekorateur u. Dekorationsgeschäft", "betriebe": "143"}]
    assert [r["familie"] for r in deckung(berufe, gewerbe)] == ["dekorateur"]   # Maurer: keine Rubrik → nicht beurteilbar


def test_skript_schreibt_json_und_markdown(tmp_path):
    import csv, json
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "werkzeuge"))
    import handwerk_deckung
    (tmp_path / "kuratierung").mkdir()
    with open(tmp_path / "kuratierung" / "berufe.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["schreibweise", "nennungen", "beruf", "status", "stellung"]); w.writeheader()
        w.writerow(b("Friseur", 700, "Friseur", "arbeiter")); w.writerow(b("Friseurmstr.", 30, "Friseurmeister", "selbstaendige"))
    with open(tmp_path / "kuratierung" / "gewerbe.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rubrik", "betriebe"]); w.writeheader(); w.writerow({"rubrik": "Friseur", "betriebe": "560"})
    (tmp_path / "docs").mkdir()
    zeilen = handwerk_deckung.main(["--wurzel", str(tmp_path)])
    assert [r["familie"] for r in zeilen] == ["friseur"]
    j = json.loads((tmp_path / "build" / "handwerk_deckung.json").read_text())
    assert j["schreibweisen"] == {"Friseur": "friseur"} and j["familien"]["friseur"]["luecke"] == 530
    md = (tmp_path / "docs" / "stellung_deckung.md").read_text()
    assert "| friseur | 700 | 30 | 560 | 530 | 76% | unbestimmt | Friseur | Friseur |" in md
