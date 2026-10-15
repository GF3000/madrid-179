"""Puntos de la pantalla de carga de la app: el centro de cada uno de los 179 municipios, proyectado al lienzo
de la bandera (300 x 200, proporción 3:2) para que la intro dibuje la silueta de la Comunidad sin esperar a la API.

Lee data/processed/municipios.geojson (propiedad `centro`, WGS84) y escribe frontend/app/src/puntos_carga.ts.
Proyección equirrectangular con corrección cos(latitud): a esta escala basta y no hace falta pyproj.
"""
import json
import math
from pathlib import Path

ORIGEN = Path("data/processed/municipios.geojson")
DESTINO = Path("frontend/app/src/puntos_carga.ts")
ANCHO, ALTO, MARGEN = 300, 200, 14


def main() -> None:
    fc = json.loads(ORIGEN.read_text(encoding="utf-8"))
    centros = sorted((f["properties"]["ine5"], *f["properties"]["centro"]) for f in fc["features"])
    assert len(centros) == 179, f"se esperaban 179 municipios y hay {len(centros)}"

    lat0 = sum(c[2] for c in centros) / len(centros)
    xs = [lon * math.cos(math.radians(lat0)) for _, lon, _ in centros]
    ys = [-lat for _, _, lat in centros]
    escala = min((ANCHO - 2 * MARGEN) / (max(xs) - min(xs)), (ALTO - 2 * MARGEN) / (max(ys) - min(ys)))
    dx = (ANCHO - escala * (max(xs) - min(xs))) / 2 - escala * min(xs)
    dy = (ALTO - escala * (max(ys) - min(ys))) / 2 - escala * min(ys)

    filas = [f'  ["{ine}", {escala * x + dx:.1f}, {escala * y + dy:.1f}],' for (ine, _, _), x, y in zip(centros, xs, ys)]
    DESTINO.write_text(
        "// Generado por backend/pipeline/puntos_carga.py: no editar a mano.\n"
        "// Centro de cada municipio en el lienzo de la bandera (300 x 200): [ine5, x, y].\n"
        "export const PUNTOS: [string, number, number][] = [\n" + "\n".join(filas) + "\n];\n",
        encoding="utf-8", newline="\n")
    print(f"{len(filas)} puntos -> {DESTINO}")


if __name__ == "__main__":
    main()
