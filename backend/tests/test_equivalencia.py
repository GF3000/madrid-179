"""El artefacto que sirve la API reproduce las salidas versionadas del pipeline (bn_*.csv, ga2m_*.csv).

Si cambias el modelo a propósito, regenera las salidas (red_bayesiana_viabilidad.py) y reentrena el artefacto.

En local la comparación es exacta. En la CI el GA²M se reentrena en otra máquina y el boosting del EBM amplifica
las diferencias de coma flotante entre procesadores aunque la semilla sea la misma: las aportaciones cambian
en torno a 1e-5 y municipios casi empatados pueden intercambiarse (visto en GitHub Actions, 2026-10-15, máx.
5e-5). Allí se tolera ese ruido, con límites estrechos; la red bayesiana sigue comprobándose exacta en todas partes.
"""
import json
import os

import numpy as np
import pandas as pd
import pytest

from madrid179.config import RAIZ
from madrid179.ranking import rankear

PROC = RAIZ / "data" / "processed"
OTRA_MAQUINA = bool(os.environ.get("CI"))
TOL_GA2M = 2e-4 if OTRA_MAQUINA else 1e-12  # por aportación, tasa neta en fracción: 2e-4 = 0,02 pp
TOL_PRED = 5e-4 if OTRA_MAQUINA else 1e-11  # predicción = suma de 24 aportaciones
MAX_SALTO = 3 if OTRA_MAQUINA else 0  # posiciones que puede moverse un municipio por ese ruido


def leer(nombre):
    return pd.read_csv(PROC / nombre, sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")


@pytest.fixture(scope="module")
def ranking_ref():
    return leer("bn_ranking_municipios.csv")


def test_umbrales(art):
    ref = json.loads((PROC / "bn_umbrales.json").read_text(encoding="utf-8"))
    assert art["umbrales"] == ref


def test_ranking_por_defecto_identico(art, ranking_ref):
    rk, _ = rankear(art["tabla"])
    assert set(rk.index) == set(ranking_ref.index)
    salto = (rk.posicion - ranking_ref.loc[rk.index, "posicion"]).abs().max()
    assert salto <= MAX_SALTO, f"un municipio se mueve {salto} posiciones"
    rk = rk.loc[ranking_ref.index]
    np.testing.assert_allclose(rk.P_Alta, ranking_ref.P_Alta, atol=1e-9)  # la red es determinista
    np.testing.assert_allclose(rk.ga2m_pred * 100, ranking_ref.ga2m_tasa_neta_pred_pct, atol=TOL_PRED * 100)
    np.testing.assert_allclose(rk.puntuacion, ranking_ref.puntuacion,
                               atol=MAX_SALTO * 100 / len(rk) + 1e-9)  # percentil: cada posición vale 100/n


def test_aportaciones_ga2m(art, ranking_ref):
    ref = leer("ga2m_contribuciones.csv").drop(columns="nombre_iecm")
    np.testing.assert_allclose(art["aportaciones"].loc[ref.index, ref.columns], ref, atol=TOL_GA2M)


def test_prediccion_es_suma_de_aportaciones(art):
    np.testing.assert_allclose(art["aportaciones"].sum(axis=1), art["tabla"].ga2m_pred, atol=1e-12)
