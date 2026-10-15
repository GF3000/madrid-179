// Pantalla de carga: los 179 municipios aparecen como puntos rojos en su sitio, se juntan en siete estrellas rojas
// (primero en forma de constelación), las estrellas se colocan como en la bandera y el carmesí entra por detrás y las
// recorta en blanco. Al terminar, el carmesí se transforma en el contorno de la Comunidad justo donde lo dibuja el
// mapa (con la cámara que tenga, girada o inclinada), las estrellas vuelan a la bandera de la cabecera y el carmesí
// se funde en los colores de los municipios.
// La animación espera a los datos reales: si no han llegado, las estrellas titilan antes de que entre el carmesí.
import { useEffect, useRef } from "react";
import type { Position } from "geojson";
import type { Geometria } from "../api";
import { PUNTOS } from "../puntos_carga";
import type { MandoMapa } from "./Mapa";
import { ESTRELLA, POSICIONES } from "./piezas";

const ANCHO = 300;
const ALTO = 200;
const RADIO_ESTRELLA = 21; // en el lienzo de 300 (10,5 en el de 150 de <Bandera>)

// Constelación de partida (una osa mayor estilizada) y sitio de cada estrella en la bandera
const OSA = [[62, 52], [100, 66], [128, 88], [152, 112], [150, 158], [214, 166], [226, 118]];
const SITIO = POSICIONES.map(([x, y]) => [x * 2, y * 2]);
const TRAZO = "M" + [0, 1, 2, 3, 4, 5, 6, 3].map((k) => OSA[k].join(" ")).join(" L");

// Tiempos de la secuencia, en milisegundos de animación (no de reloj: la velocidad puede cambiar)
const T = { juntar: 1050, trazar: 1800, deslizar: 2300, telon: 2950, salir: 3800, fin: 5300 };
const DURACION_TELON = 650;
const CLAVE_VISTA = "madrid179-intro-vista";
const ESPERA_MAPA = 2500; // ms que se espera a que cargue el mapa antes de salir sin él
const MUESTRAS = 320; // puntos de la transformación bandera → contorno

const limitar = (x: number) => Math.min(1, Math.max(0, x));
const tramo = (v: number, desde: number, dura: number) => limitar((v - desde) / dura);
const salida = (x: number) => 1 - Math.pow(1 - x, 3);
const suave = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const rebote = (x: number) => 1 + 2.2 * Math.pow(x - 1, 3) + 1.2 * Math.pow(x - 1, 2);

// Datos fijos de cada punto: retraso de aparición (onda desde Madrid), estrella a la que va y un azar estable
const MADRID = PUNTOS.find(([i]) => i === "28079")!;
const LEJOS = Math.max(...PUNTOS.map(([, x, y]) => Math.hypot(x - MADRID[1], y - MADRID[2])));
// Reparto equilibrado: cada estrella recoge unos 26 puntos, empezando por las parejas punto-estrella más cercanas
const destinos = new Array<number>(PUNTOS.length).fill(-1);
const cupo = OSA.map(() => Math.ceil(PUNTOS.length / OSA.length));
PUNTOS.flatMap(([, x, y], i) => OSA.map(([ox, oy], k) => ({ i, k, d: Math.hypot(x - ox, y - oy) })))
  .sort((a, b) => a.d - b.d)
  .forEach(({ i, k }) => {
    if (destinos[i] < 0 && cupo[k] > 0) { destinos[i] = k; cupo[k]--; }
  });
const DOTS = PUNTOS.map(([ine, x, y], i) => ({
  x, y, destino: destinos[i], retraso: (Math.hypot(x - MADRID[1], y - MADRID[2]) / LEJOS) * 620,
  azar: ((Number(ine) * 9301 + 49297) % 233280) / 233280,
}));
const POR_ESTRELLA = OSA.map((_, k) => DOTS.filter((d) => d.destino === k).length);

// ------------------------------------------- geometría de la transformación
type P = [number, number];

// n puntos a igual distancia a lo largo de un anillo cerrado
function remuestrear(anillo: P[], n: number): P[] {
  const pts = [...anillo, anillo[0]];
  const acum = [0];
  for (let i = 1; i < pts.length; i++) acum.push(acum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const total = acum[acum.length - 1];
  const fuera: P[] = [];
  let j = 1;
  for (let k = 0; k < n; k++) {
    const d = (k / n) * total;
    while (acum[j] < d) j++;
    const t = (d - acum[j - 1]) / (acum[j] - acum[j - 1] || 1);
    fuera.push([pts[j - 1][0] + (pts[j][0] - pts[j - 1][0]) * t, pts[j - 1][1] + (pts[j][1] - pts[j - 1][1]) * t]);
  }
  return fuera;
}

// Rectángulo de esquinas redondeadas, en sentido horario en pantalla
function rectanguloRedondeado(x: number, y: number, an: number, al: number, r: number): P[] {
  const esquinas = [[x + an - r, y + r, -90], [x + an - r, y + al - r, 0], [x + r, y + al - r, 90], [x + r, y + r, 180]];
  return esquinas.flatMap(([cx, cy, a0]) => Array.from({ length: 9 }, (_, i): P => {
    const a = ((a0 + i * 11.25) * Math.PI) / 180;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  }));
}

const area = (pts: P[]) => pts.reduce((s, [x, y], i) => {
  const [x2, y2] = pts[(i + 1) % pts.length];
  return s + x * y2 - x2 * y;
}, 0) / 2;

// Centro en el origen y tamaño unidad, para emparejar formas distintas punto a punto
function normalizar(pts: P[]): P[] {
  const cx = pts.reduce((s, q) => s + q[0], 0) / pts.length;
  const cy = pts.reduce((s, q) => s + q[1], 0) / pts.length;
  const r = Math.sqrt(pts.reduce((s, [x, y]) => s + (x - cx) ** 2 + (y - cy) ** 2, 0) / pts.length) || 1;
  return pts.map(([x, y]) => [(x - cx) / r, (y - cy) / r]);
}

// Anillo exterior mayor del contorno, remuestreado en lon/lat (longitud corregida por la latitud)
function anilloContorno(contorno: Geometria["contorno"]): P[] {
  const g = contorno.geometry;
  const anillos = (g.type === "Polygon" ? [g.coordinates[0]] : g.coordinates.map((x) => x[0])) as P[][];
  const mayor = anillos.reduce((a, b) => (Math.abs(area(b)) > Math.abs(area(a)) ? b : a));
  const c = Math.cos((40.4 * Math.PI) / 180);
  return remuestrear(mayor.slice(0, -1).map(([x, y]) => [x * c, y]), MUESTRAS).map(([x, y]) => [x / c, y]);
}

interface Morfo {
  rect: P[]; // la bandera en pantalla
  geo: Position[]; // el contorno en lon/lat, emparejado punto a punto con rect
  desde: { x: number; y: number; s: number }[]; // estrellas en la bandera grande
  hacia: { x: number; y: number; s: number }[]; // estrellas en la bandera de la cabecera
  mini: DOMRect; // bandera de la cabecera
}

interface Props {
  listo: boolean; // han llegado los datos
  mapa: MandoMapa | null; // para proyectar el contorno con la cámara real
  contorno: Geometria["contorno"] | null;
  onRevelar: () => void; // montar la app por debajo (entra el carmesí)
  onFin: () => void;
}

export default function Intro({ listo, mapa, contorno, onRevelar, onFin }: Props) {
  const raiz = useRef<HTMLDivElement>(null);
  const listoRef = useRef(listo);
  listoRef.current = listo;
  const mapaRef = useRef({ mapa, contorno });
  mapaRef.current = { mapa, contorno };
  const avisos = useRef({ onRevelar, onFin });
  avisos.current = { onRevelar, onFin };
  const prisa = useRef(1);

  useEffect(() => {
    const el = raiz.current!;
    const q = <E extends Element>(s: string) => [...el.querySelectorAll<E>(s)];
    const puntos = q<SVGCircleElement>(".intro-puntos circle");
    const rojas = q<SVGGElement>(".intro-rojas g");
    const blancas = q<SVGGElement>(".intro-blancas g");
    const [trazo] = q<SVGPathElement>(".intro-trazo");
    const [marco] = q<SVGRectElement>(".intro-marco");
    const telon = q<SVGRectElement>(".intro-telon");
    const [brillo] = q<SVGRectElement>(".intro-brillo");
    const [lienzo] = q<HTMLDivElement>(".intro-lienzo");
    const [fondo] = q<HTMLDivElement>(".intro-fondo");
    const textos = q<HTMLElement>(".intro-titulo, .intro-frase");
    const [titulo] = q<HTMLElement>(".intro-titulo");
    const [frase] = q<HTMLElement>(".intro-frase");
    const [forma] = q<SVGPathElement>(".intro-forma path");
    const [mini] = q<SVGRectElement>(".intro-forma rect");
    const voladoras = q<SVGGElement>(".intro-voladoras g");

    const reducido = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let repetida = false;
    try { repetida = sessionStorage.getItem(CLAVE_VISTA) === "1"; sessionStorage.setItem(CLAVE_VISTA, "1"); } catch { /* sin almacenamiento */ }

    let v = reducido ? T.salir - 1 : 0;
    let antes = performance.now();
    let revelada = false;
    let vuelo: { dx: number; dy: number; s: number } | null = null;
    let morfo: Morfo | null = null;
    let esperaMapa = 0;
    const paso = OSA.map(() => (reducido ? -1e9 : Infinity)); // instante en que el carmesí cubre cada estrella
    let textoFrase = "";
    let id = 0;

    const decir = (t: string) => {
      if (t === textoFrase) return;
      textoFrase = t;
      frase.textContent = t;
    };

    const cuadro = (ahora: number) => {
      const dt = Math.min(50, ahora - antes);
      antes = ahora;
      const listo = listoRef.current;
      const velocidad = Math.max(prisa.current, repetida ? 1.9 : 1, listo ? 1.3 : 1);
      v += dt * velocidad;
      const tope = reducido ? T.salir - 1 : T.telon;
      const esperando = !listo && v >= tope;
      if (!listo) v = Math.min(v, tope);
      // antes de salir, un margen para que el mapa termine de cargar (si no llega, se sale sin él)
      if (v >= T.salir && !morfo && !vuelo && !reducido && !mapaRef.current.mapa?.cargado() && esperaMapa < ESPERA_MAPA) {
        esperaMapa += dt;
        v = T.salir;
      }

      // 1 · aparecen los municipios (onda desde Madrid) · 2 · se juntan en las estrellas
      const llegada = OSA.map(() => 0);
      DOTS.forEach((d, i) => {
        const a = tramo(v, d.retraso, 380);
        const j = suave(tramo(v, T.juntar + d.azar * 320, 640));
        const tx = OSA[d.destino][0] - d.x;
        const ty = OSA[d.destino][1] - d.y;
        const giro = Math.sin(Math.PI * j) * 0.22 * (d.azar > 0.5 ? 1 : -1);
        const c = puntos[i];
        c.setAttribute("cx", (d.x + tx * j - ty * giro).toFixed(2));
        c.setAttribute("cy", (d.y + ty * j + tx * giro).toFixed(2));
        c.setAttribute("r", (2.3 * rebote(a) * (1 - 0.6 * j)).toFixed(2));
        c.setAttribute("opacity", (a * (j < 0.85 ? 1 : (1 - j) / 0.15)).toFixed(3));
        llegada[d.destino] += limitar((j - 0.6) / 0.4);
      });

      // 3 · constelación trazada · 4 · las estrellas van a su sitio en la bandera · 5 · entra el carmesí
      const pt = salida(tramo(v, T.trazar, 480));
      const pd = tramo(v, T.deslizar, 600);
      trazo.style.strokeDashoffset = String(1 - pt);
      trazo.style.opacity = String(pt * (1 - limitar(pd * 2)));
      const pc = suave(tramo(v, T.telon, DURACION_TELON));
      const borde = pc * ANCHO;
      marco.style.opacity = String(0.9 * pd * (1 - pc));
      telon.forEach((r) => r.setAttribute("width", borde.toFixed(2)));
      brillo.setAttribute("x", (borde - 16).toFixed(2));
      brillo.style.opacity = String(Math.sin(Math.PI * pc) * 0.55);

      OSA.forEach(([ox, oy], k) => {
        const s = llegada[k] / POR_ESTRELLA[k];
        const m = suave(tramo(v, T.deslizar + k * 40, 520));
        const x = ox + (SITIO[k][0] - ox) * m;
        const y = oy + (SITIO[k][1] - oy) * m;
        if (borde >= x + RADIO_ESTRELLA && paso[k] === Infinity) paso[k] = v;
        const pulso = Math.sin(Math.PI * tramo(v, paso[k], 300)) * 0.22;
        const titila = esperando && !reducido ? 0.08 * Math.sin(ahora / 240 + k * 0.9) : 0;
        const escala = 2 * Math.max(0, rebote(s)) * (1 + pulso + titila);
        const t = `translate(${x.toFixed(2)} ${y.toFixed(2)}) rotate(${(-90 * (1 - s)).toFixed(1)}) scale(${escala.toFixed(3)})`;
        rojas[k].setAttribute("transform", t);
        blancas[k].setAttribute("transform", t);
      });

      // textos
      if (v < T.juntar) decir(`${DOTS.filter((d) => v >= d.retraso + 190).length} de 179 municipios`);
      else if (esperando) decir("Preparando el mapa…");
      else if (v < T.telon) decir("Reuniendo los datos de cada municipio");
      else decir("Dónde abrir una oficina en los 179 municipios de la Comunidad de Madrid");
      const pti = salida(tramo(v, T.telon + 250, 450));
      titulo.style.opacity = String(pti);
      titulo.style.transform = `translateY(${(1 - pti) * 10}px)`;

      if (listo && v >= T.telon && !revelada) {
        revelada = true;
        avisos.current.onRevelar();
      }

      // 6 · salida: el carmesí se transforma en el contorno de la Comunidad y se funde en el mapa, y las estrellas
      // vuelan a la bandera de la cabecera. Sin mapa, la bandera vuela entera; con movimiento reducido, se funde.
      const ps = tramo(v, T.salir, T.fin - T.salir);
      if (ps > 0 && !morfo && !vuelo) {
        const destino = document.querySelector(".app .marca .bandera")?.getBoundingClientRect();
        const origen = lienzo.getBoundingClientRect();
        const { mapa, contorno } = mapaRef.current;
        const hayDestino = !reducido && destino !== undefined && destino.width > 0;
        if (hayDestino && mapa?.cargado() && contorno) morfo = prepararMorfo(origen, destino, mapa, contorno);
        else vuelo = hayDestino
          ? { dx: destino.left - origen.left, dy: destino.top - origen.top, s: destino.width / origen.width }
          : { dx: 0, dy: 0, s: 1 };
      }
      if (morfo) {
        const d = T.fin - T.salir;
        const pm = suave(tramo(v, T.salir, 0.6 * d));
        lienzo.style.opacity = "0";
        // se proyecta en cada cuadro: si la cámara se mueve (enlace directo a una ficha), el contorno la sigue
        const pantalla = mapaRef.current.mapa!.proyectar(morfo.geo);
        forma.setAttribute("d", "M" + morfo.rect.map(([x, y], k) =>
          `${(x + (pantalla[k][0] - x) * pm).toFixed(1)} ${(y + (pantalla[k][1] - y) * pm).toFixed(1)}`).join("L") + "Z");
        forma.style.fillOpacity = String(1 - suave(tramo(v, T.salir + 0.55 * d, 0.4 * d)));
        forma.style.strokeOpacity = String(tramo(v, T.salir + 0.4 * d, 0.25 * d));
        fondo.style.opacity = String(1 - suave(tramo(v, T.salir + 0.35 * d, 0.45 * d)));
        textos.forEach((t) => (t.style.opacity = String(Math.min(Number(t.style.opacity || 1), 1 - tramo(v, T.salir, 0.2 * d)))));
        const m = morfo.mini;
        mini.setAttribute("x", String(m.left));
        mini.setAttribute("y", String(m.top));
        mini.setAttribute("width", String(m.width));
        mini.setAttribute("height", String(m.height));
        mini.setAttribute("rx", String((6 / 150) * m.width));
        mini.style.opacity = String(tramo(v, T.salir + 0.45 * d, 0.25 * d));
        morfo.desde.forEach((a, k) => {
          const b = morfo!.hacia[k];
          const e = suave(tramo(v, T.salir + 0.04 * d * k, 0.6 * d));
          const arco = Math.sin(Math.PI * e) * 60;
          const x = a.x + (b.x - a.x) * e - arco * 0.3;
          const y = a.y + (b.y - a.y) * e - arco;
          voladoras[k].setAttribute("transform",
            `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${(e * 144).toFixed(1)}) scale(${(a.s + (b.s - a.s) * e).toFixed(3)})`);
        });
      }
      if (vuelo) {
        const pv = suave(ps);
        lienzo.style.transform = `translate(${vuelo.dx * pv}px, ${vuelo.dy * pv}px) scale(${1 + (vuelo.s - 1) * pv})`;
        if (vuelo.s === 1) lienzo.style.opacity = String(1 - pv);
        fondo.style.opacity = String(1 - pv);
        textos.forEach((t) => (t.style.opacity = String(Math.min(Number(t.style.opacity || 1), 1 - limitar(pv * 3)))));
      }

      if (v >= T.fin) avisos.current.onFin();
      else id = requestAnimationFrame(cuadro);
    };
    id = requestAnimationFrame(cuadro);
    return () => cancelAnimationFrame(id);
  }, []);

  return (
    <div className="intro" ref={raiz} role="status" aria-label="Cargando Madrid 179" onClick={() => (prisa.current = 3)}>
      <div className="intro-fondo" />
      <div className="intro-lienzo">
        <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} aria-hidden>
          <defs>
            <clipPath id="intro-corte"><rect className="intro-telon" width="0" height={ALTO} /></clipPath>
            <linearGradient id="intro-luz">
              <stop offset="0" stopColor="#fff" stopOpacity="0" />
              <stop offset="1" stopColor="#fff" stopOpacity="1" />
            </linearGradient>
          </defs>
          <rect className="intro-marco" x="0.5" y="0.5" width={ANCHO - 1} height={ALTO - 1} rx="12" />
          <g clipPath="url(#intro-corte)">
            <rect className="intro-bandera" width={ANCHO} height={ALTO} rx="12" />
            <rect className="intro-brillo" y="0" width="16" height={ALTO} fill="url(#intro-luz)" opacity="0" />
          </g>
          <path className="intro-trazo" d={TRAZO} pathLength={1} />
          <g className="intro-puntos">{DOTS.map((d, i) => <circle key={i} cx={d.x} cy={d.y} r="0" />)}</g>
          <g className="intro-rojas">{OSA.map((_, k) => <g key={k} transform="scale(0)"><polygon points={ESTRELLA} /></g>)}</g>
          <g className="intro-blancas" clipPath="url(#intro-corte)">
            {OSA.map((_, k) => <g key={k} transform="scale(0)"><polygon points={ESTRELLA} /></g>)}
          </g>
        </svg>
      </div>
      <h1 className="intro-titulo">Madrid <span>179</span></h1>
      <p className="intro-frase" aria-live="polite" />
      <svg className="intro-forma" aria-hidden>
        <path />
        <rect opacity="0" />
        <g className="intro-voladoras">{OSA.map((_, k) => <g key={k} transform="scale(0)"><polygon points={ESTRELLA} /></g>)}</g>
      </svg>
    </div>
  );
}

// Empareja la bandera en pantalla con el contorno proyectado: mismo sentido de giro y el desfase que menos retuerce
function prepararMorfo(origen: DOMRect, destino: DOMRect, mapa: MandoMapa, contorno: Geometria["contorno"]): Morfo {
  const rect = remuestrear(rectanguloRedondeado(origen.left, origen.top, origen.width, origen.height,
    (12 / ANCHO) * origen.width), MUESTRAS);
  let geo = anilloContorno(contorno);
  let pantalla = mapa.proyectar(geo);
  if (Math.sign(area(pantalla)) !== Math.sign(area(rect))) {
    geo = [...geo].reverse();
    pantalla = [...pantalla].reverse();
  }
  const a = normalizar(rect);
  const b = normalizar(pantalla);
  let mejor = 0;
  let menor = Infinity;
  for (let o = 0; o < MUESTRAS; o += 2) {
    let suma = 0;
    for (let i = 0; i < MUESTRAS; i += 4) {
      const [x, y] = b[(i + o) % MUESTRAS];
      suma += (a[i][0] - x) ** 2 + (a[i][1] - y) ** 2;
    }
    if (suma < menor) { menor = suma; mejor = o; }
  }
  return {
    rect,
    geo: geo.map((_, i) => geo[(i + mejor) % MUESTRAS]),
    // ESTRELLA mide en el lienzo de 150 de <Bandera>
    desde: SITIO.map(([x, y]) => ({ x: origen.left + (x / ANCHO) * origen.width, y: origen.top + (y / ALTO) * origen.height,
      s: origen.width / 150 })),
    hacia: POSICIONES.map(([x, y]) => ({ x: destino.left + (x / 150) * destino.width, y: destino.top + (y / 100) * destino.height,
      s: destino.width / 150 })),
    mini: destino,
  };
}
