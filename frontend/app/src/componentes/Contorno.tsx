// Elementos alrededor del mapa: marca, aviso, buscador, leyenda, controles de cámara, etiqueta flotante y
// los diálogos «Cómo se decide», «Acerca de» y el vídeo.
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { Meta, Municipio } from "../api";
import { CLASES, CUADRANTES, FILTRADO, FUERA, pesoMinimoModelo, type Situacion } from "../modelo";
import type { Camara, MandoMapa } from "./Mapa";
import type { Modo } from "./Navegacion";
import { nombreLegible } from "./Ficha";
import { VIDEO } from "./Navegacion";
import { Bandera, Cerrar, Columna } from "./piezas";

export function Marca() {
  return (
    <header className="marca">
      <div className="marca-texto">
        <Bandera />
        <h1>Madrid <span>179</span></h1>
      </div>
      <p>Dónde abrir una oficina en los 179 municipios de la Comunidad de Madrid</p>
    </header>
  );
}

const DATATHON = "https://datathon-mad.sel.inf.uc3m.es/";
const REPOSITORIO = "https://github.com/GF3000/madrid-179";
const EN_REPOSITORIO = (ruta: string) => `${REPOSITORIO}/blob/main/${ruta}`;
// Correo de contacto público: vacío mientras el equipo no decida cuál (entonces solo se ofrece GitHub)
const CORREO = "";

// Equipo: aparece en «Acerca de» (enlace directo: /#equipo) y en el aviso sobre el mapa. Sin roles: el
// trabajo es de los dos. `github` y `foto` (en public/equipo/,
// cuadrada de 176 px) son opcionales: sin foto, las iniciales
const EQUIPO = [
  { nombre: "Gregorio García Velasco", corto: "Gregorio García", centro: "Universidad Carlos III de Madrid",
    linkedin: "https://www.linkedin.com/in/gregorio-garc%C3%ADa-velasco-481847265/", github: "", foto: "" },
  { nombre: "Guillermo Franco Gimeno", corto: "Guillermo Franco", centro: "Universidad Politécnica de Madrid",
    linkedin: "https://www.linkedin.com/in/guillermo-franco-gimeno-335256229/", github: "",
    foto: "/equipo/guillermo-franco.jpg" },
];

// Aviso permanente sobre el mapa, como una atribución: la herramienta no es oficial
export function AvisoMapa({ onAcerca }: { onAcerca: () => void }) {
  return (
    <p className="aviso-mapa">
      <b>Herramienta no oficial</b>, no vinculada a la Comunidad de Madrid · Hecha por{" "}
      <button className="enlace" onClick={onAcerca}>{EQUIPO.map((p) => p.corto).join(" y ")}</button>
    </p>
  );
}

const sinTildes = (t: string) => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

export function Buscador({ municipios, onSeleccionar }: { municipios: Municipio[]; onSeleccionar: (i: string) => void }) {
  const [texto, setTexto] = useState("");
  const [activo, setActivo] = useState(0);
  const lista = useMemo(() => municipios.map((m) => ({ ine5: m.ine5, nombre: nombreLegible(m.municipio) }))
    .sort((a, b) => a.nombre.localeCompare(b.nombre, "es")), [municipios]);
  const q = sinTildes(texto.trim());
  const res = q ? lista.filter((m) => sinTildes(m.nombre).includes(q)).slice(0, 7) : [];
  const elegir = (i: string) => {
    onSeleccionar(i);
    setTexto("");
  };
  return (
    <div className="buscador">
      <input value={texto} placeholder="Busca un municipio…" aria-label="Buscar municipio"
        onChange={(e) => { setTexto(e.target.value); setActivo(0); }}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown") setActivo((a) => Math.min(a + 1, res.length - 1));
          else if (e.key === "ArrowUp") setActivo((a) => Math.max(a - 1, 0));
          else if (e.key === "Enter" && res[activo]) elegir(res[activo].ine5);
          else if (e.key === "Escape") setTexto("");
        }} />
      <span className="lupa" aria-hidden />
      {res.length > 0 && (
        <ul className="sugerencias" role="listbox">
          {res.map((m, k) => (
            <li key={m.ine5} role="option" aria-selected={k === activo}>
              <button className={k === activo ? "activo" : ""} onMouseDown={() => elegir(m.ine5)}>{m.nombre}</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// Pasar el ratón por un grupo lo resalta en el mapa (vista previa); un clic lo fija y se pueden fijar varios.
// En «Dónde actuar», las cuatro situaciones del diagnóstico (la altura es la necesidad, no el grupo).
export function Leyenda({ resaltada, fijadas, onResaltar, onFijar, onLimpiar, modo }: {
  resaltada: string | null; fijadas: Set<string>; onResaltar: (c: string | null) => void;
  onFijar: (c: string) => void; onLimpiar: () => void; modo: Modo;
}) {
  const actuar = modo === "actuar";
  const clases = actuar ? [...Object.values(CUADRANTES), FUERA] : [...CLASES, FILTRADO, FUERA];
  const unidad = actuar ? ["situación", "situaciones"] : ["grupo", "grupos"];
  return (
    <div className={`leyenda${fijadas.size > 0 ? " con-fijadas" : ""}`} onMouseLeave={() => onResaltar(null)}>
      {fijadas.size > 0
        ? <button className="leyenda-titulo leyenda-quitar" onClick={onLimpiar} title={actuar ? "Volver a ver todas las situaciones" : "Volver a ver todos los grupos"}>
            Solo {fijadas.size === 1 ? `1 ${unidad[0]}` : `${fijadas.size} ${unidad[1]}`}<span>{actuar ? "Ver todas" : "Ver todos"}</span>
          </button>
        : <span className="leyenda-titulo">{modo === "perfiles" ? "Con este perfil" : actuar ? "Situación del municipio" : "Condiciones para una oficina"}</span>}
      <div className="leyenda-clases">
        {clases.map((c) => (
          <button key={c.id} className={`${resaltada === c.id ? "activa" : ""}${fijadas.has(c.id) ? " fijada" : ""}`}
            aria-pressed={fijadas.has(c.id)} onMouseEnter={() => onResaltar(c.id)} onClick={() => onFijar(c.id)}
            onFocus={() => onResaltar(c.id)} onBlur={() => onResaltar(null)}
            title={`${c.resumen} ${fijadas.has(c.id) ? `Clic para dejar de mostrar solo ${actuar ? "esta" : "este"} ${unidad[0]}.` : `Clic para mostrar solo ${actuar ? "esta" : "este"} ${unidad[0]}.`}`}>
            <Columna clase={c} />
            <span>{c.nombre}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function ControlesMapa({ camara, mando }: { camara: Camara; mando: MandoMapa | null }) {
  if (!mando) return null;
  const en3d = camara.inclinacion > 10;
  return (
    <div className="controles">
      <button className="brujula" onClick={mando.norte} title="Orientar al norte" aria-label="Orientar al norte">
        <svg viewBox="0 0 40 40" style={{ transform: `rotate(${-camara.rumbo}deg)` }} aria-hidden>
          <path d="M20 5 L25 20 L20 18 L15 20Z" className="aguja-n" />
          <path d="M20 35 L15 20 L20 22 L25 20Z" className="aguja-s" />
          <text x="20" y="4.2" textAnchor="middle">N</text>
        </svg>
      </button>
      <div className="controles-grupo">
        <button onClick={() => mando.girar(-30)} aria-label="Girar a la izquierda"><span className="giro izq" aria-hidden /></button>
        <span className="controles-rotulo">Girar</span>
        <button onClick={() => mando.girar(30)} aria-label="Girar a la derecha"><span className="giro der" aria-hidden /></button>
      </div>
      <button onClick={mando.alternarVista}>{en3d ? "Vista en planta" : "Vista 3D"}</button>
      <button onClick={mando.recentrar}>Toda la región</button>
      <p className="pista">Arrastra con el botón derecho para girar e inclinar</p>
    </div>
  );
}

export function Etiqueta({ x, y, municipio, situacion, pista = "Pulsa para ver por qué" }: {
  x: number; y: number; municipio: Municipio | undefined; situacion: Situacion | undefined; pista?: string;
}) {
  if (!municipio || !situacion) return null;
  return (
    <div className="etiqueta" style={{ transform: `translate(${x + 14}px, ${y + 14}px)` }}>
      <strong>{nombreLegible(municipio.municipio)}</strong>
      <span><Columna clase={situacion.clase} /> {situacion.clase.nombre}</span>
      <em>{pista}</em>
    </div>
  );
}

// Diálogo modal: velo, foco al abrir y cabecera con el título y el aspa
function Ventana({ titulo, clase, onCerrar, children }: {
  titulo: string; clase?: string; onCerrar: () => void; children: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);
  return (
    <div className="velo" onClick={onCerrar}>
      <div className={`dialogo${clase ? ` ${clase}` : ""}`} role="dialog" aria-modal aria-labelledby="titulo-dialogo"
        tabIndex={-1} ref={ref} onClick={(e) => e.stopPropagation()}>
        <div className="dialogo-cabecera">
          <h2 id="titulo-dialogo">{titulo}</h2>
          <Cerrar onClick={onCerrar} />
        </div>
        {children}
      </div>
    </div>
  );
}

export function ComoFunciona({ meta, onCerrar }: { meta: Meta; onCerrar: () => void }) {
  return (
    <Ventana titulo="Cómo se decide" onCerrar={onCerrar}>
        <ol className="pasos">
          <li>
            <span className="paso-num">1</span>
            <div>
              <h3>Datos públicos de los 179 municipios</h3>
              <p>Población, renta, talento, coste inmobiliario, paro, transporte y servicios, de fuentes oficiales
                de la Comunidad de Madrid, el Catastro y datos abiertos como OpenStreetMap.</p>
            </div>
          </li>
          <li>
            <span className="paso-num">2</span>
            <div>
              <h3>Aprende de lo que ya pasó</h3>
              <p>El modelo observa en qué municipios creció más el número de empresas entre 2020 y 2024 y qué
                condiciones tenían en común. No adivina el futuro: compara cada municipio con el resto.</p>
            </div>
          </li>
          <li>
            <span className="paso-num">3</span>
            <div>
              <h3>Dos lecturas que se complementan</h3>
              <p><b>La tabla de factores</b> (un modelo aditivo, GA²M) suma lo que aporta cada rasgo y decide el
                grupo de cada municipio. <b>La red de causas</b> (una red bayesiana) explica de qué depende la
                viabilidad y permite explorar perfiles. Las dos se pueden revisar a mano, factor a factor.</p>
            </div>
          </li>
          <li>
            <span className="paso-num">4</span>
            <div>
              <h3>Tus prioridades, a la vista</h3>
              <p>Transporte, coste, tamaño, talento… los pones tú, a mano o contando tu negocio con tus palabras
                (un asistente lo traduce al momento y puedes deshacerlo). Las condiciones del municipio siguen pesando al menos{" "}
                {pesoMinimoModelo(meta.tope_preferencias)}, y el mapa muestra qué municipios suben o bajan de grupo y por qué.</p>
            </div>
          </li>
        </ol>
        <div className="comprobado">
          <h3>Cómo se ha comprobado</h3>
          <p>Se probó con municipios que el modelo no había visto: de los que sitúa en el tercio más favorable,
            casi dos de cada tres lo estaban de verdad, el doble que eligiendo al azar. Por eso mostramos
            <b> grupos</b> y <b>razones</b> en lugar de puntuaciones exactas: es una orientación sólida para
            comparar municipios, que conviene completar con el conocimiento del terreno.</p>
          <p className="nota">Los factores describen lo que acompaña al crecimiento empresarial; no garantizan que
            cambiarlos lo provoque. Modelo {meta.version_modelo} · entrenado el {fecha(meta.entrenado)}.</p>
        </div>
    </Ventana>
  );
}

export function AcercaDe({ meta, onCerrar, onComo }: { meta: Meta; onCerrar: () => void; onComo: () => void }) {
  const fuera = { target: "_blank", rel: "noreferrer" };
  return (
    <Ventana titulo="Acerca de Madrid 179" onCerrar={onCerrar}>
      {VIDEO && <Video />}
      <p className="acerca-entrada">
        Madrid 179 ayuda a decidir dónde abrir o trasladar una oficina entre los 179 municipios de la Comunidad de
        Madrid: compara las condiciones de cada municipio con tus prioridades y explica cada resultado con datos
        abiertos. Es nuestro proyecto para el <a href={DATATHON} {...fuera}>MAD Open Data Challenge 2026</a>.
      </p>
      <section className="equipo" id="equipo" aria-labelledby="titulo-equipo">
        <h3 id="titulo-equipo">Equipo</h3>
        <ul>
          {EQUIPO.map((p) => (
            <li key={p.nombre}>
              {p.foto
                ? <img className="equipo-foto" src={p.foto} alt="" width={44} height={44} loading="lazy" />
                : <span className="equipo-foto" aria-hidden>{p.nombre.split(" ").slice(0, 2).map((x) => x[0]).join("")}</span>}
              <div>
                <strong>{p.nombre}</strong>
                <span className="equipo-centro">{p.centro}</span>
                <span className="equipo-enlaces">
                  <a href={p.linkedin} {...fuera}>LinkedIn</a>
                  {p.github && <a href={p.github} {...fuera}>GitHub</a>}
                </span>
              </div>
            </li>
          ))}
        </ul>
        <p>
          ¿Una idea, un error o una pregunta? Escríbenos por LinkedIn o{" "}
          <a href={`${REPOSITORIO}/issues`} {...fuera}>abre una incidencia en GitHub</a>
          {CORREO && <>; también en <a href={`mailto:${CORREO}`}>{CORREO}</a></>}.
        </p>
      </section>
      <div className="acerca-secciones">
        <section>
          <h3>Transparencia</h3>
          <p>Cada número se puede rehacer a mano: el código, los datos derivados y los cálculos están publicados.</p>
          <ul className="acerca-enlaces">
            <li><button className="enlace" onClick={onComo}>Cómo se decide, en cuatro pasos</button></li>
            <li><a href={EN_REPOSITORIO("docs/informe/Aproximacion_tecnica_CAM.pdf")} {...fuera}>Aproximación técnica</a> (PDF)</li>
            <li><a href={EN_REPOSITORIO("docs/informe/Calculo_CPTs_CAM.pdf")} {...fuera}>La red bayesiana, calculada paso a paso</a> (PDF)</li>
            <li><a href={EN_REPOSITORIO("docs/informe/Fuentes_de_datos_CAM.pdf")} {...fuera}>Fuentes de datos</a> (PDF)</li>
            <li><a href="/docs" {...fuera}>API abierta</a> y <a href={REPOSITORIO} {...fuera}>código en GitHub</a></li>
          </ul>
        </section>
        <section>
          <h3>Datos y licencia</h3>
          <p>
            Datos abiertos de la Comunidad y el Ayuntamiento de Madrid, el INE, el Catastro, el Consorcio de
            Transportes, la BDNS y OpenStreetMap; cada conjunto conserva la licencia de su fuente
            (<a href={EN_REPOSITORIO("data/README.md")} {...fuera}>detalle</a>). Resúmenes de Wikipedia (CC BY-SA 4.0)
            y fotos de Wikimedia Commons con su autor. El código es libre, con <a href={EN_REPOSITORIO("LICENSE")} {...fuera}>licencia MIT</a>.
          </p>
        </section>
        <section className="acerca-aviso">
          <h3>Herramienta no oficial</h3>
          <p>
            No está vinculada ni avalada por la Comunidad de Madrid. Los resultados son orientativos: describen lo que
            acompañó al crecimiento empresarial entre 2020 y 2024, no garantizan lo que pasará.
          </p>
        </section>
      </div>
      <p className="nota acerca-version">Modelo {meta.version_modelo} · entrenado el {fecha(meta.entrenado)}</p>
    </Ventana>
  );
}

export function VentanaVideo({ onCerrar }: { onCerrar: () => void }) {
  return (
    <Ventana titulo="Madrid 179 en vídeo" clase="dialogo-video" onCerrar={onCerrar}>
      <Video />
    </Ventana>
  );
}

function Video() {
  return (
    <div className="video">
      <iframe src={VIDEO} title="Vídeo de presentación de Madrid 179" allowFullScreen
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" />
    </div>
  );
}

function fecha(t: string) {
  const d = new Date(t);
  return isNaN(d.getTime()) ? t : d.toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });
}
