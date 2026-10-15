"""Configuración del modelo: nodos, DAG, filtros duros e hiperparámetros.

Fuente única para el pipeline (red_bayesiana_viabilidad.py, auditoría, diagramas) y para la API.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]
# Secretos (claves de API) en .env en la raíz, fuera de git; ver .env.example. Las variables de entorno
# ya definidas (p. ej. en el despliegue) tienen prioridad sobre el fichero.
load_dotenv(RAIZ / ".env", override=False)


def clave_api(nombre="DEEPSEEK_API_KEY"):
    """Devuelve la clave o lanza un error claro si falta (nunca la escribe en logs)."""
    valor = os.environ.get(nombre, "").strip()
    if not valor:
        raise RuntimeError(f"Falta {nombre}: añádela a {RAIZ / '.env'} (ver .env.example) o como variable de entorno.")
    return valor

DATASET = RAIZ / "data" / "processed" / "dataset_bn_municipios.csv"
ARTEFACTO = RAIZ / "data" / "processed" / "modelo.joblib"

# Equivalent sample size del prior BDeu. Con 179 filas, ESS = 50 calibra mucho mejor que 10 (log-loss
# 1,009 frente a 1,103; uniforme 1,099) sin perder orden (experimento_red_ampliada.py, #37).
ESS = 50
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
    "Densidad":                  ("densidad_hab_km2",        ["Baja", "Media", "Alta"],   "terciles"),
    "Juventud":                  ("pct_menores_45",          ["Baja", "Media", "Alta"],   "terciles"),
    "Sanidad":                   ("sanidad_por_1000hab",     ["Baja", "Media", "Alta"],   "terciles"),
    "Paro":                      ("paro_por_100hab",         ["Bajo", "Medio", "Alto"],   "terciles"),
    "Viabilidad_Empresarial":    ("tasa_neta_emp",           ["Baja", "Media", "Alta"],   "terciles"),
}
EVIDENCIAS = [n for n in NODOS if n != OBJETIVO]

# ---------------------------------------------------------------------------
# 3. DAG (máx. 2 padres por nodo)
#    v2 (2026-10-14): padres de la viabilidad Dinamismo + Densidad (mejor log-loss, ρ de P(Alta) 0,398 frente
#    a 0,284, una sola violación de monotonía; experimento_red_ampliada.py). Padres de los nodos nuevos elegidos
#    por puntuación BDeu local entre candidatos plausibles (máx. 2). Especialización sigue en la red para
#    consultas con evidencia parcial, pero ya no es padre del objetivo.
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
    ("Distancia_Madrid", "Densidad"),
    ("Coste_Inmobiliario", "Densidad"),
    ("Distancia_Madrid", "Juventud"),
    ("Densidad", "Juventud"),
    ("Densidad", "Sanidad"),
    ("Distancia_Madrid", "Paro"),
    ("Renta", "Paro"),
    ("Dinamismo_Demografico", "Viabilidad_Empresarial"),
    ("Densidad", "Viabilidad_Empresarial"),
]
PADRES_OBJETIVO = [p for p, h in EDGES if h == OBJETIVO]

# Ranking final (PENDIENTES #5). Con evidencia completa la red solo da 9 niveles; un GA²M (EBM) sobre
# variables continuas desempata y ordena mejor. Con las 7 variables originales (ga2m_desempate.py, CV-5 x 5,
# Spearman con la tasa neta): BN 0,284 · GA²M 0,398 · media de rangos 0,369 · lexicográfico 0,291.
# Modelo v2 (2026-10-14, #44): GA²M 0,529 · red 0,398.
# Decisión 2026-10-07 (PENDIENTES #40, opción b): el GA²M da la puntuación; la red bayesiana explica,
# atiende consultas con evidencia parcial y sostiene el simulador do() de la Administración.
#   "ga2m"           -> puntuación = percentil del GA²M entre los candidatos, 0-100 (por defecto)
#   "media_rangos"   -> media del percentil de la red y del percentil del GA²M
#   "lexicografico"  -> nivel de la red y el GA²M solo desempata dentro de cada nivel
#   "bn"             -> solo la red, 100 × P(Alta)
COMBINACION = "ga2m"
EBM_KW = dict(interactions=10, max_bins=32, min_samples_leaf=10, outer_bags=8, learning_rate=0.02,
              max_rounds=3000, random_state=0)
# El GA²M usa las variables de la red y además las que han mostrado señal propia (#44,
# experimento_variables.py y experimento_ga2m_ampliado.py). Las que tienen fuga (stock de unidades
# productivas o afiliados al final del periodo del objetivo) no entran.
EXTRAS_GA2M = ["uu_oficinas_por_1000hab", "dist_ferro_km", "poblacion"]  # señal dudosa (+0,01) pero no empeoran: entran (#44)
FEATURES_GA2M = list(dict.fromkeys([NODOS[n][0] for n in EVIDENCIAS] + EXTRAS_GA2M))

# Etiquetas legibles de las columnas (ficha del municipio, aportaciones del GA²M)
ETIQUETAS = {
    "dist_sol_km": "Distancia a Madrid (km a Sol)",
    "pct_estudios_superiores": "Talento (% con estudios superiores)",
    "paradas_ferro": "Paradas ferroviarias",
    "vc_residencial_por_uu": "Valor de la vivienda (valor catastral residencial)",
    "rdb_per_capita": "Renta disponible per cápita",
    "pct_up_servicios_prof": "Especialización en servicios profesionales",
    "crec_pob_5a": "Crecimiento de población (5 años)",
    "densidad_hab_km2": "Densidad de población (hab./km²)",
    "pct_menores_45": "Población joven (% menores de 45)",
    "sanidad_por_1000hab": "Sanidad (centros y farmacias por 1.000 hab.)",
    "paro_por_100hab": "Paro registrado (por 100 hab.)",
    "uu_oficinas_por_1000hab": "Oficinas (Catastro, por 1.000 hab.)",
    "dist_ferro_km": "Distancia a la estación ferroviaria (km)",
    "poblacion": "Población",
}

# Cómo leer una variable cuyo signo en el GA²M puede confundir (ficha y asistente). El GA²M explica el saldo de
# empresas, no lo que le cuesta instalarse a quien busca sitio: cuando ambas lecturas chocan, se dicen las dos.
LECTURAS = {
    "vc_residencial_por_uu": (
        "Mide lo que vale la vivienda, no el alquiler de oficinas. El modelo lo lee como señal de demanda: donde la "
        "vivienda vale más, el saldo de empresas fue algo mejor en 2020-2024 (asociación, no causa). Para quien se "
        "instala, un valor alto también anticipa locales más caros; si eso te importa, activa «Coste inmobiliario bajo»."),
}

# Pesos de la Opción B (contribución de cada estado padre a la utilidad de viabilidad, escala 0-1)
PESOS_B = {"Dinamismo_Demografico": 0.55, "Especializacion_Servicios": 0.45}
TEMPERATURA_B = 0.25  # menor = CPT más determinista

AVISO_SENAL = ("Señal moderada: el modelo ordena claramente mejor que el azar (el 64 % de su tercio superior lo es "
               "de verdad, frente al 33 % al azar) y sus probabilidades mejoran a la uniforme, pero siguen siendo "
               "aproximadas. Usa el orden como orientación, no como predicción. Son asociaciones, no efectos causales.")
