"""Preferencias del usuario fuera del modelo (PENDIENTES #12, #38): utilidades, pesos calibrados y puntuación final.

Puntuación base S ∈ [0, 1]: percentil del GA²M entre los candidatos (COMBINACION="ga2m").
Cada preferencia k aporta una utilidad u_k ∈ [0, 1] del municipio y una importancia r_k elegida por el usuario.

    a_k = r_k · sd(S) / sd(u_k)                    (iguala la dispersión: r = 1 -> pesa tanto como el modelo)
    S'  = (S + Σ a_k · u_k) / (1 + Σ a_k)          con una sola preferencia, w = a / (1 + a)

"Imprescindible" no es un peso: es un filtro duro (se aplica antes). "No lo sé" = peso 0.
"""
import numpy as np
import pandas as pd

IMPORTANCIA = {"Me da igual": 0.0, "No lo sé": 0.0, "Poco importante": 0.5, "Muy importante": 1.0}
PREFERENCIAS = ["transporte", "ayudas"]


def utilidad_transporte(dist_ferro_km, bueno_km=2.0, malo_km=15.0):
    """1 si hay estación a ≤ bueno_km, 0 a ≥ malo_km, lineal entre ambos."""
    return ((malo_km - np.clip(dist_ferro_km, bueno_km, malo_km)) / (malo_km - bueno_km)).astype(float)


def utilidad_ayudas(nivel_ayudas_num):
    """Bajo = 0, Medio = 0,5, Alto = 1 (columna nivel_ayudas_num del dataset)."""
    return pd.Series(nivel_ayudas_num, dtype=float)


def pesos(S, utilidades, importancias):
    """a_k por preferencia, calibrados por dispersión sobre los candidatos actuales."""
    sd_s = float(np.std(S))
    return {k: IMPORTANCIA[importancias[k]] * sd_s / float(np.std(u)) if np.std(u) > 0 else 0.0
            for k, u in utilidades.items()}


def puntuar(S, utilidades, importancias):
    """Devuelve la puntuación final (0-100) y la aportación de cada parte, para mostrarla desglosada."""
    a = pesos(S, utilidades, importancias)
    den = 1 + sum(a.values())
    partes = pd.DataFrame({"modelo": S / den, **{k: a[k] * u / den for k, u in utilidades.items()}}) * 100
    return partes.sum(axis=1), partes, a
