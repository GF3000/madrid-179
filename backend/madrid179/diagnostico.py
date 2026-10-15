"""Diagnóstico territorial para la Administración («Dónde actuar»).

Qué municipios necesitan actividad (reequilibrio), cuáles pueden atraerla (viabilidad del GA²M) y qué les frena
(palanca política o factor estructural). Todo se rehace a mano desde la tabla del artefacto: percentiles entre los
178 municipios (los 179 menos Madrid capital, que es la referencia). Describe la situación; no simula políticas.
"""
import pandas as pd

from .config import CORTE_DIAGNOSTICO, ETIQUETAS, FUERZA, LECTURAS, NECESIDAD, SENAL_DUDOSA, TIPO_FACTOR

CAPITAL = "28079"
MAX_FRENOS = 3
UMBRAL_FRENO = FUERZA[-1][0]  # pp: solo cuenta como freno lo que resta al menos «algo» (como en la ficha)
AVISO = "Diagnóstico según los datos de 2020 a 2024: describe la situación, no mide el efecto de ninguna política."
NOTA_NECESIDAD = ("Media de percentiles (0-100, pesos iguales) de cada componente en el sentido que indica necesidad, "
                  "entre los 178 municipios. Propuesta provisional. Madrid capital queda fuera: es la referencia.")
CUADRANTES = [
    {"id": "oportunidad", "nombre": "Necesita actividad y puede atraerla",
     "lectura": "Su situación pide actividad y el modelo lo sitúa entre los de mejor saldo esperado de empresas: "
                "atraer empresas puede funcionar."},
    {"id": "apoyo", "nombre": "Necesita actividad y le cuesta atraerla",
     "lectura": "Su situación pide actividad, pero el modelo lo sitúa en la mitad baja: atraer empresas por sí solo "
                "probablemente no baste."},
    {"id": "autonomo", "nombre": "Va por su cuenta",
     "lectura": "Necesidad por debajo de la mitad y viabilidad en la mitad alta: según los datos, avanza sin "
                "necesitar prioridad."},
    {"id": "vigilar", "nombre": "Sin urgencia, poca viabilidad",
     "lectura": "Ni la necesidad ni la viabilidad destacan: conviene seguir su evolución."},
]
NODO_DISTANCIA = "Distancia_Madrid"


def percentil(serie, sentido="alto"):
    """Percentil 0-100 (empates promedio); con sentido 'bajo', el valor más bajo da el percentil más alto."""
    return serie.rank(pct=True, ascending=sentido != "bajo") * 100


def cuadrante(necesidad, viabilidad, corte=CORTE_DIAGNOSTICO):
    if necesidad >= corte:
        return "oportunidad" if viabilidad >= corte else "apoyo"
    return "autonomo" if viabilidad >= corte else "vigilar"


def tipo_termino(termino):
    """Un término «a & b» es palanca si alguna de sus columnas lo es."""
    cols = [c.strip() for c in termino.split("&")]
    return "palanca" if any(TIPO_FACTOR.get(c) == "palanca" for c in cols) else "estructural"


def frenos(contrib):
    """Aportaciones del GA²M <= -UMBRAL_FRENO pp (sin intercepto ni señal dudosa), de la más negativa a la menos.
    Devuelve (las MAX_FRENOS primeras, la primera de tipo palanca o None)."""
    lista = []
    for termino, v in contrib.drop("intercepto").items():
        cols = [c.strip() for c in termino.split("&")]
        if v * 100 > -UMBRAL_FRENO or any(c in SENAL_DUDOSA for c in cols):
            continue
        lista.append({"termino": termino, "etiqueta": " × ".join(ETIQUETAS.get(c, c) for c in cols),
                      "aportacion_pp": round(float(v) * 100, 4), "tipo": tipo_termino(termino),
                      "lectura": " ".join(LECTURAS[c] for c in cols if c in LECTURAS) or None})
    lista.sort(key=lambda x: x["aportacion_pp"])
    return lista[:MAX_FRENOS], next((f for f in lista if f["tipo"] == "palanca"), None)


def tabla_diagnostico(tabla):
    """Percentiles de necesidad y viabilidad y cuadrante de los 178 municipios (sin la capital)."""
    t = tabla.drop(index=CAPITAL, errors="ignore")
    d = pd.DataFrame(index=t.index)
    for col, sentido in NECESIDAD.items():
        d[f"pct_{col}"] = percentil(t[col], sentido)
    d["necesidad"] = d[[f"pct_{c}" for c in NECESIDAD]].mean(axis=1)
    d["viabilidad"] = percentil(t["ga2m_pred"])
    d["cuadrante"] = [cuadrante(n, v) for n, v in zip(d.necesidad, d.viabilidad)]
    return d


def diagnostico(tabla, aportaciones, candidatos):
    """Respuesta de GET /api/v1/diagnostico. `candidatos`: índices del ranking por defecto."""
    d = tabla_diagnostico(tabla)
    cand = set(candidatos)
    municipios = []
    for i in d.sort_values("necesidad", ascending=False, kind="mergesort").index:
        r, x = tabla.loc[i], d.loc[i]
        principales, palanca = frenos(aportaciones.loc[i])
        municipios.append({
            "ine5": i, "municipio": r.nombre_iecm, "poblacion": int(r.poblacion), "distancia": r[NODO_DISTANCIA],
            "candidato": i in cand,
            "necesidad": round(float(x.necesidad), 2),
            "componentes": {c: {"valor": round(float(r[c]), 4), "percentil": round(float(x[f"pct_{c}"]), 2)}
                            for c in NECESIDAD},
            "viabilidad": round(float(x.viabilidad), 2),
            "cuadrante": x.cuadrante,
            "frenos": principales,
            "freno_palanca": palanca,
        })
    return {
        "corte": CORTE_DIAGNOSTICO,
        "aviso": AVISO,
        "necesidad": {"componentes": [{"columna": c, "etiqueta": ETIQUETAS.get(c, c), "sentido": s}
                                      for c, s in NECESIDAD.items()],
                      "nota": NOTA_NECESIDAD},
        "cuadrantes": CUADRANTES,
        "municipios": municipios,
    }
