import pytest

from madrid179 import config


def test_clave_api_desde_entorno(monkeypatch):
    monkeypatch.setenv("CLAVE_DE_PRUEBA", "  sk-prueba  ")
    assert config.clave_api("CLAVE_DE_PRUEBA") == "sk-prueba"


def test_clave_api_falta(monkeypatch):
    monkeypatch.delenv("CLAVE_DE_PRUEBA", raising=False)
    with pytest.raises(RuntimeError, match="Falta CLAVE_DE_PRUEBA"):
        config.clave_api("CLAVE_DE_PRUEBA")
