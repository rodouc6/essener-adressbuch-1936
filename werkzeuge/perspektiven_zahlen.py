"""Rechnet die Zahlen nach, die die Texte der Schlaglichter nennen — gegen site/daten/ebenen und layout.
Aufruf: python3 werkzeuge/perspektiven_zahlen.py. Kein Test, ein Prüfblatt (nach jeder Prüfrunde wiederholen)."""
import json, pathlib
W = pathlib.Path(__file__).resolve().parents[1] / "site" / "daten"
st = json.loads((W / "ebenen" / "stadtteile.json").read_text())
sr = json.loads((W / "ebenen" / "strassen.json").read_text())
kz = json.loads((W / "kennzahlen.json").read_text())
S = lambda k: sum(x.get(k, 0) for x in st)


def rang(zaehler, nenner, min_n=50, rev=True, n=5):
    r = []
    for x in st:
        d = sum(x.get(k, 0) for k in nenner)
        if d < min_n: continue
        z = sum(x.get(k, 0) for k in zaehler)
        r.append((x["id"], z, d, round(100 * z / d, 1)))
    return sorted(r, key=lambda t: t[3], reverse=rev)[:n]


BS = ["n_bs_privatperson", "n_bs_stadt_staat", "n_bs_bergbau", "n_bs_industrie", "n_bs_genossenschaft_siedlung", "n_bs_kirche_stiftung", "n_bs_bank_versicherung", "n_bs_sonstige", "n_bs_gemischt"]
ST = ["n_st_arbeiter", "n_st_angestellte", "n_st_beamte", "n_st_selbstaendige", "n_st_freie_berufe", "n_st_unternehmer", "n_st_kaufleute", "n_st_ohne_erwerb"]
print("Kennzahlen:", {k: kz[k] for k in ("adressen", "besitz_geprueft", "besitz_hand", "besitz_regel", "teil_i_n", "stellung_hand_n", "stellung_unbestimmt_n", "betriebe_n")})
print("Besitz gesamt:", {k: S(k) for k in BS}, "ungeprüft", S("n_bs_ungeprueft"))
print("Privat oben:", rang(["n_bs_privatperson"], BS)); print("Privat unten:", rang(["n_bs_privatperson"], BS, rev=False))
print("Zechen+Werke:", rang(["n_bs_bergbau", "n_bs_industrie"], BS)); print("Genossenschaft:", rang(["n_bs_genossenschaft_siedlung"], BS))
print("Stiftung:", rang(["n_bs_kirche_stiftung"], BS, n=2))
print("Stellung gesamt:", {k: S(k) for k in ST}, "unbestimmt", S("n_st_unbestimmt"), "Teil I", S("n_I"))
print("Arbeiter oben:", rang(["n_st_arbeiter"], ST, 200)); print("Arbeiter unten:", rang(["n_st_arbeiter"], ST, 200, rev=False))
print("Bürgertum:", rang(["n_st_beamte", "n_st_angestellte", "n_st_freie_berufe", "n_st_unternehmer"], ST, 200))
print("unbestimmt oben:", rang(["n_st_unbestimmt"], ST + ["n_st_unbestimmt"], 200)); print("unbestimmt unten:", rang(["n_st_unbestimmt"], ST + ["n_st_unbestimmt"], 200, rev=False))
GW = sorted({k for x in st for k in x if k.startswith("n_gw_")})
print("Gewerbe je Branche:", sorted(((k, S(k)) for k in GW), key=lambda t: -t[1]), "Betriebe", S("n_III"))
d = sorted(((x["id"], round(1000 * x.get("n_III", 0) / x["n_I"]), x.get("n_III", 0)) for x in st if x["n_I"] >= 200), key=lambda t: -t[1])
print("Dichte oben:", d[:5], "unten:", d[-4:])
l = sorted(((x["id"], round(1000 * x.get("n_gw_lebensmittel", 0) / x["n_I"], 1)) for x in st if x["n_I"] >= 200), key=lambda t: -t[1])
print("Lebensmittel oben:", l[:5], "unten:", l[-3:])
g = sorted(((x["name"], x.get("n_III", 0), x.get("n_I", 0), round(1000 * x.get("n_III", 0) / x["n_I"])) for x in sr if x.get("n_I", 0) >= 30), key=lambda t: -t[3])
print("Geschäftsstraßen nach Dichte:", g[:6])
print("Geschäftsstraßen nach Zahl:", sorted(((x["name"], x.get("n_III", 0)) for x in sr), key=lambda t: -t[1])[:5])
for name in ("eigentuemer", "gewerbe"):
    kreise = json.loads((W / "layout" / f"{name}.json").read_text())["kreise"]
    print(name, len(kreise), [(k["id"], k["n"], k["gruppe"]) for k in sorted(kreise, key=lambda k: -k["n"])[:10]])
