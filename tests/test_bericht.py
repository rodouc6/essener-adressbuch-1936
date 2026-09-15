from pipeline.lib.bericht import erzeuge


def test_bericht_enthaelt_kernzahlen():
    def e_(**kw):
        basis = dict(teil="I", stufe="haus", grund="", herkunft="heutig", parse_status="ok",
                     mehrdeutig="nein", grund_mehrdeutig="", zeitlich_abweichend="nein",
                     teilstrecke_abgetrennt="nein")
        basis.update(kw)
        return basis
    e = [e_(), e_(stufe="offen", grund="kein_treffer"), e_(teil="II", stufe="strasse", herkunft="konkordanz")]
    a = [dict(strasse_heute="A", hausnr="1", hausnr_zusatz="", stadtteil="", stufe="haus", lat="51.4", lon="7.0",
              display_name="x", zeilen="2", herkunft="", strasse_roh="A", grund="", parse_status="ok"),
         dict(strasse_heute="B", hausnr="2", hausnr_zusatz="", stadtteil="", stufe="offen", lat="", lon="",
              display_name="", zeilen="1", herkunft="", strasse_roh="B", grund="kein_treffer", parse_status="ok")]
    md, geo = erzeuge(e, a, strassen=[], dubletten=[{"id": "1", "dublette_von": "2"}], ausgeschlossen=[], vorschlaege=[])
    assert "| haus |" in md and "33,3" in md and "Dubletten: 1" in md
    assert geo["type"] == "FeatureCollection" and len(geo["features"]) == 1
    assert geo["features"][0]["geometry"]["coordinates"] == [7.0, 51.4]


def eintrag(**kw):
    basis = dict(teil="I", stufe="haus", grund="", herkunft="heutig", parse_status="ok",
                 mehrdeutig="nein", grund_mehrdeutig="", zeitlich_abweichend="nein",
                 teilstrecke_abgetrennt="nein")
    basis.update(kw)
    return basis


def adresse(**kw):
    basis = dict(strasse_heute="A", hausnr="1", hausnr_zusatz="", stadtteil="", stufe="haus",
                 lat="51.4", lon="7.0", display_name="x", zeilen="2", herkunft="heutig",
                 strasse_roh="A", grund="", parse_status="ok")
    basis.update(kw)
    return basis


def test_bericht_enthaelt_grund_mehrdeutig_und_vorort_tabelle():
    e = [eintrag(), eintrag(mehrdeutig="ja", grund_mehrdeutig="homonym_1936", stufe="offen",
                 grund="strasse_offen")]
    md, _ = erzeuge(e, [adresse()], strassen=[], dubletten=[], ausgeschlossen=[], vorschlaege=[],
                    zuordnung=[{"strasse_roh_norm": "hstr."}],
                    statistik={"cache_treffer": 7, "cache_anfragen": 10})
    assert "| homonym_1936 | 1 |" in md
    assert "Vorort → heutige Stadtteile" in md and "| Ueberruhr |" in md
    assert "Zuordnungstabelle: 1" in md
    assert "Cache-Treffer: 7 von 10" in md


def test_bericht_ohne_statistik_laeuft():
    md, _ = erzeuge([eintrag()], [adresse()], strassen=[], dubletten=[], ausgeschlossen=[],
                    vorschlaege=[])
    assert "Cache-Treffer" not in md and "Zuordnungstabelle: 0" in md


def test_bericht_zeitlich_abweichend_tabelle():
    e = [eintrag(zeitlich_abweichend="ja"), eintrag()]
    md, _ = erzeuge(e, [adresse()], strassen=[], dubletten=[], ausgeschlossen=[], vorschlaege=[])
    assert "Zeitlich abweichend" in md and "| ja | 1 |" in md


def test_bericht_teilstrecke_tabelle():
    md, _ = erzeuge([eintrag(teilstrecke_abgetrennt="ja"), eintrag()], [adresse()], strassen=[],
                    dubletten=[], ausgeschlossen=[], vorschlaege=[])
    assert "Teilstrecke abgetrennt" in md
