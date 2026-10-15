// Traducción del modelo a lenguaje claro: clases en lugar de cifras, frases en lugar de coeficientes.
// Las puntuaciones del modelo son orientativas, así que la interfaz enseña grupos y razones, no decimales.
import type { Aportacion, Filtros, Municipio, Ranking } from "./api";

export type Rgb = [number, number, number];

export interface Clase {
  id: string;
  nombre: string;
  resumen: string;
  color: Rgb;
  altura: number; // metros de extrusión en el mapa 3D
  orden: number;
}

// Cinco grupos por posición entre los candidatos (quintiles), del rojo intenso de la bandera al rosa pálido.
export const CLASES: Clase[] = [
  { id: "c0", orden: 0, nombre: "Muy favorable", color: [138, 10, 31], altura: 7200,
    resumen: "Está en el grupo de municipios con mejores condiciones para abrir una oficina." },
  { id: "c1", orden: 1, nombre: "Favorable", color: [200, 16, 46], altura: 5400,
    resumen: "Reúne buenas condiciones: por encima de la mayoría de municipios de la región." },
  { id: "c2", orden: 2, nombre: "Intermedio", color: [226, 98, 108], altura: 3700,
    resumen: "Condiciones en la media de la región: con puntos a favor y en contra equilibrados." },
  { id: "c3", orden: 3, nombre: "Menos favorable", color: [238, 163, 158], altura: 2200,
    resumen: "Algunos factores clave le restan atractivo frente a otros municipios." },
  { id: "c4", orden: 4, nombre: "Poco favorable", color: [245, 210, 202], altura: 1100,
    resumen: "Hoy reúne menos condiciones que el resto para una oficina; puede cambiar con tus preferencias." },
];

export const FILTRADO: Clase = {
  id: "filtrado", orden: 5, nombre: "No cumple tus requisitos", color: [204, 197, 188], altura: 260,
  resumen: "Lo descartan los requisitos imprescindibles que has marcado.",
};
export const FUERA: Clase = {
  id: "fuera", orden: 6, nombre: "Fuera del análisis", color: [226, 220, 212], altura: 90,
  resumen: "No entra en la comparación por decisión de diseño.",
};

export const MOTIVOS: Record<string, string> = {
  excluir_madrid_capital:
    "La capital queda fuera a propósito: el objetivo es llevar actividad y empleo al resto de la región.",
  min_uu_oficinas:
    "No tiene ningún local de oficinas registrado en el Catastro: hoy no hay espacio donde instalarse.",
};

export interface Situacion {
  clase: Clase;
  posicion: number | null; // solo para ordenar; no se muestra
  desglose: Record<string, number> | null;
}

/** Clase de cada municipio según el ranking actual (con preferencias y filtros del usuario). */
export function clasificar(ranking: Ranking, municipios: Municipio[]): Map<string, Situacion> {
  const filas = new Map(ranking.resultados.map((f) => [f.ine5, f]));
  const n = ranking.candidatos;
  const salida = new Map<string, Situacion>();
  for (const m of municipios) {
    const f = filas.get(m.ine5);
    if (!m.candidato) salida.set(m.ine5, { clase: FUERA, posicion: null, desglose: null });
    else if (!f) salida.set(m.ine5, { clase: FILTRADO, posicion: null, desglose: null });
    else {
      const i = Math.min(4, Math.floor(((f.posicion - 1) * 5) / Math.max(n, 1)));
      salida.set(m.ine5, { clase: CLASES[i], posicion: f.posicion, desglose: f.desglose });
    }
  }
  return salida;
}

// ------------------------------------------------------------ factores
export interface InfoNodo {
  nombre: string;
  que: string; // qué mide, en una frase
  estados: Record<string, string>; // estado del modelo -> palabra para el usuario
}

// Nodos de la red (backend/madrid179/config.py) en lenguaje claro.
export const NODOS: Record<string, InfoNodo> = {
  Distancia_Madrid: { nombre: "Distancia a Madrid", que: "Kilómetros en línea recta hasta la Puerta del Sol (centro del municipio).",
    estados: { Cerca: "cerca", Media: "media", Lejos: "lejos" } },
  Talento: { nombre: "Talento", que: "Población con estudios superiores.",
    estados: { Bajo: "bajo", Medio: "medio", Alto: "alto" } },
  Acceso_Ferroviario: { nombre: "Tren", que: "Si el municipio tiene estación de Cercanías, Metro o Metro Ligero.",
    estados: { No: "sin estación", Si: "con estación" } },
  Coste_Inmobiliario: { nombre: "Valor inmobiliario", que: "Valor catastral medio de la vivienda.",
    estados: { Bajo: "bajo", Medio: "medio", Alto: "alto" } },
  Renta: { nombre: "Renta", que: "Renta disponible por habitante.",
    estados: { Baja: "baja", Media: "media", Alta: "alta" } },
  Especializacion_Servicios: { nombre: "Servicios profesionales", que: "Peso de las empresas de servicios profesionales.",
    estados: { Baja: "baja", Media: "media", Alta: "alta" } },
  Dinamismo_Demografico: { nombre: "Crecimiento de la población", que: "Cuánto ha crecido el padrón en cinco años.",
    estados: { Bajo: "bajo", Medio: "medio", Alto: "alto" } },
  Densidad: { nombre: "Densidad", que: "Habitantes por kilómetro cuadrado.",
    estados: { Baja: "baja", Media: "media", Alta: "alta" } },
  Juventud: { nombre: "Población joven", que: "Proporción de vecinos menores de 45 años.",
    estados: { Baja: "baja", Media: "media", Alta: "alta" } },
  Sanidad: { nombre: "Oferta sanitaria", que: "Hospitales, clínicas, consultas y farmacias por habitante.",
    estados: { Baja: "baja", Media: "media", Alta: "alta" } },
  Paro: { nombre: "Paro", que: "Paro registrado sobre la población.",
    estados: { Bajo: "bajo", Medio: "medio", Alto: "alto" } },
  Viabilidad_Empresarial: { nombre: "Viabilidad empresarial", que: "Saldo neto de empresas creadas entre 2020 y 2024.",
    estados: { Baja: "baja", Media: "media", Alta: "alta" } },
};

// Columna del GA²M -> nodo de la red (para describir el valor con su nivel)
const COLUMNA_NODO: Record<string, string> = {
  dist_sol_km: "Distancia_Madrid", pct_estudios_superiores: "Talento", paradas_ferro: "Acceso_Ferroviario",
  vc_residencial_por_uu: "Coste_Inmobiliario", rdb_per_capita: "Renta",
  pct_up_servicios_prof: "Especializacion_Servicios", crec_pob_5a: "Dinamismo_Demografico",
  densidad_hab_km2: "Densidad", pct_menores_45: "Juventud", sanidad_por_1000hab: "Sanidad",
  paro_por_100hab: "Paro",
};

const num = (x: number, d = 0) => x.toLocaleString("es-ES", { maximumFractionDigits: d });

// Variables del GA²M que no son nodo: se describen con su dato real (es un hecho, no una estimación)
const EXTRAS: Record<string, { nombre: string; valor: (x: number) => string }> = {
  uu_oficinas_por_1000hab: { nombre: "Parque de oficinas", valor: (x) => `${num(x, 1)} locales por 1.000 hab.` },
  dist_ferro_km: { nombre: "Estación más cercana", valor: (x) => `a ${num(x, 1)} km` },
  poblacion: { nombre: "Tamaño", valor: (x) => `${num(x)} habitantes` },
};

export function nombreColumna(c: string): string {
  return COLUMNA_NODO[c] ? NODOS[COLUMNA_NODO[c]].nombre : EXTRAS[c]?.nombre ?? c;
}

function valorColumna(c: string, estados: Record<string, string>, valores: Record<string, number>): string {
  const nodo = COLUMNA_NODO[c];
  if (nodo) return NODOS[nodo].estados[estados[nodo]] ?? estados[nodo];
  return EXTRAS[c] ? EXTRAS[c].valor(valores[c]) : num(valores[c], 2);
}

const minuscula = (t: string) => t.charAt(0).toLowerCase() + t.slice(1);

export type Fuerza = 3 | 2 | 1;

/** Magnitud de una aportación del GA²M (puntos porcentuales de tasa neta) en tres niveles.
 *  Umbrales sobre la distribución de |aportación| en los 179 municipios: p90 ≈ 0,13 · p75 ≈ 0,06 · p50 ≈ 0,02. */
export function fuerza(pp: number): Fuerza | null {
  const a = Math.abs(pp);
  return a >= 0.13 ? 3 : a >= 0.05 ? 2 : a >= 0.02 ? 1 : null;
}

export const PALABRA_FUERZA: Record<Fuerza, string> = { 3: "mucho", 2: "bastante", 1: "algo" };

export interface Factor {
  termino: string;
  titulo: string;
  detalle: string;
  signo: 1 | -1;
  fuerza: Fuerza;
  combinado: boolean;
  columnas: string[];
}

export function factores(aportaciones: Aportacion[], estados: Record<string, string>): Factor[] {
  const salida: Factor[] = [];
  for (const a of aportaciones) {
    const f = fuerza(a.aportacion_pp);
    if (!f) continue;
    const cols = a.termino.split("&").map((c) => c.trim());
    const combinado = cols.length > 1;
    salida.push({
      termino: a.termino,
      titulo: combinado ? cols.map((c, k) => (k ? minuscula(nombreColumna(c)) : nombreColumna(c))).join(" y ") : nombreColumna(cols[0]),
      detalle: cols.map((c) => valorColumna(c, estados, a.valores)).join(" · "),
      signo: a.aportacion_pp >= 0 ? 1 : -1,
      fuerza: f,
      combinado,
      columnas: cols,
    });
  }
  return salida;
}

/** Frase-resumen con los factores que más pesan a favor y en contra. */
export function resumenFactores(fs: Factor[]): string {
  const minus = (t: string) => t.charAt(0).toLowerCase() + t.slice(1);
  const lista = (xs: Factor[]) => {
    const t = xs.map((x) => minus(x.titulo));
    return t.length > 1 ? `${t.slice(0, -1).join(", ")} y ${t[t.length - 1]}` : t[0];
  };
  const pos = fs.filter((f) => f.signo > 0 && !f.combinado).slice(0, 2);
  const neg = fs.filter((f) => f.signo < 0 && !f.combinado).slice(0, 2);
  if (pos.length && neg.length) return `Le favorecen sobre todo ${lista(pos)}; le resta ${lista(neg)}.`;
  if (pos.length) return `Le favorecen sobre todo ${lista(pos)}, sin factores importantes en contra.`;
  if (neg.length) return `Le pesa sobre todo ${lista(neg)}.`;
  return "Ningún factor destaca: sus condiciones están cerca de la media regional.";
}

// ---------------------------------------------------------- preferencias
export const OPCIONES_IMPORTANCIA = [
  { valor: "Me da igual", etiqueta: "Me da igual" },
  { valor: "Poco importante", etiqueta: "Algo" },
  { valor: "Muy importante", etiqueta: "Mucho" },
] as const;

/** Utilidad de una preferencia (0-1) en palabras. */
export function palabraUtilidad(u: number): string {
  return u >= 0.66 ? "mucho" : u >= 0.33 ? "algo" : u > 0 ? "poco" : "nada";
}

export function nivel(estados: string[], estado: string): number {
  return Math.max(0, estados.indexOf(estado));
}

export function palabraImportancia(i: string): string {
  return i === "Muy importante" ? "Mucho" : i === "Poco importante" ? "Algo" : "Me da igual";
}

export const FILTROS_VACIOS: Filtros = {
  estacion_max_km: null, madrid_max_km: null, madrid_min_km: null, poblacion_min: null, poblacion_max: null,
  solo_con_ayudas: false, con_coworking: false,
};

const miles = (x: number) => x.toLocaleString("es-ES");

/** Requisito «imprescindible» en una frase. */
export function describirFiltro(k: keyof Filtros, v: number | boolean | null): string {
  switch (k) {
    case "estacion_max_km": return `Estación de tren a menos de ${v} km`;
    case "madrid_max_km": return `A menos de ${v} km de Madrid`;
    case "madrid_min_km": return `A más de ${v} km de Madrid`;
    case "poblacion_min": return `Más de ${miles(Number(v))} habitantes`;
    case "poblacion_max": return `Menos de ${miles(Number(v))} habitantes`;
    case "solo_con_ayudas": return "Solo municipios con ayudas por tamaño";
    case "con_coworking": return "Solo municipios con coworking";
  }
}

export function filtrosActivos(f: Filtros): [keyof Filtros, number | boolean][] {
  return (Object.entries(f) as [keyof Filtros, number | boolean | null][])
    .filter((e): e is [keyof Filtros, number | boolean] => e[1] !== null && e[1] !== false);
}
