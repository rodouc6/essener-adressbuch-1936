"""Ein- und Ausgabe: Pfade und CSV-Helfer."""
from __future__ import annotations

import csv
import os
from pathlib import Path

csv.field_size_limit(10**9)


def projektwurzel() -> Path:
    return Path(__file__).resolve().parents[2]


def strassen_dir() -> Path:
    env = os.environ.get("ESSENER_STRASSEN_DIR")
    if env:
        return Path(env)
    return (projektwurzel().parent / "essener-strassen" / "daten").resolve()


def lies_csv(pfad: Path | str, delimiter: str = ",") -> list[dict]:
    quoting = csv.QUOTE_NONE if delimiter == "\t" else csv.QUOTE_MINIMAL
    with open(pfad, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=delimiter, quoting=quoting))


def schreib_csv(pfad: Path | str, zeilen: list[dict], felder: list[str]) -> None:
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(zeilen)
