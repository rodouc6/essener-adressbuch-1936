import pytest

from werkzeuge.faksimile_mets import parse_seiten

METS = """<?xml version="1.0"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/">
  <mets:structMap TYPE="LOGICAL"><mets:div TYPE="periodical"/></mets:structMap>
  <mets:structMap TYPE="PHYSICAL">
    <mets:div TYPE="physSequence">
      <mets:div TYPE="page" ORDER="1" ORDERLABEL=" - "/>
      <mets:div TYPE="page" ORDER="355" ORDERLABEL="I. Teil:  333"/>
      <mets:div TYPE="page" ORDER="694" ORDERLABEL="II. Teil:  2"/>
      <mets:div TYPE="page" ORDER="1090" ORDERLABEL="III. Teil:  IV"/>
      <mets:div TYPE="page" ORDER="1091" ORDERLABEL="III. Teil:  5"/>
    </mets:div>
  </mets:structMap>
</mets:mets>"""


def test_parse_seiten_ordnet_gedruckte_seite_dem_bild_zu():
    z = parse_seiten(METS)
    assert [(x["seite"], x["bild"]) for x in z] == [("I-333", 355), ("II-002", 694), ("III-005", 1091)]
    assert z[0]["etikett"] == "I. Teil:  333"


def test_parse_seiten_weist_mehrdeutige_seiten_ab():
    doppelt = METS.replace('ORDER="694" ORDERLABEL="II. Teil:  2"', 'ORDER="694" ORDERLABEL="I. Teil:  333"')
    with pytest.raises(ValueError, match="mehrdeutig"):
        parse_seiten(doppelt)
