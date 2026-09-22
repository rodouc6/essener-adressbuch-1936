import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from werkzeuge.eigentuemer_cluster import lade_katalog, normalisiere, rechtsform_anzeige

W = pathlib.Path(__file__).resolve().parents[1]
KAT = lade_katalog(W / "kuratierung" / "eigentuemer_abkuerzungen.csv")


def test_rechtsformen():
    for s in ("Fried. Krupp A.G.", "Fried. Krupp A. G.", "Fried. Krupp A.-G.", "Fried. Krupp AG.", "Fried. Krupp, A. -G.", "Fried. Krupp AG"):
        assert normalisiere(s, KAT) == "friedrich krupp ag", s
    assert normalisiere("Bau- u. Sparverein e.G.m.b.H.", KAT) == normalisiere("Bau- u. Sparverein e. G. m. b. H.", KAT)
    assert normalisiere("Wohnungsbau G.m.b.H.", KAT).endswith(" gmbh")
    assert normalisiere("Kath. Kirchengemeinde St. Josef", KAT) == "kath kirchengemeinde st josef"


def test_abkuerzungen_und_ver_regel():
    assert normalisiere("Gew. Math. Stinnes", KAT) == "gewerkschaft math stinnes"
    assert normalisiere("Gewerksch. Viktoria Mathias", KAT) == normalisiere("Gewerkschaft Viktoria Mathias", KAT)
    assert normalisiere("Ver. Stahlw. A.G.", KAT) == normalisiere("Vereinigte Stahlwerke A.-G.", KAT) == "vereinigte stahlwerke ag"
    # „Ver.“ ohne Firmenwort bleibt „ver“ (kann „Verein“ heißen)
    assert normalisiere("Ver. Kirchengemeinde", KAT) == "ver kirchengemeinde"
    # „Verein“ ohne Punkt ist keine Abkürzung
    assert normalisiere("Bergbau Verein Essen", KAT) == "bergbau verein essen"


def test_kompositum():
    assert normalisiere("Mülh. Bergw. Verein", KAT) == normalisiere("Mülheimer Bergwerksverein", KAT) == "mülheimer bergwerksverein"
    assert normalisiere("Ess. Bergw. Verein König Wilhelm", KAT) == "essener bergwerksverein könig wilhelm"


def test_rechtsform_anzeige():
    assert rechtsform_anzeige("Fried. Krupp A. -G.") == "Fried. Krupp AG"
    assert rechtsform_anzeige("Fried. Krupp, A.G.") == "Fried. Krupp AG"
    assert rechtsform_anzeige("Sparverein e. G. m. b. H.") == "Sparverein eGmbH"
    assert rechtsform_anzeige("Stadt Essen") == "Stadt Essen"
