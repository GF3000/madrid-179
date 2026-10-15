// Ficha de un municipio: en qué grupo está y por qué, en lenguaje claro y sin cifras del modelo.
// Arriba, foto y resumen de Wikipedia (con sus créditos) y, si hay asistente, lo mejor y lo peor redactado por el
// LLM a partir de los mismos hechos que enseña la ficha.
import { useEffect, useState } from "react";
import { api, type Explicacion, type Ficha as TFicha, type Meta, type Peticion, type Wikipedia } from "../api";
import {
  factores, MOTIVOS, NODOS, nivel, palabraUtilidad, PALABRA_FUERZA, resumenFactores, type Factor, type Situacion,
} from "../modelo";
import { Cerrar, Columna, Escalones, MarcasFuerza, Reparto, Seccion } from "./piezas";

interface Props {
  ficha: TFicha | null;
  cargando: boolean;
  situacion: Situacion | undefined;
  meta: Meta;
  pesos: Record<string, number>;
  peticion: Peticion;
  onCerrar: () => void;
}

const num = (x: number) => x.toLocaleString("es-ES", { maximumFractionDigits: 0 });

export default function Ficha({ ficha, cargando, situacion, meta, pesos, peticion, onCerrar }: Props) {
  if (!ficha) {
    return (
      <aside className="ficha cargando" aria-busy>
        <div className="ficha-cabecera"><span className="sombra-texto ancho" /><Cerrar onClick={onCerrar} /></div>
        <span className="sombra-texto" /><span className="sombra-texto corto" />
      </aside>
    );
  }
  const clase = situacion?.clase;
  const fs = factores(ficha.ga2m.aportaciones, ficha.red.estados);
  const aFavor = fs.filter((f) => f.signo > 0 && !f.combinado).slice(0, 5);
  const enContra = fs.filter((f) => f.signo < 0 && !f.combinado).slice(0, 5);
  const combinados = fs.filter((f) => f.combinado).slice(0, 3);
  const prefActivas = Object.values(pesos).some((w) => w > 0);

  return (
    <aside className={`ficha${cargando ? " refrescando" : ""}`} key={ficha.ine5} aria-label={`Ficha de ${ficha.municipio}`}>
      {ficha.wikipedia?.imagen ? <Foto wiki={ficha.wikipedia} nombre={nombreLegible(ficha.municipio)} onCerrar={onCerrar} /> : (
        <div className="ficha-cabecera">
          <span className="miga">Municipio · código INE {ficha.ine5}</span>
          <Cerrar onClick={onCerrar} />
        </div>
      )}
      <h2 className="ficha-nombre">{nombreLegible(ficha.municipio)}</h2>
      <p className="ficha-datos">
        {num(ficha.poblacion)} habitantes
        {ficha.ine5 !== "28079" && <> · {distancia(ficha.red.estados.Distancia_Madrid)}</>}
        {" · "}{ficha.red.estados.Acceso_Ferroviario === "Si" ? "con estación de tren" : "sin estación de tren"}
      </p>

      {clase && (
        <div className={`veredicto ${clase.id}`} style={{ ["--c" as string]: `rgb(${clase.color.join(",")})` }}>
          <Columna clase={clase} grande />
          <div>
            <strong>{clase.nombre}</strong>
            <p>{ficha.motivo_exclusion
              ? ficha.motivo_exclusion.map((m) => MOTIVOS[m] ?? m).join(" ")
              : clase.resumen}</p>
          </div>
        </div>
      )}

      {meta.asistente_disponible && (
        <EnPocasPalabras ine5={ficha.ine5} clase={clase?.nombre ?? null} preferencias={peticion.preferencias} />
      )}

      {ficha.wikipedia?.resumen && (
        <p className="wiki-resumen">
          {ficha.wikipedia.resumen}{" "}
          {ficha.wikipedia.url && <a href={ficha.wikipedia.url} target="_blank" rel="noreferrer">Wikipedia</a>}
        </p>
      )}

      {!ficha.motivo_exclusion && (
        <>
          <Seccion titulo="Por qué" nota={resumenFactores(fs)}>
            <div className="factores">
              <ListaFactores titulo="A favor" lista={aFavor} vacio="Ningún factor destaca a favor." />
              <ListaFactores titulo="En contra" lista={enContra} vacio="Ningún factor destaca en contra." />
            </div>
            {combinados.length > 0 && (
              <div className="combinados">
                <h4>Combinaciones que también cuentan</h4>
                <ul>
                  {combinados.map((f) => (
                    <li key={f.termino} title={f.lectura ?? undefined}>
                      <MarcasFuerza fuerza={f.fuerza} signo={f.signo} />
                      <span>{f.titulo} ({f.detalle}) {f.signo > 0 ? "suman" : "restan"} {PALABRA_FUERZA[f.fuerza]}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Seccion>

          {prefActivas && <Preferencias ficha={ficha} pesos={pesos} meta={meta} peticion={peticion} />}

          <LecturaCausal ficha={ficha} meta={meta} />
        </>
      )}

      <Seccion titulo="Su perfil" nota="Cada rasgo, comparado con los 179 municipios: un tercio está en cada nivel.">
        <dl className="perfil">
          {Object.entries(meta.nodos).filter(([n]) => n !== meta.objetivo).map(([n, d]) => (
            <div key={n} className="rasgo" title={NODOS[n]?.que}>
              <dt>{NODOS[n]?.nombre ?? n}</dt>
              <dd>
                <Escalones total={d.estados.length} nivel={nivel(d.estados, ficha.red.estados[n])} />
                {NODOS[n]?.estados[ficha.red.estados[n]] ?? ficha.red.estados[n]}
              </dd>
            </div>
          ))}
        </dl>
      </Seccion>
    </aside>
  );
}

function Foto({ wiki, nombre, onCerrar }: { wiki: Wikipedia; nombre: string; onCerrar: () => void }) {
  const [cargada, setCargada] = useState(false);
  const img = wiki.imagen!;
  return (
    <figure className="ficha-foto">
      <img src={img.url} alt={`Vista de ${nombre}`} onLoad={() => setCargada(true)} className={cargada ? "cargada" : ""} />
      <Cerrar onClick={onCerrar} />
      <figcaption>
        Foto: {img.fuente ? <a href={img.fuente} target="_blank" rel="noreferrer">{img.autor}</a> : img.autor}
        {img.licencia && <> · {img.url_licencia
          ? <a href={img.url_licencia} target="_blank" rel="noreferrer">{img.licencia}</a> : img.licencia}</>}
        {" · Wikimedia Commons"}
      </figcaption>
    </figure>
  );
}

/** Lo mejor y lo peor del municipio, redactado por el LLM solo con los hechos de esta ficha. */
function EnPocasPalabras({ ine5, clase, preferencias }: {
  ine5: string; clase: string | null; preferencias: Peticion["preferencias"];
}) {
  const [texto, setTexto] = useState<Explicacion | null>(null);
  const [estado, setEstado] = useState<"cargando" | "listo" | "error">("cargando");
  const clave = JSON.stringify(preferencias);
  useEffect(() => {
    let vigente = true;
    setEstado("cargando");
    const t = setTimeout(() => {
      api.explicacion(ine5, clase, preferencias)
        .then((e) => { if (vigente) { setTexto(e); setEstado("listo"); } })
        .catch(() => { if (vigente) setEstado("error"); });
    }, 250);
    return () => { vigente = false; clearTimeout(t); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ine5, clase, clave]);

  if (estado === "error") return null; // la ficha ya lo explica todo: si el asistente falla, la sección no aparece
  return (
    <section className={`pocas-palabras${estado === "cargando" ? " cargando" : ""}`} aria-busy={estado === "cargando"}>
      <h3>En pocas palabras</h3>
      {estado === "cargando" || !texto ? (
        <>
          <span className="sombra-texto" /><span className="sombra-texto" /><span className="sombra-texto corto" />
        </>
      ) : (
        <>
          {texto.titular && <p className="titular">{texto.titular}</p>}
          <div className="mejor-peor">
            {texto.mejor.length > 0 && (
              <div className="mejor"><h4>Lo mejor</h4><ul>{texto.mejor.map((f) => <li key={f}>{f}</li>)}</ul></div>
            )}
            {texto.peor.length > 0 && (
              <div className="peor"><h4>Lo que conviene vigilar</h4><ul>{texto.peor.map((f) => <li key={f}>{f}</li>)}</ul></div>
            )}
          </div>
          <p className="firma">Redactado con IA a partir de los factores y datos de esta ficha.</p>
        </>
      )}
    </section>
  );
}

function ListaFactores({ titulo, lista, vacio }: { titulo: string; lista: Factor[]; vacio: string }) {
  return (
    <div className="lista-factores">
      <h4>{titulo}</h4>
      {lista.length === 0 ? <p className="vacio">{vacio}</p> : (
        <ul>
          {lista.map((f, k) => (
            <li key={f.termino} style={{ animationDelay: `${120 + k * 50}ms` }}>
              <MarcasFuerza fuerza={f.fuerza} signo={f.signo} />
              <span className="factor-titulo">{f.titulo}</span>
              <span className="factor-detalle">{f.detalle}</span>
              {f.lectura && <span className="factor-lectura">{f.lectura}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Preferencias({ ficha, pesos, meta, peticion }: {
  ficha: TFicha; pesos: Record<string, number>; meta: Meta; peticion: Peticion;
}) {
  const activas = meta.catalogo.filter((c) => (pesos[c.clave] ?? 0) > 0)
    .sort((a, b) => pesos[b.clave] - pesos[a.clave]);
  return (
    <Seccion titulo="Con lo que te importa">
      <ul className="lineas-pref">
        {activas.map((c) => {
          const f = ficha.preferencias[c.clave];
          const sentido = peticion.preferencias[c.clave]?.sentido ?? "";
          const u = f?.utilidad[sentido] ?? f?.utilidad[""] ?? 0;
          const etiqueta = c.sentidos?.find((s) => s.valor === sentido)?.etiqueta;
          return (
            <li key={c.clave}>
              <span className="pref-nombre">{c.nombre}{etiqueta && <> · {etiqueta.toLowerCase()}</>}</span>
              <span className="pref-dato">{f?.dato}</span>
              <span className={`pref-suma u${Math.round(u * 3)}`}>le suma <b>{palabraUtilidad(u)}</b></span>
              {c.en_modelo && <small>El modelo ya lo tiene en cuenta; tú le das peso extra.</small>}
            </li>
          );
        })}
      </ul>
    </Seccion>
  );
}

function LecturaCausal({ ficha, meta }: { ficha: TFicha; meta: Meta }) {
  const estados = meta.nodos[meta.objetivo].estados;
  const probs = ficha.red.probabilidades;
  const masProbable = estados.reduce((a, b) => (probs[b] > probs[a] ? b : a));
  const padres = Object.entries(ficha.red.padres).map(([n, s]) =>
    `${(NODOS[n]?.nombre ?? n).toLowerCase()} ${NODOS[n]?.estados[s] ?? s}`);
  const gaAlto = (ficha.ga2m.percentil ?? 0) >= 50;
  const redAlta = masProbable === estados[estados.length - 1];
  return (
    <Seccion titulo="La lectura de causas"
      nota={`La red bayesiana mira de qué depende el crecimiento empresarial. Para este municipio pesan su ${padres.join(" y su ")}.`}>
      <Reparto probabilidades={probs} estados={estados} etiqueta="Viabilidad esperada en municipios con este perfil" />
      <p className="conclusion">
        Lo más habitual en municipios así es una viabilidad <b>{masProbable.toLowerCase()}</b>.{" "}
        {ficha.discrepancia
          ? gaAlto
            ? "La red es más prudente que la tabla de factores: sus puntos fuertes están en rasgos que la red no usa directamente."
            : "La red ve más potencial del que refleja su grupo: su perfil de crecimiento y densidad es mejor que el conjunto de sus factores."
          : gaAlto === redAlta
            ? "Coincide con su grupo en el mapa."
            : "Matiza su grupo en el mapa sin contradecirlo."}
      </p>
    </Seccion>
  );
}

// "Acebeda (La)" -> "La Acebeda"
export function nombreLegible(n: string) {
  const m = n.match(/^(.*) \((La|El|Los|Las)\)$/);
  return m ? `${m[2]} ${m[1]}` : n;
}

function distancia(estado: string) {
  return estado === "Cerca" ? "cerca de Madrid" : estado === "Media" ? "a media distancia de Madrid" : "lejos de Madrid";
}
