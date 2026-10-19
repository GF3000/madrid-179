// Pestaña «Dónde actuar» (Administración): qué municipios necesitan crecer, cuál es su pronóstico empresarial y qué les
// frena. Diagnóstico de la situación 2020-2024 (/api/v1/diagnostico); no es un simulador ni habla de efectos.
import { useEffect, useRef } from "react";
import type { ContextoPolitica, Diagnostico, IdCuadrante, MunicipioDiagnostico } from "../api";
import { CUADRANTES, enPalabras, fuerza } from "../modelo";
import { nombreLegible } from "./Ficha";
import { Columna, MarcasFuerza, Segmentado } from "./piezas";
import { Casilla } from "./PanelDecidir";
import { useEsTactil } from "../movil";

export interface Ambito {
  poblacion: "todas" | "menos2500" | "medio" | "mas20000";
  distancia: "da-igual" | "Cerca" | "Media" | "Lejos";
  // filtros del contexto para la política (no del modelo): restringen la lista, los recuentos y el mapa
  sinOficinas: boolean;
  leader: boolean;
}

export const AMBITO_TODO: Ambito = { poblacion: "todas", distancia: "da-igual", sinOficinas: false, leader: false };

const POBLACIONES = [
  { valor: "todas", etiqueta: "Todas" },
  { valor: "menos2500", etiqueta: "< 2.500" },
  { valor: "medio", etiqueta: "2.500–20.000" },
  { valor: "mas20000", etiqueta: "> 20.000" },
] as const;

const DISTANCIAS = [
  { valor: "da-igual", etiqueta: "Da igual" },
  { valor: "Cerca", etiqueta: "Cerca" },
  { valor: "Media", etiqueta: "Media" },
  { valor: "Lejos", etiqueta: "Lejos" },
] as const;

export function enAmbito(m: MunicipioDiagnostico, a: Ambito): boolean {
  const p = m.poblacion;
  const okPob = a.poblacion === "todas" || (a.poblacion === "menos2500" ? p < 2500
    : a.poblacion === "medio" ? p >= 2500 && p <= 20000 : p > 20000);
  return okPob && (a.distancia === "da-igual" || m.distancia === a.distancia)
    && (!a.sinOficinas || m.contexto.oficinas.locales === 0)
    && (!a.leader || !!m.contexto.ayudas?.leader);
}

interface Props {
  diagnostico: Diagnostico | null;
  error: boolean;
  ambito: Ambito;
  onAmbito: (a: Ambito) => void;
  fijados: Set<string>; // cuadrantes elegidos (en el panel o en la leyenda)
  onElegirCuadrante: (id: IdCuadrante) => void;
  onResaltarCuadrante: (id: string | null) => void;
  diagnosticado: string | null;
  onDiagnosticar: (ine5: string) => void;
  onPerfil: (ine5: string) => void;
  onFicha: (ine5: string) => void;
}

export default function PanelActuar(p: Props) {
  const bloqueMunicipio = useRef<HTMLDivElement>(null);
  // en táctil no hay vista previa: el toque emula un «pasar» que no se va (como en la leyenda)
  const tactil = useEsTactil();
  const previa = (c: IdCuadrante | null) => { if (!tactil) p.onResaltarCuadrante(c); };
  // al elegir un municipio (lista, mapa o buscador) el panel lleva la vista a su diagnóstico
  useEffect(() => {
    if (p.diagnosticado) bloqueMunicipio.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [p.diagnosticado]);

  if (p.error) {
    return (
      <div className="panel-contenido">
        <p className="entradilla">Qué municipios necesitan crecer, cuál es su pronóstico empresarial y qué les frena.</p>
        <p className="nota">El diagnóstico no está disponible ahora mismo. Comprueba que el servidor está actualizado y
          vuelve a intentarlo.</p>
      </div>
    );
  }
  const d = p.diagnostico;
  const dentro = d ? d.municipios.filter((m) => enAmbito(m, p.ambito)) : [];
  const enElAmbito = d ? d.municipios.filter((m) => enAmbito(m, { ...p.ambito, sinOficinas: false, leader: false })).length : 0;
  const filtrando = p.ambito.sinOficinas || p.ambito.leader;
  const hayAyudas = !!d?.municipios.some((m) => m.contexto.ayudas);
  const lista = dentro.filter((m) => p.fijados.has(m.cuadrante)).sort((a, b) => b.necesidad - a.necesidad);
  const elegido = d?.municipios.find((m) => m.ine5 === p.diagnosticado) ?? null;

  return (
    <div className="panel-contenido actuar">
      <p className="entradilla">
        Qué municipios <b>necesitan crecer</b>, cuál es su <b>pronóstico empresarial</b> y qué les frena. Cada
        columna se levanta según la necesidad del municipio; el color dice en qué situación está. El pronóstico es el
        saldo de empresas que el modelo espera para su perfil, no lo que ha pasado.
      </p>

      <div className="bloque">
        <h3><span className="paso-n">1</span>Ámbito</h3>
        <div className="pregunta">
          <span className="pregunta-titulo">Población</span>
          <Segmentado compacto nombre="Población" opciones={POBLACIONES} valor={p.ambito.poblacion}
            onCambio={(v) => p.onAmbito({ ...p.ambito, poblacion: v })} />
        </div>
        <div className="pregunta">
          <span className="pregunta-titulo">Distancia a Madrid</span>
          <Segmentado compacto nombre="Distancia a Madrid" opciones={DISTANCIAS} valor={p.ambito.distancia}
            onCambio={(v) => p.onAmbito({ ...p.ambito, distancia: v })} />
        </div>
        {d && <p className="nota">{enElAmbito === d.municipios.length
          ? `Los ${d.municipios.length} municipios del análisis (Madrid capital es la referencia y queda fuera).`
          : `${enElAmbito} de ${d.municipios.length} municipios dentro del ámbito.`}</p>}
      </div>

      <div className="bloque">
        <h3><span className="paso-n">2</span>Cuatro situaciones</h3>
        {!d && <div className="cargando-actuar"><span className="sombra-texto" /><span className="sombra-texto corto" /></div>}
        {d && (
          <div className="filtros-contexto">
            <span className="pregunta-titulo">Solo los que… <small>(contexto, no modelo)</small></span>
            <Casilla marcada={p.ambito.sinOficinas} onCambio={(v) => p.onAmbito({ ...p.ambito, sinOficinas: v })}
              texto={<><b>Sin oficinas</b>: ningún local de oficinas en el Catastro</>} />
            {hayAyudas && (
              <Casilla marcada={p.ambito.leader} onCambio={(v) => p.onAmbito({ ...p.ambito, leader: v })}
                texto={<><b>En LEADER</b>: dentro de un Grupo de Acción Local (2023-2027)</>} />
            )}
            {filtrando && <p className="nota">{dentro.length} de {enElAmbito} municipios del ámbito cumplen el filtro.</p>}
          </div>
        )}
        {d && (
          <div className="cuadrantes" onMouseLeave={() => previa(null)}>
            {d.cuadrantes.map((c) => {
              const n = dentro.filter((m) => m.cuadrante === c.id).length;
              const activo = p.fijados.has(c.id);
              return (
                <button key={c.id} className={`cuadrante${activo ? " activo" : ""}`} aria-pressed={activo}
                  style={{ ["--c" as string]: `rgb(${CUADRANTES[c.id].color.join(",")})` }}
                  onMouseEnter={() => previa(c.id)} onFocus={() => previa(c.id)}
                  onBlur={() => previa(null)} onClick={() => p.onElegirCuadrante(c.id)}>
                  <span className="cuadrante-cabecera">
                    <i className="cuadrante-color" aria-hidden />
                    <strong>{c.nombre}</strong>
                    <span className="cuadrante-cuenta">{n}</span>
                  </span>
                  <span className="cuadrante-lectura">{c.lectura}</span>
                </button>
              );
            })}
          </div>
        )}
        {d && p.fijados.size > 0 && (
          lista.length === 0
            ? <p className="nota">Ningún municipio del ámbito{filtrando ? " con estos filtros" : ""} está en esta situación.</p>
            : (
              <>
                <p className="nota">De más a menos necesidad. Elige uno para ver su diagnóstico.</p>
                <ul className="grupo-lista lista-actuar">
                  {lista.map((m) => (
                    <li key={m.ine5}>
                      <button className={p.diagnosticado === m.ine5 ? "activo" : ""} onClick={() => p.onDiagnosticar(m.ine5)}>
                        {nombreLegible(m.municipio)}
                      </button>
                    </li>
                  ))}
                </ul>
              </>
            )
        )}
        {d && p.fijados.size === 0 && <p className="nota">Pulsa una situación para verla en el mapa y listar sus municipios.</p>}
      </div>

      <div className="bloque" ref={bloqueMunicipio}>
        <h3><span className="paso-n">3</span>Diagnóstico del municipio</h3>
        {!elegido && <p className="nota">Elige un municipio en la lista, en el mapa o con el buscador.</p>}
        {elegido && d && <DiagnosticoMunicipio m={elegido} d={d} onPerfil={p.onPerfil} onFicha={p.onFicha} />}
      </div>

      <div className="bloque en-desarrollo" aria-disabled>
        <h3><span className="paso-n">4</span>Escenario <span className="etiqueta-desarrollo">En desarrollo</span></h3>
        <p className="nota">
          El simulador de políticas llegará cuando el modelo tenga intervalos de incertidumbre y probabilidades que se
          muevan siempre en el sentido esperado. Hasta entonces no mostramos efectos: un efecto sin su incertidumbre
          prometería más de lo que los datos permiten.
        </p>
      </div>

      {d && (
        <div className="pie-actuar">
          <p className="nota">{d.aviso}</p>
          <p className="nota"><b>Cómo se mide la necesidad.</b> {d.necesidad.nota}</p>
          <p className="nota"><b>Contexto para la política.</b> {d.contexto_nota}</p>
        </div>
      )}
    </div>
  );
}

function DiagnosticoMunicipio({ m, d, onPerfil, onFicha }: {
  m: MunicipioDiagnostico; d: Diagnostico; onPerfil: (i: string) => void; onFicha: (i: string) => void;
}) {
  const c = d.cuadrantes.find((x) => x.id === m.cuadrante);
  const color = `rgb(${CUADRANTES[m.cuadrante].color.join(",")})`;
  return (
    <div className="diagnostico" key={m.ine5} style={{ ["--c" as string]: color }}>
      <div className="diagnostico-cabecera">
        <Columna clase={CUADRANTES[m.cuadrante]} grande />
        <div>
          <strong className="diagnostico-nombre">{nombreLegible(m.municipio)}</strong>
          <span className="nota">{m.poblacion.toLocaleString("es-ES")} habitantes · {DISTANCIA[m.distancia]}</span>
        </div>
      </div>
      {c && <p className="diagnostico-situacion"><b>{c.nombre}.</b> {c.lectura}</p>}

      <Medida titulo="Necesidad de crecer" que="necesidad" valor={m.necesidad} corte={d.corte} />
      <ul className="componentes">
        {d.necesidad.componentes.map((k) => {
          const x = m.componentes[k.columna];
          if (!x) return null;
          return (
            <li key={k.columna}>
              <span className="componente-nombre">{k.etiqueta}</span>
              <span className="componente-valor">{valorComponente(k.columna, x.valor)}</span>
              <span className="barra-fina" aria-hidden><i style={{ width: `${x.percentil}%` }} /></span>
              <small>En esto, más necesidad {enPalabras(x.percentil)}</small>
            </li>
          );
        })}
      </ul>

      <Medida titulo="Pronóstico empresarial" que="viabilidad" valor={m.viabilidad} corte={d.corte}
        nota="Saldo esperado de empresas según el modelo (orientativo)." />

      <h4 className="frenos-titulo">Qué le frena</h4>
      {m.frenos.length === 0
        ? <p className="vacio">El modelo no encuentra ningún factor que le reste de forma apreciable.</p>
        : <ul className="frenos">{m.frenos.map((f) => <li key={f.termino}><Freno f={f} /></li>)}</ul>}
      {m.frenos.length > 0 && (
        <div className="palanca">
          <h4>Lo que una política podría mover</h4>
          {m.freno_palanca
            ? <Freno f={m.freno_palanca} />
            : <p className="nota">Según el modelo, lo que más le frena es estructural (no depende de una política a corto
                plazo).</p>}
        </div>
      )}

      <ContextoMunicipio c={m.contexto} cuadrante={m.cuadrante} />

      <div className="diagnostico-acciones">
        <button className="boton-secundario" onClick={() => onPerfil(m.ine5)}>Ver su perfil en la red</button>
        <button className="enlace" onClick={() => onFicha(m.ine5)}>Ficha completa</button>
      </div>
    </div>
  );
}

// Contexto para la política: oficinas y programas oficiales. No sale del modelo ni dice qué efecto tendrían.
function ContextoMunicipio({ c, cuadrante }: { c: ContextoPolitica; cuadrante: IdCuadrante }) {
  const n = (x: number, dec = 0) => x.toLocaleString("es-ES", { maximumFractionDigits: dec });
  const o = c.oficinas;
  const a = c.ayudas;
  const instrumentos = a ? [
    a.leader && (
      <li key="leader">
        <b>LEADER 2023-2027</b>: grupo {a.leader.grupo} ·{" "}
        <a className="enlace" href={a.leader.fuente} target="_blank" rel="noopener noreferrer">convenio en el BOCM</a>
      </li>
    ),
    a.irpf_menos_2500 && <li key="irpf">Deducciones del IRPF por trasladarse o comprar vivienda (menos de 2.500 hab.)</li>,
    a.pir_sin_cofinanciacion && <li key="pir"><b>PIR</b>: no cofinancia sus inversiones</li>,
  ].filter(Boolean) : [];
  return (
    <section className="contexto-politica" aria-label="Contexto para la política">
      <h4>Contexto para la política</h4>
      <span className="contexto-subtitulo">Datos de contexto, no resultado del modelo</span>

      <h5>Oficinas</h5>
      {/* Cifra editorial: el dato manda, sin caja de alerta */}
      <div className={`contexto-cifra${o.locales === 0 ? " nula" : ""}`}>
        <span className="cifra">{n(o.locales)}</span>
        <span className="cifra-pie">
          {o.locales === 1 ? "local" : "locales"} de oficinas en el Catastro
          {o.locales > 0 && <><br />{n(o.por_1000hab, 1)} por cada 1.000 hab.</>}
        </span>
      </div>
      {o.locales === 0 && (
        <p className="contexto-dato">
          Hoy una empresa no tendría dónde instalarse.
          {(cuadrante === "oportunidad" || cuadrante === "apoyo") &&
            " Una política puede cubrirlo directamente: vivero, coworking o suelo para oficinas."}
        </p>
      )}
      {o.coworking > 0 && (
        <p className="contexto-dato">
          {n(o.coworking)} {o.coworking === 1 ? "espacio" : "espacios"} de coworking según OpenStreetMap.
        </p>
      )}

      <h5>Ayudas oficiales que le alcanzan</h5>
      {!a
        ? <p className="vacio">No disponibles ahora mismo.</p>
        : instrumentos.length === 0
          ? <p className="contexto-dato">No está en LEADER ni en los programas para municipios de menos de 2.500 habitantes.</p>
          : <ul className="contexto-lista">{instrumentos}</ul>}
      {a && (
        <small>
          {a.irpf_menos_2500 ? `Umbral de 2.500 hab. con el padrón a 1 de enero de ${a.anio_padron}. ` : ""}
          Tener un programa no mide su efecto en la viabilidad.
        </small>
      )}
    </section>
  );
}

function Medida({ titulo, que, valor, corte, nota }: { titulo: string; que: string; valor: number; corte: number; nota?: string }) {
  return (
    <div className="medida">
      <div className="medida-cabecera">
        <span>{titulo}</span>
        <b>{valor >= corte ? "Mitad alta" : "Mitad baja"}</b>
      </div>
      <span className="barra-medida" aria-hidden>
        <i style={{ width: `${valor}%` }} />
        <em style={{ left: `${corte}%` }} title="Corte entre mitad alta y baja" />
      </span>
      <small>Más {que} {enPalabras(valor)}{nota ? `. ${nota}` : ""}</small>
    </div>
  );
}

function Freno({ f }: { f: MunicipioDiagnostico["frenos"][number] }) {
  const n = fuerza(f.aportacion_pp);
  return (
    <div className="freno">
      {n ? <MarcasFuerza fuerza={n} signo={-1} /> : <span className="marcas" />}
      <span className="freno-titulo">{f.etiqueta}</span>
      <span className={`chip-tipo ${f.tipo}`}>{f.tipo === "palanca" ? "Palanca" : "Estructural"}</span>
      {f.lectura && <em className="freno-lectura">{f.lectura}</em>}
    </div>
  );
}

const DISTANCIA: Record<string, string> = { Cerca: "cerca de Madrid", Media: "a media distancia de Madrid", Lejos: "lejos de Madrid" };

function valorComponente(columna: string, v: number): string {
  const n = (x: number, dec = 1) => x.toLocaleString("es-ES", { maximumFractionDigits: dec });
  switch (columna) {
    case "crec_pob_5a": return `${v > 0 ? "+" : ""}${n(v * 100, 0)} % en 5 años`;
    case "pct_menores_45": return `${n(v)} % menores de 45`;
    case "paro_por_100hab": return `${n(v)} parados por 100 hab.`;
    case "poblacion": return `${n(v, 0)} habitantes`;
    default: return n(v, 2);
  }
}

