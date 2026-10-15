// Contrato con la API de Madrid 179 (backend/api/esquemas.py). La app solo habla con /api/v1.
import type { Feature, FeatureCollection, MultiPolygon, Polygon } from "geojson";

const API = "/api/v1";

export type Importancia = "Me da igual" | "No lo sé" | "Poco importante" | "Muy importante";

export interface Nodo {
  columna: string;
  estados: string[];
  cortes: number[];
}

export interface PreferenciaCatalogo {
  clave: string;
  nombre: string;
  grupo: string;
  descripcion: string;
  sentidos: { valor: string; etiqueta: string }[] | null;
  en_modelo: boolean;
}

export interface Meta {
  version_modelo: string;
  entrenado: string;
  aviso: string;
  objetivo: string;
  padres_objetivo: string[];
  nodos: Record<string, Nodo>;
  preferencias: string[];
  catalogo: PreferenciaCatalogo[];
  importancias: Importancia[];
  tope_preferencias: number;
  asistente_disponible: boolean;
  municipios: number;
  candidatos_por_defecto: number;
  validacion: {
    repeticiones: number;
    particiones: number;
    acierto: number[];
    log_loss: number[];
    acierto_azar: number;
    log_loss_uniforme: number;
  } | null;
}

export interface Municipio {
  ine5: string;
  municipio: string;
  poblacion: number;
  candidato: boolean;
  nivel_ayudas: string;
  dist_ferro_km: number;
  estados: Record<string, string>;
}

export interface FilaRanking {
  posicion: number;
  ine5: string;
  municipio: string;
  puntuacion: number;
  desglose: Record<string, number>;
  p_alta_red: number;
  nivel_ayudas: string;
  dist_ferro_km: number;
}

export interface Ranking {
  candidatos: number;
  pesos: Record<string, number>;
  resultados: FilaRanking[];
}

export interface PreferenciaUsuario {
  importancia: Importancia;
  sentido: string | null;
}

export interface Filtros {
  estacion_max_km: number | null;
  madrid_max_km: number | null;
  madrid_min_km: number | null;
  poblacion_min: number | null;
  poblacion_max: number | null;
  solo_con_ayudas: boolean;
  con_coworking: boolean;
}

export interface Peticion {
  preferencias: Record<string, PreferenciaUsuario>;
  filtros: Filtros;
}

export interface Interpretacion {
  resumen: string;
  sector: string | null;
  preferencias: Record<string, PreferenciaUsuario & { motivo: string }>;
  filtros: Partial<Filtros>;
  dudas: string[];
  avisos: string[];
}

export interface Aportacion {
  termino: string;
  etiqueta: string;
  aportacion_pp: number;
  valores: Record<string, number>;
  lectura: string | null;  // cómo leerla cuando el signo puede confundir
}

export interface Ficha {
  ine5: string;
  municipio: string;
  poblacion: number;
  candidato: boolean;
  motivo_exclusion: string[] | null;
  posicion: number | null;
  de: number;
  ga2m: { prediccion_pct: number; intercepto_pct: number; percentil: number | null; aportaciones: Aportacion[] };
  red: {
    estados: Record<string, string>;
    probabilidades: Record<string, number>;
    padres: Record<string, string>;
    percentil: number | null;
  };
  discrepancia: string | null;
  preferencias: Record<string, { dato: string; utilidad: Record<string, number> }>;
  wikipedia: Wikipedia | null;
  ayudas: AyudasFicha | null; // null si el servidor no tiene ayudas_oficiales.csv
}

/** Ayudas oficiales que alcanzan a una empresa o a su gente (sin el PIR, que financia obras municipales). */
export interface AyudasFicha {
  leader: { grupo: string; fuente: string; web: string } | null; // LEADER 2023-2027: web del grupo y convenio en el BOCM
  irpf_menos_2500: boolean; // deducciones del IRPF por trasladarse o comprar vivienda (Ley 5/2024)
  anio_padron: string;
}

export interface Wikipedia {
  titulo: string | null;
  resumen: string | null;
  url: string | null;
  imagen: { url: string; autor: string; licencia: string | null; url_licencia: string | null; fuente: string | null } | null;
}

export interface Explicacion {
  titular: string;
  mejor: string[];
  peor: string[];
  apoyos: { mejor: string[][]; peor: string[][] };  // hechos de la ficha en que se basa cada frase
  comprobacion: { corregida: boolean; descartadas: number };
}

/** Lo que el usuario contó de su negocio (de /interpretar): adapta «En pocas palabras». */
export interface Negocio {
  sector: string | null;
  resumen: string | null;
}

export interface Consulta {
  evidencia: Record<string, string>;
  probabilidades: Record<string, number>;
  a_priori: Record<string, number>;
  municipios: { ine5: string; municipio: string; candidato: boolean }[];
}

// Diagnóstico territorial («Dónde actuar», perfil Administración). Describe la situación; no simula políticas.
export type IdCuadrante = "oportunidad" | "apoyo" | "autonomo" | "vigilar";

export interface Freno {
  termino: string;
  etiqueta: string;
  aportacion_pp: number;
  tipo: "palanca" | "estructural";
  lectura: string | null;
}

export interface MunicipioDiagnostico {
  ine5: string;
  municipio: string;
  poblacion: number;
  distancia: "Cerca" | "Media" | "Lejos";
  candidato: boolean;
  necesidad: number;   // percentil 0-100 entre los 178 (sin Madrid capital)
  componentes: Record<string, { valor: number; percentil: number }>;
  viabilidad: number;  // percentil 0-100 del GA²M entre los mismos
  cuadrante: IdCuadrante;
  frenos: Freno[];
  freno_palanca: Freno | null;
  contexto: ContextoPolitica;
}

// Contexto para la política: datos de contexto, no resultado del modelo
export interface ContextoPolitica {
  oficinas: { locales: number; por_1000hab: number; coworking: number }; // Catastro; coworking según OpenStreetMap
  ayudas: {
    leader: { grupo: string; fuente: string } | null; // LEADER 2023-2027 (convenio en el BOCM)
    irpf_menos_2500: boolean;        // deducciones del IRPF por traslado o compra de vivienda (Ley 5/2024)
    pir_sin_cofinanciacion: boolean; // PIR 2022-2026
    anio_padron: string;
  } | null; // null si el servidor no tiene ayudas_oficiales.csv
}

export interface Diagnostico {
  corte: number;
  aviso: string;
  necesidad: { componentes: { columna: string; etiqueta: string; sentido: "bajo" | "alto" }[]; nota: string };
  cuadrantes: { id: IdCuadrante; nombre: string; lectura: string }[];
  municipios: MunicipioDiagnostico[];
  contexto_nota: string;
}

export interface PropsMunicipio {
  ine5: string;
  municipio: string;
  area_km2: number;
  centro: [number, number];
}

export type Geometria = FeatureCollection<Polygon | MultiPolygon, PropsMunicipio> & {
  contorno: Feature<Polygon | MultiPolygon>;
};

async function pedir<T>(ruta: string, cuerpo?: unknown): Promise<T> {
  const r = await fetch(API + ruta, cuerpo === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
  const datos = await r.json();
  if (!r.ok) throw new Error(typeof datos.detail === "string" ? datos.detail : JSON.stringify(datos.detail));
  return datos as T;
}

export const api = {
  meta: () => pedir<Meta>("/meta"),
  municipios: () => pedir<Municipio[]>("/municipios"),
  geometria: () => pedir<Geometria>("/geometria"),
  ranking: (p: Peticion) => pedir<Ranking>("/ranking", p),
  ficha: (ine5: string) => pedir<Ficha>(`/municipios/${ine5}`),
  explicacion: (ine5: string, clase: string | null, preferencias: Peticion["preferencias"], negocio: Negocio | null) =>
    pedir<Explicacion>(`/municipios/${ine5}/explicacion`, { clase, preferencias, negocio }),
  interpretar: (texto: string) => pedir<Interpretacion>("/interpretar", { texto }),
  ejemplo: () => pedir<{ texto: string; sector: string | null }>("/ejemplo", {}),
  consulta: (evidencia: Record<string, string>) => pedir<Consulta>("/consulta", { evidencia }),
  diagnostico: () => pedir<Diagnostico>("/diagnostico"),
};
