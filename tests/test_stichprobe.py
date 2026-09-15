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
