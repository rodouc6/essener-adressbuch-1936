"""Rauchtests der Seite: python3 -m pytest tests/e2e -q -m e2e (braucht playwright + chromium und site/daten)."""
import pathlib, socket, subprocess, sys, time, urllib.request, urllib.error

import pytest

pytestmark = pytest.mark.e2e
W = pathlib.Path(__file__).resolve().parents[2]


def _freier_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0)); return s.getsockname()[1]


def _warte_auf_server(url, timeout=10.0):
    ablauf = time.time() + timeout
    letzter_fehler = None
    while time.time() < ablauf:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except (urllib.error.URLError, ConnectionError) as e:
            letzter_fehler = e
            time.sleep(0.1)
    raise RuntimeError(f"Server antwortet nicht unter {url}: {letzter_fehler}")


@pytest.fixture(scope="module")
def basis():
    if not (W / "site" / "daten" / "adressen.pmtiles").exists():
        pytest.skip("site/daten fehlt (Stufe 06 nicht gelaufen)")
    port = _freier_port()
    p = subprocess.Popen([sys.executable, str(W / "werkzeuge" / "serve.py"), str(port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    basis_url = f"http://127.0.0.1:{port}/site/"
    try:
        _warte_auf_server(basis_url + "index.html", timeout=15.0)
        yield basis_url
    finally:
        p.terminate()


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _seite(browser, breite=1200):
    s = browser.new_page(viewport={"width": breite, "height": 800})
    s.fehler = []
    s.on("pageerror", lambda e: s.fehler.append(str(e)))
    return s


def test_startseite_sucht_und_verlinkt(basis, browser):
    s = _seite(browser)
    s.goto(basis + "index.html")
    s.fill("#suche", "Sep")
    s.wait_for_selector("#vorschlaege .eintrag", timeout=5000)
    assert "PERSONEN" in s.inner_text("#vorschlaege").upper()
    assert s.get_attribute("#vorschlaege .eintrag", "href").startswith("karte.html?")
    assert s.fehler == []


def test_kartenseite_zeigt_punkte_und_hausansicht(basis, browser):
    s = _seite(browser)
    s.goto(basis + "karte.html?z=15&c=7.045,51.486")
    s.wait_for_function("window.karte && window.karte.map && window.karte.map.loaded && window.karte.map.loaded()", timeout=20000)
    s.wait_for_timeout(1500)
    n = s.evaluate("karte.map.queryRenderedFeatures({layers:['adressen-haus','adressen-ungenau']}).length")
    assert n > 20
    # "Sepan" (Karlstr. 70, Kray) ist ein Stadtplan-1935-Punkt ohne heutige Straße.
    s.fill("#suche", "Sepan")
    s.wait_for_selector("#vorschlaege .eintrag", timeout=5000)
    s.click("#vorschlaege .eintrag")
    s.wait_for_selector(".haus-kopf", timeout=8000)
    assert "Stadtplan 1935" in s.inner_text("#inhalt")
    assert "Faksimile" in s.inner_text("#inhalt")
    assert "id=" in s.url
    assert s.fehler == []


def test_urlzustand_und_stilwechsel(basis, browser):
    s = _seite(browser)
    s.goto(basis + "karte.html?ebene=II&karte=liberty&z=14&c=7.01,51.45")
    s.wait_for_function("window.karte && window.karte.map && window.karte.map.loaded && window.karte.map.loaded()", timeout=20000)
    assert s.get_attribute(".pill.II", "aria-pressed") == "true"
    assert s.get_attribute(".pill.I", "aria-pressed") == "false"
    s.click("#steuerung [data-karte]")
    s.wait_for_function("window.karte.map.getLayer('adressen-haus')", timeout=15000)
    assert "karte=liberty" not in s.url
    assert s.evaluate("!!karte.map.getLayer('adressen-haus')")
    assert s.fehler == []


def test_mobil_sheet(basis, browser):
    s = _seite(browser, breite=390)
    s.goto(basis + "karte.html")
    s.wait_for_function("window.karte && window.karte.map && window.karte.map.loaded && window.karte.map.loaded()", timeout=20000)
    assert s.get_attribute("#sidebar", "data-stufe") == "griff"
    s.click("#griff")
    assert s.get_attribute("#sidebar", "data-stufe") == "halb"
    assert s.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert s.fehler == []


def test_thema_besitz_legende_und_hausansicht(basis, browser):
    """Thema Besitz: Legende zeigt Kategorien; ein Haus mit geprüftem Eigentümer zeigt „Zugeordnet“."""
    import json
    s = _seite(browser)
    s.goto(basis + "karte.html?thema=besitz")
    s.wait_for_selector("#legende .zeile")
    legende = s.locator("#legende").inner_text()
    assert "Industrie" in legende and "ungeprüft" in legende
    liste = json.loads((W / "site" / "daten" / "suche" / "eigentuemer.json").read_text(encoding="utf-8"))
    if not liste:
        pytest.skip("noch kein geprüfter Eigentümer im Datenpaket")
    name = liste[0][1]
    s.goto(basis + "karte.html?thema=besitz&eigentuemer=" + name)
    s.wait_for_selector(".treffer")
    s.locator(".treffer").first.click()
    s.wait_for_selector(".eintrag")
    assert "Zugeordnet" in s.locator("#inhalt").inner_text()
    assert s.fehler == []
