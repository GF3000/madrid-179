import numpy as np
import pytest

from madrid179.preferencias import CATALOGO, POR_CLAVE, PREFERENCIAS, TOPE_PREFERENCIAS
from madrid179.ranking import candidatos, rankear


def test_me_da_igual_es_el_modelo(art):
    base, _ = rankear(art["tabla"])
    con, a = rankear(art["tabla"], {"transporte": "Me da igual", "ayudas": "No lo sé"})
    assert set(a) == set(PREFERENCIAS) and not any(a.values())
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


def test_catalogo_quince_preferencias(art):
    assert len(CATALOGO) == 15 and len(POR_CLAVE) == 15
    c = candidatos(art["tabla"])
    for p in CATALOGO:
        for s in [v for v, _ in p.sentidos] or [None]:
            u = p.utilidad_en(c, s)
            assert u.between(0, 1).all() and u.std() > 0, p.clave
        assert p.dato(c.iloc[0])  # texto de la ficha


@pytest.mark.parametrize("clave", [p.clave for p in CATALOGO if p.sentidos])
def test_sentido_contrario_invierte(art, clave):
    c = candidatos(art["tabla"])
    p = POR_CLAVE[clave]
    a, b = (p.utilidad_en(c, s) for s, _ in p.sentidos)
    np.testing.assert_allclose(a + b, 1)


def test_tope_el_modelo_pesa_al_menos_una_cuarta_parte(art):
    todas = {k: "Muy importante" for k in PREFERENCIAS}
    todas |= {p.clave: {"importancia": "Muy importante", "sentido": p.sentidos[0][0]} for p in CATALOGO if p.sentidos}
    c, a = rankear(art["tabla"], todas)
    assert sum(a.values()) == pytest.approx(TOPE_PREFERENCIAS)
    assert (c.parte_modelo / c.puntuacion).min() >= 0.0  # la parte del modelo existe
    assert c.parte_modelo.max() == pytest.approx(100 / (1 + TOPE_PREFERENCIAS))
    partes = c[[f"parte_{k}" for k in ["modelo", *PREFERENCIAS]]].sum(axis=1)
    np.testing.assert_allclose(partes, c.puntuacion)


def test_sentido_cambia_el_orden(art):
    cerca, _ = rankear(art["tabla"], {"distancia_madrid": {"importancia": "Muy importante", "sentido": "cerca"}})
    lejos, _ = rankear(art["tabla"], {"distancia_madrid": {"importancia": "Muy importante", "sentido": "lejos"}})
    assert cerca.head(20).dist_sol_km.median() < lejos.head(20).dist_sol_km.median()


@pytest.mark.parametrize("preferencias", [{"inventada": "Muy importante"}, {"transporte": "Muchísimo"},
                                          {"tamano": {"importancia": "Muy importante", "sentido": "mediano"}}])
def test_preferencias_invalidas(art, preferencias):
    with pytest.raises((KeyError, ValueError)):
        rankear(art["tabla"], preferencias)


def test_filtros_nuevos(art):
    c, _ = rankear(art["tabla"], madrid_max_km=30, poblacion_min=5000, poblacion_max=50000)
    assert len(c) > 0 and (c.dist_sol_km <= 30).all() and c.poblacion.between(5000, 50000).all()
    c, _ = rankear(art["tabla"], con_coworking=True)
    assert len(c) > 0 and (c.coworking_osm > 0).all()
