import pytest

API = "/api/v1"


def test_meta(cliente):
    m = cliente.get(f"{API}/meta").json()
    assert m["municipios"] == 179 and m["candidatos_por_defecto"] == 139
    assert "causales" in m["aviso"]  # el aviso siempre recuerda que son asociaciones
    assert m["objetivo"] == "Viabilidad_Empresarial"


def test_municipios(cliente):
    ms = cliente.get(f"{API}/municipios").json()
    assert len(ms) == 179 and all(len(m["ine5"]) == 5 for m in ms)


def test_ranking_por_defecto(cliente, servicio):
    r = cliente.post(f"{API}/ranking", json={}).json()
    assert r["candidatos"] == 139 and len(r["resultados"]) == 139
    assert [f["ine5"] for f in r["resultados"]] == list(servicio.base.index)
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
    octavo = cliente.post(f"{API}/ranking", json={"limite": 8}).json()["resultados"][-1]
    f = cliente.get(f"{API}/municipios/{octavo['ine5']}").json()
    assert f["candidato"] and f["posicion"] == 8 and f["puntuacion"] == octavo["puntuacion"]
    assert sum(f["red"]["probabilidades"].values()) == pytest.approx(1, abs=1e-3)
    suma = f["ga2m"]["intercepto_pct"] + sum(a["aportacion_pp"] for a in f["ga2m"]["aportaciones"])
    assert suma == pytest.approx(f["ga2m"]["prediccion_pct"], abs=1e-3)


def test_discrepancia(servicio):
    """El aviso aparece exactamente cuando los percentiles de la red y del GA²M distan ≥ 50 puntos."""
    from madrid179.servicio import UMBRAL_DISCREPANCIA
    b = servicio.base
    for ine5 in b.index[::7]:
        esperado = abs(b.loc[ine5, "percentil_ga2m"] - b.loc[ine5, "percentil_bn"]) >= UMBRAL_DISCREPANCIA
        assert bool(servicio.ficha(ine5)["discrepancia"]) == esperado


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


def test_geometria(cliente, servicio):
    r = cliente.get(f"{API}/geometria")
    assert r.status_code == 200
    g = r.json()
    assert {f["properties"]["ine5"] for f in g["features"]} == {m["ine5"] for m in servicio.municipios()}
    assert g["contorno"]["geometry"]["type"] in ("Polygon", "MultiPolygon")


def test_meta_catalogo(cliente):
    m = cliente.get(f"{API}/meta").json()
    assert len(m["catalogo"]) == 15 and m["tope_preferencias"] == 3
    assert {"clave", "nombre", "grupo", "sentidos", "en_modelo"} <= set(m["catalogo"][0])


def test_ranking_preferencias_con_sentido(cliente):
    r = cliente.post(f"{API}/ranking", json={
        "preferencias": {"tamano": {"importancia": "Muy importante", "sentido": "pequeno"}, "coste": "Poco importante"},
        "filtros": {"madrid_max_km": 50}}).json()
    assert r["pesos"]["tamano"] > 0 and r["pesos"]["coste"] > 0 and r["pesos"]["transporte"] == 0
    assert set(r["resultados"][0]["desglose"]) == {"modelo", "tamano", "coste"}


@pytest.mark.parametrize("cuerpo", [{"preferencias": {"inventada": "Muy importante"}},
                                    {"preferencias": {"tamano": {"importancia": "Muy importante", "sentido": "x"}}},
                                    {"filtros": {"poblacion_min": -5}}])
def test_ranking_preferencia_invalida(cliente, cuerpo):
    assert cliente.post(f"{API}/ranking", json=cuerpo).status_code == 422


def test_ficha_preferencias(cliente):
    f = cliente.get(f"{API}/municipios/28149").json()
    assert len(f["preferencias"]) == 15
    assert set(f["preferencias"]["tamano"]["utilidad"]) == {"grande", "pequeno"}
    assert all(0 <= u <= 1 for p in f["preferencias"].values() for u in p["utilidad"].values())


def test_interpretar_sin_clave(cliente, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    r = cliente.post(f"{API}/interpretar", json={"texto": "Una consultora de diez personas"})
    assert r.status_code == 503


def test_interpretar_sanea_la_respuesta(cliente, monkeypatch):
    import json
    from madrid179 import asistente
    falsa = {"resumen": "Buscas un sitio barato con tren.", "sector": "diseño",
             "preferencias": {"coste": {"importancia": "Muy importante", "motivo": "lo pides"},
                              "transporte": {"importancia": "Poco importante", "motivo": ""},
                              "tamano": {"importancia": "Muy importante", "sentido": "mediano"},
                              "inventada": {"importancia": "Muy importante"},
                              "talento": {"importancia": "Importantísimo"}},
             "filtros": {"madrid_max_km": 40, "poblacion_min": "mucha", "con_coworking": True, "volar": 3},
             "dudas": ["¿Necesitas tren?", "", 7]}
    monkeypatch.setattr(asistente, "_llamar", lambda texto: json.dumps(falsa))
    r = cliente.post(f"{API}/interpretar", json={"texto": "Estudio de diseño de 8 personas"}).json()
    assert set(r["preferencias"]) == {"coste", "transporte"}
    assert r["filtros"] == {"madrid_max_km": 40, "con_coworking": True}
    assert r["dudas"] == ["¿Necesitas tren?"] and len(r["avisos"]) == 5
    # lo que devuelve el asistente es una petición válida para /ranking
    pet = {"preferencias": {k: {"importancia": v["importancia"], "sentido": v["sentido"]} for k, v in r["preferencias"].items()},
           "filtros": r["filtros"]}
    assert cliente.post(f"{API}/ranking", json=pet).status_code == 200


def test_interpretar_texto_corto(cliente):
    assert cliente.post(f"{API}/interpretar", json={"texto": "hola"}).status_code == 422


def test_ejemplo(cliente, monkeypatch):
    import json
    from madrid179 import asistente
    recibido = {}

    def falso(texto, sistema=None, temperatura=0.2):
        recibido.update(json.loads(texto))
        return json.dumps({"texto": "Somos una gestoría de 8 personas y queremos tren cerca.", "sector": "gestoría"})
    monkeypatch.setattr(asistente, "_llamar", falso)
    r = cliente.post(f"{API}/ejemplo").json()
    assert r == {"texto": "Somos una gestoría de 8 personas y queremos tren cerca.", "sector": "gestoría"}
    assert recibido["sector"] in asistente.SECTORES_EJEMPLO and 2 <= len(recibido["necesidades"]) <= 3
    monkeypatch.setattr(asistente, "_llamar", lambda *a, **k: json.dumps({"texto": ""}))
    assert cliente.post(f"{API}/ejemplo").status_code == 502
    monkeypatch.undo()  # vuelve el _llamar real, que sin clave no llega a la red
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert cliente.post(f"{API}/ejemplo").status_code == 503


def test_ficha_wikipedia(cliente):
    w = cliente.get(f"{API}/municipios/28070").json()["wikipedia"]
    assert w["titulo"].startswith("Horcajo de la Sierra")  # enlazado por código INE, no se confunde con Horcajuelo
    assert w["resumen"] and w["imagen"]["url"].startswith("https://") and "wikimedia.org/" in w["imagen"]["url"] and "?" not in w["imagen"]["url"]
    assert w["imagen"]["autor"] and w["imagen"]["licencia"]


def test_hechos_solo_lo_calculado(servicio):
    h = servicio.hechos("28149", "Muy favorable", {"tamano": {"importancia": "Muy importante", "sentido": "pequeno"}})
    assert h["grupo"] == "Muy favorable" and h["factores"]["a favor"]
    assert all(f["fuerza"] in {"mucho", "bastante", "algo"} for lado in h["factores"].values() for f in lado)
    assert h["preferencias_del_usuario"][0]["encaje"] in {"alto", "medio", "bajo"}
    assert servicio.hechos("28087")["municipio"] == "Los Molinos"  # el LLM recibe el nombre legible
    fuera = servicio.hechos("28079")
    assert fuera["fuera_del_analisis"] and not fuera["factores"]["a favor"] and not fuera["factores"]["en contra"]


def test_valor_vivienda_se_lee_como_demanda(servicio):
    """Un valor de la vivienda alto suma en el GA²M (señal de demanda), pero no debe leerse como «es caro, y es bueno»."""
    from madrid179.asistente import INSTRUCCIONES_EXPLICAR
    aport = {a["termino"]: a for a in servicio.ficha("28080")["ga2m"]["aportaciones"]}  # Majadahonda
    vc = aport["vc_residencial_por_uu"]
    assert vc["aportacion_pp"] > 0 and "demanda" in vc["lectura"] and "Coste inmobiliario bajo" in vc["lectura"]
    assert aport["rdb_per_capita"]["lectura"] is None  # solo las variables que pueden confundir llevan lectura
    h = servicio.hechos("28080")
    f = next(f for f in h["factores"]["a favor"] if f["factor"].startswith("Valor de la vivienda"))
    assert f["nivel"] == "alto" and f["como_leerlo"] == vc["lectura"] and f["para_quien_se_instala"] == "inconveniente"
    assert "valor de la vivienda" in h["perfil"] and "coste inmobiliario" not in h["perfil"]
    assert "como_leerlo" in INSTRUCCIONES_EXPLICAR and "para_quien_se_instala" in INSTRUCCIONES_EXPLICAR


def _id(hechos, prefijo, lado=None):
    """Id del factor de los hechos cuya etiqueta empieza por `prefijo`."""
    lados = [lado] if lado else ["a favor", "en contra"]
    return next(f["id"] for l in lados for f in hechos["factores"][l] if f["factor"].startswith(prefijo))


def test_oficinas_senal_dudosa(servicio):
    """Muchas oficinas restan en el GA²M (señal dudosa), pero para quien se instala son una ventaja."""
    of = next(a for a in servicio.ficha("28083")["ga2m"]["aportaciones"] if a["termino"] == "uu_oficinas_por_1000hab")
    assert of["aportacion_pp"] < 0 and of["senal_dudosa"] and of["para_quien_se_instala"] == "ventaja"
    assert "Oferta de oficinas" in of["lectura"]
    f = next(f for f in servicio.hechos("28083")["factores"]["en contra"] if f["factor"].startswith("Oficinas"))
    assert f["senal"] == "dudosa" and f["para_quien_se_instala"] == "ventaja"


def test_explicacion(cliente, monkeypatch):
    """La respuesta del LLM se revisa: si incumple reglas se pide una corrección y lo que siga mal se descarta."""
    import json
    from madrid179 import asistente
    llamadas = []

    def falso(texto, sistema=None, temperatura=0.2):
        entrada = json.loads(texto)
        llamadas.append(entrada)
        h = entrada.get("hechos", entrada)
        fa = next(f["id"] for f in h["factores"]["a favor"] if "senal" not in f and "para_quien_se_instala" not in f)
        fc = next(f["id"] for f in h["factores"]["en contra"] if "senal" not in f and "para_quien_se_instala" not in f)
        if "problemas" not in entrada:
            return json.dumps({"titular": "Un municipio joven y en crecimiento.",
                               "mejor": [{"texto": "Crece mucho.", "apoyo": [fa]},
                                         {"texto": "Tiene 999.999 empresas.", "apoyo": [fa]},
                                         {"texto": "Le resta, pero lo pongo aquí.", "apoyo": [fc]}],
                               "peor": [{"texto": "Le resta algo.", "apoyo": [fc]}]})
        return json.dumps({"titular": "Un municipio joven y en crecimiento.",
                           "mejor": [{"texto": "Crece mucho.", "apoyo": [fa]}],
                           "peor": [{"texto": "Le resta algo.", "apoyo": [fc]},
                                    {"texto": "Esto provoca cierres.", "apoyo": [fc]}]})
    monkeypatch.setattr(asistente, "_llamar", falso)
    asistente._CACHE_EXPLICAR.clear()
    r = cliente.post(f"{API}/municipios/28149/explicacion", json={"clase": "Muy favorable"}).json()
    assert r["titular"] == "Un municipio joven y en crecimiento."
    assert r["mejor"] == ["Crece mucho."] and r["peor"] == ["Le resta algo."]
    assert r["comprobacion"] == {"corregida": True, "descartadas": 1}  # «provoca» sigue mal tras la corrección
    assert len(r["apoyos"]["mejor"]) == 1 and r["apoyos"]["mejor"][0][0].endswith(")")  # factor (nivel)
    assert len(llamadas) == 2 and llamadas[0]["municipio"] == "Torrejón de la Calzada"
    problemas = " ".join(llamadas[1]["problemas"])
    assert "999.999" in problemas and "pone en lo mejor algo que resta" in problemas


def test_explicacion_adaptada_al_negocio(cliente, monkeypatch):
    """Con el negocio del usuario, el titular debe nombrar su actividad: si no, se pide una corrección."""
    import json
    from madrid179 import asistente
    llamadas = []

    def falso(texto, sistema=None, temperatura=0.2):
        llamadas.append(json.loads(texto))
        titular = "Favorable para una oficina." if len(llamadas) == 1 else "Favorable para tu empresa de ciberseguridad."
        return json.dumps({"titular": titular, "mejor": [{"texto": "Tiene buen perfil.", "apoyo": ["perfil"]}], "peor": []})
    monkeypatch.setattr(asistente, "_llamar", falso)
    asistente._CACHE_EXPLICAR.clear()
    negocio = {"sector": "ciberseguridad", "resumen": "Oficina de ciberseguridad de 12 personas."}
    r = cliente.post(f"{API}/municipios/28149/explicacion", json={"clase": "Favorable", "negocio": negocio}).json()
    assert llamadas[0]["negocio_del_usuario"] == negocio
    assert "no nombra la actividad" in llamadas[1]["problemas"][0]
    assert r["titular"] == "Favorable para tu empresa de ciberseguridad." and r["comprobacion"]["corregida"]


def test_revisar_reglas(servicio):
    """Cada regla del verificador de explicaciones, sobre Majadahonda con la preferencia de coste bajo."""
    from madrid179.asistente import revisar
    h = servicio.hechos("28080", "Favorable", {"coste": {"importancia": "Muy importante"}})
    vivienda, distancia = _id(h, "Valor de la vivienda"), _id(h, "Distancia a Madrid")
    talento, crecimiento = _id(h, "Talento", "a favor"), _id(h, "Crecimiento", "en contra")
    dudosa = next(f["id"] for l in h["factores"].values() for f in l if f.get("senal") == "dudosa")
    coste = h["preferencias_del_usuario"][0]
    assert coste["encaje"] == "bajo"

    def problemas(lado, texto, apoyo):
        return revisar({"titular": "", lado: [{"texto": texto, "apoyo": apoyo}]}, h)[1]

    assert not problemas("mejor", "Tiene mucho talento y 73.625 habitantes.", [talento])  # cifra de los hechos
    assert not problemas("peor", "El valor de la vivienda es alto: los locales serán más caros.", [vivienda])
    assert not problemas("peor", "No encaja con tu preferencia de coste bajo.", [coste["id"]])
    assert not problemas("peor", "La población crece poco.", [crecimiento])
    # el lado: lo que es un inconveniente para quien se instala no va en lo mejor aunque el GA²M lo sume
    assert problemas("mejor", "La vivienda vale mucho.", [vivienda])
    assert problemas("peor", "Estar cerca de Madrid es un coste.", [distancia])  # cerca = ventaja
    assert problemas("mejor", "La población crece poco.", [crecimiento])
    assert problemas("mejor", "Encaja con el coste.", [coste["id"]])
    assert problemas("mejor", "Tiene lo que buscas.", [dudosa])                      # señal dudosa
    assert problemas("mejor", "Tiene talento.", [])                                 # sin apoyo
    assert problemas("mejor", "Tiene talento.", ["F999"])                           # hecho inexistente
    assert problemas("mejor", "Tiene 12.345 empresas de talento.", [talento])       # cifra inventada
    assert problemas("mejor", "El talento garantiza el éxito.", [talento])          # lenguaje causal
    assert problemas("mejor", "Según el modelo, tiene talento.", [talento])         # jerga
    assert problemas("mejor", "Tiene talento y poca competencia.", [talento])       # mecanismo inventado
    assert problemas("mejor", "Es caro, pero tiene talento.", [talento])            # lo caro como ventaja
    assert revisar({"titular": "Majadahonda provoca empresas.", "mejor": []}, h)[1]  # el titular también se revisa


def test_explicacion_errores(cliente, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    from madrid179 import asistente
    asistente._CACHE_EXPLICAR.clear()
    assert cliente.post(f"{API}/municipios/28149/explicacion", json={}).status_code == 503
    assert cliente.post(f"{API}/municipios/99999/explicacion", json={}).status_code == 404

