import pathlib, sys
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.berufe import (AUTOMATIK, NIVEAUS, STATUS, falte_form, formen_von, gesperrt, lade_kuratierung,
                                 lade_ohdab, niveau_schluessel)

OHDAB_KOPF = "ohdab_id,qid,norm,maennlich,weiblich,niveau,gattung_id,gattung\n"
OHDAB_ZEILEN = (
    "B 21112-100,Q659279,Bergmann/-frau,Bergmann,Bergfrau,fachlich,B 21112,Berufe im Berg- und Tagebau – fachlich ausgerichtete Tätigkeiten\n"
    "B 84124-120,Q1,Lehrer/in,Lehrer,Lehrerin,hochkomplex,B 84124,Lehrkräfte in der Sekundarstufe – hoch komplexe Tätigkeiten\n"
    "B 84124-521,Q2,\"Lehrer/in, akadem.\",akademischer Lehrer,akademische Lehrerin,hochkomplex,B 84124,Lehrkräfte in der Sekundarstufe – hoch komplexe Tätigkeiten\n"
    "B 20001-503,Q3,Arbeiter/in - ungelernte/r,ungelernter Arbeiter,ungelernte Arbeiterin,helfer,B 20001,Allgemeine Berufe in der Produktion – Helfer-/Anlerntätigkeit\n"
    "B 20002-500,Q4,Arbeiter/in - allgemein,Arbeiter,Arbeiterin,fachlich,B 20002,Allgemeine Berufe in der Produktion – fachlich ausgerichtete Tätigkeiten\n"
    "A 10200-502,Q5,Invalide/Invalidin,Invalide,Invalidin,keins,A 10200,Invalide\n"
)


@pytest.fixture
def ohdab_pfad(tmp_path):
    p = tmp_path / "ohdab.csv"
    p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8")
    return p


def test_niveau_schluessel():
    assert niveau_schluessel("Fachliche Tätigkeiten") == "fachlich"
    assert niveau_schluessel("Tätigkeitsprofil Helfer- und Anlerntätigkeiten") == "helfer"
    assert niveau_schluessel("Hoch komplexe Tätigkeiten") == "hochkomplex"
    assert niveau_schluessel("Kein Anforderungsniveau") == "keins"
    assert niveau_schluessel("") == "keins"
    assert set(NIVEAUS) == {"helfer", "fachlich", "spezialist", "hochkomplex", "aufsicht", "fuehrung", "keins"}


def test_falte_form_und_formen():
    assert falte_form("Kraftwagen-Führer") == "kraftwagen fuehrer"
    assert falte_form("  Bergmann ") == "bergmann"
    z = dict(norm="Technische/r Kaufmann/-frau - Holz", maennlich="Technischer Kaufmann Fachrichtung Holz", weiblich="Technische Kauffrau Fachrichtung Holz")
    assert "technischer kaufmann fachrichtung holz" in formen_von(z)
    assert "technische kaufmann holz" in formen_von(z)   # norm ohne Geschlechtszusätze und ohne „ - “
    assert formen_von(dict(norm="Lehrer/in", maennlich="", weiblich="")) == ["lehrer"]


def test_lade_ohdab(ohdab_pfad, tmp_path):
    o = lade_ohdab(ohdab_pfad)
    assert o["B 21112-100"]["maennlich"] == "Bergmann" and o["B 21112-100"]["niveau"] == "fachlich"
    assert len(o) == 6
    with pytest.raises(FileNotFoundError, match="ohdab.csv fehlt"):
        lade_ohdab(tmp_path / "nein.csv")


def test_kuratierung_und_sperre():
    k = lade_kuratierung([dict(schreibweise=" Bergm. ", beruf="Bergmann", geprueft="", bearbeiter=AUTOMATIK),
                          dict(schreibweise="", beruf="x")])
    assert list(k) == ["Bergm."]
    assert not gesperrt(dict(geprueft="", bearbeiter=AUTOMATIK))
    assert gesperrt(dict(geprueft="ja", bearbeiter=AUTOMATIK))
    assert gesperrt(dict(geprueft="", bearbeiter="christos"))
    assert STATUS == ("ruhestand", "invalide", "witwe")


def test_ohdab_zeilen_aus():
    from werkzeuge.ohdab_laden import zeilen_aus
    text = ("i,id,norm,m,w,nivLabel,kat\n"
            "https://database.factgrid.de/entity/Q659279,B 21112-100,Bergmann/-frau,Bergmann,Bergfrau,Fachliche Tätigkeiten,B 21112: Berufe im Berg- und Tagebau\n"
            "https://database.factgrid.de/entity/Q659279,B 21112-100,Miner,Bergmann,Bergfrau,Fachliche Tätigkeiten,B 21112: Berufe im Berg- und Tagebau\n"
            "https://database.factgrid.de/entity/Q5,A 10200-502,Invalide/Invalidin,Invalide,Invalidin,,\n")
    z = zeilen_aus(text)
    assert [x["ohdab_id"] for x in z] == ["A 10200-502", "B 21112-100"]
    b = z[1]
    assert (b["qid"], b["norm"], b["niveau"], b["gattung_id"], b["gattung"]) == ("Q659279", "Bergmann/-frau", "fachlich", "B 21112", "Berufe im Berg- und Tagebau")
    assert z[0]["niveau"] == "keins"
