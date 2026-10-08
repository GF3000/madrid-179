"""Construye la tabla municipal (179 filas, clave ine5) con las variables candidatas para la red bayesiana.
Salida: data/processed/dataset_bn_municipios.csv
Requiere el venv con pandas, pyshp, shapely, pyproj (ver docs/memoria/ESTADO.md).
"""
import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import shape
from pyproj import Transformer

MUN = "data/processed/municipal/"


def load(name):
    d = pd.read_csv(MUN + name + ".csv", sep=";", dtype=str, encoding="utf-8-sig")
    d.columns = [c.replace("�", "?") for c in d.columns]
    d = d.rename(columns={c: "Anio" for c in d.columns if c.startswith("A") and c.endswith("o") and len(c) == 3})
    if "Tipo territorio" in d.columns:  # evita que "Municipio de Madrid" (zona estadística) duplique 28079
        d = d[d["Tipo territorio"] == "Municipios"]
    d = d[d.ine5.notna()].copy()
    d["Valor"] = pd.to_numeric(d["Valor"], errors="coerce")
    return d


def last_year(d, **flt):
    for k, v in flt.items():
        d = d[d[k] == v]
    y = d["Anio"].max()
    return d[d["Anio"] == y].groupby("ine5")["Valor"].sum(), y


out = pd.read_csv("data/processed/maestro_municipios.csv", dtype=str, encoding="utf-8-sig").set_index("ine5")
log = {}

# --- Target: dinámica empresarial (unidades productivas), pooled 2020-2024 ---
de = load("din_emp")
de = de[de["Anio"].isin([str(y) for y in range(2020, 2025)])]
p = de.pivot_table(index="ine5", columns="Medida", values="Valor", aggfunc="sum")
up = lambda m: p["Unidades productivas " + m]
out["UP_inicio_sum"] = up("inicio periodo")
out["UP_nacen"] = up("nacen"); out["UP_mueren"] = up("mueren")
out["UP_entran"] = up("entran"); out["UP_salen"] = up("salen")
out["tasa_natalidad_emp"] = out.UP_nacen / out.UP_inicio_sum
out["tasa_mortalidad_emp"] = out.UP_mueren / out.UP_inicio_sum
out["tasa_neta_emp_bruta"] = (out.UP_nacen + out.UP_entran - out.UP_mueren - out.UP_salen) / out.UP_inicio_sum
# Contracción empírico-bayesiana hacia la media regional: municipios con pocas unidades-año
# (p.ej. Madarcos) tienen tasas muy ruidosas. k = mediana de UP_inicio_sum -> peso 50% para el municipio mediano.
net = out.UP_nacen + out.UP_entran - out.UP_mueren - out.UP_salen
r_bar = net.sum() / out.UP_inicio_sum.sum()
k = float(out.UP_inicio_sum.median())
out["tasa_neta_emp"] = (net + k * r_bar) / (out.UP_inicio_sum + k)
log["target"] = f"din_emp 2020-2024 pooled; r_bar={r_bar:.4f}; k={k:.0f}"

# --- Población y estructura ---
# El fichero trae Hombres, Mujeres y Total por municipio: usar solo Total (sumar las tres duplicaba la población).
pad = load("padron_por_sexo")
pad = pad[pad.Sexo == "Total"]
pob, y = last_year(pad); out["poblacion"] = pob; log["poblacion"] = y
p0 = pad[pad.Anio == str(int(y) - 5)].groupby("ine5").Valor.sum()
assert pad.groupby(["ine5", "Anio"]).size().max() == 1, "padrón con más de una fila por municipio y año"
out["crec_pob_5a"] = out.poblacion / p0 - 1
juv = load("grado_juventud_por_edad"); jy = juv.Anio.max()
out["pct_menores_45"] = juv[(juv.Anio == jy) & (juv.Edad.str.startswith("Menores de 45"))].set_index("ine5").Valor
log["juventud"] = jy

# --- Talento: % población 15+ con educación superior ---
es = load("poblacion_censada_por_estudios_y_sexo"); ey = es.Anio.max()
es = es[(es.Anio == ey) & (es.Sexo == "Total")]
sup = es[es.Estudios == "Educación superior"].set_index("ine5").Valor
tot = es[es.Estudios == "Total"].set_index("ine5").Valor
out["pct_estudios_superiores"] = sup / tot * 100; log["estudios"] = ey

# --- Renta disponible bruta per cápita ---
rd = load("irpf_indicador_renta")
out["rdb_per_capita"], log["renta"] = last_year(rd, Medida="Per cápita")

# --- Mercado laboral ---
out["paro_por_100hab"], log["paro"] = last_year(load("1902280"))
out["afiliados_por_1000hab"], log["afiliados"] = last_year(load("1905840"))

# --- Tejido empresarial (stock) ---
ce = load("col_emp_ramas")
up_tot, log["col_emp"] = last_year(ce, **{"Rama Actividad": "Total", "Medida": "Unidades productivas"})
out["up_por_1000hab"] = up_tot / out.poblacion * 1000
isp, _ = last_year(ce, **{"Rama Actividad": "Información y servicios profesionales", "Medida": "Unidades productivas"})
out["pct_up_servicios_prof"] = isp / up_tot * 100

# --- Coste inmobiliario: valor catastral medio por unidad urbana residencial (todos los municipios) ---
out["vc_residencial_por_uu"], log["vc"] = last_year(load("1002054"))
uu = load("unidades_urbanas_por_uso"); uy = uu.Anio.max()
uu = uu[(uu.Anio == uy) & (uu.Medida == "Unidades")]
out["uu_oficinas"] = uu[uu.Uso == "Oficinas"].groupby("ine5").Valor.sum()
out["uu_oficinas_por_1000hab"] = out.uu_oficinas / out.poblacion * 1000

# --- Transporte (GTFS CRTM) y amenidades (OSM) ---
g = pd.read_csv("data/processed/gtfs_paradas_por_municipio.csv", sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
out["superficie_km2"] = g.superficie_km2
out["paradas_total"] = g.paradas_total
out["paradas_ferro"] = g[["paradas_metro", "paradas_metroligero", "paradas_cercanias"]].sum(axis=1)
out["paradas_por_1000hab"] = out.paradas_total / out.poblacion * 1000
o = pd.read_csv("data/processed/osm_conteo_por_municipio.csv", sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
amen = [c for c in ["rest_restaurant", "rest_cafe", "rest_fastfood", "rest_bar", "gimnasios", "guarderias", "coworking"] if c in o.columns]
out["amenidades_osm"] = o[amen].sum(axis=1)
out["amenidades_por_1000hab"] = out.amenidades_osm / out.poblacion * 1000
out["coworking_osm"] = o.get("coworking", 0)
san = [c for c in o.columns if c.startswith("san_") and not c.endswith("_por_km2")]
out["sanidad_osm"] = o[san].sum(axis=1)  # hospitales, clínicas, consultas y farmacias
out["sanidad_por_1000hab"] = out.sanidad_osm / out.poblacion * 1000
out["deporte_osm"] = o.get("deporte", 0)  # polideportivos, pistas, piscinas, estadios
out["deporte_por_1000hab"] = out.deporte_osm / out.poblacion * 1000
log["amenidades_cols"] = ",".join(amen)

# --- Distancia euclídea del centroide municipal a la Puerta del Sol (km) ---
r = shapefile.Reader("data/raw/cam_geo/secciones_shp/Seccionado_2019.shp", encoding="latin-1")
acc = {}
for sr in r.shapeRecords():
    gg = shape(sr.shape.__geo_interface__)
    m = "28" + sr.record.as_dict()["CDMUNI"]
    a, cx, cy = acc.get(m, (0, 0, 0))
    acc[m] = (a + gg.area, cx + gg.centroid.x * gg.area, cy + gg.centroid.y * gg.area)
sx, sy = Transformer.from_crs(4326, 25830, always_xy=True).transform(-3.70358, 40.41695)
out["dist_sol_km"] = pd.Series({m: np.hypot(cx / a - sx, cy / a - sy) / 1000 for m, (a, cx, cy) in acc.items()})

out["densidad_hab_km2"] = out.poblacion / out.superficie_km2

# --- Distancia del centroide a la estación ferroviaria más cercana (Metro, Metro Ligero, Cercanías; km) ---
# Preferencia de transporte del usuario (PENDIENTES #38); no es nodo de la red.
st = pd.read_csv("data/processed/gtfs_paradas_con_seccion.csv", sep=";", dtype={"ine5": str}, encoding="utf-8-sig")
st = st[st.modo.isin(["metro", "metroligero", "cercanias"])]
fx, fy = Transformer.from_crs(4326, 25830, always_xy=True).transform(st.lon.to_numpy(), st.lat.to_numpy())
out["dist_ferro_km"] = pd.Series({m: np.min(np.hypot(fx - cx / a, fy - cy / a)) / 1000 for m, (a, cx, cy) in acc.items()})

# --- Nivel de ayudas por elegibilidad normativa (PENDIENTES #10) ---
# No entra en la red bayesiana: es capa informativa, filtro duro opcional o peso explícito (#12).
# Tramos de los planes de la CAM: Plan de Reequilibrio y Pueblos con Vida (< 20.000 hab.),
# rebaja fiscal por residencia (< 2.500 hab.). Listas oficiales pendientes de verificar (#11).
out["nivel_ayudas"] = pd.cut(out.poblacion, [-np.inf, 2500, 20000, np.inf], right=False,
                             labels=["Alto", "Medio", "Bajo"]).astype(str)
out["nivel_ayudas_num"] = out.nivel_ayudas.map({"Bajo": 0.0, "Medio": 0.5, "Alto": 1.0})
log["nivel_ayudas"] = out.nivel_ayudas.value_counts().to_dict()
out.index.name = "ine5"
out.to_csv("data/processed/dataset_bn_municipios.csv", sep=";", encoding="utf-8-sig")
print("filas", len(out), "| años usados:", log)
print(out.isna().sum()[out.isna().sum() > 0])
print(out.describe(percentiles=[.33, .5, .66]).T.round(3).to_string())
