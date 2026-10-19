// Mapa 3D: MapLibre dibuja la base (estilo propio sobre teselas abiertas) y deck.gl las columnas de los
// municipios. Altura y color = grupo del municipio; los cambios de grupo se animan para que se vea qué se mueve.
import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl, { type StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { AmbientLight, DirectionalLight, LightingEffect, WebMercatorViewport, type PickingInfo } from "@deck.gl/core";
import { GeoJsonLayer, PathLayer, SolidPolygonLayer, TextLayer } from "@deck.gl/layers";
import type { Feature, Geometry, Position } from "geojson";
import type { Geometria, PropsMunicipio } from "../api";
import { FUERA, type Rgb, type Situacion } from "../modelo";
import { esMovil, esTactil } from "../movil";
import { nombreLegible } from "./Ficha";

type Rasgo = Feature<Geometry, PropsMunicipio>;

export interface Camara {
  rumbo: number;
  inclinacion: number;
}

export interface MandoMapa {
  recentrar: () => void;
  alternarVista: () => void;
  norte: () => void;
  girar: (grados: number) => void;
  // Para la intro: lon/lat → píxeles en pantalla con la cámara actual (giro e inclinación incluidos)
  proyectar: (puntos: Position[]) => [number, number][];
  cargado: () => boolean;
  // Para el recorrido del Top: volar a un municipio (de cerca, inclinado) o volver a ver la región entera
  volarA: (centro: Position, o: { rumbo: number; duracion: number; derecha: number }) => void;
  verRegion: (duracion: number) => void;
  encuadrar: (puntos: Position[], o: { duracion: number; derecha: number }) => void; // derecha: hueco para la tarjeta
}

// px tapados por el panel, la ficha o (en móvil) la hoja inferior
export interface Margenes {
  izquierda: number;
  derecha: number;
  abajo?: number;
}

interface Props {
  geometria: Geometria;
  situaciones: Map<string, Situacion>;
  seleccionado: string | null;
  destacado: string | null; // parada actual del recorrido: contorno como el seleccionado, sin mover la cámara
  resaltados: Set<string> | null; // si hay, el resto se atenúa (perfiles, leyenda)
  etiquetas: string[];
  onSeleccionar: (ine5: string | null) => void;
  onPasar: (info: { ine5: string; x: number; y: number } | null) => void;
  onCamara: (c: Camara) => void;
  onMando: (m: MandoMapa) => void;
  margenes: Margenes;
  entrar: boolean; // el contorno de la intro ha aterrizado: inclinar y levantar columnas
}

const PAPEL: Rgb = [246, 242, 236];
const TINTA: Rgb = [38, 28, 32];
const ATENUADO: Rgb = [228, 231, 235]; // frío, para no confundirse con «Poco favorable»
const ESCALA_ALTURA = 1.15;
const ALTURA_APAGADO = 60; // columnas atenuadas (perfiles, leyenda, recorrido)
const DURACION_ALTURA = 950;
// Rótulos: en la vista general, solo los fijos (Madrid, los 5 primeros, el seleccionado); al acercarse, todos los
// municipios visibles. Si dos chocan, se queda el de más prioridad y el otro aparece al acercarse más o al pasar el ratón.
// Los choques se resuelven en la CPU al pararse el mapa (CollisionFilterExtension de deck.gl no funciona con MapLibre
// intercalado: esconde todos los rótulos)
const ZOOM_TODOS = 9.3;
const TAM_FIJO = 12.5;
const TAM_RESTO = 11;

interface Rotulo {
  ine5: string;
  texto: string;
  centro: Position;
  altura: number;
  prioridad: number;
}

/** Rótulos del resto que caben sin montarse entre sí ni sobre los fijos (voraz, por prioridad). */
function sinChoques(m: maplibregl.Map, fijos: Rotulo[], resto: Rotulo[], subida: number,
  margenes: Margenes): Set<string> {
  const c = m.getCenter();
  const pad = m.getPadding();
  const vista = new WebMercatorViewport({ width: m.getContainer().clientWidth, height: m.getContainer().clientHeight,
    longitude: c.lng, latitude: c.lat, zoom: m.getZoom(), pitch: m.getPitch(), bearing: m.getBearing(),
    padding: { left: pad.left, right: pad.right, top: pad.top, bottom: pad.bottom } });
  const cajas: [number, number, number, number][] = [];
  const caja = (r: Rotulo, tam: number) => {
    const [x, y] = vista.project([r.centro[0], r.centro[1], r.altura * subida * ESCALA_ALTURA + 250]);
    const ancho = r.texto.length * tam * 0.56 + 14; // ancho medio de la Hanken Grotesk + relleno del fondo
    return [x - ancho / 2, y - tam * 1.3 - 6, x + ancho / 2, y + 2] as [number, number, number, number];
  };
  const choca = (a: number[]) => cajas.some((b) => a[0] < b[2] + 4 && a[2] > b[0] - 4 && a[1] < b[3] + 2 && a[3] > b[1] - 2);
  for (const r of fijos) cajas.push(caja(r, TAM_FIJO));
  const salida = new Set<string>();
  const { width, height } = vista;
  for (const r of [...resto].sort((a, b) => b.prioridad - a.prioridad)) {
    const k = caja(r, TAM_RESTO);
    // fuera de pantalla o detrás del panel o de la ficha: no se ve, así que no ocupa sitio
    if (k[0] < margenes.izquierda - 16 || k[2] > width - margenes.derecha + 16 || k[1] < 0
      || k[3] > height - (margenes.abajo ?? 0) || choca(k)) continue;
    cajas.push(k);
    salida.add(r.ine5);
  }
  return salida;
} // ms de la transición de altura al cambiar de grupo o de foco
const VISTA_INICIAL = { center: [-3.72, 40.5] as [number, number], zoom: 8.25, pitch: 0, bearing: 0 };
const VISTA_3D = { zoom: 8.75, pitch: 50, bearing: -14 };
// Móvil: inclinación moderada (menos teselas y columnas en pantalla, más fluido) y la región entera en el hueco que
// deja la hoja inferior. El 3D sigue a mano: botón de vista y gesto de dos dedos
const INCLINACION_MOVIL = 35;
const REGION: [[number, number], [number, number]] = [[-4.6, 39.87], [-3.04, 41.17]];
const MARGEN_ARRIBA = 40;
const MARGEN_ABAJO = 120;
type Relleno = { left: number; right: number; top: number; bottom: number };

/** Zoom con el que la región cabe en el hueco libre (en móvil baja el de escritorio, pensado para pantallas anchas). */
function zoomRegion(ancho: number, alto: number, pad: Relleno) {
  const no = maplibregl.MercatorCoordinate.fromLngLat([REGION[0][0], REGION[1][1]]);
  const se = maplibregl.MercatorCoordinate.fromLngLat([REGION[1][0], REGION[0][1]]);
  const libreX = Math.max(ancho - pad.left - pad.right, 120);
  const libreY = Math.max(alto - pad.top - pad.bottom, 120);
  return Math.min(Math.log2(libreX / ((se.x - no.x) * 512)), Math.log2(libreY / ((se.y - no.y) * 512))) - 0.1;
}

/** Vista general inclinada: la de siempre en escritorio; en móvil, más plana y con la región entera. */
function vista3d(m: maplibregl.Map, pad: Relleno) {
  if (!esMovil()) return VISTA_3D;
  const c = m.getContainer();
  // +0,3: la inclinación encoge el eje vertical
  return { zoom: Math.max(7, Math.min(VISTA_3D.zoom, zoomRegion(c.clientWidth, c.clientHeight, pad) + 0.3)),
    pitch: INCLINACION_MOVIL, bearing: VISTA_3D.bearing };
}

// Resolución del lienzo: con pantallas de 3× el coste de pintar se dispara sin que se note la diferencia
const densidad = () => Math.min(typeof devicePixelRatio === "number" ? devicePixelRatio : 1, esMovil() ? 1.5 : 2);
const CAPITAL = "28079";
const FUENTE = "Hanken Grotesk Variable, Hanken Grotesk, sans-serif";

// Base: Positron de OpenFreeMap (sin clave) recoloreado en tonos papel; sin rótulos, que pone la app.
async function estiloBase(): Promise<StyleSpecification> {
  const vacio: StyleSpecification = {
    version: 8, sources: {},
    layers: [{ id: "fondo", type: "background", paint: { "background-color": "#f3eee7" } }],
  };
  try {
    const r = await fetch("https://tiles.openfreemap.org/styles/positron");
    if (!r.ok) return vacio;
    const s = (await r.json()) as StyleSpecification;
    const colores: Record<string, string> = {
      background: "#f3eee7", water: "#d7e0e2", park: "#e8e6d9", landcover_wood: "#e6e4d6",
      landuse_residential: "#ece5dc", building: "#e4dcd2",
    };
    s.layers = s.layers.filter((l) => l.type !== "symbol" && l.type !== "raster" && !l.id.startsWith("boundary"));
    for (const l of s.layers) {
      const c = colores[l.id];
      if (c && l.type === "background") l.paint = { ...l.paint, "background-color": c };
      else if (c && l.type === "fill") l.paint = { ...l.paint, "fill-color": c };
      else if (l.type === "line" && l.id.startsWith("highway")) l.paint = { ...l.paint, "line-color": "#e2d8cc" };
      else if (l.type === "line" && l.id.startsWith("railway")) l.paint = { ...l.paint, "line-color": "#b9aea3" };
    }
    s.sources = Object.fromEntries(Object.entries(s.sources).filter(([, v]) => v.type !== "raster"));
    return s;
  } catch {
    return vacio; // sin conexión: el mapa sigue funcionando con las formas de los municipios
  }
}

// El estilo se pide al arrancar la app, mientras corre la intro (solo red): así el mapa no lo espera al montarse
let estiloPedido: Promise<StyleSpecification> | null = null;
export const precargarEstilo = () => (estiloPedido ??= estiloBase());

function mascara(contorno: Geometria["contorno"]): Position[][] {
  const g = contorno.geometry;
  const huecos = g.type === "Polygon" ? [g.coordinates[0]] : g.coordinates.map((p) => p[0]);
  const marco: Position[] = [[-7.5, 38.2], [0, 38.2], [0, 42.8], [-7.5, 42.8], [-7.5, 38.2]];
  return [marco, ...huecos];
}

function lineasContorno(contorno: Geometria["contorno"]): Position[][] {
  const g = contorno.geometry;
  return g.type === "Polygon" ? [g.coordinates[0]] : g.coordinates.map((p) => p[0]);
}

const luces = new LightingEffect({
  ambiente: new AmbientLight({ color: [255, 250, 245], intensity: 1.05 }),
  sol: new DirectionalLight({ color: [255, 244, 232], intensity: 1.6, direction: [-3, -9, -4] }),
  contraluz: new DirectionalLight({ color: [210, 220, 255], intensity: 0.45, direction: [4, 6, -2] }),
});

const MATERIAL = { ambient: 0.62, diffuse: 0.55, shininess: 18, specularColor: [40, 30, 30] as Rgb };

export default function Mapa(p: Props) {
  const nodo = useRef<HTMLDivElement>(null);
  const mapa = useRef<maplibregl.Map | null>(null);
  const capa = useRef<MapboxOverlay | null>(null);
  const [listo, setListo] = useState(false);
  // Las capas de deck.gl se crean en cuanto carga el mapa (aunque no se vean hasta que aterrice la intro): crearlas
  // compila sus shaders, que en la primera visita bloquea el hilo principal más de un segundo. La intro no sale hasta que
  // el mapa ha pintado con ellas, así que ese tirón cae mientras la bandera está quieta y no a mitad del contorno
  const dibujado = useRef(false);
  const esperandoDibujo = useRef(false);
  const [subida, setSubida] = useState(0); // 0 → 1: las columnas crecen al entrar
  const [cerca, setCerca] = useState(false); // zoom ≥ ZOOM_TODOS: se rotulan todos los municipios visibles
  const [caben, setCaben] = useState<Set<string>>(new Set()); // rótulos del resto que no chocan
  const candidatos = useRef<{ fijos: Rotulo[]; resto: Rotulo[]; subida: number }>({ fijos: [], resto: [], subida: 0 });
  const recolocar = useRef(() => undefined as void);
  const [realce, setRealce] = useState(1); // 0 → 1: contorno y rótulo del destacado suben a la par que su columna
  const llamadas = useRef(p);
  llamadas.current = p;
  // Táctil (sin «pasar por encima»): el primer toque enseña la etiqueta y resalta el municipio; el segundo sobre el
  // mismo abre su ficha. Con ratón, pasar y pulsar como siempre. Solo refs y setters: vale desde cualquier cierre
  const tocado = useRef<string | null>(null);
  const [marcado, setMarcado] = useState<string | null>(null);
  const tocar = (ine5: string | null, x = 0, y = 0) => {
    const segundo = ine5 !== null && ine5 === tocado.current;
    tocado.current = segundo ? null : ine5;
    setMarcado(tocado.current);
    llamadas.current.onPasar(tocado.current && ine5 ? { ine5, x, y } : null);
    if (segundo) trasToque(() => llamadas.current.onSeleccionar(ine5));
  };

  // ------------------------------------------------------------ montaje
  useEffect(() => {
    let cancelado = false;
    precargarEstilo().then((pedido) => {
      const style = structuredClone(pedido); // copia: MapLibre no debe tocar la que se guarda
      if (cancelado || !nodo.current) return;
      const caja = nodo.current;
      const inicial = esMovil() ? { ...VISTA_INICIAL, zoom: Math.max(7, Math.min(VISTA_INICIAL.zoom,
        zoomRegion(caja.clientWidth, caja.clientHeight, { left: 0, right: 0, top: MARGEN_ARRIBA, bottom: MARGEN_ABAJO }))) }
        : VISTA_INICIAL;
      const m = new maplibregl.Map({
        container: caja, style, ...inicial, maxPitch: 72, minZoom: 7, maxZoom: 14,
        maxBounds: [[-6.2, 39.2], [-1.4, 41.9]], attributionControl: false, dragRotate: true,
        pitchWithRotate: true, fadeDuration: 0, pixelRatio: densidad(),
      });
      m.addControl(new maplibregl.AttributionControl({
        compact: true, customAttribution: "Límites: INE / Comunidad de Madrid",
      }), "bottom-right");
      // MapLibre abre el crédito compacto al cargar; en móvil taparía los controles: se queda en el botón «i»
      if (esMovil()) m.once("load", () => {
        const c = caja.querySelector(".maplibregl-ctrl-attrib");
        c?.classList.remove("maplibregl-compact-show");
        c?.removeAttribute("open");
      });
      // en táctil, un toque fuera de los municipios quita la etiqueta
      const o = new MapboxOverlay({ interleaved: true, effects: [luces], layers: [], useDevicePixels: densidad(),
        onClick: (i: PickingInfo) => { if (esTactil() && !i.object) tocar(null); } });
      m.addControl(o);
      mapa.current = m;
      capa.current = o;

      const avisar = () => llamadas.current.onCamara({ rumbo: m.getBearing(), inclinacion: m.getPitch() });
      m.on("rotate", avisar);
      m.on("pitch", avisar);
      m.on("zoom", () => setCerca(m.getZoom() >= ZOOM_TODOS));
      recolocar.current = () => {
        const { fijos, resto, subida: s } = candidatos.current;
        const nuevo = resto.length ? sinChoques(m, fijos, resto, s, llamadas.current.margenes) : new Set<string>();
        setCaben((antes) => (antes.size === nuevo.size && [...nuevo].every((i) => antes.has(i)) ? antes : nuevo));
      };
      m.on("moveend", () => recolocar.current());
      // la etiqueta del toque se queda quieta en la pantalla: si el mapa se mueve, deja de señalar su municipio
      m.on("movestart", () => { if (tocado.current) tocar(null); });
      let cargado = false;
      m.on("load", () => { cargado = true; setListo(true); });

      const padding = () => relleno(llamadas.current.margenes, MARGEN_ARRIBA, MARGEN_ABAJO, m);
      llamadas.current.onMando({
        recentrar: () => m.flyTo({ center: VISTA_INICIAL.center, ...vista3d(m, padding()), padding: padding(), duration: 1400 }),
        alternarVista: () => m.easeTo(m.getPitch() > 10
          ? { pitch: 0, bearing: 0, duration: 900 }
          : { pitch: vista3d(m, padding()).pitch, bearing: VISTA_3D.bearing, duration: 900 }),
        norte: () => m.easeTo({ bearing: 0, duration: 700 }),
        girar: (g) => m.easeTo({ bearing: m.getBearing() + g, duration: 700 }),
        proyectar: (puntos) => {
          const caja = m.getContainer().getBoundingClientRect();
          return puntos.map(([x, y]) => {
            const q = m.project([x, y]);
            return [caja.left + q.x, caja.top + q.y];
          });
        },
        cargado: () => cargado && dibujado.current,
        volarA: (centro, o) => m.flyTo({ center: centro as [number, number], zoom: 9.55,
          pitch: esMovil() ? INCLINACION_MOVIL : 52, bearing: o.rumbo,
          padding: { ...padding(), right: o.derecha }, duration: o.duracion, curve: 1.3, essential: true }),
        // fitBounds suma el margen que dejó el último vuelo; aquí el zoom se calcula a mano para el hueco que queda
        encuadrar: (puntos, o) => {
          const caja = puntos.reduce((b, q) => b.extend(q as [number, number]), new maplibregl.LngLatBounds());
          const no = maplibregl.MercatorCoordinate.fromLngLat(caja.getNorthWest());
          const se = maplibregl.MercatorCoordinate.fromLngLat(caja.getSouthEast());
          // en móvil la tarjeta del recorrido va abajo: manda el margen de la hoja, no los 110 px fijos
          const p = padding();
          const margen = { ...p, top: esMovil() ? p.top : 110, bottom: Math.max(110, p.bottom), right: o.derecha };
          const ancho = Math.max(40, m.getContainer().clientWidth - margen.left - margen.right);
          const alto = Math.max(40, m.getContainer().clientHeight - margen.top - margen.bottom);
          // 512 px = el mundo a zoom 0; la inclinación alarga el eje vertical (≈ ×1,6 a 50°)
          const zoom = Math.min(Math.log2(ancho / (Math.max(se.x - no.x, 1e-6) * 512)),
            Math.log2(alto / (Math.max(se.y - no.y, 1e-6) * 512 * 1.6))) - 0.85; // margen: columnas, rótulos y giro
          m.flyTo({ center: caja.getCenter(), zoom: Math.min(9.4, Math.max(7.6, zoom)), pitch: vista3d(m, margen).pitch,
            bearing: VISTA_3D.bearing, padding: margen, duration: o.duracion, essential: true });
        },
        verRegion: (duracion) => m.flyTo({ center: VISTA_INICIAL.center, ...vista3d(m, padding()), padding: padding(), duration: duracion,
          essential: true }),
      });
    });
    return () => {
      cancelado = true;
      mapa.current?.remove();
      mapa.current = null;
    };
  }, []);

  // ------------------------------------- entrada: inclinar y levantar columnas
  useEffect(() => {
    if (!listo || !p.entrar || !mapa.current) return;
    const m = mapa.current;
    // con un enlace directo a una ficha, la cámara va al municipio (efecto de selección) en vez de a la región
    // sin espera: la intro avisa justo cuando su contorno coincide con el del mapa y el carmesí se funde en las columnas
    if (!llamadas.current.seleccionado) {
      const padding = relleno({ ...llamadas.current.margenes, derecha: 0 }, MARGEN_ARRIBA, MARGEN_ABAJO, m);
      m.easeTo({ ...vista3d(m, padding), center: VISTA_INICIAL.center, duration: 2600, padding,
        easing: (t) => 1 - Math.pow(1 - t, 3) });
    }
    const t0 = performance.now();
    let id = 0;
    const paso = (t: number) => {
      const x = Math.min(1, Math.max(0, (t - t0) / 2200));
      setSubida(1 - Math.pow(1 - x, 3));
      if (x < 1) id = requestAnimationFrame(paso);
    };
    id = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listo, p.entrar]);

  // ---------------- destacado del recorrido: misma curva y duración que la transición de altura de las columnas
  useEffect(() => {
    if (!p.destacado) return;
    const t0 = performance.now();
    let id = 0;
    const paso = (t: number) => {
      const x = Math.min(1, (t - t0) / DURACION_ALTURA);
      setRealce(suave(x));
      if (x < 1) id = requestAnimationFrame(paso);
    };
    setRealce(0);
    id = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(id);
  }, [p.destacado]);

  // -------------------------------------------- cámara al seleccionar
  useEffect(() => {
    const m = mapa.current;
    if (tocado.current) tocar(null); // elegido desde el panel: fuera la etiqueta del toque
    if (!m || !p.seleccionado) return;
    const f = p.geometria.features.find((x) => x.properties.ine5 === p.seleccionado);
    if (!f) return;
    m.flyTo({ center: f.properties.centro, zoom: Math.max(m.getZoom(), 9.15),
      pitch: Math.max(m.getPitch(), esMovil() ? 30 : 45),
      bearing: listo && m.getPitch() > 10 ? m.getBearing() : VISTA_3D.bearing,
      padding: relleno(p.margenes, 60, MARGEN_ABAJO, m), duration: 1500, essential: true });
    // en móvil la hoja de la ficha cambia el margen de abajo después de elegir: se recentra en la franja que queda
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.seleccionado, listo, p.margenes.abajo]);

  // Al plegar o desplegar el panel, lo que estaba en el centro de lo visible sigue en el centro
  const izquierdaPrevia = useRef(p.margenes.izquierda);
  useEffect(() => {
    const m = mapa.current;
    if (!m || izquierdaPrevia.current === p.margenes.izquierda) return;
    izquierdaPrevia.current = p.margenes.izquierda;
    m.easeTo({ padding: relleno(p.margenes, MARGEN_ARRIBA, MARGEN_ABAJO, m), duration: 600 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.margenes.izquierda]);

  // ---------------------------------------------------------------- capas
  const centros = useMemo(() => new Map(p.geometria.features.map((f) => [f.properties.ine5, f.properties.centro])),
    [p.geometria]);
  const anillos = useMemo(() => mascara(p.geometria.contorno), [p.geometria]);
  const bordes = useMemo(() => lineasContorno(p.geometria.contorno), [p.geometria]);
  const indices = useMemo(() => new Map(p.geometria.features.map((f, k) => [f.properties.ine5, k])), [p.geometria]);

  useEffect(() => {
    if (!capa.current || !listo) return;
    const { situaciones, resaltados, seleccionado, destacado } = p;
    const opacidad = p.entrar ? 1 : 0; // hasta que aterriza la intro, el mapa base solo (como antes de crear las capas)
    const clave = [situaciones.size, [...situaciones.values()].map((s) => s.clase.id).join(""),
      resaltados ? [...resaltados].join(",") : "-", seleccionado, destacado].join("|");
    const situ = (f: Rasgo) => situaciones.get(f.properties.ine5);
    const apagado = (f: Rasgo) => resaltados !== null && !resaltados.has(f.properties.ine5);
    const altura = (f: Rasgo) => (apagado(f) ? ALTURA_APAGADO : (situ(f)?.clase.altura ?? FUERA.altura));
    // el destacado viene de estar apagado: su contorno y su rótulo acompañan a la columna mientras crece
    const alturaVisible = (f: Rasgo) => f.properties.ine5 === destacado && f.properties.ine5 !== seleccionado
      ? ALTURA_APAGADO + (altura(f) - ALTURA_APAGADO) * realce : altura(f);

    // Contorno del municipio elegido en la cara superior y en el suelo: se distingue sin tapar su color
    const seleccion: Position[][] = [];
    for (const elegido of p.geometria.features.filter((f) => f.properties.ine5 === seleccionado || f.properties.ine5 === destacado)) {
      const g = elegido.geometry;
      const exteriores = g.type === "Polygon" ? [g.coordinates[0]] : g.type === "MultiPolygon" ? g.coordinates.map((x) => x[0]) : [];
      const z = alturaVisible(elegido) * subida * ESCALA_ALTURA + 40;
      for (const anillo of exteriores) {
        seleccion.push(anillo.map(([x, y]) => [x, y, z]));
        seleccion.push(anillo.map(([x, y]) => [x, y, 15]));
      }
    }
    const rotulos: Rotulo[] = [CAPITAL, ...p.etiquetas.filter((i) => i !== CAPITAL)].filter((i) => centros.has(i)).map((i) => {
      const f = p.geometria.features.find((x) => x.properties.ine5 === i)!;
      return { ine5: i, texto: i === CAPITAL ? "Madrid · fuera del análisis" : nombreLegible(f.properties.municipio), centro: centros.get(i)!, altura: alturaVisible(f), prioridad: 1000 };
    });

    // Resto de municipios al acercarse (sin los atenuados, que no están en juego). Prioridad: mejor grupo y posición;
    // los fuera de la comparación, los últimos
    const fijos = new Set(rotulos.map((r) => r.ine5));
    const resto: Rotulo[] = !cerca || destacado ? [] : p.geometria.features
      .filter((f) => !fijos.has(f.properties.ine5) && !apagado(f))
      .map((f) => ({ ine5: f.properties.ine5, texto: nombreLegible(f.properties.municipio), centro: f.properties.centro,
        altura: alturaVisible(f), prioridad: 800 - (situ(f)?.posicion ?? 800) }));
    candidatos.current = { fijos: rotulos, resto, subida };
    const tactil = esTactil();

    capa.current.setProps({
      layers: [
        new SolidPolygonLayer({
          id: "mascara", data: [{ anillos }], getPolygon: ((d: { anillos: Position[][] }) => d.anillos) as never,
          getFillColor: [...PAPEL, 150], pickable: false, opacity: opacidad,
        }),
        new GeoJsonLayer<PropsMunicipio>({
          id: "municipios",
          data: p.geometria as never,
          extruded: true, wireframe: false, filled: true, stroked: false, pickable: true, opacity: opacidad,
          // en táctil el resaltado lo fija el toque (el automático se quedaría pegado donde se levantó el dedo)
          autoHighlight: !tactil, highlightColor: [255, 255, 255, 80],
          highlightedObjectIndex: tactil ? (marcado ? indices.get(marcado) ?? -1 : -1) : null,
          elevationScale: (subida * ESCALA_ALTURA) as never,
          getElevation: (f: Rasgo) => altura(f),
          getFillColor: (f: Rasgo) => (apagado(f) ? ATENUADO : (situ(f)?.clase.color ?? FUERA.color)),
          getLineColor: [255, 252, 248, 120],
          material: MATERIAL,
          transitions: { getElevation: { duration: DURACION_ALTURA, easing: suave }, getFillColor: { duration: 700, easing: suave } },
          updateTriggers: { getElevation: clave, getFillColor: clave },
          onClick: (i: PickingInfo<Rasgo>, e: object) => {
            if (!i.object) return false;
            if (!esTactil()) llamadas.current.onSeleccionar(i.object.properties.ine5);
            else if ((e as { tapCount?: number }).tapCount !== 2) tocar(i.object.properties.ine5, i.x, i.y); // el doble toque ya lo trataron los dos simples
            return true;
          },
          // en táctil no hay hover de verdad: los mousemove emulados tras un toque dejarían etiquetas pegadas
          onHover: (i: PickingInfo<Rasgo>) => !esTactil() && llamadas.current.onPasar(
            i.object ? { ine5: i.object.properties.ine5, x: i.x, y: i.y } : null),
        }),
        new PathLayer({
          id: "seleccion", data: seleccion, getPath: (d: Position[]) => d as never,
          getColor: [...TINTA, 255], getWidth: 2.5, widthUnits: "pixels", pickable: false, jointRounded: true, opacity: opacidad,
        }),
        new PathLayer({
          id: "contorno", data: bordes, getPath: (d: Position[]) => d as never,
          getColor: [...TINTA, 170], getWidth: 1.6, widthUnits: "pixels", pickable: false, opacity: opacidad,
        }),
        new TextLayer({
          id: "rotulos", data: rotulos,
          getPosition: (d: (typeof rotulos)[number]) => [d.centro[0], d.centro[1], d.altura * subida * ESCALA_ALTURA + 250],
          getText: (d: (typeof rotulos)[number]) => d.texto,
          getSize: (d: (typeof rotulos)[number]) => (d.ine5 === seleccionado || d.ine5 === destacado ? 15 : d.ine5 === CAPITAL ? 11.5 : TAM_FIJO),
          getColor: [...TINTA, 255], fontFamily: FUENTE, fontWeight: 600, characterSet: "auto",
          background: true, getBackgroundColor: [255, 253, 250, 235], backgroundPadding: [6, 3, 6, 3],
          getTextAnchor: "middle", getAlignmentBaseline: "bottom", billboard: true, sizeUnits: "pixels",
          opacity: subida, updateTriggers: { getPosition: [clave, subida, realce], getSize: [seleccionado, destacado] },
          parameters: { depthCompare: "always" } as never,
        }),
        new TextLayer({
          id: "rotulos-resto", data: resto.filter((r) => caben.has(r.ine5)),
          getPosition: (d: Rotulo) => [d.centro[0], d.centro[1], d.altura * subida * ESCALA_ALTURA + 250],
          getText: (d: Rotulo) => d.texto,
          getSize: TAM_RESTO, getColor: [...TINTA, 215], fontFamily: FUENTE, fontWeight: 500, characterSet: "auto", opacity: opacidad,
          background: true, getBackgroundColor: [255, 253, 250, 205], backgroundPadding: [5, 2, 5, 2],
          getTextAnchor: "middle", getAlignmentBaseline: "bottom", billboard: true, sizeUnits: "pixels",
          updateTriggers: { getPosition: [clave, subida, realce] },
          parameters: { depthCompare: "always" } as never,
        }),
      ],
    });
    // primera vez: setProps acaba de crear las capas (y compilar sus shaders); el mapa cuenta como listo para la intro
    // cuando ha pintado un par de cuadros con ellas
    const m = mapa.current;
    if (m && !dibujado.current && !esperandoDibujo.current) {
      esperandoDibujo.current = true;
      let cuadros = 0;
      const contar = () => {
        if (++cuadros < 2) return m.triggerRepaint();
        m.off("render", contar);
        dibujado.current = true;
      };
      m.on("render", contar);
      m.triggerRepaint();
    }
    // sin «p» entero en las dependencias: cada movimiento del ratón vuelve a pintar App y rehacía todas las capas
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listo, p.entrar, p.situaciones, p.resaltados, p.seleccionado, p.destacado, p.etiquetas, p.geometria, subida, realce,
    cerca, caben, anillos, bordes, centros, indices, marcado]);

  // Al cambiar qué se rotula (grupos, foco, zoom), se recalculan los choques; al mover el mapa, en «moveend»
  useEffect(() => recolocar.current(), [cerca, p.situaciones, p.resaltados, p.etiquetas, p.destacado, p.seleccionado,
    p.margenes.izquierda, p.margenes.derecha, p.margenes.abajo]);

  // el mouseleave emulado tras un toque borraría la etiqueta recién puesta
  return <div ref={nodo} className="mapa" onMouseLeave={() => !esTactil() && p.onPasar(null)} />;
}

/** Tras un toque el navegador emite ratón de compatibilidad (mousedown… click) y el mousedown hace que MapLibre pare
 * cualquier vuelo de cámara: lo que mueve la cámara espera a que acabe esa ráfaga (o 350 ms si no llega). */
function trasToque(f: () => void) {
  let hecho = false;
  const una = () => {
    if (hecho) return;
    hecho = true;
    removeEventListener("click", una, true);
    clearTimeout(t);
    setTimeout(f, 0);
  };
  addEventListener("click", una, true);
  const t = setTimeout(una, 350);
}

/** Padding de cámara: lo que tapan panel, ficha y hoja inferior (en móvil, la hoja sustituye al margen de abajo).
 * Con una hoja muy alta se deja siempre una franja de mapa de 140 px. */
function relleno(mg: Margenes, arriba: number, abajo: number, m: maplibregl.Map): Relleno {
  const libre = m.getContainer().clientHeight - arriba - 140;
  return { left: mg.izquierda, right: mg.derecha, top: arriba,
    bottom: mg.abajo ? Math.max(0, Math.min(mg.abajo + 24, libre)) : abajo };
}

function suave(t: number) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
