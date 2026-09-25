import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.gewerbe import ARTEN, GRUPPEN, FELDER_GEWERBE, betriebsschluessel, entschieden, gewerbe_export, gewerbe_quelle, gewerbe_vorschlag, lade_gewerbe, rubrik_von
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
    # Prinzipien 2026-09-25 (docs/gewerbe.md): Waren-Fallback zuletzt; Beratung/Geld eigene Gruppe; Photograph,
    # Buchbinder, Wäscher = Handwerk; Ingenieur ohne erkennbare Branche; Genussmittel bei Lebensmitteln.
    assert "finanzen_recht" in GRUPPEN and len(GRUPPEN) == 15
    assert gewerbe_vorschlag("Versicherungsgeschäft") == ("finanzen_recht", "dienstleistung")
    assert gewerbe_vorschlag("Bücherrevisor") == ("finanzen_recht", "freier_beruf")
    assert gewerbe_vorschlag("Buchbinderei") == ("bildung_kultur_kirche", "handwerk")
    assert gewerbe_vorschlag("Photogr. Atelier") == ("bildung_kultur_kirche", "handwerk")
    assert gewerbe_vorschlag("Ingenieur") == ("sonstige", "freier_beruf")
    assert gewerbe_vorschlag("Prüfingenieur f. Statik") == ("bau", "freier_beruf")
    assert gewerbe_vorschlag("Tiefbauunternehmer") == ("bau", "handwerk")
    assert gewerbe_vorschlag("Wasch- und Plättanstalt") == ("haus_reinigung", "handwerk")
    assert gewerbe_vorschlag("Zigarren") == ("lebensmittel", "handel")
    assert gewerbe_vorschlag("Landwirtschaftl. Maschinen") != ("gastgewerbe", "gastgewerbe")   # „wirtschaft“ nur am Wortanfang
    assert gewerbe_vorschlag("Baumschule") == ("haus_reinigung", "handwerk")                   # nicht „schule“
    assert gewerbe_vorschlag("Auto-Treibstoffe") != ("textil_bekleidung", "handel")


def test_export_schluessel_und_baue():
    # Seit 2026-09-25: Vorschlag wird exportiert, die Quelle kennzeichnet (wie stellung_quelle).
    assert gewerbe_export(dict(gruppe="lebensmittel", art="handwerk", geprueft="ja")) == ("lebensmittel", "handwerk")
    assert gewerbe_quelle(dict(gruppe="lebensmittel", art="handwerk", geprueft="ja")) == "hand"
    assert gewerbe_export(dict(gruppe="lebensmittel", art="handwerk", geprueft="", bearbeiter="gewerbe_vorschlag")) == ("lebensmittel", "handwerk")
    assert gewerbe_quelle(dict(gruppe="lebensmittel", art="handwerk", geprueft="", bearbeiter="gewerbe_vorschlag")) == "vorschlag"
    assert gewerbe_quelle(dict(gruppe="lebensmittel", art="handwerk", geprueft="", bearbeiter="claude")) == "claude"
    assert gewerbe_export(dict(gruppe="adel", art="handwerk", geprueft="ja")) == ("ungeprueft", "ungeprueft")
    assert gewerbe_export(None) == ("ungeprueft", "ungeprueft") and gewerbe_quelle(None) == ""
    assert entschieden(dict(geprueft="", bearbeiter="claude")) and entschieden(dict(geprueft="ja", bearbeiter="christos")) and not entschieden(dict(geprueft="", bearbeiter="gewerbe_vorschlag"))
    e = dict(Firmenname="M. Jäger, Althandlung", strasse_norm="brüningstraße", hausnr="13", Vorort="")
    assert betriebsschluessel(e) == "m jaeger|brüningstraße|13|"
    eintraege = [dict(teil="III", Firmenname="A, Bäcker"), dict(teil="III", Firmenname="B, Bäcker"), dict(teil="III", Firmenname="C, Kohlen"),
                 dict(teil="I", Firmenname="D, Bäcker"), dict(teil="III", Firmenname="Ohne")]
    alt = [dict(rubrik="Bäcker", betriebe="1", gruppe="handel", art="handel", geprueft="ja", bearbeiter="christos", datum="d", hinweis="")]
    neu = baue_gewerbe(eintraege, alt, "2026-09-26")
    assert [(z["rubrik"], z["betriebe"], z["gruppe"], z["art"], z["geprueft"]) for z in neu] == [("Bäcker", "2", "handel", "handel", "ja"), ("Kohlen", "1", "handel", "handel", "")]
    assert list(lade_gewerbe(neu)) == ["Bäcker", "Kohlen"]
