"""LLM-Reserve der Berufs-Vorschläge (Spec §4 Schritt 5): nur für ungesperrte Zeilen ohne Vorschlag; das Modell wählt
genau eine OhdAB-ID aus den 20 nächstliegenden Formen oder „unklar“. Ergebnis ist ein Vorschlag (vorschlag_grund=llm),
nie geprüft. Aufruf über werkzeuge/berufe_vorschlag.py --llm; braucht ANTHROPIC_API_KEY in der Umgebung."""
from __future__ import annotations

import json
import os
import urllib.request

from pipeline.lib.berufe import NIVEAUS, gesperrt
from werkzeuge.berufe_vorschlag import aehnlich

MODELL = "claude-sonnet-5"


def frage_anthropic(prompt: str, modell: str = MODELL) -> str:
    schluessel = os.environ.get("ANTHROPIC_API_KEY")
    if not schluessel:
        raise SystemExit("ANTHROPIC_API_KEY fehlt — --llm braucht einen API-Schlüssel")
    daten = json.dumps({"model": modell, "max_tokens": 40, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=daten, method="POST",
                                 headers={"x-api-key": schluessel, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        antwort = json.loads(r.read())
    return "".join(b.get("text", "") for b in antwort.get("content", [])).strip()


def baue_prompt(schreibweise: str, belege: list[dict], kandidaten: list[tuple[str, float]], ohdab: dict[str, dict]) -> str:
    zeilen = [f"{oid}: {ohdab[oid]['norm']} ({NIVEAUS.get(ohdab[oid]['niveau'], '')}; {ohdab[oid]['gattung']})" for oid, _ in kandidaten]
    b = "; ".join(f"{x['name']}, {x['adresse']} (Teil {x['teil']}, S. {x['seite']})" for x in belege[:3]) or "keine"
    return ("Adressbuch Essen 1936, Berufsangabe (abgekürzt): „" + schreibweise + "“.\nBeispiel-Einträge: " + b +
            "\nWelcher der folgenden OhdAB-Einträge bezeichnet diesen Beruf? Antworte NUR mit der ID (z. B. B 21112-100) "
            "oder mit „unklar“, wenn keiner sicher passt.\n" + "\n".join(zeilen))


def ergaenze_llm(zeilen: list[dict], belege: dict[str, list[dict]], ohdab: dict[str, dict], index: dict[str, list[str]],
                 datum: str, frage=frage_anthropic) -> list[dict]:
    if frage is frage_anthropic and not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY fehlt — --llm braucht einen API-Schlüssel")
    out = [dict(z) for z in zeilen]
    for z in out:
        if gesperrt(z) or z.get("ohdab_id"):
            continue
        kandidaten = aehnlich(z.get("beruf") or z["schreibweise"], index, schwelle=0.0, n=20)
        if not kandidaten:
            continue
        antwort = frage(baue_prompt(z["schreibweise"], belege.get(z["schreibweise"], []), kandidaten, ohdab)).strip()
        if antwort in {oid for oid, _ in kandidaten}:
            z.update(ohdab_id=antwort, vorschlag_grund="llm", datum=datum)
    return out
