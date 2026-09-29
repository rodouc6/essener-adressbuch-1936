from werkzeuge.versioniere import versioniere_html, versioniere_konfig


HTML = ('<head><link rel="stylesheet" href="css/stil.css"><link rel="stylesheet" href="vendor/maplibre-gl.css"></head>'
        '<body><script src="vendor/pmtiles.js"></script><script type="module" src="js/app.js"></script></body>')


def test_versioniere_html_markiert_skripte_und_stile_und_setzt_import_map():
    out = versioniere_html(HTML, "abc1234", ["js/app.js", "js/karte.js", "js/formen/balken.js"])
    assert 'href="css/stil.css?v=abc1234"' in out
    assert 'href="vendor/maplibre-gl.css?v=abc1234"' in out
    assert 'src="vendor/pmtiles.js?v=abc1234"' in out
    assert 'src="js/app.js?v=abc1234"' in out
    # Import-Map vor dem ersten Modul-Skript, alle Module mit Marke, Schlüssel relativ zur Seite
    ip = out.index('<script type="importmap">')
    assert ip < out.index('<script type="module"')
    assert '"./js/karte.js": "./js/karte.js?v=abc1234"' in out
    assert '"./js/formen/balken.js": "./js/formen/balken.js?v=abc1234"' in out


def test_versioniere_html_laesst_externe_urls_und_seiten_ohne_module_in_ruhe():
    html = '<a href="https://example.org/x.js">x</a><script src="https://cdn.example/lib.js"></script>'
    assert versioniere_html(html, "abc1234", ["js/app.js"]) == html


def test_versioniere_html_inline_modul_bekommt_import_map():
    html = '<script type="module">import { Lader } from "./js/daten.js";</script>'
    out = versioniere_html(html, "abc1234", ["js/daten.js"])
    assert out.index('<script type="importmap">') < out.index('<script type="module">')


def test_versioniere_konfig_ersetzt_dev_marke():
    js = 'export const DATEN = "daten/";\nexport const VERSION = "dev";\n'
    assert 'export const VERSION = "abc1234";' in versioniere_konfig(js, "abc1234")
    assert "dev" not in versioniere_konfig(js, "abc1234")
