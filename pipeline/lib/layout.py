"""Deterministische Bubble-Layouts (Teilprojekt 5a, Spec §5.4): Kreispackung per Spiralsuche, Gruppenpackung,
Beeswarm je Spalte. Keine Zufallszahl, keine Simulation — gleiche Eingabe, gleiche Koordinaten. Einheiten sind
abstrakte Pixel; die Seite skaliert."""
from __future__ import annotations

import math

MIN_R = 2.0


def radius(wert: float, max_wert: float, max_r: float = 60.0) -> float:
    if wert <= 0 or max_wert <= 0:
        return MIN_R
    return max(MIN_R, round(max_r * math.sqrt(wert / max_wert), 3))


def ueberlappen(kreise: list[dict]) -> list[tuple[str, str]]:
    paare = []
    for i, a in enumerate(kreise):
        for b in kreise[i + 1:]:
            if math.hypot(a["x"] - b["x"], a["y"] - b["y"]) < a["r"] + b["r"] - 1e-6:
                paare.append((a["id"], b["id"]))
    return paare


class _Raster:
    """Nachbarschaftsgitter für schnelle Überlappungsprüfung."""

    def __init__(self, zelle: float):
        self.zelle = max(zelle, 1.0)
        self.zellen: dict[tuple[int, int], list[dict]] = {}

    def _k(self, x: float, y: float) -> tuple[int, int]:
        return int(math.floor(x / self.zelle)), int(math.floor(y / self.zelle))

    def frei(self, x: float, y: float, r: float, abstand: float) -> bool:
        kx, ky = self._k(x, y)
        reich = int(math.ceil((r + abstand) / self.zelle)) + 1
        for i in range(kx - reich, kx + reich + 1):
            for j in range(ky - reich, ky + reich + 1):
                for o in self.zellen.get((i, j), ()):
                    if math.hypot(o["x"] - x, o["y"] - y) < o["r"] + r + abstand:
                        return False
        return True

    def lege(self, k: dict) -> None:
        self.zellen.setdefault(self._k(k["x"], k["y"]), []).append(k)


def _spirale(schritt: float, start_radius: float = 0.0):
    """Punkte auf einer archimedischen Spirale, deterministisch. `start_radius` lässt die Suche
    nahe am aktuellen Packungsradius beginnen statt immer wieder am Ursprung — das hält die
    Spiralsuche bei vielen Kreisen schnell, ohne Zufall ins Spiel zu bringen."""
    t = 2.0 * max(start_radius, 0.0)
    if t == 0.0:
        yield 0.0, 0.0
    while True:
        t += schritt / max(1.0, 0.5 * t)
        yield 0.5 * t * math.cos(t), 0.5 * t * math.sin(t)


def _packe(kreise: list[dict], abstand: float, cx: float = 0.0, cy: float = 0.0) -> None:
    if not kreise:
        return
    reihenfolge = sorted(kreise, key=lambda k: (-k["r"], str(k["id"])))
    raster = _Raster(2 * max(k["r"] for k in kreise) + abstand)
    packungsradius = 0.0
    for k in reihenfolge:
        for x, y in _spirale(max(k["r"], 1.0), packungsradius - k["r"]):
            if raster.frei(cx + x, cy + y, k["r"], abstand):
                k["x"], k["y"] = round(cx + x, 2), round(cy + y, 2)
                raster.lege(k)
                packungsradius = max(packungsradius, math.hypot(x, y) + k["r"])
                break


def packe_kreise(kreise: list[dict], abstand: float = 1.0) -> list[dict]:
    """Kreise {id, r} → mit x, y; größte zuerst um den Ursprung, Reihenfolge der Liste bleibt."""
    out = [dict(k) for k in kreise]
    _packe(out, abstand)
    return out


def packe_gruppen(kreise: list[dict], abstand: float = 12.0) -> tuple[list[dict], list[dict]]:
    """Erst jede Gruppe für sich packen, dann die Gruppenkreise packen und die Mitglieder verschieben."""
    gruppen: dict[str, list[dict]] = {}
    out = [dict(k) for k in kreise]
    for k in out:
        gruppen.setdefault(k["gruppe"], []).append(k)
    huellen = []
    for g, mitglieder in sorted(gruppen.items()):
        _packe(mitglieder, 1.0)
        r = max(math.hypot(k["x"], k["y"]) + k["r"] for k in mitglieder)
        huellen.append(dict(id=g, gruppe=g, r=round(r + abstand / 2, 2)))
    _packe(huellen, abstand)
    for h in huellen:
        for k in gruppen[h["gruppe"]]:
            k["x"], k["y"] = round(k["x"] + h["x"], 2), round(k["y"] + h["y"], 2)
    return out, [dict(gruppe=h["gruppe"], x=h["x"], y=h["y"], r=h["r"]) for h in huellen]


def beeswarm(kreise: list[dict], spalten: list[str], breite: float = 80.0, spaltenabstand: float = 200.0) -> list[dict]:
    """Je Spalte: Kreise nach Größe absteigend, y vom Ursprung nach außen (abwechselnd ±), x innerhalb des Bands
    (Mitte zuerst, dann nach außen), erste freie Stelle gewinnt."""
    out = [dict(k) for k in kreise]
    for k in out:
        if k["r"] > breite:
            raise ValueError(
                f"Kreis {k.get('id')!r} hat Radius {k['r']}, größer als die Bandbreite {breite} — "
                "beeswarm() würde nie eine freie Stelle finden (breite muss >= max(r) sein)."
            )
    je_spalte: dict[str, list[dict]] = {}
    for k in out:
        je_spalte.setdefault(k["spalte"], []).append(k)
    for i, s in enumerate(spalten):
        mitte = i * spaltenabstand
        gelegt: list[dict] = []
        for k in sorted(je_spalte.get(s, []), key=lambda k: (-k["r"], str(k["id"]))):
            versaetze = [0.0] + [v * d for v in (0.25, 0.5, 0.75, 1.0) for d in (1, -1)]
            gefunden = False
            y = 0.0
            # Schrittweite an die Kreisgröße koppeln (statt fest 1.0): bei großen Kreisen sind
            # viele kleine Schritte unnötig, weil ohnehin erst nach ~einem Radius wieder Platz
            # sein kann. Bleibt deterministisch, da nur von k["r"] abhängig.
            schritt = max(1.0, k["r"] * 0.25)
            while not gefunden:
                for vz in (1, -1):
                    for v in versaetze:
                        x = mitte + v * (breite - k["r"])
                        if abs(x - mitte) + k["r"] > breite + 1e-9:
                            continue
                        if all(math.hypot(o["x"] - x, o["y"] - vz * y) >= o["r"] + k["r"] + 1.0 for o in gelegt):
                            # Auf 2 Nachkommastellen zu runden könnte den Kreis (bei v=1.0, also am
                            # Bandrand) minimal über die Bandgrenze schieben; 6 Stellen halten den
                            # Rundungsfehler unter der Prüftoleranz von 1e-6.
                            k["x"], k["y"] = round(x, 6), round(vz * y, 6)
                            gelegt.append(k); gefunden = True
                            break
                    if gefunden:
                        break
                y += schritt
    return out
