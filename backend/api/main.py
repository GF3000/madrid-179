"""API de Madrid 179.

Arranque (desde la raíz del repo):
    .venv/Scripts/python -m uvicorn api.main:app --app-dir backend --reload
Documentación interactiva: http://localhost:8000/docs · App: http://localhost:8000/ (si está compilada,
`npm run build` en frontend/app) · Prototipo: http://localhost:8000/prototipo/
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from madrid179 import artefactos, asistente, limites
from madrid179.config import ARTEFACTO, RAIZ
from madrid179.servicio import ErrorEvidencia, Servicio

from .esquemas import (Ficha, Meta, Municipio, PeticionConsulta, PeticionExplicacion, PeticionInterpretar,
                       PeticionRanking, RespuestaConsulta, RespuestaDiagnostico, RespuestaEjemplo,
                       RespuestaExplicacion, RespuestaInterpretar, RespuestaRanking)

PROTOTIPO = RAIZ / "frontend" / "prototipo"
APP = RAIZ / "frontend" / "app" / "dist"
GEOMETRIA = RAIZ / "data" / "processed" / "municipios.geojson"  # backend/pipeline/limites_municipales.py


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


def _cliente(request: Request):
    """IP del visitante (uvicorn la toma de X-Forwarded-For con --proxy-headers; ver madrid179/limites.py)."""
    return request.client.host if request.client else None


def _demasiadas(e: limites.LimiteSuperado):
    return HTTPException(429, str(e), headers={"Retry-After": str(e.reintentar_s)})


@v1.get("/meta", response_model=Meta)
def meta(request: Request):
    return servicio(request).meta()


@v1.get("/municipios", response_model=list[Municipio])
def municipios(request: Request):
    return servicio(request).municipios()


@v1.post("/ranking", response_model=RespuestaRanking)
def ranking(peticion: PeticionRanking, request: Request):
    prefs = {k: v if isinstance(v, str) else v.model_dump() for k, v in peticion.preferencias.items()}
    try:
        return servicio(request).ranking(importancias=prefs, limite=peticion.limite, **peticion.filtros.model_dump())
    except KeyError as e:
        raise HTTPException(422, f"Preferencia desconocida: {e.args[0]}. Ver el catálogo en /api/v1/meta") from None
    except ValueError as e:
        raise HTTPException(422, str(e)) from None


@v1.get("/municipios/{ine5}", response_model=Ficha)
def ficha(ine5: str, request: Request):
    try:
        return servicio(request).ficha(ine5)
    except KeyError:
        raise HTTPException(404, f"Municipio desconocido: {ine5}") from None


@v1.post("/municipios/{ine5}/explicacion", response_model=RespuestaExplicacion)
def explicacion(ine5: str, peticion: PeticionExplicacion, request: Request):
    """Lo mejor y lo peor del municipio en lenguaje natural (LLM), redactado solo con los hechos de su ficha."""
    prefs = {k: v if isinstance(v, str) else v.model_dump() for k, v in peticion.preferencias.items()}
    try:
        hechos = servicio(request).hechos(ine5, peticion.clase, prefs,
                                          peticion.negocio.model_dump() if peticion.negocio else None)
    except KeyError:
        raise HTTPException(404, f"Municipio o preferencia desconocidos: {ine5}") from None
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    try:
        return asistente.explicar(hechos, cliente=_cliente(request))
    except limites.LimiteSuperado as e:
        raise _demasiadas(e) from None
    except asistente.AsistenteNoDisponible:
        raise HTTPException(503, "El asistente no está configurado (falta DEEPSEEK_API_KEY en .env)") from None
    except asistente.ErrorAsistente as e:
        raise HTTPException(502, str(e)) from None


@v1.post("/consulta", response_model=RespuestaConsulta)
def consulta(peticion: PeticionConsulta, request: Request):
    try:
        return servicio(request).consulta(peticion.evidencia)
    except ErrorEvidencia as e:
        raise HTTPException(422, str(e)) from None


@v1.get("/diagnostico", response_model=RespuestaDiagnostico)
def diagnostico(request: Request):
    """Diagnóstico territorial (Administración, «Dónde actuar»): necesidad de reequilibrio, viabilidad según el
    GA²M y frenos (palanca o estructural) de los 178 municipios sin la capital. Describe; no simula políticas."""
    return servicio(request).diagnostico()


@v1.post("/interpretar", response_model=RespuestaInterpretar)
def interpretar(peticion: PeticionInterpretar, request: Request):
    """Traduce la descripción libre del negocio en preferencias y requisitos (LLM). No puntúa: solo traduce;
    el resultado se valida contra el catálogo; la app lo aplica, lo muestra y permite deshacerlo."""
    try:
        return asistente.interpretar(peticion.texto, cliente=_cliente(request))
    except limites.LimiteSuperado as e:
        raise _demasiadas(e) from None
    except asistente.AsistenteNoDisponible:
        raise HTTPException(503, "El asistente no está configurado (falta DEEPSEEK_API_KEY en .env)") from None
    except asistente.ErrorAsistente as e:
        raise HTTPException(502, str(e)) from None


@v1.post("/ejemplo", response_model=RespuestaEjemplo)
def ejemplo(request: Request):
    """Inventa la descripción de un negocio (LLM) para probar el asistente sin tener que escribirla.
    Solo genera texto; para aplicarlo hay que pasarlo por /interpretar."""
    try:
        return asistente.ejemplo(cliente=_cliente(request))
    except limites.LimiteSuperado as e:
        raise _demasiadas(e) from None
    except asistente.AsistenteNoDisponible:
        raise HTTPException(503, "El asistente no está configurado (falta DEEPSEEK_API_KEY en .env)") from None
    except asistente.ErrorAsistente as e:
        raise HTTPException(502, str(e)) from None


@v1.get("/geometria", response_class=FileResponse,
        responses={200: {"content": {"application/geo+json": {}}}})
def geometria():
    """Límites municipales simplificados (WGS84) con el contorno de la Comunidad como miembro extra."""
    if not GEOMETRIA.exists():
        raise HTTPException(404, "Falta municipios.geojson: ejecuta backend/pipeline/limites_municipales.py")
    return FileResponse(GEOMETRIA, media_type="application/geo+json")


app.include_router(v1)

if PROTOTIPO.exists():
    app.mount("/prototipo", StaticFiles(directory=PROTOTIPO, html=True), name="prototipo")

if APP.exists():  # la app compilada ocupa la raíz; se monta al final para no tapar /api ni /docs
    app.mount("/", StaticFiles(directory=APP, html=True), name="app")
elif PROTOTIPO.exists():
    @app.get("/", include_in_schema=False)
    def inicio():
        return RedirectResponse("/prototipo/")
