"""Cache-Busting für den Pages-Schnappschuss (werkzeuge/deploy.sh).

GitHub Pages liefert mit max-age=600; ohne Marke kann ein Browser bis zu zehn Minuten nach einem Deploy
altes HTML mit neuen Modulen mischen (Absturz wie in 4294014). Deshalb bekommen im Schnappschuss alle
relativen Skript- und Stil-URLs `?v=<Commit>`, jede Seite mit Modul-Skript eine Import-Map, die die
relativen Modul-Importe (`./sidebar.js`) auf die markierten URLs umlenkt, und konfig.js die Marke, mit der
der Lader die Daten-URLs markiert. Der Arbeitsbaum bleibt unverändert; nur die Blobs im Deploy-Index ändern sich.
"""
import json
import re
import sys

_REL = re.compile(r'((?:src|href)=")(?!https?://|//|data:)([^"?#]+\.(?:js|css))(")')


def versioniere_html(html: str, version: str, module: list[str]) -> str:
    """Markiert relative .js/.css-URLs und setzt vor das erste Modul-Skript eine Import-Map über `module`
    (Pfade relativ zur Seite, z. B. "js/app.js"). Seiten ohne Modul-Skript bekommen keine Import-Map."""
    out = _REL.sub(lambda m: f"{m.group(1)}{m.group(2)}?v={version}{m.group(3)}", html)
    if "<script type=\"module\"" in out and module:
        imports = {f"./{p}": f"./{p}?v={version}" for p in sorted(module)}
        karte = "<script type=\"importmap\">" + json.dumps({"imports": imports}, ensure_ascii=False) + "</script>\n"
        out = out.replace("<script type=\"module\"", karte + "<script type=\"module\"", 1)
    return out


def versioniere_konfig(js: str, version: str) -> str:
    neu, n = re.subn(r'export const VERSION = "dev";', f'export const VERSION = "{version}";', js)
    if n != 1:
        raise ValueError("konfig.js hat keine Zeile 'export const VERSION = \"dev\";'")
    return neu


if __name__ == "__main__":   # Aufruf aus deploy.sh: versioniere.py html|konfig VERSION [modul …] < ein > aus
    art, version, *module = sys.argv[1:]
    text = sys.stdin.read()
    sys.stdout.write(versioniere_html(text, version, module) if art == "html" else versioniere_konfig(text, version))
