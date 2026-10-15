"""Servicio del modelo: lo que expone la API (meta, municipios, ranking, ficha, consulta) sobre el artefacto cargado.

No depende de FastAPI: los tests y cualquier otro cliente pueden usarlo directamente.
"""
import json
import re

import numpy as np
import pandas as pd
from pgmpy.inference import VariableElimination

from . import asistente
from . import diagnostico as diag
from .config import (AVISO_SENAL, ETIQUETAS, EVIDENCIAS, FILTROS, FUERZA, LECTURAS, NODOS, OBJETIVO, PADRES_OBJETIVO,
                     PARA_QUIEN_SE_INSTALA, RAIZ, SENAL_DUDOSA)
from .preferencias import (CATALOGO, IMPORTANCIA, POR_CLAVE, PREFERENCIAS, TOPE_PREFERENCIAS, catalogo_publico,
                           normalizar)
from .ranking import rankear
from .red import distribucion

UMBRAL_DISCREPANCIA = 50  # puntos de percentil entre la red y el GA²M
WIKIPEDIA = RAIZ / "data" / "processed" / "wikipedia_municipios.json"  # backend/pipeline/descargar_wikipedia.py
MOTIVOS = {"excluir_madrid_capital": "la capital queda fuera a propósito: el objetivo es llevar actividad al resto de la región",
           "min_uu_oficinas": "no tiene ningún local de oficinas en el Catastro"}
NODOS_LEGIBLES = {
    "Distancia_Madrid": "distancia a Madrid", "Talento": "talento (estudios superiores)",
    "Acceso_Ferroviario": "estación de tren", "Coste_Inmobiliario": "valor de la vivienda", "Renta": "renta",
    "Especializacion_Servicios": "servicios profesionales", "Dinamismo_Demografico": "crecimiento de la población",
    "Densidad": "densidad", "Juventud": "población joven", "Sanidad": "oferta sanitaria", "Paro": "paro",
}


class ErrorEvidencia(ValueError):
    """Nodo o estado no válido en una consulta."""


class Servicio:
    def __init__(self, art):
        self.art = art
        self.tabla = art["tabla"]
        self.inferencia = VariableElimination(art["red"])
        self.base, _ = rankear(self.tabla)  # ranking por defecto (sin preferencias ni filtros del usuario)
        self.wikipedia = json.loads(WIKIPEDIA.read_text(encoding="utf-8")) if WIKIPEDIA.exists() else {}
        self.tercios = {c: self.tabla[c].quantile([1 / 3, 2 / 3]).tolist() for c in PARA_QUIEN_SE_INSTALA}
        self._diagnostico = None

    def para_quien_se_instala(self, termino, r):
        """'ventaja' / 'inconveniente' de un valor para quien se instala (tercio superior o inferior), o None."""
        alto = PARA_QUIEN_SE_INSTALA.get(termino)
        if alto is None:
            return None
        bajo_q, alto_q = self.tercios[termino]
        if r[termino] >= alto_q:
            return alto
        if r[termino] <= bajo_q:
            return "ventaja" if alto == "inconveniente" else "inconveniente"
        return None

    # ------------------------------------------------------------------ meta
    def meta(self):
        a = self.art
        return {
            "version_modelo": a["version"], "entrenado": a["entrenado"], "huella_dataset": a["huella_dataset"],
            "validacion": a["validacion"], "aviso": AVISO_SENAL,
            "objetivo": OBJETIVO, "padres_objetivo": PADRES_OBJETIVO,
            "nodos": {n: {"columna": NODOS[n][0], "estados": NODOS[n][1], "cortes": a["umbrales"][n]["cortes"]}
                      for n in NODOS},
            "preferencias": PREFERENCIAS, "catalogo": catalogo_publico(), "importancias": list(IMPORTANCIA),
            "tope_preferencias": TOPE_PREFERENCIAS, "asistente_disponible": asistente.disponible(),
            "filtros_base": list(FILTROS), "municipios": len(self.tabla), "candidatos_por_defecto": len(self.base),
        }

    # ------------------------------------------------------------ municipios
    def municipios(self):
        t = self.tabla
        cand = set(self.base.index)
        return [{"ine5": i, "municipio": r.nombre_iecm, "poblacion": int(r.poblacion), "candidato": i in cand,
                 "nivel_ayudas": r.nivel_ayudas, "dist_ferro_km": round(float(r.dist_ferro_km), 2),
                 "estados": {n: r[n] for n in EVIDENCIAS}}
                for i, r in t.iterrows()]

    # --------------------------------------------------------------- ranking
    def ranking(self, importancias=None, estacion_max_km=None, solo_con_ayudas=False, limite=None, **filtros):
        c, a = rankear(self.tabla, importancias, estacion_max_km, solo_con_ayudas, **filtros)
        filas = c if limite is None else c.head(limite)
        partes = [k for k in ["modelo", *PREFERENCIAS] if f"parte_{k}" in c.columns]
        return {
            "candidatos": len(c),
            "pesos": {k: round(v, 4) for k, v in a.items()},
            "resultados": [{"posicion": int(r.posicion), "ine5": i, "municipio": r.nombre_iecm,
                            "puntuacion": round(float(r.puntuacion), 2),
                            "desglose": {k: round(float(r[f"parte_{k}"]), 2) for k in partes},
                            "p_alta_red": round(float(r.P_Alta), 4),
                            "prediccion_ga2m_pct": round(float(r.ga2m_pred) * 100, 3),
                            "nivel_ayudas": r.nivel_ayudas, "dist_ferro_km": round(float(r.dist_ferro_km), 2)}
                           for i, r in filas.iterrows()],
        }

    # ----------------------------------------------------------------- ficha
    def ficha(self, ine5):
        if ine5 not in self.tabla.index:
            raise KeyError(ine5)
        r = self.tabla.loc[ine5]
        en_base = ine5 in self.base.index
        b = self.base.loc[ine5] if en_base else None

        contrib = self.art["aportaciones"].loc[ine5]
        aport = []
        for termino, v in contrib.drop("intercepto").items():
            cols = [c.strip() for c in termino.split("&")]
            aport.append({"termino": termino, "etiqueta": " × ".join(ETIQUETAS.get(c, c) for c in cols),
                          "aportacion_pp": round(float(v) * 100, 4),
                          "valores": {c: round(float(r[c]), 4) for c in cols},
                          "lectura": " ".join(LECTURAS[c] for c in cols if c in LECTURAS) or None,
                          "senal_dudosa": any(c in SENAL_DUDOSA for c in cols),
                          "para_quien_se_instala": self.para_quien_se_instala(termino, r)})
        aport.sort(key=lambda x: abs(x["aportacion_pp"]), reverse=True)

        discrepancia = None
        if en_base and abs(b.percentil_ga2m - b.percentil_bn) >= UMBRAL_DISCREPANCIA:
            mejor = "el GA²M" if b.percentil_ga2m > b.percentil_bn else "la red bayesiana"
            p_alta = f"{r.P_Alta:.2f}".replace(".", ",")
            discrepancia = (f"Los dos modelos discrepan: percentil {b.percentil_ga2m:.0f} en el GA²M frente a "
                            f"{b.percentil_bn:.0f} en la red (P(Alta) = {p_alta}). Lo valora mejor {mejor}; "
                            "revisa las aportaciones antes de fiarte de la puntuación.")

        return {
            "ine5": ine5, "municipio": r.nombre_iecm, "poblacion": int(r.poblacion),
            "candidato": en_base,
            "motivo_exclusion": None if en_base else self._motivo_exclusion(ine5),
            "posicion": int(b.posicion) if en_base else None,
            "puntuacion": round(float(b.puntuacion), 2) if en_base else None,
            "de": len(self.base),
            "ga2m": {"prediccion_pct": round(float(r.ga2m_pred) * 100, 4),
                     "intercepto_pct": round(float(contrib["intercepto"]) * 100, 4),
                     "percentil": round(float(b.percentil_ga2m), 2) if en_base else None,
                     "aportaciones": aport},
            "red": {"estados": {n: r[n] for n in NODOS},
                    "probabilidades": {s: round(float(r[f"P_{s}"]), 4) for s in NODOS[OBJETIVO][1]},
                    "padres": {p: r[p] for p in PADRES_OBJETIVO},
                    "percentil": round(float(b.percentil_bn), 2) if en_base else None},
            "discrepancia": discrepancia,
            "preferencias": self._preferencias(ine5),
            "wikipedia": self.wikipedia.get(ine5),
        }

    def _preferencias(self, ine5):
        """Dato y utilidad (0-1, entre los candidatos por defecto) de cada preferencia, en cada sentido."""
        grupo = self.tabla.loc[self.base.index.union([ine5])]
        r = self.tabla.loc[ine5]
        salida = {}
        for p in CATALOGO:
            sentidos = [v for v, _ in p.sentidos] or [None]
            salida[p.clave] = {"dato": p.dato(r),
                               "utilidad": {s or "": round(float(p.utilidad_en(grupo, s).loc[ine5]), 4) for s in sentidos}}
        return salida

    def hechos(self, ine5, clase=None, preferencias=None, negocio=None):
        """Lo que ya ha calculado la herramienta sobre un municipio, en palabras: la única materia prima del LLM.
        `negocio` ({sector, resumen}, de /interpretar) permite adaptar la redacción a quien pregunta."""
        f = self.ficha(ine5)
        est = f["red"]["estados"]

        def nivel(col):
            nodo = next((n for n in NODOS if NODOS[n][0] == col), None)
            return est[nodo].lower() if nodo else None

        factores = {"a favor": [], "en contra": []}
        n = 0
        for a in ([] if f["motivo_exclusion"] else f["ga2m"]["aportaciones"]):  # fuera del análisis: no se valora
            fuerza = next((w for u, w in FUERZA if abs(a["aportacion_pp"]) >= u), None)
            if not fuerza:
                continue
            detalle = [nivel(c) or _redondo(v) for c, v in a["valores"].items()]
            n += 1
            factores["a favor" if a["aportacion_pp"] > 0 else "en contra"].append(
                {"id": f"F{n}", "factor": a["etiqueta"], "nivel": " · ".join(detalle), "fuerza": fuerza,
                 **({"senal": "dudosa"} if a["senal_dudosa"] else {}),
                 **({"como_leerlo": a["lectura"]} if a["lectura"] else {}),
                 **({"para_quien_se_instala": a["para_quien_se_instala"]} if a["para_quien_se_instala"] else {})})

        prefs = []
        for k, (imp, sentido) in normalizar(preferencias).items():
            if IMPORTANCIA[imp] == 0:
                continue
            util = f["preferencias"][k]["utilidad"]
            u = util.get(sentido or "", next(iter(util.values())))
            prefs.append({"id": f"P{len(prefs) + 1}", "preferencia": POR_CLAVE[k].nombre + (f" ({sentido})" if sentido else ""),
                          "importancia": imp, "dato": f["preferencias"][k]["dato"],
                          "encaje": "alto" if u >= 0.66 else "medio" if u >= 0.33 else "bajo"})
        probs = f["red"]["probabilidades"]
        return {
            "municipio": _legible(f["municipio"]), "habitantes": f["poblacion"], "grupo": clase,
            "fuera_del_analisis": [MOTIVOS.get(m, m) for m in f["motivo_exclusion"] or []] or None,
            "factores": factores,
            "perfil": {NODOS_LEGIBLES.get(n, n): s.lower() for n, s in est.items() if n != OBJETIVO},
            "red_de_causas": {"viabilidad_mas_habitual_en_municipios_asi": max(probs, key=probs.get).lower(),
                              "depende_de": {NODOS_LEGIBLES.get(n, n): s.lower() for n, s in f["red"]["padres"].items()},
                              "discrepa_de_la_tabla_de_factores": bool(f["discrepancia"])},
            "preferencias_del_usuario": prefs or None,
            "resumen_wikipedia": (f.get("wikipedia") or {}).get("resumen"),
            "negocio_del_usuario": {k: v for k, v in (negocio or {}).items() if v} or None,
        }

    def _motivo_exclusion(self, ine5):
        fila = self.tabla.loc[[ine5]]
        return [nombre for nombre, f in FILTROS.items() if not bool(np.asarray(f(fila))[0])]

    # ----------------------------------------------------------- diagnóstico
    def diagnostico(self):
        """Diagnóstico territorial de la Administración (madrid179/diagnostico.py); se calcula una vez."""
        if self._diagnostico is None:
            self._diagnostico = diag.diagnostico(self.tabla, self.art["aportaciones"], self.base.index)
        return self._diagnostico

    # -------------------------------------------------------------- consulta
    def consulta(self, evidencia):
        for n, s in evidencia.items():
            if n == OBJETIVO:
                raise ErrorEvidencia(f"{OBJETIVO} es el objetivo: no puede ser evidencia")
            if n not in NODOS:
                raise ErrorEvidencia(f"Nodo desconocido: {n}. Válidos: {', '.join(EVIDENCIAS)}")
            if s not in NODOS[n][1]:
                raise ErrorEvidencia(f"Estado desconocido para {n}: {s}. Válidos: {', '.join(NODOS[n][1])}")
        t = self.tabla
        mask = pd.Series(True, index=t.index)
        for n, s in evidencia.items():
            mask &= t[n] == s
        cand = set(self.base.index)
        return {
            "evidencia": evidencia,
            "probabilidades": {k: round(v, 4) for k, v in distribucion(self.inferencia, evidencia).items()},
            "a_priori": {k: round(v, 4) for k, v in distribucion(self.inferencia, {}).items()},
            "municipios": [{"ine5": i, "municipio": t.loc[i, "nombre_iecm"], "candidato": i in cand}
                           for i in t.index[mask]],
        }


def _redondo(x):
    """Número legible en español: 3,9 · 10.653."""
    return f"{x:,.0f}".replace(",", ".") if abs(x) >= 100 else f"{x:.1f}".replace(".", ",")


def _legible(nombre):
    """«Molinos (Los)» -> «Los Molinos» (nombres del IECM con artículo pospuesto)."""
    m = re.match(r"^(.*) \((La|El|Los|Las)\)$", nombre)
    return f"{m[2]} {m[1]}" if m else nombre
