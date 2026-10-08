"""Discretización de las variables continuas en los estados de la red (terciles de los 179 municipios)."""
import numpy as np
import pandas as pd

from .config import NODOS


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
