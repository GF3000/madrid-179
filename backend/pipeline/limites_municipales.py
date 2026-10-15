"""Límites municipales simplificados (GeoJSON) para el mapa de la app (PENDIENTES #23).

Disuelve las secciones censales de Seccionado_2019.shp por municipio, simplifica en UTM 30N (EPSG:25830)
y reproyecta a WGS84 para MapLibre/deck.gl.

Entrada:  data/raw/cam_geo/secciones_shp/Seccionado_2019.shp, data/processed/maestro_municipios.csv
Salida:   data/processed/municipios.geojson (179 polígonos; propiedades ine5, municipio, area_km2,
          centro [lon, lat] para etiquetas y cámara). Miembro extra «contorno»: límite exterior de la
          Comunidad, que la app usa para atenuar lo que queda fuera.

Uso: .venv/Scripts/python -I backend/pipeline/limites_municipales.py
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import shapefile
from pyproj import Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform, unary_union

SHP = Path("data/raw/cam_geo/secciones_shp/Seccionado_2019.shp")
MAESTRO = Path("data/processed/maestro_municipios.csv")
SALIDA = Path("data/processed/municipios.geojson")
TOLERANCIA_M = 60  # simplificación en metros: suficiente para la escala regional, ~10 veces menos vértices


def redondear(geom, d=5):
    """Redondea las coordenadas a 5 decimales (~1 m) para reducir el tamaño del fichero."""
    def r(coords):
        return [[round(x, d), round(y, d)] for x, y in coords]
    g = mapping(geom)
    if g["type"] == "Polygon":
        g["coordinates"] = [r(anillo) for anillo in g["coordinates"]]
    else:
        g["coordinates"] = [[r(anillo) for anillo in pol] for pol in g["coordinates"]]
    return g


def main():
    with MAESTRO.open(encoding="utf-8-sig") as f:
        nombres = {fila["ine5"]: fila["nombre_iecm"] for fila in csv.DictReader(f)}

    piezas = defaultdict(list)
    for sr in shapefile.Reader(str(SHP), encoding="latin-1").shapeRecords():
        piezas["28" + sr.record["CDMUNI"]].append(shape(sr.shape.__geo_interface__).buffer(0))

    a_wgs84 = Transformer.from_crs(25830, 4326, always_xy=True).transform
    rasgos, todos = [], []
    for ine5 in sorted(piezas):
        if ine5 not in nombres:
            raise SystemExit(f"Municipio sin nombre en el maestro: {ine5}")
        # buffer(+1/-1) cierra las rendijas de 1 m entre secciones vecinas antes de simplificar
        utm = unary_union(piezas[ine5]).buffer(1).buffer(-1)
        todos.append(utm)
        simple = utm.simplify(TOLERANCIA_M, preserve_topology=True)
        centro = transform(a_wgs84, utm.representative_point())
        rasgos.append({
            "type": "Feature",
            "properties": {"ine5": ine5, "municipio": nombres[ine5], "area_km2": round(utm.area / 1e6, 2),
                           "centro": [round(centro.x, 5), round(centro.y, 5)]},
            "geometry": redondear(transform(a_wgs84, simple)),
        })

    assert len(rasgos) == 179, f"Se esperaban 179 municipios y hay {len(rasgos)}"
    comunidad = unary_union(todos).buffer(5).buffer(-5).simplify(TOLERANCIA_M * 2, preserve_topology=True)
    contorno = {"type": "Feature", "properties": {"nombre": "Comunidad de Madrid"},
                "geometry": redondear(transform(a_wgs84, comunidad))}
    SALIDA.write_text(json.dumps({"type": "FeatureCollection", "features": rasgos, "contorno": contorno}, ensure_ascii=False,
                                 separators=(",", ":")), encoding="utf-8")
    print(f"{SALIDA}: {len(rasgos)} municipios, {SALIDA.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
