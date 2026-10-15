import numpy as np
import pytest

import pandas as pd

from madrid179.preferencias import (CATALOGO, POR_CLAVE, PREFERENCIAS, TOPE_PREFERENCIAS, ayudas_en, unir_ayudas,
                                  utilidad_ayudas)
from madrid179.ranking import candidatos, rankear


def test_me_da_igual_es_el_modelo(tabla):
    base, _ = rankear(tabla)
    con, a = rankear(tabla, {"transporte": "Me da igual", "ayudas": "No lo sé"})
    assert set(a) == set(PREFERENCIAS) and not any(a.values())
    np.testing.assert_allclose(con.puntuacion, base.puntuacion)


@pytest.mark.parametrize("pref, importancia, w", [
    ("transporte", "Poco importante", 0.267), ("transporte", "Muy importante", 0.421),
    ("ayudas", "Poco importante", 0.226), ("ayudas", "Muy importante", 0.368),
])
def test_pesos_documentados(tabla, pref, importancia, w):
    """Pesos de PENDIENTES.md (#40): w = a / (1 + a) con una sola preferencia. Las ayudas pasaron de 0,291 / 0,450
    a 0,226 / 0,368 el 2026-10-15 al usar la lista oficial: la utilidad es casi binaria (LEADER sí o no), su sd
    sube de ≈ 0,37 a 0,495 y a = r·sd(S)/sd(u) baja."""
    _, a = rankear(tabla, {pref: importancia})
    assert a[pref] / (1 + a[pref]) == pytest.approx(w, abs=5e-4)


def test_desglose_suma_la_puntuacion(tabla):
    c, _ = rankear(tabla, {"transporte": "Muy importante", "ayudas": "Poco importante"})
    partes = c[["parte_modelo", "parte_transporte", "parte_ayudas"]].sum(axis=1)
    np.testing.assert_allclose(partes, c.puntuacion)


def test_filtros_restringen_y_recalculan(tabla):
    c, _ = rankear(tabla, estacion_max_km=5, solo_con_ayudas=True)
    assert 0 < len(c) < 139
    assert (c.dist_ferro_km <= 5).all() and (ayudas_en(c) > 0).all()
    assert c.percentil_ga2m.max() == pytest.approx(100)  # el percentil se recalcula entre los que quedan


def test_catalogo_quince_preferencias(tabla):
    assert len(CATALOGO) == 15 and len(POR_CLAVE) == 15
    c = candidatos(tabla)
    for p in CATALOGO:
        for s in [v for v, _ in p.sentidos] or [None]:
            u = p.utilidad_en(c, s)
            assert u.between(0, 1).all() and u.std() > 0, p.clave
        assert p.dato(c.iloc[0])  # texto de la ficha


@pytest.mark.parametrize("clave", [p.clave for p in CATALOGO if p.sentidos])
def test_sentido_contrario_invierte(tabla, clave):
    c = candidatos(tabla)
    p = POR_CLAVE[clave]
    a, b = (p.utilidad_en(c, s) for s, _ in p.sentidos)
    np.testing.assert_allclose(a + b, 1)


def test_tope_el_modelo_pesa_al_menos_una_cuarta_parte(tabla):
    todas = {k: "Muy importante" for k in PREFERENCIAS}
    todas |= {p.clave: {"importancia": "Muy importante", "sentido": p.sentidos[0][0]} for p in CATALOGO if p.sentidos}
    c, a = rankear(tabla, todas)
    assert sum(a.values()) == pytest.approx(TOPE_PREFERENCIAS)
    assert (c.parte_modelo / c.puntuacion).min() >= 0.0  # la parte del modelo existe
    assert c.parte_modelo.max() == pytest.approx(100 / (1 + TOPE_PREFERENCIAS))
    partes = c[[f"parte_{k}" for k in ["modelo", *PREFERENCIAS]]].sum(axis=1)
    np.testing.assert_allclose(partes, c.puntuacion)


def test_sentido_cambia_el_orden(tabla):
    cerca, _ = rankear(tabla, {"distancia_madrid": {"importancia": "Muy importante", "sentido": "cerca"}})
    lejos, _ = rankear(tabla, {"distancia_madrid": {"importancia": "Muy importante", "sentido": "lejos"}})
    assert cerca.head(20).dist_sol_km.median() < lejos.head(20).dist_sol_km.median()


@pytest.mark.parametrize("preferencias", [{"inventada": "Muy importante"}, {"transporte": "Muchísimo"},
                                          {"tamano": {"importancia": "Muy importante", "sentido": "mediano"}}])
def test_preferencias_invalidas(tabla, preferencias):
    with pytest.raises((KeyError, ValueError)):
        rankear(tabla, preferencias)


def test_filtros_nuevos(tabla):
    c, _ = rankear(tabla, madrid_max_km=30, poblacion_min=5000, poblacion_max=50000)
    assert len(c) > 0 and (c.dist_sol_km <= 30).all() and c.poblacion.between(5000, 50000).all()
    c, _ = rankear(tabla, con_coworking=True)
    assert len(c) > 0 and (c.coworking_osm > 0).all()


def test_utilidad_ayudas_lista_oficial():
    """LEADER = 1 (con o sin IRPF), solo < 2.500 hab. = 0,5, nada = 0."""
    u = utilidad_ayudas(pd.Series(["GALSINMA (Sierra Norte)", "ARACOVE (sureste)", "", ""]),
                        pd.Series([True, False, True, False]))
    assert u.tolist() == [1.0, 1.0, 0.5, 0.0]


def test_ayudas_en_los_municipios(tabla):
    p = POR_CLAVE["ayudas"]
    u = p.utilidad_en(tabla)
    assert (u == 1).sum() == 99 and (u == 0.5).sum() == 2 and set(u.unique()) == {0.0, 0.5, 1.0}
    canencia, getafe = tabla.loc["28034"], tabla.loc["28065"]
    assert u["28034"] == 1 and p.dato(canencia) == "en LEADER (GALSINMA (Sierra Norte))"
    assert u["28065"] == 0 and p.dato(getafe) == "sin ayudas verificadas"
    solo_irpf = tabla.index[u == 0.5][0]
    assert p.dato(tabla.loc[solo_irpf]) == "menos de 2.500 hab. (deducciones del IRPF)"


def test_filtro_ayudas_es_utilidad_positiva(tabla):
    c, _ = rankear(tabla, solo_con_ayudas=True)
    base = candidatos(tabla)
    assert set(c.index) == set(base.index[ayudas_en(base) > 0])
    assert c.leader_gal.ne("").sum() + c.irpf_menos_2500.sum() >= len(c)


def test_sin_fichero_de_ayudas_degrada(art):
    """Sin ayudas_oficiales.csv: la preferencia no pesa ni cambia el orden y el filtro no deja candidatos."""
    t = unir_ayudas(art["tabla"], None)
    base, _ = rankear(t)
    con, a = rankear(t, {"ayudas": "Muy importante"})
    assert a["ayudas"] == 0 and list(con.index) == list(base.index)
    assert POR_CLAVE["ayudas"].dato(t.iloc[0]) == "sin datos de ayudas oficiales"
    assert rankear(t, solo_con_ayudas=True)[0].empty


def test_ayudas_muy_importante_sube_los_de_leader(tabla):
    c, _ = rankear(tabla, {"ayudas": "Muy importante"})
    assert (c.head(10).leader_gal != "").all()
