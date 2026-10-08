"""Red bayesiana: construcción, validación cruzada e inferencia."""
from itertools import product

import numpy as np
from pgmpy.estimators import BayesianEstimator
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from pgmpy.models import DiscreteBayesianNetwork

from .config import EDGES, ESS, EVIDENCIAS, NODOS, OBJETIVO, PESOS_B, TEMPERATURA_B


def cpd_utilidad(estados_nodo):
    """Opción B: P(Viabilidad | padres) a partir de una utilidad ponderada de los estados padre."""
    padres = [p for p, h in EDGES if h == OBJETIVO]
    est_p = [estados_nodo[p] for p in padres]
    est_v = estados_nodo[OBJETIVO]
    centros = np.linspace(0, 1, len(est_v))  # Baja=0, Media=0.5, Alta=1
    cols = []
    for combo in product(*[range(len(e)) for e in est_p]):  # orden de columnas de pgmpy: último padre varía más rápido
        u = sum(PESOS_B[p] * (i / (len(estados_nodo[p]) - 1)) for p, i in zip(padres, combo))
        w = np.exp(-((centros - u) ** 2) / (2 * TEMPERATURA_B ** 2))
        cols.append(w / w.sum())
    return TabularCPD(OBJETIVO, len(est_v), np.array(cols).T, evidence=padres,
                      evidence_card=[len(e) for e in est_p],
                      state_names={OBJETIVO: est_v, **{p: estados_nodo[p] for p in padres}})


def construir_modelo(disc, modo="A"):
    estados = {n: NODOS[n][1] for n in NODOS}
    model = DiscreteBayesianNetwork(EDGES)
    est = BayesianEstimator(model, disc[list(NODOS)], state_names=estados)  # pgmpy >= 1.0
    model.add_cpds(*est.get_parameters(prior_type="BDeu", equivalent_sample_size=ESS))
    if modo == "B":
        model.remove_cpds(model.get_cpds(OBJETIVO))
        model.add_cpds(cpd_utilidad(estados))
    assert model.check_model()
    return model


def distribucion(inferencia, evidencia, variable=OBJETIVO):
    """P(variable | evidencia) como diccionario estado -> probabilidad."""
    p = inferencia.query([variable], evidence=evidencia, show_progress=False)
    return {s: float(v) for s, v in zip(p.state_names[variable], p.values)}


def validar(disc, modo="A", k=5, seed=0):
    """CV k-fold: precisión y log-loss al predecir Viabilidad con el resto de nodos como evidencia."""
    rng = np.random.default_rng(seed)
    folds = np.array_split(rng.permutation(len(disc)), k)
    est_v = NODOS[OBJETIVO][1]
    acc, ll = [], []
    for f in folds:
        test, train = disc.iloc[f], disc.drop(disc.index[f])
        inf = VariableElimination(construir_modelo(train, modo))
        for _, row in test.iterrows():
            probs = distribucion(inf, {n: row[n] for n in EVIDENCIAS})
            acc.append(max(probs, key=probs.get) == row[OBJETIVO])
            ll.append(-np.log(max(probs[row[OBJETIVO]], 1e-9)))
    return float(np.mean(acc)), float(np.mean(ll)), float(np.log(len(est_v)))
