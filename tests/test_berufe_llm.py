import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.berufe import AUTOMATIK, lade_ohdab
from werkzeuge.berufe_llm import baue_prompt, ergaenze_llm
from werkzeuge.berufe_vorschlag import formen_index
from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN


def test_ergaenze_llm_nur_offene_automatikzeilen(tmp_path):
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8")
    o = lade_ohdab(p); idx = formen_index(o)
    zeilen = [dict(schreibweise="Bergmnn.", beruf="Bergmnn.", status="", ohdab_id="", vorschlag_grund="", geprueft="", bearbeiter=AUTOMATIK, datum="", hinweis="", nennungen="5", niveau_unsicher=""),
              dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", vorschlag_grund="exakt", geprueft="", bearbeiter=AUTOMATIK, datum="", hinweis="", nennungen="9", niveau_unsicher=""),
              dict(schreibweise="Xy.", beruf="Xy.", status="", ohdab_id="", vorschlag_grund="", geprueft="", bearbeiter="christos", datum="", hinweis="", nennungen="5", niveau_unsicher="")]
    fragen = []
    def frage(prompt):
        fragen.append(prompt)
        return "B 21112-100" if "Bergmnn." in prompt else "unklar"
    neu = ergaenze_llm(zeilen, {"Bergmnn.": [dict(name="A", adresse="X 1", teil="I", seite="I-1")]}, o, idx, "2026-09-24", frage=frage)
    assert len(fragen) == 1 and "X 1" in fragen[0] and "B 21112-100" in fragen[0]
    assert neu[0]["ohdab_id"] == "B 21112-100" and neu[0]["vorschlag_grund"] == "llm" and neu[0]["geprueft"] == "" and neu[0]["datum"] == "2026-09-24"
    assert neu[1] == zeilen[1] and neu[2] == zeilen[2]


def test_llm_antwort_ausserhalb_der_liste_wird_verworfen(tmp_path):
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8")
    o = lade_ohdab(p); idx = formen_index(o)
    z = [dict(schreibweise="Bergmnn.", beruf="Bergmnn.", status="", ohdab_id="", vorschlag_grund="", geprueft="", bearbeiter=AUTOMATIK, datum="", hinweis="", nennungen="5", niveau_unsicher="")]
    neu = ergaenze_llm(z, {}, o, idx, "d", frage=lambda p: "A 10200-502")   # nicht unter den 20 nächsten → verwerfen
    assert neu[0]["ohdab_id"] == "" and neu[0]["vorschlag_grund"] == ""
