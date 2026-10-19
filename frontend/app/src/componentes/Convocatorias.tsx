// Convocatorias abiertas para pymes y autónomos (BDNS, revisadas una a una): contexto, no puntúan.
// Tras el asistente, las que encajan con el negocio descrito; en la ficha, las restringidas al tamaño del municipio.
import { useEffect, useState } from "react";
import { api, type Convocatoria, type Convocatorias } from "../api";

let cache: Promise<Convocatorias | null> | null = null;
const cargar = () => (cache ??= api.convocatorias().catch(() => null)); // sin tabla en el servidor: se oculta

function plazo(c: Convocatoria) {
  if (!c.fin_solicitud) return c.nota ?? "Plazo: consulta las bases";
  const d = new Date(c.fin_solicitud);
  const txt = isNaN(d.getTime()) ? c.fin_solicitud : d.toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });
  return `Hasta el ${txt}`;
}

export function ListaConvocatorias({ lista }: { lista: Convocatoria[] }) {
  return (
    <ul className="convocatorias">
      {lista.map((c) => (
        <li key={c.num}>
          <a className="enlace" href={c.url} target="_blank" rel="noopener noreferrer">{c.titulo}</a>
          <small>{c.nivel} · {plazo(c)}</small>
        </li>
      ))}
    </ul>
  );
}

// Primero las que cierran antes (con fecha), luego las de plazo sin fecha
const orden = (a: Convocatoria, b: Convocatoria) =>
  (a.fin_solicitud ?? "9999").localeCompare(b.fin_solicitud ?? "9999");

export function ConvocatoriasNegocio({ perfiles }: { perfiles: string[] }) {
  const [datos, setDatos] = useState<Convocatorias | null>(null);
  const [todas, setTodas] = useState(false);
  useEffect(() => { cargar().then(setDatos); }, []);
  if (!datos || perfiles.length === 0) return null;
  const encajan = datos.convocatorias.filter((c) => c.perfiles.some((p) => perfiles.includes(p))).sort(orden);
  if (encajan.length === 0) return null;
  const vistas = todas ? encajan : encajan.slice(0, 4);
  return (
    <div className="convocatorias-negocio">
      <h4>Ayudas abiertas que encajan con tu negocio</h4>
      <p className="nota">Por lo que nos has contado: {perfiles.map((p) => datos.perfiles[p]?.toLowerCase() ?? p).join(", ")}.
        Valen para cualquier municipio.</p>
      <ListaConvocatorias lista={vistas} />
      {encajan.length > vistas.length && (
        <button className="enlace" onClick={() => setTodas(true)}>Ver las {encajan.length}</button>
      )}
      <small className="convocatorias-aviso">{datos.aviso}</small>
    </div>
  );
}

// En la ficha: las generales valen para cualquier municipio. Con negocio descrito, las que le encajan; si no, todas.
export function ConvocatoriasGenerales({ perfiles }: { perfiles: string[] }) {
  const [datos, setDatos] = useState<Convocatorias | null>(null);
  useEffect(() => { cargar().then(setDatos); }, []);
  if (!datos || datos.convocatorias.length === 0) return null;
  const filtrar = perfiles.length > 0;
  const lista = (filtrar ? datos.convocatorias.filter((c) => c.perfiles.some((p) => perfiles.includes(p))) : [...datos.convocatorias])
    .sort(orden);
  if (lista.length === 0) return null;
  return (
    <details className="convocatorias-generales">
      <summary>
        {filtrar
          ? <>Además, <b>{lista.length} ayudas estatales y de la Comunidad abiertas</b> que encajan con tu negocio, aquí y en cualquier municipio</>
          : <>Además, <b>{lista.length} convocatorias abiertas</b> para pymes y autónomos en toda la Comunidad</>}
      </summary>
      {!filtrar && <p className="nota">Describe tu negocio en «Cuéntanos tu negocio» para ver solo las que te encajan.</p>}
      <ListaConvocatorias lista={lista} />
      <small className="convocatorias-aviso">{datos.aviso}</small>
    </details>
  );
}
