from werkzeuge.zechen_wikipedia import hole_koordinaten, parse_zechen

WIKI = """
{| class="wikitable sortable"
! Name !! Stadtteil !! Betrieb !! Koordinaten
|-
| [[Zeche Zollverein]] || [[Essen-Katernberg|Katernberg]] || 1851–1986 || {{Coordinate|text=DMS|NS=51.4861|EW=7.0447|type=landmark|region=DE-NW|name=Zollverein}}
|-
| [[Zeche Alt]] || Werden || 1800–1900 ||
|}
"""


def test_parse_zechen_liest_name_stadtteil_jahre_koordinaten():
    z = parse_zechen(WIKI)
    assert z[0]["name"] == "Zeche Zollverein" and z[0]["stadtteil"] == "Katernberg"
    assert (z[0]["betrieb_von"], z[0]["betrieb_bis"]) == ("1851", "1986")
    assert (z[0]["lat"], z[0]["lon"]) == ("51.4861", "7.0447")
    assert z[0]["quelle"] == "https://de.wikipedia.org/wiki/Zeche_Zollverein"
    assert z[1]["name"] == "Zeche Alt" and z[1]["lat"] == "" and z[1]["stadtteil"] == "Werden"


class _StubAntwort:
    """Simuliert eine requests.Response mit fest hinterlegtem JSON, ohne Netzwerk."""

    status_code = 200

    def __init__(self, daten):
        self._daten = daten

    def raise_for_status(self):
        pass

    def json(self):
        return self._daten


def test_hole_koordinaten_mit_und_ohne_treffer_und_ueber_redirect():
    # "Zeche A" hat direkt Koordinaten, "Zeche B" keine, "Alte Zeche" leitet auf "Zeche Ziel"
    # weiter, die Koordinaten hat — der ursprüngliche Titel "Alte Zeche" muss trotzdem
    # einen Treffer bekommen.
    antwort = _StubAntwort({
        "query": {
            "redirects": [{"from": "Alte Zeche", "to": "Zeche Ziel"}],
            "pages": {
                "1": {"title": "Zeche A", "coordinates": [{"lat": 51.4861, "lon": 7.0447, "primary": ""}]},
                "2": {"title": "Zeche B"},
                "3": {"title": "Zeche Ziel", "coordinates": [{"lat": 51.5, "lon": 7.1, "primary": ""}]},
            },
        }
    })

    aufrufe = []

    def fake_get(url, params, headers, timeout):
        aufrufe.append(params)
        return antwort

    ergebnis = hole_koordinaten(["Zeche A", "Zeche B", "Alte Zeche"], get=fake_get)

    assert ergebnis["Zeche A"] == ("51.4861", "7.0447")
    assert "Zeche B" not in ergebnis
    assert ergebnis["Alte Zeche"] == ("51.5", "7.1")
    assert len(aufrufe) == 1
    assert aufrufe[0]["titles"] == "Zeche A|Zeche B|Alte Zeche"
