"""Diagramas de estados (estilo UML) del funcionamiento de la aplicación, por perfil.
Salidas: docs/informe/estados_emprendedor.{dot,png,svg} y docs/informe/estados_administracion.{dot,png,svg}
Transiciones: "evento [condición] / acción". Colores: azul = lógica ya implementada en el proyecto;
blanco discontinuo = pendiente (número de PENDIENTES.md).
"""
import subprocess

FONT = "Segoe UI"
HECHO = 'fillcolor="#e6effb", color="#256abf"'
PEND = 'fillcolor="#ffffff", color="#898781", style="rounded,dashed,filled"'
UI = 'fillcolor="#ffffff", color="#52514e"'


def st(nid, titulo, detalle="", tipo=UI, nota=""):
    det = f'<BR/><FONT POINT-SIZE="9.5" COLOR="#52514e">{detalle}</FONT>' if detalle else ""
    nt = f'<BR/><FONT POINT-SIZE="8.5" COLOR="#b8312f">{nota}</FONT>' if nota else ""
    return f'  {nid} [label=<<B>{titulo}</B>{det}{nt}>, {tipo}];'


def tr(a, b, ev, extra=""):
    return f'  {a} -> {b} [label=< {ev} >{", " + extra if extra else ""}];'


def cabecera(titulo, sub):
    return [
        "digraph G {",
        f'  graph [rankdir=TB, compound=true, newrank=true, bgcolor="#fcfcfb", pad=0.45, nodesep=0.45, ranksep=0.5, fontname="{FONT}", '
        f'label=<<FONT POINT-SIZE="21"><B>{titulo}</B></FONT><BR/><FONT POINT-SIZE="11" COLOR="#52514e">{sub}</FONT><BR/> >, labelloc=t];',
        f'  node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=12, margin="0.16,0.08", penwidth=1.2];',
        f'  edge [fontname="{FONT}", fontsize=9.5, color="#52514e", fontcolor="#3a3936", arrowsize=0.75, penwidth=1.1];',
        '  inicio [shape=circle, label="", width=0.22, style=filled, fillcolor="#0b0b0b", color="#0b0b0b"];',
        '  fin [shape=doublecircle, label="", width=0.16, style=filled, fillcolor="#0b0b0b", color="#0b0b0b"];',
    ]


def cluster(cid, titulo, color, cuerpo):
    return ([f'  subgraph {cid} {{ label=<<B>{titulo}</B>>; fontname="{FONT}"; fontsize=12; style="rounded"; color="{color}"; margin=12;']
            + ["  " + x for x in cuerpo] + ["  }"])


LEYENDA = [
    '  leyenda [shape=plaintext, style="", label=<<TABLE BORDER="0" CELLSPACING="4">'
    '<TR><TD BGCOLOR="#e6effb" BORDER="1" COLOR="#256abf" WIDTH="22"> </TD><TD ALIGN="LEFT"><FONT POINT-SIZE="10">Lógica ya implementada (scripts del proyecto)</FONT></TD></TR>'
    '<TR><TD BGCOLOR="#ffffff" BORDER="1" COLOR="#52514e"> </TD><TD ALIGN="LEFT"><FONT POINT-SIZE="10">Pantalla o interacción (aplicación por construir, #32)</FONT></TD></TR>'
    '<TR><TD BGCOLOR="#ffffff" BORDER="1" STYLE="dashed" COLOR="#898781"> </TD><TD ALIGN="LEFT"><FONT POINT-SIZE="10">Lógica pendiente · <FONT COLOR="#b8312f">#N</FONT> = tarea en PENDIENTES.md</FONT></TD></TR>'
    '<TR><TD COLSPAN="2" ALIGN="LEFT"><FONT POINT-SIZE="9.5" COLOR="#52514e">Transiciones: evento [condición] / acción</FONT></TD></TR>'
    '</TABLE>>];',
]

# ===================================================================================
# EMPRENDEDOR / EMPRESA
# ===================================================================================
E = cabecera("Diagrama de estados · Perfil Empresa / Emprendedor",
             "Buscar dónde abrir o trasladar una oficina en la Comunidad de Madrid")
E += [st("perfil", "Selección de perfil", "Administración · Empresa / Emprendedor")]
E += cluster("cluster_onb", "1 · ONBOARDING CONVERSACIONAL", "#c98a12", [
    st("describe", "Describiendo el negocio", "texto libre: sector, plantilla, m²,<BR/>presupuesto, transporte, ayudas…"),
    st("clasifica", "Clasificando intención (LLM)", "salida estructurada: filtros duros ·<BR/>preferencias blandas · variables inciertas", PEND, "#29"),
    st("confirma", "Confirmando lo entendido", "resumen editable antes de calcular"),
])
E += cluster("cluster_calc", "2 · CÁLCULO", "#256abf", [
    st("filtra", "Aplicando filtros duros", "Madrid capital · oficinas ≥ 1 ·<BR/>imprescindibles del usuario", HECHO),
    st("vacio", "Sin candidatos", "ningún municipio cumple todos los filtros"),
    st("infiere", "Puntuando candidatos", "GA²M: percentil 0-100 ·<BR/>red bayesiana: P(Alta) y causas para explicar", HECHO),
    st("pondera", "Combinando preferencias", "(S + Σ a·u) / (1 + Σ a) · transporte y ayudas<BR/>(preferencias.py)", HECHO, "coste neto pendiente #36"),
])
E += cluster("cluster_expl", "3 · EXPLORACIÓN EN EL MAPA 3D", "#52514e", [
    st("mapa", "Mapa 3D actualizado", "altura y color = puntuación ·<BR/>descartados aplanados · capas de ayudas y tren"),
    st("pregunta", "Pregunta inteligente", "la de mayor valor de la información ·<BR/>Me da igual · Poco · Muy · Imprescindible · No lo sé", PEND, "#30"),
    st("ficha", "Ficha de municipio", "puntuación desglosada · ayudas aplicables ·<BR/>estación más cercana · coste neto", PEND, "#13 · #31 · #36"),
])
E += cluster("cluster_res", "4 · RESULTADO", "#b8312f", [
    st("propuestas", "Mejores propuestas", "vuelo de cámara al primero ·<BR/>top N con explicación de factores", PEND, "#5 empates · #31"),
    st("compara", "Comparando municipios", "2-3 candidatos lado a lado"),
    st("exporta", "Informe exportado", "PDF con puntuación, supuestos y fuentes"),
])
E += [
    tr("inicio", "perfil", "abrir aplicación"),
    tr("perfil", "describe", "elige Empresa"),
    tr("describe", "clasifica", "enviar descripción"),
    tr("clasifica", "describe", "[descripción ambigua] / pedir aclaración", 'style=dashed'),
    tr("clasifica", "confirma", "/ filtros, evidencias e inciertas"),
    tr("confirma", "describe", "corregir", 'style=dashed'),
    tr("confirma", "filtra", "confirmar"),
    tr("filtra", "vacio", "[0 candidatos]"),
    tr("vacio", "confirma", "relajar un filtro / sugerir el más restrictivo", 'style=dashed'),
    tr("filtra", "infiere", "[≥ 1 candidato] / atributos reales = evidencia"),
    tr("infiere", "pondera", "/ S por municipio"),
    tr("pondera", "mapa", "/ redibujar alturas con transición"),
    tr("mapa", "pregunta", "[quedan inciertas que desempatan]"),
    tr("pregunta", "filtra", "Imprescindible / añadir filtro duro"),
    tr("pregunta", "pondera", "Poco · Muy / peso a calibrado"),
    tr("pregunta", "mapa", "Me da igual · No lo sé / w = 0, reformular más tarde", 'style=dashed'),
    tr("mapa", "ficha", "clic en municipio"),
    tr("ficha", "mapa", "cerrar"),
    tr("mapa", "confirma", "editar preferencias", 'style=dashed'),
    tr("mapa", "propuestas", "Ver mejores propuestas"),
    tr("propuestas", "ficha", "abrir detalle"),
    tr("propuestas", "compara", "seleccionar 2-3"),
    tr("compara", "propuestas", "volver"),
    tr("propuestas", "exporta", "exportar"),
    tr("compara", "exporta", "exportar"),
    tr("exporta", "fin", "salir"),
    tr("propuestas", "mapa", "seguir explorando", 'style=dashed'),
    "  {rank=sink; leyenda}",
] + LEYENDA + ["}"]

# ===================================================================================
# ADMINISTRACIÓN
# ===================================================================================
A = cabecera("Diagrama de estados · Perfil Administración",
             "Diagnóstico territorial y simulación de políticas de reequilibrio · los resultados son escenarios según el modelo, no predicciones")
A += [st("perfil", "Selección de perfil", "Administración · Empresa / Emprendedor"),
      st("objetivo", "Eligiendo objetivo de análisis", "diagnóstico · simular política · comparar municipios")]
A += cluster("cluster_diag", "1 · DIAGNÓSTICO TERRITORIAL", "#256abf", [
    st("ambito", "Definiendo ámbito", "toda la CAM · comarca · tramo de población<BR/>(p. ej. municipios elegibles a reequilibrio)"),
    st("base", "Mapa de viabilidad base", "puntuación GA²M sin preferencias · P(Alta) de la red ·<BR/>capas: dinamismo, ayudas, transporte, coste", HECHO),
    st("municipio", "Ficha diagnóstica de municipio", "estados de los 8 nodos · qué factor limita ·<BR/>tablas y conteos de la auditoría", HECHO),
])
A += cluster("cluster_sim", "2 · SIMULADOR DE POLÍTICAS", "#b8312f", [
    st("politica", "Eligiendo política", "catálogo: ayuda al alquiler / IBI · vivero de empresas ·<BR/>nueva estación · …", PEND, "#17"),
    st("hipotesis", "Revisando hipótesis de traducción", "política → palanca del modelo ·<BR/>p. ej. ayuda al alquiler = Coste baja un nivel (editable)", PEND, "#17"),
    st("supuesto", "Supuesto experto marcado", "palanca sin efecto aprendido en los datos<BR/>(p. ej. tren): se usa un prior declarado"),
    st("interviene", "Intervención do()", "fija la palanca, re-predice sus descendientes,<BR/>mantiene lo demás", PEND, "#16 · requiere #3 monotonía"),
    st("incierto", "Calculando incertidumbre", "bootstrap de los 179 municipios", PEND, "#6"),
    st("escenario", "Escenario calculado", "Δ puntuación con intervalo · municipios que cambian de nivel ·<BR/>efecto sobre el reequilibrio"),
])
A += cluster("cluster_out", "3 · COMPARACIÓN E INFORME", "#52514e", [
    st("comparar", "Comparando escenarios", "lado a lado · base frente a políticas"),
    st("informe", "Informe exportado", "supuestos, intervalos y fuentes ·<BR/>advertencia: escenario, no predicción"),
])
A += [
    tr("inicio", "perfil", "abrir aplicación"),
    tr("perfil", "objetivo", "elige Administración"),
    tr("objetivo", "ambito", "diagnóstico"),
    tr("objetivo", "politica", "simular política"),
    tr("objetivo", "comparar", "comparar municipios / selección múltiple en el mapa"),
    tr("ambito", "base", "aplicar ámbito / puntuación sin preferencias"),
    tr("base", "municipio", "clic en municipio"),
    tr("municipio", "base", "cerrar"),
    tr("municipio", "politica", "simular sobre este municipio"),
    tr("base", "politica", "simular sobre el ámbito"),
    tr("politica", "hipotesis", "seleccionar"),
    tr("hipotesis", "politica", "cambiar política", 'style=dashed'),
    tr("hipotesis", "interviene", "[palanca con efecto aprendido] aceptar"),
    tr("hipotesis", "supuesto", "[palanca sin efecto en los datos]"),
    tr("supuesto", "interviene", "aceptar supuesto / se registra en el informe"),
    tr("interviene", "incierto", "/ P(Viab | do(palanca), resto)"),
    tr("incierto", "escenario", "/ media e intervalo del 90 %"),
    tr("escenario", "hipotesis", "ajustar intensidad", 'style=dashed'),
    tr("escenario", "comparar", "guardar escenario"),
    tr("comparar", "politica", "añadir otra política", 'style=dashed'),
    tr("comparar", "informe", "exportar"),
    tr("escenario", "base", "volver al mapa", 'style=dashed'),
    tr("informe", "fin", "salir"),
    "  {rank=sink; leyenda}",
] + LEYENDA + ["}"]

for nombre, lineas in (("estados_emprendedor", E), ("estados_administracion", A)):
    ruta = f"docs/informe/{nombre}"
    open(ruta + ".dot", "w", encoding="utf-8").write("\n".join(lineas))
    for fmt, extra in (("png", ["-Gdpi=150"]), ("svg", [])):
        subprocess.run(["dot", f"-T{fmt}", *extra, ruta + ".dot", "-o", f"{ruta}.{fmt}"], check=True)
    print("ok:", ruta + ".png")
# Versión de alta resolución del perfil Administración para el PDF de aproximación técnica
subprocess.run(["dot", "-Tpng", "-Gdpi=300", "docs/informe/estados_administracion.dot", "-o",
                "docs/informe/estados_administracion_300ppp.png"], check=True)
