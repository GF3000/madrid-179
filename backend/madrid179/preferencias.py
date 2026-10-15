"""Preferencias del usuario fuera del modelo (PENDIENTES #12, #38, #47): catálogo, utilidades, pesos y puntuación.

Puntuación base S ∈ [0, 1]: percentil del GA²M entre los candidatos (COMBINACION="ga2m").
Cada preferencia k aporta una utilidad u_k ∈ [0, 1] del municipio y una importancia r_k elegida por el usuario.

    a_k = r_k · sd(S) / sd(u_k)                    (iguala la dispersión: r = 1 -> pesa tanto como el modelo)
    S'  = (S + Σ a_k · u_k) / (1 + Σ a_k)          con una sola preferencia, w = a / (1 + a)

Tope: si Σ a_k > TOPE, los a_k se escalan para que sumen TOPE, conservando sus proporciones. El 2026-10-15 se
subió de 1 a 3: con 1, cada preferencia nueva restaba peso a las demás y el Top 5 apenas cambiaba (en 300
combinaciones de 2-5 preferencias solo 36 municipios llegaban al Top 5 y uno salía en el 56 %; con 3, 64 y 40 %).
Ahora hasta tres preferencias «muy importantes» cuentan enteras y el modelo pesa siempre al menos una cuarta parte.

"Imprescindible" no es un peso: es un filtro duro (ranking.candidatos). "No lo sé" = peso 0.

Utilidades: tren y ayudas conservan su forma calibrada (#38, #12). El resto usa el percentil del dato entre
los candidatos (robusto a colas largas como la población), invertido si "menos es mejor". Las preferencias con
dos sentidos (cerca o lejos de Madrid, municipio grande o pequeño) se invierten con el sentido elegido.
"""
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

IMPORTANCIA = {"Me da igual": 0.0, "No lo sé": 0.0, "Poco importante": 0.5, "Muy importante": 1.0}
TOPE_PREFERENCIAS = 3.0  # Σ a_k máximo: el modelo pesa al menos 1 / (1 + TOPE) = 25 %


def utilidad_transporte(dist_ferro_km, bueno_km=2.0, malo_km=15.0):
    """1 si hay estación a ≤ bueno_km, 0 a ≥ malo_km, lineal entre ambos."""
    return ((malo_km - np.clip(dist_ferro_km, bueno_km, malo_km)) / (malo_km - bueno_km)).astype(float)


def utilidad_ayudas(nivel_ayudas_num):
    """Bajo = 0, Medio = 0,5, Alto = 1 (columna nivel_ayudas_num del dataset)."""
    return pd.Series(nivel_ayudas_num, dtype=float)


def percentil(x, mas_es_mejor=True):
    """Percentil del dato entre los municipios recibidos, en (0, 1]."""
    x = pd.Series(x, dtype=float)
    return (x if mas_es_mejor else -x).rank(pct=True)


def _num(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


@dataclass(frozen=True)
class Preferencia:
    clave: str
    nombre: str
    grupo: str
    descripcion: str
    columnas: tuple[str, ...]
    utilidad: Callable[[pd.DataFrame], pd.Series]  # en el sentido por defecto (el primero)
    dato: Callable[[pd.Series], str]  # el hecho del municipio, para la ficha
    sentidos: tuple[tuple[str, str], ...] = field(default=())  # (valor, etiqueta); vacío = un solo sentido
    en_modelo: bool = False  # el GA²M ya usa este dato: la preferencia le da peso extra

    def utilidad_en(self, c, sentido=None):
        u = self.utilidad(c)
        if self.sentidos and sentido not in (None, self.sentidos[0][0]):
            u = 1 - u  # las preferencias con dos sentidos usan percentiles: el contrario es 1 - u
        return pd.Series(u, index=c.index, dtype=float)


def _calidad_vida(c):
    # oferta absoluta: por habitante premiaría pueblos diminutos con una sola instalación
    return pd.concat([percentil(c[k]) for k in ("amenidades_osm", "sanidad_osm", "deporte_osm")], axis=1).mean(axis=1)


CATALOGO = [
    # ----------------------------------------------------------- ubicación y transporte
    Preferencia("transporte", "Estación de tren cerca", "Ubicación y transporte",
                "Distancia a la estación de Cercanías, Metro o Metro Ligero más cercana.",
                ("dist_ferro_km",), lambda c: utilidad_transporte(c.dist_ferro_km),
                lambda r: f"estación a {_num(r.dist_ferro_km, 1)} km", en_modelo=True),
    Preferencia("transporte_publico", "Buena red de autobús y transporte público", "Ubicación y transporte",
                "Paradas de transporte público por km² (autobús interurbano, urbano, Metro y tren).",
                ("paradas_total", "superficie_km2"), lambda c: percentil(c.paradas_total / c.superficie_km2),
                lambda r: f"{_num(r.paradas_total / r.superficie_km2, 1)} paradas por km²"),
    Preferencia("distancia_madrid", "Distancia a Madrid", "Ubicación y transporte",
                "Kilómetros en línea recta hasta la Puerta del Sol.",
                ("dist_sol_km",), lambda c: percentil(c.dist_sol_km, mas_es_mejor=False),
                lambda r: f"a {_num(r.dist_sol_km)} km de Sol",
                sentidos=(("cerca", "Cerca"), ("lejos", "Lejos")), en_modelo=True),
    # ------------------------------------------------------------------ coste y ayudas
    Preferencia("coste", "Coste inmobiliario bajo", "Coste y ayudas",
                "Valor catastral medio de los inmuebles residenciales, indicador del nivel de precios del suelo.",
                ("vc_residencial_por_uu",), lambda c: percentil(c.vc_residencial_por_uu, mas_es_mejor=False),
                lambda r: f"valor catastral medio {_num(r.vc_residencial_por_uu)} mil €", en_modelo=True),
    Preferencia("ayudas", "Poder optar a ayudas", "Coste y ayudas",
                "Ayudas al reequilibrio territorial por tamaño: más en municipios de menos de 20.000 y de 2.500 habitantes.",
                ("nivel_ayudas_num",), lambda c: utilidad_ayudas(c.nivel_ayudas_num),
                lambda r: {"Alto": "acceso amplio a ayudas", "Medio": "acceso parcial a ayudas",
                           "Bajo": "sin ayudas por tamaño"}.get(r.nivel_ayudas, r.nivel_ayudas)),
    # ------------------------------------------------------------- plantilla y talento
    Preferencia("talento", "Talento cualificado", "Plantilla y talento",
                "Población con estudios superiores.",
                ("pct_estudios_superiores",), lambda c: percentil(c.pct_estudios_superiores),
                lambda r: f"{_num(r.pct_estudios_superiores)} % con estudios superiores", en_modelo=True),
    Preferencia("mano_obra", "Mano de obra disponible", "Plantilla y talento",
                "Personas en paro registradas sobre la población: más candidatos para contratar.",
                ("paro_por_100hab",), lambda c: percentil(c.paro_por_100hab),
                lambda r: f"{_num(r.paro_por_100hab, 1)} parados por 100 hab.", en_modelo=True),
    Preferencia("juventud", "Población joven", "Plantilla y talento",
                "Proporción de vecinos menores de 45 años.",
                ("pct_menores_45",), lambda c: percentil(c.pct_menores_45),
                lambda r: f"{_num(r.pct_menores_45)} % menores de 45", en_modelo=True),
    # ------------------------------------------------------------------------ mercado
    Preferencia("tamano", "Tamaño del municipio", "Mercado y entorno",
                "Número de habitantes: una ciudad grande o un pueblo pequeño.",
                ("poblacion",), lambda c: percentil(c.poblacion),
                lambda r: f"{_num(r.poblacion)} habitantes",
                sentidos=(("grande", "Grande"), ("pequeno", "Pequeño")), en_modelo=True),
    Preferencia("renta", "Clientes con poder adquisitivo", "Mercado y entorno",
                "Renta disponible por habitante.",
                ("rdb_per_capita",), lambda c: percentil(c.rdb_per_capita),
                lambda r: f"{_num(r.rdb_per_capita)} € de renta por habitante", en_modelo=True),
    Preferencia("servicios_prof", "Ecosistema de servicios profesionales", "Mercado y entorno",
                "Peso de las empresas de servicios profesionales (consultoría, tecnología, finanzas…).",
                ("pct_up_servicios_prof",), lambda c: percentil(c.pct_up_servicios_prof),
                lambda r: f"{_num(r.pct_up_servicios_prof)} % de empresas de servicios profesionales", en_modelo=True),
    Preferencia("crecimiento", "Municipio en crecimiento", "Mercado y entorno",
                "Cuánto ha crecido la población en los últimos cinco años.",
                ("crec_pob_5a",), lambda c: percentil(c.crec_pob_5a),
                lambda r: f"población {'+' if r.crec_pob_5a >= 0 else ''}{_num(r.crec_pob_5a * 100, 1)} % en 5 años",
                en_modelo=True),
    # --------------------------------------------------------- espacios y calidad de vida
    Preferencia("oficinas", "Oferta de oficinas", "Espacios y calidad de vida",
                "Locales de uso oficina en el Catastro por cada 1.000 habitantes.",
                ("uu_oficinas_por_1000hab",), lambda c: percentil(c.uu_oficinas_por_1000hab),
                lambda r: f"{_num(r.uu_oficinas_por_1000hab, 1)} oficinas por 1.000 hab.", en_modelo=True),
    Preferencia("coworking", "Espacio de coworking", "Espacios y calidad de vida",
                "Si hay algún coworking registrado en OpenStreetMap (cobertura incompleta: pocos municipios lo tienen).",
                ("coworking_osm",), lambda c: (c.coworking_osm > 0).astype(float),
                lambda r: "con coworking" if r.coworking_osm > 0 else "sin coworking registrado"),
    Preferencia("calidad_vida", "Servicios para la plantilla", "Espacios y calidad de vida",
                "Restaurantes y ocio, sanidad y deporte en el municipio (OpenStreetMap).",
                ("amenidades_osm", "sanidad_osm", "deporte_osm"), _calidad_vida,
                lambda r: f"{_num(r.amenidades_osm)} locales de ocio, {_num(r.sanidad_osm)} de sanidad y "
                          f"{_num(r.deporte_osm)} de deporte"),
]
POR_CLAVE = {p.clave: p for p in CATALOGO}
PREFERENCIAS = [p.clave for p in CATALOGO]
COLUMNAS = sorted({c for p in CATALOGO for c in p.columnas} | {"nivel_ayudas"})


def normalizar(preferencias):
    """{clave: importancia | {importancia, sentido}} -> {clave: (importancia, sentido)} (claves desconocidas: error)."""
    salida = {}
    for k, v in (preferencias or {}).items():
        if k not in POR_CLAVE:
            raise KeyError(k)
        imp, sentido = (v, None) if isinstance(v, str) else (v.get("importancia", "Me da igual"), v.get("sentido"))
        if imp not in IMPORTANCIA:
            raise ValueError(f"Importancia desconocida para {k}: {imp}")
        validos = [s for s, _ in POR_CLAVE[k].sentidos]
        if sentido is not None and sentido not in validos:
            raise ValueError(f"Sentido desconocido para {k}: {sentido}. Válidos: {', '.join(validos) or 'ninguno'}")
        salida[k] = (imp, sentido)
    return salida


def utilidades(c, preferencias=None):
    """Utilidad de cada preferencia activa (importancia > 0) en los municipios c."""
    prefs = normalizar(preferencias)
    return {k: POR_CLAVE[k].utilidad_en(c, s) for k, (imp, s) in prefs.items() if IMPORTANCIA[imp] > 0}


def pesos(S, utilidades, importancias):
    """a_k por preferencia, calibrados por dispersión sobre los candidatos actuales y con el tope del modelo."""
    sd_s = float(np.std(S))
    a = {k: IMPORTANCIA[importancias[k]] * sd_s / float(np.std(u)) if np.std(u) > 0 else 0.0
         for k, u in utilidades.items()}
    total = sum(a.values())
    if total > TOPE_PREFERENCIAS:
        a = {k: v * TOPE_PREFERENCIAS / total for k, v in a.items()}
    return a


def puntuar(S, utilidades, importancias):
    """Devuelve la puntuación final (0-100) y la aportación de cada parte, para mostrarla desglosada."""
    a = pesos(S, utilidades, importancias)
    den = 1 + sum(a.values())
    partes = pd.DataFrame({"modelo": S / den, **{k: a[k] * u / den for k, u in utilidades.items()}}) * 100
    return partes.sum(axis=1), partes, a


def catalogo_publico():
    """Lo que necesita un cliente (la app, el asistente) para describir y pedir preferencias."""
    return [{"clave": p.clave, "nombre": p.nombre, "grupo": p.grupo, "descripcion": p.descripcion,
             "sentidos": [{"valor": v, "etiqueta": e} for v, e in p.sentidos] or None, "en_modelo": p.en_modelo}
            for p in CATALOGO]
