"""PENDIENTES #5 · ¿Aporta un GA²M (EBM de InterpretML) para desempatar el ranking de la red bayesiana?

Compara, con CV de 5 particiones repetida 5 veces y predicciones fuera de muestra:
  BN          P(Viabilidad = Alta) de la red (9 niveles posibles)
  GA2M        EBM con interacciones por pares sobre las 7 variables continuas de la red
  GAM         EBM sin interacciones
  Lineal      regresión ridge sobre rangos (referencia simple)
  BN > GA2M   orden lexicográfico: nivel de la red y, dentro de cada nivel, el GA²M (desempate)
  Media rangos  media del rango de BN y del rango de GA²M
Métricas: Spearman con la tasa neta observada, precisión en el tercio superior, nº de puntuaciones distintas.
Salida: data/processed/ga2m_cv.csv
"""
import sys
import warnings

import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingRegressor
from scipy.stats import spearmanr
from sklearn.linear_model import RidgeCV

warnings.filterwarnings("ignore")
sys.path.insert(0, "backend/pipeline")
import red_bayesiana_viabilidad as rb  # noqa: E402
from pgmpy.inference import VariableElimination  # noqa: E402

FEATS = [rb.NODOS[n][0] for n in rb.NODOS if n != "Viabilidad_Empresarial"]
TARGET = "tasa_neta_emp"
EBM_KW = dict(max_bins=32, min_samples_leaf=10, outer_bags=8, learning_rate=0.02, max_rounds=3000)

d = pd.read_csv(rb.DATA, sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
disc, _ = rb.discretizar(d)  # umbrales sobre los 179 (igual que en producción)
y = d[TARGET].to_numpy()
alta = (disc["Viabilidad_Empresarial"] == "Alta").to_numpy()


def p_alta_bn(train_idx, test_idx):
    inf = VariableElimination(rb.construir_modelo(disc.iloc[train_idx], "A"))
    out = []
    for _, row in disc.iloc[test_idx].iterrows():
        ev = {n: row[n] for n in rb.NODOS if n != "Viabilidad_Empresarial"}
        q = inf.query(["Viabilidad_Empresarial"], evidence=ev, show_progress=False)
        out.append(dict(zip(q.state_names["Viabilidad_Empresarial"], q.values))["Alta"])
    return np.array(out)


def ebm(interacciones, seed):
    return ExplainableBoostingRegressor(interactions=interacciones, random_state=seed, **EBM_KW)


def rank(a):
    return pd.Series(a).rank(method="average").to_numpy()


filas = []
for rep in range(5):
    rng = np.random.default_rng(rep)
    folds = np.array_split(rng.permutation(len(d)), 5)
    oof = {k: np.zeros(len(d)) for k in ["BN", "GA2M", "GAM", "Lineal"]}
    for f in folds:
        tr = np.setdiff1d(np.arange(len(d)), f)
        Xtr, Xte = d.iloc[tr][FEATS], d.iloc[f][FEATS]
        oof["BN"][f] = p_alta_bn(tr, f)
        oof["GA2M"][f] = ebm(5, rep).fit(Xtr, y[tr]).predict(Xte)
        oof["GAM"][f] = ebm(0, rep).fit(Xtr, y[tr]).predict(Xte)
        lin = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(Xtr.rank(pct=True), y[tr])
        # rangos del test referidos a la distribución de entrenamiento
        Xte_r = pd.DataFrame({c: [np.mean(Xtr[c].to_numpy() <= v) for v in Xte[c]] for c in FEATS})
        oof["Lineal"][f] = lin.predict(Xte_r)
    # combinaciones (dentro de cada repetición, con predicciones fuera de muestra)
    oof["BN > GA2M"] = np.round(oof["BN"], 6) * 1e6 + rank(oof["GA2M"]) / (len(d) + 1)  # lexicográfico
    oof["Media rangos"] = (rank(oof["BN"]) + rank(oof["GA2M"])) / 2
    for k, s in oof.items():
        top = s >= np.quantile(s, 2 / 3)
        filas.append({"rep": rep, "modelo": k, "spearman": spearmanr(s, y).statistic,
                      "precision_tercio_sup": alta[top].mean(), "puntuaciones_distintas": len(np.unique(np.round(s, 9)))})
    print(f"repetición {rep + 1}/5 hecha", flush=True)

r = pd.DataFrame(filas)
r.to_csv("data/processed/ga2m_cv.csv", sep=";", index=False, encoding="utf-8-sig")
res = r.groupby("modelo").agg(spearman=("spearman", "mean"), spearman_sd=("spearman", "std"),
                              prec_top=("precision_tercio_sup", "mean"), prec_top_sd=("precision_tercio_sup", "std"),
                              distintas=("puntuaciones_distintas", "mean")).sort_values("spearman", ascending=False)
print(res.round(3).to_string())
print("Referencia: precisión del tercio superior por azar = 0,335 (60/179); Spearman por azar = 0")
