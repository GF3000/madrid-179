import pytest

API = "/api/v1"


def test_meta(cliente):
    m = cliente.get(f"{API}/meta").json()
    assert m["municipios"] == 179 and m["candidatos_por_defecto"] == 139
    assert "débil" in m["aviso"]
    assert m["objetivo"] == "Viabilidad_Empresarial"


def test_municipios(cliente):
    ms = cliente.get(f"{API}/municipios").json()
    assert len(ms) == 179 and all(len(m["ine5"]) == 5 for m in ms)


def test_ranking_por_defecto(cliente):
    r = cliente.post(f"{API}/ranking", json={}).json()
    assert r["candidatos"] == 139 and len(r["resultados"]) == 139
    assert r["resultados"][0]["municipio"] == "Boadilla del Monte"
    assert r["resultados"][0]["puntuacion"] == 100


def test_ranking_con_preferencias_y_limite(cliente):
    r = cliente.post(f"{API}/ranking", json={"preferencias": {"transporte": "Muy importante"}, "limite": 10}).json()
    assert len(r["resultados"]) == 10
    for f in r["resultados"]:
        assert sum(f["desglose"].values()) == pytest.approx(f["puntuacion"], abs=0.05)


def test_ranking_filtros_que_vacian(cliente):
    r = cliente.post(f"{API}/ranking", json={"filtros": {"estacion_max_km": 0, "solo_con_ayudas": True}}).json()
    assert r["candidatos"] == len(r["resultados"])


@pytest.mark.parametrize("cuerpo", [
    {"preferencias": {"transporte": "Muchísimo"}},
    {"filtros": {"estacion_max_km": -1}},
    {"limite": 0},
])
def test_ranking_entrada_invalida(cliente, cuerpo):
    assert cliente.post(f"{API}/ranking", json=cuerpo).status_code == 422


def test_ficha(cliente):
    f = cliente.get(f"{API}/municipios/28149").json()  # Torrejón de la Calzada: GA²M y red discrepan
    assert f["candidato"] and f["posicion"] == 8
    assert sum(f["red"]["probabilidades"].values()) == pytest.approx(1, abs=1e-3)
    suma = f["ga2m"]["intercepto_pct"] + sum(a["aportacion_pp"] for a in f["ga2m"]["aportaciones"])
    assert suma == pytest.approx(f["ga2m"]["prediccion_pct"], abs=1e-3)
    assert f["discrepancia"]


def test_ficha_no_candidato(cliente):
    f = cliente.get(f"{API}/municipios/28079").json()
    assert not f["candidato"] and f["motivo_exclusion"] == ["excluir_madrid_capital"] and f["posicion"] is None


def test_ficha_desconocida(cliente):
    assert cliente.get(f"{API}/municipios/99999").status_code == 404


def test_consulta(cliente):
    r = cliente.post(f"{API}/consulta", json={"evidencia": {"Talento": "Alto", "Distancia_Madrid": "Lejos"}}).json()
    assert sum(r["probabilidades"].values()) == pytest.approx(1, abs=1e-3)
    assert all(m["ine5"] for m in r["municipios"])


@pytest.mark.parametrize("evidencia", [
    {"Talento": "Altísimo"}, {"Nodo_Inventado": "Alto"}, {"Viabilidad_Empresarial": "Alta"},
])
def test_consulta_invalida(cliente, evidencia):
    r = cliente.post(f"{API}/consulta", json={"evidencia": evidencia})
    assert r.status_code == 422 and r.json()["detail"]
