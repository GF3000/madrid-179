// Estrellas del asistente al mapa: cada preferencia o requisito que ha entendido el asistente lanza una estrella
// desde su línea de la tarjeta hasta un municipio que sube de grupo con ella; al llegar deja una onda y entonces se
// mueven las columnas. Así se ve que lo entendido es lo que cambia el mapa.
import { useEffect, useRef } from "react";
import { ESTRELLA } from "./piezas";

export interface Trayecto {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

// Tiempos en ms: salida escalonada, vuelo y onda al llegar
const ESCALON = 90;
const VUELO = 620;
const ONDA = 480;
export const DURACION_VIAJE = (n: number) => (n - 1) * ESCALON + VUELO; // cuándo ha llegado la última

const limitar = (x: number) => Math.min(1, Math.max(0, x));
const suave = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

// Orígenes: las etiquetas de la tarjeta «lo que hemos entendido» (como mucho siete, una por estrella de la bandera)
export function origenesTarjeta(): { x: number; y: number }[] {
  return [...document.querySelectorAll(".entendido-lista .chip")].slice(0, 7).map((e) => {
    const r = e.getBoundingClientRect();
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  });
}

export default function Viaje({ trayectos, onFin }: { trayectos: Trayecto[]; onFin: () => void }) {
  const raiz = useRef<SVGSVGElement>(null);
  const fin = useRef(onFin);
  fin.current = onFin;

  useEffect(() => {
    const estrellas = [...raiz.current!.querySelectorAll<SVGGElement>(".viaje-estrella")];
    const ondas = [...raiz.current!.querySelectorAll<SVGCircleElement>(".viaje-onda")];
    const total = DURACION_VIAJE(trayectos.length) + ONDA;
    const t0 = performance.now();
    let id = 0;
    const cuadro = (ahora: number) => {
      const t = ahora - t0;
      trayectos.forEach((v, k) => {
        const e = suave(limitar((t - k * ESCALON) / VUELO));
        const arco = Math.sin(Math.PI * e) * Math.min(140, Math.hypot(v.x1 - v.x0, v.y1 - v.y0) * 0.3);
        const x = v.x0 + (v.x1 - v.x0) * e;
        const y = v.y0 + (v.y1 - v.y0) * e - arco;
        const escala = e < 1 ? 0.9 + 0.5 * Math.sin(Math.PI * e) : 0;
        estrellas[k].setAttribute("transform", `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${(e * 216).toFixed(0)}) scale(${escala.toFixed(3)})`);
        estrellas[k].style.opacity = t < k * ESCALON ? "0" : "1";
        const o = limitar((t - k * ESCALON - VUELO) / ONDA);
        ondas[k].setAttribute("r", (4 + 26 * (1 - Math.pow(1 - o, 3))).toFixed(1));
        ondas[k].style.opacity = o > 0 && o < 1 ? String(1 - o) : "0";
      });
      if (t < total) id = requestAnimationFrame(cuadro);
      else fin.current();
    };
    id = requestAnimationFrame(cuadro);
    return () => cancelAnimationFrame(id);
  }, [trayectos]);

  return (
    <svg className="viaje" ref={raiz} aria-hidden>
      {trayectos.map((v, k) => (
        <g key={k}>
          <circle className="viaje-onda" cx={v.x1} cy={v.y1} r="0" />
          <g className="viaje-estrella" transform="scale(0)"><polygon points={ESTRELLA} /></g>
        </g>
      ))}
    </svg>
  );
}
