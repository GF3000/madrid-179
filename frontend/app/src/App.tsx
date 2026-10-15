import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, type Consulta, type Ficha as TFicha, type Geometria, type Interpretacion, type Meta, type Municipio,
  type Peticion, type Ranking } from "./api";
import { clasificar, describirFiltro, FILTROS_VACIOS, palabraImportancia, type Situacion } from "./modelo";
import Mapa, { type Camara, type MandoMapa } from "./componentes/Mapa";
import Ficha from "./componentes/Ficha";
import PanelDecidir, { type Cambio } from "./componentes/PanelDecidir";
import PanelPerfiles from "./componentes/PanelPerfiles";
import Intro from "./componentes/Intro";
import Viaje, { DURACION_VIAJE, origenesTarjeta, type Trayecto } from "./componentes/Viaje";
import { Buscador, ComoFunciona, ControlesMapa, Etiqueta, Leyenda, Marca, Pie } from "./componentes/Contorno";

const PETICION_INICIAL: Peticion = { preferencias: {}, filtros: FILTROS_VACIOS };
const ANCHO_PANEL = 392;
const ANCHO_FICHA = 432;

interface Datos {
  meta: Meta;
  municipios: Municipio[];
  geometria: Geometria;
}

export default function App() {
  const [datos, setDatos] = useState<Datos | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ranking, setRanking] = useState<Ranking | null>(null);
  const [peticion, setPeticion] = useState<Peticion>(PETICION_INICIAL);
  const [cambios, setCambios] = useState<{ lista: Cambio[]; motivo: string } | null>(null);
  const [pestana, setPestana] = useState<"decidir" | "perfiles">("decidir");
  const [seleccionado, setSeleccionado] = useState<string | null>(enlaceFicha); // enlace directo: /#28149
  const [ficha, setFicha] = useState<TFicha | null>(null);
  const [evidencia, setEvidencia] = useState<Record<string, string>>({});
  const [consulta, setConsulta] = useState<Consulta | null>(null);
  const [pasando, setPasando] = useState<{ ine5: string; x: number; y: number } | null>(null);
  const [claseResaltada, setClaseResaltada] = useState<string | null>(null); // vista previa al pasar el ratón
  const [clasesFijadas, setClasesFijadas] = useState<Set<string>>(new Set()); // fijadas con un clic en la leyenda
  const [camara, setCamara] = useState<Camara>({ rumbo: 0, inclinacion: 0 });
  const [mando, setMando] = useState<MandoMapa | null>(null);
  const [ayuda, setAyuda] = useState(false);
  const [intro, setIntro] = useState<"carga" | "revelando" | "fin">("carga");
  const [viajes, setViajes] = useState<Trayecto[] | null>(null);
  const desdeAsistente = useRef(false); // el próximo ranking viene del asistente: estrellas de la tarjeta al mapa
  const mandoRef = useRef(mando);
  mandoRef.current = mando;
  const seleccionadoRef = useRef(seleccionado);
  seleccionadoRef.current = seleccionado;
  const previa = useRef<Map<string, Situacion> | null>(null);
  const motivo = useRef("");

  // ------------------------------------------------------------- carga
  useEffect(() => {
    Promise.all([api.meta(), api.municipios(), api.geometria(), api.ranking(PETICION_INICIAL),
      document.fonts.ready])
      .then(([meta, municipios, geometria, r]) => {
        setDatos({ meta, municipios, geometria });
        setRanking(r);
      })
      .catch(() => setError("No hemos podido cargar los datos. Comprueba que el servidor de Madrid 179 está en marcha y recarga la página."));
  }, []);

  const situaciones = useMemo(
    () => (ranking && datos ? clasificar(ranking, datos.municipios) : new Map<string, Situacion>()),
    [ranking, datos]);

  // ----------------------------------------------- preferencias → ranking
  const cambiarPeticion = useCallback((p: Peticion, porque?: string) => {
    motivo.current = porque ?? (datos ? describirCambio(peticion, p, datos.meta) : "");
    previa.current = situaciones;
    setPeticion(p);
  }, [peticion, situaciones, datos]);

  // Lo que entiende el asistente se aplica al momento y sustituye a lo marcado a mano; se puede deshacer
  const antesDelAsistente = useRef<Peticion | null>(null);
  const aplicarAsistente = useCallback((i: Interpretacion) => {
    antesDelAsistente.current = peticion;
    desdeAsistente.current = true;
    const preferencias = Object.fromEntries(Object.entries(i.preferencias)
      .map(([k, v]) => [k, { importancia: v.importancia, sentido: v.sentido }]));
    cambiarPeticion({ preferencias, filtros: { ...FILTROS_VACIOS, ...i.filtros } },
      "Hemos aplicado lo que describiste: el mapa combina ahora las condiciones de cada municipio con tus preferencias.");
  }, [cambiarPeticion, peticion]);
  const deshacerAsistente = useCallback(() => {
    if (!antesDelAsistente.current) return;
    cambiarPeticion(antesDelAsistente.current, "Has deshecho lo que aplicó el asistente: vuelves a lo que tenías marcado.");
    antesDelAsistente.current = null;
  }, [cambiarPeticion]);

  useEffect(() => {
    if (!datos || peticion === PETICION_INICIAL) return;
    let vigente = true;
    let llegada = 0;
    const t = setTimeout(() => {
      api.ranking(peticion).then((r) => {
        if (!vigente) return;
        const nuevas = clasificar(r, datos.municipios);
        const antes = previa.current;
        const lista: Cambio[] = [];
        if (antes) {
          for (const [i, s] of nuevas) {
            const a = antes.get(i);
            if (a && a.clase.id !== s.clase.id) lista.push({ ine5: i, antes: a.clase, despues: s.clase });
          }
        }
        const aplicar = () => {
          if (antes) setCambios({ lista, motivo: motivo.current });
          setRanking(r);
        };
        // Con el asistente, las columnas se mueven cuando llegan las estrellas
        const trayectos = desdeAsistente.current
          ? trayectosAsistente(lista, nuevas, datos.geometria, mandoRef.current, seleccionadoRef.current !== null) : [];
        desdeAsistente.current = false;
        if (trayectos.length === 0) return aplicar();
        setViajes(trayectos);
        llegada = window.setTimeout(aplicar, DURACION_VIAJE(trayectos.length) - 60);
      }).catch(() => setError("No hemos podido actualizar el resultado. Vuelve a intentarlo."));
    }, 120);
    return () => { vigente = false; clearTimeout(t); clearTimeout(llegada); };
  }, [peticion, datos]);

  // ---------------------------------------------------------------- ficha
  useEffect(() => {
    if (!seleccionado) { setFicha(null); history.replaceState(null, "", location.pathname); return; }
    history.replaceState(null, "", `#${seleccionado}`);
    let vigente = true;
    api.ficha(seleccionado).then((f) => vigente && setFicha(f)).catch(() => vigente && setSeleccionado(null));
    return () => { vigente = false; };
  }, [seleccionado]);

  useEffect(() => {
    const enlace = () => {
      const i = enlaceFicha();
      if (i) setSeleccionado(i);
    };
    window.addEventListener("hashchange", enlace);
    return () => window.removeEventListener("hashchange", enlace);
  }, []);

  useEffect(() => {
    const tecla = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (ayuda) setAyuda(false); else setSeleccionado(null);
    };
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [ayuda]);

  // ------------------------------------------------------------- perfiles
  useEffect(() => {
    if (!datos || pestana !== "perfiles") return;
    let vigente = true;
    api.consulta(evidencia).then((c) => vigente && setConsulta(c)).catch(() => undefined);
    return () => { vigente = false; };
  }, [evidencia, pestana, datos]);

  // ------------------------------------------------- qué se resalta en el mapa
  const clasesVisibles = useMemo(() => {
    const s = new Set(clasesFijadas);
    if (claseResaltada) s.add(claseResaltada);
    return s;
  }, [clasesFijadas, claseResaltada]);
  const alternarClase = useCallback((id: string) => setClasesFijadas((antes) => {
    const s = new Set(antes);
    if (s.has(id)) s.delete(id); else s.add(id);
    return s;
  }), []);

  const resaltados = useMemo(() => {
    if (pestana === "perfiles" && consulta && Object.keys(evidencia).length > 0)
      return new Set(consulta.municipios.map((m) => m.ine5));
    if (clasesVisibles.size > 0)
      return new Set([...situaciones].filter(([, s]) => clasesVisibles.has(s.clase.id)).map(([i]) => i));
    return null;
  }, [pestana, consulta, evidencia, clasesVisibles, situaciones]);

  const etiquetas = useMemo(() => {
    // los cinco mejores de lo que se ve: de todos, o solo de los grupos resaltados o fijados
    const top = pestana === "decidir"
      ? [...situaciones].filter(([, s]) => s.posicion !== null && (clasesVisibles.size === 0 || clasesVisibles.has(s.clase.id)))
        .sort((a, b) => a[1].posicion! - b[1].posicion!).slice(0, 5).map(([i]) => i) : [];
    return seleccionado ? [...top.filter((i) => i !== seleccionado), seleccionado] : top;
  }, [situaciones, seleccionado, pestana, clasesVisibles]);

  const porIne = useMemo(() => new Map(datos?.municipios.map((m) => [m.ine5, m])), [datos]);

  if (error && !datos) return <div className="pantalla-aviso"><Marca onAyuda={() => undefined} /><p>{error}</p></div>;
  // La intro tapa la carga; cuando entra el carmesí de la bandera se monta la app por debajo
  const pantallaIntro = intro !== "fin" && (
    <Intro listo={!!datos && !!ranking} mapa={mando} contorno={datos?.geometria.contorno ?? null} onRevelar={() => setIntro("revelando")} onFin={() => setIntro("fin")} />);
  if (!datos || !ranking || intro === "carga") return pantallaIntro;

  return (<>
    <div className={`app${seleccionado ? " con-ficha" : ""}${intro !== "fin" ? " intro-activa" : ""}`}>
      <Mapa geometria={datos.geometria} situaciones={situaciones} seleccionado={seleccionado}
        resaltados={resaltados} etiquetas={etiquetas} onSeleccionar={setSeleccionado} onPasar={setPasando}
        onCamara={setCamara} onMando={setMando} entrar={intro === "fin"}
        margenes={{ izquierda: ANCHO_PANEL + 32, derecha: seleccionado ? ANCHO_FICHA + 32 : 0 }} />

      <aside className="panel" style={{ width: ANCHO_PANEL }}>
        <Marca onAyuda={() => setAyuda(true)} />
        <Buscador municipios={datos.municipios} onSeleccionar={setSeleccionado} />
        <nav className="pestanas" style={{ ["--i" as string]: pestana === "decidir" ? 0 : 1 }}>
          <span className="pestanas-cursor" aria-hidden />
          <button className={pestana === "decidir" ? "activa" : ""} onClick={() => setPestana("decidir")}>Dónde abrir</button>
          <button className={pestana === "perfiles" ? "activa" : ""} onClick={() => setPestana("perfiles")}>Explorar perfiles</button>
        </nav>
        <div className="panel-desplazable" key={pestana}>
          {pestana === "decidir"
            ? <PanelDecidir meta={datos.meta} peticion={peticion} onPeticion={cambiarPeticion}
                onAsistente={aplicarAsistente} onDeshacerAsistente={deshacerAsistente} pesos={ranking.pesos} municipios={datos.municipios}
                situaciones={situaciones} cambios={cambios} onCerrarCambios={() => setCambios(null)}
                onSeleccionar={setSeleccionado} onResaltarClase={setClaseResaltada} seleccionado={seleccionado} />
            : <PanelPerfiles meta={datos.meta} evidencia={evidencia} onEvidencia={setEvidencia} consulta={consulta}
                onSeleccionar={setSeleccionado} />}
        </div>
        <Pie />
      </aside>

      {seleccionado && (
        <Ficha ficha={ficha?.ine5 === seleccionado ? ficha : null} cargando={false}
          situacion={situaciones.get(seleccionado)} meta={datos.meta} pesos={ranking.pesos} peticion={peticion}
          onCerrar={() => setSeleccionado(null)} />
      )}

      <Leyenda resaltada={claseResaltada} fijadas={clasesFijadas} onResaltar={setClaseResaltada} onFijar={alternarClase}
        onLimpiar={() => setClasesFijadas(new Set())} modo={pestana} />
      <ControlesMapa camara={camara} mando={mando} />
      {pasando && <Etiqueta x={pasando.x} y={pasando.y} municipio={porIne.get(pasando.ine5)}
        situacion={situaciones.get(pasando.ine5)} />}
      {error && <div className="brindis" role="status" onClick={() => setError(null)}>{error}</div>}
      {ayuda && <ComoFunciona meta={datos.meta} onCerrar={() => setAyuda(false)} />}
      {viajes && <Viaje trayectos={viajes} onFin={() => setViajes(null)} />}
    </div>
    {pantallaIntro}
  </>);
}

// Una estrella por cada cosa entendida, hacia los municipios que suben de grupo (y si no sube ninguno, hacia los
// primeros del ranking), siempre que se vean en pantalla y no queden tapados por el panel o la ficha
function trayectosAsistente(lista: Cambio[], nuevas: Map<string, Situacion>, geometria: Geometria,
  mando: MandoMapa | null, conFicha: boolean): Trayecto[] {
  if (!mando || matchMedia("(prefers-reduced-motion: reduce)").matches) return [];
  const origenes = origenesTarjeta();
  if (origenes.length === 0) return [];
  const suben = lista.filter((c) => c.despues.orden < c.antes.orden)
    .sort((a, b) => a.despues.orden - b.despues.orden || (nuevas.get(a.ine5)?.posicion ?? 999) - (nuevas.get(b.ine5)?.posicion ?? 999))
    .map((c) => c.ine5);
  const primeros = [...nuevas].filter(([, s]) => s.posicion !== null)
    .sort((a, b) => a[1].posicion! - b[1].posicion!).map(([i]) => i);
  const centros = new Map(geometria.features.map((f) => [f.properties.ine5, f.properties.centro]));
  const elegidos = [...new Set([...suben, ...primeros])].filter((i) => centros.has(i)).slice(0, 40);
  const derecha = innerWidth - (conFicha ? ANCHO_FICHA + 48 : 48);
  const destinos = mando.proyectar(elegidos.map((i) => centros.get(i)!))
    .filter(([x, y]) => x > ANCHO_PANEL + 56 && x < derecha && y > 48 && y < innerHeight - 110)
    .slice(0, origenes.length);
  if (destinos.length === 0) return [];
  return origenes.map((o, k) => ({ x0: o.x, y0: o.y, x1: destinos[k % destinos.length][0], y1: destinos[k % destinos.length][1] }));
}

function enlaceFicha(): string | null {
  return location.hash.match(/^#(\d{5})$/)?.[1] ?? null;
}

function describirCambio(a: Peticion, b: Peticion, meta: Meta): string {
  for (const c of meta.catalogo) {
    const x = a.preferencias[c.clave];
    const y = b.preferencias[c.clave];
    if (x?.importancia === y?.importancia && x?.sentido === y?.sentido) continue;
    const nombre = c.nombre.toLowerCase();
    if (!y) return `Has dejado de tener en cuenta «${nombre}»: el orden vuelve a apoyarse más en las condiciones del municipio.`;
    const sentido = c.sentidos?.find((s) => s.valor === y.sentido)?.etiqueta.toLowerCase();
    return `Ahora «${nombre}»${sentido ? ` (${sentido})` : ""} cuenta ${palabraImportancia(y.importancia).toLowerCase()}: `
      + "suben los municipios que mejor lo cumplen.";
  }
  for (const k of Object.keys(b.filtros) as (keyof Peticion["filtros"])[]) {
    const x = a.filtros[k];
    const y = b.filtros[k];
    if (x === y) continue;
    return y === null || y === false
      ? `Ya no exiges «${describirFiltro(k, x).toLowerCase()}»: vuelven a la comparación los municipios que lo incumplían.`
      : `Solo se comparan municipios con «${describirFiltro(k, y).toLowerCase()}»; los grupos se recalculan entre ellos.`;
  }
  return "";
}
