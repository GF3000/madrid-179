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


class RespuestaEjemplo(BaseModel):
    texto: str
    sector: str | None


class NegocioUsuario(BaseModel):
    sector: str | None = Field(None, max_length=80, examples=["ciberseguridad"])
    resumen: str | None = Field(None, max_length=600, description="Lo que entendió /interpretar del negocio")


class PeticionExplicacion(BaseModel):
    clase: str | None = Field(None, max_length=60, description="Grupo que muestra la app (depende de las preferencias)")
    preferencias: dict[str, Importancia | PreferenciaUsuario] = Field(default_factory=dict)
    negocio: NegocioUsuario | None = Field(None, description="Si el usuario describió su negocio, la explicación se adapta a él")


class ComprobacionExplicacion(BaseModel):
    corregida: bool = Field(description="Se pidió al LLM corregir frases que incumplían las reglas")
    descartadas: int = Field(description="Frases descartadas por seguir incumpliéndolas")


class RespuestaExplicacion(BaseModel):
    titular: str
    mejor: list[str]
    peor: list[str]
    apoyos: dict[str, list[list[str]]] = Field(description="Hechos de la ficha en que se apoya cada frase")
    comprobacion: ComprobacionExplicacion


class ComponenteNecesidad(BaseModel):
    columna: str
    etiqueta: str
    sentido: Literal["alto", "bajo"]


class Necesidad(BaseModel):
    componentes: list[ComponenteNecesidad]
    nota: str


class Cuadrante(BaseModel):
    id: Literal["oportunidad", "apoyo", "autonomo", "vigilar"]
    nombre: str
    lectura: str


class ValorComponente(BaseModel):
    valor: float
    percentil: float


class Freno(BaseModel):
    termino: str
    etiqueta: str
    aportacion_pp: float
    tipo: Literal["palanca", "estructural"]
    lectura: str | None


class OficinasContexto(BaseModel):
    locales: int = Field(description="Locales de uso oficinas en el Catastro")
    por_1000hab: float
    coworking: int = Field(description="Espacios de coworking en OpenStreetMap (muy incompleto)")


class Leader(BaseModel):
    grupo: str = Field(description="Grupo de Acción Local")
    fuente: str = Field(description="Convenio en el BOCM")


class AyudasContexto(BaseModel):
    leader: Leader | None
    irpf_menos_2500: bool = Field(description="Deducciones autonómicas del IRPF por traslado y compra de vivienda")
    pir_sin_cofinanciacion: bool = Field(description="PIR 2022-2026: no cofinancia sus inversiones")
    anio_padron: str = Field(description="Padrón a 1 de enero con que se aplica el umbral de 2.500 habitantes")


class ContextoPolitica(BaseModel):
    """Datos de contexto, no resultado del modelo."""
    oficinas: OficinasContexto
    ayudas: AyudasContexto | None = Field(description="null si falta data/processed/ayudas_oficiales.csv")


class MunicipioDiagnostico(BaseModel):
    ine5: str
    municipio: str
    poblacion: int
    distancia: str = Field(description="Estado del nodo Distancia_Madrid (Cerca, Media, Lejos)")
    candidato: bool
    necesidad: float = Field(description="Media de percentiles de los componentes (0-100)")
    componentes: dict[str, ValorComponente]
    viabilidad: float = Field(description="Percentil 0-100 de la predicción del GA²M entre los 178")
    cuadrante: Literal["oportunidad", "apoyo", "autonomo", "vigilar"]
    frenos: list[Freno]
    freno_palanca: Freno | None
    contexto: ContextoPolitica


class RespuestaDiagnostico(BaseModel):
    corte: float
    aviso: str
    necesidad: Necesidad
    cuadrantes: list[Cuadrante]
    municipios: list[MunicipioDiagnostico]
    contexto_nota: str
