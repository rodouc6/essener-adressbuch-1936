# Adressbuch Essen 1936 — Datenpipeline (v2)

Erzeugt aus dem DES-Export des Essener Adreßbuchs 1936 (`data/essen1936.csv`, Tab-getrennt)
eine geokodierte Tabelle mit ausgewiesener Präzisionsstufe je Eintrag.

## Voraussetzungen
- Python ≥ 3.12, `pip install -e .[test]`
- Lokale Nominatim-Instanz unter `http://localhost:8080` (NRW-Extrakt)
- Straßendatensatz `essener-strassen` (Umgebungsvariable `ESSENER_STRASSEN_DIR`, Standard `../essener-strassen/daten`)

## Aufruf
```
python3 pipeline/01_einlesen.py
python3 pipeline/02_adresse_parsen.py
python3 pipeline/03_strasse_aufloesen.py
python3 pipeline/04_geokodieren.py
python3 pipeline/05_bericht.py
```
Ausgaben liegen in `build/` (löschbar). Vom Menschen gepflegte Tabellen in `kuratierung/`.

Spezifikation und Plan: `docs/superpowers/`. Projektdokumentation liegt im Obsidian-Vault des Projekts.
