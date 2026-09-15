from pathlib import Path
from pipeline.lib import einlesen

FIX = Path(__file__).parent / "fixtures"


def test_verarbeite_mini():
    bereinigt, dubletten, ausgeschlossen = einlesen.verarbeite(FIX / "mini_quelle.tsv", FIX / "mini_zeilenkorrekturen.csv")
    ids = [z["id"] for z in bereinigt]
    assert ids == ["16385477", "17259959", "11111111", "11111112"]
    assert dubletten == [{"id": "16385478", "dublette_von": "16385477"}]
    assert ausgeschlossen == [{"id": "17915624", "grund": "teil_IV_W"}]
    hoeing = bereinigt[1]
    assert hoeing["Eigentümer"] == "Eigentümer" and hoeing["Vorort"] == "Steele" and hoeing["teil"] == "II" and hoeing["seite"] == "40"
    karl = bereinigt[2]
    assert karl["Vorort"] == "Karnap" and karl["Adresse"] == "Schulstr. 1" and karl["vorort_ok"] == "ja"
    anna = bereinigt[3]
    assert anna["Vorort"] == "Frillendorf" and anna["abweichender Wohnort"] == ""


def test_unbekannter_vorort_bleibt_markiert(tmp_path):
    q = FIX / "mini_quelle.tsv"
    leer = tmp_path / "k.csv"
    leer.write_text("id,aktion,feld,neu,beleg\n", encoding="utf-8")
    bereinigt, _, _ = einlesen.verarbeite(q, leer)
    anna = [z for z in bereinigt if z["id"] == "11111112"][0]
    assert anna["Vorort"] == "Frillenburg" and anna["vorort_ok"] == "nein"


def test_zeile_mit_falscher_feldzahl_ohne_korrektur_wird_ausgeschlossen(tmp_path):
    q = FIX / "mini_quelle.tsv"
    leer = tmp_path / "k.csv"
    leer.write_text("id,aktion,feld,neu,beleg\n", encoding="utf-8")
    _, _, ausgeschlossen = einlesen.verarbeite(q, leer)
    assert {"id": "17259959", "grund": "feldzahl_18"} in ausgeschlossen
