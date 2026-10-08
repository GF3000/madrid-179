"""Genera docs/informe/Aproximacion_tecnica_CAM.pdf: descripción breve de la aproximación técnica propuesta.
Mismo estilo que generar_pdf_fuentes.py. Requiere reportlab y docs/informe/red_bayesiana.png (diagrama_red_bayesiana.py).
"""
import struct

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

pdfmetrics.registerFont(TTFont("Segoe", "C:/Windows/Fonts/segoeui.ttf"))
pdfmetrics.registerFont(TTFont("SegoeB", "C:/Windows/Fonts/segoeuib.ttf"))
pdfmetrics.registerFont(TTFont("Mono", "C:/Windows/Fonts/consola.ttf"))
pdfmetrics.registerFontFamily("Segoe", normal="Segoe", bold="SegoeB")

INK, INK2, MUTED, RULE = colors.HexColor("#0b0b0b"), colors.HexColor("#52514e"), colors.HexColor("#898781"), colors.HexColor("#d9d8d0")
BLUE_BG, GREY_BG = colors.HexColor("#e6effb"), colors.HexColor("#f4f3ef")

st = {
    "eyebrow": ParagraphStyle("eyebrow", fontName="Segoe", fontSize=8.5, textColor=MUTED, leading=11, spaceAfter=2),
    "title": ParagraphStyle("title", fontName="SegoeB", fontSize=19, leading=23, textColor=INK, spaceAfter=9),
    "lede": ParagraphStyle("lede", fontName="Segoe", fontSize=10, leading=14.5, textColor=INK2, spaceAfter=4),
    "h2": ParagraphStyle("h2", fontName="SegoeB", fontSize=12.5, leading=16, textColor=INK, spaceBefore=11, spaceAfter=5, keepWithNext=1),
    "body": ParagraphStyle("body", fontName="Segoe", fontSize=9.4, leading=13.4, textColor=INK, spaceAfter=4),
    "cell": ParagraphStyle("cell", fontName="Segoe", fontSize=8.4, leading=11, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="SegoeB", fontSize=8.6, leading=11, textColor=INK),
    "head": ParagraphStyle("head", fontName="SegoeB", fontSize=7.8, leading=10, textColor=INK2),
    "note": ParagraphStyle("note", fontName="Segoe", fontSize=8, leading=11, textColor=MUTED),
    "formula": ParagraphStyle("formula", fontName="Mono", fontSize=9.2, leading=13, textColor=INK, leftIndent=8),
    "bullet": ParagraphStyle("bullet", fontName="Segoe", fontSize=9.3, leading=13.2, textColor=INK, leftIndent=10, bulletIndent=0, spaceAfter=1.5),
}
P = lambda t, s="cell": Paragraph(t, st[s])
B = lambda items: [Paragraph(t, st["bullet"], bulletText="•") for t in items]


def tabla(filas, cab, anchos, mono_col=None):
    data = [[P(c, "head") for c in cab]]
    for f in filas:
        data.append([P(f[0], "cellb")] + [P(f"<font face='Mono' size='7.8'>{x}</font>" if i == mono_col else x)
                                          for i, x in enumerate(f[1:], start=1)])
    t = Table(data, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK2), ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def caja(contenido, bg=GREY_BG):
    t = Table([[contenido]], colWidths=[W])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LEFTPADDING", (0, 0), (-1, -1), 9),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 7),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Segoe", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 10 * mm, "Datathon CAM · Aproximación técnica · octubre 2026")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate("docs/informe/Aproximacion_tecnica_CAM.pdf", pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=16 * mm, bottomMargin=17 * mm, title="Aproximación técnica · Localización de oficinas CAM",
                        author="Gregorio García Velasco; Guillermo Franco Gimeno", subject="Descripción de la aproximación técnica propuesta")
W = A4[0] - 36 * mm

ARQ = [
    ("Aplicación de escritorio", "React y TypeScript empaquetados con Tauri o Electron",
     "Una sola base de código para la interfaz; instalable y sin dependencia de navegador"),
    ("Mapa 3D", "MapLibre con Deck.gl / React Three Fiber (WebGL, WebGPU)",
     "Los 179 municipios extruidos según su puntuación, animados a 60 fps"),
    ("Motores de modelo", "Python, FastAPI, pgmpy (red bayesiana) e InterpretML (GA²M)",
     "Ambos modelos se cargan en memoria; puntuar los 179 municipios lleva milisegundos"),
    ("Datos", "Ficheros Parquet y GeoJSON simplificado de límites municipales",
     "179 filas y datos anuales: no hace falta un gestor de base de datos"),
    ("Asistente conversacional", "LLM con salidas estructuradas (esquema JSON)",
     "Convierte la descripción libre del negocio en filtros, evidencias y preguntas pendientes"),
    ("Despliegue", "Contenedor serverless (Cloud Run, App Runner) o instancia ligera con Nginx",
     "Coste mínimo en reposo; el frontend se sirve como estáticos"),
]

NODOS = [
    ("Distancia Madrid", "Distancia del centroide a la Puerta del Sol (km)", "Raíz", "31,8 / 45,2 km"),
    ("Talento", "% de población de 15 y más años con estudios superiores", "Raíz", "30,6 / 39,5 %"),
    ("Acceso Ferroviario", "Estaciones de Metro, Metro Ligero o Cercanías (GTFS CRTM)", "Distancia", "0 / más de 0"),
    ("Coste Inmobiliario", "Valor catastral residencial por unidad urbana (miles €)", "Distancia, Talento", "69,8 / 95,7"),
    ("Renta", "Renta disponible bruta per cápita (€)", "Talento", "17.065 / 19.992"),
    ("Especialización Servicios", "% de unidades productivas en información y servicios profesionales", "Distancia, Talento", "12,7 / 18,3 %"),
    ("Dinamismo Demográfico", "Crecimiento de la población en 5 años (padrón)", "Distancia, Coste", "6,8 / 12,9 %"),
    ("Viabilidad Empresarial", "Tasa neta anual de unidades productivas 2020-2024 (objetivo)", "Dinamismo, Especialización", "0,60 / 0,98 %"),
]

st["h3"] = ParagraphStyle("h3", fontName="SegoeB", fontSize=10.5, leading=14, textColor=INK, spaceBefore=8, spaceAfter=3, keepWithNext=1)


def img_alto(ruta, alto_max, ancho_max):
    """PNG escalado para caber en la página respetando su proporción."""
    w, h = struct.unpack(">II", open(ruta, "rb").read(24)[16:24])
    k = min(alto_max / h, ancho_max / w)
    return Image(ruta, width=w * k, height=h * k)


def img_png(ruta, ancho):
    w, h = struct.unpack(">II", open(ruta, "rb").read(24)[16:24])
    return Image(ruta, width=ancho, height=ancho * h / w)


ORIGEN = [
    ("Viabilidad Empresarial (objetivo)", "Tasa neta de unidades productivas: (nacen + entran − mueren − salen) / activas",
     "Dinámica Empresarial · Dirección General de Economía e Industria (CAM)", "IECM · <i>din_emp</i>", "2020-24"),
    ("Dinamismo Demográfico", "Crecimiento de la población empadronada en 5 años",
     "Padrón municipal · INE", "IECM · <i>padron_por_sexo</i>", "2020-25"),
    ("Talento", "% de población de 15 y más años con estudios superiores",
     "Censo de Población anual · INE", "IECM · <i>poblacion_censada_por_estudios_y_sexo</i>", "2024"),
    ("Renta", "Renta disponible bruta per cápita",
     "Indicador de Renta Disponible Bruta Municipal · INE", "IECM · <i>irpf_indicador_renta</i>", "2023"),
    ("Especialización Servicios", "% de unidades productivas en información y servicios profesionales",
     "Colectivo Empresarial · Dirección General de Economía e Industria (CAM)", "IECM · <i>col_emp_ramas</i>", "2025"),
    ("Coste Inmobiliario", "Valor catastral residencial medio por unidad urbana",
     "Catastro Inmobiliario · Dirección General del Catastro", "IECM · <i>1002054</i>", "2026"),
    ("Distancia Madrid", "Km del centroide municipal a la Puerta del Sol",
     "Cálculo propio sobre el seccionado censal", "Comunidad de Madrid · <i>secciones_censales</i>", "2019"),
    ("Acceso Ferroviario · distancia a estación", "Estaciones de Metro, Metro Ligero y Cercanías",
     "Consorcio Regional de Transportes de Madrid (GTFS)", "Portal de datos abiertos del CRTM", "2026"),
    ("Filtro: oferta de oficinas", "Unidades urbanas de uso oficinas",
     "Catastro Inmobiliario · Dirección General del Catastro", "IECM · <i>unidades_urbanas_por_uso</i>", "2026"),
    ("Nivel de ayudas", "Tramo de población: ≥ 20.000 / 2.500-20.000 / < 2.500 hab.",
     "Padrón (INE) y tramos del Plan de Reequilibrio Territorial y de la rebaja fiscal por residencia (CAM)",
     "Regla propia; listas oficiales en verificación", "2025"),
    ("Convocatorias de ayudas", "Convocatorias y concesiones con ámbito Madrid",
     "Base de Datos Nacional de Subvenciones · IGAE, Ministerio de Hacienda", "API de infosubvenciones.es", "2014-26"),
    ("Servicios para trabajadores", "Restauración, gimnasios, guarderías, coworking, sanidad, deporte",
     "OpenStreetMap (licencia ODbL)", "Overpass API", "2026"),
]

PREGUNTAS = [
    ("¿Qué municipios tienen más potencial para atraer oficinas?", "Mapa base: puntuación del GA²M sin preferencias, filtrable por ámbito", "Disponible"),
    ("¿Qué frena a un municipio concreto?", "Ficha diagnóstica: contribución de cada factor (GA²M) y cadena causal (red bayesiana)", "Disponible"),
    ("¿Las ayudas llegan donde hay potencial?", "Cruce del nivel de ayudas con la puntuación: municipios elegibles con buena puntuación frente a elegibles sin ella", "Disponible"),
    ("¿Cuánto reequilibrio produce una recomendación?", "Peso de municipios pequeños y alejados en el top del ranking, con y sin preferencias", "Disponible"),
    ("¿Qué pasaría si se bonifica el alquiler o se crea un vivero?", "Simulador: intervención do() sobre la palanca del modelo, con intervalo de incertidumbre", "En desarrollo"),
    ("¿Y si llega el Cercanías?", "Escenario con supuesto experto declarado (el efecto no se observa en los datos)", "En desarrollo"),
]

story = [
    P("ANEXO · APROXIMACIÓN TÉCNICA", "eyebrow"),
    P("Sistema de localización inteligente y descentralización de oficinas en la Comunidad de Madrid", "title"),
    P("Proponemos una herramienta de apoyo a la decisión para dos públicos. Las <b>empresas y emprendedores</b> buscan dónde abrir o "
      "trasladar una oficina dentro de los 179 municipios de la Comunidad de Madrid. Las <b>administraciones</b> (la Comunidad, los "
      "ayuntamientos y las agencias de desarrollo local) necesitan saber dónde hay potencial, qué lo frena y qué políticas lo activarían "
      "para descongestionar la capital y fijar actividad y población en las coronas intermedias y las cabeceras comarcales. Ambos "
      "perfiles trabajan sobre los mismos datos públicos y los mismos modelos.", "lede"),

    P("1. Enfoque general", "h2"),
    P("El sistema combina <b>dos modelos únicos para toda la región</b>, entrenados sobre los mismos 179 municipios; no hay un modelo "
      "por municipio. Un <b>GA²M</b> (modelo aditivo explicable con interacciones por pares) da la puntuación, porque es el que mejor "
      "ordena. Una <b>red bayesiana</b> explica las causas de cada resultado, responde consultas con información parcial y sostiene "
      "el simulador de políticas de la Administración. La puntuación de cada municipio es:", "body"),
    caja(P("S = percentil del GA²M entre los municipios candidatos (0-100)<br/>"
           "Puntuación = (S + Σ a<sub>k</sub>·u<sub>k</sub>) / (1 + Σ a<sub>k</sub>)<br/>"
           "u<sub>k</sub>: utilidad del municipio en la preferencia k · a<sub>k</sub>: peso según la importancia que indica el usuario",
           "formula")),
    Spacer(1, 5),
    P("Las restricciones se separan en dos tipos para que los modelos nunca reciban condiciones imposibles:", "body"),
    *B([
        "<b>Filtros duros.</b> Condiciones no negociables, como excluir Madrid capital, exigir oferta existente de oficinas o "
        "limitarse a municipios elegibles para ayudas contra la despoblación. Se aplican antes de puntuar; los municipios descartados "
        "reciben puntuación nula y se muestran aplanados en el mapa.",
        "<b>Preferencias blandas.</b> Factores que se ponderan sin descartar territorio, como el transporte, las ayudas o el coste. "
        "Se suman a la puntuación con un peso explícito, calibrado para que «muy importante» pese tanto como el modelo y «poco "
        "importante» la mitad, y se muestran por separado en la explicación.",
    ]),

    P("2. Arquitectura", "h2"),
    tabla(ARQ, ["Capa", "Tecnología", "Motivo"], [0.2 * W, 0.37 * W, 0.43 * W]),

    P("3. Datos y origen de cada variable", "h2"),
    P("Todas las fuentes de la versión base son públicas y se unen por código INE municipal, sección censal o coordenadas. La "
      "mayoría llega a través del portal de datos abiertos de la Comunidad de Madrid (datos.comunidad.madrid), donde el Instituto de "
      "Estadística de la Comunidad de Madrid (IECM) republica estadísticas de otros organismos. Por eso la tabla distingue la "
      "<b>fuente primaria</b>, que produce el dato, de quién lo <b>publica</b> y en qué conjunto de datos.", "body"),
    tabla(ORIGEN, ["Variable y uso", "Indicador", "Fuente primaria", "Publicado en · conjunto", "Año"],
          [0.19 * W, 0.24 * W, 0.27 * W, 0.22 * W, 0.08 * W]),
    Spacer(1, 4),
    P("IECM: Instituto de Estadística de la Comunidad de Madrid. Los conjuntos se identifican por su nombre en el portal de datos "
      "abiertos (datos.comunidad.madrid/catalogo/dataset/&lt;nombre&gt;). El anexo de fuentes amplía las fuentes previstas y privadas.", "note"),
    P("La canalización ya construida:", "body"),
    *B([
        "<b>Recolección automatizada</b> de los catálogos de datos abiertos de la Comunidad y del Ayuntamiento de Madrid (2.263 y 674 "
        "conjuntos), con descarga de 621 tablas municipales, la BDNS, los edificios del Catastro de los 179 municipios, las redes GTFS "
        "del Consorcio de Transportes y 153.517 puntos de interés de OpenStreetMap.",
        "<b>Normalización territorial:</b> cada tabla recibe el código INE de 5 dígitos a partir de un maestro de 179 municipios, con "
        "corrección de codificaciones y variantes de nombre. Paradas y puntos de interés se asignan a su sección censal por "
        "intersección espacial.",
        "<b>Tabla analítica única:</b> 179 municipios sin valores nulos, con unas 40 variables de demografía, renta, talento, empleo, "
        "tejido empresarial, coste inmobiliario, accesibilidad y servicios.",
    ]),
    P("<b>Variable objetivo.</b> En municipios muy pequeños la tasa neta empresarial es muy ruidosa (pocas unidades productivas), así "
      "que se acerca a la media regional en proporción inversa a su tamaño (contracción empírico-bayesiana).", "body"),
]

story.append(P("4. Modelos: red bayesiana y GA²M", "h2"))
story.append(P("La red tiene ocho nodos con un máximo de dos padres cada uno, para que sus tablas de probabilidad sean pequeñas y estén "
               "bien estimadas con 179 municipios. Cada variable continua se discretiza en terciles de su distribución real (unos 60 "
               "municipios por estado), salvo el acceso ferroviario, que es binario.", "body"))
story.append(KeepTogether([img_png("docs/informe/red_bayesiana.png", 0.84 * W),
                           P("Figura 1. Flujo completo: filtros duros, red bayesiana y puntuación con el GA²M y las preferencias. "
                             "Las etiquetas de las aristas de la red son correlaciones de Spearman entre las variables continuas, "
                             "solo como referencia descriptiva.", "note")]))
story += [
    Spacer(1, 6),
    tabla(NODOS, ["Nodo", "Variable", "Padres", "Cortes (p33 / p66)"], [0.21 * W, 0.42 * W, 0.19 * W, 0.18 * W]),
    Spacer(1, 6),
    P("<b>Aprendizaje de la red.</b> Las tablas de probabilidad se estiman con <i>BayesianEstimator</i> de pgmpy y prior BDeu "
      "(tamaño de muestra equivalente 10) sobre los estados discretizados. La red supera <i>check_model()</i> y cada probabilidad se "
      "verifica a mano en un anexo de transparencia.", "body"),
    P("<b>GA²M.</b> <i>Explainable Boosting Machine</i> de InterpretML sobre las mismas siete variables, sin discretizar, que predice "
      "la tasa neta empresarial. Es aditivo: la predicción es la suma de una curva por variable y de pocas interacciones, y cada curva "
      "se puede dibujar, así que la puntuación de cada municipio se descompone exactamente en contribuciones.", "body"),
    P("<b>Validación.</b> Validación cruzada de 5 particiones repetida 5 veces, con predicciones fuera de muestra. Mide cómo de bien "
      "ordena cada modelo los municipios frente a su tasa neta real:", "body"),
    tabla([
        ("GA²M", "0,398 ± 0,04", "51,7 %", "Elegido para puntuar: ordena mejor y sin empates"),
        ("Modelo lineal (referencia)", "0,383 ± 0,01", "48,3 %", "Cercano al GA²M, menos flexible"),
        ("Red bayesiana", "0,284 ± 0,05", "49,1 %", "Solo 9 niveles: la discretización pierde información"),
        ("Azar", "0", "33,5 %", "—"),
    ], ["Modelo", "Spearman con la realidad", "Acierto en el tercio superior", "Comentario"], [0.24 * W, 0.2 * W, 0.2 * W, 0.36 * W]),
    Spacer(1, 3),
    P("La señal es real pero moderada. La red acierta el estado de viabilidad el 45,9 % de las veces (azar 33,3 %), pero su log-loss "
      "medio (1,103 ± 0,015) no mejora el de una distribución uniforme (1,099): sus probabilidades no deben leerse como probabilidad "
      "literal de éxito. Por eso la puntuación se presenta como posición relativa entre candidatos (percentil) y la red se usa para "
      "explicar y simular.", "note"),

    P("5. Experiencia de usuario", "h2"),
    P("La aplicación arranca con una selección de perfil. Los dos recorridos comparten mapa, datos y modelos, pero responden a "
      "preguntas distintas: la empresa busca <i>dónde ir</i>; la Administración busca <i>dónde actuar y cómo</i>.", "body"),
    P("5.1 Empresas y emprendedores", "h3"),
    *B([
        "<b>Onboarding conversacional:</b> el usuario describe su negocio en texto libre (por ejemplo, un estudio de diseño de 8 "
        "personas que busca alquiler moderado y buen transporte). Un LLM lo traduce, con un esquema estructurado, en filtros duros, "
        "preferencias y variables aún inciertas, y el usuario confirma el resumen antes de calcular.",
        "<b>Mapa 3D y preguntas inteligentes:</b> la altura y el color de cada municipio siguen su puntuación. El panel lateral elige "
        "la siguiente pregunta por valor de la información (la que más reduce la incertidumbre del ranking entre los candidatos). Las "
        "respuestas (me da igual, poco o muy importante, imprescindible, no lo sé) se convierten en pesos o, si son imprescindibles, en "
        "filtros duros, y el mapa se recalcula al instante.",
        "<b>Mejores propuestas:</b> la cámara vuela al primer municipio y se muestra su desglose: aportación de cada variable según el "
        "GA²M, cadena causal de la red, aportación de cada preferencia y ayudas aplicables. Si la red y el GA²M discrepan, se avisa.",
    ]),
    P("5.2 Administraciones", "h3"),
    P("Pensado para la dirección general responsable del reequilibrio territorial y la administración local, para la consejería de "
      "economía y empleo y para los ayuntamientos y agencias de desarrollo local. El recorrido tiene tres bloques; el diagrama de estados completo está en la figura 2, al final del documento.", "body"),
    *B([
        "<b>Definir el ámbito.</b> Toda la región, una comarca, un tramo de población (por ejemplo, los municipios elegibles al Plan de "
        "Reequilibrio) o una selección de municipios.",
        "<b>Diagnóstico territorial.</b> Mapa base con la puntuación sin preferencias de empresa y capas superpuestas: dinamismo "
        "demográfico, nivel de ayudas, distancia a estación y coste. Al pinchar un municipio se abre su <b>ficha diagnóstica</b>: "
        "puesto en el ranking, estado de cada nodo de la red, contribución de cada factor y el factor que más lo limita, con los "
        "conteos y las tablas de la auditoría para quien quiera comprobarlos.",
        "<b>Simulador de políticas.</b> El técnico elige una política de un catálogo (bonificación del alquiler o del IBI, vivero de "
        "empresas, nueva estación…). La herramienta muestra la <b>hipótesis de traducción</b> a una palanca del modelo (por ejemplo, "
        "«ayuda al alquiler = el coste baja un nivel»), que es editable. Después aplica una intervención causal sobre la red: fija la "
        "palanca, recalcula lo que depende de ella y mantiene lo demás. El resultado es un <b>escenario</b> con el cambio de puntuación "
        "y su intervalo de incertidumbre. Si la palanca no tiene efecto observable en los datos, como el tren, la herramienta exige "
        "declarar un supuesto experto, que queda registrado.",
        "<b>Comparación e informe.</b> Los escenarios se guardan y se comparan con la situación base. El informe exportado incluye "
        "supuestos, intervalos y fuentes, con la advertencia de que es un escenario según el modelo y no una predicción.",
    ]),
]
story.append(KeepTogether([
    P("Ejemplo de ficha diagnóstica: Buitrago del Lozoya", "h3"),
    P("Cabecera comarcal de la Sierra Norte (2.034 habitantes, a más de 45 km de Madrid). Ocupa el puesto 125 de 139 candidatos "
      "(puntuación 10,8). Según el GA²M, su principal freno es el <b>estancamiento demográfico</b> (−0,28 puntos de tasa neta "
      "empresarial al año), seguido de un <b>valor inmobiliario bajo</b>, indicador de demanda débil (−0,15), y de un nivel formativo "
      "medio (−0,09). La distancia a Madrid, en cambio, no le penaliza en el modelo (+0,06). La red coincide: Dinamismo Bajo y "
      "P(Viabilidad Alta) = 0,19. Lectura para el técnico: las políticas que atraigan población (vivienda, servicios) probablemente "
      "rindan más aquí que las ayudas directas a la empresa. Su nivel de ayudas es Alto: con menos de 2.500 habitantes opta al Plan de Reequilibrio y a la rebaja fiscal por residencia.", "body"),
]))
story += [
    KeepTogether([
        P("6. Valor para la Administración", "h2"),
        P("La herramienta da a la Administración una vista común, basada en datos públicos y auditable, para decidir dónde y cómo "
          "actuar. Estas son las preguntas que responde y su estado actual:", "body"),
        tabla(PREGUNTAS, ["Pregunta", "Cómo la responde", "Estado"], [0.33 * W, 0.53 * W, 0.14 * W]),
    ]),
    Spacer(1, 6),
    P("<b>Indicador de reequilibrio.</b> Sirve para medir si una recomendación contribuye al objetivo territorial. De los 139 "
      "municipios candidatos, 103 (74 %) tienen menos de 20.000 habitantes. Sin preferencias, el top 20 del ranking incluye 13 (65 %): "
      "el modelo, por sí solo, da algo más de peso a municipios medianos y grandes en expansión. Si la empresa marca las ayudas como "
      "«poco importantes», el top 20 pasa a estar formado íntegramente por municipios de menos de 20.000 habitantes, 7 de ellos de "
      "menos de 2.500; como «muy importantes», 12 de menos de 2.500. Esto indica dos cosas: las ayudas son una palanca eficaz de "
      "reequilibrio, y sus pesos deben calibrarse con cuidado para no anular la viabilidad.", "body"),
    P("<b>Transparencia y rendición de cuentas.</b> Toda probabilidad de la red se puede rehacer a mano a partir de conteos de "
      "municipios (anexo de cálculo, verificado automáticamente frente a la librería) y toda puntuación del GA²M se descompone en "
      "contribuciones exactas. Los datos son públicos y citables, y los supuestos de cada escenario quedan escritos en el informe. "
      "Esto permite justificar decisiones de inversión pública con un razonamiento que cualquiera puede revisar.", "body"),

    P("7. Limitaciones y siguientes pasos", "h2"),
    *B([
        "<b>Simulador de políticas.</b> Está diseñado y prototipado (al bajar el coste, mediana de +4,5 puntos en 119 municipios), pero "
        "antes de ofrecerlo a la Administración necesita restricciones de monotonía en la red (hoy, por escasez de datos en algunas "
        "casillas, abaratar el coste puede bajar la puntuación) e intervalos de incertidumbre por remuestreo.",
        "<b>Calibración de la red.</b> Probar más suavizado y monotonía para que sus probabilidades superen a la distribución uniforme.",
        "<b>Transporte.</b> En los datos no explica la creación neta de empresas, ni siquiera a igual distancia de Madrid: cerca de la "
        "capital, tener estación coincide con ciudades grandes y maduras. Se incorpora como preferencia del usuario y, en el simulador, "
        "como supuesto experto declarado.",
        "<b>Ayudas.</b> El nivel se deduce hoy de tramos de población; falta verificar las listas oficiales de municipios de cada "
        "programa y recopilar tipos de IBI e IAE para una calculadora de coste neto.",
        "<b>Coste de oficinas.</b> El coste inmobiliario es un indicador residencial. Las rentas de oficinas, de acceso privado, y la "
        "cobertura de fibra y 5G mejorarían el modelo.",
        "<b>Validación con técnicos de la Comunidad de Madrid</b> del grafo, los umbrales, el catálogo de políticas y los pesos de las "
        "preferencias.",
    ]),
]
story += [PageBreak(),
          img_alto("docs/informe/estados_administracion_300ppp.png", alto_max=238 * mm, ancho_max=W),
          P("Figura 2. Diagrama de estados del perfil Administración (300 ppp: se puede ampliar). Azul: lógica ya implementada; "
            "blanco: pantallas de la aplicación; discontinuo: en desarrollo, con su número de tarea en la lista de pendientes.", "note")]
doc.build(story, onFirstPage=pie, onLaterPages=pie)
print("ok")
