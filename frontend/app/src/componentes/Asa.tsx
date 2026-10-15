// Asa de las hojas inferiores en móvil (panel y ficha). Arrastrarla cambia la altura de la hoja sin pasar por React en
// cada cuadro; al soltar se queda en la altura fija más cercana, o en la siguiente si el gesto es rápido. Tocarla (o
// Intro/Espacio) pasa a la siguiente altura y desde la mayor vuelve a la menor. Con onCerrar, arrastrarla por debajo
// de la menor cierra la hoja.
import { useLayoutEffect, useRef, type RefObject } from "react";

interface Props {
  hoja: RefObject<HTMLElement>;
  alturas: number[]; // px, de menor a mayor
  indice: number;
  onIndice: (k: number) => void;
  onMover?: (px: number) => void; // altura en vivo, para lo que va pegado encima de la hoja (leyenda)
  onCerrar?: () => void;
  etiqueta: string;
}

const UMBRAL = 6; // px de recorrido para que cuente como arrastre y no como toque
const RAPIDO = 0.5; // px/ms: un gesto más rápido salta a la altura siguiente en su sentido
const CERRAR = 90; // px por debajo de la menor altura para cerrar

export default function Asa({ hoja, alturas, indice, onIndice, onMover, onCerrar, etiqueta }: Props) {
  const gesto = useRef<{ y0: number; h0: number; y: number; t: number; v: number; movido: boolean } | null>(null);
  const sinClic = useRef(false); // el clic que sigue a un arrastre no alterna
  const mover = useRef(onMover);
  mover.current = onMover;

  const fijar = (px: number, animar: boolean) => {
    const e = hoja.current;
    if (!e) return;
    e.classList.toggle("arrastrando", !animar);
    e.style.height = `${Math.round(px)}px`;
    mover.current?.(px);
  };

  useLayoutEffect(() => fijar(alturas[indice] ?? alturas[0], true),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [indice, alturas]);
  // Al volver a escritorio (o cerrar la hoja) la hoja recupera su tamaño de CSS
  useLayoutEffect(() => {
    const e = hoja.current;
    return () => { e?.style.removeProperty("height"); e?.classList.remove("arrastrando"); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const soltar = (cancelado: boolean) => {
    const g = gesto.current;
    gesto.current = null;
    if (!g || !g.movido || !hoja.current) return;
    sinClic.current = true;
    const h = hoja.current.getBoundingClientRect().height;
    if (!cancelado && onCerrar && (h < alturas[0] - CERRAR || (g.v > RAPIDO && h < alturas[0]))) return onCerrar();
    let k = alturas.reduce((m, a, i) => (Math.abs(a - h) < Math.abs(alturas[m] - h) ? i : m), 0);
    if (!cancelado && g.v > RAPIDO) k = Math.max(0, alturas.filter((a) => a < h - 1).length - 1);
    else if (!cancelado && g.v < -RAPIDO) {
      const arriba = alturas.findIndex((a) => a > h + 1);
      k = arriba < 0 ? alturas.length - 1 : arriba;
    }
    fijar(alturas[k], true);
    onIndice(k);
  };

  return (
    <button type="button" className="asa" aria-label={etiqueta}
      onClick={() => {
        if (sinClic.current) { sinClic.current = false; return; }
        onIndice(indice < alturas.length - 1 ? indice + 1 : 0);
      }}
      onPointerDown={(e) => {
        if (e.button !== 0 || !hoja.current) return;
        e.currentTarget.setPointerCapture(e.pointerId);
        sinClic.current = false;
        gesto.current = { y0: e.clientY, h0: hoja.current.getBoundingClientRect().height, y: e.clientY, t: e.timeStamp, v: 0,
          movido: false };
      }}
      onPointerMove={(e) => {
        const g = gesto.current;
        if (!g) return;
        const dy = e.clientY - g.y0;
        if (!g.movido && Math.abs(dy) < UMBRAL) return;
        g.movido = true;
        g.v = (e.clientY - g.y) / Math.max(1, e.timeStamp - g.t);
        g.y = e.clientY;
        g.t = e.timeStamp;
        const minimo = alturas[0] - (onCerrar ? CERRAR * 1.6 : 24);
        fijar(Math.min(alturas[alturas.length - 1] + 16, Math.max(minimo, g.h0 - dy)), false);
      }}
      onPointerUp={() => soltar(false)}
      onPointerCancel={() => soltar(true)} />
  );
}
