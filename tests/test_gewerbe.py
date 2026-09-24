import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.gewerbe import ARTEN, FELDER_GEWERBE, betriebsschluessel, gewerbe_export, gewerbe_vorschlag, lade_gewerbe, rubrik_von
from werkzeuge.gewerbe_vorschlag import baue_gewerbe


def test_rubrik_aus_firmenname():
    assert rubrik_von("M. Jäger, Althandlung") == ("M. Jäger", "Althandlung")
    assert rubrik_von("Fritz Loosen, Architekt") == ("Fritz Loosen", "Architekt")
    assert rubrik_von("Müller & Co., G.m.b.H., Kohlen") == ("Müller & Co., G.m.b.H.", "Kohlen")
    assert rubrik_von("Ohne Suffix") == ("Ohne Suffix", "")
    assert rubrik_von("") == ("", "")


def test_vorschlag():
    assert list(ARTEN) == ["handwerk", "handel", "gastgewerbe", "dienstleistung", "industrie", "freier_beruf", "sonstige"]
    assert gewerbe_vorschlag("Bäcker") == ("lebensmittel", "handwerk")
    assert gewerbe_vorschlag("Kolonialwaren") == ("lebensmittel", "handel")
    assert gewerbe_vorschlag("Schankwirt") == ("gastgewerbe", "gastgewerbe")
    assert gewerbe_vorschlag("Schneider für Herren") == ("textil_bekleidung", "handwerk")
    assert gewerbe_vorschlag("Architekt") == ("bau", "freier_beruf")
    assert gewerbe_vorschlag("Fuhrgeschäft") == ("verkehr_bahn_post", "dienstleistung")
    assert gewerbe_vorschlag("Hebamme") == ("gesundheit", "freier_beruf")
    assert gewerbe_vorschlag("Eisenwaren") == ("handel", "handel")
    assert gewerbe_vorschlag("Maschinenfabrik") == ("metall_maschinen", "industrie")
    assert gewerbe_vorschlag("Bergwerks- und Hüttenbedarf") == ("bergbau", "handel")
    assert gewerbe_vorschlag("Xyz") == ("sonstige", "sonstige")
    # Realdaten-Funde (Task 5, Step 5): generisches „handel“ muss zuletzt greifen, sonst überdeckt
    # es speziellere Kategorien, die selbst Waren-/Bedarfs-Wörter enthalten.
    assert gewerbe_vorschlag("Friseureinrichtungen u. -apparate") == ("haus_reinigung", "dienstleistung")
    assert gewerbe_vorschlag("Versicherungsgeschäft") == ("verwaltung", "dienstleistung")
    assert gewerbe_vorschlag("Buchbinderei") == ("bildung_kultur_kirche", "freier_beruf")


def test_export_schluessel_und_baue():
    assert gewerbe_export(dict(gruppe="lebensmittel", art="handwerk", geprueft="ja")) == ("lebensmittel", "handwerk")
    assert gewerbe_export(dict(gruppe="lebensmittel", art="handwerk", geprueft="")) == ("ungeprueft", "ungeprueft")
    assert gewerbe_export(None) == ("ungeprueft", "ungeprueft")
    e = dict(Firmenname="M. Jäger, Althandlung", strasse_norm="brüningstraße", hausnr="13", Vorort="")
    assert betriebsschluessel(e) == "m jaeger|brüningstraße|13|"
    eintraege = [dict(teil="III", Firmenname="A, Bäcker"), dict(teil="III", Firmenname="B, Bäcker"), dict(teil="III", Firmenname="C, Kohlen"),
                 dict(teil="I", Firmenname="D, Bäcker"), dict(teil="III", Firmenname="Ohne")]
    alt = [dict(rubrik="Bäcker", betriebe="1", gruppe="handel", art="handel", geprueft="ja", bearbeiter="christos", datum="d", hinweis="")]
    neu = baue_gewerbe(eintraege, alt, "2026-09-26")
    assert [(z["rubrik"], z["betriebe"], z["gruppe"], z["art"], z["geprueft"]) for z in neu] == [("Bäcker", "2", "handel", "handel", "ja"), ("Kohlen", "1", "handel", "handel", "")]
    assert list(lade_gewerbe(neu)) == ["Bäcker", "Kohlen"]
