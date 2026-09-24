import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.ebenen import HEX_KANTE, aggregiere, hex_id, hex_polygon, hex_zelle, strassenschluessel, zaehlfelder


def _im_polygon(lon, lat, poly):
    innen = False
    for i in range(len(poly) - 1):
        (x1, y1), (x2, y2) = poly[i], poly[i + 1]
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            innen = not innen
    return innen


def test_hexzelle_enthaelt_punkt_und_ist_eindeutig():
    punkte = [(51.45, 7.01), (51.4501, 7.0101), (51.50, 6.95), (51.40, 7.10), (51.4512345, 7.0123456)]
    for lat, lon in punkte:
        q, r = hex_zelle(lat, lon)
        assert _im_polygon(lon, lat, hex_polygon(q, r)), (lat, lon, q, r)
    assert hex_zelle(51.45, 7.01) == (0, 0) and hex_id(0, 0) == "0_0" and hex_id(-3, 12) == "-3_12"
    poly = hex_polygon(0, 0)
    assert len(poly) == 7 and poly[0] == poly[-1]
    # Kantenlänge ≈ 120 m: Abstand gegenüberliegender Ecken = 2 · Kante
    (x1, y1), (x2, y2) = poly[0], poly[3]
    dy = (y2 - y1) * 111_320; dx = (x2 - x1) * 111_320 * math.cos(math.radians(51.45))
    assert abs(math.hypot(dx, dy) - 2 * HEX_KANTE) < 1.0


def _adresse(i, lat, lon, strasse="Grenzstraße", schl="00464", stadtteil="Katernberg", besitz="ungeprueft", eintraege=()):
    return dict(id=str(i), lat=lat, lon=lon, stadtteil=stadtteil, strasse_heute=strasse, hausnr="1", besitz=besitz,
                eintraege=[dict(teil=t, schl_nr=schl, strasse_roh="Grenzstr.", Vorort=stadtteil, _beruf=b, _gewerbe=g) for t, b, g in eintraege])


def test_zaehlfelder_und_aggregation():
    b1 = dict(niveau="fachlich", stellung="arbeiter", gruppe="bergbau")
    b2 = dict(niveau="unsicher", stellung="unbestimmt", gruppe="ungeprueft")
    g1 = dict(gruppe="lebensmittel", art="handwerk", schluessel="a|x|1|")
    a1 = _adresse(1, 51.45, 7.01, besitz="privatperson", eintraege=[("I", b1, None), ("I", b1, None), ("I", b2, None), ("II", None, None), ("III", None, g1), ("III", None, g1)])
    a2 = _adresse(2, 51.4501, 7.0101, besitz="bergbau", eintraege=[("I", b1, None), ("I", None, None)])
    a3 = _adresse(3, 51.40, 7.10, strasse="Heckstraße", schl="01226", stadtteil="Werden", eintraege=[("I", b2, None)])
    z = zaehlfelder(a1)
    assert z == {"n_I": 3, "n_II": 1, "n_III": 2, "n_fachlich": 2, "n_unsicher": 1, "n_st_arbeiter": 2, "n_st_unbestimmt": 1,
                 "n_gr_bergbau": 2, "n_gr_ungeprueft": 1, "n_gw_lebensmittel": 1, "n_gwa_handwerk": 1, "n_bs_privatperson": 1}
    assert zaehlfelder(a2)["n_st_unbestimmt"] == 1        # Eintrag ohne geprüften Beruf zählt als unbestimmt
    adressen = {a["id"]: a for a in (a1, a2, a3)}
    st = aggregiere(adressen, "strasse")
    assert [s["id"] for s in st] == ["00464", "01226"]
    assert st[0] == {"id": "00464", "name": "Grenzstraße", "stadtteil": "Katernberg", "adressen": 2, "n_I": 5, "n_II": 1, "n_III": 2,
                     "n_fachlich": 3, "n_unsicher": 1, "n_st_arbeiter": 3, "n_st_unbestimmt": 2, "n_gr_bergbau": 3, "n_gr_ungeprueft": 2,
                     "n_gw_lebensmittel": 1, "n_gwa_handwerk": 1, "n_bs_privatperson": 1, "n_bs_bergbau": 1}
    sd = aggregiere(adressen, "stadtteil")
    assert [s["id"] for s in sd] == ["Katernberg", "Werden"] and sd[0]["lat"] == round((51.45 + 51.4501) / 2, 5) and sd[0]["rang_nord"] == 1 and sd[1]["rang_nord"] == 2
    hx = aggregiere(adressen, "hex")
    assert sum(h["adressen"] for h in hx) == 3 and all(h["id"] == hex_id(*hex_zelle(h["lat"], h["lon"])) for h in hx)
    assert strassenschluessel(_adresse(9, 51.4, 7.0, strasse="", schl="", eintraege=[("I", None, None)])) == ("1936:Grenzstr.|Katernberg", "Grenzstr. (1936)")
