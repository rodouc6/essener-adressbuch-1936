import random

from werkzeuge.stichprobe import ziehe_gezielt, grenzen_aus_zuordnung


def adr(**kw):
    basis = dict(stufe="haus", strasse_roh="X", hausnr="1", hausnr_zusatz="", stadtteil="", strasse_heute="S",
                 display_name="", lat="1", lon="2", herkunft="heutig", vorort_angenommen="nein",
                 nummer_unsicher="nein", teilstrecke_abgetrennt="nein")
    basis.update(kw)
    return basis


def test_grenzen_aus_zuordnung():
    z = [{"strasse_roh_norm": "a", "strasse_heute": "A", "hausnr_von": "1", "hausnr_bis": "323"},
         {"strasse_roh_norm": "a", "strasse_heute": "B", "hausnr_von": "324", "hausnr_bis": ""},
         {"strasse_roh_norm": "k", "strasse_heute": "K", "hausnr_von": "", "hausnr_bis": ""}]
    assert grenzen_aus_zuordnung(z) == {"A": {323}, "B": {324}}


def test_ziehe_gezielt_gruppen_und_umfang():
    adressen = (
        [adr(strasse_roh=f"k{i}", vorort_angenommen="ja") for i in range(60)]
        + [adr(strasse_roh=f"b{i}", herkunft="kuratiert", strasse_heute="A", hausnr=str(309 + i)) for i in range(30)]
        + [adr(strasse_roh=f"w{i}", herkunft="kuratiert", strasse_heute="A", hausnr=str(i + 1)) for i in range(50)]
        + [adr(strasse_roh=f"t{i}", teilstrecke_abgetrennt="ja", strasse_heute="Beuststraße") for i in range(30)]
        + [adr(strasse_roh="unberührt")]
    )
    probe = ziehe_gezielt(adressen, {"A": {323}}, ["Beuststraße"], seed=1)
    gruppen = {}
    for p in probe:
        gruppen.setdefault(p["gruppe"], []).append(p)
    assert len(gruppen["kernstadt_angenommen"]) == 40
    assert len(gruppen["bereichsgrenze"]) == 40
    assert len(gruppen["teilstrecke_neu"]) == 20
    # Grenznahe zuerst: alle 30 Adressen im Streifen ±15 um 323 sind drin, Rest aufgefüllt
    nahe = [p for p in gruppen["bereichsgrenze"] if abs(int(p["hausnr"]) - 323) <= 15]
    assert len(nahe) == 30
    assert all(p["urteil"] == "" for p in probe)
    assert "unberührt" not in {p["strasse_roh"] for p in probe}


def test_ziehe_gezielt_ist_reproduzierbar():
    adressen = [adr(strasse_roh=f"k{i}", vorort_angenommen="ja") for i in range(100)]
    a = ziehe_gezielt(adressen, {}, [], seed=7)
    b = ziehe_gezielt(adressen, {}, [], seed=7)
    assert [p["strasse_roh"] for p in a] == [p["strasse_roh"] for p in b]


def test_ziehe_paare_grosse_paare_je_eine_adresse_und_rest_zufaellig():
    from werkzeuge.stichprobe import ziehe_paare
    from pipeline.lib.normalisierung import norm_strasse
    paare = [{"strasse_norm": norm_strasse(f"Probe{i}str."), "strasse_heute": f"H{i}", "zeilen": str(100 - i)}
             for i in range(50)]
    adressen = []
    for i in range(50):
        adressen += [adr(strasse_roh=f"Probe{i}str.", strasse_heute=f"H{i}", hausnr=str(h)) for h in range(1, 6)]
    adressen.append(adr(strasse_roh="Fremdstr.", strasse_heute="F"))
    probe = ziehe_paare(adressen, paare, seed=3)
    gross = [p for p in probe if p["gruppe"] == "neu_gross"]
    rest = [p for p in probe if p["gruppe"] == "neu_rest"]
    assert len(gross) == 40 and len(rest) == 20
    # je großes Paar genau eine Adresse, und zwar aus den 40 zeilenstärksten
    assert sorted(p["strasse_heute"] for p in gross) == sorted(f"H{i}" for i in range(40))
    assert {p["strasse_heute"] for p in rest} <= {f"H{i}" for i in range(40, 50)}
    assert "F" not in {p["strasse_heute"] for p in probe}


def test_ziehe_paare_bevorzugt_hausebene_und_verortete():
    from werkzeuge.stichprobe import ziehe_paare
    paare = [{"strasse_norm": "astraße", "strasse_heute": "A", "zeilen": "9"}]  # norm_strasse("Astr.")
    adressen = [adr(strasse_roh="Astr.", strasse_heute="A", stufe="offen", lat="", lon=""),
                adr(strasse_roh="Astr.", strasse_heute="A", stufe="strasse", hausnr="2"),
                adr(strasse_roh="Astr.", strasse_heute="A", stufe="haus", hausnr="3")]
    probe = ziehe_paare(adressen, paare, seed=1)
    assert [p["stufe"] for p in probe] == ["haus"]
