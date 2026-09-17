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


def test_norm_strasse_nbsp():
    # geschütztes Leerzeichen (U+00A0) wird zum normalen Leerzeichen
    assert norm_strasse("Bochumer\u00a0Str.") == "bochumer straße"
    assert norm_stadtteil("Altenessen\u00a0Nord") == "Altenessen Nord"


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
    ("Schönebeck", "Schönebeck"),   # eigener Stadtteil bei Borbeck, nicht der Vorort Schonnebeck
    ("Margarethenhöhe", "Margaretenhöhe"),
    ("Steele", "Steele"),
    ("Überruhr-Hinsel", "Überruhr-Hinsel"),
    ("Kettwig vor der Brücke", "Kettwig"),
])
def test_norm_stadtteil(roh, erwartet):
    assert norm_stadtteil(roh) == erwartet


# --- Schlüsselformen (Runde 5: Schreibvarianten) ---------------------------------
from pipeline.lib.normalisierung import schluesselformen


def _erste_gleiche_stufe(a: str, b: str):
    ka, kb = schluesselformen(a), schluesselformen(b)
    for i, (x, y) in enumerate(zip(ka, kb)):
        if x == y:
            return i
    return None


@pytest.mark.parametrize("a, b, stufe", [
    ("teißelsberg", "teisselsberg", 0),                    # ß/ss
    ("eickenscheidter straße", "eickenscheidterstraße", 1),  # Leerzeichen
    ("richard wagner straße", "richard-wagner-straße", 1),   # Bindestrich
    ("klementinenstraße", "clementinenstraße", 2),         # c/k
    ("kortstraße", "korthstraße", 2),                      # th/t
    ("yorkstraße", "yorckstraße", 2),                      # ck/k
    ("ueberruhrstraße", "überruhrstraße", 3),              # Umlaut-Umschrift
    ("phönixhütte", "phoenixhütte", 3),
    ("meyerstraße", "maierstraße", 3),                     # ei/ey/ai
    ("heidhausener straße", "heidhauser straße", 4),       # -ener/-er
    ("einigkeitstraße", "einigkeitsstraße", 4),            # Genitiv-s
    ("schederhoffstraße", "schederhofstraße", 4),          # Doppelbuchstabe
])
def test_schluesselformen_stufe(a, b, stufe):
    assert _erste_gleiche_stufe(a, b) == stufe


@pytest.mark.parametrize("a, b", [
    ("karlstraße", "kurtstraße"),
    ("hermannstraße", "hermann-göring-straße"),
    ("schulstraße", "schulweg"),
])
def test_schluesselformen_trennen_verschiedene_namen(a, b):
    assert _erste_gleiche_stufe(a, b) is None


def test_schluesselformen_sind_monoton_gleich_lang():
    assert len(schluesselformen("x")) == len(schluesselformen("eickenscheidter straße")) == 5
