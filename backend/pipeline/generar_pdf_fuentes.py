"""Genera docs/informe/Fuentes_de_datos_CAM.pdf: anexo breve de fuentes públicas y privadas (agrupadas por categoría)."""
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

pdfmetrics.registerFont(TTFont("Segoe", "C:/Windows/Fonts/segoeui.ttf"))
pdfmetrics.registerFont(TTFont("SegoeB", "C:/Windows/Fonts/segoeuib.ttf"))
pdfmetrics.registerFontFamily("Segoe", normal="Segoe", bold="SegoeB")

INK, INK2, MUTED, RULE = colors.HexColor("#0b0b0b"), colors.HexColor("#52514e"), colors.HexColor("#898781"), colors.HexColor("#d9d8d0")
BLUE, BLUE_BG, AMBER_BG, GREY_BG = colors.HexColor("#1c5cab"), colors.HexColor("#e6effb"), colors.HexColor("#fdf1d8"), colors.HexColor("#f0efec")

st = {
    "eyebrow": ParagraphStyle("eyebrow", fontName="Segoe", fontSize=8.5, textColor=MUTED, leading=11, spaceAfter=2),
    "title": ParagraphStyle("title", fontName="SegoeB", fontSize=19, leading=23, textColor=INK, spaceAfter=9),
    "lede": ParagraphStyle("lede", fontName="Segoe", fontSize=10, leading=14.5, textColor=INK2, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="SegoeB", fontSize=12.5, leading=16, textColor=INK, spaceBefore=10, spaceAfter=5),
    "body": ParagraphStyle("body", fontName="Segoe", fontSize=9.5, leading=13.5, textColor=INK, alignment=TA_LEFT),
    "cell": ParagraphStyle("cell", fontName="Segoe", fontSize=8.4, leading=11, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="SegoeB", fontSize=8.6, leading=11, textColor=INK),
    "head": ParagraphStyle("head", fontName="SegoeB", fontSize=7.8, leading=10, textColor=INK2),
    "note": ParagraphStyle("note", fontName="Segoe", fontSize=8, leading=11, textColor=MUTED),
    "bullet": ParagraphStyle("bullet", fontName="Segoe", fontSize=9.3, leading=13.2, textColor=INK, leftIndent=10, bulletIndent=0),
}
ESTADO_BG = {"Integrada": BLUE_BG, "Parcial": AMBER_BG, "Prevista": GREY_BG}

P = lambda t, s="cell": Paragraph(t, st[s])

PUBLICAS = [
    ("Estadística oficial regional",
     "Instituto de Estadística de la Comunidad de Madrid: portal de datos abiertos, Banco de Datos Municipal, Nomecalles",
     "Padrón, censo anual, dinámica y colectivo empresarial, renta disponible, afiliación, paro. Fuente del <b>target</b> y de la mayoría de nodos de la red",
     "Integrada"),
    ("Estadística oficial nacional",
     "INE: padrón continuo, Censo 2021, Atlas de Distribución de Renta, Directorio Central de Empresas, migraciones",
     "Renta y nivel formativo por sección censal; empresas por actividad y tamaño; saldo migratorio",
     "Parcial"),
    ("Datos municipales",
     "Ayuntamiento de Madrid (datos abiertos) y portales de grandes municipios",
     "Detalle por distrito y barrio de la capital; censo de locales y actividades; equipamientos",
     "Parcial"),
    ("Ayudas e incentivos",
     "Base de Datos Nacional de Subvenciones, BOCM, planes de reequilibrio territorial y ordenanzas fiscales municipales",
     "Convocatorias y concesiones con ámbito Madrid; municipios elegibles; tipos y bonificaciones de IBI, IAE e ICIO",
     "Parcial"),
    ("Inmobiliario y suelo",
     "Dirección General del Catastro (servicios INSPIRE y estadísticas), Portal del Suelo de la CAM, Ministerio de Vivienda",
     "Superficie y uso de edificios (oficinas, comercio, industria), valor catastral, suelo terciario ofertado, alquiler residencial",
     "Integrada"),
    ("Movilidad y transporte",
     "Consorcio Regional de Transportes (redes GTFS, Encuesta Domiciliaria de Movilidad), Renfe/Adif, Ministerio de Transportes",
     "Paradas, frecuencias y acceso ferroviario por municipio; flujos origen-destino; red viaria de alta capacidad",
     "Integrada"),
    ("Telecomunicaciones",
     "Ministerio para la Transformación Digital (informe de cobertura de banda ancha), CNMC",
     "Cobertura de fibra FTTH y 5G por municipio; candidata a filtro o nodo de conectividad",
     "Prevista"),
    ("Servicios y calidad de vida",
     "Registros de la Comunidad de Madrid: centros sanitarios, educación, entidades deportivas, calidad del aire",
     "Contexto de bienestar para el dashboard y como variables secundarias del modelo",
     "Parcial"),
    ("Cartografía y geoespacial",
     "Secciones censales de la CAM, Geoportal IDEM, Centro Nacional de Información Geográfica",
     "Límites y unión espacial; relieve y usos del suelo para el visor 3D",
     "Integrada"),
    ("Datos colaborativos abiertos",
     "OpenStreetMap (Overpass API y extractos regionales), licencia ODbL",
     "Densidad de servicios para trabajadores: restauración, gimnasios, guarderías, coworking, oficinas, uso del suelo",
     "Integrada"),
]

PRIVADAS = [
    ("Mercado de oficinas",
     "Consultoras inmobiliarias (CBRE, JLL, Colliers, Cushman &amp; Wakefield, Savills)",
     "Renta de oficinas en €/m², disponibilidad y absorción por submercado. Cubre el principal hueco de los datos abiertos",
     "Informes públicos trimestrales; series detalladas bajo licencia"),
    ("Portales inmobiliarios",
     "Idealista (API), Fotocasa y similares",
     "Precio de oferta y rotación de locales y oficinas por municipio o distrito",
     "Acuerdo de acceso a API; el scraping queda sujeto a sus condiciones de uso"),
    ("Información empresarial",
     "Registro Mercantil y bases comerciales (SABI, Informa, Axesor)",
     "Sede, tamaño y supervivencia de empresas; permite georreferenciar beneficiarios de ayudas",
     "Suscripción de pago"),
    ("Puntos de interés comerciales",
     "Google Places API",
     "Servicios y valoraciones con mayor cobertura que OpenStreetMap en municipios rurales",
     "Pago por uso; OpenStreetMap como alternativa abierta"),
    ("Movilidad por telefonía",
     "Operadores de telecomunicaciones y proveedores de analítica de movilidad",
     "Flujos pendulares residencia-trabajo con alta frecuencia temporal",
     "Convenio o compra de datos agregados"),
]


def tabla(filas, cab, anchos, estado_col=None):
    data = [[P(c, "head") for c in cab]]
    for f in filas:
        data.append([P(f[0], "cellb")] + [P(x) for x in f[1:]])
    t = Table(data, colWidths=anchos, repeatRows=1)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK2),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if estado_col is not None:
        for i, f in enumerate(filas, start=1):
            style.append(("BACKGROUND", (estado_col, i), (estado_col, i), ESTADO_BG[f[estado_col]]))
    t.setStyle(TableStyle(style))
    return t


def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Segoe", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 10 * mm, "Datathon CAM · Anexo de fuentes de datos · octubre 2026")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate("docs/informe/Fuentes_de_datos_CAM.pdf", pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=16 * mm, bottomMargin=17 * mm, title="Fuentes de datos · Localización de oficinas CAM",
                        author="Gregorio García Velasco; Guillermo Franco Gimeno", subject="Anexo de fuentes públicas y privadas")
W = A4[0] - 36 * mm
story = [
    P("ANEXO · FUENTES DE DATOS", "eyebrow"),
    P("Fuentes de datos para la localización de oficinas en la Comunidad de Madrid", "title"),
    P("La solución propuesta estima la viabilidad de abrir o trasladar oficinas en los 179 municipios de la Comunidad de Madrid, "
      "con el objetivo de descongestionar la capital y dinamizar los municipios periféricos y rurales. Combina una red bayesiana "
      "explicable, un modelo aditivo (GA²M) y un dashboard 3D. Este anexo enumera, agrupadas por categoría, las fuentes públicas "
      "y privadas que alimentan la solución.", "lede"),
    P("Todas las fuentes se integran por el <b>código INE municipal</b> (5 dígitos), por la <b>sección censal</b> (10 dígitos) "
      "o por <b>coordenadas</b> (ETRS89 / UTM 30N), lo que permite trabajar a escala de municipio, distrito, sección o punto.", "body"),
    Spacer(1, 4),
    P("1. Fuentes públicas", "h2"),
    tabla(PUBLICAS, ["Categoría", "Fuentes", "Qué aporta a la solución", "Estado"], [0.195 * W, 0.315 * W, 0.375 * W, 0.115 * W], estado_col=3),
    Spacer(1, 3),
    P("Estado: <b>Integrada</b>, datos descargados y unidos por código INE; <b>Parcial</b>, parte de la fuente integrada y el resto "
      "localizado; <b>Prevista</b>, fuente identificada pendiente de descarga.", "note"),
]
story.append(KeepTogether([
    P("2. Fuentes privadas o de acceso restringido", "h2"),
    P("Complementan los huecos que no cubren los datos abiertos, sobre todo el precio y la disponibilidad de oficinas. "
      "Su incorporación depende de licencias o acuerdos y no condiciona el funcionamiento de la versión abierta del sistema.", "body"),
    Spacer(1, 5),
    tabla(PRIVADAS, ["Categoría", "Fuentes", "Qué aporta a la solución", "Acceso"], [0.17 * W, 0.27 * W, 0.36 * W, 0.20 * W]),
]))
story += [
    P("3. Criterios de uso", "h2"),
    *[Paragraph(t, st["bullet"], bulletText="•") for t in [
        "<b>Prioridad a lo abierto.</b> El modelo funciona solo con fuentes públicas; las privadas mejoran la precisión del coste operativo.",
        "<b>Licencias y atribución.</b> Se respeta la atribución exigida (OpenStreetMap ODbL, Dirección General del Catastro, "
        "reutilización de datos del sector público) y las condiciones de uso de la BDNS.",
        "<b>Datos personales.</b> Solo se usan datos agregados por territorio; los beneficiarios individuales de ayudas no se publican ni se perfilan.",
        "<b>Actualización.</b> Las fuentes mensuales (afiliación, paro, ayudas) y anuales (padrón, renta, catastro) se recargan "
        "con los scripts del proyecto; el resto se revisa en cada edición.",
    ]],
]
doc.build(story, onFirstPage=pie, onLaterPages=pie)
print("ok")
