"""Servicio del modelo: lo que expone la API (meta, municipios, ranking, ficha, consulta) sobre el artefacto cargado.

No depende de FastAPI: los tests y cualquier otro cliente pueden usarlo directamente.
"""
import numpy as np
import pandas as pd
from pgmpy.inference import VariableElimination

from .config import AVISO_SENAL, EVIDENCIAS, FILTROS, NODOS, OBJETIVO, PADRES_OBJETIVO
from .preferencias import IMPORTANCIA, PREFERENCIAS
from .ranking import rankear, utilidades
from .red import distribucion

ETIQUETAS = {
    "dist_sol_km": "Distancia a Madrid (km a Sol)",
    "pct_estudios_superiores": "Talento (% con estudios superiores)",
    "paradas_ferro": "Paradas ferroviarias",
    "vc_residencial_por_uu": "Coste inmobiliario (valor catastral residencial)",
    "rdb_per_capita": "Renta disponible per cápita",
    "pct_up_servicios_prof": "Especialización en servicios profesionales",
    "crec_pob_5a": "Crecimiento de población (5 años)",
}
UMBRAL_DISCREPANCIA = 50  # puntos de percentil entre la red y el GA²M


class ErrorEvidencia(ValueError):
    """Nodo o estado no válido en una consulta."""


class Servicio:
    def __init__(self, art):
        self.art = art
        self.tabla = art["tabla"]
        self.inferencia = VariableElimination(art["red"])
        self.base, _ = rankear(self.tabla)  # ranking por defecto (sin preferencias ni filtros del usuario)

    # ------------------------------------------------------------------ meta
    def meta(self):
        a = self.art
        return {
            "version_modelo": a["version"], "entrenado": a["entrenado"], "huella_dataset": a["huella_dataset"],
            "validacion": a["validacion"], "aviso": AVISO_SENAL,
            "objetivo": OBJETIVO, "padres_objetivo": PADRES_OBJETIVO,
            "nodos": {n: {"columna": NODOS[n][0], "estados": NODOS[n][1], "cortes": a["umbrales"][n]["cortes"]}
                      for n in NODOS},
            "preferencias": PREFERENCIAS, "importancias": list(IMPORTANCIA),
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
    def ranking(self, importancias=None, estacion_max_km=None, solo_con_ayudas=False, limite=None):
        c, a = rankear(self.tabla, importancias, estacion_max_km, solo_con_ayudas)
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
                          "valores": {c: round(float(r[c]), 4) for c in cols}})
        aport.sort(key=lambda x: abs(x["aportacion_pp"]), reverse=True)

        discrepancia = None
        if en_base and abs(b.percentil_ga2m - b.percentil_bn) >= UMBRAL_DISCREPANCIA:
            mejor = "el GA²M" if b.percentil_ga2m > b.percentil_bn else "la red bayesiana"
            p_alta = f"{r.P_Alta:.2f}".replace(".", ",")
            discrepancia = (f"Los dos modelos discrepan: percentil {b.percentil_ga2m:.0f} en el GA²M frente a "
                            f"{b.percentil_bn:.0f} en la red (P(Alta) = {p_alta}). Lo valora mejor {mejor}; "
                            "revisa las aportaciones antes de fiarte de la puntuación.")

        u = utilidades(self.tabla.loc[[ine5]])
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
            "preferencias": {"transporte": {"dist_ferro_km": round(float(r.dist_ferro_km), 2),
                                            "utilidad": round(float(u["transporte"].iloc[0]), 4)},
                             "ayudas": {"nivel": r.nivel_ayudas, "utilidad": float(u["ayudas"].iloc[0])}},
        }

    def _motivo_exclusion(self, ine5):
        fila = self.tabla.loc[[ine5]]
        return [nombre for nombre, f in FILTROS.items() if not bool(np.asarray(f(fila))[0])]

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
