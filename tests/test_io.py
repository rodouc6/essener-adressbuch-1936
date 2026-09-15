from pathlib import Path
from pipeline.lib import io


def test_projektwurzel_enthaelt_pyproject():
    assert (io.projektwurzel() / "pyproject.toml").exists()


def test_strassen_dir_aus_umgebung(monkeypatch, tmp_path):
    monkeypatch.setenv("ESSENER_STRASSEN_DIR", str(tmp_path))
    assert io.strassen_dir() == tmp_path


def test_csv_roundtrip(tmp_path):
    pfad = tmp_path / "x.csv"
    io.schreib_csv(pfad, [{"a": "1", "b": "ä,ö"}], ["a", "b"])
    assert io.lies_csv(pfad) == [{"a": "1", "b": "ä,ö"}]


def test_lies_tsv_ohne_quoting(tmp_path):
    pfad = tmp_path / "x.tsv"
    pfad.write_text('a\tb\n1\t"x\n', encoding="utf-8")
    assert io.lies_csv(pfad, delimiter="\t") == [{"a": "1", "b": '"x'}]
