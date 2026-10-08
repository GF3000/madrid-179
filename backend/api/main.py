"""API de Madrid 179.

Arranque (desde la raíz del repo):
    .venv/Scripts/python -m uvicorn api.main:app --app-dir backend --reload
Documentación interactiva: http://localhost:8000/docs · Prototipo: http://localhost:8000/
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from madrid179 import artefactos
from madrid179.config import ARTEFACTO, RAIZ
from madrid179.servicio import ErrorEvidencia, Servicio

from .esquemas import Ficha, Meta, Municipio, PeticionConsulta, PeticionRanking, RespuestaConsulta, RespuestaRanking

PROTOTIPO = RAIZ / "frontend" / "prototipo"


@asynccontextmanager
async def lifespan(app: FastAPI):
    ruta = Path(os.environ.get("MADRID179_MODELO", ARTEFACTO))
    app.state.servicio = Servicio(artefactos.cargar(ruta))
    yield


app = FastAPI(title="Madrid 179 API", version="1.0.0", lifespan=lifespan,
              description="Ranking, explicación y consultas del modelo de viabilidad empresarial municipal. "
                          "La señal del modelo es débil: el orden es orientativo (ver /api/v1/meta).")
app.add_middleware(CORSMiddleware, allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
                   allow_methods=["*"], allow_headers=["*"])

v1 = APIRouter(prefix="/api/v1")


def servicio(request: Request) -> Servicio:
    return request.app.state.servicio


@v1.get("/meta", response_model=Meta)
def meta(request: Request):
    return servicio(request).meta()


@v1.get("/municipios", response_model=list[Municipio])
def municipios(request: Request):
    return servicio(request).municipios()


@v1.post("/ranking", response_model=RespuestaRanking)
def ranking(peticion: PeticionRanking, request: Request):
    return servicio(request).ranking(importancias=peticion.preferencias.model_dump(),
                                     estacion_max_km=peticion.filtros.estacion_max_km,
                                     solo_con_ayudas=peticion.filtros.solo_con_ayudas,
                                     limite=peticion.limite)


@v1.get("/municipios/{ine5}", response_model=Ficha)
def ficha(ine5: str, request: Request):
    try:
        return servicio(request).ficha(ine5)
    except KeyError:
        raise HTTPException(404, f"Municipio desconocido: {ine5}") from None


@v1.post("/consulta", response_model=RespuestaConsulta)
def consulta(peticion: PeticionConsulta, request: Request):
    try:
        return servicio(request).consulta(peticion.evidencia)
    except ErrorEvidencia as e:
        raise HTTPException(422, str(e)) from None


app.include_router(v1)

if PROTOTIPO.exists():
    app.mount("/prototipo", StaticFiles(directory=PROTOTIPO, html=True), name="prototipo")

    @app.get("/", include_in_schema=False)
    def inicio():
        return RedirectResponse("/prototipo/")
