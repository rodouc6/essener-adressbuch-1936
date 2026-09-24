import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.layout import beeswarm, packe_gruppen, packe_kreise, radius, ueberlappen


def kreise(n, seed_werte=None):
    werte = seed_werte or [((i * 7919) % 97) + 1 for i in range(n)]
    return [dict(id=f"k{i}", r=radius(w, max(werte))) for i, w in enumerate(werte)]


def test_radius_flaeche_proportional():
    assert radius(100, 100) == 60.0 and abs(radius(25, 100) - 30.0) < 1e-9 and radius(0, 100) == 2.0


def test_packung_deterministisch_und_ueberlappungsfrei():
    k = kreise(300)
    a, b = packe_kreise(k), packe_kreise([dict(x) for x in k])
    assert [x["id"] for x in a] == [x["id"] for x in k]
    assert [(x["x"], x["y"]) for x in a] == [(x["x"], x["y"]) for x in b]
    assert ueberlappen(a) == []
    assert all(math.hypot(x["x"], x["y"]) < 1500 for x in a)          # kompakt, nicht in einer Reihe
    assert packe_kreise([]) == []


def test_gruppen_packung():
    k = [dict(x, gruppe=("a", "b", "c")[i % 3]) for i, x in enumerate(kreise(90))]
    kr, gr = packe_gruppen(k)
    assert ueberlappen(kr) == [] and {g["gruppe"] for g in gr} == {"a", "b", "c"}
    for g in gr:                                                       # jeder Kreis liegt in seinem Gruppenkreis
        for x in kr:
            if x["gruppe"] == g["gruppe"]:
                assert math.hypot(x["x"] - g["x"], x["y"] - g["y"]) + x["r"] <= g["r"] + 1e-6
    assert ueberlappen([dict(id=g["gruppe"], r=g["r"], x=g["x"], y=g["y"]) for g in gr]) == []


def test_beeswarm_spalten():
    k = [dict(x, spalte=("helfer", "fachlich", "hochkomplex")[i % 3]) for i, x in enumerate(kreise(120))]
    out = beeswarm(k, ["helfer", "fachlich", "hochkomplex"], breite=80.0)
    assert ueberlappen(out) == []
    for x in out:
        mitte = ["helfer", "fachlich", "hochkomplex"].index(x["spalte"]) * 200.0
        assert abs(x["x"] - mitte) + x["r"] <= 80.0 + 1e-6               # bleibt im Band
    assert out == beeswarm([dict(x) for x in k], ["helfer", "fachlich", "hochkomplex"], breite=80.0)


def test_ueberlappen_findet_paare():
    assert ueberlappen([dict(id="a", r=5, x=0, y=0), dict(id="b", r=5, x=8, y=0), dict(id="c", r=1, x=50, y=0)]) == [("a", "b")]


def test_beeswarm_zu_grosser_kreis_wirft_wertfehler():
    k = [dict(id="a", r=90.0, spalte="s")]
    try:
        beeswarm(k, ["s"], breite=80.0)
    except ValueError:
        pass
    else:
        raise AssertionError("erwarteter ValueError blieb aus")
