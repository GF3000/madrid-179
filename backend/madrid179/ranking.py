"""Ranking: filtros duros → percentil del GA²M entre los candidatos → preferencias → orden.

El percentil y los pesos se recalculan sobre los candidatos que quedan tras los filtros: si el usuario
exige una estación cercana, cambian el conjunto, sd(S) y sd(u).
"""
import numpy as np

from .config import FILTROS
from .preferencias import PREFERENCIAS, normalizar, puntuar, utilidades

# Filtros «imprescindible» que puede pedir el usuario: nombre -> condición sobre la tabla
FILTROS_USUARIO = {
    "estacion_max_km": lambda t, v: t.dist_ferro_km <= v,
    "madrid_max_km": lambda t, v: t.dist_sol_km <= v,
    "madrid_min_km": lambda t, v: t.dist_sol_km >= v,
    "poblacion_min": lambda t, v: t.poblacion >= v,
    "poblacion_max": lambda t, v: t.poblacion <= v,
    "solo_con_ayudas": lambda t, v: t.nivel_ayudas != "Bajo" if v else t.index == t.index,
    "con_coworking": lambda t, v: t.coworking_osm > 0 if v else t.index == t.index,
}


def candidatos(tabla, estacion_max_km=None, solo_con_ayudas=False, **filtros):
    """Aplica los filtros duros de la configuración y los que elige el usuario («imprescindible»)."""
    filtros = {"estacion_max_km": estacion_max_km, "solo_con_ayudas": solo_con_ayudas, **filtros}
    desconocidos = set(filtros) - set(FILTROS_USUARIO)
    if desconocidos:
        raise KeyError(", ".join(sorted(desconocidos)))
    mask = np.logical_and.reduce([f(tabla) for f in FILTROS.values()])
    for nombre, valor in filtros.items():
        if valor is not None and valor is not False:
            mask &= np.asarray(FILTROS_USUARIO[nombre](tabla, valor))
    return tabla[mask]


def rankear(tabla, importancias=None, estacion_max_km=None, solo_con_ayudas=False, **filtros):
    """Devuelve (candidatos ordenados con puntuación y desglose, pesos a_k de las 15 preferencias).

    importancias: {clave: importancia} o {clave: {"importancia": ..., "sentido": ...}}.
    Sin preferencias, la puntuación es el percentil del GA²M (0-100), igual que bn_ranking_municipios.csv."""
    prefs = normalizar(importancias)
    c = candidatos(tabla, estacion_max_km, solo_con_ayudas, **filtros).copy()
    a = {k: 0.0 for k in PREFERENCIAS}
    if c.empty:
        return c, a
    S = c.ga2m_pred.rank(pct=True)
    U = utilidades(c, importancias)
    total, partes, pesos = puntuar(S, U, {k: prefs[k][0] for k in U})
    a |= pesos
    c["percentil_ga2m"] = S * 100
    c["percentil_bn"] = c.P_Alta.rank(pct=True) * 100
    c["puntuacion"] = total
    for k in partes.columns:
        c[f"parte_{k}"] = partes[k]
    c = c.sort_values(["puntuacion", "P_Alta"], ascending=False)
    c.insert(0, "posicion", range(1, len(c) + 1))
    return c, a
