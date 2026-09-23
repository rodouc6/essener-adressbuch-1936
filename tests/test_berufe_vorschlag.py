import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from werkzeuge.berufe_vorschlag import lade_katalog, loese_auf, zerlege

KATALOG = "kurz,lang,status,beleg,bearbeiter,datum\nBergm.,Bergmann,,üblich,Claude,2026-09-23\nKfm.,Kaufmann,,üblich,Claude,2026-09-23\nKaufm.,Kaufmann,,üblich,Claude,2026-09-23\nFühr.,Führer,,üblich,Claude,2026-09-23\nKraftw. Führ.,Kraftwagenführer,,üblich,Claude,2026-09-23\nBerginval.,Bergmann,invalide,üblich,Claude,2026-09-23\n"


def katalog(tmp_path):
    p = tmp_path / "k.csv"; p.write_text(KATALOG, encoding="utf-8"); return lade_katalog(p)


def test_zerlege_status():
    assert zerlege("Bergm. i. R.") == ("Bergm.", ["ruhestand"])
    assert zerlege("Lehrer a.D.") == ("Lehrer", ["ruhestand"])
    assert zerlege("Bergm. Ww.") == ("Bergm.", ["witwe"])
    assert zerlege("Schlosser, Inval.") == ("Schlosser", ["invalide"])
    assert zerlege("Invalide") == ("", ["invalide"])
    assert zerlege("Pensionär") == ("", ["ruhestand"])
    assert zerlege("Bergm. i. R. Ww.") == ("Bergm.", ["ruhestand", "witwe"])
    assert zerlege("Berginval.") == ("Berginval.", [])          # kein Wortanfang vor „inval“ → bleibt dem Katalog
    assert zerlege("  Schlosser  ") == ("Schlosser", [])
    assert zerlege("Rentn.") == ("", ["ruhestand"])
    assert zerlege("Bergm. Pension.") == ("Bergm.", ["ruhestand"])
    assert zerlege("Schlosser Invalid.") == ("Schlosser", ["invalide"])
    assert zerlege("Inval") == ("", ["invalide"])
    assert zerlege("Rentier") == ("Rentier", [])


def test_loese_auf(tmp_path):
    k = katalog(tmp_path)
    assert loese_auf("Bergm.", k) == ("Bergmann", [], True)
    assert loese_auf("Kraftw. Führ.", k) == ("Kraftwagenführer", [], True)     # ganze Folge vor Einzelwörtern
    assert loese_auf("Führ.", k) == ("Führer", [], True)
    assert loese_auf("Berginval.", k) == ("Bergmann", ["invalide"], True)
    assert loese_auf("Schlosser", k) == ("Schlosser", [], True)
    assert loese_auf("Fabrkarb.", k) == ("Fabrkarb.", [], False)             # unaufgelöstes Punktwort → unvollständig
    assert loese_auf("Kfm. u. Vertreter", k) == ("Kaufmann u. Vertreter", [], True)
