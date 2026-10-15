// Pestaña «Dónde abrir»: asistente, lo que le importa al usuario, sus requisitos y el resultado por grupos.
import { useEffect, useRef, useState } from "react";
import type { Filtros, Importancia, Interpretacion, Meta, Municipio, Peticion, PreferenciaCatalogo } from "../api";
import { CLASES, FILTRADO, OPCIONES_IMPORTANCIA, pesoMinimoModelo, type Clase, type Situacion } from "../modelo";
import Asistente from "./Asistente";
import { nombreLegible } from "./Ficha";
import { Ayuda, Columna, Segmentado } from "./piezas";

export interface Cambio {
  ine5: string;
  antes: Clase;
  despues: Clase;
}

interface Props {
  meta: Meta;
  peticion: Peticion;
  onPeticion: (p: Peticion, motivo?: string) => void;
  onAsistente: (i: Interpretacion) => void;
  onDeshacerAsistente: () => void;
  pesos: Record<string, number>;
  municipios: Municipio[];
  situaciones: Map<string, Situacion>;
  cambios: { lista: Cambio[]; motivo: string } | null;
  onCerrarCambios: () => void;
  onSeleccionar: (ine5: string) => void;
  onResaltarClase: (c: string | null) => void;
  seleccionado: string | null;
}

// Tamaño imprescindible: atajos sobre poblacion_min / poblacion_max
const TAMANOS = [
  { valor: "cualquiera", etiqueta: "Cualquiera", min: null, max: null },
  { valor: "menos5", etiqueta: "< 5.000", min: null, max: 5000 },
  { valor: "menos20", etiqueta: "< 20.000", min: null, max: 20000 },
  { valor: "mas20", etiqueta: "> 20.000", min: 20000, max: null },
] as const;

export default function PanelDecidir(p: Props) {
  const [abiertos, setAbiertos] = useState<Set<string>>(new Set(["c0"]));
  const [gruposPref, setGruposPref] = useState<Set<string>>(new Set());
  const nombres = new Map(p.municipios.map((m) => [m.ine5, nombreLegible(m.municipio)]));
  const bloqueCambios = useRef<HTMLDivElement>(null);
  // tras un cambio, el panel lleva la vista a «Qué ha cambiado»: la explicación acompaña al movimiento del mapa
  useEffect(() => {
    bloqueCambios.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [p.cambios]);
  const { preferencias: pref, filtros } = p.peticion;

  const importancia = (k: string): Importancia => pref[k]?.importancia ?? "Me da igual";
  const ponerPref = (c: PreferenciaCatalogo, cambio: { importancia?: Importancia; sentido?: string }) => {
    const actual = pref[c.clave] ?? { importancia: "Me da igual" as Importancia, sentido: c.sentidos?.[0].valor ?? null };
    const nueva = { ...actual, ...cambio };
    const prefs = { ...pref };
    if (nueva.importancia === "Me da igual") delete prefs[c.clave]; else prefs[c.clave] = nueva;
    p.onPeticion({ preferencias: prefs, filtros });
  };
  const ponerFiltro = (f: Partial<Filtros>) => p.onPeticion({ preferencias: pref, filtros: { ...filtros, ...f } });

  const porGrupo = new Map<string, PreferenciaCatalogo[]>();
  for (const c of p.meta.catalogo) porGrupo.set(c.grupo, [...(porGrupo.get(c.grupo) ?? []), c]);
  const alternarPref = (g: string) => setGruposPref((s) => alternar(s, g));

  const tamano = TAMANOS.find((t) => t.min === filtros.poblacion_min && t.max === filtros.poblacion_max);
  const opcionesTamano = tamano ? TAMANOS : [...TAMANOS, { valor: "otro", etiqueta: "Otro", min: null, max: null }];

  const grupos = [...CLASES, FILTRADO].map((clase) => ({
    clase,
    lista: [...p.situaciones.entries()].filter(([, s]) => s.clase.id === clase.id)
      .sort((a, b) => (a[1].posicion ?? 999) - (b[1].posicion ?? 999)).map(([i]) => i),
  })).filter((g) => g.lista.length > 0);

  const suben = p.cambios?.lista.filter((c) => c.despues.orden < c.antes.orden) ?? [];
  const bajan = p.cambios?.lista.filter((c) => c.despues.orden > c.antes.orden) ?? [];
  const activas = p.meta.catalogo.filter((c) => (p.pesos[c.clave] ?? 0) > 0);

  return (
    <div className="panel-contenido">
      <p className="entradilla">
        Cada municipio se levanta según sus condiciones para abrir una oficina: <b>más alto y más rojo, más
        favorable</b>. Cuéntanos qué necesitas y mira cómo se reordena la región.
      </p>

      {p.meta.asistente_disponible && <Asistente meta={p.meta} onAplicar={p.onAsistente} onDeshacer={p.onDeshacerAsistente} />}

      <div className="bloque">
        <div className="bloque-cabecera">
          <h3>Lo que te importa</h3>
          {Object.keys(pref).length > 0 && (
            <button className="enlace" onClick={() => p.onPeticion({ preferencias: {}, filtros },
              "Has quitado tus preferencias: cada municipio vuelve a depender solo de sus condiciones.")}>Quitar todas</button>
          )}
        </div>
        {activas.length > 0 && <Reparto pesos={p.pesos} activas={activas} tope={p.meta.tope_preferencias} />}
        {[...porGrupo.entries()].map(([grupo, lista]) => {
          const n = lista.filter((c) => importancia(c.clave) !== "Me da igual").length;
          const abierto = gruposPref.has(grupo);
          return (
            <div key={grupo} className={`grupo-pref${abierto ? " abierto" : ""}`}>
              <button className="grupo-pref-cabecera" onClick={() => alternarPref(grupo)} aria-expanded={abierto}>
                <span>{grupo}</span>
                {n > 0 && <span className="insignia">{n}</span>}
                <span className="plegar" aria-hidden />
              </button>
              {abierto && (
                <div className="grupo-pref-cuerpo">
                  {lista.map((c) => (
                    <div className={`pregunta${importancia(c.clave) !== "Me da igual" ? " activa" : ""}`} key={c.clave}>
                      <Ayuda texto={c.descripcion} clase="pregunta-titulo">{c.nombre}</Ayuda>
                      {c.sentidos && (
                        <Segmentado compacto nombre={`Sentido: ${c.nombre}`} opciones={c.sentidos}
                          valor={pref[c.clave]?.sentido ?? c.sentidos[0].valor}
                          onCambio={(v) => ponerPref(c, {
                            sentido: v,
                            importancia: importancia(c.clave) === "Me da igual" ? "Poco importante" : importancia(c.clave),
                          })} />
                      )}
                      <Segmentado nombre={`Importancia: ${c.nombre}`} opciones={OPCIONES_IMPORTANCIA}
                        valor={importancia(c.clave)} onCambio={(v) => ponerPref(c, { importancia: v as Importancia })} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="bloque">
        <h3>Imprescindible</h3>
        <Casilla marcada={filtros.estacion_max_km !== null}
          onCambio={(m) => ponerFiltro({ estacion_max_km: m ? 5 : null })}
          texto={<>Estación de tren a menos de <b>{filtros.estacion_max_km ?? 5} km</b></>} />
        {filtros.estacion_max_km !== null && (
          <Deslizador min={1} max={20} valor={filtros.estacion_max_km} etiqueta="Distancia máxima a la estación"
            onCambio={(v) => ponerFiltro({ estacion_max_km: v })} />
        )}
        <Casilla marcada={filtros.madrid_max_km !== null}
          onCambio={(m) => ponerFiltro({ madrid_max_km: m ? 30 : null })}
          texto={<>A menos de <b>{filtros.madrid_max_km ?? 30} km</b> de Madrid</>} />
        {filtros.madrid_max_km !== null && (
          <Deslizador min={10} max={70} paso={5} valor={filtros.madrid_max_km} etiqueta="Distancia máxima a Madrid"
            onCambio={(v) => ponerFiltro({ madrid_max_km: v })} />
        )}
        <Casilla marcada={filtros.madrid_min_km !== null}
          onCambio={(m) => ponerFiltro({ madrid_min_km: m ? 30 : null })}
          texto={<>A más de <b>{filtros.madrid_min_km ?? 30} km</b> de Madrid</>} />
        {filtros.madrid_min_km !== null && (
          <Deslizador min={10} max={60} paso={5} valor={filtros.madrid_min_km} etiqueta="Distancia mínima a Madrid"
            onCambio={(v) => ponerFiltro({ madrid_min_km: v })} />
        )}
        <div className="pregunta">
          <span className="pregunta-titulo">Habitantes del municipio</span>
          <Segmentado compacto nombre="Tamaño imprescindible" opciones={opcionesTamano}
            valor={tamano?.valor ?? "otro"}
            onCambio={(v) => {
              const t = TAMANOS.find((x) => x.valor === v);
              if (t) ponerFiltro({ poblacion_min: t.min, poblacion_max: t.max });
            }} />
          {!tamano && (
            <span className="nota">
              {[filtros.poblacion_min !== null && `más de ${filtros.poblacion_min.toLocaleString("es-ES")}`,
                filtros.poblacion_max !== null && `menos de ${filtros.poblacion_max.toLocaleString("es-ES")}`]
                .filter(Boolean).join(" y ")} habitantes
            </span>
          )}
        </div>
        <Casilla marcada={filtros.solo_con_ayudas} onCambio={(m) => ponerFiltro({ solo_con_ayudas: m })}
          texto="Solo municipios donde haya ayudas por tamaño" />
        <Casilla marcada={filtros.con_coworking} onCambio={(m) => ponerFiltro({ con_coworking: m })}
          texto="Solo municipios con coworking" />
      </div>

      {p.cambios && (suben.length > 0 || bajan.length > 0) && (
        <div className="cambios" key={p.cambios.motivo} ref={bloqueCambios}>
          <div className="cambios-cabecera">
            <h3>Qué ha cambiado</h3>
            <button className="enlace" onClick={p.onCerrarCambios}>Entendido</button>
          </div>
          <p className="nota">{p.cambios.motivo}</p>
          <div className="cambios-columnas">
            <ListaCambios titulo={`Suben de grupo (${suben.length})`} lista={suben} nombres={nombres}
              onSeleccionar={p.onSeleccionar} sentido="sube" />
            <ListaCambios titulo={`Bajan de grupo (${bajan.length})`} lista={bajan} nombres={nombres}
              onSeleccionar={p.onSeleccionar} sentido="baja" />
          </div>
        </div>
      )}

      <div className="bloque">
        <h3>Municipios por grupo</h3>
        {grupos.length === 0 && <p className="nota">Ningún municipio cumple a la vez todos tus requisitos imprescindibles.
          Prueba a relajar alguno.</p>}
        {grupos.map(({ clase, lista }) => (
          <div key={clase.id} className={`grupo${abiertos.has(clase.id) ? " abierto" : ""}`}
            onMouseEnter={() => p.onResaltarClase(clase.id)} onMouseLeave={() => p.onResaltarClase(null)}>
            <button className="grupo-cabecera" onClick={() => setAbiertos((s) => alternar(s, clase.id))}
              aria-expanded={abiertos.has(clase.id)}>
              <Columna clase={clase} />
              <span className="grupo-nombre">{clase.nombre}</span>
              <span className="grupo-cuenta">{lista.length}</span>
              <span className="plegar" aria-hidden />
            </button>
            {abiertos.has(clase.id) && (
              <ul className="grupo-lista">
                {lista.map((i) => (
                  <li key={i}>
                    <button className={p.seleccionado === i ? "activo" : ""} onClick={() => p.onSeleccionar(i)}>
                      {nombres.get(i)}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/** Cuánto pesa cada cosa en el orden: el modelo siempre al menos 1 / (1 + tope) (tope del backend). */
function Reparto({ pesos, activas, tope }: { pesos: Record<string, number>; activas: PreferenciaCatalogo[]; tope: number }) {
  const minimo = pesoMinimoModelo(tope);
  const total = 1 + activas.reduce((s, c) => s + pesos[c.clave], 0);
  return (
    <div className="reparto-pesos">
      <div className="reparto-pesos-barra">
        <span className="peso-modelo" style={{ flexGrow: 1 / total }} title="Condiciones del municipio (modelo)" />
        {activas.map((c, k) => (
          <span key={c.clave} className="peso-pref" style={{ flexGrow: pesos[c.clave] / total, opacity: 1 - (k % 4) * 0.18 }}
            title={c.nombre} />
        ))}
      </div>
      <p className="nota">
        <i className="punto modelo" /> Las condiciones del municipio deciden al menos {minimo};{" "}
        <i className="punto pref" /> tus preferencias, el resto.
      </p>
    </div>
  );
}

function Casilla({ marcada, onCambio, texto }: { marcada: boolean; onCambio: (m: boolean) => void; texto: React.ReactNode }) {
  return (
    <label className="casilla">
      <input type="checkbox" checked={marcada} onChange={(e) => onCambio(e.target.checked)} />
      <span className="caja" aria-hidden />
      <span>{texto}</span>
    </label>
  );
}

function Deslizador({ min, max, paso = 1, valor, etiqueta, onCambio }: {
  min: number; max: number; paso?: number; valor: number; etiqueta: string; onCambio: (v: number) => void;
}) {
  return (
    <input className="deslizador" type="range" min={min} max={max} step={paso} value={valor} aria-label={etiqueta}
      onChange={(e) => onCambio(Number(e.target.value))} />
  );
}

function alternar(s: Set<string>, id: string) {
  const n = new Set(s);
  if (n.has(id)) n.delete(id); else n.add(id);
  return n;
}

function ListaCambios({ titulo, lista, nombres, onSeleccionar, sentido }: {
  titulo: string; lista: Cambio[]; nombres: Map<string, string>; onSeleccionar: (i: string) => void;
  sentido: "sube" | "baja";
}) {
  if (lista.length === 0) return null;
  const orden = [...lista].sort((a, b) => Math.abs(b.antes.orden - b.despues.orden) - Math.abs(a.antes.orden - a.despues.orden));
  return (
    <div className={`lista-cambios ${sentido}`}>
      <h4><span className="flecha" aria-hidden />{titulo}</h4>
      <ul>
        {orden.slice(0, 6).map((c) => (
          <li key={c.ine5}>
            <button onClick={() => onSeleccionar(c.ine5)}>
              {nombres.get(c.ine5)}
              <small>{c.antes.nombre.toLowerCase()} → {c.despues.nombre.toLowerCase()}</small>
            </button>
          </li>
        ))}
        {orden.length > 6 && <li className="mas">y {orden.length - 6} más</li>}
      </ul>
    </div>
  );
}
