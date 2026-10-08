"""Red bayesiana de viabilidad empresarial municipal (CAM) con pgmpy.

Entrada : data/processed/dataset_bn_municipios.csv  (179 municipios, clave ine5; lo genera construir_dataset_bn.py)
Salidas : data/processed/bn_dataset_discretizado.csv, data/processed/bn_umbrales.json, data/processed/bn_cpts.txt,
          data/processed/bn_ranking_municipios.csv
Uso     : python red_bayesiana_viabilidad.py [--modo A|B]
          A = CPTs empíricas con BayesianEstimator (prior BDeu)   [por defecto]
          B = CPT de Viabilidad por función de utilidad ponderada; resto de nodos empíricos
"""
import argparse
import json
from itertools import product

import numpy as np
import pandas as pd
from pgmpy.estimators import BayesianEstimator
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from pgmpy.models import DiscreteBayesianNetwork

DATA = "data/processed/dataset_bn_municipios.csv"
OUT = "data/processed/"
ESS = 10  # equivalent sample size del prior BDeu (179 filas -> prior moderado)

# ---------------------------------------------------------------------------
# 1. Filtros duros (preprocesado tabular, NO entran en la red)
# ---------------------------------------------------------------------------
FILTROS = {
    # Objetivo de reequilibrio: la capital no es candidata a recibir la oficina deslocalizada
    "excluir_madrid_capital": lambda d: d.index != "28079",
    # Mínimo de oferta terciaria existente (Catastro: unidades urbanas de uso oficinas)
    "min_uu_oficinas": lambda d: d.uu_oficinas >= 1,
    # Opcional, según preferencias del negocio: exigir elegibilidad a ayudas de despoblación (<20.000 hab.)
    # "solo_elegibles_despoblacion": lambda d: d.poblacion < 20000,
}

# ---------------------------------------------------------------------------
# 2. Nodos de la red: columna origen, estados y método de corte
#    'terciles' -> cortes en p33/p66 de la distribución real de los 179 municipios
# ---------------------------------------------------------------------------
NODOS = {
    "Distancia_Madrid":          ("dist_sol_km",             ["Cerca", "Media", "Lejos"], "terciles"),
    "Talento":                   ("pct_estudios_superiores", ["Bajo", "Medio", "Alto"],   "terciles"),
    "Acceso_Ferroviario":        ("paradas_ferro",           ["No", "Si"],                "binario>0"),
    "Coste_Inmobiliario":        ("vc_residencial_por_uu",   ["Bajo", "Medio", "Alto"],   "terciles"),
    "Renta":                     ("rdb_per_capita",          ["Baja", "Media", "Alta"],   "terciles"),
    "Especializacion_Servicios": ("pct_up_servicios_prof",   ["Baja", "Media", "Alta"],   "terciles"),
    "Dinamismo_Demografico":     ("crec_pob_5a",             ["Bajo", "Medio", "Alto"],   "terciles"),
    "Viabilidad_Empresarial":    ("tasa_neta_emp",           ["Baja", "Media", "Alta"],   "terciles"),
}

# ---------------------------------------------------------------------------
# 3. DAG (máx. 2 padres por nodo)
# ---------------------------------------------------------------------------
EDGES = [
    ("Distancia_Madrid", "Acceso_Ferroviario"),
    ("Distancia_Madrid", "Coste_Inmobiliario"),
    ("Talento", "Coste_Inmobiliario"),
    ("Talento", "Renta"),
    ("Talento", "Especializacion_Servicios"),
    ("Distancia_Madrid", "Especializacion_Servicios"),
    ("Distancia_Madrid", "Dinamismo_Demografico"),
    ("Coste_Inmobiliario", "Dinamismo_Demografico"),
    ("Dinamismo_Demografico", "Viabilidad_Empresarial"),
    ("Especializacion_Servicios", "Viabilidad_Empresarial"),
]

# Ranking final (PENDIENTES #5). Con evidencia completa la red solo da 9 niveles; un GA²M (EBM) sobre las
# mismas 7 variables continuas desempata y ordena mejor (ga2m_desempate.py, CV-5 x 5, Spearman con la tasa
# neta: BN 0,284 · GA²M 0,398 · media de rangos 0,369 · lexicográfico 0,291).
# Decisión 2026-10-07 (PENDIENTES #40, opción b): el GA²M da la puntuación; la red bayesiana explica,
# atiende consultas con evidencia parcial y sostiene el simulador do() de la Administración.
#   "ga2m"           -> puntuación = percentil del GA²M entre los candidatos, 0-100 (por defecto)
#   "media_rangos"   -> media del percentil de la red y del percentil del GA²M
#   "lexicografico"  -> nivel de la red y el GA²M solo desempata dentro de cada nivel
#   "bn"             -> solo la red, 100 × P(Alta)
COMBINACION = "ga2m"
EBM_KW = dict(interactions=5, max_bins=32, min_samples_leaf=10, outer_bags=8, learning_rate=0.02,
              max_rounds=3000, random_state=0)

# Pesos de la Opción B (contribución de cada estado padre a la utilidad de viabilidad, escala 0-1)
PESOS_B = {"Dinamismo_Demografico": 0.55, "Especializacion_Servicios": 0.45}
TEMPERATURA_B = 0.25  # menor = CPT más determinista


def discretizar(d):
    umbrales, disc = {}, pd.DataFrame(index=d.index)
    for nodo, (col, estados, metodo) in NODOS.items():
        x = d[col]
        if metodo == "terciles":
            q1, q2 = x.quantile([1 / 3, 2 / 3])
            cortes = [-np.inf, q1, q2, np.inf]
        elif metodo == "binario>0":
            cortes = [-np.inf, 0, np.inf]
        disc[nodo] = pd.cut(x, cortes, labels=estados, right=True).astype(str)
        umbrales[nodo] = {"columna": col, "metodo": metodo, "estados": estados,
                          "cortes": [float(c) for c in cortes[1:-1]],
                          "conteo": disc[nodo].value_counts().reindex(estados).fillna(0).astype(int).tolist()}
    return disc, umbrales


def cpd_utilidad(estados_nodo):
    """Opción B: P(Viabilidad | padres) a partir de una utilidad ponderada de los estados padre."""
    padres = [p for p, h in EDGES if h == "Viabilidad_Empresarial"]
    est_p = [estados_nodo[p] for p in padres]
    est_v = estados_nodo["Viabilidad_Empresarial"]
    centros = np.linspace(0, 1, len(est_v))  # Baja=0, Media=0.5, Alta=1
    cols = []
    for combo in product(*[range(len(e)) for e in est_p]):  # orden de columnas de pgmpy: último padre varía más rápido
        u = sum(PESOS_B[p] * (i / (len(estados_nodo[p]) - 1)) for p, i in zip(padres, combo))
        w = np.exp(-((centros - u) ** 2) / (2 * TEMPERATURA_B ** 2))
        cols.append(w / w.sum())
    return TabularCPD("Viabilidad_Empresarial", len(est_v), np.array(cols).T, evidence=padres,
                      evidence_card=[len(e) for e in est_p],
                      state_names={"Viabilidad_Empresarial": est_v, **{p: estados_nodo[p] for p in padres}})


def construir_modelo(disc, modo):
    estados = {n: NODOS[n][1] for n in NODOS}
    model = DiscreteBayesianNetwork(EDGES)
    est = BayesianEstimator(model, disc[list(NODOS)], state_names=estados)  # pgmpy >= 1.0
    model.add_cpds(*est.get_parameters(prior_type="BDeu", equivalent_sample_size=ESS))
    if modo == "B":
        model.remove_cpds(model.get_cpds("Viabilidad_Empresarial"))
        model.add_cpds(cpd_utilidad(estados))
    assert model.check_model()
    return model


def validar(disc, modo, k=5, seed=0):
    """CV k-fold: precisión y log-loss al predecir Viabilidad con el resto de nodos como evidencia."""
    rng = np.random.default_rng(seed)
    folds = np.array_split(rng.permutation(len(disc)), k)
    est_v = NODOS["Viabilidad_Empresarial"][1]
    acc, ll = [], []
    for f in folds:
        test, train = disc.iloc[f], disc.drop(disc.index[f])
        inf = VariableElimination(construir_modelo(train, modo))
        for _, row in test.iterrows():
            ev = {n: row[n] for n in NODOS if n != "Viabilidad_Empresarial"}
            p = inf.query(["Viabilidad_Empresarial"], evidence=ev, show_progress=False)
            probs = dict(zip(p.state_names["Viabilidad_Empresarial"], p.values))
            acc.append(max(probs, key=probs.get) == row["Viabilidad_Empresarial"])
            ll.append(-np.log(max(probs[row["Viabilidad_Empresarial"]], 1e-9)))
    return float(np.mean(acc)), float(np.mean(ll)), float(np.log(len(est_v)))


def ga2m(d, candidatos):
    """Ajusta el GA²M sobre los 179 municipios y devuelve predicción y contribución de cada término
    para los candidatos (base de la explicación por municipio, PENDIENTES #31)."""
    from interpret.glassbox import ExplainableBoostingRegressor  # import local: el resto de scripts no lo necesita
    feats = [NODOS[n][0] for n in NODOS if n != "Viabilidad_Empresarial"]
    ebm = ExplainableBoostingRegressor(**EBM_KW).fit(d[feats], d[NODOS["Viabilidad_Empresarial"][0]])
    Xc = d.loc[candidatos, feats]
    contrib = pd.DataFrame(ebm.eval_terms(Xc), index=candidatos, columns=ebm.term_names_)
    contrib.insert(0, "intercepto", float(ebm.intercept_))
    imp = pd.Series(ebm.term_importances(), index=ebm.term_names_).sort_values(ascending=False)
    return pd.Series(ebm.predict(Xc), index=candidatos), contrib, imp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", choices=["A", "B"], default="A")
    modo = ap.parse_args().modo

    d = pd.read_csv(DATA, sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
    # Los umbrales se calculan sobre los 179 municipios (distribución real de la CAM) ...
    disc, umbrales = discretizar(d)
    disc.join(d[["nombre_iecm"]]).to_csv(OUT + "bn_dataset_discretizado.csv", sep=";", encoding="utf-8-sig")
    json.dump(umbrales, open(OUT + "bn_umbrales.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    model = construir_modelo(disc, modo)
    print(f"Modo {modo} | nodos={len(model.nodes())} aristas={len(model.edges())} | check_model() = {model.check_model()}")
    for n, u in umbrales.items():
        print(f"  {n:27s} {u['columna']:25s} cortes={[round(c, 4) for c in u['cortes']]} n={u['conteo']}")
    with open(OUT + "bn_cpts.txt", "w", encoding="utf-8") as fh:
        for cpd in model.get_cpds():  # tabla completa (str(cpd) trunca columnas)
            fh.write(f"## P({cpd.variable} | {', '.join(cpd.variables[1:]) or '-'})\n")
            ev = cpd.variables[1:]
            cols = pd.MultiIndex.from_tuples(list(product(*[cpd.state_names[e] for e in ev])), names=ev) if ev else ["P"]
            tab = pd.DataFrame(cpd.get_values(), index=cpd.state_names[cpd.variable], columns=cols)
            fh.write(tab.round(4).to_string() + "\n\n")

    acc, ll, ll_base = validar(disc, modo)
    print(f"CV 5-fold Viabilidad: accuracy={acc:.3f} (azar 0.333) | log-loss={ll:.3f} (uniforme {ll_base:.3f})")

    # ... y los filtros duros solo restringen el conjunto de candidatos que se puntúa.
    mask = np.logical_and.reduce([f(d) for f in FILTROS.values()])
    inf = VariableElimination(model)
    filas = []
    for ine5, row in disc[mask].iterrows():
        ev = {n: row[n] for n in NODOS if n != "Viabilidad_Empresarial"}
        p = inf.query(["Viabilidad_Empresarial"], evidence=ev, show_progress=False)
        probs = dict(zip(p.state_names["Viabilidad_Empresarial"], p.values))
        filas.append({"ine5": ine5, "municipio": d.loc[ine5, "nombre_iecm"], "P_Alta": probs["Alta"],
                      "P_Media": probs["Media"], "P_Baja": probs["Baja"], **ev,
                      "Viabilidad_observada": row["Viabilidad_Empresarial"]})
    rk = pd.DataFrame(filas).set_index("ine5")
    pred, contrib, imp = ga2m(d, rk.index)
    rk["ga2m_tasa_neta_pred_pct"] = pred * 100
    rk["percentil_bn"] = rk.P_Alta.rank(pct=True) * 100
    rk["percentil_ga2m"] = pred.rank(pct=True) * 100
    if COMBINACION == "ga2m":
        rk["puntuacion"] = rk.percentil_ga2m
    elif COMBINACION == "media_rangos":
        rk["puntuacion"] = (rk.percentil_bn + rk.percentil_ga2m) / 2
    elif COMBINACION == "lexicografico":
        rk["puntuacion"] = rk.P_Alta.round(6) * 100 + rk.percentil_ga2m / 1000
    else:
        rk["puntuacion"] = rk.P_Alta * 100
    if "nivel_ayudas" in d.columns:  # informativo (#10): no interviene en la puntuación
        rk["nivel_ayudas"] = d.loc[rk.index, "nivel_ayudas"]
    rk = rk.sort_values(["puntuacion", "P_Alta"], ascending=False)
    rk.insert(0, "posicion", range(1, len(rk) + 1))
    rk.reset_index().to_csv(OUT + "bn_ranking_municipios.csv", sep=";", index=False, encoding="utf-8-sig")
    contrib.loc[rk.index].join(d[["nombre_iecm"]]).to_csv(OUT + "ga2m_contribuciones.csv", sep=";", encoding="utf-8-sig")
    imp.rename("importancia_media_abs").to_csv(OUT + "ga2m_importancias.csv", sep=";", encoding="utf-8-sig")
    print(f"Candidatos tras filtros duros: {mask.sum()} de {len(d)} | combinación: {COMBINACION} | "
          f"puntuaciones distintas: {rk.puntuacion.round(6).nunique()} (solo red: {rk.P_Alta.round(6).nunique()})")
    print(rk.head(10)[["posicion", "municipio", "puntuacion", "P_Alta", "ga2m_tasa_neta_pred_pct"]].round(3).to_string(index=False))
    print("Importancia de los términos del GA²M:", imp.round(5).head(8).to_dict())

    # Ejemplo de consulta con preferencias de negocio como evidencia parcial
    q = inf.query(["Viabilidad_Empresarial"], evidence={"Talento": "Alto", "Distancia_Madrid": "Lejos"}, show_progress=False)
    print("\nP(Viabilidad | Talento=Alto, Distancia=Lejos):", dict(zip(q.state_names["Viabilidad_Empresarial"], q.values.round(3))))


if __name__ == "__main__":
    main()
