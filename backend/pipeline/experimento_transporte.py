"""Experimento: ¿qué variable de transporte aporta señal y dónde colocarla en la red?
1. Construye métricas de transporte por municipio desde el GTFS del CRTM.
2. Mide su asociación con el target y su colinealidad con los nodos actuales.
3. Compara estructuras alternativas con la misma CV de 5 particiones que red_bayesiana_viabilidad.py.
No modifica el modelo de producción. Salida: data/processed/experimento_transporte.csv
"""
import sys

import numpy as np
import pandas as pd
import shapefile
from pyproj import Transformer
from shapely.geometry import shape

sys.path.insert(0, "backend/pipeline")
import madrid179.discretizacion as md  # noqa: E402
import madrid179.red as mr  # noqa: E402
import red_bayesiana_viabilidad as rb  # noqa: E402

d = pd.read_csv(rb.DATA, sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
st = pd.read_csv("data/processed/gtfs_paradas_con_seccion.csv", sep=";", dtype={"ine5": str}, encoding="utf-8-sig")
T = Transformer.from_crs(4326, 25830, always_xy=True)
st["x"], st["y"] = T.transform(st.lon.to_numpy(), st.lat.to_numpy())

# Centroide de cada municipio (ponderado por área de sus secciones)
acc = {}
for sr in shapefile.Reader("data/raw/cam_geo/secciones_shp/Seccionado_2019.shp", encoding="latin-1").shapeRecords():
    g = shape(sr.shape.__geo_interface__); m = "28" + sr.record.as_dict()["CDMUNI"]
    a, cx, cy = acc.get(m, (0, 0, 0)); acc[m] = (a + g.area, cx + g.centroid.x * g.area, cy + g.centroid.y * g.area)
cen = pd.DataFrame({m: (cx / a, cy / a) for m, (a, cx, cy) in acc.items()}, index=["cx", "cy"]).T

ferro = st[st.modo.isin(["metro", "metroligero", "cercanias"])][["x", "y"]].to_numpy()
cerc = st[st.modo == "cercanias"][["x", "y"]].to_numpy()
bus = st[st.modo.isin(["interurbanos", "emt"])]


def dist_min(pts):
    return pd.Series({m: np.min(np.hypot(pts[:, 0] - r.cx, pts[:, 1] - r.cy)) / 1000 for m, r in cen.iterrows()})


t = pd.DataFrame(index=d.index)
t["dist_ferro_km"] = dist_min(ferro)                       # distancia a la estación ferroviaria más cercana
t["dist_cercanias_km"] = dist_min(cerc)
t["paradas_bus_km2"] = bus.groupby("ine5").size().reindex(d.index).fillna(0) / d.superficie_km2
t["paradas_total_km2"] = d.paradas_total / d.superficie_km2
t["paradas_ferro"] = d.paradas_ferro
t["paradas_por_1000hab"] = d.paradas_por_1000hab
t.to_csv("data/processed/experimento_transporte_metricas.csv", sep=";", encoding="utf-8-sig")

print("== Spearman de cada métrica de transporte ==")
ref = {"target": d.tasa_neta_emp, "Dinamismo": d.crec_pob_5a, "Especializ.": d.pct_up_servicios_prof, "Distancia": d.dist_sol_km}
print(pd.DataFrame({k: [t[c].corr(v, method="spearman") for c in t] for k, v in ref.items()}, index=t.columns).round(2).to_string())

# ---- Comparación de estructuras ----
d2 = d.drop(columns=["dist_ferro_km"], errors="ignore").join(t[["dist_ferro_km", "paradas_bus_km2"]])  # el dataset ya trae dist_ferro_km (2026-10-07)
rb.DATA_DF = d2
BASE_NODOS, BASE_EDGES = dict(rb.NODOS), list(rb.EDGES)
TRANSP = ("Transporte_Publico", ("dist_ferro_km", ["Bueno", "Medio", "Malo"], "terciles"))  # menos km = mejor


def variante(nombre, nodos_extra, quitar_edges, poner_edges):
    nodos = dict(BASE_NODOS); nodos.update(nodos_extra)
    edges = [e for e in BASE_EDGES if e not in quitar_edges] + poner_edges
    return nombre, nodos, edges


V = [
    variante("S0 actual", {}, [], []),
    variante("S1 Viab ← Dinamismo, Transporte", dict([TRANSP]),
             [("Especializacion_Servicios", "Viabilidad_Empresarial")],
             [("Distancia_Madrid", "Transporte_Publico"), ("Transporte_Publico", "Viabilidad_Empresarial")]),
    variante("S2 Viab ← Especialización, Transporte", dict([TRANSP]),
             [("Dinamismo_Demografico", "Viabilidad_Empresarial")],
             [("Distancia_Madrid", "Transporte_Publico"), ("Transporte_Publico", "Viabilidad_Empresarial")]),
    variante("S3 Viab ← Dinamismo, Especialización, Transporte (3 padres)", dict([TRANSP]), [],
             [("Distancia_Madrid", "Transporte_Publico"), ("Transporte_Publico", "Viabilidad_Empresarial")]),
    variante("S4 Viab ← Dinamismo, Especialización, Acceso Ferroviario (3 padres, binario)", {},
             [], [("Acceso_Ferroviario", "Viabilidad_Empresarial")]),
]
# Al cambiar el nodo de Acceso por Transporte_Publico en S1-S3 se quita Acceso para no duplicar señal
for i in (1, 2, 3):
    n, nodos, edges = V[i]
    nodos.pop("Acceso_Ferroviario")
    V[i] = (n, nodos, [e for e in edges if "Acceso_Ferroviario" not in e])

res = []
for nombre, nodos, edges in V:
    # Las funciones viven en el paquete madrid179: se cambia la estructura allí (solo en este proceso)
    md.NODOS = mr.NODOS = nodos
    mr.EDGES = edges
    mr.EVIDENCIAS = [n for n in nodos if n != "Viabilidad_Empresarial"]
    disc, _ = rb.discretizar(d2)
    accs, lls = [], []
    for seed in range(5):  # 5 repeticiones de CV-5 para estabilizar
        a, ll, base = rb.validar(disc, "A", seed=seed)
        accs.append(a); lls.append(ll)
    n_padres = sum(1 for _, h in edges if h == "Viabilidad_Empresarial")
    res.append({"estructura": nombre, "padres_target": n_padres, "celdas_por_combinacion": round(179 / (3 ** (n_padres) if "binario" not in nombre else 18), 1),
                "accuracy": np.mean(accs), "accuracy_sd": np.std(accs), "logloss": np.mean(lls), "logloss_sd": np.std(lls)})
    print(f"{nombre:75s} acc={np.mean(accs):.3f}±{np.std(accs):.3f}  logloss={np.mean(lls):.4f}±{np.std(lls):.4f}")
print(f"(uniforme log-loss = {base:.4f}, azar acc = 0.333)")
pd.DataFrame(res).to_csv("data/processed/experimento_transporte.csv", sep=";", index=False, encoding="utf-8-sig")
