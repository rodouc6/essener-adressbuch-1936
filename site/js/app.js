import { Karte } from "./karte.js";
import { liesZustand } from "./zustand.js";

const zustand = liesZustand(location.search);
const karte = new Karte("karte", zustand, {
  onKlick: (id, lngLat) => karte.zeigePopup(lngLat, `<b>${id}</b>`),
  onBewegt: () => {},
  onHover: () => {},
});
await karte.bereit();
window.karte = karte;
