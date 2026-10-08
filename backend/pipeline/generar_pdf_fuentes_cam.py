"""Documento 2 · Fuentes de datos (sobrio, con las fuentes oficiales de la Comunidad de Madrid en primer plano).
Salida: docs/presentaciones/2_Fuentes_de_datos.pdf
Tipografías de la plantilla de las presentaciones (Poppins y Didact Gothic, instaladas para el usuario).
"""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FD = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "Fonts")
pdfmetrics.registerFont(TTFont("Poppins", os.path.join(FD, "Poppins-SemiBold.ttf")))
pdfmetrics.registerFont(TTFont("Body", os.path.join(FD, "DidactGothic-Regular.ttf")))
pdfmetrics.registerFont(TTFont("BodyB", os.path.join(FD, "Poppins-Medium.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyB")

NAVY, INK, GREY, RULE, TINT = (colors.HexColor(c) for c in ("#374768", "#1b1b1b", "#5a5f6b", "#c9cfdc", "#eef1f8"))
st = {
    "eyebrow": ParagraphStyle("e", fontName="Body", fontSize=8.5, leading=11, textColor=GREY, spaceAfter=3),
    "title": ParagraphStyle("t", fontName="Poppins", fontSize=20, leading=25, textColor=INK, spaceAfter=4),
    "sub": ParagraphStyle("s", fontName="Body", fontSize=10.5, leading=14, textColor=GREY, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Poppins", fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=12, spaceAfter=5),
    "body": ParagraphStyle("b", fontName="Body", fontSize=9.6, leading=13.6, textColor=INK, spaceAfter=5),
    "cell": ParagraphStyle("c", fontName="Body", fontSize=8.3, leading=10.8, textColor=INK),
    "cellb": ParagraphStyle("cb", fontName="BodyB", fontSize=8.3, leading=10.8, textColor=INK),
    "head": ParagraphStyle("h", fontName="BodyB", fontSize=7.8, leading=10, textColor=NAVY),
    "note": ParagraphStyle("n", fontName="Body", fontSize=8, leading=11, textColor=GREY),
    "big": ParagraphStyle("big", fontName="Poppins", fontSize=17, leading=20, textColor=NAVY),
    "bigl": ParagraphStyle("bigl", fontName="Body", fontSize=8.3, leading=10.5, textColor=GREY),
    "bullet": ParagraphStyle("bu", fontName="Body", fontSize=9.4, leading=13.2, textColor=INK, leftIndent=10, bulletIndent=0, spaceAfter=2, bulletFontName="Body"),
}
P = lambda t, s="cell": Paragraph(t, st[s])
W = A4[0] - 40 * mm


def tabla(filas, cab, anchos):
    data = [[P(c, "head") for c in cab]] + [[P(f[0], "cellb")] + [P(x) for x in f[1:]] for f in filas]
    t = Table(data, colWidths=[a * W for a in anchos], repeatRows=1)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, NAVY), ("LINEBELOW", (0, 0), (-1, 0), 0.8, NAVY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.35, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def cifras(items):
    celdas = [[P(n, "big") for n, _ in items], [P(l, "bigl") for _, l in items]]
    t = Table(celdas, colWidths=[W / len(items)] * len(items))
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TINT), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, 0), 9), ("BOTTOMPADDING", (0, 1), (-1, 1), 9),
                           ("LINEAFTER", (0, 0), (-2, -1), 0.6, colors.white)]))
    return t


def pie(c, doc):
    c.saveState()
    c.setFont("Body", 7.5)
    c.setFillColor(GREY)
    c.drawString(20 * mm, 11 * mm, "Madrid 179 · Fuentes de datos · Localización inteligente de oficinas y reequilibrio territorial")
    c.drawRightString(A4[0] - 20 * mm, 11 * mm, str(doc.page))
    c.setStrokeColor(RULE)
    c.setLineWidth(0.4)
    c.line(20 * mm, 14 * mm, A4[0] - 20 * mm, 14 * mm)
    c.restoreState()


CAM = [
    ("Instituto de Estadística de la Comunidad de Madrid",
     "Portal de datos abiertos <i>datos.comunidad.madrid</i>: padrón, censo anual, renta disponible bruta municipal, afiliación a la "
     "Seguridad Social, estadísticas del Catastro por municipio",
     "Demografía, talento, renta, empleo y coste inmobiliario. Canal de 6 de las 8 variables del modelo", "Integrada"),
    ("Dirección General de Economía e Industria (Consejería de Economía, Hacienda y Empleo)",
     "Dinámica Empresarial y Colectivo Empresarial, publicados por el Instituto de Estadística",
     "<b>Variable objetivo</b> (tasa neta de creación de unidades productivas) y especialización en servicios profesionales", "Integrada"),
    ("Dirección General del Servicio Público de Empleo (Consejería de Economía, Hacienda y Empleo)",
     "Paro registrado por municipio, publicado por el Instituto de Estadística", "Mercado laboral local", "Integrada"),
    ("Consorcio Regional de Transportes de Madrid",
     "Portal de datos abiertos del Consorcio: redes GTFS de Metro, Metro Ligero, Cercanías, EMT y autobuses; Encuesta Domiciliaria de "
     "Movilidad 2018", "Acceso ferroviario, distancia a la estación más cercana, densidad de paradas, flujos de movilidad", "Integrada"),
    ("Comunidad de Madrid · cartografía regional",
     "Secciones censales (geometría) y Geoportal IDEM (unidades administrativas, servicios de mapas)",
     "Unión territorial por sección, distancia a Madrid y base del mapa 3D", "Integrada (secciones); prevista (servicios IDEM)"),
    ("Instituto de Estadística · Banco de Datos Municipal y Nomecalles",
     "Series municipales históricas; callejero, secciones censales y códigos postales", "Series largas y geocodificación", "Parcial"),
    ("Dirección General de Suelo", "Portal del Suelo: parcelas de suelo público ofertadas", "Suelo terciario e industrial disponible", "Descargada"),
    ("Registros de la Comunidad de Madrid", "Centros sanitarios, oficinas de farmacia, entidades deportivas, estaciones de calidad del aire",
     "Servicios y calidad de vida para el dashboard", "Descargada"),
    ("BOCM y programas de la Comunidad", "Plan de Reequilibrio Territorial, Pueblos con Vida, deducción fiscal por residencia en "
     "municipios de menos de 2.500 habitantes", "Nivel de ayudas por elegibilidad (capa informativa, filtro o peso opcional)",
     "Parcial: listas oficiales en verificación"),
]

VARIABLES = [
    ("Viabilidad empresarial (objetivo)", "Tasa neta de unidades productivas 2020-24", "D. G. de Economía e Industria (CAM)", "Instituto de Estadística · <i>din_emp</i>"),
    ("Especialización en servicios", "% de unidades productivas en información y servicios profesionales, 2025", "D. G. de Economía e Industria (CAM)", "Instituto de Estadística · <i>col_emp_ramas</i>"),
    ("Dinamismo demográfico", "Crecimiento del padrón 2020-25", "Padrón municipal · INE", "Instituto de Estadística · <i>padron_por_sexo</i>"),
    ("Talento", "% de población con estudios superiores, 2024", "Censo de Población anual · INE", "Instituto de Estadística · <i>poblacion_censada_por_estudios_y_sexo</i>"),
    ("Renta", "Renta disponible bruta per cápita, 2023", "Indicador de renta municipal · INE", "Instituto de Estadística · <i>irpf_indicador_renta</i>"),
    ("Coste inmobiliario", "Valor catastral residencial por unidad urbana, 2026", "Dirección General del Catastro", "Instituto de Estadística · <i>1002054</i>"),
    ("Distancia a Madrid", "Km del centroide municipal a la Puerta del Sol", "Cálculo propio", "Comunidad de Madrid · <i>secciones_censales</i>"),
    ("Acceso ferroviario", "Estaciones de Metro, Metro Ligero o Cercanías", "Consorcio Regional de Transportes (CAM)", "Portal de datos abiertos del Consorcio"),
]

OTRAS = [
    ("INE", "Atlas de Distribución de Renta de los Hogares, Directorio Central de Empresas, Censo 2021, migraciones",
     "Renta y formación por sección censal; empresas por actividad y tamaño", "Parcial"),
    ("Dirección General del Catastro", "Edificios y parcelas INSPIRE de los 179 municipios", "Superficie y uso de los edificios; base del 3D", "Descargada"),
    ("Tesorería General de la Seguridad Social y SEPE", "Afiliación y paro por municipio (también vía el Instituto de Estadística)", "Empleo", "Integrada"),
    ("Base de Datos Nacional de Subvenciones (IGAE)", "Convocatorias y concesiones con ámbito Madrid (API abierta)", "Ayudas aplicables por perfil de negocio", "Descargada"),
    ("Ministerio para la Transformación Digital", "Cobertura de fibra FTTH y 5G por municipio", "Conectividad (filtro opcional)", "Prevista"),
    ("Ayuntamiento de Madrid", "Portal de datos abiertos (674 conjuntos): distritos, barrios, locales y actividades", "Detalle intramunicipal de la capital", "Parcial"),
    ("CNIG / IGN", "Límites, modelos digitales del terreno, usos del suelo", "Relieve y usos del suelo para el mapa 3D", "Prevista"),
    ("OpenStreetMap", "153.517 puntos de interés en 18 categorías (licencia ODbL)", "Servicios para trabajadores: restauración, guarderías, coworking, sanidad, deporte", "Integrada"),
]

PRIVADAS = [
    ("Consultoras inmobiliarias", "Renta de oficinas por m², disponibilidad y absorción por zona", "Informes públicos; series detalladas bajo licencia"),
    ("Portales inmobiliarios", "Precio de oferta y rotación de locales y oficinas", "Acuerdo de acceso a su API"),
    ("Bases de información empresarial", "Sede, tamaño y supervivencia de empresas", "Suscripción"),
    ("Proveedores de puntos de interés", "Servicios y valoraciones con más cobertura rural", "Pago por uso; OpenStreetMap como alternativa"),
    ("Analítica de movilidad por telefonía", "Flujos residencia-trabajo con alta frecuencia", "Convenio o compra de datos agregados"),
]

story = [
    P("MADRID 179 · DOCUMENTO 2 · FUENTES DE DATOS", "eyebrow"),
    P("Fuentes de datos del sistema de localización de oficinas", "title"),
    P("Localización inteligente y reequilibrio territorial en la Comunidad de Madrid · Gregorio García Velasco (UC3M) · "
      "Guillermo Franco Gimeno (UPM)", "sub"),
    P("El sistema se construye sobre los <b>datos oficiales de la Comunidad de Madrid</b>. Todas las variables del modelo se obtienen "
      "de su portal de datos abiertos o de organismos de la Comunidad, y se unen por el código INE de cada uno de los 179 municipios. "
      "Las fuentes estatales y colaborativas complementan esa base, y las privadas son opcionales: el sistema funciona sin ellas.", "body"),
    Spacer(1, 4),
    cifras([("8 de 8", "variables del modelo obtenidas de fuentes de la Comunidad"),
            ("621", "tablas municipales descargadas de datos.comunidad.madrid"),
            ("2.263", "conjuntos de datos del portal catalogados"),
            ("179", "municipios unidos por código INE")]),
    Spacer(1, 6),
    P("1. Fuentes oficiales de la Comunidad de Madrid", "h2"),
    tabla(CAM, ["Organismo", "Fuente o conjunto", "Qué aporta al sistema", "Estado"], [0.22, 0.34, 0.29, 0.15]),
    Spacer(1, 3),
    P("Estado: <b>integrada</b>, en la tabla de 179 municipios y en uso; <b>descargada</b>, disponible y pendiente de explotar; "
      "<b>parcial</b>, integrada en parte; <b>prevista</b>, identificada y pendiente de descarga.", "note"),
]
story.append(KeepTogether([
    P("2. Origen de cada variable del modelo", "h2"),
    P("Cada variable indica quién produce el dato y el conjunto concreto del que se obtiene, para que cualquier cifra se pueda "
      "rehacer. Cuando el productor es el INE o el Catastro, la Comunidad lo republica a escala municipal.", "body"),
    tabla(VARIABLES, ["Variable", "Indicador", "Productor del dato", "Obtenido de"], [0.2, 0.3, 0.22, 0.28]),
]))
story += [
    P("3. Otras fuentes públicas", "h2"),
    tabla(OTRAS, ["Fuente", "Contenido", "Qué aporta al sistema", "Estado"], [0.22, 0.34, 0.29, 0.15]),
]
story.append(KeepTogether([
    P("4. Fuentes privadas o de acceso restringido (opcionales)", "h2"),
    P("Cubrirían el principal hueco de los datos abiertos, el precio y la disponibilidad de oficinas. Su incorporación depende de "
      "licencias o acuerdos y no condiciona la versión basada en datos públicos.", "body"),
    tabla(PRIVADAS, ["Categoría", "Qué aportaría", "Acceso"], [0.26, 0.42, 0.32]),
]))
story += [
    P("5. Criterios de uso", "h2"),
    *[Paragraph(t, st["bullet"], bulletText="•") for t in [
        "<b>Prioridad a la fuente de la Comunidad.</b> Cuando un dato existe en el portal de la Comunidad y en otra fuente, se usa "
        "el de la Comunidad, que ya viene en escala municipal y con código territorial.",
        "<b>Trazabilidad.</b> Cada variable conserva el nombre del conjunto de origen y su año; los cálculos del modelo se pueden "
        "rehacer a mano.",
        "<b>Licencias.</b> Se respetan las condiciones de reutilización de cada portal y la atribución que exigen (por ejemplo, "
        "OpenStreetMap con licencia ODbL).",
        "<b>Datos personales.</b> Solo se usan datos agregados por territorio; los beneficiarios individuales de ayudas no se "
        "publican ni se perfilan.",
        "<b>Actualización.</b> Las series mensuales (afiliación, paro, ayudas) y anuales (padrón, renta, catastro) se recargan con "
        "los scripts del proyecto.",
    ]],
]
SimpleDocTemplate("docs/presentaciones/2_Fuentes_de_datos.pdf", pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                  topMargin=18 * mm, bottomMargin=20 * mm, title="Fuentes de datos · Localización de oficinas CAM",
                  author="Gregorio García Velasco; Guillermo Franco Gimeno").build(story, onFirstPage=pie, onLaterPages=pie)
print("ok")
