// Elementos alrededor del mapa: marca, buscador, leyenda, controles de cámara, etiqueta flotante y
// la explicación de cómo se decide.
import { useEffect, useMemo, useRef, useState } from "react";
import type { Meta, Municipio } from "../api";
import { CLASES, FILTRADO, FUERA, type Situacion } from "../modelo";
import type { Camara, MandoMapa } from "./Mapa";
import { nombreLegible } from "./Ficha";
import { Bandera, Cerrar, Columna } from "./piezas";

export function Marca({ onAyuda }: { onAyuda: () => void }) {
  return (
    <header className="marca">
      <div className="marca-texto">
        <Bandera />
        <h1>Madrid <span>179</span></h1>
      </div>
      <p>Dónde abrir una oficina en los 179 municipios de la Comunidad de Madrid</p>
      <button className="boton-ayuda" onClick={onAyuda}>Cómo se decide</button>
    </header>
  );
}

const DATATHON = "https://datathon-mad.sel.inf.uc3m.es/";
const REPOSITORIO = "https://github.com/GF3000/madrid-179";

// Pie del panel: deja claro que la herramienta no es oficial y enlaza el datathon y el código
export function Pie() {
  return (
    <footer className="pie">
      <p><b>Herramienta no oficial.</b> No está vinculada ni avalada por la Comunidad de Madrid. Los resultados son
        orientativos y salen de datos abiertos.</p>
      <p>
        Proyecto para el <a href={DATATHON} target="_blank" rel="noreferrer">MAD Open Data Challenge 2026</a>
        {" · "}<span className="sin-partir"><a href={REPOSITORIO} target="_blank" rel="noreferrer">Código y fuentes</a> (MIT)</span>
      </p>
    </footer>
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

export function Leyenda({ resaltada, onResaltar, modo }: {
  resaltada: string | null; onResaltar: (c: string | null) => void; modo: "decidir" | "perfiles";
}) {
  return (
    <div className="leyenda" onMouseLeave={() => onResaltar(null)}>
      <span className="leyenda-titulo">{modo === "perfiles" ? "Con este perfil" : "Condiciones para una oficina"}</span>
      <div className="leyenda-clases">
        {[...CLASES, FILTRADO, FUERA].map((c) => (
          <button key={c.id} className={resaltada === c.id ? "activa" : ""} onMouseEnter={() => onResaltar(c.id)}
            onFocus={() => onResaltar(c.id)} onBlur={() => onResaltar(null)} title={c.resumen}>
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

export function Etiqueta({ x, y, municipio, situacion }: {
  x: number; y: number; municipio: Municipio | undefined; situacion: Situacion | undefined;
}) {
  if (!municipio || !situacion) return null;
  return (
    <div className="etiqueta" style={{ transform: `translate(${x + 14}px, ${y + 14}px)` }}>
      <strong>{nombreLegible(municipio.municipio)}</strong>
      <span><Columna clase={situacion.clase} /> {situacion.clase.nombre}</span>
      <em>Pulsa para ver por qué</em>
    </div>
  );
}

export function ComoFunciona({ meta, onCerrar }: { meta: Meta; onCerrar: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.focus();
  }, []);
  return (
    <div className="velo" onClick={onCerrar}>
      <div className="dialogo" role="dialog" aria-modal aria-labelledby="titulo-como" tabIndex={-1} ref={ref}
        onClick={(e) => e.stopPropagation()}>
        <div className="dialogo-cabecera">
          <h2 id="titulo-como">Cómo se decide</h2>
          <Cerrar onClick={onCerrar} />
        </div>
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
                (un asistente lo traduce al momento y puedes deshacerlo). Las condiciones del municipio siguen decidiendo al menos la
                mitad, y el mapa muestra qué municipios suben o bajan de grupo y por qué.</p>
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
      </div>
    </div>
  );
}

function fecha(t: string) {
  const d = new Date(t);
  return isNaN(d.getTime()) ? t : d.toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });
}
