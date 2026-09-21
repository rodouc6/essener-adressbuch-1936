// Geometrie der Startseite: eine Koordinate auf das per object-fit: cover zugeschnittene Planbild legen.
// Das Bild (EPSG:3857-Box, Seitenverhältnis) füllt den Behälter; überstehende Ränder werden nach
// ankerX (0 = links, 1 = rechts; vertikal immer mittig) beschnitten. Ergebnis in Prozent des Behälters,
// oder null, wenn der Punkt außerhalb des sichtbaren Ausschnitts liegt.
const R = 6378137;

export function nach3857(lon, lat) {
  const x = (lon * Math.PI / 180) * R;
  const y = Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI / 180) / 2)) * R;
  return [x, y];
}

export function punktLage(lon, lat, plan, breite, hoehe) {
  const [x0, y0, x1, y1] = plan.bbox3857;
  const [x, y] = nach3857(lon, lat);
  const u = (x - x0) / (x1 - x0), v = (y1 - y) / (y1 - y0);   // Anteil im Bild (0..1), v von oben
  if (u < 0 || u > 1 || v < 0 || v > 1) return null;
  const bildBreite = plan.seitenverhaeltnis;                   // Bild als (r × 1)
  const skala = Math.max(breite / bildBreite, hoehe / 1);      // cover: größerer Faktor
  const bw = bildBreite * skala, bh = 1 * skala;               // gerenderte Bildgröße in Behälterpixeln
  const ox = (breite - bw) * (plan.ankerX ?? 0.5), oy = (hoehe - bh) * 0.5;
  const px = ox + u * bw, py = oy + v * bh;
  if (px < 0 || px > breite || py < 0 || py > hoehe) return null;
  return { x: 100 * px / breite, y: 100 * py / hoehe };
}
