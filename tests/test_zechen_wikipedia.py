from werkzeuge.zechen_wikipedia import parse_zechen

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
