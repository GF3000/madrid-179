"""Configuración del modelo: nodos, DAG, filtros duros e hiperparámetros.

Fuente única para el pipeline (red_bayesiana_viabilidad.py, auditoría, diagramas) y para la API.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATASET = RAIZ / "data" / "processed" / "dataset_bn_municipios.csv"
ARTEFACTO = RAIZ / "data" / "processed" / "modelo.joblib"

ESS = 10  # equivalent sample size del prior BDeu (179 filas -> prior moderado)
OBJETIVO = "Viabilidad_Empresarial"

# ---------------------------------------------------------------------------
# 1. Filtros duros (preprocesado tabular, NO entran en la red)
# ---------------------------------------------------------------------------
FILTROS = {
    # Objetivo de reequilibrio: la capital no es candidata a recibir la oficina deslocalizada
    "excluir_madrid_capital": lambda d: d.index != "28079",
    # Mínimo de oferta terciaria existente (Catastro: unidades urbanas de uso oficinas)
    "min_uu_oficinas": lambda d: d.uu_oficinas >= 1,
    # Opcional, según preferencias del negocio: exigir elegibilidad a ayudas de despoblación (<20.000 hab.)
    # "solo_elegibles_despoblacion": lambda d: d.poblacion < 20000,
}

# ---------------------------------------------------------------------------
# 2. Nodos de la red: columna origen, estados y método de corte
#    'terciles' -> cortes en p33/p66 de la distribución real de los 179 municipios
# ---------------------------------------------------------------------------
NODOS = {
    "Distancia_Madrid":          ("dist_sol_km",             ["Cerca", "Media", "Lejos"], "terciles"),
    "Talento":                   ("pct_estudios_superiores", ["Bajo", "Medio", "Alto"],   "terciles"),
    "Acceso_Ferroviario":        ("paradas_ferro",           ["No", "Si"],                "binario>0"),
    "Coste_Inmobiliario":        ("vc_residencial_por_uu",   ["Bajo", "Medio", "Alto"],   "terciles"),
    "Renta":                     ("rdb_per_capita",          ["Baja", "Media", "Alta"],   "terciles"),
    "Especializacion_Servicios": ("pct_up_servicios_prof",   ["Baja", "Media", "Alta"],   "terciles"),
    "Dinamismo_Demografico":     ("crec_pob_5a",             ["Bajo", "Medio", "Alto"],   "terciles"),
    "Viabilidad_Empresarial":    ("tasa_neta_emp",           ["Baja", "Media", "Alta"],   "terciles"),
}
EVIDENCIAS = [n for n in NODOS if n != OBJETIVO]

# ---------------------------------------------------------------------------
# 3. DAG (máx. 2 padres por nodo)
# ---------------------------------------------------------------------------
EDGES = [
    ("Distancia_Madrid", "Acceso_Ferroviario"),
    ("Distancia_Madrid", "Coste_Inmobiliario"),
    ("Talento", "Coste_Inmobiliario"),
    ("Talento", "Renta"),
    ("Talento", "Especializacion_Servicios"),
    ("Distancia_Madrid", "Especializacion_Servicios"),
    ("Distancia_Madrid", "Dinamismo_Demografico"),
    ("Coste_Inmobiliario", "Dinamismo_Demografico"),
    ("Dinamismo_Demografico", "Viabilidad_Empresarial"),
    ("Especializacion_Servicios", "Viabilidad_Empresarial"),
]
PADRES_OBJETIVO = [p for p, h in EDGES if h == OBJETIVO]

# Ranking final (PENDIENTES #5). Con evidencia completa la red solo da 9 niveles; un GA²M (EBM) sobre las
# mismas 7 variables continuas desempata y ordena mejor (ga2m_desempate.py, CV-5 x 5, Spearman con la tasa
# neta: BN 0,284 · GA²M 0,398 · media de rangos 0,369 · lexicográfico 0,291).
# Decisión 2026-10-07 (PENDIENTES #40, opción b): el GA²M da la puntuación; la red bayesiana explica,
# atiende consultas con evidencia parcial y sostiene el simulador do() de la Administración.
#   "ga2m"           -> puntuación = percentil del GA²M entre los candidatos, 0-100 (por defecto)
#   "media_rangos"   -> media del percentil de la red y del percentil del GA²M
#   "lexicografico"  -> nivel de la red y el GA²M solo desempata dentro de cada nivel
#   "bn"             -> solo la red, 100 × P(Alta)
COMBINACION = "ga2m"
EBM_KW = dict(interactions=5, max_bins=32, min_samples_leaf=10, outer_bags=8, learning_rate=0.02,
              max_rounds=3000, random_state=0)
FEATURES_GA2M = [NODOS[n][0] for n in EVIDENCIAS]

# Pesos de la Opción B (contribución de cada estado padre a la utilidad de viabilidad, escala 0-1)
PESOS_B = {"Dinamismo_Demografico": 0.55, "Especializacion_Servicios": 0.45}
TEMPERATURA_B = 0.25  # menor = CPT más determinista

AVISO_SENAL = ("Señal débil: el modelo ordena algo mejor que el azar, pero sus probabilidades no están "
               "calibradas (log-loss similar a la distribución uniforme). Usa el orden como orientación, "
               "no como predicción. Son asociaciones, no efectos causales.")
