"""Logo, imágenes para compartir e iconos de la app (frontend/app/public/).

- favicon.svg: el logo. La silueta de la Comunidad (unión de los 179 municipios) en blanco sobre un cuadrado
  carmesí, con un punto carmesí dentro: «de todo el territorio, este sitio». El punto no es ningún municipio
  concreto ni Madrid capital: es el punto más alejado del contorno a más de 25 km del centro de Madrid.
- og.png (1200 × 630): vista previa al compartir el enlace (Open Graph / Twitter), con los 179 municipios
  dibujados desde data/processed/municipios.geojson y las fuentes y colores de la app.
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
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform, unary_union

RAIZ = Path.cwd()
GEOJSON = RAIZ / "data" / "processed" / "municipios.geojson"
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


def mapa_svg(ancho, alto):
    """Los 179 municipios en una proyección equirrectangular corregida por la latitud media."""
    feats = json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]
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
        relleno = ROJO if ine5 == "28079" else ROJO_MEDIO
        caminos.append(f'<path d="{d}" fill="{relleno}"/>')
    w, h = (max(xs) - x0) * esc, (max(ys) - y0) * esc
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.1f} {h:.1f}">'
            f'<g stroke="{PAPEL_CLARO}" stroke-width="1.1" stroke-linejoin="round">{"".join(caminos)}</g></svg>')


def logo_svg(esquina=22):
    """El logo en un lienzo de 100 × 100: silueta en UTM 30N simplificada a ~1,5 km (se lee a 16 px)."""
    feats = json.loads(GEOJSON.read_text(encoding="utf-8"))["features"]
    utm = Transformer.from_crs(4326, 25830, always_xy=True).transform
    union = unary_union([transform(utm, shape(f["geometry"])) for f in feats]).buffer(50).buffer(-50)
    if union.geom_type == "MultiPolygon":  # fragmentos sueltos de la unión: queda el territorio principal
        union = max(union.geoms, key=lambda g: g.area)
    madrid = transform(utm, Point(*next(f["properties"]["centro"] for f in feats
                                        if f["properties"]["ine5"] == "28079")))
    x0, y0, x1, y1 = union.bounds
    # Punto del logo: el más alejado del contorno (rejilla de 60 × 60) a más de 25 km de Madrid capital
    rejilla = (Point(x0 + (x1 - x0) * i / 59, y0 + (y1 - y0) * j / 59) for i in range(60) for j in range(60))
    punto = max((p for p in rejilla if union.contains(p) and p.distance(madrid) > 25_000),
                key=lambda p: p.distance(union.boundary))
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
    logo = logo_svg()
    return f"""<!doctype html><meta charset="utf-8"><style>
{fuente("Fraunces", "fraunces/files/fraunces-latin-wght-normal.woff2")}
{fuente("Hanken Grotesk", "hanken-grotesk/files/hanken-grotesk-latin-wght-normal.woff2")}
html, body {{ margin: 0; width: 1200px; height: 630px; overflow: hidden; background: {PAPEL}; color: {TINTA}; }}
body {{ display: grid; grid-template-columns: 640px 1fr; align-items: center; font-family: 'Hanken Grotesk', sans-serif; }}
.texto {{ padding: 0 0 0 64px; }}
.marca {{ display: flex; align-items: center; gap: 14px; font-size: 22px; font-weight: 600; color: {ROJO_HONDO};
  letter-spacing: .02em; }}
.marca svg {{ width: 44px; height: 44px; }}
h1 {{ font-family: 'Fraunces', serif; font-weight: 600; font-size: 100px; line-height: 1; margin: 34px 0 28px; white-space: nowrap;
  letter-spacing: -.02em; }}
p {{ font-size: 33px; line-height: 1.28; margin: 0; max-width: 500px; }}
.pie {{ margin-top: 34px; font-size: 21px; color: {PIZARRA}; }}
.mapa {{ display: flex; justify-content: center; }}
</style>
<div class="texto">
  <div class="marca">{logo} Datathon CAM · herramienta no oficial</div>
  <h1>Madrid 179</h1>
  <p>Dónde abrir una oficina en los 179 municipios de la Comunidad</p>
  <div class="pie">madrid179.web.app · datos públicos, modelo explicable</div>
</div>
<div class="mapa">{mapa_svg(520, 540)}</div>"""


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
