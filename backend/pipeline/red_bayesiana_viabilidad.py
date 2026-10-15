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
from pgmpy.inference import VariableElimination

# La lógica vive en el paquete madrid179 (backend/madrid179); este script la ejecuta y escribe las salidas.
# Los nombres se reexportan porque auditoria_cpts.py, diagrama_red_bayesiana.py y los experimentos los usan.
from madrid179.config import (COMBINACION, EBM_KW, EDGES, ESS, FILTROS, NODOS, PESOS_B,  # noqa: F401
                              TEMPERATURA_B)
from madrid179.discretizacion import discretizar
from madrid179.ga2m import ga2m
from madrid179.red import construir_modelo, cpd_utilidad, validar  # noqa: F401

DATA = "data/processed/dataset_bn_municipios.csv"
OUT = "data/processed/"


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
