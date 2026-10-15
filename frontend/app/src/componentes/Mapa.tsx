// Mapa 3D: MapLibre dibuja la base (estilo propio sobre teselas abiertas) y deck.gl las columnas de los
// municipios. Altura y color = grupo del municipio; los cambios de grupo se animan para que se vea qué se mueve.
import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl, { type StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { AmbientLight, DirectionalLight, LightingEffect, type PickingInfo } from "@deck.gl/core";
import { GeoJsonLayer, PathLayer, SolidPolygonLayer, TextLayer } from "@deck.gl/layers";
import type { Feature, Geometry, Position } from "geojson";
import type { Geometria, PropsMunicipio } from "../api";
import { FUERA, type Rgb, type Situacion } from "../modelo";
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
}

interface Props {
  geometria: Geometria;
  situaciones: Map<string, Situacion>;
  seleccionado: string | null;
  resaltados: Set<string> | null; // si hay, el resto se atenúa (perfiles, leyenda)
  etiquetas: string[];
  onSeleccionar: (ine5: string | null) => void;
  onPasar: (info: { ine5: string; x: number; y: number } | null) => void;
  onCamara: (c: Camara) => void;
  onMando: (m: MandoMapa) => void;
  margenes: { izquierda: number; derecha: number };
  entrar: boolean; // la intro ha terminado: inclinar y levantar columnas
}

const PAPEL: Rgb = [246, 242, 236];
const TINTA: Rgb = [38, 28, 32];
const ATENUADO: Rgb = [228, 231, 235]; // frío, para no confundirse con «Poco favorable»
const ESCALA_ALTURA = 1.15;
const VISTA_INICIAL = { center: [-3.72, 40.5] as [number, number], zoom: 8.25, pitch: 0, bearing: 0 };
const VISTA_3D = { zoom: 8.75, pitch: 50, bearing: -14 };
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
  const [subida, setSubida] = useState(0); // 0 → 1: las columnas crecen al entrar
  const llamadas = useRef(p);
  llamadas.current = p;

  // ------------------------------------------------------------ montaje
  useEffect(() => {
    let cancelado = false;
    estiloBase().then((style) => {
      if (cancelado || !nodo.current) return;
      const m = new maplibregl.Map({
        container: nodo.current, style, ...VISTA_INICIAL, maxPitch: 72, minZoom: 7, maxZoom: 14,
        maxBounds: [[-6.2, 39.2], [-1.4, 41.9]], attributionControl: false, dragRotate: true,
        pitchWithRotate: true, fadeDuration: 0,
      });
      m.addControl(new maplibregl.AttributionControl({
        compact: true, customAttribution: "Límites: INE / Comunidad de Madrid",
      }), "bottom-right");
      const o = new MapboxOverlay({ interleaved: true, effects: [luces], layers: [] });
      m.addControl(o);
      mapa.current = m;
      capa.current = o;

      const avisar = () => llamadas.current.onCamara({ rumbo: m.getBearing(), inclinacion: m.getPitch() });
      m.on("rotate", avisar);
      m.on("pitch", avisar);
      let cargado = false;
      m.on("load", () => { cargado = true; setListo(true); });

      const padding = () => ({ left: llamadas.current.margenes.izquierda, right: llamadas.current.margenes.derecha,
        top: 40, bottom: 120 });
      llamadas.current.onMando({
        recentrar: () => m.flyTo({ center: VISTA_INICIAL.center, ...VISTA_3D, padding: padding(), duration: 1400 }),
        alternarVista: () => m.easeTo(m.getPitch() > 10
          ? { pitch: 0, bearing: 0, duration: 900 } : { pitch: VISTA_3D.pitch, bearing: VISTA_3D.bearing, duration: 900 }),
        norte: () => m.easeTo({ bearing: 0, duration: 700 }),
        girar: (g) => m.easeTo({ bearing: m.getBearing() + g, duration: 700 }),
        proyectar: (puntos) => {
          const caja = m.getContainer().getBoundingClientRect();
          return puntos.map(([x, y]) => {
            const q = m.project([x, y]);
            return [caja.left + q.x, caja.top + q.y];
          });
        },
        cargado: () => cargado,
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
    const espera = setTimeout(() => !llamadas.current.seleccionado && m.easeTo({ ...VISTA_3D, center: VISTA_INICIAL.center, duration: 2600,
      padding: { left: p.margenes.izquierda, right: 0, top: 40, bottom: 120 },
      easing: (t) => 1 - Math.pow(1 - t, 3) }), 350);
    const t0 = performance.now() + 350;
    let id = 0;
    const paso = (t: number) => {
      const x = Math.min(1, Math.max(0, (t - t0) / 2200));
      setSubida(1 - Math.pow(1 - x, 3));
      if (x < 1) id = requestAnimationFrame(paso);
    };
    id = requestAnimationFrame(paso);
    return () => { cancelAnimationFrame(id); clearTimeout(espera); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listo, p.entrar]);

  // -------------------------------------------- cámara al seleccionar
  useEffect(() => {
    const m = mapa.current;
    if (!m || !p.seleccionado) return;
    const f = p.geometria.features.find((x) => x.properties.ine5 === p.seleccionado);
    if (!f) return;
    m.flyTo({ center: f.properties.centro, zoom: Math.max(m.getZoom(), 9.15), pitch: Math.max(m.getPitch(), 45),
      bearing: listo && m.getPitch() > 10 ? m.getBearing() : VISTA_3D.bearing,
      padding: { left: p.margenes.izquierda, right: p.margenes.derecha, top: 60, bottom: 120 },
      duration: 1500, essential: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.seleccionado, listo]);

  // ---------------------------------------------------------------- capas
  const centros = useMemo(() => new Map(p.geometria.features.map((f) => [f.properties.ine5, f.properties.centro])),
    [p.geometria]);
  const anillos = useMemo(() => mascara(p.geometria.contorno), [p.geometria]);
  const bordes = useMemo(() => lineasContorno(p.geometria.contorno), [p.geometria]);

  useEffect(() => {
    if (!capa.current) return;
    const { situaciones, resaltados, seleccionado } = p;
    const clave = [situaciones.size, [...situaciones.values()].map((s) => s.clase.id).join(""),
      resaltados ? [...resaltados].join(",") : "-", seleccionado].join("|");
    const situ = (f: Rasgo) => situaciones.get(f.properties.ine5);
    const apagado = (f: Rasgo) => resaltados !== null && !resaltados.has(f.properties.ine5);
    const altura = (f: Rasgo) => (apagado(f) ? 60 : (situ(f)?.clase.altura ?? FUERA.altura));

    // Contorno del municipio elegido en la cara superior y en el suelo: se distingue sin tapar su color
    const elegido = p.geometria.features.find((f) => f.properties.ine5 === seleccionado);
    const seleccion: Position[][] = [];
    if (elegido) {
      const g = elegido.geometry;
      const exteriores = g.type === "Polygon" ? [g.coordinates[0]] : g.type === "MultiPolygon" ? g.coordinates.map((x) => x[0]) : [];
      const z = altura(elegido) * subida * ESCALA_ALTURA + 40;
      for (const anillo of exteriores) {
        seleccion.push(anillo.map(([x, y]) => [x, y, z]));
        seleccion.push(anillo.map(([x, y]) => [x, y, 15]));
      }
    }
    const rotulos = [CAPITAL, ...p.etiquetas.filter((i) => i !== CAPITAL)].filter((i) => centros.has(i)).map((i) => {
      const f = p.geometria.features.find((x) => x.properties.ine5 === i)!;
      return { ine5: i, texto: i === CAPITAL ? "Madrid · fuera del análisis" : nombreLegible(f.properties.municipio), centro: centros.get(i)!, altura: altura(f) };
    });

    capa.current.setProps({
      layers: [
        new SolidPolygonLayer({
          id: "mascara", data: [{ anillos }], getPolygon: ((d: { anillos: Position[][] }) => d.anillos) as never,
          getFillColor: [...PAPEL, 150], pickable: false,
        }),
        new GeoJsonLayer<PropsMunicipio>({
          id: "municipios",
          data: p.geometria as never,
          extruded: true, wireframe: false, filled: true, stroked: false, pickable: true,
          autoHighlight: true, highlightColor: [255, 255, 255, 80],
          elevationScale: (subida * ESCALA_ALTURA) as never,
          getElevation: (f: Rasgo) => altura(f),
          getFillColor: (f: Rasgo) => (apagado(f) ? ATENUADO : (situ(f)?.clase.color ?? FUERA.color)),
          getLineColor: [255, 252, 248, 120],
          material: MATERIAL,
          transitions: { getElevation: { duration: 950, easing: suave }, getFillColor: { duration: 700, easing: suave } },
          updateTriggers: { getElevation: clave, getFillColor: clave },
          onClick: (i: PickingInfo<Rasgo>) => i.object && llamadas.current.onSeleccionar(i.object.properties.ine5),
          onHover: (i: PickingInfo<Rasgo>) => llamadas.current.onPasar(
            i.object ? { ine5: i.object.properties.ine5, x: i.x, y: i.y } : null),
        }),
        new PathLayer({
          id: "seleccion", data: seleccion, getPath: (d: Position[]) => d as never,
          getColor: [...TINTA, 255], getWidth: 2.5, widthUnits: "pixels", pickable: false, jointRounded: true,
        }),
        new PathLayer({
          id: "contorno", data: bordes, getPath: (d: Position[]) => d as never,
          getColor: [...TINTA, 170], getWidth: 1.6, widthUnits: "pixels", pickable: false,
        }),
        new TextLayer({
          id: "rotulos", data: rotulos,
          getPosition: (d: (typeof rotulos)[number]) => [d.centro[0], d.centro[1], d.altura * subida * ESCALA_ALTURA + 250],
          getText: (d: (typeof rotulos)[number]) => d.texto,
          getSize: (d: (typeof rotulos)[number]) => (d.ine5 === seleccionado ? 15 : d.ine5 === CAPITAL ? 11.5 : 12.5),
          getColor: [...TINTA, 255], fontFamily: FUENTE, fontWeight: 600, characterSet: "auto",
          background: true, getBackgroundColor: [255, 253, 250, 235], backgroundPadding: [6, 3, 6, 3],
          getTextAnchor: "middle", getAlignmentBaseline: "bottom", billboard: true, sizeUnits: "pixels",
          opacity: subida, updateTriggers: { getPosition: [clave, subida], getSize: seleccionado },
          parameters: { depthCompare: "always" } as never,
        }),
      ],
    });
  }, [p.situaciones, p.resaltados, p.seleccionado, p.etiquetas, p.geometria, subida, anillos, bordes, centros, p]);

  return <div ref={nodo} className="mapa" onMouseLeave={() => p.onPasar(null)} />;
}

function suave(t: number) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}
