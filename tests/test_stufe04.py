import requests

from pipeline.lib.stufen import geokodiere_zeilen


class FakeClient:
    def __init__(self):
        self.n = 0

    def suche(self, params):
        self.n += 1
        if params["street"].startswith("5 "):
            return [{"lat": "1", "lon": "2", "osm_type": "way", "osm_id": "9", "class": "building", "type": "yes",
                     "display_name": "x", "address": {"house_number": "5", "road": "Bochumer Straße", "suburb": "Steele", "city": "Essen"}}]
        return []


def test_geokodiere_zeilen_dedupliziert_adressen():
    HERKUNFT = dict(herkunft="heutig", zeitlich_abweichend="nein", mehrdeutig="nein",
                    grund_mehrdeutig="", teilstrecke_abgetrennt="nein")
    z = [dict(id=str(i), strasse_heute="Bochumer Straße", hausnr="5", hausnr_zusatz="", stadtteil="Steele",
              parse_status="ok", strasse_roh="Bochumer Str.", **HERKUNFT) for i in range(3)]
    z.append(dict(id="x", strasse_heute="", hausnr="", hausnr_zusatz="", stadtteil="", parse_status="leer",
                  strasse_roh="", **dict(HERKUNFT, herkunft="offen")))
    c = FakeClient()
    out, adressen = geokodiere_zeilen(z, c, [], threads=2)
    assert [o["stufe"] for o in out] == ["haus", "haus", "haus", "offen"]
    assert c.n == 1
    assert len(adressen) == 2 and adressen[0]["zeilen"] == "3"


class FakeClientMitFehler:
    """Wirft für eine Adresse eine requests.RequestException, alle anderen funktionieren normal."""

    def suche(self, params):
        if params["street"].startswith("9 "):
            raise requests.RequestException("Verbindung fehlgeschlagen")
        if params["street"].startswith("5 "):
            return [{"lat": "1", "lon": "2", "osm_type": "way", "osm_id": "9", "class": "building", "type": "yes",
                     "display_name": "x", "address": {"house_number": "5", "road": "Bochumer Straße", "suburb": "Steele", "city": "Essen"}}]
        return []


def test_geokodiere_zeilen_faengt_request_exception_pro_adresse():
    z = [
        dict(strasse_heute="Bochumer Straße", hausnr="5", hausnr_zusatz="", stadtteil="Steele",
             parse_status="ok", strasse_roh="Bochumer Str.", herkunft="heutig",
             zeitlich_abweichend="nein", mehrdeutig="nein", grund_mehrdeutig="",
             teilstrecke_abgetrennt="nein"),
        dict(strasse_heute="Fehlerstraße", hausnr="9", hausnr_zusatz="", stadtteil="",
             parse_status="ok", strasse_roh="Fehlerstr.", herkunft="heutig",
             zeitlich_abweichend="nein", mehrdeutig="nein", grund_mehrdeutig="",
             teilstrecke_abgetrennt="nein"),
    ]
    out, adressen = geokodiere_zeilen(z, FakeClientMitFehler(), [], threads=2)
    stufen = {o["strasse_heute"]: (o["stufe"], o["grund"]) for o in out}
    assert stufen["Bochumer Straße"] == ("haus", "")
    assert stufen["Fehlerstraße"] == ("offen", "fehler")
    assert len(adressen) == 2


def test_adressschluessel_enthaelt_herkunftsfelder():
    """Herkunft, Zeitflag und Mehrdeutigkeit gehören zum Adressschlüssel, damit
    04_geokodiert.csv je Adresse eindeutig ist und 05 nicht nachjoinen muss."""
    from pipeline.lib.stufen import ADRESSSCHLUESSEL
    assert ADRESSSCHLUESSEL[-5:-1] == ["herkunft", "zeitlich_abweichend", "mehrdeutig", "grund_mehrdeutig"]


def test_adressen_mit_verschiedener_herkunft_bleiben_getrennt():
    basis = dict(strasse_heute="Bochumer Straße", hausnr="5", hausnr_zusatz="", stadtteil="Steele",
                 parse_status="ok", strasse_roh="Bochumer Str.", zeitlich_abweichend="nein",
                 mehrdeutig="nein", grund_mehrdeutig="", teilstrecke_abgetrennt="nein")
    z = [dict(basis, herkunft="heutig"), dict(basis, herkunft="kuratiert")]
    out, adressen = geokodiere_zeilen(z, FakeClient(), [], threads=2)
    assert len(adressen) == 2
    assert {a["herkunft"] for a in adressen} == {"heutig", "kuratiert"}


def test_adressschluessel_enthaelt_teilstrecke():
    from pipeline.lib.stufen import ADRESSFELDER, ADRESSSCHLUESSEL
    assert ADRESSSCHLUESSEL[-1] == "teilstrecke_abgetrennt"
    assert "teilstrecke_abgetrennt" in ADRESSFELDER
