# Bergbau-Kapitel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Kapitel 4 „Bergbau 1936“ der Schlaglichter mit einer neuen Punktkarten-Form (Hexfeld, vier Gruppen, Übergang aus gepackten Kreisen), dazu das Thema „Bergbau“ mit schaltbaren Klassen auf der Hauptkarte.

**Architecture:** Die Pipeline liest eine kuratierte Tabelle Norm → Gruppe, schreibt vier Zählfelder `n_bb_*` je Adresse/Straße/Stadtteil/Hexfeld, ein Rangfeld `bergbau` je Adresse und eine vorgepackte Kapiteldatei. Die Site bekommt die Form `punktkarte` (SVG, `zeige` + `aktualisiere` für fließende Übergänge), das Kapitel-JSON und ein Thema mit Legendenschaltern, dessen Filter und Farbausdruck rein in `themen.js` gebaut werden.

**Tech Stack:** Python 3.12 (Pipeline, pytest), ES-Module ohne Bundler, `node --test site/tests/*.test.js`, MapLibre GL (vendored), Scrollama, Playwright (Python) im Scratchpad für Sichtprüfungen.

**Spec:** `docs/superpowers/specs/2026-09-28-bergbau-kapitel-design.md`

## Global Constraints

- Precision first: keine Zahl ohne Grundlage, Grenzfälle benannt, ungeprüfte Berufe als Ausschluss sichtbar (Spec §1).
- Bezugsgröße heißt in allen Texten „eingetragene Personen“ oder „Einträge des Einwohnerverzeichnisses“, nie „Haushaltsvorstand“ (Spec §2.1).
- Gruppen: `belegschaft | aufsicht | leitung | invaliden`; Rang `leitung > aufsicht > belegschaft > invaliden` (Spec §2.2, §2.3).
- Kapitelfarben: Belegschaft `#c2410c`, Aufsicht `#1d4ed8`, Leitung und Beamte `#7c3aed`, Berginvaliden `#15803d` (Spec §3).
- Hexfeld 120 m Kante; Kreisfläche = absolute Zahl; kein `min_n` in der Punktkarte (Spec §1).
- Radius auf der Karte `max(1.6, 0.62 · r_packung)`; hausgenaue Punkte Radius 2.4, Ring bei `stufe ≠ haus` (Spec §4).
- Kapitel `freigegeben: false` bis der Projektleiter die Texte schreibt (Spec §6).
- `PLAN_FREIGEGEBEN` in `site/js/konfig.js` bleibt `false`; kein Push ohne Nachfrage.
- Tests: `python3 -m pytest -q` und `node --test site/tests/*.test.js` (Node 22 kann keine Verzeichnisform).
- Commits enden mit `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

## Review Focus

1. Thema „Bergbau“ mit `klassen=leitung`, Haus mit Bergmann und Zechenbeamtem: der Punkt bleibt sichtbar und lila (Rang), ein Haus nur mit Bergmann fällt weg — Test in Task 8 (`schalterFilter`/`schalterFarbe`).
2. `?klassen=…` ohne Thema oder mit einem Thema ohne `schalter` (Besitz): kein Filter, keine Fehlermeldung, Karte wie bisher — Test in Task 8 (`farbregel` ohne Schalter ignoriert klassen).
3. Kapitelschritt mit `punkte.hervor` auf einen Namen, der keine Gruppe ist: kein Kreis wird gedimmt, kein Fehler — Test in Task 5 (`normalisiere` filtert `hervor`).
4. Bühne schmaler als 600 px (Handy): vier Karten untereinander, keine Karte über den Rand — Test in Task 6 (`raster(500)` liefert 1 Spalte).
5. Adresse in Teil I ohne geprüften Beruf: kein Feld `bergbau`, kein `n_bb_*`, zählt weiter in `n_gr_ungeprueft` — Test in Task 2 (`zaehlfelder`).

---

### Task 1: Eigentümer-Zusammenführung (König Wilhelm, Mülheimer Bergwerks-Verein, Carolus Magnus)

**Files:**
- Modify: `kuratierung/eigentuemer.csv` (Zeilen 1175, 1308, 1309, 1523 und alle mit `Mühlheimer Bergwerks-Verein`, `Gewerkschft Zeche Carolus Magnus`)
- Test: `tests/test_eigentuemer.py`

**Interfaces:**
- Consumes: `pipeline.lib.eigentuemer.lade_kuratierung(zeilen)`, `pipeline.lib.io.lies_csv`
- Produces: kanonische Namen `Essener Bergwerks-Verein König Wilhelm`, `Mülheimer Bergwerks-Verein`, `Gewerkschaft Zeche Carolus Magnus` (Task 3 und Task 4 verlassen sich auf diese Schreibungen)

- [ ] **Step 1: Failing test — kanonische Bergbau-Namen sind eindeutig**

Am Ende von `tests/test_eigentuemer.py` anhängen:

```python
def test_kuratierung_bergbau_kanonische_namen_ohne_dubletten():
    """Spec Bergbau §2.5: ein kanonischer Name je Gesellschaft — sonst zählt das Kapitel eine Gesellschaft mehrfach."""
    from pipeline.lib.io import lies_csv, projektwurzel
    zeilen = lies_csv(projektwurzel() / "kuratierung" / "eigentuemer.csv")
    kanon = {z["eigentuemer"].strip() for z in zeilen if z.get("kategorie") == "bergbau" and z.get("geprueft") == "ja"}
    assert [k for k in kanon if "König Wilhelm" in k] == ["Essener Bergwerks-Verein König Wilhelm"]
    assert [k for k in kanon if "lheimer Bergwerks" in k] == ["Mülheimer Bergwerks-Verein"]
    assert "Gewerkschft Zeche Carolus Magnus" not in kanon and "Gewerkschaft Zeche Carolus Magnus" in kanon
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_eigentuemer.py -k kanonische_namen`
Expected: FAIL — die Liste enthält vier König-Wilhelm-Namen.

- [ ] **Step 3: Tabelle bereinigen (nur die Spalte `eigentuemer`, Schreibweisen bleiben)**

```bash
cd /home/christos/Projekte/essener-adressbuch-1936
python3 - <<'EOF'
import csv
p = "kuratierung/eigentuemer.csv"
rows = list(csv.DictReader(open(p, encoding="utf-8")))
ziel = {"Ss. Bergw. Verein König Wilhelm": "Essener Bergwerks-Verein König Wilhelm",
        "Essen. Bergwerksverein König Wilhelm": "Essener Bergwerks-Verein König Wilhelm",
        "Mühlheimer Bergwerksverein": "Mülheimer Bergwerks-Verein",
        "Mühlheimer Bergwerks-Verein": "Mülheimer Bergwerks-Verein",
        "Gewerkschft Zeche Carolus Magnus": "Gewerkschaft Zeche Carolus Magnus"}
n = 0
for r in rows:
    if r["eigentuemer"].strip() in ziel:
        r["eigentuemer"] = ziel[r["eigentuemer"].strip()]; r["datum"] = "2026-09-28"; n += 1
with open(p, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n"); w.writeheader(); w.writerows(rows)
print("geändert:", n)
EOF
git diff --stat kuratierung/eigentuemer.csv
```

Expected: „geändert:“ etwa 30 Zeilen; `git diff` zeigt nur die Spalten `eigentuemer` und `datum`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_eigentuemer.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add kuratierung/eigentuemer.csv tests/test_eigentuemer.py
git commit -m "fix(kuratierung): Eigentümer-Dubletten zusammengeführt — König Wilhelm (4 Namen), Mülheimer Bergwerks-Verein (2), Tippfehler Carolus Magnus

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Bergbau-Tabelle, Zählfelder `n_bb_*`, Rangfeld, Kennzahlen

**Files:**
- Create: `kuratierung/merkmale/bergbau.csv`, `pipeline/lib/bergbau.py`, `tests/test_bergbau.py`
- Modify: `pipeline/lib/ebenen.py:57-84` (`zaehlfelder`), `pipeline/lib/karte_export.py:190-232` (`gruppiere`), `:270-284` (`punkt_feature`), `:474-524` (`baue_kennzahlen`), `:820-840` (`schreibe_paket`), `pipeline/06_karte_export.py:30-56`, `pipeline/lib/merkmale.py:26-43` (`lade_regeln` überspringt `bergbau.csv`)
- Test: `tests/test_bergbau.py`, `tests/test_ebenen.py`, `tests/test_karte_export.py`

**Interfaces:**
- Consumes: `pipeline.lib.berufe.zuordnung` liefert `beruf` (Norm) je Eintrag; `zaehlfelder(a)`; `falte`
- Produces: `pipeline.lib.bergbau.GRUPPEN`, `RANG`, `NAMEN`, `lade_bergbau(zeilen) -> dict[str, str]`, `pruefe_gegen_berufe(tabelle, berufe_zeilen) -> list[str]`, `rang_gruppe(zaehl: dict) -> str | None`; Zählfelder `n_bb_<gruppe>` in `zaehlfelder`; Eintragsfeld `_beruf["bergbau"]`; Punktfeld `bergbau`; Kennzahlen `bergbau_n`, `bergbau_belegschaft_n`, `bergbau_aufsicht_n`, `bergbau_leitung_n`, `bergbau_invaliden_n`, `bergbau_haeuser_n`; `schreibe_paket(..., bergbau=list[dict] | None)`

- [ ] **Step 1: Tabelle anlegen**

`kuratierung/merkmale/bergbau.csv` (Spec §2.2; `geprueft` leer, `hinweis` bei Grenzfällen):

```csv
beruf,gruppe,geprueft,bearbeiter,datum,hinweis
Bergmann,belegschaft,,claude,2026-09-28,
Hauer,belegschaft,,claude,2026-09-28,
Bergarbeiter,belegschaft,,claude,2026-09-28,
Zechenarbeiter,belegschaft,,claude,2026-09-28,
Fördermaschinist,belegschaft,,claude,2026-09-28,
Anschläger,belegschaft,,claude,2026-09-28,
Kettenanschläger,belegschaft,,claude,2026-09-28,
Schachthauer,belegschaft,,claude,2026-09-28,
Fahrhauer,belegschaft,,claude,2026-09-28,
Lehrhauer,belegschaft,,claude,2026-09-28,
Grubenschlosser,belegschaft,,claude,2026-09-28,
Zechenschmied,belegschaft,,claude,2026-09-28,
Zechenschreiner,belegschaft,,claude,2026-09-28,
Zechenschlosser,belegschaft,,claude,2026-09-28,
Bergtagelöhner,belegschaft,,claude,2026-09-28,
Schießhauer,belegschaft,,claude,2026-09-28,
Gesteinshauer,belegschaft,,claude,2026-09-28,
Zechenbote,belegschaft,,claude,2026-09-28,
Kokereiarbeiter,belegschaft,,claude,2026-09-28,Grenzfall: Kokerei meist Betriebsteil der Zeche
Koksarbeiter,belegschaft,,claude,2026-09-28,Grenzfall: Kokerei meist Betriebsteil der Zeche
Schlepper,belegschaft,,claude,2026-09-28,Grenzfall: im Ruhrbergbau Bergbau-Beruf; OhdAB führt ihn unter Verkehr (B 5131)
Steiger,aufsicht,,claude,2026-09-28,
Fahrsteiger,aufsicht,,claude,2026-09-28,
Fahrsteig.,aufsicht,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Maschinensteiger,aufsicht,,claude,2026-09-28,
Maschinensteig.,aufsicht,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Obersteiger,aufsicht,,claude,2026-09-28,
Reviersteiger,aufsicht,,claude,2026-09-28,
Reviersteig.,aufsicht,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Grubensteiger,aufsicht,,claude,2026-09-28,
Grubensteig.,aufsicht,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Elektrosteiger,aufsicht,,claude,2026-09-28,
Wettersteiger,aufsicht,,claude,2026-09-28,
Schießmeister,aufsicht,,claude,2026-09-28,
Förderaufseher,aufsicht,,claude,2026-09-28,
Koksmeister,aufsicht,,claude,2026-09-28,
Lampenmeister,aufsicht,,claude,2026-09-28,
Schachtaufseh.,aufsicht,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Bohrmeister,aufsicht,,claude,2026-09-28,
Obermaschinenmeister,aufsicht,,claude,2026-09-28,
Zechenbeamter,leitung,,claude,2026-09-28,
Grubenbeamter,leitung,,claude,2026-09-28,
Bergbeamter,leitung,,claude,2026-09-28,
Bergwerksbeamter,leitung,,claude,2026-09-28,
kaufmännischer Grubenbeamter,leitung,,claude,2026-09-28,
Bergassess.,leitung,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Bergassessor,leitung,,claude,2026-09-28,
Bergrat,leitung,,claude,2026-09-28,
Bergwerksdirektor,leitung,,claude,2026-09-28,
Bergwerksunternehm.,leitung,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Grubeninspektor,leitung,,claude,2026-09-28,
Bergrevierinspekt.,leitung,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Markscheider,leitung,,claude,2026-09-28,
Markscheiderassistent,leitung,,claude,2026-09-28,
Bergbauingenieur,leitung,,claude,2026-09-28,
Kokereiassist.,leitung,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Zechenangest.,leitung,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Bergbauangest.,leitung,,claude,2026-09-28,abgekürzte Normvariante in berufe.csv
Oberschaffner,leitung,,claude,2026-09-28,Grenzfall: OhdAB B 2111; Bedeutung im Bergbau unklar
Berginvalide,invaliden,,claude,2026-09-28,
```

- [ ] **Step 2: Failing tests für das Modul**

`tests/test_bergbau.py`:

```python
import pathlib, sys
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from pipeline.lib.bergbau import GRUPPEN, RANG, NAMEN, lade_bergbau, pruefe_gegen_berufe, rang_gruppe
from pipeline.lib.io import lies_csv, projektwurzel

W = projektwurzel()


def test_konstanten():
    assert GRUPPEN == ("belegschaft", "aufsicht", "leitung", "invaliden")
    assert RANG == ("leitung", "aufsicht", "belegschaft", "invaliden")
    assert NAMEN["leitung"] == "Leitung und Beamte" and NAMEN["invaliden"] == "Berginvaliden"


def test_lade_bergbau_norm_zu_gruppe_und_fehler():
    t = lade_bergbau([dict(beruf="Bergmann", gruppe="belegschaft"), dict(beruf=" Steiger ", gruppe="aufsicht")])
    assert t == {"Bergmann": "belegschaft", "Steiger": "aufsicht"}
    with pytest.raises(ValueError, match="gruppe"):
        lade_bergbau([dict(beruf="Bergmann", gruppe="chef")])
    with pytest.raises(ValueError, match="doppelt"):
        lade_bergbau([dict(beruf="Bergmann", gruppe="belegschaft"), dict(beruf="Bergmann", gruppe="aufsicht")])
    with pytest.raises(ValueError, match="beruf"):
        lade_bergbau([dict(beruf="", gruppe="belegschaft")])


def test_pruefe_gegen_berufe_nennt_fehlende_normen():
    t = {"Bergmann": "belegschaft", "Erfundener": "aufsicht"}
    assert pruefe_gegen_berufe(t, [dict(beruf="Bergmann"), dict(beruf="Hauer")]) == ["Erfundener"]


def test_rang_gruppe():
    assert rang_gruppe({"n_bb_belegschaft": 3, "n_bb_aufsicht": 1}) == "aufsicht"
    assert rang_gruppe({"n_bb_invaliden": 1}) == "invaliden"
    assert rang_gruppe({"n_I": 4}) is None


def test_kuratierte_tabelle_passt_zu_berufe_csv():
    """Spec §2.2: jede Norm der Tabelle existiert in berufe.csv, keine Norm in zwei Gruppen."""
    t = lade_bergbau(lies_csv(W / "kuratierung" / "merkmale" / "bergbau.csv"))
    assert pruefe_gegen_berufe(t, lies_csv(W / "kuratierung" / "berufe.csv")) == []
    assert set(t.values()) == set(GRUPPEN)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m pytest -q tests/test_bergbau.py`
Expected: FAIL mit `ModuleNotFoundError: pipeline.lib.bergbau`

- [ ] **Step 4: Modul schreiben**

`pipeline/lib/bergbau.py`:

```python
"""Bergbau-Gruppen je Berufsnorm (Spec 2026-09-28 §2.2/§2.3): kuratierte Tabelle kuratierung/merkmale/bergbau.csv
(Spalten beruf, gruppe, geprueft, bearbeiter, datum, hinweis). `beruf` ist die Norm aus berufe.csv, nicht die
Schreibweise. Keine OhdAB-Hauptgruppe: B21 enthält Techniker, Ingenieure, Glas und Keramik."""
from __future__ import annotations

GRUPPEN = ("belegschaft", "aufsicht", "leitung", "invaliden")
# Rang bei mehreren Gruppen im Haus (Adressfeld `bergbau`, Thema auf der Karte): die kleinen Gruppen
# verschwänden sonst unter der Belegschaft.
RANG = ("leitung", "aufsicht", "belegschaft", "invaliden")
NAMEN = {"belegschaft": "Belegschaft", "aufsicht": "Aufsicht", "leitung": "Leitung und Beamte", "invaliden": "Berginvaliden"}


def lade_bergbau(zeilen: list[dict]) -> dict[str, str]:
    """Norm → Gruppe. Laut bei leerer Norm, unbekannter Gruppe oder doppelter Norm — eine stille Auslassung
    hieße, Bergleute unbemerkt aus dem Kapitel zu verlieren."""
    out: dict[str, str] = {}
    for z in zeilen:
        beruf = (z.get("beruf") or "").strip()
        gruppe = (z.get("gruppe") or "").strip()
        if not beruf:
            raise ValueError("bergbau.csv: beruf fehlt")
        if gruppe not in GRUPPEN:
            raise ValueError(f"bergbau.csv: gruppe {gruppe!r} für {beruf!r} unbekannt (erlaubt: {GRUPPEN})")
        if beruf in out:
            raise ValueError(f"bergbau.csv: Norm {beruf!r} doppelt")
        out[beruf] = gruppe
    return out


def pruefe_gegen_berufe(tabelle: dict[str, str], berufe_zeilen: list[dict]) -> list[str]:
    """Normen der Tabelle, die in berufe.csv (Spalte beruf) nicht vorkommen — sie zählten nie."""
    normen = {(z.get("beruf") or "").strip() for z in berufe_zeilen}
    return sorted(n for n in tabelle if n not in normen)


def rang_gruppe(zaehl: dict) -> str | None:
    """Höchste vorhandene Gruppe nach RANG aus den Zählfeldern n_bb_<gruppe>; None ohne Bergbau-Eintrag."""
    for g in RANG:
        if zaehl.get(f"n_bb_{g}", 0) > 0:
            return g
    return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m pytest -q tests/test_bergbau.py`
Expected: PASS (5 Tests). Fällt `test_kuratierte_tabelle_passt_zu_berufe_csv`, nennt er die Norm, die in `berufe.csv` anders geschrieben ist — dann die Tabelle (nicht `berufe.csv`) anpassen und im Ledger notieren.

- [ ] **Step 6: Failing test — `lade_regeln` überspringt `bergbau.csv`**

`lade_regeln` liest jede CSV in `kuratierung/merkmale/` als Merkmalsregel und würde an `bergbau.csv` scheitern (Spalte `art` fehlt). In `tests/test_merkmale.py` anhängen:

```python
def test_lade_regeln_ueberspringt_bergbau_tabelle(tmp_path):
    from pipeline.lib.merkmale import lade_regeln
    (tmp_path / "akademiker.csv").write_text("feld,art,muster,merkmal,beleg\nBeruf o. ä.,praefix,Dr.,akademiker,Titel\n", encoding="utf-8")
    (tmp_path / "bergbau.csv").write_text("beruf,gruppe,geprueft,bearbeiter,datum,hinweis\nBergmann,belegschaft,,,,\n", encoding="utf-8")
    assert len(lade_regeln(tmp_path)) == 1
```

- [ ] **Step 7: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_merkmale.py -k ueberspringt`
Expected: FAIL mit `KeyError: 'art'` oder `ValueError`.

- [ ] **Step 8: `lade_regeln` anpassen**

In `pipeline/lib/merkmale.py`, Schleife in `lade_regeln`:

```python
    for pfad in sorted(Path(ordner).glob("*.csv")):
        if pfad.name == "bergbau.csv":     # Gruppen-Tabelle (pipeline/lib/bergbau.py), keine Merkmalsregel
            continue
        for z in lies_csv(pfad):
```

- [ ] **Step 9: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_merkmale.py`
Expected: PASS

- [ ] **Step 10: Failing test — Zählfelder `n_bb_*`**

In `tests/test_ebenen.py` anhängen:

```python
def test_zaehlfelder_bergbau():
    b_berg = dict(niveau="fachlich", stellung="arbeiter", stellung_quelle="hand", gruppe="B21", bergbau="belegschaft")
    b_steig = dict(niveau="aufsicht", stellung="angestellte", stellung_quelle="hand", gruppe="B21", bergbau="aufsicht")
    b_ohne = dict(niveau="fachlich", stellung="arbeiter", stellung_quelle="hand", gruppe="B24")
    a = _adresse(1, 51.45, 7.01, eintraege=[("I", b_berg, None), ("I", b_berg, None), ("I", b_steig, None), ("I", b_ohne, None), ("I", None, None)])
    z = zaehlfelder(a)
    assert z["n_bb_belegschaft"] == 2 and z["n_bb_aufsicht"] == 1
    assert "n_bb_leitung" not in z and z["n_gr_ungeprueft"] == 1       # ungeprüfter Beruf: kein n_bb_, bleibt Ausschluss
    assert sum(1 for k in z if k.startswith("n_bb_")) == 2
```

- [ ] **Step 11: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_ebenen.py -k bergbau`
Expected: FAIL mit `KeyError: 'n_bb_belegschaft'`

- [ ] **Step 12: `zaehlfelder` erweitern**

In `pipeline/lib/ebenen.py`, im Zweig `if e["teil"] == "I":` nach `n["n_gr_" + ...] += 1`:

```python
            if b.get("bergbau"):
                n["n_bb_" + b["bergbau"]] += 1     # Bergbau-Gruppe je Norm (pipeline/lib/bergbau.py)
```

- [ ] **Step 13: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_ebenen.py`
Expected: PASS

- [ ] **Step 14: Failing test — `gruppiere` hängt die Gruppe an, `punkt_feature` schreibt das Rangfeld**

In `tests/test_karte_export.py` anhängen (Muster: `test_niveau_je_adresse_und_berufsnormindex` in derselben Datei):

```python
def test_gruppiere_bergbau_gruppe_und_rangfeld(tmp_path):
    from pipeline.lib.berufe import lade_ohdab, lade_kuratierung as lade_berufe
    from tests.test_berufe import OHDAB_KOPF, OHDAB_ZEILEN
    p = tmp_path / "o.csv"; p.write_text(OHDAB_KOPF + OHDAB_ZEILEN, encoding="utf-8"); o = lade_ohdab(p)
    # Beide Schreibweisen auf ein Item aus der Test-OhdAB (B 21112-100); die Bergbau-Gruppe hängt an der Norm, nicht am Item.
    b = lade_berufe([dict(schreibweise="Bergm.", beruf="Bergmann", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja"),
                     dict(schreibweise="Steiger", beruf="Steiger", status="", ohdab_id="B 21112-100", niveau_unsicher="", geprueft="ja"),
                     dict(schreibweise="Lehrer", beruf="Lehrer", status="", ohdab_id="B 84124-120", niveau_unsicher="", geprueft="ja")])
    basis = dict(stufe="haus", lat="51.4", lon="7.0", strasse_norm="x", strasse_roh="X", hausnr="1", Vorort="", stadtteil="Kray", lastname="N", firstname="", page="I-1")
    def e(i, beruf, hausnr="1"):
        return dict(basis, id=str(i), teil="I", hausnr=hausnr, **{"Beruf o. ä.": beruf})
    eintraege = [e(1, "Bergm."), e(2, "Steiger"), e(3, "Bergm.", "2"), e(4, "Lehrer", "3"), e(5, "Kfm.", "4")]
    a = gruppiere(eintraege, [], None, berufe=b, ohdab=o, bergbau={"Bergmann": "belegschaft", "Steiger": "aufsicht"})
    nach_nr = {x["hausnr"]: x for x in a.values()}
    assert [x["_beruf"].get("bergbau") for x in nach_nr["1"]["eintraege"]] == ["belegschaft", "aufsicht"]
    p1 = punkt_feature(nach_nr["1"])["properties"]
    assert p1["bergbau"] == "aufsicht" and p1["n_bb_belegschaft"] == 1 and p1["n_bb_aufsicht"] == 1   # Rang: Aufsicht vor Belegschaft
    assert punkt_feature(nach_nr["2"])["properties"]["bergbau"] == "belegschaft"
    assert "bergbau" not in punkt_feature(nach_nr["3"])["properties"] and "bergbau" not in nach_nr["3"]["eintraege"][0]["_beruf"]
    assert "bergbau" not in punkt_feature(nach_nr["4"])["properties"]      # ungeprüfter Beruf: kein Feld, kein n_bb_
    kz = baue_kennzahlen(eintraege, a, "2026-09-28")
    assert (kz["bergbau_n"], kz["bergbau_belegschaft_n"], kz["bergbau_aufsicht_n"], kz["bergbau_leitung_n"], kz["bergbau_haeuser_n"]) == (3, 2, 1, 0, 0)
```

`baue_kennzahlen` und `gruppiere`, `punkt_feature` sind oben in der Datei bereits importiert (sonst den Import um `baue_kennzahlen` ergänzen).

- [ ] **Step 15: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_karte_export.py -k bergbau`
Expected: FAIL mit `TypeError: gruppiere() got an unexpected keyword argument 'bergbau'`

- [ ] **Step 16: `gruppiere`, `punkt_feature`, `baue_kennzahlen`, `schreibe_paket` erweitern**

In `pipeline/lib/karte_export.py`:

1. Import ergänzen: `from pipeline.lib.bergbau import GRUPPEN as BB_GRUPPEN, rang_gruppe`.
2. Signatur `gruppiere(..., stadtteile=None, bergbau: dict[str, str] | None = None)`; nach `beruf["gruppe"] = hauptgruppe(...)`:

```python
        if beruf and bergbau and bergbau.get(beruf["beruf"]):
            beruf["bergbau"] = bergbau[beruf["beruf"]]      # Spec Bergbau §2.3
```

3. `punkt_feature`: `p.update(zaehlfelder(a))` ersetzen durch

```python
    z = zaehlfelder(a)
    p.update(z)
    bb = rang_gruppe(z)
    if bb:
        p["bergbau"] = bb        # höchste Bergbau-Gruppe im Haus (Thema auf der Karte, Spec §5)
```

4. `baue_kennzahlen`: vor dem `return dict(...)`

```python
    bb = [e for e in teil_i if (e.get("_beruf") or {}).get("bergbau")]
    bb_je = {g: sum(1 for e in bb if e["_beruf"]["bergbau"] == g) for g in BB_GRUPPEN}
```

und im `dict(...)`:

```python
                bergbau_n=len(bb), bergbau_belegschaft_n=bb_je["belegschaft"], bergbau_aufsicht_n=bb_je["aufsicht"],
                bergbau_leitung_n=bb_je["leitung"], bergbau_invaliden_n=bb_je["invaliden"],
                bergbau_haeuser_n=sum(1 for a in adressen.values() if a.get("besitz") == "bergbau"),
```

5. `schreibe_paket(..., perspektiven=None, bergbau: list[dict] | None = None)`: vor `gruppiere(...)`

```python
    bb_tabelle = lade_bergbau(bergbau or [])
    if bb_tabelle and berufe:
        fehlt = pruefe_gegen_berufe(bb_tabelle, berufe)
        if fehlt:
            raise ValueError(f"kuratierung/merkmale/bergbau.csv: Norm nicht in berufe.csv: {fehlt}")
```

(Import: `from pipeline.lib.bergbau import GRUPPEN as BB_GRUPPEN, lade_bergbau, pruefe_gegen_berufe, rang_gruppe`) und `gruppiere(..., stadtteile=stadtteile, bergbau=bb_tabelle)`.

6. `pipeline/06_karte_export.py`: nach `gewerbe = ...`

```python
bergbau_pfad = W / "kuratierung" / "merkmale" / "bergbau.csv"
bergbau = lies_csv(bergbau_pfad) if bergbau_pfad.exists() else []
```

und `schreibe_paket(..., perspektiven=W / "kuratierung" / "perspektiven", bergbau=bergbau)`.

- [ ] **Step 17: Run tests to verify they pass**

Run: `python3 -m pytest -q tests/test_karte_export.py tests/test_ebenen.py tests/test_bergbau.py`
Expected: PASS

- [ ] **Step 18: Commit**

```bash
git add kuratierung/merkmale/bergbau.csv pipeline/lib/bergbau.py pipeline/lib/ebenen.py pipeline/lib/karte_export.py pipeline/lib/merkmale.py pipeline/06_karte_export.py tests/test_bergbau.py tests/test_ebenen.py tests/test_karte_export.py tests/test_merkmale.py
git commit -m "feat(pipeline): Bergbau-Gruppen je Norm aus kuratierter Tabelle — Zählfelder n_bb_*, Rangfeld bergbau je Adresse, Kennzahlen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Kapiteldaten `perspektiven/bergbau_punkte.json`

**Files:**
- Modify: `pipeline/lib/karte_export.py` (neue Funktion `baue_bergbau_punkte`, Aufruf in `schreibe_paket`)
- Test: `tests/test_karte_export.py`

**Interfaces:**
- Consumes: `pipeline.lib.layout.packe_kreise(kreise, abstand)`, `pipeline.lib.ebenen.hex_zelle, hex_mitte, hex_id, _lonlat`, `pipeline.lib.bergbau.GRUPPEN, NAMEN`, `falte`
- Produces: `baue_bergbau_punkte(adressen) -> dict` mit Schlüsseln `gruppen, hex, haeuser, gesellschaften, maxn` (Spec §2.4); Datei `site/daten/perspektiven/bergbau_punkte.json`; Gesellschafts-ID = `falte(name).replace(" ", "_")`, ohne Namen `unbekannt`

- [ ] **Step 1: Failing test**

In `tests/test_karte_export.py` anhängen:

```python
def test_baue_bergbau_punkte():
    from pipeline.lib.karte_export import baue_bergbau_punkte
    from pipeline.lib.ebenen import hex_id, hex_zelle
    from pipeline.lib.layout import ueberlappen
    def adr(i, lat, lon, gruppen=(), besitz="ungeprueft", eig="", stufe="haus"):
        eintraege = [dict(teil="I", _beruf=dict(bergbau=g)) for g in gruppen]
        if eig:
            eintraege.append(dict(teil="II", _eigentuemer=eig, _kategorie="bergbau"))
        return dict(id=str(i), lat=lat, lon=lon, stufe=stufe, besitz=besitz, eintraege=eintraege)
    adressen = {a["id"]: a for a in [
        adr(1, 51.45, 7.01, ["belegschaft", "belegschaft", "aufsicht"]),
        adr(2, 51.4501, 7.0101, ["belegschaft"], besitz="bergbau", eig="Gewerkschaft Mathias Stinnes"),
        adr(3, 51.40, 7.10, ["leitung"], besitz="bergbau", eig="Gewerkschaft Mathias Stinnes", stufe="strasse"),
        adr(4, 51.41, 7.11, [], besitz="bergbau"),
        adr(5, 51.42, 7.12, [], besitz="privatperson")]}
    p = baue_bergbau_punkte(adressen)
    assert [g["id"] for g in p["gruppen"]] == ["belegschaft", "aufsicht", "leitung", "invaliden"]
    assert p["gruppen"][0] == dict(id="belegschaft", name="Belegschaft", n=3, felder=1)     # Adresse 1 und 2 im selben Hexfeld
    assert p["maxn"] == 3
    b = p["hex"]["belegschaft"]
    assert len(b) == 1 and b[0]["n"] == 3 and b[0]["id"] == hex_id(*hex_zelle(51.45, 7.01)) and b[0]["r"] == 9.0
    assert set(b[0]) == {"id", "lon", "lat", "n", "r", "x", "y"}
    assert p["hex"]["invaliden"] == [] and ueberlappen(p["hex"]["belegschaft"] + []) == []
    assert [h["eig"] for h in p["haeuser"]] == ["gewerkschaft_mathias_stinnes", "gewerkschaft_mathias_stinnes", "unbekannt"]
    assert p["haeuser"][1]["stufe"] == "strasse" and set(p["haeuser"][0]) == {"id", "lon", "lat", "eig", "stufe"}
    assert p["gesellschaften"] == [dict(id="gewerkschaft_mathias_stinnes", name="Gewerkschaft Mathias Stinnes", haeuser=2),
                                   dict(id="unbekannt", name="unbekannter Bergbau-Eigentümer", haeuser=1)]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest -q tests/test_karte_export.py -k bergbau_punkte`
Expected: FAIL mit `ImportError: cannot import name 'baue_bergbau_punkte'`

- [ ] **Step 3: Funktion schreiben**

In `pipeline/lib/karte_export.py` nach `baue_layouts`:

```python
def baue_bergbau_punkte(adressen: dict[str, dict]) -> dict:
    """Kapiteldaten des Bergbau-Kapitels (Spec 2026-09-28 §2.4): je Gruppe ein Kreis je Hexfeld mit Packung
    (gesammelter Zustand) und Lage (verteilter Zustand); dazu alle geprüften Häuser der Klasse Bergbau mit
    ihrer Gesellschaft. Radius ∝ sqrt(n / maxn), ein Maßstab über alle Gruppen (max 9, min 1.2)."""
    from pipeline.lib.bergbau import GRUPPEN as BB, NAMEN
    from pipeline.lib.ebenen import _lonlat, hex_id, hex_mitte, hex_zelle
    je_feld: dict[str, dict[str, int]] = {g: defaultdict(int) for g in BB}
    haeuser: list[dict] = []
    gesellschaften: dict[str, dict] = {}
    for a in adressen.values():
        hid = hex_id(*hex_zelle(a["lat"], a["lon"]))
        for e in a["eintraege"]:
            g = (e.get("_beruf") or {}).get("bergbau") if e.get("teil") == "I" else None
            if g:
                je_feld[g][hid] += 1
        if a.get("besitz") == "bergbau":
            name = next((e["_eigentuemer"] for e in a["eintraege"] if e.get("teil") == "II" and e.get("_kategorie") == "bergbau" and e.get("_eigentuemer")),
                        a.get("besitz_eigentuemer") or "")
            eid = falte(name).replace(" ", "_") if name else "unbekannt"
            haeuser.append(dict(id=a["id"], lon=a["lon"], lat=a["lat"], eig=eid, stufe=a.get("stufe", "haus")))
            x = gesellschaften.setdefault(eid, dict(id=eid, name=name or "unbekannter Bergbau-Eigentümer", haeuser=0))
            x["haeuser"] += 1
    maxn = max((n for z in je_feld.values() for n in z.values()), default=0)

    def r_von(n: int) -> float:
        return max(1.2, round(9.0 * math.sqrt(n / maxn), 3)) if maxn else 1.2

    hexe: dict[str, list[dict]] = {}
    for g in BB:
        kreise = []
        for hid, n in je_feld[g].items():
            q, r = (int(v) for v in hid.split("_"))
            lon, lat = _lonlat(*hex_mitte(q, r))
            kreise.append(dict(id=hid, lon=lon, lat=lat, n=n, r=r_von(n)))
        kreise.sort(key=lambda k: (-k["n"], k["id"]))
        hexe[g] = packe_kreise(kreise, abstand=0.6) if kreise else []
    gruppen = [dict(id=g, name=NAMEN[g], n=sum(je_feld[g].values()), felder=len(je_feld[g])) for g in BB]
    return dict(gruppen=gruppen, hex=hexe, haeuser=haeuser,
                gesellschaften=sorted(gesellschaften.values(), key=lambda x: (-x["haeuser"], x["id"])), maxn=maxn)
```

(`import math` oben in der Datei ergänzen, falls nicht vorhanden; `packe_kreise` in den bestehenden Import aus `pipeline.lib.layout` aufnehmen.)

In `schreibe_paket`, direkt nach der Layout-Schleife:

```python
    _json(ausgabe / "perspektiven" / "bergbau_punkte.json", baue_bergbau_punkte(adressen))
```

Achtung: `06_karte_export.py` löscht `perspektiven/` vor dem Export; die Datei wird hier neu geschrieben, das Kapitel-JSON folgt weiter unten in derselben Funktion.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest -q tests/test_karte_export.py tests/test_layout.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pipeline/lib/karte_export.py tests/test_karte_export.py
git commit -m "feat(pipeline): Kapiteldaten Bergbau — gepackte Kreise je Hexfeld und Gruppe, Häuser der Zechen mit Gesellschaft

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Kapitel-JSON, Thema-JSON, Schemaprüfung, Wortwahl-Korrekturen, Export

**Files:**
- Create: `kuratierung/perspektiven/bergbau.json`, `kuratierung/themen/bergbau.json`
- Modify: `pipeline/lib/perspektiven.py:7-17, 52-70` (DATEN, FORMEN, `punkte`), `pipeline/lib/karte_export.py` (`schreibe_paket`: Prüfung der Gesellschafts-IDs), `kuratierung/perspektiven/stellung.json`, `kuratierung/perspektiven/datenbasis.json`
- Test: `tests/test_perspektiven.py`

**Interfaces:**
- Consumes: `baue_bergbau_punkte` (Task 3), Kennzahlen `bergbau_*` (Task 2)
- Produces: Kapitel `bergbau` mit Schritten `gruppen, karten, belegschaft-leitung, invaliden, hausherr`; Ansichtsfeld `punkte: {zustand, hervor}`; Thema `bergbau` mit `schalter: {praefix, klassen, namen}`; `pruefe_punkte_bezug(k, punkte) -> list[str]`; Datenpaket neu exportiert

- [ ] **Step 1: Failing tests — Schema kennt `punktkarte`, `bergbau`, `punkte`; Gesellschaften geprüft**

In `tests/test_perspektiven.py` anhängen:

```python
def test_punktkarte_und_punkte_feld():
    k = json.loads(json.dumps(GUT))
    k["schritte"][0]["ansicht"].update(daten="bergbau", form="punktkarte", punkte={"zustand": "karten", "hervor": ["Privat"]},
                                       gruppen=[{"name": "Privat", "aus": ["belegschaft"], "farbe": "#c2410c"}])
    assert pruefe_kapitel(k) == []
    k["schritte"][0]["ansicht"]["punkte"] = {"zustand": "fliegen", "hervor": "Privat"}
    f = pruefe_kapitel(k)
    assert any("zustand" in x for x in f) and any("hervor" in x for x in f)


def test_pruefe_punkte_bezug_nennt_unbekannte_gesellschaften():
    from pipeline.lib.perspektiven import pruefe_punkte_bezug
    k = json.loads(json.dumps(GUT))
    k["schritte"][0]["ansicht"].update(daten="besitz", ebene="adresse", form="punktkarte", punkte={"zustand": "haeuser", "hervor": []},
                                       gruppen=[{"name": "Stinnes", "aus": ["gewerkschaft_mathias_stinnes"], "farbe": "#e69f00"}, {"name": "X", "aus": ["gibts_nicht"], "farbe": "#000"}])
    punkte = {"gesellschaften": [{"id": "gewerkschaft_mathias_stinnes", "name": "Gewerkschaft Mathias Stinnes", "haeuser": 725}]}
    assert pruefe_punkte_bezug(k, punkte) == ["Kapitel 'wohneigentum', Schritt 'anteile': Gesellschaft 'gibts_nicht' fehlt in bergbau_punkte.json"]
    assert pruefe_punkte_bezug(GUT, punkte) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest -q tests/test_perspektiven.py`
Expected: FAIL — `form 'punktkarte' unbekannt`, `daten 'bergbau' unbekannt`; ImportError für `pruefe_punkte_bezug`.

- [ ] **Step 3: Schema erweitern**

In `pipeline/lib/perspektiven.py`:

```python
DATEN = ("stellung", "gruppe", "niveau", "besitz", "gewerbe", "bergbau")
FORMEN = ("karte", "stadtteilkarte", "bubbles", "balken", "multiples", "rangliste", "punktkarte")
PUNKTE_ZUSTAENDE = ("gesammelt", "karten", "haeuser")
```

In `pruefe_ansicht`, vor `return f`:

```python
    p = a.get("punkte")
    if a["form"] == "punktkarte" or p is not None:
        if not isinstance(p, dict): f.append(f"{wo}: punktkarte braucht punkte {{zustand, hervor}}")
        else:
            if p.get("zustand") not in PUNKTE_ZUSTAENDE: f.append(f"{wo}: punkte.zustand {p.get('zustand')!r} unbekannt")
            if not isinstance(p.get("hervor"), list): f.append(f"{wo}: punkte.hervor muss Liste sein")
            elif any(h not in namen for h in p["hervor"]): f.append(f"{wo}: punkte.hervor nennt keine Gruppe")
```

Neue Funktion:

```python
def pruefe_punkte_bezug(k: dict, punkte: dict) -> list[str]:
    """Schritte im Zustand `haeuser` gruppieren nach Gesellschafts-IDs; jede muss in bergbau_punkte.json stehen —
    sonst bliebe eine Gesellschaft stumm grau, und der Text spräche von Häusern, die niemand sieht."""
    ids = {g["id"] for g in punkte.get("gesellschaften", [])}
    f = []
    for s in k.get("schritte", []):
        a = s.get("ansicht", {})
        if a.get("form") != "punktkarte" or (a.get("punkte") or {}).get("zustand") != "haeuser": continue
        for g in a.get("gruppen", []):
            for aus in g.get("aus", []):
                if aus not in ids:
                    f.append(f"Kapitel {k.get('id')!r}, Schritt {s.get('id')!r}: Gesellschaft {aus!r} fehlt in bergbau_punkte.json")
    return f
```

In `schreibe_paket` (karte_export.py): `punkte = baue_bergbau_punkte(adressen)` vor dem Schreiben behalten und in der Kapitelschleife `fehler = pruefe_kapitel(k) + pruefe_kennzahlen_bezug(k, kennzahlen) + pruefe_punkte_bezug(k, punkte)` (Import ergänzen).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest -q tests/test_perspektiven.py`
Expected: PASS

- [ ] **Step 5: Thema anlegen**

`kuratierung/themen/bergbau.json`:

```json
{
  "id": "bergbau",
  "titel": "Bergbau",
  "text": "Adressen mit Bergbau-Berufen laut Teil I, nach Gruppe: Belegschaft, Aufsicht, Leitung und Beamte, Berginvaliden. Bei mehreren Gruppen im Haus zählt die höchste. Die Kästchen in der Legende schalten Gruppen ab und zu; Adressen ohne eingeschaltete Gruppe verschwinden.",
  "grundlage": "Bergbau-Tabelle kuratierung/merkmale/bergbau.csv (Norm → Gruppe, noch ungeprüft) über die Berufs-Kuratierung kuratierung/berufe.csv; nur verortete Einträge des Einwohnerverzeichnisses mit geprüftem Beruf",
  "freigegeben": true,
  "filter": { "ebenen": ["I"] },
  "farbe": { "art": "kategorien", "feld": "bergbau",
             "werte": { "leitung": "#7c3aed", "aufsicht": "#1d4ed8", "belegschaft": "#c2410c", "invaliden": "#15803d" } },
  "schalter": { "praefix": "n_bb_", "klassen": ["leitung", "aufsicht", "belegschaft", "invaliden"],
                "namen": { "leitung": "Leitung und Beamte", "aufsicht": "Aufsicht", "belegschaft": "Belegschaft", "invaliden": "Berginvaliden" } },
  "zusatz": { "zechen": true },
  "legende": "Farbe: höchste Bergbau-Gruppe im Haus"
}
```

- [ ] **Step 6: Kapitel anlegen**

`kuratierung/perspektiven/bergbau.json` (Texte sind Platzhalter; Zahlen nennt die Grafik):

```json
{
  "id": "bergbau",
  "reihenfolge": 4,
  "titel": "Bergbau 1936",
  "untertitel": "Zechen, Belegschaft, Aufsicht, Leitung: Wo die Bergleute wohnten",
  "freigegeben": false,
  "datenbasis": "{bergbau_n} von {teil_i_n} verorteten Einträgen des Einwohnerverzeichnisses tragen einen Bergbau-Beruf; Grundlage sind die {beruf_geprueft_n} Einträge mit geprüftem Beruf.",
  "datenbasis_schritt": "gruppe",
  "ausschluss": "Beruf ungeprüft oder keine Bergbau-Norm",
  "einleitung": "Platzhalter. Das Einwohnerverzeichnis nennt zu jeder eingetragenen Person einen Beruf. Wer Bergmann, Hauer, Steiger, Zechenbeamter oder Berginvalide war, lässt sich daran ablesen; wer als Techniker oder Ingenieur auf einer Zeche arbeitete, nicht. Das Kapitel nimmt nur die Berufe, die eindeutig zum Bergbau gehören, und zeigt, wo diese Menschen wohnten, wo ihre Aufsicht und Leitung, und welche Gesellschaften welche Häuser besaßen.",
  "quellen": ["Adreßbuch Essen 1936, Teil I (Einwohner) und Teil II (Häuserbuch)", "Bergbau-Tabelle kuratierung/merkmale/bergbau.csv", "Zechen in Förderung 1936: Historisches Portal Essen (Huske-Auszüge), kuratierung/zechen.csv"],
  "grenzen": "Grundlage sind {teil_i_n} verortete Einträge des Einwohnerverzeichnisses, davon {beruf_geprueft_n} mit geprüftem Beruf; Einträge ohne geprüften Beruf bleiben ausgeschlossen. Die Namen H bis J fehlen in der Vorlage. Gezählt werden eingetragene Personen, nicht Haushalte und nicht Einwohner: Ehefrauen ohne eigenen Eintrag und Kinder fehlen. Kokereiarbeiter, Koksarbeiter, Schlepper und Oberschaffner sind Grenzfälle und zählen mit. Die Karte zeigt Wohnorte, keine Arbeitsplätze: Wer neben einer Zeche wohnte, muss dort nicht gearbeitet haben. Betriebe des Bergbaus aus dem Branchenverzeichnis sind nicht gezeigt, weil ihre Zuordnung noch ungeprüft ist. Die Zechen tragen keinen Betreiber. Häuser: {bergbau_haeuser_n} geprüfte Adressen der Klasse Bergbau; ungeprüfte Adressen bleiben außen vor.",
  "schritte": [
    {"id": "gruppen", "text": "Platzhalter. Vier Gruppen, ein Maßstab: Jeder Kreis ist ein Hexfeld von 120 Metern Kantenlänge, seine Fläche die Zahl der dort eingetragenen Personen mit einem Bergbau-Beruf. Zusammengeschoben zeigen die Kreise die Größenordnung: Die Belegschaft ist um ein Vielfaches größer als Aufsicht, Leitung und Berginvaliden zusammen.",
     "beschreibung": "Vier gepackte Kreisgruppen nach Größe sortiert: Belegschaft, Aufsicht, Berginvaliden, Leitung und Beamte, mit Zahl der eingetragenen Personen.",
     "hervorheben": [],
     "ansicht": {"daten": "bergbau", "ebene": "hex", "form": "punktkarte",
                 "gruppen": [{"name": "Belegschaft", "aus": ["belegschaft"], "farbe": "#c2410c"}, {"name": "Aufsicht", "aus": ["aufsicht"], "farbe": "#1d4ed8"}, {"name": "Leitung und Beamte", "aus": ["leitung"], "farbe": "#7c3aed"}, {"name": "Berginvaliden", "aus": ["invaliden"], "farbe": "#15803d"}],
                 "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Belegschaft", "min_n": 0, "filter": {}, "karte": null,
                 "punkte": {"zustand": "gesammelt", "hervor": []}}},
    {"id": "karten", "text": "Platzhalter. Dieselben Kreise, auf ihre Lage verteilt, eine Karte je Gruppe. Die Belegschaft füllt ein Band im Norden von Bergeborbeck bis Katernberg und einen zweiten Schwerpunkt im Südosten um Kupferdreh und Überruhr. Die Aufsicht folgt dem Muster dünner. Schlägel und Eisen markieren die 24 Zechen, die 1936 förderten. Nähe zu einer Zeche heißt nicht, dort gearbeitet zu haben.",
     "beschreibung": "Vier kleine Karten des Stadtgebiets, je Gruppe ein Kreis je Hexfeld; Zechen in Förderung 1936 als Schlägel und Eisen.",
     "hervorheben": [],
     "ansicht": {"daten": "bergbau", "ebene": "hex", "form": "punktkarte", "gruppen": "wie:gruppen",
                 "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Belegschaft", "min_n": 0, "filter": {}, "karte": null,
                 "punkte": {"zustand": "karten", "hervor": []}}},
    {"id": "belegschaft-leitung", "text": "Platzhalter. Belegschaft und Leitung nebeneinander: Wo die Belegschaft dicht wohnt, fehlt die Leitung fast ganz. Zechenbeamte, Bergassessoren und Direktoren wohnen in der Stadtmitte und im Süden, kaum in den Kolonien. Die Leitung sind nur wenige hundert Einträge, darum zeigt die Karte Zahlen, keine Anteile.",
     "beschreibung": "Dieselben vier Karten; Belegschaft und Leitung hervorgehoben, Aufsicht und Berginvaliden abgeblendet.",
     "hervorheben": [],
     "ansicht": {"daten": "bergbau", "ebene": "hex", "form": "punktkarte", "gruppen": "wie:gruppen",
                 "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Belegschaft", "min_n": 0, "filter": {}, "karte": null,
                 "punkte": {"zustand": "karten", "hervor": ["Belegschaft", "Leitung und Beamte"]}}},
    {"id": "invaliden", "text": "Platzhalter. Die Berginvaliden, aus dem Bergbau ausgeschieden, wohnen wie die Belegschaft: in denselben Straßen im Norden und Südosten. Das Buch führt sie als eigenen Stand, nicht als Beruf.",
     "beschreibung": "Dieselben vier Karten; Berginvaliden hervorgehoben, die übrigen abgeblendet.",
     "hervorheben": [],
     "ansicht": {"daten": "bergbau", "ebene": "hex", "form": "punktkarte", "gruppen": "wie:gruppen",
                 "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Belegschaft", "min_n": 0, "filter": {}, "karte": null,
                 "punkte": {"zustand": "karten", "hervor": ["Berginvaliden"]}}},
    {"id": "hausherr", "text": "Platzhalter. Die Zeche als Hausherr: Jeder Punkt ist ein Haus im Besitz einer Bergbaugesellschaft, die Farbe nennt die Gesellschaft. Die Kolonien liegen als Blöcke um die Schachtanlagen. Die Gewerkschaft Graf Beust besaß 1936 noch 166 Häuser, obwohl ihre Zeche seit 1929 stillgelegt war. Die Zechen sind neutral markiert, weil ihre Betreiber noch nicht belegt sind.",
     "beschreibung": "Eine Karte des Stadtgebiets mit einem Punkt je Haus im Besitz einer Bergbaugesellschaft, gefärbt nach Gesellschaft; Ring für nur straßengenau verortete Häuser.",
     "hervorheben": [],
     "ansicht": {"daten": "besitz", "ebene": "adresse", "form": "punktkarte",
                 "gruppen": [{"name": "Essener Bergwerks-Verein König Wilhelm", "aus": ["essener_bergwerks_verein_koenig_wilhelm"], "farbe": "#e69f00"},
                             {"name": "Gelsenkirchener Bergwerks-AG", "aus": ["gelsenkirchener_bergwerks_ag_gbag"], "farbe": "#56b4e9"},
                             {"name": "Gewerkschaft Mathias Stinnes", "aus": ["gewerkschaft_mathias_stinnes"], "farbe": "#009e73"},
                             {"name": "Gewerkschaft Viktoria Mathias", "aus": ["gewerkschaft_viktoria_mathias"], "farbe": "#f0e442"},
                             {"name": "Zeche Langenbrahm", "aus": ["zeche_langenbrahm"], "farbe": "#0072b2"},
                             {"name": "Mülheimer Bergwerks-Verein", "aus": ["muelheimer_bergwerks_verein"], "farbe": "#d55e00"},
                             {"name": "Gewerkschaft Friedrich Ernestine", "aus": ["gewerkschaft_friedrich_ernestine"], "farbe": "#cc79a7"},
                             {"name": "Essener Steinkohlenbergwerke AG", "aus": ["essener_steinkohlenbergwerke_ag"], "farbe": "#7c3aed"},
                             {"name": "Gewerkschaft Graf Beust", "aus": ["gewerkschaft_graf_beust"], "farbe": "#15803d"},
                             {"name": "Gewerkschaft Zeche Carolus Magnus", "aus": ["gewerkschaft_zeche_carolus_magnus"], "farbe": "#c2410c"},
                             {"name": "Zeche Heinrich", "aus": ["zeche_heinrich"], "farbe": "#0e7490"}],
                 "kaufleute": "unbestimmt", "unsicher": false, "mass": "anteil", "bezug": "Essener Bergwerks-Verein König Wilhelm", "min_n": 0, "filter": {}, "karte": null,
                 "punkte": {"zustand": "haeuser", "hervor": []}}}
  ]
}
```

Die IDs in `aus` sind `falte(name).replace(" ", "_")`; `falte` entfernt Bindestriche und Klammern und schreibt Umlaute aus (`Mülheimer` → `muelheimer`). Der Export prüft sie gegen `bergbau_punkte.json` (Step 3); stimmt eine nicht, nennt die Fehlermeldung die ID, dann `python3 -c "from pipeline.lib.karte_export import falte; print(falte('…'))"` und die Kapiteldatei korrigieren.

- [ ] **Step 7: Wortwahl korrigieren (Spec §2.1)**

In `kuratierung/perspektiven/stellung.json`: `"Das Einwohnerverzeichnis nennt zu jedem Haushaltsvorstand einen Beruf."` → `"Das Einwohnerverzeichnis nennt zu jeder eingetragenen Person einen Beruf."`; im Schritt `anteile`: `"Mehr als jeder zweite Haushaltsvorstand mit bestimmter Stellung"` → `"Mehr als jede zweite eingetragene Person mit bestimmter Stellung"`. In `kuratierung/perspektiven/datenbasis.json`: `"Haushaltsvorstände mit Beruf und Adresse."` → `"Eingetragene Personen mit Beruf und Adresse: Erwerbstätige, Witwen, Rentner, auch erwachsene Söhne im selben Haus."`. Prüfen: `grep -rn "Haushaltsvorst" kuratierung/ site/*.html` liefert nichts.

- [ ] **Step 8: Export laufen lassen**

```bash
cd /home/christos/Projekte/essener-adressbuch-1936
python3 pipeline/06_karte_export.py 2>&1 | tail -5
python3 - <<'EOF'
import json
p = json.load(open("site/daten/perspektiven/bergbau_punkte.json"))
print([ (g["id"], g["n"], g["felder"]) for g in p["gruppen"]], "maxn", p["maxn"], "haeuser", len(p["haeuser"]))
print([ (g["id"], g["haeuser"]) for g in p["gesellschaften"][:12]])
kz = json.load(open("site/daten/kennzahlen.json")); print({k: v for k, v in kz.items() if k.startswith("bergbau")})
t = json.load(open("site/daten/themen/index.json")); print(t)
import subprocess; print(subprocess.run(["grep", "-c", '"bergbau"', "site/daten/adressen.geojson"], capture_output=True, text=True).stdout)
EOF
git status --short site/daten | head
```

Expected: Export ohne `ValueError`; Gruppen etwa Belegschaft ≈ 26.000 / Aufsicht ≈ 1.200 / Leitung ≈ 400 / Invaliden ≈ 600; elf Gesellschaften mit > 90 Häusern, darunter `essener_bergwerks_verein_koenig_wilhelm` ≈ 968 (925 + 22 + 15 + 6) und `muelheimer_bergwerks_verein` ≈ 518; `bergbau_n` in den Kennzahlen; Thema `bergbau` im Index; `grep -c` > 0. Schlägt die Gesellschaftsprüfung fehl: IDs im Kapitel nachziehen (Step 6) und erneut exportieren. Die Kennzahlen im Wohneigentum-Kapitel (Rangliste der Eigentümer) ändern sich durch Task 1: `kuratierung/perspektiven/wohneigentum.json` nach Zahlen zu König Wilhelm/Mülheimer durchsuchen (`grep -n "König Wilhelm\|Mülheimer\|Mühlheimer" kuratierung/perspektiven/wohneigentum.json`) und, wenn dort Häuserzahlen stehen, gegen `site/daten/layout/eigentuemer.json` nachziehen; danach Export erneut.

- [ ] **Step 9: Tests**

Run: `python3 -m pytest -q`
Expected: alle PASS (bisher 433, jetzt mehr).

- [ ] **Step 10: Commit**

```bash
git add kuratierung/perspektiven/bergbau.json kuratierung/themen/bergbau.json kuratierung/perspektiven/stellung.json kuratierung/perspektiven/datenbasis.json kuratierung/perspektiven/wohneigentum.json pipeline/lib/perspektiven.py pipeline/lib/karte_export.py tests/test_perspektiven.py site/daten
git commit -m "feat(kapitel): Bergbau 1936 als Kapitel 4 (Vorschau) und Thema Bergbau mit Schaltern; Wortwahl eingetragene Personen; Datenpaket neu exportiert

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Ansicht-Modell, Lader, Kapitel-Links

**Files:**
- Modify: `site/js/ansicht.js:3-8, 19-21, 24-46, 113-119`, `site/js/daten.js:57`, `site/js/daten_ebenen.js:4-9`, `site/js/perspektiven_modell.js:52-66`
- Test: `site/tests/ansicht.test.js`, `site/tests/daten_ebenen.test.js`, `site/tests/perspektiven.test.js`

**Interfaces:**
- Consumes: Kapiteldatei (Task 3), Thema-ID `bergbau`, Klassen-Schlüssel = `gruppe.aus[0]`
- Produces: `DATEN` enthält `bergbau` (Präfix `n_bb_`, Nenner `n_I`); `FORMEN` enthält `punktkarte`; `PUNKTE_ZUSTAENDE = ["gesammelt", "karten", "haeuser"]`; `normalisiere` liefert `punkte: {zustand, hervor}` bei `form === "punktkarte"`, sonst `punkte: null`; `BERGBAU` Konstante und `standardGruppen("bergbau")`; `Lader.punkte()`, `Lader.zechen()`; `ladeEbenen` liefert zusätzlich `punkte` und `zechen`; `formFuer` → `"punktkarte"`; `linkKarte(ansicht)` liefert für Punktkarten `karte.html?thema=bergbau[&klassen=…]`, im Zustand `haeuser` `null`; `linkWerkstatt` unverändert

- [ ] **Step 1: Failing tests — Ansicht-Modell**

In `site/tests/ansicht.test.js` anhängen:

```js
import { BERGBAU, DATEN, FORMEN, PUNKTE_ZUSTAENDE } from "../js/ansicht.js";

test("bergbau als Datenkern: Präfix, Standardgruppen, punktkarte als Form", () => {
  assert.ok(DATEN.includes("bergbau")); assert.ok(FORMEN.includes("punktkarte"));
  assert.equal(praefix("bergbau"), "n_bb_");
  assert.deepEqual(PUNKTE_ZUSTAENDE, ["gesammelt", "karten", "haeuser"]);
  const g = standardGruppen("bergbau");
  assert.deepEqual(g.map((x) => x.aus[0]), ["belegschaft", "aufsicht", "leitung", "invaliden"]);
  assert.equal(g[2].name, "Leitung und Beamte"); assert.equal(g[3].farbe, "#15803d");
  assert.equal(BERGBAU.belegschaft[1], "#c2410c");
  const e = { n_I: 10, n_bb_belegschaft: 4, n_bb_aufsicht: 1, n_gr_ungeprueft: 2 };
  const k = kennzahlen(e, normalisiere({ daten: "bergbau", ebene: "hex", gruppen: g, bezug: "Belegschaft", min_n: 0 }));
  assert.equal(k.N, 5); assert.equal(k.zaehler.Belegschaft, 4);
});

test("punkte nur bei punktkarte; hervor auf Gruppennamen gefiltert; unbekannter Zustand → gesammelt", () => {
  const g = standardGruppen("bergbau");
  const a = normalisiere({ daten: "bergbau", ebene: "hex", form: "punktkarte", gruppen: g, punkte: { zustand: "karten", hervor: ["Belegschaft", "Erfunden"] } });
  assert.deepEqual(a.punkte, { zustand: "karten", hervor: ["Belegschaft"] });
  assert.equal(normalisiere({ daten: "bergbau", form: "punktkarte", gruppen: g, punkte: { zustand: "fliegen" } }).punkte.zustand, "gesammelt");
  assert.deepEqual(normalisiere({ daten: "bergbau", form: "punktkarte", gruppen: g }).punkte, { zustand: "gesammelt", hervor: [] });
  assert.equal(normalisiere({ daten: "bergbau", form: "balken", gruppen: g, punkte: { zustand: "karten" } }).punkte, null);
  assert.deepEqual(dekodiere(kodiere(a)), a);      // Rundreise erhält punkte
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test site/tests/ansicht.test.js`
Expected: FAIL — `BERGBAU`/`PUNKTE_ZUSTAENDE` nicht exportiert.

- [ ] **Step 3: Ansicht-Modell erweitern**

In `site/js/ansicht.js`:

```js
export const DATEN = ["stellung", "gruppe", "niveau", "besitz", "gewerbe", "bergbau"];
export const FORMEN = ["karte", "stadtteilkarte", "bubbles", "balken", "multiples", "rangliste", "punktkarte"];
export const PUNKTE_ZUSTAENDE = ["gesammelt", "karten", "haeuser"];
export const STANDARD_ANSICHT = Object.freeze({ daten: "stellung", ebene: "stadtteil", form: "karte", gruppen: [], kaufleute: "unbestimmt", unsicher: false, mass: "anteil", bezug: "", min_n: 200, filter: {}, karte: null, punkte: null });
const PRAEFIX = { stellung: "n_st_", gruppe: "n_gr_", niveau: "n_", besitz: "n_bs_", gewerbe: "n_gw_", bergbau: "n_bb_" };
const NENNER = { stellung: "n_I", gruppe: "n_I", niveau: "n_I", besitz: "adressen", gewerbe: "n_III", bergbau: "n_I" };
// Bergbau-Gruppen (Spec 2026-09-28 §3): Reihenfolge = Reihenfolge im Kapitel und in der Legende.
export const BERGBAU = { belegschaft: ["Belegschaft", "#c2410c"], aufsicht: ["Aufsicht", "#1d4ed8"], leitung: ["Leitung und Beamte", "#7c3aed"], invaliden: ["Berginvaliden", "#15803d"] };
```

In `normalisiere`, im Rückgabeobjekt nach `karte: …`:

```js
    punkte: punkteVon(o, form, namen),
```

wobei `form` vorher als `const form = wahl(o.form, FORMEN, STANDARD_ANSICHT.form);` gezogen und im Objekt als `form` verwendet wird. Neue Hilfsfunktion über `normalisiere`:

```js
// Zustand der Punktkarte (Spec Bergbau §3): nur diese Form trägt das Feld; hervor nennt nur echte Gruppen.
function punkteVon(o, form, namen) {
  if (form !== "punktkarte") return null;
  const p = o.punkte && typeof o.punkte === "object" ? o.punkte : {};
  const hervor = (Array.isArray(p.hervor) ? p.hervor : []).map(String).filter((h) => namen.has(h));
  return { zustand: wahl(p.zustand, PUNKTE_ZUSTAENDE, "gesammelt"), hervor };
}
```

In `standardGruppen`: `if (daten === "bergbau") return Object.entries(BERGBAU).map(([k, [name, farbe]]) => ({ name, aus: [k], farbe }));`

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test site/tests/ansicht.test.js`
Expected: PASS

- [ ] **Step 5: Failing tests — Lader und Modell-Links**

In `site/tests/daten_ebenen.test.js` anhängen (`D` ist das Dateiwörterbuch der Datei):

```js
test("ladeEbenen liefert Kapitelpunkte und Zechen, fehlend → null", async () => {
  const D2 = { ...D, "daten/perspektiven/bergbau_punkte.json": { gruppen: [], hex: {}, haeuser: [], gesellschaften: [], maxn: 0 } };
  const f = async (u) => ({ ok: u in D2, status: u in D2 ? 200 : 404, json: async () => D2[u] });
  const d = await ladeEbenen(new Lader("daten/", f));
  assert.deepEqual(d.punkte.gruppen, []); assert.equal(d.zechen, null);
});
```

In `site/tests/perspektiven.test.js` anhängen:

```js
test("formFuer punktkarte; linkKarte führt Punktkarten auf das Thema Bergbau mit Klassen, Häuser-Zustand ohne Link", () => {
  const g = [{ name: "Belegschaft", aus: ["belegschaft"], farbe: "#c2410c" }, { name: "Leitung und Beamte", aus: ["leitung"], farbe: "#7c3aed" }];
  const a = normalisiere({ daten: "bergbau", ebene: "hex", form: "punktkarte", gruppen: g, punkte: { zustand: "karten", hervor: [] } });
  assert.equal(formFuer(a), "punktkarte");
  assert.equal(linkKarte(a), "karte.html?thema=bergbau");
  assert.equal(linkKarte({ ...a, punkte: { zustand: "karten", hervor: ["Leitung und Beamte"] } }), "karte.html?thema=bergbau&klassen=leitung");
  assert.equal(linkKarte({ ...a, daten: "besitz", punkte: { zustand: "haeuser", hervor: [] } }), null);
  assert.match(linkKarte(normalisiere({ daten: "besitz", ebene: "stadtteil", gruppen: g })), /^karte\.html\?ansicht=/);
});
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `node --test site/tests/daten_ebenen.test.js site/tests/perspektiven.test.js`
Expected: FAIL — `d.punkte` undefined; `formFuer` liefert `balken`; `linkKarte` liefert `?ansicht=`.

- [ ] **Step 7: Lader, `ladeEbenen`, `formFuer`, `linkKarte`**

`site/js/daten.js` in `Lader`:

```js
  punkte() { return this.json("perspektiven/bergbau_punkte.json"); }
  zechen() { return this.json("zechen.geojson"); }
```

`site/js/daten_ebenen.js`:

```js
export async function ladeEbenen(lader) {
  const [strassen, stadtteile, hex, berufe, eigentuemer, gewerbe, hauptgruppen, polygone, kz, punkte, zechen] = await Promise.all([
    lader.ebene("strassen"), lader.ebene("stadtteile"), lader.ebene("hex"), lader.layout("berufe"), lader.layout("eigentuemer"), lader.layout("gewerbe"),
    lader.hauptgruppen(), lader.stadtteilePolygone(), lader.kennzahlen(), lader.punkte(), lader.zechen()]);
  return { strassen: strassen || [], stadtteile: stadtteile || [], hex: hex || [], layout: { berufe, eigentuemer, gewerbe }, hauptgruppen: hauptgruppen || {}, polygone, kennzahlen: kz || {}, punkte: punkte || null, zechen: zechen || null };
}
```

`site/js/perspektiven_modell.js`:

```js
// Punktkarten (Bergbau) führen nicht in eine ?ansicht=, sondern auf das Thema der Karte mit den
// hervorgehobenen Klassen (Spec Bergbau §6); die hausgenaue Karte verlinkt je Gesellschaft im Detailkasten.
export function linkKarte(ansicht) {
  if (ansicht && ansicht.form === "punktkarte") {
    if (!ansicht.punkte || ansicht.punkte.zustand === "haeuser") return null;
    const klassen = ansicht.punkte.hervor.map((h) => (ansicht.gruppen.find((g) => g.name === h) || { aus: [] }).aus[0]).filter(Boolean);
    return `karte.html?thema=bergbau${klassen.length ? `&klassen=${klassen.join(",")}` : ""}`;
  }
  return `karte.html?ansicht=${kodiere(ansicht)}`;
}
```

und in `formFuer`: `if (form === "punktkarte") return "punktkarte";` vor der `karte`-Zeile.

- [ ] **Step 8: Run tests to verify they pass**

Run: `node --test site/tests/*.test.js`
Expected: PASS (alle Dateien; `formen.test.js` lädt `ladeEbenen` mit einer Attrappe ohne `punkte`, muss weiter grün sein).

- [ ] **Step 9: Commit**

```bash
git add site/js/ansicht.js site/js/daten.js site/js/daten_ebenen.js site/js/perspektiven_modell.js site/tests/ansicht.test.js site/tests/daten_ebenen.test.js site/tests/perspektiven.test.js
git commit -m "feat(site): Datenkern bergbau und Form punktkarte im Ansicht-Modell; Kapitelpunkte und Zechen im Lader; Kapitellinks auf das Thema Bergbau

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Form `punktkarte.js`

**Files:**
- Create: `site/js/formen/punktkarte.js`, `site/tests/punktkarte.test.js`

**Interfaces:**
- Consumes: `daten.punkte` (Task 3), `daten.polygone`, `daten.zechen` (Task 5), `daten.kennzahlen.teil_i_n / beruf_geprueft_n`, `skalen.js` (`esc, formatZahl, GRAU, svgKopf, einheitKlasse, leer`), `ansicht.punkte`
- Produces: `zeige(ansicht, daten, optionen) → { svg, legende, zahlen, hoehe }`, `aktualisiere(svgEl, ansicht, daten, optionen) → { legende, zahlen }`, `berechne(ansicht, daten, optionen) → { breite, hoehe, kreise, karten, titel, legende, zahlen }`, `raster(breite) → { spalten }`; Kreise sind `<circle class="einheit p" data-id="<hex>|<gruppe>" data-gruppe data-zeile style="transform: translate(x px, y px)" r>`; Kartengruppen `<g class="karte" data-g="<gruppe>" style="opacity">`; Zechensymbol `<symbol id="pk-zeche">`

- [ ] **Step 1: Failing tests**

`site/tests/punktkarte.test.js`:

```js
import test from "node:test";
import assert from "node:assert/strict";
import { normalisiere, standardGruppen } from "../js/ansicht.js";
import { aktualisiere, berechne, raster, zeige } from "../js/formen/punktkarte.js";

const G = standardGruppen("bergbau");
const Q = (id, x, y) => ({ type: "Feature", properties: { id }, geometry: { type: "Polygon", coordinates: [[[x, y], [x + 0.1, y], [x + 0.1, y + 0.1], [x, y + 0.1], [x, y]]] } });
const PUNKTE = {
  gruppen: [{ id: "belegschaft", name: "Belegschaft", n: 5, felder: 2 }, { id: "aufsicht", name: "Aufsicht", n: 1, felder: 1 }, { id: "leitung", name: "Leitung und Beamte", n: 0, felder: 0 }, { id: "invaliden", name: "Berginvaliden", n: 0, felder: 0 }],
  hex: { belegschaft: [{ id: "0_0", lon: 7.01, lat: 51.45, n: 4, r: 9, x: 0, y: 0 }, { id: "1_0", lon: 7.02, lat: 51.46, n: 1, r: 4.5, x: 14, y: 0 }],
         aufsicht: [{ id: "0_0", lon: 7.01, lat: 51.45, n: 1, r: 4.5, x: 0, y: 0 }], leitung: [], invaliden: [] },
  haeuser: [{ id: "a1", lon: 7.01, lat: 51.45, eig: "gewerkschaft_mathias_stinnes", stufe: "haus" }, { id: "a2", lon: 7.02, lat: 51.46, eig: "zeche_x", stufe: "strasse" }],
  gesellschaften: [{ id: "gewerkschaft_mathias_stinnes", name: "Gewerkschaft Mathias Stinnes", haeuser: 1 }, { id: "zeche_x", name: "Zeche X", haeuser: 1 }],
  maxn: 4,
};
const DATEN = { punkte: PUNKTE, polygone: { type: "FeatureCollection", features: [Q("Katernberg", 7.0, 51.4)] },
  zechen: { type: "FeatureCollection", features: [{ type: "Feature", geometry: { type: "Point", coordinates: [7.05, 51.45] }, properties: { name: "Zollverein", aktiv_1936: true } }, { type: "Feature", geometry: { type: "Point", coordinates: [7.0, 51.4] }, properties: { name: "Alt", aktiv_1936: false } }] },
  kennzahlen: { teil_i_n: 100, beruf_geprueft_n: 80 } };
const A = (punkte) => normalisiere({ daten: "bergbau", ebene: "hex", form: "punktkarte", gruppen: G, bezug: "Belegschaft", min_n: 0, punkte });
const O = { breite: 1000, hoehe: 700 };

test("gesammelt: ein Kreis je Feld und Gruppe, Packung nebeneinander, Karten unsichtbar", () => {
  const r = zeige(A({ zustand: "gesammelt" }), DATEN, O);
  assert.equal((r.svg.match(/<circle class="einheit p"/g) || []).length, 3);
  assert.match(r.svg, /data-id="0_0\|belegschaft"[^>]*data-gruppe="belegschaft"/);
  assert.match(r.svg, /<g class="karte" data-g="belegschaft" style="opacity:0"/);
  assert.match(r.svg, /Belegschaft/); assert.match(r.svg, /5 eingetragene Personen/);
  const b = berechne(A({ zustand: "gesammelt" }), DATEN, O);
  const xs = b.titel.map((t) => t.x);
  assert.deepEqual([...xs].sort((p, q) => p - q), xs);                    // nach Größe sortiert von links nach rechts
  assert.ok(b.kreise.every((k) => k.x >= 0 && k.x <= 1000 && k.y >= 0 && k.y <= 700));
  assert.equal(r.zahlen.N, 6); assert.equal(r.zahlen.n_aus, 20);           // ungeprüfte Berufe als Ausschluss
  assert.equal(r.legende.find((l) => l.name === "Belegschaft").text, "Belegschaft · 5");
  assert.match(r.legende.map((l) => l.text).join(" "), /größter Wert 4/);
});

test("karten: jeder Kreis liegt im Feld seiner Gruppe, Mindestradius, nur Zechen in Förderung", () => {
  const b = berechne(A({ zustand: "karten" }), DATEN, O);
  for (const k of b.kreise) {
    const f = b.karten.find((c) => c.gruppe === k.gruppe);
    assert.ok(k.x >= f.x && k.x <= f.x + f.w && k.y >= f.y && k.y <= f.y + f.h, `${k.id} außerhalb`);
  }
  assert.ok(b.kreise.every((k) => k.r >= 1.6));
  assert.equal(b.karten[0].zechen.length, 1); assert.equal(b.karten[0].zechen[0].name, "Zollverein");
  const r = zeige(A({ zustand: "karten" }), DATEN, O);
  assert.match(r.svg, /<g class="karte" data-g="belegschaft" style="opacity:1"/);
  assert.match(r.svg, /<use class="zeche" href="#pk-zeche"/);
});

test("hervor dimmt die anderen Gruppen", () => {
  const b = berechne(A({ zustand: "karten", hervor: ["Belegschaft"] }), DATEN, O);
  assert.ok(b.kreise.filter((k) => k.gruppe === "aufsicht").every((k) => k.gedimmt));
  assert.ok(b.kreise.filter((k) => k.gruppe === "belegschaft").every((k) => !k.gedimmt));
  assert.match(zeige(A({ zustand: "karten", hervor: ["Belegschaft"] }), DATEN, O).svg, /class="einheit p gedimmt"/);
});

test("haeuser: ein Punkt je Haus, Farbe nach Gesellschaft, Ring bei nur straßengenau, Rest grau", () => {
  const a = normalisiere({ daten: "besitz", ebene: "adresse", form: "punktkarte", min_n: 0, bezug: "Stinnes",
    gruppen: [{ name: "Stinnes", aus: ["gewerkschaft_mathias_stinnes"], farbe: "#e69f00" }], punkte: { zustand: "haeuser" } });
  const r = zeige(a, DATEN, O);
  assert.equal((r.svg.match(/<circle class="einheit p/g) || []).length, 2);
  assert.match(r.svg, /data-id="a1"[^>]*fill="#e69f00"/);
  assert.match(r.svg, /data-id="a2"[^>]*fill="none"[^>]*stroke="#c8c8c8"/);
  assert.equal(r.zahlen.N, 2); assert.match(r.legende.map((l) => l.text).join(" "), /Ring: nur straßengenau oder Stadtplan 1935 \(1\)/);
  assert.match(r.legende.map((l) => l.text).join(" "), /übrige Bergbau-Eigentümer/);
});

test("raster: zwei Spalten ab 600 px, sonst eine", () => {
  assert.deepEqual(raster(1000), { spalten: 2 }); assert.deepEqual(raster(500), { spalten: 1 });
});

test("aktualisiere setzt Lage, Radius und Dimmung auf vorhandene Knoten, ohne sie zu ersetzen", () => {
  const knoten = (id, gruppe) => ({ dataset: { id, gruppe }, style: {}, attrs: {}, klassen: new Set(["einheit", "p"]),
    setAttribute(k, v) { this.attrs[k] = v; }, classList: { toggle(c, an) { an ? this.owner.klassen.add(c) : this.owner.klassen.delete(c); } } });
  const ks = [knoten("0_0|belegschaft", "belegschaft"), knoten("1_0|belegschaft", "belegschaft"), knoten("0_0|aufsicht", "aufsicht")];
  ks.forEach((k) => { k.classList.owner = k; });
  const karten = [{ dataset: { g: "belegschaft" }, style: {} }, { dataset: { g: "aufsicht" }, style: {} }];
  const titel = [{ dataset: { g: "belegschaft" }, style: {}, setAttribute(k, v) { this[k] = v; } }];
  const svgEl = { querySelectorAll: (sel) => sel === "circle.p" ? ks : sel === "g.karte" ? karten : titel };
  const r = aktualisiere(svgEl, A({ zustand: "karten", hervor: ["Belegschaft"] }), DATEN, O);
  assert.match(ks[0].style.transform, /^translate\([\d.]+px, ?[\d.]+px\)$/);
  assert.ok(Number(ks[0].attrs.r) >= 1.6); assert.ok(ks[2].klassen.has("gedimmt")); assert.ok(!ks[0].klassen.has("gedimmt"));
  assert.equal(karten[0].style.opacity, 1);
  assert.equal(r.zahlen.N, 6); assert.ok(Array.isArray(r.legende));
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `node --test site/tests/punktkarte.test.js`
Expected: FAIL mit `Cannot find module '../js/formen/punktkarte.js'`

- [ ] **Step 3: Form schreiben**

`site/js/formen/punktkarte.js`:

```js
// site/js/formen/punktkarte.js — Punktkarte des Bergbau-Kapitels (Spec 2026-09-28 §4): ein Kreis je Hexfeld und
// Gruppe, Kreisfläche = eingetragene Personen (absolut, kein min_n). Drei Zustände derselben Kreise:
// gesammelt (Packungen nebeneinander, nach Größe), karten (eine kleine Karte je Gruppe), haeuser (ein Punkt je
// Haus im Zechenbesitz, Farbe nach Gesellschaft). `zeige` baut das SVG, `aktualisiere` verschiebt die vorhandenen
// Kreise — die CSS-Transition macht daraus den fließenden Übergang. Rein, ohne DOM (node:test).
import { esc, formatZahl, GRAU, hinweisText, leer, svgKopf } from "./skalen.js";

const COS = Math.cos((51.45 * Math.PI) / 180);
const K_MAP = 0.62;            // Radius auf der Karte relativ zur Packung
const R_MIN_KARTE = 1.6;
const R_HAUS = 2.4;
const ABSTAND = 40;            // zwischen zwei Packungen
// Schlägel und Eisen (site/bilder/zeche.svg, Wikimedia Commons, gemeinfrei) als Symbol im SVG.
const ZECHE_PFAD = "M215 0 …";  // d-Attribut aus site/bilder/zeche.svg — beim Schreiben der Datei einsetzen (siehe Step 3a)

export const raster = (breite) => ({ spalten: breite >= 600 ? 2 : 1 });
const ringe = (g) => (!g ? [] : g.type === "MultiPolygon" ? g.coordinates.flat() : g.type === "Polygon" ? g.coordinates : []);

// Bounding-Box der Stadtteile in der Plattkarte (x = lon·cos φ, y = −lat).
function box(polygone) {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const f of polygone.features) for (const r of ringe(f.geometry)) for (const [lon, lat] of r) {
    const x = lon * COS, y = -lat;
    if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y;
  }
  return { minX, maxX, minY, maxY };
}

// Projektion in ein Rechteck; gibt xy(lon, lat) → [x, y] zurück.
function projektion(b, x0, y0, w, h) {
  const s = Math.min(w / (b.maxX - b.minX || 1), h / (b.maxY - b.minY || 1));
  const ox = x0 + (w - (b.maxX - b.minX) * s) / 2, oy = y0 + (h - (b.maxY - b.minY) * s) / 2;
  return { s, xy: (lon, lat) => [ox + (lon * COS - b.minX) * s, oy + (-lat - b.minY) * s] };
}

const pfad = (polygone, p) => polygone.features.map((f) => ringe(f.geometry).map((r) => "M" + r.map(([lon, lat]) => p.xy(lon, lat).map((v) => v.toFixed(1)).join(",")).join("L") + "Z").join("")).join("");

const zechenAktiv = (zechen) => (zechen && Array.isArray(zechen.features) ? zechen.features : []).filter((f) => f.properties && f.properties.aktiv_1936 && f.geometry && f.geometry.type === "Point");

// Alles, was Zeichnen und Aktualisieren gemeinsam brauchen: Kreise mit Ziel-Lage, Kartenfelder, Titel, Legende, Zahlen.
export function berechne(ansicht, daten, optionen = {}) {
  const P = daten && daten.punkte;
  const breite = optionen.breite || 600, hoehe = optionen.hoehe || 500;
  const zustand = (ansicht.punkte && ansicht.punkte.zustand) || "gesammelt";
  const hervor = new Set((ansicht.punkte && ansicht.punkte.hervor) || []);
  const farbeJe = new Map(); const nameJe = new Map();
  for (const g of ansicht.gruppen) for (const k of g.aus) { if (!farbeJe.has(k)) { farbeJe.set(k, g.farbe); nameJe.set(k, g.name); } }
  const b = daten.polygone && daten.polygone.features && daten.polygone.features.length ? box(daten.polygone) : null;
  const zechen = zechenAktiv(daten.zechen);

  if (zustand === "haeuser") {
    const rand = 16;
    const p = b ? projektion(b, rand, rand, breite - 2 * rand, hoehe - 2 * rand - 20) : null;
    const kreise = []; let ringeN = 0; const jeGes = new Map();
    for (const h of P.haeuser || []) {
      const [x, y] = p ? p.xy(h.lon, h.lat) : [0, 0];
      const inGruppe = farbeJe.has(h.eig);
      const ring = h.stufe !== "haus"; if (ring) ringeN += 1;
      jeGes.set(h.eig, (jeGes.get(h.eig) || 0) + 1);
      kreise.push({ id: h.id, gruppe: h.eig, x, y, r: R_HAUS, farbe: inGruppe ? farbeJe.get(h.eig) : GRAU, ring, gedimmt: false,
        zeile: `${inGruppe ? nameJe.get(h.eig) : "übrige Bergbau-Eigentümer"} · ${ring ? "nur straßengenau" : "hausgenau"}` });
    }
    const karten = [{ gruppe: "haeuser", x: rand, y: rand, w: breite - 2 * rand, h: hoehe - 2 * rand - 20, titel: "", pfad: b && p ? pfad(daten.polygone, p) : "",
      zechen: p ? zechen.map((z) => { const [x, y] = p.xy(z.geometry.coordinates[0], z.geometry.coordinates[1]); return { x, y, name: z.properties.name }; }) : [], sichtbar: true }];
    const legende = [...ansicht.gruppen.map((g) => ({ name: g.name, farbe: g.farbe, text: `${g.name} · ${formatZahl(g.aus.reduce((s, k) => s + (jeGes.get(k) || 0), 0))}` })),
      { name: "übrige", farbe: GRAU, text: "übrige Bergbau-Eigentümer" },
      { name: "ring", farbe: null, text: `Ring: nur straßengenau oder Stadtplan 1935 (${formatZahl(ringeN)})` },
      { name: "zechen", farbe: null, text: "Schlägel und Eisen: Zechen in Förderung 1936, Betreiber nicht zugeordnet" }];
    const N = kreise.length;
    const zahlen = { N, n_aus: 0, unter_min: 0, einheiten: N, einheiten_gesamt: N, hinweis: `${formatZahl(N)} geprüfte Häuser der Klasse Bergbau, ein Punkt je Haus` };
    return { breite, hoehe, kreise, karten, titel: [], legende, zahlen, zustand };
  }

  // gesammelt / karten: Gruppen in Kapitelreihenfolge, Packung je Gruppe nach Größe sortiert nebeneinander.
  const gruppen = ansicht.gruppen.map((g) => ({ name: g.name, farbe: g.farbe, schluessel: g.aus[0], n: (P.gruppen.find((x) => x.id === g.aus[0]) || { n: 0 }).n }));
  const reihe = [...gruppen].sort((a, c) => c.n - a.n);
  const ext = {}; for (const g of gruppen) { const ps = P.hex[g.schluessel] || []; ext[g.schluessel] = ps.length ? Math.max(...ps.map((k) => Math.hypot(k.x, k.y) + k.r)) : 4; }
  const kPack = Math.min(1.3, (breite - 2 * ABSTAND) / (reihe.reduce((s, g) => s + 2 * ext[g.schluessel], 0) + ABSTAND * (reihe.length - 1)));
  const mitte = {}; { let x = ABSTAND; for (const g of reihe) { x += ext[g.schluessel] * kPack; mitte[g.schluessel] = [x, hoehe / 2 - 24]; x += ext[g.schluessel] * kPack + ABSTAND; } }
  const { spalten } = raster(breite);
  const zeilen = Math.ceil(gruppen.length / spalten);
  const fw = breite / spalten, fh = (hoehe - 20) / zeilen;
  const karten = gruppen.map((g, i) => {
    const x = (i % spalten) * fw, y = Math.floor(i / spalten) * fh;
    const p = b ? projektion(b, x + 10, y + 20, fw - 20, fh - 26) : null;
    return { gruppe: g.schluessel, x, y, w: fw, h: fh, titel: `${g.name} · ${formatZahl(g.n)}`, pfad: b && p ? pfad(daten.polygone, p) : "", p,
      zechen: p ? zechen.map((z) => { const [zx, zy] = p.xy(z.geometry.coordinates[0], z.geometry.coordinates[1]); return { x: zx, y: zy, name: z.properties.name }; }) : [], sichtbar: zustand === "karten" };
  });
  const kreise = [];
  for (const g of gruppen) {
    const k = karten.find((c) => c.gruppe === g.schluessel);
    const gedimmt = hervor.size > 0 && !hervor.has(g.name);
    for (const pkt of P.hex[g.schluessel] || []) {
      let x, y, r;
      if (zustand === "karten" && k.p) { [x, y] = k.p.xy(pkt.lon, pkt.lat); r = Math.max(R_MIN_KARTE, pkt.r * kPack * K_MAP); }
      else { x = mitte[g.schluessel][0] + pkt.x * kPack; y = mitte[g.schluessel][1] + pkt.y * kPack; r = pkt.r * kPack; }
      kreise.push({ id: `${pkt.id}|${g.schluessel}`, gruppe: g.schluessel, x, y, r, farbe: g.farbe, ring: false, gedimmt,
        zeile: `${g.name} · ${formatZahl(pkt.n)} eingetragene Personen · Feld ${pkt.id}` });
    }
  }
  const titel = reihe.map((g) => ({ gruppe: g.schluessel, x: mitte[g.schluessel][0], y: mitte[g.schluessel][1] + ext[g.schluessel] * kPack + 18,
    name: g.name, wert: `${formatZahl(g.n)} eingetragene Personen`, sichtbar: zustand === "gesammelt" }));
  const N = gruppen.reduce((s, g) => s + g.n, 0);
  const kz = daten.kennzahlen || {};
  const n_aus = Math.max(0, (kz.teil_i_n || 0) - (kz.beruf_geprueft_n || 0));
  const zahlen = { N, n_aus, unter_min: 0, einheiten: kreise.length, einheiten_gesamt: kreise.length, hinweis: `${formatZahl(N)} eingetragene Personen mit Bergbau-Beruf, ${formatZahl(n_aus)} Einträge ohne geprüften Beruf ausgeschlossen` };
  const legende = [...gruppen.map((g) => ({ name: g.name, farbe: g.farbe, text: `${g.name} · ${formatZahl(g.n)}` })),
    { name: "mass", farbe: null, text: `Kreisfläche = eingetragene Personen je Hexfeld (120 m Kante), größter Wert ${formatZahl(P.maxn)}` },
    { name: "zechen", farbe: null, text: "Schlägel und Eisen: Zechen in Förderung 1936" }];
  return { breite, hoehe, kreise, karten, titel, legende, zahlen, zustand };
}

const kreisHtml = (k) => `<circle class="einheit p${k.gedimmt ? " gedimmt" : ""}" data-id="${esc(k.id)}" data-gruppe="${esc(k.gruppe)}" data-zeile="${esc(k.zeile)}" style="transform: translate(${k.x.toFixed(1)}px, ${k.y.toFixed(1)}px)" r="${k.r.toFixed(2)}" fill="${k.ring ? "none" : esc(k.farbe)}"${k.ring ? ` stroke="${esc(k.farbe)}" stroke-width="1.2"` : ""}><title>${esc(k.zeile)}</title></circle>`;

export function zeige(ansicht, daten, optionen = {}) {
  if (!daten || !daten.punkte || !Array.isArray(daten.punkte.gruppen)) return leer("Kapiteldaten des Bergbau-Kapitels fehlen");
  const b = berechne(ansicht, daten, optionen);
  const t = [svgKopf(b.breite, b.hoehe), `<defs><symbol id="pk-zeche" viewBox="0 0 430 430"><path d="${ZECHE_PFAD}"/></symbol></defs>`];
  for (const k of b.karten) {
    t.push(`<g class="karte" data-g="${esc(k.gruppe)}" style="opacity:${k.sichtbar ? 1 : 0}"><path class="umriss" d="${k.pfad}"/>`);
    if (k.titel) t.push(`<text class="karte-titel" x="${(k.x + 12).toFixed(1)}" y="${(k.y + 14).toFixed(1)}">${esc(k.titel)}</text>`);
    for (const z of k.zechen) t.push(`<use class="zeche" href="#pk-zeche" x="${(z.x - 6).toFixed(1)}" y="${(z.y - 6).toFixed(1)}" width="12" height="12"><title>${esc(z.name)}</title></use>`);
    t.push(`</g>`);
  }
  for (const k of b.kreise) t.push(kreisHtml(k));
  for (const ti of b.titel) t.push(`<text class="gruppe-titel" data-g="${esc(ti.gruppe)}" text-anchor="middle" x="${ti.x.toFixed(1)}" y="${ti.y.toFixed(1)}" style="opacity:${ti.sichtbar ? 1 : 0}">${esc(ti.name)}<tspan class="wert" x="${ti.x.toFixed(1)}" dy="15">${esc(ti.wert)}</tspan></text>`);
  t.push("</svg>");
  return { svg: t.join(""), legende: b.legende, zahlen: b.zahlen };
}

// Verschiebt die vorhandenen Kreise auf die Lage des neuen Zustands (Übergang per CSS-Transition auf transform/r).
// Voraussetzung: das SVG stammt aus `zeige` mit denselben Gruppen und einem Zustand ≠ haeuser (perspektiven.js prüft das).
export function aktualisiere(svgEl, ansicht, daten, optionen = {}) {
  const b = berechne(ansicht, daten, optionen);
  const je = new Map(b.kreise.map((k) => [k.id, k]));
  for (const el of svgEl.querySelectorAll("circle.p")) {
    const k = je.get(el.dataset.id); if (!k) continue;
    el.style.transform = `translate(${k.x.toFixed(1)}px, ${k.y.toFixed(1)}px)`;
    el.setAttribute("r", k.r.toFixed(2));
    el.classList.toggle("gedimmt", k.gedimmt);
  }
  for (const g of svgEl.querySelectorAll("g.karte")) { const k = b.karten.find((c) => c.gruppe === g.dataset.g); g.style.opacity = k && k.sichtbar ? 1 : 0; }
  for (const t of svgEl.querySelectorAll("text.gruppe-titel")) { const ti = b.titel.find((x) => x.gruppe === t.dataset.g); t.style.opacity = ti && ti.sichtbar ? 1 : 0; }
  return { legende: b.legende, zahlen: b.zahlen };
}
```

- [ ] **Step 3a: Zechenpfad einsetzen**

```bash
cd /home/christos/Projekte/essener-adressbuch-1936
python3 - <<'EOF'
import re
d = re.search(r'd="([^"]+)"', open("site/bilder/zeche.svg").read()).group(1)
p = "site/js/formen/punktkarte.js"; s = open(p).read()
s = s.replace('const ZECHE_PFAD = "M215 0 …";  // d-Attribut aus site/bilder/zeche.svg — beim Schreiben der Datei einsetzen (siehe Step 3a)', f'const ZECHE_PFAD = "{d}";')
open(p, "w").write(s); print("ok", len(d))
EOF
grep -c "M215 0 …" site/js/formen/punktkarte.js
```

Expected: `ok 3…`, danach `0`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `node --test site/tests/punktkarte.test.js`
Expected: PASS (6 Tests). Schlägt „jeder Kreis im Feld“ fehl, liegt es an Karten ohne Polygone (`p` null): die Testdaten haben ein Polygon, also die Projektion prüfen.

- [ ] **Step 5: Koppelnder Test — Zechenpfad gleich `bilder/zeche.svg`**

An `site/tests/punktkarte.test.js` anhängen:

```js
import { readFileSync } from "node:fs";
test("Zechensymbol der Punktkarte ist der Pfad aus bilder/zeche.svg", () => {
  const d = readFileSync(new URL("../bilder/zeche.svg", import.meta.url), "utf8").match(/ d="([^"]+)"/)[1];
  const js = readFileSync(new URL("../js/formen/punktkarte.js", import.meta.url), "utf8");
  assert.ok(js.includes(`const ZECHE_PFAD = "${d}"`));
});
```

Run: `node --test site/tests/punktkarte.test.js`
Expected: PASS (7 Tests).

- [ ] **Step 6: Commit**

```bash
git add site/js/formen/punktkarte.js site/tests/punktkarte.test.js
git commit -m "feat(formen): Punktkarte — Kreis je Hexfeld und Gruppe, gesammelt/karten/haeuser, aktualisiere für fließende Übergänge

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Perspektiven-Seite: Punktkarte einbinden, Übergänge, Links, Sichtprüfung

**Files:**
- Modify: `site/js/perspektiven.js:10-17, 88-98, 114-160`, `site/css/perspektiven.css` (Ende)

**Interfaces:**
- Consumes: `punktkarte.zeige/aktualisiere` (Task 6), `formFuer`, `linkKarte` (Task 5), `daten.punkte`
- Produces: Schrittwechsel zwischen zwei Punktkarten-Schritten derselben Gruppen (beide `zustand ≠ haeuser`) ruft `aktualisiere` statt `zeige`; Kapitel-Links: Punktkarte nur „Auf der Karte öffnen“ (kein Werkstatt-Link), im Zustand `haeuser` keine Links; Detailkasten bei Kreisen zeigt `data-zeile`

- [ ] **Step 1: Form registrieren und Links anpassen**

`site/js/perspektiven.js`:

```js
import * as punktkarte from "./formen/punktkarte.js";
const FORMEN = { balken, rangliste, stadtteilkarte, bubbles, trichter, punktkarte };
```

In `kapitelHtml`, die Zeile mit den Links ersetzen:

```js
    const a = normalisiere(s.ansicht);
    const lk = linkKarte(a);
    const links = [lk ? `<a href="${esc(lk)}">Auf der Karte öffnen</a>` : "", a.form === "punktkarte" ? "" : `<a href="${esc(linkWerkstatt(a))}">In der Werkstatt öffnen</a>`].filter(Boolean).join(" · ");
    return `${kopf}${links ? `<p class="links">${links}</p>` : ""}</article>`;
```

- [ ] **Step 2: Aktualisieren statt Ersetzen**

In `zeichne(sec, schritt, k)` nach `const optionen = …` und vor dem ersten `form.zeige`:

```js
  // Punktkarte → Punktkarte (gleiche Gruppen, kein Häuser-Zustand): die Kreise bleiben und wandern (Spec Bergbau §4).
  const vorige = gezeigt.ansicht;
  const gleitet = form === punktkarte && vorige && vorige.form === "punktkarte" && gezeigt.svg === svg
    && ansicht.punkte.zustand !== "haeuser" && vorige.punkte && vorige.punkte.zustand !== "haeuser"
    && JSON.stringify(vorige.gruppen) === JSON.stringify(ansicht.gruppen) && svg.querySelector("circle.p");
  if (gleitet) {
    const r = punktkarte.aktualisiere(svg, ansicht, daten, { ...zeichenflaeche(svg.clientWidth, svg.clientHeight), ...optionen });
    legende.innerHTML = legendeHtml(r.legende);
    zahlen.textContent = r.zahlen.hinweis;
    svg.setAttribute("aria-label", schritt.beschreibung || "");
    gezeigt = { ...gezeigt, ansicht, ausschluss: optionen.ausschlussText };
    return;
  }
```

Achtung: `gezeigt.svg` ist heute der Behälter `.svg` (siehe Zuweisung `gezeigt = { …, svg, … }`), `aktualisiere` erwartet ein Element mit `querySelectorAll` — der Behälter reicht, weil die Kreise darunter liegen. `zahlenText(r, ansicht)` bleibt für die anderen Formen; für die Punktkarte steht der Hinweis vollständig in `r.zahlen.hinweis` (kein min_n), darum in beiden Pfaden:

```js
  zahlen.textContent = trichterSchritt ? vorab.zahlen.hinweis : form === punktkarte ? vorab.zahlen.hinweis : zahlenText(vorab, ansicht);
```

Beim Klick auf einen Kreis (`.einheit`) füllt der bestehende Detailkasten `detailTextGruppe`/`data-zeile`: `kontextVon` liefert für unbekannte IDs `art: "einheit"`; damit der Kasten nicht ins Leere greift, in `kontextVon` ergänzen:

```js
  if (ansicht.form === "punktkarte") return { art: "kreis", ...k };
```

- [ ] **Step 3: CSS**

An `site/css/perspektiven.css` anhängen:

```css
/* Punktkarte (Bergbau): Kreise wandern per Transition zwischen Packung und Karte; Karten blenden. */
.buehne svg circle.p { transition: transform .9s cubic-bezier(.4, 0, .2, 1), r .9s cubic-bezier(.4, 0, .2, 1), opacity .5s ease; fill-opacity: .62; }
.buehne svg circle.p.gedimmt { opacity: .12; }
.buehne svg g.karte { transition: opacity .6s ease; }
.buehne svg g.karte .umriss { fill: #fff; stroke: #c9c5bc; stroke-width: .7; }
.buehne svg g.karte .zeche { fill: var(--text); opacity: .85; }
.buehne svg .karte-titel { font-size: 12px; font-weight: 600; fill: var(--text); }
.buehne svg .gruppe-titel { font-size: 13px; font-weight: 600; fill: var(--text); transition: opacity .6s ease; }
.buehne svg .gruppe-titel .wert { font-size: 12px; font-weight: 400; fill: var(--grau); }
@media (prefers-reduced-motion: reduce) { .buehne svg circle.p, .buehne svg g.karte, .buehne svg .gruppe-titel { transition: none; } }
```

- [ ] **Step 4: Sichtprüfung mit Playwright (Scratchpad)**

Dev-Server: `nohup python3 werkzeuge/serve.py 8765 >/dev/null 2>&1 &` falls `curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/site/schlaglichter.html` nicht 200 liefert. Skript im Scratchpad:

```python
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1400, "height": 900})
        fehler = []; pg.on("pageerror", lambda e: fehler.append(str(e)))
        await pg.goto("http://localhost:8765/site/schlaglichter.html?vorschau=1#k-bergbau")
        await pg.wait_for_selector("#k-bergbau .schritt")
        sec = pg.locator("#k-bergbau")
        for i, sid in enumerate(["gruppen", "karten", "belegschaft-leitung", "invaliden", "hausherr"]):
            await sec.locator(f'.schritt[data-schritt="{sid}"]').focus()
            await pg.wait_for_timeout(1200)
            await sec.locator(".buehne").screenshot(path=f"build/mockups/kapitel_bergbau_{i}_{sid}.png")
            if sid == "gruppen":
                erster = await sec.locator(".buehne circle.p").first.evaluate("el => { el.__marke = 1; return el.dataset.id }")
            if sid == "karten":
                gleich = await sec.locator(".buehne circle.p").first.evaluate("el => el.__marke === 1")
                print("Knoten bleibt beim Übergang erhalten:", gleich, erster)
        print("Kreise:", await sec.locator(".buehne circle.p").count(), "| Fehler:", fehler)
        print("Links:", await sec.locator(".links a").all_inner_texts())
        await b.close()
asyncio.run(main())
```

Expected: „Knoten bleibt beim Übergang erhalten: True“, keine Fehler, Screenshots zeigen Packungen, vier Karten mit Zechen, Dimmung, hausgenaue Karte; Links „Auf der Karte öffnen“ bei den Schritten 2–4, keine Werkstatt-Links, keine Links beim Häuser-Schritt. Screenshots ansehen (Read) und Abweichungen beheben.

- [ ] **Step 5: Tests**

Run: `node --test site/tests/*.test.js`
Expected: PASS

Hinweis (Spec §4): Die Bildrate des Übergangs misst der Projektleiter im eigenen Browser (Laptop und Handy) über `build/mockups/bergbau.html` (Anzeige oben rechts) oder auf der Kapitelseite. Liegt sie am Handy unter 30 fps, folgt ein eigener Plan für den Canvas-Rückfall; dieser Plan legt SVG fest.

- [ ] **Step 6: Commit**

```bash
git add site/js/perspektiven.js site/css/perspektiven.css
git commit -m "feat(schlaglichter): Punktkarte im Kapitel — Kreise wandern zwischen Schritten statt neu zu zeichnen; Kapitellinks auf das Thema Bergbau

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Thema-Schalter auf der Hauptkarte

**Files:**
- Modify: `site/js/themen.js`, `site/js/zustand.js:2-7, 27-45`, `site/js/karte.js:224-246` (`setzeFilter`), `site/js/app.js:95-140` (`setzeZustand`, `wendeThemaAn`), `:332-346` (Themenlegende), `site/css/stil.css:38-40`
- Test: `site/tests/themen.test.js`, `site/tests/zustand.test.js`, `site/tests/karte_ebenen.test.js`

**Interfaces:**
- Consumes: Thema-JSON mit `schalter: {praefix, klassen, namen}` (Task 4), Kachelfelder `n_bb_*` und `bergbau` (Task 2)
- Produces: `zustand.klassen` (String: `""` = alle, `"keine"`, sonst Komma-Liste); `schalterKlassen(thema, klassen) → string[]`; `schalterFilter(thema, klassen) → Ausdruck | null`; `schalterFarbe(thema, klassen) → Ausdruck`; `farbregel(thema, klassen = "")` liefert zusätzlich `filter` (Ausdruck oder null) und `klassen`; `ladeThema(lader, id, klassen = "")`; `karte.setzeFilter` hängt `this.farbe.filter` an; Legende mit Kästchen `input[type=checkbox][data-klasse]`

- [ ] **Step 1: Failing tests — Zustand**

In `site/tests/zustand.test.js` anhängen:

```js
test("klassen: Komma-Liste oder 'keine', Standard leer, Rundreise", () => {
  assert.equal(STANDARD.klassen, "");
  assert.equal(liesZustand("?thema=bergbau&klassen=leitung,aufsicht").klassen, "leitung,aufsicht");
  assert.equal(liesZustand("?klassen=keine").klassen, "keine");
  assert.equal(liesZustand("").klassen, "");
  assert.equal(schreibeZustand({ ...STANDARD, thema: "bergbau", klassen: "leitung" }), "klassen=leitung&thema=bergbau");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test site/tests/zustand.test.js`
Expected: FAIL — `STANDARD.klassen` undefined.

- [ ] **Step 3: Zustand**

`site/js/zustand.js`: in `STANDARD` nach `thema: ""` → `klassen: ""` ergänzen; in `liesZustand` nach `thema:` → `klassen: p.get("klassen") || "",`. (`schreibeZustand` läuft über `STANDARD`-Schlüssel und schreibt das Feld automatisch.)

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test site/tests/zustand.test.js`
Expected: PASS

- [ ] **Step 5: Failing tests — Schalterlogik**

In `site/tests/themen.test.js` anhängen:

```js
import { schalterFarbe, schalterFilter, schalterKlassen } from "../js/themen.js";
const BB = { id: "bergbau", titel: "Bergbau", freigegeben: true, filter: { ebenen: ["I"] },
  farbe: { art: "kategorien", feld: "bergbau", werte: { leitung: "#7c3aed", aufsicht: "#1d4ed8", belegschaft: "#c2410c", invaliden: "#15803d" } },
  schalter: { praefix: "n_bb_", klassen: ["leitung", "aufsicht", "belegschaft", "invaliden"], namen: { leitung: "Leitung und Beamte", aufsicht: "Aufsicht", belegschaft: "Belegschaft", invaliden: "Berginvaliden" } },
  zusatz: { zechen: true }, legende: "Farbe: höchste Bergbau-Gruppe im Haus" };

test("schalterKlassen: leer = alle, keine = [], unbekannte Werte fallen weg, Reihenfolge des Themas", () => {
  assert.deepEqual(schalterKlassen(BB, ""), ["leitung", "aufsicht", "belegschaft", "invaliden"]);
  assert.deepEqual(schalterKlassen(BB, "keine"), []);
  assert.deepEqual(schalterKlassen(BB, "belegschaft,quatsch,leitung"), ["leitung", "belegschaft"]);
  assert.deepEqual(schalterKlassen({ id: "besitz" }, "leitung"), []);
});

test("schalterFilter: any über eingeschaltete Klassen; alle aus → null; Thema ohne Schalter → null", () => {
  assert.deepEqual(schalterFilter(BB, "leitung,belegschaft"),
    ["any", [">", ["coalesce", ["get", "n_bb_leitung"], 0], 0], [">", ["coalesce", ["get", "n_bb_belegschaft"], 0], 0]]);
  assert.equal(schalterFilter(BB, "keine"), null);
  assert.equal(schalterFilter({ id: "besitz", farbe: { art: "kategorien", feld: "besitz", werte: {} } }, "leitung"), null);
});

test("schalterFarbe: case nach Rang über eingeschaltete Klassen, sonst Grau", () => {
  const f = schalterFarbe(BB, "aufsicht,belegschaft");
  assert.deepEqual(f, ["case", [">", ["coalesce", ["get", "n_bb_aufsicht"], 0], 0], "#1d4ed8", [">", ["coalesce", ["get", "n_bb_belegschaft"], 0], 0], "#c2410c", "#c8c8c8"]);
  // Haus mit Bergmann und Zechenbeamtem bei klassen=leitung: lila; Haus nur mit Bergmann: Grau (und per Filter weg)
  const nur = schalterFarbe(BB, "leitung");
  assert.deepEqual(nur, ["case", [">", ["coalesce", ["get", "n_bb_leitung"], 0], 0], "#7c3aed", "#c8c8c8"]);
});

test("farbregel mit Schalter trägt filter und klassen; ohne Schalter ignoriert sie klassen", () => {
  const r = farbregel(BB, "leitung");
  assert.deepEqual(r.filter, ["any", [">", ["coalesce", ["get", "n_bb_leitung"], 0], 0]]);
  assert.deepEqual(r.klassen, ["leitung"]); assert.equal(r.ausdruck[0], "case");
  const b = farbregel({ filter: {}, farbe: { art: "kategorien", feld: "besitz", werte: { bergbau: "#111" } } }, "leitung");
  assert.equal(b.filter, null); assert.equal(b.ausdruck[0], "match");
});
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `node --test site/tests/themen.test.js`
Expected: FAIL — `schalterKlassen` nicht exportiert.

- [ ] **Step 7: Schalterlogik**

`site/js/themen.js`, vor `farbregel`:

```js
// Schalter eines Themas (Spec Bergbau §5): welche Klassen an sind, welcher Kartenfilter und welche Farbe daraus folgt.
// `klassen` ist der URL-String: "" = alle, "keine" = keine, sonst Komma-Liste; Unbekanntes fällt weg.
export function schalterKlassen(thema, klassen = "") {
  const s = thema && thema.schalter;
  if (!s || !Array.isArray(s.klassen)) return [];
  if (klassen === "keine") return [];
  if (!klassen) return [...s.klassen];
  const gew = new Set(String(klassen).split(",").map((k) => k.trim()));
  return s.klassen.filter((k) => gew.has(k));
}
const feld = (thema, k) => [">", ["coalesce", ["get", `${thema.schalter.praefix}${k}`], 0], 0];
export function schalterFilter(thema, klassen = "") {
  const an = schalterKlassen(thema, klassen);
  return an.length ? ["any", ...an.map((k) => feld(thema, k))] : null;
}
// Farbe nach Rang: die Reihenfolge in schalter.klassen ist der Rang; abgeschaltete Klassen färben nicht.
export function schalterFarbe(thema, klassen = "") {
  const an = schalterKlassen(thema, klassen);
  const werte = (thema.farbe && thema.farbe.werte) || {};
  return ["case", ...an.flatMap((k) => [feld(thema, k), werte[k] || "#c8c8c8"]), (thema.farbe && thema.farbe.sonst) || "#c8c8c8"];
}
```

`farbregel(thema, klassen = "")`: im Zweig `kategorien` vor dem `return`:

```js
    if (thema.schalter) {
      return { merkmal: null, ausdruck: schalterFarbe(thema, klassen), kategorien: f.werte || {}, sonst: f.sonst || "#c8c8c8",
               filter: schalterFilter(thema, klassen), klassen: schalterKlassen(thema, klassen) };
    }
    return { merkmal: null, ausdruck: [...], kategorien: f.werte || {}, sonst: f.sonst || "#c8c8c8", filter: null };
```

`ladeThema(lader, id, klassen = "")` → `farbregel: farbregel(t, klassen)`.

- [ ] **Step 8: Run tests to verify they pass**

Run: `node --test site/tests/themen.test.js`
Expected: PASS

- [ ] **Step 9: Failing test — `setzeFilter` hängt den Schalterfilter an**

In `site/tests/karte_ebenen.test.js` anhängen:

```js
test("setzeFilter: Schalterfilter des Themas wird Teil des Adressfilters", () => {
  const filter = {}; const paint = {};
  const map = { getLayer: () => true, setFilter: (l, f) => { filter[l] = f; }, setPaintProperty: (l, k, v) => { paint[`${l}.${k}`] = v; }, setLayoutProperty: () => {} };
  const self = { map, farbe: { ausdruck: "#111", filter: ["any", [">", ["coalesce", ["get", "n_bb_leitung"], 0], 0]] }, ansicht: null, treffer: new Set(), _deckkraftSetzen() {} };
  Karte.prototype.setzeFilter.call(self, { ebene: ["I"], praez: ["haus"], stadtteil: "" });
  assert.ok(JSON.stringify(filter["adressen-haus"]).includes('"n_bb_leitung"'));
  self.farbe = { ausdruck: "#111", filter: null };
  Karte.prototype.setzeFilter.call(self, { ebene: ["I"], praez: ["haus"], stadtteil: "" });
  assert.ok(!JSON.stringify(filter["adressen-haus"]).includes("n_bb_"));
});
```

- [ ] **Step 10: Run test to verify it fails**

Run: `node --test site/tests/karte_ebenen.test.js`
Expected: FAIL — Filter enthält `n_bb_leitung` nicht.

- [ ] **Step 11: Karte und Seite**

`site/js/karte.js` in `setzeFilter` nach der `merkmal`-Bedingung:

```js
    if (this.farbe && this.farbe.filter) bedingungen.push(this.farbe.filter);   // Schalter eines Themas (Spec Bergbau §5)
```

`site/js/app.js`:

1. In `setzeZustand`: `if (alt.thema !== zustand.thema || alt.klassen !== zustand.klassen) await wendeThemaAn();`
2. `wendeThemaAn`: `const t = zustand.thema ? await ladeThema(lader, zustand.thema, zustand.klassen) : null;` und, damit `klassen` nicht an einem Thema ohne Schalter klebt: nach `themaAktiv = t;` → `if (!(t && t.schalter) && zustand.klassen) zustand = { ...zustand, klassen: "" };`
3. Themenlegende, Zweig `kategorien` ersetzen:

```js
    } else if (farbe.art === "kategorien" && themaAktiv.schalter) {
      html += `<div class="zeile"><b>${esc(themaAktiv.legende)}</b></div>`;
      const an = new Set(themaAktiv.farbregel.klassen || []);
      for (const k of themaAktiv.schalter.klassen) {
        html += `<label class="zeile schalter"><input type="checkbox" data-klasse="${esc(k)}"${an.has(k) ? " checked" : ""}><span class="punkt" style="background:${esc(farbe.werte[k] || "#c8c8c8")}"></span> ${esc(themaAktiv.schalter.namen?.[k] || k)}</label>`;
      }
      html += an.size ? `<div class="zeile klein">Adressen ohne eingeschaltete Gruppe sind ausgeblendet.</div>` : `<div class="zeile klein">Keine Gruppe gewählt – alle Adressen in Grundfarbe.</div>`;
    } else if (farbe.art === "kategorien") {
```

Nach `document.getElementById("legende").innerHTML = html;`:

```js
  document.querySelectorAll("#legende [data-klasse]").forEach((cb) => cb.addEventListener("change", () => {
    const alle = themaAktiv.schalter.klassen;
    const an = alle.filter((k) => document.querySelector(`#legende [data-klasse="${k}"]`).checked);
    setzeZustand({ klassen: an.length === alle.length ? "" : an.length ? an.join(",") : "keine" }, false);
  }));
```

`site/css/stil.css` nach `.legende .punkt`: `.legende label.schalter { cursor: pointer; } .legende label.schalter input { margin: 0 2px 0 0; }`.

- [ ] **Step 12: Run tests to verify they pass**

Run: `node --test site/tests/*.test.js`
Expected: PASS

- [ ] **Step 13: Sichtprüfung (Scratchpad-Playwright)**

```python
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1300, "height": 850})
        fehler = []; pg.on("pageerror", lambda e: fehler.append(str(e)))
        await pg.goto("http://localhost:8765/site/karte.html?thema=bergbau&klassen=leitung,aufsicht&z=13&c=7.01,51.47")
        await pg.wait_for_selector("#legende [data-klasse]")
        print("Kästchen:", await pg.evaluate("[...document.querySelectorAll('#legende [data-klasse]')].map(c => c.dataset.klasse + ':' + c.checked)"))
        await pg.click('#legende [data-klasse="belegschaft"]'); await pg.wait_for_timeout(300)
        print("URL nach Klick:", pg.url)
        await pg.click('#legende [data-klasse="leitung"]'); await pg.click('#legende [data-klasse="aufsicht"]'); await pg.click('#legende [data-klasse="belegschaft"]'); await pg.wait_for_timeout(300)
        print("URL keine:", pg.url, "| Text:", await pg.inner_text("#legende"))
        await pg.screenshot(path="build/mockups/karte_bergbau_thema.png")
        print("Fehler:", fehler)
        await b.close()
asyncio.run(main())
```

Expected: Kästchen leitung/aufsicht an, belegschaft/invaliden aus; nach Klick enthält die URL `klassen=leitung,aufsicht,belegschaft` (Reihenfolge des Themas); alle aus → `klassen=keine` und Text „Keine Gruppe gewählt“; keine Fehler. Screenshot ansehen.

- [ ] **Step 14: Commit**

```bash
git add site/js/themen.js site/js/zustand.js site/js/karte.js site/js/app.js site/css/stil.css site/tests/themen.test.js site/tests/zustand.test.js site/tests/karte_ebenen.test.js
git commit -m "feat(karte): Thema Bergbau mit Schaltern in der Legende — Klassen an- und abschalten, Filter und Rangfärbung aus dem Thema, Zustand in der URL (klassen=)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Dokumentation

**Files:**
- Create: `docs/bergbau.md`
- Modify: `README.md` (Abschnitte „Themenformat“, „Zählfelder und Aggregationsebenen“, „Kennzahlen“, „Perspektiven“, „URL-Parameter“), `site/ueber.html:25-31`

**Interfaces:**
- Consumes: alles aus Task 1–8
- Produces: Doku der Abgrenzung mit Begründungen für Nicht-Aufgenommenes (Spec §7)

- [ ] **Step 1: `docs/bergbau.md` schreiben**

```markdown
# Bergbau-Gruppen je Berufsnorm (Kapitel 4 der Schlaglichter, Thema „Bergbau“)

Stand: 2026-09-28. Tabelle `kuratierung/merkmale/bergbau.csv` (Norm → Gruppe), Modul `pipeline/lib/bergbau.py`,
Spec `docs/superpowers/specs/2026-09-28-bergbau-kapitel-design.md`.

## Warum nicht die OhdAB-Hauptgruppe B21?

B21 („Rohstoffgewinnung und -aufbereitung, Glas- und Keramikherstellung“) enthält neben Bergleuten Techniker,
Diplomingenieure, Schleifer, Gießer, Glasmacher, Steinmetze und Ziegler — Berufe, die ebenso in der
Metallverarbeitung standen. Für ein Bergbau-Kapitel zählen nur Berufe, die eindeutig zum Bergbau gehören.

## Vier Gruppen

| Gruppe | Schlüssel | Beispiele |
|---|---|---|
| Belegschaft | `belegschaft` | Bergmann, Hauer, Bergarbeiter, Anschläger, Fördermaschinist, Grubenschlosser |
| Aufsicht | `aufsicht` | Steiger (alle Arten), Schießmeister, Förderaufseher, Koksmeister |
| Leitung und Beamte | `leitung` | Zechenbeamter, Grubenbeamter, Bergassessor, Bergrat, Markscheider, Bergwerksdirektor |
| Berginvaliden | `invaliden` | Berginvalide |

Rang bei mehreren Gruppen im Haus (Adressfeld `bergbau`): Leitung > Aufsicht > Belegschaft > Berginvaliden.

## Grenzfälle (aufgenommen, mit Hinweis in der Tabelle)

- Kokereiarbeiter, Koksarbeiter: die Kokerei war meist Betriebsteil der Zeche, aber ein eigener Betriebsteil.
- Schlepper: im Ruhrbergbau ein Bergbau-Beruf; die OhdAB führt ihn unter Verkehr (B 5131).
- Oberschaffner: OhdAB B 2111, Bedeutung im Bergbau unklar.

## Nicht aufgenommen (mit Grund)

Techniker, Diplomingenieur (Tätigkeit ohne Branche), Schleifer, Gießer (Metall), Glasmacher, Steinmetz, Ziegler,
Zementeur (Steine, Glas, Keramik), Schachtmeister (Tiefbau-Polier, B 3229), Zimmerhauer (Bau), Kohlenhändler
(Handel), Bremser (Bahn).

## Zählfelder und Dateien

`n_bb_<gruppe>` je Adresse (Kacheln), Straße, Stadtteil, Hexfeld; Adressfeld `bergbau` (Rang); Kennzahlen
`bergbau_n`, `bergbau_<gruppe>_n`, `bergbau_haeuser_n`; Kapiteldaten `site/daten/perspektiven/bergbau_punkte.json`
(gepackte Kreise je Hexfeld und Gruppe, Häuser der Zechen mit Gesellschaft). Thema `kuratierung/themen/bergbau.json`
mit `schalter` (Kästchen in der Legende, URL-Parameter `klassen=`).

## Bezugsgröße

Teil I führt jede erwachsene Person mit eigenem Beruf oder Stand, nicht einen Eintrag je Haushalt (Befund 2026-09-28:
in 11.046 Fällen derselbe Nachname mehrfach an einer Adresse). Alle Texte sagen „eingetragene Personen“.

## Offen

Betreiber je Zeche (Historisches Portal), Adressabgleich Bergleute in Zechenhäusern, Betriebe des Bergbaus aus
Teil III nach Handprüfung, Prüfung der Tabelle durch den Projektleiter (`geprueft`).
```

- [ ] **Step 2: README und Über-Seite**

README: im Abschnitt „Themenformat“ einen Satz zu `schalter: {praefix, klassen, namen}` und `klassen=` in „URL-Parameter“; in „Zählfelder und Aggregationsebenen“ die Zeile `n_bb_<gruppe>` und das Adressfeld `bergbau`; in „Kennzahlen“ die `bergbau_*`-Schlüssel; in „Perspektiven“ die Form `punktkarte` mit `punkte: {zustand, hervor}` und Verweis auf `docs/bergbau.md`. `site/ueber.html`: „in vier Kapiteln“ → „in fünf Kapiteln“ und die Aufzählung um „Bergbau“ ergänzen (beide Stellen, Zeilen 26 und 31).

- [ ] **Step 3: Tests komplett**

Run: `python3 -m pytest -q && node --test site/tests/*.test.js`
Expected: alles PASS.

- [ ] **Step 4: Commit**

```bash
git add docs/bergbau.md README.md site/ueber.html
git commit -m "docs: Bergbau-Gruppen, Grenzfälle und Nicht-Aufgenommenes; Themenschalter, Punktkarte und Kennzahlen im README; Über-Seite fünf Kapitel

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```
