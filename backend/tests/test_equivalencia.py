"""El artefacto que sirve la API reproduce las salidas versionadas del pipeline (bn_*.csv, ga2m_*.csv).

Si cambias el modelo a propósito, regenera las salidas (red_bayesiana_viabilidad.py) y reentrena el artefacto.
"""
import json

import numpy as np
import pandas as pd
import pytest

from madrid179.config import RAIZ
from madrid179.ranking import rankear

PROC = RAIZ / "data" / "processed"


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
    assert list(rk.index) == list(ranking_ref.index)
    np.testing.assert_allclose(rk.puntuacion, ranking_ref.puntuacion, atol=1e-9)
    np.testing.assert_allclose(rk.P_Alta, ranking_ref.P_Alta, atol=1e-9)
    np.testing.assert_allclose(rk.ga2m_pred * 100, ranking_ref.ga2m_tasa_neta_pred_pct, atol=1e-9)


def test_aportaciones_ga2m(art, ranking_ref):
    ref = leer("ga2m_contribuciones.csv").drop(columns="nombre_iecm")
    np.testing.assert_allclose(art["aportaciones"].loc[ref.index, ref.columns], ref, atol=1e-12)


def test_prediccion_es_suma_de_aportaciones(art):
    np.testing.assert_allclose(art["aportaciones"].sum(axis=1), art["tabla"].ga2m_pred, atol=1e-12)
