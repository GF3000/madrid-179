"""¿Mejoran las predicciones si el objetivo excluye 2020 y 2021 (años afectados por la COVID)?

El objetivo de producción es la tasa neta de unidades productivas acumulada 2020-2024 (din_emp, IECM),
con contracción empírico-bayesiana (k = mediana de unidades-año). Aquí se rehace con otras ventanas:
  2020-2024  producción (comprobación: debe coincidir con tasa_neta_emp del dataset)
  2021-2024  sin 2020
  2022-2024  sin 2020 ni 2021
  2015-2019  prepandemia: solo para medir cuánto se parece el objetivo a sí mismo entre periodos (techo)
  2020-2021  solo pandemia: ídem

Comparación justa. Con menos años, el objetivo tiene menos unidades-año y es más ruidoso, así que un
Spearman más bajo no significa por sí solo que el modelo sea peor. Por eso:
  1. Cada GA²M se entrena con una ventana y sus predicciones fuera de muestra se evalúan contra TODAS
     las ventanas. La pregunta práctica es: si lo que interesa es la dinámica pospandemia (2022-2024),
     ¿la predice mejor un modelo entrenado solo con esos años o el actual entrenado con 2020-2024?
  2. Fiabilidad del objetivo: Spearman entre ventanas disjuntas (p. ej. 2015-2019 frente a 2022-2024).
  3. Red bayesiana: acierto y log-loss con la viabilidad discretizada en terciles de cada ventana.

Mismo protocolo que experimento_variables.py: CV-5 × 5 repeticiones, mismas particiones para todas las
ventanas (comparación pareada), EBM de producción (config.EBM_KW). Variables explicativas sin cambios.
No toca producción. Salida: data/processed/experimento_covid.csv
Uso: python backend/pipeline/experimento_covid.py [--reps 5]
"""
import argparse
import time
import warnings

import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingRegressor
from scipy.stats import spearmanr

from madrid179.artefactos import leer_dataset
from madrid179.config import EBM_KW, FEATURES_GA2M, NODOS, OBJETIVO
from madrid179.discretizacion import discretizar
from madrid179.red import validar

warnings.filterwarnings("ignore")

VENTANAS = {"2020-2024": range(2020, 2025), "2021-2024": range(2021, 2025), "2022-2024": range(2022, 2025),
            "2015-2019": range(2015, 2020), "2020-2021": range(2020, 2022)}
ENTRENAR = ["2020-2024", "2021-2024", "2022-2024"]  # las otras dos solo sirven para medir la fiabilidad
KW = {**{k: v for k, v in EBM_KW.items() if k != "random_state"}, "n_jobs": 4}  # poca memoria libre


def objetivo(anios, indice):
    """Tasa neta acumulada en la ventana, con la misma contracción que construir_dataset_bn.py."""
    de = pd.read_csv("data/processed/municipal/din_emp.csv", sep=";", dtype=str, encoding="utf-8-sig")
    de = de.rename(columns={c: "Anio" for c in de.columns if c.startswith("A") and c.endswith("o") and len(c) == 3})
    de = de[(de["Tipo territorio"] == "Municipios") & de.ine5.notna() & de.Anio.isin([str(a) for a in anios])]
    de["Valor"] = pd.to_numeric(de.Valor, errors="coerce")
    p = de.pivot_table(index="ine5", columns="Medida", values="Valor", aggfunc="sum").reindex(indice)
    up = lambda m: p["Unidades productivas " + m]
    net = up("nacen") + up("entran") - up("mueren") - up("salen")
    inicio = up("inicio periodo")
    r_bar, k = net.sum() / inicio.sum(), float(inicio.median())
    return (net + k * r_bar) / (inicio + k), inicio


def cv_oof(X, y, reps):
    """Predicciones fuera de muestra (CV-5) por repetición; particiones fijadas por la semilla."""
    out = []
    for rep in range(reps):
        folds = np.array_split(np.random.default_rng(rep).permutation(len(X)), 5)
        oof = np.zeros(len(X))
        for f in folds:
            tr = np.setdiff1d(np.arange(len(X)), f)
            oof[f] = ExplainableBoostingRegressor(random_state=rep, **KW).fit(X.iloc[tr], y[tr]).predict(X.iloc[f])
        out.append(oof)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    args = ap.parse_args()

    d = leer_dataset()
    Y, inicio = {}, {}
    for v, anios in VENTANAS.items():
        Y[v], inicio[v] = objetivo(anios, d.index)
    assert np.allclose(Y["2020-2024"], d[NODOS[OBJETIVO][0]]), "la ventana 2020-2024 no reproduce el objetivo de producción"
    assert all(Y[v].notna().all() for v in Y), "faltan municipios en alguna ventana"

    print("Unidades-año por municipio (mediana): " + " · ".join(f"{v} {inicio[v].median():.0f}" for v in VENTANAS))
    print("\nFiabilidad del objetivo (Spearman entre ventanas):")
    vs = list(VENTANAS)
    fiab = pd.DataFrame([[spearmanr(Y[a], Y[b]).statistic for b in vs] for a in vs], index=vs, columns=vs)
    print(fiab.round(3).to_string())

    filas = []
    print("\nRed bayesiana (viabilidad en terciles de cada ventana; CV-5 × reps):")
    disc0, _ = discretizar(d)
    for v in ENTRENAR:
        disc = disc0.copy()
        disc[OBJETIVO] = pd.qcut(Y[v], 3, labels=NODOS[OBJETIVO][1]).astype(str)
        r = np.array([validar(disc, seed=s)[:2] for s in range(args.reps)])
        filas.append({"modelo": "red", "entrenado_con": v, "evaluado_con": v, "acierto": r[:, 0].mean(),
                      "acierto_sd": r[:, 0].std(), "logloss": r[:, 1].mean(), "logloss_sd": r[:, 1].std()})
        print(f"  {v}: acierto {r[:, 0].mean():.3f} ± {r[:, 0].std():.3f} · log-loss {r[:, 1].mean():.4f} ± "
              f"{r[:, 1].std():.4f} (uniforme {np.log(3):.4f})")

    print("\nGA²M (filas: entrenado con · columnas: evaluado contra; Spearman fuera de muestra):", flush=True)
    t0 = time.time()
    X = d[FEATURES_GA2M]
    for v in ENTRENAR:
        oofs = cv_oof(X, Y[v].to_numpy(), args.reps)
        linea = []
        for e in vs:
            y = Y[e].to_numpy()
            rho = np.array([spearmanr(o, y).statistic for o in oofs])
            alta = y >= np.quantile(y, 2 / 3)
            prec = np.array([alta[o >= np.quantile(o, 2 / 3)].mean() for o in oofs])
            baja = y <= np.quantile(y, 1 / 3)
            top10 = np.array([baja[np.argsort(-o)[:10]].mean() for o in oofs])  # recomendados que acaban en el tercio inferior
            filas.append({"modelo": "ga2m", "entrenado_con": v, "evaluado_con": e, "spearman": rho.mean(),
                          "spearman_sd": rho.std(), "precision_tercio_sup": prec.mean(),
                          "top10_en_tercio_inf": top10.mean(), "spearman_por_rep": " ".join(f"{x:.3f}" for x in rho)})
            linea.append(f"{e} {rho.mean():.3f}±{rho.std():.3f}")
        print(f"  {v}: " + " · ".join(linea) + f"  [{time.time() - t0:.0f} s]", flush=True)

    r = pd.DataFrame(filas)
    r.to_csv("data/processed/experimento_covid.csv", sep=";", index=False, encoding="utf-8-sig")
    fiab.to_csv("data/processed/experimento_covid_fiabilidad.csv", sep=";", encoding="utf-8-sig")
    print("\nGuardado en data/processed/experimento_covid.csv y experimento_covid_fiabilidad.csv")


if __name__ == "__main__":
    main()
