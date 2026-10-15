// Recorrido por los mejores: cuando el asistente aplica lo que ha entendido, la cámara vuela de municipio en municipio
// por el Top y en cada parada aparece lo mejor de ese municipio en una tarjeta (1-3 cosas). Dura algo más de 30 s; se puede
// saltar (botón, Escape o tocando el mapa) y cada tarjeta abre la ficha del municipio.
import { useEffect, useRef, useState } from "react";
import type { Position } from "geojson";
import { api, type Meta, type Peticion, type Wikipedia } from "../api";
import { puntosFuertes, type Clase, type PuntoFuerte } from "../modelo";
import type { MandoMapa } from "./Mapa";
import { nombreLegible } from "./Ficha";
import { Columna } from "./piezas";
import { esMovil } from "../movil";

export interface Parada {
  ine5: string;
  municipio: string;
  clase: Clase;
  centro: Position;
}

interface Props {
  paradas: Parada[];
  mando: MandoMapa;
  meta: Meta;
  pesos: Record<string, number>;
  peticion: Peticion;
  onDestacar: (ine5: string | null) => void;
  onAbrir: (ine5: string) => void;
  onFin: () => void;
}

// Tiempos en ms: presentación, cada parada (vuelo incluido) y vuelta a la región
const INTRO = 1700;
const PARADA = 5000;
const VUELO = 1400;
const SALIDA = 6000;
const RUMBOS = [-24, 6, -34, 14, -10]; // la cámara cambia de ángulo en cada parada para que se note el viaje
const ANCHO_TARJETA = 480; // la tarjeta va a la derecha, a la altura de la vista: es lo que hay que leer
const HUECO_TARJETA = ANCHO_TARJETA + 56; // píxeles que deja a la derecha la cámara para no tapar el municipio
// En móvil la tarjeta va abajo, a todo el ancho y como mucho min(54 % del alto, 460 px) (movil.css): el hueco lo deja
// abajo la cámara con margenes.abajo de App, así que a la derecha no hace falta
const hueco = () => (esMovil() ? 0 : HUECO_TARJETA);
export const huecoTarjetaMovil = (alto: number) => Math.round(Math.min(alto * 0.54, 460) + 24);

export default function Recorrido({ paradas, mando, meta, pesos, peticion, onDestacar, onAbrir, onFin }: Props) {
  const [paso, setPaso] = useState(-1); // -1 presentación · 0..n-1 paradas · n despedida
  const [puntos, setPuntos] = useState<Record<string, PuntoFuerte[]>>({});
  const [fotos, setFotos] = useState<Record<string, Wikipedia["imagen"]>>({});
  const n = paradas.length;
  const terminado = useRef(false);
  const llamadas = useRef({ onDestacar, onFin });
  llamadas.current = { onDestacar, onFin };

  const terminar = (volver: boolean) => {
    if (terminado.current) return;
    terminado.current = true;
    if (volver) mando.verRegion(1200);
    llamadas.current.onDestacar(null);
    llamadas.current.onFin();
  };

  // Lo mejor de cada parada sale de su ficha (los mismos datos que enseña la ficha, sin LLM): se piden todas a la vez
  useEffect(() => {
    let vigente = true;
    for (const p of paradas) {
      api.ficha(p.ine5).then((f) => {
        if (!vigente) return;
        setPuntos((antes) => ({ ...antes, [p.ine5]: puntosFuertes(f, pesos, peticion, meta) }));
        const img = f.wikipedia?.imagen ?? null;
        if (img) new Image().src = img.url; // precarga: la foto ya está cuando llega su parada
        setFotos((antes) => ({ ...antes, [p.ine5]: img }));
      })
        .catch(() => vigente && setPuntos((antes) => ({ ...antes, [p.ine5]: [] })));
    }
    return () => { vigente = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Guion: presentación → una parada tras otra → despedida
  useEffect(() => {
    const t = [...paradas.map((_, k) => setTimeout(() => setPaso(k), INTRO + k * PARADA)),
      setTimeout(() => setPaso(n), INTRO + n * PARADA),
      setTimeout(() => terminar(false), INTRO + n * PARADA + SALIDA)];
    mando.encuadrar(paradas.map((q) => q.centro), { duracion: INTRO, derecha: hueco() });
    return () => { t.forEach(clearTimeout); llamadas.current.onDestacar(null); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (terminado.current) return;
    if (paso >= 0 && paso < n) {
      mando.volarA(paradas[paso].centro, { rumbo: RUMBOS[paso % RUMBOS.length], duracion: VUELO, derecha: hueco() });
      llamadas.current.onDestacar(paradas[paso].ine5);
    } else if (paso === n) {
      mando.encuadrar(paradas.map((q) => q.centro), { duracion: 1600, derecha: hueco() });
      llamadas.current.onDestacar(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paso]);

  // Saltar: Escape, o en cuanto el usuario toca o mueve el mapa (la cámara pasa a ser suya)
  useEffect(() => {
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && terminar(true);
    const tocar = (e: Event) => (e.target as Element).closest?.(".mapa") && terminar(false);
    window.addEventListener("keydown", tecla);
    window.addEventListener("pointerdown", tocar, true);
    window.addEventListener("wheel", tocar, { capture: true, passive: true });
    return () => {
      window.removeEventListener("keydown", tecla);
      window.removeEventListener("pointerdown", tocar, true);
      window.removeEventListener("wheel", tocar, true);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const parada = paso >= 0 && paso < n ? paradas[paso] : null;
  const lista = parada ? puntos[parada.ine5] : undefined;
  const foto = parada ? fotos[parada.ine5] : null;

  return (
    <div className="recorrido" style={{ ["--ancho" as string]: `${ANCHO_TARJETA}px` }} role="region" aria-label="Recorrido por tus mejores municipios" aria-live="polite">
      <div className="recorrido-tarjeta" key={paso} style={{ ["--vuelo" as string]: `${parada ? VUELO * 0.55 : 0}ms` }}>
        <div className="recorrido-cabecera">
          <ol className="recorrido-pasos" aria-hidden>
            {paradas.map((p, k) => (
              <li key={p.ine5} className={k < paso ? "hecho" : k === paso ? "actual" : ""}
                style={k === paso ? { ["--dura" as string]: `${PARADA}ms` } : undefined}><i /></li>
            ))}
          </ol>
          <button className="enlace" onClick={() => terminar(true)}>{paso === n ? "Cerrar" : "Saltar"}</button>
        </div>

        {paso === -1 && (
          <div className="recorrido-cuerpo">
            <span className="recorrido-miga">Con lo que nos has contado</span>
            <h3>Estos son tus {n} mejores municipios</h3>
            <p className="nota">Vamos uno a uno. El orden es orientativo: el modelo ve una tendencia moderada, no una certeza.</p>
          </div>
        )}

        {parada && (
          <button className="recorrido-cuerpo recorrido-parada" onClick={() => { terminar(false); onAbrir(parada.ine5); }}
            title="Abrir su ficha">
            {foto && (
              <span className="recorrido-foto">
                <img src={foto.url} alt={`Vista de ${nombreLegible(parada.municipio)}`} />
                <small>Foto: {foto.autor}{foto.licencia && <> · {foto.licencia}</>} · Wikimedia Commons</small>
              </span>
            )}
            <span className="recorrido-numero">{paso + 1}</span>
            <span className="recorrido-titulo">
              <span className="recorrido-miga"><Columna clase={parada.clase} /> {parada.clase.nombre}</span>
              <h3>{nombreLegible(parada.municipio)}</h3>
            </span>
            <ul className="recorrido-puntos">
              {lista === undefined
                ? [0, 1].map((k) => <li key={k} className="sombra-texto" />)
                : lista.length === 0
                  ? <li style={{ ["--k" as string]: 0 }}>{parada.clase.resumen}</li>
                  : lista.map((p, k) => (
                    <li key={p.titulo} style={{ ["--k" as string]: k }} className={p.tuyo ? "tuyo" : ""}>
                      <b>{p.titulo}</b> {p.detalle}{p.tuyo && <small>lo que pediste</small>}
                    </li>
                  ))}
            </ul>
            <span className="recorrido-abrir">Ver su ficha →</span>
          </button>
        )}

        {paso === n && (
          <div className="recorrido-cuerpo">
            <span className="recorrido-miga">Tu selección</span>
            <ol className="recorrido-resumen">
              {paradas.map((p) => (
                <li key={p.ine5}><button className="enlace" onClick={() => { terminar(false); onAbrir(p.ine5); }}>
                  {nombreLegible(p.municipio)}</button></li>
              ))}
            </ol>
            <p className="nota">Toca cualquiera para ver por qué está ahí.</p>
          </div>
        )}
      </div>
    </div>
  );
}
