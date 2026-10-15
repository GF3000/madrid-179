import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, type Consulta, type Diagnostico, type Ficha as TFicha, type Geometria, type IdCuadrante, type Interpretacion,
  type Meta, type Municipio, type Negocio, type Peticion, type Ranking } from "./api";
import { clasificar, describirFiltro, FILTROS_VACIOS, palabraImportancia, situacionesActuar, type Situacion } from "./modelo";
import Mapa, { type Camara, type MandoMapa } from "./componentes/Mapa";
import Ficha from "./componentes/Ficha";
import PanelDecidir, { type Cambio } from "./componentes/PanelDecidir";
import PanelPerfiles from "./componentes/PanelPerfiles";
import PanelActuar, { AMBITO_TODO, enAmbito, type Ambito } from "./componentes/PanelActuar";
import Intro from "./componentes/Intro";
import Viaje, { DURACION_VIAJE, origenesTarjeta, type Trayecto } from "./componentes/Viaje";
import Recorrido, { type Parada } from "./componentes/Recorrido";
import Navegacion, { type Dialogo, type Modo } from "./componentes/Navegacion";
import { AcercaDe, AvisoMapa, Buscador, ComoFunciona, ControlesMapa, Etiqueta, Leyenda, Marca, VentanaVideo } from "./componentes/Contorno";

const PETICION_INICIAL: Peticion = { preferencias: {}, filtros: FILTROS_VACIOS };
const ANCHO_NAV = 68; // barra de navegación vertical
const ANCHO_PANEL = 392;
const ANCHO_FICHA = 432;
// Borde izquierdo de lo que se ve del mapa: barra (16 + 68), hueco de 8, panel y 16 de aire; sin panel, barra y aire
const IZQ_PANEL = 16 + ANCHO_NAV + 8 + ANCHO_PANEL + 16;
const IZQ_SIN_PANEL = 16 + ANCHO_NAV + 16;
const TOP_RECORRIDO = 5; // municipios que visita el recorrido tras el asistente
const TITULOS: Record<Modo, string> = { decidir: "Dónde abrir", actuar: "Dónde actuar", perfiles: "Explorar perfiles" };

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
  const [pestana, setPestana] = useState<Modo>("decidir");
  const [panelAbierto, setPanelAbierto] = useState(true); // pulsar el modo activo en la barra pliega el panel
  const [seleccionado, setSeleccionado] = useState<string | null>(enlaceFicha); // enlace directo: /#28149
  const [ficha, setFicha] = useState<TFicha | null>(null);
  const [evidencia, setEvidencia] = useState<Record<string, string>>({});
  const [consulta, setConsulta] = useState<Consulta | null>(null);
  const [pasando, setPasando] = useState<{ ine5: string; x: number; y: number } | null>(null);
  const [claseResaltada, setClaseResaltada] = useState<string | null>(null); // vista previa al pasar el ratón
  const [clasesFijadas, setClasesFijadas] = useState<Set<string>>(new Set()); // fijadas con un clic en la leyenda
  const [camara, setCamara] = useState<Camara>({ rumbo: 0, inclinacion: 0 });
  const [mando, setMando] = useState<MandoMapa | null>(null);
  const [dialogo, setDialogo] = useState<Dialogo | null>(() => (enlaceEquipo() ? "acerca" : null)); // /#equipo
  const [intro, setIntro] = useState<"carga" | "revelando" | "fin">("carga");
  const [viajes, setViajes] = useState<Trayecto[] | null>(null);
  const [recorrido, setRecorrido] = useState<{ id: number; paradas: Parada[] } | null>(null);
  const [destacado, setDestacado] = useState<string | null>(null); // parada actual del recorrido
  // «Dónde actuar»: diagnóstico (se pide al entrar en el modo), ámbito y municipio diagnosticado en el panel
  const [diagnostico, setDiagnostico] = useState<Diagnostico | null>(null);
  const [errorDiagnostico, setErrorDiagnostico] = useState(false);
  const [ambito, setAmbito] = useState<Ambito>(AMBITO_TODO);
  const [diagnosticado, setDiagnosticado] = useState<string | null>(null);
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
    setRecorrido(null); // un cambio nuevo interrumpe el recorrido en curso
    setPeticion(p);
  }, [peticion, situaciones, datos]);

  // Lo que entiende el asistente se aplica al momento y sustituye a lo marcado a mano; se puede deshacer
  const antesDelAsistente = useRef<{ peticion: Peticion; negocio: Negocio | null } | null>(null);
  const [negocio, setNegocio] = useState<Negocio | null>(null); // lo que contó de su negocio: adapta las explicaciones
  const aplicarAsistente = useCallback((i: Interpretacion) => {
    antesDelAsistente.current = { peticion, negocio };
    setNegocio(i.sector || i.resumen ? { sector: i.sector, resumen: i.resumen } : null);
    desdeAsistente.current = true;
    const preferencias = Object.fromEntries(Object.entries(i.preferencias)
      .map(([k, v]) => [k, { importancia: v.importancia, sentido: v.sentido }]));
    cambiarPeticion({ preferencias, filtros: { ...FILTROS_VACIOS, ...i.filtros } },
      "Hemos aplicado lo que describiste: el mapa combina ahora las condiciones de cada municipio con tus preferencias.");
  }, [cambiarPeticion, peticion, negocio]);
  const deshacerAsistente = useCallback(() => {
    if (!antesDelAsistente.current) return;
    setNegocio(antesDelAsistente.current.negocio);
    cambiarPeticion(antesDelAsistente.current.peticion, "Has deshecho lo que aplicó el asistente: vuelves a lo que tenías marcado.");
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
        // Con el asistente, al aplicar arranca el recorrido por los mejores
        const paradas = desdeAsistente.current && mandoRef.current && !movimientoReducido()
          ? paradasRecorrido(nuevas, datos) : [];
        const aplicar = () => {
          if (antes) setCambios({ lista, motivo: motivo.current });
          setRanking(r);
          if (paradas.length > 0) {
            setSeleccionado(null);
            setRecorrido({ id: Date.now(), paradas });
          }
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
      if (enlaceEquipo()) setDialogo("acerca");
    };
    window.addEventListener("hashchange", enlace);
    return () => window.removeEventListener("hashchange", enlace);
  }, []);

  useEffect(() => {
    const tecla = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (dialogo) setDialogo(null); else if (seleccionado) setSeleccionado(null); else setDiagnosticado(null);
    };
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [dialogo, seleccionado]);

  const cambiarModo = useCallback((m: Modo) => {
    setPestana(m);
    setPanelAbierto(true);
    setClasesFijadas(new Set()); // grupos y situaciones no se comparten entre modos
    setClaseResaltada(null);
  }, []);
  const elegirModo = useCallback((m: Modo) => {
    if (m === pestana) return setPanelAbierto((a) => !a);
    cambiarModo(m);
  }, [pestana, cambiarModo]);

  // ---------------------------------------------------------- dónde actuar
  useEffect(() => {
    if (!datos || pestana !== "actuar" || diagnostico) return;
    let vigente = true;
    setErrorDiagnostico(false);
    api.diagnostico().then((d) => vigente && setDiagnostico(d)).catch(() => vigente && setErrorDiagnostico(true));
    return () => { vigente = false; };
  }, [datos, pestana, diagnostico]);

  const situacionesMapa = useMemo(
    () => (pestana === "actuar" && diagnostico && datos ? situacionesActuar(diagnostico, datos.municipios) : situaciones),
    [pestana, diagnostico, datos, situaciones]);

  // En «Dónde actuar», elegir un municipio (mapa, buscador, lista) abre su diagnóstico en el panel; la ficha completa,
  // si ya está abierta, le sigue. Madrid capital no tiene diagnóstico (es la referencia): abre su ficha.
  const diagnosticar = useCallback((i: string | null) => {
    if (i && diagnostico && !diagnostico.municipios.some((m) => m.ine5 === i)) return setSeleccionado(i);
    setDiagnosticado(i);
    if (i) setPanelAbierto(true);
    if (i && seleccionado) setSeleccionado(i);
  }, [diagnostico, seleccionado]);
  const seleccionar = pestana === "actuar" ? diagnosticar : setSeleccionado;

  const elegirCuadrante = useCallback((id: IdCuadrante) => setClasesFijadas((s) =>
    (s.size === 1 && s.has(id) ? new Set<string>() : new Set<string>([id]))), []);

  // «Ver su perfil en la red»: explorar perfiles con los estados de los padres del objetivo de ese municipio
  const verPerfil = useCallback((ine5: string) => {
    if (!datos) return;
    const estados = datos.municipios.find((m) => m.ine5 === ine5)?.estados ?? {};
    setEvidencia(Object.fromEntries(datos.meta.padres_objetivo.filter((n) => estados[n]).map((n) => [n, estados[n]])));
    cambiarModo("perfiles");
  }, [datos, cambiarModo]);

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
    // recorrido: en cada parada solo queda en pie ese municipio (se levanta al llegar la cámara); al empezar y al
    // terminar, los cinco
    if (recorrido) return new Set(destacado ? [destacado] : recorrido.paradas.map((p) => p.ine5));
    // actuar: lo que cae fuera del ámbito o de las situaciones elegidas se atenúa
    if (pestana === "actuar") {
      if (!diagnostico || (ambito === AMBITO_TODO && clasesVisibles.size === 0)) return null;
      return new Set(diagnostico.municipios.filter((m) => enAmbito(m, ambito)
        && (clasesVisibles.size === 0 || clasesVisibles.has(m.cuadrante))).map((m) => m.ine5));
    }
    if (pestana === "perfiles" && consulta && Object.keys(evidencia).length > 0)
      return new Set(consulta.municipios.map((m) => m.ine5));
    if (clasesVisibles.size > 0)
      return new Set([...situaciones].filter(([, s]) => clasesVisibles.has(s.clase.id)).map(([i]) => i));
    return null;
  }, [pestana, consulta, evidencia, clasesVisibles, situaciones, recorrido, destacado, diagnostico, ambito]);

  const etiquetas = useMemo(() => {
    if (recorrido) return recorrido.paradas.map((p) => p.ine5);
    // los cinco mejores de lo que se ve: de todos, o solo de los grupos resaltados o fijados
    // en actuar, los cinco con más necesidad de lo que se ve (la posición ordena por necesidad)
    const top = pestana === "decidir" || pestana === "actuar"
      ? [...situacionesMapa].filter(([i, s]) => s.posicion !== null && (pestana === "actuar"
        ? !resaltados || resaltados.has(i) : clasesVisibles.size === 0 || clasesVisibles.has(s.clase.id)))
        .sort((a, b) => a[1].posicion! - b[1].posicion!).slice(0, 5).map(([i]) => i) : [];
    const elegido = seleccionado ?? (pestana === "actuar" ? diagnosticado : null);
    return elegido ? [...top.filter((i) => i !== elegido), elegido] : top;
  }, [situacionesMapa, seleccionado, diagnosticado, pestana, clasesVisibles, recorrido, resaltados]);

  const porIne = useMemo(() => new Map(datos?.municipios.map((m) => [m.ine5, m])), [datos]);

  if (error && !datos) return <div className="pantalla-aviso"><Marca /><p>{error}</p></div>;
  // La intro tapa la carga; cuando entra el carmesí de la bandera se monta la app por debajo
  const pantallaIntro = intro !== "fin" && (
    <Intro listo={!!datos && !!ranking} mapa={mando} contorno={datos?.geometria.contorno ?? null} onRevelar={() => setIntro("revelando")} onFin={() => setIntro("fin")} />);
  if (!datos || !ranking || intro === "carga") return pantallaIntro;
  const izquierda = panelAbierto ? IZQ_PANEL : IZQ_SIN_PANEL;

  return (<>
    <div className={`app${seleccionado ? " con-ficha" : ""}${intro !== "fin" ? " intro-activa" : ""}${recorrido ? " recorriendo" : ""}`}
      style={{ ["--izq" as string]: `${izquierda}px` }}>
      <Mapa geometria={datos.geometria} situaciones={situacionesMapa}
        seleccionado={seleccionado ?? (pestana === "actuar" ? diagnosticado : null)} destacado={destacado}
        resaltados={resaltados} etiquetas={etiquetas} onSeleccionar={seleccionar} onPasar={setPasando}
        onCamara={setCamara} onMando={setMando} entrar={intro === "fin"}
        margenes={{ izquierda: izquierda, derecha: seleccionado ? ANCHO_FICHA + 32 : 0 }} />

      <Navegacion modo={pestana} abierto={panelAbierto} onModo={elegirModo} onDialogo={setDialogo} />
      <aside className={`panel${panelAbierto ? "" : " plegado"}`} style={{ width: ANCHO_PANEL, left: 16 + ANCHO_NAV + 8 }}>
        <Marca />
        <Buscador municipios={datos.municipios} onSeleccionar={seleccionar} />
        <h2 className="panel-titulo">{TITULOS[pestana]}</h2>
        <div className="panel-desplazable" key={pestana}>
          {pestana === "decidir"
            ? <PanelDecidir meta={datos.meta} peticion={peticion} onPeticion={cambiarPeticion}
                onAsistente={aplicarAsistente} onDeshacerAsistente={deshacerAsistente} pesos={ranking.pesos} municipios={datos.municipios}
                situaciones={situaciones} cambios={cambios} onCerrarCambios={() => setCambios(null)}
                onSeleccionar={setSeleccionado} onResaltarClase={setClaseResaltada} seleccionado={seleccionado} />
            : pestana === "actuar"
            ? <PanelActuar diagnostico={diagnostico} error={errorDiagnostico} ambito={ambito} onAmbito={setAmbito}
                fijados={clasesFijadas} onElegirCuadrante={elegirCuadrante} onResaltarCuadrante={setClaseResaltada}
                diagnosticado={diagnosticado} onDiagnosticar={diagnosticar} onPerfil={verPerfil} onFicha={setSeleccionado} />
            : <PanelPerfiles meta={datos.meta} evidencia={evidencia} onEvidencia={setEvidencia} consulta={consulta}
                onSeleccionar={setSeleccionado} />}
        </div>
      </aside>
      <AvisoMapa onAcerca={() => setDialogo("acerca")} />

      {seleccionado && (
        <Ficha ficha={ficha?.ine5 === seleccionado ? ficha : null} cargando={false}
          situacion={situaciones.get(seleccionado)} meta={datos.meta} pesos={ranking.pesos} peticion={peticion}
          negocio={negocio} onCerrar={() => setSeleccionado(null)} />
      )}

      <Leyenda resaltada={claseResaltada} fijadas={clasesFijadas} onResaltar={setClaseResaltada} onFijar={alternarClase}
        onLimpiar={() => setClasesFijadas(new Set())} modo={pestana} />
      <ControlesMapa camara={camara} mando={mando} />
      {pasando && <Etiqueta x={pasando.x} y={pasando.y} municipio={porIne.get(pasando.ine5)}
        situacion={situacionesMapa.get(pasando.ine5)}
        pista={pestana === "actuar" ? "Pulsa para ver su diagnóstico" : undefined} />}
      {error && <div className="brindis" role="status" onClick={() => setError(null)}>{error}</div>}
      {dialogo === "como" && <ComoFunciona meta={datos.meta} onCerrar={() => setDialogo(null)} />}
      {dialogo === "acerca" && <AcercaDe meta={datos.meta} onCerrar={() => setDialogo(null)} onComo={() => setDialogo("como")} />}
      {dialogo === "video" && <VentanaVideo onCerrar={() => setDialogo(null)} />}
      {viajes && <Viaje trayectos={viajes} onFin={() => setViajes(null)} />}
      {recorrido && mando && (
        <Recorrido key={recorrido.id} paradas={recorrido.paradas} mando={mando} meta={datos.meta} pesos={ranking.pesos}
          peticion={peticion} onDestacar={setDestacado} onAbrir={setSeleccionado} onFin={() => setRecorrido(null)} />
      )}
    </div>
    {pantallaIntro}
  </>);
}

// Una estrella por cada cosa entendida, hacia los municipios que suben de grupo (y si no sube ninguno, hacia los
// primeros del ranking), siempre que se vean en pantalla y no queden tapados por el panel o la ficha
function trayectosAsistente(lista: Cambio[], nuevas: Map<string, Situacion>, geometria: Geometria,
  mando: MandoMapa | null, conFicha: boolean): Trayecto[] {
  if (!mando || movimientoReducido()) return [];
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
    .filter(([x, y]) => x > IZQ_PANEL + 24 && x < derecha && y > 48 && y < innerHeight - 110)
    .slice(0, origenes.length);
  if (destinos.length === 0) return [];
  return origenes.map((o, k) => ({ x0: o.x, y0: o.y, x1: destinos[k % destinos.length][0], y1: destinos[k % destinos.length][1] }));
}

const movimientoReducido = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

// Paradas del recorrido: los primeros del ranking nuevo (Madrid capital nunca compite, así que no aparece)
function paradasRecorrido(nuevas: Map<string, Situacion>, datos: Datos): Parada[] {
  const rasgos = new Map(datos.geometria.features.map((f) => [f.properties.ine5, f.properties]));
  return [...nuevas].filter(([i, s]) => s.posicion !== null && rasgos.has(i))
    .sort((a, b) => a[1].posicion! - b[1].posicion!).slice(0, TOP_RECORRIDO)
    .map(([i, s]) => ({ ine5: i, municipio: rasgos.get(i)!.municipio, clase: s.clase, centro: rasgos.get(i)!.centro }));
}

function enlaceFicha(): string | null {
  return location.hash.match(/^#(\d{5})$/)?.[1] ?? null;
}

// Enlace para compartir (portfolio, tarjeta): abre «Acerca de» con el equipo
const enlaceEquipo = () => location.hash === "#equipo";

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
