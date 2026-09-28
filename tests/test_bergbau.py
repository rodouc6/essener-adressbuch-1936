import pathlib, sys
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.bergbau import GRUPPEN, RANG, NAMEN, lade_bergbau, pruefe_gegen_berufe, rang_gruppe
from pipeline.lib.io import lies_csv, projektwurzel

W = projektwurzel()


def test_konstanten():
    assert GRUPPEN == ("belegschaft", "aufsicht", "leitung", "invaliden")
    assert RANG == ("leitung", "aufsicht", "belegschaft", "invaliden")
    assert NAMEN["leitung"] == "Leitung und Beamte" and NAMEN["invaliden"] == "Berginvaliden"


def test_lade_bergbau_norm_zu_gruppe_und_fehler():
    t = lade_bergbau([dict(beruf="Bergmann", gruppe="belegschaft"), dict(beruf=" Steiger ", gruppe="aufsicht")])
    assert t == {"Bergmann": "belegschaft", "Steiger": "aufsicht"}
    with pytest.raises(ValueError, match="gruppe"):
        lade_bergbau([dict(beruf="Bergmann", gruppe="chef")])
    with pytest.raises(ValueError, match="doppelt"):
        lade_bergbau([dict(beruf="Bergmann", gruppe="belegschaft"), dict(beruf="Bergmann", gruppe="aufsicht")])
    with pytest.raises(ValueError, match="beruf"):
        lade_bergbau([dict(beruf="", gruppe="belegschaft")])


def test_pruefe_gegen_berufe_nennt_fehlende_normen():
    t = {"Bergmann": "belegschaft", "Erfundener": "aufsicht"}
    assert pruefe_gegen_berufe(t, [dict(beruf="Bergmann"), dict(beruf="Hauer")]) == ["Erfundener"]


def test_rang_gruppe():
    assert rang_gruppe({"n_bb_belegschaft": 3, "n_bb_aufsicht": 1}) == "aufsicht"
    assert rang_gruppe({"n_bb_invaliden": 1}) == "invaliden"
    assert rang_gruppe({"n_I": 4}) is None


def test_kuratierte_tabelle_passt_zu_berufe_csv():
    """Spec §2.2: jede Norm der Tabelle existiert in berufe.csv, keine Norm in zwei Gruppen."""
    t = lade_bergbau(lies_csv(W / "kuratierung" / "merkmale" / "bergbau.csv"))
    assert pruefe_gegen_berufe(t, lies_csv(W / "kuratierung" / "berufe.csv")) == []
    assert set(t.values()) == set(GRUPPEN)
