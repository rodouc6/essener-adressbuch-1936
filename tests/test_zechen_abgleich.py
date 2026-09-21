import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from werkzeuge.zechen_abgleich import infobox_jahre, plan_treffer, status_ableiten, zechen_abgleichen

METS = """{{Infobox Bergwerk
 |NAME=Zeche Fridolin
 |BETRIEBSJAHRE_VON=
 |BETRIEBSJAHRE_BIS=1899
 |NACHFOLGENUTZUNG=Konsolidierung zur [[Zeche Eiberg]]
}}
Die '''Zeche Fridolin''' war ..."""


def test_infobox_jahre_liest_vierstellige_jahre():
    assert infobox_jahre(METS) == ("", "1899")
    assert infobox_jahre("{{Infobox Bergwerk\n |BETRIEBSJAHRE_VON=6. August 1791\n |BETRIEBSJAHRE_BIS=30. September 1962\n}}") == ("1791", "1962")
    assert infobox_jahre("kein Kasten") == ("", "")


PLAN = [
    dict(text="Zeche Karl Funke", art="zeche", lat="51.40514", lon="7.04896"),
    dict(text="ehem. Zeche Pauline", art="zeche", lat="51.37487", lon="6.99790"),
    dict(text="Zeche Neuessen", art="zeche", lat="51.50332", lon="7.00896"),
    dict(text="Schacht Katharina", art="schacht", lat="51.45775", lon="7.05565"),
]


def test_plan_treffer_findet_namensvarianten_im_umkreis():
    assert plan_treffer(dict(name="Carl Funke", lat="51.4060", lon="7.0500"), PLAN)["text"] == "Zeche Karl Funke"
    assert plan_treffer(dict(name="Pauline", lat="51.3750", lon="6.9980"), PLAN)["text"] == "ehem. Zeche Pauline"
    # Schächte zählen als Beleg, wenn der Name passt
    assert plan_treffer(dict(name="Katharina", lat="51.4575", lon="7.0578"), PLAN)["text"] == "Schacht Katharina"
    # gleicher Name, aber 5 km entfernt → kein Treffer
    assert plan_treffer(dict(name="Carl Funke", lat="51.45", lon="7.05"), PLAN) is None
    # ohne Koordinaten kein Treffer
    assert plan_treffer(dict(name="Carl Funke", lat="", lon=""), PLAN) is None


def test_status_ableiten():
    # beide Wikipedia-Quellen aktiv, im Plan beschriftet → aktiv
    assert status_ableiten("1850", "1967", "1804", "1973", "Zeche Karl Funke") == ("aktiv", "")
    # beide aktiv, im Plan nicht gefunden → aktiv mit Hinweis
    assert status_ableiten("1855", "1967", "1859", "1973", "") == ("aktiv", "im Plan 1935 nicht beschriftet")
    # beide aktiv, Plan sagt „ehem.“ → unklar
    assert status_ableiten("1880", "1950", "1880", "1950", "ehem. Zeche X")[0] == "unklar"
    # beide stillgelegt → stillgelegt; Plan-Beschriftung ohne ehem. nur als Hinweis
    assert status_ableiten("1873", "1892", "1873", "1892", "ehem. Zeche Kaiserin Augusta") == ("stillgelegt", "")
    assert status_ableiten("1840", "1929", "1842", "1929", "Zeche Graf Beust") == ("stillgelegt", "im Plan 1935 noch beschriftet")
    # Widerspruch (Fridolin) → unklar
    s, h = status_ableiten("1836", "1960", "", "1899", "")
    assert s == "unklar" and "Liste" in h and "Artikel" in h
    # Artikel ohne Jahre → unklar
    assert status_ableiten("1830", "1959", "", "", "")[0] == "unklar"


def test_zechen_abgleichen_setzt_spalten_und_prueftliste():
    zechen = [
        dict(name="Carl Funke", stadtteil="Heisingen", lat="51.4060", lon="7.0500", betrieb_von="1850", betrieb_bis="1967",
             quelle="https://de.wikipedia.org/wiki/Zeche_Carl_Funke", bearbeiter="wikipedia", datum="2026-09-21"),
        dict(name="Fridolin", stadtteil="Steele", lat="51.4389", lon="7.1105", betrieb_von="1836", betrieb_bis="1960",
             quelle="https://de.wikipedia.org/wiki/Zeche_Fridolin", bearbeiter="wikipedia", datum="2026-09-21"),
    ]
    artikel = {"https://de.wikipedia.org/wiki/Zeche_Carl_Funke": ("1804", "1973"),
               "https://de.wikipedia.org/wiki/Zeche_Fridolin": ("", "1899")}
    neu, pruefung = zechen_abgleichen(zechen, PLAN, artikel)
    assert neu[0]["status_1936"] == "aktiv" and neu[0]["plan_1935"] == "Zeche Karl Funke"
    assert neu[0]["artikel_von"] == "1804" and neu[0]["artikel_bis"] == "1973"
    assert neu[1]["status_1936"] == "unklar" and neu[1]["plan_1935"] == ""
    assert neu[0]["status_geprueft"] == "nein"
    assert [p["name"] for p in pruefung] == ["Fridolin"]
    assert pruefung[0]["liste"] == "1836–1960" and pruefung[0]["artikel"] == "–1899"


def test_zechen_abgleichen_respektiert_handpruefung():
    z = [dict(name="Fridolin", lat="51.4389", lon="7.1105", betrieb_von="1836", betrieb_bis="1960",
              quelle="https://de.wikipedia.org/wiki/Zeche_Fridolin", status_1936="stillgelegt", status_geprueft="ja",
              hinweis="Huske 2006: 1899 zu Eiberg")]
    neu, pruefung = zechen_abgleichen(z, PLAN, {"https://de.wikipedia.org/wiki/Zeche_Fridolin": ("", "1899")})
    assert neu[0]["status_1936"] == "stillgelegt" and neu[0]["hinweis"] == "Huske 2006: 1899 zu Eiberg"
    assert neu[0]["artikel_bis"] == "1899" and pruefung == []


def test_zechen_abgleichen_huske_entscheidet():
    zechen = [
        dict(name="Fridolin", stadtteil="Steele", lat="51.4389", lon="7.1105", betrieb_von="1836", betrieb_bis="1960",
             quelle="https://de.wikipedia.org/wiki/Zeche_Fridolin"),
        dict(name="Heinrich", stadtteil="Überruhr", lat="51.4183", lon="7.0747", betrieb_von="1809", betrieb_bis="1968",
             quelle="https://de.wikipedia.org/wiki/Zeche_Heinrich"),
    ]
    artikel = {"https://de.wikipedia.org/wiki/Zeche_Fridolin": ("", "1899"), "https://de.wikipedia.org/wiki/Zeche_Heinrich": ("1852", "1968")}
    huske = {("Fridolin", "Steele"): dict(huske_status="stillgelegt", grund="1882 zu Eiberg", url="https://p/1213126"),
             ("Heinrich", "Überruhr"): dict(huske_status="unklar", grund="Portaltext abgeschnitten (endet 1885)", url="https://p/1213325")}
    neu, pruefung = zechen_abgleichen(zechen, PLAN, artikel, huske)
    # Huske eindeutig → entscheidet, Wikipedia-Widerspruch wird nur vermerkt
    assert neu[0]["status_1936"] == "stillgelegt" and neu[0]["hinweis"].startswith("Huske (Portal): 1882 zu Eiberg")
    assert neu[0]["huske_url"] == "https://p/1213126"
    # Huske unklar → Wikipedia/Plan-Regel (Liste und Artikel aktiv, Plan fehlt in PLAN) mit Portal-Vermerk
    assert neu[1]["status_1936"] == "aktiv" and "Portal: Portaltext abgeschnitten" in neu[1]["hinweis"]
    assert pruefung == []
