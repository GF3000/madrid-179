"""Exporta las variables municipales del dataset de la red bayesiana a JSON para el dashboard."""
import json
import pandas as pd

d = pd.read_csv("data/processed/dataset_bn_municipios.csv", sep=";", dtype={"ine5": str}, encoding="utf-8-sig").set_index("ine5")
um = json.load(open("data/processed/bn_umbrales.json", encoding="utf-8"))
nodo_por_col = {u["columna"]: (n, u["cortes"]) for n, u in um.items()}
# (columna, etiqueta, grupo, unidad, escala log sugerida)
VARS = [
    ("tasa_neta_emp", "Tasa neta empresarial (target)", "Empresa", "%/año", False),
    ("tasa_natalidad_emp", "Natalidad empresarial", "Empresa", "%/año", False),
    ("tasa_mortalidad_emp", "Mortalidad empresarial", "Empresa", "%/año", False),
    ("up_por_1000hab", "Unidades productivas / 1.000 hab", "Empresa", "ud", False),
    ("pct_up_servicios_prof", "% UP servicios profesionales", "Empresa", "%", False),
    ("poblacion", "Población", "Demografía", "hab", True),
    ("densidad_hab_km2", "Densidad", "Demografía", "hab/km²", True),
    ("crec_pob_5a", "Crecimiento población 5 años", "Demografía", "%", False),
    ("pct_menores_45", "% menores de 45 años", "Demografía", "%", False),
    ("pct_estudios_superiores", "% estudios superiores", "Talento y renta", "%", False),
    ("rdb_per_capita", "Renta disponible per cápita", "Talento y renta", "€", False),
    ("paro_por_100hab", "Paro / 100 hab", "Mercado laboral", "", False),
    ("afiliados_por_1000hab", "Afiliados / 1.000 hab", "Mercado laboral", "", True),
    ("vc_residencial_por_uu", "Valor catastral residencial", "Inmobiliario", "miles €", False),
    ("uu_oficinas_por_1000hab", "Inmuebles de oficinas / 1.000 hab", "Inmobiliario", "", True),
    ("dist_sol_km", "Distancia a Sol", "Accesibilidad", "km", False),
    ("paradas_por_1000hab", "Paradas TP / 1.000 hab", "Accesibilidad", "", True),
    ("paradas_ferro", "Estaciones ferroviarias", "Accesibilidad", "", False),
    ("amenidades_por_1000hab", "Amenidades OSM / 1.000 hab", "Servicios", "", True),
    ("sanidad_por_1000hab", "Sanidad OSM / 1.000 hab", "Servicios", "", True),
    ("deporte_por_1000hab", "Deporte OSM / 1.000 hab", "Servicios", "", True),
]
PCT = {"tasa_neta_emp", "tasa_natalidad_emp", "tasa_mortalidad_emp", "crec_pob_5a"}  # fracciones -> %
vars_ = []
for c, lab, g, u, lg in VARS:
    f = 100 if c in PCT else 1
    n = nodo_por_col.get(c)
    vars_.append({"key": c, "label": lab, "group": g, "unit": u, "log": lg,
                  "node": n[0] if n else None, "cuts": [x * f for x in n[1]] if n else []})
rows = [{"ine5": i, "name": r.nombre_iecm, **{c: round(float(r[c]) * (100 if c in PCT else 1), 4) for c, *_ in VARS}}
        for i, r in d.iterrows()]
json.dump({"vars": vars_, "rows": rows}, open("data/processed/dashboard_data.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(rows), "filas,", len(vars_), "variables")
