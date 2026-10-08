import numpy as np
import pytest

from madrid179.ranking import rankear


def test_me_da_igual_es_el_modelo(art):
    base, _ = rankear(art["tabla"])
    con, a = rankear(art["tabla"], {"transporte": "Me da igual", "ayudas": "No lo sé"})
    assert a == {"transporte": 0.0, "ayudas": 0.0}
    np.testing.assert_allclose(con.puntuacion, base.puntuacion)


@pytest.mark.parametrize("pref, importancia, w", [
    ("transporte", "Poco importante", 0.267), ("transporte", "Muy importante", 0.421),
    ("ayudas", "Poco importante", 0.291), ("ayudas", "Muy importante", 0.450),
])
def test_pesos_documentados(art, pref, importancia, w):
    """Pesos de PENDIENTES.md (#40): w = a / (1 + a) con una sola preferencia."""
    _, a = rankear(art["tabla"], {pref: importancia})
    assert a[pref] / (1 + a[pref]) == pytest.approx(w, abs=5e-4)


def test_desglose_suma_la_puntuacion(art):
    c, _ = rankear(art["tabla"], {"transporte": "Muy importante", "ayudas": "Poco importante"})
    partes = c[["parte_modelo", "parte_transporte", "parte_ayudas"]].sum(axis=1)
    np.testing.assert_allclose(partes, c.puntuacion)


def test_filtros_restringen_y_recalculan(art):
    c, _ = rankear(art["tabla"], estacion_max_km=5, solo_con_ayudas=True)
    assert 0 < len(c) < 139
    assert (c.dist_ferro_km <= 5).all() and (c.nivel_ayudas != "Bajo").all()
    assert c.percentil_ga2m.max() == pytest.approx(100)  # el percentil se recalcula entre los que quedan
