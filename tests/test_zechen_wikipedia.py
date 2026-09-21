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
    # ein führendes "Zeche " wird im Namen vereinheitlicht entfernt (quelle bleibt unberührt)
    assert z[0]["name"] == "Zollverein" and z[0]["stadtteil"] == "Katernberg"
    assert (z[0]["betrieb_von"], z[0]["betrieb_bis"]) == ("1851", "1986")
    assert (z[0]["lat"], z[0]["lon"]) == ("51.4861", "7.0447")
    assert z[0]["quelle"] == "https://de.wikipedia.org/wiki/Zeche_Zollverein"
    assert z[1]["name"] == "Alt" and z[1]["lat"] == "" and z[1]["stadtteil"] == "Werden"


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

    ergebnis = hole_koordinaten(["Zeche A", "Zeche B", "Alte Zeche"], get=fake_get, pause=0)

    assert ergebnis["Zeche A"] == ("51.4861", "7.0447")
    assert "Zeche B" not in ergebnis
    assert ergebnis["Alte Zeche"] == ("51.5", "7.1")
    assert len(aufrufe) == 1
    assert aufrufe[0]["titles"] == "Zeche A|Zeche B|Alte Zeche"


def test_hole_koordinaten_folgt_continue_ueber_mehrere_anfragen():
    # prop=coordinates liefert pro Anfrage nur eine begrenzte Zahl Koordinaten zurück und
    # setzt ein "continue"-Token, auch innerhalb eines einzigen Titel-Stapels; hole_koordinaten
    # muss diesem Token folgen, bis alle Titel im Stapel eine Antwort bekommen haben.
    erste_antwort = _StubAntwort({
        "continue": {"cocontinue": "5|100", "continue": "||"},
        "query": {
            "pages": {
                "1": {"title": "Zeche A", "coordinates": [{"lat": 51.4, "lon": 7.0, "primary": ""}]},
            },
        },
    })
    zweite_antwort = _StubAntwort({
        "query": {
            "pages": {
                "2": {"title": "Zeche B", "coordinates": [{"lat": 51.5, "lon": 7.1, "primary": ""}]},
            },
        },
    })

    aufrufe = []

    def fake_get(url, params, headers, timeout):
        aufrufe.append(params)
        return erste_antwort if len(aufrufe) == 1 else zweite_antwort

    ergebnis = hole_koordinaten(["Zeche A", "Zeche B"], get=fake_get, pause=0)

    assert ergebnis["Zeche A"] == ("51.4", "7.0")
    assert ergebnis["Zeche B"] == ("51.5", "7.1")
    assert len(aufrufe) == 2
    assert "cocontinue" not in aufrufe[0] and "continue" not in aufrufe[0]
    assert aufrufe[1]["cocontinue"] == "5|100"
    assert aufrufe[1]["continue"] == "||"
    assert aufrufe[1]["titles"] == "Zeche A|Zeche B"
