from pipeline.lib.stufen import geokodiere_zeilen


class FakeClient:
    def __init__(self):
        self.n = 0

    def suche(self, params):
        self.n += 1
        if params["street"].startswith("5 "):
            return [{"lat": "1", "lon": "2", "osm_type": "way", "osm_id": "9", "class": "building", "type": "yes",
                     "display_name": "x", "address": {"house_number": "5", "road": "Bochumer Straße", "suburb": "Steele"}}]
        return []


def test_geokodiere_zeilen_dedupliziert_adressen():
    z = [dict(id=str(i), strasse_heute="Bochumer Straße", hausnr="5", hausnr_zusatz="", stadtteil="Steele",
              parse_status="ok", strasse_roh="Bochumer Str.") for i in range(3)]
    z.append(dict(id="x", strasse_heute="", hausnr="", hausnr_zusatz="", stadtteil="", parse_status="leer", strasse_roh=""))
    c = FakeClient()
    out, adressen = geokodiere_zeilen(z, c, [], threads=2)
    assert [o["stufe"] for o in out] == ["haus", "haus", "haus", "offen"]
    assert c.n == 1
    assert len(adressen) == 2 and adressen[0]["zeilen"] == "3"
