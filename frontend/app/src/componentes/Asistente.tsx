// Asistente: el usuario describe su negocio y un LLM lo traduce en preferencias y requisitos del catálogo.
// Se aplica al mapa en cuanto llega; la tarjeta muestra lo entendido, se puede deshacer de un clic y todo queda
// en los controles para retocarlo.
import { useState } from "react";
import { api, type Filtros, type Interpretacion, type Meta } from "../api";
import { describirFiltro, palabraImportancia } from "../modelo";
import { ConvocatoriasNegocio } from "./Convocatorias";
import { EstrellasPensando } from "./piezas";

interface Props {
  meta: Meta;
  onAplicar: (i: Interpretacion) => void;
  onDeshacer: () => void;
}

const EJEMPLO = "Somos un estudio de diseño de 8 personas. Buscamos un alquiler moderado, que el equipo pueda llegar en tren y algo de ambiente con restaurantes cerca.";

export default function Asistente({ meta, onAplicar, onDeshacer }: Props) {
  const [texto, setTexto] = useState("");
  const [estado, setEstado] = useState<"reposo" | "pensando" | "listo" | "deshecho" | "error">("reposo");
  const [resultado, setResultado] = useState<Interpretacion | null>(null);
  const [inventando, setInventando] = useState(false);
  const nombres = new Map(meta.catalogo.map((p) => [p.clave, p]));

  const interpretar = async () => {
    if (texto.trim().length < 10) return;
    setEstado("pensando");
    try {
      const r = await api.interpretar(texto.trim());
      setResultado(r);
      setEstado("listo");
      if (Object.keys(r.preferencias).length > 0 || Object.keys(r.filtros).length > 0) onAplicar(r);
    } catch {
      setEstado("error");
    }
  };

  // Para probar la app sin escribir: el LLM inventa un negocio y lo deja en el cuadro, listo para interpretar
  const inventar = async () => {
    setInventando(true);
    try {
      setTexto((await api.ejemplo()).texto);
    } catch {
      setTexto(EJEMPLO);
    } finally {
      setInventando(false);
    }
  };

  const prefs = resultado ? Object.entries(resultado.preferencias) : [];
  const filtros = resultado ? Object.entries(resultado.filtros) as [keyof Filtros, number | boolean][] : [];
  const vacio = resultado && prefs.length === 0 && filtros.length === 0;

  return (
    <div className="bloque asistente">
      <h3>Cuéntanos tu negocio</h3>
      <div className={`asistente-caja${estado === "pensando" ? " pensando" : ""}`}>
        <textarea value={texto} rows={3} maxLength={2000} placeholder={EJEMPLO}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) interpretar(); }} />
        <div className="asistente-pie">
          <span className="nota">A qué te dedicas, cuántos sois y qué necesitáis.{" "}
            <button className="enlace" disabled={inventando || estado === "pensando"} onClick={inventar}>
              {inventando ? "Inventando…" : "Inventar un ejemplo"}
            </button>
          </span>
          <button className={`boton-primario${estado === "pensando" ? " leyendo" : ""}`}
            disabled={estado === "pensando" || texto.trim().length < 10} onClick={interpretar}
            aria-label={estado === "pensando" ? "Leyendo tu descripción" : undefined}>
            {estado === "pensando" ? <EstrellasPensando /> : "Interpretar"}
          </button>
        </div>
      </div>

      {estado === "error" && (
        <p className="nota asistente-aviso">No hemos podido leer la descripción ahora mismo. Puedes marcar lo que te importa
          justo debajo; el resultado es el mismo.</p>
      )}

      {(estado === "listo" || estado === "deshecho") && resultado && (
        <div className={`entendido${estado === "deshecho" ? " deshecho" : ""}`}>
          <h4>{vacio ? "No hemos encontrado preferencias" : estado === "deshecho" ? "Deshecho: esto es lo que habíamos entendido"
            : "Aplicado al mapa: esto es lo que hemos entendido"}</h4>
          {resultado.resumen && <p className="entendido-resumen">{resultado.resumen}</p>}
          {vacio && <p className="nota">No hemos encontrado preferencias concretas. Prueba a contar qué necesitáis: transporte,
            coste, tamaño del municipio, tipo de perfil que buscáis contratar…</p>}
          {prefs.length > 0 && (
            <ul className="entendido-lista">
              {prefs.map(([k, v]) => {
                const p = nombres.get(k);
                const sentido = p?.sentidos?.find((s) => s.valor === v.sentido)?.etiqueta;
                return (
                  <li key={k}>
                    <span className={`chip ${v.importancia === "Muy importante" ? "fuerte" : ""}`}>
                      {palabraImportancia(v.importancia)}
                    </span>
                    <span>
                      <b>{p?.nombre ?? k}</b>{sentido && <> · {sentido.toLowerCase()}</>}
                      {v.motivo && <small>{v.motivo}</small>}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
          {filtros.length > 0 && (
            <ul className="entendido-lista">
              {filtros.map(([k, v]) => (
                <li key={k}><span className="chip imprescindible">Imprescindible</span><span><b>{describirFiltro(k, v)}</b></span></li>
              ))}
            </ul>
          )}
          {estado === "listo" && <ConvocatoriasNegocio perfiles={resultado.perfiles_ayudas ?? []} />}
          {resultado.dudas.length > 0 && (
            <div className="dudas">
              <h4>Para afinar</h4>
              <ul>{resultado.dudas.map((d) => <li key={d}>{d}</li>)}</ul>
              <p className="nota">Responde en el texto y vuelve a interpretar, o ajústalo a mano debajo.</p>
            </div>
          )}
          <div className="entendido-acciones">
            <button className="enlace" onClick={() => { setResultado(null); setEstado("reposo"); }}>Cerrar</button>
            {!vacio && estado === "listo" && (
              <button className="boton-secundario" onClick={() => { onDeshacer(); setEstado("deshecho"); }}>Deshacer</button>
            )}
            {!vacio && estado === "deshecho" && (
              <button className="boton-primario" onClick={() => { onAplicar(resultado); setEstado("listo"); }}>Volver a aplicar</button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
