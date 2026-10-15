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
    assert set(d) == {"corte", "aviso", "necesidad", "cuadrantes", "municipios", "contexto_nota"}
    assert "no resultado del modelo" in d["contexto_nota"]
    assert [c["id"] for c in d["cuadrantes"]] == ["oportunidad", "apoyo", "autonomo", "vigilar"]
    assert set(d["municipios"][0]) == {"ine5", "municipio", "poblacion", "distancia", "candidato", "necesidad",
                                       "componentes", "viabilidad", "cuadrante", "frenos", "freno_palanca", "contexto"}
    c = d["municipios"][0]["contexto"]
    assert set(c) == {"oficinas", "ayudas"} and set(c["oficinas"]) == {"locales", "por_1000hab", "coworking"}
    assert set(c["ayudas"]) == {"leader", "irpf_menos_2500", "pir_sin_cofinanciacion", "anio_padron"}
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


def test_contexto_oficinas(diag, servicio):
    """Locales de oficinas, por 1.000 hab. y coworking salen de la tabla del artefacto, sin tocar."""
    t = servicio.tabla
    sin = {m["ine5"] for m in diag["municipios"] if m["contexto"]["oficinas"]["locales"] == 0}
    assert sin == set(t.drop(index=CAPITAL).index[t.drop(index=CAPITAL).uu_oficinas < 1])
    assert len(sin) == 39
    for m in diag["municipios"]:
        o = m["contexto"]["oficinas"]
        assert o["locales"] == int(t.at[m["ine5"], "uu_oficinas"]) and o["coworking"] >= 0


def test_contexto_ayudas(diag):
    """99 municipios en LEADER (Madrid no lo está); IRPF y PIR = población < 2.500 con el padrón del CSV."""
    ms = diag["municipios"]
    assert all(m["contexto"]["ayudas"] is not None for m in ms)
    leader = [m for m in ms if m["contexto"]["ayudas"]["leader"]]
    assert len(leader) == 99
    assert {m["contexto"]["ayudas"]["leader"]["grupo"] for m in leader} == {
        "ARACOVE (sureste)", "GALSINMA (Sierra Norte)", "ADI Sierra Oeste (suroeste)"}
    assert all(m["contexto"]["ayudas"]["leader"]["fuente"].startswith("https://www.bocm.es/") for m in leader)
    for m in ms:
        a = m["contexto"]["ayudas"]
        assert a["irpf_menos_2500"] == (m["poblacion"] < 2500) == a["pir_sin_cofinanciacion"]
        assert a["anio_padron"] == "2025"
    assert sum(m["contexto"]["ayudas"]["irpf_menos_2500"] for m in ms) == 70


def test_contexto_sin_fichero_de_ayudas(servicio):
    """Sin ayudas_oficiales.csv el diagnóstico sigue saliendo, con `ayudas: null`."""
    from madrid179.diagnostico import diagnostico
    d = diagnostico(servicio.tabla, servicio.art["aportaciones"], servicio.base.index, None)
    assert all(m["contexto"]["ayudas"] is None for m in d["municipios"])
