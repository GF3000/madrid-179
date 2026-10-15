"""Asistente LLM (PENDIENTES #29): traduce la descripción de un negocio en preferencias y filtros (interpretar) y
redacta lo mejor y lo peor de un municipio a partir de los hechos ya calculados de su ficha (explicar). También
inventa descripciones de negocio de ejemplo para probar la app (ejemplo).

El LLM (DeepSeek, API compatible con OpenAI) solo **traduce**: devuelve un JSON con preferencias del catálogo
(preferencias.CATALOGO), filtros «imprescindible», un resumen y dudas. No puntúa ni explica municipios: eso lo
hacen el GA²M y la red bayesiana. Todo lo que devuelve se valida y se sanea aquí (claves desconocidas,
importancias o sentidos no válidos y números fuera de rango se descartan y se informa de ello). La app lo aplica
al momento, muestra lo entendido y permite deshacerlo.

Clave en .env (DEEPSEEK_API_KEY); modelo y URL configurables con DEEPSEEK_MODELO y DEEPSEEK_URL.
"""
import json
import logging
import os
import random

import httpx

from . import limites
from .config import clave_api
from .preferencias import CATALOGO, POR_CLAVE

log = logging.getLogger(__name__)

URL = os.environ.get("DEEPSEEK_URL", "https://api.deepseek.com/chat/completions")
MODELO = os.environ.get("DEEPSEEK_MODELO", "deepseek-chat")
TIEMPO_MAX_S = 45
LIMITE = limites.Limitador.desde_entorno()  # protege el saldo del LLM en la URL pública
IMPORTANCIAS_LLM = ("Poco importante", "Muy importante")

# Filtros «imprescindible» que puede proponer el LLM: nombre -> (tipo, mínimo, máximo, descripción)
FILTROS_LLM = {
    "estacion_max_km": (float, 0.5, 30, "estación de tren a como mucho X km"),
    "madrid_max_km": (float, 5, 80, "como mucho a X km de Madrid (Puerta del Sol)"),
    "madrid_min_km": (float, 5, 80, "al menos a X km de Madrid"),
    "poblacion_min": (int, 100, 250_000, "al menos X habitantes"),
    "poblacion_max": (int, 100, 250_000, "como mucho X habitantes"),
    "solo_con_ayudas": (bool, None, None, "solo municipios donde haya ayudas al reequilibrio por tamaño"),
    "con_coworking": (bool, None, None, "solo municipios con coworking"),
}


class AsistenteNoDisponible(RuntimeError):
    """Falta la clave de la API."""


class ErrorAsistente(RuntimeError):
    """El LLM no respondió o respondió algo inutilizable."""


def disponible():
    return bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())


def instrucciones():
    prefs = "\n".join(
        f'- "{p.clave}": {p.nombre}. {p.descripcion}'
        + (f' Sentido obligatorio: {" o ".join(repr(v) for v, _ in p.sentidos)}.' if p.sentidos else "")
        for p in CATALOGO)
    filtros = "\n".join(f'- "{k}" ({t.__name__}): {d}' for k, (t, _, _, d) in FILTROS_LLM.items())
    return f"""Eres el asistente de Madrid 179, una herramienta que recomienda en qué municipios de la Comunidad de
Madrid abrir o trasladar una oficina. Tu única tarea es traducir la descripción que hace el usuario de su negocio
en preferencias y requisitos que la herramienta entiende. No recomiendes municipios ni des cifras.

Preferencias disponibles (usa exactamente estas claves):
{prefs}

Importancias: "Poco importante" o "Muy importante". Incluye solo las preferencias que el usuario menciona o que
se deducen con claridad de su actividad; si la deduces del sector, dilo en el motivo ("deducido de tu actividad").
No incluyas las que le dan igual. Usa "Muy importante" solo si lo dice con énfasis o es esencial para el negocio.

Requisitos imprescindibles (filtros duros, descartan municipios). Ponlos solo si el usuario los expresa como
obligatorios o da una cifra concreta; nunca te inventes números:
{filtros}

Si algo relevante no queda claro (por ejemplo, si necesita tren o si prefiere ciudad o pueblo), no lo
supongas: añade una pregunta corta en "dudas" (como mucho 3).

Responde solo con un objeto JSON, en español, con esta forma:
{{"resumen": "una o dos frases en segunda persona sobre lo que has entendido",
  "sector": "actividad del negocio en pocas palabras o null",
  "preferencias": {{"<clave>": {{"importancia": "Poco importante|Muy importante", "sentido": "<valor o null>",
                    "motivo": "por qué, en pocas palabras"}}}},
  "filtros": {{"<nombre>": <valor>}},
  "dudas": ["pregunta corta"]}}"""


def _llamar(texto, sistema=None, temperatura=0.2):
    """Llama al LLM y devuelve el contenido (texto JSON) de la respuesta."""
    try:
        clave = clave_api("DEEPSEEK_API_KEY")
    except RuntimeError as e:
        raise AsistenteNoDisponible(str(e)) from None
    cuerpo = {"model": MODELO, "temperature": temperatura, "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": sistema or instrucciones()},
                           {"role": "user", "content": texto}]}
    try:
        r = httpx.post(URL, json=cuerpo, headers={"Authorization": f"Bearer {clave}"}, timeout=TIEMPO_MAX_S)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise ErrorAsistente(f"El servicio del asistente respondió {e.response.status_code}") from None
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
        raise ErrorAsistente(f"No se pudo consultar al asistente ({type(e).__name__})") from None


def sanear(bruto):
    """Valida la respuesta del LLM contra el catálogo. Devuelve (resultado limpio, avisos de lo descartado)."""
    avisos = []
    if not isinstance(bruto, dict):
        raise ErrorAsistente("La respuesta del asistente no es un objeto JSON")

    prefs = {}
    for k, v in (bruto.get("preferencias") or {}).items():
        p = POR_CLAVE.get(k)
        if p is None or not isinstance(v, dict):
            avisos.append(f"Preferencia desconocida descartada: {k}")
            continue
        imp = v.get("importancia")
        if imp not in IMPORTANCIAS_LLM:
            avisos.append(f"Importancia no válida en {k}: {imp}")
            continue
        validos = [s for s, _ in p.sentidos]
        sentido = v.get("sentido") if validos else None
        if validos and sentido not in validos:
            avisos.append(f"Sin sentido válido en {k}: se pregunta al usuario")
            continue
        prefs[k] = {"importancia": imp, "sentido": sentido, "motivo": str(v.get("motivo") or "")[:200]}

    filtros = {}
    for k, v in (bruto.get("filtros") or {}).items():
        if k not in FILTROS_LLM or v is None:
            if k not in FILTROS_LLM:
                avisos.append(f"Requisito desconocido descartado: {k}")
            continue
        tipo, lo, hi, _ = FILTROS_LLM[k]
        if tipo is bool:
            if v is True:
                filtros[k] = True
            continue
        try:
            x = tipo(v)
        except (TypeError, ValueError):
            avisos.append(f"Valor no numérico en {k}: {v}")
            continue
        if not lo <= x <= hi:
            avisos.append(f"Valor fuera de rango en {k}: {v}")
            continue
        filtros[k] = x
    if "poblacion_min" in filtros and "poblacion_max" in filtros and filtros["poblacion_min"] > filtros["poblacion_max"]:
        avisos.append("Rango de población contradictorio: descartado")
        filtros.pop("poblacion_min"), filtros.pop("poblacion_max")

    dudas = [str(d)[:200] for d in (bruto.get("dudas") or []) if isinstance(d, str) and d.strip()][:3]
    sector = bruto.get("sector")
    return {"resumen": str(bruto.get("resumen") or "")[:600], "sector": str(sector)[:80] if sector else None,
            "preferencias": prefs, "filtros": filtros, "dudas": dudas}, avisos


def interpretar(texto, cliente=None):
    LIMITE.consumir(cliente)
    contenido = _llamar(texto)
    try:
        bruto = json.loads(contenido)
    except (TypeError, ValueError):
        raise ErrorAsistente("El asistente no devolvió JSON válido") from None
    limpio, avisos = sanear(bruto)
    if avisos:
        log.info("Asistente: %s", "; ".join(avisos))
    return {**limpio, "avisos": avisos}


# ------------------------------------------------------------------ explicación de un municipio
INSTRUCCIONES_EXPLICAR = """Eres el asistente de Madrid 179, una herramienta que compara los 179 municipios de la Comunidad de
Madrid para abrir una oficina. Recibes en JSON los hechos que la herramienta ya ha calculado sobre un municipio: su
grupo, los factores que le favorecen y le restan (con su fuerza: mucho, bastante, algo), su perfil comparado con el
resto de municipios, la lectura de la red de causas y, si las hay, las preferencias del usuario.

Escribe en español claro, para alguien que no sabe de estadística:
- "titular": una frase que resuma el municipio como sitio para una oficina.
- "mejor": de 2 a 3 frases cortas con lo mejor del municipio.
- "peor": de 1 a 3 frases cortas con lo peor o lo que conviene vigilar.

Reglas estrictas:
- Usa solo los hechos que recibes. No añadas datos, cifras, empresas, lugares ni historia que no estén en el JSON.
  El resumen de Wikipedia solo sirve para situar el municipio (comarca, carácter), nunca como argumento económico.
- No inventes porcentajes ni puntuaciones. Puedes citar los datos reales que vienen escritos (habitantes, km).
- Son asociaciones observadas en los datos de 2020 a 2024, no causas: no digas que algo "provoca" o "garantiza".
- Si un factor parece contraintuitivo (por ejemplo, paro bajo que resta), explícalo con prudencia o no lo destaques.
- Si el municipio está fuera del análisis, explica por qué con el motivo que recibes y no lo valores.
- Si hay preferencias del usuario, menciona cómo encaja con ellas.

Responde solo con un objeto JSON: {"titular": "...", "mejor": ["..."], "peor": ["..."]}"""

_CACHE_EXPLICAR = {}


def explicar(hechos, cliente=None):
    """Redacta lo mejor y lo peor del municipio a partir de los hechos de la ficha (con caché en memoria).
    Solo las llamadas que no están en caché cuentan para el límite."""
    clave = json.dumps(hechos, sort_keys=True, ensure_ascii=False)
    if clave in _CACHE_EXPLICAR:
        return _CACHE_EXPLICAR[clave]
    LIMITE.consumir(cliente)
    contenido = _llamar(json.dumps(hechos, ensure_ascii=False), INSTRUCCIONES_EXPLICAR, temperatura=0.4)
    try:
        bruto = json.loads(contenido)
    except (TypeError, ValueError):
        raise ErrorAsistente("El asistente no devolvió JSON válido") from None
    if not isinstance(bruto, dict):
        raise ErrorAsistente("La respuesta del asistente no es un objeto JSON")

    def frases(x, n):
        return [str(f).strip()[:300] for f in (x or []) if isinstance(f, str) and f.strip()][:n]

    salida = {"titular": str(bruto.get("titular") or "").strip()[:300],
              "mejor": frases(bruto.get("mejor"), 3), "peor": frases(bruto.get("peor"), 3)}
    if not salida["titular"] and not salida["mejor"]:
        raise ErrorAsistente("El asistente devolvió una explicación vacía")
    if len(_CACHE_EXPLICAR) > 500:
        _CACHE_EXPLICAR.clear()
    _CACHE_EXPLICAR[clave] = salida
    return salida


# ------------------------------------------------------------------ ejemplo de negocio para probar la app
# El sorteo se hace aquí y no en el LLM, que con la misma petición tiende a repetir el mismo negocio.
SECTORES_EJEMPLO = (
    "consultora de ingeniería", "estudio de arquitectura", "agencia de marketing digital", "gestoría y asesoría fiscal",
    "empresa de desarrollo de software", "despacho de abogados", "centro de atención telefónica",
    "empresa de logística ligera y reparto", "laboratorio de análisis de alimentos", "academia de formación",
    "productora audiovisual", "startup de energía solar", "inmobiliaria", "agencia de viajes rurales",
    "clínica de fisioterapia con oficina administrativa", "empresa de ciberseguridad", "editorial pequeña",
    "cooperativa agroalimentaria (oficina comercial)", "estudio de videojuegos", "empresa de traducción",
)
PLANTILLAS_EJEMPLO = ("2 o 3 personas", "unas 8 personas", "15 a 20 personas", "unas 40 personas", "más de 100 personas")
NECESIDADES_EJEMPLO = (
    "que la plantilla pueda llegar en tren", "buen transporte público", "estar cerca de Madrid",
    "alejarse de Madrid para ganar calidad de vida", "un alquiler barato", "aprovechar ayudas para pueblos pequeños",
    "contratar personal muy cualificado", "contratar mano de obra sin necesidad de titulación", "un municipio joven",
    "una ciudad grande", "un pueblo pequeño y tranquilo", "clientes con poder adquisitivo",
    "proveedores y servicios profesionales cerca", "un municipio en crecimiento", "otras oficinas alrededor",
    "un coworking para empezar", "restaurantes, guarderías y servicios para el equipo",
)
INSTRUCCIONES_EJEMPLO = """Escribes ejemplos para probar Madrid 179, una herramienta que recomienda en qué municipio de la
Comunidad de Madrid abrir una oficina. Recibes un sector, un tamaño de plantilla y unas necesidades. Inventa un negocio
verosímil y escribe cómo se lo describiría su responsable a la herramienta: en primera persona del plural, en español
coloquial, de 2 a 4 frases y menos de 450 caracteres. Di a qué os dedicáis, cuántos sois y qué necesitáis, con tus
palabras (no copies las necesidades al pie de la letra). No nombres municipios concretos ni marcas reales.

Responde solo con un objeto JSON: {"texto": "...", "sector": "actividad en pocas palabras"}"""


def ejemplo(cliente=None, azar=None):
    """Inventa la descripción de un negocio para probar el asistente. Sector, plantilla y necesidades se sortean
    aquí; el LLM solo los redacta. No puntúa ni toca el ranking: el texto pasa luego por interpretar()."""
    azar = azar or random.Random()
    semilla = {"sector": azar.choice(SECTORES_EJEMPLO), "plantilla": azar.choice(PLANTILLAS_EJEMPLO),
               "necesidades": azar.sample(NECESIDADES_EJEMPLO, azar.randint(2, 3))}
    LIMITE.consumir(cliente)
    contenido = _llamar(json.dumps(semilla, ensure_ascii=False), INSTRUCCIONES_EJEMPLO, temperatura=1.0)
    try:
        bruto = json.loads(contenido)
    except (TypeError, ValueError):
        raise ErrorAsistente("El asistente no devolvió JSON válido") from None
    texto = str(bruto.get("texto") or "").strip() if isinstance(bruto, dict) else ""
    if len(texto) < 10:
        raise ErrorAsistente("El asistente devolvió un ejemplo vacío")
    sector = bruto.get("sector")
    return {"texto": texto[:2000], "sector": str(sector)[:80] if sector else semilla["sector"]}
