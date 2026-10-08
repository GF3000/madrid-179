"""Entrenar, guardar y cargar el artefacto del modelo (data/processed/modelo.joblib).

La API carga el artefacto y nunca reentrena: sirve exactamente el modelo que ha pasado la auditoría.
"""
import hashlib
import subprocess
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from pgmpy.inference import VariableElimination

from . import ga2m
from .config import ARTEFACTO, DATASET, EVIDENCIAS, NODOS, RAIZ
from .discretizacion import discretizar
from .red import construir_modelo, distribucion, validar

FORMATO = 1
COLUMNAS_INFO = ["nombre_iecm", "poblacion", "uu_oficinas", "dist_ferro_km", "nivel_ayudas", "nivel_ayudas_num"]


def leer_dataset(ruta=DATASET):
    return pd.read_csv(ruta, sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")


def _version():
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True,
                           check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        h = "sin-git"
    return f"{fecha}+{h}"


def entrenar(d=None, repeticiones_cv=5, modo="A"):
    """Ajusta la red y el GA²M sobre los 179 municipios y precalcula todo lo que sirve la API."""
    desde_fichero = d is None
    d = leer_dataset() if desde_fichero else d
    disc, umbrales = discretizar(d)
    red = construir_modelo(disc, modo)
    inf = VariableElimination(red)
    probs = pd.DataFrame([distribucion(inf, {n: row[n] for n in EVIDENCIAS}) for _, row in disc.iterrows()],
                         index=disc.index).add_prefix("P_")
    ebm = ga2m.ajustar(d)
    pred, contrib, imp = ga2m.evaluar(ebm, d)
    columnas = [NODOS[n][0] for n in NODOS]
    tabla = d[COLUMNAS_INFO + columnas].join(disc).join(probs).assign(ga2m_pred=pred)

    validacion = None
    if repeticiones_cv:
        res = np.array([validar(disc, modo, seed=s)[:2] for s in range(repeticiones_cv)])
        validacion = {"repeticiones": repeticiones_cv, "particiones": 5,
                      "acierto": [float(res[:, 0].mean()), float(res[:, 0].std())],
                      "log_loss": [float(res[:, 1].mean()), float(res[:, 1].std())],
                      "acierto_azar": 1 / len(NODOS["Viabilidad_Empresarial"][1]),
                      "log_loss_uniforme": float(np.log(len(NODOS["Viabilidad_Empresarial"][1])))}

    return {"formato": FORMATO, "version": _version(), "entrenado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "huella_dataset": hashlib.sha256(DATASET.read_bytes()).hexdigest() if desde_fichero else None,
            "modo": modo, "umbrales": umbrales, "red": red, "ebm": ebm, "tabla": tabla,
            "aportaciones": contrib, "importancias": imp, "validacion": validacion}


def guardar(art, ruta=ARTEFACTO):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(art, ruta, compress=3)
    return ruta


def cargar(ruta=ARTEFACTO):
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}. Entrena primero: python backend/pipeline/entrenar.py")
    art = joblib.load(ruta)
    if art.get("formato") != FORMATO:
        raise RuntimeError(f"{ruta} tiene un formato antiguo. Reentrena: python backend/pipeline/entrenar.py")
    return art
