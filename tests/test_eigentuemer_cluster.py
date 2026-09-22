import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.eigentuemer import AUTOMATIK
from pipeline.lib.io import lies_csv
from werkzeuge.eigentuemer_cluster import (
    aktualisiere_kuratierung, auto_name, cluster_id, clustere, lade_katalog,
    main, normalisiere, rechtsform_anzeige, sammle, vorschlagszeilen,
)

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


def test_clustere_zahlen_waechter_blockiert_merge():
    # F3: unterschiedliche Hausnummern/Zählungen dürfen trotz hoher Ähnlichkeit nicht verschmelzen —
    # echte Funde: „Adolf-Hitler-Straße 19“ vs. „… 81“ (0,95) und „Ev. Schule“ vs. „Ev. Schule II“.
    z1 = {"Adolf-Hitler-Straße 19": 6, "Adolf-Hitler-Straße 81": 5}
    c1 = clustere(z1, KAT)
    assert len(c1) == 2
    gross1, klein1 = (c1[0], c1[1]) if c1[0]["haeuser"] >= c1[1]["haeuser"] else (c1[1], c1[0])
    assert klein1["vorschlag_fuer"] == gross1["id"]     # als Vorschlag markiert statt gemergt

    z2 = {"Ev. Schule, Stadt Essen": 9, "Ev. Schule II, Stadt Essen": 6}
    c2 = clustere(z2, KAT)
    assert len(c2) == 2
    gross2, klein2 = (c2[0], c2[1]) if c2[0]["haeuser"] >= c2[1]["haeuser"] else (c2[1], c2[0])
    assert klein2["vorschlag_fuer"] == gross2["id"]


def test_clustere_gleiche_zahlentoken_mergt_weiter():
    # Gegenprobe: identische Zahl-Token (hier keine) stehen einer normalen Fusion nicht im Weg
    z = {"Fried. Krupp A.G. Schacht 3": 6, "Fried. Krupp AG Schacht 3": 4}
    c = clustere(z, KAT)
    assert len(c) == 1 and c[0]["haeuser"] == 10


def test_clustere_complete_linkage_keine_kette():
    # a~b und b~c ähnlich, a~c nicht → höchstens zwei zusammen, nie alle drei
    z = {"Bauverein Essen Nord": 5, "Bauverein Essen Nord West": 5, "Bauverein Essen West Süd": 5}
    c = clustere(z, KAT, schwelle=0.8, vorschlag_ab=0.5)
    assert max(len(x["mitglieder"]) for x in c) <= 2


def test_auto_name():
    assert auto_name([("Fried. Krupp A.G.", 257), ("Fried. Krupp A. G.", 181)]) == "Fried. Krupp AG"
    assert auto_name([("Stadt Essen", 3)]) == "Stadt Essen"


def _z(**k):
    z = dict(teil="II", id="1", Firmenname="", lastname="", firstname="", Adresse="", strasse_roh="Grenzstr.", hausnr="1",
             hausnr_zusatz="", stadtteil="Katernberg", Verwalter="", page="II-001", lat="51.49", lon="7.06", stufe="haus")
    z.update(k); return z


def test_sammle_trennt_und_belegt():
    e = [_z(id="1", Firmenname="Stadt Essen"), _z(id="2", Firmenname="Stadt Essen", hausnr="2"),
         _z(id="3", lastname="Schmidt", firstname="Wilh."), _z(id="4", teil="I", lastname="Nicht", firstname="Teil II"),
         _z(id="5", lat="", lon="", stufe="offen", Firmenname="Stadt Essen")]
    k, p, belege = sammle(e)
    assert k == {"Stadt Essen": 3} and p == {"Schmidt, Wilh.": 1}
    assert [b["id"] for b in belege["Stadt Essen"]] == ["1", "2", "5"]
    assert belege["Stadt Essen"][0] == dict(id="1", adresse="Grenzstr. 1", stadtteil="Katernberg", verwalter="", seite="II-001", lat=51.49, lon=7.06, stufe="haus")
    assert belege["Stadt Essen"][2]["lat"] is None


def test_vorschlagszeilen_und_pruefpflicht():
    c = clustere({"Fried. Krupp A.G.": 6, "Fried. Krupp AG": 1, "Klein GmbH": 2}, KAT)
    z = vorschlagszeilen(c, {"Schmidt, Wilh.": 7, "Meier, Karl": 2}, min_haeuser=5)
    by = {x["schreibweise"]: x for x in z}
    assert by["Fried. Krupp A.G."]["pruefpflichtig"] == "ja" and by["Fried. Krupp AG"]["pruefpflichtig"] == "ja"
    assert by["Klein GmbH"]["pruefpflichtig"] == "nein"
    assert by["Schmidt, Wilh."] == dict(schreibweise="Schmidt, Wilh.", art="person", anzahl="7", cluster_id=cluster_id("Schmidt, Wilh."),
                                        cluster_name="Schmidt, Wilh.", aehnlichkeit="1.0", vorschlag_fuer="", pruefpflichtig="ja")
    assert by["Meier, Karl"]["pruefpflichtig"] == "nein"
    assert [x["schreibweise"] for x in z][:3] == ["Fried. Krupp A.G.", "Fried. Krupp AG", "Schmidt, Wilh."]   # nach Häusern absteigend, bei Gleichstand nach Name


def test_aktualisiere_kuratierung_sperre():
    alt = [dict(schreibweise="Stadt Essen", art="koerperschaft", eigentuemer="Stadt Essen", kategorie="stadt_staat", geprueft="ja", bearbeiter="christos", datum="2026-09-20", hinweis=""),
           dict(schreibweise="Fried. Krupp A.G.", art="koerperschaft", eigentuemer="Altname", kategorie="industrie", geprueft="", bearbeiter=AUTOMATIK, datum="2026-09-20", hinweis="x"),
           dict(schreibweise="Fried. Krupp AG.", art="koerperschaft", eigentuemer="Krupp", kategorie="", geprueft="", bearbeiter="christos", datum="2026-09-21", hinweis=""),
           dict(schreibweise="Weg GmbH", art="koerperschaft", eigentuemer="Weg GmbH", kategorie="", geprueft="", bearbeiter=AUTOMATIK, datum="2026-09-20", hinweis="")]
    vorschlag = [dict(schreibweise="Stadt Essen", art="koerperschaft", cluster_name="Stadt Essen (neu)"),
                 dict(schreibweise="Fried. Krupp A.G.", art="koerperschaft", cluster_name="Fried. Krupp AG"),
                 dict(schreibweise="Fried. Krupp AG.", art="koerperschaft", cluster_name="Fried. Krupp AG"),
                 dict(schreibweise="Schmidt, Wilh.", art="person", cluster_name="Schmidt, Wilh.", pruefpflichtig="ja"),
                 dict(schreibweise="Meier, Karl", art="person", cluster_name="Meier, Karl", pruefpflichtig="nein")]
    neu = {z["schreibweise"]: z for z in aktualisiere_kuratierung(alt, vorschlag, "2026-09-22")}
    assert neu["Stadt Essen"]["eigentuemer"] == "Stadt Essen"                       # geprüft: unverändert
    assert neu["Fried. Krupp A.G."]["eigentuemer"] == "Fried. Krupp AG"             # Automatik-Zeile: neuer Vorschlag
    assert neu["Fried. Krupp A.G."]["kategorie"] == "industrie" and neu["Fried. Krupp A.G."]["hinweis"] == "x"  # Kategorie/Hinweis bleiben
    assert neu["Fried. Krupp A.G."]["datum"] == "2026-09-22"
    assert neu["Fried. Krupp AG."]["eigentuemer"] == "Krupp"                        # vom Menschen angefasst: bleibt
    assert neu["Schmidt, Wilh."] == dict(schreibweise="Schmidt, Wilh.", art="person", eigentuemer="Schmidt, Wilh.", kategorie="privatperson", geprueft="", bearbeiter=AUTOMATIK, datum="2026-09-22", hinweis="")
    assert neu["Weg GmbH"]["eigentuemer"] == "Weg GmbH"                              # verwaist: bleibt stehen
    assert "Meier, Karl" not in neu                                                  # Person unter Untergrenze: keine neue Zeile
    assert list(neu) == ["Stadt Essen", "Fried. Krupp A.G.", "Fried. Krupp AG.", "Weg GmbH", "Schmidt, Wilh."]  # alte Reihenfolge, Neues hinten


def test_main_schreibt_dateien(tmp_path):
    (tmp_path / "build").mkdir(); (tmp_path / "kuratierung").mkdir()
    import shutil; shutil.copy(W / "kuratierung" / "eigentuemer_abkuerzungen.csv", tmp_path / "kuratierung")
    from pipeline.lib.io import schreib_csv
    e = [_z(id="1", Firmenname="Stadt Essen"), _z(id="2", lastname="Schmidt", firstname="Wilh.")]
    schreib_csv(tmp_path / "build" / "eintraege.csv", e, list(e[0]))
    k = main(["--min-haeuser", "1", "--wurzel", str(tmp_path)])
    assert k["koerperschaften"] == 1 and k["personen"] == 1 and k["pruefpflichtig"] == 2
    assert (tmp_path / "build" / "eigentuemer_vorschlag.csv").exists()
    belege = json.loads((tmp_path / "build" / "eigentuemer_belege.json").read_text(encoding="utf-8"))
    assert belege["Stadt Essen"][0]["id"] == "1"
    kur = lies_csv(tmp_path / "kuratierung" / "eigentuemer.csv")
    assert [z["schreibweise"] for z in kur] == ["Stadt Essen", "Schmidt, Wilh."]
    assert kur[1]["kategorie"] == "privatperson"
