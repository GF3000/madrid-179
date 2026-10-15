"""Límite de llamadas al LLM (madrid179/limites.py) y su respuesta 429 en la API."""
import json

import pytest

from madrid179 import asistente, limites

API = "/api/v1"


class Reloj:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_limite_por_cliente_y_ventana_deslizante():
    reloj = Reloj()
    lim = limites.Limitador(por_cliente_hora=3, global_hora=0, global_dia=0, reloj=reloj)
    for _ in range(3):
        lim.consumir("1.1.1.1")
    with pytest.raises(limites.LimiteSuperado) as e:
        lim.consumir("1.1.1.1")
    assert 3590 < e.value.reintentar_s <= 3601
    lim.consumir("2.2.2.2")  # otro visitante no se ve afectado
    reloj.t += 3601  # pasada la hora, vuelve a poder
    lim.consumir("1.1.1.1")


def test_limite_global_por_hora_y_por_dia():
    reloj = Reloj()
    lim = limites.Limitador(por_cliente_hora=0, global_hora=2, global_dia=3, reloj=reloj)
    lim.consumir("a"), lim.consumir("b")
    with pytest.raises(limites.LimiteSuperado, match="muy solicitado"):
        lim.consumir("c")
    reloj.t += 3601
    lim.consumir("c")
    with pytest.raises(limites.LimiteSuperado, match="diario"):
        lim.consumir("d")
    reloj.t += 86400
    lim.consumir("d")


def test_rechazos_no_cuentan():
    reloj = Reloj()
    lim = limites.Limitador(por_cliente_hora=1, global_hora=0, global_dia=0, reloj=reloj)
    lim.consumir("x")
    for _ in range(5):
        with pytest.raises(limites.LimiteSuperado):
            lim.consumir("x")
    reloj.t += 3601
    lim.consumir("x")  # los intentos rechazados no alargan el bloqueo


def test_api_responde_429_y_la_cache_no_gasta(cliente, monkeypatch):
    llamadas = []

    def falso(texto, sistema=None, temperatura=0.2):
        llamadas.append(1)
        return json.dumps({"titular": "Un municipio tranquilo.", "mejor": ["Es tranquilo."], "peor": []})
    monkeypatch.setattr(asistente, "_llamar", falso)
    monkeypatch.setattr(asistente, "LIMITE", limites.Limitador(por_cliente_hora=1, global_hora=0, global_dia=0))
    asistente._CACHE_EXPLICAR.clear()

    assert cliente.post(f"{API}/municipios/28149/explicacion", json={}).status_code == 200
    assert cliente.post(f"{API}/municipios/28149/explicacion", json={}).status_code == 200  # caché: no gasta
    r = cliente.post(f"{API}/municipios/28087/explicacion", json={})
    assert r.status_code == 429 and int(r.headers["Retry-After"]) > 0 and "asistente" in r.json()["detail"]
    r = cliente.post(f"{API}/interpretar", json={"texto": "Una consultora de diez personas"})
    assert r.status_code == 429
    assert len(llamadas) == 1
