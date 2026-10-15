import pytest
from fastapi.testclient import TestClient

from madrid179 import artefactos
from madrid179.servicio import Servicio


@pytest.fixture(scope="session")
def art():
    """El artefacto en disco (lo genera backend/pipeline/entrenar.py; la CI lo entrena antes de los tests)."""
    return artefactos.cargar()


@pytest.fixture(scope="session")
def servicio(art):
    return Servicio(art)


@pytest.fixture(scope="session")
def cliente():
    from api.main import app
    with TestClient(app) as c:
        yield c
