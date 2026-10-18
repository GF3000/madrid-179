"""Genera docs/informe/Aproximacion_tecnica_CAM.pdf: descripción breve de la aproximación técnica propuesta.
Mismo estilo que generar_pdf_fuentes.py. Requiere reportlab y docs/informe/red_bayesiana.png (diagrama_red_bayesiana.py).
Cifras del modelo v2 (2026-10-14) y de la app (2026-10-18): si cambia el modelo, revisarlas a mano.
"""
import struct

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
    canvas.drawString(18 * mm, 10 * mm, "Madrid 179 · Aproximación técnica · modelo v2 · octubre 2026")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate("docs/informe/Aproximacion_tecnica_CAM.pdf", pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=16 * mm, bottomMargin=17 * mm, title="Madrid 179 · Aproximación técnica",
                        author="Gregorio García Velasco; Guillermo Franco Gimeno", subject="Descripción de la aproximación técnica")
W = A4[0] - 36 * mm

ARQ = [
    ("Aplicación web", "React y TypeScript (Vite), servida por la propia API en madrid179.web.app",
     "Sin instalación; versión de escritorio y de móvil con la misma base de código"),
    ("Mapa 3D", "MapLibre con deck.gl (WebGL)",
     "Los 179 municipios como columnas por grupo de puntuación, con transiciones al cambiar preferencias"),
    ("Motores de modelo", "Python, FastAPI (API /api/v1), pgmpy (red bayesiana) e InterpretML (GA²M)",
     "Un artefacto entrenado se carga en memoria; la API no reentrena y responde en milisegundos"),
    ("Datos", "Tablas CSV con clave INE, artefacto del modelo y GeoJSON de límites municipales",
     "179 filas y datos anuales: no hace falta un gestor de base de datos"),
    ("Asistente", "LLM (DeepSeek, salidas JSON) con saneado contra el catálogo y verificador en código",
     "Traduce la descripción del negocio a preferencias y filtros, y redacta un resumen ceñido a los datos de la ficha"),
    ("Despliegue", "Contenedor en Cloud Run (Madrid) tras Firebase Hosting; CI con tests en GitHub Actions",
     "Coste mínimo en reposo; los tests comprueban que el artefacto reproduce los resultados versionados"),
]

NODOS = [
    ("Distancia Madrid", "Distancia del centroide a la Puerta del Sol (km)", "Raíz", "31,8 / 45,2 km"),
    ("Talento", "% de población de 15 y más años con estudios superiores", "Raíz", "30,6 / 39,5 %"),
    ("Acceso Ferroviario", "Estaciones de Metro, Metro Ligero o Cercanías (GTFS CRTM)", "Distancia", "0 / más de 0"),
    ("Coste Inmobiliario", "Valor catastral residencial por unidad urbana (miles €)", "Distancia, Talento", "69,8 / 95,7"),
    ("Renta", "Renta disponible bruta per cápita (€)", "Talento", "17.065 / 19.992"),
    ("Especialización Servicios", "% de unidades productivas en información y servicios profesionales", "Distancia, Talento", "12,7 / 18,3 %"),
    ("Dinamismo Demográfico", "Crecimiento de la población en 5 años (padrón)", "Distancia, Coste", "6,8 / 12,9 %"),
    ("Densidad", "Habitantes por km²", "Distancia, Coste", "61 / 249"),
    ("Juventud", "% de población menor de 45 años", "Distancia, Densidad", "47,7 / 51,9 %"),
    ("Sanidad", "Centros sanitarios y farmacias por 1.000 hab. (OpenStreetMap)", "Densidad", "0,28 / 0,61"),
    ("Paro", "Paro registrado por 100 habitantes", "Distancia, Renta", "4,05 / 5,21"),
    ("Viabilidad Empresarial", "Tasa neta anual de unidades productivas 2020-2024 (objetivo)", "Dinamismo, Densidad", "0,60 / 0,98 %"),
]

st["h3"] = ParagraphStyle("h3", fontName="SegoeB", fontSize=10.5, leading=14, textColor=INK, spaceBefore=8, spaceAfter=3, keepWithNext=1)


def img_png(ruta, ancho):
    w, h = struct.unpack(">II", open(ruta, "rb").read(24)[16:24])
    return Image(ruta, width=ancho, height=ancho * h / w)


ORIGEN = [
    ("Viabilidad Empresarial (objetivo)", "Tasa neta de unidades productivas: (nacen + entran − mueren − salen) / activas",
     "Dinámica Empresarial · Dirección General de Economía e Industria (CAM)", "IECM · <i>din_emp</i>", "2020-24"),
    ("Dinamismo Demográfico · Densidad", "Crecimiento de la población empadronada en 5 años; habitantes por km²",
     "Padrón municipal · INE", "IECM · <i>padron_por_sexo</i>", "2020-25"),
    ("Juventud", "% de población menor de 45 años",
     "Padrón municipal · INE", "IECM · <i>grado_juventud_por_edad</i>", "2025"),
    ("Talento", "% de población de 15 y más años con estudios superiores",
     "Censo de Población anual · INE", "IECM · <i>poblacion_censada_por_estudios_y_sexo</i>", "2024"),
    ("Renta", "Renta disponible bruta per cápita",
     "Indicador de Renta Disponible Bruta Municipal · INE", "IECM · <i>irpf_indicador_renta</i>", "2023"),
    ("Paro", "Paro registrado por 100 habitantes",
     "Servicio Público de Empleo (CAM)", "IECM · <i>1902280</i>", "2025"),
    ("Especialización Servicios", "% de unidades productivas en información y servicios profesionales",
     "Colectivo Empresarial · Dirección General de Economía e Industria (CAM)", "IECM · <i>col_emp_ramas</i>", "2025"),
    ("Coste Inmobiliario", "Valor catastral residencial medio por unidad urbana",
     "Catastro Inmobiliario · Dirección General del Catastro", "IECM · <i>1002054</i>", "2026"),
    ("GA²M y filtro: oferta de oficinas", "Unidades urbanas de uso oficinas (total y por 1.000 hab.)",
     "Catastro Inmobiliario · Dirección General del Catastro", "IECM · <i>unidades_urbanas_por_uso</i>", "2026"),
    ("Distancia Madrid", "Km del centroide municipal a la Puerta del Sol",
     "Cálculo propio sobre el seccionado censal", "Comunidad de Madrid · <i>secciones_censales</i>", "2019"),
    ("Acceso Ferroviario · distancia a estación", "Estaciones de Metro, Metro Ligero y Cercanías",
     "Consorcio Regional de Transportes de Madrid (GTFS)", "Portal de datos abiertos del CRTM", "2026"),
    ("Sanidad · servicios para la plantilla", "Sanidad, restauración, gimnasios, guarderías, coworking, deporte",
     "OpenStreetMap (licencia ODbL)", "Overpass API", "2026"),
    ("Ayudas oficiales (fuera del modelo)", "Municipios de los grupos LEADER 2023-2027; reglas para menos de 2.500 hab.",
     "Convenios con los tres grupos de acción local (anexo I) · Ley 5/2024 (deducciones del IRPF)",
     "BOCM 18-01-2025 · padrón (INE)", "2025"),
]

PREGUNTAS = [
    ("¿Dónde me conviene abrir una oficina?", "«Dónde abrir»: ranking del GA²M ajustado por las preferencias y filtros del usuario", "Disponible"),
    ("¿Qué favorece y qué frena a un municipio?", "Ficha: aportación de cada factor (GA²M), lectura de la red bayesiana y ayudas que le alcanzan", "Disponible"),
    ("¿Qué municipios necesitan actividad y cuáles pueden atraerla?", "«Dónde actuar»: necesidad de reequilibrio frente a viabilidad, en cuatro grupos, con frenos y contexto", "Disponible"),
    ("¿Qué municipios encajan con un perfil?", "«Explorar perfiles»: consulta a la red con información parcial", "Disponible"),
    ("¿Cuánto reequilibrio produce una recomendación?", "Peso de municipios pequeños y en LEADER en el top del ranking, con y sin preferencias", "Disponible"),
    ("¿Qué pasaría si se bonifica el alquiler o se crea un vivero?", "Simulador: intervención do() sobre la palanca del modelo, con intervalo de incertidumbre", "En desarrollo"),
]

story = [
    P("MADRID 179 · ANEXO · APROXIMACIÓN TÉCNICA", "eyebrow"),
    P("Localización de oficinas y reequilibrio territorial en los 179 municipios de la Comunidad de Madrid", "title"),
    P("Madrid 179 es una herramienta de apoyo a la decisión para dos públicos. Las <b>empresas y emprendedores</b> buscan dónde abrir o "
      "trasladar una oficina dentro de los 179 municipios de la Comunidad. Las <b>administraciones</b> (la Comunidad, los "
      "ayuntamientos y las agencias de desarrollo local) necesitan saber qué municipios necesitan actividad, cuáles pueden atraerla y "
      "qué la frena. Ambos perfiles trabajan sobre los mismos datos públicos y los mismos modelos. La aplicación está publicada en "
      "<b>madrid179.web.app</b> y el código es abierto (licencia MIT).", "lede"),

    P("1. Enfoque general", "h2"),
    P("El sistema combina <b>dos modelos únicos para toda la región</b>, entrenados sobre los mismos 179 municipios; no hay un modelo "
      "por municipio. Un <b>GA²M</b> (modelo aditivo explicable con interacciones por pares) da la puntuación, porque es el que mejor "
      "ordena. Una <b>red bayesiana</b> no puntúa: explica cada resultado, responde consultas con información parcial y sostendrá el "
      "simulador de políticas. La puntuación de cada municipio es:", "body"),
    caja(P("S = percentil del GA²M entre los municipios candidatos (0-100)<br/>"
           "Puntuación = (S + Σ a<sub>k</sub>·u<sub>k</sub>) / (1 + Σ a<sub>k</sub>)<br/>"
           "u<sub>k</sub>: utilidad del municipio en la preferencia k (0-1)<br/>"
           "a<sub>k</sub> = r · sd(S) / sd(u<sub>k</sub>) · r = 0 / 0,5 / 1 · Σ a<sub>k</sub> ≤ 3",
           "formula")),
    Spacer(1, 5),
    P("Las restricciones se separan en dos tipos para que los modelos nunca reciban condiciones imposibles:", "body"),
    *B([
        "<b>Filtros duros.</b> Siempre: Madrid capital no es candidata (es la referencia del reequilibrio) y se exige al menos un "
        "local de oficinas en el Catastro (139 candidatos). El usuario puede añadir 7 más marcando algo como imprescindible: "
        "estación a menos de cierta distancia, distancia a Madrid mínima o máxima, población mínima o máxima, coworking o poder "
        "optar a ayudas. Se aplican antes de puntuar; los municipios descartados se muestran aparte en el mapa.",
        "<b>Preferencias</b> (15). Factores que se ponderan sin descartar territorio: tren, transporte público, distancia a Madrid, "
        "coste, ayudas, talento, mano de obra, juventud, tamaño, renta, servicios profesionales, crecimiento, oficinas, coworking y "
        "servicios para la plantilla. «Muy importante» pesa tanto como el modelo y «poco importante» la mitad; con todas sumadas, "
        "el modelo pesa siempre al menos una cuarta parte. Cada preferencia se muestra por separado en la explicación.",
    ]),

    P("2. Arquitectura", "h2"),
    tabla(ARQ, ["Capa", "Tecnología", "Motivo"], [0.2 * W, 0.37 * W, 0.43 * W]),

    P("3. Datos y origen de cada variable", "h2"),
    P("Todas las fuentes son públicas y se unen por código INE municipal, sección censal o coordenadas. La mayoría llega a través "
      "del portal de datos abiertos de la Comunidad de Madrid (datos.comunidad.madrid), donde el Instituto de Estadística de la "
      "Comunidad de Madrid (IECM) republica estadísticas de otros organismos. Por eso la tabla distingue la <b>fuente primaria</b>, "
      "que produce el dato, de quién lo <b>publica</b> y en qué conjunto de datos.", "body"),
    tabla(ORIGEN, ["Variable y uso", "Indicador", "Fuente primaria", "Publicado en · conjunto", "Año"],
          [0.19 * W, 0.24 * W, 0.27 * W, 0.22 * W, 0.08 * W]),
    Spacer(1, 4),
    P("IECM: Instituto de Estadística de la Comunidad de Madrid. Los conjuntos se identifican por su nombre en el portal de datos "
      "abiertos (datos.comunidad.madrid/catalogo/dataset/&lt;nombre&gt;). Las ayudas oficiales no entran en ningún modelo: se "
      "muestran como información, como preferencia o como filtro. El anexo de fuentes amplía las fuentes previstas y privadas.", "note"),
    P("La canalización construida:", "body"),
    *B([
        "<b>Recolección automatizada</b> de los catálogos de datos abiertos de la Comunidad y del Ayuntamiento de Madrid (2.263 y 674 "
        "conjuntos), con descarga de 621 tablas municipales, los edificios del Catastro de los 179 municipios, las redes GTFS "
        "del Consorcio de Transportes y 153.517 puntos de interés de OpenStreetMap.",
        "<b>Normalización territorial:</b> cada tabla recibe el código INE de 5 dígitos a partir de un maestro de 179 municipios, con "
        "corrección de codificaciones y variantes de nombre. Paradas y puntos de interés se asignan a su sección censal por "
        "intersección espacial.",
        "<b>Tabla analítica única:</b> 179 municipios sin valores nulos, con unas 40 variables de demografía, renta, talento, empleo, "
        "tejido empresarial, coste inmobiliario, accesibilidad y servicios.",
    ]),
    P("<b>Variable objetivo.</b> En municipios muy pequeños la tasa neta empresarial es muy ruidosa (pocas unidades productivas), así "
      "que se acerca a la media regional en proporción inversa a su tamaño (contracción empírico-bayesiana). Esa contracción "
      "favorece en parte a los municipios grandes y densos; se tiene en cuenta al leer el peso de la densidad y la población.", "body"),
]

story.append(P("4. Modelos: red bayesiana y GA²M", "h2"))
story.append(P("La red tiene <b>12 nodos y 17 aristas</b>, con un máximo de dos padres cada uno, para que sus tablas de probabilidad "
               "sean pequeñas y estén bien estimadas con 179 municipios. Cada variable continua se discretiza en terciles de su "
               "distribución real (unos 60 municipios por estado), salvo el acceso ferroviario, que es binario. Los padres de los "
               "cuatro nodos añadidos en la versión 2 (densidad, juventud, sanidad y paro) se eligieron por puntuación BDeu local "
               "entre candidatos plausibles.", "body"))
story.append(KeepTogether([img_png("docs/informe/red_bayesiana.png", 0.84 * W),
                           P("Figura 1. Flujo completo: filtros duros, red bayesiana y puntuación con el GA²M y las preferencias. "
                             "Las etiquetas de las aristas de la red son correlaciones de Spearman entre las variables continuas, "
                             "solo como referencia descriptiva.", "note")]))
story += [
    Spacer(1, 6),
    tabla(NODOS, ["Nodo", "Variable", "Padres", "Cortes (p33 / p66)"], [0.21 * W, 0.42 * W, 0.19 * W, 0.18 * W]),
    Spacer(1, 6),
    P("<b>Aprendizaje de la red.</b> Las tablas de probabilidad se estiman con <i>BayesianEstimator</i> de pgmpy y prior BDeu "
      "(tamaño de muestra equivalente 50, elegido por validación cruzada) sobre los estados discretizados. La red supera "
      "<i>check_model()</i> y cada probabilidad se verifica a mano en el anexo de cálculo, que falla si la librería y el cálculo "
      "manual difieren.", "body"),
    P("<b>GA²M.</b> <i>Explainable Boosting Machine</i> de InterpretML sobre <b>14 variables</b> sin discretizar (las 11 de la red, la "
      "oferta de oficinas por habitante, la distancia a la estación y la población) y 10 interacciones, que predice la tasa neta "
      "empresarial. Es aditivo: la predicción es la suma de una curva por variable y de pocas interacciones, así que la puntuación de "
      "cada municipio se descompone exactamente en aportaciones. Se excluyen las variables con fuga de información (stock de "
      "unidades productivas y afiliados al final del periodo del objetivo).", "body"),
    P("<b>Validación.</b> Validación cruzada de 5 particiones repetida 5 veces, con predicciones fuera de muestra. Mide cómo de bien "
      "ordena cada modelo los municipios frente a su tasa neta real:", "body"),
    tabla([
        ("GA²M v2 (14 variables)", "0,529 ± 0,03", "64,3 %", "Elegido para puntuar"),
        ("GA²M v1 (7 variables)", "0,398 ± 0,04", "51,7 %", "Versión anterior"),
        ("Modelo lineal (7 variables)", "0,383 ± 0,01", "48,3 %", "Referencia"),
        ("Red bayesiana v2, P(Alta)", "0,398", "—", "Explica; con evidencia completa solo da 9 niveles"),
        ("Azar", "0", "33,5 %", "—"),
    ], ["Modelo", "Spearman con la realidad", "Acierto en el tercio superior", "Comentario"], [0.26 * W, 0.19 * W, 0.2 * W, 0.35 * W]),
    Spacer(1, 3),
    P("La señal es real pero <b>moderada</b>. La red acierta el estado de viabilidad el 44,7 % de las veces (azar 33,3 %) y su "
      "log-loss medio (1,008 ± 0,015) ya mejora el de una distribución uniforme (1,099; la versión 1 no lo hacía), pero sus "
      "probabilidades siguen siendo aproximadas. Por eso la puntuación se presenta como posición relativa entre candidatos "
      "(percentil) y siempre como asociación, no como efecto causal. El transporte no mostró señal propia sobre el objetivo: entra "
      "como preferencia o filtro del usuario.", "note"),

    P("5. La aplicación", "h2"),
    P("Tres modos comparten mapa, datos y modelos, y responden a preguntas distintas: la empresa busca <i>dónde ir</i>; la "
      "Administración busca <i>dónde actuar</i>.", "body"),
    P("5.1 «Dónde abrir» (empresas y emprendedores)", "h3"),
    *B([
        "<b>Asistente:</b> el usuario describe su negocio en texto libre. Un LLM solo lo <i>traduce</i> a preferencias y filtros del "
        "catálogo (JSON saneado contra el catálogo); la aplicación muestra lo que ha entendido y permite deshacerlo. También se "
        "puede ajustar cada preferencia a mano (me da igual, poco o muy importante, imprescindible).",
        "<b>Mapa 3D:</b> cada municipio es una columna con la altura y el color de su grupo (cinco quintiles, «no cumple tus "
        "requisitos» y «fuera del análisis»). Al cambiar una preferencia, las columnas se recolocan y un panel explica qué ha "
        "cambiado. Un recorrido guiado vuela por los mejores municipios.",
        "<b>Ficha:</b> factores a favor y en contra según el GA²M en tres niveles de fuerza, lectura de la red bayesiana, perfil en "
        "terciles, ayudas oficiales que alcanzan al municipio y un resumen «En pocas palabras» redactado por el LLM. Un verificador "
        "en código comprueba que cada frase cite datos de la ficha, que las cifras coincidan y que no haya lenguaje causal; lo que "
        "no pasa la revisión se descarta. Si la red y el GA²M discrepan, se avisa.",
    ]),
    P("5.2 «Dónde actuar» (Administración)", "h3"),
    P("Pensado para la dirección general responsable del reequilibrio territorial, la consejería de economía y empleo y los "
      "ayuntamientos y agencias de desarrollo local. Cubre 178 municipios (Madrid capital es la referencia).", "body"),
    *B([
        "<b>Ámbito:</b> tramo de población, distancia a Madrid, municipios sin oficinas o municipios en LEADER.",
        "<b>Diagnóstico en cuatro grupos:</b> <i>necesidad de reequilibrio</i> (media de percentiles de crecimiento de población bajo, "
        "pocos menores de 45 años, paro alto y población pequeña) frente a <i>viabilidad</i> (percentil del GA²M). Resultado: "
        "necesita actividad y puede atraerla (33), necesita actividad y le cuesta atraerla (56), va por su cuenta (57) y sin "
        "urgencia, con poca viabilidad (32).",
        "<b>Frenos:</b> las aportaciones negativas del GA²M de cada municipio, marcadas como <i>palanca</i> (algo que una política "
        "puede mover a medio plazo, como la especialización o la oferta de oficinas) o <i>estructural</i>. El resultado es "
        "revelador: el modelo atribuye casi todo a factores estructurales (crecimiento, densidad, distancia).",
        "<b>Contexto para la política</b>, separado del modelo: oficinas en el Catastro (39 municipios sin ningún local), coworking "
        "y programas oficiales (LEADER, deducciones del IRPF y PIR sin cofinanciación para menos de 2.500 habitantes).",
        "<b>Escenarios</b> (en desarrollo): intervención do() sobre la red con su intervalo de incertidumbre, presentada siempre "
        "como escenario según el modelo y no como predicción.",
    ]),
    P("5.3 «Explorar perfiles»", "h3"),
    P("Consulta a la red bayesiana con información parcial (por ejemplo, «lejos de Madrid y con talento alto»): devuelve la "
      "probabilidad de cada nivel de viabilidad y resalta en el mapa los municipios que encajan.", "body"),
]
story.append(KeepTogether([
    P("Ejemplo de ficha: Buitrago del Lozoya", "h3"),
    P("Cabecera comarcal de la Sierra Norte (2.034 habitantes, a 64 km de Madrid). Ocupa el puesto 126 de 139 candidatos "
      "(puntuación 10,1). Según el GA²M, su principal freno es el <b>escaso crecimiento de población</b> (−0,31 puntos de tasa "
      "neta empresarial al año), seguido del <b>valor de la vivienda</b>, que el modelo lee como señal de demanda (−0,09), de la "
      "densidad (−0,05) y del nivel formativo (−0,04). La distancia a Madrid, en cambio, le suma (+0,15). La red coincide: "
      "Dinamismo Bajo y Densidad Media, con P(Viabilidad Alta) = 0,22 y P(Baja) = 0,56. En «Dónde actuar» queda en el grupo "
      "«necesita actividad y le cuesta atraerla», con frenos estructurales. Lectura para el técnico: las políticas que atraigan "
      "población (vivienda, servicios) probablemente rindan más aquí que las ayudas directas a la empresa. Está en el grupo LEADER "
      "GALSINMA (Sierra Norte) y, por tener menos de 2.500 habitantes, quien se traslade puede optar a las deducciones del IRPF.", "body"),
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
      "municipios candidatos, 103 (74 %) tienen menos de 20.000 habitantes y 33 menos de 2.500. Sin preferencias, el top 20 incluye "
      "13 de menos de 20.000 (65 %), 1 de menos de 2.500 y 8 en LEADER: el modelo, por sí solo, da algo más de peso a municipios "
      "medianos y grandes en expansión. Si la empresa marca «Poder optar a ayudas» como poco importante, el top 20 pasa a 17, 2 y "
      "16; como muy importante, los 20 son de menos de 20.000 habitantes y están en LEADER, y 5 tienen menos de 2.500. Las ayudas "
      "son una palanca eficaz de reequilibrio, y por eso su peso tiene un tope: el modelo nunca pesa menos de una cuarta parte.", "body"),
    P("<b>Transparencia y rendición de cuentas.</b> Toda probabilidad de la red se puede rehacer a mano a partir de conteos de "
      "municipios (anexo de cálculo, verificado automáticamente frente a la librería) y toda puntuación del GA²M se descompone en "
      "aportaciones exactas. Los datos son públicos y citables, el código es abierto y la API es pública. Esto permite justificar "
      "decisiones de inversión pública con un razonamiento que cualquiera puede revisar.", "body"),

    P("7. Limitaciones y siguientes pasos", "h2"),
    *B([
        "<b>Señal moderada.</b> El modelo ordena claramente mejor que el azar, pero no predice el éxito de una empresa concreta. "
        "Son asociaciones observadas en 2020-2024, no efectos causales.",
        "<b>Simulador de políticas.</b> Diseñado y prototipado, pero antes de ofrecerlo necesita monotonía completa en la tabla del "
        "objetivo (queda una violación, por escasez de datos en una casilla) e intervalos de incertidumbre por remuestreo.",
        "<b>Necesidad de reequilibrio.</b> Su definición es provisional: hoy correlaciona mucho con el tamaño (ρ = −0,66 con la "
        "población), así que los grupos de necesidad alta se llenan de pueblos muy pequeños. Sus variables y pesos deben validarse "
        "con técnicos de la Comunidad.",
        "<b>Ayudas.</b> Integradas las listas oficiales de LEADER y las reglas para menos de 2.500 habitantes. Faltan Pueblos con "
        "Vida, las ayudas estatales al reto demográfico y las convocatorias vigentes por perfil de negocio (Base de Datos Nacional "
        "de Subvenciones, ya descargada pero sin integrar).",
        "<b>Coste de oficinas.</b> El coste inmobiliario es un indicador residencial. Las rentas de oficinas, de acceso privado, la "
        "superficie de oficinas del Catastro y la cobertura de fibra y 5G mejorarían el modelo.",
        "<b>Validación con técnicos de la Comunidad de Madrid</b> del grafo, los umbrales, los textos de la ficha y los pesos de las "
        "preferencias.",
    ]),
]
doc.build(story, onFirstPage=pie, onLaterPages=pie)
print("ok")
