import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.gruppen import FELDER_GRUPPEN, GRUPPEN, gruppe_export, gruppe_vorschlag, lade_gruppen
from werkzeuge.gruppen_vorschlag import baue_gruppen


def item(norm, gattung):
    return dict(norm=norm, gattung=gattung, niveau="fachlich", gattung_id="B 1")


def test_vokabular():
    assert list(GRUPPEN) == ["bergbau", "metall_maschinen", "bau", "holz_moebel", "textil_bekleidung", "lebensmittel", "handel",
                             "gastgewerbe", "verkehr_bahn_post", "verwaltung", "bildung_kultur_kirche", "gesundheit", "haus_reinigung", "sonstige"]
    assert FELDER_GRUPPEN == ["ohdab_id", "norm", "nennungen", "gruppe", "geprueft", "bearbeiter", "datum", "hinweis"]


def test_vorschlag_aus_gattung_und_norm():
    assert gruppe_vorschlag(item("Bergmann/-frau", "Berufe im Berg- und Tagebau – fachlich")) == "bergbau"
    assert gruppe_vorschlag(item("Kokereiarbeiter/in", "Berufe in der Kokerei")) == "bergbau"
    assert gruppe_vorschlag(item("Schlosser/in", "Berufe im Metallbau")) == "metall_maschinen"
    assert gruppe_vorschlag(item("Maurer/in", "Berufe im Hochbau")) == "bau"
    assert gruppe_vorschlag(item("Tischler/in", "Berufe in der Holz- und Möbelherstellung")) == "holz_moebel"
    assert gruppe_vorschlag(item("Schneider/in", "Berufe in der Bekleidungs-, Hut- und Mützenherstellung")) == "textil_bekleidung"
    assert gruppe_vorschlag(item("Bäcker/in", "Berufe in der Backwarenherstellung")) == "lebensmittel"
    assert gruppe_vorschlag(item("Kaufmann/-frau", "Kaufleute im Handel")) == "handel"
    assert gruppe_vorschlag(item("Gastwirt/in", "Berufe in der Gastronomie")) == "gastgewerbe"
    assert gruppe_vorschlag(item("Lokomotivführer/in", "Triebfahrzeugführer/innen im Eisenbahnverkehr")) == "verkehr_bahn_post"
    assert gruppe_vorschlag(item("Postbote/-botin", "Berufe für Post- und Zustelldienste")) == "verkehr_bahn_post"
    assert gruppe_vorschlag(item("Stadtsekretär/in", "Berufe in der öffentlichen Verwaltung")) == "verwaltung"
    assert gruppe_vorschlag(item("Lehrer/in", "Lehrkräfte in der Sekundarstufe")) == "bildung_kultur_kirche"
    assert gruppe_vorschlag(item("Pfarrer/in", "Theologen und Seelsorger")) == "bildung_kultur_kirche"
    assert gruppe_vorschlag(item("Arzt/Ärztin", "Ärzte/Ärztinnen")) == "gesundheit"
    assert gruppe_vorschlag(item("Hebamme", "Berufe in der Geburtshilfe")) == "gesundheit"
    assert gruppe_vorschlag(item("Hausangestellte/r", "Hauswirtschaftliche Berufe")) == "haus_reinigung"
    assert gruppe_vorschlag(item("Invalide/Invalidin", "Invalide")) == "sonstige"
    # Regression: „ausgerichtete“ (sehr häufig in Gattung-Texten wie „… fachlich ausgerichtete
    # Tätigkeiten“) enthält als Substring „gericht“ — ohne Wortgrenze landete das fälschlich in
    # „verwaltung“ statt in der eigentlich passenden Gruppe (hier: metall_maschinen).
    assert gruppe_vorschlag(item("Schlosser/in", "Berufe im Metallbau – fachlich ausgerichtete Tätigkeiten")) == "metall_maschinen"
    # Regression (Review Fix-Runde 2): dieselbe Fehlerklasse bei der nackten Alternative „bau“ —
    # ohne Wortgrenze trifft sie als Teilstring „Gartenbau“, „Gerätebau“ und „Ackerbauer“.
    assert gruppe_vorschlag(item("Gärtner/in", "Berufe im Gartenbau")) == "haus_reinigung"
    assert gruppe_vorschlag(item("Anlagenkonstrukteur/in", "Berufe in der Konstruktion und im Gerätebau")) == "metall_maschinen"
    assert gruppe_vorschlag(item("Ackerbauer/-bäuerin", "Berufe in der Landwirtschaft")) == "sonstige"
    # Regression (Review TP5a Task 2): „hauer“ ohne Wortgrenze zog Bildhauer, Feilenhauer, Steinhauer,
    # Trichinenschauer (über „schauer“) und Zimmerhauer fälschlich nach „bergbau“ — echte Bergbauberufe
    # tragen ohnehin eine Berg-/Tagebau-Gattung.
    assert gruppe_vorschlag(item("Bildhauer/in", "Berufe in der Bildhauerei – fachlich ausgerichtete Tätigkeiten")) != "bergbau"
    assert gruppe_vorschlag(item("Steinhauer/in - allgemein", "Berufe in der Naturstein- und Mineralaufbereitung – fachlich ausgerichtete Tätigkeiten")) != "bergbau"
    assert gruppe_vorschlag(item("Bergmann/-frau", "Berufe im Berg- und Tagebau – fachlich ausgerichtete Tätigkeiten")) == "bergbau"


def test_export_und_baue():
    assert gruppe_export(dict(gruppe="bergbau", geprueft="ja")) == "bergbau"
    assert gruppe_export(dict(gruppe="bergbau", geprueft="")) == "ungeprueft"
    berufe = [dict(schreibweise="Bergm.", nennungen="9", ohdab_id="B 21112-100", geprueft="ja"),
              dict(schreibweise="Bergarb.", nennungen="4", ohdab_id="B 21112-100", geprueft="ja"),
              dict(schreibweise="Kfm", nennungen="3", ohdab_id="", geprueft="")]
    ohdab = {"B 21112-100": dict(item("Bergmann/-frau", "Berufe im Berg- und Tagebau"), ohdab_id="B 21112-100")}
    alt = [dict(ohdab_id="B 21112-100", norm="Bergmann/-frau", nennungen="1", gruppe="metall_maschinen", geprueft="ja", bearbeiter="christos", datum="2026-09-25", hinweis="")]
    neu = baue_gruppen(berufe, ohdab, alt, "2026-09-26")
    assert neu == [dict(ohdab_id="B 21112-100", norm="Bergmann/-frau", nennungen="13", gruppe="metall_maschinen", geprueft="ja", bearbeiter="christos", datum="2026-09-25", hinweis="")]
    neu2 = baue_gruppen(berufe, ohdab, [], "2026-09-26")
    assert neu2[0]["gruppe"] == "bergbau" and neu2[0]["geprueft"] == "" and neu2[0]["bearbeiter"] == "gruppen_vorschlag"
    assert list(lade_gruppen(neu2)) == ["B 21112-100"]
