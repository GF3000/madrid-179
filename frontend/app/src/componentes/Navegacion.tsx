// Barra de navegación vertical a la izquierda: arriba los modos de trabajo (abren el panel; pulsar el activo lo
// pliega y deja el mapa entero), abajo la información (cómo se decide, vídeo y acerca de). «Dónde abrir» es la
// pregunta de la empresa; «Dónde actuar», la de la Administración.
import type { ReactNode } from "react";

export type Modo = "decidir" | "actuar" | "perfiles";
export type Dialogo = "como" | "video" | "acerca";

// Vídeo de presentación: dejar vacío mientras no exista (se ocultan el botón y la sección). URL de inserción,
// p. ej. "https://www.youtube-nocookie.com/embed/<id>"
export const VIDEO = "";

export default function Navegacion({ modo, abierto, onModo, onDialogo }: {
  modo: Modo; abierto: boolean; onModo: (m: Modo) => void; onDialogo: (d: Dialogo) => void;
}) {
  const boton = (m: Modo, texto: string, icono: ReactNode) => {
    const activo = modo === m;
    return (
      <button className={`nav-boton${activo ? " activo" : ""}${activo && !abierto ? " plegado" : ""}`}
        aria-pressed={activo} aria-expanded={activo ? abierto : undefined} onClick={() => onModo(m)}
        title={activo ? (abierto ? "Ocultar el panel y ver el mapa entero" : "Mostrar el panel") : texto}>
        {icono}<span>{texto}</span>
      </button>
    );
  };
  return (
    <nav className="navegacion" aria-label="Secciones">
      <div className="nav-grupo">
        {boton("decidir", "Dónde abrir", <IconoColumnas />)}
        {boton("actuar", "Dónde actuar", <IconoDiana />)}
        {boton("perfiles", "Explorar perfiles", <IconoRed />)}
      </div>
      <div className="nav-grupo">
        <button className="nav-boton" onClick={() => onDialogo("como")}><IconoPasos /><span>Cómo se decide</span></button>
        {VIDEO && <button className="nav-boton" onClick={() => onDialogo("video")}><IconoVideo /><span>Vídeo</span></button>}
        <button className="nav-boton" onClick={() => onDialogo("acerca")}><IconoInfo /><span>Acerca de</span></button>
      </div>
    </nav>
  );
}

function Icono({ children }: { children: ReactNode }) {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.7"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden>{children}</svg>
  );
}

// Las columnas del mapa
const IconoColumnas = () => (
  <Icono>
    <rect x="3.5" y="11" width="4.2" height="9" rx="1" />
    <rect x="9.9" y="4" width="4.2" height="16" rx="1" className="relleno" />
    <rect x="16.3" y="8" width="4.2" height="12" rx="1" />
  </Icono>
);

// Diana sobre el territorio: dónde poner el foco
const IconoDiana = () => (
  <Icono>
    <path d="M3 19.5c2.6-1.4 5.4-1.4 8 0s5.4 1.4 8 0" />
    <circle cx="12" cy="10" r="6.5" />
    <circle cx="12" cy="10" r="3.6" />
    <circle cx="12" cy="10" r="1.3" className="relleno" />
  </Icono>
);

// Nodos y aristas de la red bayesiana
const IconoRed = () => (
  <Icono>
    <path d="M7.6 7.3 10.6 15M16.4 7.3 13.4 15M8.5 6h7" />
    <circle cx="6" cy="6" r="2.4" />
    <circle cx="18" cy="6" r="2.4" />
    <circle cx="12" cy="18" r="2.6" className="relleno" />
  </Icono>
);

// Pasos numerados, como en «Cómo se decide»
const IconoPasos = () => (
  <Icono>
    <circle cx="5.5" cy="6" r="1.6" className="relleno" />
    <circle cx="5.5" cy="12" r="1.6" />
    <circle cx="5.5" cy="18" r="1.6" />
    <path d="M10 6h10M10 12h10M10 18h7" />
  </Icono>
);

const IconoVideo = () => (
  <Icono>
    <rect x="3" y="5" width="18" height="14" rx="3" />
    <path d="M10.2 9.2v5.6l4.6-2.8z" className="relleno" />
  </Icono>
);

const IconoInfo = () => (
  <Icono>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 11v5.5" />
    <circle cx="12" cy="7.8" r="0.4" className="relleno" />
  </Icono>
);
