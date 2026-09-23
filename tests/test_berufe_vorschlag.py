import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.lib.berufe import lade_ohdab
from werkzeuge.berufe_vorschlag import STATUS_ITEMS, aehnlich, exakt, formen_index, vorschlag_fuer, waehle
from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN


def ohdab(tmp_path):
    p = tmp_path / "ohdab.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); return lade_ohdab(p)


def test_exakt_und_wahl(tmp_path):
    o = ohdab(tmp_path); idx = formen_index(o)
    assert exakt("Bergmann", idx) == ["B 21112-100"]
    assert exakt("Bergfrau", idx) == ["B 21112-100"]
    assert sorted(exakt("Lehrer", idx)) == ["B 84124-120"]            # „akademischer Lehrer“ ist eine andere Form
    assert sorted(exakt("Arbeiter", idx)) == ["B 20002-500"]
    assert exakt("Fabrikarbeiter", idx) == []
    assert waehle(["B 84124-521", "B 84124-120"], o) == "B 84124-120"   # kürzeste Normbezeichnung


def test_aehnlich(tmp_path):
    o = ohdab(tmp_path); idx = formen_index(o)
    a = aehnlich("Bergmnn", idx)
    assert a and a[0][0] == "B 21112-100" and a[0][1] >= 0.90
    assert aehnlich("Zahnarzt", idx, schwelle=0.90) == []
    assert all(w >= 0.90 for _, w in a)


def test_status_items_aus_schnappschuss():
    # Rulings des Controllers: reale IDs aus kuratierung/ohdab.csv (2026-09-23), keine Platzhalter.
    assert STATUS_ITEMS == {
        "invalide": "A 10200-502",
        "ruhestand": "A 10300-529",
        "witwe": "A 21200-502",
    }


def test_vorschlag_fuer(tmp_path):
    o = ohdab(tmp_path); idx = formen_index(o)
    k = {"Bergm.": ("Bergmann", ""), "Berginval.": ("Bergmann", "invalide")}
    v = vorschlag_fuer("Bergm. i. R.", k, o, idx)
    assert (v["beruf"], v["status"], v["ohdab_id"], v["grund"]) == ("Bergmann", "ruhestand", "B 21112-100", "katalog; exakt")
    v = vorschlag_fuer("Berginval.", k, o, idx)
    assert (v["beruf"], v["status"], v["ohdab_id"]) == ("Bergmann", "invalide", "B 21112-100")
    v = vorschlag_fuer("Lehrer", k, o, idx)
    assert (v["ohdab_id"], v["grund"]) == ("B 84124-120", "exakt")
    # Nur-Status, Original-Schreibweise trifft exakt eine Form (hier: die Fixture-OhdAB kennt
    # nur "Invalide/Invalidin" als Status-Item) → Grund "status; exakt" (Ruling, weicht vom
    # Brief-Grund "status" ab, siehe task-3-report.md).
    v = vorschlag_fuer("Invalide", k, o, idx)
    assert (v["beruf"], v["status"], v["ohdab_id"], v["grund"]) == ("Invalide", "invalide", "A 10200-502", "status; exakt")
    # Nur-Status, Original-Schreibweise trifft KEINE Form (Kürzel „Inval.“) → Rückfall auf
    # STATUS_ITEMS, Grund "status".
    v = vorschlag_fuer("Inval.", k, o, idx)
    assert (v["beruf"], v["status"], v["ohdab_id"], v["grund"]) == ("Invalide", "invalide", "A 10200-502", "status")
    v = vorschlag_fuer("Fabrkarb.", k, o, idx)
    assert v["ohdab_id"] == "" and v["grund"] == "" and v["beruf"] == "Fabrkarb."
    v = vorschlag_fuer("Bergmnn", k, o, idx)
    assert v["ohdab_id"] == "B 21112-100" and v["grund"].startswith("aehnlich 0.9")
    assert v["kandidaten"][0][0] == "B 21112-100"
