"""Esquemas de entrada y salida de la API: el contrato que usan el prototipo y la app."""
from typing import Literal

from pydantic import BaseModel, Field

Importancia = Literal["Me da igual", "No lo sé", "Poco importante", "Muy importante"]


# ------------------------------------------------------------------ entrada
class PreferenciaUsuario(BaseModel):
    importancia: Importancia = "Me da igual"
    sentido: str | None = Field(None, description="Solo en preferencias con dos sentidos (ver /meta, catálogo)")


class Filtros(BaseModel):
    estacion_max_km: float | None = Field(None, ge=0, description="Imprescindible: estación ferroviaria a ≤ X km")
    solo_con_ayudas: bool = Field(False, description="Imprescindible: excluir municipios sin ayudas (nivel Bajo)")
    madrid_max_km: float | None = Field(None, ge=0, description="Imprescindible: a ≤ X km de la Puerta del Sol")
    madrid_min_km: float | None = Field(None, ge=0, description="Imprescindible: a ≥ X km de la Puerta del Sol")
    poblacion_min: int | None = Field(None, ge=0, description="Imprescindible: al menos X habitantes")
    poblacion_max: int | None = Field(None, ge=0, description="Imprescindible: como mucho X habitantes")
    con_coworking: bool = Field(False, description="Imprescindible: con coworking en OpenStreetMap")


class PeticionRanking(BaseModel):
    preferencias: dict[str, Importancia | PreferenciaUsuario] = Field(
        default_factory=dict, description="Clave del catálogo (/meta) → importancia, o {importancia, sentido}",
        examples=[{"transporte": "Muy importante", "distancia_madrid": {"importancia": "Poco importante", "sentido": "lejos"}}])
    filtros: Filtros = Filtros()
    limite: int | None = Field(None, ge=1, le=179)


class PeticionInterpretar(BaseModel):
    texto: str = Field(..., min_length=10, max_length=2000,
                       examples=["Estudio de diseño de 8 personas; buscamos alquiler moderado y buen transporte."])


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


class Sentido(BaseModel):
    valor: str
    etiqueta: str


class PreferenciaCatalogo(BaseModel):
    clave: str
    nombre: str
    grupo: str
    descripcion: str
    sentidos: list[Sentido] | None
    en_modelo: bool


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
    catalogo: list[PreferenciaCatalogo]
    importancias: list[str]
    tope_preferencias: float
    asistente_disponible: bool
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


class PreferenciaFicha(BaseModel):
    dato: str = Field(..., description="El hecho del municipio, en texto")
    utilidad: dict[str, float] = Field(..., description="Utilidad 0-1 entre los candidatos por sentido ('' = único)")


class Imagen(BaseModel):
    url: str
    autor: str
    licencia: str | None
    url_licencia: str | None
    fuente: str | None


class Wikipedia(BaseModel):
    titulo: str | None
    resumen: str | None
    url: str | None
    imagen: Imagen | None


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
    preferencias: dict[str, PreferenciaFicha]
    wikipedia: Wikipedia | None = Field(None, description="Resumen (CC BY-SA 4.0) y foto de Commons con su licencia")


class MunicipioConsulta(BaseModel):
    ine5: str
    municipio: str
    candidato: bool


class RespuestaConsulta(BaseModel):
    evidencia: dict[str, str]
    probabilidades: dict[str, float]
    a_priori: dict[str, float]
    municipios: list[MunicipioConsulta]


class PreferenciaInterpretada(BaseModel):
    importancia: Importancia
    sentido: str | None
    motivo: str


class RespuestaInterpretar(BaseModel):
    resumen: str
    sector: str | None
    preferencias: dict[str, PreferenciaInterpretada]
    filtros: dict[str, float | int | bool]
    dudas: list[str]
    avisos: list[str]


class PeticionExplicacion(BaseModel):
    clase: str | None = Field(None, max_length=60, description="Grupo que muestra la app (depende de las preferencias)")
    preferencias: dict[str, Importancia | PreferenciaUsuario] = Field(default_factory=dict)


class RespuestaExplicacion(BaseModel):
    titular: str
    mejor: list[str]
    peor: list[str]
