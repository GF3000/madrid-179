"""Esquemas de entrada y salida de la API: el contrato que usan el prototipo y la app."""
from typing import Literal

from pydantic import BaseModel, Field

Importancia = Literal["Me da igual", "No lo sé", "Poco importante", "Muy importante"]


# ------------------------------------------------------------------ entrada
class Preferencias(BaseModel):
    transporte: Importancia = "Me da igual"
    ayudas: Importancia = "Me da igual"


class Filtros(BaseModel):
    estacion_max_km: float | None = Field(None, ge=0, description="Imprescindible: estación ferroviaria a ≤ X km")
    solo_con_ayudas: bool = Field(False, description="Imprescindible: excluir municipios sin ayudas (nivel Bajo)")


class PeticionRanking(BaseModel):
    preferencias: Preferencias = Preferencias()
    filtros: Filtros = Filtros()
    limite: int | None = Field(None, ge=1, le=179)


class PeticionConsulta(BaseModel):
    evidencia: dict[str, str] = Field(default_factory=dict, examples=[{"Talento": "Alto", "Distancia_Madrid": "Lejos"}])


# ------------------------------------------------------------------- salida
class Validacion(BaseModel):
    repeticiones: int
    particiones: int
    acierto: list[float]
    log_loss: list[float]
    acierto_azar: float
    log_loss_uniforme: float


class Nodo(BaseModel):
    columna: str
    estados: list[str]
    cortes: list[float]


class Meta(BaseModel):
    version_modelo: str
    entrenado: str
    huella_dataset: str | None
    validacion: Validacion | None
    aviso: str
    objetivo: str
    padres_objetivo: list[str]
    nodos: dict[str, Nodo]
    preferencias: list[str]
    importancias: list[str]
    filtros_base: list[str]
    municipios: int
    candidatos_por_defecto: int


class Municipio(BaseModel):
    ine5: str
    municipio: str
    poblacion: int
    candidato: bool
    nivel_ayudas: str
    dist_ferro_km: float
    estados: dict[str, str]


class FilaRanking(BaseModel):
    posicion: int
    ine5: str
    municipio: str
    puntuacion: float
    desglose: dict[str, float]
    p_alta_red: float
    prediccion_ga2m_pct: float
    nivel_ayudas: str
    dist_ferro_km: float


class RespuestaRanking(BaseModel):
    candidatos: int
    pesos: dict[str, float]
    resultados: list[FilaRanking]


class Aportacion(BaseModel):
    termino: str
    etiqueta: str
    aportacion_pp: float
    valores: dict[str, float]


class FichaGA2M(BaseModel):
    prediccion_pct: float
    intercepto_pct: float
    percentil: float | None
    aportaciones: list[Aportacion]


class FichaRed(BaseModel):
    estados: dict[str, str]
    probabilidades: dict[str, float]
    padres: dict[str, str]
    percentil: float | None


class Ficha(BaseModel):
    ine5: str
    municipio: str
    poblacion: int
    candidato: bool
    motivo_exclusion: list[str] | None
    posicion: int | None
    puntuacion: float | None
    de: int
    ga2m: FichaGA2M
    red: FichaRed
    discrepancia: str | None
    preferencias: dict[str, dict[str, float | str]]


class MunicipioConsulta(BaseModel):
    ine5: str
    municipio: str
    candidato: bool


class RespuestaConsulta(BaseModel):
    evidencia: dict[str, str]
    probabilidades: dict[str, float]
    a_priori: dict[str, float]
    municipios: list[MunicipioConsulta]
