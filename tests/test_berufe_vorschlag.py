import json
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.lib.berufe import AUTOMATIK, lade_kuratierung, lade_ohdab
from pipeline.lib.io import lies_csv
from werkzeuge.berufe_vorschlag import (STATUS_ITEMS, aehnlich, aktualisiere_kuratierung, exakt, formen_index,
                                         lade_katalog, loese_auf, main, sammle, vorschlag_fuer, waehle, zerlege)
from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN

KATALOG = "kurz,lang,status,beleg,bearbeiter,datum\nBergm.,Bergmann,,üblich,Claude,2026-09-23\nKfm.,Kaufmann,,üblich,Claude,2026-09-23\nKaufm.,Kaufmann,,üblich,Claude,2026-09-23\nFühr.,Führer,,üblich,Claude,2026-09-23\nKraftw. Führ.,Kraftwagenführer,,üblich,Claude,2026-09-23\nBerginval.,Bergmann,invalide,üblich,Claude,2026-09-23\n"


def katalog(tmp_path):
    p = tmp_path / "k.csv"; p.write_text(KATALOG, encoding="utf-8"); return lade_katalog(p)


def ohdab(tmp_path):
    p = tmp_path / "ohdab.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); return lade_ohdab(p)


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
    assert zerlege("Bergm. Inv.") == ("Bergm.", ["invalide"])
    assert zerlege("Berginv.") == ("Berginv.", [])          # kein Wortanfang vor „Inv.“ → bleibt dem Katalog
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


def test_exakt_und_wahl(tmp_path):
    o = ohdab(tmp_path); idx = formen_index(o)
    assert exakt("Bergmann", idx) == ["B 21112-100"]
    assert exakt("Bergfrau", idx) == ["B 21112-100"]
    assert sorted(exakt("Lehrer", idx)) == ["B 84124-120"]            # „akademischer Lehrer“ ist eine andere Form
    assert sorted(exakt("Arbeiter", idx)) == ["B 20002-500"]
    assert exakt("Fabrikarbeiter", idx) == []
    assert waehle(["B 84124-521", "B 84124-120"], o) == "B 84124-120"   # kürzeste Normbezeichnung


def test_waehle_bevorzugt_unqualifiziertes_item(tmp_path):
    """Ein Item mit Qualifizierung darf das genau passende Item nicht verdrängen (Ruling Fix-Runde 1).

    Beide Items tragen die männliche Form „Bergmann“, sind also beide Exakt-Treffer. Die
    Normbezeichnungen sind gleich lang, der alte Schlüssel entschiede über die kleinere ID.
    """
    p = tmp_path / "o.csv"
    p.write_text(OHDAB_KOPF
                 + "B 21112-050,Q9,Bergmann - Tag,Bergmann,Bergfrau,fachlich,B 21112,Berg- und Tagebau\n"
                 + "B 21112-100,Q8,Bergmann/-frau,Bergmann,Bergfrau,fachlich,B 21112,Berg- und Tagebau\n",
                 encoding="utf-8")
    o = lade_ohdab(p)
    ids = ["B 21112-050", "B 21112-100"]
    assert waehle(ids, o) == "B 21112-050"                      # ohne Beruf: kleinste ID bei gleicher Länge
    assert waehle(ids, o, "Bergmann") == "B 21112-100"          # mit Beruf: unqualifizierte Normbezeichnung


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
    assert v["kandidaten"][0][0] == "A 10200-502"
    # Nur-Status, Original-Schreibweise trifft KEINE Form (Kürzel „Inval.“) → Rückfall auf
    # STATUS_ITEMS, Grund "status".
    v = vorschlag_fuer("Inval.", k, o, idx)
    assert (v["beruf"], v["status"], v["ohdab_id"], v["grund"]) == ("Invalide", "invalide", "A 10200-502", "status")
    v = vorschlag_fuer("Fabrkarb.", k, o, idx)
    assert v["ohdab_id"] == "" and v["grund"] == "" and v["beruf"] == "Fabrkarb."
    v = vorschlag_fuer("Bergmnn", k, o, idx)
    assert v["ohdab_id"] == "B 21112-100" and v["grund"].startswith("aehnlich 0.9")
    assert v["kandidaten"][0][0] == "B 21112-100"


def test_sammle_zaehlt_nur_teil_I_und_II():
    e = [dict(teil="I", **{"Beruf o. ä.": " Bergm. "}, lastname="A", firstname="B", strasse_roh="X", hausnr="1", Vorort="Kray", page="I-1", id="1"),
         dict(teil="II", **{"Beruf o. ä.": "Bergm."}, lastname="C", firstname="", strasse_roh="Y", hausnr="2", Vorort="", page="II-1", id="2"),
         dict(teil="III", **{"Beruf o. ä.": "Bergm."}, lastname="D", firstname="", strasse_roh="Z", hausnr="3", Vorort="", page="III-1", id="3"),
         dict(teil="I", **{"Beruf o. ä.": ""}, lastname="E", firstname="", strasse_roh="Z", hausnr="3", Vorort="", page="I-2", id="4")]
    n, belege = sammle(e)
    assert n == {"Bergm.": 2}
    assert [b["name"] for b in belege["Bergm."]] == ["A, B", "C"] and belege["Bergm."][0]["adresse"] == "X 1, Kray" and belege["Bergm."][0]["seite"] == "I-1"


def test_aktualisiere_kuratierung_sperre_und_untergrenze():
    alt = [dict(schreibweise="Bergm.", nennungen="1", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja", vorschlag_grund="katalog; exakt", bearbeiter="christos", datum="2026-09-23", hinweis=""),
           dict(schreibweise="Kfm.", nennungen="1", beruf="Kfm.", status="", ohdab_id="", niveau_unsicher="", geprueft="", vorschlag_grund="", bearbeiter=AUTOMATIK, datum="2026-09-23", hinweis="alt")]
    v = {"Bergm.": dict(beruf="Bergarbeiter", status="", ohdab_id="X", grund="exakt", kandidaten=[]),
         "Kfm.": dict(beruf="Kaufmann", status="", ohdab_id="B 1", grund="katalog; exakt", kandidaten=[]),
         "Neu.": dict(beruf="Neu.", status="", ohdab_id="", grund="", kandidaten=[]),
         "Selten": dict(beruf="Selten", status="", ohdab_id="", grund="", kandidaten=[])}
    n = {"Bergm.": 99, "Kfm.": 7, "Neu.": 5, "Selten": 4}
    neu = aktualisiere_kuratierung(alt, v, n, "2026-09-24", 5)
    z = {x["schreibweise"]: x for x in neu}
    assert z["Bergm."]["beruf"] == "Bergmann" and z["Bergm."]["nennungen"] == "99" and z["Bergm."]["geprueft"] == "ja"   # gesperrt, nur nennungen
    assert z["Kfm."]["beruf"] == "Kaufmann" and z["Kfm."]["ohdab_id"] == "B 1" and z["Kfm."]["hinweis"] == "alt" and z["Kfm."]["datum"] == "2026-09-24"
    assert z["Neu."]["bearbeiter"] == AUTOMATIK and z["Neu."]["geprueft"] == "" and z["Neu."]["niveau_unsicher"] == ""
    assert "Selten" not in z
    assert aktualisiere_kuratierung(neu, v, n, "2026-09-25", 5) == neu      # idempotent


def test_main_schreibt_dateien(tmp_path):
    (tmp_path / "build").mkdir(); (tmp_path / "kuratierung").mkdir()
    (tmp_path / "kuratierung" / "ohdab.csv").write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8")
    (tmp_path / "kuratierung" / "berufe_abkuerzungen.csv").write_text(KATALOG, encoding="utf-8")
    kopf = "id,teil,page,lastname,firstname,Beruf o. ä.,strasse_roh,hausnr,hausnr_zusatz,Vorort\n"
    zeilen = "".join(f"{i},I,I-1,N{i},V,Bergm.,Str,{i + 1},,Kray\n" for i in range(6)) + "9,I,I-2,X,Y,Lehrer,Str,2,,\n"
    (tmp_path / "build" / "eintraege.csv").write_text(kopf + zeilen, encoding="utf-8")
    k = main(["--wurzel", str(tmp_path)])
    assert k["schreibweisen"] == 1 and k["zeilen"] == 1        # Lehrer hat nur 1 Nennung → unter der Untergrenze
    z = lade_kuratierung(lies_csv(tmp_path / "kuratierung" / "berufe.csv"))
    assert z["Bergm."]["ohdab_id"] == "B 21112-100" and z["Bergm."]["nennungen"] == "6"
    kand = json.loads((tmp_path / "build" / "berufe_kandidaten.json").read_text(encoding="utf-8"))
    assert kand["Bergm."][0][0] == "B 21112-100"
    belege = json.loads((tmp_path / "build" / "berufe_belege.json").read_text(encoding="utf-8"))
    assert len(belege["Bergm."]) == 5
