import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.merkmale import Regel
from pipeline.lib.stellung import STELLUNGEN, stellung_export, stellung_vorschlag

REGELN = [Regel("Beruf o. ä.", "praefix", "Dr.", "akademiker"), Regel("Beruf o. ä.", "praefix", "Dipl.", "akademiker")]


def item(norm, niveau="fachlich", gattung="Berufe im Berg- und Tagebau – fachlich ausgerichtete Tätigkeiten", gattung_id="B 21112"):
    return dict(ohdab_id="X", norm=norm, maennlich="", weiblich="", niveau=niveau, gattung_id=gattung_id, gattung=gattung)


def zeile(schreibweise, status="", beruf=""):
    return dict(schreibweise=schreibweise, status=status, beruf=beruf or schreibweise)


def test_vokabular():
    assert list(STELLUNGEN) == ["arbeiter", "angestellte", "beamte", "selbstaendige", "freie_berufe", "unternehmer",
                                "ohne_erwerb", "kaufleute", "unbestimmt"]


def test_regeln_in_reihenfolge():
    assert stellung_vorschlag(zeile("Bergm. i. R.", status="ruhestand"), item("Bergmann/-frau"), REGELN) == ("ohne_erwerb", "status")
    assert stellung_vorschlag(zeile("Invalide", status="invalide"), item("Invalide/Invalidin", "keins", "Invalide", "A 10200"), REGELN) == ("ohne_erwerb", "status")
    assert stellung_vorschlag(zeile("Berufslos"), item("Berufslose/r", "keins", "Berufslose", "A 10100"), REGELN) == ("ohne_erwerb", "item A 1")
    assert stellung_vorschlag(zeile("Bäckerei", status="gewerbe"), item("Bäcker/in"), REGELN) == ("selbstaendige", "gewerbe")
    assert stellung_vorschlag(zeile("Bäckermstr."), item("Bäckermeister/in", "aufsicht", "Aufsichtskräfte – Lebensmittel"), REGELN) == ("selbstaendige", "handwerksmeister")
    assert stellung_vorschlag(zeile("Werkmstr."), item("Werkmeister/in", "aufsicht", "Aufsichtskräfte – Produktion"), REGELN) == ("angestellte", "betriebsmeister")
    assert stellung_vorschlag(zeile("Dr. med."), item("Arzt/Ärztin", "hochkomplex", "Ärzte"), REGELN) == ("freie_berufe", "akademiker")
    assert stellung_vorschlag(zeile("Rechtsanwalt"), item("Rechtsanwalt/-anwältin", "hochkomplex", "Rechtsberatung"), REGELN) == ("freie_berufe", "freier beruf")
    assert stellung_vorschlag(zeile("Fabrikant"), item("Fabrikant/in", "fuehrung", "Geschäftsführer/innen und Vorstände"), REGELN) == ("unternehmer", "unternehmer")
    assert stellung_vorschlag(zeile("Direktor"), item("Direktor/in", "fuehrung", "Geschäftsführer/innen und Vorstände – hoch komplexe Tätigkeiten"), REGELN) == ("unternehmer", "unternehmer")
    assert stellung_vorschlag(zeile("Kfm."), item("Kaufmann/-frau", "fachlich", "Kaufleute im Handel"), REGELN) == ("kaufleute", "kaufmann")
    assert stellung_vorschlag(zeile("kfm. Angest."), item("Kaufmännische/r Angestellte/r", "fachlich", "Kaufleute"), REGELN) == ("angestellte", "angestellte")
    assert stellung_vorschlag(zeile("Reichsbahnbeamt."), item("Bahnbeamt(er/in) (mittl. Dienst)", "fachlich", "Eisenbahnverkehrsbetrieb"), REGELN) == ("beamte", "beamte")
    assert stellung_vorschlag(zeile("Lehrer"), item("Lehrer/in", "hochkomplex", "Lehrkräfte in der Sekundarstufe"), REGELN) == ("beamte", "beamte")
    assert stellung_vorschlag(zeile("Lokomotivführer"), item("Lokomotivführer/in", "fachlich", "Triebfahrzeugführer"), REGELN) == ("beamte", "beamte")
    assert stellung_vorschlag(zeile("Steiger"), item("Steiger/in", "spezialist", "Berufe im Berg- und Tagebau – komplexe Spezialistentätigkeiten"), REGELN) == ("angestellte", "angestellte")
    assert stellung_vorschlag(zeile("Techniker"), item("Techniker/in", "spezialist", "Maschinenbau"), REGELN) == ("angestellte", "angestellte")
    assert stellung_vorschlag(zeile("Gastwirt"), item("Gastwirt/in", "fachlich", "Gastronomie"), REGELN) == ("selbstaendige", "selbstaendig")
    assert stellung_vorschlag(zeile("Kolonialwarenhändler"), item("Kolonialwarenhändler/in", "fachlich", "Handel"), REGELN) == ("selbstaendige", "selbstaendig")
    assert stellung_vorschlag(zeile("Bergm."), item("Bergmann/-frau"), REGELN) == ("arbeiter", "niveau fachlich")
    assert stellung_vorschlag(zeile("Arbeiter"), item("Arbeiter/in - allgemein", "helfer", "Produktion"), REGELN) == ("arbeiter", "niveau helfer")
    assert stellung_vorschlag(zeile("Musiker"), item("Musiker/in", "keins", "Musik"), REGELN) == ("unbestimmt", "")
    assert stellung_vorschlag(zeile("Xyz"), None, REGELN) == ("unbestimmt", "")


def test_regeln_ohne_gattung_fehltreffer():
    """Die OhdAB-Gattung darf keine Fehltreffer aus Wortbestandteilen auslösen (Review zu TP5a Task 1)."""
    # „Obersteiger“ enthält „oberst“ als Präfix — kein Offizier, sondern Aufsichtskraft im Bergbau wie alle Steiger.
    assert stellung_vorschlag(zeile("Ob. Steiger"), item("Obersteiger/in", "spezialist", "Berufe im Berg- und Tagebau – komplexe Spezialistentätigkeiten"), REGELN) == ("angestellte", "angestellte")
    # „Unteroffiziere“ (Gattung) enthält „offizier“ als Bestandteil — kein Anlass für „beamte“.
    assert stellung_vorschlag(zeile("Rottenführ."), item("Rottenführer/in", "spezialist", "Unteroffiziere ohne Portepee vor 1945"), REGELN)[0] != "beamte"
    # „Sportlehrer“ (Gattung) enthält „lehrer“ als Bestandteil — ein Trainer ist kein Lehrer/Beamter.
    assert stellung_vorschlag(zeile("Trainer"), item("Trainer/in - allgemein", "spezialist", "Sportlehrer/innen (ohne Spezialisierung) – komplexe Spezialistentätigkeiten"), REGELN)[0] != "beamte"
    # „Oberstudiendirektor“ und „Katasterdirektor“ sind Beamte der Schul-/Verwaltungsleitung, keine Unternehmer.
    assert stellung_vorschlag(zeile("Ob. Studiendirekt."), item("Oberstudiendirektor/in", "fuehrung", "Führungskräfte – Allgemeinbildende Schulen"), REGELN) == ("beamte", "beamte")
    assert stellung_vorschlag(zeile("Katasterdirekt."), item("Katasterdirektor/in", "fuehrung", "Führungskräfte – Verwaltung"), REGELN) == ("beamte", "beamte")
    # Echte Unternehmer-Direktoren bleiben unternehmer.
    assert stellung_vorschlag(zeile("Bankdirektor"), item("Bankdirektor/in", "fuehrung", "Führungskräfte – Versicherungs- und Finanzdienstleistungen"), REGELN) == ("unternehmer", "unternehmer")
    # „lehrer“/„offizier“ zählen nur im eigenen Titel (Norm), nicht in der Gattung — echte Lehrer-Komposita bleiben beamte.
    assert stellung_vorschlag(zeile("Hauptlehr.", beruf="Hauptlehrer"), item("Hauptlehrer/in", "hochkomplex", "Lehrkräfte an allgemeinbildenden Schulen"), REGELN) == ("beamte", "beamte")


def test_export_nur_doppelt_geprueft():
    assert stellung_export(dict(geprueft="ja", stellung="arbeiter", stellung_geprueft="ja")) == "arbeiter"
    assert stellung_export(dict(geprueft="ja", stellung="arbeiter", stellung_geprueft="")) == "unbestimmt"
    assert stellung_export(dict(geprueft="", stellung="arbeiter", stellung_geprueft="ja")) == "unbestimmt"
    assert stellung_export(dict(geprueft="ja", stellung="", stellung_geprueft="ja")) == "unbestimmt"


def test_ergaenze_stellung_fuellt_nur_ungeprueft():
    from werkzeuge.stellung_vorschlag import ergaenze_stellung
    ohdab = {"B 21112-100": item("Bergmann/-frau"), "B 84124-120": item("Lehrer/in", "hochkomplex", "Lehrkräfte")}
    zeilen = [dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", geprueft="ja", stellung="", stellung_geprueft=""),
              dict(schreibweise="Lehrer", beruf="Lehrer", status="", ohdab_id="B 84124-120", geprueft="ja", stellung="freie_berufe", stellung_geprueft="ja"),
              dict(schreibweise="Kfm", beruf="Kfm", status="", ohdab_id="", geprueft="", stellung="", stellung_geprueft="")]
    neu, kenn = ergaenze_stellung(zeilen, ohdab, REGELN)
    assert [z["stellung"] for z in neu] == ["arbeiter", "freie_berufe", "unbestimmt"]
    assert [z["stellung_geprueft"] for z in neu] == ["", "ja", ""]
    assert kenn == {"niveau fachlich": 1, "ohne": 1, "geprueft": 1}


def test_ergaenze_stellung_laesst_geprueft_ohne_stellung_unangetastet():
    """stellung_geprueft='ja' ist allein maßgeblich — die Automatik darf es nie zurücksetzen, auch wenn
    stellung (noch) leer ist (Review-Fund TP5a Task 2: Doppelbedingung hätte stellung_geprueft überschrieben)."""
    from werkzeuge.stellung_vorschlag import ergaenze_stellung
    ohdab = {"B 21112-100": item("Bergmann/-frau")}
    zeilen = [dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", geprueft="ja", stellung="", stellung_geprueft="ja")]
    neu, kenn = ergaenze_stellung(zeilen, ohdab, REGELN)
    assert neu == zeilen
    assert kenn == {"geprueft": 1}
