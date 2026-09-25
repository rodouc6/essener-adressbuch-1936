import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.gruppen import UNGEPRUEFT, fehlende_bezeichnungen, gruppe3, hauptgruppe, lade_hauptgruppen
from pipeline.lib.io import lies_csv


def test_hauptgruppe_und_gruppe3():
    assert hauptgruppe("B 21112") == "B21" and gruppe3("B 21112") == "B211"
    assert hauptgruppe("A 10200") == "A10" and gruppe3("A 10200") == "A102"
    assert hauptgruppe("94243") == "B94"                       # OhdAB-Zeile ohne Buchstaben (Bodybuilder/in)
    assert hauptgruppe("") == UNGEPRUEFT and gruppe3("B 2") == UNGEPRUEFT


def test_hauptgruppen_csv_deckt_den_ohdab_schnappschuss():
    W = pathlib.Path(__file__).resolve().parents[1]
    ohdab = {r["ohdab_id"]: r for r in lies_csv(W / "kuratierung" / "ohdab.csv")}
    hg = lade_hauptgruppen(lies_csv(W / "kuratierung" / "hauptgruppen.csv"))
    assert fehlende_bezeichnungen(ohdab, hg) == set()
    assert all(v["bezeichnung"] and v["kurz"] and v["quelle"] in ("KldB 2010", "OhdAB") for v in hg.values())
    assert fehlende_bezeichnungen({"x": {"gattung_id": "B 99999"}}, hg) == {"B99"}
