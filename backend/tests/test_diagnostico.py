import pytest

from madrid179.config import CORTE_DIAGNOSTICO, FEATURES_GA2M, NECESIDAD, SENAL_DUDOSA, TIPO_FACTOR
from madrid179.diagnostico import CAPITAL, UMBRAL_FRENO, cuadrante, tipo_termino

API = "/api/v1"


@pytest.fixture(scope="module")
def diag(servicio):
    return servicio.diagnostico()


def test_tipo_factor_cubre_el_ga2m():
    assert set(TIPO_FACTOR) == set(FEATURES_GA2M)
    assert set(TIPO_FACTOR.values()) <= {"palanca", "estructural"}
    assert tipo_termino("rdb_per_capita & pct_up_servicios_prof") == "palanca"
    assert tipo_termino("crec_pob_5a & densidad_hab_km2") == "estructural"


def test_universo(diag):
    ms = diag["municipios"]
    assert len(ms) == 178 and CAPITAL not in {m["ine5"] for m in ms}
    assert any(not m["candidato"] for m in ms)  # incluye municipios sin oficinas
    assert [m["necesidad"] for m in ms] == sorted((m["necesidad"] for m in ms), reverse=True)


def test_percentiles_y_cuadrantes(diag):
    for m in diag["municipios"]:
        assert 0 <= m["necesidad"] <= 100 and 0 <= m["viabilidad"] <= 100
        assert set(m["componentes"]) == set(NECESIDAD)
        assert all(0 <= c["percentil"] <= 100 for c in m["componentes"].values())
        media = sum(c["percentil"] for c in m["componentes"].values()) / len(NECESIDAD)
        assert m["necesidad"] == pytest.approx(media, abs=0.02)
        assert m["cuadrante"] == cuadrante(m["necesidad"], m["viabilidad"], CORTE_DIAGNOSTICO)


def test_frenos(diag):
    for m in diag["municipios"]:
        assert len(m["frenos"]) <= 3
        todos = m["frenos"] + ([m["freno_palanca"]] if m["freno_palanca"] else [])
        for f in todos:
            assert f["aportacion_pp"] <= -UMBRAL_FRENO
            assert not any(c.strip() in SENAL_DUDOSA for c in f["termino"].split("&"))
        assert [f["aportacion_pp"] for f in m["frenos"]] == sorted(f["aportacion_pp"] for f in m["frenos"])
        if m["freno_palanca"]:
            assert m["freno_palanca"]["tipo"] == "palanca"


def test_endpoint(cliente):
    r = cliente.get(f"{API}/diagnostico")
    assert r.status_code == 200
    d = r.json()
    assert set(d) == {"corte", "aviso", "necesidad", "cuadrantes", "municipios"}
    assert [c["id"] for c in d["cuadrantes"]] == ["oportunidad", "apoyo", "autonomo", "vigilar"]
    assert set(d["municipios"][0]) == {"ine5", "municipio", "poblacion", "distancia", "candidato", "necesidad",
                                       "componentes", "viabilidad", "cuadrante", "frenos", "freno_palanca"}
    assert {m["distancia"] for m in d["municipios"]} <= {"Cerca", "Media", "Lejos"}


def test_vivienda_no_es_palanca():
    """El valor de la vivienda es señal de demanda en el GA²M, no algo que convenga «subir»."""
    assert TIPO_FACTOR["vc_residencial_por_uu"] == "estructural"
    assert tipo_termino("vc_residencial_por_uu & densidad_hab_km2") == "estructural"


def test_umbral_freno(servicio):
    """Frenos = aportaciones <= -0,02 pp (umbral «algo» de la ficha); por debajo no se listan."""
    import pandas as pd
    from madrid179.diagnostico import frenos
    assert UMBRAL_FRENO == 0.02
    contrib = pd.Series({"intercepto": 0.5, "crec_pob_5a": -0.0003, "sanidad_por_1000hab": -0.00019,
                         "densidad_hab_km2": 0.01, "poblacion": -0.5})  # poblacion: señal dudosa
    principales, palanca = frenos(contrib)
    assert [f["termino"] for f in principales] == ["crec_pob_5a"] and palanca is None
    assert frenos(contrib.drop("crec_pob_5a")) == ([], None)
