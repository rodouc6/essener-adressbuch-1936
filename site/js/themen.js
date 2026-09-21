// Ein Thema ist eine Voreinstellung: Merkmalsfilter, Farbregel, Zusatzebenen, Text (Spec §8).
export function farbregel(thema) {
  const f = thema.farbe;
  if (!f) return null;
  if (f.art === "einfach") return { merkmal: thema.filter?.merkmal || null, ausdruck: f.wert };
  if (f.art === "skala") {
    const stufen = f.stufen.flatMap(([w, farbe]) => [w, farbe]);
    return { merkmal: f.merkmal, ausdruck: ["interpolate", ["linear"], ["coalesce", ["get", `m_${f.merkmal}`], 0], ...stufen] };
  }
  return null;
}

export async function ladeThema(lader, id) {
  const t = await lader.thema(id);
  if (!t) return null;
  return { ...t, farbregel: farbregel(t), ebenen: t.filter?.ebenen || null };
}

export async function themenListe(lader) {
  const l = (await lader.json("themen/index.json")) || [];
  return l.filter((t) => t.freigegeben).map((t) => ({ id: t.id, titel: t.titel }));
}
