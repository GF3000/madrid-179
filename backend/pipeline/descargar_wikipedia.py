"""Imagen y resumen de cada municipio desde Wikidata, Wikipedia y Wikimedia Commons (ficha de la app).

1. Wikidata (SPARQL): municipio por su código INE de 5 dígitos (P772), foto representativa (P18) y artículo
   de la Wikipedia en español. Se enlaza por código, no por nombre: evita confundir Horcajo y Horcajuelo de la
   Sierra o los nombres con artículo pospuesto («Molinos (Los)»).
2. Wikipedia (API REST, /page/summary): primer párrafo del artículo.
3. Commons (imageinfo + extmetadata): miniatura de 800 px, autor y licencia de la foto, que hay que citar.

Salida: data/processed/wikipedia_municipios.json  {ine5: {titulo, resumen, url, imagen: {url, autor, licencia,
        url_licencia, fuente}}}. Textos de Wikipedia: CC BY-SA 4.0. Fotos: la licencia de cada una (Commons).
Uso: .venv/Scripts/python -I backend/pipeline/descargar_wikipedia.py
"""
import csv
import html
import json
import re
import time
from pathlib import Path
from urllib.parse import quote, unquote

import httpx

MAESTRO = Path("data/processed/maestro_municipios.csv")
SALIDA = Path("data/processed/wikipedia_municipios.json")
# Política de Wikimedia: el User-Agent debe identificar el proyecto con una URL de contacto
CABECERAS = {"User-Agent": "Madrid179-datathon/1.0 (https://github.com/GF3000/madrid-179)"}
SPARQL = """SELECT ?ine ?img ?art WHERE {
  ?item wdt:P772 ?ine . FILTER(STRLEN(?ine) = 5 && STRSTARTS(?ine, "28"))
  OPTIONAL { ?item wdt:P18 ?img }
  OPTIONAL { ?art schema:about ?item ; schema:isPartOf <https://es.wikipedia.org/> }
}"""
ANCHO = 800


def limpiar(texto):
    """Quita etiquetas HTML de los metadatos de Commons (el autor suele venir como enlace)."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", texto or ""))).strip()


def recortar(texto, maximo=700):
    """Recorta el resumen en un final de frase."""
    if len(texto) <= maximo:
        return texto
    corte = texto[:maximo].rsplit(". ", 1)[0]
    return corte + "."


def main():
    with MAESTRO.open(encoding="utf-8-sig") as f:
        nombres = {r["ine5"]: r["nombre_iecm"] for r in csv.DictReader(f)}
    cliente = httpx.Client(headers=CABECERAS, timeout=60, follow_redirects=True)

    filas = cliente.get("https://query.wikidata.org/sparql", params={"query": SPARQL, "format": "json"}).json()
    datos = {}
    for b in sorted(filas["results"]["bindings"], key=lambda b: b.get("img", {}).get("value", "")):
        ine5 = b["ine"]["value"]
        if ine5 not in nombres:
            continue
        d = datos.setdefault(ine5, {"img": None, "art": None})
        d["img"] = d["img"] or (b.get("img") or {}).get("value")
        d["art"] = d["art"] or (b.get("art") or {}).get("value")
    faltan = sorted(set(nombres) - set(datos))
    print(f"Wikidata: {len(datos)} de {len(nombres)} municipios" + (f" · sin entrada: {faltan}" if faltan else ""))

    salida = {}
    for i, (ine5, d) in enumerate(sorted(datos.items()), 1):
        ficha = {"titulo": None, "resumen": None, "url": None, "imagen": None}
        if d["art"]:
            titulo = unquote(d["art"].rsplit("/", 1)[1])
            r = cliente.get(f"https://es.wikipedia.org/api/rest_v1/page/summary/{quote(titulo, safe='')}")
            if r.status_code == 200:
                s = r.json()
                ficha.update(titulo=s.get("title"), resumen=recortar(s.get("extract", "")),
                             url=s.get("content_urls", {}).get("desktop", {}).get("page"))
        if d["img"]:
            fichero = unquote(d["img"].rsplit("/", 1)[1])
            r = cliente.get("https://commons.wikimedia.org/w/api.php", params={
                "action": "query", "titles": f"File:{fichero}", "prop": "imageinfo", "format": "json",
                "iiprop": "url|extmetadata", "iiurlwidth": ANCHO})
            paginas = r.json().get("query", {}).get("pages", {})
            info = next(iter(paginas.values()), {}).get("imageinfo", [{}])[0]
            meta = info.get("extmetadata", {})
            if info.get("thumburl"):
                ficha["imagen"] = {
                    "url": info["thumburl"].split("?")[0],  # sin parámetros de seguimiento (utm_*)
                    "autor": limpiar(meta.get("Artist", {}).get("value")) or "Autor desconocido",
                    "licencia": limpiar(meta.get("LicenseShortName", {}).get("value")) or None,
                    "url_licencia": meta.get("LicenseUrl", {}).get("value"),
                    "fuente": info.get("descriptionurl"),
                }
        salida[ine5] = ficha
        if i % 20 == 0:
            print(f"  {i}/{len(datos)}")
        time.sleep(0.15)  # cortesía con las API de Wikimedia

    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    con_img = sum(1 for v in salida.values() if v["imagen"])
    con_txt = sum(1 for v in salida.values() if v["resumen"])
    print(f"{SALIDA}: {len(salida)} municipios · {con_txt} con resumen · {con_img} con foto · "
          f"{SALIDA.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
