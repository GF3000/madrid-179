"""Convocatorias abiertas de la BDNS (#13): fuera del modelo, generales en /convocatorias y por tamaño en la ficha."""
import json

API = "/api/v1"


def test_convocatorias_generales(cliente):
    r = cliente.get(f"{API}/convocatorias").json()
    assert r["fecha_consulta"] and r["fecha_consulta"] in r["aviso"] and "BDNS" in r["aviso"]
    assert r["convocatorias"], "la tabla revisada no debería estar vacía"
    for c in r["convocatorias"]:
        assert c["max_habitantes"] is None  # las restringidas por tamaño van a la ficha
        assert c["url"].startswith("https://www.infosubvenciones.es/") and c["url"].endswith(c["num"])
        assert c["perfiles"] and set(c["perfiles"]) <= set(r["perfiles"])


def test_ficha_convocatorias_por_tamano(cliente):
    """Las de comercio en municipios de menos de 1.000 habitantes: en Madarcos sí, en Getafe no."""
    pequeno = cliente.get(f"{API}/municipios/28078").json()
    assert pequeno["poblacion"] < 1000
    assert pequeno["convocatorias"] and all(c["max_habitantes"] == 1000 for c in pequeno["convocatorias"])
    assert cliente.get(f"{API}/municipios/28065").json()["convocatorias"] == []


def test_interpretar_perfiles_ayudas(cliente, monkeypatch):
    from madrid179 import asistente
    falsa = {"resumen": "Vas a contratar.", "sector": "software", "preferencias": {}, "filtros": {},
             "perfiles_ayudas": ["contratar", "innovar", "contratar", "volar"], "dudas": []}
    monkeypatch.setattr(asistente, "_llamar", lambda texto: json.dumps(falsa))
    r = cliente.post(f"{API}/interpretar", json={"texto": "Empresa de software que va a contratar"}).json()
    assert r["perfiles_ayudas"] == ["contratar", "innovar"]  # sin repetidos ni perfiles fuera de la lista
    assert any("volar" in a for a in r["avisos"])
    sin = {**falsa, "perfiles_ayudas": None}
    monkeypatch.setattr(asistente, "_llamar", lambda texto: json.dumps(sin))
    assert cliente.post(f"{API}/interpretar", json={"texto": "Empresa de software"}).json()["perfiles_ayudas"] == []
