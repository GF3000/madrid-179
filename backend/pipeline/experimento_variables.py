"""¿Tienen señal otras variables del dataset? (sanidad, deporte, ocio, oficinas, paro, juventud, tamaño…)

Para cada variable candidata que hoy NO está en el modelo:
  1. Asociación simple: Spearman con la tasa neta (179 municipios) y Spearman parcial controlando tamaño
     (población) y distancia a Madrid, porque casi todo lo municipal va con el tamaño.
  2. Valor incremental: GA²M base (las 7 variables del modelo) frente a base + candidata, con CV-5 × 5
     repeticiones, mismas particiones y misma semilla en las dos (comparación pareada). Métricas fuera de
     muestra: Spearman con la tasa neta y precisión en el tercio superior.
  3. Control de azar: variables de ruido puro (5 en el cribado, 3 en la confirmación) pasan por el mismo proceso. Una candidata solo tiene señal
     si mejora más que el mejor ruido y en al menos 4 de las 5 repeticiones.

Fases (el EBM de producción tarda ~16 s por ajuste):
  --fase cribado        GAM ligero (sin interacciones, 4 bolsas): todas las candidatas, ~12 min
  --fase confirmacion   configuración de producción (5 interacciones, 8 bolsas) para las que se indiquen
                        con --variables, ~7 min por variable más la base

No toca producción. Salidas: data/processed/experimento_variables_{cribado,confirmacion}.csv
Uso: python backend/pipeline/experimento_variables.py --fase cribado
"""
import argparse
import time
import warnings

import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingRegressor
from scipy.stats import spearmanr

from madrid179.config import EBM_KW, FEATURES_GA2M
from madrid179.artefactos import leer_dataset
from madrid179.discretizacion import discretizar

warnings.filterwarnings("ignore")

TARGET = "tasa_neta_emp"
# Candidatas: columnas del dataset que no están en el modelo. fuga = medida al final del periodo del objetivo
# (2020-2024) que incluye mecánicamente su resultado: se prueba solo como control de que el método la detecta.
CANDIDATAS = {
    "sanidad_por_1000hab": "Sanidad (OSM) por 1.000 hab.",
    "deporte_por_1000hab": "Deporte (OSM) por 1.000 hab.",
    "amenidades_por_1000hab": "Ocio y servicios (OSM) por 1.000 hab.",
    "coworking_osm": "Espacios de coworking (OSM)",
    "uu_oficinas_por_1000hab": "Oficinas (Catastro) por 1.000 hab.",
    "paro_por_100hab": "Paro registrado por 100 hab.",
    "pct_menores_45": "% población menor de 45 años",
    "poblacion": "Población",
    "densidad_hab_km2": "Densidad (hab./km²)",
    "paradas_por_1000hab": "Paradas de transporte por 1.000 hab.",
    "dist_ferro_km": "Distancia a la estación ferroviaria (km)",
    "nivel_ayudas_num": "Nivel de ayudas (por población)",
    "afiliados_por_1000hab": "Afiliados a la Seg. Social por 1.000 hab.",
    "up_por_1000hab": "Unidades productivas por 1.000 hab. [FUGA: stock al final del periodo]",
}
RUIDOS = [f"ruido_{i}" for i in range(5)]
CONFIG = {
    "cribado": dict(interactions=0, outer_bags=4, max_rounds=1000, learning_rate=0.04,
                    max_bins=32, min_samples_leaf=10, n_jobs=1),
    # n_jobs=4: el equipo tiene poca memoria libre y cada proceso del EBM ocupa la suya
    "confirmacion": {**{k: v for k, v in EBM_KW.items() if k != "random_state"}, "n_jobs": 4},
}


def asociacion(d, col):
    """Spearman simple y parcial (controlando rangos de población y distancia a Madrid)."""
    r = d[[col, TARGET, "poblacion", "dist_sol_km"]].rank()
    Z = np.column_stack([np.ones(len(r)), r.poblacion, r.dist_sol_km])
    res = lambda v: v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0]
    parcial = np.corrcoef(res(r[col].to_numpy()), res(r[TARGET].to_numpy()))[0, 1] if col != "poblacion" else np.nan
    return spearmanr(d[col], d[TARGET]).statistic, parcial


def cv(d, feats, alta, kw, reps=5, k=5):
    """Spearman y precisión en el tercio superior fuera de muestra, por repetición."""
    y = d[TARGET].to_numpy()
    out = []
    for rep in range(reps):
        folds = np.array_split(np.random.default_rng(rep).permutation(len(d)), k)
        oof = np.zeros(len(d))
        for f in folds:
            tr = np.setdiff1d(np.arange(len(d)), f)
            m = ExplainableBoostingRegressor(random_state=rep, **kw).fit(d.iloc[tr][feats], y[tr])
            oof[f] = m.predict(d.iloc[f][feats])
        top = oof >= np.quantile(oof, 2 / 3)
        out.append((spearmanr(oof, y).statistic, alta[top].mean()))
    return np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fase", choices=["cribado", "confirmacion"], default="cribado")
    ap.add_argument("--variables", nargs="*", help="candidatas a evaluar (por defecto, todas)")
    ap.add_argument("--conjunto", nargs="*", default=[], help="además, evaluar estas candidatas añadidas a la vez")
    args = ap.parse_args()

    d = leer_dataset()
    rng = np.random.default_rng(12345)
    for c in RUIDOS:
        d[c] = rng.normal(size=len(d))
    disc, _ = discretizar(d)
    alta = (disc["Viabilidad_Empresarial"] == "Alta").to_numpy()
    kw = CONFIG[args.fase]
    variables = args.variables or list(CANDIDATAS)
    ruidos = RUIDOS if args.fase == "cribado" else RUIDOS[:3]  # en confirmación cada variable cuesta ~7 min
    variables += [r for r in ruidos if r not in variables]

    t0 = time.time()
    base = cv(d, FEATURES_GA2M, alta, kw)
    print(f"Base (7 variables): Spearman {base[:, 0].mean():.3f} ± {base[:, 0].std():.3f} · "
          f"precisión tercio sup. {base[:, 1].mean():.3f}  [{time.time() - t0:.0f} s]", flush=True)

    filas = []
    pruebas = [[c] for c in variables] + ([args.conjunto] if args.conjunto else [])
    for extra in pruebas:
        col = extra[0] if len(extra) == 1 else "conjunto: " + " + ".join(extra)
        rho, parcial = asociacion(d, extra[0]) if len(extra) == 1 else (np.nan, np.nan)
        m = cv(d, FEATURES_GA2M + extra, alta, kw)
        delta = m - base
        filas.append({"variable": col, "descripcion": CANDIDATAS.get(col, "variables añadidas a la vez" if len(extra) > 1 else "control: ruido aleatorio"),
                      "spearman_simple": rho, "spearman_parcial": parcial,
                      "cv_spearman": m[:, 0].mean(), "delta_spearman": delta[:, 0].mean(),
                      "delta_spearman_sd": delta[:, 0].std(), "reps_mejora": int((delta[:, 0] > 0).sum()),
                      "delta_precision_tercio": delta[:, 1].mean()})
        print(f"  {col:26s} ρ={rho:+.2f} parcial={parcial:+.2f}  Δ Spearman CV={delta[:, 0].mean():+.4f} "
              f"± {delta[:, 0].std():.4f} ({(delta[:, 0] > 0).sum()}/5)  [{time.time() - t0:.0f} s]", flush=True)

    r = pd.DataFrame(filas)
    banda = r[r.variable.isin(RUIDOS)].delta_spearman.max()
    r["supera_ruido"] = (r.delta_spearman > banda) & (r.reps_mejora >= 4) & ~r.variable.isin(RUIDOS)
    r = r.sort_values("delta_spearman", ascending=False)
    r.insert(1, "fase", args.fase)
    r.to_csv(f"data/processed/experimento_variables_{args.fase}.csv", sep=";", index=False, encoding="utf-8-sig")
    print(f"\nBase: {base[:, 0].mean():.3f}. Mejor ruido: Δ = {banda:+.4f}. Con señal (Δ > ruido y ≥ 4/5 repeticiones):")
    print(r[r.supera_ruido][["variable", "delta_spearman", "reps_mejora", "spearman_parcial"]].round(4).to_string(index=False)
          if r.supera_ruido.any() else "  ninguna")


if __name__ == "__main__":
    main()
