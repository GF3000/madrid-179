// Piezas pequeñas de la interfaz, dibujadas a medida (sin librerías de iconos).
import type { ReactNode } from "react";
import type { Clase, Fuerza } from "../modelo";

export function Segmentado<T extends string>(p: {
  opciones: readonly { valor: T; etiqueta: string }[];
  valor: T;
  onCambio: (v: T) => void;
  nombre: string;
  compacto?: boolean;
}) {
  const i = Math.max(0, p.opciones.findIndex((o) => o.valor === p.valor));
  return (
    <div className={`segmentado${p.compacto ? " compacto" : ""}`} role="radiogroup" aria-label={p.nombre}
      style={{ ["--n" as string]: p.opciones.length, ["--i" as string]: i }}>
      <span className="segmentado-cursor" aria-hidden />
      {p.opciones.map((o) => (
        <button key={o.valor} role="radio" aria-checked={o.valor === p.valor}
          className={o.valor === p.valor ? "activo" : ""} onClick={() => p.onCambio(o.valor)}>
          {o.etiqueta}
        </button>
      ))}
    </div>
  );
}

/** Columna en miniatura con el color del grupo: la misma metáfora que el mapa. */
export function Columna({ clase, grande }: { clase: Clase; grande?: boolean }) {
  const h = grande ? 34 : 18;
  const alto = Math.max(3, Math.round((clase.altura / 7200) * h));
  const [r, g, b] = clase.color;
  return (
    <svg className={`columna${grande ? " grande" : ""}`} width={grande ? 21 : 14} height={(h + 5) * (grande ? 1.5 : 1)}
      viewBox={`0 0 14 ${h + 5}`} aria-hidden>
      <path d={`M1 ${h + 2 - alto} L7 ${h - 1 - alto} L13 ${h + 2 - alto} L7 ${h + 5 - alto}Z`}
        fill={`rgb(${Math.min(255, r + 40)},${Math.min(255, g + 40)},${Math.min(255, b + 40)})`} />
      <path d={`M1 ${h + 2 - alto} L7 ${h + 5 - alto} L7 ${h + 5} L1 ${h + 2}Z`} fill={`rgb(${r},${g},${b})`} />
      <path d={`M13 ${h + 2 - alto} L7 ${h + 5 - alto} L7 ${h + 5} L13 ${h + 2}Z`}
        fill={`rgb(${Math.round(r * 0.78)},${Math.round(g * 0.78)},${Math.round(b * 0.78)})`} />
    </svg>
  );
}

/** Tres marcas que se llenan según la fuerza de un factor. */
export function MarcasFuerza({ fuerza, signo }: { fuerza: Fuerza; signo: 1 | -1 }) {
  return (
    <span className={`marcas ${signo > 0 ? "a-favor" : "en-contra"}`} aria-label={`fuerza ${fuerza} de 3`}>
      {[1, 2, 3].map((n) => <i key={n} className={n <= fuerza ? "llena" : ""} style={{ animationDelay: `${n * 70}ms` }} />)}
    </span>
  );
}

/** Nivel en tres escalones (bajo, medio, alto) o dos (no, sí). */
export function Escalones({ total, nivel }: { total: number; nivel: number }) {
  return (
    <span className="escalones" aria-hidden>
      {Array.from({ length: total }, (_, k) => <i key={k} className={k <= nivel ? "lleno" : ""}
        style={{ height: `${6 + k * (total === 2 ? 8 : 4)}px` }} />)}
    </span>
  );
}

/** Reparto Baja / Media / Alta sin cifras: la anchura cuenta la historia. */
export function Reparto({ probabilidades, estados, etiqueta }: {
  probabilidades: Record<string, number>; estados: string[]; etiqueta?: string;
}) {
  return (
    <div className="reparto">
      {etiqueta && <span className="reparto-etiqueta">{etiqueta}</span>}
      <div className="reparto-barra">
        {estados.map((s, k) => (
          <span key={s} className={`tramo t${k}`} style={{ flexGrow: Math.max(probabilidades[s] ?? 0, 0.001) }}
            title={`Viabilidad ${s.toLowerCase()}`}>
            {(probabilidades[s] ?? 0) > 0.16 && <em>{s}</em>}
          </span>
        ))}
      </div>
    </div>
  );
}

export function Seccion({ titulo, children, nota }: { titulo: string; children: ReactNode; nota?: ReactNode }) {
  return (
    <section className="seccion">
      <h3>{titulo}</h3>
      {nota && <p className="nota">{nota}</p>}
      {children}
    </section>
  );
}

/** Siete estrellas de la bandera de la Comunidad, como firma visual. */
export function Estrellas({ n = 7, tam = 7 }: { n?: number; tam?: number }) {
  return (
    <span className="estrellas" aria-hidden>
      {Array.from({ length: n }, (_, k) => (
        <svg key={k} width={tam} height={tam} viewBox="0 0 20 20" style={{ animationDelay: `${300 + k * 60}ms` }}>
          <path d="M10 1.2l2.6 6.1 6.6.5-5 4.3 1.6 6.5L10 15.1l-5.8 3.5 1.6-6.5-5-4.3 6.6-.5z" />
        </svg>
      ))}
    </span>
  );
}

export function Cerrar({ onClick, etiqueta = "Cerrar" }: { onClick: () => void; etiqueta?: string }) {
  return (
    <button className="cerrar" onClick={onClick} aria-label={etiqueta}>
      <span className="aspa" aria-hidden />
    </button>
  );
}
