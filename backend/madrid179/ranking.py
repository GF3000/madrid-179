"""Ranking: filtros duros → percentil del GA²M entre los candidatos → preferencias → orden.

El percentil y los pesos se recalculan sobre los candidatos que quedan tras los filtros: si el usuario
exige una estación cercana, cambian el conjunto, sd(S) y sd(u).
"""
import numpy as np

from .config import FILTROS
from .preferencias import PREFERENCIAS, puntuar, utilidad_ayudas, utilidad_transporte


def candidatos(tabla, estacion_max_km=None, solo_con_ayudas=False):
    """Aplica los filtros duros de la configuración y los que elige el usuario («imprescindible»)."""
    mask = np.logical_and.reduce([f(tabla) for f in FILTROS.values()])
    if estacion_max_km is not None:
        mask &= (tabla.dist_ferro_km <= estacion_max_km).to_numpy()
    if solo_con_ayudas:
        mask &= (tabla.nivel_ayudas != "Bajo").to_numpy()
    return tabla[mask]


def utilidades(c):
    return {"transporte": utilidad_transporte(c.dist_ferro_km), "ayudas": utilidad_ayudas(c.nivel_ayudas_num)}


def rankear(tabla, importancias=None, estacion_max_km=None, solo_con_ayudas=False):
    """Devuelve (candidatos ordenados con puntuación y desglose, pesos a_k).
    Sin preferencias, la puntuación es el percentil del GA²M (0-100), igual que bn_ranking_municipios.csv."""
    imp = {k: "Me da igual" for k in PREFERENCIAS} | (importancias or {})
    c = candidatos(tabla, estacion_max_km, solo_con_ayudas).copy()
    if c.empty:
        return c, {k: 0.0 for k in PREFERENCIAS}
    S = c.ga2m_pred.rank(pct=True)
    total, partes, a = puntuar(S, utilidades(c), imp)
    c["percentil_ga2m"] = S * 100
    c["percentil_bn"] = c.P_Alta.rank(pct=True) * 100
    c["puntuacion"] = total
    for k in partes.columns:
        c[f"parte_{k}"] = partes[k]
    c = c.sort_values(["puntuacion", "P_Alta"], ascending=False)
    c.insert(0, "posicion", range(1, len(c) + 1))
    return c, a
