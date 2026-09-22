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


def test_rechtsform_nicht_bei_initialen():
    assert normalisiere("A. G. Müller", KAT) == "a g müller"
    assert normalisiere("Schmidt K. G.", KAT) == "schmidt kg"        # am Ende: Rechtsform
    assert normalisiere("K. G. Schmidt", KAT) == "k g schmidt"
    assert normalisiere("Gelsenk. Bergw. A.G., Abt. II", KAT).startswith("gelsenk bergwerks ag")
    assert rechtsform_anzeige("A. G. Müller") == "A. G. Müller"
    assert rechtsform_anzeige("Fried. Krupp, A. G.") == "Fried. Krupp AG"


from werkzeuge.eigentuemer_cluster import auto_name, cluster_id, clustere


def test_clustere_krupp_zusammen_pfarreien_getrennt():
    z = {"Fried. Krupp A.G.": 257, "Fried. Krupp A. G.": 181, "Fried. Krupp A.-G.": 79, "Friedr. Krupp A.G.": 40,
         "Fried. Krupp AG": 9, "Frau-Margarete-Krupp-Stiftung": 31,
         "Kath. Kirchengemeinde St. Josef": 12, "Kath. Kirchengemeinde St. Andreas": 8,
         "Stadt Essen": 1027}
    c = clustere(z, KAT)
    namen = {x["name"]: x for x in c}
    krupp = namen["Fried. Krupp AG"]
    assert [m[0] for m in krupp["mitglieder"]] == ["Fried. Krupp A.G.", "Fried. Krupp A. G.", "Fried. Krupp A.-G.", "Friedr. Krupp A.G.", "Fried. Krupp AG"]
    assert krupp["haeuser"] == 566 and krupp["aehnlichkeit"] == 1.0
    assert "Frau-Margarete-Krupp-Stiftung" in namen                     # nicht mit Krupp AG verschmolzen
    assert "Kath. Kirchengemeinde St. Josef" in namen and "Kath. Kirchengemeinde St. Andreas" in namen
    assert c[0]["name"] == "Stadt Essen"                                 # nach Häusern sortiert
    assert krupp["id"] == cluster_id("friedrich krupp ag") and len(krupp["id"]) == 10


def test_clustere_grenzfall_wird_vorschlag():
    # Gleicher Block „gewerkschaft“; Token-Set-Ähnlichkeit zwischen 0,75 und 0,92 → kein Merge, aber Vorschlag
    z = {"Gewerkschaft Viktoria Mathias": 79, "Gewerksch. Viktoria Mathias": 67, "Gewerkschaft Viktoria Mathias Schacht 3": 4}
    c = clustere(z, KAT)
    gross = next(x for x in c if x["haeuser"] == 146)
    klein = next(x for x in c if x["haeuser"] == 4)
    assert len(gross["mitglieder"]) == 2 and gross["vorschlag_fuer"] == ""
    assert klein["vorschlag_fuer"] == gross["id"]


def test_clustere_complete_linkage_keine_kette():
    # a~b und b~c ähnlich, a~c nicht → höchstens zwei zusammen, nie alle drei
    z = {"Bauverein Essen Nord": 5, "Bauverein Essen Nord West": 5, "Bauverein Essen West Süd": 5}
    c = clustere(z, KAT, schwelle=0.8, vorschlag_ab=0.5)
    assert max(len(x["mitglieder"]) for x in c) <= 2


def test_auto_name():
    assert auto_name([("Fried. Krupp A.G.", 257), ("Fried. Krupp A. G.", 181)]) == "Fried. Krupp AG"
    assert auto_name([("Stadt Essen", 3)]) == "Stadt Essen"
