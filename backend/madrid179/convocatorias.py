"""Convocatorias abiertas para pymes y autónomos (BDNS, PENDIENTES #13): contexto para «Dónde abrir», fuera del modelo.

La tabla la genera backend/pipeline/convocatorias_bdns.py a una fecha de consulta: convocatorias estatales y de la
Comunidad de Madrid con el beneficiario oficial «PYME y personas físicas que desarrollan actividad económica»,
abiertas a esa fecha y revisadas una a una. La mayoría vale para cualquier municipio; las que tienen
`max_habitantes` solo alcanzan a los municipios por debajo de ese umbral y se muestran en su ficha.
"""
import logging

import pandas as pd

from .config import RAIZ

log = logging.getLogger(__name__)

RUTA = RAIZ / "data" / "processed" / "convocatorias_abiertas.csv"

# Perfiles de ayuda que el asistente puede deducir de la descripción del negocio (clave -> etiqueta en la app)
PERFILES = {
    "contratar": "Contratar personal",
    "autonomos": "Autónomos",
    "emprender": "Crear una empresa",
    "innovar": "Innovación e I+D",
    "digitalizar": "Digitalización",
    "exportar": "Exportar",
    "financiacion": "Financiación",
    "comercio": "Comercio",
    "energia": "Eficiencia energética",
}

AVISO = ("Según la Base de Datos Nacional de Subvenciones (BDNS) a {fecha}: abiertas y dirigidas a pymes y autónomos. "
         "Revisadas una a una, pero comprueba plazo y requisitos en las bases antes de solicitar. No forman parte "
         "de la puntuación.")


def leer():
    """Lista de convocatorias (dict) o None si falta la tabla (se avisa en el log; la app oculta el bloque)."""
    if not RUTA.exists():
        log.warning("No está %s: sin convocatorias abiertas (generarla con backend/pipeline/convocatorias_bdns.py)", RUTA)
        return None
    d = pd.read_csv(RUTA, sep=";", dtype=str, encoding="utf-8-sig", keep_default_na=False)
    filas = []
    for r in d.to_dict("records"):
        filas.append({
            "num": r["num"], "nivel": r["nivel"], "organo": r["organo"], "titulo": r["titulo"],
            "para_quien": r["para_quien"], "perfiles": [p for p in r["perfiles"].split(",") if p in PERFILES],
            "fin_solicitud": r["fin_solicitud"] or None, "nota": r["nota"] or None, "url": r["url"],
            "max_habitantes": int(float(r["max_habitantes"])) if r.get("max_habitantes") else None,
            "fecha_consulta": r["fecha_consulta"],
        })
    return filas


def generales(filas):
    """Las que no dependen del municipio, con la fecha de consulta y el aviso (GET /api/v1/convocatorias)."""
    if filas is None:
        return None
    fecha = filas[0]["fecha_consulta"] if filas else None
    return {"fecha_consulta": fecha, "aviso": AVISO.format(fecha=fecha), "perfiles": PERFILES,
            "convocatorias": [f for f in filas if f["max_habitantes"] is None]}


def del_municipio(filas, poblacion):
    """Las restringidas por tamaño a las que llega un municipio (ficha)."""
    return [f for f in filas or [] if f["max_habitantes"] is not None and poblacion < f["max_habitantes"]]
