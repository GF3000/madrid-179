"""Logo, imágenes para compartir e iconos de la app (frontend/app/public/).

- favicon.svg: el logo. La silueta de la Comunidad (unión de los 179 municipios) en blanco sobre un cuadrado
  carmesí, con un punto carmesí dentro: «de todo el territorio, este sitio» (ver silueta()).
- og.png (1200 × 630): vista previa al compartir el enlace (Open Graph / Twitter), con el logo, los 179 municipios
  dibujados desde data/processed/municipios.geojson y el punto del logo, con las fuentes y colores de la app.
- apple-touch-icon.png (180 × 180), icon-192.png e icon-512.png: el logo en PNG para móviles y el manifest.

Se dibuja en HTML/SVG y se fotografía con Chrome o Edge sin interfaz (el venv no lleva matplotlib ni Pillow).
Uso (desde la raíz): .venv/Scripts/python -I backend/pipeline/imagen_social.py
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from functools import cache
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform, unary_union

RAIZ = Path.cwd()
GEOJSON = RAIZ / "data" / "processed" / "municipios.geojson"
RANKING = RAIZ / "data" / "processed" / "bn_ranking_municipios.csv"  # red_bayesiana_viabilidad.py
PUBLIC = RAIZ / "frontend" / "app" / "public"
FUENTES = RAIZ / "frontend" / "app" / "node_modules" / "@fontsource-variable"
NAVEGADORES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "msedge",
]

# Colores de frontend/app/src/estilos.css
PAPEL, PAPEL_CLARO, TINTA, ROJO, ROJO_HONDO, ROJO_MEDIO, PIZARRA = (
    "#f6f2ec", "#fcfaf7", "#261c20", "#c8102e", "#8a0a1f", "#f3c9c4", "#56677a")
# Grupos del mapa (CLASES y FUERA en frontend/app/src/modelo.ts), de «Muy favorable» a «Poco favorable»
GRUPOS = ["#7a0018", "#c8102e", "#d2847c", "#e4c6bc", "#eae2da"]
FUERA = "#d2d6db"


def navegador():
    for n in NAVEGADORES:
        ruta = n if Path(n).exists() else shutil.which(n)
        if ruta:
            return ruta
    sys.exit("No encuentro Chrome ni Edge para hacer la captura")


def fotografiar(html, salida, ancho, alto):
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "pagina.html"
        pagina.write_text(html, encoding="utf-8")
        subprocess.run([navegador(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--allow-file-access-from-files", "--force-device-scale-factor=1",
                        f"--user-data-dir={Path(tmp) / 'perfil'}", "--virtual-time-budget=3000",
                        f"--window-size={ancho},{alto}", f"--screenshot={salida}", pagina.as_uri()],
                       check=True, capture_output=True)
    with open(salida, "rb") as f:  # cabecera PNG: ancho y alto en los bytes 16-24
        cab = f.read(24)
    dims = int.from_bytes(cab[16:20], "big"), int.from_bytes(cab[20:24], "big")
    if dims != (ancho, alto):
        sys.exit(f"{salida.name}: {dims[0]}×{dims[1]}, se esperaba {ancho}×{alto}")
    print(f"{salida.relative_to(RAIZ)}  {ancho}×{alto}  {salida.stat().st_size // 1024} KB")


def grupos():
    """Grupo de cada municipio en la clasificación por defecto (sin preferencias ni filtros), como en el mapa de la
    app (frontend/app/src/modelo.ts, clasificar): quintiles por posición entre candidatos; el resto, fuera."""
    filas = RANKING.read_text(encoding="utf-8-sig").splitlines()
    cab = filas[0].split(";")
    pos = {c[cab.index("ine5")]: int(c[cab.index("posicion")]) for c in (f.split(";") for f in filas[1:] if f)}
    n = len(pos)
    return {ine5: min(4, (p - 1) * 5 // n) for ine5, p in pos.items()}


def mapa_svg(ancho, alto):
    """Los 179 municipios (proyección equirrectangular corregida por la latitud media) con el color de su grupo."""
    feats = json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]
    grupo = grupos()
    k = math.cos(math.radians(40.5))
    anillos = []
    for f in feats:
        g = f["geometry"]
        polis = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        anillos.append((f["properties"]["ine5"], [anillo for p in polis for anillo in p]))
    xs = [lon * k for _, an in anillos for a in an for lon, _ in a]
    ys = [-lat for _, an in anillos for a in an for _, lat in a]
    x0, y0 = min(xs), min(ys)
    esc = min(ancho / (max(xs) - x0), alto / (max(ys) - y0))
    caminos = []
    for ine5, an in anillos:
        d = " ".join("M" + "L".join(f"{(lon * k - x0) * esc:.1f},{(-lat - y0) * esc:.1f}" for lon, lat in a) + "Z"
                     for a in an)
        color = GRUPOS[grupo[ine5]] if ine5 in grupo else FUERA
        caminos.append(f'<path d="{d}" fill="{color}"/>')
    w, h = (max(xs) - x0) * esc, (max(ys) - y0) * esc
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.1f} {h:.1f}">'
            f'<g stroke="{PAPEL}" stroke-width="1" stroke-linejoin="round">{"".join(caminos)}</g></svg>')


@cache
def silueta():
    """Contorno de la Comunidad (unión de los municipios, UTM 30N) y el punto del logo, que no es ningún municipio
    concreto ni Madrid capital: el más alejado del contorno (rejilla de 60 × 60) a más de 25 km de Madrid."""
    feats = json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]
    utm = Transformer.from_crs(4326, 25830, always_xy=True).transform
    union = unary_union([transform(utm, shape(f["geometry"])) for f in feats]).buffer(50).buffer(-50)
    if union.geom_type == "MultiPolygon":  # fragmentos sueltos de la unión: queda el territorio principal
        union = max(union.geoms, key=lambda g: g.area)
    madrid = transform(utm, Point(*next(f["properties"]["centro"] for f in feats
                                        if f["properties"]["ine5"] == "28079")))
    x0, y0, x1, y1 = union.bounds
    rejilla = (Point(x0 + (x1 - x0) * i / 59, y0 + (y1 - y0) * j / 59) for i in range(60) for j in range(60))
    punto = max((p for p in rejilla if union.contains(p) and p.distance(madrid) > 25_000),
                key=lambda p: p.distance(union.boundary))
    return union, punto


def logo_svg(esquina=22):
    """El logo en un lienzo de 100 × 100: silueta simplificada a ~1,5 km (se lee a 16 px) y el punto."""
    union, punto = silueta()
    x0, y0, x1, y1 = union.bounds
    lado, margen = 100, 11
    esc = (lado - 2 * margen) / max(x1 - x0, y1 - y0)
    ox = (lado - (x1 - x0) * esc) / 2
    oy = (lado - (y1 - y0) * esc) / 2
    xy = lambda x, y: f"{ox + (x - x0) * esc:.1f} {oy + (y1 - y) * esc:.1f}"
    d = "M" + "L".join(xy(x, y) for x, y in union.simplify(1500).exterior.coords) + "Z"
    cx, cy = xy(punto.x, punto.y).split()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado} {lado}">'
            f'<rect width="{lado}" height="{lado}" rx="{esquina}" fill="{ROJO}"/>'
            f'<path d="{d}" fill="#fff"/><circle cx="{cx}" cy="{cy}" r="5.5" fill="{ROJO}"/></svg>\n')


def fuente(familia, fichero):
    return (f"@font-face {{ font-family: '{familia}'; font-weight: 100 900; "
            f"src: url('{(FUENTES / fichero).as_uri()}') format('woff2'); }}")


def og():
    """Vista previa al compartir. Pensada para leerse también en miniatura (WhatsApp, iMessage): titular grande,
    poco texto pequeño y el mapa con la clasificación real por defecto."""
    logo = logo_svg()
    leyenda = "".join(f'<i style="background:{c}"></i>' for c in GRUPOS)
    return f"""<!doctype html><meta charset="utf-8"><style>
{fuente("Fraunces", "fraunces/files/fraunces-latin-wght-normal.woff2")}
{fuente("Hanken Grotesk", "hanken-grotesk/files/hanken-grotesk-latin-wght-normal.woff2")}
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; background: {PAPEL}; color: {TINTA}; }}
body {{ display: grid; grid-template-columns: 650px 1fr; align-items: center; font-family: 'Hanken Grotesk', sans-serif; }}
.texto {{ padding: 0 0 0 64px; }}
.marca {{ display: flex; align-items: center; gap: 14px; font-size: 22px; font-weight: 600; color: {ROJO_HONDO};
  letter-spacing: .02em; }}
.marca svg {{ width: 44px; height: 44px; }}
h1 {{ font-family: 'Fraunces', serif; font-weight: 600; font-size: 112px; line-height: 1; margin: 26px 0 20px;
  white-space: nowrap; letter-spacing: -.02em; }}
p {{ font-size: 34px; line-height: 1.25; margin: 0; max-width: 540px; }}
.cifras {{ display: flex; gap: 38px; margin-top: 38px; }}
.cifras div {{ font-size: 20px; line-height: 1.2; color: {PIZARRA}; }}
.cifras b {{ display: block; font-family: 'Fraunces', serif; font-weight: 600; font-size: 46px; line-height: 1.05;
  color: {ROJO}; }}
.pie {{ margin-top: 34px; font-size: 21px; color: {PIZARRA}; }}
.mapa {{ display: flex; flex-direction: column; align-items: center; gap: 14px; }}
.leyenda {{ display: flex; align-items: center; gap: 8px; font-size: 17px; color: {PIZARRA}; }}
.leyenda span {{ display: flex; }}
.leyenda i {{ width: 24px; height: 13px; }}
.leyenda .fuera {{ margin-left: 14px; }}
.leyenda .fuera i {{ width: 18px; }}
</style>
<div class="texto">
  <div class="marca">{logo} Localización de oficinas</div>
  <h1>Madrid 179</h1>
  <p>Encuentra dónde encaja tu oficina en la Comunidad de Madrid</p>
  <div class="cifras">
    <div><b>179</b>municipios</div>
    <div><b>15</b>criterios a tu<br>medida</div>
    <div><b>✓</b>cada resultado<br>explicado</div>
  </div>
  <div class="pie">madrid179.web.app</div>
</div>
<div class="mapa">{mapa_svg(500, 500)}
  <div class="leyenda">más favorable <span>{leyenda}</span> menos<span class="fuera"><i style="background:{FUERA}"></i></span> fuera</div>
</div>"""


def icono(lado):
    return (f'<!doctype html><style>html, body {{ margin: 0; background: {ROJO}; }} '
            f'svg {{ display: block; width: {lado}px; height: {lado}px; }}</style>{logo_svg(esquina=0)}')


if __name__ == "__main__":
    os.chdir(RAIZ)
    if not GEOJSON.exists():
        sys.exit("Falta municipios.geojson: ejecuta backend/pipeline/limites_municipales.py")
    if not FUENTES.exists():
        sys.exit("Faltan las fuentes de la app: npm install en frontend/app")
    (PUBLIC / "favicon.svg").write_text(logo_svg(), encoding="utf-8")
    print("frontend/app/public/favicon.svg")
    fotografiar(og(), PUBLIC / "og.png", 1200, 630)
    # Iconos a sangre (iOS y Android ya redondean las esquinas)
    for nombre, lado in [("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)]:
        fotografiar(icono(lado), PUBLIC / nombre, lado, lado)
