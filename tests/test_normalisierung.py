import pytest
from pipeline.lib.normalisierung import VORORTE, norm_stadtteil, norm_strasse, norm_vorort


@pytest.mark.parametrize("roh, erwartet", [
    ("Karlstr.", "karlstraße"),
    ("Bochumer Str.", "bochumer straße"),
    ("Heidhausener Straße", "heidhausener straße"),
    ("Rellinghauser Strasse", "rellinghauser straße"),
    ("  Steeler  Str. ", "steeler straße"),
    ("Kl. Hammerstr.", "kleine hammerstraße"),
    ("Gr. Hammerstr.", "große hammerstraße"),
    ("Kopstadtpl.", "kopstadtplatz"),
    ("Herm.-Göring-Str.", "herm.-göring-straße"),
    ("Am krausen Bäumchen", "am krausen bäumchen"),
    ("Hermann–Göring–Straße", "hermann-göring-straße"),
    ("Luisenstr", "luisenstraße"),
    ("Bochumer Str", "bochumer straße"),
])
def test_norm_strasse(roh, erwartet):
    assert norm_strasse(roh) == erwartet


def test_norm_strasse_nfc():
    # "ä" als Kombinationszeichen (a + U+0308) muss zu NFC "ä" werden
    assert norm_strasse("Bäumchenweg") == "bäumchenweg"


def test_vororte_sind_zwoelf():
    assert len(VORORTE) == 12
    assert "Ueberruhr" in VORORTE and "Steele" in VORORTE


@pytest.mark.parametrize("roh, erwartet, ok", [
    ("Steele", "Steele", True),
    ("karnap", "Karnap", True),
    ("", "", True),
    ("Frillenburg", "Frillenburg", False),
    ("Überruhr", "Ueberruhr", True),
])
def test_norm_vorort(roh, erwartet, ok):
    assert norm_vorort(roh) == (erwartet, ok)


@pytest.mark.parametrize("roh, erwartet", [
    ("Stoppen- berg", "Stoppenberg"),
    ("Alten-essen-Süd", "Altenessen-Süd"),
    ("Ost-viertel", "Ostviertel"),
    ("Brenedey", "Bredeney"),
    ("Deltwig", "Dellwig"),
    ("Geschede", "Gerschede"),
    ("Schönnebeck", "Schonnebeck"),
    ("Schönebeck", "Schonnebeck"),
    ("Margarethenhöhe", "Margaretenhöhe"),
    ("Steele", "Steele"),
    ("Überruhr-Hinsel", "Überruhr-Hinsel"),
    ("Kettwig vor der Brücke", "Kettwig"),
])
def test_norm_stadtteil(roh, erwartet):
    assert norm_stadtteil(roh) == erwartet
