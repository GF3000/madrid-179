import { useEffect, useState } from "react";

// Pantallas estrechas (móvil): el panel y la ficha pasan a hojas inferiores. Debe coincidir con la media query
// de movil.css
export const CONSULTA_MOVIL = "(max-width: 767px)";
// Sin ratón: no hay «pasar por encima» ni atributos title visibles
export const CONSULTA_TACTIL = "(hover: none), (pointer: coarse)";

const coincide = (q: string) => typeof matchMedia === "function" && matchMedia(q).matches;
export const esMovil = () => coincide(CONSULTA_MOVIL);
export const esTactil = () => coincide(CONSULTA_TACTIL);

function useConsulta(q: string): boolean {
  const [si, setSi] = useState(() => coincide(q));
  useEffect(() => {
    const m = matchMedia(q);
    const cambio = () => setSi(m.matches);
    cambio();
    m.addEventListener("change", cambio);
    return () => m.removeEventListener("change", cambio);
  }, [q]);
  return si;
}

export const useEsMovil = () => useConsulta(CONSULTA_MOVIL);
export const useEsTactil = () => useConsulta(CONSULTA_TACTIL);
