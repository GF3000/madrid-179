"""#44 · ¿Qué conjunto de variables e interacciones usar en el GA²M de producción?

Compara configuraciones completas (no una variable cada vez) con el mismo protocolo que ga2m_desempate.py:
CV-5 × 5 repeticiones, particiones rng(rep) y EBM random_state=rep, Spearman fuera de muestra con la tasa
neta y precisión en el tercio superior. La base (7 variables, 5 interacciones) se toma de ga2m_cv.csv,
que usa exactamente esas particiones y semillas, para no repetir 25 ajustes.

Cada configuración se añade al CSV en cuanto termina (el equipo tiene poca memoria y los procesos largos
pueden cortarse). Salida: data/processed/experimento_ga2m_ampliado.csv
Uso: python backend/pipeline/experimento_ga2m_ampliado.py [--solo C1 C3 …]
"""
import argparse
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingRegressor
from scipy.stats import spearmanr

from madrid179.artefactos import leer_dataset
from madrid179.config import EBM_KW
from madrid179.discretizacion import discretizar

warnings.filterwarnings("ignore")
SALIDA = Path("data/processed/experimento_ga2m_ampliado.csv")
TARGET = "tasa_neta_emp"
# Las 7 variables del GA²M original (la red v2 ya incluye las confirmadas como nodos)
BASE = ["dist_sol_km", "pct_estudios_superiores", "paradas_ferro", "vc_residencial_por_uu", "rdb_per_capita",
        "pct_up_servicios_prof", "crec_pob_5a"]
CONFIRMADAS = ["densidad_hab_km2", "pct_menores_45", "sanidad_por_1000hab", "paro_por_100hab"]
DUDOSAS = ["uu_oficinas_por_1000hab", "dist_ferro_km"]
CONFIGS = {
    "C1 base + 4 confirmadas": (BASE + CONFIRMADAS, 5),
    "C2 C1 + 2 dudosas": (BASE + CONFIRMADAS + DUDOSAS, 5),
    "C3 C2 + población": (BASE + CONFIRMADAS + DUDOSAS + ["poblacion"], 5),
    "C4 C2 con 10 interacciones": (BASE + CONFIRMADAS + DUDOSAS, 10),
    "C5 C3 con 10 interacciones (producción)": (BASE + CONFIRMADAS + DUDOSAS + ["poblacion"], 10),
}


def cv(d, feats, interacciones, alta):
    kw = {**{k: v for k, v in EBM_KW.items() if k not in ("random_state", "interactions")}, "n_jobs": 4}
    y = d[TARGET].to_numpy()
    filas = []
    for rep in range(5):
        oof = np.zeros(len(d))
        for f in np.array_split(np.random.default_rng(rep).permutation(len(d)), 5):
            tr = np.setdiff1d(np.arange(len(d)), f)
            m = ExplainableBoostingRegressor(interactions=interacciones, random_state=rep, **kw)
            oof[f] = m.fit(d.iloc[tr][feats], y[tr]).predict(d.iloc[f][feats])
        top = oof >= np.quantile(oof, 2 / 3)
        filas.append((rep, spearmanr(oof, y).statistic, alta[top].mean()))
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", nargs="*", help="prefijos de configuración (p. ej. C1 C4)")
    args = ap.parse_args()
    d = leer_dataset()
    alta = (discretizar(d)[0]["Viabilidad_Empresarial"] == "Alta").to_numpy()
    base = pd.read_csv("data/processed/ga2m_cv.csv", sep=";", encoding="utf-8-sig")
    base = base[base.modelo == "GA2M"].set_index("rep")
    print(f"Base (ga2m_cv.csv): Spearman {base.spearman.mean():.3f} · precisión {base.precision_tercio_sup.mean():.3f}", flush=True)

    hechas = set(pd.read_csv(SALIDA, sep=";", encoding="utf-8-sig").config) if SALIDA.exists() else set()
    for nombre, (feats, inter) in CONFIGS.items():
        if (args.solo and not any(nombre.startswith(s) for s in args.solo)) or nombre in hechas:
            continue
        t0 = time.time()
        r = pd.DataFrame(cv(d, feats, inter, alta), columns=["rep", "spearman", "precision_tercio_sup"])
        r["delta_spearman"] = r.spearman - base.loc[r.rep, "spearman"].to_numpy()
        r["delta_precision"] = r.precision_tercio_sup - base.loc[r.rep, "precision_tercio_sup"].to_numpy()
        r.insert(0, "config", nombre)
        r["variables"] = len(feats)
        r["interacciones"] = inter
        r.to_csv(SALIDA, sep=";", index=False, encoding="utf-8-sig", mode="a", header=not SALIDA.exists())
        print(f"{nombre:30s} Spearman {r.spearman.mean():.3f} (Δ {r.delta_spearman.mean():+.3f} ± "
              f"{r.delta_spearman.std():.3f}, {(r.delta_spearman > 0).sum()}/5) · precisión "
              f"{r.precision_tercio_sup.mean():.3f} (Δ {r.delta_precision.mean():+.3f})  [{time.time() - t0:.0f} s]",
              flush=True)


if __name__ == "__main__":
    main()
