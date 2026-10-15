"""#37 · #7 · #44 · Calibración y estructura de la red bayesiana.

Para cada combinación de (padres de la viabilidad, ESS del prior BDeu) mide con CV-5 × 5 repeticiones
(mismas particiones que validar()): acierto, log-loss (referencia uniforme 1,099) y Spearman de P(Alta)
fuera de muestra con la tasa neta. Con evidencia completa solo cuentan los padres del objetivo, así que la
estructura relevante para predecir es el conjunto de padres; los nodos nuevos se discretizan en terciles.

También cuenta las violaciones de monotonía de la CPT del objetivo (#3): pares de casillas vecinas en las
que mejorar un padre baja P(Alta).

No toca producción. Salida: data/processed/experimento_red_ampliada.csv
"""
import warnings
from itertools import product

import numpy as np
import pandas as pd
from pgmpy.inference import VariableElimination
from scipy.stats import spearmanr

import madrid179.discretizacion as md
import madrid179.red as mr
from madrid179.artefactos import leer_dataset
from madrid179.config import EDGES, NODOS, OBJETIVO

warnings.filterwarnings("ignore")
NUEVOS = {
    "Densidad": ("densidad_hab_km2", ["Baja", "Media", "Alta"], "terciles"),
    "Juventud": ("pct_menores_45", ["Baja", "Media", "Alta"], "terciles"),
    "Sanidad": ("sanidad_por_1000hab", ["Baja", "Media", "Alta"], "terciles"),
    "Paro": ("paro_por_100hab", ["Bajo", "Medio", "Alto"], "terciles"),
}
PADRES = {
    "actual: Dinamismo + Especialización": ["Dinamismo_Demografico", "Especializacion_Servicios"],
    "Dinamismo + Densidad": ["Dinamismo_Demografico", "Densidad"],
    "Especialización + Densidad": ["Especializacion_Servicios", "Densidad"],
    "Densidad + Juventud": ["Densidad", "Juventud"],
    "Dinamismo + Juventud": ["Dinamismo_Demografico", "Juventud"],
    "Dinamismo + Especialización + Densidad": ["Dinamismo_Demografico", "Especializacion_Servicios", "Densidad"],
    "Dinamismo + Especialización + Juventud": ["Dinamismo_Demografico", "Especializacion_Servicios", "Juventud"],
}
ESS = [1, 5, 10, 20, 50, 100]


def violaciones_monotonia(red, padres):
    """Casillas vecinas (un padre sube un estado, el resto igual) en las que P(Alta) baja."""
    cpd = red.get_cpds(OBJETIVO)
    alta = cpd.state_names[OBJETIVO].index("Alta")
    vals = cpd.get_values()[alta].reshape([len(cpd.state_names[p]) for p in cpd.variables[1:]])
    n = 0
    for idx in product(*[range(s) for s in vals.shape]):
        for eje in range(vals.ndim):
            if idx[eje] + 1 < vals.shape[eje]:
                sig = list(idx); sig[eje] += 1
                n += vals[tuple(sig)] < vals[idx] - 1e-12
    return int(n)


def main():
    d = leer_dataset()
    nodos = {**NODOS, **NUEVOS}
    md.NODOS = nodos
    disc, _ = md.discretizar(d)
    y = d.tasa_neta_emp.to_numpy()
    filas = []
    for nombre, padres in PADRES.items():
        edges = [e for e in EDGES if e[1] != OBJETIVO] + [(p, OBJETIVO) for p in padres]
        usados = sorted({n for e in edges for n in e})
        mr.NODOS = {n: nodos[n] for n in usados}
        mr.EDGES = edges
        mr.EVIDENCIAS = [n for n in usados if n != OBJETIVO]
        for ess in ESS:
            mr.ESS = ess
            acc, ll, rho = [], [], []
            for rep in range(5):
                a, l, _ = mr.validar(disc, "A", seed=rep)
                acc.append(a); ll.append(l)
                # Spearman de P(Alta) fuera de muestra con la tasa neta (mismas particiones que validar)
                oof = np.zeros(len(d))
                for f in np.array_split(np.random.default_rng(rep).permutation(len(d)), 5):
                    inf = VariableElimination(mr.construir_modelo(disc.drop(disc.index[f]), "A"))
                    oof[f] = [mr.distribucion(inf, {n: r[n] for n in padres})["Alta"] for _, r in disc.iloc[f].iterrows()]
                rho.append(spearmanr(oof, y).statistic)
            mono = violaciones_monotonia(mr.construir_modelo(disc, "A"), padres)
            filas.append({"padres": nombre, "n_padres": len(padres), "ess": ess,
                          "acierto": np.mean(acc), "acierto_sd": np.std(acc), "log_loss": np.mean(ll),
                          "log_loss_sd": np.std(ll), "spearman_p_alta": np.mean(rho), "violaciones_monotonia": mono})
            print(f"{nombre:42s} ESS={ess:<4d} acierto {np.mean(acc):.3f} · log-loss {np.mean(ll):.4f} ± {np.std(ll):.4f} "
                  f"· ρ {np.mean(rho):.3f} · no monótonas {mono}", flush=True)
    r = pd.DataFrame(filas)
    r.to_csv("data/processed/experimento_red_ampliada.csv", sep=";", index=False, encoding="utf-8-sig")
    print(f"\nUniforme: log-loss {np.log(3):.4f}. Mejores por log-loss:")
    print(r.sort_values("log_loss").head(8).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
