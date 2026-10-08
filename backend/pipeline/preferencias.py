"""Preferencias del usuario fuera del modelo (PENDIENTES #12, #38): utilidades, pesos calibrados y puntuación final.

Puntuación base S ∈ [0, 1]: percentil del GA²M entre los candidatos (red_bayesiana_viabilidad.py, COMBINACION="ga2m").
Cada preferencia k aporta una utilidad u_k ∈ [0, 1] del municipio y una importancia r_k elegida por el usuario.

    a_k = r_k · sd(S) / sd(u_k)                    (iguala la dispersión: r = 1 -> pesa tanto como el modelo)
    S'  = (S + Σ a_k · u_k) / (1 + Σ a_k)          con una sola preferencia, w = a / (1 + a)

"Imprescindible" no es un peso: es un filtro duro (se aplica antes). "No lo sé" = peso 0.
Uso de demostración: python backend/pipeline/preferencias.py
"""
import numpy as np
import pandas as pd

IMPORTANCIA = {"Me da igual": 0.0, "No lo sé": 0.0, "Poco importante": 0.5, "Muy importante": 1.0}


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


if __name__ == "__main__":
    rk = pd.read_csv("data/processed/bn_ranking_municipios.csv", sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
    d = pd.read_csv("data/processed/dataset_bn_municipios.csv", sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
    S = rk.puntuacion / 100
    U = {"transporte": utilidad_transporte(d.loc[rk.index, "dist_ferro_km"]),
         "ayudas": utilidad_ayudas(d.loc[rk.index, "nivel_ayudas_num"])}
    print(f"Candidatos: {len(S)} · sd(S) = {np.std(S):.3f} · sd(u transporte) = {np.std(U['transporte']):.3f} · sd(u ayudas) = {np.std(U['ayudas']):.3f}")
    print("\nPeso w de una sola preferencia y cuántos puntos de modelo compensa una utilidad máxima:")
    for k in U:
        for imp in ["Poco importante", "Muy importante"]:
            a = pesos(S, {k: U[k]}, {k: imp})[k]
            w = a / (1 + a)
            print(f"  {k:10s} {imp:16s} w = {w:.3f} -> compensa hasta {100 * w / (1 - w):.0f} puntos")
    ejemplo = {"transporte": "Muy importante", "ayudas": "Poco importante"}
    total, partes, a = puntuar(S, U, ejemplo)
    top = partes.assign(total=total, municipio=rk.municipio).sort_values("total", ascending=False).head(8)
    print(f"\nEjemplo {ejemplo}:")
    print(top[["municipio", "total", "modelo", "transporte", "ayudas"]].round(1).to_string(index=False))
