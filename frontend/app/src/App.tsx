import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { api, type Consulta, type Ficha as TFicha, type Geometria, type Interpretacion, type Meta, type Municipio, type Negocio,
  type Peticion, type Ranking } from "./api";
import { clasificar, describirFiltro, FILTROS_VACIOS, palabraImportancia, type Situacion } from "./modelo";
import Mapa, { type Camara, type MandoMapa } from "./componentes/Mapa";
import Ficha from "./componentes/Ficha";
import PanelDecidir, { type Cambio } from "./componentes/PanelDecidir";
import PanelPerfiles from "./componentes/PanelPerfiles";
import Intro from "./componentes/Intro";
import Viaje, { DURACION_VIAJE, origenesTarjeta, type Trayecto } from "./componentes/Viaje";
import Recorrido, { huecoTarjetaMovil, type Parada } from "./componentes/Recorrido";
import { Buscador, ComoFunciona, ControlesMapa, Etiqueta, Leyenda, Marca, Pie } from "./componentes/Contorno";
import Asa from "./componentes/Asa";
import { esMovil, useEsMovil } from "./movil";

const PETICION_INICIAL: Peticion = { preferencias: {}, filtros: FILTROS_VACIOS };
const ANCHO_PANEL = 392;
const ANCHO_FICHA = 432;
const TOP_RECORRIDO = 5; // municipios que visita el recorrido tras el asistente
// Móvil: el panel es una hoja inferior plegada (marca, buscador y pestañas), media o casi completa; la ficha, otra hoja
// encima. Fracciones del alto de la ventana
const HOJA_MEDIA = 0.55;
const HOJA_COMPLETA = 0.92;
const FICHA_MEDIA = 0.7;

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
  const [recorrido, setRecorrido] = useState<{ id: number; paradas: Parada[] } | null>(null);
  const [destacado, setDestacado] = useState<string | null>(null); // parada actual del recorrido
  const desdeAsistente = useRef(false); // el próximo ranking viene del asistente: estrellas de la tarjeta al mapa
  const mandoRef = useRef(mando);
  mandoRef.current = mando;
  const seleccionadoRef = useRef(seleccionado);
  seleccionadoRef.current = seleccionado;
  const previa = useRef<Map<string, Situacion> | null>(null);
  const motivo = useRef("");

  // ------------------------------------------------------ móvil: hojas inferiores
  const movil = useEsMovil();
  const [hoja, setHoja] = useState(0); // panel: 0 plegada · 1 media · 2 completa
  const [hojaFicha, setHojaFicha] = useState(0); // ficha: 0 media · 1 completa
  const [alto, setAlto] = useState(() => innerHeight);
  const [plegada, setPlegada] = useState(180); // px hasta el pie de las pestañas, medido
  const appRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLElement>(null);
  const fichaRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const medir = () => setAlto(innerHeight);
    window.addEventListener("resize", medir);
    return () => window.removeEventListener("resize", medir);
  }, []);
  const alturasPanel = useMemo(() => {
    const media = Math.max(plegada + 60, Math.round(alto * HOJA_MEDIA));
    return [plegada, media, Math.max(media + 40, Math.round(alto * HOJA_COMPLETA))];
  }, [plegada, alto]);
  const alturasFicha = useMemo(() => [Math.round(alto * FICHA_MEDIA), Math.round(alto * HOJA_COMPLETA)], [alto]);
  // px tapados por abajo: la tarjeta del recorrido, la ficha o el panel (lo que esté delante)
  const abajo = !movil ? 0 : recorrido ? huecoTarjetaMovil(alto) : seleccionado ? alturasFicha[hojaFicha] : alturasPanel[hoja];
  const abajoRef = useRef(abajo);
  abajoRef.current = abajo;
  // --abajo en .app coloca la leyenda encima de la hoja; durante un arrastre lo mueve el asa sin pasar por React
  const moverAbajo = useCallback((px: number) => appRef.current?.style.setProperty("--abajo", `${Math.round(px)}px`), []);
  useLayoutEffect(() => { if (movil) moverAbajo(abajo); else appRef.current?.style.removeProperty("--abajo"); });

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
    if (esMovil()) { // fuera el teclado y la hoja a media altura: que se vean el mapa, las estrellas y el recorrido
      (document.activeElement as HTMLElement | null)?.blur();
      setHoja(1);
    }
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
          ? trayectosAsistente(lista, nuevas, datos.geometria, mandoRef.current,
            zonaVisible(seleccionadoRef.current !== null, abajoRef.current)) : [];
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

  // Móvil: al abrir una ficha, su hoja empieza a media altura y el panel deja de ocupar casi toda la pantalla
  useEffect(() => {
    if (!movil || !seleccionado) return;
    setHojaFicha(0);
    setHoja((h) => Math.min(h, 1));
  }, [seleccionado, movil]);

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
    // recorrido: en cada parada solo queda en pie ese municipio (se levanta al llegar la cámara); al empezar y al
    // terminar, los cinco
    if (recorrido) return new Set(destacado ? [destacado] : recorrido.paradas.map((p) => p.ine5));
    if (pestana === "perfiles" && consulta && Object.keys(evidencia).length > 0)
      return new Set(consulta.municipios.map((m) => m.ine5));
    if (clasesVisibles.size > 0)
      return new Set([...situaciones].filter(([, s]) => clasesVisibles.has(s.clase.id)).map(([i]) => i));
    return null;
  }, [pestana, consulta, evidencia, clasesVisibles, situaciones, recorrido, destacado]);

  const etiquetas = useMemo(() => {
    if (recorrido) return recorrido.paradas.map((p) => p.ine5);
    // los cinco mejores de lo que se ve: de todos, o solo de los grupos resaltados o fijados
    const top = pestana === "decidir"
      ? [...situaciones].filter(([, s]) => s.posicion !== null && (clasesVisibles.size === 0 || clasesVisibles.has(s.clase.id)))
        .sort((a, b) => a[1].posicion! - b[1].posicion!).slice(0, 5).map(([i]) => i) : [];
    return seleccionado ? [...top.filter((i) => i !== seleccionado), seleccionado] : top;
  }, [situaciones, seleccionado, pestana, clasesVisibles, recorrido]);

  const porIne = useMemo(() => new Map(datos?.municipios.map((m) => [m.ine5, m])), [datos]);

  // Altura plegada: justo hasta el pie de las pestañas (más el margen seguro de abajo)
  const montada = !!datos && !!ranking && intro !== "carga";
  useLayoutEffect(() => {
    const panel = panelRef.current;
    const nav = panel?.querySelector<HTMLElement>(".pestanas");
    if (!movil || !panel || !nav) return;
    setPlegada(Math.round(nav.offsetTop + nav.offsetHeight + parseFloat(getComputedStyle(panel).paddingBottom || "0") + 4));
  }, [movil, montada, alto]);

  if (error && !datos) return <div className="pantalla-aviso"><Marca onAyuda={() => undefined} /><p>{error}</p></div>;
  // La intro tapa la carga; cuando entra el carmesí de la bandera se monta la app por debajo
  const pantallaIntro = intro !== "fin" && (
    <Intro listo={!!datos && !!ranking} mapa={mando} contorno={datos?.geometria.contorno ?? null} onRevelar={() => setIntro("revelando")} onFin={() => setIntro("fin")} />);
  if (!datos || !ranking || intro === "carga") return pantallaIntro;

  const fichaEl = seleccionado && (
    <Ficha ficha={ficha?.ine5 === seleccionado ? ficha : null} cargando={false}
      situacion={situaciones.get(seleccionado)} meta={datos.meta} pesos={ranking.pesos} peticion={peticion}
      negocio={negocio} onCerrar={() => setSeleccionado(null)} />);
  // En móvil, cambiar de pestaña con la hoja plegada la abre para ver el contenido
  const elegirPestana = (p: "decidir" | "perfiles") => {
    setPestana(p);
    if (movil) setHoja((h) => Math.max(h, 1));
  };

  return (<>
    <div ref={appRef} className={`app${seleccionado ? " con-ficha" : ""}${intro !== "fin" ? " intro-activa" : ""}${recorrido ? " recorriendo" : ""}${movil ? ` hoja-${NOMBRES_HOJA[hoja]}` : ""}`}>
      <Mapa geometria={datos.geometria} situaciones={situaciones} seleccionado={seleccionado} destacado={destacado}
        resaltados={resaltados} etiquetas={etiquetas} onSeleccionar={setSeleccionado} onPasar={setPasando}
        onCamara={setCamara} onMando={setMando} entrar={intro === "fin"}
        margenes={movil ? { izquierda: 0, derecha: 0, abajo }
          : { izquierda: ANCHO_PANEL + 32, derecha: seleccionado ? ANCHO_FICHA + 32 : 0 }} />

      <aside className="panel" ref={panelRef} style={movil ? undefined : { width: ANCHO_PANEL }}
        onFocus={movil ? (e) => { if ((e.target as HTMLElement).matches("input, textarea")) setHoja(2); } : undefined}>
        {movil && <Asa hoja={panelRef} alturas={alturasPanel} indice={hoja} onIndice={setHoja} onMover={moverAbajo}
          etiqueta={hoja < 2 ? "Ampliar el panel" : "Plegar el panel"} />}
        <Marca onAyuda={() => setAyuda(true)} />
        <Buscador municipios={datos.municipios} onSeleccionar={setSeleccionado} />
        <nav className="pestanas" style={{ ["--i" as string]: pestana === "decidir" ? 0 : 1 }}>
          <span className="pestanas-cursor" aria-hidden />
          <button className={pestana === "decidir" ? "activa" : ""} onClick={() => elegirPestana("decidir")}>Dónde abrir</button>
          <button className={pestana === "perfiles" ? "activa" : ""} onClick={() => elegirPestana("perfiles")}>Explorar perfiles</button>
        </nav>
        <div className="panel-desplazable" key={pestana}>
          {pestana === "decidir"
            ? <PanelDecidir meta={datos.meta} peticion={peticion} onPeticion={cambiarPeticion}
                onAsistente={aplicarAsistente} onDeshacerAsistente={deshacerAsistente} pesos={ranking.pesos} municipios={datos.municipios}
                situaciones={situaciones} cambios={cambios} onCerrarCambios={() => setCambios(null)}
                onSeleccionar={setSeleccionado} onResaltarClase={setClaseResaltada} seleccionado={seleccionado} />
            : <PanelPerfiles meta={datos.meta} evidencia={evidencia} onEvidencia={setEvidencia} consulta={consulta}
                onSeleccionar={setSeleccionado} />}
          {movil && <Pie />}
        </div>
        {!movil && <Pie />}
      </aside>

      {seleccionado && (movil
        ? <div className="hoja-ficha" ref={fichaRef}>
            <Asa hoja={fichaRef} alturas={alturasFicha} indice={hojaFicha} onIndice={setHojaFicha} onMover={moverAbajo}
              onCerrar={() => setSeleccionado(null)} etiqueta={hojaFicha === 0 ? "Ampliar la ficha" : "Reducir la ficha"} />
            {fichaEl}
          </div>
        : fichaEl)}

      <Leyenda resaltada={claseResaltada} fijadas={clasesFijadas} onResaltar={setClaseResaltada} onFijar={alternarClase}
        onLimpiar={() => setClasesFijadas(new Set())} modo={pestana} />
      <ControlesMapa camara={camara} mando={mando} />
      {pasando && <Etiqueta x={pasando.x} y={pasando.y} municipio={porIne.get(pasando.ine5)}
        situacion={situaciones.get(pasando.ine5)} abajo={abajo} />}
      {error && <div className="brindis" role="status" onClick={() => setError(null)}>{error}</div>}
      {ayuda && <ComoFunciona meta={datos.meta} onCerrar={() => setAyuda(false)} />}
      {viajes && <Viaje trayectos={viajes} onFin={() => setViajes(null)} />}
      {recorrido && mando && (
        <Recorrido key={recorrido.id} paradas={recorrido.paradas} mando={mando} meta={datos.meta} pesos={ranking.pesos}
          peticion={peticion} onDestacar={setDestacado} onAbrir={setSeleccionado} onFin={() => setRecorrido(null)} />
      )}
    </div>
    {pantallaIntro}
  </>);
}

const NOMBRES_HOJA = ["plegada", "media", "completa"];

// Zona del mapa que se ve (px de ventana): en escritorio, entre el panel y la ficha; en móvil, entre los controles de
// arriba y la leyenda que va encima de la hoja inferior
interface Zona { izq: number; der: number; arriba: number; abajo: number }
function zonaVisible(conFicha: boolean, tapadoAbajo: number): Zona {
  return esMovil()
    ? { izq: 12, der: innerWidth - 12, arriba: 64, abajo: innerHeight - tapadoAbajo - 64 }
    : { izq: ANCHO_PANEL + 56, der: innerWidth - (conFicha ? ANCHO_FICHA + 48 : 48), arriba: 48, abajo: innerHeight - 110 };
}

// Una estrella por cada cosa entendida, hacia los municipios que suben de grupo (y si no sube ninguno, hacia los
// primeros del ranking), siempre que se vean en pantalla y no queden tapados por el panel o la ficha
function trayectosAsistente(lista: Cambio[], nuevas: Map<string, Situacion>, geometria: Geometria,
  mando: MandoMapa | null, zona: Zona): Trayecto[] {
  if (!mando || movimientoReducido()) return [];
  let origenes = origenesTarjeta();
  if (esMovil()) { // en la hoja, solo las etiquetas que se ven dentro de su zona desplazable
    const caja = document.querySelector(".panel-desplazable")?.getBoundingClientRect();
    origenes = caja ? origenes.filter((o) => o.y > caja.top && o.y < caja.bottom) : [];
  }
  if (origenes.length === 0) return [];
  const suben = lista.filter((c) => c.despues.orden < c.antes.orden)
    .sort((a, b) => a.despues.orden - b.despues.orden || (nuevas.get(a.ine5)?.posicion ?? 999) - (nuevas.get(b.ine5)?.posicion ?? 999))
    .map((c) => c.ine5);
  const primeros = [...nuevas].filter(([, s]) => s.posicion !== null)
    .sort((a, b) => a[1].posicion! - b[1].posicion!).map(([i]) => i);
  const centros = new Map(geometria.features.map((f) => [f.properties.ine5, f.properties.centro]));
  const elegidos = [...new Set([...suben, ...primeros])].filter((i) => centros.has(i)).slice(0, 40);
  const destinos = mando.proyectar(elegidos.map((i) => centros.get(i)!))
    .filter(([x, y]) => x > zona.izq && x < zona.der && y > zona.arriba && y < zona.abajo)
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
