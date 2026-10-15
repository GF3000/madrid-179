// Pestaña «Explorar perfiles»: el usuario describe un tipo de municipio y la red bayesiana dice qué
// viabilidad suele acompañarlo. El mapa resalta los municipios que encajan.
import { useState } from "react";
import type { Consulta, Meta } from "../api";
import { NODOS } from "../modelo";
import { nombreLegible } from "./Ficha";
import { Ayuda, Reparto, Segmentado } from "./piezas";

interface Props {
  meta: Meta;
  evidencia: Record<string, string>;
  onEvidencia: (e: Record<string, string>) => void;
  consulta: Consulta | null;
  onSeleccionar: (ine5: string) => void;
}

const CUALQUIERA = "";
// Primero los dos rasgos de los que depende directamente la viabilidad en la red; el resto, plegados.
export default function PanelPerfiles({ meta, evidencia, onEvidencia, consulta, onSeleccionar }: Props) {
  const [todos, setTodos] = useState(false);
  const nodos = Object.keys(meta.nodos).filter((n) => n !== meta.objetivo);
  const principales = meta.padres_objetivo;
  const resto = nodos.filter((n) => !principales.includes(n));
  const estadosObjetivo = meta.nodos[meta.objetivo].estados;
  const alta = estadosObjetivo[estadosObjetivo.length - 1];
  const fijados = Object.keys(evidencia).length;

  const fila = (n: string) => (
    <div className="pregunta" key={n}>
      <Ayuda texto={NODOS[n]?.que} clase="pregunta-titulo">{NODOS[n]?.nombre ?? n}</Ayuda>
      <Segmentado compacto nombre={NODOS[n]?.nombre ?? n}
        opciones={[{ valor: CUALQUIERA, etiqueta: "Da igual" },
          ...meta.nodos[n].estados.map((s) => ({ valor: s, etiqueta: cap(NODOS[n]?.estados[s] ?? s) }))]}
        valor={evidencia[n] ?? CUALQUIERA}
        onCambio={(v) => {
          const e = { ...evidencia };
          if (v === CUALQUIERA) delete e[n]; else e[n] = v;
          onEvidencia(e);
        }} />
    </div>
  );

  let lectura = "Marca uno o varios rasgos para ver qué viabilidad suele acompañarlos.";
  if (consulta && fijados > 0) {
    const r = consulta.probabilidades[alta] / Math.max(consulta.a_priori[alta], 1e-6);
    lectura = r >= 1.15
      ? "Con este perfil, la viabilidad alta es más frecuente que en un municipio cualquiera."
      : r <= 0.87
        ? "Con este perfil, la viabilidad alta es menos frecuente que en un municipio cualquiera."
        : "Este perfil no cambia mucho las expectativas: se parece a un municipio cualquiera.";
  }

  return (
    <div className="panel-contenido">
      <p className="entradilla">
        Describe un tipo de municipio y mira qué <b>viabilidad empresarial</b> suele acompañarlo, según la red
        de causas aprendida con los datos de 2020 a 2024.
      </p>

      <div className="bloque">
        <div className="bloque-cabecera">
          <h3>Rasgos del perfil</h3>
          {fijados > 0 && <button className="enlace" onClick={() => onEvidencia({})}>Limpiar</button>}
        </div>
        <p className="nota">Estos dos son los que más influyen directamente:</p>
        {principales.map(fila)}
        <button className="enlace desplegar" onClick={() => setTodos(!todos)} aria-expanded={todos}>
          {todos ? "Ocultar el resto de rasgos" : `Más rasgos (${resto.length})`}
        </button>
        {todos && <div className="mas-rasgos">{resto.map(fila)}</div>}
      </div>

      <div className="bloque resultado-perfil">
        <h3>Qué cabe esperar</h3>
        {consulta && (
          <>
            <Reparto probabilidades={consulta.probabilidades} estados={estadosObjetivo} etiqueta="Este perfil" />
            <Reparto probabilidades={consulta.a_priori} estados={estadosObjetivo} etiqueta="Un municipio cualquiera" />
          </>
        )}
        <p className="conclusion">{lectura}</p>
      </div>

      {consulta && fijados > 0 && (
        <div className="bloque">
          <h3>Municipios con este perfil ({consulta.municipios.length})</h3>
          {consulta.municipios.length === 0
            ? <p className="nota">Ningún municipio reúne a la vez todos estos rasgos; la red lo estima igualmente a partir de los parecidos.</p>
            : (
              <ul className="nube">
                {consulta.municipios.map((m) => (
                  <li key={m.ine5}><button onClick={() => onSeleccionar(m.ine5)}>{nombreLegible(m.municipio)}</button></li>
                ))}
              </ul>
            )}
        </div>
      )}
    </div>
  );
}

const cap = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);
